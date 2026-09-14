# Runbook 04 — Configurer l'intégration Cyberwatch dans XSIAM

Objectif : brancher le simulateur Cyberwatch comme 2e source de vulnérabilités. Deux chemins possibles selon disponibilité du content pack.

⚠️ **Cyberwatch n'est PAS listé** dans les intégrations built-in Exposure Management (contrairement à Rapid7). Deux plans :

- **Plan A** : content pack **"Cyberwatch (Partner Contribution)"** installé via Marketplace → configuration UI classique
- **Plan B** : passer par la **Vulnerability Ingest API** de Cortex (script Python qui pousse assets + vulns au format normalisé)

## Plan A — Content pack Partner Contribution

### 4.1A — Installer le content pack

XSIAM → **Marketplace** → chercher **"Cyberwatch"**.

- Si trouvé (label "Partner Contribution") → Install
- Si introuvable → passer au Plan B

### 4.2A — Ajouter l'intégration

XSIAM → **Settings** → **Data Sources & Integrations** → **+ Add integration** → chercher "Cyberwatch".

Formulaire :

| Champ | Valeur |
|-------|--------|
| **Name** | `BusinessCorp-Cyberwatch-Demo` |
| **Server URL / Master URL** | `https://cyberwatch-simulator-<hash>-ew.a.run.app` |
| **Access Key** | `cw-businesscorp-demo-access` |
| **Secret Key** | `cw-BusinessCorp-Demo-S3cret-2026` |
| **Fetch assets and vulnerabilities** | ✅ Coché |
| **First fetch time** | `7 days` |
| **Fetch interval** | `1 hour` |

Test → Connect.

### 4.3A — Validation (identique Rapid7)

```xql
config timeframe = 24h
| dataset = cyberwatch_assets_raw
| limit 5
```
*(nom exact à confirmer via `datasets` command)*

```xql
config timeframe = 24h
| dataset = uvm_findings
| filter source = "Cyberwatch" and cve = "CVE-2022-30190"
| limit 5
```

## Plan B — Vulnerability Ingest API

Si le content pack Cyberwatch n'est pas disponible, on utilise l'API générique d'ingestion vulnérabilités.

### 4.1B — Récupérer les credentials API XSIAM

XSIAM → **Settings** → **API Keys** → **New Key** :

- Name : `BusinessCorp-VulnIngest-Demo`
- Security Level : **Advanced**
- Role : rôle avec permission **Manage Vulnerabilities** + **API Access**

Noter :
- API Key ID (ex : `123`)
- API Key (secret longue chaîne)
- FQDN API (ex : `api-<tenant>.xdr.eu.paloaltonetworks.com`)

### 4.2B — Script d'ingestion (Python)

Créer `C:\Users\jcourtemanch\Documents\dev\demo\sims\ingest-cyberwatch-to-xsiam.py` :

```python
"""
Bridge Cyberwatch sim → Cortex XSIAM Vulnerability Ingest API.
Poll le sim Cyberwatch toutes les heures et push au format Cortex.
Non-prioritaire v1 — squelette à compléter si Plan A indisponible.
"""
import os
import requests
import hashlib
from datetime import datetime, timezone

# --- Config ---
CW_URL = os.environ["CW_SIM_URL"]  # https://cyberwatch-simulator-<hash>-ew.a.run.app
CW_KEY = os.environ["CW_ACCESS_KEY"]
CW_SEC = os.environ["CW_SECRET_KEY"]

XSIAM_FQDN = os.environ["XSIAM_API_FQDN"]  # api-<tenant>.xdr.eu.paloaltonetworks.com
XSIAM_KEY_ID = os.environ["XSIAM_API_KEY_ID"]
XSIAM_KEY = os.environ["XSIAM_API_KEY"]

VENDOR = "Cyberwatch"
PRODUCT = "Cyberwatch Vulnerability Manager"

# --- 1. Pull assets + vulns from Cyberwatch sim ---
def fetch_cyberwatch_assets():
    r = requests.get(
        f"{CW_URL}/api/v3/vulnerabilities/servers",
        auth=(CW_KEY, CW_SEC),
        params={"per_page": 100},
    )
    r.raise_for_status()
    return r.json()

def fetch_asset_detail(server_id):
    r = requests.get(
        f"{CW_URL}/api/v3/vulnerabilities/servers/{server_id}",
        auth=(CW_KEY, CW_SEC),
    )
    r.raise_for_status()
    return r.json()

# --- 2. Normalize to Cortex Vulnerability Ingest schema ---
# Reference: Cortex XSIAM Platform APIs → Vulnerability Management APIs
def build_ingest_payload(cw_servers_detail):
    records = []
    for srv in cw_servers_detail:
        for cve_entry in srv.get("cve_announcements", []):
            records.append({
                "asset": {
                    "hostname": srv["hostname"],
                    "ip_address": srv.get("last_communication_ip") or srv.get("addresses", [{}])[0].get("ip"),
                    "os_name": srv.get("os", {}).get("name"),
                    "os_version": srv.get("os", {}).get("version"),
                    "vendor": VENDOR,
                    "product": PRODUCT,
                    "unique_identifier": f"cw-{srv['id']}",
                },
                "vulnerability": {
                    "cve": cve_entry["cve_code"],
                    "first_seen": cve_entry.get("detected_at"),
                    "last_seen": datetime.now(timezone.utc).isoformat(),
                    # CVSS/EPSS/KEV seront auto-enrichis par Cortex Vulnerability Intelligence
                },
            })
    return {"records": records}

# --- 3. Push to Cortex XSIAM Vulnerability Ingest API ---
def push_to_xsiam(payload):
    # NOTE: endpoint exact à vérifier dans la doc Cortex — placeholder
    headers = {
        "x-xdr-auth-id": str(XSIAM_KEY_ID),
        "Authorization": XSIAM_KEY,
        "Content-Type": "application/json",
    }
    endpoint = f"https://{XSIAM_FQDN}/public_api/v1/vulnerability_management/ingest"
    r = requests.post(endpoint, headers=headers, json=payload)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    servers = fetch_cyberwatch_assets().get("data", [])
    details = [fetch_asset_detail(s["id"]) for s in servers]
    payload = build_ingest_payload(details)
    print(f"Pushing {len(payload['records'])} records to XSIAM...")
    result = push_to_xsiam(payload)
    print(result)
```

**⚠️ Le endpoint exact `/public_api/v1/vulnerability_management/ingest`** est un placeholder — à vérifier dans la documentation Cortex XSIAM Platform APIs. Voir `validation/open-questions-tenant.md` question 8.

### 4.3B — Planifier l'exécution

Sur poste de démo (ou VM dédiée), Task Scheduler Windows toutes les heures :

```powershell
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\Users\jcourtemanch\Documents\dev\demo\sims\ingest-cyberwatch-to-xsiam.py"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName "XSIAM-Cyberwatch-Ingest" -Action $action -Trigger $trigger
```

Alternative : conteneuriser le script + Cloud Run Job + Cloud Scheduler pour rester 100% GCP.

### 4.4B — Validation

```xql
config timeframe = 24h
| dataset = uvm_findings
| filter vendor = "Cyberwatch"
| limit 20
```

Vérifier :
- Records créés avec `findings_source = "Third Party Scanner"`
- Assets créés avec `asset_type = "Generic Device"`
- Enrichissement CVSS/EPSS/KEV effectif

## Comparer Rapid7 vs Cyberwatch — vérifier la dédup

Après les 2 intégrations, vérifier que la dédup fonctionne :

```xql
config timeframe = 24h
| dataset = uvm_findings
| filter cve = "CVE-2021-44228" and host_name = "srv-web-01.business.org"
| comp count() as dup_count
```

Attendu : `dup_count = 1` (Cortex a dédupliqué même si Rapid7 ET Cyberwatch la voient).

Si `dup_count > 1` → vérifier le mapping `unique_identifier` de chaque source.

## Notes

- Le talk track de l'Acte 2 valorise cette dédup explicitement — c'est un différenciateur clé de la plateforme
- Le sim Cyberwatch a EPSS natif dans son catalogue — utilisable comme "cross-check" pour valider que Cortex utilise sa propre source EPSS (Vulnerability Intelligence) et pas celle du scanner

## Suivant

→ [`05-create-tags-and-groups.md`](05-create-tags-and-groups.md)
