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
