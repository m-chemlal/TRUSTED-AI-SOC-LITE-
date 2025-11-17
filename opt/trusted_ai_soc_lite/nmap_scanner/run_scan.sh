#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGETS_FILE="${SCRIPT_DIR}/targets.txt"
REPORT_DIR="${SCRIPT_DIR}/reports"
TIMESTAMP="$(date +%F_%H%M%S)"
XML_REPORT="${REPORT_DIR}/scan_${TIMESTAMP}.xml"
JSON_REPORT="${REPORT_DIR}/scan_${TIMESTAMP}.json"

if ! command -v nmap >/dev/null 2>&1; then
  echo "[ERREUR] nmap n'est pas installé.\nInstallez-le via: sudo apt install nmap" >&2
  exit 1
fi

if [ ! -s "${TARGETS_FILE}" ]; then
  echo "[ERREUR] ${TARGETS_FILE} est introuvable ou vide." >&2
  exit 1
fi

mkdir -p "${REPORT_DIR}"

echo "[INFO] Lancement du scan Nmap (${TARGETS_FILE})"
nmap -sV -O -oX "${XML_REPORT}" -iL "${TARGETS_FILE}"

echo "[INFO] Conversion XML -> JSON"
python3 "${SCRIPT_DIR}/parse_nmap.py" "${XML_REPORT}" "${JSON_REPORT}"

echo "[OK] Rapports enregistrés dans ${REPORT_DIR}"
