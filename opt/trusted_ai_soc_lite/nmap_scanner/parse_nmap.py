#!/usr/bin/env python3
"""Convertit un rapport XML Nmap en JSON lisible par l'IA."""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def parse_table(table_elem: ET.Element) -> dict[str, Any]:
    """Convertit récursivement les blocs <table> des scripts NSE en dictionnaire."""

    parsed: dict[str, Any] = {}
    # Les éléments simples sont stockés sous forme clé/valeur.
    for elem in table_elem.findall("elem"):
        key = elem.attrib.get("key") or "items"
        value = (elem.text or "").strip() or None
        if key in parsed:
            # Normalise en liste si plusieurs entrées partagent la même clé.
            if not isinstance(parsed[key], list):
                parsed[key] = [parsed[key]]
            parsed[key].append(value)
        else:
            parsed[key] = value

    # Les sous-tables deviennent elles-mêmes des dictionnaires imbriqués.
    for sub_table in table_elem.findall("table"):
        key = sub_table.attrib.get("key") or "tables"
        value = parse_table(sub_table)
        if key in parsed:
            if not isinstance(parsed[key], list):
                parsed[key] = [parsed[key]]
            parsed[key].append(value)
        else:
            parsed[key] = value

    return parsed


def parse_script_blocks(parent: ET.Element | None) -> list[dict[str, Any]]:
    if parent is None:
        return []

    scripts: list[dict[str, Any]] = []
    for script in parent.findall("script"):
        scripts.append(
            {
                "id": script.attrib.get("id"),
                "output": script.attrib.get("output"),
                "elements": [
                    {
                        "key": elem.attrib.get("key"),
                        "value": (elem.text or "").strip() or None,
                    }
                    for elem in script.findall("elem")
                ],
                "tables": [parse_table(table) for table in script.findall("table")],
            }
        )
    return scripts


def parse_services(host_elem: ET.Element) -> list[dict[str, Any]]:
    services: list[dict[str, Any]] = []
    ports_elem = host_elem.find("ports")
    if ports_elem is None:
        return services
    for port in ports_elem.findall("port"):
        service_elem = port.find("service")
        services.append(
            {
                "protocol": port.attrib.get("protocol"),
                "portid": port.attrib.get("portid"),
                "state": (port.find("state").attrib.get("state") if port.find("state") is not None else None),
                "service": (
                    {
                        "name": service_elem.attrib.get("name"),
                        "product": service_elem.attrib.get("product"),
                        "version": service_elem.attrib.get("version"),
                    }
                    if service_elem is not None
                    else None
                ),
                "scripts": parse_script_blocks(port),
            }
        )
    return services


def parse_host(host_elem: ET.Element) -> dict:
    addr = host_elem.find("address")
    hostname_elem = host_elem.find("hostnames/hostname")
    osmatch = host_elem.find("os/osmatch")
    return {
        "address": addr.attrib.get("addr") if addr is not None else None,
        "hostname": hostname_elem.attrib.get("name") if hostname_elem is not None else None,
        "status": host_elem.find("status").attrib.get("state") if host_elem.find("status") is not None else None,
        "os": osmatch.attrib.get("name") if osmatch is not None else None,
        "accuracy": int(osmatch.attrib.get("accuracy", 0)) if osmatch is not None else None,
        "services": parse_services(host_elem),
        "scripts": parse_script_blocks(host_elem.find("hostscript")),
    }


def convert(xml_path: Path, json_path: Path) -> None:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    run_stats = root.find("runstats/finished")
    scan_info = root.find("scaninfo")

    start_attr = root.attrib.get("start")
    start_dt = (
        datetime.fromtimestamp(int(start_attr), tz=UTC).isoformat().replace("+00:00", "Z")
        if start_attr is not None
        else None
    )

    payload = {
        "metadata": {
            "scanner": root.attrib.get("scanner"),
            "args": root.attrib.get("args"),
            "start": start_dt,
            "elapsed": float(run_stats.attrib.get("elapsed", 0)) if run_stats is not None else None,
            "hosts_up": int(run_stats.attrib.get("hosts_up", 0)) if run_stats is not None else None,
            "hosts_total": int(run_stats.attrib.get("hosts_total", 0)) if run_stats is not None else None,
            "scan_type": scan_info.attrib.get("type") if scan_info is not None else None,
        },
        "hosts": [parse_host(host) for host in root.findall("host")],
    }

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main(argv: list[str]) -> None:
    if len(argv) not in {2, 3}:
        raise SystemExit(f"Usage: {argv[0]} <scan.xml> [scan.json]")

    xml_path = Path(argv[1])
    if len(argv) == 3:
        json_path = Path(argv[2])
    else:
        json_path = xml_path.with_suffix(".json")

    convert(xml_path, json_path)


if __name__ == "__main__":
    main(sys.argv)
