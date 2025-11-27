# React dashboard (sans Wazuh)

Ce tableau de bord moderne lit uniquement les sorties locales du pipeline Nmap → IA → réponse (`audit/*.json`). L'interface a été réorganisée façon KPI produit (cartes, histogramme "risk by stage", donut, détails hôte/CVE) pour un rendu proche d'un dashboard professionnel.

## Pré-requis
- Debian + Node.js ≥ 18 et npm (ou pnpm)
- Le projet synchronisé dans `/opt/trusted_ai_soc_lite`

## Utilisation rapide
```bash
cd /opt/trusted_ai_soc_lite/dashboard-react
./sync_data.sh          # copie les JSON d'audit vers public/data (utilise un jeu d'exemple si vide)
npm install             # première fois uniquement
npm run dev             # lance le serveur Vite (port 4173)
```
Ensuite ouvrez http://localhost:4173 pour voir :
- KPIs (scores moyens, volumétrie par criticité)
- Timeline des scans
- Détails CVE/TI par hôte
- Table des hôtes avec findings et services
- Historique des actions du moteur de réponse
- Sélecteur de scan (scan_id) pour filtrer l'ensemble des widgets sur un scan précis

## Rafraîchir les données après un scan
1. Exécuter votre scan complet :
   ```bash
   cd /opt/trusted_ai_soc_lite
   ./run_all.sh --profile full
   ```
2. Re-synchroniser les JSON pour le dashboard :
   ```bash
   cd /opt/trusted_ai_soc_lite/dashboard-react
   ./sync_data.sh
   ```
3. Le dashboard se met à jour automatiquement (hot reload Vite).

## Parcours complet "scan ➜ dashboard"
Pour un enchaînement linéaire sur Debian (sans autres composants) :
```bash
# 1) dépendances système (une fois)
sudo apt update && sudo apt install -y git nmap python3 python3-venv rsync nodejs npm

# 2) clone + déploiement
cd /opt
sudo git clone https://github.com/<votre-espace>/TRUSTED-AI-SOC-LITE-.git trusted_ai_soc_lite_repo
cd trusted_ai_soc_lite_repo
sudo rsync -av opt/trusted_ai_soc_lite/ /opt/trusted_ai_soc_lite/

# 3) venv IA (une fois)
cd /opt/trusted_ai_soc_lite/ai_engine
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate

# 4) lancer un scan complet
cd /opt/trusted_ai_soc_lite
./run_all.sh --profile full --ti-offline

# 5) synchroniser les données pour le dashboard React
cd /opt/trusted_ai_soc_lite/dashboard-react
./sync_data.sh

# 6) démarrer le dashboard React
npm install   # première fois uniquement
npm run dev   # ouvrez http://localhost:4173
```
Après chaque nouveau scan, relancez simplement `./sync_data.sh` pour rafraîchir les données affichées.

## Mode démo sans scan
Si vos fichiers `audit/*.json` sont vides, `sync_data.sh` injecte un petit dataset d'exemple afin de visualiser le rendu sans lancer Nmap/IA.

## Astuce filtrage par scan
- Le menu "Scan" dans la page permet de choisir un `scan_id` issu de `audit/scan_history.json` ou des champs `scan_id` présents dans vos logs IA/réponse.
- Le bouton "Reset" repasse en vue agrégée sur l'ensemble des scans.

## Personnalisation
- Les fichiers affichés sont dans `public/data/*.json` (copiés depuis `audit/`).
- Les jeux d'exemple sont dans `src/sample/*.json`.
- Les couleurs/sections se modifient dans `src/index.css` et `src/App.jsx`.
