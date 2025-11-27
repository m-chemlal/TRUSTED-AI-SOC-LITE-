# Profils Nmap (`profiles.d`)

Ce dossier regroupe des *presets* prêts à l'emploi pour `run_scan.sh`. Chaque fichier `.env`
peut être chargé automatiquement en positionnant `SCAN_PROFILE=<nom>` avant d'exécuter le
script ou en exportant les variables définies à l'intérieur.

```
# Exemple : lancer un scan "balanced"
export SCAN_PROFILE=balanced
/opt/trusted_ai_soc_lite/nmap_scanner/run_scan.sh
```

Les variables déclarées dans les fichiers sont injectées dans l'environnement avant la
construction de la ligne de commande Nmap (ports, timeouts, scripts, etc.).

| Fichier | Description |
| --- | --- |
| `fast.env` | 200 ports les plus courants, scripts sûrs uniquement (`default,vuln,safe`). |
| `balanced.env` | Ports 1-2048 + scripts `auth` et `malware`, timeouts intermédiaires. |
| `full.env` | Profil SOC recommandé (ports 1-4096, scripts vuln/auth/malware). |
| `aggressive.env` | Profil laboratoire : tous les ports, scripts exploit/brute, `unsafe=1`. |

Vous pouvez créer vos propres presets (ex. `webapp.env`, `dmz.env`). Il suffit de copier un
fichier existant et d'ajuster les variables (port range, `EXTRA_NMAP_ARGS`, etc.).
