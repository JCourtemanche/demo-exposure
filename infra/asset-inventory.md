# Business Corp — Inventaire des actifs focus

Les **24 actifs focus** qui portent la narration de la démo. Ils sont taggés dans XSIAM (voir `runbook/05-create-tags-and-groups.md`) et rattachés aux compensating controls (voir `runbook/06-declare-compensating-controls.md`).

**Origine des assets** :
- **Natif** = présent nativement dans `EXTRA_SERVER_SEED` (Rapid7 et/ou Cyberwatch) ou dans les personas partagées `xsiam-shared-personas`
- **Custom** = ajouté via `config/business-corp-config.yaml` (extra_assets) et injecté dans les 2 sims via `sync-config-to-sims.py` + patch de `generators/assets.py` (voir `runbook/02b`)

Les ~225 actifs de volume (endpoints Windows corporate + postes dev Linux similaires) apparaissent en volume mais **ne sont pas nommés** dans le narratif.

## Actifs focus (24)

| # | Hostname | Origine | Sim source | OS | Zone | Owner group | Compensating controls | Rôle narratif |
|---|----------|---------|------------|----|------|-------------|----------------------|---------------|
| 1 | `srv-web-01.business.org` | Natif | Rapid7+CW | Windows Server 2019 / Ubuntu 22.04* | `zone-dmz-web` | `grp-owner-appdev` | WAF F5 + NGFW PAN + XDR | Portail public / front web |
| 2 | `srv-web-02.business.org` | Natif | Rapid7+CW | Ubuntu 22.04 | `zone-dmz-web` | `grp-owner-appdev` | WAF F5 + NGFW PAN + XDR | Front web redondant |
| 3 | `srv-portail.business.org` | **Custom** | Rapid7+CW | Ubuntu 22.04 | `zone-dmz-web` | `grp-owner-appdev` | WAF F5 + NGFW PAN + XDR | **Hero 6** — portail transfert public |
| 4 | `srv-vpn.business.org` | Natif | Rapid7+CW | Ubuntu 20.04 | `zone-dmz-edge` | `grp-owner-secops` | **NGFW seul** — pas d'XDR | **Hero 1** — VPN box exposé (CVE-2024-3400) |
| 5 | `smtp-relay.business.org` | **Custom** | Rapid7+CW | Debian 12 | `zone-dmz-edge` | `grp-owner-it-corp` | NGFW + XDR Linux | Relais SMTP sortant |
| 6 | `srv-ad-01.business.org` | Natif | Rapid7+CW | Windows Server 2022 | `zone-tier0` | `grp-owner-secops` | XDR + AppLocker | AD Domain Controller |
| 7 | `srv-adfs-01.business.org` | **Custom** | Rapid7+CW | Windows Server 2022 | `zone-tier0` | `grp-owner-secops` | XDR + segmentation | Fédération identité |
| 8 | `srv-db-01.business.org` | Natif | Rapid7+CW | Debian 12 | `zone-tier1` | `grp-owner-it-corp` | XDR Linux | PostgreSQL principal |
| 9 | `srv-db-02.business.org` | Natif | Rapid7+CW | Debian 12 | `zone-tier1` | `grp-owner-it-corp` | XDR Linux | PostgreSQL réplica |
| 10 | `srv-mail.business.org` | Natif | Rapid7+CW | Windows Server 2019 | `zone-tier1` | `grp-owner-it-corp` | XDR + Exchange hardening | **Hero 2** — Exchange (ProxyLogon CVE-2021-26855) |
| 11 | `srv-fs-01.business.org` | Natif | Rapid7+CW | Windows Server 2019 | `zone-tier1` | `grp-owner-it-corp` | XDR | Fileserver DFS |
| 12 | `srv-monitoring.business.org` | Natif | Rapid7+CW | Debian 12 | `zone-tier1` | `grp-owner-it-corp` | XDR Linux | Prometheus + Grafana |
| 13 | `esxi-01.business.org` | Natif | **CW seul** | Ubuntu 20.04 (hypervisor label) | `zone-infra` | `grp-owner-it-corp` | **Aucun** (appliance) | **Hero 3** — ESXi sans agent (Zerologon proxy CVE-2020-1472) |
| 14 | `nas-01.business.org` | Natif | **CW seul** | Debian 12 (network_device label) | `zone-infra` | `grp-owner-it-corp` | Aucun | Stockage NAS Synology |
| 15 | `srv-print.business.org` | **Custom** | Rapid7 seul | Windows Server 2016 | `zone-infra` | `grp-owner-it-corp` | Aucun | Print server (souvent oublié) |
| 16 | `srv-ci.business.org` | Natif | Rapid7+CW | Ubuntu 22.04 | `zone-cicd` | `grp-owner-devops` | XDR Linux + AST | **Hero 5** — CI Java + Log4Shell (CVE-2021-44228) |
| 17 | `alice.business.org` | Natif (persona) | Rapid7+CW | Windows 10 | `zone-endpoints-win` | `grp-owner-it-corp` | XDR Windows | **Hero 4** — Follina (CVE-2022-30190) |
| 18 | `bob.business.org` | Natif (persona) | Rapid7+CW | Windows 11 | `zone-endpoints-win` | `grp-owner-it-corp` | XDR Windows | Persona Windows n°2 |
| 19 | `charlie.business.org` | Natif (persona) | Rapid7+CW | Ubuntu 22.04 | `zone-devs-linux` | `grp-owner-devops` | XDR Linux | Poste dev senior |
| 20 | `david.business.org` | Natif (persona) | Rapid7+CW | Debian 12 | `zone-devs-linux` | `grp-owner-devops` | XDR Linux | Poste dev backend |
| 21 | `emma.business.org` | Natif (persona) | Rapid7+CW | Ubuntu 22.04 | `zone-devs-linux` | `grp-owner-devops` | XDR Linux | Poste dev SRE |
| 22 | `flora.business.org` | Natif (persona) | Rapid7+CW | Ubuntu 20.04 | `zone-devs-linux` | `grp-owner-devops` | XDR Linux | Poste dev data |
| 23 | `cloud-lb-01.business.org` | Natif | Rapid7 seul | Ubuntu 22.04 | `zone-cloud` | `grp-owner-devops` | Aucun natif (visibilité ASM) | Load balancer cloud |
| 24 | `cloud-app-01.business.org` | Natif | Rapid7 seul | Debian 12 | `zone-cloud` | `grp-owner-devops` | Aucun natif | App server cloud |

⚠️ Note ligne 1 : `srv-web-01` a un OS différent selon le sim (Rapid7 = Windows Server 2019, Cyberwatch = Ubuntu 22.04). Cortex XSIAM va potentiellement voir 2 assets distincts si le mapping n'est pas basé sur hostname strict. À observer post-ingestion — s'il y a dédup, c'est parfait pour l'Acte 2 du talk track. Sinon, on peut narrativer "Business Corp a 2 serveurs web avec le même préfixe" ou aligner les OS via patch du sim.

⚠️ Note personas : hostnames exacts (`alice.business.org`, `bob.business.org`, etc.) à confirmer via **dump discovery** du runbook 02 § 2.4. Le nom persona utilisé dans le code est le prénom minuscule — le hostname complet dépend de la fonction `os_for_persona` et de la structure des personas. Si les hostnames sont différents (ex : `alice-desktop.business.org`), ajuster ce document en conséquence.

## Mapping owner → responsabilité

| Groupe owner | Population | Email démo | Périmètre |
|--------------|------------|------------|-----------|
| `grp-owner-secops` | Équipe sécurité | secops@business.org | Tier 0 + périmètre exposé (DMZ edge) |
| `grp-owner-it-corp` | IT corporate | it-corp@business.org | Tier 1 + infra + endpoints Windows + print |
| `grp-owner-appdev` | Développeurs applicatifs | appdev@business.org | Services web DMZ |
| `grp-owner-devops` | Équipe DevOps/SRE | devops@business.org | CI/CD + postes Linux + cloud |

## Volumétrie totale attendue dans XSIAM après ingestion

- 6 personas partagées (Alice, Bob, Charlie, David, Emma, Flora) → visibles dans les 2 sims → dédup si mapping OK, sinon 12 assets
- 12 servers natifs Rapid7 (dont `srv-vpn`, `srv-ci`, `cloud-lb-01`, `cloud-app-01`) + 12 servers natifs Cyberwatch (dont `esxi-01`, `nas-01`) — recouvrement ~10 → ~14 servers uniques
- 4 extra assets custom (`srv-portail`, `srv-adfs-01`, `srv-print`, `smtp-relay`)
- **Total focus ~24 assets**
- + ~225 endpoints/postes de volume simulé (voir talk track "volume" narratif)

## Vulnérabilités attendues

- Rapid7 : ~180 findings brutes (18 assets × ~10 vulns moyennes)
- Cyberwatch : ~150 findings brutes
- Après dédup Cortex : ~200-250 findings uniques
- Après funnel : **6-15 cases prioritaires** (dont les 6 hero cases pinnées)
