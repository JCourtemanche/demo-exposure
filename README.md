# Cortex Exposure Management — Business Corp Demo Kit

> Kit démo prêt-à-l'emploi (FR) pour l'addon **Exposure Management** de Palo Alto Networks Cortex XDR / XSIAM.
> Infrastructure fictive **Business Corp** (~250 actifs), 2 sources de vulnérabilités (Rapid7 + Cyberwatch simulés en Cloud Run), 6 hero cases pinnées illustrant les 6 règles du funnel de priorisation, compensating controls et policies XSIAM.

**Objectif** : montrer à un client, en 35 minutes, comment un funnel de priorisation intelligent transforme 2 000+ vulnérabilités brutes en 6-15 cases actionnables avec ownership clair.

---

## ⚡ Quickstart

Prérequis : compte GCP, tenant XSIAM avec addon Exposure Management, `gcloud` + `git` + `python3` (+ `pyyaml`).

```bash
# 1. Cloner ce repo
git clone https://github.com/JCourtemanche/demo-exposure.git
cd demo-exposure

# 2. Configurer les droits IAM GCP (une seule fois par projet)
bash scripts/bootstrap-gcp-iam.sh

# 3. Éditer la config Business Corp (extra assets + hero pinning)
# → config/business-corp-config.yaml

# 4. Pipeline complet : clone sims → auto-patch → sync config → deploy Cloud Run
bash scripts/deploy-full.sh

# 5. Smoke test
bash scripts/smoke-test.sh

# 6. Suivre le runbook XSIAM
# → runbook/03-configure-xsiam-rapid7.md
```

Une fois les 2 sims déployés et branchés à XSIAM, dérouler le [talk track FR](narratif/talk-track-fr.md) chronomètre en main.

---

## 🎯 Ce que la démo raconte

**Acte 1 (5 min, slides)** — Business Corp lundi matin : 2 000 vulnérabilités remontées par Rapid7 + Cyberwatch. Paralysie décisionnelle.

**Acte 2 (10 min, console)** — Funnel Exposure Management : 5 filtres (Not Internet Exposed, Low Business Impact, No Known Exploits, Low/Medium CVSS, Custom Policy) → ~15 cases prioritaires.

**Acte 3 (10 min, drill-down)** — 6 hero cases illustrant 6 règles narratives :

| # | Règle | Hero case pinnée |
|---|-------|------------------|
| 1 | Urgence Périmètre (CVRS≥90 + Internet Exposed) | `srv-vpn` + CVE-2024-3400 |
| 2 | Arme aux mains de l'ennemi (KEV) | `srv-mail` + CVE-2021-26855 (ProxyLogon) |
| 3 | Maillon Faible (pas de Compensating Control) | `esxi-01` + CVE-2020-1472 (Zerologon) |
| 4 | Menace Imminente (EPSS>90%) | `alice` + CVE-2022-30190 (Follina) |
| 5 | Risque Confirmé Workload (Package-in-use) | `srv-ci` + CVE-2021-44228 (Log4Shell) |
| 6 | Nettoyage de Surface (modéré + exposé) | `srv-portail` + CVE-2016-3189 |

**Acte 4 (5 min)** — Compensating controls : WAF F5, PANW NGFW, Cortex XDR agent → effet CVRS.

**Acte 5 (3 min)** — Owner assignment via asset groups tag-based.

**Acte 6 (2 min)** — Conclusion + roadmap.

Voir [`narratif/talk-track-fr.md`](narratif/talk-track-fr.md) pour le script complet.

---

## 📁 Structure du repo

```
demo-exposure/
├── README.md                        # Ce fichier
├── LICENSE                          # MIT
├── .gitignore
│
├── config/                          ⭐ Source de vérité unique
│   ├── business-corp-config.yaml    # Extra assets + hero pinning (à éditer)
│   ├── sync-config-to-sims.py       # Génère business_corp_overrides.py pour les 2 sims
│   ├── catalogs-inventory.md        # 40 CVE disponibles dans chaque sim
│   └── patches/
│       ├── rapid7-patch.md          # Diff manuel Rapid7 (fallback)
│       └── cyberwatch-patch.md      # Diff manuel Cyberwatch (fallback)
│
├── scripts/                         ⭐ Automatisation
│   ├── bootstrap-gcp-iam.sh         # Droits IAM GCP (une fois)
│   ├── apply-patches.py             # Auto-patch les 2 forks (idempotent)
│   ├── deploy-full.sh               # Pipeline complet clone→patch→sync→deploy
│   ├── deploy-vanilla-parallel.sh   # Deploy vanilla // pour A/B testing
│   ├── smoke-test.sh                # Sanity checks post-deploy
│   └── init-git-and-push.sh         # Push initial vers GitHub
│
├── infra/
│   ├── business-corp-infra.mermaid.md   # Diagramme Mermaid (9 zones)
│   └── asset-inventory.md               # 24 actifs focus détaillés
│
├── narratif/
│   ├── talk-track-fr.md             # Script 35 min complet
│   ├── funnel-rules-table.md        # 6 règles narratives
│   └── hero-cases.md                # Storyline détaillée par CVE
│
├── runbook/
│   ├── 01-prerequisites.md
│   ├── 02-deploy-simulators.md      # Mode vanilla (sims non-patchés)
│   ├── 02b-patch-sims-with-config.md ⭐ Mode Business Corp (recommandé)
│   ├── 03-configure-xsiam-rapid7.md
│   ├── 04-configure-xsiam-cyberwatch.md
│   ├── 05-create-tags-and-groups.md
│   ├── 06-declare-compensating-controls.md
│   ├── 07-create-vulnerability-policy.md
│   ├── 08-validation-checklist.md
│   └── 09-teardown.md
│
└── validation/
    └── open-questions-tenant.md     # 9 points à valider live dans le tenant
```

---

## 🔧 Comment ça marche (mécanisme d'injection)

Les 2 simulateurs (Rapid7, Cyberwatch) ont chacun un catalogue **déterministe** de 40 CVE et ~18 assets natifs. Pour aligner sur le narratif Business Corp, ce kit :

1. **Ajoute 4 assets custom** (`srv-portail`, `srv-adfs-01`, `srv-print`, `smtp-relay`) qui n'existent pas nativement
2. **Pin 6 paires (asset, CVE)** pour garantir les hero cases à chaque ingestion

Le mécanisme :

```
config/business-corp-config.yaml    (source de vérité, éditable)
              │
              ▼
config/sync-config-to-sims.py       (génère business_corp_overrides.py)
              │
              ▼
<fork>/simulator/generators/business_corp_overrides.py   (dans chaque fork)
              │
              ▼ (import via patch appliqué UNE FOIS par scripts/apply-patches.py)
<fork>/simulator/generators/assets.py   (patch idempotent)
              │
              ▼
Cloud Run redeploy → ingestion XSIAM → hero cases garanties
```

**Pour changer un hero case** :
```bash
# Éditer config/business-corp-config.yaml (section hero_pinning)
python config/sync-config-to-sims.py       # regénère les overrides
cd ../sims/Rapid7InsightVM-simul && bash deploy-cloudrun.sh
cd ../cyberwatch-simul && bash deploy-cloudrun.sh
# Attendre 5-15 min ingestion XSIAM + "Fetch Now" pour accélérer
```

Aucune retouche Python dans les sims après le premier `apply-patches.py`.

---

## 📋 Prérequis détaillés

| Composant | Version min | Comment vérifier |
|-----------|-------------|------------------|
| GCP | Projet + facturation | `gcloud config get-value project` |
| gcloud CLI | 400+ | `gcloud --version` |
| Python | 3.11+ | `python3 --version` |
| pyyaml | 6+ | `pip show pyyaml` |
| git | 2.30+ | `git --version` |
| Cortex XSIAM | Addon Exposure Management activé | Menu Posture Management → Exposure Management visible |
| Bash | 4+ | `bash --version` (Windows : Git Bash ou WSL) |

Voir [`runbook/01-prerequisites.md`](runbook/01-prerequisites.md) pour la checklist complète, y compris les permissions XSIAM et les content packs Marketplace à installer.

---

## 🚦 Statut du kit

- ✅ Documentation infra + narratif FR complets
- ✅ Runbook 9 étapes end-to-end
- ✅ Config Business Corp + auto-patch idempotent
- ✅ Scripts bootstrap GCP + smoke tests
- ⚠️ 9 points à valider live dans le tenant (voir [`validation/open-questions-tenant.md`](validation/open-questions-tenant.md))
- 🔜 Roadmap : playbook XSOAR (owner lookup + push compensating control), script mensuel d'update CVE actualité

---

## 🤝 Contributions

PRs bienvenues, notamment :
- Nouveaux hero cases (ajouter dans `config/business-corp-config.yaml`)
- Traduction talk track (EN, DE, ES)
- Améliorations `apply-patches.py` (heuristiques Cyberwatch)
- Retours d'expérience terrain dans `validation/open-questions-tenant.md`

---

## 📚 Références

- Doc Cortex Exposure Management : https://cortex-docs.paloaltonetworks.com/cortex-xdr-5.x/detect-investigate-and-respond-to-threats/exposure-management
- Doc Vulnerability Management : https://cortex-docs.paloaltonetworks.com/cortex-xdr-5.x/detect-investigate-and-respond-to-threats/vulnerability-management
- Simulateur Rapid7 InsightVM : https://github.com/JCourtemanche/Rapid7InsightVM-simul
- Simulateur Cyberwatch : https://github.com/JCourtemanche/cyberwatch-simul
- Shared personas package : https://github.com/JCourtemanche/xsiam-shared-personas

---

## 📄 License

MIT — voir [LICENSE](LICENSE).
