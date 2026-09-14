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

MARKER_BEGIN = "# --- Business Corp overrides (patched by apply-patches.py) ---"
MARKER_END = "# --- end Business Corp overrides ---"


# ------------------------------------------------------------
# Blocs à injecter (formatés pour Python)
# ------------------------------------------------------------

IMPORT_BLOCK = f"""
{MARKER_BEGIN}
try:
    from .business_corp_overrides import EXTRA_ASSETS as _BC_EXTRA_ASSETS, PINNED_CVES as _BC_PINNED_CVES
    EXTRA_SERVER_SEED = EXTRA_SERVER_SEED + _BC_EXTRA_ASSETS
except ImportError:
    _BC_PINNED_CVES = {{}}
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

    assets_py.write_text(src, encoding="utf-8")
    print(f"  ✅ Rapid7: {assets_py.name} patché")
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

    assets_py.write_text(src, encoding="utf-8")
    print(f"  ✅ Cyberwatch: {assets_py.name} patché (structure de base)")
    return True


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main() -> int:
    config = load_config()
    targets = config.get("sync_targets", {})

    if not targets:
        print("❌ Config missing 'sync_targets' section")
        return 1

    print("🔨 Application des patches Business Corp aux sim forks")
    print("")

    all_ok = True
    for sim_key, target in targets.items():
        fork_path = Path(target["fork_path"])
        assets_py = fork_path / "simulator" / "generators" / "assets.py"

        print(f"→ {sim_key} @ {fork_path}")

        if not fork_path.exists():
            print(f"  ⚠️  Fork path introuvable — cloner d'abord le sim")
            all_ok = False
            continue

        if not assets_py.exists():
            print(f"  ❌ {assets_py} introuvable")
            all_ok = False
            continue

        if sim_key == "rapid7":
            success = patch_rapid7(assets_py)
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
