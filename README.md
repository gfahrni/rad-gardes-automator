# RAD Gardes Automator — V5

Attribution des gardes de radiologues à partir d'un **classeur Excel simple**.
Pas de PDF, pas de planning existant à décoder : on décrit les créneaux à
couvrir et le nombre de gardes de chacun, l'application produit le planning et
un rapport.

- application **macOS** (`.app`) et **Windows portable** (`.exe`, sans installation) ;
- interface minimale : choisir le classeur, cliquer, lire le rapport ;
- **refus strict** : si le classeur ne correspond pas exactement au format,
  l'application refuse, liste les problèmes et n'écrit rien.

## Télécharger

Les deux archives sont dans la dernière release GitHub (page « Releases ») :

| Plateforme | Fichier | Note |
|---|---|---|
| macOS (Apple Silicon) | `RAD-Gardes-V5-macos-arm64.zip` | app non notariée : au premier lancement, clic droit → « Ouvrir » si macOS bloque |
| Windows x64 | `RAD-Gardes-V5-windows-x64.zip` | exe non signé : « Informations complémentaires » → « Exécuter quand même » |

Chaque archive contient l'application, `gardes-in-vide.xlsx` (le classeur type)
et `gardes-in-demo.xlsx` (un exemple correct, pour essayer).

## Essayer en 30 secondes

1. Ouvrir l'application.
2. « Parcourir… » puis choisir `gardes-in-demo.xlsx`.
3. « Lancer le calcul » : le rapport s'affiche — **100 % (8/8)**, quotas 4/4.
4. « Ouvrir le résultat » ouvre le classeur produit à côté de l'entrée.

## Utilisation

Interface : un champ pour le classeur, « Parcourir… », « Modèle vierge… » (écrit
un classeur type prêt à remplir), « Lancer le calcul », « Ouvrir le résultat ».

En ligne de commande (depuis les sources) :

```bash
python3 -m gardes_simple                                   # interface graphique
python3 -m gardes_simple --entree examples/gardes-in-demo.xlsx
python3 -m gardes_simple --modele gardes-in-vide.xlsx      # classeur type
```

Codes de sortie : `0` succès, `2` refus (format), `3` quotas impossibles.

## Le classeur d'entrée

Un fichier `.xlsx` avec deux feuilles utiles (une éventuelle feuille
« Mode d'emploi » est ignorée).

**Feuille `Dates`** — une ligne par créneau à couvrir, à partir de la ligne 2 :

| A | B |
|---|---|
| `Date` | `Créneau` |
| 01.03.2027 | Matin |
| 01.03.2027 | Soir |

- `Date` : une **vraie date Excel** (format date), pas du texte ;
- `Créneau` : `Matin` ou `Soir` (liste déroulante dans le classeur type).

**Feuille `Personnes`** — une ligne par personne :

| A | B |
|---|---|
| `Nom` | `Gardes` |
| Muller | 3 |
| Rossi | 2 |

- `Nom` : unique (majuscules et espaces multiples ignorés à la comparaison) ;
- `Gardes` : nombre **entier** ≥ 0, nombre **exact** de gardes de la personne.

Le bouton « Modèle vierge » (ou `--modele`) écrit ce classeur : en-têtes,
colonne date pré-formatée, liste déroulante Matin/Soir et contrôles de saisie.

## Les règles vérifiées

1. La somme des `Gardes` doit être **exactement** égale au nombre de lignes de
   `Dates`. Sinon refus.
2. Une personne ne peut pas faire **deux gardes le même jour** (Matin + Soir).
3. Chaque créneau reçoit une seule personne, et chaque personne fait exactement
   son quota.
4. En-têtes, colonnes vides en trop, doublons de créneau, doublons de nom,
   dates en texte ou vides, créneaux inconnus, formules : **refus explicite**.

Le solveur est un flot maximal entier (b-matching biparti) : polynomial, donc
pas de recherche qui explose sur 200 créneaux. Une passe déterministe échange
ensuite des dates entre personnes pour casser les **deux jours consécutifs**
autant que faire se peut, et évite le pire enchaînement « Soir puis Matin le
lendemain ».

## Quand le classeur ne correspond pas

Rien n'est écrit, et chaque problème est listé avec sa cellule :

```text
REFUS — le classeur ne respecte pas le format attendu.

2 problème(s) :
  1. Dates, ligne 4 : créneau « Matinée » invalide (attendu « Matin » ou « Soir »).
  2. Somme des gardes (7) ≠ nombre de créneaux (8) : il manque 1 garde
     dans la colonne « Gardes ».
```

## Sorties

À côté du classeur choisi (ou dans `--sortie`) :

- `<nom>-resultat.xlsx` : feuille `Attribution` (Date, Créneau, Nom) et feuille
  `Synthèse` (prévu / attribué / écart / matins / soirs) ;
- `<nom>-rapport.txt` : le même rapport que dans l'interface.

```text
RÉSULTAT : OK
Taux de réussite : 100 % (8/8 créneaux attribués).
Quotas respectés : 4/4 personnes.
Jours consécutifs : 1 paire(s).
```

Sur l'exemple, cette paire restante est inévitable : Muller doit 3 gardes sur
4 dates, donc il travaille forcément deux jours voisins.

## Développement

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m gardes_simple   # interface
.venv/bin/python -m pytest -q
```

Structure :

```text
gardes_simple/      moteur + interface (tkinter)
examples/           classeurs de démonstration
packaging/          PyInstaller : spec, icône, scripts mac/Windows
tests/              suite pytest
```

## Construire les applications

macOS (sur un Mac) :

```bash
packaging/build-macos.sh        # → dist/RAD Gardes V5.app
```

Windows (sur un PC Windows, Python 3.12) :

```powershell
.\packaging\build-windows.ps1   # → dist\RAD-Gardes-V5-windows-x64.zip
```

GitHub Actions construit et teste l'exe Windows (workflow `release-v5`, manuel
ou tag `v5*`) : les tests, le build, un self-test de l'exe, puis l'archive
attachée à la release. L'app macOS n'est pas construite par la CI (pas de
runner macOS disponible sur ce dépôt) : elle se construit localement.

## Limites

- Quotas exacts : pas de « au moins » / « au plus ».
- Pas d'indisponibilités ni de souhaits : seulement les règles ci-dessus.
- Pas de reprise d'un planning précédent : chaque run repart du classeur.
- App macOS en arm64 uniquement, non notariée ; exe Windows non signé.

## Version précédente

La V4 (moteur PDF + planning + interface PySide6) reste disponible dans le tag
`v4.0.1` et dans la release `v4.0.1`. Pour la consulter :

```bash
git checkout v4.0.1
```

## Licence

MIT — voir [`LICENSE`](LICENSE).
