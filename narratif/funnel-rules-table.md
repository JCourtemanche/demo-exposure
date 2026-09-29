# Les 8 règles narratives du funnel — source de vérité (v1.1)

Ces 8 règles définissent la **logique de déclenchement des tickets / incidents** en fonction de la criticité réelle et du contexte d'exposition. Elles sont **centrées sur le CVRS** (Cortex Vulnerability Risk Score, propriétaire Cortex) plutôt que sur le CVSS seul — c'est le principal différenciateur d'Exposure Management vs un scanner classique.

⚠️ **Naming convention** — les policies sont préfixées `EM-demo-POL-` (tenant XSIAM mutualisé). Les libellés narratifs FR sont conservés pour le discours client (plus mémorables) mais le nom technique dans XSIAM est corporate.

## Tableau canonique (à afficher en slide "Acte 1")

| Ref | Nom XSIAM (technique) | Libellé narratif FR | Logique de Détection | Sévérité | SLA | Objectif & Justification |
|-----|----------------------|---------------------|----------------------|----------|-----|--------------------------|
| **R1** | `EM-demo-POL-R1-Critical-KEV-Internet-Exposed` | **Exploitation active périmètre** | `(KEV OR EPSS≥0.9) AND (Internet Exposed OR Asset Group in DMZ)` | **Critique** | **48 h** | Exploitation confirmée + exposition Internet. Cible n°1 des scanners d'attaquants. |
| **R2** | `EM-demo-POL-R2-Critical-Perimeter-CVRS90` | **Urgence périmètre** | `CVRS ≥ 90 AND (Internet Exposed OR Asset Group in DMZ)` | **Critique** | **72 h** | Faille critique contextualisée exposée sur Internet sans contrôles suffisants. |
| **R3** | `EM-demo-POL-R3-High-Internal-Tier0-KEV` | **Angle mort interne** | `KEV AND CVRS ≥ 90 AND Internet Exposed = No AND Asset Group in [EM-demo-business-tier0]` | **Haute** | **7 j** | Faille KEV en interne sur un actif Tier 0 (risque de mouvement latéral). |
| **R4** | `EM-demo-POL-R4-High-Weaponized-Patchable` | **Exploit prêt patchable** | `(EPSS ≥ 0.7 OR Exploit Level = Weaponized) AND CVRS ≥ 80 AND Fix Available = Yes` | **Haute** | **14 j** | Faille exploitable mal contrôlée mais disposant d'un patch. |
| **R5** | `EM-demo-POL-R5-High-NoPatch-Compensating` | **Compensation obligatoire** | `CVRS ≥ 80 AND Fix Available = No` | **Haute** | **30 j** | Absence de correctif : le ticket impose un contrôle compensatoire (WAF, règle XDR, segmentation). |
| **R6** | `EM-demo-POL-R6-Medium-Batch-Hygiene` | **Hygiène prioritaire** | `CVRS in [70, 89] AND Fix Available = Yes` | **Moyenne** | **30 j** | Traitement mensuel par lot (batch). |
| **R7** | `EM-demo-POL-R7-Medium-External-Surface` | **Réduction surface externe** | `CVRS in [60, 89] AND (Internet Exposed OR Asset Group in DMZ)` | **Moyenne** | **30 j** | Vulnérabilités moyennes externes pouvant servir de chaîne d'attaque. |
| **R8** | `EM-demo-POL-R8-Low-Rolling-Update` | **Cycle patch continu** | `CVRS in [40, 69] AND Fix Available = Yes` | **Faible** | **90 j** | Cycle de mise à jour régulier. Intégré dans une campagne mensuelle globale sans ticket individuel. |

## Pourquoi CVRS et pas CVSS ?

Le **CVRS** (Cortex Vulnerability Risk Score, 0–100, **per-finding**) est calculé par Cortex à partir de **5 facteurs contextuels** :

1. **Vulnerability Context** — CVSS base score
2. **Exploit Intelligence** — EPSS, CISA KEV, exploited-in-the-wild, exploit maturity
3. **Asset Risk** — Internet Exposed (via ASM/CNA/public IP)
4. **Environment Risk** — Package-in-use (validé par Attack Surface Testing)
5. **Compensating Controls** — Effectivité des contrôles (XDR agent, WAF, NGFW) sur cette CVE **au niveau de cet asset précis** (Q3 confirmée)

**Le CVSS seul ne dit rien du contexte** — CVE 10.0 sur asset patché derrière un WAF avec XDR agent = risque réel faible. Le CVRS reflète cette nuance **per (CVE, asset)**.

## Correspondance avec les hero cases de la démo

| Hero case (asset + CVE) | Règle déclenchée | Angle démo |
|-------------------------|------------------|------------|
| **`srv-vpn` + CVE-2024-3400** (PAN-OS) | **R2** Urgence périmètre | Boîtier VPN critique exposé, pas d'agent XDR possible |
| **`srv-mail` + CVE-2021-26855** (ProxyLogon) | **R1** Exploitation active périmètre | Exchange OWA exposé, exploitation active documentée (KEV) |
| **`srv-adfs-01` + CVE-2020-1472** (Zerologon) | **R3** Angle mort interne | ADFS Tier 0 sans agent XDR — mouvement latéral facile |
| **`srv-web-01` + CVE-2022-22965** (Spring4Shell) | **R4** Exploit prêt patchable | Serveur web exposé, patch disponible mais pas déployé |
| **`srv-ci` + CVE-2021-44228** (Log4Shell) | **R4** Exploit prêt patchable | CI Java, Package In Use confirmé par AST |
| **`srv-portail` + CVE-2016-3189** (bzip2) | **R7** Réduction surface externe | Portail public, vuln modérée mais visible depuis Shodan |

Note : les règles R5, R6, R8 sont **documentées et actives** dans la Vulnerability Policy, mais **pas illustrées par un hero case dédié** — elles apparaîtront naturellement dans le funnel Command Center comme "Deprioritized by Policy" pour les vulns de sévérité moindre.

## Utilisation en démo

**Acte 1** (slide) : afficher ce tableau tel quel. Message : "Voici la grille de priorisation qu'on va appliquer à Business Corp — 8 règles CVRS-centric qui remplacent le tri CVSS traditionnel."

**Acte 3** (drill-down console) : pour chaque hero case, dire "Cette case déclenche la règle **R{n}** — voici pourquoi (montrer le breakdown CVRS)". Le libellé FR sert de mnémonique pour l'audience, le nom technique EM-demo-POL est visible à l'écran.

**Acte 4** (compensating controls) : montrer qu'un asset avec XDR + WAF a un CVRS plus bas qu'un asset identique sans (démonstration factor "Compensating Controls" dans Risk Details).

## Personnalisation client

Les 8 règles sont **une proposition Business Corp** — chaque client peut :
- Ajuster les seuils CVRS (`≥ 90`, `≥ 80`, `≥ 70`) selon son appétit au risque
- Ajouter des règles spécifiques (compliance PCI-DSS, HDS, NIS2, souveraineté)
- Modifier les SLA selon les engagements internes (48h/72h/7j...)
- Créer des asset groups métier (`{Prod critique}`, `{Data-classification=Secret}`, etc.)
- **Renommer le préfixe** `EM-demo-` en `PROD-VulnMgmt-` (ou équivalent) pour un tenant client dédié

C'est le levier principal pour transformer un modèle générique en politique alignée à la maturité du client.

## Note sur MITRE ATT&CK (Q6 résolue)

⚠️ **Aucune notion de MITRE ATT&CK dans les findings Cortex Exposure Management** — le mapping technique/tactique est réservé aux alerts XDR/XSIAM (correlation rules), pas au vuln management. **Ne pas promettre de kill-chain / TTP mapping dans le talk track EM.**
