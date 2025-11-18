#!/bin/bash
# Active response example for TRUSTED AI SOC LITE
# Usage: trusted_ai_block.sh <src_ip>

IP="$1"
LOG_FILE="/opt/trusted_ai_soc_lite/response_engine/actions.log"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

if [ -z "$IP" ]; then
  echo "[trusted_ai_block] No IP provided" >&2
  exit 1
fi

/usr/sbin/ufw deny from "$IP" > /dev/null 2>&1 || true
mkdir -p "$(dirname "$LOG_FILE")"
printf '{"timestamp":"%s","action":"block","ip":"%s","source":"wazuh_active_response"}\n' "$TIMESTAMP" "$IP" >> "$LOG_FILE"

exit 0
