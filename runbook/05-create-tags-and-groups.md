# Runbook 05 — Tags et Asset Groups

Objectif : matérialiser les 9 zones logiques (`zone-*`) et les 4 groupes owner (`grp-owner-*`) via tags + groupes dynamiques XSIAM. Ces groupes seront ensuite référencés par les compensating controls (runbook 06) et la Vulnerability Policy (runbook 07).

## Étape 5.1 — Valider le format de tag dans votre tenant

⚠️ **Prérequis** : avoir répondu à la question 1 de `validation/open-questions-tenant.md` (format key=value vs flat).

**Deux hypothèses possibles** :
- **A. Key=value** : `zone=dmz-web`, `tier=0`, `owner=secops` → configuration ci-dessous "Approche A"
- **B. Flat labels** : `dmz-web`, `tier-0`, `owner-secops` → configuration ci-dessous "Approche B"

Adapter les commandes de tagging en conséquence.

## Étape 5.2 — Tagger les 25 actifs focus

Deux approches selon vos préférences et le format tenant :

### Approche 1 — UI (25 actifs, ~30 min)

XSIAM → **Inventory** → **Assets** → filtrer `host_name contains business.org`.

Pour chaque asset de `infra/asset-inventory.md` :
1. Cliquer l'asset → panneau détail
2. Onglet **Tags** → **+ Add Tag**
3. Ajouter : `zone=<zone>`, `tier=<tier>`, `owner=<owner_group>` (adapter au format tenant)

Fastidieux mais pédagogique — recommandé si on veut vraiment comprendre où se placent les tags dans l'UI.

### Approche 2 — API bulk (recommandée production démo, ~5 min)

Créer `C:\Users\jcourtemanch\Documents\dev\demo\sims\bulk-tag-assets.py` :

```python
"""
Bulk tagging des 25 assets focus Business Corp.
⚠️ Endpoint API tags à valider dans le tenant (open question #1).
"""
import os
import requests

XSIAM_FQDN = os.environ["XSIAM_API_FQDN"]
XSIAM_KEY_ID = os.environ["XSIAM_API_KEY_ID"]
XSIAM_KEY = os.environ["XSIAM_API_KEY"]

HEADERS = {
    "x-xdr-auth-id": str(XSIAM_KEY_ID),
    "Authorization": XSIAM_KEY,
    "Content-Type": "application/json",
}

# Source de vérité : infra/asset-inventory.md
ASSETS = [
    # Assets natifs des 2 sims (hostnames validés via WebFetch du code)
    {"hostname": "srv-web-01.business.org",     "zone": "dmz-web",       "tier": "1", "owner": "appdev"},
    {"hostname": "srv-web-02.business.org",     "zone": "dmz-web",       "tier": "1", "owner": "appdev"},
    {"hostname": "srv-vpn.business.org",        "zone": "dmz-edge",      "tier": "0", "owner": "secops"},
    {"hostname": "srv-ad-01.business.org",      "zone": "tier0",         "tier": "0", "owner": "secops"},
    {"hostname": "srv-db-01.business.org",      "zone": "tier1",         "tier": "1", "owner": "it-corp"},
    {"hostname": "srv-db-02.business.org",      "zone": "tier1",         "tier": "1", "owner": "it-corp"},
    {"hostname": "srv-mail.business.org",       "zone": "tier1",         "tier": "1", "owner": "it-corp"},
    {"hostname": "srv-fs-01.business.org",      "zone": "tier1",         "tier": "1", "owner": "it-corp"},
    {"hostname": "srv-monitoring.business.org", "zone": "tier1",         "tier": "2", "owner": "it-corp"},
    {"hostname": "esxi-01.business.org",        "zone": "infra",         "tier": "1", "owner": "it-corp"},
    {"hostname": "nas-01.business.org",         "zone": "infra",         "tier": "2", "owner": "it-corp"},
    {"hostname": "srv-ci.business.org",         "zone": "cicd",          "tier": "1", "owner": "devops"},
    {"hostname": "cloud-lb-01.business.org",    "zone": "cloud",         "tier": "2", "owner": "devops"},
    {"hostname": "cloud-app-01.business.org",   "zone": "cloud",         "tier": "2", "owner": "devops"},
    # Personas partagées (hostnames à confirmer via dump discovery — format probable prénom.business.org)
    {"hostname": "alice.business.org",          "zone": "endpoints-win", "tier": "3", "owner": "it-corp"},
    {"hostname": "bob.business.org",            "zone": "endpoints-win", "tier": "3", "owner": "it-corp"},
    {"hostname": "charlie.business.org",        "zone": "devs-linux",    "tier": "3", "owner": "devops"},
    {"hostname": "david.business.org",          "zone": "devs-linux",    "tier": "3", "owner": "devops"},
    {"hostname": "emma.business.org",           "zone": "devs-linux",    "tier": "3", "owner": "devops"},
    {"hostname": "flora.business.org",          "zone": "devs-linux",    "tier": "3", "owner": "devops"},
    # Extra assets custom (ajoutés via config/business-corp-config.yaml — voir runbook 02b)
    {"hostname": "srv-portail.business.org",    "zone": "dmz-web",       "tier": "1", "owner": "appdev"},
    {"hostname": "srv-adfs-01.business.org",    "zone": "tier0",         "tier": "0", "owner": "secops"},
    {"hostname": "srv-print.business.org",      "zone": "infra",         "tier": "3", "owner": "it-corp"},
    {"hostname": "smtp-relay.business.org",     "zone": "dmz-edge",      "tier": "2", "owner": "it-corp"},
]

def resolve_asset_id(hostname):
    """Search asset by hostname, return asset_id."""
    # Endpoint à valider — hypothèse public API
    r = requests.post(
        f"https://{XSIAM_FQDN}/public_api/v1/assets/search",
        headers=HEADERS,
        json={"filter": {"host_name": hostname}},
    )
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0]["id"] if results else None

def apply_tags(asset_id, tags):
    """Apply tags to asset — endpoint à valider (open question #1)."""
    # Hypothèse : format key=value via API dédiée
    r = requests.post(
        f"https://{XSIAM_FQDN}/public_api/v1/assets/{asset_id}/tags",
        headers=HEADERS,
        json={"tags": tags},
    )
    r.raise_for_status()

for a in ASSETS:
    asset_id = resolve_asset_id(a["hostname"])
    if not asset_id:
        print(f"⚠️  Not found: {a['hostname']}")
        continue
    tags = [
        f"zone={a['zone']}",
        f"tier={a['tier']}",
        f"owner={a['owner']}",
    ]
    apply_tags(asset_id, tags)
    print(f"✅ Tagged {a['hostname']} ({asset_id}) with {tags}")
```

Lancer :
```powershell
$env:XSIAM_API_FQDN = "api-<tenant>.xdr.eu.paloaltonetworks.com"
$env:XSIAM_API_KEY_ID = "123"
$env:XSIAM_API_KEY = "<votre_secret>"
python bulk-tag-assets.py
```

## Étape 5.3 — Créer les 9 groupes dynamiques par zone

XSIAM → **Inventory** → **Assets** → **Groups** → **+ Add Group**.

Pour chaque zone, créer un groupe **Dynamic** avec le filtre approprié :

| Nom du groupe | Type | Filtre (Approche key=value) | Filtre (Approche flat) |
|---------------|------|------------------------------|-------------------------|
| `grp-zone-dmz-web` | Dynamic | `tags contains "zone=dmz-web"` | `tags contains "dmz-web"` |
| `grp-zone-dmz-edge` | Dynamic | `tags contains "zone=dmz-edge"` | `tags contains "dmz-edge"` |
| `grp-zone-tier0` | Dynamic | `tags contains "zone=tier0"` | `tags contains "tier0"` |
| `grp-zone-tier1` | Dynamic | `tags contains "zone=tier1"` | `tags contains "tier1"` |
| `grp-zone-infra` | Dynamic | `tags contains "zone=infra"` | `tags contains "infra"` |
| `grp-zone-cicd` | Dynamic | `tags contains "zone=cicd"` | `tags contains "cicd"` |
| `grp-zone-devs-linux` | Dynamic | `tags contains "zone=devs-linux"` | `tags contains "devs-linux"` |
| `grp-zone-endpoints-win` | Dynamic | `tags contains "zone=endpoints-win"` | `tags contains "endpoints-win"` |
| `grp-zone-cloud` | Dynamic | `tags contains "zone=cloud"` | `tags contains "cloud"` |

## Étape 5.4 — Créer les 4 groupes dynamiques par owner

| Nom du groupe | Filtre |
|---------------|--------|
| `grp-owner-secops` | `tags contains "owner=secops"` |
| `grp-owner-it-corp` | `tags contains "owner=it-corp"` |
| `grp-owner-appdev` | `tags contains "owner=appdev"` |
| `grp-owner-devops` | `tags contains "owner=devops"` |

## Étape 5.5 — Créer le groupe transverse `grp-business-tier0`

Utilisé par la Vulnerability Policy (runbook 07) pour escalader les cases Tier 0.

| Nom | Filtre |
|-----|--------|
| `grp-business-tier0` | `tags contains "tier=0"` |

Attendu : 3 assets (srv-vpn, srv-ad-01, srv-adfs-01).

## Étape 5.6 — Attribution "Business Criticality" (optionnel, boost narratif)

XSIAM → **Inventory** → **Assets** → sélectionner les assets Tier 0 → **Set Business Criticality** → **Critical**.

Impact : ils remontent dans le filtre "Low Business Impact" du funnel Command Center → deviennent visibles dans les cases prioritaires.

## Étape 5.7 — Validation

XSIAM → **Inventory** → **Assets** → **Groups** :
- Compter : 9 + 4 + 1 = 14 groupes créés
- Chaque groupe montre un `member count` cohérent :
  - `grp-zone-dmz-web` : 3
  - `grp-zone-dmz-edge` : 2
  - `grp-zone-tier0` : 2
  - `grp-zone-tier1` : 4
  - `grp-zone-infra` : 3 (esxi-01, nas-01, srv-print)
  - `grp-zone-cicd` : 2
  - `grp-zone-devs-linux` : 4 (personas partagées) + ~6 générés (selon ingestion)
  - `grp-zone-endpoints-win` : 2 (Alice, Bob) + volume selon ingestion
  - `grp-zone-cloud` : 2
  - `grp-business-tier0` : 3

Attendre 15-30 min pour propagation complète (Cortex documente "immediate for new/updated assets; a few hours for previously untouched assets").

XQL de validation :
```xql
config timeframe = 1h
| dataset = asset_groups
| filter group_name startswith "grp-"
```

## Suivant

→ [`06-declare-compensating-controls.md`](06-declare-compensating-controls.md)
