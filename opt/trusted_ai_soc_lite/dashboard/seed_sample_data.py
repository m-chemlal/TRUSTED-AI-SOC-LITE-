#!/usr/bin/env python3
"""Seed sample data so the Streamlit dashboard renders without a prior scan.

Writes minimal IA decisions, response actions, and scan history files. Use
`--force` to overwrite existing files, otherwise existing data is preserved.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_IA = BASE_DIR / "audit/ia_decisions.json"
DEFAULT_RESPONSES = BASE_DIR / "audit/response_actions.json"
DEFAULT_HISTORY = BASE_DIR / "audit/scan_history.json"


def iso_now(offset_minutes: int = 0) -> str:
    return (datetime.now(timezone.utc)).isoformat()


def sample_ia() -> List[Dict[str, Any]]:
    return [
        {
            "timestamp": iso_now(),
            "host": "192.168.1.10",
            "risk_score": 82,
            "risk_level": "critical",
            "top_findings": ["CVE-2024-12345", "SSH weak cipher"],
        },
        {
            "timestamp": iso_now(),
            "host": "192.168.1.20",
            "risk_score": 68,
            "risk_level": "high",
            "top_findings": ["Apache outdated", "TLS 1.0 enabled"],
        },
        {
            "timestamp": iso_now(),
            "host": "192.168.1.30",
            "risk_score": 35,
            "risk_level": "medium",
            "top_findings": ["Open ports: 80/443"],
        },
        {
            "timestamp": iso_now(),
            "host": "192.168.1.40",
            "risk_score": 12,
            "risk_level": "low",
            "top_findings": ["Only SSH open"],
        },
    ]


def sample_responses() -> List[Dict[str, Any]]:
    return [
        {
            "timestamp": iso_now(),
            "host": "192.168.1.10",
            "action": "block",
            "risk_level": "critical",
            "details": "Blocked via UFW after AI critical alert",
        }
    ]


def sample_history() -> List[Dict[str, Any]]:
    return [
        {
            "timestamp": iso_now(),
            "critical": 1,
            "high": 1,
            "medium": 1,
            "low": 1,
        }
    ]


def maybe_write(path: Path, data: Any, force: bool) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed sample SOC data for the dashboard")
    parser.add_argument("--ia", type=Path, default=DEFAULT_IA, help="IA decisions file path")
    parser.add_argument(
        "--responses", type=Path, default=DEFAULT_RESPONSES, help="Response actions file path"
    )
    parser.add_argument(
        "--history", type=Path, default=DEFAULT_HISTORY, help="Scan history file path"
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    maybe_write(args.ia, sample_ia(), args.force)
    maybe_write(args.responses, sample_responses(), args.force)
    maybe_write(args.history, sample_history(), args.force)

    print("[OK] Données d'exemple écrites pour le dashboard Streamlit.")


if __name__ == "__main__":
    main()
