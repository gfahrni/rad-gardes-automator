# AGENTS.md — consignes de travail

Projet : **RAD Gardes Automator** (moteur Python + interface PySide6).
Code dans `src/gardes/` et `src/gardes_gui/`, tests dans `tests/`.
Ce dossier est synchronisé par **Syncthing** entre plusieurs machines.

## Règle absolue : aucun `.git` dans ce dossier

Le dossier de travail ne doit **jamais** contenir de `.git` : Syncthing
synchronise les fichiers `.git` (index, locks, objets) et casse le dépôt.
Il ne doit pas non plus contenir de fichier `.git` de délégation.

- Ne lancez **jamais** `git init`, `git clone` ou `git worktree add` ici.
- L'historique Git vit **en dehors** du dossier, dans
  `~/.rad-gardes-automator/.git` (dossier surchargeable avec
  `RAD_GARDES_SUPPORT_DIR`), et pointe sur ce dossier via `core.worktree`.
  Un `git` lancé sans variable d'environnement ne verra donc pas le dépôt :
  c'est normal.
- Le dépôt distant :
  `git@github.com:gfahrni/rad-gardes-automator.git` (branche `main`).

## Pousser sur GitHub

Toujours passer par le script du projet :

```bash
./scripts/gh.sh status            # fichiers modifiés / ajoutés / supprimés
./scripts/gh.sh diff              # différences avec le dernier commit
./scripts/gh.sh push -m "Message de commit"
```

`push` fait, dans l'ordre : `git add -A` → `commit` (si changement) →
`git push origin main`. Sans `-m`, un message daté est généré.

Autres commandes utiles :

```bash
./scripts/gh.sh log 20            # 20 derniers commits
./scripts/gh.sh pull              # récupère origin/main (fast-forward)
```

Au **premier appel** sur une machine, le script clone automatiquement
l'historique depuis GitHub dans `~/.rad-gardes-automator` (`--no-checkout`),
sans toucher aux fichiers du dossier. Aucune configuration préalable n'est
requise hors une clé SSH autorisée sur GitHub.

### Équivalent manuel (si le script est indisponible)

Chaque commande doit définir `GIT_DIR` et `GIT_WORK_TREE` :

```bash
export GIT_DIR="$HOME/.rad-gardes-automator/.git"
export GIT_WORK_TREE="$PWD"

# une seule fois par machine, si GIT_DIR n'existe pas encore :
env -u GIT_DIR -u GIT_WORK_TREE \
  git clone --no-checkout git@github.com:gfahrni/rad-gardes-automator.git \
  "$HOME/.rad-gardes-automator"
git config core.worktree "$GIT_WORK_TREE"
git reset --mixed

# puis, à chaque publication :
git add -A && git commit -m "Message" && git push origin main
```

## Vérifier qu'une publication est bien passée

```bash
./scripts/gh.sh log 3
git ls-remote git@github.com:gfahrni/rad-gardes-automator.git refs/heads/main
```

Le commit affiché par le script doit être le même que celui de `origin/main`.
Chaque push sur `main` déclenche la CI GitHub Actions (`.github/workflows/tests.yml`).

## Pièges et dépannage

- **« not a git repository »** : `GIT_DIR` n'est pas défini. Utilisez le
  script, ou exportez les deux variables ci-dessus.
- **`~/.rad-gardes-automator` supprimé** : relancez `./scripts/gh.sh status`,
  il reclone l'historique depuis GitHub. Les commits non poussés sont perdus :
  poussez régulièrement.
- **Dossier du projet déplacé/renommé** : mettez à jour
  `git config core.worktree "<nouveau chemin>"` (ou supprimez
  `~/.rad-gardes-automator` pour forcer un reclonage).
- **Conflit à `pull`** : le script refuse si des modifications locales ne
  sont pas commitées. Commitez/poussez, ou annulez les modifications, puis
  relancez.
- **Fichiers ignorés** : `.gitignore` est respecté ; `data/`, `.venv/`,
  `build/`, `dist/`, `__pycache__/` et les documents locaux (`V3/`,
  `exemples/`, `algorithme.md`, etc.) ne partent jamais sur GitHub.

## Avant de pousser

```bash
make test                         # ou : QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
```

Gardez `README.md` et `STATUS.md` cohérents avec les changements de
comportement. Respectez le style existant (français, docstrings concises,
code moteur dans `src/gardes/`, UI dans `src/gardes_gui/`).
