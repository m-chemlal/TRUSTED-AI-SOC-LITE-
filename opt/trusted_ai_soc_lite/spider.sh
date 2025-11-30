#!/usr/bin/env bash
set -euo pipefail

# Spider orchestrator: single-entry launcher for the Nmap -> IA/XAI -> response pipeline
# with an optional React dashboard helper.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_ALL="${PROJECT_ROOT}/run_all.sh"
DASHBOARD_DIR="${PROJECT_ROOT}/dashboard-react"
DASHBOARD_PORT="5173"
PROFILE="full"
MODE="scan"           # scan | scan+dashboard | dashboard
DRY_RUN=0
TARGET_REFRESH=1
EXTRA_NMAP_ARGS=""
AI_EXTRA_ARGS=""
RESPONDER_EXTRA_ARGS=""
TI_OFFLINE=0
START_TIME="$(date -Is)"

C_RESET="\033[0m"
C_BOLD="\033[1m"
C_CYAN="\033[96m"
C_MAGENTA="\033[95m"
C_YELLOW="\033[93m"
C_GREEN="\033[92m"
C_BLUE="\033[94m"
C_PURPLE="\033[38;5;135m"
C_TEAL="\033[38;5;45m"

usage() {
  cat <<'USAGE'
spider.sh - One-command launcher for TRUSTED AI SOC LITE

Usage:
  ./spider.sh [options]

Options:
  -p, --profile <fast|balanced|full|aggressive>  Choose scan preset (default: full)
  -m, --mode <scan|scan+dashboard|dashboard>      Select what to run (default: scan)
      --no-target-refresh                        Do not regenerate targets.txt
      --extra-nmap-args "..."                    Extra args forwarded to Nmap
      --ai-extra "..."                           Extra args forwarded to analyse_scan.py
      --responder-extra "..."                    Extra args forwarded to responder.py
      --ti-offline                               Force offline TI cache for AI
      --dashboard-port <port>                    Port for the React dashboard (default: 5173)
      --dry-run                                  Print the resolved actions without executing
      --help                                     Show this help

Examples:
  ./spider.sh --profile fast --dry-run
  ./spider.sh --mode scan+dashboard --profile balanced
USAGE
}

banner() {
  cat <<"EOF" | sed "s/<P>/${C_PURPLE}${C_BOLD}/g; s/<T>/${C_TEAL}${C_BOLD}/g; s/<B>/${C_BLUE}${C_BOLD}/g; s/<G>/${C_GREEN}${C_BOLD}/g; s/<C>/${C_CYAN}${C_BOLD}/g; s/<R>/${C_RESET}/g"
<P>███████<T>███████<B>███████<G>███████<R>
<P>██   ██<T>██   ██<B>██   ██<G>██   ██<R>   <C>TRUSTED AI SOC LITE</C>
<P>███████<T>███████<B>███████<G>███████<R>   <C>SPIDER LAUNCHER</C>
<P>██     <T>██     <B>██     <G>██     <R>
<P>██     <T>██     <B>██     <G>██     <R>
<T>┌──────────────────────────────────────────────────────────────┐<R>
<T>│<R>  <C>Scan → IA/XAI → Response</C>  <T>│<R>  <C>Autopilot · Single Command</C>  <T>│<R>
<T>└──────────────────────────────────────────────────────────────┘<R>
EOF

  printf "%bHello to TRUSTED AI SOC LITE — SPIDER mode engaged at %s%b\n" "${C_MAGENTA}${C_BOLD}" "${START_TIME}" "${C_RESET}"
  printf "%bMode:%b %s    %bProfile:%b %s\n" "${C_PURPLE}${C_BOLD}" "${C_RESET}" "${MODE}" "${C_YELLOW}${C_BOLD}" "${C_RESET}" "${PROFILE}"
  printf "%bUse --help for options. Stay lethal. 🕷️%b\n" "${C_TEAL}${C_BOLD}" "${C_RESET}"
}

launch_dashboard() {
  if [ ! -d "${DASHBOARD_DIR}" ]; then
    echo "[WARN] Tableau React introuvable (${DASHBOARD_DIR})." >&2
    return 1
  fi
  if ! command -v npm >/dev/null 2>&1; then
    echo "[WARN] npm est requis pour le dashboard React. Installez-le ou lancez le mode scan seul." >&2
    return 1
  fi

  local log_file="/tmp/trusted_ai_soc_dashboard.log"
  local need_install=0
  if [ ! -d "${DASHBOARD_DIR}/node_modules" ]; then
    need_install=1
  fi

  echo "[INFO] Préparation du dashboard React (port ${DASHBOARD_PORT})"
  if [ "${DRY_RUN}" = "1" ]; then
    if [ "${need_install}" = "1" ]; then
      echo "[DRY-RUN] (cd ${DASHBOARD_DIR} && npm install)"
    fi
    echo "[DRY-RUN] (cd ${DASHBOARD_DIR} && npm run dev -- --host 0.0.0.0 --port ${DASHBOARD_PORT})"
    return 0
  fi

  if [ "${need_install}" = "1" ]; then
    (cd "${DASHBOARD_DIR}" && npm install >/dev/null)
  fi

  # Run the dashboard in a background subshell so $! is defined even with "set -u".
  (
    cd "${DASHBOARD_DIR}" &&
    npm run dev -- --host 0.0.0.0 --port "${DASHBOARD_PORT}" >>"${log_file}" 2>&1
  ) &
  local dash_pid=$!
  echo "[OK] Dashboard démarré (PID ${dash_pid}) sur http://localhost:${DASHBOARD_PORT}";
  echo "[INFO] Logs: ${log_file}";
}

run_pipeline() {
  if [ ! -x "${RUN_ALL}" ]; then
    echo "[ERREUR] ${RUN_ALL} introuvable ou non exécutable" >&2
    exit 1
  fi

  local cmd=("${RUN_ALL}" "--profile" "${PROFILE}")
  if [ "${TARGET_REFRESH}" = "0" ]; then
    cmd+=("--no-target-refresh")
  fi
  if [ -n "${EXTRA_NMAP_ARGS}" ]; then
    cmd+=("--extra-nmap-args" "${EXTRA_NMAP_ARGS}")
  fi
  if [ -n "${AI_EXTRA_ARGS}" ]; then
    cmd+=("--ai-extra" "${AI_EXTRA_ARGS}")
  fi
  if [ -n "${RESPONDER_EXTRA_ARGS}" ]; then
    cmd+=("--responder-extra" "${RESPONDER_EXTRA_ARGS}")
  fi
  if [ "${TI_OFFLINE}" = "1" ]; then
    cmd+=("--ti-offline")
  fi
  if [ "${DRY_RUN}" = "1" ]; then
    cmd+=("--dry-run")
  fi

  echo "[INFO] Lancement du pipeline Nmap → IA/XAI → réponse"
  printf '[CMD]'; printf ' %q' "${cmd[@]}"; printf '\n'
  if [ "${DRY_RUN}" = "1" ]; then
    return 0
  fi

  "${cmd[@]}"
}

MODE_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--profile) PROFILE="$2"; shift 2;;
    -m|--mode) MODE="$2"; shift 2;;
    --no-target-refresh) TARGET_REFRESH=0; shift;;
    --extra-nmap-args) EXTRA_NMAP_ARGS="$2"; shift 2;;
    --ai-extra) AI_EXTRA_ARGS="$2"; shift 2;;
    --responder-extra) RESPONDER_EXTRA_ARGS="$2"; shift 2;;
    --ti-offline) TI_OFFLINE=1; shift;;
    --dashboard-port) DASHBOARD_PORT="$2"; shift 2;;
    --dry-run) DRY_RUN=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "[ERREUR] Option inconnue: $1" >&2; usage; exit 1;;
  esac
done

banner

case "${MODE}" in
  scan)
    run_pipeline
    ;;
  scan+dashboard)
    run_pipeline
    launch_dashboard
    ;;
  dashboard)
    launch_dashboard
    ;;
  *)
    echo "[ERREUR] Mode inconnu: ${MODE}" >&2
    usage
    exit 1
    ;;
esac

printf "%bSPIDER terminé.%b\n" "${C_MAGENTA}${C_BOLD}" "${C_RESET}"
