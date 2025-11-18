# Wazuh Integration Pack for TRUSTED AI SOC LITE

This folder centralizes everything you need to hook the AI engine output into a Wazuh Manager/Agent stack on a single Debian host.  Each file is a ready-to-use template that you can copy into `/var/ossec/` (manager) or `/var/ossec/etc/` (agent) and adapt to your environment.

## Contents

| File | Where it goes | Purpose |
| ---- | ------------- | ------- |
| `ossec.local.conf` | `/var/ossec/etc/ossec.conf` (agent) | Adds the AI log (`/var/log/trusted_ai_soc_lite.log`) as a JSON monitored file. |
| `decoders/trusted_ai_soc_lite_decoder.xml` | `/var/ossec/etc/decoders/` (manager) | Parses the JSON payload and exposes `risk_score`, `risk_level`, `host`, `scan_id`, etc. |
| `rules/trusted_ai_soc_lite_rules.xml` | `/var/ossec/etc/rules/` (manager) | Maps risk levels to SOC severities (LOW → lvl3 … CRITICAL → lvl12) and tags alerts for dashboards. |
| `active-response/trusted_ai_block.sh` | `/var/ossec/active-response/bin/` (agent) | Example response hook to block the offending host with `ufw` and append the action to the SOC audit trail. |

## Quick deployment steps

1. **Copy the templates**
   ```bash
   sudo cp opt/trusted_ai_soc_lite/wazuh/ossec.local.conf /var/ossec/etc/ossec.conf.d/trusted_ai_soc_lite.conf
   sudo cp opt/trusted_ai_soc_lite/wazuh/decoders/trusted_ai_soc_lite_decoder.xml /var/ossec/etc/decoders/
   sudo cp opt/trusted_ai_soc_lite/wazuh/rules/trusted_ai_soc_lite_rules.xml /var/ossec/etc/rules/
   sudo cp opt/trusted_ai_soc_lite/wazuh/active-response/trusted_ai_block.sh /var/ossec/active-response/bin/
   sudo chmod +x /var/ossec/active-response/bin/trusted_ai_block.sh
   ```

2. **Restart the daemons**
   ```bash
   sudo systemctl restart wazuh-agent
   sudo systemctl restart wazuh-manager
   ```

3. **Trigger a scan** (`run_scan.sh`) and confirm that:
   * `/var/log/trusted_ai_soc_lite.log` receives fresh IA events.
   * Wazuh Dashboard shows the alerts under the *Security Events* tab (filter `rule.group: trusted_ai_soc_lite`).
   * For `risk_level = critical`, the active response script blocks the IP and writes to `/opt/trusted_ai_soc_lite/response_engine/actions.log` (create the file if needed).

## Customization tips

* **Different log path?** Update both `ossec.local.conf` and the AI automation block in `run_scan.sh` so the agent and IA agree on the destination.
* **Need email/Slack notifications?** Replace the `active-response` script with your preferred action (mail, webhook, ticket API).
* **Clustered Wazuh?** Deploy the decoder/rules files to the manager nodes only.  Agents only need the `ossec.conf` snippet and (optionally) the response script.
* **Testing:** use `sudo /var/ossec/bin/wazuh-logtest` and paste one of the AI JSON lines to verify decoding/rule matching before restarting production services.

With these files in place, every AI decision is ingested, scored, visualized, and can trigger containment directly from Wazuh.
