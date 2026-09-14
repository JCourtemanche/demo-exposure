"""
sync-config-to-sims.py — génère et copie business_corp_overrides.py
dans chaque fork sim, à partir de business-corp-config.yaml.

Usage :
    pip install pyyaml
    python config/sync-config-to-sims.py

Portable : les chemins des forks sont résolus via l'env var SIMS_DIR
(défaut : ../sims relatif à la racine du repo).
Noms de dossiers hardcodés (convention) : Rapid7InsightVM-simul,
cyberwatch-simul.

Le script est idempotent — peut être re-lancé sans risque.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from textwrap import dedent

try:
    import yaml
except ImportError:
    print("❌ Module 'pyyaml' manquant. Installer avec: pip install pyyaml")
    sys.exit(1)


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
CONFIG_FILE = HERE / "business-corp-config.yaml"

# Convention hardcoded : les 2 sims sont toujours dans ces dossiers
SIM_DIRNAMES = {
    "rapid7":     "Rapid7InsightVM-simul",
    "cyberwatch": "cyberwatch-simul",
}
OVERRIDES_DEST_REL = Path("simulator/generators/business_corp_overrides.py")


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")
    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


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


def build_overrides_py(config: dict, target_sim: str) -> str:
    """Generate the Python content for business_corp_overrides.py.

    Adapts the EXTRA_ASSETS tuple shape to each sim:
      - Rapid7    : (hostname, ip, os_name, site_id)
      - Cyberwatch: (hostname, ip, os_name, category, description, [group_ids])
    """
    extras = [a for a in config.get("extra_assets", []) if target_sim in a.get("inject_in", [])]
    pinning = [p for p in config.get("hero_pinning", []) if p.get("source") in (target_sim, "both")]

    lines: list[str] = []
    lines.append('"""')
    lines.append("business_corp_overrides — GENERATED FILE, DO NOT EDIT MANUALLY.")
    lines.append("")
    lines.append("Source: exposure-management/config/business-corp-config.yaml")
    lines.append("Regenerate: python exposure-management/config/sync-config-to-sims.py")
    lines.append(f"Target sim: {target_sim}")
    lines.append('"""')
    lines.append("")

    # --- EXTRA_ASSETS ---
    lines.append("# Extra assets to append to EXTRA_SERVER_SEED in generators/assets.py")
    lines.append("EXTRA_ASSETS = [")
    if target_sim == "rapid7":
        for a in extras:
            lines.append(
                f"    ({a['hostname']!r}, {a['ip']!r}, {a['os']!r}, {a['site_id']}),"
                f"  # {a.get('zone_hint','')}/{a.get('owner_hint','')}"
            )
    elif target_sim == "cyberwatch":
        # Cyberwatch tuple format (5 éléments) : hostname, os_key, category, description, group_ids
        # IP calculée dans _extra_assets, PAS dans le tuple
        for a in extras:
            groups = a.get("cw_groups", [])
            lines.append(
                f"    ({a['hostname']!r}, "
                f"{a.get('cw_os_key', 'ubuntu_2204_64')!r}, "
                f"{a.get('cw_category', 'server')!r}, "
                f"{a.get('cw_description', '')!r}, "
                f"{groups!r}),"
                f"  # {a.get('zone_hint','')}/{a.get('owner_hint','')}"
            )
    lines.append("]")
    lines.append("")

    # --- PINNED_CVES ---
    lines.append("# Guaranteed (asset, CVE) pairs — appended after r.sample() in builders")
    lines.append("# Key: hostname (lower)   Value: list of CVE codes")
    lines.append("PINNED_CVES = {")
    merged: dict[str, list[str]] = {}
    for p in pinning:
        host = p["asset"].lower()
        merged.setdefault(host, []).extend(p["cves"])
    for host, cves in merged.items():
        lines.append(f"    {host!r}: {cves!r},")
    lines.append("}")
    lines.append("")

    return "\n".join(lines) + "\n"


def sync_to_fork(sim_key: str, overrides_content: str) -> bool:
    fork_path = resolve_fork_path(sim_key)
    dest = fork_path / OVERRIDES_DEST_REL

    if not fork_path.exists():
        print(f"⚠️  {sim_key}: fork path not found — {fork_path}")
        print(f"    → Set SIMS_DIR env var or ensure it exists (clone the sim first)")
        return False

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(overrides_content, encoding="utf-8")
    print(f"✅ {sim_key}: wrote {dest}")
    return True


def main() -> int:
    config = load_config()

    print(f"📁 Sims dir  : {resolve_sims_dir()}")
    print(f"📄 Config    : {CONFIG_FILE}")
    print()

    all_ok = True
    for sim_key in SIM_DIRNAMES:
        overrides = build_overrides_py(config, sim_key)
        if not sync_to_fork(sim_key, overrides):
            all_ok = False

    print()
    print(dedent("""\
        --- Next steps ---
        1. Ensure the one-time patch is applied to generators/assets.py in each fork
           (via `python scripts/apply-patches.py` OR manually per config/patches/*-patch.md).
        2. Rebuild & redeploy Cloud Run in each fork:
              cd <fork>
              bash deploy-cloudrun.sh
        3. Wait 5-15 min for XSIAM to re-ingest.
        4. Validate hero cases: runbook/08-validation-checklist.md § H
        """))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
