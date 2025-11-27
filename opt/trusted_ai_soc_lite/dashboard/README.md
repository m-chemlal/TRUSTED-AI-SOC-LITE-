# Dashboard Streamlit

Ce dossier fournit une application Streamlit minimaliste et autonome (aucun
dashboard Wazuh requis) permettant de suivre les scores IA, les enrichissements
Threat Intelligence et les réponses automatiques.

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

Pour prévisualiser la mise en page sans lancer de scan ni installer Nmap :

```bash
cd /opt/trusted_ai_soc_lite
./run_all.sh --dashboard-only --seed-sample-data --keep-dashboard
```
ou directement :

```bash
python3 dashboard/seed_sample_data.py --force
streamlit run dashboard/app.py
```

Variables d'environnement utiles :

| Variable | Description |
| --- | --- |
| `IA_DECISIONS_FILE` | Chemin alternatif pour `ia_decisions.json`. |
| `RESPONSE_ACTIONS_FILE` | Chemin personnalisé pour `response_actions.json`. |
| `SCAN_HISTORY_FILE` | Journal consolidé des scans (par défaut `audit/scan_history.json`). |

Une fois lancé, le dashboard affiche une mise en page « produit » proche du
visuel fourni (cartes KPI, barre + donut, tableau synthétique) :

- KPIs : hôtes analysés, scores élevés/critique, score moyen, actions déclenchées ;
- Graphiques : barre « progression des statuts » et donut de répartition des risques ;
- Timeline : évolution des niveaux de risque issus de `scan_history` ;
- Tableau : hôtes / scores / observations principales ;
- Vue "Détails vulnérabilités et CVE" : filtre par hôte, tableau des CVE (CVSS, source TI, nom de menace) et fiche explicative IA avec observations majeures / explication ;
- Historique : actions de réponse enregistrées.

Astuce : si vos fichiers `audit/*.json` sont encore vides, cochez l'option «
Afficher un exemple statique » dans l'interface pour visualiser immédiatement la
mise en forme avant d'exécuter vos vrais scans.

Servez-vous-en pour vos démonstrations PFA ou pour brancher l'outil sur un tunnel
SSH (`ssh -L 8501:localhost:8501`), Streamlit exposant par défaut l'interface
sur http://localhost:8501.
