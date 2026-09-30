"""
apply-patches.py — Applique automatiquement les patches Business Corp
aux 2 forks de simulateurs (Rapid7 + Cyberwatch).

Idempotent : peut être relancé sans risque, ne re-patch pas si déjà patché.

Usage:
    pip install pyyaml
    python scripts/apply-patches.py

Alternative manuelle : voir config/patches/{rapid7,cyberwatch}-patch.md
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("❌ Module 'pyyaml' manquant. pip install pyyaml")
    sys.exit(1)


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
CONFIG_FILE = REPO_ROOT / "config" / "business-corp-config.yaml"

# Convention hardcoded : les 2 sims sont toujours dans ces dossiers
SIM_DIRNAMES = {
    "rapid7":     "Rapid7InsightVM-simul",
    "cyberwatch": "cyberwatch-simul",
}


def resolve_sims_dir() -> Path:
    """Portable resolution of the sims parent directory.

    Priority :
      1. Env var SIMS_DIR
      2. ../sims relative to REPO_ROOT (default)
    """
    env = os.environ.get("SIMS_DIR")
    return Path(env) if env else (REPO_ROOT.parent / "sims")


def resolve_fork_path(sim_key: str) -> Path:
    return resolve_sims_dir() / SIM_DIRNAMES[sim_key]

MARKER_BEGIN = "# --- Business Corp overrides (patched by apply-patches.py) ---"
MARKER_END = "# --- end Business Corp overrides ---"


# ------------------------------------------------------------
# Blocs à injecter (formatés pour Python)
# ------------------------------------------------------------

IMPORT_BLOCK = f"""
{MARKER_BEGIN}
try:
    from .business_corp_overrides import (
        EXTRA_ASSETS as _BC_EXTRA_ASSETS,
        PINNED_CVES as _BC_PINNED_CVES,
        PUBLIC_IPS as _BC_PUBLIC_IPS,
    )
    EXTRA_SERVER_SEED = EXTRA_SERVER_SEED + _BC_EXTRA_ASSETS
except ImportError:
    _BC_PINNED_CVES = {{}}
    _BC_PUBLIC_IPS = {{}}
{MARKER_END}
"""

HELPER_RAPID7 = '''

def _apply_pinned_cves(sampled, vulns_pool, hostname):
    """Business Corp override: guarantee pinned CVEs on this hostname."""
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

'''

HELPER_CYBERWATCH = '''

def _apply_pinned_cves(sampled_cve_codes, cve_catalog, hostname):
    """Business Corp override: guarantee pinned CVE codes on this hostname."""
    pinned = _BC_PINNED_CVES.get(hostname.lower(), [])
    if not pinned:
        return sampled_cve_codes
    available = {c.get("cve_code") for c in cve_catalog}
    for cve in pinned:
        if cve in available and cve not in sampled_cve_codes:
            sampled_cve_codes.append(cve)
    return sampled_cve_codes

'''

# --- Patch pour Rapid7 routes/reports.py — routes manquantes utilisées par XSIAM ---
# Le sim upstream implémente POST /reports mais pas GET/DELETE — d'où 404 sur le
# poll du connecteur XSIAM Rapid7 InsightVM. Bloc à appender à reports.py.
# Note : reports_bp a déjà url_prefix='/api/3', donc les routes utilisent /reports (pas /api/3/reports).
REPORTS_MARKER = "# BC-patch: missing report routes"

REPORTS_ROUTES_BLOCK = '''


# BC-patch: missing report routes — pour XSIAM Rapid7 InsightVM connector
# Le sim upstream implémente POST /reports mais pas GET (list + single) ni DELETE.
# Le connecteur XSIAM poll GET /reports/<id> après POST → sans ça, 404 systématique.
@reports_bp.route("/reports", methods=["GET"])
@require_basic_auth
def list_reports_bc_patch():
    resources = list(_REPORTS.values())
    return jsonify({
        "resources": resources,
        "page": {"number": 0, "size": len(resources), "totalResources": len(resources), "totalPages": 1},
        "links": [{"href": "/api/3/reports", "rel": "self"}],
    })


@reports_bp.route("/reports/<int:report_id>", methods=["GET"])
@require_basic_auth
def get_report_bc_patch(report_id):
    report = _REPORTS.get(report_id)
    if report is None:
        # Report synthétique — évite le 404 sur le poll XSIAM après un POST (multi-worker ou reboot container)
        return jsonify({
            "id": report_id,
            "name": f"report-{report_id}",
            "format": "json",
            "template": "vulnerability-details",
            "status": "complete",
            "history": [{"id": 5000 + report_id, "status": "complete", "version": 1}],
            "links": [
                {"href": f"/api/3/reports/{report_id}", "rel": "self"},
                {"href": f"/api/3/reports/{report_id}/history/{5000 + report_id}", "rel": "history"},
            ],
        })
    return jsonify(report)


@reports_bp.route("/reports/<int:report_id>", methods=["DELETE"])
@require_basic_auth
def delete_report_bc_patch(report_id):
    _REPORTS.pop(report_id, None)
    return "", 204


@reports_bp.route("/reports/<int:report_id>/history/<int:instance_id>", methods=["DELETE"])
@require_basic_auth
def delete_report_history_bc_patch(report_id, instance_id):
    report = _REPORTS.get(report_id)
    if report is not None:
        report["history"] = [h for h in report.get("history", []) if h.get("id") != instance_id]
    return "", 204
'''


# ------------------------------------------------------------
# Utilitaires
# ------------------------------------------------------------

def is_patched(source: str) -> bool:
    return MARKER_BEGIN in source


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")
    return yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))


def _insert_import_block(src: str) -> tuple[str, bool]:
    """Insert IMPORT_BLOCK just after the closing ']' of EXTRA_SERVER_SEED."""
    pattern = re.compile(r"(EXTRA_SERVER_SEED\s*=\s*\[.*?\n\])", re.DOTALL)
    m = pattern.search(src)
    if not m:
        return src, False
    insert_pos = m.end()
    return src[:insert_pos] + "\n" + IMPORT_BLOCK + src[insert_pos:], True


# ------------------------------------------------------------
# Patcheurs par sim
# ------------------------------------------------------------

def patch_rapid7(assets_py: Path) -> bool:
    src = assets_py.read_text(encoding="utf-8")
    if is_patched(src):
        print(f"  ⏭️  {assets_py.name} déjà patché — skip")
        return True

    # 1. Import block
    src, ok = _insert_import_block(src)
    if not ok:
        print(f"  ❌ Rapid7: EXTRA_SERVER_SEED introuvable dans {assets_py}")
        return False

    # 2. Helper before def _persona_assets
    if "def _persona_assets" not in src:
        print(f"  ❌ Rapid7: def _persona_assets introuvable")
        return False
    src = src.replace("def _persona_assets", HELPER_RAPID7 + "\ndef _persona_assets", 1)

    # 3. Wrap r.sample dans _persona_assets (k=r.randint(4, 12))
    pattern_persona = re.compile(
        r"(vulns\s*=\s*r\.sample\(vulns_pool,\s*k=r\.randint\(4,\s*12\)\))"
    )
    if not pattern_persona.search(src):
        print(f"  ⚠️  Rapid7: pattern 'r.sample(vulns_pool, k=r.randint(4, 12))' introuvable")
        print(f"     → Le pinning ne sera pas appliqué sur personas. À patcher manuellement.")
    else:
        src = pattern_persona.sub(
            r"\1\n        vulns = _apply_pinned_cves(vulns, vulns_pool, persona.get('hostname', ''))",
            src,
            count=1,
        )

    # 4. Wrap r.sample dans _extra_assets (k=r.randint(8, 20))
    pattern_extra = re.compile(
        r"(vulns\s*=\s*r\.sample\(vulns_pool,\s*k=r\.randint\(8,\s*20\)\))"
    )
    if not pattern_extra.search(src):
        print(f"  ⚠️  Rapid7: pattern 'r.sample(vulns_pool, k=r.randint(8, 20))' introuvable")
        print(f"     → Le pinning ne sera pas appliqué sur extra assets. À patcher manuellement.")
    else:
        src = pattern_extra.sub(
            r"\1\n        vulns = _apply_pinned_cves(vulns, vulns_pool, hostname)",
            src,
            count=1,
        )

    # 5. Neutraliser le slicing EXTRA_SERVER_SEED[:count] qui tronque nos ajouts
    # Sinon count=12 (default de build_assets_catalog) ignore nos 4 extras Business Corp
    pattern_slice = re.compile(r"seed\s*=\s*EXTRA_SERVER_SEED\[:count\]")
    if pattern_slice.search(src):
        src = pattern_slice.sub(
            "seed = EXTRA_SERVER_SEED  # patched: include all extras (natives + BC custom)",
            src,
            count=1,
        )
    else:
        print(f"  ⚠️  Rapid7: 'seed = EXTRA_SERVER_SEED[:count]' introuvable")
        print(f"     → Les extra_assets custom peuvent être ignorés si count reste = 12.")

    # 6. REMPLACER l'IP privée par l'IP publique pour les assets exposés (v1.3).
    # Le pack Rapid7 XSIAM ingère via Data Warehouse endpoint qui remonte UNE
    # seule IP par asset (champ mono-valué). On doit donc remplacer l'IP
    # dans le champ principal `ip` ET dans addresses[0] pour que Cortex la voie.
    # Le hook est IDEMPOTENT : ne remplace que si l'IP privée est encore là.
    marker_public_ip = "# BC-patch: REPLACE private IP with public IP for exposed assets"
    if marker_public_ip not in src:
        enrichment = (
            "\n    " + marker_public_ip + "\n"
            "    for _a in assets:\n"
            "        _pub = _BC_PUBLIC_IPS.get((_a.get('hostName') or '').lower())\n"
            "        if _pub and _a.get('ip') != _pub:\n"
            "            _a['ip'] = _pub\n"
            "            _addrs = _a.get('addresses') or []\n"
            "            if _addrs:\n"
            "                _addrs[0] = {**_addrs[0], 'ip': _pub}\n"
            "            else:\n"
            "                _addrs = [{'ip': _pub}]\n"
            "            _a['addresses'] = _addrs\n"
            "    return assets"
        )
        # Remplacer chaque `    return assets` (indentation à 4 espaces) par le bloc
        pattern_return = re.compile(r"\n    return assets(?=\s*(?:\n|$))")
        matches = pattern_return.findall(src)
        if matches:
            src = pattern_return.sub(enrichment, src)
            print(f"  ✓ Rapid7: {len(matches)} public-IP remplacement(s) inséré(s) — hook idempotent")
        else:
            print(f"  ⚠️  Rapid7: '    return assets' introuvable — IP publiques non injectées")

    assets_py.write_text(src, encoding="utf-8")
    print(f"  ✅ Rapid7: {assets_py.name} patché")
    return True


def patch_rapid7_reports(reports_py: Path) -> bool:
    """Append missing GET/DELETE report routes to routes/reports.py.

    Idempotent — checks for BC marker before appending.
    """
    src = reports_py.read_text(encoding="utf-8")
    if REPORTS_MARKER in src:
        print(f"  ⏭️  {reports_py.name} déjà patché (report routes) — skip")
        return True

    src = src.rstrip() + "\n" + REPORTS_ROUTES_BLOCK
    reports_py.write_text(src, encoding="utf-8")
    print(f"  ✅ Rapid7: {reports_py.name} patché (4 routes ajoutées : list, get, 2×delete)")
    return True


# --- Patch pour Rapid7 routes/assets.py — enrichir GET /assets/<id>/tags ---
# Le sim upstream retourne 2 tags codés en dur (Business Corp:custom, site-N:location).
# On y ajoute les tags Business Corp par asset pour que Cortex les ingère nativement
# (auto-tagging via xdm.asset.tags — évite le bulk-tagging manuel côté XSIAM).
ASSETS_ROUTES_MARKER = "# BC-patch: append Business Corp custom tags"

ASSETS_TAGS_INJECTION = '''    # BC-patch: append Business Corp custom tags
    try:
        # Import absolu — le fichier est simulator/generators/business_corp_overrides.py
        # et routes/ n'est pas dans le même package que generators/
        from generators.business_corp_overrides import ASSET_TAGS as _BC_ASSET_TAGS
        _bc_host = (ASSETS_BY_ID[asset_id].get("hostName") or "").lower()
        _bc_next = 100
        for _bc_name, _bc_type in _BC_ASSET_TAGS.get(_bc_host, []):
            tags.append({
                "id": _bc_next,
                "name": _bc_name,
                "type": _bc_type,
                "links": [{"href": f"/api/3/tags/{_bc_next}", "rel": "self"}],
            })
            _bc_next += 1
    except ImportError:
        pass
'''


def patch_rapid7_assets_routes(assets_routes_py: Path) -> bool:
    """Enrich GET /api/3/assets/<id>/tags with Business Corp tags."""
    src = assets_routes_py.read_text(encoding="utf-8")
    if ASSETS_ROUTES_MARKER in src:
        print(f"  ⏭️  {assets_routes_py.name} déjà patché (asset tags) — skip")
        return True

    # Cherche la ligne `return jsonify(page_envelope(tags, 0, 500, f'/api/3/assets/{asset_id}/tags'))`
    pattern = re.compile(
        r"(\n)(    return jsonify\(page_envelope\(tags,\s*0,\s*500,\s*f'/api/3/assets/\{asset_id\}/tags'\)\),\s*200)"
    )
    if not pattern.search(src):
        print(f"  ⚠️  Rapid7 routes/assets.py: pattern get_asset_tags return introuvable")
        print(f"     → Enrichissement tags custom non appliqué. Le bulk-tagging manuel reste possible.")
        return True  # Non bloquant

    src = pattern.sub(r"\1" + ASSETS_TAGS_INJECTION + r"\2", src, count=1)
    assets_routes_py.write_text(src, encoding="utf-8")
    print(f"  ✅ Rapid7: {assets_routes_py.name} patché (tags Business Corp injectés)")
    return True


# --- Patch pour Rapid7 generators/report_csv.py — CRUCIAL pour ingestion XSIAM ---
# Le pack Rapid7 XSIAM lit un CSV Data Warehouse Report (pas /api/3/assets/<id>/tags).
# Ce CSV est généré par _asset_row() qui HARDCODE 2 tags. Sans patch ici, les tags
# Business Corp injectés dans routes/assets.py sont invisibles côté XSIAM.
REPORT_CSV_MARKER = "# BC-patch: append Business Corp custom tags to CSV report"

REPORT_CSV_INJECTION = '''    # BC-patch: append Business Corp custom tags to CSV report
    try:
        from .business_corp_overrides import ASSET_TAGS as _BC_ASSET_TAGS
        _bc_host = (asset.get('hostName') or '').lower()
        for _bc_name, _bc_type in _BC_ASSET_TAGS.get(_bc_host, []):
            tags.append({'Name': _bc_name, 'Type': _bc_type})
    except ImportError:
        pass
'''


def patch_rapid7_report_csv(report_csv_py: Path) -> bool:
    """Enrich _asset_row() to include Business Corp tags in the SQL Data Warehouse CSV.

    Idempotent — checks for BC marker before injecting.
    """
    src = report_csv_py.read_text(encoding="utf-8")
    if REPORT_CSV_MARKER in src:
        print(f"  ⏭️  {report_csv_py.name} déjà patché (CSV tags) — skip")
        return True

    # Cherche le bloc `tags = [...]` avec les 2 tags hardcodés dans _asset_row
    # Le pattern matche jusqu'à ']' de fermeture (avec la virgule et les 2 tags dedans)
    pattern = re.compile(
        r"(\n    tags = \[\n"
        r"        \{'Name': 'Business Corp', 'Type': 'custom'\},\n"
        r"        \{'Name': f'site-\{asset\[\"sites\"\]\[0\]\}', 'Type': 'location'\},\n"
        r"    \])"
    )
    if not pattern.search(src):
        print(f"  ⚠️  Rapid7 generators/report_csv.py: pattern hardcoded tags introuvable")
        print(f"     → CSV tags Business Corp non injectés → XSIAM ne verra pas les tags custom")
        return False  # Bloquant : sans ça, la démo tags ne fonctionne pas

    src = pattern.sub(r"\1\n" + REPORT_CSV_INJECTION, src, count=1)
    report_csv_py.write_text(src, encoding="utf-8")
    print(f"  ✅ Rapid7: {report_csv_py.name} patché (tags custom ajoutés au CSV DW)")
    return True


def patch_cyberwatch(assets_py: Path) -> bool:
    src = assets_py.read_text(encoding="utf-8")
    if is_patched(src):
        print(f"  ⏭️  {assets_py.name} déjà patché — skip")
        return True

    # 1. Import block
    src, ok = _insert_import_block(src)
    if not ok:
        print(f"  ❌ Cyberwatch: EXTRA_SERVER_SEED introuvable dans {assets_py}")
        return False

    # 2. Helper before def _persona_assets
    if "def _persona_assets" not in src:
        print(f"  ❌ Cyberwatch: def _persona_assets introuvable")
        return False
    src = src.replace("def _persona_assets", HELPER_CYBERWATCH + "\ndef _persona_assets", 1)

    # 3. & 4. Wrap l'assignment des cve_codes dans _persona_assets et _extra_assets
    # Structure Cyberwatch : chercher les patterns qui affectent une liste de cve_codes
    # Pattern générique : cve_codes = r.sample(..., k=...) ou similaire
    patterns_wrap = [
        # Cas persona : hostname disponible via persona.get
        (
            re.compile(r"(cve_codes\s*=\s*r\.sample\([^)]+\))(\s*\n)"),
            r"\1\2        cve_codes = _apply_pinned_cves(list(cve_codes), cve_catalog, persona.get('hostname', ''))\n",
            "persona-like",
        ),
    ]

    wrapped_count = 0
    for pattern, replacement, label in patterns_wrap:
        matches = list(pattern.finditer(src))
        if matches:
            # Remplacer chaque match — mais on doit distinguer persona vs extra
            # Pour simplicité on wrap toutes les occurrences, en utilisant hostname si dispo
            # Note : ce heuristique peut nécessiter ajustement selon la structure exacte
            src, n = pattern.subn(replacement, src)
            wrapped_count += n
            print(f"  ✓ Cyberwatch: {n} wrap(s) '{label}' appliqué(s)")

    if wrapped_count == 0:
        print(f"  ⚠️  Cyberwatch: aucun pattern cve_codes reconnu automatiquement")
        print(f"     → Vérifiez manuellement generators/assets.py :")
        print(f"       - Chercher les assignments 'cve_codes = r.sample(...)'")
        print(f"       - Ajouter APRÈS chaque assignment :")
        print(f"         cve_codes = _apply_pinned_cves(list(cve_codes), cve_catalog, <hostname_var>)")
        print(f"     → Voir config/patches/cyberwatch-patch.md pour détail")

    # Neutraliser le slicing qui tronque les extras (idem Rapid7)
    pattern_slice = re.compile(r"seed\s*=\s*EXTRA_SERVER_SEED\[:count\]")
    if pattern_slice.search(src):
        src = pattern_slice.sub(
            "seed = EXTRA_SERVER_SEED  # patched: include all extras (natives + BC custom)",
            src,
            count=1,
        )
    else:
        print(f"  ⚠️  Cyberwatch: 'seed = EXTRA_SERVER_SEED[:count]' introuvable")
        print(f"     → Les extra_assets custom peuvent être ignorés si count reste = 12.")

    assets_py.write_text(src, encoding="utf-8")
    print(f"  ✅ Cyberwatch: {assets_py.name} patché (structure de base)")
    return True


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main() -> int:
    print("🔨 Application des patches Business Corp aux sim forks")
    print(f"📁 Sims dir : {resolve_sims_dir()}")
    print("")

    all_ok = True
    for sim_key in SIM_DIRNAMES:
        fork_path = resolve_fork_path(sim_key)
        assets_py = fork_path / "simulator" / "generators" / "assets.py"

        print(f"→ {sim_key} @ {fork_path}")

        if not fork_path.exists():
            print(f"  ⚠️  Fork path introuvable — cloner d'abord le sim (voir scripts/deploy-full.sh)")
            all_ok = False
            continue

        if not assets_py.exists():
            print(f"  ❌ {assets_py} introuvable")
            all_ok = False
            continue

        if sim_key == "rapid7":
            success = patch_rapid7(assets_py)
            # Patch supplémentaire sur routes/reports.py (routes manquantes pour XSIAM connector)
            reports_py = fork_path / "simulator" / "routes" / "reports.py"
            if reports_py.exists():
                if not patch_rapid7_reports(reports_py):
                    success = False
            else:
                print(f"  ⚠️  Rapid7: {reports_py} introuvable — skip patch reports")
            # Patch supplémentaire sur routes/assets.py (auto-tagging via Cortex ingest)
            assets_routes_py = fork_path / "simulator" / "routes" / "assets.py"
            if assets_routes_py.exists():
                if not patch_rapid7_assets_routes(assets_routes_py):
                    success = False
            else:
                print(f"  ⚠️  Rapid7: {assets_routes_py} introuvable — skip patch assets routes")
            # Patch CRUCIAL sur generators/report_csv.py (le pack XSIAM lit le CSV, pas /tags)
            report_csv_py = fork_path / "simulator" / "generators" / "report_csv.py"
            if report_csv_py.exists():
                if not patch_rapid7_report_csv(report_csv_py):
                    success = False
            else:
                print(f"  ⚠️  Rapid7: {report_csv_py} introuvable — skip patch report_csv")
        elif sim_key == "cyberwatch":
            success = patch_cyberwatch(assets_py)
        else:
            print(f"  ⚠️  Sim inconnu: {sim_key}")
            continue

        if not success:
            all_ok = False

    print("")
    if all_ok:
        print("✅ Patches appliqués. Prochaine étape :")
        print("   python config/sync-config-to-sims.py")
        return 0
    else:
        print("⚠️  Certains patches n'ont pas pu être appliqués automatiquement.")
        print("   → Consulter config/patches/{rapid7,cyberwatch}-patch.md pour le manuel.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
