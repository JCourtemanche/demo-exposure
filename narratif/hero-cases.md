# Les 6 hero cases — storyline détaillée

Chaque hero case = **1 (asset, CVE) réel** issu des catalogues déterministes des simulateurs Rapid7 et Cyberwatch, qui illustre **1 des 6 règles narratives** du funnel.

✅ **Garantie de reproductibilité** : les 6 paires (asset, CVE) ci-dessous sont **pinnées** dans `config/business-corp-config.yaml` et injectées via le patch du runbook `02b`. Après `sync-config-to-sims.py` + redeploy, ces paires sont **garanties** à chaque ingestion XSIAM. Les "Plan B" ne servent plus que si vous choisissez volontairement de retirer un pinning.

## Hero Case 1 — Urgence Périmètre

| Champ | Valeur |
|-------|--------|
| **Règle** | 1 — CVRS ≥ 90 + Internet Exposed |
| **CVE principale** | CVE-2024-3400 (PAN-OS GlobalProtect command injection) |
| **Plan B** | CVE-2021-44228 (Log4Shell) si CVE-2024-3400 absente du catalogue Rapid7 |
| **Asset** | `srv-vpn.business.org` (natif Rapid7+CW, tagué comme boîtier VPN) — ou `srv-web-01` (Ubuntu) pour plan B |
| **Zone** | `zone-dmz-edge` (ou `zone-dmz-web` plan B) |
| **Source ingestion** | Rapid7 InsightVM sim |
| **CVRS attendu** | ≥ 95 |
| **Compensating Control** | NGFW présent MAIS "Not Effective" pour exploitation applicative (couche 7) |

**Talk track (30 sec)** :
> "Voici notre boîtier VPN, exposé sur Internet. Il porte CVE-2024-3400, la vulnérabilité qui a fait la une l'an dernier. CVRS de 96 sur 100. Le NGFW en amont ne peut rien : c'est une injection dans le protocole applicatif. **C'est LE dossier du lundi matin.**"

**Ce qu'on montre à l'écran** :
- Vue Case → CVRS chip = 96
- Onglet Overview : badge "Internet Exposed" (ASM) + "In CISA KEV"
- Onglet Risk Details : Asset Risk = High, Compensating Controls = Not Effective

---

## Hero Case 2 — Arme aux mains de l'ennemi

| Champ | Valeur |
|-------|--------|
| **Règle** | 2 — CISA KEV + Internet Exposed |
| **CVE principale** | CVE-2021-26855 (ProxyLogon Exchange Server SSRF) |
| **Plan B** | CVE-2023-34362 (MOVEit Transfer SQL injection) |
| **Asset** | `srv-mail.business.org` (Exchange) — ou `srv-portail.business.org` (portail transfert) |
| **Zone** | `zone-tier1` (Exchange exposé via reverse proxy DMZ) |
| **Source ingestion** | Rapid7 InsightVM sim (+ potentiellement Cyberwatch dédup) |
| **CVRS attendu** | 85-95 |
| **Compensating Control** | XDR Windows présent, mais règle EPP ne bloque pas la chaîne d'exploitation SSRF → RCE |

**Talk track (30 sec)** :
> "Notre Exchange, exposé pour l'accès webmail. ProxyLogon est dans le catalogue CISA KEV depuis 2021 : ça veut dire qu'il existe des scanners automatiques qui cherchent cette faille sur Internet 24h/24. Même score CVSS que d'autres, mais **le badge KEV nous dit "un attaquant lambda peut le faire ce soir"**. Priorité absolue."

**Ce qu'on montre à l'écran** :
- Overview → badge orange "In CISA KEV"
- Exploit Intelligence facteur : "Exploited in the wild" + Exploit Maturity = High
- Lien vers Vulnerability Intelligence page → historique d'exploitation

---

## Hero Case 3 — Le Maillon Faible (Interne)

| Champ | Valeur |
|-------|--------|
| **Règle** | 3 — CVSS ≥ 8 + Compensating Control = None |
| **CVE principale** | CVE-2020-1472 (Zerologon) sur AD **OU** CVE-2021-21985 (vSphere Client RCE) sur ESXi |
| **Plan B** | Toute CVE CVSS ≥ 9 sur `esxi-01`, `nas-01`, `srv-print.business.org` |
| **Asset** | `esxi-01.business.org` (préféré — appliance sans agent possible) |
| **Zone** | `zone-infra` |
| **Source ingestion** | Rapid7 InsightVM sim (scanner réseau détecte l'ESXi) |
| **CVRS attendu** | 75-85 (ne bénéficie pas de la baisse "Compensating Control = Effective") |
| **Compensating Control** | **AUCUN** — c'est le point clé |

**Talk track (60 sec — plus long car pédagogique)** :
> "Regardez cet ESXi. CVSS 9.8. Pas exposé Internet, donc on pourrait penser 'moins urgent'. Sauf que **son CVRS reste à 85** — quasi identique au CVSS. Pourquoi ? Parce que Cortex regarde 'quels contrôles compensatoires j'ai autour de cet actif ?' — et là, la réponse est : aucun. Pas d'agent XDR (impossible sur appliance ESXi), pas de segmentation stricte. Un attaquant qui est déjà dans le réseau — via phishing, rançongiciel, insider — trouve un chemin direct vers l'hyperviseur qui héberge vos VMs critiques. **C'est le maillon faible du blast radius d'une intrusion.**"

**Ce qu'on montre à l'écran** :
- Onglet Risk Details → facteur "Compensating Controls" = badge gris "Unknown" ou rouge "Not Effective"
- Comparer côte-à-côte : ce même CVE sur un serveur Windows Tier 1 avec XDR (CVRS descend à 55-60)

---

## Hero Case 4 — Menace Imminente (EPSS)

| Champ | Valeur |
|-------|--------|
| **Règle** | 4 — EPSS > 90% + Internet Exposed |
| **CVE principale** | CVE-2022-30190 (Follina — MSDT RCE via document Office) |
| **Plan B** | CVE-2022-22965 (Spring4Shell) sur `srv-web-01` |
| **Asset** | `alice.business.org` (endpoint Windows recevant emails externes) — ou serveur Spring |
| **Zone** | `zone-endpoints-win` |
| **Source ingestion** | Cyberwatch sim (a l'EPSS natif) |
| **CVRS attendu** | 75-85 (EPSS pousse le score) |
| **Compensating Control** | XDR Windows présent — "Partially Effective" (bloque exécution mais pas ouverture initiale) |

**Talk track (40 sec)** :
> "Ici, Follina, CVE-2022-30190. Elle n'est plus dans le top KEV, mais **son EPSS est à 97%** : ça veut dire qu'il y a 97% de probabilité qu'elle soit exploitée dans les 30 prochains jours. C'est la métrique prédictive. Sur les postes Windows recevant des emails externes, c'est le vecteur d'entrée typique d'un ransomware. **On ne veut pas attendre qu'elle passe KEV pour agir.**"

**Ce qu'on montre à l'écran** :
- Overview → EPSS bar quasi pleine + score numérique (0.97)
- Onglet Exploit Intelligence → note "High probability of exploitation in the next 30 days"

---

## Hero Case 5 — Risque Confirmé (Workload)

| Champ | Valeur |
|-------|--------|
| **Règle** | 5 — CVRS ≥ 70 + Package-in-use |
| **CVE principale** | CVE-2021-44228 (Log4Shell) — bibliothèque `log4j-core` |
| **Plan B** | CVE-2022-22965 Spring4Shell si Log4j déjà utilisé en case 1 |
| **Asset** | `srv-ci.business.org` (Ubuntu + Java runtime pour builds) |
| **Zone** | `zone-cicd` |
| **Source ingestion** | Rapid7 (détection package) + validation Cortex Attack Surface Testing |
| **CVRS attendu** | 80-90 |
| **Compensating Control** | XDR Linux présent, mais Java runtime en usage confirmé → Environment Risk élevé |

**Talk track (45 sec)** :
> "Log4Shell, encore. Mais ici c'est différent : Cortex Attack Surface Testing a vérifié que **le package log4j-core est bien chargé en mémoire par un process actif** — dans notre cas, un Jenkins CI. C'est ce que Cortex appelle 'Package in Use'. Ça élimine tous les faux positifs 'j'ai la lib installée mais jamais lancée'. **Sur des milliers d'alertes Log4Shell qu'un scanner classique remonte, celui-ci est le SEUL vraiment exploitable.**"

**Ce qu'on montre à l'écran** :
- Onglet Risk Details → facteur "Environment Risk" = "Package In Use" (validé par AST)
- Contraste avec un autre asset ayant Log4Shell "présent mais non chargé" → CVRS 30-40

---

## Hero Case 6 — Nettoyage de Surface

| Champ | Valeur |
|-------|--------|
| **Règle** | 6 — CVRS 60-80 + Internet Exposed |
| **CVE principale** | CVE-2016-3189 (bzip2 use-after-free, CVSS 6.5) — présent dans les 2 catalogues |
| **Plan B** | CVE-2023-24880 SmartScreen bypass (CVSS 5.4 + KEV, hybride intéressant) |
| **Asset** | `srv-portail.business.org` (portail public de transfert) |
| **Zone** | `zone-dmz-web` |
| **Source ingestion** | Rapid7 InsightVM sim |
| **CVRS attendu** | 60-75 |
| **Compensating Control** | WAF F5 présent → "Partially Effective" (WAF ne bloque pas signature TLS) |

**Talk track (30 sec)** :
> "Enfin, la dernière catégorie : les vulns moyennes mais visibles depuis Internet. Elles ne mettront pas le SI par terre, mais **elles apparaissent sur Shodan quand un attaquant scanne votre entreprise**. On les traite en 'nettoyage de surface' : moins urgent, mais dans le pipeline patch mensuel. Objectif : faire disparaître Business Corp des radars d'attaquants opportunistes."

**Ce qu'on montre à l'écran** :
- Vue liste des cases : cette case est en sévérité "Medium", après les 5 précédentes
- Overview → CVRS ~68, Internet Exposed = True

---

## Synthèse — Ce que le client doit retenir en sortie

1. **Le funnel n'est pas magique — il est explicable** : chaque case coche une règle claire, avec des preuves consultables dans Risk Details
2. **CVRS ≠ CVSS** : le CVRS intègre l'exposition, l'exploitabilité active, les contrôles compensatoires → un CVSS 10 sur un actif bien protégé peut redescendre à CVRS 40 (et donc sortir du top des cases)
3. **Compensating controls valorisent votre investissement existant** : XDR agent, WAF, NGFW ne sont pas juste des lignes budget — ils **modifient activement la priorisation** des vulnérabilités
4. **Le "Maillon Faible" (hero 3) est le message clé de l'ROI** : c'est là que les scanners classiques ratent l'essentiel (ils crient sur toutes les CVSS 10) alors que le vrai risque est l'actif oublié sans agent

## Cheatsheet des CVE pinnées (garanties via `business-corp-config.yaml`)

| CVE | Nom court | Asset pinné | Sim source | Hero |
|-----|-----------|-------------|------------|------|
| CVE-2024-3400 | PAN-OS GlobalProtect | `srv-vpn.business.org` | Rapid7 + CW | Hero 1 |
| CVE-2021-26855 | ProxyLogon | `srv-mail.business.org` | Rapid7 | Hero 2 |
| CVE-2020-1472 | Zerologon (proxy narratif ESXi) | `esxi-01.business.org` | Cyberwatch | Hero 3 |
| CVE-2022-30190 | Follina | `alice.business.org` | Cyberwatch (EPSS natif) | Hero 4 |
| CVE-2021-44228 | Log4Shell | `srv-ci.business.org` | Rapid7 | Hero 5 |
| CVE-2016-3189 | bzip2 use-after-free | `srv-portail.business.org` | Rapid7 | Hero 6 |

Toutes présentes dans le catalogue commun des 2 sims (voir `config/catalogs-inventory.md`).

Pour changer un pinning : éditer `config/business-corp-config.yaml`, section `hero_pinning`, puis relancer `python config/sync-config-to-sims.py` + redeploy Cloud Run.
