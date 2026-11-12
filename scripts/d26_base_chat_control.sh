#!/usr/bin/env bash
# Decision 35 / D-26: the untouched student (family chat template attached, weights untrained)
# scored on the full suite in chat mode. GPU 0. Usage: d26_base_chat_control.sh <seed>
set -uo pipefail
source ~/harness.env
SEED="$1"; cd ~/distillation-evasion-harness
BASE=$HARNESS_HOST_REPO/checkpoints/repair_only_s${SEED}/base; L=$HARNESS_HOST_REPO/logs
O=~/logs/d26_base_chat_s${SEED}.log
log() { echo "$(date -Is) $*" >> $O; }
[ -f "$BASE/base_manifest.json" ] || { log "FAILED: no base checkpoint"; exit 1; }
nohup bash scripts/serve_student.sh "$BASE" student-base-chat 8002 0 > $L/serve_student_launcher_base_chat.log 2>&1 &
for i in $(seq 1 120); do curl -sf -o /dev/null http://127.0.0.1:8002/health && break; sleep 5; done
curl -sf -o /dev/null http://127.0.0.1:8002/health || { log "FAILED: student server"; exit 1; }
log "scoring start"
.venv/bin/python scripts/score_suite.py --base-url http://127.0.0.1:8002 --model student-base-chat --mode chat \
    --label student_base_chat_s${SEED} --k 4 --concurrency 64 > ~/logs/score_base_chat_s${SEED}.log 2>&1
log "scoring exit $?"
for p in $(pgrep -f "served-model-name student-base-chat"); do kill $p 2>/dev/null; done
sleep 10
log "D26_DONE"
