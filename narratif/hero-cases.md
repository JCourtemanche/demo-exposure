# Les 6 hero cases — storyline détaillée (v1 Rapid7 only)

Chaque hero case = **1 (asset, CVE) réel** issu du catalogue déterministe du simulateur Rapid7, qui déclenche **1 des 8 règles narratives** du funnel (voir `funnel-rules-table.md`).

✅ **Garantie de reproductibilité** : les 6 paires (asset, CVE) sont **pinnées** dans `config/business-corp-config.yaml` et injectées via le patch du runbook `02b`. Après `sync-config-to-sims.py` + redeploy, ces paires sont **garanties** à chaque ingestion XSIAM (après ~2h de délai Vulnerability Intelligence).

⚠️ **Cyberwatch a été retiré de la v1** — le pack Partner Contribution alimente `cyberwatch_generic_alert_raw` mais pas `asset_inventory` d'Exposure Management. Roadmap v2 : bridge via Vulnerability Ingest API.

---

## Hero Case 1 — Urgence Périmètre (R2)

| Champ | Valeur |
|-------|--------|
| **Règle déclenchée** | **R2** — Urgence périmètre (CVRS ≥ 90 + Internet Exposed) |
| **CVE principale** | CVE-2024-3400 (PAN-OS GlobalProtect command injection) |
| **Asset** | `srv-vpn.business.org` (natif Rapid7) |
| **IP publique** | 203.0.113.5 (marque Internet Exposed pour Cortex) |
| **Zone** | `zone-dmz-edge` |
| **CVRS attendu** | ≥ 95 |
| **Compensating Control** | NGFW présent MAIS "Not Effective" pour exploitation applicative (couche 7) |
| **SLA** | 72 h |

**Talk track (30 sec)** :
> "Voici notre boîtier VPN. Adresse publique 203.0.113.5, exposé Internet 24/7. Il porte CVE-2024-3400, la vulnérabilité PAN-OS qui a fait la une l'an dernier. CVRS de 96 sur 100. Le NGFW en amont ne peut rien : c'est une injection dans le protocole applicatif. **Règle R2 déclenchée, SLA 72h. C'est LE dossier du lundi matin.**"

**Ce qu'on montre à l'écran** :
- Vue Case → CVRS chip = 96
- Onglet Overview : badge "Internet Exposed" (ASM inféré via public IP) + "In CISA KEV"
- Onglet Risk Details : Asset Risk = High, Compensating Controls = Not Effective
- Vulnerability Policy = `POL-BC-R2-Urgence-Perimetre` déclenchée

---

## Hero Case 2 — Feu de forêt (R1)

| Champ | Valeur |
|-------|--------|
| **Règle déclenchée** | **R1** — Feu de forêt (KEV OR EPSS≥0.9) + Internet Exposed |
| **CVE principale** | CVE-2021-26855 (ProxyLogon Exchange Server SSRF) |
| **Asset** | `srv-mail.business.org` (natif Rapid7) |
| **IP publique** | 203.0.113.20 |
| **Zone** | `zone-tier1` (Exchange exposé via OWA) |
| **CVRS attendu** | 85-95 |
| **Compensating Control** | XDR Windows présent, mais règle EPP ne bloque pas la chaîne d'exploitation SSRF → RCE |
| **SLA** | 48 h |

**Talk track (30 sec)** :
> "Notre Exchange, exposé pour l'accès webmail. ProxyLogon est dans le catalogue CISA KEV depuis 2021 : ça veut dire qu'il existe des scanners automatiques qui cherchent cette faille sur Internet 24h/24. Même score CVSS que d'autres, mais **le badge KEV nous dit 'un attaquant lambda peut le faire ce soir'**. Règle R1 Feu de forêt : SLA 48h. Priorité absolue."

**Ce qu'on montre à l'écran** :
- Overview → badge orange "In CISA KEV"
- Exploit Intelligence facteur : "Exploited in the wild" + Exploit Maturity = High
- Lien vers Vulnerability Intelligence page → historique d'exploitation ITW

---

## Hero Case 3 — Le Maillon Faible Interne (R3)

| Champ | Valeur |
|-------|--------|
| **Règle déclenchée** | **R3** — Maillon faible interne (KEV + CVRS≥90 + Interne + Tier 0) |
| **CVE principale** | CVE-2020-1472 (Zerologon — Netlogon protocol RCE) |
| **Asset** | `srv-adfs-01.business.org` (**extra BC** injecté) |
| **IP publique** | Aucune — asset interne |
| **Zone** | `zone-tier0` (identité fédération SSO) |
| **CVRS attendu** | 90-95 (KEV + CVSS 10 sans compensating control) |
| **Compensating Control** | **AUCUN** — ADFS traité comme appliance, pas d'agent XDR Windows Server déployé |
| **SLA** | 7 j |

**Talk track (60 sec — temps fort pédagogique)** :
> "Regardez cet ADFS, notre fédération d'identité SAML/OIDC. Tier 0. CVSS 10 pour Zerologon. Il n'est PAS exposé Internet. On pourrait penser 'moins urgent'. Sauf que **son CVRS reste à 92** — quasi identique au CVSS. Pourquoi ? Parce que Cortex regarde 'quels contrôles compensatoires j'ai autour de cet actif ?' — et là, la réponse est : aucun. Pas d'agent XDR (l'équipe SecOps considère l'ADFS comme une appliance et n'a jamais déployé l'agent), pas de segmentation stricte. Un attaquant qui est déjà dans le réseau — via phishing, ransomware, insider — trouve un chemin direct vers l'ADFS et de là compromet TOUTE l'authentification de l'entreprise. **C'est le maillon faible du blast radius d'une intrusion. Règle R3.**"

**Ce qu'on montre à l'écran** :
- Overview → CVRS ≈ 92, badge KEV, Internet Exposed = False
- Onglet Risk Details → facteur "Compensating Controls" = badge rouge "Not Effective" ou "Unknown"
- Asset Group : `grp-business-tier0` — c'est le trigger de la partie "Asset Group in {Prod critique}" de R3
- Comparer côte-à-côte : ce même Zerologon sur un serveur Windows Tier 1 avec XDR (CVRS descend à 55-60)

---

## Hero Case 4 — Exploit prêt (R4) — variante EPSS/Weaponized

| Champ | Valeur |
|-------|--------|
| **Règle déclenchée** | **R4** — Exploit prêt sans compensation (EPSS≥0.7 + CVRS≥80 + Fix Available) |
| **CVE principale** | CVE-2022-22965 (Spring4Shell — Spring Framework RCE) |
| **Asset** | `srv-web-01.business.org` (natif Rapid7) |
| **IP publique** | 203.0.113.10 |
| **Zone** | `zone-dmz-web` |
| **CVRS attendu** | 80-90 (EPSS élevé + Weaponized) |
| **Compensating Control** | WAF F5 en amont — "Partially Effective" (bloque signature basique mais pas variantes) |
| **SLA** | 14 j |

**Talk track (40 sec)** :
> "Ici, Spring4Shell, CVE-2022-22965. Elle n'est pas dans le top KEV, mais **son EPSS est à 87%** : ça veut dire qu'il y a 87% de probabilité qu'elle soit exploitée dans les 30 prochains jours. C'est la métrique prédictive. **Un patch existe (Spring 5.3.18+)** — la règle R4 déclenche, SLA 14 jours. On ne veut pas attendre qu'elle passe KEV pour agir. Le WAF F5 en amont aide, mais Cortex l'évalue 'Partiellement Efficace' — la RCE Spring peut se déclencher sur des payloads que le WAF ne connaît pas."

**Ce qu'on montre à l'écran** :
- Overview → EPSS bar quasi pleine + score numérique (0.87)
- Onglet Exploit Intelligence → note "High probability of exploitation in the next 30 days" + Weaponized
- Fix Available : True (badge patch disponible)

---

## Hero Case 5 — Exploit prêt (R4) — variante Package-in-use

| Champ | Valeur |
|-------|--------|
| **Règle déclenchée** | **R4** — Exploit prêt sans compensation (validé par Package-In-Use) |
| **CVE principale** | CVE-2021-44228 (Log4Shell — Apache Log4j) |
| **Asset** | `srv-ci.business.org` (natif Rapid7) |
| **IP publique** | Aucune (CI interne) |
| **Zone** | `zone-cicd` |
| **CVRS attendu** | 85-95 |
| **Compensating Control** | XDR Linux présent, mais Java runtime en usage confirmé → Environment Risk élevé |
| **SLA** | 14 j |

**Talk track (45 sec)** :
> "Log4Shell, encore. Mais ici c'est différent : Cortex Attack Surface Testing a vérifié que **le package log4j-core est bien chargé en mémoire par un process actif** — dans notre cas, un Jenkins CI. C'est ce que Cortex appelle 'Package In Use'. Ça élimine tous les faux positifs 'j'ai la lib installée mais jamais lancée'. **Sur des milliers d'alertes Log4Shell qu'un scanner classique remonte, celui-ci est le SEUL vraiment exploitable.** Règle R4 : Log4Shell dispose d'un patch (Log4j 2.17.1), SLA 14 jours."

**Ce qu'on montre à l'écran** :
- Onglet Risk Details → facteur "Environment Risk" = "Package In Use" (validé par AST)
- Contraste avec un autre asset ayant Log4Shell "présent mais non chargé" → CVRS 30-40, aucune règle ne déclenche

---

## Hero Case 6 — Surface externe (R7)

| Champ | Valeur |
|-------|--------|
| **Règle déclenchée** | **R7** — Surface externe à surveiller (CVRS moyen + Internet Exposed) |
| **CVE principale** | CVE-2016-3189 (bzip2 use-after-free) |
| **Asset** | `srv-portail.business.org` (**extra BC** injecté) |
| **IP publique** | 203.0.113.30 |
| **Zone** | `zone-dmz-web` |
| **CVRS attendu** | 60-75 |
| **Compensating Control** | WAF F5 présent → "Partially Effective" (WAF ne bloque pas parseur binaire) |
| **SLA** | 30 j |

**Talk track (30 sec)** :
> "Enfin, la dernière catégorie : les vulns moyennes mais visibles depuis Internet. Elles ne mettront pas le SI par terre, mais **elles apparaissent sur Shodan quand un attaquant scanne votre entreprise**. On les traite en 'hygiène surface externe' via règle R7 : moins urgent, SLA 30 jours, dans le pipeline patch mensuel. Objectif : faire disparaître Business Corp des radars d'attaquants opportunistes."

**Ce qu'on montre à l'écran** :
- Vue liste des cases : cette case est en sévérité "Medium", après les 5 précédentes
- Overview → CVRS ~68, Internet Exposed = True (via public IP 203.0.113.30)

---

## Synthèse — Ce que le client doit retenir en sortie

1. **Le funnel n'est pas magique — il est explicable** : chaque case coche une règle R1-R8 claire, avec des preuves consultables dans Risk Details
2. **CVRS ≠ CVSS** : le CVRS intègre l'exposition, l'exploitabilité active, les contrôles compensatoires → un CVSS 10 sur un actif bien protégé peut redescendre à CVRS 40 (et donc sortir du top des cases)
3. **Compensating controls valorisent votre investissement existant** : XDR agent, WAF, NGFW ne sont pas juste des lignes budget — ils **modifient activement la priorisation** des vulnérabilités
4. **Le "Maillon Faible" R3 (hero 3) est le message clé de l'ROI** : c'est là que les scanners classiques ratent l'essentiel (ils crient sur toutes les CVSS 10) alors que le vrai risque est l'actif oublié sans agent en Tier 0
5. **Les SLA sont explicites et défendables** : 48h/72h/7j/14j/30j/90j — cadre clair pour l'équipe Ops et pour les instances de gouvernance

## Cheatsheet des CVE pinnées

| CVE | Nom court | Asset pinné | Règle | Sim source |
|-----|-----------|-------------|-------|------------|
| CVE-2024-3400 | PAN-OS GlobalProtect | `srv-vpn.business.org` | R2 Urgence périmètre | Rapid7 |
| CVE-2021-26855 | ProxyLogon | `srv-mail.business.org` | R1 Feu de forêt | Rapid7 |
| CVE-2020-1472 | Zerologon | `srv-adfs-01.business.org` | R3 Maillon faible | Rapid7 (extra BC) |
| CVE-2022-22965 | Spring4Shell | `srv-web-01.business.org` | R4 Exploit prêt (EPSS) | Rapid7 |
| CVE-2021-44228 | Log4Shell | `srv-ci.business.org` | R4 Exploit prêt (Package-in-use) | Rapid7 |
| CVE-2016-3189 | bzip2 use-after-free | `srv-portail.business.org` | R7 Surface externe | Rapid7 (extra BC) |

Toutes présentes dans le `VULN_CATALOG_SEED` de Rapid7 (voir `config/catalogs-inventory.md`).

Pour changer un pinning : éditer `config/business-corp-config.yaml`, section `hero_pinning`, puis relancer `python config/sync-config-to-sims.py` + redeploy Cloud Run.
