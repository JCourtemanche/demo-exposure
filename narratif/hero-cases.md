# Les 6 hero cases — storyline détaillée (v1.4, Rapid7 only)

Chaque hero case = **1 couple (asset, CVE) réel** issu du catalogue déterministe du simulateur Rapid7, qui déclenche **1 des 5 règles** du funnel (voir `funnel-rules-table.md`).

✅ **Reproductibilité** : les paires (asset, CVE) sont **épinglées** dans `config/business-corp-config.yaml` (`hero_pinning`) et injectées par le patch du runbook `02b`. Après `sync-config-to-sims.py` + redeploy, elles sont garanties à chaque ingestion XSIAM (après ~2 h de délai Vulnerability Intelligence).

✅ **Cohérence (v1.4)** : le simulateur n'attribue plus que des CVE applicables à l'OS et aux logiciels de chaque asset. Les heroes et les autres vulnérabilités visibles dans une issue sont donc défendables devant un client (plus d'Exchange sur un Mac ni de PAN-OS sur une Debian).

⚠️ **Internet Exposed** : le flag Cortex reste vide sur les assets Rapid7 (il vient de l'ASM / CNA, pas d'une IP remontée par un scanner). Ne pas promettre de badge « Internet Exposed » à l'écran : l'exposition est portée par l'asset group `EM-demo-grp-Business-Corp-exposed` (« la zone exposée de Business Corp »).

⚠️ **Cyberwatch a été retiré de la v1** : le pack Partner Contribution alimente `cyberwatch_generic_alert_raw` mais pas `asset_inventory` d'Exposure Management. Roadmap v2 : bridge via Vulnerability Ingest API.

---

## Hero Case 1 — Urgence périmètre (R1)

| Champ | Valeur |
|-------|--------|
| **Règle déclenchée** | **R1** — Exploitation active périmètre (KEV sur asset exposé) |
| **CVE principale** | CVE-2024-3400 (PAN-OS GlobalProtect command injection) |
| **Asset** | `srv-vpn.business.org` : pare-feu **PAN-OS 10.2** (natif Rapid7, OS surchargé par `os_overrides`) |
| **IP publique** | 203.0.113.5 |
| **Périmètre** | groupe exposé, zone `dmz-edge` |
| **CVRS attendu** | ≥ 95 |
| **Compensating Control** | **Aucun** : pas d'agent installable sur un pare-feu, et le NGFW ne se protège pas lui-même |
| **SLA** | 48 h |

**Talk track (30 sec)** :
> « Voici notre pare-feu VPN GlobalProtect, adresse publique 203.0.113.5, joignable depuis Internet 24/7. Il porte CVE-2024-3400, la vulnérabilité PAN-OS qui a fait la une : injection de commande sans authentification, exploitée activement, dans le catalogue CISA KEV. Aucun agent ne peut être installé sur ce type d'équipement. **Règle R1, SLA 48 h. C'est LE dossier du lundi matin.** »

**Ce qu'on montre à l'écran** :
- Vue issue → CVRS ≈ 96, badge KEV
- Asset : OS PAN-OS, asset group `EM-demo-grp-Business-Corp-exposed`
- Onglet Risk Details : Compensating Controls = Not Effective / Unknown
- Policy : `EM-demo-POL-R1-Critical-KEV-Internet-Exposed`

---

## Hero Case 2 — Exploitation active périmètre (R1)

| Champ | Valeur |
|-------|--------|
| **Règle déclenchée** | **R1** — Exploitation active périmètre (KEV sur asset exposé) |
| **CVE principale** | CVE-2021-26855 (ProxyLogon Exchange Server SSRF) |
| **Asset** | `srv-mail.business.org` (Windows Server 2019 + Exchange, natif Rapid7) |
| **IP publique** | 203.0.113.20 |
| **Périmètre** | groupe exposé (zone `tier1`, Exchange publié via OWA) |
| **CVRS attendu** | 85-95 |
| **Compensating Control** | XDR Windows présent, mais ne bloque pas la chaîne d'exploitation SSRF → RCE |
| **SLA** | 48 h |

⚠️ srv-mail n'est pas en zone DMZ : il faut que R1 soit cadrée sur le groupe « exposés » (tag `exposure:internet`), sinon ce ProxyLogon tombe dans R3.

**Talk track (30 sec)** :
> « Notre Exchange, exposé pour l'accès webmail. ProxyLogon est dans le catalogue CISA KEV depuis 2021 : des scanners automatiques cherchent cette faille sur Internet 24 h/24. **Le badge KEV nous dit "un attaquant lambda peut le faire ce soir".** Règle R1, SLA 48 h. Priorité absolue. »

**Ce qu'on montre à l'écran** :
- Overview → badge « In CISA KEV »
- Facteur Exploit Intelligence : exploited in the wild, maturité d'exploit élevée
- Sur le même serveur, les autres CVE sont toutes des failles Exchange / Windows Server (ProxyNotShell, PrintNightmare…) : cohérent

---

## Hero Case 3 — Le maillon faible interne (R3)

| Champ | Valeur |
|-------|--------|
| **Règle déclenchée** | **R3** — Angle mort interne (KEV + CVRS ≥ 90, asset interne) |
| **CVE principale** | CVE-2020-1472 (Zerologon, Netlogon) |
| **Asset** | `srv-ad-01.business.org` (contrôleur de domaine, Windows Server 2022, natif Rapid7) |
| **IP publique** | Aucune, asset interne |
| **Zone** | `tier0` (identité) |
| **CVRS attendu** | 90-95 (KEV + CVSS 10 sans contrôle compensatoire) |
| **Compensating Control** | **Aucun** : le DC a été exclu du déploiement de l'agent XDR (runbook 06) |
| **SLA** | 7 j |

v1.4 : déplacé de `srv-adfs-01` vers `srv-ad-01`. Zerologon est une faille du protocole Netlogon des **contrôleurs de domaine**, pas d'un serveur ADFS.

**Talk track (60 sec, temps fort pédagogique)** :
> « Regardez notre contrôleur de domaine. Tier 0. CVSS 10 pour Zerologon. Il n'est PAS exposé à Internet : on pourrait penser "moins urgent". Sauf que **son CVRS reste à 92**. Pourquoi ? Parce que Cortex regarde quels contrôles compensatoires entourent cet actif, et la réponse est : aucun. Lors du projet de déploiement, le DC a été exclu de l'agent XDR par crainte d'impact sur l'authentification. Un attaquant déjà dans le réseau, via phishing, ransomware ou insider, devient administrateur du domaine en quelques secondes et compromet TOUTE l'entreprise. **C'est le maillon faible du blast radius d'une intrusion. Règle R3.** »

**Ce qu'on montre à l'écran** :
- Overview → CVRS ≈ 92, badge KEV
- Onglet Risk Details → Compensating Controls = Not Effective / Unknown
- Asset group : `EM-demo-business-tier0`
- Comparaison : la même faille Windows (ex. PrintNightmare) sur `srv-fs-01`, couvert par l'agent XDR, a un CVRS plus bas

---

## Hero Case 4 — Exploit prêt sur front web exposé (R1)

| Champ | Valeur |
|-------|--------|
| **Règle déclenchée** | **R1** — Exploitation active périmètre (KEV / EPSS élevé sur asset exposé) |
| **CVE principale** | CVE-2022-22965 (Spring4Shell, Spring Framework RCE) |
| **Asset** | `srv-web-01.business.org` (Windows Server 2019, application Java / Spring sous Tomcat) |
| **IP publique** | 203.0.113.10 |
| **Périmètre** | groupe exposé, zone `dmz-web` |
| **CVRS attendu** | 85-95 |
| **Compensating Control** | WAF F5 en amont, « Partially Effective » (bloque les signatures connues, pas les variantes) |
| **SLA** | 48 h |

**Talk track (40 sec)** :
> « Ici, Spring4Shell sur notre front web Java. **Son EPSS est très élevé** : forte probabilité d'exploitation dans les 30 prochains jours, et elle est désormais dans le catalogue KEV. Un correctif existe (Spring 5.3.18+). Le WAF F5 en amont aide, mais Cortex l'évalue "partiellement efficace" : la RCE Spring passe avec des payloads que le WAF ne connaît pas. Règle R1 : on n'attend pas. »

**Ce qu'on montre à l'écran** :
- Overview → score EPSS + badge KEV
- Fix Available : True
- Risk Details : Compensating Controls = Partially Effective (WAF)

Sur ce même serveur, **CVE-2024-38063** (Windows TCP/IP, non KEV, CVRS ≈ 97) illustre **R2** « Urgence périmètre » : critique contextualisée sur un asset exposé, même sans exploitation documentée.

---

## Hero Case 5 — Risque confirmé sur workload interne (R3)

| Champ | Valeur |
|-------|--------|
| **Règle déclenchée** | **R3** — Angle mort interne (KEV + CVRS ≥ 90) |
| **CVE principale** | CVE-2021-44228 (Log4Shell, Apache Log4j) |
| **Asset** | `srv-ci.business.org` (Ubuntu 22.04, CI Java / TeamCity, natif Rapid7) |
| **IP publique** | Aucune (CI interne) |
| **Zone** | `cicd` |
| **CVRS attendu** | 90-95 |
| **Compensating Control** | XDR Linux présent, mais Java runtime en usage confirmé → Environment Risk élevé |
| **SLA** | 7 j |

**Talk track (45 sec)** :
> « Log4Shell, encore. Mais ici, Cortex Attack Surface Testing a vérifié que **le package log4j-core est bien chargé par un process actif** de notre CI. C'est ce que Cortex appelle "Package In Use" : ça élimine les faux positifs "la lib est installée mais jamais lancée". **Sur des milliers d'alertes Log4Shell qu'un scanner classique remonte, celle-ci est vraiment exploitable.** Règle R3. »

**Ce qu'on montre à l'écran** :
- Risk Details → Environment Risk = « Package In Use » (validé par AST)
- Sur le même serveur, **CVE-2024-23917** (TeamCity, non KEV, exploitable) illustre **R4** « Exploit prêt »

---

## Hero Case 6 — Surface externe (R5)

| Champ | Valeur |
|-------|--------|
| **Règle déclenchée** | **R5** — Réduction surface externe (CVRS ≤ 89 sur asset exposé) |
| **CVE principale** | CVE-2016-3189 (bzip2 use-after-free) |
| **Asset** | `srv-portail.business.org` (Ubuntu 22.04, portail de transfert type GoAnywhere MFT, **extra BC**) |
| **IP publique** | 203.0.113.30 |
| **Périmètre** | groupe exposé, zone `dmz-web` |
| **CVRS attendu** | 60-75 |
| **Compensating Control** | WAF F5 présent, « Partially Effective » (le WAF ne protège pas un parseur binaire) |
| **SLA** | 30 j |

**Talk track (30 sec)** :
> « Enfin, les vulnérabilités moyennes mais visibles depuis Internet. Elles ne mettront pas le SI par terre, mais **elles apparaissent quand un attaquant cartographie votre entreprise**. On les traite en hygiène de surface externe via la règle R5 : SLA 30 jours, dans le cycle de patch mensuel. »

**Ce qu'on montre à l'écran** :
- Liste des issues : sévérité Medium, après les précédentes
- Overview → CVRS ≈ 68, asset dans le groupe exposé

---

## Synthèse — ce que le client doit retenir

1. **Le funnel est explicable** : chaque issue coche une règle R1 à R5 claire, avec des preuves dans Risk Details
2. **CVRS ≠ CVSS** : le CVRS intègre l'exposition, l'exploitabilité active et les contrôles compensatoires ; un CVSS 10 sur un actif bien protégé peut redescendre nettement
3. **Les contrôles compensatoires valorisent l'existant** : agent XDR, WAF, NGFW modifient activement la priorisation
4. **Le « maillon faible » R3 (hero 3) est le message clé** : les scanners classiques crient sur tous les CVSS 10, alors que le vrai risque est l'actif Tier 0 oublié, sans agent
5. **Les SLA sont explicites** : 48 h / 72 h / 7 j / 14 j / 30 j

## Cheatsheet des CVE épinglées

| CVE | Nom court | Asset épinglé | Règle | Rôle |
|-----|-----------|---------------|-------|------|
| CVE-2024-3400 | PAN-OS GlobalProtect | `srv-vpn.business.org` (PAN-OS) | R1 | Hero 1 |
| CVE-2021-26855 | ProxyLogon | `srv-mail.business.org` | R1 | Hero 2 |
| CVE-2020-1472 | Zerologon | `srv-ad-01.business.org` | R3 | Hero 3 |
| CVE-2022-22965 | Spring4Shell | `srv-web-01.business.org` | R1 | Hero 4 |
| CVE-2021-44228 | Log4Shell | `srv-ci.business.org` | R3 | Hero 5 |
| CVE-2016-3189 | bzip2 use-after-free | `srv-portail.business.org` | R5 | Hero 6 |
| CVE-2024-38063 | Windows TCP/IP RCE | `srv-web-01.business.org` | R2 | Illustration R2 |
| CVE-2024-23917 | TeamCity auth bypass | `srv-ci.business.org` | R4 | Illustration R4 |
| CVE-2024-38063 | Windows TCP/IP RCE | `BSNS-WIN-ALICE`, `CHARLIE`, `DAVID` | R4 (non KEV, exploitable) | Scénario Intune |
| CVE-2023-42917 | Apple WebKit | `BSNS-MAC-EMMA`, `BSNS-MOB-FLORA` | R3 ou R4 (selon CVRS) | Scénario Intune |

Toutes présentes dans le `VULN_CATALOG_SEED` du sim Rapid7 (voir `config/catalogs-inventory.md`). Les CVE du scénario Intune servent la démo de remédiation du repo [intune-simul](https://github.com/JCourtemanche/intune-simul).

Pour changer un épinglage : éditer `config/business-corp-config.yaml` (`hero_pinning`), relancer `python config/sync-config-to-sims.py`, puis redéployer Cloud Run. Une CVE épinglée sur un asset incompatible est acceptée (choix explicite), mais elle casse la cohérence : préférer une CVE compatible avec l'OS et les rôles de l'asset.
