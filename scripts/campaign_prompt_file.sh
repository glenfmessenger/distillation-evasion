#!/usr/bin/env bash
# A campaign from a committed prompt file, issued as the pilot was (one identity, sessions of 100,
# 44 workers). Teacher on the given GPU, port 8001. Usage: campaign_prompt_file.sh <label> <prompt_file> <gpu>
set -uo pipefail
source ~/harness.env
cd ~/distillation-evasion-harness
LABEL="$1"; PF="$2"; GPU="${3:-1}"
O=~/logs/campaign_${LABEL}.log
log() { echo "$(date -Is) $*" >> $O; }
[ -f "$PF" ] || { log "FAILED: no prompt file $PF"; exit 1; }
if ! curl -sf -o /dev/null http://127.0.0.1:8001/health; then
  log "starting teacher on GPU $GPU"
  nohup bash scripts/serve_teacher.sh $GPU 8001 > ~/logs/serve_teacher_${LABEL}.log 2>&1 &
  for i in $(seq 1 180); do curl -sf -o /dev/null http://127.0.0.1:8001/health && break; sleep 5; done
fi
curl -sf -o /dev/null http://127.0.0.1:8001/health || { log "FAILED: teacher"; exit 1; }
log "campaign start"
.venv/bin/python scripts/run_campaign.py --base-url http://127.0.0.1:8001 --label "$LABEL" --prompt-file "$PF" \
  --identity campaign-0 --session-size 100 --concurrency 44 > ~/logs/run_campaign_${LABEL}.log 2>&1
log "campaign exit $? ; $(tail -n 1 ~/logs/run_campaign_${LABEL}.log | cut -c1-200)"
log "CAMPAIGN_DONE"
