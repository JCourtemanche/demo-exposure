# Runbook 02b — Patcher les sims avec la config Business Corp

Objectif : appliquer la configuration `business-corp-config.yaml` aux 2 forks de simulateurs pour garantir :
- Les 4 assets narratifs custom (srv-portail, srv-adfs-01, srv-print, smtp-relay)
- Les 6 hero cases pinnées (asset ↔ CVE)

⚠️ **Ce runbook remplace la partie "déploiement vanilla" du runbook 02 si vous suivez l'approche B (fork + config). Le runbook 02 vanilla reste valide si vous avez choisi l'approche A (as-is).**

## Prérequis

- Runbook 01 complété
- Python 3.11+ + `pip install pyyaml`
- Compte GitHub personnel (pour héberger vos forks — ou juste clones locaux si vous ne pushez pas)

## Étape 2b.1 — Forker et cloner les 2 repos

**Option 2b.1.a — Vrais forks GitHub** (recommandé si vous voulez versionner vos patches) :

1. Sur GitHub : bouton "Fork" sur `https://github.com/JCourtemanche/Rapid7InsightVM-simul` et `https://github.com/JCourtemanche/cyberwatch-simul`
2. Cloner vos forks :
```powershell
mkdir C:\Users\jcourtemanch\Documents\dev\demo\sims
cd C:\Users\jcourtemanch\Documents\dev\demo\sims

git clone https://github.com/<your-user>/Rapid7InsightVM-simul.git
git clone https://github.com/<your-user>/cyberwatch-simul.git
```

**Option 2b.1.b — Clones locaux uniquement** (si vous ne voulez pas polluer GitHub) :

```powershell
mkdir C:\Users\jcourtemanch\Documents\dev\demo\sims
cd C:\Users\jcourtemanch\Documents\dev\demo\sims

git clone https://github.com/JCourtemanche/Rapid7InsightVM-simul.git
git clone https://github.com/JCourtemanche/cyberwatch-simul.git
```

Créer une branche locale pour vos patches dans chaque repo :
```powershell
cd Rapid7InsightVM-simul; git checkout -b businesscorp-demo
cd ..\cyberwatch-simul; git checkout -b businesscorp-demo
```

## Étape 2b.2 — Éditer la config `business-corp-config.yaml`

Ouvrir `C:\Users\jcourtemanch\Documents\dev\demo\exposure-management\config\business-corp-config.yaml`.

Vérifier / adapter :
- Section `extra_assets` — les 4 assets custom (peut être enrichie)
- Section `hero_pinning` — les 6 paires (asset, CVE)
- Section `sync_targets` — **chemins locaux des forks** (obligatoirement à jour)

## Étape 2b.3 — Appliquer le patch UNE FOIS sur chaque fork

Le patch est un ajout **isolé et idempotent** de ~4 blocs de code dans `generators/assets.py`. À appliquer une seule fois. Après ça, toute évolution de la démo passe par le YAML uniquement.

- Pour Rapid7 : suivre `config/patches/rapid7-patch.md` étapes 1 à 4
- Pour Cyberwatch : suivre `config/patches/cyberwatch-patch.md` étapes 1 à 4

Commit dans la branche `businesscorp-demo` :
```powershell
cd C:\Users\jcourtemanch\Documents\dev\demo\sims\Rapid7InsightVM-simul
git add simulator/generators/assets.py
git commit -m "feat: business-corp overrides hook for extra_assets and CVE pinning"

cd ..\cyberwatch-simul
git add simulator/generators/assets.py
git commit -m "feat: business-corp overrides hook for extra_assets and CVE pinning"
```

## Étape 2b.4 — Générer et synchroniser `business_corp_overrides.py`

```powershell
cd C:\Users\jcourtemanch\Documents\dev\demo\exposure-management
python config\sync-config-to-sims.py
```

Sortie attendue :
```
✅ rapid7: wrote C:\...\sims\Rapid7InsightVM-simul\simulator\generators\business_corp_overrides.py
✅ cyberwatch: wrote C:\...\sims\cyberwatch-simul\simulator\generators\business_corp_overrides.py

--- Next steps ---
...
```

Le script est idempotent — safe à relancer.

## Étape 2b.5 — Test local avant Cloud Run

Avant de payer un cycle de build/deploy, valider localement :

**Rapid7** :
```powershell
cd C:\Users\jcourtemanch\Documents\dev\demo\sims\Rapid7InsightVM-simul
python -m pip install -r simulator/requirements.txt
python -m flask --app simulator.app run --port 5001
```

Dans un autre terminal :
```powershell
# Vérifier présence des extra assets
curl -u nxadmin:nxadmin-secret "http://localhost:5001/api/3/assets?size=30" | ConvertFrom-Json | Select-Object -ExpandProperty resources | Select-Object hostName | Where-Object hostName -like "*business.org"
```
Attendu (18 personas+servers natifs + 4 extras Rapid7 = 22 assets Business Corp) :
```
alice.business.org, bob.business.org, charlie.business.org, ...
srv-web-01.business.org, srv-web-02.business.org, srv-db-01.business.org, ...
srv-vpn.business.org, srv-monitoring.business.org, srv-ci.business.org,
cloud-lb-01.business.org, cloud-app-01.business.org,
srv-portail.business.org, srv-adfs-01.business.org, srv-print.business.org, smtp-relay.business.org
```

**Vérifier le pinning** — pour chaque hero case, vérifier que la CVE attendue est bien assignée :
```powershell
# Trouver l'asset id de srv-vpn.business.org
$vpn = curl -u nxadmin:nxadmin-secret "http://localhost:5001/api/3/assets?size=100" | ConvertFrom-Json | Select-Object -ExpandProperty resources | Where-Object hostName -eq "srv-vpn.business.org"
$vpnId = $vpn.id

# Lister ses vulnérabilités et chercher CVE-2024-3400
curl -u nxadmin:nxadmin-secret "http://localhost:5001/api/3/assets/$vpnId/vulnerabilities?size=100" | Select-String "cve-2024-3400"
```
Si trouvé : ✅ pinning fonctionne.

Répéter pour :
- `srv-mail.business.org` + CVE-2021-26855
- `srv-ci.business.org` + CVE-2021-44228
- `srv-portail.business.org` + CVE-2016-3189

**Cyberwatch** — même logique sur le port 5002 :
```powershell
cd C:\Users\jcourtemanch\Documents\dev\demo\sims\cyberwatch-simul
python -m flask --app simulator.app run --port 5002
# Puis curl équivalents sur /api/v3/vulnerabilities/servers pour vérifier
# esxi-01 + CVE-2020-1472 et alice + CVE-2022-30190
```

## Étape 2b.6 — Deploy Cloud Run

Une fois validé en local, déployer :

```powershell
cd C:\Users\jcourtemanch\Documents\dev\demo\sims\Rapid7InsightVM-simul
$env:NEXPOSE_USER = "businesscorp-demo"
$env:NEXPOSE_PASS = "R@pid7-D3mo-BusinessCorp-2026"
bash deploy-cloudrun.sh

cd ..\cyberwatch-simul
$env:CW_ACCESS_KEY = "cw-businesscorp-demo-access"
$env:CW_SECRET_KEY = "cw-BusinessCorp-Demo-S3cret-2026"
bash deploy-cloudrun.sh
```

Sanity check :
```powershell
$rapid7Url = "<url_cloud_run_rapid7>"
$cwUrl = "<url_cloud_run_cyberwatch>"

# Vérifier que srv-portail apparaît bien via l'URL Cloud Run
curl -u "businesscorp-demo:R@pid7-D3mo-BusinessCorp-2026" "$rapid7Url/api/3/assets?size=30" | ConvertFrom-Json | Select-Object -ExpandProperty resources | Where-Object hostName -eq "srv-portail.business.org"
```

## Étape 2b.7 — Itérations futures

Pour changer un hero case ou ajouter un asset :

1. Éditer `business-corp-config.yaml`
2. `python config\sync-config-to-sims.py`
3. `git add . && git commit -m "config: update hero pinning"` dans chaque fork (optionnel)
4. `bash deploy-cloudrun.sh` dans chaque fork
5. Attendre 5-15 min ingestion XSIAM
6. Faire "Fetch Now" sur les 2 intégrations XSIAM pour accélérer

**Aucun besoin de re-patcher `generators/assets.py`** — le patch initial reste valide, seul le `business_corp_overrides.py` change.

## Étape 2b.8 — Configuration XSIAM

Une fois les 2 URLs Cloud Run stables, poursuivre avec le runbook `03-configure-xsiam-rapid7.md` (l'intégration XSIAM ne voit AUCUNE différence entre sim vanilla et sim patché — elle consomme juste plus d'assets).

## Troubleshooting

| Symptôme | Cause probable | Fix |
|----------|----------------|-----|
| `sync-config-to-sims.py` échoue "fork path not found" | `sync_targets` dans le YAML pointe sur un dossier inexistant | Ajuster le YAML |
| Extra assets absents des réponses du sim | Patch bloc 1 non appliqué | Re-vérifier `generators/assets.py` du fork |
| Pinning CVE ne fonctionne pas | Patch bloc 3 ou 4 non appliqué | Ajouter les 2 lignes `_apply_pinned_cves(...)` |
| CVE pinnée absente du catalogue | La CVE n'est pas dans `VULN_CATALOG_SEED` / `CVE_CATALOG_SEED` | Choisir une autre CVE (voir `config/catalogs-inventory.md`) |
| Cloud Run redéploie mais retour identique | Cache Cloud Build ou révision non mise à jour | Forcer via `gcloud run services update-traffic <service> --to-latest --region=europe-west1` |

## Suivant

→ [`03-configure-xsiam-rapid7.md`](03-configure-xsiam-rapid7.md)
