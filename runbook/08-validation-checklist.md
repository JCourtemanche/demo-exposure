# Runbook 08 — Validation checklist (à faire la veille de la démo)

Objectif : vérifier bout-en-bout que la démo est prête. À dérouler intégralement **24-48 h avant** la démo, pour absorber les cycles Cortex (24h Compensating Controls) et corriger les éventuels problèmes.

## Section A — Infrastructure GCP

- [ ] **Rapid7 sim Cloud Run** répond : `curl -u <user>:<pass> https://<url-rapid7>/api/3/assets?size=1` renvoie JSON valide
- [ ] **Cyberwatch sim Cloud Run** répond : `curl -u <key>:<sec> https://<url-cw>/api/v3/ping` renvoie 200 OK
- [ ] Les 2 services sont en état "Serving" (`gcloud run services list --region=europe-west1`)
- [ ] Budget GCP surveillé : `gcloud billing budgets list` (pas de dépassement inattendu)

## Section B — Ingestion XSIAM

- [ ] **Intégration Rapid7** en status "Active — Last fetch < 2h" (Settings → Data Sources)
- [ ] **Intégration Cyberwatch** en status "Active — Last fetch < 2h" (ou script Ingest exécuté récemment)
- [ ] XQL : `dataset = asset_inventory | filter host_name contains "business.org" | comp count()` → **≥ 15 assets**
- [ ] XQL : `dataset = uvm_findings | filter host_name contains "business.org" | comp count()` → **≥ 150 findings**

## Section C — Enrichissement Vulnerability Intelligence

Pour au moins **3 CVE hero** (CVE-2021-44228 Log4Shell, CVE-2021-26855 ProxyLogon, CVE-2020-1472 Zerologon), vérifier :

```xql
config timeframe = 24h
| dataset = uvm_findings
| filter cve = "CVE-2021-44228"
| fields host_name, cve, cvss_score, epss_score, kev, exploit_maturity
| limit 5
```

- [ ] `cvss_score` peuplé (numérique, ex 10.0)
- [ ] `epss_score` peuplé (numérique 0-1)
- [ ] `kev` = true (pour CVE réellement dans KEV)
- [ ] `exploit_maturity` peuplé (ex "high", "functional")

⚠️ Si un de ces champs est vide → l'enrichissement Vulnerability Intelligence n'a pas tourné. Attendre 1h et re-tester. Si toujours vide, ouvrir un ticket support PANW.

## Section D — Tags et groupes

- [ ] 14 groupes créés (9 zones + 4 owner + 1 tier0)
- [ ] Chaque groupe a le bon `member count` (voir tableau `runbook/05` § 5.7)
- [ ] Les 25 assets focus sont tous taggés (spot check 5 assets via l'UI)

## Section E — Compensating Controls

- [ ] 4 contrôles manuels créés : `WAF-F5-BigIP-Prod`, `NGFW-PANW-Perimeter`, `Cortex-XDR-Agent-Endpoints`, `VPN-Concentrator-RemoteAccess`
- [ ] Tous en status **Active** (pas Discovery)
- [ ] Portée (Asset Groups) correcte (spot check 1 contrôle)
- [ ] Cortex XDR auto-détecté si vraie flotte agents (bonus)

## Section F — Vulnerability Policies

- [ ] `POL-BusinessCorp-Tier0-Escalate` enabled, position 1
- [ ] `POL-BusinessCorp-DevLab-Ignore` enabled, position 2
- [ ] Test : ouvrir une case Tier 0 → sévérité = Critical
- [ ] Test : ouvrir Vulnerability Issues, filter `status = ignored` → au moins 1 finding avec raison "POL-BusinessCorp-DevLab-Ignore"

## Section G — Command Center Funnel

XSIAM → **Posture Management** → **Exposure Management** → **Command Center**.

- [ ] Funnel complet visible : Vulnerabilities → Duplicative → Unique → Deprioritized → Open Issues → Cases
- [ ] Chiffres cohérents (décroissants)
- [ ] Onglet **Cases → Require Attention** : entre 6 et 20 cases visibles
- [ ] Décomposition Deprioritized montre 5 filtres actifs

## Section H — Les 6 hero cases

Pour chaque hero case (voir `narratif/hero-cases.md`), ouvrir la case correspondante et vérifier :

### Hero 1 — Urgence Périmètre
- [ ] Case existe sur `srv-vpn` (ou plan B `srv-web-01`)
- [ ] CVE = CVE-2024-3400 (ou CVE-2021-44228)
- [ ] CVRS ≥ 90
- [ ] Badge Internet Exposed visible
- [ ] Badge CISA KEV visible

### Hero 2 — Arme aux mains de l'ennemi
- [ ] Case existe sur `srv-mail` (ou plan B `srv-portail`)
- [ ] CVE = CVE-2021-26855 (ou CVE-2023-34362)
- [ ] Badge CISA KEV présent
- [ ] Exploit Maturity = High/Functional

### Hero 3 — Maillon Faible
- [ ] Case existe sur `esxi-01` (ou `srv-ad-01`)
- [ ] CVSS ≥ 8
- [ ] Compensating Control facteur = "Not Effective" ou "Unknown"

### Hero 4 — Menace Imminente EPSS
- [ ] Case existe sur `alice` (ou serveur Spring)
- [ ] CVE = CVE-2022-30190 ou CVE-2022-22965
- [ ] EPSS > 0.90

### Hero 5 — Risque Confirmé Workload
- [ ] Case existe sur `srv-ci`
- [ ] CVE = CVE-2021-44228 (Log4Shell)
- [ ] Environment Risk = "Package In Use" (si AST activé)

### Hero 6 — Nettoyage de Surface
- [ ] Case existe sur `srv-portail` (ou `srv-web-01`)
- [ ] Sévérité = Medium
- [ ] Internet Exposed = True

## Section I — Répétition talk track

- [ ] Ouvrir `narratif/talk-track-fr.md` sur second écran
- [ ] Dérouler chronomètre en main
- [ ] Cible : **35 minutes ±5**
- [ ] Identifier les cases où le narratif "colle" moins bien à ce qui est affiché → ajuster le talk track OU changer la hero case pour un plan B

## Section J — Backup

- [ ] Screenshots capturés des 6 hero cases (dossier `narratif/screenshots/`)
- [ ] Screenshot du Command Center funnel avec chiffres
- [ ] Screenshot du Security Controls avec les 4 controls Active
- [ ] Vidéo screencast de la démo complète (au cas où le tenant lag le jour J)

## Actions si échec de validation

| Symptôme | Action |
|----------|--------|
| Aucune ingestion depuis Rapid7 | Vérifier auth Cloud Run, faire "Fetch Now" |
| CVSS/EPSS/KEV vides | Attendre 1h, sinon ticket support PANW |
| Une hero case manquante | Utiliser le plan B documenté dans `hero-cases.md` |
| Compensating Control encore en Discovery | Patience — cycle 24h documenté |
| Funnel Command Center vide | Vérifier que ≥ 1 vuln policy est en état Enabled |
| CVRS ne baisse pas malgré XDR agent | Vérifier que le groupe cible bien les bons assets ; consulter open question #3 |

## Suivant

→ [`09-teardown.md`](09-teardown.md) (à consulter uniquement après la démo si nécessaire)
