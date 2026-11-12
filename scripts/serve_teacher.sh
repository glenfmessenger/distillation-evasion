#!/usr/bin/env bash
# Launch the teacher in vLLM with the metric surface the protocol needs (PROTOCOL §5, PLAN M1.3).
# Flags: reasoning parser (reasoning_tokens in usage), prefix caching + prompt-token details
# (cached_tokens in usage). The exact command and the installed vLLM version are recorded in
# docs/environment.md at M1; do not change flags without logging a decision.
set -euo pipefail
source ~/harness.env
MODEL="${MODEL:-Qwen/Qwen3-8B}"
GPU="${1:-0}"          # replica = one GPU; usage: serve_teacher.sh <gpu_index> <port>
PORT="${2:-$((8000 + GPU))}"
export CUDA_VISIBLE_DEVICES="$GPU"
LOG="${HARNESS_HOST_REPO}/logs/vllm_serve_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$(dirname "$LOG")"
cd ~/distillation-evasion-harness
echo "launch: $(date -Is) gpu=$GPU port=$PORT vllm=$(.venv/bin/python -c 'import vllm;print(vllm.__version__)') model=$MODEL log=$LOG"
exec .venv/bin/vllm serve "$MODEL" \
  --port "$PORT" \
  --served-model-name "$MODEL" \
  --reasoning-parser qwen3 \
  --enable-prefix-caching \
  --enable-prompt-tokens-details \
  --max-model-len 16384 \
  --gpu-memory-utilization 0.90 \
  --dtype bfloat16 \
  --disable-log-requests \
  > "$LOG" 2>&1
