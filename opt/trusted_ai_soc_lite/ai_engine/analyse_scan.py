#!/usr/bin/env python3
"""Analyse un rapport Nmap JSON et produit un score IA + explication XAI simplifiée."""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

try:
    import joblib
except ModuleNotFoundError:  # pragma: no cover - dépendance optionnelle
    joblib = None  # type: ignore

from feature_engineering import HostFeatures, extract_features_from_scan
from lime_explainer import explain_with_lime
from shap_explainer import explain_with_shap
from ti_enricher import ThreatIntelClient

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_LOG = BASE_DIR / "logs/ia_events.log"
DEFAULT_WAZUH_LOG = Path("/var/log/trusted_ai_soc_lite.log")
DEFAULT_AUDIT = (BASE_DIR.parent / "audit/ia_decisions.json").resolve()
DEFAULT_MODEL = BASE_DIR / "models/model.pkl"
LAST_FEATURES = BASE_DIR / "logs/last_features.json"
SCAN_HISTORY = (BASE_DIR.parent / "audit/scan_history.json").resolve()
DEFAULT_TI_CACHE = BASE_DIR / "logs/ti_cache.json"

FEATURE_NAMES = [
    "open_ports",
    "risky_services",
    "cve_count",
    "has_anonymous_ftp",
    "has_default_http_admin",
    "max_cvss",
    "avg_cvss",
]


class ModelUnavailable(RuntimeError):
    """Indique qu'aucun modèle ML n'est accessible."""


def load_model(model_path: Path):
    if not model_path.exists():
        raise ModelUnavailable(f"Modèle introuvable: {model_path}")
    if joblib is None:
        raise ModelUnavailable("joblib/scikit-learn non installés dans l'environnement IA")
    return joblib.load(model_path)


def heuristic_score(features: HostFeatures) -> tuple[int, list[str]]:
    score = 15
    reasons: list[str] = []

    score += features.open_ports * 2
    if features.open_ports:
        reasons.append(f"{features.open_ports} ports ouverts")

    score += features.risky_services * 8
    if features.risky_services:
        reasons.append(f"{features.risky_services} services sensibles (FTP/SMB/etc.)")

    score += features.cve_count * 8
    if features.cve_count:
        reasons.append(f"{features.cve_count} CVE détectées")

    if features.max_cvss:
        score += int(features.max_cvss)
        reasons.append(f"CVSS max {features.max_cvss:.1f}")

    if features.has_anonymous_ftp:
        score += 15
        reasons.append("FTP anonyme autorisé")

    if features.has_default_http_admin:
        score += 10
        reasons.append("Panneaux d'administration HTTP accessibles")

    score = max(0, min(100, score))
    return score, reasons


def feature_vector(features: HostFeatures) -> list[float]:
    return [
        float(features.open_ports),
        float(features.risky_services),
        float(features.cve_count),
        float(int(features.has_anonymous_ftp)),
        float(int(features.has_default_http_admin)),
        float(features.max_cvss),
        float(features.avg_cvss),
    ]


def score_with_model(model: Any, vector: list[float], features: HostFeatures) -> tuple[int, list[str]]:
    prediction = model.predict_proba([vector])[0]
    score = int(round(prediction[-1] * 100))
    explanation = [
        f"Modèle ML : probabilité {prediction[-1]:.2f} d'état critique",
        f"open_ports={features.open_ports}",
        f"risky_services={features.risky_services}",
        f"cve_count={features.cve_count}",
    ]
    return score, explanation


def risk_label(score: int) -> str:
    if score >= 85:
        return "critical"
    if score >= 65:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def persist_json_line(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def update_audit_file(event: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            history = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(history, list):
                history = []
        except json.JSONDecodeError:
            history = []
    else:
        history = []
    history.append(event)
    path.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def write_last_features(features: list[HostFeatures]) -> None:
    LAST_FEATURES.parent.mkdir(parents=True, exist_ok=True)
    LAST_FEATURES.write_text(
        json.dumps([feat.to_dict() for feat in features], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def build_event(features: HostFeatures, scan_id: str, score: int, reasons: list[str]) -> dict[str, Any]:
    timestamp = datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")
    return {
        "timestamp": timestamp,
        "scan_id": scan_id,
        "host": features.host or features.hostname,
        "hostname": features.hostname,
        "os": features.os,
        "risk_score": score,
        "risk_level": risk_label(score),
        "top_findings": reasons[:5],
    }


def update_scan_history(
    scan_id: str,
    events: list[dict[str, Any]],
    history_path: Path,
    metadata: dict[str, Any],
) -> None:
    if not history_path:
        return
    history: list[dict[str, Any]] = []
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text(encoding="utf-8"))
            if not isinstance(history, list):
                history = []
        except json.JSONDecodeError:
            history = []

    levels = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for event in events:
        level = (event.get("risk_level") or "low").lower()
        levels[level] = levels.get(level, 0) + 1

    snapshot = {
        "scan_id": scan_id,
        "timestamp": metadata.get("start") or datetime.now(tz=UTC).isoformat().replace("+00:00", "Z"),
        "host_count": len(events),
        "average_score": statistics.fmean(e.get("risk_score", 0) for e in events) if events else 0,
        **levels,
    }
    history.append(snapshot)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(history, indent=2), encoding="utf-8")


def analyse_report(
    report_path: Path,
    model_path: Path,
    log_path: Path,
    wazuh_log: Path | None,
    audit_path: Path,
    *,
    scan_history: Path | None,
    ti_cache: Path,
    enable_shap: bool,
    enable_lime: bool,
    ti_offline: bool,
) -> list[dict[str, Any]]:
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    features = extract_features_from_scan(payload)
    write_last_features(features)
    feature_vectors = [feature_vector(feat) for feat in features]
    try:
        model = load_model(model_path)
        scorer = lambda feat, vec: score_with_model(model, vec, feat)
    except ModelUnavailable as exc:
        print(f"[WARN] {exc} → utilisation de l'heuristique intégrée", file=sys.stderr)
        model = None
        scorer = lambda feat, vec: heuristic_score(feat)

    events: list[dict[str, Any]] = []
    scan_id = report_path.stem
    shap_payloads = (
        explain_with_shap(model, feature_vectors, FEATURE_NAMES) if enable_shap else None
    )
    lime_payloads = (
        explain_with_lime(model, feature_vectors, FEATURE_NAMES) if enable_lime else None
    )
    ti_client = ThreatIntelClient(cache_path=ti_cache, offline=ti_offline)

    for idx, host_features in enumerate(features):
        vector = feature_vectors[idx]
        score, reasons = scorer(host_features, vector)
        event = build_event(host_features, scan_id, score, reasons)
        event["cves"] = host_features.cve_list
        event["cvss"] = {"max": host_features.max_cvss, "avg": host_features.avg_cvss}
        if shap_payloads and shap_payloads[idx]:
            event["shap_top_features"] = shap_payloads[idx]
        if lime_payloads and lime_payloads[idx]:
            event["lime_top_features"] = lime_payloads[idx]
        ti_data = ti_client.enrich(event.get("host"), host_features.cve_list)
        if ti_data:
            event["threat_intel"] = ti_data.to_dict()
            event["risk_score"] = min(100, event["risk_score"] + ti_data.score_adjustment)
            event["risk_level"] = risk_label(event["risk_score"])
        events.append(event)
        persist_json_line(event, log_path)
        if wazuh_log is not None:
            try:
                persist_json_line(event, wazuh_log)
            except PermissionError:
                print(f"[WARN] Impossible d'écrire dans {wazuh_log}, permissions insuffisantes", file=sys.stderr)
    for event in events:
        update_audit_file(event, audit_path)
    if scan_history is not None:
        update_scan_history(scan_id, events, scan_history, payload.get("metadata", {}))
    return events


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyse IA d'un rapport Nmap JSON")
    parser.add_argument("report", type=Path, help="Rapport JSON produit par parse_nmap.py")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--log-file", type=Path, default=DEFAULT_LOG)
    parser.add_argument(
        "--wazuh-log",
        type=str,
        default=str(DEFAULT_WAZUH_LOG),
        help="Fichier surveillé par le Wazuh Agent (désactiver avec --wazuh-log '' )",
    )
    parser.add_argument("--audit-file", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--scan-history", type=Path, default=SCAN_HISTORY)
    parser.add_argument("--ti-cache", type=Path, default=DEFAULT_TI_CACHE)
    parser.add_argument("--disable-shap", action="store_true")
    parser.add_argument("--disable-lime", action="store_true")
    parser.add_argument("--ti-offline", action="store_true", help="Désactive les appels réseau TI")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    wazuh_path = Path(args.wazuh_log) if args.wazuh_log else None
    events = analyse_report(
        args.report,
        args.model,
        args.log_file,
        wazuh_path,
        args.audit_file,
        scan_history=args.scan_history,
        ti_cache=args.ti_cache,
        enable_shap=not args.disable_shap,
        enable_lime=not args.disable_lime,
        ti_offline=args.ti_offline,
    )
    print(f"[INFO] {len(events)} hôtes analysés → logs IA prêts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
