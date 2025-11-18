#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NMAP_RUNNER="${PROJECT_ROOT}/nmap_scanner/run_scan.sh"
DASHBOARD_APP="${PROJECT_ROOT}/dashboard/app.py"
OPENVAS_LAUNCHER="${PROJECT_ROOT}/nmap_scanner/openvas_integration/launch_openvas_scan.py"

SCAN_PROFILE="full"
AUTO_TARGET_DISCOVERY="${AUTO_TARGET_DISCOVERY:-1}"
AI_AUTORUN="${AI_AUTORUN:-1}"
RESPONSE_AUTORUN="${RESPONSE_AUTORUN:-1}"
RUN_DASHBOARD=0
KEEP_DASHBOARD=0
DASHBOARD_PORT="${DASHBOARD_PORT:-8501}"
DASHBOARD_LOG="${PROJECT_ROOT}/dashboard/streamlit.log"
TI_OFFLINE=0
LOOP_INTERVAL=""
DRY_RUN=0
EXTRA_NMAP_ARGS=""
AI_EXTRA_ARGS=""
RESPONDER_EXTRA_ARGS=""
RUN_OPENVAS=0
OPENVAS_ARGS=""
START_TIME="$(date -Is)"

usage() {
  cat <<'USAGE'
Usage: run_all.sh [options]

This wrapper refreshes targets, launches the Nmap scanner (with AI + response automation),
and optionally starts the Streamlit dashboard or an OpenVAS task.

Options:
  -p, --profile <fast|balanced|full|aggressive>  Choose the scan preset (default: full)
      --no-target-refresh                        Skip automatic target discovery
      --ai-off                                   Disable automatic AI analysis
      --response-off                             Disable automatic response orchestration
      --ti-offline                               Force AI Threat Intelligence to offline mode
      --extra-nmap-args "..."                    Extra args passed to nmap (quoted string)
      --ai-extra "..."                           Extra args forwarded to analyse_scan.py
      --responder-extra "..."                    Extra args forwarded to responder.py
      --openvas                                  Trigger the OpenVAS helper before Nmap
      --openvas-args "..."                       Arguments for the OpenVAS helper
      --dashboard                                Launch the Streamlit dashboard (background)
      --keep-dashboard                           Keep dashboard running after the script exits
      --loop <seconds>                           Rerun the full pipeline every N seconds
      --dry-run                                  Print the resolved commands without executing
      --help                                     Display this message
USAGE
}

start_dashboard() {
  if [ ! -f "${DASHBOARD_APP}" ]; then
    echo "[AVERTISSEMENT] Dashboard introuvable (${DASHBOARD_APP})"
    return 1
  fi
  if ! command -v streamlit >/dev/null 2>&1; then
    echo "[AVERTISSEMENT] streamlit n'est pas installé (pip install -r dashboard/requirements.txt)"
    return 1
  fi
  mkdir -p "$(dirname "${DASHBOARD_LOG}")"
  echo "[INFO] Lancement du dashboard Streamlit (port ${DASHBOARD_PORT})"
  nohup streamlit run "${DASHBOARD_APP}" --server.port "${DASHBOARD_PORT}" --server.headless true > "${DASHBOARD_LOG}" 2>&1 &
  DASHBOARD_PID=$!
  echo "[OK] Dashboard démarré (PID ${DASHBOARD_PID}). Logs: ${DASHBOARD_LOG}"
}

stop_dashboard() {
  if [ -n "${DASHBOARD_PID:-}" ] && kill -0 "${DASHBOARD_PID}" 2>/dev/null; then
    echo "[INFO] Arrêt du dashboard (PID ${DASHBOARD_PID})"
    kill "${DASHBOARD_PID}"
  fi
}

run_openvas_helper() {
  if [ ! -f "${OPENVAS_LAUNCHER}" ]; then
    echo "[AVERTISSEMENT] Script OpenVAS introuvable (${OPENVAS_LAUNCHER})"
    return 1
  fi
  echo "[INFO] Déclenchement du scan OpenVAS"
  # shellcheck disable=SC2206
  local helper_args=(${OPENVAS_ARGS})
  if [ "${DRY_RUN}" = "1" ]; then
    echo "[DRY-RUN] python3 ${OPENVAS_LAUNCHER} ${helper_args[*]}"
    return 0
  fi
  python3 "${OPENVAS_LAUNCHER}" "${helper_args[@]}"
}

run_pipeline_once() {
  if [ "${RUN_OPENVAS}" = "1" ]; then
    run_openvas_helper
  fi

  if [ ! -x "${NMAP_RUNNER}" ]; then
    echo "[ERREUR] ${NMAP_RUNNER} est introuvable ou non exécutable" >&2
    return 1
  fi

  local env_vars=(
    "AUTO_TARGET_DISCOVERY=${AUTO_TARGET_DISCOVERY}"
    "SCAN_PROFILE=${SCAN_PROFILE}"
    "AI_AUTORUN=${AI_AUTORUN}"
    "RESPONSE_AUTORUN=${RESPONSE_AUTORUN}"
    "AI_TI_OFFLINE=${TI_OFFLINE}"
    "EXTRA_NMAP_ARGS=${EXTRA_NMAP_ARGS}"
    "AI_EXTRA_ARGS=${AI_EXTRA_ARGS}"
    "RESPONDER_EXTRA_ARGS=${RESPONDER_EXTRA_ARGS}"
  )

  echo "[INFO] === Démarrage du pipeline SOC (${SCAN_PROFILE}) à ${START_TIME} ==="
  if [ "${DRY_RUN}" = "1" ]; then
    printf '[DRY-RUN] env'
    for var in "${env_vars[@]}"; do
      printf ' %q' "$var"
    done
    printf ' %q\n' "${NMAP_RUNNER}"
    return 0
  fi

  env "${env_vars[@]}" "${NMAP_RUNNER}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--profile)
      SCAN_PROFILE="$2"; shift 2;;
    --no-target-refresh)
      AUTO_TARGET_DISCOVERY=0; shift;;
    --ai-off)
      AI_AUTORUN=0; shift;;
    --response-off)
      RESPONSE_AUTORUN=0; shift;;
    --ti-offline)
      TI_OFFLINE=1; shift;;
    --extra-nmap-args)
      EXTRA_NMAP_ARGS="$2"; shift 2;;
    --ai-extra)
      AI_EXTRA_ARGS="$2"; shift 2;;
    --responder-extra)
      RESPONDER_EXTRA_ARGS="$2"; shift 2;;
    --openvas)
      RUN_OPENVAS=1; shift;;
    --openvas-args)
      OPENVAS_ARGS="$2"; shift 2;;
    --dashboard)
      RUN_DASHBOARD=1; shift;;
    --keep-dashboard)
      KEEP_DASHBOARD=1; shift;;
    --loop)
      LOOP_INTERVAL="$2"; shift 2;;
    --dry-run)
      DRY_RUN=1; shift;;
    --help|-h)
      usage; exit 0;;
    *)
      echo "[ERREUR] Option inconnue: $1" >&2
      usage
      exit 1;;
  esac
done

if [ "${RUN_DASHBOARD}" = "1" ] && [ "${DRY_RUN}" = "0" ]; then
  start_dashboard || true
  if [ "${KEEP_DASHBOARD}" = "0" ]; then
    trap stop_dashboard EXIT
  fi
fi

run_pipeline_once

if [ -n "${LOOP_INTERVAL}" ]; then
  if ! [[ "${LOOP_INTERVAL}" =~ ^[0-9]+$ ]]; then
    echo "[ERREUR] --loop attend un entier (secondes)" >&2
    exit 1
  fi
  echo "[INFO] Boucle active toutes les ${LOOP_INTERVAL}s"
  while true; do
    sleep "${LOOP_INTERVAL}"
    START_TIME="$(date -Is)"
    run_pipeline_once
  done
fi

if [ "${RUN_DASHBOARD}" = "1" ] && [ "${KEEP_DASHBOARD}" = "1" ]; then
  echo "[INFO] Dashboard laissé actif. Arrêtez-le manuellement (PID ${DASHBOARD_PID:-"unknown"})."
fi

exit 0
