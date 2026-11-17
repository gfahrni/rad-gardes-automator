# AGENTS.md — consignes de travail

Projet : **RAD Gardes Automator V6** — moteur Python + interface PySide6,
avec applications macOS et Windows. Code dans `src/gardes/` et
`src/gardes_gui/`, tests dans `tests/`, packaging dans `packaging/`.
Ce dossier est synchronisé par **Syncthing** entre plusieurs machines.

## Règle absolue : aucun `.git` dans ce dossier

Syncthing synchronise les fichiers internes de Git (index, locks, objets)
et corrompt le dépôt. Donc :

- **jamais** de `git init`, `git clone` ou `git worktree add` ici ;
- jamais de dossier `.git` ni de fichier `.git` de délégation ;
- tout ce qui touche à Git se fait **sans `.git` local**, via `GIT_DIR`
  pointant hors du dossier (voir ci-dessous).

Dépôt distant : `git@github.com:gfahrni/rad-gardes-automator.git`
(branche `main`). La V6 repart de la V4 (`v4.0.1`) ; la V5 simplifiée est
abandonnée mais ses tags `v5.0.x` restent dans l'historique.

## Interagir avec GitHub

Deux méthodes, au choix. Dans les deux cas, le dossier de travail reste
un simple dossier de fichiers.

### 1. Historique externe (méthode habituelle)

L'historique vit dans `~/.rad-gardes-automator/.git` et pointe sur ce
dossier via `core.worktree`. Chaque commande Git doit définir les deux
variables :

```bash
export GIT_DIR="$HOME/.rad-gardes-automator/.git"
export GIT_WORK_TREE="$PWD"

git status
git add -A && git commit -m "Message" && git push origin main
```

Si ce dossier n'existe pas encore (autre machine, ou supprimé), le
recréer une fois — cela ne touche pas aux fichiers du projet :

```bash
env -u GIT_DIR -u GIT_WORK_TREE \
  git clone --no-checkout git@github.com:gfahrni/rad-gardes-automator.git \
  "$HOME/.rad-gardes-automator"
git config core.worktree "$PWD"
git reset --mixed
```

### 2. Clone temporaire (si l'historique externe est indisponible)

```bash
TMP="$(mktemp -d)"
git clone git@github.com:gfahrni/rad-gardes-automator.git "$TMP/repo"
rsync -a --delete --exclude '.git/' --exclude '.venv/' --exclude 'build/' \
  --exclude 'dist/' --exclude 'data/' --exclude '__pycache__/' \
  --exclude '.build-venv/' --exclude '.build-work/' \
  ./ "$TMP/repo/"
cd "$TMP/repo" && git add -A && git commit -m "Message" && git push
cd - && rm -rf "$TMP"
```

`.gitignore` reste la référence : ne forcez jamais l'ajout de fichiers
ignorés (`git add -f` interdit).

## Vérifier une publication

```bash
git ls-remote git@github.com:gfahrni/rad-gardes-automator.git refs/heads/main
```

Le SHA distant doit correspondre au dernier commit local. Un push sur
`main` déclenche la CI GitHub Actions (`.github/workflows/tests.yml`).
Un tag `v6*` déclenche `.github/workflows/release-v6.yml` (exe Windows +
release). L'app macOS se construit localement
(`packaging/build-macos.sh`) puis son ZIP est ajouté à la release avec
`gh release upload`.

## Avant de pousser

```bash
make test      # ou : QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
```

Pour une release, vérifier aussi les deux builds :

```bash
packaging/build-macos.sh                 # macOS
packaging/build-windows.ps1              # Windows (PowerShell)
```

Gardez `README.md` et `STATUS.md` cohérents avec les changements de
comportement. Style : français, docstrings concises, moteur dans
`src/gardes/`, UI dans `src/gardes_gui/`.

## Pièges

- **« not a git repository »** : `GIT_DIR` / `GIT_WORK_TREE` ne sont pas
  définis. Utilisez la méthode ci-dessus.
- **Dossier du projet déplacé** : `git config core.worktree "<nouveau
  chemin>"`, ou supprimez `~/.rad-gardes-automator` pour forcer un
  reclonage.
- **`pull` avec modifications locales** : commit suspect ou conflit,
  inspectez avant de forcer quoi que ce soit.
- **Fichiers ignorés** : `data/`, `.venv/`, `.build-venv/`, `.build-work/`,
  `build/`, `dist/`, `__pycache__/`, `.DS_Store` et les documents locaux
  (`V3/`, `exemples/`, `algorithme.md`, etc.) ne doivent jamais partir sur
  GitHub.
- **Builds** : ne pas lancer PyInstaller dans un venv synchronisé par
  Syncthing ; utiliser `.build-venv/` (ignoré) ou `BUILD_VENV` hors du
  dossier.
