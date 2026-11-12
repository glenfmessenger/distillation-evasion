import json

import pytest

from dev_harness.sft_data import examples_for, load_pairs


def _write(tmp_path, rows):
    p = tmp_path / "pairs.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return p


def _row(i, finish="stop", gen=100):
    return {
        "id": f"x:{i}",
        "finish": finish,
        "generated_tokens": gen,
        "messages": [{"role": "user", "content": "q"}],
        "reasoning": "r",
        "content": "a",
    }


def test_load_pairs_counts_everything_it_leaves_out(tmp_path):
    rows = [
        _row(1),
        _row(1),
        _row(2, finish="length"),
        _row(3, gen=5000),
        {"id": "x:9", "error": "e"},
    ]
    kept, counts, h0 = load_pairs(_write(tmp_path, rows))
    assert [r["id"] for r in kept] == ["x:1", "x:3"]
    assert counts == {"errors": 1, "dropped_finish_length": 1, "dropped_over_max_gen": 0}
    kept, counts, h1 = load_pairs(_write(tmp_path, rows), max_gen_tokens=4096)
    assert [r["id"] for r in kept] == ["x:1"]
    assert counts["dropped_over_max_gen"] == 1
    assert h0 != h1  # the data hash follows the selection


def test_load_pairs_raises_when_nothing_is_usable(tmp_path):
    with pytest.raises(RuntimeError):
        load_pairs(_write(tmp_path, [_row(1, finish="length")]))


def test_answer_only_copy_puts_the_think_block_in_the_prompt():
    one = examples_for("P", _row(1), "<eos>", answer_only_copy=False)
    assert one == [{"prompt": "P", "completion": "<think>\nr\n</think>\n\na<eos>"}]
    two = examples_for("P", _row(1), "<eos>", answer_only_copy=True)
    assert two[0] == one[0]
    assert two[1] == {"prompt": "P<think>\nr\n</think>\n\n", "completion": "a<eos>"}
