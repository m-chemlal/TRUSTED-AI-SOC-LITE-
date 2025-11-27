"""Fonctions utilitaires pour extraire les features des rapports Nmap JSON."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
from typing import Any, Iterable

CVE_PATTERN = re.compile(r"CVE-\d{4}-\d+", re.IGNORECASE)
CVSS_PATTERN = re.compile(r"CVSS(?:v[23])?[^0-9]*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
RISKY_SERVICES = {
    "ftp",
    "telnet",
    "rdp",
    "vnc",
    "smb",
    "rpcbind",
    "mysql",
    "postgresql",
    "rdp",
    "ldap",
    "mssql",
}


@dataclass
class HostFeatures:
    host: str | None
    hostname: str | None
    os: str | None
    open_ports: int
    risky_services: int
    cve_count: int
    cve_list: list[str]
    has_anonymous_ftp: bool
    has_default_http_admin: bool
    script_findings: list[str]
    max_cvss: float
    avg_cvss: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "hostname": self.hostname,
            "os": self.os,
            "open_ports": self.open_ports,
            "risky_services": self.risky_services,
            "cve_count": self.cve_count,
            "cve_list": self.cve_list,
            "max_cvss": self.max_cvss,
            "avg_cvss": self.avg_cvss,
            "has_anonymous_ftp": int(self.has_anonymous_ftp),
            "has_default_http_admin": int(self.has_default_http_admin),
        }


def _iter_script_outputs(scripts: Iterable[dict[str, Any]]) -> Iterable[str]:
    for script in scripts:
        if script.get("output"):
            yield script["output"]
        for elem in script.get("elements", []):
            value = elem.get("value")
            if isinstance(value, str):
                yield value
        for table in script.get("tables", []):
            yield from _iter_table_strings(table)


def _iter_table_strings(table: Any) -> Iterable[str]:
    if isinstance(table, dict):
        for value in table.values():
            if isinstance(value, str):
                yield value
            elif isinstance(value, list):
                for item in value:
                    yield from _iter_table_strings(item)
            elif isinstance(value, dict):
                yield from _iter_table_strings(value)


def _extract_cves_and_scores(scripts: Iterable[dict[str, Any]]) -> tuple[list[str], list[float]]:
    cves: dict[str, None] = {}
    scores: list[float] = []
    for text in _iter_script_outputs(scripts):
        if not isinstance(text, str):
            continue
        for match in CVE_PATTERN.findall(text):
            cves[match.upper()] = None
        for match in CVSS_PATTERN.findall(text):
            try:
                scores.append(float(match))
            except ValueError:
                continue
    return list(cves.keys()), scores


def _has_anonymous_ftp(scripts: Iterable[dict[str, Any]]) -> bool:
    for text in _iter_script_outputs(scripts):
        if "anonymous" in text.lower():
            return True
    return False


def _has_http_admin_exposure(scripts: Iterable[dict[str, Any]]) -> bool:
    for text in _iter_script_outputs(scripts):
        lowered = text.lower()
        if "admin" in lowered and any(keyword in lowered for keyword in {"login", "panel", "console"}):
            return True
    return False


def extract_features_from_host(host: dict[str, Any]) -> HostFeatures:
    services = host.get("services", [])
    open_services = [svc for svc in services if svc.get("state") == "open"]
    risky_services = [
        svc for svc in open_services if (svc.get("service", {}) or {}).get("name") in RISKY_SERVICES
    ]

    combined_scripts: list[dict[str, Any]] = list(host.get("scripts", []))
    per_service_scripts = list(open_services_scripts(open_services))
    for svc in open_services:
        combined_scripts.extend(svc.get("scripts", []))

    cve_list, cvss_scores = _extract_cves_and_scores(combined_scripts)
    max_cvss = max(cvss_scores) if cvss_scores else 0.0
    avg_cvss = (sum(cvss_scores) / len(cvss_scores)) if cvss_scores else 0.0

    return HostFeatures(
        host=host.get("address"),
        hostname=host.get("hostname"),
        os=host.get("os"),
        open_ports=len(open_services),
        risky_services=len(risky_services),
        cve_count=len(cve_list),
        cve_list=cve_list,
        has_anonymous_ftp=_has_anonymous_ftp(per_service_scripts),
        has_default_http_admin=_has_http_admin_exposure(per_service_scripts),
        script_findings=list({text for text in _iter_script_outputs(combined_scripts)}),
        max_cvss=max_cvss,
        avg_cvss=avg_cvss,
    )


def open_services_scripts(services: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for svc in services:
        yield from svc.get("scripts", [])


def _load_scan_payload(scan_source: Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(scan_source, Path):
        return json.loads(scan_source.read_text(encoding="utf-8"))
    return scan_source


def extract_features_from_scan(scan_source: Path | dict[str, Any]) -> list[HostFeatures]:
    data = _load_scan_payload(scan_source)
    hosts = data.get("hosts", [])
    return [extract_features_from_host(host) for host in hosts]

