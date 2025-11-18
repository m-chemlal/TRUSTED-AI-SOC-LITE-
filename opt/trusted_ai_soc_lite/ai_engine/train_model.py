#!/usr/bin/env python3
"""Script d'entraînement rapide pour le moteur IA du SOC."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
from sklearn.ensemble import RandomForestClassifier

from feature_engineering import extract_features_from_scan

LABEL_ORDER = ["low", "medium", "high", "critical"]
LABEL_TO_INT = {label: idx for idx, label in enumerate(LABEL_ORDER)}


def load_labels(path: Path) -> list[dict[str, Any]]:
    mapping = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(mapping, list):
        raise ValueError("Le fichier de labels doit contenir une liste JSON")
    return mapping


def match_label(host: dict[str, Any], labels: list[dict[str, Any]], scan_id: str) -> str | None:
    address = host.get("host") or host.get("address")
    hostname = host.get("hostname")
    for entry in labels:
        if entry.get("scan_id") not in {None, scan_id}:
            continue
        if entry.get("host") in {address, hostname}:
            return entry.get("label")
    return None


def build_dataset(reports: list[Path], labels_file: Path) -> tuple[list[list[int]], list[int]]:
    labels = load_labels(labels_file)
    X: list[list[int]] = []
    y: list[int] = []
    for report in reports:
        features = extract_features_from_scan(report)
        scan_id = report.stem
        for feat in features:
            label = match_label(feat.to_dict(), labels, scan_id)
            if label is None or label not in LABEL_TO_INT:
                continue
            X.append(
                [
                    feat.open_ports,
                    feat.risky_services,
                    feat.cve_count,
                    int(feat.has_anonymous_ftp),
                    int(feat.has_default_http_admin),
                ]
            )
            y.append(LABEL_TO_INT[label])
    if not X:
        raise ValueError("Aucune donnée étiquetée n'a été trouvée. Complétez labels.json")
    return X, y


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Entraîne un modèle IA sur des rapports JSON")
    parser.add_argument("reports", type=Path, help="Dossier contenant les rapports JSON (parse_nmap)")
    parser.add_argument("--labels", type=Path, default=Path("labels.json"), help="Fichier JSON listant host + label")
    parser.add_argument("--output", type=Path, default=Path("models/model.pkl"))
    parser.add_argument("--trees", type=int, default=200)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    reports = sorted(args.reports.glob("*.json"))
    if not reports:
        raise SystemExit("Aucun rapport JSON détecté dans le dossier spécifié")
    X, y = build_dataset(reports, args.labels)
    model = RandomForestClassifier(n_estimators=args.trees, max_depth=12, random_state=42)
    model.fit(X, y)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.output)
    print(f"[INFO] Modèle entraîné sauvegardé dans {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
