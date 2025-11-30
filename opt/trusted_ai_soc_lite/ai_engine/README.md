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

## 5. Fonctionnement détaillé pas à pas
Cette section décrit le mécanisme complet du moteur IA/XAI, de l'entrée JSON jusqu'aux
sorties audit/réponse :

1. **Chargement du rapport Nmap**  
   `analyse_scan.py` lit un ou plusieurs fichiers JSON produits par `parse_nmap.py`
   (chemin par défaut : `../nmap_scanner/reports/*.json`).

2. **Normalisation & Features**  
   `feature_engineering.py` transforme le JSON hôte/ports/scripts en un dictionnaire
   structuré (ports ouverts, CVE/NSE, services, OS, stats réseau) et calcule des
   indicateurs numériques (ex. `open_ports`, `cve_count`, `cvss_max`, `service_score`).

3. **Enrichissement Threat Intel (optionnel)**  
   `ti_enricher.py` charge un cache local (`logs/ti_cache.json`) ou interroge l'API
   OTX si `OTX_API_KEY` est défini. Les scores CVE/CVSS et la présence « seen in the
   wild » sont intégrés aux features.

4. **Scoring ML / Heuristique**  
   - Si `models/model.pkl` existe, le modèle (RandomForest/XGBoost) est appliqué aux
     features agrégées pour produire un `risk_score` (0–100) et un `risk_level`
     (low/medium/high/critical).  
   - Sinon, un **fallback heuristique** basé sur les CVE/ports/scores TI assure un
     score exploitable même sans modèle.

5. **Explicabilité (XAI)**  
   - SHAP : si la lib est installée et non désactivée (`--disable-shap`),
     `shap_explainer.py` génère les contributions principales par feature.  
   - LIME : idem pour `lime_explainer.py` si non désactivé (`--disable-lime`).  
   Les explications sont résumées dans `top_findings` et/ou `explanations`.

6. **Journalisation & Audit**  
   Chaque hôte produit une entrée JSON ligne dans `logs/ia_events.log` (consommée par
   le moteur de réponse). Les décisions agrégées sont ajoutées à
   `../audit/ia_decisions.json` et la chronologie globale dans
   `../audit/scan_history.json`.

7. **Remontée au moteur de réponse**  
   `run_core.sh` ou `run_all.sh` peuvent appeler `response_engine/responder.py` avec
   le log IA pour déclencher des actions UFW/mail. Les chemins se configurent via
   les variables `AI_LOG_FILE`, `AI_AUDIT_FILE`, `AI_SCAN_HISTORY`.

8. **Technologies clés**  
   - **Python 3.11+** (recommandé)  
   - **pandas / numpy** pour le préprocessing  
   - **scikit-learn** pour RandomForest ou XGBoost (si installé)  
   - **joblib** pour sérialiser le modèle  
   - **SHAP / LIME** pour l'explicabilité optionnelle  
   - **Requests** (optionnel) pour les appels OTX TI  
   - **JSON lines** pour la compatibilité avec le moteur de réponse et les audits
