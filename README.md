# TRUSTED AI SOC LITE (Déploiement Debian, sans Wazuh ni dashboard)

Ce projet fournit un SOC minimal **Nmap ➜ IA/XAI ➜ Réponse** fonctionnant nativement sur une seule machine Debian.
Aucun composant Wazuh ni dashboard externe n'est requis : les journaux restent locaux dans `ai_engine/logs/` et `audit/`.

## 1. Mise en route rapide (Debian)

1. **Installer les paquets de base**
   ```bash
   sudo apt update
   sudo apt install git nmap python3 python3-venv
   ```

2. **Cloner puis déployer dans `/opt/trusted_ai_soc_lite/`**
   ```bash
   cd /opt
   sudo git clone https://github.com/<votre-espace>/TRUSTED-AI-SOC-LITE-.git trusted_ai_soc_lite_repo
   cd trusted_ai_soc_lite_repo
   sudo mkdir -p /opt/trusted_ai_soc_lite
   sudo rsync -av opt/trusted_ai_soc_lite/ /opt/trusted_ai_soc_lite/
   ```

3. **Préparer l'environnement Python de l'IA**
   ```bash
   cd /opt/trusted_ai_soc_lite/ai_engine
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   deactivate
   ```

4. **(Optionnel) Ajuster les cibles Nmap**
   ```bash
   nano /opt/trusted_ai_soc_lite/nmap_scanner/targets.txt
   ```
   > Par défaut, `run_core.sh`/`run_scan.sh` régénèrent `targets.txt` avant chaque
   > exécution en détectant vos interfaces (`generate_targets.py`). Si vous
   > préférez conserver un fichier entièrement manuel, lancez avec
   > `--no-target-refresh` ou exportez `AUTO_TARGET_DISCOVERY=0`.

5. **Lancer le pipeline complet (scan ➜ IA ➜ réponse)**
   ```bash
   cd /opt/trusted_ai_soc_lite
   ./run_core.sh --profile full
   ```
   * Le wrapper rafraîchit les cibles (sauf `--no-target-refresh`), lance Nmap, convertit XML→JSON, exécute l'IA/XAI et le moteur de réponse.
   * Pour un essai rapide : `./run_core.sh --profile fast --ti-offline --response-off`.

6. **Publier le projet sur GitHub (répétable)**
   ```bash
   # depuis le répertoire du dépôt cloné
   git remote add origin git@github.com:<votre-espace>/<repo>.git  # ou HTTPS
   git branch -m main                                            # optionnel
   git push -u origin main
   ```
   Cette séquence fonctionne sur un dépôt GitHub vide (sans README/LICENCE). Le `-u` règle l'upstream pour les pushes suivants.

## 1bis. Pas-à-pas détaillé (de zéro jusqu'aux résultats)

Ces étapes supposent une Debian fraîche (VM ou poste). Copiez/collez les blocs dans un terminal root ou sudo.

1) **Installer les dépendances système**
   ```bash
   sudo apt update
   sudo apt install -y git nmap python3 python3-venv rsync
   ```

2) **Récupérer le dépôt et déployer sous /opt**
   ```bash
   cd /opt
   sudo git clone https://github.com/<votre-espace>/TRUSTED-AI-SOC-LITE-.git trusted_ai_soc_lite_repo
   cd trusted_ai_soc_lite_repo
   sudo mkdir -p /opt/trusted_ai_soc_lite
   sudo rsync -av opt/trusted_ai_soc_lite/ /opt/trusted_ai_soc_lite/
   ```

3) **Préparer l'IA (venv + dépendances)**
   ```bash
   cd /opt/trusted_ai_soc_lite/ai_engine
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   deactivate
   ```

4) **Régler les cibles de scan (optionnel mais recommandé)**
   ```bash
   nano /opt/trusted_ai_soc_lite/nmap_scanner/targets.txt
   ```
   *Par défaut : loopback, hôte local, /24, scanme.nmap.org.*

5) **Lancer un scan complet + IA + réponse**
   ```bash
   cd /opt/trusted_ai_soc_lite
   ./run_core.sh --profile full --ti-offline
   ```
   - La commande régénère `targets.txt` (sauf `--no-target-refresh`), lance Nmap (XML), convertit en JSON, exécute l'IA/XAI puis le moteur de réponse.
   - Si vous voulez un essai court : `./run_core.sh --profile fast --ti-offline --response-off`.

6) **Consulter les résultats produits**
   ```bash
   ls /opt/trusted_ai_soc_lite/nmap_scanner/reports
   tail -n 5 /opt/trusted_ai_soc_lite/ai_engine/logs/ia_events.log
   tail -n 5 /opt/trusted_ai_soc_lite/audit/ia_decisions.json
   tail -n 5 /opt/trusted_ai_soc_lite/audit/response_actions.json
   ```
   - Les rapports Nmap sont en XML/JSON avec les sorties NSE.
   - `ia_events.log` contient chaque verdict IA (score, label, explications).
   - `ia_decisions.json` agrège l'historique des décisions.
   - `response_actions.json` trace les blocages UFW/emails si la réponse auto est active.

6bis) **Afficher un dashboard React moderne (sans Wazuh)**
   ```bash
   cd /opt/trusted_ai_soc_lite/dashboard-react
   ./sync_data.sh          # copie les fichiers audit vers public/data (sinon charge un jeu d'exemple)
   npm install             # première fois uniquement
   npm run dev             # serveur Vite sur http://localhost:4173
   ```
   - Ouvrez le navigateur sur http://localhost:4173 pour voir : KPIs, timeline des scans, CVE/TI, table des hôtes et actions de
     réponse.
   - Après chaque nouveau scan : relancez `./sync_data.sh` pour rafraîchir les données.

7) **Personnaliser ou relancer**
   - Changer de preset : `./run_core.sh --profile fast|balanced|full|aggressive`.
   - Passer des arguments Nmap : `--extra-nmap-args "--top-ports 200"`.
   - Désactiver la réponse : `--response-off` ou `RESPONDER_AUTORUN=0`.
   - Désactiver TI en ligne : `--ti-offline`.

### Parcours complet : du scan au dashboard React (étape par étape)
Ce scénario part d'une Debian fraîche et aboutit à l'affichage des résultats dans le dashboard React, sans dépendre d'un SIEM exte
rne.

1) **Installer les dépendances système**
   ```bash
   sudo apt update
   sudo apt install -y git nmap python3 python3-venv rsync nodejs npm
   ```

2) **Cloner et déployer sous /opt**
   ```bash
   cd /opt
   sudo git clone https://github.com/<votre-espace>/TRUSTED-AI-SOC-LITE-.git trusted_ai_soc_lite_repo
   cd trusted_ai_soc_lite_repo
   sudo mkdir -p /opt/trusted_ai_soc_lite
   sudo rsync -av opt/trusted_ai_soc_lite/ /opt/trusted_ai_soc_lite/
   ```

3) **Installer le venv IA/XAI**
   ```bash
   cd /opt/trusted_ai_soc_lite/ai_engine
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   deactivate
   ```

4) **Lancer un scan complet (Nmap ➜ IA ➜ réponse)**
   ```bash
   cd /opt/trusted_ai_soc_lite
   ./run_all.sh --profile full --ti-offline
   ```
   - pour un essai court : `./run_all.sh --profile fast --ti-offline --response-off`
   - pour conserver un `targets.txt` manuel : ajouter `--no-target-refresh`

5) **Synchroniser les données pour le dashboard React**
   ```bash
   cd /opt/trusted_ai_soc_lite/dashboard-react
   ./sync_data.sh   # copie audit/*.json vers public/data, ou injecte un dataset de démo si vide
   ```

6) **Démarrer le dashboard React**
   ```bash
   npm install      # première fois uniquement
   npm run dev      # dashboard sur http://localhost:4173
   ```

7) **Après chaque nouveau scan**
   ```bash
   cd /opt/trusted_ai_soc_lite/dashboard-react
   ./sync_data.sh   # rafraîchit les données affichées
   ```


En suivant ces étapes, vous passez du clone initial jusqu'aux fichiers de sortie (rapports Nmap, journaux IA, audit, réponse) sans dépendance à Wazuh ni dashboard externe.

## 2. Architecture minimale

```
/opt/trusted_ai_soc_lite/
├── nmap_scanner/        # Scans + parsing XML→JSON
├── ai_engine/           # Features, scoring ML/XAI, logs/audit
├── response_engine/     # Actions UFW/email + audit
├── audit/               # Historique des décisions
├── run_core.sh          # Orchestrateur Nmap ➜ IA ➜ réponse
└── run_all.sh           # Variante avec presets et OpenVAS optionnel
```

📘 Pour un rappel synthétique du rôle de chaque fichier/dossier, voir `docs/FILE_ROLES.md`.

🧭 Besoin d’un cheminement détaillé de l’exécution (ordre des scripts, commandes et vérifications) ? Consultez `docs/SCAN_TO_DASHBOARD_STEPS.md`.

## 3. Utilisation des scripts

### `run_core.sh`
Pipeline minimal sans dépendance externe.

```bash
./run_core.sh --profile full \
  --ti-offline \
  --extra-nmap-args "--top-ports 200" \
  --ai-extra "--disable-shap" \
  --responder-extra "--dry-run"
```

Options clés :
- `--profile <fast|balanced|full|aggressive>` : preset Nmap.
- `--no-target-refresh` : ne pas régénérer `targets.txt`.
- `--ti-offline` : désactive les requêtes réseau du module TI.
- `--response-off` : saute le moteur de réponse.

### `run_all.sh`
Wrapper équivalent mais capable de chaîner un scan OpenVAS avant Nmap.

```bash
./run_all.sh --profile full --openvas --openvas-args "--user gvm --password *****"
```

## 4. Où trouver les résultats ?
- Rapports Nmap : `nmap_scanner/reports/scan_*.{xml,json}`
- Logs IA : `ai_engine/logs/ia_events.log`
- Audit cumulatif : `audit/ia_decisions.json`
- Historique des réponses : `audit/response_actions.json`

## 5. Modules

### nmap_scanner
- `run_scan.sh` : lance Nmap selon le preset (`SCAN_PROFILE`), stocke l'XML et appelle `parse_nmap.py` pour générer le JSON.
- `parse_nmap.py` : normalise services, CVE, scripts NSE, et prépare les données pour l'IA.
- `profiles.d/*.env` : presets FAST/BALANCED/FULL/AGGRESSIVE.

### ai_engine
- `feature_engineering.py` : extraction de features (ports, CVE, services, scores CVSS, TI hors-ligne/OTX facultatif).
- `analyse_scan.py` : applique le modèle ML, produit le score et les explications SHAP/LIME (si installées).
- `train_model.py` : entraînement RandomForest/XGBoost (dataset local JSON).
- `logs/` : `ia_events.log`, `last_features.json`, cache TI.

### response_engine
- `responder.py` : lit les décisions IA et déclenche UFW ou alertes mail.
- `ufw_actions.sh` : wrapper firewall.
- `mailer.py` : helper SMTP (optionnel, peut être désactivé en ligne de commande).

## 6. Dépannage rapide
- **Nmap absent** : `sudo apt install nmap`
- **Python libs manquantes** : activer le venv IA puis `pip install -r requirements.txt`.
- **Aucun JSON généré** : vérifier que `run_scan.sh` est exécutable et que `parse_nmap.py` ne remonte pas d'erreur.
- **Réponse désactivée** : relancer sans `--response-off` ou sans `RESPONDER_AUTORUN=0`.

Ce guide couvre uniquement le pipeline local Nmap ➜ IA ➜ réponse. Aucun composant Wazuh ou dashboard n'est nécessaire.
