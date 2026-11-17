# STATUS — V6

## État

**V6 prête pour la release.** La V4 complète (moteur + interface PySide6) a
été restaurée depuis le tag `v4.0.1`, puis dotée d'applications macOS et
Windows. La V5 simplifiée est abandonnée ; ses tags `v5.0.x` restent dans
l'historique.

- Tests : **52 verts** (7 interface/contrôleur + 4 chemins + 41 moteur/CLI).
- App macOS : construite, signée ad-hoc, self-test et smoke test verts,
  archive extraite et retestée.
- App Windows : construite par la CI GitHub Actions sur tag `v6*`, avec
  self-test, smoke test et archive ZIP.

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
```

## Ce qui marche

| Écran | Contenu |
|---|---|
| 1. Fichiers | Sélection PDF / planning / souhaits / dossier, bouton « Charger les exemples » |
| 2. Planning | Métriques 181/112/88/24/80/8, pré-remplis et cellules, jours `fer.` |
| 3. Crédit de Gardes | 12 personnes assignables × 5 colonnes (`Nom`, `Samedi`, `Dimanche`, `Fériés`, `Départ / Arrivée`), lecture seule, validation |
| 4. Souhaits | Métriques 14/12/181/227/384/106/1817, détail par personne, avertissements |
| 5. Attribution | 87/88, 3 rouges, 74 verts, onglets affectations/trous/rouges/quotas/solveur |
| 6. Export | 87 noms écrits, 1 trou, 24 fixes, rapport intégré, boutons d'ouverture, nouveau run |

Thème sombre complet : `QPalette` + feuille de style, cartes/tableaux/onglets/
scrollbars/tooltips, `QMessageBox`/`QDialog`, et `QFileDialog` Qt non natif
pour rester dark.

## Référence sur les exemples

- Couverture : **87/88**
- Rouges forcés : **3**
- Verts : **74**
- Trou restant : **1 férié** (`2027-01-02` soir)
- Fixes : **24** préservés
- Solveur : OR-Tools CP-SAT 9.15.6755, `OPTIMAL`, ~0,2 s

## Applications

Un seul spec PyInstaller : `packaging/rad_gardes_v6.spec`. Il embarque le
moteur, l'interface, PySide6, OR-Tools, pdfplumber, openpyxl et `examples/`.

| Plateforme | Commande | Sortie |
|---|---|---|
| macOS Apple Silicon | `packaging/build-macos.sh` | `dist/RAD Gardes V6.app`, `dist/RAD-Gardes-V6-macos-arm64.zip` |
| Windows x64 | `packaging/build-windows.ps1` | `dist\RAD Gardes V6\`, `dist\RAD-Gardes-V6-windows-x64.zip` |

Vérifications intégrées aux builds :

```bash
"RAD Gardes V6" --self-test    # pipeline complet sur les exemples
"RAD Gardes V6" --smoke-test   # ouverture/fermeture de la fenêtre Qt
```

L'app macOS est signée en ad-hoc (`codesign --force --deep --sign -`) et
l'archive est créée avec `ditto --norsrc --noextattr` pour éviter les fichiers
AppleDouble `._`. Taille constatée : app ~255 Mo, ZIP ~97 Mo.

## Exemples anonymisés

Les fichiers de `examples/` ont été nettoyés pour une publication GitHub :

- noms réels remplacés par des noms fictifs cohérents entre PDF, planning et
  souhaits ;
- feuilles internes inutilisées et feuilles vides supprimées ;
- colonnes non nécessaires au moteur vidées ; seules les colonnes `GARDE`
  jour/soir, les dates et les indicateurs restent utiles ;
- zones de texte, images, hyperliens, paramètres d'imprimante, vues
  personnalisées et noms d'utilisateurs supprimés ;
- métadonnées, logo et initiales du PDF remplacés ou supprimés ;
- captures d'écran régénérées avec des chemins neutres.

Voir `examples/README.md` pour le détail.

## Commandes

```bash
# Installation
uv venv .venv --python 3.12
UV_HTTP_TIMEOUT=900 uv pip install --python .venv/bin/python -e ".[dev]"

# Tests
QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q

# Interface
.venv/bin/python -m gardes_gui

# Captures d'écran
make screenshots

# Applications
packaging/build-macos.sh
packaging/build-windows.ps1
```

## Release V6

Workflow : `.github/workflows/release-v6.yml`, déclenché par un tag `v6*`.

1. `git tag v6.0.0 && git push origin v6.0.0`
2. La CI teste le projet, construit l'app Windows, exécute `--self-test` et
   `--smoke-test`, crée `RAD-Gardes-V6-windows-x64.zip` et la release.
3. L'app macOS est construite localement (les runners macOS ne sont pas
   disponibles sur cette installation GitHub Actions), puis ajoutée :

```bash
packaging/build-macos.sh
gh release upload v6.0.0 dist/RAD-Gardes-V6-macos-arm64.zip
```

## Architecture

- `src/gardes_gui/controller.py` : orchestration sans Qt, réutilise le moteur intégré.
- `src/gardes_gui/state.py` : chemins et données du run.
- `src/gardes_gui/main_window.py` : fenêtre, sidebar, navigation, erreurs.
- `src/gardes_gui/widgets/` : six écrans + widgets communs.
- `src/gardes_gui/workers.py` : solveur CP-SAT en `QThread`.
- `src/gardes/` : moteur (steps 1 à 5), intégré dans V6.
- `packaging/` : spec unique, icônes, scripts macOS/Windows, LISEZ-MOI.
- `examples/` : documents synthétiques.
- `scripts/generate_screenshots.py` : captures reproductibles.

## Décisions appliquées

- **V6 = V4 complète + applications macOS/Windows.** La V5 simplifiée est
  abandonnée ; `main` repart de `v4.0.1` et les tags `v5.0.x` sont conservés.
- GUI PySide6 depuis les sources, un seul spec PyInstaller pour les deux OS.
- App macOS construite et publiée localement ; exe Windows construit par la CI.
- Signature macOS ad-hoc, pas de notarisation ; pas de signature Windows.
- Le moteur est intégré dans `src/gardes` ; V6 est autonome.
- Extraction PDF via `pdfplumber` (MIT) : PyMuPDF (AGPL-3.0) reste exclu.
- Couleurs des souhaits : toute couleur non reconnue bloque avec la liste des
  cellules fautives et les couleurs autorisées.
- Aucun nom de personne n'est codé en dur dans le moteur.

## Limites connues

- macOS fourni pour Apple Silicon (`arm64`) uniquement ; pas d'universel.
- Pas de onefile ; version Windows fournie en `onedir`.
- Pas de signature Windows/macOS ni de notarisation.
- Pas de round suivant.
- Pas de version été.
- Géométrie PDF/planning calée sur les exemples.

## Reprise / sécurité

- Le dépôt est à la racine du projet, avec un historique Git propre.
- La V4 reste accessible au tag `v4.0.1`, la V5 aux tags `v5.0.0`/`v5.0.1`.
- En cas de reprise : `git log --oneline`, `cat STATUS.md`, puis
  `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q`.
- Une erreur métier s'affiche dans une boîte de dialogue et laisse l'écran
  courant intact ; aucune correction silencieuse.
