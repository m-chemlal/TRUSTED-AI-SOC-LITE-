# nmap_scanner

Ce dossier regroupe tous les fichiers nécessaires pour lancer les scans réseau Nmap
sur la machine Debian qui héberge TRUSTED AI SOC LITE.

## Prérequis logiciels

| Outil | Pourquoi | Commande d'installation (Debian) |
| --- | --- | --- |
| `git` | cloner ou mettre à jour le dépôt | `sudo apt install git`
| `nmap` | effectuer les scans réseau | `sudo apt install nmap`
| `python3` + `python3-venv` | exécuter `parse_nmap.py` et les scripts IA | `sudo apt install python3 python3-venv`

> 💡 Vérifiez la présence des binaires avec `git --version`, `nmap --version` et
> `python3 --version`.

## Installation locale

```bash
# 1. Cloner le dépôt complet
cd /opt
sudo git clone https://github.com/<votre-espace>/TRUSTED-AI-SOC-LITE-.git trusted_ai_soc_lite_repo
cd trusted_ai_soc_lite_repo

# 2. Copier (ou lier) le dossier du scanner vers /opt/trusted_ai_soc_lite
sudo mkdir -p /opt/trusted_ai_soc_lite
sudo rsync -av opt/trusted_ai_soc_lite/nmap_scanner/ /opt/trusted_ai_soc_lite/nmap_scanner/
cd /opt/trusted_ai_soc_lite/nmap_scanner
```

Adaptez `targets.txt` pour votre périmètre (IP uniques, plages CIDR, noms DNS… une entrée par ligne).

## Utilisation rapide

```bash
cd /opt/trusted_ai_soc_lite/nmap_scanner
./run_scan.sh
```

Le script :
1. vérifie la présence de `nmap` et `targets.txt` ;
2. génère `reports/scan_YYYY-MM-DD_HHMMSS.xml` ;
3. appelle `parse_nmap.py` pour produire le JSON correspondant.

## Tests & validations

- **Test à blanc** : ajoutez `scanme.nmap.org` dans `targets.txt` puis lancez `./run_scan.sh`. Vous devez obtenir un couple de fichiers XML/JSON.
- **Parser seul** : `python3 parse_nmap.py reports/scan_test.xml reports/scan_test.json` pour valider la conversion sur un fichier existant.
- **Intégration IA** : copiez les fichiers JSON vers `ai_engine/` ou pointez `analyse_scan.py` sur le dossier `reports/` pour vérifier l'enchaînement complet.

## Automatisation (optionnel)

Pour exécuter le scan chaque heure via cron :

```bash
sudo crontab -e
0 * * * * /opt/trusted_ai_soc_lite/nmap_scanner/run_scan.sh >/var/log/nmap_scanner.cron.log 2>&1
```

Ou créez un timer `systemd` si vous préférez un contrôle plus fin (journalisation, dépendances réseau, etc.).
