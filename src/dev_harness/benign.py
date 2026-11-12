"""Benign traffic model (PROTOCOL §4, decision 8): a replay schedule derived from WildChat-1M.

The schedule carries prompt text because the replay must send real prompts to the teacher so that
serving statistics are real. Detectors never see this module's objects: they read RequestRecord,
which has no content field. Content is used here for CONSTRUCTION only (e.g. selecting
conversations that contain code fences for the code-assistant component), as the protocol states.

Identity = pseudo-user = sha1(hashed_ip | user-agent). Session = a pseudo-user's requests with no
idle gap above SESSION_GAP_S. Request k of a conversation is its k-th user turn; the replay
supplies the teacher's own earlier answers as history. Scheduled time is the corpus timestamp of the reply to each turn
(seconds from the identity's first request; WildChat does not timestamp user messages), or a seeded machine cadence for constructed
heavy-tail components. Loaders raise on missing files or columns; conversations lacking user
timestamps are skipped and counted, never patched.
"""

from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from pathlib import Path

SESSION_GAP_S = 1800.0
COMPONENTS = ("conversational", "eval_harness", "batch_summarise", "agent_loop", "code_assistant")
WEIGHTS = {
    "conversational": 0.85,
    "eval_harness": 0.04,
    "batch_summarise": 0.03,
    "agent_loop": 0.03,
    "code_assistant": 0.05,
}
REQUIRED_COLUMNS = ("conversation_hash", "conversation", "language", "toxic", "hashed_ip", "header")
LONG_PROMPT_CHARS = 4000
MAX_PROMPT_CHARS = (
    24000  # ~6k tokens; longer prompts cannot leave room for an answer in 16k context
)
AGENT_MIN_TURNS = 8


class BenignDataError(RuntimeError):
    pass


@dataclass(frozen=True)
class Conversation:
    conv_hash: str
    user_key: str
    turns: tuple[tuple[float, str], ...]  # (unix seconds, user content) per user turn, in order
    has_code: bool


@dataclass(frozen=True)
class ScheduledRequest:
    identity_id: str
    session_id: str
    request_index: int  # within session
    component: str
    t_sched_s: float  # seconds on the identity's own timeline
    conv_id: str  # requests sharing conv_id form one multi-turn conversation
    turn_index: int  # 0-based user turn within the conversation
    user_content: str


def user_key(hashed_ip: str, user_agent: str | None) -> str:
    return hashlib.sha1(f"{hashed_ip}|{user_agent or ''}".encode()).hexdigest()[:16]


def iter_wildchat(
    parquet_files: Iterable[Path], english_only: bool = True
) -> Iterator[Conversation | None]:
    """Yield Conversation, or None for a row skipped for missing user timestamps (caller counts)."""
    import pyarrow.parquet as pq

    files = list(parquet_files)
    if not files:
        raise BenignDataError("no WildChat parquet files given")
    for f in files:
        pf = pq.ParquetFile(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in pf.schema_arrow.names]
        if missing:
            raise BenignDataError(f"{f}: missing columns {missing}")
        for batch in pf.iter_batches(batch_size=2000, columns=list(REQUIRED_COLUMNS)):
            for row in batch.to_pylist():
                if row["toxic"] or (english_only and row["language"] != "English"):
                    continue
                turns, code, bad = [], False, False
                msgs = row["conversation"]
                for k, m in enumerate(msgs):
                    code = code or "```" in (m["content"] or "")
                    if m["role"] != "user":
                        continue
                    # WildChat timestamps the assistant reply, not the user message (FINDINGS F31):
                    # a turn's time is the timestamp of the reply that follows it.
                    reply = (
                        msgs[k + 1]
                        if k + 1 < len(msgs) and msgs[k + 1]["role"] == "assistant"
                        else None
                    )
                    if reply is None or reply["timestamp"] is None:
                        bad = True
                        break
                    turns.append((reply["timestamp"].timestamp(), m["content"] or ""))
                if bad:
                    yield None
                    continue
                if not turns or any(not c.strip() or len(c) > MAX_PROMPT_CHARS for _, c in turns):
                    continue
                ua = (row["header"] or {}).get("user-agent")
                yield Conversation(
                    row["conversation_hash"], user_key(row["hashed_ip"], ua), tuple(turns), code
                )


def _machine_gaps(rng: random.Random, n: int) -> list[float]:
    """Seeded machine cadence: small think time between consecutive requests."""
    t, out = 0.0, []
    for _ in range(n):
        out.append(t)
        t += rng.uniform(0.5, 2.0)
    return out


def _sessionise(
    identity: str, component: str, reqs: list[tuple[float, str, int, str]]
) -> list[ScheduledRequest]:
    """reqs: (t_abs_s, conv_id, turn_index, content), any order. Splits sessions on idle gaps."""
    reqs = sorted(reqs, key=lambda r: (r[0], r[1], r[2]))
    t0, out, sess, idx, last = reqs[0][0], [], 0, 0, reqs[0][0]
    for t, conv, turn, content in reqs:
        if t - last > SESSION_GAP_S:
            sess, idx = sess + 1, 0
        out.append(
            ScheduledRequest(
                identity, f"{identity}:s{sess}", idx, component, t - t0, conv, turn, content
            )
        )
        idx, last = idx + 1, t
    return out


def build_schedule(
    conversations: Iterable[Conversation | None],
    n_identities: int,
    seed: int,
    eval_prompts: list[str],
) -> tuple[list[ScheduledRequest], dict]:
    """Build the five-component mixture. Weights are over identities (PROTOCOL §4)."""
    rng = random.Random(seed)
    by_user: dict[str, list[Conversation]] = defaultdict(list)
    n_skipped_ts = 0
    for c in conversations:
        if c is None:
            n_skipped_ts += 1
        else:
            by_user[c.user_key].append(c)
    if not by_user:
        raise BenignDataError("no usable conversations")
    users = sorted(by_user)
    rng.shuffle(users)
    want = {k: round(WEIGHTS[k] * n_identities) for k in COMPONENTS}

    code_users = [u for u in users if any(c.has_code for c in by_user[u])]
    code_set = set(code_users[: want["code_assistant"]])
    agent_convs = [
        c for u in users if u not in code_set for c in by_user[u] if len(c.turns) >= AGENT_MIN_TURNS
    ]
    long_prompts = [
        (c.conv_hash, t[1])
        for u in users
        for c in by_user[u]
        if len(c.turns) == 1
        for t in c.turns
        if len(t[1]) >= LONG_PROMPT_CHARS
    ]
    conv_users = [u for u in users if u not in code_set][: want["conversational"]]
    for name, have, need in (
        ("code_assistant", len(code_set), want["code_assistant"]),
        ("conversational", len(conv_users), want["conversational"]),
        ("agent_loop", len(agent_convs), want["agent_loop"]),
        ("batch_summarise", len(long_prompts), 20 * want["batch_summarise"]),
    ):
        if have < need:
            raise BenignDataError(
                f"component {name}: need {need}, corpus slice provides {have}; read more files"
            )
    if want["eval_harness"] and len(eval_prompts) < 200:
        raise BenignDataError(f"eval_harness needs >= 200 prompts, got {len(eval_prompts)}")

    sched: list[ScheduledRequest] = []

    def real_user(u: str, component: str) -> None:
        reqs = [
            (t, c.conv_hash, i, content)
            for c in by_user[u]
            for i, (t, content) in enumerate(c.turns)
        ]
        sched.extend(_sessionise(f"b:{component[:4]}:{u}", component, reqs))

    for u in conv_users:
        real_user(u, "conversational")
    for u in sorted(code_set):
        real_user(u, "code_assistant")
    rng.shuffle(agent_convs)
    for k, c in enumerate(agent_convs[: want["agent_loop"]]):
        ident = f"b:agen:{k:05d}"
        for i, (g, (_, content)) in enumerate(zip(_machine_gaps(rng, len(c.turns)), c.turns)):
            sched.append(
                ScheduledRequest(ident, f"{ident}:s0", i, "agent_loop", g, c.conv_hash, i, content)
            )
    rng.shuffle(long_prompts)
    pos = 0
    for k in range(want["batch_summarise"]):
        n = rng.randint(20, min(200, max(20, len(long_prompts) // max(want["batch_summarise"], 1))))
        ident = f"b:batc:{k:05d}"
        chunk = long_prompts[pos : pos + n]
        pos += n
        for i, (g, (h, content)) in enumerate(zip(_machine_gaps(rng, len(chunk)), chunk)):
            sched.append(
                ScheduledRequest(
                    ident, f"{ident}:s0", i, "batch_summarise", g, f"{h}:{k}", 0, content
                )
            )
    for k in range(want["eval_harness"]):
        n = rng.randint(200, min(1000, len(eval_prompts)))
        ident = f"b:eval:{k:05d}"
        picks = rng.sample(eval_prompts, n)
        for i, (g, content) in enumerate(zip(_machine_gaps(rng, n), picks)):
            sched.append(
                ScheduledRequest(
                    ident, f"{ident}:s0", i, "eval_harness", g, f"{ident}:q{i}", 0, content
                )
            )

    per_ident: dict[str, int] = defaultdict(int)
    per_sess: dict[str, int] = defaultdict(int)
    comp_of: dict[str, str] = {}
    for r in sched:
        per_ident[r.identity_id] += 1
        per_sess[r.session_id] += 1
        comp_of[r.identity_id] = r.component

    def q(vals: list[int], p: float) -> int:
        v = sorted(vals)
        return v[min(len(v) - 1, int(p * len(v)))]

    manifest = {
        "seed": seed,
        "n_identities_requested": n_identities,
        "weights": WEIGHTS,
        "session_gap_s": SESSION_GAP_S,
        "n_identities": len(per_ident),
        "n_sessions": len(per_sess),
        "n_requests": len(sched),
        "n_conversations_skipped_missing_timestamps": n_skipped_ts,
        "n_users_in_slice": len(users),
        "identities_by_component": {
            k: sum(1 for c in comp_of.values() if c == k) for k in COMPONENTS
        },
        "requests_by_component": {k: sum(1 for r in sched if r.component == k) for k in COMPONENTS},
        "requests_per_identity": {
            "p50": q(list(per_ident.values()), 0.5),
            "p90": q(list(per_ident.values()), 0.9),
            "p99": q(list(per_ident.values()), 0.99),
            "max": max(per_ident.values()),
        },
        "requests_per_session": {
            "p50": q(list(per_sess.values()), 0.5),
            "p90": q(list(per_sess.values()), 0.9),
            "p99": q(list(per_sess.values()), 0.99),
            "max": max(per_sess.values()),
        },
        "identities_with_ge_30_requests": sum(v >= 30 for v in per_ident.values()),
        "identities_with_ge_30_by_component": {
            k: sum(1 for i, v in per_ident.items() if v >= 30 and comp_of[i] == k)
            for k in COMPONENTS
        },
        "sessions_with_ge_10_requests": sum(v >= 10 for v in per_sess.values()),
        "prompt_chars_total": sum(len(r.user_content) for r in sched),
    }
    return sched, manifest


def real_user_schedule(
    conversations: Iterable[Conversation | None],
) -> tuple[list[ScheduledRequest], int]:
    """Every real pseudo-user in the corpus slice, sessionised on the corpus timeline. Component is
    code_assistant if any of the user's conversations contains a code fence, else conversational."""
    by_user: dict[str, list[Conversation]] = defaultdict(list)
    skipped = 0
    for c in conversations:
        if c is None:
            skipped += 1
        else:
            by_user[c.user_key].append(c)
    if not by_user:
        raise BenignDataError("no usable conversations")
    sched: list[ScheduledRequest] = []
    for u in sorted(by_user):
        comp = "code_assistant" if any(c.has_code for c in by_user[u]) else "conversational"
        reqs = [
            (t, c.conv_hash, i, content)
            for c in by_user[u]
            for i, (t, content) in enumerate(c.turns)
        ]
        sched.extend(_sessionise(f"b:{comp[:4]}:{u}", comp, reqs))
    return sched, skipped


def constructed_schedule(
    conversations: Iterable[Conversation | None],
    eval_prompts: list[str],
    seed: int,
    n_eval: int,
    n_batch: int,
    n_agent: int,
    eval_range: tuple[int, int] = (50, 200),
    batch_range: tuple[int, int] = (30, 60),
) -> list[ScheduledRequest]:
    """Constructed heavy-tail components at machine cadence: eval harness, batch jobs, agent loops."""
    rng = random.Random(seed)
    convs = [c for c in conversations if c is not None]
    agent = [c for c in convs if len(c.turns) >= AGENT_MIN_TURNS]
    long_prompts = [
        (c.conv_hash, c.turns[0][1])
        for c in convs
        if len(c.turns) == 1 and len(c.turns[0][1]) >= LONG_PROMPT_CHARS
    ]
    if (
        len(agent) < n_agent
        or len(long_prompts) < n_batch * batch_range[1]
        or len(eval_prompts) < eval_range[1]
    ):
        raise BenignDataError(
            f"constructed components: agent {len(agent)}/{n_agent}, long prompts "
            f"{len(long_prompts)}/{n_batch * batch_range[1]}, eval prompts {len(eval_prompts)}"
        )
    out: list[ScheduledRequest] = []
    rng.shuffle(agent)
    for k, c in enumerate(agent[:n_agent]):
        ident = f"b:agen:{k:05d}"
        for i, (g, (_, content)) in enumerate(zip(_machine_gaps(rng, len(c.turns)), c.turns)):
            out.append(
                ScheduledRequest(
                    ident, f"{ident}:s0", i, "agent_loop", g, f"{c.conv_hash}:a{k}", i, content
                )
            )
    rng.shuffle(long_prompts)
    pos = 0
    for k in range(n_batch):
        n = rng.randint(*batch_range)
        ident = f"b:batc:{k:05d}"
        for i, (g, (h, content)) in enumerate(
            zip(_machine_gaps(rng, n), long_prompts[pos : pos + n])
        ):
            out.append(
                ScheduledRequest(
                    ident, f"{ident}:s0", i, "batch_summarise", g, f"{h}:b{k}", 0, content
                )
            )
        pos += n
    for k in range(n_eval):
        n = rng.randint(*eval_range)
        ident = f"b:eval:{k:05d}"
        for i, (g, content) in enumerate(zip(_machine_gaps(rng, n), rng.sample(eval_prompts, n))):
            out.append(
                ScheduledRequest(
                    ident, f"{ident}:s0", i, "eval_harness", g, f"{ident}:q{i}", 0, content
                )
            )
    return out


def select_replay_subset(
    full: list[ScheduledRequest],
    n_heavy: int,
    n_light: int,
    cap: int,
    seed: int,
    heavy_min: int = 30,
) -> tuple[list[ScheduledRequest], dict]:
    """Stratified replay subset of real users: `n_heavy` identities with >= heavy_min requests and
    `n_light` with fewer, each truncated to its first `cap` requests on its own timeline (a prefix,
    so conversation histories stay intact). Strata sizes and population counts are returned so the
    sample can be re-weighted. Raises if a stratum is too small."""
    rng = random.Random(seed)
    by_ident: dict[str, list[ScheduledRequest]] = defaultdict(list)
    for r in full:
        by_ident[r.identity_id].append(r)
    heavy = sorted(i for i, v in by_ident.items() if len(v) >= heavy_min)
    light = sorted(i for i, v in by_ident.items() if len(v) < heavy_min)
    if len(heavy) < n_heavy or len(light) < n_light:
        raise BenignDataError(
            f"strata too small: heavy {len(heavy)}/{n_heavy}, light {len(light)}/{n_light}"
        )
    pick = rng.sample(heavy, n_heavy) + rng.sample(light, n_light)
    out: list[ScheduledRequest] = []
    n_trunc = 0
    for i in pick:
        reqs = sorted(by_ident[i], key=lambda r: (r.t_sched_s, r.session_id, r.request_index))
        n_trunc += len(reqs) > cap
        out.extend(reqs[:cap])
    info = {
        "population_heavy": len(heavy),
        "population_light": len(light),
        "sampled_heavy": n_heavy,
        "sampled_light": n_light,
        "cap_per_identity": cap,
        "identities_truncated": n_trunc,
        "heavy_min": heavy_min,
        "seed": seed,
    }
    return out, info


def write_schedule(sched: list[ScheduledRequest], path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with path.open("w") as fh:
        for r in sched:
            line = json.dumps(asdict(r), ensure_ascii=False) + "\n"
            fh.write(line)
            h.update(line.encode())
    return h.hexdigest()


def read_schedule(path: Path) -> list[ScheduledRequest]:
    out = []
    with Path(path).open() as fh:
        for n, line in enumerate(fh, 1):
            try:
                out.append(ScheduledRequest(**json.loads(line)))
            except Exception as e:  # noqa: BLE001
                raise BenignDataError(f"{path}:{n}: malformed schedule row: {e}") from e
    if not out:
        raise BenignDataError(f"{path}: empty schedule")
    return out
