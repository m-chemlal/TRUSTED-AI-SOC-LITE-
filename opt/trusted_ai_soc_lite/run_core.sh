#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NMAP_RUNNER="${PROJECT_ROOT}/nmap_scanner/run_scan.sh"

SCAN_PROFILE="full"
AUTO_TARGET_DISCOVERY="${AUTO_TARGET_DISCOVERY:-1}"
TI_OFFLINE=0
EXTRA_NMAP_ARGS=""
AI_EXTRA_ARGS=""
RESPONDER_EXTRA_ARGS=""
RESPONSE_AUTORUN=1
AI_AUTORUN=1
DRY_RUN=0

usage() {
  cat <<'USAGE'
Usage: run_core.sh [options]

Run only the Nmap → AI → response pipeline (no dashboard, no Wazuh).

Options:
  -p, --profile <fast|balanced|full|aggressive>  Scan preset (default: full)
      --no-target-refresh                        Skip automatic target discovery
      --ti-offline                               Force offline TI cache
      --extra-nmap-args "..."                    Extra args passed to nmap
      --ai-extra "..."                           Extra args forwarded to analyse_scan.py
      --responder-extra "..."                    Extra args forwarded to responder.py
      --ai-off                                   Disable the AI step
      --response-off                             Disable the responder step
      --dry-run                                  Print the resolved command only
      --help                                     Show this help
USAGE
}

run_once() {
  if [ ! -x "${NMAP_RUNNER}" ]; then
    echo "[ERREUR] ${NMAP_RUNNER} introuvable ou non exécutable" >&2
    return 1
  fi

  if [ "${DRY_RUN}" = "0" ] && ! command -v nmap >/dev/null 2>&1; then
    echo "[ERREUR] nmap n'est pas installé. Installez-le via: sudo apt install nmap" >&2
    return 1
  fi

  local env_vars=(
    "AUTO_TARGET_DISCOVERY=${AUTO_TARGET_DISCOVERY}"
    "SCAN_PROFILE=${SCAN_PROFILE}"
    "AI_AUTORUN=${AI_AUTORUN}"
    "AI_TI_OFFLINE=${TI_OFFLINE}"
    "AI_EXTRA_ARGS=${AI_EXTRA_ARGS}"
    "RESPONSE_AUTORUN=${RESPONSE_AUTORUN}"
    "RESPONDER_EXTRA_ARGS=${RESPONDER_EXTRA_ARGS}"
    "EXTRA_NMAP_ARGS=${EXTRA_NMAP_ARGS}"
  )

  echo "[INFO] Pipeline coeur : Nmap → IA → réponse (profil ${SCAN_PROFILE})"
  if [ "${DRY_RUN}" = "1" ]; then
    printf '[DRY-RUN] env'
    for var in "${env_vars[@]}"; do printf ' %q' "$var"; done
    printf ' %q\n' "${NMAP_RUNNER}"
    return 0
  fi

  env "${env_vars[@]}" "${NMAP_RUNNER}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--profile) SCAN_PROFILE="$2"; shift 2;;
    --no-target-refresh) AUTO_TARGET_DISCOVERY=0; shift;;
    --ti-offline) TI_OFFLINE=1; shift;;
    --extra-nmap-args) EXTRA_NMAP_ARGS="$2"; shift 2;;
    --ai-extra) AI_EXTRA_ARGS="$2"; shift 2;;
    --responder-extra) RESPONDER_EXTRA_ARGS="$2"; shift 2;;
    --ai-off) AI_AUTORUN=0; shift;;
    --response-off) RESPONSE_AUTORUN=0; shift;;
    --dry-run) DRY_RUN=1; shift;;
    --help|-h) usage; exit 0;;
    *) echo "[ERREUR] Option inconnue: $1" >&2; usage; exit 1;;
  esac
done

run_once
