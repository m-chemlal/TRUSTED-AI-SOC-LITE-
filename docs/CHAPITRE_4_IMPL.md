# CHAPITRE 4 — Implémentation et Réalisation Technique du Système TRUSTED-AI-SOC-LITE

## 4.1 Introduction du chapitre

Ce chapitre détaille l’implémentation concrète du SOC intelligent TRUSTED-AI-SOC-LITE sur une machine Debian. Il présente l’environnement technique, les dépendances, l’implémentation de chaque module, les scripts clés, les formats XML/JSON utilisés, les résultats d’exécution, ainsi que les limites et pistes d’amélioration.

## 4.2 Environnement de développement et d’exécution

### 4.2.1 Configuration matérielle
- Machine Debian 12 (ou 11)
- CPU : 2–4 cœurs
- RAM : 4–8 Go
- Stockage : 20 Go SSD
- Réseau : accès LAN pour tests

### 4.2.2 Configuration logicielle
- Debian 12 + UFW
- Python 3.11, Bash 5.x
- Librairies Python : scikit-learn, numpy, pandas, lxml, xmltodict, shap, lime, matplotlib (optionnel)
- Nmap + NSE vulnérabilité (vulners, vulscan)
- Outils mails (msmtp/ssmtp ou SMTP API)

### 4.2.3 Arborescence du projet
Organisation officielle dans `/opt/trusted_ai_soc_lite` :
```
/opt/trusted_ai_soc_lite
│── nmap_scanner/
│── ai_engine/
│── response_engine/
│── audit/
│── config/
│── logs/
│── run_core.sh
│── run_scan.sh
│── README.md
```

### 4.2.4 Installation des dépendances
- Script `install.sh` (ou équivalent) pour automatiser l’installation de Nmap, la création du venv Python, l’installation des modules IA/XAI, la configuration des permissions UFW et la création des répertoires nécessaires.

## 4.3 Implémentation du module 1 : nmap_scanner

### 4.3.1 Objectifs du module
- Détecter automatiquement les hôtes
- Lancer des scans Nmap multi-profils
- Générer des sorties XML/TXT pour analyse

### 4.3.2 Profils de scans
- FastScan
- BalancedScan
- FullScan
- AggressiveScan (scripts NSE vuln/auth/exploit)

### 4.3.3 Script run_scan.sh (détaillé)
- Rafraîchit les cibles
- Applique le profil choisi
- Exécute le scan
- Produit `scan.xml` et `scan.txt`
- Trace dans `scan_history.json`

### 4.3.4 Génération de données XML
- Hôtes → ports → services → CPE → CVE → scripts NSE

### 4.3.5 Problèmes rencontrés
- Lenteur UDP
- Incohérence NSE
- OS fingerprinting non fiable

## 4.4 Implémentation du module 2 : parse_nmap.py

### 4.4.1 Objectifs
- Convertir XML → JSON normalisé
- Extraire toutes les données utiles à l’IA
- Aplatir les structures imbriquées

### 4.4.2 Pipelines de parsing
1. Lecture XML
2. Conversion dictionnaire
3. Extraction
4. Enrichissement (CPE → produits → CVE)
5. Nettoyage
6. Stockage JSON

### 4.4.3 Structure JSON finale
- host, ports, services, CVEs, OS guess, RTT/latence, scripts exploit/vuln, features IA pré-calculées

### 4.4.4 Gestion des erreurs
- XML corrompu
- Scan incomplet
- Absence de CPE

## 4.5 Implémentation du module 3 : ai_engine

### 4.5.1 Feature engineering
- Nombre de ports ouverts
- Ports sensibles
- CVSS max/moyen
- Familles de services (HTTP/SSH/SMB)
- Ratio open/closed
- Empreinte OS

### 4.5.2 Modèle ML (RandomForest)
- Paramètres (nombre d’arbres, profondeur)
- Importance des features

### 4.5.3 Analyse Scan → Score
1. Charger le modèle
2. Générer les features
3. Prédire le score
4. Classifier (Low/Medium/High/Critical)
5. Enregistrer dans `logs/ia_events.log` et `audit/ia_decisions.json`

### 4.5.4 Intégration XAI
- SHAP global : summary plot, bar chart importance
- SHAP local : waterfall plot par hôte
- LIME : explication locale plus rapide

## 4.6 Implémentation du module 4 : xai_engine (si séparé)
- Génération de graphiques SHAP
- Version JSON des explications
- Filtrage des top 10 features contributives
- Appel conditionnel (optimisation temps)

## 4.7 Implémentation du module 5 : response_engine

### 4.7.1 Objectifs
- Appliquer des actions automatiques selon le niveau de risque
- Journaliser chaque décision

### 4.7.2 Politiques de réponse
- Low : logs uniquement
- Medium : logs + recommandation
- High : blocage IP (UFW)
- Critical : blocage + email + enrichissement TI

### 4.7.3 Script ufw_actions.sh
- `deny from IP`
- `delete deny`
- Vérification des règles
- Logs UFW

### 4.7.4 Script mailer.py
- Envoi email via SMTP
- Format du message
- Pièces jointes (rapport JSON)

### 4.7.5 Fichier JSON de réponse
```
{
  "timestamp": "...",
  "ip": "...",
  "action": "block",
  "reason": "High risk score",
  "details": {...}
}
```

## 4.8 Implémentation du module 6 : audit

### 4.8.1 Objectifs
- Journalisation exhaustive
- Conformité SOC
- Traçabilité ISO 27001

### 4.8.2 Fichiers générés
- `scan_history.json`
- `ia_decisions.json`
- `response_actions.json`
- `ia_events.log`

### 4.8.3 Architecture du système d’audit
- Append-only
- Horodatages ISO8601
- Réutilisation dans une interface Web ultérieure

## 4.9 Intégration globale : orchestrateur run_core.sh
- Étapes : scan → parse → IA → XAI → réponse → audit → logs
- Illustration du pipeline (ASCII/UML/timeline)

## 4.10 Tests, validation et scénarios

### 4.10.1 Jeux de tests
- Scan machine Debian
- Scan VM Windows
- Scan réseau local

### 4.10.2 Vérification de la chaîne complète
- Résultat scan
- Résultat IA
- Explication XAI
- Blocage firewall
- Logs audit

### 4.10.3 Tests de charge
- Nombre d’hôtes
- Profils agressifs
- Limitation UDP

## 4.11 Discussion critique

### 4.11.1 Forces
- Pipeline complet automatisé
- XAI intégrée
- Faible coût
- Portabilité Linux

### 4.11.2 Limites
- Dépendance Nmap
- Lenteur SHAP
- Dashboard externe non inclus

### 4.11.3 Améliorations futures
- Dashboard Kibana/React
- Apprentissage auto-supervisé
- Threat Intelligence online
- Corrélation multi-hôtes
- API REST complète

## 4.12 Conclusion du chapitre
- Rappel des objectifs
- Synthèse de l’implémentation
- Importance de la modularité
- Contribution du SOC dans une approche Zero-Trust
- Transition vers les résultats (Chapitre 5 éventuel)

