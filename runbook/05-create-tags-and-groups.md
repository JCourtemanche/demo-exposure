# Runbook 05 — Tags et Asset Groups (v1.1, préfixe `EM-demo-*`)

Objectif : matérialiser les 7 zones logiques et les 4 groupes owner via tags + groupes dynamiques XSIAM. Ces groupes seront ensuite référencés par les compensating controls (runbook 06) et les 8 Vulnerability Policies (runbook 07).

⚠️ **Environnement mutualisé** — tenant XSIAM PANW partagé. Tous les asset groups créés ici utilisent le préfixe `EM-demo-*` pour éviter les collisions avec d'autres démos.

## Étape 5.1 — Format des tags (Q1 résolue)

Le format tag natif Cortex est **`key:value`** (séparateur `:`, pas `=`), stocké dans `xdm.asset.tags` sous `xdm.asset.normalized_fields`.

**Format Business Corp v1** :
- `zone:dmz-web`, `zone:tier0`, `zone:cicd`, etc.
- `owner:secops`, `owner:it-corp`, `owner:appdev`, `owner:devops`
- `tier:0`, `tier:1`, `tier:2`, `tier:3`

## Étape 5.2 — Tagger les 16 actifs focus

Deux approches selon vos préférences :

### Approche 1 — UI (16 actifs, ~20 min)

XSIAM → **Inventory** → **Assets** → filtrer `xdm.host.hostname contains "business.org"`.

Pour chaque asset de `infra/asset-inventory.md` :
1. Cliquer l'asset → panneau détail
2. Onglet **Tags** → **+ Add Tag**
3. Ajouter : `zone:<zone>`, `tier:<tier>`, `owner:<owner_group>` (format `key:value` avec `:`)

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
    # esxi-01 et nas-01 retirés en v1 (Cyberwatch-only)
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
        f"zone:{a['zone']}",
        f"tier:{a['tier']}",
        f"owner:{a['owner']}",
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

## Étape 5.3 — Créer les 7 groupes dynamiques par zone

XSIAM → **Inventory** → **Assets** → **Groups** → **+ Add Group**.

Pour chaque zone, créer un groupe **Dynamic** avec le filtre approprié (format tag `key:value` confirmé Q1) :

| Nom du groupe | Type | Filtre |
|---------------|------|--------|
| `EM-demo-zone-dmz-web` | Dynamic | `xdm.asset.tags.zone = "dmz-web"` |
| `EM-demo-zone-dmz-edge` | Dynamic | `xdm.asset.tags.zone = "dmz-edge"` |
| `EM-demo-zone-tier0` | Dynamic | `xdm.asset.tags.zone = "tier0"` |
| `EM-demo-zone-tier1` | Dynamic | `xdm.asset.tags.zone = "tier1"` |
| `EM-demo-zone-infra` | Dynamic | `xdm.asset.tags.zone = "infra"` |
| `EM-demo-zone-cicd` | Dynamic | `xdm.asset.tags.zone = "cicd"` |
| `EM-demo-zone-cloud` | Dynamic | `xdm.asset.tags.zone = "cloud"` |

⚠️ La syntaxe exacte du filtre dépend de l'UI XSIAM — si `xdm.asset.tags.zone = "dmz-web"` ne fonctionne pas, essayer `tags contains "zone:dmz-web"` (approche substring). Voir Q1 pour le formatting Rapid7 natif.

## Étape 5.4 — Créer les 4 groupes dynamiques par owner

| Nom du groupe | Filtre |
|---------------|--------|
| `EM-demo-owner-secops` | `tags contains "owner:secops"` |
| `EM-demo-owner-it-corp` | `tags contains "owner:it-corp"` |
| `EM-demo-owner-appdev` | `tags contains "owner:appdev"` |
| `EM-demo-owner-devops` | `tags contains "owner:devops"` |

## Étape 5.5 — Créer le groupe transverse `EM-demo-business-tier0`

Utilisé par la Vulnerability Policy R3 "Angle mort interne" (runbook 07) pour escalader les cases Tier 0.

| Nom | Filtre |
|-----|--------|
| `EM-demo-business-tier0` | `xdm.asset.tags.tier = "0"` |

Attendu : 3 assets (srv-vpn, srv-ad-01, srv-adfs-01).

## Étape 5.6 — Attribution "Business Criticality" (optionnel, boost narratif)

XSIAM → **Inventory** → **Assets** → sélectionner les assets Tier 0 → **Set Business Criticality** → **Critical**.

Impact : ils remontent dans le filtre "Low Business Impact" du funnel Command Center → deviennent visibles dans les cases prioritaires.

## Étape 5.7 — Validation

XSIAM → **Inventory** → **Assets** → **Groups** :
- Compter : 7 zones + 4 owners + 1 tier0 = **12 groupes** `EM-demo-*` créés
- Chaque groupe montre un `member count` cohérent (v1 Rapid7 only) :
  - `EM-demo-zone-dmz-web` : 3 (srv-web-01, srv-web-02, srv-portail)
  - `EM-demo-zone-dmz-edge` : 2 (srv-vpn, smtp-relay)
  - `EM-demo-zone-tier0` : 2 (srv-ad-01, srv-adfs-01)
  - `EM-demo-zone-tier1` : 5 (srv-db-01/02, srv-mail, srv-fs-01, srv-monitoring)
  - `EM-demo-zone-infra` : 1 (srv-print) — v1 sans esxi-01/nas-01
  - `EM-demo-zone-cicd` : 1 (srv-ci)
  - `EM-demo-zone-cloud` : 2 (cloud-lb-01, cloud-app-01)
  - `EM-demo-owner-secops` : ~4 (Tier 0 + VPN)
  - `EM-demo-owner-it-corp` : ~6 (Tier 1 + infra + smtp)
  - `EM-demo-owner-appdev` : 3 (DMZ web)
  - `EM-demo-owner-devops` : ~3 (CI + cloud)
  - `EM-demo-business-tier0` : 3 (srv-vpn, srv-ad-01, srv-adfs-01)

Attendre 15-30 min pour propagation complète (Cortex documente "immediate for new/updated assets; a few hours for previously untouched assets").

XQL de validation :
```xql
config timeframe = 1h
| dataset = asset_groups
| filter group_name startswith "EM-demo-"
```

## Suivant

→ [`06-declare-compensating-controls.md`](06-declare-compensating-controls.md)
