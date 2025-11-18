#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGETS_FILE="${SCRIPT_DIR}/targets.txt"
REPORT_DIR="${SCRIPT_DIR}/reports"
TIMESTAMP="$(date +%F_%H%M%S)"
XML_REPORT="${REPORT_DIR}/full_soc_scan_${TIMESTAMP}.xml"
AUTO_TARGET_DISCOVERY="${AUTO_TARGET_DISCOVERY:-1}"
SCAN_PROFILE="${SCAN_PROFILE:-full}"
EXTRA_NMAP_ARGS="${EXTRA_NMAP_ARGS:-}"

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

echo "[OK] Rapports enregistrés dans ${REPORT_DIR}"
