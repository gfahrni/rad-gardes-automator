# STATUS — V7

## État

**V7 prête pour la release.** Le moteur de la V4 et le packaging de la V6 sont
conservés, mais l'interface est réduite à **un seul écran** : trois fichiers,
un dossier de sortie, « Lancer », puis le rapport et le planning rempli.

- Tests : **54 verts** (moteur, contrôleur, écran unique, thème, chemins).
- App macOS : construite, signée ad-hoc, self-test, smoke test et lancement
  Cocoa vérifiés ; ZIP extrait et retesté.
- App Windows : construite par la CI GitHub Actions sur tag `v7*`, avec
  self-test, smoke test et archive ZIP.

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
```

### Allègement 7.2.0

Exclusion de `sqlite3`/`_sqlite3`, inutilisés par l'application. Sur macOS,
cela retire aussi les bibliothèques ICU dont SQLite dépend :

- app macOS : **255 Mo → 217 Mo** ;
- archive macOS : **97 Mo → 82 Mo** ;
- self-test et smoke test vérifiés après exclusion.

Le gain est marginal sous Windows (le ZIP n'embarque pas d'ICU).

### Compatibilité 7.1.0

Les en-têtes de garde du soir `13h-23h` **et** `15h-23h` sont acceptés.
Testé sur les deux templates de backup :

- `backup_ete.2026.xlsx` : 184 jours, 112 créneaux, 4 fériés, 0 garde pré-remplie ;
- `backup_hiver.2027.xlsx` : 181 jours, 102 créneaux, 0 férié, 0 garde pré-remplie.

Aucun code spécifique à l'hiver n'était nécessaire : les deux classeurs ont la
même structure `Feuille1` (6 zones mensuelles, mêmes colonnes GARDE).

### Correctif 7.0.1

Les sélecteurs de fichiers s'ouvrent désormais dans le **dossier de travail**
(par défaut `~/Documents/RAD Gardes Automator/run`), créé au démarrage de
l'application, au lieu de `~/Documents` ou de la racine. Après un premier
choix, le dialogue reprend le dernier dossier utilisé. Une option de
diagnostic `--paths` affiche les chemins résolus.

## Flux V7

| Étape | Contenu |
|---|---|
| 1. Fichiers | PDF des gardes, planning Excel, souhaits Excel |
| 2. Dossier | Sortie proposée : `~/Documents/RAD Gardes Automator/run` |
| 3. Lancer | Scan planning → PDF → validation → souhaits → CP-SAT → export |
| 4. Résultat | Rapport à l'écran + `planning-rempli.xlsx` + `rapport.txt` |

Aucune validation manuelle, aucun écran intermédiaire. Le contrôleur exécute
le pipeline avec `persist=False` : seuls les deux fichiers de sortie sont
écrits, pas les JSON intermédiaires de la V6.

## Référence sur les exemples

- Couverture : **87/88**
- Rouges forcés : **3**
- Verts : **74**
- Trou restant : **1 férié** (`2027-01-02` soir)
- Fixes : **24** préservés
- Solveur : OR-Tools CP-SAT 9.15.6755, `OPTIMAL`, ~0,2 s

## Applications

Un seul spec PyInstaller : `packaging/rad_gardes_v7.spec`. Il embarque le
moteur, l'écran unique, PySide6, OR-Tools, pdfplumber, openpyxl et `examples/`.

| Plateforme | Commande | Sortie |
|---|---|---|
| macOS Apple Silicon | `packaging/build-macos.sh` | `dist/RAD Gardes V7.app`, `dist/RAD-Gardes-V7-macos-arm64.zip` |
| Windows x64 | `packaging/build-windows.ps1` | `dist\RAD Gardes V7\`, `dist\RAD-Gardes-V7-windows-x64.zip` |

Vérifications intégrées aux builds :

```bash
"RAD Gardes V7" --self-test    # pipeline complet sur les exemples
"RAD Gardes V7" --smoke-test   # ouverture/fermeture de la fenêtre Qt
```

L'app macOS est signée en ad-hoc et l'archive est créée avec
`ditto --norsrc --noextattr`. Taille constatée : app ~255 Mo, ZIP ~97 Mo.

## Exemples anonymisés

Les fichiers de `examples/` sont synthétiques et cohérents entre eux (PDF,
planning, souhaits). Voir `examples/README.md` pour le détail du nettoyage.

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

## Release V7

Workflow : `.github/workflows/release-v7.yml`, déclenché par un tag `v7*`.

1. `git tag v7.2.0 && git push origin v7.2.0`
2. La CI teste le projet, construit l'app Windows, exécute `--self-test` et
   `--smoke-test`, crée `RAD-Gardes-V7-windows-x64.zip` et la release.
3. L'app macOS est construite localement (les runners macOS ne sont pas
   disponibles sur cette installation GitHub Actions), puis ajoutée :

```bash
packaging/build-macos.sh
gh release upload v7.2.0 dist/RAD-Gardes-V7-macos-arm64.zip
```

## Architecture

- `src/gardes_gui/main_window.py` : écran unique (fichiers, dossier, Lancer,
  résultat).
- `src/gardes_gui/controller.py` : pipeline complet, option `persist` pour
  écrire ou non les JSON intermédiaires, `run_complete()`.
- `src/gardes_gui/workers.py` : `RunWorker`, pipeline + export dans un fil.
- `src/gardes_gui/widgets/common.py` : cartes, lignes de fichiers, métriques.
- `src/gardes_gui/state.py`, `paths.py` : chemins et état du run.
- `src/gardes/` : moteur (steps 1 à 5), inchangé.
- `packaging/` : spec unique, icônes, scripts macOS/Windows, LISEZ-MOI.
- `docs/screenshots/` : avant/après calcul.

## Décisions appliquées

- **V7 = moteur V4 + écran unique.** La V6 (six écrans) reste au tag `v6.0.0`.
- Le dossier de sortie par défaut est toujours
  `~/Documents/RAD Gardes Automator/run`, en source comme dans les apps.
- L'application ne produit que `planning-rempli.xlsx` et `rapport.txt`.
- La validation est automatique ; en cas de donnée incohérente, l'erreur
  existante du moteur est affichée avec ses détails.
- Un seul spec PyInstaller pour macOS et Windows.
- Signature macOS ad-hoc, pas de notarisation ; pas de signature Windows.
- Extraction PDF via `pdfplumber` (MIT) ; PyMuPDF (AGPL-3.0) reste exclu.

## Limites connues

- macOS fourni pour Apple Silicon (`arm64`) uniquement ; pas d'universel.
- Pas de onefile ; version Windows fournie en `onedir`.
- Pas de signature Windows/macOS ni de notarisation.
- Pas de round suivant ; pas de version été.
- Géométrie PDF/planning calée sur les exemples.

## Reprise / sécurité

- La V6 reste accessible au tag `v6.0.0`, la V4 à `v4.0.1`, la V5 aux tags
  `v5.0.x`.
- En cas de reprise : `git log --oneline`, `cat STATUS.md`, puis
  `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q`.
- Une erreur métier s'affiche dans une boîte de dialogue ; aucune correction
  silencieuse.
