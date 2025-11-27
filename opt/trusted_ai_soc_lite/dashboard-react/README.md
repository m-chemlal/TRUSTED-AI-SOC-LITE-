# React dashboard (sans Wazuh)

Ce tableau de bord moderne lit uniquement les sorties locales du pipeline Nmap → IA → réponse (`audit/*.json`).

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

## Mode démo sans scan
Si vos fichiers `audit/*.json` sont vides, `sync_data.sh` injecte un petit dataset d'exemple afin de visualiser le rendu sans lancer Nmap/IA.

## Personnalisation
- Les fichiers affichés sont dans `public/data/*.json` (copiés depuis `audit/`).
- Les jeux d'exemple sont dans `src/sample/*.json`.
- Les couleurs/sections se modifient dans `src/index.css` et `src/App.jsx`.
