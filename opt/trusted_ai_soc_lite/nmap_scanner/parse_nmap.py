#!/usr/bin/env python3
"""Convertit un rapport XML Nmap en JSON lisible par l'IA."""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path


def parse_services(host_elem: ET.Element) -> list[dict]:
    services: list[dict] = []
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
    if len(argv) != 3:
        raise SystemExit(f"Usage: {argv[0]} <scan.xml> <scan.json>")
    xml_path = Path(argv[1])
    json_path = Path(argv[2])
    convert(xml_path, json_path)


if __name__ == "__main__":
    main(sys.argv)
