# Runbook 09 — Teardown / Reset entre démos

Objectif : nettoyer l'environnement après une démo pour :
- Réutiliser le tenant sans polluer avec des données stales
- Économiser le compute GCP
- Éviter que les compensating controls dérivent

Deux modes : **soft reset** (garder l'infra, purger les données) et **full teardown** (tout supprimer).

## Mode 1 — Soft reset (recommandé entre 2 démos)

À faire dans les 24 h après démo, pour préserver le setup.

### 1.1 — Suspendre les Cloud Run

```powershell
# Ramener à 0 les instances actives (économie compute)
gcloud run services update rapid7-nexpose-simulator --min-instances=0 --max-instances=0 --region=europe-west1
gcloud run services update cyberwatch-simulator --min-instances=0 --max-instances=0 --region=europe-west1
```

Pour réactiver avant la prochaine démo :
```powershell
gcloud run services update rapid7-nexpose-simulator --min-instances=0 --max-instances=2 --region=europe-west1
gcloud run services update cyberwatch-simulator --min-instances=0 --max-instances=2 --region=europe-west1
```

### 1.2 — Désactiver les intégrations XSIAM (au lieu de supprimer)

XSIAM → Settings → Data Sources & Integrations :
- Instance `BusinessCorp-Rapid7-Demo` → Toggle **Disable**
- Instance `BusinessCorp-Cyberwatch-Demo` → Toggle **Disable**

Cortex arrêtera les fetches, mais garde toute la configuration.

### 1.3 — Ne PAS supprimer

Garder tel quel :
- Asset Groups (14)
- Compensating Controls (4)
- Vulnerability Policies (2)
- Tags sur assets

Ces artefacts restent valides et prêts pour la prochaine démo.

### 1.4 — Optionnel : purger les vulnerability issues obsolètes

Si les données restent après désactivation et polluent la vue :

XSIAM → Vulnerability Issues → filtrer par asset `business.org` → sélectionner tout → **Mark as Resolved** (bulk action).

## Mode 2 — Full teardown (fin de cycle démo, changement client)

⚠️ Attention : opérations irréversibles.

### 2.1 — Supprimer les Cloud Run

```powershell
gcloud run services delete rapid7-nexpose-simulator --region=europe-west1 --quiet
gcloud run services delete cyberwatch-simulator --region=europe-west1 --quiet
```

### 2.2 — Supprimer les images Artifact Registry

```powershell
gcloud artifacts docker images delete europe-west1-docker.pkg.dev/<PROJECT_ID>/rapid7-nexpose-simulator/rapid7-nexpose-simulator --quiet
gcloud artifacts docker images delete europe-west1-docker.pkg.dev/<PROJECT_ID>/cyberwatch-simulator/cyberwatch-simulator --quiet
```

Ou supprimer les repos entiers :
```powershell
gcloud artifacts repositories delete rapid7-nexpose-simulator --location=europe-west1 --quiet
gcloud artifacts repositories delete cyberwatch-simulator --location=europe-west1 --quiet
```

### 2.3 — Supprimer les intégrations XSIAM

XSIAM → Settings → Data Sources & Integrations → sélectionner les 2 instances → **Delete**.

### 2.4 — Supprimer les Vulnerability Policies

XSIAM → Vulnerability Management → Vulnerability Policies → supprimer :
- `POL-BusinessCorp-Tier0-Escalate`
- `POL-BusinessCorp-DevLab-Ignore`

### 2.5 — Supprimer les Compensating Controls

XSIAM → Settings → Exposure Management → Security Controls → supprimer :
- `WAF-F5-BigIP-Prod`
- `NGFW-PANW-Perimeter`
- `Cortex-XDR-Agent-Endpoints`
- `VPN-Concentrator-RemoteAccess`

### 2.6 — Supprimer les Asset Groups

XSIAM → Inventory → Assets → Groups → supprimer tous les `grp-*` créés (14 groupes).

### 2.7 — Purger les tags sur les assets

Script inverse de `bulk-tag-assets.py` — supprimer les tags `zone=`, `tier=`, `owner=` sur les 25 assets ciblés. Optionnel : les assets orphelins finiront par être auto-purgés selon la rétention configurée du tenant.

### 2.8 — Supprimer la clé API XSIAM

XSIAM → Settings → API Keys → révoquer `BusinessCorp-VulnIngest-Demo`.

### 2.9 — Nettoyer local

```powershell
Remove-Item -Recurse -Force "C:\Users\jcourtemanch\Documents\dev\demo\sims"
Remove-Item -Force "C:\Users\jcourtemanch\Documents\dev\demo\exposure-management\.secrets.local.md"
```

Garder la doc `exposure-management/` pour réutilisation future.

## Coûts après teardown

- Cloud Run : 0 € (services supprimés)
- Artifact Registry : 0 € (repos supprimés)
- Tenant XSIAM : inchangé (facturation PANW)

## Checkpoint post-teardown

- [ ] `gcloud run services list --region=europe-west1` ne retourne plus les 2 sims
- [ ] XSIAM Data Sources ne montre plus les 2 intégrations
- [ ] XSIAM Asset Groups ne montre plus les `grp-*`
- [ ] `.secrets.local.md` supprimé du disque

## Recommencer la démo à zéro

Repartir de `runbook/01-prerequisites.md`. Compter ~3-4 h de setup complet + 24 h d'attente cycle compensating controls.
