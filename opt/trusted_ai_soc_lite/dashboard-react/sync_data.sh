#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./sync_data.sh [--dry-run]
Copies the latest audit outputs into the React dashboard public/data folder.

Environment vars:
  SOURCE_ROOT   Override source root (default: parent of this folder)
USAGE
}

if [[ "${1-}" == "--help" ]]; then
  usage
  exit 0
fi

DRY_RUN=0
if [[ "${1-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

SCRIPT_DIR=$(cd -- "$(dirname "$0")" && pwd)
ROOT=${SOURCE_ROOT:-"$(dirname "$SCRIPT_DIR")"}
DEST="$SCRIPT_DIR/public/data"
mkdir -p "$DEST"

copy_or_seed() {
  local src="$1"; shift
  local dest="$1"; shift
  local seed="$1"; shift
  if [[ -f "$src" && -s "$src" ]]; then
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "[DRY-RUN] Would copy $src -> $dest"
    else
      cp "$src" "$dest"
    fi
  else
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "[DRY-RUN] Missing $src, would seed from $seed"
    else
      cp "$seed" "$dest"
    fi
  fi
}

copy_or_seed "$ROOT/audit/ia_decisions.json" "$DEST/ia_decisions.json" "$SCRIPT_DIR/src/sample/ia_decisions.sample.json"
copy_or_seed "$ROOT/audit/response_actions.json" "$DEST/response_actions.json" "$SCRIPT_DIR/src/sample/response_actions.sample.json"
copy_or_seed "$ROOT/audit/scan_history.json" "$DEST/scan_history.json" "$SCRIPT_DIR/src/sample/scan_history.sample.json"

echo "[OK] Dashboard data synced to $DEST"
