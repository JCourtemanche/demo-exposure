# Runbook 01 — Prérequis

Objectif : s'assurer que tous les composants nécessaires sont disponibles **avant** de commencer le déploiement.

## Checklist

### GCP (pour héberger les simulateurs sur Cloud Run)

- [ ] Compte GCP avec projet actif + facturation activée
- [ ] `gcloud` CLI installé et authentifié (`gcloud auth login`)
- [ ] Projet par défaut configuré (`gcloud config set project <PROJECT_ID>`)
- [ ] APIs GCP activées :
  ```powershell
  gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
  ```
- [ ] Rôles IAM minimum sur votre compte : `Cloud Run Admin`, `Artifact Registry Writer`, `Cloud Build Editor`, `Service Account User`
- [ ] Région cible choisie : **`europe-west1`** (par défaut dans les scripts sim) — cohérent RGPD / latence France

### Cortex XSIAM

- [ ] Tenant XSIAM actif (URL de type `<tenant>.xdr.<region>.paloaltonetworks.com`)
- [ ] **Addon Exposure Management activé** (vérifier avec votre CSM PANW si doute — sans lui, pas de Command Center funnel, pas de Security Controls, pas de CVRS avancé)
- [ ] Utilisateur avec **rôle admin** ou au minimum rôle custom incluant :
  - `Manage Vulnerabilities` (permission clé pour Exposure Management)
  - `Manage Integrations`
  - `Manage Asset Groups`
  - `Manage Vulnerability Policies`
  - `Run XQL` (pour la validation)

### Content packs XSIAM à installer (Cortex Marketplace)

- [ ] **Rapid7 InsightVM** — status "built-in" attendu (natif Exposure Management)
- [ ] **Cyberwatch** — recherche : "Cyberwatch (Partner Contribution)"
  - Si introuvable : **fallback API Vulnerability Ingest** documenté dans `runbook/04`
- [ ] **Cortex Core** (généralement pré-installé)
- [ ] **CommonScripts** (pour éventuelles automations XSOAR post-v1)

Pour installer : XSIAM → Marketplace → chercher le nom → Install.

### Local (poste de préparation démo)

- [ ] Git (pour cloner les 2 repos de sim)
- [ ] Docker Desktop (pour test local des sims avant push Cloud Run)
- [ ] Python 3.11+ (pour lancer le script "Dump discovery" du runbook 02)
- [ ] Éditeur markdown de choix pour le talk track

### Validation live du tenant (⚠️ à faire avant le runbook 02)

Ouvrir `validation/open-questions-tenant.md` et **répondre aux 8 questions** en explorant le tenant. Certaines réponses influencent la suite du runbook (notamment tags key=value vs flat, et disponibilité Cyberwatch built-in).

## Budget indicatif

| Poste | Coût mensuel estimé |
|-------|---------------------|
| GCP Cloud Run (2 sims, 0-2 instances, europe-west1) | 5–15 € |
| Artifact Registry (2 images ~200 Mo) | < 1 € |
| Tenant XSIAM avec addon EM | inclus dans licence PANW |
| **Total démo** | ~15 €/mois |

## Timing global runbook

| Runbook | Durée active | Attente |
|---------|--------------|---------|
| 01 Prérequis | 30 min | — |
| 02 Déploiement sims | 30 min | 5-10 min (build Cloud Build) |
| 03 Config Rapid7 XSIAM | 15 min | **5-15 min ingestion** |
| 04 Config Cyberwatch XSIAM | 20 min | 5-15 min ingestion |
| 05 Tags & groupes | 45 min | Quelques minutes (propagation) |
| 06 Compensating controls | 30 min | **24 h** (cycle Discovery → Active) |
| 07 Vulnerability Policy | 15 min | Immédiat |
| 08 Validation checklist | 30 min | — |
| **Total** | ~3h30 actif | **~24h** avant démo |

**Recommandation** : démarrer runbook 01-07 **au moins 48 h avant la démo** pour absorber le cycle de 24 h des compensating controls et éventuels ajustements.

## Suivant

→ [`02-deploy-simulators.md`](02-deploy-simulators.md)
