# Business Corp — Architecture réseau (Mermaid)

Diagramme de l'infrastructure fictive utilisée pour la démo. Version textuelle éditable (à convertir en draw.io ou capture PNG pour les slides).

## Vue d'ensemble

```mermaid
flowchart TB
    Internet((Internet)) --> WAF[WAF F5 Big-IP]
    Internet --> NGFW[PANW NGFW Périmétrique]

    subgraph DMZ_WEB["zone-dmz-web (WAF + NGFW + XDR)"]
        Web1[srv-web-01<br/>Portail client]
        RevProxy[Reverse Proxy Nginx]
    end

    subgraph DMZ_EDGE["zone-dmz-edge (NGFW seul, PAS d'XDR)"]
        VPN[srv-vpn<br/>Boîtier VPN Ubuntu 20.04<br/>tag rôle: vpn_gateway]
        SMTP[smtp-relay<br/>Relais SMTP]
    end

    WAF --> DMZ_WEB
    NGFW --> DMZ_EDGE

    subgraph TIER0["zone-tier0 (XDR + accès restreint)"]
        AD[srv-ad-01<br/>Active Directory]
        ADFS[ADFS]
    end

    subgraph TIER1["zone-tier1 (XDR)"]
        DB[srv-db-01<br/>PostgreSQL]
        Mail[srv-mail<br/>Exchange 2019]
        FS[Fileserver]
    end

    subgraph INFRA["zone-infra (PAS d'XDR — appliances)"]
        ESXi[esxi-01<br/>VMware vSphere]
        NAS[nas-01<br/>QNAP]
        Mon[Monitoring]
    end

    subgraph CICD["zone-cicd (XDR)"]
        CI[srv-ci<br/>GitLab CI + Java runtime]
    end

    subgraph DEVS["zone-devs-linux (~10 postes)"]
        DevLnx[Charlie / David / Emma / Flora + 6 générés<br/>Ubuntu 22.04 / Debian 12]
    end

    subgraph EPWIN["zone-endpoints-win (~200 postes)"]
        EpWin[Workstations Windows 10/11<br/>Corporate parc]
    end

    subgraph CLOUD["zone-cloud (optionnel ASM)"]
        CloudSrv[Cloud workloads AWS/Azure]
    end

    DMZ_WEB -.-> TIER1
    DMZ_EDGE -.-> TIER0
    TIER0 -.-> TIER1
    TIER1 -.-> INFRA
    CICD -.-> TIER1
    DEVS -.-> CICD
    EPWIN -.-> AD

    classDef exposed fill:#ffcccc,stroke:#cc0000,stroke-width:2px
    classDef critical fill:#ffe6cc,stroke:#ff8800,stroke-width:2px
    classDef nocontrol fill:#fff2cc,stroke:#d6b656,stroke-width:2px
    classDef normal fill:#dae8fc,stroke:#6c8ebf,stroke-width:1px

    class Web1,RevProxy,VPN,SMTP exposed
    class AD,ADFS,DB,Mail critical
    class ESXi,NAS,Mon,VPN,SMTP nocontrol
    class DevLnx,EpWin,CI,Cloud,FS,CloudSrv normal
```

## Légende

- **Rouge** (`exposed`) : actifs exposés Internet — cibles principales du funnel règles 1, 2, 4, 6
- **Orange** (`critical`) : actifs Tier 0/1 critiques — porteurs de la Vulnerability Policy `POL-BusinessCorp-Tier0-Escalate`
- **Jaune** (`nocontrol`) : actifs sans Cortex XDR agent — matérialisent règle 3 "Maillon Faible"
- **Bleu** (`normal`) : actifs standards protégés par XDR

## Chiffres clés à afficher en slide

| Métrique | Valeur |
|----------|--------|
| Total actifs Business Corp | ~250 |
| Actifs "focus" (porteurs de vulns narratives) | 25 |
| Endpoints Windows corporate | ~200 |
| Postes dev Linux | ~10 |
| Zones logiques | 9 |
| Compensating controls déclarés | 4 (+ XDR auto) |
| Vulnerability Policies custom | 1 |
| Hero cases attendues après funnel | 6 |
| Vulnerabilités brutes avant funnel (Rapid7 + Cyberwatch) | ~2000+ (dont ~150 marquées "critique") |

## Conversion vers draw.io / slide

1. Coller le bloc Mermaid ci-dessus dans https://mermaid.live pour prévisualiser
2. Export SVG → import dans draw.io ou PowerPoint pour polissage graphique
3. Alternative : capture d'écran directe pour la slide "Acte 1 — Le problème"

## Notes de mise à jour

- Les serveurs `srv-web-01`, `srv-db-01`, `srv-mail`, `srv-vpn`, `esxi-01`, `nas-01`, `srv-ci` correspondent aux noms générés par `EXTRA_SERVER_SEED` des 2 sims
- Les personas utilisateurs Alice/Bob (Windows) et Charlie/David/Emma/Flora (Linux) proviennent de `xsiam-shared-personas`
- `srv-portail`, `srv-adfs-01`, `srv-print`, `smtp-relay` sont **injectés via `config/business-corp-config.yaml`** (extra_assets custom) — voir `runbook/02b`
- WAF F5, NGFW hardware, reverse proxy sont **des ajouts purement narratifs** (représentés dans XSIAM uniquement comme compensating controls attachés aux groupes d'assets, pas comme assets)
