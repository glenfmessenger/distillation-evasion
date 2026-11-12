#!/usr/bin/env bash
# Amendment A5 / decision 25: two exploratory SFT variants on the pilot pairs, MATH-500 only.
# Non-reportable. GPU 1. Waits for the pilot's remaining after-SFT scoring to release the GPU.
# Usage: d20_sft_variants.sh <seed>
set -uo pipefail
source ~/harness.env
SEED="$1"; cd ~/distillation-evasion-harness
CK=$HARNESS_HOST_REPO/checkpoints/d20_s${SEED}; L=$HARNESS_HOST_REPO/logs
PAIRS=$HARNESS_HOST_REPO/results/raw/campaign/pilot_baseline/pairs.jsonl
O=~/logs/d20_sft_variants_s${SEED}.log
log() { echo "$(date -Is) $*" >> $O; }
mkdir -p "$CK"
log "waiting for the pilot after-SFT scoring to finish"
while pgrep -f "overnight_reorder.sh" >/dev/null; do sleep 60; done
sleep 30
run() { # name, extra train flags...
  local V="$1"; shift
  log "$V: SFT start ($*)"
  CUDA_VISIBLE_DEVICES=1 .venv/bin/python scripts/train_sft.py --pairs "$PAIRS" --out "$CK/$V" --seed $SEED --regime full "$@" > $L/sft_d20_${V}_s${SEED}.log 2>&1
  log "$V: SFT exit $?"
  [ -f "$CK/$V/train_manifest.json" ] || { log "FAILED: $V SFT ended without a manifest"; return 1; }
  nohup bash scripts/serve_student.sh "$CK/$V" "student-d20-$V" 8003 1 > $L/serve_student_launcher_d20_$V.log 2>&1 &
  for i in $(seq 1 120); do curl -sf -o /dev/null http://127.0.0.1:8003/health && break; sleep 5; done
  curl -sf -o /dev/null http://127.0.0.1:8003/health || { log "FAILED: $V server"; return 1; }
  .venv/bin/python scripts/score_suite.py --base-url http://127.0.0.1:8003 --model "student-d20-$V" --mode chat \
      --label "explore_d20_${V}_s${SEED}" --suites math500 --k 4 --concurrency 64 > ~/logs/score_d20_${V}_s${SEED}.log 2>&1
  log "$V: scoring exit $? ; $(grep pass@1 ~/logs/score_d20_${V}_s${SEED}.log | tail -n 1)"
  for p in $(pgrep -f "served-model-name student-d20-$V"); do kill $p 2>/dev/null; done
  sleep 15
}
run short --max-gen-tokens 4096
run short_aw --max-gen-tokens 4096 --answer-only-copy
log "D20_DONE"
