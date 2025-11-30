"""Offline-friendly Threat Intelligence helpers."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:  # pragma: no cover - optional dependency
    import requests
except ModuleNotFoundError:  # pragma: no cover
    requests = None  # type: ignore

BUILTIN_CVE_DB = {
    "CVE-2024-36391": {
        "threat_name": "Apache HTTPD path traversal",
        "cvss": 9.8,
        "source": "cnvd",
        "exploit": True,
    },
    "CVE-2024-47850": {
        "threat_name": "CUPS IPP RCE",
        "cvss": 7.5,
        "source": "nvd",
        "exploit": True,
    },
    "CVE-2023-48795": {
        "threat_name": "SSH Terrapin attack",
        "cvss": 7.1,
        "source": "mitre",
        "exploit": False,
    },
}

SUSPICIOUS_HOSTS = {
    "scanme.nmap.org": {"reputation": "unknown", "score": 2},
    "192.168.1.171": {"reputation": "iot", "score": 4},
}


@dataclass
class ThreatIntelResult:
    cve_matches: List[Dict[str, Any]]
    host_reputation: Optional[Dict[str, Any]]
    score_adjustment: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cve_matches": self.cve_matches,
            "host_reputation": self.host_reputation,
            "score_adjustment": self.score_adjustment,
        }


class ThreatIntelClient:
    """Performs lightweight TI lookups (offline first)."""

    def __init__(self, cache_path: Path | None = None, offline: bool = False) -> None:
        self.cache_path = cache_path
        self.offline = offline or requests is None
        self.cache: Dict[str, Any] = {}
        if cache_path and cache_path.exists():
            try:
                self.cache = json.loads(cache_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self.cache = {}

    def _save_cache(self) -> None:
        if not self.cache_path:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, indent=2), encoding="utf-8")

    def enrich(self, host: str | None, cves: Iterable[str]) -> ThreatIntelResult | None:
        cve_list = list(dict.fromkeys(cves))
        matches = [self._lookup_cve(cve) for cve in cve_list]
        matches = [match for match in matches if match is not None]
        reputation = self._lookup_host(host) if host else None

        if not matches and not reputation:
            return None

        score_bonus = 0
        if matches:
            score_bonus += int(max(item.get("cvss", 0.0) for item in matches))
        if reputation:
            score_bonus += int(reputation.get("score", 0))

        result = ThreatIntelResult(matches, reputation, min(score_bonus, 15))
        if self.cache_path:
            self.cache[f"{host}:{','.join(cve_list)}"] = result.to_dict()
            self._save_cache()
        return result

    def _lookup_cve(self, cve_id: str) -> Dict[str, Any] | None:
        cache_key = f"cve:{cve_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        if cve_id in BUILTIN_CVE_DB:
            data = {"cve": cve_id, **BUILTIN_CVE_DB[cve_id]}
        elif not self.offline and requests is not None:
            data = self._query_remote_cve(cve_id)
        else:
            data = None

        if data and self.cache_path:
            self.cache[cache_key] = data
        return data

    def _lookup_host(self, host: str | None) -> Dict[str, Any] | None:
        if not host:
            return None
        cache_key = f"host:{host}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        if host in SUSPICIOUS_HOSTS:
            data = {"host": host, **SUSPICIOUS_HOSTS[host]}
        else:
            data = None

        if data and self.cache_path:
            self.cache[cache_key] = data
        return data

    def _query_remote_cve(self, cve_id: str) -> Dict[str, Any] | None:
        if requests is None:
            return None
        api_key = os.getenv("OTX_API_KEY") or os.getenv("VT_API_KEY")
        if not api_key:
            return None
        headers = {"X-OTX-API-KEY": api_key}
        url = f"https://otx.alienvault.com/api/v1/indicators/cve/{cve_id}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
            data = response.json()
            pulses = data.get("pulse_info", {}).get("count", 0)
            return {
                "cve": cve_id,
                "threat_name": data.get("title") or cve_id,
                "cvss": float(data.get("cvss", 0) or 0),
                "source": "otx",
                "pulses": pulses,
            }
        except Exception:  # noqa: BLE001
            return None


__all__ = ["ThreatIntelClient", "ThreatIntelResult"]
