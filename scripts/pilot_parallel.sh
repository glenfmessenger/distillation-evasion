#!/usr/bin/env bash
# M2 pilot, two-GPU orchestration (PLAN M2 steps 5-6): after SFT, run GRPO repair on GPU 0 while
# the after-SFT checkpoint is scored on GPU 1; then score the repaired checkpoint on both GPUs.
# Each stage writes its own manifest/summary; any failure stops the script (set -e).
# Usage: pilot_parallel.sh <seed>
set -euo pipefail
source ~/harness.env
SEED="$1"; cd ~/distillation-evasion-harness
CK=$HARNESS_HOST_REPO/checkpoints/pilot_s${SEED}; L=$HARNESS_HOST_REPO/logs
while [ ! -f "$CK/sft/train_manifest.json" ]; do sleep 30; done
echo "$(date -Is) SFT checkpoint ready"
.venv/bin/python -c "import json; m=json.load(open('$HARNESS_HOST_REPO/results/raw/campaign/pilot_baseline/manifest.json')); open('$CK/sft_ids.txt','w').write('\n'.join(m['ids']))"
( CUDA_VISIBLE_DEVICES=0 .venv/bin/python scripts/train_grpo.py --model "$CK/sft" --out "$CK/repair" --seed $SEED --regime full --exclude-ids "$CK/sft_ids.txt" > $L/grpo_pilot_s${SEED}.log 2>&1; echo "GRPO_EXIT=$?" >> $L/grpo_pilot_s${SEED}.log ) &
GRPO_PID=$!
serve() { nohup bash scripts/serve_student.sh "$1" "$2" $((8002 + $3)) $3 > $L/serve_student_launcher_$3.log 2>&1 &
  for i in $(seq 1 90); do curl -sf -o /dev/null http://127.0.0.1:$((8002 + $3))/health && return 0; sleep 5; done; echo "server failed on gpu $3"; exit 1; }
stop() { for p in $(pgrep -f "served-model-name $1"); do kill $p 2>/dev/null || true; done; sleep 8; }
echo "$(date -Is) scoring after-SFT on GPU 1"
serve "$CK/sft" student-sft 1
.venv/bin/python scripts/score_suite.py --base-url http://127.0.0.1:8003 --model student-sft --mode chat --label student_after_sft_s${SEED} --k 4 --concurrency 64
stop student-sft
.venv/bin/python scripts/rescore.py student_after_sft_s${SEED} 2>&1 | grep -E "pass@1"
echo "$(date -Is) after-SFT scored; waiting for GRPO"
wait $GRPO_PID
grep -q "GRPO_EXIT=0" $L/grpo_pilot_s${SEED}.log || { echo "GRPO failed"; tail -n 30 $L/grpo_pilot_s${SEED}.log; exit 1; }
echo "$(date -Is) scoring after-repair on both GPUs"
serve "$CK/repair" student-repair 0; serve "$CK/repair" student-repair 1
.venv/bin/python scripts/score_suite.py --base-url http://127.0.0.1:8002,http://127.0.0.1:8003 --model student-repair --mode chat --label student_after_repair_s${SEED} --k 4 --concurrency 128
stop student-repair
.venv/bin/python scripts/rescore.py student_after_repair_s${SEED} 2>&1 | grep -E "pass@1"
echo "$(date -Is) === pilot parallel done (seed $SEED) ==="
