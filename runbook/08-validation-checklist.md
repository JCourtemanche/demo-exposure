# Runbook 08 — Validation checklist (v1 Rapid7 only)

Objectif : vérifier bout-en-bout que la démo est prête. À dérouler intégralement **48-72 h avant** la démo pour absorber :
- Le cycle 24 h Compensating Controls (Discovery → Active)
- **Le délai ~2 h d'enrichissement Cortex Vulnerability Intelligence** (~2h après ingestion sim, `uvm_findings` se peuple avec le CVRS calculé)

## Section A — Infrastructure GCP

- [ ] **Rapid7 sim Cloud Run** répond : `curl -u nxadmin:nxadmin-secret https://<url-rapid7>/api/3/assets?size=1` renvoie JSON valide
- [ ] Service en état "Serving" (`gcloud run services list --region=europe-west1`)
- [ ] Budget GCP surveillé : `gcloud billing budgets list` (pas de dépassement inattendu)

⚠️ **Cyberwatch retiré en v1** — pas de check nécessaire. Roadmap v2 réintégrera via Vulnerability Ingest API.

## Section B — Ingestion XSIAM

- [ ] **Intégration Rapid7** en status "Active — Last fetch < 2h" (Settings → Data Sources)
- [ ] Assets Business Corp présents (22 attendus : 16 serveurs + 6 postes) :
```xql
dataset = uvm_findings
| filter asset_name contains "business.org" or asset_name ~= "^BSNS-"
| comp count() as findings, count_distinct(asset_name) as assets
```
→ **22 assets, ~115 findings** (v1.4 : uniquement des CVE cohérentes avec l'OS et les logiciels ; ~2 h après l'ingestion brute)

## Section C — Enrichissement Vulnerability Intelligence et cohérence

Pour les CVE hero, vérifier l'enrichissement :

```xql
dataset = uvm_findings
| filter vulnerability_id in ("CVE-2024-3400", "CVE-2021-26855", "CVE-2020-1472", "CVE-2021-44228")
| dedup asset_name, vulnerability_id
| fields asset_name, operating_system, vulnerability_id, cvss_score, epss_score, has_kev,
         exploitable, cortex_vulnerability_risk_score
```

- [ ] `cvss_score`, `epss_score` peuplés
- [ ] `has_kev` = true (CVE réellement dans KEV)
- [ ] **`cortex_vulnerability_risk_score` peuplé** (0-100) : critique pour les 5 policies
- [ ] `srv-vpn` remonte l'OS **PAN-OS** (et non Ubuntu)

Contrôle de cohérence (aucun résultat attendu) : pas de CVE Exchange / Windows sur un Mac ou un Linux, pas de CVE Apple sur un Windows :
```xql
dataset = uvm_findings
| filter asset_name contains "business.org" or asset_name ~= "^BSNS-"
| filter (operating_system contains "macOS" or operating_system contains "iOS" or operating_system contains "Linux")
         and vulnerability_id in ("CVE-2021-26855", "CVE-2022-41040", "CVE-2022-41082", "CVE-2020-1472", "CVE-2021-34527", "CVE-2024-38063")
     or (operating_system contains "Windows" and vulnerability_id in ("CVE-2023-42917", "CVE-2023-41064", "CVE-2023-41993", "CVE-2024-23222"))
| fields asset_name, operating_system, vulnerability_id
```

⚠️ Si les champs d'enrichissement sont vides → Vulnerability Intelligence n'a pas encore tourné. Attendre 1 h supplémentaire (délai typique ~2 h après la première ingestion). Si toujours vide après 4 h, ouvrir un ticket support PANW.

⚠️ Des paires incohérentes peuvent subsister si elles proviennent d'une ingestion antérieure à la v1.4 : vérifier leur `last_observed`, et leur statut une fois le nouveau sim ingéré.

## Section D — Zone exposée

- [ ] Les 6 assets à IP publique remontent leur IP 203.0.113.X (`ipv4_addresses` dans `uvm_findings`) et le tag `exposure:internet`
- [ ] L'asset group `EM-demo-grp-Business-Corp-exposed` contient 6 membres : srv-vpn, srv-web-01, srv-web-02, srv-mail, srv-portail, smtp-relay
- [ ] Normal : `internet_exposed` reste **vide** (Cortex ne déduit pas ce flag d'une IP remontée par un scanner ; il vient de l'ASM / CNA)

## Section E — Tags et groupes

- [ ] Groupes `EM-demo-*` créés (zones, owners, tier0) + `EM-demo-grp-Business-Corp` (22) + `EM-demo-grp-Business-Corp-exposed` (6)
- [ ] Chaque groupe a le bon `member count` (voir `runbook/05`)
- [ ] Les 16 assets focus sont tous taggés (spot check 5 assets via l'UI)

## Section F — Compensating Controls

- [ ] 4 contrôles manuels créés : `WAF-F5-BigIP-Prod`, `NGFW-PANW-Perimeter`, `Cortex-XDR-Agent-Endpoints`, `VPN-Concentrator-RemoteAccess`
- [ ] Tous en status **Active** (pas Discovery)
- [ ] Portée (Asset Groups) correcte (spot check 1 contrôle)
- [ ] `srv-ad-01`, `srv-vpn`, `srv-print` sont **exclus** du scope XDR (pour matérialiser Hero 3 + Hero 1)

## Section G — Vulnerability Policies (5 règles CVRS R1-R5)

- [ ] `EM-demo-POL-R1-Critical-KEV-Internet-Exposed` enabled, position 1, groupe exposé
- [ ] `EM-demo-POL-R2-Critical-Perimeter-CVRS90` enabled, position 2, groupe exposé
- [ ] `EM-demo-POL-R3-High-Internal-Tier0-KEV` enabled, position 3, tout Business Corp
- [ ] `EM-demo-POL-R4-High-Weaponized` enabled, position 4, tout Business Corp
- [ ] `EM-demo-POL-R5-Medium-External-Surface` enabled, position 5, groupe exposé
- [ ] Colonne **Open Issues** non nulle pour R1 à R5. Si 0 : vérifier qu'aucune automation du tenant ne ferme les issues à leur création (runbook 07, § 7.7)

## Section H — Command Center Funnel

XSIAM → **Posture Management** → **Exposure Management** → **Command Center**.

- [ ] Funnel complet visible : Vulnerabilities → Duplicative → Unique → Deprioritized → Open Issues → Cases
- [ ] Chiffres cohérents (décroissants)
- [ ] Onglet **Cases → Require Attention** : quelques cases visibles, dont les heroes
- [ ] Décomposition Deprioritized montre les filtres natifs + Deprioritized by Policy

## Section I — Les 6 hero cases épinglées

Pour chaque hero case (voir `narratif/hero-cases.md`), ouvrir l'issue correspondante et vérifier :

### Hero 1 — R1 Urgence périmètre
- [ ] Issue sur `srv-vpn.business.org` (OS PAN-OS) avec CVE-2024-3400
- [ ] CVRS ≥ 90, badge CISA KEV
- [ ] Policy : `EM-demo-POL-R1-Critical-KEV-Internet-Exposed`

### Hero 2 — R1 Exploitation active périmètre
- [ ] Issue sur `srv-mail.business.org` avec CVE-2021-26855
- [ ] Badge CISA KEV, Exploit Maturity High/Functional
- [ ] Policy : `EM-demo-POL-R1-Critical-KEV-Internet-Exposed` (si R3 : srv-mail n'est pas dans le groupe exposé)

### Hero 3 — R3 Angle mort interne
- [ ] Issue sur `srv-ad-01.business.org` avec CVE-2020-1472
- [ ] CVRS ≥ 90
- [ ] Asset Group inclut `EM-demo-business-tier0`
- [ ] Compensating Control facteur = "Not Effective" ou "Unknown"
- [ ] Policy : `EM-demo-POL-R3-High-Internal-Tier0-KEV`

### Hero 4 — R1 Exploit prêt (zone exposée)
- [ ] Issue sur `srv-web-01.business.org` avec CVE-2022-22965
- [ ] EPSS élevé, Fix Available = True
- [ ] Policy : `EM-demo-POL-R1-Critical-KEV-Internet-Exposed`
- [ ] Illustration R2 : CVE-2024-38063 sur le même serveur, policy `EM-demo-POL-R2-Critical-Perimeter-CVRS90`

### Hero 5 — R3 Risque confirmé
- [ ] Issue sur `srv-ci.business.org` avec CVE-2021-44228
- [ ] Environment Risk = "Package In Use" (si AST activé)
- [ ] Policy : `EM-demo-POL-R3-High-Internal-Tier0-KEV`
- [ ] Illustration R4 : CVE-2024-23917 (TeamCity) sur le même serveur, policy `EM-demo-POL-R4-High-Weaponized`

### Hero 6 — R5 Surface externe
- [ ] Issue sur `srv-portail.business.org` avec CVE-2016-3189
- [ ] Sévérité = Medium
- [ ] Policy : `EM-demo-POL-R5-Medium-External-Surface`

## Section J — Répétition talk track

- [ ] Ouvrir `narratif/talk-track-fr.md` sur second écran
- [ ] Dérouler chronomètre en main
- [ ] Cible : **35 minutes ±5**
- [ ] Identifier les cases où le narratif "colle" moins bien à ce qui est affiché → ajuster le talk track ou la config

## Section K — Backup

- [ ] Screenshots capturés des 6 hero cases (dossier `narratif/screenshots/`)
- [ ] Screenshot du Command Center funnel avec chiffres
- [ ] Screenshot du Security Controls avec les 4 controls Active
- [ ] Screenshot des 8 Vulnerability Policies
- [ ] Vidéo screencast de la démo complète (au cas où le tenant lag le jour J)

## Actions si échec de validation

| Symptôme | Action |
|----------|--------|
| Aucune ingestion depuis Rapid7 | Vérifier auth Cloud Run, faire "Fetch Now" |
| CVSS/EPSS/KEV vides | Attendre 1h, sinon ticket support PANW |
| `cvrs` vide | Attendre 2h après première ingestion — délai enrichissement typique |
| Une hero case manquante | Vérifier que le pinning est bien dans le YAML + patch appliqué + redeploy Cloud Run |
| Compensating Control encore en Discovery | Patience — cycle 24h documenté |
| Funnel Command Center vide | Vérifier qu'≥ 1 vuln policy est en état Enabled |
| Policy R{n} ne matche pas | Vérifier ordre policies (top-down first-match-wins) + que `cvrs` est peuplé |

## Suivant

→ [`09-teardown.md`](09-teardown.md) (à consulter uniquement après la démo si nécessaire)
