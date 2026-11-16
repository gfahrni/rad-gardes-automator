# Prototype V5 « brut » — attribution de gardes

Prototype jetable, volontairement minimal : **un classeur Excel simple en entrée,
un classeur Excel simple en sortie, un rapport court**. Aucun PDF, aucun planning
existant, aucune reprise d'un planning précédent, pas de PySide6.

Deux consignes : **simplicité** et **robustesse**. Le programme ne devine rien :
si le classeur ne correspond pas exactement au format, il **refuse** et liste
les problèmes, sans rien écrire.

## Le format d'entrée (strict)

Un fichier `.xlsx` avec exactement deux feuilles utiles (une troisième,
« Mode d'emploi », est ignorée si elle existe).

**Feuille `Dates`** — une ligne par créneau à couvrir, à partir de la ligne 2 :

| A | B |
|---|---|
| `Date` | `Créneau` |
| 01.03.2027 | Matin |
| 01.03.2027 | Soir |

- `Date` : une **vraie date Excel** (format date), pas du texte ;
- `Créneau` : `Matin` ou `Soir` (liste déroulante dans le modèle).

**Feuille `Personnes`** — une ligne par personne :

| A | B |
|---|---|
| `Nom` | `Gardes` |
| Muller | 3 |
| Rossi | 2 |

- `Nom` : unique (comparaison sans tenir compte des majuscules ni des espaces
  multiples) ;
- `Gardes` : nombre **entier** ≥ 0. C'est le nombre **exact** de gardes de la
  personne.

Un bouton « Modèle vierge » (ou `--modele`) écrit ce classeur, en-têtes colorés,
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
autant que faire se peut, et, à la répartition près, évite le pire enchaînement
« Soir puis Matin le lendemain ».

## Utilisation

Depuis `v5-brut/` (Python 3.12, seule dépendance : `openpyxl`) :

```bash
python3 -m gardes_simple                                  # interface graphique
python3 -m gardes_simple --entree examples/gardes-in-demo.xlsx
python3 -m gardes_simple --modele gardes-in-vide.xlsx     # modèle vierge
```

Interface : choisir le fichier, « Lancer le calcul », le rapport s'affiche,
« Ouvrir le résultat » ouvre le classeur produit. Codes de sortie :
`0` succès, `2` refus, `3` quotas impossibles.

## Sorties

À côté du fichier d'entrée (ou dans `--sortie`) :

- `<nom>-resultat.xlsx` : feuille `Attribution` (Date, Créneau, Nom) et feuille
  `Synthèse` (prévu / attribué / écart / matins / soirs) ;
- `<nom>-rapport.txt` : le même rapport que dans l'interface, avec le taux de
  réussite.

```text
RÉSULTAT : OK
Taux de réussite : 100 % (8/8 créneaux attribués).
Quotas respectés : 4/4 personnes.
Jours consécutifs : 1 paire(s).
```

Ici la paire restante est inévitable : Muller doit 3 gardes sur 4 dates, donc
il travaille forcément deux jours voisins.

En cas de refus, **aucun fichier n'est écrit** :

```text
REFUS — le classeur ne respecte pas le format attendu.

2 problème(s) :
  1. Dates, ligne 4 : créneau « Matinée » invalide (attendu « Matin » ou « Soir »).
  2. Somme des gardes (7) ≠ nombre de créneaux (8) : il manque 1 garde
     dans la colonne « Gardes ».
```

## Contenu

```text
v5-brut/
├── gardes_simple/
│   ├── modele.py       # créneaux, personnes, quotas
│   ├── validate.py     # lecture et refus strict du classeur
│   ├── solve.py        # flot maximal + lissage des jours voisins
│   ├── sortie.py       # écriture atomique des classeurs
│   ├── rapport.py      # rapports texte (refus / échec / succès)
│   ├── gabarit.py      # modèle Excel vierge
│   ├── pipeline.py     # lire → valider → attribuer → écrire
│   ├── cli.py          # ligne de commande
│   └── gui.py          # interface tkinter
├── examples/
│   ├── creer_demo.py
│   ├── gardes-in-vide.xlsx
│   ├── gardes-in-demo.xlsx
│   ├── gardes-in-demo-resultat.xlsx
│   └── gardes-in-demo-rapport.txt
├── packaging/
│   ├── entree.py               # point d'entrée du binaire
│   ├── rad_gardes_v5.spec      # spec PyInstaller (.app / onedir)
│   ├── faire_icone.py          # icône PNG / ICNS / ICO
│   ├── build-macos.sh
│   ├── build-windows.ps1
│   └── LISEZ-MOI-*.txt
└── tests/test_prototype.py     # 30 tests
```

## Tests

```bash
cd v5-brut
python3 -m pytest -q     # ou : uv run --with pytest --with openpyxl python -m pytest -q
```

Les tests couvrent le cas nominal, chaque refus (en-tête, feuille, date, créneau,
doublon, somme, nom, extension), le solveur, le lissage, le CLI, le gabarit et
un passage complet par la fenêtre tkinter.

## Limites assumées du prototype

- Pas d'indisponibilités, pas de souhaits, pas de contrainte de repos
  obligatoire : seulement les quatre règles ci-dessus.
- Pas de verrouillage des affectations déjà validées ; chaque run repart de zéro.
- Quotas exacts : pas de « au moins » ni de « au plus ».
- L'interface ne montre pas le classeur : elle montre le rapport.

## Applications (macOS et Windows)

Le binaire embarque tout (Python, openpyxl, Tcl/Tk) : aucune installation.
Sans argument il ouvre l'interface ; avec `--entree` il traite un fichier.

### macOS

```bash
packaging/build-macos.sh          # → dist/RAD Gardes V5.app
```

- signature **ad-hoc** (pas d'identité développeur) : au premier lancement,
  si macOS bloque, clic droit sur l'app > « Ouvrir » ;
- construit sur ce Mac en **arm64** (Apple Silicon) ; pas de version Intel ;
- testé depuis le dossier construit : CLI (100 %, sorties écrites), refus
  (code 2, aucun fichier), modèle vierge, ouverture de la fenêtre.

Une copie de test prête à l'emploi est posée sur le Bureau :
`RAD Gardes V5 (test)/` avec l'app, `gardes-in-vide.xlsx`, `gardes-in-demo.xlsx`
et un mode d'emploi.

### Windows

PyInstaller **ne compile que sur sa propre plateforme** : l'exe Windows ne peut
pas être produit depuis ce Mac. Deux chemins, tous deux prêts :

1. **Sur un PC Windows** (Python 3.12 installé) :

   ```powershell
   .\packaging\build-windows.ps1
   # → dist\RAD-Gardes-V5-windows-x64.zip (onedir portable)
   ```

2. **Par GitHub Actions** : le workflow `.github/workflows/release-v5.yml`
   est présent sur `main` et sur la branche `v5-brut`. Lancer `release-v5`
   depuis l'onglet Actions en choisissant la branche `v5-brut`, ou pousser un
   tag `v5.0.0`. Le job `windows` exécute les tests, construit l'exe, vérifie
   qu'il produit bien `<nom>-resultat.xlsx`, puis zippe l'ensemble et
   l'attache à la release.

   L'app macOS n'est pas construite par la CI (les runners macOS ne sont pas
   disponibles ici) : elle se construit sur le Mac avec
   `packaging/build-macos.sh`.

L'archive Windows contient `RAD Gardes V5.exe`, ses dépendances, le classeur
vierge, l'exemple et un `LISEZ-MOI-windows.txt`.

## Relation avec la V4

Ce dossier est **isolé** : il ne touche ni `src/`, ni `tests/`, ni la CI de la
V4, et la V4 reste la version publiée. Pour en faire une branche :

```bash
git switch -c v5-brut   # depuis main, puis copier v5-brut/ et committer
```
