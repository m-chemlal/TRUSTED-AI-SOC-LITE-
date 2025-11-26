#!/usr/bin/env python3
"""Streamlit dashboard for TRUSTED AI SOC (complex edition).

The layout mimics a clean product-style KPI board (cards + donut + bars + table)
without relying on any external SIEM UI. Everything is rendered locally via
Streamlit and the project JSON audit files.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
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


def sample_events() -> List[Dict[str, Any]]:
    """Provide a minimal sample when no IA data exists so the UI is visible."""
    return [
        {
            "timestamp": "2025-11-18T10:00:00Z",
            "host": "192.168.1.10",
            "risk_score": 82,
            "risk_level": "critical",
            "top_findings": ["CVE-2024-12345", "SSH weak cipher"],
        },
        {
            "timestamp": "2025-11-18T10:05:00Z",
            "host": "192.168.1.20",
            "risk_score": 68,
            "risk_level": "high",
            "top_findings": ["Apache outdated", "TLS 1.0 enabled"],
        },
        {
            "timestamp": "2025-11-18T10:07:00Z",
            "host": "192.168.1.30",
            "risk_score": 35,
            "risk_level": "medium",
            "top_findings": ["Open ports: 80/443"],
        },
        {
            "timestamp": "2025-11-18T10:09:00Z",
            "host": "192.168.1.40",
            "risk_score": 12,
            "risk_level": "low",
            "top_findings": ["Only SSH open"],
        },
    ]


def main() -> None:
    st.set_page_config(page_title="TRUSTED AI SOC", layout="wide")
    st.title("TRUSTED AI SOC – Synthèse visuelle")
    st.caption(
        "Vue produit autonome : KPIs, distribution des risques, tendances et détail des hôtes."
    )

    ia_events = load_json_array(IA_DECISIONS)
    responses = load_json_array(RESPONSE_ACTIONS)
    history = load_json_array(SCAN_HISTORY)

    if not ia_events:
        st.warning(
            "Aucun événement IA disponible. Lancez `run_all.sh` pour alimenter le dashboard."
        )
        if st.checkbox("Afficher un exemple statique pour visualiser la mise en page"):
            ia_events = sample_events()
        else:
            return

    df = pd.DataFrame(ia_events)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp", ascending=False)

    unique_hosts = df["host"].nunique()
    high_and_critical = (df["risk_level"].isin(["high", "critical"])).sum()
    pending_responses = len(responses)
    avg_score = df["risk_score"].mean()

    cards = st.columns(4)
    cards[0].metric("Hôtes analysés", f"{unique_hosts}")
    cards[1].metric("Scores critiques/élevés", high_and_critical)
    cards[2].metric("Score moyen", f"{avg_score:.1f}")
    cards[3].metric("Actions déclenchées", pending_responses)

    left, right = st.columns((2, 1))

    with left:
        st.subheader("Progression des statuts de risque")
        risk_order = ["critical", "high", "medium", "low"]
        risk_counts = (
            df["risk_level"].value_counts()
            .reindex(risk_order)
            .fillna(0)
            .rename_axis("risk_level")
            .reset_index(name="count")
        )
        bar_fig = px.bar(
            risk_counts,
            x="risk_level",
            y="count",
            color="risk_level",
            color_discrete_map={
                "critical": "#f44336",
                "high": "#ff9800",
                "medium": "#ffc107",
                "low": "#4caf50",
            },
            labels={"risk_level": "Niveau", "count": "Hôtes"},
            title=None,
        )
        bar_fig.update_layout(showlegend=False, height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(bar_fig, use_container_width=True)

    with right:
        st.subheader("Répartition en un coup d'œil")
        donut_data = risk_counts.copy()
        donut_data["label"] = donut_data["risk_level"].str.title()
        donut_fig = px.pie(
            donut_data,
            values="count",
            names="label",
            hole=0.5,
            color="risk_level",
            color_discrete_map={
                "critical": "#f44336",
                "high": "#ff9800",
                "medium": "#ffc107",
                "low": "#4caf50",
            },
        )
        donut_fig.update_layout(showlegend=True, height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(donut_fig, use_container_width=True)

    st.subheader("Cycle moyen de traitement")
    if history:
        hist_df = pd.DataFrame(history)
        hist_df["timestamp"] = pd.to_datetime(hist_df["timestamp"])
        hist_df = hist_df.sort_values("timestamp")
        st.line_chart(hist_df.set_index("timestamp")[["critical", "high", "medium", "low"]])
    else:
        st.info("`audit/scan_history.json` est vide. Les scans rempliront cette timeline.")

    st.subheader("Résumé des hôtes")
    table_df = df[["timestamp", "host", "risk_score", "risk_level", "top_findings"]].copy()
    table_df.rename(
        columns={
            "timestamp": "Horodatage",
            "host": "Hôte",
            "risk_score": "Score",
            "risk_level": "Niveau",
            "top_findings": "Principales observations",
        },
        inplace=True,
    )
    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Historique des réponses")
    if responses:
        resp_df = pd.DataFrame(responses)
        resp_df["timestamp"] = pd.to_datetime(resp_df["timestamp"])
        st.dataframe(
            resp_df.sort_values("timestamp", ascending=False),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Aucune action de réponse enregistrée pour le moment.")


if __name__ == "__main__":
    main()
