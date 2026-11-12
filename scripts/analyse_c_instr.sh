#!/usr/bin/env bash
# Decision 38: C-instr campaign then the three levels and the content breadth on it.
set -uo pipefail
source ~/harness.env; cd ~/distillation-evasion-harness
O=~/logs/analyse_c_instr.log; log() { echo "$(date -Is) $*" >> $O; }
run() { local name="$1"; shift; log "$name: start"; "$@" > ~/logs/ci_$name.log 2>&1 && log "$name: ok" || log "FAILED: $name"; }
bash scripts/campaign_prompt_file.sh c_instr_v2 $HARNESS_HOST_REPO/campaign_prompts/c_instr_v2/prompts.jsonl 1
grep -q "campaign exit 0" ~/logs/campaign_c_instr_v2.log || { log "FAILED: campaign"; exit 1; }
for p in $(pgrep -f "\-\-port 8001"); do kill $p 2>/dev/null; done
run m3 .venv/bin/python scripts/m3_analyse.py --benign-label m3_v1 --campaign-label c_instr_v2 --out-label v2_c_instr
run levers .venv/bin/python scripts/m4_levers.py --benign-label m3_v1 --campaign-label c_instr_v2 --out-label v2_c_instr_levers
export CUDA_VISIBLE_DEVICES=0
C="pilot_baseline,c_real_v2:20,c_real_v2_s1,c_instr_v2"
run content .venv/bin/python scripts/m4_content.py --benign-label m3_v1 --campaigns $C --out-label v2_content_instr --device cuda --control-files uniform_firstturns=$HARNESS_HOST_REPO/campaign_prompts/benign_ctrl_v2/prompts.jsonl
run content_heavy .venv/bin/python scripts/m4_content.py --benign-label m3_v1 --campaigns $C --out-label v2_content_instr_heavy --device cuda --n-list 1 --benign-prompts-file $HARNESS_HOST_REPO/content_calibration/heavy_v1/users.jsonl
run r3 .venv/bin/python scripts/m4_content_r3batch.py --benign-label m3_v1 --campaigns pilot_baseline,c_real_v2,c_instr_v2 --content-label v2_content_instr --out-label v2_r3batch_instr --first-turns-only --fractions 0.01,0.02,0.05,0.1,0.25,0.5 --windows 20 --reference-repeats 10 --device cuda --control-files uniform_firstturns=$HARNESS_HOST_REPO/campaign_prompts/benign_ctrl_v2/prompts.jsonl
run ladder .venv/bin/python scripts/m4_ladder.py --out $HARNESS_HOST_REPO/results/aggregates/m4/ladder.md --content-label v2_content_instr --campaign "C-bench=m3_v1_pilot,v2_c_bench_levers,pilot_baseline" --campaign "C-real seed 0=v2_c_real,v2_c_real_levers,c_real_v2:20" --campaign "C-real seed 1=v2_c_real_s1,v2_c_real_s1_levers,c_real_v2_s1" --campaign "C-instr=v2_c_instr,v2_c_instr_levers,c_instr_v2"
log "C_INSTR_DONE"
