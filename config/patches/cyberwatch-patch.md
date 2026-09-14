# Patch Cyberwatch simulator — business-corp overrides

Ce patch modifie `simulator/generators/assets.py` du fork Cyberwatch pour :
1. Importer `business_corp_overrides` (généré par `sync-config-to-sims.py`)
2. Étendre `EXTRA_SERVER_SEED` avec les extra assets Business Corp
3. Wrapper l'assignment CVE pour garantir la présence des CVE pinnées

**Structure Cyberwatch différente de Rapid7** — les extra_assets ont un format plus riche (category, description, groups).

## Fichier cible

`cyberwatch-simul/simulator/generators/assets.py`

## Diff à appliquer

### Bloc 1 — Import et extension de EXTRA_SERVER_SEED (haut du fichier)

**Trouver** la fin de la définition `EXTRA_SERVER_SEED = [...]` (structure Cyberwatch : chaque tuple contient `(hostname, ip, os_name, category, description, [group_ids])`).

**Ajouter juste après** :

```python
# --- Business Corp overrides (patched — see config/patches/cyberwatch-patch.md) ---
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
def _apply_pinned_cves(sampled_cve_codes, cve_catalog, hostname):
    """Ensure pinned CVE codes for this hostname are present in sampled_cve_codes.

    sampled_cve_codes is a list of CVE code STRINGS (Cyberwatch works with codes).
    cve_catalog is the list of CVE dicts (each dict has 'cve_code' key).
    """
    pinned = _BC_PINNED_CVES.get(hostname.lower(), [])
    if not pinned:
        return sampled_cve_codes
    available = {c.get("cve_code") for c in cve_catalog}
    for cve in pinned:
        if cve in available and cve not in sampled_cve_codes:
            sampled_cve_codes.append(cve)
    return sampled_cve_codes
```

### Bloc 3 — Wrap l'assignment dans _persona_assets

**Trouver** la logique qui construit la liste des CVE codes pour un persona (typiquement quelque chose comme `cve_codes = r.sample([c['cve_code'] for c in cve_catalog], k=...)`).

**Après** cette ligne, ajouter :

```python
cve_codes = _apply_pinned_cves(list(cve_codes), cve_catalog, persona.get("hostname", ""))
```

### Bloc 4 — Wrap l'assignment dans _extra_assets

**Idem** dans `_extra_assets` — après le sampling des CVE codes pour un extra asset :

```python
cve_codes = _apply_pinned_cves(list(cve_codes), cve_catalog, hostname)
```

(la variable `hostname` est déjà disponible via la déstructuration du tuple `EXTRA_SERVER_SEED`)

### Bloc 5 — Neutraliser le slicing qui tronque les extras (⚠️ critique)

Sans ce bloc, `_extra_assets` fait `seed = EXTRA_SERVER_SEED[:count]` avec `count=12` par défaut, ce qui **ignore les extras custom Business Corp**.

**Trouver** dans `_extra_assets` :
```python
seed = EXTRA_SERVER_SEED[:count]
```

**Remplacer par** :
```python
seed = EXTRA_SERVER_SEED  # patched: include all extras (natives + BC custom)
```

## Vérification manuelle post-patch

Lancer le sim en local :

```powershell
cd C:\Users\jcourtemanch\Documents\dev\demo\sims\cyberwatch-simul
python -m flask --app simulator.app run --port 5002
```

```powershell
# Vérifier la présence des extra assets
curl -u cyberwatch-access-key:cyberwatch-secret-key "http://localhost:5002/api/v3/vulnerabilities/servers?per_page=30"
# Attendu : srv-portail, srv-adfs-01, smtp-relay dans le retour

# Vérifier pinning Follina sur alice
# (adapter selon la structure exacte de retour Cyberwatch)
```

## Note sur les groupes Cyberwatch

Les `cw_groups` dans le YAML permettent de rattacher les extra assets aux groupes existants du sim (601 PROD, 602 STAGING, 603 DEV, 610 non-web tier, 611 Web tier, 620 Lyon, 621 Paris). Vérifier la liste exacte dans `simulator/generators/base.py` du fork.

## Rollback

Idem Rapid7 : retirer les 4 blocs + supprimer `business_corp_overrides.py`.
