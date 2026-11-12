#!/usr/bin/env bash
# Node-side chain for the delegated overnight window (DECISIONS 19, 20). Does not depend on any
# remote session. Track A (GPU 1): teacher replica -> benign replay. Track B (GPU 0): when GRPO
# finishes, serve the repaired student and score it. Uses only this node.
set -uo pipefail
source ~/harness.env; cd ~/distillation-evasion-harness
L=$HARNESS_HOST_REPO/logs; P=~/logs/pilot_parallel_s0.log; CK=$HARNESS_HOST_REPO/checkpoints/pilot_s0
log() { echo "$(date -Is) $*"; }
log "waiting for the after-SFT stage of the pilot orchestrator"
while ! grep -q "after-SFT scored" $P && pgrep -f "bash scripts/pilot_parallel.sh" >/dev/null; do sleep 60; done
grep -q "after-SFT scored" $P && log "after-SFT scored" || log "WARNING: orchestrator ended without after-SFT scores"
for p in $(pgrep -f "bash scripts/pilot_parallel.sh"); do kill $p 2>/dev/null; done   # GRPO python keeps running
for p in $(pgrep -f "served-model-name student-sft"); do kill $p 2>/dev/null; done; sleep 15

track_a() {
  log "A: starting teacher replica on GPU 1"
  nohup bash scripts/serve_teacher.sh 1 8001 > $L/serve_launcher_gpu1_m3.log 2>&1 &
  for i in $(seq 1 120); do curl -sf -o /dev/null http://127.0.0.1:8001/health && break; sleep 5; done
  curl -sf -o /dev/null http://127.0.0.1:8001/health || { log "A: TEACHER FAILED TO START"; return 1; }
  log "A: replay start"
  .venv/bin/python scripts/run_replay.py --schedule $HARNESS_HOST_REPO/benign/m3_v1/replay_schedule.jsonl \
      --label m3_v1 --base-url http://127.0.0.1:8001 --concurrency 80 > ~/logs/replay_m3_v1.log 2>&1
  log "A: replay exit $? ; $(tail -n 1 ~/logs/replay_m3_v1.log | cut -c1-300)"
  for p in $(pgrep -f "\-\-port 8001"); do kill $p 2>/dev/null; done
  log "TRACK_A_DONE"
}
track_b() {
  log "B: waiting for GRPO"
  while [ ! -f "$CK/repair/repair_manifest.json" ] && pgrep -f "train_grpo.py" >/dev/null; do sleep 60; done
  [ -f "$CK/repair/repair_manifest.json" ] || { log "B: GRPO ENDED WITHOUT A MANIFEST"; tail -n 20 $L/grpo_pilot_s0.log | cut -c1-300; return 1; }
  sleep 20
  log "B: serving repaired student on GPU 0"
  nohup bash scripts/serve_student.sh "$CK/repair" student-repair 8002 0 > $L/serve_student_launcher_repair.log 2>&1 &
  for i in $(seq 1 120); do curl -sf -o /dev/null http://127.0.0.1:8002/health && break; sleep 5; done
  curl -sf -o /dev/null http://127.0.0.1:8002/health || { log "B: STUDENT SERVER FAILED"; return 1; }
  .venv/bin/python scripts/score_suite.py --base-url http://127.0.0.1:8002 --model student-repair --mode chat \
      --label student_after_repair_s0 --k 4 --concurrency 64 > ~/logs/score_after_repair_s0.log 2>&1
  log "B: scoring exit $?"
  for p in $(pgrep -f "served-model-name student-repair"); do kill $p 2>/dev/null; done
  .venv/bin/python scripts/rescore.py student_after_repair_s0 2>&1 | grep -E "pass@1"
  log "TRACK_B_DONE"
}
track_a & A=$!
track_b & B=$!
wait $A; wait $B
log "=== overnight chain finished ==="
