# Runbook 02 — Déploiement des simulateurs sur GCP Cloud Run (mode vanilla)

Objectif : déployer les 2 simulateurs (Rapid7 InsightVM + Cyberwatch) en Cloud Run et récupérer leurs URLs publiques + credentials pour la config XSIAM.

⚠️ **Deux modes possibles** :
- **Mode vanilla (ce runbook)** : sims utilisés tels quels depuis les repos originaux. Narratif adapté aux ~18 assets natifs de chaque sim. Pas de garantie sur les hero cases.
- **Mode Business Corp patché (recommandé, voir `runbook/02b`)** : forks des 2 sims avec extra_assets custom + pinning des 6 hero cases via `config/business-corp-config.yaml`. Garantie de reproductibilité.

**Si vous suivez le mode patché : allez directement à [`02b-patch-sims-with-config.md`](02b-patch-sims-with-config.md)** — ce runbook 02 est alors uniquement consulté pour la partie "Dump discovery" (étape 2.4) et les credentials Cloud Run.

## Étape 2.1 — Cloner les 2 repos

```powershell
mkdir C:\Users\jcourtemanch\Documents\dev\demo\sims
cd C:\Users\jcourtemanch\Documents\dev\demo\sims

git clone https://github.com/JCourtemanche/Rapid7InsightVM-simul.git
git clone https://github.com/JCourtemanche/cyberwatch-simul.git
```

## Étape 2.2 — Déployer Rapid7 InsightVM simulator

```powershell
cd C:\Users\jcourtemanch\Documents\dev\demo\sims\Rapid7InsightVM-simul

# Choisir des credentials démo (pas de défaut nxadmin/nxadmin-secret en prod démo)
$env:NEXPOSE_USER = "businesscorp-demo"
$env:NEXPOSE_PASS = "R@pid7-D3mo-BusinessCorp-2026"

# Lancer le script de déploiement (utilise Cloud Build + Cloud Run)
bash deploy-cloudrun.sh
```

À la fin du script, noter l'URL Cloud Run affichée. Format attendu :
```
https://rapid7-nexpose-simulator-<hash>-ew.a.run.app
```

**Sanity check** :
```powershell
$url = "https://rapid7-nexpose-simulator-<hash>-ew.a.run.app"
curl.exe -u "businesscorp-demo:R@pid7-D3mo-BusinessCorp-2026" "$url/api/3/assets?size=5"
```
Attendu : JSON avec 5 assets (personas Business Corp).

## Étape 2.3 — Déployer Cyberwatch simulator

```powershell
cd C:\Users\jcourtemanch\Documents\dev\demo\sims\cyberwatch-simul

$env:CW_ACCESS_KEY = "cw-businesscorp-demo-access"
$env:CW_SECRET_KEY = "cw-BusinessCorp-Demo-S3cret-2026"

bash deploy-cloudrun.sh
```

URL attendue :
```
https://cyberwatch-simulator-<hash>-ew.a.run.app
```

**Sanity check** :
```powershell
$url = "https://cyberwatch-simulator-<hash>-ew.a.run.app"
curl.exe -u "cw-businesscorp-demo-access:cw-BusinessCorp-Demo-S3cret-2026" "$url/api/v3/ping"
```
Attendu : `{"pong": true, ...}` ou équivalent.

## Étape 2.4 — Dump discovery (⚠️ étape critique narratif)

But : savoir **exactement** quelles CVE sont assignées à quels assets par les catalogues déterministes, pour choisir les hero cases parmi ce qui existe réellement.

**Option A — Depuis les endpoints Cloud Run** (le plus simple) :

```powershell
# Créer un dossier de sortie
$out = "C:\Users\jcourtemanch\Documents\dev\demo\exposure-management\validation\discovery"
mkdir $out -Force

# Rapid7 — lister tous les assets
$rapid7 = "https://rapid7-nexpose-simulator-<hash>-ew.a.run.app"
$cwUrl  = "https://cyberwatch-simulator-<hash>-ew.a.run.app"

curl.exe -u "businesscorp-demo:R@pid7-D3mo-BusinessCorp-2026" "$rapid7/api/3/assets?size=100" > "$out\rapid7-assets.json"

# Pour chaque asset ID, lister ses vulnerabilities
# (adapter le loop selon la structure de retour — voir README du sim pour le format exact)
$assets = (Get-Content "$out\rapid7-assets.json" | ConvertFrom-Json).resources
foreach ($a in $assets) {
  curl.exe -u "businesscorp-demo:R@pid7-D3mo-BusinessCorp-2026" `
    "$rapid7/api/3/assets/$($a.id)/vulnerabilities?size=100" > "$out\rapid7-asset-$($a.id)-vulns.json"
}

# Cyberwatch — équivalent
curl.exe -u "cw-businesscorp-demo-access:cw-BusinessCorp-Demo-S3cret-2026" "$cwUrl/api/v3/vulnerabilities/servers?per_page=100" > "$out\cyberwatch-servers.json"
```

**Option B — Script Python** (plus lisible) : voir `sims/dump_discovery.py` à créer si besoin (non prioritaire v1).

**Analyse** :
- Ouvrir `rapid7-asset-*-vulns.json`, chercher les CVE hero de `narratif/hero-cases.md` (CVE-2021-44228, CVE-2021-26855, CVE-2020-1472, CVE-2024-3400...)
- Noter sur quel asset (`hostName` + `id`) chaque CVE hero est effectivement présente
- Si une hero case candidate n'est pas assignée à l'asset attendu → utiliser le "Plan B" documenté dans `hero-cases.md` OU choisir un autre asset du même type de zone

Consigner les résultats dans `validation/discovery-results.md` (à créer manuellement — 5-10 lignes suffit).

## Étape 2.5 — Sauvegarder les credentials démo

Créer localement (⚠️ ne pas commit) :

`C:\Users\jcourtemanch\Documents\dev\demo\exposure-management\.secrets.local.md`
```
# Credentials Cloud Run sims (ne PAS commit)

## Rapid7 InsightVM sim
URL: https://rapid7-nexpose-simulator-<hash>-ew.a.run.app
User: businesscorp-demo
Pass: R@pid7-D3mo-BusinessCorp-2026

## Cyberwatch sim
URL: https://cyberwatch-simulator-<hash>-ew.a.run.app
Access Key: cw-businesscorp-demo-access
Secret Key: cw-BusinessCorp-Demo-S3cret-2026
```

Ajouter `.secrets.local.md` à `.gitignore` si vous versionnez ce dossier.

## Étape 2.6 — Teardown temporaire (optionnel entre deux démos)

Pour économiser le compute :

```powershell
gcloud run services update-traffic rapid7-nexpose-simulator --to-revisions=LATEST=0 --region=europe-west1
gcloud run services update-traffic cyberwatch-simulator --to-revisions=LATEST=0 --region=europe-west1
```

Pour redémarrer :
```powershell
gcloud run services update-traffic rapid7-nexpose-simulator --to-latest --region=europe-west1
gcloud run services update-traffic cyberwatch-simulator --to-latest --region=europe-west1
```

## Suivant

- Si mode vanilla : → [`03-configure-xsiam-rapid7.md`](03-configure-xsiam-rapid7.md)
- Si vous voulez basculer sur le mode patché : → [`02b-patch-sims-with-config.md`](02b-patch-sims-with-config.md)
