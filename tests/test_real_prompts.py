import pytest

from dev_harness.benign import Conversation
from dev_harness.real_prompts import replay_user_keys, select_real_prompts


def _c(h, user, text):
    return Conversation(h, user, ((0.0, text),), False)


def test_replay_user_keys_reads_only_real_user_identities():
    keys = replay_user_keys(["b:conv:aaaa", "b:eval:0", "b:conv:bbbb", "b:agent:3"])
    assert keys == {"aaaa", "bbbb"}
    with pytest.raises(ValueError):
        replay_user_keys(["b:eval:0"])


def test_select_real_prompts_excludes_and_counts_each_reason():
    long = " ".join(f"w{i}" for i in range(20))
    convs = [
        _c("h1", "u1", "hello there one"),
        _c("h2", "u2", "hello there one"),  # duplicate text
        _c("h3", "ex", "unique three"),  # user in the replay subset
        _c("h4", "u4", long),  # shares a 13-gram with a replay prompt
        _c("h5", "u5", "five"),
        _c("h6", "u6", "six"),
    ]
    chosen, counts = select_real_prompts(convs, {"ex"}, [long + " tail"], n=3, seed=0)
    assert sorted(d["id"] for d in chosen) == ["wc:h1", "wc:h5", "wc:h6"]
    assert counts["dropped_duplicate_text"] == 1
    assert counts["dropped_user_in_replay_subset"] == 1
    assert counts["dropped_ngram_overlap_with_replay"] == 1
    assert counts["candidates"] == 3
    with pytest.raises(ValueError):
        select_real_prompts(convs, {"ex"}, [long], n=4, seed=0)


def test_prompt_file_round_trip_survives_unicode_line_separators(tmp_path):
    """F45: a prompt containing U+2028 must come back as one record, not crash the reader."""
    import json
    import subprocess
    import sys
    from pathlib import Path

    text = "first part\u2028second part"
    f = tmp_path / "prompts.jsonl"
    f.write_text(
        json.dumps(
            {"id": "wc:1", "source": "s", "messages": [{"role": "user", "content": text}]},
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    code = (
        "import json,sys\n"
        "from pathlib import Path\n"
        "with Path(sys.argv[1]).open(encoding='utf-8') as fh:\n"
        "    rows=[json.loads(l) for l in fh if l.strip()]\n"
        "assert len(rows)==1 and rows[0]['messages'][0]['content']==%r, rows\n"
        "assert len(Path(sys.argv[1]).read_text(encoding='utf-8').splitlines())==2\n" % text
    )
    r = subprocess.run([sys.executable, "-c", code, str(f)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "with Path(a.prompt_file).open" in Path("scripts/run_campaign.py").read_text()
