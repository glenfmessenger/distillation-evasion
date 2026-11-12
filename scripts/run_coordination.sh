#!/usr/bin/env bash
set -uo pipefail
source ~/harness.env; cd ~/distillation-evasion-harness
O=~/logs/run_coordination.log; log() { echo "$(date -Is) $*" >> $O; }
for spec in "pilot_baseline 0 v2_coord_c_bench" "c_real_v2 20 v2_coord_c_real" "c_real_v2_s1 0 v2_coord_c_real_s1" "c_instr_v2 0 v2_coord_c_instr"; do
  set -- $spec
  log "$3: start"
  .venv/bin/python scripts/m4_coordination.py --benign-label m3_v1 --campaign-label $1 --max-sessions $2 --out-label $3 > ~/logs/coord_$3.log 2>&1 && log "$3: ok" || log "FAILED: $3"
done
log "COORD_DONE"
