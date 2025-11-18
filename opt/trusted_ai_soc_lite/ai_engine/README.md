# `ai_engine/` – Moteur IA + XAI

Ce dossier regroupe **le cerveau analytique** de TRUSTED AI SOC LITE :
extraction de features, scoring automatique, explication XAI et publication
des décisions vers Wazuh / audit.

---

## 1. Structure

```
ai_engine/
├── analyse_scan.py        # Pipeline d'inférence (lecture JSON → score → log)
├── feature_engineering.py # Fonctions de parsing + features partagées
├── shap_explainer.py      # SHAP (TreeExplainer) avec fallback
├── lime_explainer.py      # LIME tabulaire (peut être désactivé)
├── ti_enricher.py         # Threat Intelligence (OTX/MISP offline-friendly)
├── train_model.py         # Entraînement RandomForest sur des rapports étiquetés
├── requirements.txt       # Dépendances IA/XAI/TI (venv recommandé)
├── models/
│   └── .gitkeep           # `model.pkl` est généré après entraînement
├── logs/
│   └── .gitkeep           # `ia_events.log`, `last_features.json`, `ti_cache.json`
└── ../audit/              # `ia_decisions.json` + `scan_history.json`
```

> 💡 Installez un environnement virtuel :
> ```bash
> cd /opt/trusted_ai_soc_lite/ai_engine
> python3 -m venv venv
> source venv/bin/activate
> pip install -r requirements.txt
> ```

---

## 2. Flux fonctionnel

1. `nmap_scanner/run_scan.sh` produit `reports/scan_xxx.json` via `parse_nmap.py`.
2. `analyse_scan.py` extrait les caractéristiques clés :
   - nb de ports ouverts, services sensibles, CVE détectées,
   - indices NSE (FTP anonyme, panneaux admin, etc.),
   - contexte OS et host.
3. Un modèle ML (`models/model.pkl`) est chargé, sinon une heuristique prend le relais.
4. Pour chaque hôte :
   - calcul d'un `risk_score` (0–100) + `risk_level` (low/medium/high/critical),
   - génération d'une explication courte (`top_findings`).
5. L'événement IA est journalisé :
   - `logs/ia_events.log` (copie locale),
 - `/var/log/trusted_ai_soc_lite.log` (fichier surveillé par le Wazuh Agent),
  - `../audit/ia_decisions.json` (historique structuré pour reporting).

> ℹ️ `nmap_scanner/run_scan.sh` appelle désormais automatiquement `analyse_scan.py`. Exportez `AI_AUTORUN=0` si vous
> souhaitez lancer l'analyse manuellement ou personnalisez les chemins via `AI_ENGINE_DIR`, `AI_MODEL_PATH`,
> `AI_LOG_FILE`, `AI_WAZUH_LOG` et `AI_AUDIT_FILE`.

Exemple de payload :
```json
{
  "timestamp": "2025-11-17T11:30:00Z",
  "scan_id": "scan_2025-11-17_1130",
  "host": "192.168.1.10",
  "risk_score": 93,
  "risk_level": "critical",
  "top_findings": [
    "3 CVE détectées",
    "2 services sensibles (FTP/SMB/etc.)",
    "FTP anonyme autorisé"
  ],
  "cves": ["CVE-2024-36391", "CVE-2023-48795"],
  "cvss": {"max": 9.8, "avg": 8.4},
  "shap_top_features": [
    {"feature": "cve_count", "impact": 0.42},
    {"feature": "max_cvss", "impact": 0.31}
  ],
  "threat_intel": {
    "cve_matches": [
      {"cve": "CVE-2024-36391", "cvss": 9.8, "source": "cnvd", "threat_name": "Apache HTTPD path traversal"}
    ],
    "score_adjustment": 9
  }
}
```

---

## 3. Scripts principaux

### 3.1 `analyse_scan.py`

Commande type :
```bash
cd /opt/trusted_ai_soc_lite/ai_engine
python3 analyse_scan.py \
  ../nmap_scanner/reports/scan_2025-11-17_1130.json \
  --model models/model.pkl \
  --log-file logs/ia_events.log \
  --wazuh-log /var/log/trusted_ai_soc_lite.log \
  --audit-file ../audit/ia_decisions.json
```

Arguments utiles :
| Option | Description |
| --- | --- |
| `--model` | Modèle entraîné (joblib). S'il est absent, heuristique intégrée. |
| `--log-file` | Journal local des événements IA. |
| `--wazuh-log` | Fichier suivi par le Wazuh Agent. Désactiver avec `--wazuh-log ""`. |
| `--audit-file` | Historique JSON pour reporting / Streamlit / pandas. |
| `--scan-history` | Fichier cumulatif par scan (`audit/scan_history.json`). |
| `--ti-cache` | Cache pour l'enrichissement Threat Intelligence. |
| `--disable-shap` / `--disable-lime` | Désactivent les explications XAI si vous voulez accélérer les tests. |
| `--ti-offline` | Forcer le mode TI hors-ligne (ignore les appels réseau vers OTX). |

Sorties :
- `logs/ia_events.log` : log JSON line par host.
- `logs/last_features.json` : features brutes pour debug/XAI.
- `../audit/ia_decisions.json` : liste d'événements cumulés.

### 3.2 `feature_engineering.py`

- Normalise les données JSON issues de `parse_nmap.py`.
- Compile les scripts NSE (vulners, http-enum, ssh-brute, etc.).
- Détecte les CVE, services à risque, indices d'authentification faible.
- Produit des `HostFeatures` prêts à être consommés par l'IA.

### 3.3 `train_model.py`

Permet d'entraîner rapidement un modèle RandomForest :
```bash
python3 train_model.py ../nmap_scanner/reports \
  --labels labels.json \
  --output models/model.pkl \
  --trees 300
```

Le fichier `labels.json` doit ressembler à :
```json
[
  { "scan_id": "scan_2025-11-17_1130", "host": "192.168.1.10", "label": "critical" },
  { "host": "192.168.1.5", "label": "medium" }
]
```

Les labels acceptés sont `low`, `medium`, `high`, `critical`.

### 3.4 XAI & Threat Intelligence

- `shap_explainer.py` et `lime_explainer.py` s'activent automatiquement lorsque
  les bibliothèques sont installées. Vous pouvez les désactiver via
  `--disable-shap` ou `--disable-lime` (ou en exportant `AI_DISABLE_SHAP=1`).
- `ti_enricher.py` consomme un cache JSON (`logs/ti_cache.json`). Il réconcilie
  les CVE détectées avec une base locale (CUPS, Apache, SSH, etc.) et, si un
  token `OTX_API_KEY` est défini, interroge automatiquement l'API AlienVault.
  Chaque match ajoute des métadonnées (`threat_name`, `cvss`, `source`) et un
  `score_adjustment` plafonné à +15 points.
- `scan_history.json` est rafraîchi à chaque exécution pour alimenter le
  dashboard Streamlit (timeline et KPIs) et servir de support d'audit.

---

## 4. Intégration Wazuh

1. Ajouter dans `/var/ossec/etc/ossec.conf` :
   ```xml
   <localfile>
     <log_format>json</log_format>
     <location>/var/log/trusted_ai_soc_lite.log</location>
   </localfile>
   ```
2. Créer un decoder basé sur `risk_score` / `risk_level`.
3. Définir des règles Wazuh :
   - `risk_level = critical` → alerte niveau 12 + tag `AI_VULN_DETECTED`.
   - `risk_score > 80` → déclencheur Active Response (UFW, mail, ticket).

---

## 5. Bonnes pratiques

- **Isolation** : utilisez `venv/` pour éviter les conflits système.
- **Reproductibilité** : versionnez `models/model.pkl` uniquement s'il est anonymisé.
- **Audit** : sauvegardez `ia_decisions.json` et `response_actions.json` pour vos rapports PFA.
- **Explainability** : branchez SHAP ou LIME sur `last_features.json` si vous devez démontrer la contribution des features.
- **Automatisation** : déclenchez `analyse_scan.py` depuis `run_scan.sh` ou un service `systemd` pour que chaque scan soit immédiatement scoré.

---

## 6. Prochaines étapes possibles

- Ajouter SHAP/LIME pour générer des graphes d'explication.
- Exporter les scores vers un mini-dashboard (Streamlit / Grafana JSON).
- Intégrer d'autres sources (syslog, vulnérateurs type OpenVAS) en convertissant leurs rapports vers le même schéma JSON.

