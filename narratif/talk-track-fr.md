# Talk track FR — Démo Exposure Management (35 min)

Script démo complet, structuré en **6 actes**. Durées indicatives — chrono en main lors des répétitions.

**Public cible** : RSSI, responsable SOC, ops sécurité — profils décideurs qui veulent comprendre la logique avant les détails techniques.

**Matériel** :
- Slides : schéma d'infra `business-corp-infra.png` + tableau des 6 règles `funnel-rules-table.md`
- Console XSIAM avec le tenant configuré selon le runbook
- Backup : screenshots des cases attendues (si le tenant lag)

---

## Acte 1 — Le problème (5 min, slides uniquement)

**Slide 1 — Business Corp, notre PME fictive**
> "Aujourd'hui, on va prendre une entreprise fictive, Business Corp. Environ 250 machines, une configuration assez classique de PME/ETI française. Un peu de cloud, un parc endpoint Windows majoritaire, dix développeurs Linux, quelques serveurs métier."

Afficher le schéma d'infra `business-corp-infra.png`. Pointer avec le curseur :
- La DMZ web (portail public, serveur web)
- Le boîtier VPN
- L'Active Directory
- L'Exchange
- Les 2 ESXi qui hébergent tout ça
- Le parc endpoint

**Slide 2 — Ce que le RSSI a déjà en place**
> "Business Corp a déjà investi. Deux scanners de vulnérabilités : Rapid7 InsightVM pour le scan réseau, et Cyberwatch en agent sur les endpoints. Deux excellentes solutions. Le problème n'est pas la détection."

**Slide 3 — Le problème du lundi matin**
> "Lundi 9h. Le RSSI ouvre les deux consoles. Rapid7 lui remonte 2 000 vulnérabilités actives, dont 150 marquées critiques. Cyberwatch de son côté remonte 1 800 vulnérabilités, dont 100 critiques. Beaucoup de recouvrement entre les deux, mais aussi beaucoup d'unicités. **Question : par quoi commencer ?**"

Pause. Laisser la question flotter.

> "On va voir que la vraie question n'est pas 'quelle est la CVSS la plus élevée' — c'est 'quelle est la vulnérabilité la plus proche d'être exploitée, sur l'actif qui compte le plus, sans protection compensatoire efficace'. Et c'est exactement ce que fait le funnel de priorisation d'Exposure Management."

**Slide 4 — La grille de lecture (afficher `funnel-rules-table.md`)**
> "Avant de basculer sur la console, je vous donne notre grille de lecture. 6 règles. On les retrouvera toutes dans les cases qu'on va analyser ensemble."

Passer rapidement sur les 6 règles, insister sur la règle 3 "Maillon Faible" :
> "Retenez surtout la règle 3 : quand un actif n'a **aucun contrôle compensatoire**, le CVRS reste égal au CVSS. C'est le signal fort d'un angle mort dans votre défense."

**Transition** : "Bascule sur la console."

---

## Acte 2 — Le funnel Exposure Management (10 min, console)

**Navigation** : Cortex XSIAM → Posture Management → Exposure Management → **Command Center**

> "Voici le Command Center d'Exposure Management. Le funnel apparaît en haut."

Pointer chaque étape du funnel de gauche à droite :
1. **Vulnerabilities** — "Le total brut ingéré depuis Rapid7 et Cyberwatch. Chiffre autour de 3 500."
2. **Duplicative Findings removed** — "Cortex a dédupliqué. Une CVE-2021-44228 vue par Rapid7 ET Cyberwatch sur le même hôte = 1 seule finding."
3. **Unique Vulnerabilities** — "On tombe à environ 2 200 findings uniques."
4. **Deprioritized** — "Ici, 4 filtres natifs et 1 filtre policy s'appliquent."
5. **Open Issues** — "~15-30 issues survivent."
6. **Cases** — "Groupées par 'fix commun'. On arrive à ~6-15 cases actionnables."

**Zoom sur les Deprioritized filters** : cliquer pour ouvrir le détail.
> "Regardez : le premier filtre c'est 'Not Internet Exposed'. Cortex utilise les données ASM et cloud pour savoir si l'actif est réellement joignable depuis Internet. Deuxième filtre : 'Low Business Impact' — via les asset groups qu'on a définis. Troisième : 'No Known Public Exploits' — EPSS < 80% et pas de KEV. Quatrième : 'Low/Medium CVSS'. Cinquième : notre policy custom."

**Sur la 5e (Policy)** :
> "Ici on a créé une policy `POL-BusinessCorp-Tier0-Escalate`. Elle dit : pour tout ce qui est dans le groupe `grp-business-tier0`, jamais de dépriorisation, sévérité minimale = Critical. **C'est votre levier pour encoder les règles métier propres à votre organisation.**"

**Pointer les chiffres finaux** :
> "Résultat : de 2 200 findings à 6-15 cases. On vient d'appliquer un facteur 200 de réduction du bruit — et on n'a rien perdu de matériel, tout est traçable."

**Transition** : "On va maintenant ouvrir ces cases une par une, dans l'ordre de nos 6 règles narratives."

---

## Acte 3 — Les 6 règles en action (10 min, drill-down)

**Navigation** : Command Center → onglet **Cases** → tri par CVRS descendant.

Pour chaque hero case, dérouler la structure suivante :
1. **Annoncer la règle** : "Case n°X — Règle N°Y : [nom]"
2. **Ouvrir la case** : vue Overview
3. **Pointer les preuves** : CVRS, badges (KEV, Internet Exposed), EPSS, exploit maturity
4. **Ouvrir Risk Details** : montrer le facteur qui domine (Asset Risk, Exploit Intel, Environment Risk, Compensating Controls)
5. **Storyline** (voir `hero-cases.md` pour les scripts détaillés de 30-60 sec par case)

**Ordre recommandé** (impact narratif décroissant) :
1. Hero 1 — Urgence Périmètre (`srv-vpn` + CVE-2024-3400)
2. Hero 2 — Arme aux mains de l'ennemi (`srv-mail` + ProxyLogon)
3. Hero 3 — Maillon Faible (`esxi-01` + Zerologon-like) ← **temps fort pédagogique, 60 sec**
4. Hero 4 — Menace Imminente (`alice` + Follina)
5. Hero 5 — Risque Confirmé Workload (`srv-ci` + Log4Shell avec Package-in-Use)
6. Hero 6 — Nettoyage de Surface (`srv-portail` + OpenSSL modéré)

**Insister sur les contrastes** :
- Hero 3 vs Hero 5 : deux CVE différentes, mais le contraste vient de la présence/absence de compensating control
- Hero 2 vs Hero 4 : KEV vs EPSS — deux façons complémentaires de mesurer l'exploitabilité

**Transition** : "On a vu les compensating controls jouer un rôle central dans le calcul du CVRS. Allons voir comment ils sont configurés."

---

## Acte 4 — Compensating controls (5 min, console)

**Navigation** : Settings → Exposure Management → **Security Controls**

> "Voici les contrôles compensatoires qu'on a déclarés dans Business Corp. Deux types : ceux détectés automatiquement par Cortex, et ceux qu'on a déclarés manuellement."

**Pointer les contrôles auto-détectés** :
- **Cortex XDR agent** : "Détecté sur tous les endpoints qui ont l'agent installé. Cortex regarde même la configuration du profil exploit-protection — si 'Known Vulnerable Processes Protection' est en Block, la protection est jugée Effective sur la CVE correspondante."

**Pointer les contrôles manuels** :
- **WAF F5** sur `grp-zone-dmz-web` : "Déclaré manuellement, catégorie Network Security / WAF, vendor F5. Portée : le groupe d'actifs DMZ web."
- **PANW NGFW** sur `grp-zone-dmz-*` : "Idem, NGFW hardware — pas de télémétrie automatique donc on l'a déclaré."

**Ouvrir un contrôle** : montrer les 4 statuts d'effectiveness (Effective / Partially / Not Effective / Unknown) et l'onglet Rules.

> "Cortex ne dit pas 'le WAF F5 protège tout'. Il applique un moteur de règles : si la CVE est une injection SQL, alors WAF = Effective. Si c'est une élévation de privilèges locale, alors WAF = Not Applicable. **Le contrôle compensatoire est mesuré par CVE**."

**Revenir à une case** (Hero 3 ESXi) :
> "C'est pourquoi notre ESXi ressort. Pas d'agent XDR possible, pas de WAF pertinent, pas de NGFW efficace pour une exploitation post-authent. Cortex dit : Compensating Control = Unknown. Le CVRS ne baisse pas."

**Transition** : "Reste une question : maintenant qu'on a nos 6 cases prioritaires, qui les traite ?"

---

## Acte 5 — Owner et remédiation (3 min, console)

**Navigation** : sur une case → onglet **Assignee / Owner** (à confirmer via `validation/open-questions-tenant.md` — le nom exact de l'onglet peut varier)

> "Chaque asset appartient à un owner group, qu'on a défini via les tags."

Ouvrir Inventory → Assets → **Groups** :
- `grp-owner-secops` (secops@business.org) — Tier 0, VPN
- `grp-owner-it-corp` (it-corp@business.org) — Tier 1, endpoints Win, infra
- `grp-owner-appdev` (appdev@business.org) — DMZ web
- `grp-owner-devops` (devops@business.org) — CI/CD, dev Linux, cloud

> "Résultat : quand la case Hero 3 (ESXi) apparaît, elle atterrit chez IT Corp. Quand la Hero 1 (VPN) apparaît, elle va chez SecOps. **Fini les emails "quelqu'un peut regarder ?" en copie de 15 personnes.**"

**Ouvrir Vulnerability Intelligence** sur une CVE :
> "Chaque case pointe vers la page Vulnerability Intelligence — la KB Cortex avec la description, les liens vendor, les patches disponibles. L'owner a tout pour agir en 2 clics."

**Transition** : "On a bouclé le funnel. Récapitulons."

---

## Acte 6 — Conclusion (2 min, retour slides)

**Slide 5 — Ce qu'on a démontré**
> "En 30 minutes, on a transformé 2 sources de vulnérabilités hétérogènes en 6 cases actionnables, chacune assignée au bon owner, chacune avec une justification traçable."

**Slide 6 — La valeur d'Exposure Management**
> "1. Consolidation multi-scanners avec dédup automatique — pas besoin de choisir entre vos outils existants."
>
> "2. Enrichissement continu via Vulnerability Intelligence — CVSS, EPSS, KEV, exploit maturity, mis à jour en temps réel côté Cortex, vous n'avez rien à maintenir."
>
> "3. CVRS contextuel — le score reflète VOTRE environnement, pas juste la CVE dans l'absolu."
>
> "4. Valorisation de votre existant sécurité — chaque WAF, chaque NGFW, chaque agent XDR déjà déployé réduit activement votre backlog de patch."

**Slide 7 — Prochaines étapes**
> "Ce que Business Corp a fait en démo, on peut le mettre en place sur votre tenant en 2 semaines. Roadmap type :"
>
> - Semaine 1 : brancher vos scanners existants + définir vos asset groups
> - Semaine 2 : déclarer vos compensating controls + première itération de Vulnerability Policies
> - Après : automatisation via playbooks XSOAR (owner lookup AD, création tickets ITSM, push patch), et abonnement Vulnerability Intelligence pour les alertes CVE brûlantes du mois

**Slide 8 — Questions**
Laisser 5-10 min de Q&R hors chrono démo.

---

## Notes de pilotage démo

### Rythme
- **Ne pas se perdre dans les fonctionnalités adjacentes** (Vulnerability Policies avancées, integrations SSO, permissions RBAC) — noter les questions et renvoyer à la démo technique suivante
- **Insister sur l'ancrage métier** : chaque case = une action concrète pour une personne identifiée

### Pièges à éviter
- Ne pas dire "notre CVRS est mieux que le CVSS" — dire "le CVRS complète le CVSS avec le contexte spécifique à votre environnement"
- Ne pas promettre "zéro faux positif" — dire "on divise le bruit par 100+ avec une traçabilité complète"

### Backup si la console lag
- Screenshots dans `narratif/screenshots/` (à capturer lors de la validation `runbook/08`)
- Version démo enregistrée sur vidéo (à faire en préparation)

### Adaptation par audience
- **Audience très technique (SOC L2/L3)** : ajouter 5 min sur XQL derrière les cases (`dataset = uvm_findings`) et sur l'API de tags/groupes
- **Audience direction (CISO, DAF)** : réduire l'acte 3 à 2 hero cases (1 et 3), allonger acte 6 sur le ROI et la mesure d'impact
- **Audience compliance (RSSI grand groupe)** : ajouter mention de la traçabilité audit (chaque décision de dépriorisation est loggée) et de la conformité ANSSI/NIS2
