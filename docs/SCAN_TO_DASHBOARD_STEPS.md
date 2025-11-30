# Parcours complet : du scan au dashboard React

Ce guide liste, dans l’ordre, les scripts à lancer et les vérifications à faire pour exécuter le pipeline **Nmap → IA/XAI → Réponse → Dashboard** sur une machine Debian. Toutes les commandes sont à exécuter avec un shell ayant les droits suffisants (`sudo` ou root).

---

## 1. Prérequis système (une seule fois)
1. Mettre à jour l’index et installer les dépendances de base :
   ```bash
   sudo apt update
   sudo apt install -y git nmap python3 python3-venv rsync nodejs npm
   ```

2. (Optionnel) Autoriser l’utilisation d’`ufw` si vous comptez utiliser le moteur de réponse :
   ```bash
   sudo ufw status
   ```

---

## 2. Déployer le projet sous `/opt/trusted_ai_soc_lite/`
1. Cloner le dépôt dans `/opt` puis copier l’arborescence opérationnelle :
   ```bash
   cd /opt
   sudo git clone https://github.com/<votre-espace>/TRUSTED-AI-SOC-LITE-.git trusted_ai_soc_lite_repo
   cd trusted_ai_soc_lite_repo
   sudo mkdir -p /opt/trusted_ai_soc_lite
   sudo rsync -av opt/trusted_ai_soc_lite/ /opt/trusted_ai_soc_lite/
   ```

2. Vérifier que les scripts sont présents :
   ```bash
   ls /opt/trusted_ai_soc_lite/run_core.sh /opt/trusted_ai_soc_lite/run_all.sh
   ```

---

## 3. Préparer l’environnement IA (une seule fois)
1. Créer le virtualenv et installer les dépendances IA/XAI :
   ```bash
   cd /opt/trusted_ai_soc_lite/ai_engine
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   deactivate
   ```

2. (Optionnel) Adapter `requirements.txt` ou le modèle si vous disposez d’un GPU/CPU différent.

---

## 4. Choisir ou verrouiller les cibles de scan
- Par défaut, `run_core.sh` et `run_all.sh` régénèrent `nmap_scanner/targets.txt` via `generate_targets.py` avant chaque exécution.
- Pour forcer un fichier manuel :
  ```bash
  nano /opt/trusted_ai_soc_lite/nmap_scanner/targets.txt
  ```
  puis lancez avec `--no-target-refresh` ou exportez `AUTO_TARGET_DISCOVERY=0`.

---

## 5. Lancer un scan + IA + réponse (sans dashboard)
- Profil complet recommandé :
  ```bash
  cd /opt/trusted_ai_soc_lite
  ./run_core.sh --profile full --ti-offline
  ```
- Variante rapide pour tester :
  ```bash
  ./run_core.sh --profile fast --ti-offline --response-off
  ```

**Ce que fait `run_core.sh` dans l’ordre :**
1. (Optionnel) rafraîchit `targets.txt`.
2. Charge le preset Nmap choisi (`profiles.d/*.env`).
3. Lance Nmap et produit `reports/<scan>.xml` + `reports/<scan>.json`.
4. Exécute `ai_engine/analyse_scan.py` (features, TI offline/online, scoring, XAI).
5. Déclenche `response_engine/responder.py` (blocage/notifications) sauf si `--response-off` ou `RESPONDER_AUTORUN=0`.
6. Met à jour les journaux :
   - `ai_engine/logs/ia_events.log`
   - `audit/ia_decisions.json`
   - `audit/response_actions.json`

---

## 6. Lancer le pipeline puis afficher le dashboard React
1. Exécuter le pipeline complet (scan + IA + réponse) avec `run_all.sh` si vous voulez garder la gestion des presets et options OpenVAS :
   ```bash
   cd /opt/trusted_ai_soc_lite
   ./run_all.sh --profile full --ti-offline
   ```
   (ou `--profile fast --ti-offline --response-off` pour un test court)

2. Synchroniser les données vers le dashboard React :
   ```bash
   cd /opt/trusted_ai_soc_lite/dashboard-react
   ./sync_data.sh   # copie audit/*.json vers public/data, sinon charge un dataset d’exemple
   ```

3. Installer les dépendances front (première fois) puis lancer l’UI :
   ```bash
   npm install      # une fois
   npm run dev      # dashboard sur http://localhost:4173
   ```

4. Après chaque nouveau scan, relancer `./sync_data.sh` puis rafraîchir le navigateur.

---

## 7. Vérifier les sorties à chaque étape
- Rapports Nmap :
  ```bash
  ls /opt/trusted_ai_soc_lite/nmap_scanner/reports
  ```
- Décisions IA (historique) :
  ```bash
  tail -n 5 /opt/trusted_ai_soc_lite/audit/ia_decisions.json
  ```
- Actions de réponse :
  ```bash
  tail -n 5 /opt/trusted_ai_soc_lite/audit/response_actions.json
  ```
- Derniers événements IA (pour debug rapide) :
  ```bash
  tail -n 5 /opt/trusted_ai_soc_lite/ai_engine/logs/ia_events.log
  ```

---

## 8. Jeux de tests rapides
- **Dry-run sans scan ni réponse** (diagnostic) :
  ```bash
  ./run_core.sh --dry-run --profile fast --ti-offline --response-off
  ```
- **Scan rapide avec TI offline** :
  ```bash
  ./run_core.sh --profile fast --ti-offline
  ```
- **Scan complet + IA + réponse** :
  ```bash
  ./run_core.sh --profile full --ti-offline
  ```
- **Pipeline + dashboard** :
  ```bash
  ./run_all.sh --profile full --ti-offline
  cd /opt/trusted_ai_soc_lite/dashboard-react && ./sync_data.sh && npm run dev
  ```

---

## 9. Rappels utiles
- Pour passer des arguments Nmap personnalisés : `--extra-nmap-args "--top-ports 200"`.
- Pour désactiver la réponse auto : `--response-off` ou `RESPONDER_AUTORUN=0`.
- Pour travailler en mode 100 % offline : `--ti-offline` (pas d’appels OTX/VT).
- Les presets se trouvent dans `nmap_scanner/profiles.d/` et sont chargés automatiquement.

Ce fichier sert de mémo opérationnel : suivez les étapes dans l’ordre et vous obtiendrez les rapports Nmap, les verdicts IA/XAI, les journaux d’audit et, si souhaité, l’affichage React modernisé.
