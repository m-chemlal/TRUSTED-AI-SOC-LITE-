#!/usr/bin/env python3
"""Automated response orchestrator for TRUSTED AI SOC LITE."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from mailer import send_alert

DEFAULT_AI_LOG = "/opt/trusted_ai_soc_lite/ai_engine/logs/ia_events.log"
DEFAULT_ACTIONS_LOG = "/opt/trusted_ai_soc_lite/response_engine/actions.log"
DEFAULT_AUDIT_FILE = "/opt/trusted_ai_soc_lite/audit/response_actions.json"
DEFAULT_STATE_FILE = "/opt/trusted_ai_soc_lite/response_engine/.responder_state.json"
DEFAULT_UFW_SCRIPT = "/opt/trusted_ai_soc_lite/response_engine/ufw_actions.sh"
DEFAULT_MAILTO = os.getenv("SOC_ALERT_EMAIL", "")


class ResponderState(Dict[str, Any]):
    """Simple persisted state used to avoid reprocessing events."""

    @property
    def offset(self) -> int:
        return int(self.get("offset", 0))

    @offset.setter
    def offset(self, value: int) -> None:
        self["offset"] = int(value)


def load_state(path: Path) -> ResponderState:
    if not path.exists():
        return ResponderState()
    try:
        return ResponderState(json.loads(path.read_text()))
    except json.JSONDecodeError:
        return ResponderState()


def save_state(path: Path, state: ResponderState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state))


def read_new_events(ai_log: Path, offset: int) -> tuple[List[Dict[str, Any]], int]:
    if not ai_log.exists():
        return [], offset

    events: List[Dict[str, Any]] = []
    with ai_log.open("rb") as handle:
        handle.seek(offset)
        chunk = handle.read()
        new_offset = handle.tell()

    if not chunk:
        return [], offset

    for line in chunk.decode("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events, new_offset


def format_timestamp(value: str | None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).isoformat()


def log_action(actions_log: Path, message: str) -> None:
    actions_log.parent.mkdir(parents=True, exist_ok=True)
    with actions_log.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def run_ufw(
    script: Path, action: str, ip: str, dry_run: bool, actions_log: Path
) -> None:
    if dry_run:
        log_action(actions_log, f"[DRY-RUN] {action.upper()} {ip}")
        return

    if not script.exists():
        raise FileNotFoundError(f"UFW helper script not found: {script}")

    subprocess.run([str(script), action, ip], check=True)


def append_audit(audit_file: Path, entries: List[Dict[str, Any]]) -> None:
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    existing: List[Dict[str, Any]] = []
    if audit_file.exists():
        try:
            existing = json.loads(audit_file.read_text())
        except json.JSONDecodeError:
            existing = []
    existing.extend(entries)
    audit_file.write_text(json.dumps(existing, indent=2))


def orchestrate(args: argparse.Namespace) -> None:
    state_path = Path(args.state_file)
    ai_log = Path(args.ai_log)
    actions_log = Path(args.actions_log)
    audit_file = Path(args.audit_file)
    ufw_script = Path(args.ufw_script)

    state = load_state(state_path)
    events, new_offset = read_new_events(ai_log, state.offset)

    if not events:
        print("[INFO] Aucune nouvelle décision IA à traiter")
        save_state(state_path, state)
        return

    state.offset = new_offset
    save_state(state_path, state)

    recorded_actions: List[Dict[str, Any]] = []

    for event in events:
        host = event.get("host") or event.get("ip")
        level = (event.get("risk_level") or "").lower()
        score = event.get("risk_score")
        timestamp = format_timestamp(event.get("timestamp"))
        findings = event.get("top_findings") or []

        if not host or not level:
            continue

        description = (
            f"[{timestamp}] host={host} level={level} score={score} findings={findings}"
        )
        log_action(actions_log, description)

        send_email = False
        block_host = False
        action_label = None

        if level == "critical":
            block_host = not args.disable_ufw
            send_email = not args.disable_email
            action_label = "block"
        elif level == "high":
            send_email = not args.disable_email
            action_label = "notify"
        elif level == "medium":
            action_label = "log"
        else:
            action_label = "log"

        if block_host:
            try:
                run_ufw(ufw_script, "block", host, args.dry_run, actions_log)
            except Exception as exc:  # noqa: BLE001
                log_action(actions_log, f"[ERREUR] Impossible de bloquer {host}: {exc}")

        if send_email and args.mailto:
            subject = f"SOC Alert: {level.upper()} risk on {host}"
            body = (
                f"Host: {host}\n"
                f"Risk level: {level}\n"
                f"Risk score: {score}\n"
                f"Top findings: {', '.join(map(str, findings))}\n"
                f"Timestamp: {timestamp}\n"
            )
            try:
                if args.dry_run:
                    log_action(actions_log, f"[DRY-RUN] Email → {args.mailto}: {subject}")
                else:
                    send_alert(args.mailto, subject, body)
            except Exception as exc:  # noqa: BLE001
                log_action(actions_log, f"[ERREUR] Envoi email échoué ({exc})")

        recorded_actions.append(
            {
                "host": host,
                "risk_level": level,
                "risk_score": score,
                "action": action_label,
                "timestamp": timestamp,
            }
        )

    append_audit(audit_file, recorded_actions)
    print(f"[OK] {len(recorded_actions)} actions de réponse journalisées")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Automatisation des réponses SOC")
    parser.add_argument("--ai-log", default=DEFAULT_AI_LOG)
    parser.add_argument("--actions-log", default=DEFAULT_ACTIONS_LOG)
    parser.add_argument("--audit-file", default=DEFAULT_AUDIT_FILE)
    parser.add_argument("--state-file", default=DEFAULT_STATE_FILE)
    parser.add_argument("--ufw-script", default=DEFAULT_UFW_SCRIPT)
    parser.add_argument("--mailto", default=DEFAULT_MAILTO)
    parser.add_argument("--disable-email", action="store_true")
    parser.add_argument("--disable-ufw", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    orchestrate(parse_args())
