#!/usr/bin/env bash
# Delegated reprioritisation (DECISIONS 21): after the after-SFT MATH-500 pass completes, pause the
# remaining after-SFT suites so GPU 1 can run the benign replay first; resume them (score_suite
# resumes from its own outputs) when the replay is done. Node-side; no remote session needed.
set -uo pipefail
source ~/harness.env; cd ~/distillation-evasion-harness
P=~/logs/pilot_parallel_s0.log; O=~/logs/overnight_m3.log; CK=$HARNESS_HOST_REPO/checkpoints/pilot_s0
log() { echo "$(date -Is) $*"; }
while ! grep -q "^math500: pass@1" $P; do sleep 30; done
log "after-SFT math500 complete: $(grep '^math500: pass@1' $P | cut -c1-110)"
for p in $(pgrep -f "bash scripts/pilot_parallel.sh"); do kill $p 2>/dev/null; done
for p in $(pgrep -f "label student_after_sft_s0"); do kill $p 2>/dev/null; done
log "paused remaining after-SFT suites; overnight chain takes GPU 1 for the replay"
while ! grep -q "TRACK_A_DONE" $O; do sleep 60; done
sleep 20
log "replay done; resuming after-SFT suites on GPU 1"
nohup bash scripts/serve_student.sh "$CK/sft" student-sft 8003 1 > $HARNESS_HOST_REPO/logs/serve_student_launcher_sft_resume.log 2>&1 &
for i in $(seq 1 120); do curl -sf -o /dev/null http://127.0.0.1:8003/health && break; sleep 5; done
.venv/bin/python scripts/score_suite.py --base-url http://127.0.0.1:8003 --model student-sft --mode chat \
    --label student_after_sft_s0 --suites humaneval,mbpp_test,gsm8k_test --k 4 --concurrency 64 > ~/logs/score_after_sft_resume.log 2>&1
log "after-SFT resume exit $?"
for p in $(pgrep -f "served-model-name student-sft"); do kill $p 2>/dev/null; done
.venv/bin/python scripts/rescore.py student_after_sft_s0 2>&1 | grep -E "pass@1"
log "REORDER_DONE"
