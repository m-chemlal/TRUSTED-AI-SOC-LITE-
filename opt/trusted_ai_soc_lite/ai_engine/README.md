# `ai_engine/` – Moteur IA + XAI (sans Wazuh ni dashboard)

Ce dossier contient le pipeline analytique : extraction de features, scoring ML/XAI et
journalisation locale pour l'audit et le moteur de réponse.

## 1. Structure
```
ai_engine/
├── analyse_scan.py        # Pipeline JSON → score → log/audit
├── feature_engineering.py # Fonctions de parsing + features partagées
├── shap_explainer.py      # SHAP (TreeExplainer) si installé
├── lime_explainer.py      # LIME tabulaire (facultatif)
├── ti_enricher.py         # Threat Intelligence offline/OTX
├── train_model.py         # Entraînement RandomForest/XGBoost
├── requirements.txt       # Dépendances (utiliser venv)
├── models/                # model.pkl exporté
└── logs/                  # ia_events.log, last_features.json, ti_cache.json
```

> Installez un environnement virtuel :
> ```bash
> cd /opt/trusted_ai_soc_lite/ai_engine
> python3 -m venv venv
> source venv/bin/activate
> pip install -r requirements.txt
> ```

## 2. Flux
1. `nmap_scanner/run_scan.sh` produit `reports/scan_xxx.json`.
2. `analyse_scan.py` extrait les features (ports, CVE, scripts NSE, scores CVSS, TI hors-ligne/OTX).
3. Le modèle ML (`models/model.pkl`) est appliqué (sinon heuristique fallback).
4. Pour chaque hôte : calcul `risk_score` + `risk_level` + `top_findings` + explications SHAP/LIME (si activées).
5. Sorties locales :
   - `logs/ia_events.log` (JSON lines)
   - `logs/last_features.json`
   - `../audit/ia_decisions.json` et `../audit/scan_history.json`

> `nmap_scanner/run_scan.sh` déclenche automatiquement `analyse_scan.py`. Exportez `AI_AUTORUN=0` si vous voulez lancer
> l'analyse manuellement ou passez des chemins personnalisés via `AI_ENGINE_DIR`, `AI_MODEL_PATH`, `AI_LOG_FILE`,
> `AI_AUDIT_FILE`, `AI_SCAN_HISTORY` ou `AI_TI_CACHE`.

Exemple d'appel manuel :
```bash
cd /opt/trusted_ai_soc_lite/ai_engine
python3 analyse_scan.py \
  ../nmap_scanner/reports/scan_2025-11-17_1130.json \
  --model models/model.pkl \
  --log-file logs/ia_events.log \
  --audit-file ../audit/ia_decisions.json
```

Options clés :
- `--scan-history` : rafraîchit `audit/scan_history.json`.
- `--ti-cache` / `--ti-offline` : contrôle du module TI.
- `--disable-shap` / `--disable-lime` : désactiver les explications XAI.

## 3. Autres scripts
- `feature_engineering.py` : normalise le JSON issu de `parse_nmap.py`, agrège ports/CVE/services, calcule scores CVSS.
- `train_model.py` : entraînement rapide d'un RandomForest. Exemple :
  ```bash
  python3 train_model.py ../nmap_scanner/reports --labels labels.json --output models/model.pkl --trees 300
  ```
- `shap_explainer.py` / `lime_explainer.py` : helpers activés si les libs sont installées.
- `ti_enricher.py` : enrichit les CVE via cache local ou OTX si `OTX_API_KEY` est défini.

## 4. Bonnes pratiques
- Utilisez `venv/` pour isoler les dépendances.
- Versionnez `model.pkl` seulement s'il est anonymisé et conforme à vos contraintes.
- Conservez `audit/ia_decisions.json` et `audit/response_actions.json` pour la traçabilité.
- Activez SHAP/LIME uniquement lorsque nécessaire pour accélérer les runs quotidiens.
