# Talk track FR — Démo Exposure Management (35 min, v1 Rapid7 only)

Script démo complet, structuré en **6 actes**. Durées indicatives — chrono en main lors des répétitions.

**Public cible** : RSSI, responsable SOC, ops sécurité — profils décideurs qui veulent comprendre la logique avant les détails techniques.

**Matériel** :
- Slides : schéma d'infra `business-corp-infra.png` + tableau des 8 règles CVRS (`funnel-rules-table.md`)
- Console XSIAM avec le tenant configuré selon le runbook
- Backup : screenshots des cases attendues (si le tenant lag)

---

## Acte 1 — Le problème (5 min, slides uniquement)

**Slide 1 — Business Corp, notre PME fictive**
> "Aujourd'hui, on va prendre une entreprise fictive, Business Corp. Environ 24 machines dans le périmètre focus — un peu de cloud, un parc endpoint Windows, quelques serveurs métier, un ADFS, un CI, un portail public. Configuration assez classique de PME/ETI française."

Afficher le schéma d'infra `business-corp-infra.png`. Pointer avec le curseur :
- La DMZ web (portail public `srv-portail`, serveur web `srv-web-01/02`)
- Le boîtier VPN `srv-vpn`
- L'Active Directory `srv-ad-01` + ADFS `srv-adfs-01`
- L'Exchange `srv-mail`
- Le CI Jenkins `srv-ci`
- Les cloud workloads `cloud-lb-01`/`cloud-app-01`

**Slide 2 — Ce que le RSSI a déjà en place**
> "Business Corp a déjà investi. Rapid7 InsightVM en scan réseau, Cortex XDR agent sur les endpoints Windows et Linux, un WAF F5 devant la DMZ, un PANW NGFW en périmètre. Le problème n'est pas la détection — le problème c'est la priorisation."

**Slide 3 — Le problème du lundi matin**
> "Lundi 9h. Le RSSI ouvre Rapid7. **150 vulnérabilités marquées critiques**. Il ouvre XSIAM native — 22 assets remontés, chacun avec 5 à 20 vulns. Question : par quoi commencer ?"

Pause. Laisser la question flotter.

> "La vraie question n'est pas 'quelle est la CVSS la plus élevée' — c'est 'quelle est la vulnérabilité la plus proche d'être exploitée, sur l'actif qui compte le plus, sans protection compensatoire efficace'. Et c'est exactement ce que fait le funnel de priorisation d'Exposure Management via le **CVRS**."

**Slide 4 — Le CVRS, le score qui remplace le CVSS**
> "CVRS = Cortex Vulnerability Risk Score. Score propriétaire 0-100 calculé en temps réel par Cortex à partir de **5 facteurs** :"
>
> "1. **Vulnerability Context** : le CVSS de base"
> "2. **Exploit Intelligence** : EPSS + CISA KEV + exploited-in-the-wild + exploit maturity"
> "3. **Asset Risk** : Internet Exposed (via ASM ou public IP)"
> "4. **Environment Risk** : Package-in-use validé par Attack Surface Testing"
> "5. **Compensating Controls** : effectivité de vos WAF, NGFW, XDR agent sur cette CVE"
>
> "**Le CVSS est aveugle au contexte. Le CVRS lui, reflète VOTRE environnement.**"

**Slide 5 — La grille de lecture (afficher `funnel-rules-table.md`)**
> "On a défini 8 règles Business Corp, R1 à R8, toutes centrées sur le CVRS. Chacune a une sévérité, un SLA, une justification métier. On les retrouvera toutes dans les cases qu'on va analyser ensemble."

Passer rapidement sur les 8 règles, insister sur 3 :
> - **R1 'Exploitation active périmètre'** : KEV ou EPSS≥0.9 + Internet Exposed. SLA 48h. Le lundi matin, c'est là qu'on regarde en premier.
> - **R3 'Angle mort interne interne'** : KEV + CVRS≥90 + interne + Tier 0. La cible cachée que les scanners CVSS ratent.
> - **R7 'Réduction surface externe'** : hygiène ASM, on réduit la découvrabilité sur Shodan.

**Transition** : "Bascule sur la console."

---

## Acte 2 — Le funnel Exposure Management (10 min, console)

**Navigation** : Cortex XSIAM → Posture Management → Exposure Management → **Command Center**

> "Voici le Command Center d'Exposure Management. Le funnel apparaît en haut."

Pointer chaque étape du funnel de gauche à droite :
1. **Vulnerabilities** — "Le total brut ingéré depuis Rapid7. Chiffre autour de 200-250 findings."
2. **Duplicative Findings removed** — "Cortex a dédupliqué (même CVE vue plusieurs fois sur le même hôte)."
3. **Unique Vulnerabilities** — "On tombe à environ 150-180 findings uniques."
4. **Deprioritized** — "Ici, 4 filtres natifs Cortex + notre suite de 8 policies Business Corp s'appliquent."
5. **Open Issues** — "~15-25 issues survivent."
6. **Cases** — "Groupées par 'fix commun'. On arrive à **6-15 cases actionnables**."

**Zoom sur les Deprioritized filters** : cliquer pour ouvrir le détail.
> "Cortex natif d'abord : 'Not Internet Exposed' — via ASM + les IPs publiques déclarées dans l'inventory. 'Low Business Impact' — via les asset groups tagués 'dev/test'. 'No Known Public Exploits' — EPSS < 80% ET pas de KEV. 'Low/Medium CVSS' — pour le catalogue."
>
> "Puis notre 5e ligne, **'Deprioritized by Policy'** : c'est là que nos règles R6, R7, R8 filtrent la longue traîne des vulns moyennes ou hygiène. **Encodage explicite de la politique métier Business Corp — auditable, ajustable.**"

**Pointer les chiffres finaux** :
> "Résultat : de 200+ findings à 6-15 cases actionnables. On vient d'appliquer un facteur 20 de réduction du bruit — et on n'a rien perdu de matériel, tout est traçable et défendable en audit."

**Transition** : "On va maintenant ouvrir ces cases une par une, dans l'ordre de nos règles CVRS."

---

## Acte 3 — Les 6 hero cases en action (10 min, drill-down)

**Navigation** : Command Center → onglet **Cases** → tri par CVRS descendant.

Pour chaque hero case, dérouler la structure suivante :
1. **Annoncer la règle** : "Case n°X — Règle **R{n}** [nom] déclenchée"
2. **Ouvrir la case** : vue Overview
3. **Pointer les preuves** : CVRS, badges (KEV, Internet Exposed), EPSS, exploit maturity
4. **Ouvrir Risk Details** : montrer le facteur qui domine (Asset Risk, Exploit Intel, Environment Risk, Compensating Controls)
5. **Storyline** (voir `hero-cases.md` pour les scripts détaillés de 30-60 sec par case)

**Ordre recommandé** (impact narratif décroissant) :
1. **Hero 1 — R2 Urgence périmètre** (`srv-vpn` + CVE-2024-3400) — CVRS 96, KEV, exposé
2. **Hero 2 — R1 Exploitation active périmètre** (`srv-mail` + ProxyLogon) — KEV emblématique
3. **Hero 3 — R3 Angle mort interne** (`srv-adfs-01` + Zerologon) ← **temps fort pédagogique, 60 sec**
4. **Hero 4 — R4 Exploit prêt EPSS** (`srv-web-01` + Spring4Shell) — EPSS 87%, patch dispo
5. **Hero 5 — R4 Exploit prêt Package-in-use** (`srv-ci` + Log4Shell) — AST valide runtime actif
6. **Hero 6 — R7 Surface externe** (`srv-portail` + bzip2) — hygiène ASM

**Insister sur les contrastes** :
- Hero 3 vs Hero 5 : deux CVE différentes, mais le contraste vient de la présence/absence de compensating control (le Zerologon sur ADFS reste CVRS 92, le Log4Shell sur CI descend à 78 grâce à XDR agent partiel)
- Hero 2 vs Hero 4 : KEV vs EPSS — deux façons complémentaires de mesurer l'exploitabilité (KEV = déjà exploité, EPSS = va l'être bientôt)

**Transition** : "On a vu les compensating controls jouer un rôle central dans le calcul du CVRS. Allons voir comment ils sont configurés."

---

## Acte 4 — Compensating controls (5 min, console)

**Navigation** : Settings → Exposure Management → **Security Controls**

> "Voici les contrôles compensatoires qu'on a déclarés dans Business Corp. Deux types : ceux détectés automatiquement par Cortex, et ceux qu'on a déclarés manuellement."

**Pointer les contrôles auto-détectés** (si agents Cortex XDR réellement installés) :
- **Cortex XDR agent** : "Détecté sur tous les endpoints qui ont l'agent installé. Cortex regarde même la configuration du profil exploit-protection — si 'Known Vulnerable Processes Protection' est en Block, la protection est jugée Effective sur la CVE correspondante."

**Pointer les contrôles manuels** :
- **WAF F5** sur `EM-demo-zone-dmz-web` : "Déclaré manuellement, catégorie Network Security / WAF, vendor F5. Portée : le groupe d'actifs DMZ web (`srv-web-01/02`, `srv-portail`)."
- **PANW NGFW** sur `EM-demo-zone-dmz-*` : "NGFW hardware — pas de télémétrie automatique donc on l'a déclaré."

**Ouvrir un contrôle** : montrer les 4 statuts d'effectiveness (Effective / Partially / Not Effective / Unknown) et l'onglet Rules.

> "Cortex ne dit pas 'le WAF F5 protège tout'. Il applique un moteur de règles : si la CVE est une injection SQL, alors WAF = Effective. Si c'est une élévation de privilèges locale, alors WAF = Not Applicable. **Le contrôle compensatoire est mesuré par CVE**."

**Revenir à une case** (Hero 3 srv-adfs-01) :
> "C'est pourquoi notre ADFS ressort. Pas d'agent XDR (l'équipe SecOps considère l'ADFS comme une appliance et n'a jamais déployé l'agent), pas de WAF pertinent, pas de NGFW efficace pour une exploitation Netlogon post-authent. Cortex dit : Compensating Control = Not Effective. Le CVRS reste à 92. **C'est exactement pourquoi la règle R3 'Angle mort interne interne' a été écrite.**"

**Transition** : "Reste une question : maintenant qu'on a nos 6 cases prioritaires, qui les traite ?"

---

## Acte 5 — Owner et remédiation (3 min, console)

**Navigation** : sur une case → onglet **Assignee / Owner** (à confirmer via `validation/open-questions-tenant.md` — le nom exact de l'onglet peut varier)

> "Chaque asset appartient à un owner group, qu'on a défini via les tags."

Ouvrir Inventory → Assets → **Groups** :
- `EM-demo-owner-secops` (secops@business.org) — Tier 0, VPN, ADFS
- `EM-demo-owner-it-corp` (it-corp@business.org) — Tier 1, endpoints Win, infra
- `EM-demo-owner-appdev` (appdev@business.org) — DMZ web, portail
- `EM-demo-owner-devops` (devops@business.org) — CI/CD, dev Linux, cloud

> "Résultat : quand la case Hero 3 (ADFS + Zerologon, R3) apparaît, elle atterrit chez SecOps. Quand la Hero 1 (VPN + PAN-OS, R2) apparaît, aussi SecOps. Quand Hero 4 (web + Spring4Shell, R4) apparaît, elle va chez AppDev. **Fini les emails 'quelqu'un peut regarder ?' en copie de 15 personnes.**"

**Ouvrir Vulnerability Intelligence** sur une CVE :
> "Chaque case pointe vers la page Vulnerability Intelligence — la KB Cortex avec la description, les liens vendor, les patches disponibles, l'exploit maturity, la timeline KEV. L'owner a tout pour agir en 2 clics."

**Transition** : "On a bouclé le funnel. Récapitulons."

---

## Acte 6 — Conclusion (2 min, retour slides)

**Slide 6 — Ce qu'on a démontré**
> "En 30 minutes, on a transformé 200+ findings de vulnérabilités bruts en 6 cases actionnables, chacune assignée au bon owner, chacune avec un SLA défendable, chacune avec une justification traçable via les 8 règles CVRS."

**Slide 7 — La valeur d'Exposure Management**
> "1. **CVRS contextuel** — le score reflète VOTRE environnement (Internet Exposed, Package-in-use, Compensating Controls), pas juste la CVE dans l'absolu. C'est le vrai différenciateur vs les scanners CVSS-only."
>
> "2. **Enrichissement continu via Vulnerability Intelligence** — CVSS, EPSS, KEV, exploit maturity mis à jour en temps réel côté Cortex, vous n'avez rien à maintenir."
>
> "3. **Valorisation de votre existant sécurité** — chaque WAF, chaque NGFW, chaque agent XDR déjà déployé réduit activement votre backlog de patch."
>
> "4. **Policies auditables** — 8 règles R1-R8 explicites, avec SLA, ajustables selon vos priorités métier. Défendables en audit ANSSI/NIS2/PCI."

**Slide 8 — Prochaines étapes**
> "Ce que Business Corp a fait en démo, on peut le mettre en place sur votre tenant en 2 semaines. Roadmap type :"
>
> - Semaine 1 : brancher vos scanners existants + définir vos asset groups
> - Semaine 2 : déclarer vos compensating controls + première itération de Vulnerability Policies
> - Après : automatisation via playbooks XSOAR (owner lookup AD, création tickets ITSM, push patch), et abonnement Vulnerability Intelligence pour les alertes CVE brûlantes du mois

**Slide 9 — Questions**
Laisser 5-10 min de Q&R hors chrono démo.

---

## Notes de pilotage démo

### Rythme
- **Ne pas se perdre dans les fonctionnalités adjacentes** (Vulnerability Policies avancées, integrations SSO, permissions RBAC) — noter les questions et renvoyer à la démo technique suivante
- **Insister sur l'ancrage métier** : chaque case = une action concrète pour une personne identifiée, avec un SLA défendable

### Pièges à éviter
- Ne pas dire "notre CVRS est mieux que le CVSS" — dire "le CVRS **complète** le CVSS avec le contexte spécifique à votre environnement"
- Ne pas promettre "zéro faux positif" — dire "on divise le bruit par 20+ avec une traçabilité complète"
- Ne pas confondre les 8 règles Business Corp avec des mécaniques natives Cortex — les règles R1-R8 sont **notre proposition** ajustable, les 4 filtres natifs (Not Internet Exposed / Low Business Impact / No Known Exploits / Low-Medium CVSS) sont **built-in**

### Backup si la console lag
- Screenshots dans `narratif/screenshots/` (à capturer lors de la validation `runbook/08`)
- Version démo enregistrée sur vidéo (à faire en préparation)

### Adaptation par audience
- **Audience très technique (SOC L2/L3)** : ajouter 5 min sur XQL derrière les cases (`dataset = uvm_findings`) et sur l'API de tags/groupes
- **Audience direction (CISO, DAF)** : réduire l'acte 3 à 2 hero cases (R1 Exploitation active périmètre + R3 Angle mort interne), allonger acte 6 sur le ROI et la mesure d'impact
- **Audience compliance (RSSI grand groupe)** : ajouter mention de la traçabilité audit (chaque décision de dépriorisation est loggée) et de la conformité ANSSI/NIS2 (R5 "Sans patch" impose un contrôle compensatoire — c'est du NIS2-compliant)

### Timing v1 — délai d'ingestion à anticiper

⚠️ **La 1ère ingestion Rapid7 met ~2h à peupler `uvm_findings`** (enrichissement Cortex Vulnerability Intelligence asynchrone). Prévoir la démo **au moins 4h après le premier deploy** pour être sûr que le CVRS est calculé sur toutes les CVE. Les fetches suivantes sont plus rapides (~15 min).
