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
2. exécute un **scan SOC complet** (détection de version, scripts NSE vuln/exploit/malware, fingerprinting OS) ;
3. génère `reports/full_soc_scan_YYYY-MM-DD_HHMMSS.xml` puis appelle `parse_nmap.py` (qui écrit automatiquement le JSON associé) ;
4. livre un rapport prêt à être ingéré par l'IA et Wazuh.

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
5. **Alimenter Wazuh** via les logs IA enrichis afin d'avoir une traçabilité SOC
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

## Automatisation (optionnel)

Pour exécuter le scan chaque heure via cron :

```bash
sudo crontab -e
0 * * * * /opt/trusted_ai_soc_lite/nmap_scanner/run_scan.sh >/var/log/nmap_scanner.cron.log 2>&1
```

Ou créez un timer `systemd` si vous préférez un contrôle plus fin (journalisation, dépendances réseau, etc.).
