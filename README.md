# TRUSTED AI SOC LITE (Déploiement Debian)

Cette version du projet TRUSTED AI SOC LITE supprime Docker pour se concentrer sur un
**déploiement propre sur une seule machine Debian** (VM ou poste local). Tout y est installé
nativement tout en conservant l'idée d'un SOC autonome mêlant détection IA et orchestration de
réponse.

## 0. Mise en route rapide (clonage + dépendances)

1. **Cloner le dépôt** sur une machine Debian disposant d'un accès root :
   ```bash
   cd /opt
   sudo git clone https://github.com/<votre-espace>/TRUSTED-AI-SOC-LITE-.git trusted_ai_soc_lite_repo
   cd trusted_ai_soc_lite_repo
   ```
2. **Installer les paquets requis** (outils de base + scanner) :
   ```bash
   sudo apt update
   sudo apt install git nmap python3 python3-venv
   ```
3. **Déployer la structure** `/opt/trusted_ai_soc_lite/` (si vous n'utilisez pas déjà ce dépôt comme racine) :
   ```bash
   sudo mkdir -p /opt/trusted_ai_soc_lite
   sudo rsync -av opt/trusted_ai_soc_lite/ /opt/trusted_ai_soc_lite/
   ```
4. **Configurer chaque brique** (scanner, IA, Wazuh, réponse). Le dossier `opt/trusted_ai_soc_lite/nmap_scanner`
   possède désormais son propre `README.md` avec toutes les commandes pour lancer, tester et automatiser les scans Nmap.

## 1. Architecture logique

```
        [Réseau interne / VM cibles]
                  │
                  ▼
        (1) Nmap Scanner Automatisé
                  │  (résultats XML/JSON)
                  ▼
        (2) Moteur IA + XAI (Python)
                  │  (scores + explications)
                  ▼
        (3) Journal IA → Fichier log custom
                  │
        [Wazuh Agent - envoie les logs au Manager]
                  │
                  ▼
    [Wazuh Manager + Indexer + Dashboard (Kibana)]
                  │
                  ▼
        (4) Règles / Alertes SOC
                  │
                  ├──► (5) Dashboard SOC (Wazuh UI)
                  └──► (6) Moteur de réponse automatique
                           (UFW / iptables / mail / ticket)
```

## 2. Architecture physique sur Debian

Une seule machine Debian (ex. Debian 12) assure trois rôles :

1. **SOC Core** : Wazuh Manager + Indexer (Elastic/OpenSearch) + Dashboard (Kibana-like)
2. **Collecte & IA** : Nmap automatisé + moteur IA/XAI Python
3. **Réponse** : scripts Bash/Python (UFW/iptables, mails, tickets)

| Couche   | Composant                          | Détail                                             |
| -------- | ---------------------------------- | -------------------------------------------------- |
| OS       | Debian 12                          | Base système, utilisateurs, sudo, journaux         |
| SIEM     | Wazuh Manager                      | Corrélation, règles, alertes                       |
| SIEM     | Wazuh Indexer (Elastic/OpenSearch) | Stockage des évènements                            |
| SIEM     | Wazuh Dashboard                    | Interface web SOC                                  |
| Agent    | Wazuh Agent (local)                | Remonte les logs locaux (syslog + logs IA)         |
| Scan     | Nmap                               | Scans réguliers du réseau/VM                       |
| IA / XAI | Python + venv                      | Scoring, clustering, SHAP/LIME                     |
| Réponse  | Scripts Python/Bash                | UFW/iptables, mails, création de tickets           |
| Audit    | JSON / SQLite                      | Historique des décisions IA & réponses             |

## 3. Organisation des dossiers

```
/opt/trusted_ai_soc_lite/
├── nmap_scanner/
│   ├── targets.txt
│   ├── run_scan.sh
│   ├── parse_nmap.py
│   └── reports/
├── ai_engine/
│   ├── venv/
│   ├── train_model.py
│   ├── analyse_scan.py
│   ├── models/
│   └── logs/
├── wazuh/
│   ├── ossec.local.conf
│   ├── decoders/
│   ├── rules/
│   └── active-response/
├── response_engine/
│   ├── responder.py
│   ├── ufw_actions.sh
│   └── mailer.py
└── audit/
    ├── ia_decisions.json
    └── response_actions.json
```

Les logs consolidés envoyés vers Wazuh sont produits dans `/var/log/trusted_ai_soc_lite.log`.

### 3.1 Implémentation du dossier `nmap_scanner`

Le dépôt contient une version prête à l'emploi du dossier `/opt/trusted_ai_soc_lite/nmap_scanner`.

| Fichier / dossier | Rôle |
| --- | --- |
| `targets.txt` | Liste des IP/CIDR à scanner (une entrée par ligne). |
| `run_scan.sh` | Script principal : lance `nmap`, stocke le rapport XML, appelle le parser puis déclenche automatiquement `ai_engine/analyse_scan.py`. |
| `parse_nmap.py` | Convertit le rapport XML en JSON structuré (metadata + hosts/services). |
| `reports/` | Destination des rapports `scan_YYYY-MM-DD_HHMMSS.{xml,json}`. |

#### Utilisation

1. Copier le dossier dans `/opt/trusted_ai_soc_lite/` (ou créer un lien symbolique).
2. Adapter `targets.txt` à votre périmètre.
3. Lancer un scan ponctuel :

   ```bash
   cd /opt/trusted_ai_soc_lite/nmap_scanner
   ./run_scan.sh
   ```

   - Le script exige `nmap` et `python3`.
   - Les rapports sont placés dans `reports/`, puis `ai_engine/analyse_scan.py` est appelé automatiquement (désactivez avec `AI_AUTORUN=0`).

4. Pour une exécution régulière, ajouter une entrée cron ou un service `systemd` qui exécute `run_scan.sh`.

### 3.2 Implémentation du dossier `ai_engine`

Le dossier `opt/trusted_ai_soc_lite/ai_engine` regroupe l'ensemble du moteur IA/XAI.

| Fichier / dossier | Rôle |
| --- | --- |
| `analyse_scan.py` | Lit les rapports JSON, extrait les features, applique le modèle ML (ou l'heuristique) puis écrit les décisions dans les logs surveillés par Wazuh. |
| `feature_engineering.py` | Fonctions communes pour détecter services sensibles, CVE issues des scripts NSE, authentifications anonymes, etc. |
| `train_model.py` | Script pour entraîner un modèle RandomForest à partir des rapports Nmap + labels (`labels.json`). |
| `requirements.txt` | Dépendances à installer dans un `venv` (scikit-learn, pandas, SHAP, LIME, etc.). |
| `models/` | Contient `model.pkl` exporté via `train_model.py`. Un `.gitkeep` évite de versionner le binaire. |
| `logs/` | Stocke `ia_events.log` et `last_features.json`. |
| `../audit/ia_decisions.json` | Historique cumulatif utilisé pour les rapports/audits. |

Usage de base :

```bash
cd /opt/trusted_ai_soc_lite/ai_engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 analyse_scan.py ../nmap_scanner/reports/scan_latest.json \
  --model models/model.pkl \
  --log-file logs/ia_events.log \
  --wazuh-log /var/log/trusted_ai_soc_lite.log \
  --audit-file ../audit/ia_decisions.json
```

Chaque événement IA ressemble à :

```json
{
  "timestamp": "2025-11-17T11:30:00Z",
  "scan_id": "scan_2025-11-17_1130",
  "host": "192.168.1.10",
  "risk_score": 87,
  "risk_level": "critical",
  "top_findings": ["3 CVE détectées", "FTP anonyme autorisé"]
}
```

Il suffit ensuite de déclarer `/var/log/trusted_ai_soc_lite.log` dans Wazuh (`<localfile>`), de créer un decoder JSON et d'écrire les règles/Active Responses alignées sur `risk_score` ou `risk_level`.

### 3.3 Pack Wazuh prêt à l'emploi

Le dossier `opt/trusted_ai_soc_lite/wazuh` fournit tous les fichiers nécessaires pour intégrer rapidement l'IA au SIEM :

| Fichier | Description |
| --- | --- |
| `ossec.local.conf` | Snippet `<localfile>` à inclure sur l'agent pour surveiller `/var/log/trusted_ai_soc_lite.log`. |
| `decoders/trusted_ai_soc_lite_decoder.xml` | Decoder JSON côté manager exposant les champs `host`, `risk_level`, `risk_score`. |
| `rules/trusted_ai_soc_lite_rules.xml` | Règles 88001–88004 qui mappent les niveaux IA sur des niveaux Wazuh (LOW→3, MED→6, HIGH→10, CRIT→12). |
| `active-response/trusted_ai_block.sh` | Exemple de réponse automatique bloquant l'IP via `ufw` et journalisant l'action dans `response_engine/actions.log`. |

Copiez ces fichiers vers `/var/ossec/` (agent + manager), rendez le script exécutable puis redémarrez `wazuh-agent` et `wazuh-manager`. Une fois `run_scan.sh` exécuté, les alertes IA apparaîtront dans le Dashboard Wazuh et pourront déclencher la réponse automatique.

## 4. Flux détaillé

### 4.1 Scan réseau (Nmap)

- Lancement périodique via cron/systemd timer :
  ```bash
  nmap -sV -O -oX /opt/trusted_ai_soc_lite/nmap_scanner/reports/scan_$(date +%F_%H%M).xml -iL /opt/trusted_ai_soc_lite/nmap_scanner/targets.txt
  ```
- `parse_nmap.py` convertit le XML en JSON propre.

### 4.2 Analyse IA + XAI

- `analyse_scan.py` lit les rapports JSON, fait du feature engineering (ports/services/OS, score CVSS),
  applique un modèle (clustering, détection anomalie) puis ajoute une explication SHAP/LIME. Il est appelé
  automatiquement par `nmap_scanner/run_scan.sh` (variable `AI_AUTORUN=0` pour le désactiver ou `AI_ENGINE_DIR`,
  `AI_MODEL_PATH`, `AI_LOG_FILE`, `AI_WAZUH_LOG`, `AI_AUDIT_FILE` pour personnaliser les chemins).
- Chaque host/scan produit une ligne JSON formatée Wazuh dans `/var/log/trusted_ai_soc_lite.log`.

Exemple :
```json
{
  "timestamp": "2025-11-17T11:30:00Z",
  "host": "192.168.1.10",
  "scan_id": "scan_2025-11-17_1130",
  "risk_score": 0.87,
  "label": "HIGH",
  "top_features": ["port_22_open", "service_ftp", "os=Windows"],
  "explanation": "SSH + FTP ouverts sur hôte exposé"
}
```

### 4.3 Intégration Wazuh

1. Wazuh Agent surveille `/var/log/trusted_ai_soc_lite.log` via `<localfile>` dans `/var/ossec/etc/ossec.conf`.
   - Un fichier prêt à copier est fourni dans `opt/trusted_ai_soc_lite/wazuh/ossec.local.conf`.
2. Le Manager fournit un decoder pour parser le JSON et des règles alignées sur `risk_score` ou `label`.
   - Utilisez `opt/trusted_ai_soc_lite/wazuh/decoders/trusted_ai_soc_lite_decoder.xml` et `.../rules/trusted_ai_soc_lite_rules.xml`.
   - `risk_score > 0.8` → alerte High + tag `AI_VULN_DETECTED`
   - `label = CRITICAL` → déclenchement d'active response
3. Les alertes sont stockées dans l'indexer et visibles via le Dashboard.
4. Un exemple d'Active Response (`active-response/trusted_ai_block.sh`) montre comment bloquer automatiquement l'adresse IP lorsque `risk_level = critical`.

### 4.4 Réponse automatique

- **Option A (Wazuh Active Response)** : déclenchement d'un script local (UFW, iptables, écriture audit).
- **Option B (Service Python)** : `responder.py` lit le log, applique sa logique, bloque l'IP, envoie un mail et
  journalise dans `audit/response_actions.json`.

### 4.5 Dashboard & Audit

- Dashboard Wazuh = vue SOC (filtres par IP/score/vulnérabilité).
- Scripts additionnels pour transformer `ia_decisions.json` et `response_actions.json` en graphiques (ex. via pandas + matplotlib ou un mini dashboard Streamlit).

## 5. Couches fonctionnelles

1. **Collecte** : Nmap + scripts parsing + Wazuh Agent + logs système Debian.
2. **Analyse & IA** : Python venv, modèles ML, explications XAI, logs enrichis.
3. **SIEM & Corrélation** : Wazuh Manager + Indexer + Dashboard.
4. **Réponse & Orchestration** : Active Response Wazuh et/ou `responder.py`, scripts firewall/mail, audit.
5. **Supervision & Reporting** : Dashboard Wazuh, fichiers JSON, reporting dédié.

## 6. Phrase de synthèse

> « Le prototype TRUSTED AI SOC LITE est déployé sur une unique machine Debian. Cette instance
> héberge la pile Wazuh (Manager, Indexer et Dashboard), un agent local, un module de scan Nmap
> automatisé, un moteur d'analyse IA/XAI et un moteur de réponse automatisée. Les résultats des scans
> sont enrichis par l'IA, journalisés dans un fichier surveillé par Wazuh, puis corrélés et visualisés
> dans le tableau de bord SOC, tout en déclenchant des actions défensives automatiques et en alimentant
> des journaux d'audit. »
