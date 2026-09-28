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
- [ ] XQL : `dataset = asset_inventory | filter xdm.asset.strong_id contains "rapid7" | comp count()` → **≥ 16 assets**
- [ ] XQL : `dataset = rapid7_nexpose_vulnerabilities_raw | comp count()` → **≥ 150 findings**
- [ ] XQL : `dataset = uvm_findings | filter _vendor contains "Rapid7" | comp count()` → **≥ 100 findings normalisés** (peuple ~2h après le raw)

## Section C — Enrichissement Vulnerability Intelligence

Pour au moins **3 CVE hero** (CVE-2021-44228 Log4Shell, CVE-2021-26855 ProxyLogon, CVE-2020-1472 Zerologon), vérifier :

```xql
config timeframe = 24h
| dataset = uvm_findings
| filter cve = "CVE-2021-44228"
| fields xdm.host.hostname, cve, cvss_score, epss_score, kev, exploit_maturity, cvrs
| limit 5
```

- [ ] `cvss_score` peuplé (numérique, ex 10.0)
- [ ] `epss_score` peuplé (numérique 0-1)
- [ ] `kev` = true (pour CVE réellement dans KEV)
- [ ] `exploit_maturity` peuplé (ex "high", "functional")
- [ ] **`cvrs` peuplé** (0-100) — **critique pour les 8 policies R1-R8**

⚠️ Si un de ces champs est vide → l'enrichissement Vulnerability Intelligence n'a pas encore tourné. Attendre 1h supplémentaire (délai typique ~2h après première ingestion) et re-tester. Si toujours vide après 4h, ouvrir un ticket support PANW.

## Section D — Public IPs (Internet Exposed)

- [ ] Les 6 assets Internet Exposed ont bien leur IP publique visible :
```xql
config timeframe = 24h
| dataset = asset_inventory
| filter xdm.host.hostname in ("srv-vpn.business.org", "srv-web-01.business.org",
                              "srv-web-02.business.org", "srv-mail.business.org",
                              "srv-portail.business.org", "smtp-relay.business.org")
| fields xdm.host.hostname, xdm.host.ipv4_addresses
```
Chacun doit lister au moins **2 IPs** (privée 10.10.20.X + publique 203.0.113.X)
- [ ] Le flag `Internet Exposed` est visible dans les Vulnerability Issues pour au moins 1 hero case (via ASM ou déduction native)

## Section E — Tags et groupes

- [ ] 14 groupes créés (7 zones + 4 owner + 1 tier0 + `grp-business-tier0`)
- [ ] Chaque groupe a le bon `member count` (voir tableau `runbook/05` § 5.7)
- [ ] Les 16 assets focus sont tous taggés (spot check 5 assets via l'UI)

## Section F — Compensating Controls

- [ ] 4 contrôles manuels créés : `WAF-F5-BigIP-Prod`, `NGFW-PANW-Perimeter`, `Cortex-XDR-Agent-Endpoints`, `VPN-Concentrator-RemoteAccess`
- [ ] Tous en status **Active** (pas Discovery)
- [ ] Portée (Asset Groups) correcte (spot check 1 contrôle)
- [ ] `srv-adfs-01`, `srv-vpn`, `srv-print` sont **exclus** du scope XDR (pour matérialiser Hero 3 + Hero 1)

## Section G — Vulnerability Policies (8 règles CVRS R1-R8)

- [ ] `POL-BC-R1-Feu-de-Foret` enabled, position 1
- [ ] `POL-BC-R2-Urgence-Perimetre` enabled, position 2
- [ ] `POL-BC-R3-Maillon-Faible-Interne` enabled, position 3
- [ ] `POL-BC-R4-Exploit-Pret` enabled, position 4
- [ ] `POL-BC-R5-Sans-Patch` enabled, position 5
- [ ] `POL-BC-R6-Hygiene-Prioritaire` enabled, position 6
- [ ] `POL-BC-R7-Surface-Externe` enabled, position 7
- [ ] `POL-BC-R8-Rolling-Patch` enabled, position 8

## Section H — Command Center Funnel

XSIAM → **Posture Management** → **Exposure Management** → **Command Center**.

- [ ] Funnel complet visible : Vulnerabilities → Duplicative → Unique → Deprioritized → Open Issues → Cases
- [ ] Chiffres cohérents (décroissants)
- [ ] Onglet **Cases → Require Attention** : entre 6 et 20 cases visibles
- [ ] Décomposition Deprioritized montre 5 filtres actifs (4 natifs + 1 policy)

## Section I — Les 6 hero cases pinnées

Pour chaque hero case (voir `narratif/hero-cases.md`), ouvrir la case correspondante et vérifier :

### Hero 1 — R2 Urgence Périmètre
- [ ] Case existe sur `srv-vpn.business.org` avec CVE-2024-3400
- [ ] CVRS ≥ 90
- [ ] Badge Internet Exposed visible
- [ ] Badge CISA KEV visible
- [ ] Policy matched : `POL-BC-R2-Urgence-Perimetre`

### Hero 2 — R1 Feu de forêt
- [ ] Case existe sur `srv-mail.business.org` avec CVE-2021-26855
- [ ] Badge CISA KEV présent
- [ ] Exploit Maturity = High/Functional
- [ ] Policy matched : `POL-BC-R1-Feu-de-Foret`

### Hero 3 — R3 Maillon Faible interne
- [ ] Case existe sur `srv-adfs-01.business.org` avec CVE-2020-1472
- [ ] CVRS ≥ 90
- [ ] Internet Exposed = **False**
- [ ] Asset Group inclut `grp-business-tier0`
- [ ] Compensating Control facteur = "Not Effective" ou "Unknown"
- [ ] Policy matched : `POL-BC-R3-Maillon-Faible-Interne`

### Hero 4 — R4 Exploit prêt EPSS
- [ ] Case existe sur `srv-web-01.business.org` avec CVE-2022-22965
- [ ] EPSS ≥ 0.7
- [ ] Fix Available = True
- [ ] Policy matched : `POL-BC-R4-Exploit-Pret`

### Hero 5 — R4 Exploit prêt Package-in-use
- [ ] Case existe sur `srv-ci.business.org` avec CVE-2021-44228
- [ ] Environment Risk = "Package In Use" (si AST activé)
- [ ] Policy matched : `POL-BC-R4-Exploit-Pret`

### Hero 6 — R7 Surface externe
- [ ] Case existe sur `srv-portail.business.org` avec CVE-2016-3189
- [ ] Sévérité = Medium
- [ ] Internet Exposed = True
- [ ] Policy matched : `POL-BC-R7-Surface-Externe`

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
