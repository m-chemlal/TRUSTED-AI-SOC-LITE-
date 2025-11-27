#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-}"
IP_ADDRESS="${2:-}"
LOG_FILE="${LOG_FILE:-/opt/trusted_ai_soc_lite/response_engine/actions.log}"

usage() {
  cat <<USAGE >&2
Usage: $0 <block|unblock> <ip>
Example: $0 block 192.168.1.50
USAGE
  exit 1
}

if [[ -z "${ACTION}" || -z "${IP_ADDRESS}" ]]; then
  usage
fi

mkdir -p "$(dirname "${LOG_FILE}")"
TIMESTAMP="$(date -Is)"

case "${ACTION}" in
  block)
    if ufw deny from "${IP_ADDRESS}" >/dev/null; then
      echo "${TIMESTAMP} - BLOCKED ${IP_ADDRESS}" | tee -a "${LOG_FILE}"
    else
      echo "${TIMESTAMP} - FAILED to block ${IP_ADDRESS}" | tee -a "${LOG_FILE}" >&2
    fi
    ;;
  unblock)
    if ufw delete deny from "${IP_ADDRESS}" >/dev/null; then
      echo "${TIMESTAMP} - UNBLOCKED ${IP_ADDRESS}" | tee -a "${LOG_FILE}"
    else
      echo "${TIMESTAMP} - FAILED to unblock ${IP_ADDRESS}" | tee -a "${LOG_FILE}" >&2
    fi
    ;;
  *)
    usage
    ;;
esac
