#!/usr/bin/env bash
# ============================================================
# smoke-test.sh — Sanity checks post-déploiement Cloud Run
# ============================================================
#
# Vérifie :
#   1. Les 2 URLs Cloud Run répondent
#   2. Les extra assets custom sont présents dans les retours
#   3. Les paires (asset, CVE) pinnées sont bien injectées
#
# Usage:
#   bash scripts/smoke-test.sh
#
# Variables optionnelles :
#   REGION, NEXPOSE_USER, NEXPOSE_PASS, CW_ACCESS_KEY, CW_SECRET_KEY
# ============================================================
set -euo pipefail

REGION="${REGION:-europe-west1}"
export NEXPOSE_USER="${NEXPOSE_USER:-businesscorp-demo}"
export NEXPOSE_PASS="${NEXPOSE_PASS:-R@pid7-D3mo-BusinessCorp-2026}"
export CW_ACCESS_KEY="${CW_ACCESS_KEY:-cw-businesscorp-demo-access}"
export CW_SECRET_KEY="${CW_SECRET_KEY:-cw-BusinessCorp-Demo-S3cret-2026}"

echo "🧪 Smoke test — Business Corp sims"
echo ""

# Récupérer les URLs Cloud Run
RAPID7_URL=$(gcloud run services describe rapid7-nexpose-simulator \
  --region="$REGION" --format="value(status.url)" 2>/dev/null || echo "")
CW_URL=$(gcloud run services describe cyberwatch-simulator \
  --region="$REGION" --format="value(status.url)" 2>/dev/null || echo "")

if [ -z "$RAPID7_URL" ]; then
  echo "❌ Service Cloud Run 'rapid7-nexpose-simulator' introuvable en $REGION"
  exit 1
fi
if [ -z "$CW_URL" ]; then
  echo "❌ Service Cloud Run 'cyberwatch-simulator' introuvable en $REGION"
  exit 1
fi

echo "  Rapid7     : $RAPID7_URL"
echo "  Cyberwatch : $CW_URL"
echo ""

# --- 1. Health check ---
echo "🩺 [1/4] Health check des 2 sims..."

echo -n "  Rapid7 /api/3/assets?size=1... "
if curl -sSf -u "$NEXPOSE_USER:$NEXPOSE_PASS" "$RAPID7_URL/api/3/assets?size=1" > /dev/null; then
  echo "✓"
else
  echo "❌ Échec"
  exit 1
fi

echo -n "  Cyberwatch /api/v3/ping... "
if curl -sSf -u "$CW_ACCESS_KEY:$CW_SECRET_KEY" "$CW_URL/api/v3/ping" > /dev/null; then
  echo "✓"
else
  echo "❌ Échec"
  exit 1
fi

# --- 2. Vérifier présence des extra assets custom ---
echo ""
echo "📋 [2/4] Vérification des 4 extra assets custom..."

RAPID7_ASSETS=$(curl -sS -u "$NEXPOSE_USER:$NEXPOSE_PASS" "$RAPID7_URL/api/3/assets?size=50" || echo "")

EXTRA_ASSETS=(
  "srv-portail.business.org"
  "srv-adfs-01.business.org"
  "srv-print.business.org"
  "smtp-relay.business.org"
)

for asset in "${EXTRA_ASSETS[@]}"; do
  if echo "$RAPID7_ASSETS" | grep -q "$asset"; then
    echo "  ✓ Rapid7 contient $asset"
  else
    echo "  ⚠️  Rapid7 NE contient PAS $asset — vérifier apply-patches.py + sync-config-to-sims.py + redeploy"
  fi
done

# --- 3. Vérifier pinning des hero cases ---
echo ""
echo "🎯 [3/4] Vérification pinning hero cases..."

check_pinning_rapid7() {
  local hostname="$1"
  local cve="$2"
  local hero="$3"
  # Résoudre l'asset id
  local asset_id
  asset_id=$(echo "$RAPID7_ASSETS" | "$PYTHON_BIN_LOCAL" -c "
import json, sys
data = json.load(sys.stdin)
for a in data.get('resources', []):
    if a.get('hostName') == '$hostname':
        print(a.get('id'))
        break
" 2>/dev/null || echo "")

  if [ -z "$asset_id" ]; then
    echo "  ⚠️  Asset $hostname introuvable — pinning $hero ($cve) non testable"
    return
  fi

  local vulns
  vulns=$(curl -sS -u "$NEXPOSE_USER:$NEXPOSE_PASS" "$RAPID7_URL/api/3/assets/$asset_id/vulnerabilities?size=100" || echo "")
  # Match sur cve-YYYY-NNNN (lowercase) car les IDs Rapid7 slug lowercase
  local cve_lower
  cve_lower=$(echo "$cve" | tr '[:upper:]' '[:lower:]')
  if echo "$vulns" | grep -q "$cve_lower"; then
    echo "  ✓ $hero: $hostname porte bien $cve"
  else
    echo "  ⚠️  $hero: $hostname ne porte pas $cve — vérifier config/business-corp-config.yaml et redeploy"
  fi
}

PYTHON_BIN_LOCAL="$(command -v python3 || command -v python || true)"
if [ -n "$PYTHON_BIN_LOCAL" ]; then
  # Rapid7 pinnings
  check_pinning_rapid7 "srv-vpn.business.org"     "CVE-2024-3400"  "Hero 1 (Urgence Périmètre)"
  check_pinning_rapid7 "srv-mail.business.org"    "CVE-2021-26855" "Hero 2 (KEV ProxyLogon)"
  check_pinning_rapid7 "srv-ci.business.org"      "CVE-2021-44228" "Hero 5 (Log4Shell workload)"
  check_pinning_rapid7 "srv-portail.business.org" "CVE-2016-3189"  "Hero 6 (Nettoyage surface)"
else
  echo "  ⚠️  python indisponible — skip vérification pinning détaillée"
fi

# --- 4. Compte total d'assets ---
echo ""
echo "📊 [4/4] Statistiques d'ingestion..."

if [ -n "$PYTHON_BIN_LOCAL" ]; then
  local_count=$("$PYTHON_BIN_LOCAL" -c "
import json, sys
data = json.loads('''$RAPID7_ASSETS''')
print(len(data.get('resources', [])))
" 2>/dev/null || echo "?")
  echo "  Rapid7 : $local_count assets retournés (attendu ≥ 20)"
fi

echo ""
echo "✅ Smoke test terminé."
echo ""
echo "Si tout est ✓ : passer à runbook/03-configure-xsiam-rapid7.md"
echo "Si ⚠️ ou ❌  : consulter runbook/02b-patch-sims-with-config.md § Troubleshooting"
