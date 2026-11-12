#!/usr/bin/env bash
# PROTOCOL v2.0: after the C-real campaign finishes, the three levels on C-real (first 20 sessions)
# and on the full 8,000-request run, plus the C-bench content table in the same calibration.
set -uo pipefail
source ~/harness.env
cd ~/distillation-evasion-harness
O=~/logs/analyse_c_real.log
log() { echo "$(date -Is) $*" >> $O; }
log "waiting for the campaign"
while [ "$(grep -c CAMPAIGN_DONE ~/logs/campaign_c_real_v2.log)" -lt 2 ]; do sleep 60; done
grep -q "campaign exit 0" <(tail -n 3 ~/logs/campaign_c_real_v2.log) || { log "FAILED: campaign did not exit 0"; exit 1; }
git pull -q --ff-only 2>&1 | tail -1
for spec in "20 v2_c_real" "0 v2_c_real_8k"; do
  set -- $spec
  log "m3_analyse sessions=$1 -> $2"
  .venv/bin/python scripts/m3_analyse.py --benign-label m3_v1 --campaign-label c_real_v2 --out-label $2 --max-sessions $1 > ~/logs/m3_analyse_$2.log 2>&1 || log "FAILED: m3_analyse $2"
  log "m4_levers sessions=$1 -> $2"
  .venv/bin/python scripts/m4_levers.py --benign-label m3_v1 --campaign-label c_real_v2 --out-label ${2}_levers --max-sessions $1 > ~/logs/m4_levers_$2.log 2>&1 || log "FAILED: m4_levers $2"
done
log "m4_content"
CUDA_VISIBLE_DEVICES=0 .venv/bin/python scripts/m4_content.py --benign-label m3_v1 --campaigns pilot_baseline,c_real_v2:20,c_real_v2 --out-label v2_content_all --device cuda > ~/logs/m4_content_all.log 2>&1 || log "FAILED: m4_content"
log "ANALYSIS_DONE"
