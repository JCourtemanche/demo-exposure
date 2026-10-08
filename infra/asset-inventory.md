# Business Corp — Inventaire des actifs focus (v1 Rapid7 only)

Les **16 actifs focus** ingérés par Rapid7 InsightVM sim, qui portent la narration de la démo v1.

**Origine des assets** :
- **Natif** = présent nativement dans `EXTRA_SERVER_SEED` du sim Rapid7 (12 servers)
- **Extra BC** = ajouté via `config/business-corp-config.yaml` et injecté dans le sim via `sync-config-to-sims.py` + patch de `generators/assets.py`

Les 6 personas partagées (Alice, Bob, Charlie, David, Emma, Flora) sont ingérées mais avec un hostname court (sans `.business.org`) — non-bloquantes pour la démo car elles ne portent aucun hero case côté Rapid7.

⚠️ **Cyberwatch retiré en v1** — les assets exclusifs Cyberwatch (`esxi-01`, `nas-01`) ne font plus partie de l'inventory v1. Roadmap v2 : réintégrer via Vulnerability Ingest API.

## Actifs focus (16)

| # | Hostname | Origine | IP privée | IP publique | OS | Zone | Owner group | Compensating controls | Rôle narratif |
|---|----------|---------|-----------|-------------|----|------|-------------|----------------------|---------------|
| 1 | `srv-web-01.business.org` | Natif | 10.10.20.51 | **203.0.113.10** | Windows Server 2019 | `EM-demo-zone-dmz-web` | `EM-demo-owner-appdev` | WAF F5 + NGFW PAN + XDR | **Hero 4** — Spring4Shell (R1) ; CVE-2024-38063 (R2) |
| 2 | `srv-web-02.business.org` | Natif | 10.10.20.52 | **203.0.113.11** | Ubuntu 22.04 | `EM-demo-zone-dmz-web` | `EM-demo-owner-appdev` | WAF F5 + NGFW PAN + XDR | Front web redondant |
| 3 | `srv-portail.business.org` | **Extra BC** | 10.10.20.61 | **203.0.113.30** | Ubuntu 22.04 | `EM-demo-zone-dmz-web` | `EM-demo-owner-appdev` | WAF F5 + NGFW PAN + XDR | **Hero 6** — bzip2 (R5) |
| 4 | `srv-vpn.business.org` | Natif (OS surchargé) | 10.10.20.58 | **203.0.113.5** | **PAN-OS 10.2** (pare-feu GlobalProtect) | `EM-demo-zone-dmz-edge` | `EM-demo-owner-secops` | **Aucun** (pas d'agent possible) | **Hero 1** — CVE-2024-3400 (R1) |
| 5 | `smtp-relay.business.org` | **Extra BC** | 10.10.20.64 | **203.0.113.40** | Debian 12 | `EM-demo-zone-dmz-edge` | `EM-demo-owner-it-corp` | NGFW + XDR Linux | Relais SMTP sortant |
| 6 | `srv-ad-01.business.org` | Natif | 10.10.20.56 | — | Windows Server 2022 | `EM-demo-zone-tier0` | `EM-demo-owner-secops` | **AppLocker seul** (exclu de l'agent XDR) | **Hero 3** — Zerologon (R3), contrôleur de domaine |
| 7 | `srv-adfs-01.business.org` | **Extra BC** | 10.10.20.62 | — | Windows Server 2022 | `EM-demo-zone-tier0` | `EM-demo-owner-secops` | XDR | Fédération d'identité SSO (pas de hero) |
| 8 | `srv-db-01.business.org` | Natif | 10.10.20.53 | — | Debian 12 | `EM-demo-zone-tier1` | `EM-demo-owner-it-corp` | XDR Linux | PostgreSQL principal |
| 9 | `srv-db-02.business.org` | Natif | 10.10.20.54 | — | Debian 12 | `EM-demo-zone-tier1` | `EM-demo-owner-it-corp` | XDR Linux | PostgreSQL réplica |
| 10 | `srv-mail.business.org` | Natif | 10.10.20.55 | **203.0.113.20** | Windows Server 2019 | `EM-demo-zone-tier1` | `EM-demo-owner-it-corp` | XDR + Exchange hardening | **Hero 2** — ProxyLogon (R1, via le groupe exposé) |
| 11 | `srv-fs-01.business.org` | Natif | 10.10.20.57 | — | Windows Server 2019 | `EM-demo-zone-tier1` | `EM-demo-owner-it-corp` | XDR | Fileserver DFS |
| 12 | `srv-monitoring.business.org` | Natif | 10.10.20.59 | — | Debian 12 | `EM-demo-zone-tier1` | `EM-demo-owner-it-corp` | XDR Linux | Prometheus + Grafana |
| 13 | `srv-print.business.org` | **Extra BC** | 10.10.20.63 | — | Windows Server 2019 | `EM-demo-zone-infra` | `EM-demo-owner-it-corp` | Aucun | Print server (souvent oublié) |
| 14 | `srv-ci.business.org` | Natif | 10.10.20.60 | — | Ubuntu 22.04 | `EM-demo-zone-cicd` | `EM-demo-owner-devops` | XDR Linux + AST | **Hero 5** — Log4Shell (R3) ; TeamCity CVE-2024-23917 (R4) |
| 15 | `cloud-lb-01.business.org` | Natif | 10.20.30.10 | — | Ubuntu 22.04 | `EM-demo-zone-cloud` | `EM-demo-owner-devops` | Aucun natif (visibilité ASM) | Load balancer cloud |
| 16 | `cloud-app-01.business.org` | Natif | 10.20.30.11 | — | Debian 12 | `EM-demo-zone-cloud` | `EM-demo-owner-devops` | Aucun natif | App server cloud |

**Total** : 16 actifs focus (12 natifs Rapid7 + 4 extras BC). Ne pas confondre avec les ~250 assets narratifs mentionnés dans l'acte 1 (extension implicite non-modélisée).

## Rôles logiciels et cohérence des CVE (v1.4)

Le sim Rapid7 n'attribue à chaque asset que des CVE applicables à son OS et à ses rôles (voir `config/catalogs-inventory.md`).

| Asset | Plateforme | Rôles | CVE typiques |
|-------|-----------|-------|--------------|
| srv-web-01 | windows-server | java, web | Spring4Shell, Log4Shell, Struts, PrintNightmare, Windows TCP/IP |
| srv-web-02 | linux | web, php | POST SMTP (WordPress), regreSSHion, Looney Tunables |
| srv-portail | linux | java, mft | GoAnywhere MFT, Log4Shell, bzip2 |
| srv-vpn | panos | (OS PAN-OS) | CVE-2024-3400, CVE-2024-0012 |
| smtp-relay | linux | smtp | Postfix SMTP smuggling, regreSSHion |
| srv-ad-01 | windows-server | domain-controller | Zerologon, PrintNightmare, Windows TCP/IP |
| srv-adfs-01 / srv-print / srv-fs-01 | windows-server | aucun | Failles Windows Server uniquement |
| srv-db-01 / srv-db-02 | linux | postgresql | PostgreSQL PL/Perl, regreSSHion |
| srv-mail | windows-server | exchange | ProxyLogon, ProxyNotShell, Failles Windows Server |
| srv-monitoring | linux | grafana | Grafana directory traversal |
| srv-ci | linux | java, teamcity | Log4Shell, TeamCity |
| cloud-app-01 | linux | java, activemq | ActiveMQ, Log4Shell |
| cloud-lb-01 | linux | aucun | Failles Linux génériques |
| BSNS-WIN-* | windows-client | office, browser | Outlook, Follina, WinRAR, Windows TCP/IP, libwebp |
| BSNS-MAC-* | macos | browser | WebKit, ImageIO (BLASTPASS), libwebp |
| BSNS-MOB-FLORA | ios | aucun | WebKit, ImageIO |

## Assets avec IP publique (zone exposée)

Les 6 actifs suivants portent une IP publique dans le range TEST-NET RFC 5737 (203.0.113.0/24 — non-routable, sûr pour démo). Cortex Exposure Management déduit le flag `Internet Exposed = True` à partir de la présence de cette IP dans `addresses` :

| Asset | Public IP | Rôle |
|-------|-----------|------|
| `srv-vpn` | 203.0.113.5 | Pare-feu VPN PAN-OS (Hero 1 R1) |
| `srv-web-01` | 203.0.113.10 | Front web (Hero 4 R4) |
| `srv-web-02` | 203.0.113.11 | Front web redondant |
| `srv-mail` | 203.0.113.20 | Exchange OWA (Hero 2 R1) |
| `srv-portail` | 203.0.113.30 | Portail transfert (Hero 6 R5) |
| `smtp-relay` | 203.0.113.40 | Relais mail sortant |

Ces 6 assets portent le tag `exposure:internet` et forment l'asset group `EM-demo-grp-Business-Corp-exposed`, périmètre des règles R1 / R2 / R5. Cortex ne déduit **pas** le flag Internet Exposed de ces IP (il vient de l'ASM / CNA avec confirmation par scan externe, et la plage TEST-NET ne répond jamais) : le champ `internet_exposed` reste vide.

Les autres actifs sont **internes** : ils relèvent des règles R3 (Angle mort interne, ex. le DC `srv-ad-01`) et R4.

## Mapping owner → responsabilité

| Groupe owner | Population | Email démo | Périmètre |
|--------------|------------|------------|-----------|
| `EM-demo-owner-secops` | Équipe sécurité | secops@business.org | Tier 0 (AD, ADFS) + pare-feu VPN exposé |
| `EM-demo-owner-it-corp` | IT corporate | it-corp@business.org | Tier 1 + infra + smtp-relay + print |
| `EM-demo-owner-appdev` | Développeurs applicatifs | appdev@business.org | Services web DMZ (srv-web-01/02, srv-portail) |
| `EM-demo-owner-devops` | Équipe DevOps/SRE | devops@business.org | CI/CD (srv-ci) + cloud |

## Volumétrie totale attendue dans XSIAM après ingestion

- **~16 assets** avec hostname `.business.org` (visibles via filtre XQL classique)
- **~6 personas** avec hostname court (Alice, Bob, Charlie, David, Emma, Flora) — non narratifs
- **Total ~22 assets uniques** dans `asset_inventory` (source_id `_source_id` contient "Rapid7")

## Vulnérabilités attendues

- Rapid7 : ~115 findings brutes sur les 22 assets, toutes cohérentes avec l'OS et les logiciels de l'asset (v1.4)
- Après enrichissement Cortex (~2h) : findings normalisés dans `uvm_findings` avec CVRS calculé
- Après funnel + 5 policies : une poignée de cases prioritaires (dont les 6 hero cases épinglées)

## Notes

- **Cyberwatch retiré en v1** : les assets exclusifs `esxi-01`, `nas-01` (Cyberwatch-only) ne sont plus dans l'inventory
- **Hero 3 (Maillon Faible)** est porté depuis la v1.4 par le contrôleur de domaine `srv-ad-01` (Zerologon touche les DC, pas ADFS). Il doit être exclu du contrôle compensatoire XDR (runbook 06) pour garder un CVRS ≥ 90
- **Hero 4 (Menace Imminente EPSS)** est migré sur `srv-web-01` (natif) + Spring4Shell au lieu de `alice` + Follina — la narrative "serveur exposé, exploitation imminente" est plus vendeuse sur un serveur DMZ
- Les 6 personas partagées sont ingérées avec `hostname` court (sans domaine) : à confirmer via dump discovery si besoin
