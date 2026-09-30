# Runbook 05 — Asset Groups dynamiques (v1.2, tags auto-ingérés par Cortex)

Objectif : matérialiser les 7 zones logiques et les 4 groupes owner via **groupes dynamiques XSIAM** qui filtrent sur les tags asset ingérés automatiquement par Cortex depuis le sim Rapid7. Ces groupes seront ensuite référencés par les compensating controls (runbook 06) et les 8 Vulnerability Policies (runbook 07).

⚠️ **Environnement mutualisé** — tenant XSIAM PANW partagé. Tous les asset groups créés ici utilisent le préfixe `EM-demo-*` pour éviter les collisions avec d'autres démos.

## 🎁 v1.2 — Auto-tagging via le sim (plus de bulk-tag manuel)

**Nouveauté v1.2** : le sim Rapid7 émet directement les tags Business Corp dans son API `GET /api/3/assets/<id>/tags`. Cortex les ingère nativement dans `xdm.asset.tags` — **plus besoin de l'étape manuelle de tagging** (l'ancienne étape 5.2 bulk-tag est **obsolète v1.2**).

Il suffit donc de :
1. Vérifier que les tags sont bien remontés (§ 5.1)
2. Créer les asset groups dynamiques (§ 5.2 → 5.4)

## Étape 5.1 — Vérifier que les tags Business Corp sont bien ingérés

Le sim Rapid7 émet 3 tags custom par asset focus (via `config/business-corp-config.yaml` section `asset_tags` + patch `apply-patches.py`) :
- `zone:<zone>` (ex : `zone:dmz-web`)
- `owner:<owner_group>` (ex : `owner:secops`)
- `tier:<0|1|2|3>`

Ces tags sont ingérés par Cortex dans `xdm.asset.tags` — format `{name: type}`, tous en type `custom`.

**Vérification XQL** :
```xql
config timeframe = 24h
| dataset = asset_inventory
| filter xdm.host.hostname contains "business.org"
| fields xdm.host.hostname, xdm.asset.tags
| limit 5
```

Attendu (exemple pour `srv-vpn.business.org`) :
```
xdm.asset.tags = {
  "Business Corp": "custom",         ← tag natif sim
  "site-1": "location",              ← tag natif sim
  "zone:dmz-edge": "custom",         ← tag Business Corp
  "owner:secops": "custom",          ← tag Business Corp
  "tier:0": "custom"                 ← tag Business Corp
}
```

Si les tags Business Corp sont absents :
- Vérifier `~/sims/Rapid7InsightVM-simul/simulator/generators/business_corp_overrides.py` contient `ASSET_TAGS`
- Vérifier `routes/assets.py` a bien été patché (marker `# BC-patch: append Business Corp custom tags`)
- Redéployer : `cd ~/sims/Rapid7InsightVM-simul && bash deploy-cloudrun.sh`
- Faire "Fetch Now" dans XSIAM et attendre ~15 min

## ~~Étape 5.2 — Tagger les 16 actifs focus~~ (OBSOLÈTE v1.2)

⚠️ **Cette étape est obsolète depuis v1.2** — les tags sont maintenant émis directement par le sim et auto-ingérés par Cortex. Voir § 5.1 pour la vérification.

<details>
<summary>Ancien contenu (bulk-tag manuel — conservé pour référence historique)</summary>

Pour un tenant client sans nos patches sim, ou pour ajouter des tags supplémentaires manuellement dans XSIAM :

### Approche 1 — UI

XSIAM → **Inventory** → **Assets** → filtrer `xdm.host.hostname contains "business.org"`.

Pour chaque asset :
1. Cliquer l'asset → panneau détail
2. Onglet **Tags** → **+ Add Tag**
3. Ajouter : `zone:<zone>`, `tier:<tier>`, `owner:<owner_group>`

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

</details>

## Étape 5.2 — Créer les 7 groupes dynamiques par zone

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

## Étape 5.3 — Créer les 4 groupes dynamiques par owner

| Nom du groupe | Filtre |
|---------------|--------|
| `EM-demo-owner-secops` | `tags contains "owner:secops"` |
| `EM-demo-owner-it-corp` | `tags contains "owner:it-corp"` |
| `EM-demo-owner-appdev` | `tags contains "owner:appdev"` |
| `EM-demo-owner-devops` | `tags contains "owner:devops"` |

## Étape 5.4 — Créer le groupe transverse `EM-demo-business-tier0`

Utilisé par la Vulnerability Policy R3 "Angle mort interne" (runbook 07) pour escalader les cases Tier 0.

| Nom | Filtre |
|-----|--------|
| `EM-demo-business-tier0` | `xdm.asset.tags.tier = "0"` |

Attendu : 3 assets (srv-vpn, srv-ad-01, srv-adfs-01).


## Étape 5.5 — Attribution "Business Criticality" (optionnel, boost narratif)

XSIAM → **Inventory** → **Assets** → sélectionner les assets Tier 0 → **Set Business Criticality** → **Critical**.

Impact : ils remontent dans le filtre "Low Business Impact" du funnel Command Center → deviennent visibles dans les cases prioritaires.

## Étape 5.6 — Validation

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
