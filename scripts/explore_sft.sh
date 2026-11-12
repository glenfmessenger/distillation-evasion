#!/usr/bin/env bash
# EXPLORATORY ONLY (FINDINGS F27, DECISIONS D-17): size an SFT-recipe amendment on pilot data.
# Outputs are labelled explore_* and are never reported. Usage: explore_sft.sh <tag> <lr> <eff_batch> <epochs> <gpu>
set -euo pipefail
source ~/harness.env
TAG="$1"; LR="$2"; EB="$3"; EP="$4"; GPU="$5"
export CUDA_VISIBLE_DEVICES="$GPU"
cd ~/distillation-evasion-harness
CK=$HARNESS_HOST_REPO/checkpoints/explore_$TAG
PAIRS=$HARNESS_HOST_REPO/results/raw/campaign/pilot_baseline/pairs.jsonl
.venv/bin/python scripts/train_sft.py --pairs "$PAIRS" --out "$CK" --seed 0 --regime full --lr "$LR" --effective-batch "$EB" --epochs "$EP" 2>&1 | tail -n 2
nohup bash scripts/serve_student.sh "$CK" "student-explore-$TAG" 8002 "$GPU" > $HARNESS_HOST_REPO/logs/serve_explore_$TAG.log 2>&1 &
for i in $(seq 1 90); do curl -sf -o /dev/null http://127.0.0.1:8002/health && break; sleep 5; done
.venv/bin/python scripts/score_suite.py --base-url http://127.0.0.1:8002 --model "student-explore-$TAG" --mode chat --label "explore_$TAG" --suites math500,gsm8k_test --k 2 --limit 100 --concurrency 64
for p in $(pgrep -f "served-model-name student-explore-$TAG"); do kill $p 2>/dev/null || true; done; sleep 8
echo "=== explore $TAG done ==="
