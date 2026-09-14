# Les 6 règles narratives du funnel — source de vérité

Ces 6 règles sont **votre grille de lecture pédagogique** (screenshot fourni au démarrage du projet). Elles ne sont **pas des règles techniques dans Cortex** : Cortex applique automatiquement le funnel natif (Not Internet Exposed, Low Business Impact, No Known Exploits, Low/Medium CVSS, + Policy custom) et calcule le CVRS. Vos 6 règles sont une **surcouche narrative** qui rend l'algorithme lisible pour un décideur non-technique.

## Tableau canonique (à afficher en slide "Acte 1")

| # | Règle | Logique / Critères (Cortex Policy) | Objectif & Justification | Sévérité |
|---|-------|------------------------------------|---------------------------|----------|
| 1 | **Urgence Périmètre** | CVRS ≥ 90 + Internet Exposed = True | L'urgence absolue. La faille est critique, accessible depuis Internet, et vos défenses actuelles (compensating controls) sont jugées insuffisantes par l'algorithme pour bloquer l'attaque. | **Critique** |
| 2 | **Arme aux mains de l'ennemi** | CISA KEV = True + Internet Exposed = True | Exploitation active. Peu importe le score, si la faille est dans le catalogue CISA KEV et exposée, elle est la cible n°1 des scanners automatiques d'attaquants. | **Critique** |
| 3 | **Le Maillon Faible (Interne)** | CVSS ≥ 8.0 + CVRS ≈ CVSS + Compensating Control = None | Absence de protection. Ici, on cible les actifs où le CVRS ne baisse pas par rapport au CVSS. Cela signifie que l'actif n'a ni agent XDR, ni protection réseau. C'est une cible facile en interne. | **Haute** |
| 4 | **Menace Imminente (EPSS)** | EPSS > 90% + Internet Exposed = True | Anticipation. L'EPSS prédit une exploitation imminente. En créant un incident ici, on devance l'entrée de la CVE dans le catalogue KEV (proactif). | **Haute** |
| 5 | **Risque Confirmé (Workload)** | CVRS ≥ 70 + Package-in-use = True | Exploitabilité prouvée. L'agent Cortex confirme que le package vulnérable est chargé en mémoire (fichier sur disque, il est au cœur du runtime). | **Haute** |
| 6 | **Nettoyage de Surface** | CVRS ≥ 60 + Internet Exposed = True | Hygiène ASM. Vulnérabilités modérées mais visibles. On cherche ici à réduire la "découvrabilité" de l'entreprise sur Shodan ou Censys. | **Moyenne** |

## Correspondance avec les filtres natifs Cortex

| Votre règle narrative | Signaux Cortex correspondants | Où le voir dans la console |
|------------------------|-------------------------------|------------------------------|
| 1 — Urgence Périmètre | CVRS ≥ 90 (Overview) + "Internet Exposed" badge (ASM/AST) | Vulnerability Issue → Overview + Risk Details onglet "Asset Risk" |
| 2 — Arme aux mains de l'ennemi | Badge "In CISA KEV" + Internet Exposed | Overview → Exploit Intelligence facteur |
| 3 — Maillon Faible | Compensating Control = "Unknown" ou "Not Effective" + CVSS élevé | Risk Details onglet "Compensating Controls" |
| 4 — Menace Imminente | EPSS > 0.9 + Internet Exposed | Overview → EPSS bar + Asset Risk facteur |
| 5 — Risque Confirmé Workload | Attack Surface Testing "Package In Use" = True | Risk Details onglet "Environment Risk" |
| 6 — Nettoyage de Surface | CVRS 60-90 + Internet Exposed | Overview + funnel Command Center |

## Mapping avec le funnel Cortex natif

Les 4 dépriorisations natives Cortex (Command Center → Deprioritized filters) reproduisent implicitement vos règles :

- Vos règles **1, 2, 4, 6** = SURVIVANTES du filtre "Not Internet Exposed"
- Vos règles **1, 2, 4** = SURVIVANTES du filtre "No Known Public Exploits" (EPSS ≥ 80% ou preuve d'exploitation)
- Vos règles **1, 2, 3, 5** = SURVIVANTES du filtre "Low/Medium CVSS Base Score"
- **Toutes** doivent survivre au filtre "Low Business Impact" (asset group ≠ dev/test/low-crit)

Votre Vulnerability Policy custom `POL-BusinessCorp-Tier0-Escalate` (runbook 07) amplifie la règle 3 pour les actifs Tier 0 : elle force `severity = Critical` même si CVSS < 8, garantissant qu'un tier 0 sans compensating control ressort toujours.

## Utilisation en démo

**Acte 1** (slide) : afficher ce tableau tel quel, en français, à côté du schéma d'infra Business Corp. Message : "Voici la grille de lecture qu'on va appliquer sur la console."

**Acte 3** (drill-down console) : pour chaque case, dire à haute voix "Cette case coche la règle N°X — voici pourquoi" en pointant les preuves dans l'onglet Risk Details.

## Personnalisation client

Si le client a ses propres priorités (ex : compliance HDS, PCI-DSS, souveraineté), adapter le libellé de la règle 6 vers "Conformité HDS" ou "Data at rest — souveraineté" et créer une Vulnerability Policy supplémentaire mappée sur les asset groups concernés.
