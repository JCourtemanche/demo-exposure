"""
sync-config-to-sims.py — génère et copie business_corp_overrides.py
dans chaque fork sim, à partir de business-corp-config.yaml.

Usage :
    pip install pyyaml
    python config/sync-config-to-sims.py

Après exécution :
    1. Vérifier que le fichier <fork>/simulator/generators/business_corp_overrides.py
       existe dans chaque fork
    2. Vérifier que le patch documenté (config/patches/*-patch.md) a été appliqué
       une fois dans chaque fork sur generators/assets.py
    3. Rebuild et redeploy Cloud Run : bash deploy-cloudrun.sh dans chaque fork

Le script est idempotent — peut être re-lancé sans risque.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path
from textwrap import dedent

try:
    import yaml
except ImportError:
    print("❌ Module 'pyyaml' manquant. Installer avec: pip install pyyaml")
    sys.exit(1)


HERE = Path(__file__).resolve().parent
CONFIG_FILE = HERE / "business-corp-config.yaml"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")
    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_overrides_py(config: dict, target_sim: str) -> str:
    """Generate the Python content for business_corp_overrides.py.

    Adapts the EXTRA_ASSETS tuple shape to each sim:
      - Rapid7   : (hostname, ip, os_name, site_id)
      - Cyberwatch : (hostname, ip, os_name, category, description, [group_ids])
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
        for a in extras:
            groups = a.get("cw_groups", [])
            lines.append(
                f"    ({a['hostname']!r}, {a['ip']!r}, {a['os']!r}, "
                f"{a.get('cw_category', 'server')!r}, "
                f"{a.get('cw_description', '')!r}, {groups!r}),"
                f"  # {a.get('zone_hint','')}/{a.get('owner_hint','')}"
            )
    lines.append("]")
    lines.append("")

    # --- PINNED_CVES ---
    lines.append("# Guaranteed (asset, CVE) pairs — appended after r.sample() in builders")
    lines.append("# Key: hostname (lower)   Value: list of CVE codes")
    lines.append("PINNED_CVES = {")
    # Merge multiple pins to the same asset if any
    merged: dict[str, list[str]] = {}
    for p in pinning:
        host = p["asset"].lower()
        merged.setdefault(host, []).extend(p["cves"])
    for host, cves in merged.items():
        lines.append(f"    {host!r}: {cves!r},")
    lines.append("}")
    lines.append("")

    return "\n".join(lines) + "\n"


def sync_to_fork(sim_key: str, target_config: dict, overrides_content: str) -> None:
    fork_path = Path(target_config["fork_path"])
    dest_rel = target_config["overrides_dest"]
    dest = fork_path / dest_rel

    if not fork_path.exists():
        print(f"⚠️  {sim_key}: fork path not found — {fork_path}")
        print(f"    → git clone the sim first, then adjust sync_targets in the YAML")
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(overrides_content, encoding="utf-8")
    print(f"✅ {sim_key}: wrote {dest}")


def main() -> int:
    config = load_config()

    targets = config.get("sync_targets", {})
    if not targets:
        print("❌ Config missing 'sync_targets' section")
        return 1

    for sim_key, target_config in targets.items():
        overrides = build_overrides_py(config, sim_key)
        sync_to_fork(sim_key, target_config, overrides)

    print()
    print(dedent("""\
        --- Next steps ---
        1. Verify each fork has business_corp_overrides.py in simulator/generators/
        2. Ensure the one-time patch is applied to generators/assets.py in each fork
           (see config/patches/rapid7-patch.md and config/patches/cyberwatch-patch.md).
           This patch is idempotent — safe to re-check.
        3. Rebuild & redeploy Cloud Run in each fork:
              cd <fork>
              bash deploy-cloudrun.sh
        4. Wait 5-15 min for XSIAM to re-ingest.
        5. Validate hero cases: runbook/08-validation-checklist.md § H
        """))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
