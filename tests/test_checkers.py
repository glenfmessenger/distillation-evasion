"""The checkers must catch a planted violation (a check that cannot fail is not a check; charter 3.4)."""

from pathlib import Path

import check_no_fallbacks
import check_prose_numerals


def test_prose_checker_flags_hand_typed_numeral(tmp_path: Path):
    tex = tmp_path / "body.tex"
    tex.write_text("The detector fired on 12 sessions.\n")
    assert check_prose_numerals.violations(tex) == [(1, "The detector fired on 12 sessions.")]


def test_prose_checker_accepts_macro_and_refs(tmp_path: Path):
    tex = tmp_path / "body.tex"
    tex.write_text(
        "The detector fired on \\DSixSessions{} sessions (Table~\\ref{tab:d6}).\n"
        "\\includegraphics[width=0.9\\linewidth]{fig1}\n"
        "Section 3 % numeral-ok: section cross-reference typed by hand\n"
    )
    assert check_prose_numerals.violations(tex) == []


def test_prose_checker_main_returns_nonzero(tmp_path: Path):
    tex = tmp_path / "x.tex"
    tex.write_text("AUC was 0.91.\n")
    assert check_prose_numerals.main([str(tex)]) == 1


def test_fallback_checker_flags_defaulted_env(tmp_path: Path):
    py = tmp_path / "loader.py"
    py.write_text('root = os.environ.get("HARNESS_HOST_REPO", ".")\n')
    hits = check_no_fallbacks.scan(py)
    assert hits and any("HARNESS_HOST_REPO" in why for _, why, _ in hits)


def test_fallback_checker_flags_synthetic(tmp_path: Path):
    py = tmp_path / "loader.py"
    py.write_text("data = make_synthetic_traffic()\n")
    assert check_no_fallbacks.scan(py)


def test_fallback_checker_exemption_is_explicit(tmp_path: Path):
    py = tmp_path / "loader.py"
    py.write_text("x = 'synthetic'  # fallback-ok: string literal in an error message\n")
    assert check_no_fallbacks.scan(py) == []


def test_fallback_checker_clean_on_real_source():
    root = Path(__file__).resolve().parents[1]
    hits = [(p, h) for p in (root / "src").rglob("*.py") for h in check_no_fallbacks.scan(p)]
    assert hits == [], hits
