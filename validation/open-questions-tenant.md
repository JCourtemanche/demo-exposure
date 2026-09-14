# Points à valider live dans le tenant XSIAM

⚠️ **À faire AVANT de dérouler le runbook 02+**. Les réponses peuvent modifier des sections du runbook (notamment tags, ingestion Cyberwatch, ownership).

Ces points sont issus du rapport d'exploration de la documentation Cortex Exposure Management / Vulnerability Management : la doc publique ne répond pas explicitement à ces questions. Chacune doit être testée directement dans votre tenant.

Renseigner les réponses dans ce fichier au fur et à mesure — devient votre "notes tenant" persistantes.

---

## Q1 — Format des tags sur les assets

**Question** : Les tags sont-ils au format `key=value` (ex : `zone=dmz-web`) ou flat labels (ex : `dmz-web`) ? Existe-t-il un endpoint API dédié pour appliquer des tags en masse ?

**Comment tester** :
1. XSIAM → Inventory → Assets → sélectionner un asset → onglet Tags → tenter d'ajouter un tag avec `=` dedans
2. XSIAM → Settings → API Keys → créer une clé test → chercher un endpoint `/assets/{id}/tags` dans la doc API du tenant
3. Alternative : XQL `dataset = asset_inventory | filter tags contains "="` — voir si le résultat est non vide

**Impact runbook** :
- Si key=value : garder `zone=dmz-web`, filtres `tags contains "zone=dmz-web"`
- Si flat : simplifier en `dmz-web`, filtres `tags contains "dmz-web"`
- Si pas d'API tag dédiée : passer par API `assets/update` avec le champ tags dans le body

**Réponse (à remplir)** :
```
Format : [key=value | flat | autre]
Endpoint API : 
Notes :
```

---

## Q2 — Cyberwatch built-in ou Partner Contribution ?

**Question** : Le content pack "Cyberwatch (Partner Contribution)" est-il disponible sur Cortex Marketplace ? Sinon, le seul chemin est la Vulnerability Ingest API custom.

**Comment tester** :
1. XSIAM → Marketplace → chercher "Cyberwatch"
2. Vérifier statut : "Available" (installable) vs "Not found"

**Impact runbook** :
- Si Available : suivre Plan A dans `runbook/04-configure-xsiam-cyberwatch.md`
- Si Not found : suivre Plan B (script Python + Vulnerability Ingest API)

**Réponse (à remplir)** :
```
Disponible en Marketplace : [Oui/Non]
Version : 
Notes :
```

---

## Q3 — Scope du CVRS (per-CVE / per-asset / per-finding)

**Question** : Le CVRS est-il calculé une seule fois par CVE (score absolu) ou par couple (CVE, asset) (score contextuel) ? Ceci détermine si les compensating controls affectent réellement le score visible.

**Comment tester** :
1. Prendre 2 assets ayant la même CVE (ex : Log4Shell sur `srv-ci` et `srv-web-01`)
2. L'un avec compensating control efficace (XDR + WAF), l'autre sans
3. Ouvrir les 2 vulnerability issues → comparer le CVRS

**Impact runbook** :
- Si per-finding (contextuel) : les hero cases fonctionnent comme prévu (Acte 4 démontre l'effet)
- Si per-CVE (absolu) : ajuster le talk track — le CVRS ne bougera pas d'un asset à l'autre, seule la sévérité/priorisation change via les policies

**Réponse (à remplir)** :
```
Scope : [per-CVE | per-asset | per-finding]
Écart CVRS observé : 
Notes :
```

---

## Q4 — Champ `owner` natif sur l'asset ?

**Question** : Y a-t-il un champ `owner` ou `owner_email` de premier niveau sur l'objet asset dans XSIAM ? Ou l'ownership est-il représenté uniquement via tags/asset groups ?

**Comment tester** :
1. XSIAM → Inventory → Assets → cliquer un asset → panneau détail → chercher un champ "Owner"
2. XQL : `dataset = asset_inventory | fields *` → observer les colonnes disponibles
3. API : GET sur un asset et regarder le JSON complet

**Impact runbook** :
- Si champ owner natif : ajouter à `runbook/05` une étape pour populer via API
- Sinon : rester sur l'approche groupes `grp-owner-*` (déjà documentée)

**Réponse (à remplir)** :
```
Champ owner natif : [Oui/Non]
Nom du champ : 
Notes :
```

---

## Q5 — Manual override du flag "Internet Exposed"

**Question** : Peut-on manuellement marquer un asset comme "Internet Exposed" via UI/API, ou le flag dérive-t-il uniquement de sources automatiques (ASM/Xpanse, CNA cloud, Attack Surface Testing) ?

**Comment tester** :
1. XSIAM → Inventory → Assets → cliquer un asset non-exposé → chercher un toggle "Internet Exposed" éditable
2. Alternative : chercher dans les Vulnerability Policies s'il existe un opérateur pour forcer le flag

**Impact runbook** :
- Si override manuel possible : marquer explicitement `srv-vpn`, `srv-portail`, `srv-web-01`, `smtp-relay` comme Internet Exposed → garantit qu'ils passent les filtres
- Sinon : dépendre d'ASM (nécessite l'addon Xpanse) ou de la géométrie détectée par le sim (peu probable)

⚠️ **Ce point est bloquant pour le narratif** si aucune méthode n'est disponible : les hero cases 1, 2, 4, 6 s'effondrent. À valider en priorité.

**Réponse (à remplir)** :
```
Override manuel : [UI | API | Aucun]
Source alternative : [ASM Xpanse actif ? / CNA cloud ? / autre]
Notes :
```

---

## Q6 — MITRE ATT&CK mapping sur les findings

**Question** : Les vulnerability findings portent-ils un mapping MITRE ATT&CK (technique / tactique) ? Si oui, d'où vient-il ?

**Comment tester** :
1. XSIAM → Vulnerability Issues → ouvrir une case → chercher un panneau MITRE
2. XQL : `dataset = uvm_findings | filter mitre_technique != null | limit 5`

**Impact runbook** :
- Si mapping présent : à intégrer dans le talk track (Acte 3) — montre la corrélation avec la kill chain
- Sinon : ne pas mentionner, éviter la question

**Réponse (à remplir)** :
```
Mapping MITRE présent : [Oui/Non]
Source : 
Notes :
```

---

## Q7 — Patch availability

**Question** : Le finding a-t-il un champ boolean `patch_available` ou seulement un lien vers l'advisory vendor ?

**Comment tester** :
1. Ouvrir un finding sur CVE-2021-44228 (Log4Shell — patch existe depuis 2021)
2. Chercher un badge / champ "Patch Available: Yes"

**Impact runbook** :
- Si champ boolean : ajouter à `talk-track` Acte 5 ("Cortex vous dit lesquelles ont un patch, lesquelles nécessitent un workaround")
- Sinon : mentionner "lien vers advisory vendor" et suffit

**Réponse (à remplir)** :
```
Champ patch_available : [Boolean | Lien | Aucun]
Notes :
```

---

## Q8 — Endpoint exact Vulnerability Ingest API

**Question** : Quel est le endpoint REST exact pour push des vulnerabilités custom (utilisé dans Plan B `runbook/04`) ? La doc mentionne "Vulnerability Ingest API" mais le path exact n'est pas dans les pages publiques.

**Comment tester** :
1. XSIAM → Help / Documentation → chercher "Vulnerability Ingest API"
2. Alternative : Settings → API Reference intégrée au tenant
3. Ticket support PANW si introuvable

**Impact runbook** :
- Remplacer le placeholder `/public_api/v1/vulnerability_management/ingest` dans `runbook/04` Plan B script Python
- Ajouter le format exact du payload attendu

**Réponse (à remplir)** :
```
Endpoint : 
Version API : 
Auth : 
Payload schema : (résumé ou lien)
Notes :
```

---

## Q9 (bonus) — Cycle Discovery → Active des Compensating Controls

**Question** : Le cycle 24h documenté est-il incompressible ? Peut-on forcer la transition vers "Active" ?

**Comment tester** :
1. Créer un contrôle manuel test
2. Chercher un bouton "Force Activate" ou équivalent
3. Attendre 1 h et voir si le status change (ou reste Discovery)

**Impact runbook** :
- Si compressible : réduire le buffer temps dans `runbook/06` de 24h à quelques heures
- Sinon : garder la recommandation "48h avant démo"

**Réponse (à remplir)** :
```
Cycle raccourcissable : [Oui/Non]
Notes :
```

---

## Synthèse

Une fois les 8-9 questions renseignées, faire un diff avec les hypothèses par défaut du runbook et ajuster :
- `runbook/05` si Q1 différent de key=value
- `runbook/04` si Q2 = Not found
- `narratif/` si Q3/Q4/Q5/Q6/Q7 changent le talk track
- `runbook/04` Plan B si Q8 apporte le endpoint exact
- `runbook/06` § "cycle 24h" si Q9 raccourcissable

## Références

- Doc Exposure Management : https://cortex-docs.paloaltonetworks.com/cortex-xdr-5.x/detect-investigate-and-respond-to-threats/exposure-management
- Doc Vulnerability Management : https://cortex-docs.paloaltonetworks.com/cortex-xdr-5.x/detect-investigate-and-respond-to-threats/vulnerability-management
- Doc Asset Groups : https://cortex-docs.paloaltonetworks.com/cortex-xdr-5.x/detect-investigate-and-respond-to-threats/asset-management/asset-groups
- Doc Security Controls : https://cortex-docs.paloaltonetworks.com/cortex-xdr-5.x/detect-investigate-and-respond-to-threats/exposure-management/security-controls
