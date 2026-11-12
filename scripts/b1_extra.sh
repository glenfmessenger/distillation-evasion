#!/usr/bin/env bash
set -uo pipefail
source ~/harness.env; cd ~/distillation-evasion-harness
O=~/logs/b1_extra.log; log() { echo "$(date -Is) $*" >> $O; }
run() { local name="$1"; shift; log "$name: start"; "$@" > ~/logs/b1_$name.log 2>&1 && log "$name: ok" || log "FAILED: $name"; }
export CUDA_VISIBLE_DEVICES=0
C="pilot_baseline,c_real_v2:20,c_real_v2_s1"
run content_nm100_heavy .venv/bin/python scripts/m4_content.py --benign-label m3_v1 --campaigns $C --out-label v2_content_nm100_heavy --device cuda --n-match 100 --n-list 1 --benign-prompts-file $HARNESS_HOST_REPO/content_calibration/heavy_v1/users.jsonl
run content_ctrl .venv/bin/python scripts/m4_content.py --benign-label m3_v1 --campaigns $C --out-label v2_content_ctrl --device cuda --n-list 1 --control-files uniform_firstturns=$HARNESS_HOST_REPO/campaign_prompts/benign_ctrl_v2/prompts.jsonl
run content_ctrl_heavy .venv/bin/python scripts/m4_content.py --benign-label m3_v1 --campaigns $C --out-label v2_content_ctrl_heavy --device cuda --n-list 1 --benign-prompts-file $HARNESS_HOST_REPO/content_calibration/heavy_v1/users.jsonl --control-files uniform_firstturns=$HARNESS_HOST_REPO/campaign_prompts/benign_ctrl_v2/prompts.jsonl
log "B1_EXTRA_DONE"
