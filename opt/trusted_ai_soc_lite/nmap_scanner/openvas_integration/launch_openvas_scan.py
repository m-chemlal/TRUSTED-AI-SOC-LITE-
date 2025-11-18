#!/usr/bin/env python3
"""Helper to trigger an OpenVAS/GVM scan and export the report."""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import List

try:  # pragma: no cover - optional dependency
    from gvm.connections import TLSConnection  # type: ignore
    from gvm.protocols.gmp import Gmp  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    TLSConnection = None  # type: ignore
    Gmp = None  # type: ignore


def load_targets(path: Path) -> List[str]:
    hosts: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        hosts.append(line)
    return hosts


def ensure_gvm_available() -> None:
    if TLSConnection is None or Gmp is None:
        raise SystemExit(
            "python-gvm n'est pas installé.\n"
            "Installez-le via `pip install python-gvm` puis relancez ce script."
        )


def create_task(gmp: Gmp, name: str, targets: List[str], scan_config: str, credential: str | None) -> str:
    target_resp = gmp.create_target(name=name, hosts="\n".join(targets), ssh_credential_id=credential)
    target_id = ET.fromstring(target_resp).get("id")
    if not target_id:
        raise RuntimeError("Impossible de récupérer l'identifiant de la cible")

    task_resp = gmp.create_task(name=name, config_id=scan_config, target_id=target_id)
    task_id = ET.fromstring(task_resp).get("id")
    if not task_id:
        raise RuntimeError("Impossible de créer la tâche OpenVAS")
    return task_id


def run_task(gmp: Gmp, task_id: str) -> str:
    start_resp = gmp.start_task(task_id)
    report_id = ET.fromstring(start_resp).findtext("report/@id")
    if not report_id:
        raise RuntimeError("Le manager n'a pas renvoyé d'identifiant de rapport")
    return report_id


def export_report(gmp: Gmp, report_id: str, output: Path) -> None:
    resp = gmp.get_report(report_id=report_id, report_format_id="a994b278-1f62-11e1-96ac-406186ea4fc5")
    xml_data = ET.fromstring(resp)
    output.write_text(ET.tostring(xml_data, encoding="unicode"))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Déclenche une tâche OpenVAS puis exporte le rapport XML")
    parser.add_argument("--host", default="localhost", help="Adresse du manager GVM")
    parser.add_argument("--port", type=int, default=9390, help="Port GMP")
    parser.add_argument("--user", required=True, help="Compte GVM")
    parser.add_argument("--password", required=True, help="Mot de passe")
    parser.add_argument("--targets", type=Path, default=Path("../targets.txt"))
    parser.add_argument("--config", default="d21f6c81-2b88-4ac1-b7b4-a2a9f2ad4663", help="UUID du profil (Full and Fast par défaut)")
    parser.add_argument("--credential")
    parser.add_argument("--output", type=Path, default=Path("../reports/openvas_report.xml"))
    args = parser.parse_args(argv)

    ensure_gvm_available()
    hosts = load_targets(args.targets)
    if not hosts:
        raise SystemExit("Aucune cible valide dans targets.txt")

    connection = TLSConnection(hostname=args.host, port=args.port)
    with Gmp(connection=connection) as gmp:
        gmp.authenticate(args.user, args.password)
        task_name = f"TRUSTED-AI-SOC-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        task_id = create_task(gmp, task_name, hosts, args.config, args.credential)
        report_id = run_task(gmp, task_id)
        export_report(gmp, report_id, args.output)
        print(f"[OK] Rapport OpenVAS exporté vers {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
