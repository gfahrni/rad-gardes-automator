# AGENTS.md — consignes de travail

Projet : **RAD Gardes Automator V5** — attribution de gardes depuis un classeur
Excel simple. Moteur et interface (tkinter) dans `gardes_simple/`, tests dans
`tests/`, packaging PyInstaller dans `packaging/`, classeurs de démonstration
dans `examples/`.

Ce dossier est synchronisé par **Syncthing** entre plusieurs machines.

## Règle absolue : aucun `.git` dans ce dossier

Syncthing synchronise les fichiers internes de Git (index, locks, objets)
et corrompt le dépôt. Donc :

- **jamais** de `git init`, `git clone` ou `git worktree add` ici ;
- jamais de dossier `.git` ni de fichier `.git` de délégation ;
- tout ce qui touche à Git se fait **sans `.git` local**, via `GIT_DIR`
  pointant hors du dossier (voir ci-dessous).

Dépôt distant : `git@github.com:gfahrni/rad-gardes-automator.git`
(branche `main`, qui porte la V5 ; la V4 est au tag `v4.0.1`).

## Interagir avec GitHub

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
`main` lance la CI (`.github/workflows/tests.yml`). Un tag `v5*` lance
`.github/workflows/release-v5.yml` (exe Windows + release).

## Avant de pousser

```bash
.venv/bin/python -m pytest -q      # ou : uv run --with pytest --with openpyxl python -m pytest -q
.venv/bin/python -m ruff check .
```

Gardez `README.md` cohérent avec le comportement : c'est la doc utilisateur
de l'application. Style : français, docstrings concises, messages d'erreur
explicites et actionnables.

## Pièges

- **« not a git repository »** : `GIT_DIR` / `GIT_WORK_TREE` ne sont pas
  définis.
- **Dossier du projet déplacé** : `git config core.worktree "<nouveau
  chemin>"`, ou supprimez `~/.rad-gardes-automator` pour forcer un
  reclonage.
- **Applications** : l'app macOS se construit localement
  (`packaging/build-macos.sh`) ; l'exe Windows passe par la CI ou par un PC
  Windows (`packaging/build-windows.ps1`).
