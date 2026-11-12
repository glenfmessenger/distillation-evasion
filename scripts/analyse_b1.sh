#!/usr/bin/env bash
# Amendment B1 chain: heavy-user content calibration and C-instr prompt file (no teacher calls),
# then, after the seed-1 campaign finishes, the three levels on it and the content-level breadth
# runs (heavy-user calibration, second embedding model, matched-n and block sensitivity, share curve).
set -uo pipefail
source ~/harness.env
cd ~/distillation-evasion-harness
O=~/logs/analyse_b1.log
log() { echo "$(date -Is) $*" >> $O; }
run() { local name="$1"; shift; log "$name: start"; "$@" > ~/logs/b1_$name.log 2>&1 && log "$name: ok" || log "FAILED: $name"; }
run calib .venv/bin/python scripts/build_content_calibration.py --label heavy_v1 --exclude-labels c_real_v2,c_real_v2_s1
run instr .venv/bin/python scripts/build_instr_prompts.py --benign-label m3_v1 --label c_instr_v2 --n 2000 --seed 0
log "waiting for the seed-1 campaign"
while ! grep -q CAMPAIGN_DONE ~/logs/campaign_c_real_v2_s1.log 2>/dev/null; do sleep 60; done
grep -q "campaign exit 0" ~/logs/campaign_c_real_v2_s1.log || { log "FAILED: seed-1 campaign"; exit 1; }
run m3_s1 .venv/bin/python scripts/m3_analyse.py --benign-label m3_v1 --campaign-label c_real_v2_s1 --out-label v2_c_real_s1
run levers_s1 .venv/bin/python scripts/m4_levers.py --benign-label m3_v1 --campaign-label c_real_v2_s1 --out-label v2_c_real_s1_levers
C="pilot_baseline,c_real_v2:20,c_real_v2,c_real_v2_s1"
export CUDA_VISIBLE_DEVICES=0
run content_s1 .venv/bin/python scripts/m4_content.py --benign-label m3_v1 --campaigns $C --out-label v2_content_s1 --device cuda
run content_heavy .venv/bin/python scripts/m4_content.py --benign-label m3_v1 --campaigns $C --out-label v2_content_heavy --device cuda --benign-prompts-file $HARNESS_HOST_REPO/content_calibration/heavy_v1/users.jsonl
run content_bgebase .venv/bin/python scripts/m4_content.py --benign-label m3_v1 --campaigns $C --out-label v2_content_bgebase --device cuda --model BAAI/bge-base-en-v1.5
for nm in 10 100; do run content_nm$nm .venv/bin/python scripts/m4_content.py --benign-label m3_v1 --campaigns $C --out-label v2_content_nm$nm --device cuda --n-match $nm --n-list 1; done
for bl in 50 500; do run content_b$bl .venv/bin/python scripts/m4_content.py --benign-label m3_v1 --campaigns $C --out-label v2_content_b$bl --device cuda --block $bl --n-list 1; done
run r3share .venv/bin/python scripts/m4_content_r3batch.py --benign-label m3_v1 --campaigns pilot_baseline,c_real_v2,c_real_v2_s1 --content-label v2_content_s1 --out-label v2_r3batch_share --first-turns-only --fractions 0.01,0.02,0.05,0.1,0.25,0.5 --windows 20 --reference-repeats 10
log "B1_DONE"
