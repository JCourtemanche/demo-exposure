# Patch Rapid7 InsightVM simulator — business-corp overrides

Ce patch modifie `simulator/generators/assets.py` du fork Rapid7 pour :
1. Importer `business_corp_overrides` (généré par `sync-config-to-sims.py`)
2. Étendre `EXTRA_SERVER_SEED` avec les extra assets définis dans le YAML
3. Wrapper `r.sample(vulns_pool, ...)` pour garantir la présence des CVE pinnées sur les assets ciblés

**Ce patch est à appliquer UNE SEULE FOIS** dans le fork Rapid7. Après cela, tous les changements de config passent uniquement par le YAML + `sync-config-to-sims.py` + redeploy.

## Fichier cible

`Rapid7InsightVM-simul/simulator/generators/assets.py`

## Diff à appliquer

### Bloc 1 — Import et extension de EXTRA_SERVER_SEED (haut du fichier)

**Trouver** la fin de la définition `EXTRA_SERVER_SEED = [...]` (autour de la ligne 25-35 selon versions).

**Ajouter juste après** :

```python
# --- Business Corp overrides (patched — see config/patches/rapid7-patch.md) ---
try:
    from .business_corp_overrides import EXTRA_ASSETS as _BC_EXTRA_ASSETS, PINNED_CVES as _BC_PINNED_CVES
    EXTRA_SERVER_SEED = EXTRA_SERVER_SEED + _BC_EXTRA_ASSETS
except ImportError:
    _BC_PINNED_CVES = {}
# --- end Business Corp overrides ---
```

### Bloc 2 — Helper pour pinning des CVE

**Ajouter** juste avant `def _persona_assets(...)` :

```python
def _apply_pinned_cves(sampled, vulns_pool, hostname):
    """Ensure that CVEs pinned for this hostname are present in the sampled list.

    Idempotent — if pinned CVEs are already in sampled, no change.
    If a pinned CVE isn't found in vulns_pool, it's silently skipped.
    """
    pinned = _BC_PINNED_CVES.get(hostname.lower(), [])
    if not pinned:
        return sampled
    by_cve = {}
    for v in vulns_pool:
        for c in v.get("cves", []):
            by_cve[c] = v
    sampled_ids = {v.get("id") for v in sampled}
    for cve in pinned:
        vuln = by_cve.get(cve)
        if vuln and vuln.get("id") not in sampled_ids:
            sampled.append(vuln)
    return sampled
```

### Bloc 3 — Wrap le r.sample dans _persona_assets

**Trouver** la ligne (dans `_persona_assets`) qui ressemble à :

```python
vulns = r.sample(vulns_pool, k=r.randint(4, 12))
```

**La remplacer par** :

```python
vulns = r.sample(vulns_pool, k=r.randint(4, 12))
vulns = _apply_pinned_cves(vulns, vulns_pool, persona.get("hostname", ""))
```

### Bloc 4 — Wrap le r.sample dans _extra_assets

**Trouver** la ligne (dans `_extra_assets`) qui ressemble à :

```python
vulns = r.sample(vulns_pool, k=r.randint(8, 20))
```

**La remplacer par** :

```python
vulns = r.sample(vulns_pool, k=r.randint(8, 20))
vulns = _apply_pinned_cves(vulns, vulns_pool, hostname)
```

(la variable `hostname` est déjà dépakée du tuple par la boucle `for idx, (hostname, ip, os_name, site_id) in enumerate(seed):`)

## Vérification manuelle post-patch

Lancer le sim en local :

```powershell
cd C:\Users\jcourtemanch\Documents\dev\demo\sims\Rapid7InsightVM-simul
# Copier le business_corp_overrides.py généré (si pas déjà fait via sync-config-to-sims.py)
python -m flask --app simulator.app run --port 5001
```

Dans un autre terminal :

```powershell
curl -u nxadmin:nxadmin-secret "http://localhost:5001/api/3/assets?size=25"
```

Attendu : présence de `srv-portail.business.org`, `srv-adfs-01.business.org`, `srv-print.business.org`, `smtp-relay.business.org` dans le retour (en plus des 12 natifs + 6 personas).

Pour vérifier le pinning :

```powershell
# Trouver l'asset ID de srv-vpn.business.org
curl -u nxadmin:nxadmin-secret "http://localhost:5001/api/3/assets?size=100" | ConvertFrom-Json | Where-Object { $_.resources.hostName -eq "srv-vpn.business.org" }

# Puis lister ses vulns et chercher CVE-2024-3400
$id = <asset_id>
curl -u nxadmin:nxadmin-secret "http://localhost:5001/api/3/assets/$id/vulnerabilities?size=100" | Select-String "CVE-2024-3400"
```

Si CVE-2024-3400 apparaît → pinning fonctionnel.

## Rollback

Le patch est isolé : suffit de :
1. Retirer les 4 blocs ajoutés
2. Supprimer `simulator/generators/business_corp_overrides.py`

Pas de dépendance sur d'autres fichiers du sim.
