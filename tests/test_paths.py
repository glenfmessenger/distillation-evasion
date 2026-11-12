"""HARNESS_HOST_REPO has no default and is never the code root (charter 3.11, global rule 7)."""

import pytest

from dev_harness import paths


def test_unset_env_raises(monkeypatch):
    monkeypatch.delenv(paths.ENV_VAR, raising=False)
    with pytest.raises(paths.HostRepoUnset):
        paths.host_repo()


def test_nonexistent_dir_raises(monkeypatch, tmp_path):
    monkeypatch.setenv(paths.ENV_VAR, str(tmp_path / "missing"))
    with pytest.raises(paths.HostRepoUnset):
        paths.host_repo()


def test_resolves_under_env_not_code_root(monkeypatch, tmp_path):
    monkeypatch.setenv(paths.ENV_VAR, str(tmp_path))
    root = paths.raw_results_root()
    assert root == tmp_path.resolve() / "results" / "raw"
    code_root = paths.Path(paths.__file__).resolve().parents[2]
    assert code_root not in root.parents, "data path must not live under the code root"
