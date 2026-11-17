# AGENTS.md — consignes de travail

Projet : **RAD Gardes Automator V7** — moteur Python + interface PySide6
à écran unique, avec applications macOS et Windows. Code dans `src/gardes/`
et `src/gardes_gui/`, tests dans `tests/`, packaging dans `packaging/`.
Ce dossier est synchronisé par **Syncthing** entre plusieurs machines.

## Dépôt Git : dans le dossier

Le dépôt vit dans le `.git` de ce dossier (branche `main`, upstream
`origin/main`). Tout se fait directement ici :

```bash
git status
git add -A && git commit -m "Message" && git push origin main
```

L'ancienne méthode par `GIT_DIR` externe (`~/.rad-gardes-automator/.git`) et
celle par clone temporaire sont **abandonnées** : l'historique est maintenant
local, comme pour les autres projets du dossier `DEVELOPPEMENT`. Si
`~/.rad-gardes-automator` existe encore, il est périmé (il pointait sur le même
commit que `origin/main`) et peut être supprimé.

Dépôt distant : `https://github.com/gfahrni/rad-gardes-automator.git`
(branche `main`). La V7 succède à la V6 (tag `v6.0.0`), elle-même issue de
la V4 (`v4.0.1`) ; la V5 simplifiée est abandonnée mais ses tags `v5.0.x`
restent dans l'historique.

## Interagir avec GitHub

- Auth : `gh` alimente l'aide-mémoire HTTPS (`!gh auth git-credential` dans
  `~/.gitconfig`). Vérifier avec `gh auth status`.
- Identité du dépôt : `gfahrni <guillaume.fahrni@chuv.ch>`.
- Repli SSH si HTTPS échoue :
  `git remote set-url origin git@github.com:gfahrni/rad-gardes-automator.git`.

`.gitignore` reste la référence : ne forcez jamais l'ajout de fichiers
ignorés (`git add -f` interdit).

## Vérifier une publication

```bash
git fetch origin && git status -sb        # « ## main...origin/main » sans écart
git ls-remote origin refs/heads/main      # SHA distant == git rev-parse HEAD
```

Le SHA distant doit correspondre au dernier commit local. Un push sur
`main` déclenche la CI GitHub Actions (`.github/workflows/tests.yml`).
Un tag `v7*` déclenche `.github/workflows/release-v7.yml` (exe Windows +
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

- **« not a git repository »** : vous n'êtes pas à la racine du projet, ou le
  `.git` a disparu. Vérifier avec `git -C . rev-parse --show-toplevel`.
- **Dossier du projet déplacé** : le `.git` suit le dossier, rien à faire. Ne
  plus utiliser `core.worktree`.
- **`.git` et Syncthing** : `~/Nextcloud/.stignore` exclut `.git` ; ne pas
  retirer cette ligne, sinon index/locks/objets seront répliqués et le dépôt
  se corrompra.
- **`pull` avec modifications locales** : commit suspect ou conflit,
  inspectez avant de forcer quoi que ce soit.
- **Fichiers ignorés** : `data/`, `.venv/`, `.build-venv/`, `.build-work/`,
  `build/`, `dist/`, `__pycache__/`, `.DS_Store` et les documents locaux
  (`V3/`, `exemples/`, `algorithme.md`, etc.) ne doivent jamais partir sur
  GitHub.
- **Builds** : ne pas lancer PyInstaller dans un venv synchronisé par
  Syncthing ; utiliser `.build-venv/` (ignoré) ou `BUILD_VENV` hors du
  dossier.
