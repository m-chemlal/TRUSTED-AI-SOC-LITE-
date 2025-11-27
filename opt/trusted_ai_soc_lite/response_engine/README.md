# response_engine/

Le dossier `response_engine/` orchestre les actions défensives déclenchées par les
décisions IA.

## Fichiers principaux

| Fichier | Rôle |
| --- | --- |
| `responder.py` | Lit `ai_engine/logs/ia_events.log`, applique les politiques (mail, blocage UFW) et met à jour `audit/response_actions.json`. |
| `ufw_actions.sh` | Helper Bash qui bloque/débloque des IP via `ufw` et journalise les actions dans `response_engine/actions.log`. |
| `mailer.py` | Fonction `send_alert()` minimaliste pour envoyer des notifications SMTP (paramétrable via variables d'environnement). |

## Installation rapide

```bash
cd /opt/trusted_ai_soc_lite/response_engine
chmod +x ufw_actions.sh responder.py mailer.py
```

Configurez ensuite les variables d'environnement SMTP si nécessaire :

```bash
export SOC_SMTP_HOST=smtp.gmail.com
export SOC_SMTP_PORT=587
export SOC_SMTP_USER=mon.compte@gmail.com
export SOC_SMTP_PASSWORD="mot_de_passe_application"
export SOC_SMTP_STARTTLS=1
export SOC_ALERT_EMAIL=soc-admin@example.com
```

## Utilisation

1. Assurez-vous que `ai_engine/analyse_scan.py` génère bien `logs/ia_events.log`.
2. Lancez le responder :
   ```bash
   python3 responder.py --mailto soc-admin@example.com
   ```
3. Options utiles :
   - `--dry-run` : ne bloque pas réellement l'IP, n'envoie pas d'e-mail (mais journalise).
   - `--disable-ufw` / `--disable-email` : désactive un canal spécifique.
   - `--state-file` : change l'emplacement du curseur pour ne pas retraiter les mêmes événements.

Chaque exécution ajoute des entrées structurées dans `audit/response_actions.json` et les actions
Bash sont visibles dans `response_engine/actions.log`.

## Intégration automatique

`nmap_scanner/run_scan.sh` peut appeler `responder.py` juste après l'analyse IA en exportant :

```bash
export RESPONSE_AUTORUN=1
export RESPONSE_ALERT_EMAIL=soc-admin@example.com
./run_scan.sh
```

Vous pouvez également créer un service `systemd` ou un cron qui exécute `responder.py` toutes les
x minutes pour surveiller le journal IA en continu.
