# Points à valider live dans le tenant XSIAM — Résolutions v1

⚠️ Ce document consolide les **réponses live dans le tenant XSIAM PANW** collectées lors de la mise en place de la démo v1. Les 9 questions initiales sont marquées ✅ RÉSOLU / ⚠️ CONTOURNÉ / 🔜 v2.

---

## ✅ Q1 — Format des tags sur les assets

**Question initiale** : key=value ou flat ? Endpoint API ?

**Résolution** :
- Format **key:value** (séparateur `:` — pas `=`), stocké dans le champ `xdm.asset.tags` (objet JSON) sous `xdm.asset.normalized_fields`
- Exemple observé : `{"Business Corp":"custom","site-1":"location"}`
- Le formatting Rapid7 natif est atypique (les noms Rapid7 tags/sites remontent tels quels dans les valeurs XSIAM)
- Structure JSON complète : le record `asset_inventory` contient un champ `xdm.asset.normalized_fields` qui déserialisé donne toutes les propriétés XDM

**Impact runbook 05** :
- Tags custom Business Corp au format `zone:dmz-web`, `owner:secops`, `tier:0` (avec `:`, pas `=`)
- Filtre XQL groupes : `xdm.asset.tags.zone = "dmz-web"` (à valider selon le formatting exact accepté par XSIAM)

**Requête de vérification** :
```xql
config timeframe = 24h
| dataset = asset_inventory
| filter xdm.host.hostname contains "srv-"
| fields xdm.host.hostname, xdm.asset.tags
| limit 5
```

---

## 🔜 Q2 — Cyberwatch built-in ou Partner Contribution ?

**Résolution** : Piste **abandonnée en v1**. Le pack Cyberwatch (Partner Contribution) alimente `cyberwatch_generic_alert_raw` mais **pas `asset_inventory`** d'Exposure Management.

**Roadmap v2** : Le repo `cyberwatch-simul` a un dossier `byos-importer` (Bring Your Own Scanner) qui contient l'appel API pour aspirer le contenu des datasets Cyberwatch et les pousser dans l'API Ingest d'Exposure Management :
- URL : https://github.com/JCourtemanche/cyberwatch-simul/tree/main/byos-importer

Action v2 : intégrer ce byos-importer dans le pipeline `deploy-full.sh` pour brancher Cyberwatch en tant que source EM secondaire.

---

## ✅ Q3 — Scope du CVRS

**Question initiale** : per-CVE, per-asset, per-finding ?

**Résolution** : **per-finding (per-asset per-CVE)** — le CVRS **prend en compte les compensating controls de l'asset** au moment du calcul. Confirmé sur un finding réel :

Exemple sur `srv-ad-01.business.org` + CVE-2016-3189 :
- Score CVSS : 6.5
- Score EPSS : 0.15562
- Severity : SEV_030_MEDIUM
- Compensating controls influencent la sévérité effective (visible dans le finding)

**Impact** : les policies basées sur CVRS (R1-R5 en v1.4) fonctionnent bien au niveau finding. Un même CVE sur 2 assets différents peut avoir 2 CVRS différents selon les controls.

---

## ⚠️ Q4 — Champ `owner` natif sur l'asset ?

**Question initiale** : owner comme champ premier niveau ?

**Résolution** : **Non**, pas de champ owner natif sur l'objet asset. Deux niveaux de représentation possibles :
- **Tags asset** (via `xdm.asset.tags`) — permet de stocker un `owner:secops` mais informatif seul
- **Owner sur case/issue** — un case XSIAM peut avoir un owner attribué

**Pattern v1 recommandé** :
- Tags asset avec l'owner de référence : `zone:dmz-web`, `owner:secops` (documentaire)
- Playbook XSOAR qui, à la création d'un case, lit le tag `owner:*` de l'asset et assigne le case au bon owner group / user

**Roadmap v2** : Écrire le playbook `EM-demo-Auto-Assign-Case-Owner` :
1. Trigger : nouveau case Vulnerability Management
2. Read asset.tags → extract `owner:*`
3. Map owner → email SecOps/IT-Corp/AppDev/DevOps
4. `setOwner` sur le case

---

## ⚠️ Q5 — Manual override du flag "Internet Exposed"

**Question initiale** : override manuel possible ?

**Résolution** : **Non**, pas d'override direct sur le champ Internet Exposed (dérive uniquement d'ASM/CNA/AST).

**Contournement v1 propre** : créer un **asset group custom** basé sur les tags zone, et l'utiliser dans les Match Conditions des Vulnerability Policies en tant qu'équivalent logique.

**Exemple** :
```
Policy Match Conditions:
  (KEV = Yes) AND (
    Internet Exposed = Yes
    OR
    Asset Group in [EM-demo-zone-dmz-web, EM-demo-zone-dmz-edge]
  )
```

Ainsi les assets DMZ sont traités comme Internet Exposed même si Cortex ne l'a pas détecté nativement.

**Impact runbook 07** : intégrer cette clause OR dans les policies R1, R2, R5 (v1.4 ; R7 en v1.1) (celles qui dépendent d'Internet Exposed).

---

## ✅ Q5b — Internet Exposed déduit d'une IP publique remontée par le scanner ? (v1.4)

**Réponse : non.** Vérifié sur tenant : `internet_exposed` est **vide** (pas `false`) dans `uvm_findings` pour les 6 assets Rapid7 qui remontent une IP 203.0.113.X. D'après la documentation Cortex, l'exposition provient de l'ASM / Cloud Network Analyzer avec confirmation par scan externe ; une IP déclarée par un scanner tiers ne suffit pas. La plage TEST-NET (RFC 5737), non routable, ne répondra de toute façon jamais au scan externe.

**Impact** : les policies « périmètre » (R1, R2, R5) sont cadrées sur l'asset group `EM-demo-grp-Business-Corp-exposed` (tag `exposure:internet` émis par le sim). Ne pas promettre de badge « Internet Exposed » en démo.

---

## ❌ Q6 — MITRE ATT&CK mapping sur les findings

**Résolution** : **Aucune notion de MITRE** dans les findings ni dans la base CVE Cortex Vulnerability Intelligence.

**Impact** : **Retirer toute mention MITRE du talk track**. Ne pas promettre de kill-chain / TTP mapping côté Exposure Management. C'est réservé aux alerts Cortex XDR / XSIAM (correlation rules), pas au vuln management.

---

## ✅ Q7 — Fix Available & Compensating Controls

**Résolution** : **Oui**, les 2 champs existent sur les findings :
- `Fix Available` — Boolean (visible dans le finding détail, "Yes" observé sur CVE-2016-3189)
- `Compensating Controls` — Multi-valeur (effectivité par control)

**Impact** : les policies R4, R5, R6, R8 (qui utilisent `Fix Available`) et R3, R5 (qui utilisent effectivité des controls) sont **fonctionnelles** dans le tenant.

---

## 🔜 Q8 — Endpoint exact Vulnerability Ingest API

**Résolution** : voir Q2 — implémentation via `byos-importer` de Cyberwatch qui utilise le bon endpoint. À explorer en v2.

Documentation Cortex à consulter au moment de la v2 : Cortex XSIAM Platform APIs → Vulnerability Management APIs.

---

## ❌ Q9 — Cycle Discovery → Active Compensating Controls raccourcissable

**Résolution** : **Non**, pas de mécanisme pour forcer le passage Discovery → Active. Le cycle 24h documenté est incompressible.

**Impact planning démo** : créer les compensating controls **au minimum 48 h avant la démo** pour être sûr qu'ils sont en état Active au moment du drill-down (voir runbook 08 checklist J-2).

---

## Convention de nommage v1 — Environnement mutualisé

⚠️ Le tenant XSIAM PANW est **mutualisé** (plusieurs démos coexistent). Tous les artefacts créés pour cette démo utilisent un **préfixe `EM-demo-`** pour éviter les collisions :

| Type | Convention | Exemples |
|------|-----------|----------|
| **Asset Groups** | `EM-demo-<scope>-<name>` | `EM-demo-zone-dmz-web`, `EM-demo-owner-secops`, `EM-demo-business-tier0` |
| **Vulnerability Policies** | `EM-demo-POL-R{n}-<severity>-<discriminator>` | `EM-demo-POL-R1-Critical-KEV-Internet-Exposed` |
| **Compensating Controls** | `EM-demo-CC-<type>-<vendor>` | `EM-demo-CC-WAF-F5-BigIP` |
| **Tags asset** | `<key>:<value>` (pas de préfixe — le format tag est natif Rapid7) | `zone:dmz-web`, `owner:secops`, `tier:0` |

Ce préfixe est **hardcodé** dans les runbooks 05, 06, 07. Pour un client réel non-mutualisé, utiliser un préfixe métier (ex: `PROD-EM-*`, `TENANT-BC-*`) via find-and-replace.
