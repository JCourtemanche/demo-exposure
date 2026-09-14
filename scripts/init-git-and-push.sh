#!/usr/bin/env bash
# ============================================================
# init-git-and-push.sh — Initialise le repo git local et pousse sur GitHub
# ============================================================
#
# Prérequis:
#   1. Le repo distant existe déjà sur GitHub :
#      https://github.com/JCourtemanche/demo-exposure
#      (créez-le manuellement via https://github.com/new si absent — vide, sans README)
#   2. gh CLI (github.com/cli/cli) ou git configuré avec un token PAT
#
# Usage:
#   bash scripts/init-git-and-push.sh
#
# Idempotent : si git déjà init, ne réinitialise pas. Si remote déjà présent, skip.
# ============================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

REMOTE_URL="https://github.com/JCourtemanche/demo-exposure.git"
DEFAULT_BRANCH="main"

echo "📦 Init git + push initial pour la démo Business Corp"
echo "  Repo local  : $REPO_ROOT"
echo "  Remote      : $REMOTE_URL"
echo ""

# 1. Vérifier git
command -v git >/dev/null 2>&1 || { echo "❌ git manquant"; exit 1; }

# 2. git init si nécessaire
if [ ! -d ".git" ]; then
  echo "→ git init..."
  git init -b "$DEFAULT_BRANCH"
else
  echo "  ✓ Repo git déjà initialisé"
fi

# 3. Configurer user.name / user.email si manquants (avertissement seul)
if [ -z "$(git config user.name || true)" ]; then
  echo "  ⚠️  git config user.name non défini — première commit peut échouer"
  echo "     → git config user.name \"Votre Nom\""
fi
if [ -z "$(git config user.email || true)" ]; then
  echo "  ⚠️  git config user.email non défini"
  echo "     → git config user.email \"vous@example.com\""
fi

# 4. Vérifier .gitignore présent
if [ ! -f ".gitignore" ]; then
  echo "  ⚠️  .gitignore absent — sera créé par ce script normalement, vérifier scripts/init-git-and-push.sh"
fi

# 5. Add + commit initial (si aucun commit)
if ! git rev-parse HEAD >/dev/null 2>&1; then
  echo ""
  echo "→ Premier commit..."
  git add -A
  git commit -m "chore: initial import — Business Corp Exposure Management demo kit

- Infrastructure documentation (24 focus assets across 9 zones)
- FR narrative (talk track, funnel rules, hero cases)
- Runbook: prerequisites → deploy → configure XSIAM → tags → controls → policy → validate → teardown
- Config kit: business-corp-config.yaml as single source of truth
- Auto-patch scripts for the 2 sim forks (Rapid7 + Cyberwatch)
- Bootstrap GCP IAM script
- Validation checklist + tenant open questions"
else
  echo "  ✓ Repo a déjà des commits"
fi

# 6. Configurer le remote si absent
if git remote get-url origin >/dev/null 2>&1; then
  existing=$(git remote get-url origin)
  if [ "$existing" != "$REMOTE_URL" ]; then
    echo "  ⚠️  Remote 'origin' pointe sur $existing (attendu $REMOTE_URL)"
    echo "     → Ajuster manuellement : git remote set-url origin $REMOTE_URL"
  else
    echo "  ✓ Remote 'origin' déjà configuré"
  fi
else
  echo "→ Ajout du remote 'origin'..."
  git remote add origin "$REMOTE_URL"
fi

# 7. Push
echo ""
echo "→ Push vers origin/$DEFAULT_BRANCH..."
echo "  (auth via PAT ou SSH selon votre configuration)"
git push -u origin "$DEFAULT_BRANCH"

echo ""
echo "✅ Push terminé."
echo "   → https://github.com/JCourtemanche/demo-exposure"
