# Cortex Exposure Management — Business Corp Demo Kit (v1)

> Kit démo prêt-à-l'emploi (FR) pour l'addon **Exposure Management** de Palo Alto Networks Cortex XDR / XSIAM.
> Infrastructure fictive **Business Corp** (16 assets focus), source unique **Rapid7 InsightVM** (simulé en Cloud Run), 6 hero cases épinglées illustrant **5 règles CVRS-centric** (R1 à R5), compensating controls et policies XSIAM.

**Objectif** : montrer à un client, en 35 minutes, comment le **CVRS** (Cortex Vulnerability Risk Score, propriétaire Cortex) — combiné à un funnel de priorisation et à des compensating controls — transforme 200+ vulnérabilités brutes en 6-15 cases actionnables avec ownership et SLA clairs.

**Différenciateur principal** : le CVRS agrège CVSS + EPSS + KEV + exposition + Package-in-use + Compensating Controls dans un score 0-100 contextuel. Le CVSS seul est aveugle au contexte.

---

## ⚡ Quickstart

Prérequis : compte GCP, tenant XSIAM avec addon Exposure Management, `gcloud` + `git` + `python3` (+ `pyyaml`).

```bash
# 1. Cloner ce repo
git clone https://github.com/JCourtemanche/demo-exposure.git
cd demo-exposure

# 2. Configurer les droits IAM GCP (une seule fois par projet)
bash scripts/bootstrap-gcp-iam.sh

# 3. Éditer la config Business Corp si besoin (extras + hero pinning + public IPs)
# → config/business-corp-config.yaml

# 4. Pipeline complet : clone sim → auto-patch → sync config → deploy Cloud Run
#    (Cyberwatch skip en v1 : export SKIP_CYBERWATCH=1)
export SKIP_CYBERWATCH=1
bash scripts/deploy-full.sh

# 5. Smoke test
bash scripts/smoke-test.sh

# 6. Suivre le runbook XSIAM (03 → 05 → 06 → 07 → 08)
# → runbook/03-configure-xsiam-rapid7.md
```

**⏱️ Timing critique** : après avoir configuré Rapid7 dans XSIAM, prévoir **~2h** pour que `uvm_findings` se peuple avec CVRS + KEV + EPSS enrichis par Cortex Vulnerability Intelligence. Dérouler la démo **au moins 4h après le premier deploy** pour être sûr.

Une fois les policies R1-R5 en place, dérouler le [talk track FR](narratif/talk-track-fr.md) chronomètre en main (35 min).

---

## 🎯 Ce que la démo raconte

**Acte 1 (5 min, slides)** — Business Corp lundi matin : Rapid7 remonte plus d'une centaine de vulnérabilités, dont beaucoup critiques. Paralysie décisionnelle sans priorisation contextuelle.

**Acte 2 (10 min, console)** — Funnel Exposure Management : 5 filtres (4 natifs Cortex + 1 policies custom) → ~15 cases prioritaires. Introduction du **CVRS** comme score contextuel.

**Acte 3 (10 min, drill-down)** — 6 hero cases mappées sur les règles CVRS :

| # | Hero case pinnée | Règle CVRS déclenchée |
|---|------------------|----------------------|
| 1 | `srv-vpn` (PAN-OS) + CVE-2024-3400 | **R1** Exploitation active périmètre (KEV, zone exposée) |
| 2 | `srv-mail` + CVE-2021-26855 (ProxyLogon) | **R1** Exploitation active périmètre (KEV, zone exposée) |
| 3 | `srv-ad-01` (DC) + CVE-2020-1472 (Zerologon) | **R3** Angle mort interne (KEV + CVRS ≥ 90, interne) |
| 4 | `srv-web-01` + CVE-2022-22965 (Spring4Shell) | **R1** Exploit prêt (KEV / EPSS élevé, zone exposée) |
| 5 | `srv-ci` + CVE-2021-44228 (Log4Shell) | **R3** Risque confirmé (KEV + CVRS ≥ 90, Package-in-use) |
| 6 | `srv-portail` + CVE-2016-3189 | **R5** Réduction surface externe (CVRS ≤ 89, zone exposée) |

Illustrations complémentaires : `srv-web-01` + CVE-2024-38063 (R2), `srv-ci` + CVE-2024-23917 TeamCity (R4).

**Acte 4 (5 min)** — Compensating controls : WAF F5, PANW NGFW, Cortex XDR agent → effet CVRS.

**Acte 5 (3 min)** — Owner assignment via asset groups tag-based (SecOps / IT Corp / AppDev / DevOps).

**Acte 6 (2 min)** — Conclusion + roadmap client.

Voir [`narratif/talk-track-fr.md`](narratif/talk-track-fr.md) pour le script complet et [`narratif/funnel-rules-table.md`](narratif/funnel-rules-table.md) pour les 5 règles.

---

## 📁 Structure du repo

```
demo-exposure/
├── README.md                        # Ce fichier
├── LICENSE                          # MIT
├── .gitignore
│
├── config/                          ⭐ Source de vérité unique
│   ├── business-corp-config.yaml    # Extras + hero pinning + public IPs (à éditer)
│   ├── sync-config-to-sims.py       # Génère business_corp_overrides.py
│   ├── catalogs-inventory.md        # 49 CVE du sim Rapid7 + règles de cohérence CVE / asset
│   └── patches/
│       ├── rapid7-patch.md          # Diff manuel Rapid7 (fallback)
│       └── cyberwatch-patch.md      # Diff manuel Cyberwatch (v2 roadmap)
│
├── scripts/                         ⭐ Automatisation
│   ├── bootstrap-gcp-iam.sh         # Droits IAM GCP (une fois)
│   ├── apply-patches.py             # Auto-patch le fork (idempotent, 6 blocs)
│   ├── deploy-full.sh               # Pipeline complet — export SKIP_CYBERWATCH=1
│   ├── deploy-vanilla-parallel.sh   # Deploy vanilla // pour A/B testing (optionnel)
│   ├── diff-vanilla-vs-patched.sh   # Compare endpoints vanilla vs patched (optionnel)
│   ├── smoke-test.sh                # Sanity checks post-deploy
│   └── init-git-and-push.sh         # Push initial vers GitHub
│
├── infra/
│   ├── business-corp-infra.mermaid.md   # Diagramme Mermaid (7 zones)
│   └── asset-inventory.md               # 16 actifs focus détaillés + public IPs
│
├── narratif/
│   ├── talk-track-fr.md             # Script 35 min complet (v1 Rapid7 only)
│   ├── funnel-rules-table.md        # 5 règles CVRS (R1-R5)
│   └── hero-cases.md                # Storyline détaillée par CVE hero
│
├── runbook/
│   ├── 00-git-workflow.md           # Init repo + push + branches
│   ├── 01-prerequisites.md          # GCP, XSIAM, permissions, content packs
│   ├── 02-deploy-simulators.md      # Mode vanilla (base)
│   ├── 02b-patch-sims-with-config.md ⭐ Mode Business Corp (recommandé)
│   ├── 02c-deploy-vanilla-for-comparison.md # Deploy vanilla // (optionnel A/B)
│   ├── 03-configure-xsiam-rapid7.md
│   ├── 04-configure-xsiam-cyberwatch.md   ⚠️ Retiré v1 — roadmap v2
│   ├── 05-create-tags-and-groups.md
│   ├── 06-declare-compensating-controls.md
│   ├── 07-create-vulnerability-policy.md  ⭐ 5 policies CVRS R1-R5
│   ├── 08-validation-checklist.md   ⭐ Note délai 2h ingestion
│   └── 09-teardown.md
│
└── validation/
    └── open-questions-tenant.md     # Points à valider live dans le tenant
```

---

## 🔧 Comment ça marche (mécanisme d'injection)

Le simulateur Rapid7 a un catalogue **déterministe** de 49 CVE et 12 assets natifs. Depuis sa v1.4, il n'attribue à chaque asset que des CVE **applicables à son OS et à ses logiciels** (`CVE_REQUIREMENTS` + rôles par asset). Pour aligner sur le narratif Business Corp, ce kit :

1. **Ajoute 4 assets custom** (`srv-portail`, `srv-adfs-01`, `srv-print`, `smtp-relay`) qui n'existent pas nativement
2. **Épingle les paires (asset, CVE)** des hero cases (et du scénario Intune) à chaque ingestion
3. **Ajoute des IPs publiques** (range TEST-NET RFC 5737) et le tag `exposure:internet` à 6 assets, pour la zone exposée
4. **(v1.4) Déclare les rôles logiciels** des assets ajoutés et **surcharge l'OS** de `srv-vpn` (PAN-OS) pour garder des CVE cohérentes

Le mécanisme :

```
config/business-corp-config.yaml    (source de vérité, éditable)
              │
              ▼
config/sync-config-to-sims.py       (génère EXTRA_ASSETS + PINNED_CVES + PUBLIC_IPS + ASSET_TAGS + ASSET_ROLES + OS_OVERRIDES)
              │
              ▼
<fork>/simulator/generators/business_corp_overrides.py
              │
              ▼ (import via patch bloc 1 de apply-patches.py, idempotent)
<fork>/simulator/generators/assets.py     (6 blocs de patch)
<fork>/simulator/routes/reports.py         (4 routes GET/DELETE manquantes)
              │
              ▼
Cloud Run redeploy → ingestion XSIAM → ~2h enrichissement → hero cases garanties
```

**Pour changer un hero case** :
```bash
# Éditer config/business-corp-config.yaml (section hero_pinning ou additional_public_ips)
python config/sync-config-to-sims.py       # regénère les overrides
cd ../sims/Rapid7InsightVM-simul && bash deploy-cloudrun.sh
# Attendre 5-15 min ingestion + "Fetch Now" dans XSIAM + ~2h enrichissement Cortex
```

Aucune retouche Python dans le sim après le premier `apply-patches.py` (patch idempotent).

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
| Content pack **Rapid7 InsightVM** | Built-in | Marketplace → status "Installed" |
| Bash | 4+ | `bash --version` (Windows : Git Bash ou WSL) |

Voir [`runbook/01-prerequisites.md`](runbook/01-prerequisites.md) pour la checklist complète.

---

## 🚦 Statut du kit v1

- ✅ Documentation infra + narratif FR complets (5 règles CVRS + 6 hero cases)
- ✅ v1.4 : cohérence CVE / asset garantie par le sim (0 paire incohérente, contre 72 % avant)
- ✅ Runbook 9 étapes end-to-end (Cyberwatch marqué v2 optionnel)
- ✅ Config Business Corp + auto-patch idempotent (6 blocs + reports.py routes)
- ✅ Zone exposée : IP publiques (range TEST-NET) + tag `exposure:internet` (Cortex ne déduit pas Internet Exposed d'une IP scanner)
- ✅ Scripts bootstrap GCP + smoke tests + A/B vanilla comparison
- ✅ Testé end-to-end sur tenant XSIAM live (délai ingestion ~2h documenté)
- 🔜 Roadmap v2 :
  - Réintégrer Cyberwatch via Vulnerability Ingest API
  - Playbook XSOAR (owner lookup AD + push compensating control)
  - Script mensuel d'update CVE actualité (top KEV du mois)
  - Bridge vers Modeling Rule XQL pour Cyberwatch → asset_inventory

---

## 🤝 Contributions

PRs bienvenues, notamment :
- Nouvelles règles CVRS (compliance PCI/HDS/NIS2)
- Traduction talk track (EN, DE, ES)
- Améliorations `apply-patches.py`
- Retours d'expérience terrain dans `validation/open-questions-tenant.md`
- Bridges v2 pour Cyberwatch, Qualys, Tenable

---

## 📚 Références

- Doc Cortex Exposure Management : https://cortex-docs.paloaltonetworks.com/cortex-xdr-5.x/detect-investigate-and-respond-to-threats/exposure-management
- Doc Vulnerability Management : https://cortex-docs.paloaltonetworks.com/cortex-xdr-5.x/detect-investigate-and-respond-to-threats/vulnerability-management
- Simulateur Rapid7 InsightVM : https://github.com/JCourtemanche/Rapid7InsightVM-simul
- Remédiation Intune des postes Business Corp (playbook + simulateur Graph) : https://github.com/JCourtemanche/intune-simul
- Simulateur Cyberwatch : https://github.com/JCourtemanche/cyberwatch-simul (v2)
- Shared personas package : https://github.com/JCourtemanche/xsiam-shared-personas

---

## 📄 License

MIT — voir [LICENSE](LICENSE).
