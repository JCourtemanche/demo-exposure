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
| 1 | `srv-web-01.business.org` | Natif | 10.10.20.51 | **203.0.113.10** | Windows Server 2019 | `zone-dmz-web` | `grp-owner-appdev` | WAF F5 + NGFW PAN + XDR | **Hero 4** — Spring4Shell (R4) |
| 2 | `srv-web-02.business.org` | Natif | 10.10.20.52 | **203.0.113.11** | Ubuntu 22.04 | `zone-dmz-web` | `grp-owner-appdev` | WAF F5 + NGFW PAN + XDR | Front web redondant |
| 3 | `srv-portail.business.org` | **Extra BC** | 10.10.20.61 | **203.0.113.30** | Ubuntu 22.04 | `zone-dmz-web` | `grp-owner-appdev` | WAF F5 + NGFW PAN + XDR | **Hero 6** — bzip2 (R7) |
| 4 | `srv-vpn.business.org` | Natif | 10.10.20.58 | **203.0.113.5** | Ubuntu 20.04 | `zone-dmz-edge` | `grp-owner-secops` | NGFW seul — **pas d'XDR** | **Hero 1** — CVE-2024-3400 (R2) |
| 5 | `smtp-relay.business.org` | **Extra BC** | 10.10.20.64 | **203.0.113.40** | Debian 12 | `zone-dmz-edge` | `grp-owner-it-corp` | NGFW + XDR Linux | Relais SMTP sortant |
| 6 | `srv-ad-01.business.org` | Natif | 10.10.20.56 | — | Windows Server 2022 | `zone-tier0` | `grp-owner-secops` | XDR + AppLocker | AD Domain Controller |
| 7 | `srv-adfs-01.business.org` | **Extra BC** | 10.10.20.62 | — | Windows Server 2022 | `zone-tier0` | `grp-owner-secops` | **Aucun** (appliance-like) | **Hero 3** — Zerologon (R3) |
| 8 | `srv-db-01.business.org` | Natif | 10.10.20.53 | — | Debian 12 | `zone-tier1` | `grp-owner-it-corp` | XDR Linux | PostgreSQL principal |
| 9 | `srv-db-02.business.org` | Natif | 10.10.20.54 | — | Debian 12 | `zone-tier1` | `grp-owner-it-corp` | XDR Linux | PostgreSQL réplica |
| 10 | `srv-mail.business.org` | Natif | 10.10.20.55 | **203.0.113.20** | Windows Server 2019 | `zone-tier1` | `grp-owner-it-corp` | XDR + Exchange hardening | **Hero 2** — ProxyLogon (R1) |
| 11 | `srv-fs-01.business.org` | Natif | 10.10.20.57 | — | Windows Server 2019 | `zone-tier1` | `grp-owner-it-corp` | XDR | Fileserver DFS |
| 12 | `srv-monitoring.business.org` | Natif | 10.10.20.59 | — | Debian 12 | `zone-tier1` | `grp-owner-it-corp` | XDR Linux | Prometheus + Grafana |
| 13 | `srv-print.business.org` | **Extra BC** | 10.10.20.63 | — | Windows Server 2019 | `zone-infra` | `grp-owner-it-corp` | Aucun | Print server (souvent oublié) |
| 14 | `srv-ci.business.org` | Natif | 10.10.20.60 | — | Ubuntu 22.04 | `zone-cicd` | `grp-owner-devops` | XDR Linux + AST | **Hero 5** — Log4Shell (R4) |
| 15 | `cloud-lb-01.business.org` | Natif | 10.20.30.10 | — | Ubuntu 22.04 | `zone-cloud` | `grp-owner-devops` | Aucun natif (visibilité ASM) | Load balancer cloud |
| 16 | `cloud-app-01.business.org` | Natif | 10.20.30.11 | — | Debian 12 | `zone-cloud` | `grp-owner-devops` | Aucun natif | App server cloud |

**Total** : 16 actifs focus (12 natifs Rapid7 + 4 extras BC). Ne pas confondre avec les ~250 assets narratifs mentionnés dans l'acte 1 (extension implicite non-modélisée).

## Assets avec IP publique (Internet Exposed)

Les 6 actifs suivants portent une IP publique dans le range TEST-NET RFC 5737 (203.0.113.0/24 — non-routable, sûr pour démo). Cortex Exposure Management déduit le flag `Internet Exposed = True` à partir de la présence de cette IP dans `addresses` :

| Asset | Public IP | Rôle |
|-------|-----------|------|
| `srv-vpn` | 203.0.113.5 | Boîtier VPN (Hero 1 R2) |
| `srv-web-01` | 203.0.113.10 | Front web (Hero 4 R4) |
| `srv-web-02` | 203.0.113.11 | Front web redondant |
| `srv-mail` | 203.0.113.20 | Exchange OWA (Hero 2 R1) |
| `srv-portail` | 203.0.113.30 | Portail transfert (Hero 6 R7) |
| `smtp-relay` | 203.0.113.40 | Relais mail sortant |

Les autres actifs sont **internes** — ils déclenchent les règles R3 (Maillon faible interne, ex : ADFS) ou sont hors-scope des règles Internet-Exposed.

## Mapping owner → responsabilité

| Groupe owner | Population | Email démo | Périmètre |
|--------------|------------|------------|-----------|
| `grp-owner-secops` | Équipe sécurité | secops@business.org | Tier 0 (AD, ADFS) + périmètre exposé (VPN) |
| `grp-owner-it-corp` | IT corporate | it-corp@business.org | Tier 1 + infra + smtp-relay + print |
| `grp-owner-appdev` | Développeurs applicatifs | appdev@business.org | Services web DMZ (srv-web-01/02, srv-portail) |
| `grp-owner-devops` | Équipe DevOps/SRE | devops@business.org | CI/CD (srv-ci) + cloud |

## Volumétrie totale attendue dans XSIAM après ingestion

- **~16 assets** avec hostname `.business.org` (visibles via filtre XQL classique)
- **~6 personas** avec hostname court (Alice, Bob, Charlie, David, Emma, Flora) — non narratifs
- **Total ~22 assets uniques** dans `asset_inventory` (source_id `_source_id` contient "Rapid7")

## Vulnérabilités attendues

- Rapid7 : ~150-200 findings brutes dans `rapid7_nexpose_vulnerabilities_raw`
- Après enrichissement Cortex (~2h) : findings normalisés dans `uvm_findings` avec CVRS calculé
- Après funnel + 8 policies : **6-15 cases prioritaires** (dont les 6 hero cases pinnées)

## Notes

- **Cyberwatch retiré en v1** : les assets exclusifs `esxi-01`, `nas-01` (Cyberwatch-only) ne sont plus dans l'inventory
- **Hero 3 (Maillon Faible)** est migré sur `srv-adfs-01` (extra BC) au lieu de `esxi-01` — la narrative "actif Tier 0 sans agent XDR possible" fonctionne aussi bien sur ADFS
- **Hero 4 (Menace Imminente EPSS)** est migré sur `srv-web-01` (natif) + Spring4Shell au lieu de `alice` + Follina — la narrative "serveur exposé, exploitation imminente" est plus vendeuse sur un serveur DMZ
- Les 6 personas partagées sont ingérées avec `hostname` court (sans domaine) : à confirmer via dump discovery si besoin
