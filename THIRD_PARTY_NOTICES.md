# Licences des composants tiers

RAD Gardes Automator est distribué sous licence MIT (voir [`LICENSE`](LICENSE)).
L'archive Windows `RAD-Gardes-Automator-windows-x64.zip` embarque les
composants ci-dessous. Tous sont compatibles avec une distribution MIT, à
l'exception de PySide6/Qt (LGPL-3.0), dont les obligations sont rappelées en
fin de document.

## Dépendances d'exécution

| Composant | Version | Licence | Usage |
|---|---|---|---|
| [OR-Tools](https://github.com/google/or-tools) | 9.15.6755 | Apache-2.0 | Solveur CP-SAT (étape 4) |
| [pdfplumber](https://github.com/jsvine/pdfplumber) | 0.11.10 | MIT | Extraction des mots et de leurs coordonnées dans le PDF (étape 1) |
| [pdfminer.six](https://github.com/pdfminer/pdfminer.six) | 20260107 | MIT | Moteur d'analyse PDF utilisé par pdfplumber |
| [pypdfium2](https://github.com/pypdfium2-team/pypdfium2) | 5.14.0 | Apache-2.0 / BSD-3-Clause | Rendu PDF (dépendance de pdfplumber) |
| [PDFium](https://pdfium.googlesource.com/pdfium/) | — | BSD-3-Clause | Moteur de rendu embarqué dans pypdfium2 |
| [Pillow](https://github.com/python-pillow/Pillow) | 13.0.0 | MIT-CMU (HPND) | Traitement d'images (dépendance de pdfplumber) |
| [cryptography](https://github.com/pyca/cryptography) | 50.0.2 | Apache-2.0 OR BSD-3-Clause | PDF chiffrés (dépendance de pdfminer.six) |
| [cffi](https://github.com/python-cffi/cffi) | 2.1.1 | MIT-0 | Dépendance de cryptography |
| [pycparser](https://github.com/eliben/pycparser) | 2.x | BSD-3-Clause | Dépendance de cffi |
| [charset-normalizer](https://github.com/jawah/charset_normalizer) | 3.5.2 | MIT | Détection d'encodage (dépendance de pdfminer.six) |
| [openpyxl](https://foss.heptapod.net/openpyxl/openpyxl) | 3.1.5 | MIT | Lecture/écriture des classeurs Excel |
| [et_xmlfile](https://foss.heptapod.net/openpyxl/et_xmlfile) | 2.x | MIT | Dépendance d'openpyxl |
| [PySide6 Essentials](https://code.qt.io/cgit/pyside/pyside-setup.git/) | 6.12.0 | **LGPL-3.0** | Interface graphique (Qt 6) |
| [shiboken6](https://code.qt.io/cgit/pyside/pyside-setup.git/) | 6.12.0 | **LGPL-3.0** | Bindings Python de Qt |
| [numpy](https://numpy.org) | 2.x | BSD-3-Clause | Dépendance d'OR-Tools |
| [protobuf](https://github.com/protocolbuffers/protobuf) | 6.x | BSD-3-Clause | Dépendance d'OR-Tools |
| [absl-py](https://github.com/abseil/abseil-py) | 2.x | Apache-2.0 | Dépendance d'OR-Tools |
| [immutabledict](https://github.com/corenting/immutabledict) | 4.x | MIT | Dépendance d'OR-Tools |
| [pandas](https://pandas.pydata.org) | 2.x | BSD-3-Clause | Dépendance d'OR-Tools |
| [python-dateutil](https://github.com/dateutil/dateutil) | 2.x | Apache-2.0 / BSD-3-Clause | Dépendance de pandas |
| [pytz](https://github.com/stub42/pytz) | 2025.x | MIT | Dépendance de pandas |
| [tzdata](https://github.com/python/tzdata) | 2025.x | Apache-2.0 | Données de fuseaux horaires |
| [six](https://github.com/benjaminp/six) | 1.17.0 | MIT | Dépendance de python-dateutil |

## Outil de construction (non distribué)

| Composant | Version | Licence |
|---|---|---|
| [PyInstaller](https://pyinstaller.org) | 6.16.0 | GPL-2.0-or-later **avec exception** autorisant la distribution de binaires propriétaires ou sous une autre licence |

## PyMuPDF — retiré

Les versions ≤ 4.0.0 utilisaient [PyMuPDF](https://github.com/pymupdf/PyMuPDF),
distribué sous **AGPL-3.0** (ou licence commerciale Artifex). L'embarquer dans
un exécutable Windows imposait de placer l'ensemble de l'application sous
AGPL-3.0. Depuis la version 4.0.1, l'étape 1 utilise `pdfplumber` (MIT) et
l'application reste entièrement distribuable sous MIT.

## PySide6 / Qt (LGPL-3.0)

PySide6 et Qt sont utilisés **non modifiés**, chargés dynamiquement depuis les
DLL de l'archive. L'archive `onedir` laisse ces DLL séparées et remplaçables :
l'utilisateur peut les substituer par sa propre version de Qt, ce qui satisfait
la clause de « recombinaison » de la LGPL-3.0.

Conformément à la LGPL-3.0 :

- le texte de la licence est fourni dans `licenses/LGPL-3.0.txt` de l'archive ;
- les sources de Qt/PySide6 sont disponibles sur
  <https://download.qt.io/official_releases/QtForPython/> et
  <https://code.qt.io/cgit/qt/> ;
- aucune modification n'est apportée à Qt ni à PySide6.

Un composant LGPL-3.0 peut être redistribué dans une application MIT : la
LGPL ne s'applique qu'à ce composant et à ses modifications éventuelles, pas
au code de l'application qui l'utilise via son API publique.
