#!/usr/bin/env bash
# M2 pilot, student side (PLAN M2 steps 2, 4, 5, 6, 7). Run on the VM AFTER the teacher jobs
# finish and the teacher server is stopped. Every stage writes its own manifest; a stage that
# fails stops the pipeline (set -e); nothing is retried silently.
#
# Usage: pilot_student_pipeline.sh <pairs.jsonl> <seed> <sft_regime: full|lora> [gpu_index=0]
# Runs entirely on one GPU (serving on port 8002); the other GPU may keep serving the teacher.
set -euo pipefail
source ~/harness.env
PAIRS="$1"; SEED="$2"; REGIME="$3"; GPU="${4:-0}"
export CUDA_VISIBLE_DEVICES="$GPU"
cd ~/distillation-evasion-harness
CK=$HARNESS_HOST_REPO/checkpoints/pilot_s${SEED}; mkdir -p "$CK"
SCORE_GPUS="${SCORE_GPUS:-$GPU}"   # GPUs used for scoring replicas, e.g. "0 1"
URL=$(for g in $SCORE_GPUS; do printf "http://127.0.0.1:%d," $((8002 + g)); done | sed "s/,$//")

serve() {  # serve <model> <name>: one replica per scoring GPU; waits for health on all
  for g in $SCORE_GPUS; do
    nohup bash scripts/serve_student.sh "$1" "$2" $((8002 + g)) $g > $HARNESS_HOST_REPO/logs/serve_student_launcher_$g.log 2>&1 &
  done
  for g in $SCORE_GPUS; do
    ok=0; for i in $(seq 1 90); do curl -sf -o /dev/null http://127.0.0.1:$((8002 + g))/health && { ok=1; break; }; sleep 5; done
    [ $ok = 1 ] || { echo "student server failed to start on gpu $g"; tail -n 20 $(ls -t $HARNESS_HOST_REPO/logs/vllm_student_*.log | head -1); exit 1; }
  done
}
stop_serve() { PAT="served-model-name student-"; for p in $(pgrep -f "$PAT"); do kill $p 2>/dev/null || true; done; sleep 8; }
score() { .venv/bin/python scripts/score_suite.py --base-url $URL --model "$1" --mode "$2" --label "$3" --k 4 --concurrency 96; }

for g in $GPU $SCORE_GPUS; do if [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $g)" -gt 2000 ]; then echo "GPU $g is busy; free it first"; exit 1; fi; done

echo "=== step 2b: student-before (completion mode) ==="
serve Qwen/Qwen3-1.7B-Base student-before
score student-before completion student_before_s${SEED}
stop_serve

echo "=== step 4: SFT ($REGIME, seed $SEED) ==="
if [ -f "$CK/sft/train_manifest.json" ]; then echo "SFT checkpoint present (train_manifest.json); not retraining"; else
  .venv/bin/python scripts/train_sft.py --pairs "$PAIRS" --out "$CK/sft" --seed $SEED --regime $REGIME 2>&1 | tail -n 5
fi
echo "=== step 6a: after-SFT ==="
serve "$CK/sft" student-sft
score student-sft chat student_after_sft_s${SEED}
stop_serve

echo "=== step 5: GRPO repair ==="
.venv/bin/python - <<PY
import json; m=json.load(open("$PAIRS".replace("pairs.jsonl","manifest.json"))); open("$CK/sft_ids.txt","w").write("\n".join(m["ids"]))
PY
.venv/bin/python scripts/train_grpo.py --model "$CK/sft" --out "$CK/repair" --seed $SEED --regime $REGIME --exclude-ids "$CK/sft_ids.txt" > $HARNESS_HOST_REPO/logs/grpo_pilot_s${SEED}.log 2>&1 || { tail -n 30 $HARNESS_HOST_REPO/logs/grpo_pilot_s${SEED}.log; exit 1; }
tail -n 2 $HARNESS_HOST_REPO/logs/grpo_pilot_s${SEED}.log | cut -c1-400
echo "=== step 6b: after-repair ==="
serve "$CK/repair" student-repair
score student-repair chat student_after_repair_s${SEED}
stop_serve
echo "=== pilot student pipeline done (seed $SEED) ==="
