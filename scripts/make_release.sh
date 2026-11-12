#!/usr/bin/env bash
# Export a curated public release of this repository into a fresh directory with a single commit.
# Excludes process-only files (agent instructions, plans, status, session log, the review memo),
# build caches and anything gitignored. The development repository keeps the full history.
# Usage: scripts/make_release.sh <target-dir> [tag]
set -euo pipefail
TARGET="${1:?target dir}"; TAG="${2:-v1.0}"
SRC="$(cd "$(dirname "$0")/.." && pwd)"
[ -e "$TARGET" ] && { echo "refusing to overwrite $TARGET"; exit 1; }
mkdir -p "$TARGET"
git -C "$SRC" archive HEAD | tar -x -C "$TARGET"
cd "$TARGET"
rm -rf CLAUDE.md PLAN.md STATUS.md SESSION_LOG.md docs/review_hardstop_3_4.md docs/evidence.md
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
git init -q && git add -A && git commit -q -m "Release $TAG: harness, evidence and manuscript build for 'What a Serving Layer Must See'" && git tag "$TAG"
echo "release tree at $TARGET ($(git ls-files | wc -l | tr -d ' ') files), tag $TAG"
