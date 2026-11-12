"""Replay a schedule against the serving layer (PROTOCOL §4; decision 12).

Each session is replayed in order on one worker; a multi-turn conversation carries the teacher's
own earlier answers as history (content only, thinking stripped by the server's parser). Sessions
are dispatched in scheduled-start order with bounded concurrency. Every record carries the
scheduled timestamp (t_sched_ns), which the cadence and rate detectors use; token and cache
statistics are whatever the server reports under the replay's real load. A failed request is
written by the client as an in-flight stub and counted here; the session then stops, because its
later turns would have a broken history. A prompt that leaves no room for an answer in the context
window (sampling_fn returns None) also stops the session and is counted separately.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from dev_harness.benign import ScheduledRequest
from dev_harness.client import ChatClient, Sampling

NS = 1_000_000_000
STAT_KEYS = ("completed", "failed", "requests_skipped_after_failure", "requests_too_long")


def replay(
    schedule: list[ScheduledRequest],
    client: ChatClient,
    run_id: str,
    sampling: Sampling,
    concurrency: int,
    on_progress: Callable[[int, int, dict], None] | None = None,
    sampling_fn: Callable[[list[dict[str, str]]], Sampling | None] | None = None,
) -> dict:
    sessions: dict[str, list[ScheduledRequest]] = defaultdict(list)
    for r in schedule:
        sessions[r.session_id].append(r)
    order = sorted(sessions.values(), key=lambda s: (min(r.t_sched_s for r in s), s[0].session_id))
    stats = {"sessions": len(order), "requests": len(schedule), "sessions_aborted": 0}
    stats.update({k: 0 for k in STAT_KEYS})

    def run_session(sess: list[ScheduledRequest]) -> dict:
        sess = sorted(sess, key=lambda r: r.request_index)
        history: dict[str, list[dict[str, str]]] = defaultdict(list)
        out = {k: 0 for k in STAT_KEYS}
        for k, r in enumerate(sess):
            msgs = history[r.conv_id] + [{"role": "user", "content": r.user_content}]
            smp = sampling_fn(msgs) if sampling_fn else sampling
            if smp is None:
                out["requests_too_long"] = 1
                out["requests_skipped_after_failure"] = len(sess) - k - 1
                return out
            try:
                comp = client.send(
                    run_id=run_id,
                    identity_id=r.identity_id,
                    session_id=r.session_id,
                    request_index=r.request_index,
                    arm=f"benign:{r.component}",
                    messages=msgs,
                    sampling=smp,
                    t_sched_ns=int(r.t_sched_s * NS),
                )
            except Exception:  # noqa: BLE001 - the stub record already marks it in flight; counted here
                out["failed"] = 1
                out["requests_skipped_after_failure"] = len(sess) - k - 1
                return out
            history[r.conv_id] = msgs + [{"role": "assistant", "content": comp.content}]
            out["completed"] += 1
        return out

    n = 0
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        for res in ex.map(run_session, order):
            for k in STAT_KEYS:
                stats[k] += res[k]
            stats["sessions_aborted"] += res["failed"] + res["requests_too_long"]
            n += 1
            if on_progress and n % 200 == 0:
                on_progress(n, len(order), stats)
    return stats
