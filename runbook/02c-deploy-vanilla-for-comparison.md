# Runbook 02c — Deploy vanilla en parallèle (comparaison A/B)

Objectif : déployer les 2 simulateurs upstream **sans** nos patches Business Corp, en parallèle des patched existants, pour comparer la data ingérée dans XSIAM et isoler ce qui vient des patches vs ce qui vient de l'ingestion XSIAM elle-même.

Utile en cas de doute :
- L'ingestion XSIAM se plaint (404/405, warnings) → est-ce lié à nos patches ou intrinsèque au sim vanilla ?
- Un champ Cortex ne se remplit pas → problème du sim ou de l'enrichissement Vulnerability Intelligence ?
- Un hero pinning ne remonte pas → notre patch a échoué ou XSIAM filtre la donnée ?

## Prérequis

- Runbook 02b déjà exécuté (les sims patched sont déployés)
- Runbook 03/04 déjà exécutés (les 2 intégrations patched sont configurées dans XSIAM et ingèrent)
- Un supplément de ~5 €/mois de compute Cloud Run (2 services de plus en 0-2 instances)

## Étape 02c.1 — Deploy vanilla

Un seul script pour tout faire :

```bash
cd ~/demo-exposure
bash scripts/deploy-vanilla-parallel.sh
```

Le script :
1. Clone les 2 repos originaux dans `~/sims-vanilla/` (séparé de `~/sims/`)
2. Restore les fichiers si le clone existait déjà (idempotent — pas de patch cumulé)
3. Renomme les services Cloud Run + repos Artifact Registry avec suffix `-vanilla` via `sed` sur `deploy-cloudrun.sh` et `cloudbuild.yaml`
4. Deploy les 2 services `-vanilla` sur GCP
5. Autorise `allUsers/run.invoker` sur les 2 nouveaux services
6. Affiche les 4 URLs (2 vanilla + 2 patched)

Durée : ~10-15 min (2 builds Cloud Build en parallèle).

## Étape 02c.2 — Configurer les 2 nouvelles intégrations XSIAM

XSIAM → Settings → Data Sources & Integrations → **+ Add integration**.

### Instance `BC-Rapid7-Vanilla`

| Champ | Valeur |
|-------|--------|
| Name | `BC-Rapid7-Vanilla` |
| Server URL | (URL Cloud Run affichée par le script) |
| Username | `nxadmin` |
| Password | `nxadmin-secret` |
| Fetch assets and vulnerabilities | ✓ |
| First fetch time | `7 days` |

Test → Connect.

### Instance `BC-Cyberwatch-Vanilla`

| Champ | Valeur |
|-------|--------|
| Name | `BC-Cyberwatch-Vanilla` |
| Server URL | (URL Cloud Run vanilla Cyberwatch) |
| Access Key | `cyberwatch-access-key` |
| Secret Key | `cyberwatch-secret-key` |
| Fetch assets and vulnerabilities | ✓ |

Test → Connect.

Attendre 5-15 min pour la première fetch.

## Étape 02c.3 — Comparer via XQL

### Compte assets par instance

```xql
config timeframe = 24h
| dataset = asset_inventory
| filter host_name contains "business.org"
| comp count() as assets by _source_id
```

Attendu (approximatif) :
| _source_id | assets | Note |
|------------|--------|------|
| BC-Rapid7-BusinessCorp | 22 | 18 natifs + 4 extras BC |
| BC-Rapid7-Vanilla | 18 | seulement les natifs |
| BC-Cyberwatch-BusinessCorp | ~20 | 18 natifs + 3 extras BC (srv-print absent) |
| BC-Cyberwatch-Vanilla | 18 | seulement les natifs |

Note : selon le mapping de dédup Cortex, les mêmes hostnames Rapid7 + Cyberwatch peuvent être dédupliqués — auquel cas le compte peut être plus bas.

### Vérifier présence des CVE hero pinnées

```xql
config timeframe = 24h
| dataset = uvm_findings
| filter host_name = "srv-vpn.business.org" and cve = "CVE-2024-3400"
| fields _source_id, host_name, cve, cvss_score, epss_score, kev
```

Attendu :
- Vanilla : peut-être présent (aléatoire), peut-être absent
- Patched : **toujours présent** (grâce au pinning `hero_pinning`)

Reproduire pour les 6 hero cases pinnées (voir `narratif/hero-cases.md`).

### Compter les findings totaux

```xql
config timeframe = 24h
| dataset = uvm_findings
| filter host_name contains "business.org"
| comp count() as findings by _source_id
```

Diff attendu : les 4 sources devraient être proches (~150-200 findings chacune), avec possiblement quelques uniques côté patched grâce aux extras.

## Étape 02c.4 — Interpréter les diffs

| Observation | Diagnostic |
|-------------|------------|
| Vanilla et patched même count → OK, nos patches n'ont pas cassé l'ingestion | ✅ green light pour la démo |
| Patched < vanilla → nos patches ont détruit des assets/findings | ⚠️ revoir apply-patches.py |
| Vanilla = 0 et patched > 0 → problème d'auth ou fetch sur vanilla, patched OK | Vérifier creds vanilla |
| Vanilla > 0 et patched = 0 → nos patches font crasher le sim en runtime | Vérifier logs Cloud Run patched |
| Extras BC absents côté patched | Voir troubleshooting runbook 02b |

## Étape 02c.5 — Cleanup (une fois la comparaison terminée)

Pour supprimer les vanilla et revenir à l'état "patched only" :

```bash
# Cloud Run
gcloud run services delete rapid7-nexpose-simulator-vanilla --region=europe-west1 --quiet
gcloud run services delete cyberwatch-simulator-vanilla --region=europe-west1 --quiet

# Artifact Registry (optionnel, pour libérer l'espace)
gcloud artifacts repositories delete rapid7-nexpose-simulator-vanilla --location=europe-west1 --quiet
gcloud artifacts repositories delete cyberwatch-simulator-vanilla --location=europe-west1 --quiet

# XSIAM : désactiver ou supprimer les instances BC-*-Vanilla via UI

# Local (optionnel)
rm -rf ~/sims-vanilla
```

## Alternative si on veut garder vanilla en permanence

Rien n'empêche de laisser les 4 services tourner en permanence. Coût : ~5 €/mois de plus. Utile si on itère souvent sur les patches Business Corp — la baseline vanilla reste toujours accessible pour comparer.

## Suivant

Retour au parcours principal :
- Si comparaison OK et démo prête : → [`08-validation-checklist.md`](08-validation-checklist.md)
- Si diff révèle un bug patch → corriger, redeploy patched, refaire compare
