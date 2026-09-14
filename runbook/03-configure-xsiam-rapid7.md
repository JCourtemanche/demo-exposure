# Runbook 03 — Configurer l'intégration Rapid7 InsightVM dans XSIAM

Objectif : brancher le simulateur Rapid7 déployé en Cloud Run comme source de vulnérabilités native dans Exposure Management, et valider l'ingestion + l'auto-enrichissement CVSS/EPSS/KEV.

## Étape 3.1 — Vérifier que le content pack est installé

Console XSIAM → **Marketplace** → chercher **"Rapid7 InsightVM"**.

- Status attendu : "Installed" ou "Built-in"
- Si "Available" → cliquer Install, patienter 1-2 min

## Étape 3.2 — Ajouter l'intégration

Console XSIAM → **Settings** (roue crantée) → **Data Sources & Integrations**.

- Cliquer **+ Add integration**
- Chercher "Rapid7 InsightVM"
- Cliquer **Add** ou **Connect**

Alternative (chemin via Exposure Management) :
XSIAM → **Posture Management** → **Exposure Management** → **Data Sources** → **+ Add Integration**.

## Étape 3.3 — Configurer l'instance

Formulaire à remplir (référence : votre `.secrets.local.md`) :

| Champ | Valeur |
|-------|--------|
| **Name** | `BusinessCorp-Rapid7-Demo` |
| **Server URL** | `https://rapid7-nexpose-simulator-<hash>-ew.a.run.app` (⚠️ sans trailing slash) |
| **Username** | `businesscorp-demo` |
| **Password** | `R@pid7-D3mo-BusinessCorp-2026` |
| **2FA Token** | *(laisser vide — le sim accepte le header mais ne le valide pas)* |
| **Trust any certificate** | Non (Cloud Run fournit un certificat valide) |
| **Use system proxy settings** | Selon votre config réseau |
| **Fetch assets and vulnerabilities** | ✅ **Coché** — critique pour Exposure Management |
| **Fetch incidents** | ❌ Décoché (on ne veut pas polluer avec des incidents scanner) |
| **First fetch time** | `7 days` (couvre le catalogue complet) |
| **Fetch interval** | `1 hour` (par défaut, suffisant pour démo) |

## Étape 3.4 — Test et Connect

- Cliquer **Test** → attendu : `Success` (le sim répond au ping / au `/api/3/assets?size=1`)
- Cliquer **Connect** ou **Save**

Si Test échoue :
- Vérifier l'URL sans trailing slash
- Vérifier les credentials (copie-coller sans espace)
- Depuis un poste, `curl` l'URL avec les creds pour valider la connectivité Cloud Run
- Vérifier que le service Cloud Run est bien "unauthenticated" (`gcloud run services describe rapid7-nexpose-simulator --region=europe-west1 --format="value(spec.template.metadata.annotations)"`)

## Étape 3.5 — Attendre la première ingestion (5-15 min)

Après Connect, Cortex démarre la fetch. Observer :

**XSIAM → Data Sources & Integrations → instance `BusinessCorp-Rapid7-Demo`** :
- Status : "Active" → "Fetching" → "Active — Last fetch: X min ago"

## Étape 3.6 — Valider en XQL

XSIAM → **Investigation** → **XQL Search**.

Requête 1 — datasets bruts créés :
```xql
config timeframe = 24h
| dataset = rapid7_insightvm_assets_raw
| limit 5
```
*(le nom exact peut varier — si vide, tester `dataset = rapid7_nexpose_assets_raw` ou lister les datasets via `datasets` command)*

Requête 2 — assets normalisés dans le platform inventory :
```xql
config timeframe = 24h
| dataset = asset_inventory
| filter host_name contains "business.org"
| limit 20
```
Attendu : ~18 assets (6 personas + 12 servers).

Requête 3 — findings normalisés :
```xql
config timeframe = 24h
| dataset = uvm_findings
| filter cve = "CVE-2021-44228"
| limit 10
```
Attendu : au moins 1 ligne avec :
- `cvss_score` peuplé (auto-enrichi)
- `epss_score` peuplé (auto-enrichi)
- `kev` = true (auto-enrichi)
- `asset_id` référençant un asset ingéré

**Ceci est LA validation critique** : si CVSS/EPSS/KEV sont peuplés, l'enrichissement Vulnerability Intelligence fonctionne. Si vides, ouvrir un ticket support PANW.

## Étape 3.7 — Vérifier les cases générées

XSIAM → **Posture Management** → **Vulnerability Management** → **Vulnerability Issues**.

Filtrer par asset : `host_name contains business.org` → une trentaine d'issues devraient apparaître.

XSIAM → **Command Center Exposure Management** → observer les chiffres du funnel se peupler progressivement (peut prendre 30-60 min pour stabilisation).

## Notes

- **Volumétrie** : Rapid7 sim retourne ~18 assets × ~10 vulns moyennes = ~180 findings brutes. Après dédup, ~150.
- **Périodicité** : la fetch tourne toutes les heures — pour forcer une refetch immédiate, cliquer sur "Fetch Now" dans l'instance.
- **Dataset noms** : les noms exacts (`rapid7_insightvm_*` vs `rapid7_nexpose_*`) dépendent de la version du content pack. Documenter le nom réel dans `validation/discovery-results.md`.

## Suivant

→ [`04-configure-xsiam-cyberwatch.md`](04-configure-xsiam-cyberwatch.md)
