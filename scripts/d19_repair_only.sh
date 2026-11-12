#!/usr/bin/env bash
# Amendment A4 / decision 24: repair-only arm. Frozen repair on the untouched student (family chat
# template attached, weights untrained), then the full suite in chat mode. GPU 0.
# Usage: d19_repair_only.sh <seed>
set -uo pipefail
source ~/harness.env
SEED="$1"; cd ~/distillation-evasion-harness
CK=$HARNESS_HOST_REPO/checkpoints/repair_only_s${SEED}; L=$HARNESS_HOST_REPO/logs
PILOT=$HARNESS_HOST_REPO/checkpoints/pilot_s${SEED}
O=~/logs/d19_repair_only_s${SEED}.log
log() { echo "$(date -Is) $*" >> $O; }
mkdir -p "$CK"
[ -f "$PILOT/sft_ids.txt" ] || { log "FAILED: no pilot exclusion list"; exit 1; }
log "writing base checkpoint with chat template"
CUDA_VISIBLE_DEVICES=0 .venv/bin/python scripts/make_base_with_template.py --out "$CK/base" >> $O 2>&1 || { log "FAILED: base checkpoint"; exit 1; }
log "GRPO start"
CUDA_VISIBLE_DEVICES=0 .venv/bin/python scripts/train_grpo.py --model "$CK/base" --out "$CK/repair" --seed $SEED --regime full --exclude-ids "$PILOT/sft_ids.txt" > $L/grpo_repair_only_s${SEED}.log 2>&1
log "GRPO exit $?"
[ -f "$CK/repair/repair_manifest.json" ] || { log "FAILED: GRPO ended without a manifest"; exit 1; }
nohup bash scripts/serve_student.sh "$CK/repair" student-repair-only 8002 0 > $L/serve_student_launcher_repair_only.log 2>&1 &
for i in $(seq 1 120); do curl -sf -o /dev/null http://127.0.0.1:8002/health && break; sleep 5; done
curl -sf -o /dev/null http://127.0.0.1:8002/health || { log "FAILED: student server"; exit 1; }
.venv/bin/python scripts/score_suite.py --base-url http://127.0.0.1:8002 --model student-repair-only --mode chat \
    --label student_repair_only_s${SEED} --k 4 --concurrency 64 > ~/logs/score_repair_only_s${SEED}.log 2>&1
log "scoring exit $?"
for p in $(pgrep -f "served-model-name student-repair-only"); do kill $p 2>/dev/null; done
.venv/bin/python scripts/rescore.py student_repair_only_s${SEED} 2>&1 | grep -E "pass@1" >> $O
log "D19_DONE"
