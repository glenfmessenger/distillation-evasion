"""Assert that the hooks ARE installed, not that they could be (charter 3.4)."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_precommit_config_lists_every_checker():
    cfg = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text())
    ids = {h["id"] for repo in cfg["repos"] for h in repo["hooks"]}
    assert {"no-untraced-numerals", "no-silent-fallbacks", "pytest"} <= ids


def test_git_precommit_hook_is_installed():
    hook = ROOT / ".git" / "hooks" / "pre-commit"
    assert hook.exists(), "run `pre-commit install`; the hook is not installed"
    assert "pre-commit" in hook.read_text()
