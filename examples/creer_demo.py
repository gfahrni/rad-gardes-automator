"""Régénère le classeur d'exemple et le modèle vierge de la V5.

Usage (depuis la racine du dépôt) : python3 examples/creer_demo.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from openpyxl import Workbook

from gardes_simple import gabarit

DOSSIER = Path(__file__).resolve().parent
DATES = [date(2027, 3, 1), date(2027, 3, 2), date(2027, 3, 6), date(2027, 3, 7)]
PERSONNES = [("Muller", 3), ("Rossi", 2), ("Dupont", 2), ("Keller", 1)]


def main() -> None:
    gabarit.ecrire_modele(DOSSIER / "gardes-in-vide.xlsx")

    classeur = Workbook()
    dates = classeur.active
    dates.title = "Dates"
    dates.append(["Date", "Créneau"])
    for jour in DATES:
        for moment in ("Matin", "Soir"):
            dates.append([jour, moment])
    for ligne in range(2, len(DATES) * 2 + 2):
        dates.cell(row=ligne, column=1).number_format = "DD.MM.YYYY"

    personnes = classeur.create_sheet("Personnes")
    personnes.append(["Nom", "Gardes"])
    for nom, quota in PERSONNES:
        personnes.append([nom, quota])

    classeur.save(DOSSIER / "gardes-in-demo.xlsx")
    print("Écrit : gardes-in-vide.xlsx, gardes-in-demo.xlsx")


if __name__ == "__main__":
    main()
