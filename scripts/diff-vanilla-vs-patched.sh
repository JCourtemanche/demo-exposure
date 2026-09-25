#!/usr/bin/env bash
# ============================================================
# diff-vanilla-vs-patched.sh — Compare endpoints Cloud Run vanilla vs patched
# ============================================================
#
# But : isoler ce qui vient de nos patches Business Corp SANS passer par
# l'ingestion XSIAM. On appelle directement les 2 versions Cloud Run
# de chaque sim (vanilla + patched), on sauve les réponses JSON, et on
# affiche un tableau comparatif (status HTTP, taille, count items).
#
# Utile pour :
#   - Vérifier qu'un endpoint que XSIAM utilise n'a pas cassé côté patched
#   - Diagnostiquer les 500 / regressions structurelles
#   - Confirmer que le format API est identique entre vanilla et patched
#
# Prérequis : scripts/deploy-vanilla-parallel.sh déjà exécuté (les 4
# services Cloud Run existent : *-simulator et *-simulator-vanilla).
#
# Usage:
#   bash scripts/diff-vanilla-vs-patched.sh
#   # Puis pour diff détaillé sur un endpoint :
#   diff <(python3 -m json.tool /tmp/sims-diff/vanilla/<file>.json) \
#        <(python3 -m json.tool /tmp/sims-diff/patched/<file>.json) | less
#
# Variables optionnelles :
#   REGION            — Région Cloud Run (défaut : europe-west1)
#   OUT_DIR           — Dossier de sortie (défaut : /tmp/sims-diff)
#   NEXPOSE_USERNAME / _PASSWORD  — Creds Rapid7 (défaut natifs sim)
#   CW_ACCESS_KEY / _SECRET_KEY   — Creds Cyberwatch (défaut natifs sim)
# ============================================================
set -euo pipefail

REGION="${REGION:-europe-west1}"
OUT_DIR="${OUT_DIR:-/tmp/sims-diff}"

NEXPOSE_USERNAME="${NEXPOSE_USERNAME:-nxadmin}"
NEXPOSE_PASSWORD="${NEXPOSE_PASSWORD:-nxadmin-secret}"
CW_ACCESS_KEY="${CW_ACCESS_KEY:-cyberwatch-access-key}"
CW_SECRET_KEY="${CW_SECRET_KEY:-cyberwatch-secret-key}"

RAPID7_AUTH="${NEXPOSE_USERNAME}:${NEXPOSE_PASSWORD}"
CW_AUTH="${CW_ACCESS_KEY}:${CW_SECRET_KEY}"

echo "🔍 Diff vanilla vs patched — endpoints Cloud Run"
echo "  Region  : $REGION"
echo "  Out dir : $OUT_DIR"
echo ""

# --- 1. Récupérer les 4 URLs Cloud Run ---
get_url() {
  gcloud run services describe "$1" --region="$REGION" \
    --format='value(status.url)' 2>/dev/null || echo ""
}

R7_PATCHED=$(get_url "rapid7-nexpose-simulator")
R7_VANILLA=$(get_url "rapid7-nexpose-simulator-vanilla")
CW_PATCHED=$(get_url "cyberwatch-simulator")
CW_VANILLA=$(get_url "cyberwatch-simulator-vanilla")

if [ -z "$R7_PATCHED" ] || [ -z "$R7_VANILLA" ] || [ -z "$CW_PATCHED" ] || [ -z "$CW_VANILLA" ]; then
  echo "❌ Un ou plusieurs services Cloud Run introuvables :"
  echo "   rapid7-nexpose-simulator          : ${R7_PATCHED:-MANQUANT}"
  echo "   rapid7-nexpose-simulator-vanilla  : ${R7_VANILLA:-MANQUANT}"
  echo "   cyberwatch-simulator              : ${CW_PATCHED:-MANQUANT}"
  echo "   cyberwatch-simulator-vanilla      : ${CW_VANILLA:-MANQUANT}"
  echo ""
  echo "→ Lancer d'abord : bash scripts/deploy-vanilla-parallel.sh"
  exit 1
fi

echo "  R7 patched  : $R7_PATCHED"
echo "  R7 vanilla  : $R7_VANILLA"
echo "  CW patched  : $CW_PATCHED"
echo "  CW vanilla  : $CW_VANILLA"
echo ""

mkdir -p "$OUT_DIR/vanilla" "$OUT_DIR/patched"
# Nettoyage des anciens fichiers
find "$OUT_DIR" -name "*.json" -delete 2>/dev/null || true

# --- 2. Fonction de fetch ---
fetch() {
  local url="$1" auth="$2" endpoint="$3" out_file="$4"
  local http_code
  http_code=$(curl -sS --max-time 15 -o "$out_file" -w "%{http_code}" \
    -u "$auth" "$url$endpoint" 2>/dev/null || echo "000")
  echo "$http_code" > "${out_file}.status"
}

# --- 3. Endpoints Rapid7 à comparer ---
# Ceux typiquement utilisés par le connecteur XSIAM Rapid7 InsightVM
R7_ENDPOINTS=(
  "/api/3/assets?size=50"
  "/api/3/assets/200"
  "/api/3/assets/200/vulnerabilities?size=50"
  "/api/3/vulnerabilities?size=20"
  "/api/3/sites"
  "/api/3/scans"
  "/api/3/asset-groups"
  "/api/3/reports/templates"
  "/api/3/tags"
)

echo "▶ Rapid7 — fetch des ${#R7_ENDPOINTS[@]} endpoints (× 2 versions)"
for ep in "${R7_ENDPOINTS[@]}"; do
  slug=$(echo "$ep" | tr '/?=&' '____' | sed 's/^_*//; s/_*$//')
  fetch "$R7_VANILLA" "$RAPID7_AUTH" "$ep" "$OUT_DIR/vanilla/rapid7_${slug}.json"
  fetch "$R7_PATCHED" "$RAPID7_AUTH" "$ep" "$OUT_DIR/patched/rapid7_${slug}.json"
done

# --- 4. Endpoints Cyberwatch ---
CW_ENDPOINTS=(
  "/api/v3/ping"
  "/api/v3/vulnerabilities/servers?per_page=50"
  "/api/v3/vulnerabilities/servers/1000"
  "/api/v3/assets/servers?per_page=50"
  "/api/v3/vulnerabilities/cve_announcements?per_page=20"
  "/api/v3/security_issues?per_page=20"
  "/api/v3/compliance/assets?per_page=50"
)

echo "▶ Cyberwatch — fetch des ${#CW_ENDPOINTS[@]} endpoints (× 2 versions)"
for ep in "${CW_ENDPOINTS[@]}"; do
  slug=$(echo "$ep" | tr '/?=&' '____' | sed 's/^_*//; s/_*$//')
  fetch "$CW_VANILLA" "$CW_AUTH" "$ep" "$OUT_DIR/vanilla/cw_${slug}.json"
  fetch "$CW_PATCHED" "$CW_AUTH" "$ep" "$OUT_DIR/patched/cw_${slug}.json"
done

# --- 5. Tableau comparatif ---
echo ""
echo "═══════════════════════════════════════════════════════════════════════════════════════════"
printf "%-60s %-30s %-30s\n" "ENDPOINT" "VANILLA" "PATCHED"
echo "═══════════════════════════════════════════════════════════════════════════════════════════"

count_items() {
  local f="$1"
  # Essayer plusieurs clés courantes selon le sim
  python3 -c "
import json, sys
try:
    d = json.load(open('$f'))
    if isinstance(d, list):
        print(len(d))
    elif isinstance(d, dict):
        for key in ('resources', 'data', 'servers', 'assets', 'vulnerabilities'):
            if key in d and isinstance(d[key], list):
                print(len(d[key]))
                sys.exit(0)
        print('-')
    else:
        print('-')
except Exception:
    print('?')
" 2>/dev/null
}

VERDICT_OK=0
VERDICT_DIFF=0
VERDICT_ERR=0

for vanilla_file in "$OUT_DIR/vanilla/"*.json; do
  fname=$(basename "$vanilla_file")
  patched_file="$OUT_DIR/patched/$fname"
  [ ! -f "$patched_file" ] && continue

  v_status=$(cat "${vanilla_file}.status" 2>/dev/null || echo "?")
  p_status=$(cat "${patched_file}.status" 2>/dev/null || echo "?")
  v_size=$(wc -c < "$vanilla_file" 2>/dev/null || echo "0")
  p_size=$(wc -c < "$patched_file" 2>/dev/null || echo "0")
  v_items=$(count_items "$vanilla_file")
  p_items=$(count_items "$patched_file")

  # Icône de comparaison
  if [ "$v_status" != "$p_status" ]; then
    icon="❌"
    VERDICT_ERR=$((VERDICT_ERR + 1))
  elif [ "$v_items" = "$p_items" ] && [ "$v_size" = "$p_size" ]; then
    icon="✓"
    VERDICT_OK=$((VERDICT_OK + 1))
  else
    icon="↕"
    VERDICT_DIFF=$((VERDICT_DIFF + 1))
  fi

  printf "%s %-58s HTTP %s  size=%-6d  items=%-4s   HTTP %s  size=%-6d  items=%s\n" \
    "$icon" "${fname%.json}" "$v_status" "$v_size" "$v_items" "$p_status" "$p_size" "$p_items"
done

echo "═══════════════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Bilan : ✓ identiques : $VERDICT_OK   ↕ diffs quantitatifs : $VERDICT_DIFF   ❌ diff HTTP status : $VERDICT_ERR"
echo ""

# --- 6. Diff textuel sur les endpoints critiques ---
echo "═══════════════════════════════════════════════════════════════════════════════════════════"
echo "Diff détaillé sur les endpoints clés (les 20 premières lignes de diff — utile pour ↕ / ❌)"
echo "═══════════════════════════════════════════════════════════════════════════════════════════"

show_diff() {
  local fname="$1"
  local v="$OUT_DIR/vanilla/$fname"
  local p="$OUT_DIR/patched/$fname"
  [ ! -f "$v" ] || [ ! -f "$p" ] && return

  echo ""
  echo "─── $fname ───"
  # Tri des JSON pour normaliser l'ordre puis diff
  local vsorted=$(mktemp)
  local psorted=$(mktemp)
  python3 -c "import json,sys; print(json.dumps(json.load(open('$v')), indent=2, sort_keys=True))" 2>/dev/null > "$vsorted" || cp "$v" "$vsorted"
  python3 -c "import json,sys; print(json.dumps(json.load(open('$p')), indent=2, sort_keys=True))" 2>/dev/null > "$psorted" || cp "$p" "$psorted"
  diff "$vsorted" "$psorted" | head -20 || true
  rm -f "$vsorted" "$psorted"
}

# On affiche le diff des endpoints les plus révélateurs
show_diff "rapid7_api_3_assets_size_50.json"
show_diff "rapid7_api_3_sites.json"
show_diff "cw_api_v3_vulnerabilities_servers_per_page_50.json"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════════════════"
echo "Actions possibles :"
echo "  - Endpoint marqué ❌ (status HTTP différent) → notre patch a cassé cet endpoint côté patched"
echo "  - Endpoint marqué ↕ (items ou size différents) → notre patch a modifié la donnée (attendu si extras BC)"
echo "  - Diff détaillé sur endpoint X :"
echo "      diff <(python3 -m json.tool $OUT_DIR/vanilla/X.json) <(python3 -m json.tool $OUT_DIR/patched/X.json) | less"
echo ""
echo "  - Voir la réponse brute :"
echo "      python3 -m json.tool $OUT_DIR/patched/rapid7_api_3_assets_size_50.json | head -50"
