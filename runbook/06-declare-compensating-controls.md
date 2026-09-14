# Runbook 06 — Déclarer les compensating controls

Objectif : matérialiser les défenses de Business Corp comme **Security Controls** dans Cortex Exposure Management. Ces contrôles influencent activement le CVRS et servent de démonstration Acte 4 du talk track.

## Rappel des catégories/types Cortex

Source : doc Security Controls Cortex XDR 5.x.

| Catégorie | Types disponibles |
|-----------|-------------------|
| Network Security | Network Firewall, **Next Generation Firewall**, **Web Application Firewall**, Intrusion Prevention System, Virtual Private Network |
| Endpoint Security | **EDR**, **XDR**, Anti-Virus, Host Based FW |
| Data Security | VPN, Disk Encryption, DLP, Database Activity Monitor |
| Identity Security | MFA, SSO, PAM |
| Other | Free text (4-256 chars) |

Statuts d'effectiveness : **Effective / Partially Effective / Not Effective / Unknown**.

Cycle de vie : **Disabled → Discovery (24h) → Active → Inactive** (re-vérifié toutes les 24h).

## Étape 6.1 — Vérifier les contrôles auto-détectés

XSIAM → **Settings** → **Exposure Management** → **Security Controls** → onglet **Discovered**.

Attendu (si agents Cortex XDR réellement installés sur les endpoints ingérés) :
- **Cortex XDR agent** (Endpoint Security / XDR) — auto-détecté sur tous les endpoints ayant l'agent
- Portée : automatique par présence d'agent

⚠️ Dans notre démo, les assets viennent des **simulateurs** — pas de vrais agents installés. Donc auto-detect probablement vide. On va tout déclarer manuellement.

Alternative si votre tenant a de vrais endpoints avec agents Cortex : c'est un bonus démo à mettre en avant (montrer que l'auto-detect fonctionne sur les vrais endpoints, en plus des manuels sur les zones fictives).

## Étape 6.2 — Créer les 4 contrôles manuels

XSIAM → **Settings** → **Exposure Management** → **Security Controls** → **+ Add Manual Control**.

### Contrôle 1 — WAF F5 Big-IP

| Champ | Valeur |
|-------|--------|
| **Name** | `WAF-F5-BigIP-Prod` |
| **Category** | Network Security |
| **Type** | Web Application Firewall |
| **Vendor** | F5 |
| **Description** | WAF F5 Big-IP protégeant la DMZ web publique |
| **Scope: Asset Groups** | `grp-zone-dmz-web` |
| **Default Effectiveness** | Partially Effective (bloque OWASP Top 10 mais pas exploitations post-authent) |

### Contrôle 2 — PANW NGFW périmétrique

| Champ | Valeur |
|-------|--------|
| **Name** | `NGFW-PANW-Perimeter` |
| **Category** | Network Security |
| **Type** | Next Generation Firewall |
| **Vendor** | Palo Alto Networks |
| **Description** | NGFW hardware en périmètre — segmentation zones + inspection L7 |
| **Scope: Asset Groups** | `grp-zone-dmz-web`, `grp-zone-dmz-edge` |
| **Default Effectiveness** | Partially Effective |

⚠️ **Si vous êtes en VM-Series NGFW** (pas hardware), Cortex peut l'auto-détecter → à confirmer dans votre tenant. Dans ce cas, ne pas créer manuellement, le laisser en Discovered.

### Contrôle 3 — Cortex XDR agent (déclaration manuelle si auto-detect indisponible)

| Champ | Valeur |
|-------|--------|
| **Name** | `Cortex-XDR-Agent-Endpoints` |
| **Category** | Endpoint Security |
| **Type** | XDR |
| **Vendor** | Palo Alto Networks |
| **Description** | Cortex XDR agent déployé sur endpoints Win + Linux + serveurs Tier 0/1 |
| **Scope: Asset Groups** | `grp-zone-endpoints-win`, `grp-zone-devs-linux`, `grp-zone-tier0`, `grp-zone-tier1`, `grp-zone-cicd` |
| **Default Effectiveness** | Effective |

**⚠️ Ne PAS inclure** `grp-zone-infra` (ESXi, NAS, print) ni `grp-zone-dmz-edge` (VPN box) — c'est intentionnel pour matérialiser Hero Case 3 "Maillon Faible" et Hero Case 1 "Urgence Périmètre".

### Contrôle 4 — VPN concentrateur (contexte, effet démo mineur)

| Champ | Valeur |
|-------|--------|
| **Name** | `VPN-Concentrator-RemoteAccess` |
| **Category** | Data Security |
| **Type** | VPN |
| **Vendor** | Palo Alto Networks (GlobalProtect) |
| **Description** | VPN d'accès distant pour employés télétravail |
| **Scope: Asset Groups** | `grp-zone-endpoints-win`, `grp-zone-devs-linux` |
| **Default Effectiveness** | Unknown |

## Étape 6.3 — Effectiveness Rules (raffinement — optionnel v1)

Pour chaque contrôle, on peut créer des **Effectiveness Rules** qui définissent quand le contrôle est vraiment efficace vs pas.

Exemple pour WAF F5 :
- Règle 1 : `IF vuln.category = "SQL Injection" THEN Effective`
- Règle 2 : `IF vuln.category = "Cross-Site Scripting" THEN Effective`
- Règle 3 : `IF vuln.category = "Authentication Bypass" THEN Partially Effective`
- Règle 4 : `IF vuln.category = "Local Privilege Escalation" THEN Not Applicable`

Non critique pour v1 — la démo fonctionne avec les Default Effectiveness. À ajouter en v2 pour un discours plus fin.

## Étape 6.4 — ⏳ Attendre 24 h — cycle Discovery → Active

Cortex documente que les contrôles manuels passent par un cycle :
- **Disabled** (juste créé) → 24 h → **Discovery** (vérification portée) → **Active** (opérationnel)

**Impact planning démo** : créer les contrôles **au minimum 48 h avant la démo** pour absorber ce cycle.

Vérifier progression : XSIAM → Settings → Exposure Management → Security Controls → colonne **Status**.

## Étape 6.5 — Vérifier l'effet sur les vulnerability issues

Une fois en Active, ouvrir une case existante (ex : sur `srv-web-01.business.org`) et regarder l'onglet **Risk Details** → facteur **Compensating Controls**.

Attendu :
- Les vulns web sur `srv-web-01` : Compensating Control = "Partially Effective" (WAF F5 déclaré)
- Les vulns sur `esxi-01` : Compensating Control = "Unknown" ou "Not Effective" (aucun control couvrant)
- Les vulns sur `alice` : Compensating Control = "Effective" (XDR agent couvre)

**Ceci est LA preuve visuelle** de l'effet des compensating controls sur le CVRS — cœur de l'Acte 4 du talk track.

## Étape 6.6 — Comparer CVRS avant/après

Prendre 2 assets ayant la même CVE (ex : Log4Shell) :
- 1 asset avec compensating control efficace
- 1 asset sans

Observer l'écart CVRS. Si l'écart est notable (typiquement 15-25 points), les compensating controls sont bien pris en compte dans le score.

Si l'écart est nul (les 2 assets ont le même CVRS malgré des controls différents) :
- Vérifier que les contrôles sont bien en status "Active" (pas Discovery)
- Vérifier que les Asset Groups référencent bien les bons assets
- Consulter `validation/open-questions-tenant.md` question 3 (scope CVRS)

## Suivant

→ [`07-create-vulnerability-policy.md`](07-create-vulnerability-policy.md)
