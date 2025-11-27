#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGETS_FILE="${SCRIPT_DIR}/targets.txt"
REPORT_DIR="${SCRIPT_DIR}/reports"
TIMESTAMP="$(date +%F_%H%M%S)"
XML_REPORT="${REPORT_DIR}/full_soc_scan_${TIMESTAMP}.xml"
AUTO_TARGET_DISCOVERY="${AUTO_TARGET_DISCOVERY:-1}"
SCAN_PROFILE="${SCAN_PROFILE:-full}"
PROFILES_DIR="${PROFILES_DIR:-${SCRIPT_DIR}/profiles.d}"
PROFILE_FILE="${PROFILES_DIR}/${SCAN_PROFILE}.env"
EXTRA_NMAP_ARGS="${EXTRA_NMAP_ARGS:-}"
AI_AUTORUN="${AI_AUTORUN:-1}"
AI_ENGINE_DIR="${AI_ENGINE_DIR:-${PROJECT_ROOT}/ai_engine}"
AI_MODEL_PATH="${AI_MODEL_PATH:-${AI_ENGINE_DIR}/models/model.pkl}"
AI_LOG_FILE="${AI_LOG_FILE:-${AI_ENGINE_DIR}/logs/ia_events.log}"
AI_WAZUH_LOG="${AI_WAZUH_LOG:-/var/log/trusted_ai_soc_lite.log}"
AI_AUDIT_FILE="${AI_AUDIT_FILE:-${PROJECT_ROOT}/audit/ia_decisions.json}"
AI_SCAN_HISTORY="${AI_SCAN_HISTORY:-${PROJECT_ROOT}/audit/scan_history.json}"
TI_CACHE_FILE="${TI_CACHE_FILE:-${AI_ENGINE_DIR}/logs/ti_cache.json}"
AI_DISABLE_SHAP="${AI_DISABLE_SHAP:-0}"
AI_DISABLE_LIME="${AI_DISABLE_LIME:-0}"
AI_TI_OFFLINE="${AI_TI_OFFLINE:-0}"
AI_EXTRA_ARGS="${AI_EXTRA_ARGS:-}"
RESPONSE_AUTORUN="${RESPONSE_AUTORUN:-0}"
RESPONSE_ENGINE_DIR="${RESPONSE_ENGINE_DIR:-${PROJECT_ROOT}/response_engine}"
RESPONDER_SCRIPT="${RESPONDER_SCRIPT:-${RESPONSE_ENGINE_DIR}/responder.py}"
RESPONSE_ACTIONS_LOG="${RESPONSE_ACTIONS_LOG:-${RESPONSE_ENGINE_DIR}/actions.log}"
RESPONSE_AUDIT_FILE="${RESPONSE_AUDIT_FILE:-${PROJECT_ROOT}/audit/response_actions.json}"
RESPONDER_STATE_FILE="${RESPONDER_STATE_FILE:-${RESPONSE_ENGINE_DIR}/.responder_state.json}"
RESPONDER_EXTRA_ARGS="${RESPONDER_EXTRA_ARGS:-}"
RESPONDER_DISABLE_EMAIL="${RESPONDER_DISABLE_EMAIL:-0}"
RESPONDER_DISABLE_UFW="${RESPONDER_DISABLE_UFW:-0}"
RESPONDER_DRY_RUN="${RESPONDER_DRY_RUN:-0}"
RESPONSE_ALERT_EMAIL="${RESPONSE_ALERT_EMAIL:-${SOC_ALERT_EMAIL:-}}"

if [ -f "${PROFILE_FILE}" ]; then
  echo "[INFO] Chargement du preset ${PROFILE_FILE}"
  # shellcheck disable=SC1090
  set -a
  source "${PROFILE_FILE}"
  set +a
  SCAN_PROFILE="${SCAN_PROFILE}"
else
  if [ -n "${PROFILES_DIR}" ] && [ -d "${PROFILES_DIR}" ]; then
    echo "[INFO] Aucun preset trouvé pour ${SCAN_PROFILE} (dossier: ${PROFILES_DIR})"
  fi
fi

if ! command -v nmap >/dev/null 2>&1; then
  echo "[ERREUR] nmap n'est pas installé.\nInstallez-le via: sudo apt install nmap" >&2
  exit 1
fi

if [ "${AUTO_TARGET_DISCOVERY}" = "1" ]; then
  echo "[INFO] Mise à jour automatique de ${TARGETS_FILE}"
  python3 "${SCRIPT_DIR}/generate_targets.py" --output "${TARGETS_FILE}" --force --quiet
else
  echo "[INFO] AUTO_TARGET_DISCOVERY=0 → utilisation du fichier ${TARGETS_FILE} tel quel"
fi

if [ ! -s "${TARGETS_FILE}" ]; then
  echo "[ERREUR] ${TARGETS_FILE} est introuvable ou vide. Exécutez generate_targets.py ou remplissez-le manuellement." >&2
  exit 1
fi

mkdir -p "${REPORT_DIR}"

declare -a NMAP_ARGS
case "${SCAN_PROFILE}" in
  fast)
    PROFILE_NAME="FAST"
    PROFILE_DESC="focus sur les 200 ports principaux avec scripts sûrs"
    NMAP_ARGS=(
      -sV
      -T4
      --top-ports "${FAST_TOP_PORTS:-200}"
      --script "default,vuln,safe"
      --script-timeout "${FAST_SCRIPT_TIMEOUT:-10s}"
      --max-retries "${FAST_MAX_RETRIES:-1}"
      --host-timeout "${FAST_HOST_TIMEOUT:-45s}"
    )
    ;;
  balanced)
    PROFILE_NAME="BALANCED"
    PROFILE_DESC="découverte complète sur les 1024 premiers ports + scripts auth/malware"
    NMAP_ARGS=(
      -sV
      -sC
      -O
      -T4
      -p "${BALANCED_PORT_RANGE:-1-1024}"
      --script "default,vuln,auth,malware,safe"
      --script-timeout "${BALANCED_SCRIPT_TIMEOUT:-15s}"
      --max-retries "${BALANCED_MAX_RETRIES:-2}"
      --host-timeout "${BALANCED_HOST_TIMEOUT:-2m}"
    )
    ;;
  full|FULL|Full)
    PROFILE_NAME="FULL_SOC"
    PROFILE_DESC="scan complet stabilisé (scripts vuln/auth/malware + garde-fous)"
    FULL_SCRIPT_SETS="${FULL_SCRIPT_SETS:-default,vuln,auth,malware,safe}"
    if [ "${FULL_INCLUDE_AGGRESSIVE:-0}" = "1" ]; then
      FULL_SCRIPT_SETS="${FULL_SCRIPT_SETS},exploit,brute"
    fi
    NMAP_ARGS=(
      -sV
      -sC
      -O
      --osscan-guess
      -T4
      -p "${FULL_PORT_RANGE:-1-1024}"
      --script "${FULL_SCRIPT_SETS}"
      --script-timeout "${FULL_SCRIPT_TIMEOUT:-20s}"
      --max-retries "${FULL_MAX_RETRIES:-2}"
      --host-timeout "${FULL_HOST_TIMEOUT:-3m}"
    )
    if [ "${FULL_INCLUDE_AGGRESSIVE:-0}" = "1" ]; then
      NMAP_ARGS+=(--script-args=unsafe=1)
    fi
    ;;
  aggressive)
    PROFILE_NAME="AGGRESSIVE_LAB"
    PROFILE_DESC="tous les ports + scripts exploit/brute (réservé aux labos)"
    AGG_SCRIPT_SET="${AGGRESSIVE_SCRIPT_SETS:-default,vuln,auth,malware,exploit,brute}"
    NMAP_ARGS=(
      -sV
      -sC
      -O
      --osscan-guess
      -T4
      -p "${AGGRESSIVE_PORT_RANGE:-1-65535}"
      --script "${AGG_SCRIPT_SET}"
      --script-timeout "${AGGRESSIVE_SCRIPT_TIMEOUT:-45s}"
      --max-retries "${AGGRESSIVE_MAX_RETRIES:-1}"
      --host-timeout "${AGGRESSIVE_HOST_TIMEOUT:-10m}"
    )
    if [ "${AGGRESSIVE_INCLUDE_UNSAFE:-1}" = "1" ]; then
      NMAP_ARGS+=(--script-args=unsafe=1)
    fi
    ;;
  *)
    echo "[AVERTISSEMENT] SCAN_PROFILE=${SCAN_PROFILE} non reconnu → utilisation du profil FULL_SOC" >&2
    PROFILE_NAME="FULL_SOC"
    PROFILE_DESC="scan complet stabilisé (scripts vuln/auth/malware + garde-fous)"
    FULL_SCRIPT_SETS="${FULL_SCRIPT_SETS:-default,vuln,auth,malware,safe}"
    if [ "${FULL_INCLUDE_AGGRESSIVE:-0}" = "1" ]; then
      FULL_SCRIPT_SETS="${FULL_SCRIPT_SETS},exploit,brute"
    fi
    NMAP_ARGS=(
      -sV
      -sC
      -O
      --osscan-guess
      -T4
      -p "${FULL_PORT_RANGE:-1-1024}"
      --script "${FULL_SCRIPT_SETS}"
      --script-timeout "${FULL_SCRIPT_TIMEOUT:-20s}"
      --max-retries "${FULL_MAX_RETRIES:-2}"
      --host-timeout "${FULL_HOST_TIMEOUT:-3m}"
    )
    if [ "${FULL_INCLUDE_AGGRESSIVE:-0}" = "1" ]; then
      NMAP_ARGS+=(--script-args=unsafe=1)
    fi
    ;;
esac

if [ -n "${EXTRA_NMAP_ARGS}" ]; then
  # shellcheck disable=SC2206
  EXTRA_ARGS_ARRAY=(${EXTRA_NMAP_ARGS})
  NMAP_ARGS+=("${EXTRA_ARGS_ARRAY[@]}")
fi

echo "[INFO] Profil ${PROFILE_NAME} → ${PROFILE_DESC}"
echo "[INFO] Lancement du scan Nmap avancé (${TARGETS_FILE})"
nmap "${NMAP_ARGS[@]}" -oX "${XML_REPORT}" -iL "${TARGETS_FILE}"

echo "[INFO] Conversion XML -> JSON"
python3 "${SCRIPT_DIR}/parse_nmap.py" "${XML_REPORT}"

JSON_REPORT="${XML_REPORT%.xml}.json"
if [ ! -f "${JSON_REPORT}" ]; then
  echo "[ERREUR] ${JSON_REPORT} introuvable → impossible de lancer l'analyse IA" >&2
else
  if [ "${AI_AUTORUN}" = "1" ]; then
    DEFAULT_AI_ENGINE_DIR="/opt/trusted_ai_soc_lite/ai_engine"
    AI_ENGINE_DIR="${AI_ENGINE_DIR:-${DEFAULT_AI_ENGINE_DIR}}"
    echo "[INFO] Analyse IA automatique du rapport ${XML_REPORT}"
    if [ ! -f "${AI_ENGINE_DIR}/analyse_scan.py" ]; then
      echo "[AVERTISSEMENT] ${AI_ENGINE_DIR}/analyse_scan.py introuvable → saute l'analyse IA" >&2
    else
      mkdir -p "$(dirname "${AI_LOG_FILE}")"
      mkdir -p "$(dirname "${AI_AUDIT_FILE}")"
      AI_VENV_ACTIVATE="${AI_ENGINE_DIR}/venv/bin/activate"
      if [ -f "${AI_VENV_ACTIVATE}" ]; then
        # shellcheck disable=SC1091
        source "${AI_VENV_ACTIVATE}"
      else
        echo "[INFO] Aucun venv détecté dans ${AI_ENGINE_DIR} → utilisation de python3 système"
      fi
      ANALYSE_CMD=(
        python3 "${AI_ENGINE_DIR}/analyse_scan.py"
        "${JSON_REPORT}"
        --model "${AI_MODEL_PATH}"
        --log-file "${AI_LOG_FILE}"
        --wazuh-log "${AI_WAZUH_LOG}"
        --audit-file "${AI_AUDIT_FILE}"
        --scan-history "${AI_SCAN_HISTORY}"
        --ti-cache "${TI_CACHE_FILE}"
      )
      if [ "${AI_DISABLE_SHAP}" = "1" ]; then
        ANALYSE_CMD+=(--disable-shap)
      fi
      if [ "${AI_DISABLE_LIME}" = "1" ]; then
        ANALYSE_CMD+=(--disable-lime)
      fi
      if [ "${AI_TI_OFFLINE}" = "1" ]; then
        ANALYSE_CMD+=(--ti-offline)
      fi
      if [ -n "${AI_EXTRA_ARGS}" ]; then
        # shellcheck disable=SC2206
        EXTRA_AI_ARGS=(${AI_EXTRA_ARGS})
        ANALYSE_CMD+=("${EXTRA_AI_ARGS[@]}")
      fi
      if "${ANALYSE_CMD[@]}"; then
        echo "[OK] Analyse IA terminée"
      else
        echo "[ERREUR] L'analyse IA automatique a échoué" >&2
      fi
    fi
  else
    echo "[INFO] AI_AUTORUN=0 → analyse IA automatique désactivée"
  fi
fi

if [ "${RESPONSE_AUTORUN}" = "1" ]; then
  if [ ! -f "${RESPONDER_SCRIPT}" ]; then
    echo "[AVERTISSEMENT] ${RESPONDER_SCRIPT} introuvable → saut de la réponse automatique" >&2
  else
    echo "[INFO] Déclenchement du responder automatique"
    RESPONDER_CMD=(
      python3 "${RESPONDER_SCRIPT}"
      --ai-log "${AI_LOG_FILE}"
      --actions-log "${RESPONSE_ACTIONS_LOG}"
      --audit-file "${RESPONSE_AUDIT_FILE}"
      --state-file "${RESPONDER_STATE_FILE}"
    )
    if [ -n "${RESPONSE_ALERT_EMAIL}" ]; then
      RESPONDER_CMD+=(--mailto "${RESPONSE_ALERT_EMAIL}")
    else
      RESPONDER_CMD+=(--disable-email)
    fi
    if [ "${RESPONDER_DISABLE_EMAIL}" = "1" ]; then
      RESPONDER_CMD+=(--disable-email)
    fi
    if [ "${RESPONDER_DISABLE_UFW}" = "1" ]; then
      RESPONDER_CMD+=(--disable-ufw)
    fi
    if [ "${RESPONDER_DRY_RUN}" = "1" ]; then
      RESPONDER_CMD+=(--dry-run)
    fi
    if [ -n "${RESPONDER_EXTRA_ARGS}" ]; then
      # shellcheck disable=SC2206
      EXTRA_RESPONDER_ARGS=(${RESPONDER_EXTRA_ARGS})
      RESPONDER_CMD+=("${EXTRA_RESPONDER_ARGS[@]}")
    fi
    if "${RESPONDER_CMD[@]}"; then
      echo "[OK] Actions de réponse orchestrées"
    else
      echo "[AVERTISSEMENT] Le responder automatique a rencontré une erreur" >&2
    fi
  fi
else
  echo "[INFO] RESPONSE_AUTORUN=0 → réponse automatique désactivée"
fi

echo "[OK] Rapports enregistrés dans ${REPORT_DIR}"
