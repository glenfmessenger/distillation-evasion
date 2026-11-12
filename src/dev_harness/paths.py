"""Data and output paths.

Every path that is not code resolves through the HARNESS_HOST_REPO environment variable
(charter 3.11). Nothing here falls back to the code root; if the variable is unset the
loader raises. There is no default.
"""

from __future__ import annotations

import os
from pathlib import Path

ENV_VAR = "HARNESS_HOST_REPO"


class HostRepoUnset(RuntimeError):
    """Raised when HARNESS_HOST_REPO is not set or does not point to a directory."""


def host_repo() -> Path:
    value = os.environ.get(ENV_VAR)
    if not value:
        raise HostRepoUnset(
            f"{ENV_VAR} is not set. Data and results never resolve relative to the code root; "
            f"export {ENV_VAR}=/path/to/host/repo before running."
        )
    path = Path(value).expanduser()
    if not path.is_dir():
        raise HostRepoUnset(f"{ENV_VAR}={value!r} is not an existing directory.")
    return path.resolve()


def raw_results_root() -> Path:
    return host_repo() / "results" / "raw"


def aggregates_root() -> Path:
    return host_repo() / "results" / "aggregates"


def traces_root() -> Path:
    return host_repo() / "traces"
