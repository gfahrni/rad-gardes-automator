# RAD Gardes Automator — V6

Application locale d'attribution automatique des gardes de radiologues.
Le moteur (étapes 1 à 5) et l'interface PySide6 sombre sont dans le même
dépôt. **V6 reprend la V4 complète** et ajoute des applications distribuables
pour macOS et Windows : les deux archives sont publiées dans les releases
GitHub, sans installation de Python.

La V5 simplifiée (classeur Excel unique) est abandonnée. Les tags `v5.0.0` et
`v5.0.1` restent disponibles dans l'historique, mais `main` repart de la V4
(`v4.0.1`) et porte la V6.

## Périmètre verrouillé

- un run complet par période ;
- relance tous les 6 mois à partir des nouveaux documents de référence ;
- **pas de reprise d'un planning précédent** (« round suivant » hors V6) ;
- le moteur est intégré dans `src/gardes/`, sans duplication.

## Prérequis (depuis les sources)

- Python 3.12
- `uv`
- macOS ou Linux avec affichage graphique

## Installation

```bash
uv venv .venv --python 3.12
UV_HTTP_TIMEOUT=900 uv pip install --python .venv/bin/python -e ".[dev]"
```

PySide6 Essentials 6.12.0 est la seule dépendance graphique. Le moteur utilise
openpyxl, pdfplumber et OR-Tools, installés avec le paquet `gardes`.

## Lancer l'interface

```bash
.venv/bin/python -m gardes_gui
```

ou, si le script est installé :

```bash
.venv/bin/gardes-gui
```

## Applications macOS et Windows

Chaque release GitHub contient deux archives :

| Plateforme | Archive | Lancement |
|---|---|---|
| macOS Apple Silicon | `RAD-Gardes-V6-macos-arm64.zip` | décompresser, ouvrir `RAD Gardes V6.app` |
| Windows x64 | `RAD-Gardes-V6-windows-x64.zip` | décompresser, lancer `RAD Gardes V6.exe` |

Aucune installation de Python n'est nécessaire. Les exemples synthétiques sont
embarqués : à l'écran 1, cliquer sur « Charger les exemples ».

- **macOS** : l'app est signée en ad-hoc. Au premier lancement, si macOS la
  bloque : clic droit sur l'app > « Ouvrir » > « Ouvrir ».
- **Windows** : la version est portable (`onedir`), à extraire où vous voulez.

Les fichiers produits sont écrits par défaut dans
`Documents/RAD Gardes Automator/run`.

## Construire les applications

Le même spec PyInstaller construit l'app macOS et le dossier Windows :
`packaging/rad_gardes_v6.spec`. Il embarque le moteur, l'interface, PySide6,
OR-Tools, pdfplumber et `examples/`.

### macOS

```bash
packaging/build-macos.sh
```

Produit `dist/RAD Gardes V6.app` et
`dist/RAD-Gardes-V6-macos-arm64.zip`. L'archive est créée avec `ditto` pour
préserver les liens symboliques des frameworks Qt.

### Windows

```powershell
packaging\build-windows.ps1
```

Produit `dist\RAD Gardes V6\` et
`dist\RAD-Gardes-V6-windows-x64.zip`. Prérequis : Windows et Python 3.12.

Les deux builds exposent les options de vérification utilisées par la CI :

```bash
"RAD Gardes V6" --self-test    # pipeline complet sur les exemples, sans UI
"RAD Gardes V6" --smoke-test   # ouverture/fermeture de la fenêtre
```

## Parcours

| Écran | Rôle |
|---|---|
| **1. Fichiers** | PDF des gardes, planning Excel, souhaits Excel, dossier de sortie |
| **2. Planning** | Scan de `Feuille1` : 181 jours, 112 créneaux, 88 trous, 24 fixes, 80 WE, 8 fériés |
| **3. Crédit de Gardes** | 12 personnes assignables, `Samedi` / `Dimanche` / `Fériés` + `Départ / Arrivée`, lecture seule |
| **4. Souhaits** | 14 personnes, 181 dates, volontaires/vacances/non dispo, avertissements |
| **5. Attribution** | CP-SAT : couverture, rouges, verts, affectations, trous, quotas |
| **6. Export** | `planning-rempli.xlsx` + `rapport.txt`, ouverture des fichiers |

Le planning est scanné **avant** le crédit de gardes : c'est lui qui identifie
les personnes pré-remplies et le pool assignable.

## Exemples fournis

Les fichiers de `examples/` sont des données de démonstration anonymisées.
Ils sont cohérents entre eux : les noms du PDF, du planning et des souhaits
correspondent exactement. Ils sont embarqués dans les applications.

| Fichier | Contenu |
|---|---|
| `exemple-calcul-gardes.pdf` | PDF de calcul : 30 lignes, 26 CDC, 3 urgentistes, 1 exclu |
| `exemple-planning-vide.xlsx` | Planning de départ : `Feuille1`, 181 jours, 88 trous, 24 pré-remplis |
| `exemple-souhaits-garde.xlsx` | Souhaits : 14 personnes, 181 dates |

Référence sur ces exemples : **87/88**, **3 rouges**, **74 verts**,
**1 trou férié** (`2027-01-02` soir), 24 fixes préservés.

### Anonymisation

- Tous les noms de personnes sont remplacés par des noms fictifs plausibles.
- Les feuilles internes inutilisées et les feuilles vides ont été supprimées
  des classeurs.
- Les zones de texte, images, hyperliens, paramètres d'imprimante et vues
  personnalisées ont été retirés.
- Les métadonnées nominatives, le logo et les initiales du PDF ont été
  supprimés ou remplacés.
- Les noms fictifs sont les mêmes dans les trois documents, pour que le
  pipeline reste exécutable de bout en bout.

## Thème sombre

- Fond `#0f1115`, cartes `#171a21`, bordures `#2a303c`.
- Texte `#e6e9ef`, texte secondaire `#9aa4b2`.
- Accent bleu `#3b82f6` / `#5b9dff`.
- Tableaux, en-têtes, onglets, scrollbars, tooltips et champs stylés.
- `QMessageBox`, `QDialog` et `QFileDialog` sont thémés ; les sélecteurs de
  fichiers utilisent le dialogue Qt (`DontUseNativeDialog`) pour rester sombres.
- Palette Qt sombre appliquée via `QPalette` + feuille de style.

## Aperçu

Captures générées en mode `offscreen` à partir des exemples anonymisés.

| Fichiers | Planning |
|---|---|
| ![](docs/screenshots/00-welcome.png) | ![](docs/screenshots/01-planning.png) |

| Crédit de Gardes | Souhaits |
|---|---|
| ![](docs/screenshots/02-credit.png) | ![](docs/screenshots/03-wishes.png) |

| Attribution | Export |
|---|---|
| ![](docs/screenshots/04-attribution.png) | ![](docs/screenshots/05-export.png) |

Pour les régénérer :

```bash
make screenshots
```

### Crédit de Gardes — lecture seule

- L'écran affiche **uniquement les personnes qui seront placées dans le run** :
  les 12 assignables.
- Sont exclus : les pré-remplis/neuro, le nom exclu, les urgentistes et les CDC
  à quota week-end/férié nul.
- Colonnes : `Nom`, `Samedi`, `Dimanche`, `Fériés`, `Départ / Arrivée`.
- Aucune édition : si une valeur est fausse, la secrétaire corrige le PDF puis
  clique sur « Recharger depuis le PDF ».
- « Faire valider » enregistre `calcul-gardes.json` avec `validated = true`,
  puis scanne les souhaits.
- Sur l'exemple, la colonne `Départ / Arrivée` vaut `—` pour les 12 personnes :
  les notes de dates du PDF concernent des personnes exclues du pool.

Les noms sont comparés **exactement** (casse, accents, espaces). Une typo dans
le planning ou dans les souhaits bloque l'étape avec un message explicite.

### Couleurs des souhaits

- Vert `FF00FF00` = volontaire, cyan `FF00FFFF` = vacances/formation, rouge
  `FFFF0000` = non dispo.
- Neutres : fond de ligne, blanc, gris, `none`, `theme0`.
- **Toute autre couleur est bloquante**, même sur une personne non candidate.
  Le message liste les cellules, la personne, la date, le RGB et les couleurs
  autorisées. L'utilisateur corrige le fichier des souhaits puis relance.
- Rouge/vert sur un jour de semaine : warning (couleur reconnue mais hors scope).

## Sorties

Dans le dossier choisi (par défaut `data/run` en source, ou
`Documents/RAD Gardes Automator/run` dans les applications) :

- `gardes-a-remplir.json`
- `calcul-gardes.json`
- `souhaits-gardes.json`
- `attribution-gardes.json`
- `planning-rempli.xlsx`
- `rapport.txt`

## Tests

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
```

La suite (**52 tests** : 7 interface/contrôleur + 4 chemins + 41 moteur/CLI) couvre le contrôleur
(pipeline complet, validation des crédits), un smoke test Qt qui parcourt les
six écrans en mode `offscreen`, un test du thème sombre, les chemins
source/onedir/onefile, le CLI et les steps 1 à 5.
La CI GitHub Actions exécute la même suite sur Ubuntu et sur Windows (workflow
de release).

## Structure

```text
rad-gardes-automator/
├── examples/                  # PDF + classeurs synthétiques
├── src/gardes/                # moteur : steps 1 à 5, CLI, validation
├── src/gardes_gui/            # interface PySide6
├── tests/                     # 52 tests
├── scripts/                   # captures et entrée PyInstaller
├── docs/screenshots/          # aperçu README
├── packaging/                 # spec macOS/Windows, icônes, scripts, LISEZ-MOI
└── .github/workflows/         # CI + release V6 (Windows)
```

## Publier une release V6

```bash
git tag v6.0.0
git push origin v6.0.0
```

Le workflow `.github/workflows/release-v6.yml` construit alors l'application
Windows en `onedir`, exécute les tests puis le self-test et le smoke test,
crée l'archive ZIP et la publie dans la release GitHub.

L'application macOS se construit localement (les runners macOS ne sont pas
disponibles sur cette installation GitHub Actions), puis son archive est
ajoutée à la release :

```bash
packaging/build-macos.sh
gh release upload v6.0.0 dist/RAD-Gardes-V6-macos-arm64.zip
```

Le workflow peut aussi être lancé manuellement depuis l'onglet Actions ; dans
ce cas l'archive Windows est disponible comme artifact, sans création de
release.

## Limites V6

- macOS fourni pour Apple Silicon (`arm64`) uniquement ; pas d'universel.
- Pas d'exécutable onefile ; la version Windows est fournie en `onedir`.
- Pas de signature Windows/macOS ni de notarisation.
- Pas de round suivant : chaque période repart des trois documents de référence.
- Pas de version été.
- Le PDF et le planning sont calés sur le format des exemples fournis.

Voir `STATUS.md` pour l'état du build et la reprise.

## Licence

MIT — voir [`LICENSE`](LICENSE).

Les composants tiers embarqués dans les archives sont listés dans
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). Toutes les dépendances du
moteur sont sous licence permissive (MIT, BSD, Apache-2.0) : l'extraction PDF
utilise `pdfplumber` depuis la version 4.0.1, PyMuPDF (AGPL-3.0) ayant été
retiré pour que les exécutables puissent être distribués sous MIT. Seul
PySide6/Qt est sous LGPL-3.0, utilisé non modifié et livré en bibliothèques
remplaçables.
