#!/usr/bin/env bash
# Serve a student checkpoint (HF id or local directory) in vLLM for scoring.
# Usage: serve_student.sh <model_path_or_id> <served_name> [port]
# The base checkpoint has no chat template; completion-mode scoring does not need one. SFT
# checkpoints carry the Qwen3 template saved by train_sft.py. Reasoning parser is set so the
# student's <think> spans are counted in usage like the teacher's.
set -euo pipefail
source ~/harness.env
MODEL="$1"; NAME="$2"; PORT="${3:-8002}"; GPU="${4:-0}"
export CUDA_VISIBLE_DEVICES="$GPU"
LOG="${HARNESS_HOST_REPO}/logs/vllm_student_$(date +%Y%m%d_%H%M%S).log"
cd ~/distillation-evasion-harness
echo "launch: $(date -Is) gpu=$GPU model=$MODEL served=$NAME port=$PORT log=$LOG"
exec .venv/bin/vllm serve "$MODEL" \
  --port "$PORT" \
  --served-model-name "$NAME" \
  --reasoning-parser qwen3 \
  --enable-prefix-caching \
  --enable-prompt-tokens-details \
  --max-model-len 16384 \
  --gpu-memory-utilization 0.85 \
  --dtype bfloat16 \
  --disable-log-requests \
  > "$LOG" 2>&1
