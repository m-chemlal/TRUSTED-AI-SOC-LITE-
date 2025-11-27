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

### Comment choisir des cibles valides ?

1. **Identifiez votre adresse IP locale** :

   ```bash
   ip -4 a
   ```

   Relevez la ligne `inet` correspondant à votre interface (ex. `inet 192.168.1.5/24`).

2. **Déduisez le sous-réseau** : l'exemple ci-dessus signifie que vous pouvez scanner
   `192.168.1.0/24` (hôtes `192.168.1.1` à `192.168.1.254`).

3. **Remplissez `targets.txt` avec des adresses atteignables** depuis votre machine :
   - `127.0.0.1` (loopback) et votre IP locale (autoscan sûrs) ;
   - autres hôtes de votre LAN ou accessibles via VPN/route ;
   - plages CIDR ou noms DNS résolvables.

4. **Option facultative** : ajoutez `scanme.nmap.org`, la cible de test officielle
  d'Nmap, pour valider rapidement vos scripts.

### Génération automatique d'un `targets.txt` valide

- Le script `generate_targets.py` détecte vos interfaces IPv4 et écrit un
  `targets.txt` aligné sur votre machine (loopback, IP locale, sous-réseau et,
  si souhaité, `scanme.nmap.org`).
- `run_scan.sh` l'exécute automatiquement avant chaque scan. Pour une
  génération manuelle :

  ```bash
  cd /opt/trusted_ai_soc_lite/nmap_scanner
  python3 generate_targets.py --force
  ```

- Si vous voulez garder votre propre liste, exportez `AUTO_TARGET_DISCOVERY=0`
  avant de lancer `run_scan.sh` ; le script n'écrasera plus le fichier.
- Les utilisateurs avancés peuvent aussi appeler `python3 generate_targets.py \
  --output chemin_personnalisé` pour alimenter un fichier différent.
- Pour éviter les **doublons** dans les rapports Nmap, le générateur n'ajoute
  plus `localhost` par défaut ; la cible `127.0.0.1` couvre déjà le loopback.
  Ajoutez-la manuellement uniquement si vous avez besoin d'un test DNS
  explicite.

> ⚠️ Des IP extérieures à votre réseau (ou non routées) conduiront à des échecs
> de scan. Assurez-vous que chaque entrée correspond bien à un segment reachable
> depuis votre Debian.

## Utilisation rapide

```bash
cd /opt/trusted_ai_soc_lite/nmap_scanner
./run_scan.sh
```

Le script :
1. vérifie la présence de `nmap` et `targets.txt` ;
2. exécute un **scan SOC complet stabilisé** (détection de version, scripts NSE `default,vuln,auth,malware,safe`, fingerprinting OS) pour éviter les gels sur les réseaux encombrés ;
3. génère `reports/full_soc_scan_YYYY-MM-DD_HHMMSS.xml` puis appelle `parse_nmap.py` (qui écrit automatiquement le JSON associé) ;
4. livre un rapport prêt à être ingéré par l'IA.

💡 Pour tout déclencher depuis la racine du projet (scan + IA + réponse),
utilisez simplement `../run_core.sh` ou `../run_all.sh` (sans dépendances dashboard/Wazuh).

### Choisir un profil de scan adapté

`run_scan.sh` embarque désormais trois profils sélectionnables via la variable
d'environnement `SCAN_PROFILE` :

| Profil | Commande d'exemple | Cas d'usage | Options clés |
| --- | --- | --- | --- |
| `full` *(défaut)* | `SCAN_PROFILE=full ./run_scan.sh` | SOC complet stabilisé : ports `1-1024` + scripts `default,vuln,auth,malware,safe` → XML/JSON garantis même lorsque des hôtes filtrent agressivement. | `-p 1-1024`, `--script-timeout 20s`, `--max-retries 2`, `--host-timeout 3m`. |
| `balanced` | `SCAN_PROFILE=balanced ./run_scan.sh` | Compromis ~5 min : ports 1-1024 + scripts `default,vuln,auth,malware,safe`. | Timeout NSE 15s, host-timeout 2 min. |
| `fast` | `SCAN_PROFILE=fast ./run_scan.sh` | Contrôle rapide (<2 min) basé sur les 200 ports principaux et des scripts sûrs. | Timeout NSE 10s, host-timeout 45s. |

Par défaut, le profil **FULL_SOC** privilégie la stabilité : il couvre les 1024
ports les plus critiques et exécute les scripts NSE nécessaires
(`default,vuln,auth,malware,safe`) tout en appliquant des garde-fous
(`--script-timeout`, `--max-retries`, `--host-timeout`). Résultat :
`parse_nmap.py` produit systématiquement le JSON même si certains hôtes répondent
lentement ou laissent tomber les paquets.

Besoin de revenir au scan « full agressif » (tous les ports + scripts
`exploit,brute` + `unsafe=1`) ? Exportez `FULL_INCLUDE_AGGRESSIVE=1
FULL_PORT_RANGE=-` avant d'exécuter le script pour réactiver l'ancien
comportement.

### Ajuster finement les options

- `FULL_SCRIPT_TIMEOUT`, `FULL_MAX_RETRIES` et `FULL_HOST_TIMEOUT` peuvent être
  surchargés pour rallonger ou réduire les garde-fous sans perdre le profil
  complet :

  ```bash
  FULL_HOST_TIMEOUT=20m FULL_SCRIPT_TIMEOUT=45s SCAN_PROFILE=full ./run_scan.sh
  ```

- `FULL_PORT_RANGE` permet de redéfinir la plage scannée (par défaut `1-1024`).
- `FULL_INCLUDE_AGGRESSIVE=1` réactive automatiquement les scripts
  `exploit,brute` ainsi que `--script-args=unsafe=1` pour retrouver la couverture
  historique.

- `EXTRA_NMAP_ARGS="--min-parallelism 32" ./run_scan.sh` ajoute dynamiquement des
  options supplémentaires.
- Les profils `fast`/`balanced` exposent aussi leurs overrides (`FAST_TOP_PORTS`,
  `BALANCED_PORT_RANGE`, etc.).

Résultat : vous pouvez choisir la vitesse désirée tout en conservant, par
défaut, le scan FULL SOC demandé.

#### Utiliser `profiles.d/` pour partager vos presets

Les overrides précédents sont disponibles dans `profiles.d/*.env`. Exportez
simplement `SCAN_PROFILE=fast` (ou `balanced`, `full`, `aggressive`) pour
qu'ils soient chargés automatiquement. Chaque fichier contient les variables
pertinentes (`*_PORT_RANGE`, `*_SCRIPT_TIMEOUT`, `EXTRA_NMAP_ARGS`, etc.).

Ajoutez vos propres presets (ex. `dmz.env`, `webapps.env`) pour documenter vos
scénarios SOC : `run_scan.sh` chargera n'importe quel `.env` portant le même nom
que la valeur de `SCAN_PROFILE`.

### Analyse IA automatique après chaque scan

- Une fois le JSON généré, `run_scan.sh` déclenche automatiquement
  `../ai_engine/analyse_scan.py` afin de produire le score, l'explication XAI,
  `logs/ia_events.log`, `/var/log/trusted_ai_soc_lite.log` et
  `../audit/ia_decisions.json`.
- Exportez `AI_AUTORUN=0` si vous voulez désactiver cette étape (tests unitaires,
  exécution hors IA, etc.).
- Chemins personnalisables :

  | Variable | Effet |
  | --- | --- |
  | `AI_ENGINE_DIR` | Répertoire contenant `analyse_scan.py` et le `venv`. |
  | `AI_MODEL_PATH` | Modèle IA à charger (par défaut `ai_engine/models/model.pkl`). |
  | `AI_LOG_FILE` | Journal local IA (par défaut `ai_engine/logs/ia_events.log`). |
  | `AI_AUDIT_FILE` | Historique structuré (par défaut `../audit/ia_decisions.json`). |

- Si un `venv` est présent dans `ai_engine/venv`, il est automatiquement
  activé avant l'exécution. Sinon, le Python système est utilisé.
- En cas d'erreur IA, le scanner affiche un message explicite mais conserve les
  rapports XML/JSON pour permettre le diagnostic.
- Nouveaux toggles disponibles :
  - `AI_DISABLE_SHAP=1` ou `AI_DISABLE_LIME=1` pour accélérer les tests ;
  - `AI_TI_OFFLINE=1` pour forcer le mode Threat Intelligence hors-ligne ;
  - `AI_SCAN_HISTORY=/chemin` pour personnaliser le fichier d'historique local.

### Brancher OpenVAS / Greenbone

Le dossier `openvas_integration/` contient un script `launch_openvas_scan.py`
qui crée une tâche GVM, déclenche le scan « Full and Fast » et exporte le
rapport XML directement dans `reports/`. Il réutilise `targets.txt`, ce qui
permet d'exécuter Nmap **et** OpenVAS sur le même périmètre avant d'alimenter
`ai_engine/`.

1. Installez `python-gvm` (`pip install python-gvm`).
2. Exportez les identifiants GVM (`--user`, `--password`).
3. Lancez :
   ```bash
   cd /opt/trusted_ai_soc_lite/nmap_scanner/openvas_integration
   python3 launch_openvas_scan.py --user admin --password '***'
   ```
4. Convertissez ensuite le rapport en JSON pour enrichir l'IA (les champs CVE / CVSS
   sont déjà pris en charge par `feature_engineering.py`).

> 💡 Vous pouvez enchaîner `run_scan.sh` puis `launch_openvas_scan.py` dans un même
> service `systemd` pour disposer d'une vision complète (Nmap + OpenVAS) avant la
> phase IA/XAI.

### Réponse automatique (response_engine)

- Exportez `RESPONSE_AUTORUN=1` pour lancer `../response_engine/responder.py`
  juste après l'analyse IA.
- Par défaut, le responder lit `ai_engine/logs/ia_events.log`, applique la
  politique (blocage UFW, e-mail) puis met à jour `../audit/response_actions.json`.
- Variables utiles :

  | Variable | Effet |
  | --- | --- |
  | `RESPONSE_ENGINE_DIR` / `RESPONDER_SCRIPT` | Chemins personnalisés du responder. |
  | `RESPONSE_ALERT_EMAIL` ou `SOC_ALERT_EMAIL` | Destinataire des alertes `high/critical`. |
  | `RESPONDER_DISABLE_EMAIL` / `RESPONDER_DISABLE_UFW` | Désactive un canal lors des tests. |
  | `RESPONDER_DRY_RUN` | Simule les actions (utile sur un poste sans `ufw`). |
  | `RESPONDER_EXTRA_ARGS` | Ajoute des arguments supplémentaires (`"--mailto csirt@example.com"`). |

- Les actions réalisées apparaissent dans
  `response_engine/actions.log` et `audit/response_actions.json`.

### Structure des rapports JSON produits

`parse_nmap.py` enrichit maintenant la sortie avec les résultats NSE, ce qui
permet d'exploiter immédiatement les preuves de vulnérabilités dans l'IA.

```jsonc
{
  "metadata": {
    "scanner": "nmap",
    "args": "...",
    "start": "2025-11-17T14:05:00Z",
    "elapsed": 32.51,
    "hosts_up": 1,
    "hosts_total": 1,
    "scan_type": "syn"
  },
  "hosts": [
    {
      "address": "192.168.1.10",
      "hostname": "server-lab",
      "status": "up",
      "os": "Linux 5.10",
      "accuracy": 93,
      "services": [
        {
          "protocol": "tcp",
          "portid": "22",
          "state": "open",
          "service": {"name": "ssh", "product": "OpenSSH", "version": "7.4"},
          "scripts": [
            {
              "id": "ssh2-enum-algos",
              "output": "(truncated)",
              "elements": [...],
              "tables": [...]
            }
          ]
        }
      ],
      "scripts": [
        {
          "id": "vulners",
          "output": "CVE-2021-41773 (CVSS 7.5)",
          "tables": [{"cve": "CVE-2021-41773", "cvss": "7.5"}]
        }
      ]
    }
  ]
}
```

Chaque bloc `scripts` contient :

- `id` : identifiant du script NSE exécuté ;
- `output` : synthèse textuelle affichée par Nmap ;
- `elements` : liste clé/valeur simple (utile pour les flags booléens) ;
- `tables` : dictionnaires imbriqués lorsque Nmap fournit des tableaux (ex. CVE,
  suites TLS, comptes anonymes, etc.).

Ces informations alimentent directement les features IA (CVE détectées, suites
faibles, anonymat FTP, etc.) sans avoir à relancer Nmap.

## Ce que vous pouvez faire avec ce dépôt Nmap

Ce module constitue la **brique "collecte réseau"** du projet TRUSTED AI SOC LITE. Une
fois installé, vous pouvez :

1. **Cartographier rapidement** les hôtes présents sur un sous-réseau (ping sweep).
2. **Établir un inventaire des services** exposés (ports TCP/UDP, bannières, versions).
3. **Détecter les dérives** (ports ouverts inattendus, nouveaux hôtes, services non
   conformes aux durcissements attendus).
4. **Produire des rapports XML/JSON** compatibles avec l'IA interne (`ai_engine`)
   pour scoring, priorisation et explications XAI.
   complète (détection → explication → réponse).
6. **Automatiser vos contrôles** grâce à cron/systemd, en conservant les traces dans
   `reports/` pour audit ou relecture.

## Catalogue de modes de scan utiles

Adaptez les commandes ci-dessous (interface réseau, plage d'adresses, options) à
votre périmètre. Tous les exemples supposent que vous êtes dans
`/opt/trusted_ai_soc_lite/nmap_scanner`.

| Objectif | Commande | Notes |
| --- | --- | --- |
| Découverte rapide des hôtes | `nmap -sn -iL targets.txt` | Ping sweep sans détail de ports. |
| Scan TCP standard | `nmap -sS -p 1-1024 -iL targets.txt` | SYN scan rapide sur 1-1024, nécessite sudo. |
| Inventaire complet | `nmap -sS -sV -O -p- -iL targets.txt` | Détection services/OS sur tous les ports. |
| Scan UDP ciblé | `sudo nmap -sU -p 53,67,123 -iL targets.txt` | Utile pour DNS, DHCP, NTP. |
| Scripts NSE vulnérabilités | `nmap -sV --script vuln -iL targets.txt` | Cherche les vulnérabilités connues. |
| Détection version + SSL/TLS | `nmap -sV --script ssl-enum-ciphers -p 443 -iL targets.txt` | Analyse des suites chiffrées. |
| Performance contrôlée | `nmap -sS -T2 -iL targets.txt` | Plus lent mais discret (péri. sensible). |
| Mode hors réseau (depuis fichier) | `nmap -iL targets.txt -oX reports/scan.xml && python3 parse_nmap.py reports/scan.xml reports/scan.json` | Utilise directement les scripts du dépôt. |

💡 Vous pouvez décliner `run_scan.sh` en plusieurs profils (ex. `run_scan_full.sh`,
`run_scan_udp.sh`) selon les besoins, chaque script pointant vers un sous-dossier
`reports/` différent pour conserver l'historique.

## Profils de scans avancés pour la chasse aux vulnérabilités

Les commandes suivantes reprennent exactement les profils recommandés pour une
détection poussée (SOC / Red Team). Remplacez `targets.txt` par votre propre
liste si nécessaire.

### 1. Scan vulnérabilités "full power" (recommandé)

```bash
nmap -sV -sC --script vuln,malware,auth,default,safe \
     -O --osscan-guess \
     --script-args=unsafe=1 \
     -oX reports/vuln_scan_$(date +%F_%H%M).xml \
     -iL targets.txt
```

- Combine détection de version, scripts NSE orientés vulnérabilités, fingerprint
  OS et tests supplémentaires "safe".
- Repère services obsolètes (OpenSSH, Apache, MySQL, etc.), mauvaises configs
  FTP/SSH/SMB, faiblesses SSL/TLS et signatures malware.

### 2. Variante très agressive (lab uniquement)

```bash
nmap -A -T4 \
     --script vuln,exploit,brute,auth \
     --script-args=unsafe=1 \
     -oX reports/aggressive_vuln_$(date +%F_%H%M).xml \
     -iL targets.txt
```

- Active le mode `-A` (OS + traceroute + scripts par défaut) et ajoute NSE
  exploit/brute-force. À utiliser uniquement sur des environnements contrôlés.

### 3. Extraction CVE automatique

```bash
nmap -sV --script vulners \
     -oX reports/cve_scan_$(date +%F_%H%M).xml \
     -iL targets.txt
```

- Produit directement les CVE et CVSS liés aux versions détectées.
- Idéal pour alimenter votre moteur IA (features CVE + score).

### 4. Ultimate SOC Scan (intégré à `run_scan.sh`)

```bash
nmap -sV -sC -O --osscan-guess -T4 \
     --script "default,vuln,exploit,auth,malware,brute,safe" \
     --script-args=unsafe=1 \
     -oX reports/full_soc_scan_$(date +%F_%H%M).xml \
     -iL targets.txt
```

- Couvre la découverte complète, la recherche de vulnérabilités, les tests
  d'authentification et quelques scénarios d'exploitation non destructifs.
- C'est le profil par défaut utilisé par `run_scan.sh`.

## Comprendre les avertissements « sendto: Network is unreachable »

Lorsque vous scannez un sous-réseau complet (`192.168.1.0/24` par exemple),
certains scripts NSE "broadcast" découvrent des adresses supplémentaires via
IGMP/MDNS/UPnP. Nmap essaie alors de contacter ces hôtes, mais si votre machine
n'a pas de route valide (ou si l'hôte a quitté le réseau), le noyau renvoie :

```
sendto in send_ip_packet_sd: sendto(5, ..., 192.168.1.172, 28728) => Network is unreachable
```

💡 **Ce n'est pas une erreur fatale.** Le scan continue, les rapports XML/JSON
sont générés et les services réellement accessibles (ex. `127.0.0.1`, votre IP
locale, les hôtes actifs) sont analysés normalement.

Pour vérifier que tout fonctionne :

1. Observez les messages `[INFO]` / `[OK]` en fin de `run_scan.sh` ;
2. Vérifiez que `reports/full_soc_scan_*.xml` et `*.json` existent et
   contiennent vos hôtes ;
3. Contrôlez la présence des sections `PORT`, `Service Info`, `Host script
   results`, etc. dans la sortie Nmap.

Si vous souhaitez réduire le bruit :

- Limitez `targets.txt` à des IP connues et accessibles ;
- Exportez `AUTO_TARGET_DISCOVERY=0` pour empêcher l'ajout automatique
  d'adresses ;
- Ajustez le profil (ex. supprimer `broadcast-*` des scripts NSE) si vous
  n'avez pas besoin de découverte passive.

Ces messages deviennent utiles lorsqu'ils changent soudainement (ex. un nouvel
hôte 192.168.1.180 apparaît puis disparaît), car ils reflètent l'activité
réseau détectée par les scripts.

## Tests & validations

- **Test à blanc** : ajoutez `scanme.nmap.org` dans `targets.txt` puis lancez `./run_scan.sh`. Vous devez obtenir un couple de fichiers XML/JSON.
- **Parser seul** : `python3 parse_nmap.py reports/scan_test.xml reports/scan_test.json` pour valider la conversion sur un fichier existant.
- **Intégration IA** : copiez les fichiers JSON vers `ai_engine/` ou pointez `analyse_scan.py` sur le dossier `reports/` pour vérifier l'enchaînement complet.

### Dépannage rapide

| Symptôme | Cause probable | Correctif |
| --- | --- | --- |
| `./run_scan.sh` s'arrête immédiatement avec `[ERREUR] nmap n'est pas installé.` | Le paquet `nmap` n'est pas présent dans la machine (ou pas dans le `PATH`). | Installez-le via `sudo apt install nmap`, puis relancez `nmap --version` pour vérifier. |
| `python3: command not found` lors de `parse_nmap.py`. | Paquet `python3` manquant. | `sudo apt install python3 python3-venv` puis rejouer le script. |
| Pas de fichier JSON généré. | Le scan Nmap n'a pas fini (profil trop agressif, hôtes injoignables) ou a été interrompu. | Essayez `SCAN_PROFILE=fast ./run_scan.sh` pour valider la chaîne, puis revenez à `full`. Vérifiez aussi que les hôtes listés dans `targets.txt` sont atteignables. |
| Messages `sendto ... Network is unreachable` en boucle. | Des IP découvertes via broadcast ne sont pas routables depuis votre machine. | Normal : limitez `targets.txt` ou exportez `AUTO_TARGET_DISCOVERY=0` si vous ne souhaitez que vos cibles manuelles. |

## Automatisation (optionnel)

Pour exécuter le scan chaque heure via cron :

```bash
sudo crontab -e
0 * * * * /opt/trusted_ai_soc_lite/nmap_scanner/run_scan.sh >/var/log/nmap_scanner.cron.log 2>&1
```

Ou créez un timer `systemd` si vous préférez un contrôle plus fin (journalisation, dépendances réseau, etc.).
