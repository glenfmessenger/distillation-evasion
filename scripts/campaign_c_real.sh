#!/usr/bin/env bash
# PROTOCOL v2.0 §3: the C-real campaign, 8,000 held-out ordinary prompts, one identity, sessions of
# 100, issued as the pilot was (44 workers). Teacher on GPU 1 port 8001. Usage: campaign_c_real.sh
set -uo pipefail
source ~/harness.env
cd ~/distillation-evasion-harness
O=~/logs/campaign_c_real_v2.log
log() { echo "$(date -Is) $*" >> $O; }
log "starting teacher on GPU 1"
nohup bash scripts/serve_teacher.sh 1 8001 > ~/logs/serve_teacher_c_real.log 2>&1 &
for i in $(seq 1 180); do curl -sf -o /dev/null http://127.0.0.1:8001/health && break; sleep 5; done
curl -sf -o /dev/null http://127.0.0.1:8001/health || { log "FAILED: teacher"; exit 1; }
log "campaign start"
.venv/bin/python scripts/run_campaign.py --base-url http://127.0.0.1:8001 --label c_real_v2 \
  --prompt-file $HARNESS_HOST_REPO/campaign_prompts/c_real_v2/prompts.jsonl \
  --identity campaign-0 --session-size 100 --concurrency 44 > ~/logs/run_campaign_c_real_v2.log 2>&1
log "campaign exit $? ; $(tail -n 1 ~/logs/run_campaign_c_real_v2.log | cut -c1-200)"
for p in $(pgrep -f "\-\-port 8001"); do kill $p 2>/dev/null; done
log "CAMPAIGN_DONE"
