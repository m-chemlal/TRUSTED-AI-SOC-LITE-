# Intégration OpenVAS / Greenbone

Ce dossier fournit un exemple d'orchestration OpenVAS (GVM) pour compléter les
scans Nmap avec une analyse de vulnérabilités authentifiée.

## Pré-requis

- Greenbone Community Edition (manager + scanner) accessible depuis la machine
  SOC ;
- compte GVM avec droits de création de tâches ;
- Python 3.10+ avec `python-gvm` (`pip install python-gvm`).

## Script `launch_openvas_scan.py`

```bash
cd /opt/trusted_ai_soc_lite/nmap_scanner/openvas_integration
python3 launch_openvas_scan.py \
  --host 192.168.1.50 \
  --user admin --password '...'
```

Options principales :

| Option | Description |
| --- | --- |
| `--targets` | Fichier d'hôtes (par défaut `../targets.txt`). |
| `--config` | UUID du profil OpenVAS (Full and Fast = `d21f6c81-...`). |
| `--credential` | UUID d'un couple login/mot de passe pour lancer des scans authentifiés. |
| `--output` | Emplacement du rapport XML exporté (consommable par `ai_engine`). |

Le script :

1. lit les cibles (même format que `targets.txt`) ;
2. crée un `target` + une `task` GVM avec le profil choisi ;
3. déclenche le scan et récupère l'`report_id` ;
4. exporte le rapport XML dans `../reports/openvas_report.xml`.

Vous pouvez ensuite convertir ce rapport vers JSON via `gvm-cli` ou un parser
custom et l'injecter dans `ai_engine/feature_engineering.py` (les champs CVE/CVSS
sont déjà prévus pour accueillir d'autres sources que Nmap).

> 💡 Pour automatiser complètement le pipeline : ajoutez un cron ou un service
> `systemd` qui exécute `launch_openvas_scan.py` après `run_scan.sh`, puis placez
> le rapport JSON converti dans `/opt/trusted_ai_soc_lite/nmap_scanner/reports/`.
