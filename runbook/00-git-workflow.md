# Runbook 00 — Workflow Git & publication GitHub

Objectif : versionner ce kit démo sur GitHub (`https://github.com/JCourtemanche/demo-exposure`) et cadrer le workflow d'évolution.

## Étape 0.1 — Créer le repo GitHub

1. Sur GitHub, cliquer **New repository**
2. Owner : `JCourtemanche`, Name : `demo-exposure`
3. **Visibility** : Public (ou Private selon votre stratégie)
4. **Ne PAS** initialiser avec README, .gitignore ou LICENSE — on push ceux locaux
5. Cliquer **Create repository**

Note : si un repo `demo-exposure` existe déjà et n'est pas vide, soit vous mergez, soit vous supprimez d'abord.

## Étape 0.2 — Configurer les credentials git

**Option A — Personal Access Token (PAT) HTTPS** :
1. GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token
2. Scope minimum : `Contents: Read and write` + `Metadata: Read-only`
3. Copier le token
4. Windows : Git Credential Manager le gérera au premier push (prompt automatique)

**Option B — SSH** :
```powershell
ssh-keygen -t ed25519 -C "vous@example.com"
# Puis coller ~/.ssh/id_ed25519.pub dans GitHub → Settings → SSH keys
```

Adapter le remote URL en `git@github.com:JCourtemanche/demo-exposure.git` dans `scripts/init-git-and-push.sh` si SSH.

## Étape 0.3 — Init + push initial

Depuis la racine `C:\Users\jcourtemanch\Documents\dev\demo\exposure-management\` :

```powershell
bash scripts/init-git-and-push.sh
```

Le script :
1. `git init -b main`
2. Vérifie config user.name/user.email
3. Commit initial complet
4. Ajoute remote `origin` = `https://github.com/JCourtemanche/demo-exposure.git`
5. Push

Après succès : ouvrir `https://github.com/JCourtemanche/demo-exposure` pour vérifier.

## Étape 0.4 — Workflow d'évolution

Pour toute évolution ultérieure du kit :

```powershell
# Créer une branche feature
git checkout -b feat/nouveau-hero-case

# Modifier les fichiers (généralement uniquement business-corp-config.yaml)
# ...

# Regénérer les overrides + tester en local si possible
python config/sync-config-to-sims.py

# Commit + push
git add -A
git commit -m "feat: add hero case for CVE-XXXX-YYYY on srv-XXX"
git push -u origin feat/nouveau-hero-case

# Ouvrir une PR sur GitHub, merger vers main
```

## Étape 0.5 — Cycle de vie recommandé

- **`main`** : branche stable, prête pour démo. Chaque merge dans `main` = version démo-ready.
- **`feat/*`** : évolutions du narratif, nouveaux hero cases, adaptations client-spécifique
- **Tags** : `v1.0.0` pour première release démo-ready, `v1.1.0` pour ajouts hero cases, etc.

Créer un tag :
```powershell
git tag -a v1.0.0 -m "First demo-ready version"
git push origin v1.0.0
```

## Étape 0.6 — Attention aux secrets

Le `.gitignore` exclut :
- `.secrets.local.md` (credentials Cloud Run + XSIAM API keys)
- `.env`, `.env.local`
- `validation/discovery/` (dumps JSON post-ingestion)
- `narratif/screenshots/` (captures d'écran client, souvent sensibles)
- `sims/` (forks des simulateurs, versionnés séparément)

**Avant chaque push** : `git status` pour confirmer qu'aucun secret ne se glisse dedans.

Si vous avez accidentellement commit un secret :
```powershell
# Retirer le fichier de tous les commits (attention destructif)
git filter-repo --path <fichier> --invert-paths
git push --force
# Puis révoquer le secret compromis
```

Alternative moins invasive : `git rm --cached <fichier> && git commit -m "remove secret" && git push` — mais l'historique garde le secret. Toujours révoquer.

## Étape 0.7 — Forks des sims

Les 2 sims (`Rapid7InsightVM-simul`, `cyberwatch-simul`) sont clonés dans `../sims/` (voir `scripts/deploy-full.sh`), en dehors du repo `demo-exposure`. Ils suivent leur propre lifecycle git.

Si vous voulez versionner **vos patches** aux sims :
1. Fork sur GitHub (bouton Fork depuis les repos originaux)
2. Cloner vos forks
3. Commiter les patches (une fois `apply-patches.py` exécuté)
4. Push sur vos forks
5. Optionnel : PR upstream si les patches sont d'intérêt général

Sinon, garder les clones locaux non-versionnés — les patches restent sur disque.

## Suivant

→ [`01-prerequisites.md`](01-prerequisites.md)
