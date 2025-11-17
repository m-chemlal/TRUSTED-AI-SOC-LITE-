# TRUSTED AI SOC LITE (Déploiement Debian)

Cette version du projet TRUSTED AI SOC LITE supprime Docker pour se concentrer sur un
**déploiement propre sur une seule machine Debian** (VM ou poste local). Tout y est installé
nativement tout en conservant l'idée d'un SOC autonome mêlant détection IA et orchestration de
réponse.

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
├── response_engine/
│   ├── responder.py
│   ├── ufw_actions.sh
│   └── mailer.py
└── audit/
    ├── ia_decisions.json
    └── response_actions.json
```

Les logs consolidés envoyés vers Wazuh sont produits dans `/var/log/trusted_ai_soc_lite.log`.

## 4. Flux détaillé

### 4.1 Scan réseau (Nmap)

- Lancement périodique via cron/systemd timer :
  ```bash
  nmap -sV -O -oX /opt/trusted_ai_soc_lite/nmap_scanner/reports/scan_$(date +%F_%H%M).xml -iL /opt/trusted_ai_soc_lite/nmap_scanner/targets.txt
  ```
- `parse_nmap.py` convertit le XML en JSON propre.

### 4.2 Analyse IA + XAI

- `analyse_scan.py` lit les rapports JSON, fait du feature engineering (ports/services/OS, score CVSS),
  applique un modèle (clustering, détection anomalie) puis ajoute une explication SHAP/LIME.
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
2. Le Manager fournit un decoder pour parser le JSON et des règles alignées sur `risk_score` ou `label`.
   - `risk_score > 0.8` → alerte High + tag `AI_VULN_DETECTED`
   - `label = CRITICAL` → déclenchement d'active response
3. Les alertes sont stockées dans l'indexer et visibles via le Dashboard.

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
