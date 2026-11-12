"""Verifiers must pass a correct answer and fail a wrong one; contamination must catch a plant."""

from dev_harness.pool import Item, _boxed, contamination, normalise
from dev_harness.stats import mean_bca_ci
from dev_harness.verify import (
    verify_gsm8k,
    verify_humaneval,
    verify_math_boxed,
    verify_mbpp,
    verify_apps,
)


def test_boxed_extraction_balanced():
    assert _boxed(r"so \boxed{\frac{1}{2}} done") == r"\frac{1}{2}"
    assert _boxed("no box") is None


def test_math_boxed_equivalence_and_rejection():
    assert verify_math_boxed(r"answer: \boxed{1/2}", r"\frac{1}{2}")
    assert not verify_math_boxed(r"answer: \boxed{1/3}", r"\frac{1}{2}")
    assert verify_math_boxed(
        "so the answer is $\\frac{1}{2}$.", r"\frac{1}{2}"
    )  # un-boxed, extracted (F25)
    assert not verify_math_boxed("so the answer is $\\frac{1}{3}$.", r"\frac{1}{2}")
    assert not verify_math_boxed("no answer here", r"\frac{1}{2}")


def test_gsm8k_numeric():
    assert verify_gsm8k("so the total is 1,234 dollars", "1234")
    assert verify_gsm8k(r"\boxed{42}", "42")
    assert not verify_gsm8k("so 41 then 43", "42")


def test_mbpp_asserts_pass_and_fail():
    tests = ["assert add(1, 2) == 3"]
    assert verify_mbpp("```python\ndef add(a, b):\n    return a + b\n```", tests, "")
    assert not verify_mbpp("```python\ndef add(a, b):\n    return a - b\n```", tests, "")


def test_humaneval_completion_mode():
    prompt = 'def inc(x):\n    """return x+1"""\n'
    test = "def check(f):\n    assert f(1) == 2\n"
    assert verify_humaneval("    return x + 1\n", prompt, test, "inc", completion_mode=True)
    assert not verify_humaneval("    return x\n", prompt, test, "inc", completion_mode=True)


def test_apps_io():
    code = "```python\nimport sys\nprint(int(sys.stdin.readline())*2)\n```"
    assert verify_apps(code, ["3\n"], ["6\n"])
    assert not verify_apps(code, ["3\n"], ["7\n"])


def test_sandbox_timeout_is_a_failure():
    assert not verify_mbpp("```python\nwhile True: pass\n```", ["assert True"], "")


def _item(i, prompt):
    return Item(i, "src", "math", prompt, "math_boxed", {"answer": "1"})


def test_contamination_catches_exact_and_ngram_plants():
    suite = {
        "s": [
            _item(
                "s1",
                "Find the sum of the first ten positive integers that are divisible by three and five.",
            )
        ]
    }
    pool = {
        "p": [
            _item(
                "p1",
                "Find the sum of the first ten positive integers that are divisible by three and five.",
            ),
            _item(
                "p2",
                "A question: find the sum of the first ten positive integers that are divisible by three and five, then double it.",
            ),
            _item("p3", "Compute 2+2."),
        ]
    }
    clean, rep = contamination(pool, suite, n=13)
    assert [it.id for it in clean["p"]] == ["p3"]
    assert rep["exact_hits"]["p"]["s"] == 1 and rep["ngram_hits"]["p"]["s"] == 1


def test_normalise():
    assert normalise("  Hello,  World! ") == "hello world"


def test_bca_ci_brackets_mean():
    ci = mean_bca_ci([0, 1, 1, 0, 1, 1, 1, 0, 1, 1], seed=0)
    assert ci["lo"] <= ci["mean"] <= ci["hi"] and ci["method"] == "BCa"


def test_math_verification_works_inside_worker_threads():
    """F17: math-verify's signal-based timeout raises in threads; our wrapper must not turn that into False."""
    import threading

    out = {}

    def w():
        out["r"] = verify_math_boxed(r"\boxed{p-q}", "p - q")

    t = threading.Thread(target=w)
    t.start()
    t.join()
    assert out["r"] is True


def test_math_verification_blowup_is_killed_and_the_pool_recovers():
    """F38: a tower of powers makes sympy build an integer with billions of digits in one
    interpreter-lock-holding operation. The verifier must give up within its budget (raising,
    never returning a silent False after hanging) and keep working afterwards."""
    import time

    import pytest

    from dev_harness.verify import VerifyTimeout

    t0 = time.monotonic()
    with pytest.raises(VerifyTimeout):
        verify_math_boxed(r"\boxed{10^{10^{10}} \cdot 3^{9^{9}}}", "2", timeout_s=4.0)
    assert time.monotonic() - t0 < 15
    assert verify_math_boxed(r"\boxed{1/2}", r"\frac{1}{2}")


def test_answer_text_rule_a7():
    from dev_harness.verify import answer_text

    assert answer_text("x", "r") == ("x", False)
    assert answer_text("", "r") == ("r", True)
    assert answer_text("  ", None) == ("  ", False)


def test_creditable_rule_a8():
    from dev_harness.verify import creditable

    assert creditable("so the answer is 5", "stop")
    assert creditable(r"\boxed{5} and then cut", "length")
    assert not creditable("looping text ... 1 ... 1 ... 1", "length")
