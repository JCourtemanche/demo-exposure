#!/usr/bin/env bash
# ============================================================
# deploy-full.sh — Pipeline complet de déploiement Business Corp
# ============================================================
#
# Chaîne : clone sims → patch → sync config → deploy Cloud Run.
# Idempotent : ré-exécutable à volonté.
#
# Prérequis (une seule fois) :
#   1. bash scripts/bootstrap-gcp-iam.sh   (droits IAM GCP)
#   2. Éditer config/business-corp-config.yaml
#      (extra_assets et hero_pinning)
#
# Usage:
#   bash scripts/deploy-full.sh
#
# Variables d'environnement optionnelles :
#   SIMS_DIR              — Où cloner les 2 forks (défaut : ../sims relatif au repo)
#   NEXPOSE_USER / _PASS  — Credentials Rapid7 sim (défauts démo dans le script)
#   CW_ACCESS_KEY / _SEC  — Credentials Cyberwatch sim
#   REGION                — Région Cloud Run (défaut : europe-west1)
# ============================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SIMS_DIR="${SIMS_DIR:-$(cd "$REPO_ROOT/.." && pwd)/sims}"
export SIMS_DIR   # utilisé par apply-patches.py et sync-config-to-sims.py
REGION="${REGION:-europe-west1}"

# Credentials des sims — noms de variables EXACTS attendus par chaque
# deploy-cloudrun.sh upstream (à ne PAS renommer sinon le sim retombe sur ses defaults).
#
#   Rapid7 sim (deploy-cloudrun.sh) : NEXPOSE_USERNAME / NEXPOSE_PASSWORD
#     → deviennent NEXPOSE_USERNAME / NEXPOSE_PASSWORD dans le container
#     → defaults sim : nxadmin / nxadmin-secret
#
#   Cyberwatch sim (deploy-cloudrun.sh) : CW_ACCESS_KEY / CW_SECRET_KEY
#     → deviennent CYBERWATCH_ACCESS_KEY / CYBERWATCH_SECRET_KEY dans le container (remapping du sim)
#     → defaults sim : cyberwatch-access-key / cyberwatch-secret-key
#
# On garde les defaults natifs des sims pour éviter les mismatches ; si vous
# voulez des creds custom pour la démo, exportez-les avant de lancer ce script :
#   export NEXPOSE_USERNAME=businesscorp-demo NEXPOSE_PASSWORD=R@pid7-D3mo...
#   export CW_ACCESS_KEY=cw-businesscorp-demo CW_SECRET_KEY=cw-BusinessCorp-Demo-S3cret
export NEXPOSE_USERNAME="${NEXPOSE_USERNAME:-nxadmin}"
export NEXPOSE_PASSWORD="${NEXPOSE_PASSWORD:-nxadmin-secret}"
export CW_ACCESS_KEY="${CW_ACCESS_KEY:-cyberwatch-access-key}"
export CW_SECRET_KEY="${CW_SECRET_KEY:-cyberwatch-secret-key}"

RAPID7_FORK="$SIMS_DIR/Rapid7InsightVM-simul"
CYBERWATCH_FORK="$SIMS_DIR/cyberwatch-simul"

PYTHON_BIN="$(command -v python3 || command -v python || true)"

echo "🚀 Deploy Business Corp demo — pipeline complet (7 étapes)"
echo "  Repo         : $REPO_ROOT"
echo "  Sims dir     : $SIMS_DIR"
echo "  Region       : $REGION"
echo ""

# --- 1. Sanity checks ---
echo "🔍 [1/6] Vérification des outils..."
command -v gcloud >/dev/null 2>&1 || { echo "❌ gcloud CLI manquant"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "❌ git manquant"; exit 1; }
[ -n "$PYTHON_BIN" ] || { echo "❌ python manquant"; exit 1; }
echo "  ✓ gcloud, git, python OK"
echo ""

# --- 2. Clone forks si absents ---
echo "📥 [2/6] Clone des sim forks (si absents)..."
mkdir -p "$SIMS_DIR"

if [ ! -d "$RAPID7_FORK" ]; then
  echo "  → git clone Rapid7InsightVM-simul..."
  git clone https://github.com/JCourtemanche/Rapid7InsightVM-simul.git "$RAPID7_FORK"
  cd "$RAPID7_FORK" && git checkout -b businesscorp-demo 2>/dev/null || true
  cd "$REPO_ROOT"
else
  echo "  ✓ Rapid7InsightVM-simul déjà cloné"
fi

if [ ! -d "$CYBERWATCH_FORK" ]; then
  echo "  → git clone cyberwatch-simul..."
  git clone https://github.com/JCourtemanche/cyberwatch-simul.git "$CYBERWATCH_FORK"
  cd "$CYBERWATCH_FORK" && git checkout -b businesscorp-demo 2>/dev/null || true
  cd "$REPO_ROOT"
else
  echo "  ✓ cyberwatch-simul déjà cloné"
fi
echo ""

# --- 3. Résolution auto des forks (portable) ---
echo "📝 [3/6] Résolution automatique des forks..."
echo "  → SIMS_DIR=$SIMS_DIR"
echo "  → Rapid7  : $RAPID7_FORK"
echo "  → CW      : $CYBERWATCH_FORK"
echo ""

# --- 4. Appliquer les patches (idempotent) ---
echo "🔨 [4/6] Application des patches Business Corp..."
"$PYTHON_BIN" "$REPO_ROOT/scripts/apply-patches.py"
echo ""

# --- 5. Sync config → génère business_corp_overrides.py ---
echo "🔄 [5/6] Synchronisation config → business_corp_overrides.py..."
"$PYTHON_BIN" "$REPO_ROOT/config/sync-config-to-sims.py"
echo ""

# --- 6. Deploy Cloud Run ---
echo "☁️  [6/6] Déploiement Cloud Run..."

echo ""
echo "  → Rapid7 InsightVM simulator..."
echo "    (creds: NEXPOSE_USERNAME=$NEXPOSE_USERNAME)"
cd "$RAPID7_FORK"
if [ ! -f deploy-cloudrun.sh ]; then
  echo "  ❌ deploy-cloudrun.sh introuvable dans $RAPID7_FORK"
  exit 1
fi
bash deploy-cloudrun.sh

echo ""
echo "  → Cyberwatch simulator..."
echo "    (creds: CW_ACCESS_KEY=$CW_ACCESS_KEY)"
cd "$CYBERWATCH_FORK"
if [ ! -f deploy-cloudrun.sh ]; then
  echo "  ❌ deploy-cloudrun.sh introuvable dans $CYBERWATCH_FORK"
  exit 1
fi
bash deploy-cloudrun.sh

cd "$REPO_ROOT"
echo ""

# --- 7. Rendre les 2 services invocables publiquement (idempotent) ---
echo "🌐 [7/7] Autorisation invocations publiques (allUsers → run.invoker)..."
for svc in rapid7-nexpose-simulator cyberwatch-simulator; do
  if gcloud run services add-iam-policy-binding "$svc" \
       --region="$REGION" \
       --member="allUsers" \
       --role="roles/run.invoker" \
       --quiet 2>/dev/null; then
    echo "  ✓ $svc : allUsers/run.invoker OK"
  else
    echo "  ⚠️  $svc : binding refusée (probable org policy iam.allowedPolicyMemberDomains)"
    echo "     → Demander à un admin org de lever la policy sur ce projet,"
    echo "       ou basculer XSIAM sur bearer token GCP (non recommandé pour démo)."
  fi
done
echo ""

# --- Récap URLs ---
echo "✅ Déploiement complet."
echo ""
echo "URLs Cloud Run :"
gcloud run services list --region="$REGION" --format="table(metadata.name,status.url)"

echo ""
echo "Prochaine étape :"
echo "  1. Sanity check : bash scripts/smoke-test.sh"
echo "  2. Configuration XSIAM : runbook/03-configure-xsiam-rapid7.md"
