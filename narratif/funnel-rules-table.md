# Les 5 règles du funnel : source de vérité (v1.4)

Ces 5 Vulnerability Policies définissent la **création des issues** et leur sévérité en fonction de la criticité réelle et du contexte d'exposition. Elles sont **centrées sur le CVRS** (Cortex Vulnerability Risk Score, propriétaire Cortex) plutôt que sur le CVSS seul : c'est le principal différenciateur d'Exposure Management face à un scanner classique.

**v1.4 : simplification de 8 à 5 règles.** Huit règles étaient difficiles à expliquer en direct. Les cinq retenues couvrent les trois messages clés : exposition, angle mort interne, exploitabilité.

**Naming convention** : préfixe `EM-demo-POL-` (tenant XSIAM mutualisé). Les libellés narratifs FR servent au discours client, le nom technique est visible à l'écran.

## Tableau canonique (slide "Acte 1")

| Ref | Nom XSIAM (technique) | Libellé narratif FR | Condition | Périmètre (asset group) | Sévérité | SLA |
|-----|----------------------|---------------------|-----------|-------------------------|----------|-----|
| **R1** | `EM-demo-POL-R1-Critical-KEV-Internet-Exposed` | **Exploitation active périmètre** | `Has KEV = Yes OR EPSS ≥ 90 %` | Assets exposés | **Critique** | **48 h** |
| **R2** | `EM-demo-POL-R2-Critical-Perimeter-CVRS90` | **Urgence périmètre** | `CVRS ≥ 90` | Assets exposés | **Critique** | **72 h** |
| **R3** | `EM-demo-POL-R3-High-Internal-Tier0-KEV` | **Angle mort interne** | `Has KEV = Yes AND CVRS ≥ 90` | Tout Business Corp | **Haute** | **7 j** |
| **R4** | `EM-demo-POL-R4-High-Weaponized` | **Exploit prêt** | `CVRS ≥ 80 AND Exploitable = Yes` | Tout Business Corp | **Haute** | **14 j** |
| **R5** | `EM-demo-POL-R5-Medium-External-Surface` | **Réduction surface externe** | `CVRS ≤ 89` | Assets exposés | **Moyenne** | **30 j** |

Les policies sont évaluées **dans l'ordre, la première qui correspond gagne** (R1 → R5). Une vulnérabilité qui ne correspond à aucune règle ne crée pas d'issue (sauf policies par défaut du tenant).

### Pourquoi un périmètre « assets exposés » plutôt que `Internet Exposed = Yes`

Cortex ne déduit pas **Internet Exposed** d'une IP publique remontée par un scanner tiers : le flag vient de l'ASM / Cloud Network Analyzer, avec confirmation par un scan externe. Les IP de démo (plage TEST-NET 203.0.113.0/24, non routable) ne répondront jamais à ce scan, et le champ `internet_exposed` reste vide sur les assets Rapid7.

R1, R2 et R5 sont donc **cadrées sur un asset group** :

- **recommandé (v1.4)** : `EM-demo-grp-Business-Corp-exposed`, construit sur le tag `exposure:internet` émis par le sim pour les 6 assets à IP publique (`srv-vpn`, `srv-web-01`, `srv-web-02`, `srv-mail`, `srv-portail`, `smtp-relay`). Voir runbook 05.
- **variante** : les groupes de zone DMZ (`dmz-web` + `dmz-edge`). Attention, `srv-mail` (Exchange OWA, hero 2) est en zone `tier1` et n'y figure pas : il retombe alors dans R3.

Les clauses `Internet Exposed = Yes` peuvent rester dans les conditions : elles deviennent utiles en production, quand l'ASM est déployé.

En démo, le discours reste simple : « ces assets sont dans la zone exposée de Business Corp ».

## Pourquoi CVRS et pas CVSS ?

Le **CVRS** (Cortex Vulnerability Risk Score, 0 à 100, **par finding**) est calculé par Cortex à partir de 5 facteurs contextuels :

1. **Vulnerability Context** : CVSS base score
2. **Exploit Intelligence** : EPSS, CISA KEV, exploited-in-the-wild, maturité d'exploit
3. **Asset Risk** : Internet Exposed (ASM / CNA)
4. **Environment Risk** : Package-in-use (validé par Attack Surface Testing)
5. **Compensating Controls** : efficacité des contrôles (agent XDR, WAF, NGFW) sur cette CVE, **au niveau de cet asset précis**

**Le CVSS seul ne dit rien du contexte** : une CVE notée 10 sur un asset protégé par un WAF et un agent XDR présente un risque réel plus faible. Le CVRS reflète cette nuance par couple (CVE, asset).

## Correspondance avec les hero cases

Toutes les paires (asset, CVE) sont cohérentes avec l'OS et les logiciels de l'asset (v1.4, voir `config/catalogs-inventory.md`).

| Hero case (asset + CVE) | Règle attendue | Pourquoi cette règle (first-match) | Angle démo |
|-------------------------|----------------|------------------------------------|------------|
| **`srv-vpn` + CVE-2024-3400** (PAN-OS GlobalProtect) | **R1** | KEV sur asset exposé | Pare-feu VPN exposé, aucun agent possible |
| **`srv-mail` + CVE-2021-26855** (ProxyLogon) | **R1** | KEV sur asset exposé (srv-mail dans le groupe exposé) | Exchange OWA exposé, exploitation active documentée |
| **`srv-ad-01` + CVE-2020-1472** (Zerologon) | **R3** | KEV + CVRS ≥ 90, asset interne | Contrôleur de domaine Tier 0, mouvement latéral immédiat |
| **`srv-web-01` + CVE-2022-22965** (Spring4Shell) | **R1** | KEV sur asset exposé | Front web Java exposé, exploitation imminente |
| **`srv-ci` + CVE-2021-44228** (Log4Shell) | **R3** | KEV + CVRS ≥ 90, asset interne | CI Java, Package In Use confirmé par AST |
| **`srv-portail` + CVE-2016-3189** (bzip2) | **R5** | Non KEV, CVRS moyen, asset exposé | Vulnérabilité modérée mais visible depuis Internet |

Illustrations complémentaires (épinglées pour que chaque règle ait un exemple) :

| Asset + CVE | Règle attendue | Pourquoi |
|-------------|----------------|----------|
| `srv-web-01` + CVE-2024-38063 (Windows TCP/IP) | **R2** | Non KEV, CVRS ≥ 90 (≈ 97 observé), asset exposé |
| `srv-ci` + CVE-2024-23917 (TeamCity) | **R4** | Non KEV, exploitable, CVRS ≥ 80 (à valider sur le tenant) |

## Utilisation en démo

**Acte 1** (slide) : afficher ce tableau. Message : « Voici la grille de priorisation de Business Corp : 5 règles centrées sur le CVRS, qui remplacent le tri CVSS traditionnel. »

**Acte 3** (drill-down console) : pour chaque hero case, « cette issue est créée par la règle **R{n}**, voici pourquoi (breakdown CVRS dans Risk Details) ». La colonne **Open Issues** de la page Vulnerability Policies montre le volume par règle.

**Acte 4** (compensating controls) : un asset avec XDR + WAF a un CVRS plus bas qu'un asset identique sans contrôle (facteur Compensating Controls dans Risk Details).

## Personnalisation client

Les 5 règles sont **une proposition Business Corp**. Chaque client peut :

- ajuster les seuils CVRS (`≥ 90`, `≥ 80`, `≤ 89`) selon son appétit au risque ;
- ajouter des règles spécifiques (PCI-DSS, HDS, NIS2, souveraineté) ;
- modifier les SLA selon ses engagements internes ;
- remplacer le groupe « exposés » par le flag natif `Internet Exposed` dès que l'ASM est déployé ;
- renommer le préfixe `EM-demo-` (ex. `PROD-VulnMgmt-`) sur un tenant dédié.
