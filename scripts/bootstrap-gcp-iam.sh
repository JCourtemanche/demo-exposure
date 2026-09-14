#!/usr/bin/env bash
# ============================================================
# bootstrap-gcp-iam.sh — Prépare les droits IAM GCP pour la démo
# ============================================================
#
# Usage:
#   bash scripts/bootstrap-gcp-iam.sh
#
# Prérequis:
#   - gcloud CLI authentifié (gcloud auth login)
#   - Projet GCP configuré par défaut (gcloud config set project <ID>)
#   - Vous devez être Owner ou avoir "roles/resourcemanager.projectIamAdmin"
#     sur le projet pour attribuer des rôles à d'autres membres.
#
# À lancer UNE SEULE FOIS par projet GCP. Idempotent.
# ============================================================
set -euo pipefail

echo "🔧 Bootstrap IAM pour la démo Cortex Exposure Management"
echo ""

# --- 1. Récupération des variables d'environnement ---
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -z "$PROJECT_ID" ]; then
  echo "❌ Aucun projet GCP configuré. Lancez: gcloud config set project <PROJECT_ID>"
  exit 1
fi

USER_EMAIL=$(gcloud config get-value core/account 2>/dev/null || echo "")
if [ -z "$USER_EMAIL" ]; then
  echo "❌ Aucun compte utilisateur. Lancez: gcloud auth login"
  exit 1
fi

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "  Projet         : $PROJECT_ID"
echo "  Utilisateur    : $USER_EMAIL"
echo "  Compte service : $SERVICE_ACCOUNT"
echo ""

# --- 2. Activation des APIs GCP ---
echo "🔌 Activation des APIs GCP requises..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  iam.googleapis.com \
  --project="$PROJECT_ID"

# --- 3. Droits utilisateur (déclencher builds, upload code, deploy Cloud Run) ---
echo ""
echo "👤 Attribution des droits utilisateur ($USER_EMAIL)..."

USER_ROLES=(
  "roles/cloudbuild.builds.editor"      # Déclencher Cloud Build
  "roles/storage.admin"                  # Upload sources vers Cloud Storage
  "roles/run.admin"                      # Déployer et administrer les services Cloud Run
  "roles/iam.serviceAccountUser"         # Impersonate le SA Cloud Build
  "roles/artifactregistry.admin"         # Créer/gérer les repos Artifact Registry
)

for role in "${USER_ROLES[@]}"; do
  echo "  → $role"
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="user:$USER_EMAIL" \
    --role="$role" \
    --condition=None \
    --quiet > /dev/null
done

# --- 4. Droits du compte de service Cloud Build (build + push image) ---
echo ""
echo "🤖 Attribution des droits compte de service ($SERVICE_ACCOUNT)..."

SA_ROLES=(
  "roles/storage.admin"                  # Lire les sources uploadées
  "roles/artifactregistry.writer"        # Pousser l'image Docker construite
  "roles/run.developer"                  # Déployer les révisions Cloud Run
  "roles/logging.logWriter"              # Écrire les logs de build
)

for role in "${SA_ROLES[@]}"; do
  echo "  → $role"
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="$role" \
    --condition=None \
    --quiet > /dev/null
done

# --- 5. Vérification finale ---
echo ""
echo "🔍 Vérification finale..."
gcloud projects get-iam-policy "$PROJECT_ID" \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:$USER_EMAIL" \
  | head -20 || true

echo ""
echo "✅ Configuration IAM terminée."
echo ""
echo "Prochaine étape :"
echo "  bash scripts/deploy-full.sh"
