# Dashboard Streamlit

Ce dossier fournit une application Streamlit minimaliste permettant de suivre les
scores IA, les enrichissements Threat Intelligence et les réponses automatiques.

## Installation rapide

```bash
cd /opt/trusted_ai_soc_lite/dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Lancement

```bash
streamlit run app.py
```

Variables d'environnement utiles :

| Variable | Description |
| --- | --- |
| `IA_DECISIONS_FILE` | Chemin alternatif pour `ia_decisions.json`. |
| `RESPONSE_ACTIONS_FILE` | Chemin personnalisé pour `response_actions.json`. |
| `SCAN_HISTORY_FILE` | Journal consolidé des scans (par défaut `audit/scan_history.json`). |

Une fois lancé, le dashboard affiche :

- les KPIs (nombre d'hôtes, score moyen, alertes critiques) ;
- la répartition des niveaux de risque et une timeline issue de `scan_history` ;
- le top des hôtes à surveiller avec leurs explications IA ;
- les détails Threat Intelligence (CVE, CVSS, sources) ;
- l'historique des actions de réponse.

Servez-vous-en pour vos démonstrations PFA ou pour brancher l'outil sur un tunnel
SSH (`ssh -L 8501:localhost:8501`), Streamlit exposant par défaut l'interface
sur http://localhost:8501.
