#!/usr/bin/env bash
# ============================================================
# deploy-vanilla-parallel.sh — Deploy VANILLA sims en parallèle
# ============================================================
#
# But : comparer A/B dans XSIAM la data des sims VANILLA (upstream, sans
# nos patches Business Corp) vs la data des sims PATCHED (avec extras +
# hero pinning). Utile pour isoler ce qui vient de nos patches vs ce qui
# vient de l'ingestion XSIAM elle-même.
#
# Approche :
#   1. Clone les 2 repos dans ~/sims-vanilla/ (dossier séparé de ~/sims/)
#   2. N'applique PAS les patches Business Corp
#   3. Renomme les services Cloud Run avec suffix -vanilla via sed sur
#      deploy-cloudrun.sh + cloudbuild.yaml (pas d'écrasement des patched)
#   4. Deploy les 2 vanilla
#   5. Affiche les 4 URLs (2 vanilla + 2 patched) pour la config XSIAM
#
# Idempotent : ré-exécutable — git checkout restaure les fichiers avant
# le nouveau sed, donc pas de "vanilla-vanilla" cumulé.
#
# Usage:
#   bash scripts/deploy-vanilla-parallel.sh
#
# Variables optionnelles :
#   SIMS_VANILLA_DIR  — Où cloner (défaut : ../sims-vanilla)
#   REGION            — Région Cloud Run (défaut : europe-west1)
# ============================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SIMS_VANILLA_DIR="${SIMS_VANILLA_DIR:-$(cd "$REPO_ROOT/.." && pwd)/sims-vanilla}"
REGION="${REGION:-europe-west1}"

# Creds vanilla — on force les defaults natifs pour comparabilité
export NEXPOSE_USERNAME="${NEXPOSE_USERNAME:-nxadmin}"
export NEXPOSE_PASSWORD="${NEXPOSE_PASSWORD:-nxadmin-secret}"
export CW_ACCESS_KEY="${CW_ACCESS_KEY:-cyberwatch-access-key}"
export CW_SECRET_KEY="${CW_SECRET_KEY:-cyberwatch-secret-key}"

echo "🚀 Deploy VANILLA sims en parallèle (comparaison A/B avec les patched)"
echo "  Dossier vanilla : $SIMS_VANILLA_DIR"
echo "  Region          : $REGION"
echo ""

# --- 1. Sanity checks ---
command -v gcloud >/dev/null 2>&1 || { echo "❌ gcloud manquant"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "❌ git manquant"; exit 1; }
command -v sed >/dev/null 2>&1 || { echo "❌ sed manquant"; exit 1; }

# --- 2. Clone les 2 repos vanilla ---
mkdir -p "$SIMS_VANILLA_DIR"

for repo in "Rapid7InsightVM-simul" "cyberwatch-simul"; do
  if [ ! -d "$SIMS_VANILLA_DIR/$repo" ]; then
    echo "📥 Clone $repo (vanilla)..."
    git clone "https://github.com/JCourtemanche/$repo.git" "$SIMS_VANILLA_DIR/$repo"
  else
    echo "  ✓ $repo déjà cloné, remise à zéro..."
    cd "$SIMS_VANILLA_DIR/$repo"
    # Restore tous les fichiers modifiés (dont deploy-cloudrun.sh, cloudbuild.yaml, assets.py)
    git checkout -- . 2>/dev/null || true
    # Retirer les overrides potentiels laissés d'une exécution précédente
    rm -f simulator/generators/business_corp_overrides.py
    cd "$REPO_ROOT"
  fi
done

# --- 3. Renommer services + repos Artifact Registry ---
echo ""
echo "🔧 Renommage services Cloud Run → *-vanilla (sed sur deploy-cloudrun.sh + cloudbuild.yaml)"

rename_service() {
  local dir="$1"
  local base_name="$2"
  local vanilla_name="${base_name}-vanilla"

  cd "$dir"
  for f in deploy-cloudrun.sh cloudbuild.yaml; do
    if [ -f "$f" ]; then
      # Remplacement global — service Cloud Run + repo Artifact Registry
      sed -i "s|${base_name}|${vanilla_name}|g" "$f"
      echo "  ✓ $dir/$f patché"
    else
      echo "  ⚠️  $dir/$f introuvable — skip"
    fi
  done
  cd "$REPO_ROOT"
}

rename_service "$SIMS_VANILLA_DIR/Rapid7InsightVM-simul" "rapid7-nexpose-simulator"
rename_service "$SIMS_VANILLA_DIR/cyberwatch-simul" "cyberwatch-simulator"

# --- 4. Deploy les 2 vanilla ---
echo ""
echo "☁️  [1/2] Deploy Rapid7 vanilla..."
cd "$SIMS_VANILLA_DIR/Rapid7InsightVM-simul"
bash deploy-cloudrun.sh

echo ""
echo "☁️  [2/2] Deploy Cyberwatch vanilla..."
cd "$SIMS_VANILLA_DIR/cyberwatch-simul"
bash deploy-cloudrun.sh

cd "$REPO_ROOT"

# --- 5. Autorisation invocations publiques (idempotent) ---
echo ""
echo "🌐 Autorisation allUsers/run.invoker pour les 2 nouveaux services..."
for svc in rapid7-nexpose-simulator-vanilla cyberwatch-simulator-vanilla; do
  if gcloud run services add-iam-policy-binding "$svc" \
       --region="$REGION" --member="allUsers" --role="roles/run.invoker" \
       --quiet 2>/dev/null; then
    echo "  ✓ $svc"
  else
    echo "  ⚠️  $svc : binding refusée (org policy)"
  fi
done

# --- 6. Récap URLs (les 4 services) ---
echo ""
echo "✅ Deploy vanilla terminé."
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "URLs Cloud Run (les 4 services — 2 vanilla + 2 patched Business Corp) :"
echo "═══════════════════════════════════════════════════════════════════"
gcloud run services list --region="$REGION" \
  --format="table(metadata.name,status.url)" \
  --filter="metadata.name~rapid7-nexpose-simulator|metadata.name~cyberwatch-simulator"

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "Prochaines étapes — configuration XSIAM pour comparaison A/B :"
echo "═══════════════════════════════════════════════════════════════════"
cat <<'INSTRUCTIONS'
1. Ouvrir XSIAM → Settings → Data Sources & Integrations
2. Ajouter 2 nouvelles instances (garder les 2 BC existantes) :

   ┌─────────────────────────────────────────────────────────────────┐
   │ BC-Rapid7-Vanilla                                               │
   │   Server URL : https://rapid7-nexpose-simulator-vanilla-*.run.app│
   │   Username   : nxadmin                                          │
   │   Password   : nxadmin-secret                                   │
   │   Fetch assets and vulnerabilities : ✓                          │
   └─────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────────┐
   │ BC-Cyberwatch-Vanilla                                           │
   │   Server URL : https://cyberwatch-simulator-vanilla-*.run.app   │
   │   Access Key : cyberwatch-access-key                            │
   │   Secret Key : cyberwatch-secret-key                            │
   │   Fetch assets and vulnerabilities : ✓                          │
   └─────────────────────────────────────────────────────────────────┘

3. Attendre 5-15 min pour la première fetch des 2 nouvelles instances.

4. XQL de comparaison :

   config timeframe = 24h
   | dataset = asset_inventory
   | filter host_name contains "business.org"
   | comp count() as assets by _source_id

   # Ou par nom d'intégration selon le champ exact dans votre tenant :
   config timeframe = 24h
   | dataset = uvm_findings
   | filter host_name contains "business.org"
   | comp count() as findings by source_integration_name

5. Diffs attendus :
   - Vanilla : 18 assets Rapid7 (12 servers + 6 personas)
   - Patched : 22 assets (18 natifs + 4 extras Business Corp)
   - Vanilla : pinning aléatoire des CVE hero
   - Patched : CVE hero garanties sur assets pinnés (srv-vpn+CVE-2024-3400, etc.)

6. Une fois la comparaison faite, pour supprimer les vanilla :
   gcloud run services delete rapid7-nexpose-simulator-vanilla --region=europe-west1 --quiet
   gcloud run services delete cyberwatch-simulator-vanilla --region=europe-west1 --quiet
   # (garder ou supprimer aussi ~/sims-vanilla/ selon besoin)
INSTRUCTIONS
