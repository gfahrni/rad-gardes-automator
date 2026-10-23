# STATUS — V4

## État

**V4 prête pour GitHub.** Moteur et interface PySide6 sombre terminés, testés,
avec trois documents d'exemple entièrement anonymisés.

- Tests GUI : **7 verts** (3 contrôleur + 4 smoke Qt, dont le thème sombre).
- Tests chemins : **4 verts** (source, onedir, onefile, dossier de travail).
- Tests moteur : **40 verts** (steps 1 à 5 + CLI, référence métier).
- Total : **51 tests verts**.

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
```

## Release Windows

Workflow : `.github/workflows/release-windows.yml`.

- Déclenchement par tag `v*` ou manuellement.
- Build `onedir` avec PyInstaller sur `windows-latest`.
- Self-test du pipeline complet avec `--self-test`.
- Smoke test de l'interface avec `--smoke-test`.
- Archive `RAD-Gardes-Automator-windows-x64.zip` publiée dans la release.
- En lancement manuel, l'archive reste un artifact GitHub Actions.

## Architecture

- `src/gardes_gui/controller.py` : orchestration sans Qt, réutilise le moteur intégré.
- `src/gardes_gui/state.py` : chemins et données du run.
- `src/gardes_gui/main_window.py` : fenêtre, sidebar, navigation, erreurs.
- `src/gardes_gui/widgets/` : six écrans + widgets communs.
- `src/gardes_gui/workers.py` : solveur CP-SAT en `QThread`.
- `src/gardes/` : moteur (steps 1 à 5), intégré dans V4.
- `examples/` : documents synthétiques.
- `scripts/generate_screenshots.py` : captures reproductibles.

## Décisions appliquées

- GUI PySide6 depuis les sources.
- Pas d'exécutable, pas de signature.
- Pas de round suivant ; un run complet par période, relancé tous les 6 mois
  à partir des nouveaux documents de référence.
- Aucune persistance d'état entre deux runs.
- Le pré-scan du planning reste obligatoire et bloque si les données sont
  incohérentes.
- Couleurs des souhaits : toute couleur non reconnue bloque avec la liste des
  cellules fautives et les couleurs autorisées ; l'utilisateur corrige le
  fichier puis relance. Rouge/vert en semaine restent des warnings.
- Le moteur est intégré dans `src/gardes` ; V4 est autonome.
- Extraction PDF via `pdfplumber` (MIT) depuis 4.0.1 : PyMuPDF (AGPL-3.0) a été
  retiré pour que l'exécutable Windows puisse être distribué sous MIT.
- Aucun nom de personne n'est codé en dur dans le moteur.

## Limites connues

- Pas de onefile ; version Windows fournie en `onedir`.
- Pas de signature Windows/macOS.
- Pas de round suivant.
- Pas de version été.
- Géométrie PDF/planning calée sur les exemples.
- V4 est autonome : aucune dépendance à un dossier voisin.

## Reprise / sécurité

- Le dépôt est à la racine du projet, avec un historique Git propre.
- Les 40 tests du moteur sont dans `tests/` et doivent rester verts.
- En cas de reprise : `git log --oneline`, `cat STATUS.md`, puis
  `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q`.
- Une erreur métier s'affiche dans une boîte de dialogue et laisse l'écran
  courant intact ; aucune correction silencieuse.

## Étapes suivantes éventuelles

- Exécutable onefile / signature Windows et macOS (hors périmètre V4).
- Version été.
- Mode « round suivant » (hors périmètre V4).
