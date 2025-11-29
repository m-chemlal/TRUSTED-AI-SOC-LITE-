# Rôle des fichiers et dossiers principaux

Ce référentiel décrit en une page le rôle de chaque brique importante du projet. Il suit le flux Nmap ➜ IA/XAI ➜ Réponse et inclut les utilitaires associés.

## Racine / orchestration
- `run_core.sh` : enchaîne la découverte des cibles (sauf option), le scan Nmap, la conversion XML→JSON, le passage IA/XAI et le moteur de réponse.
- `run_all.sh` : variante avec gestion de presets, options OpenVAS et aides de diagnostic; délègue ensuite à `run_core.sh`.
- `audit/` : journaux persistants du SOC (décisions IA, actions de réponse, historique de scans).

## nmap_scanner/
- `run_scan.sh` : lance Nmap selon le profil courant, génère les rapports XML/JSON et déclenche l’IA.
- `profiles.d/*.env` : presets fast/balanced/full/aggressive (ports, scripts, timeouts).
- `generate_targets.py` : détecte les interfaces locales pour régénérer `targets.txt` sauf désactivation explicite.
- `targets.txt` : liste de cibles utilisée par Nmap; peut être auto-générée ou maintenue manuellement.
- `parse_nmap.py` : convertit le XML Nmap en JSON enrichi (scripts NSE, services, OS, CVE…).
- `openvas_integration/launch_openvas_scan.py` : option pour déclencher un scan Greenbone/OpenVAS et produire un rapport exploitable.
- `reports/` : stockage des sorties Nmap (XML/JSON).
- `README.md` : guide d’usage du scanner (profils, options, dépannage).

## ai_engine/
- `analyse_scan.py` : pipeline IA/XAI opérationnel (features, score, SHAP/LIME optionnels, enrichissement TI, logs/audit).
- `feature_engineering.py` : extraction des caractéristiques à partir des rapports Nmap/JSON.
- `train_model.py` : entraînement d’un modèle (RandomForest par défaut) et sauvegarde sous `models/`.
- `shap_explainer.py` / `lime_explainer.py` : aides pour générer des explications locales.
- `ti_enricher.py` : enrichissement Threat Intelligence (mode hors ligne + OTX optionnel).
- `requirements.txt` : dépendances Python de l’IA.
- `logs/` : traces locales (`ia_events.log`, `last_features.json`).
- `models/` : modèle ML persistant (`model.pkl` et objets associés).
- `README.md` : mode d’emploi détaillé de l’IA.

## response_engine/
- `responder.py` : lit les décisions IA et déclenche les actions (UFW, e-mail) avec journalisation.
- `ufw_actions.sh` : wrapper firewall pour bloquer/débloquer une IP.
- `mailer.py` : envoi d’e-mails pour les niveaux élevés.
- `README.md` : configuration et options du moteur de réponse.
- `.gitignore` : ignore les fichiers d’état ou secrets locaux.

## dashboard-react/
- `src/` (App.jsx + composants) : dashboard React/Vite moderne pour visualiser KPIs, hôtes, CVE, actions, et filtrer par scan.
- `sync_data.sh` : copie les JSON d’audit vers `public/data` ou injecte des jeux d’essai.
- `package.json` / `vite.config.js` : configuration front-end.
- `README.md` : démarrage rapide et synchronisation des données.

## Utilitaires et données
- `opt/trusted_ai_soc_lite/audit/*.json` : traces IA et réponse (lecture par le dashboard et archivage local).
- `.gitignore` (module-specifiques) : empêchent la mise en suivi des artefacts générés (logs, modèles, venv, node_modules, etc.).

## Comment naviguer
- Démarrer un SOC minimal : `./run_core.sh --profile full --ti-offline`.
- Vérifier les décisions IA : `tail -n 5 ai_engine/logs/ia_events.log`.
- Visualiser via React : `dashboard-react/sync_data.sh` puis `npm run dev`.

Cette fiche peut être copiée dans un rapport ou lue en complément des README de chaque module pour savoir où intervenir.
