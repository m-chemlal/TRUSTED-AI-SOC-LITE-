#!/usr/bin/env python3
"""Streamlit dashboard for TRUSTED AI SOC (complex edition)."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
IA_DECISIONS = Path(os.getenv("IA_DECISIONS_FILE", BASE_DIR / "audit/ia_decisions.json"))
RESPONSE_ACTIONS = Path(
    os.getenv("RESPONSE_ACTIONS_FILE", BASE_DIR / "audit/response_actions.json")
)
SCAN_HISTORY = Path(os.getenv("SCAN_HISTORY_FILE", BASE_DIR / "audit/scan_history.json"))


def load_json_array(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(data, list):
        return data
    return []


def main() -> None:
    st.set_page_config(page_title="TRUSTED AI SOC", layout="wide")
    st.title("TRUSTED AI SOC – Dashboard analytique")

    ia_events = load_json_array(IA_DECISIONS)
    responses = load_json_array(RESPONSE_ACTIONS)
    history = load_json_array(SCAN_HISTORY)

    if not ia_events:
        st.warning("Aucun événement IA disponible. Lancez `run_scan.sh` pour alimenter le dashboard.")
        return

    df = pd.DataFrame(ia_events)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp', ascending=False)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Hosts analysés", len(df))
    col2.metric("Score moyen", f"{df['risk_score'].mean():.1f}")
    col3.metric("Critiques", int((df['risk_level'] == 'critical').sum()))
    col4.metric("Réponses déclenchées", len(responses))

    st.subheader("Répartition des niveaux de risque")
    risk_counts = df['risk_level'].value_counts().rename_axis('risk_level').reset_index(name='count')
    st.bar_chart(risk_counts, x='risk_level', y='count')

    st.subheader("Timeline des scans")
    if history:
        hist_df = pd.DataFrame(history)
        hist_df['timestamp'] = pd.to_datetime(hist_df['timestamp'])
        st.area_chart(hist_df.set_index('timestamp')[['critical', 'high', 'medium', 'low']])
    else:
        st.info("`audit/scan_history.json` est vide. L'analyse IA le remplira automatiquement.")

    st.subheader("Top hôtes à surveiller")
    st.dataframe(
        df[['timestamp', 'host', 'risk_score', 'risk_level', 'top_findings']]
        .head(25)
        .reset_index(drop=True)
    )

    st.subheader("Détails Threat Intelligence")
    ti_rows = [event.get('threat_intel') for event in ia_events if event.get('threat_intel')]
    if ti_rows:
        flat: List[Dict[str, Any]] = []
        for entry in ti_rows:
            base = {
                'host': entry.get('host_reputation', {}).get('host'),
                'score_adjustment': entry.get('score_adjustment'),
            }
            for match in entry.get('cve_matches', []):
                flat.append({
                    **base,
                    'cve': match.get('cve'),
                    'threat_name': match.get('threat_name'),
                    'cvss': match.get('cvss'),
                    'source': match.get('source'),
                })
        st.dataframe(pd.DataFrame(flat))
    else:
        st.info("Aucun enrichissement TI enregistré pour l'instant.")

    st.subheader("Historique des réponses")
    if responses:
        resp_df = pd.DataFrame(responses)
        resp_df['timestamp'] = pd.to_datetime(resp_df['timestamp'])
        st.dataframe(resp_df.sort_values('timestamp', ascending=False).head(50))
    else:
        st.info("`response_actions.json` est encore vide.")


if __name__ == "__main__":
    main()
