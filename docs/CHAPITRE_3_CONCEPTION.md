# CHAPITRE 3 — Conception et Architecture du Système TRUSTED-AI-SOC-LITE

## 3.1 Introduction
Ce chapitre détaille la conception globale du SOC léger et intelligent TRUSTED-AI-SOC-LITE. Il fait le lien entre les fondations théoriques (Chapitre 2) et l’implémentation (Chapitre 4) en décrivant l’architecture, les flux et les choix structurants qui permettent de passer d’une idée à un système opérationnel. L’objectif est de clarifier l’organisation des modules, les échanges de données, et la façon dont la conception répond aux besoins fonctionnels et non fonctionnels d’un SOC autonome sur une machine Debian.

## 3.2 Analyse des besoins fonctionnels
### 3.2.1 Besoins fonctionnels généraux
- Lancer un scan réseau.
- Collecter et normaliser les résultats.
- Analyser via IA/ML.
- Produire un score de risque.
- Expliquer la décision (XAI).
- Appliquer une réponse automatique.
- Journaliser toutes les actions.

### 3.2.2 Besoins fonctionnels détaillés (use cases avancés)
- UF1 : Détection automatique des hôtes.
- UF2 : Scan réseau multiprofil (fast, balanced, full, aggressive).
- UF3 : Extraction CVE/CVSS à partir des scripts Nmap/TI.
- UF4 : Feature engineering avancé (services, versions, CVSS, ratios de ports).
- UF5 : Scoring ML (RandomForest/XGBoost) et heuristiques.
- UF6 : Génération des explications SHAP/LIME.
- UF7 : Blocage d’IP (UFW) selon la politique de réponse.
- UF8 : Notification par email/webhook.
- UF9 : Génération de rapports d’audit (ia_decisions.json, response_actions.json, scan_history.json).

## 3.3 Analyse des besoins non fonctionnels
### 3.3.1 Performance
- Temps moyen d’un scan par profil.
- Temps de parsing XML → JSON.
- Temps d’inférence et d’explication ML/XAI.

### 3.3.2 Sécurité
- Isolation des modules (permissions minimales, venv dédié IA).
- Restrictions sudo/ufw, logs append-only.
- Comportement fail-safe en cas d’erreur (journalisation et arrêt propre).

### 3.3.3 Scalabilité
- Passage d’un hôte unique à un sous-réseau complet.
- Ajout de nouveaux profils de scan ou modèles IA sans perturber la chaîne existante.

### 3.3.4 Portabilité
- Fonctionnement natif sur Debian (pas de dépendance Docker obligatoire).
- Modes hors ligne (scan + IA + réponse) et TI optionnel.

### 3.3.5 Maintenabilité
- Code modulaire par dossier.
- Profils et variables d’environnement externalisés.
- Journaux structurés pour faciliter le debug et la traçabilité.

## 3.4 Architecture générale du système
### 3.4.1 Vue d’ensemble globale
Le pipeline complet se compose de six briques principales : `nmap_scanner`, `parse_nmap`, `ai_engine` (scoring + XAI + TI), `response_engine`, `audit` et un tableau de bord optionnel. L’orchestrateur (`run_all.sh` ou `run_core.sh`) enchaîne automatiquement ces étapes.

### 3.4.2 Schéma d’architecture (ASCII)
```
        ┌─────────────┐
        │  run_core   │
        └──────┬──────┘
               │
      ┌────────▼───────────┐
      │    Nmap Scanner     │
      └────────┬────────────┘
               │ XML
      ┌────────▼───────────┐
      │    Parseur JSON     │
      └────────┬────────────┘
               │ JSON enrichi
      ┌────────▼───────────┐
      │     IA Engine       │
      └────────┬────────────┘
               │ scoring + XAI
      ┌────────▼───────────┐
      │  Response Engine    │
      └────────┬────────────┘
               │ audit
      ┌────────▼───────────┐
      │   Audit / Logs      │
      └─────────────────────┘
```

### 3.4.3 Architecture logique (composants logiciels)
- Scripts Bash pour l’orchestration (run_all, run_core, run_scan).
- Parsers Python pour XML → JSON et enrichissement.
- IA/XAI en Python (feature_engineering, ti_enricher, analyse_scan, shap_explainer, lime_explainer).
- Réponse Python/Bash (responder, ufw_actions, mailer) écrivant dans les journaux d’audit.
- Fichiers de configuration (profils .env, presets Nmap) et journaux JSON.

### 3.4.4 Architecture physique
- Machine Debian unique hébergeant tous les services.
- Réseau local scanné via Nmap ; UFW pour la réaction locale.
- Arborescence `/opt/trusted_ai_soc_lite` avec permissions restreintes.

## 3.5 Modélisation UML
### 3.5.1 Diagramme de cas d’utilisation
- Acteur principal : Opérateur SOC.
- Cas d’utilisation : lancer un scan, consulter le scoring, déclencher/valider la réponse, exporter les audits.

### 3.5.2 Diagramme de séquence du pipeline complet
- Séquence : `run_core.sh` → `run_scan.sh` → Nmap → `parse_nmap.py` → `analyse_scan.py` → `responder.py` → journaux d’audit.

### 3.5.3 Diagramme d’activité
- Étapes : démarrer → détecter cibles → scanner → parser → extraire features → scorer → expliquer → appliquer réponse → consigner audit → fin.

### 3.5.4 Diagramme d’état
- États : Découvert → Scanné → Classé → Répondu → Archivé.

### 3.5.5 Diagramme de classes (optionnel)
- Classes : `ScanResult`, `FeatureExtractor`, `RiskAnalyzer`, `Responder`, `AuditLogger`.

## 3.6 Conception détaillée des modules
### 3.6.1 Module 1 : nmap_scanner/
- Profils fast/balanced/full/aggressive, génération automatique des cibles, scripts NSE vuln/auth, export XML/JSON.

### 3.6.2 Module 2 : parse_nmap.py
- Parsing XML Nmap, extraction des services/CPE/CVE, flattening des scripts NSE, production d’un JSON enrichi pour l’IA.

### 3.6.3 Module 3 : ai_engine/
- Feature engineering (ports, services, CVE/CVSS, ratios), scoring ML/heuristique, XAI (SHAP/LIME), TI optionnelle, sortie vers `ia_events.log`, `ia_decisions.json`, `scan_history.json`.

### 3.6.4 Module 4 : xai_engine/ (inclus dans ai_engine)
- Génération des explications locales/globales SHAP/LIME, formats JSON/graphes pour la restitution.

### 3.6.5 Module 5 : response_engine/
- Application de politiques : blocage UFW, notifications, journalisation des actions (`response_actions.json`).

### 3.6.6 Module 6 : audit/
- Journaux structurés (JSON horodaté), traçabilité des décisions IA et des réponses, alignement avec les bonnes pratiques ISO/IEC.

## 3.7 Sécurité, résilience et conformité
### 3.7.1 Durcissement des modules
- Permissions Unix minimales, exécution avec les droits nécessaires uniquement, séparation des comptes lorsque possible.

### 3.7.2 Protection contre les abus
- Limitation des profils trop agressifs par défaut, contrôles d’arguments, timeouts pour les scripts Nmap.

### 3.7.3 Conformité
- Journalisation horodatée pour la traçabilité (ISO 27001), absence de données personnelles (RGPD), alignement NIS2 pour la détection/notification.

## 3.8 Difficultés rencontrées et solutions
- Parsing XML hétérogène des scripts NSE et gestion des tables imbriquées.
- Lenteur des scans UDP ou des scripts brute/exploit → profils et timeouts paramétrables.
- Intégration SHAP/LIME coûteuse → options de désactivation/échantillonnage.
- Permissions UFW et envoi d’emails → scripts dédiés et erreurs explicites.
- Harmonisation des journaux JSON (scans, IA, réponses) pour simplifier l’audit.

## 3.9 Conclusion
La conception détaillée de TRUSTED-AI-SOC-LITE démontre comment un SOC léger peut rester cohérent, sécurisé et explicable sur une seule machine Debian. Les besoins fonctionnels et non fonctionnels sont traduits en modules clairement séparés, orchestrés par des scripts simples. Les modèles UML éclairent les interactions clés, tandis que la prise en compte des contraintes de performance, de sécurité et d’audit prépare la mise en œuvre décrite au Chapitre 4.
