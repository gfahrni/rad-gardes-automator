"""Gabarit Excel vierge à remplir à la main."""

from __future__ import annotations

import os
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from .validate import ENTETE_DATES, ENTETE_PERSONNES, FEUILLE_DATES, FEUILLE_PERSONNES

LIGNES_DATES = 200
LIGNES_PERSONNES = 60
FOND_ENTETE = PatternFill("solid", fgColor="1F3864")
POLICE_ENTETE = Font(bold=True, color="FFFFFF")

MODE_EMPLOI = (
    "Comment remplir ce classeur",
    "",
    "1. Feuille « Dates » : une ligne par créneau à couvrir.",
    "   - colonne A « Date » : une vraie date Excel (jj.mm.aaaa), pas du texte ;",
    "   - colonne B « Créneau » : Matin ou Soir (liste déroulante).",
    "",
    "2. Feuille « Personnes » : un nom par ligne.",
    "   - colonne A « Nom » : nom unique ;",
    "   - colonne B « Gardes » : nombre exact de gardes que la personne doit faire.",
    "",
    "3. Règles vérifiées par le programme :",
    "   - la somme des « Gardes » doit être exactement égale au nombre de lignes de « Dates » ;",
    "   - une personne ne peut pas faire Matin et Soir le même jour ;",
    "   - une personne ne peut pas faire deux gardes le même jour.",
    "",
    "4. Au moindre écart, le programme refuse et liste les problèmes :",
    "   il ne devine rien, ne corrige rien, ne complète rien.",
    "",
    "5. Lancer :",
    "   - interface : python3 -m gardes_simple",
    "   - ligne de commande : python3 -m gardes_simple --entree gardes-in.xlsx",
    "   - modèle vierge : python3 -m gardes_simple --modele gardes-in-vide.xlsx",
    "",
    "Cette feuille est ignorée par le programme.",
)


def ecrire_modele(
    chemin: str | Path,
    lignes_dates: int = LIGNES_DATES,
    lignes_personnes: int = LIGNES_PERSONNES,
) -> Path:
    """Écrit le gabarit et renvoie son chemin."""
    cible = Path(chemin)
    classeur = Workbook()

    feuille_dates = classeur.active
    feuille_dates.title = FEUILLE_DATES
    _entetes(feuille_dates, ENTETE_DATES, (14, 12))
    feuille_dates["A1"].comment = Comment(
        "Une vraie date Excel par ligne (format Date, jj.mm.aaaa).", "Prototype V5"
    )
    feuille_dates["B1"].comment = Comment(
        "Matin ou Soir. La liste déroulante est déjà posée sur la colonne.", "Prototype V5"
    )
    for ligne in range(2, lignes_dates + 2):
        feuille_dates.cell(row=ligne, column=1).number_format = "DD.MM.YYYY"
    valide_creneau = DataValidation(
        type="list", formula1='"Matin,Soir"', allow_blank=True, showErrorMessage=True
    )
    valide_creneau.error = "Choisissez Matin ou Soir."
    valide_creneau.errorTitle = "Créneau invalide"
    feuille_dates.add_data_validation(valide_creneau)
    valide_creneau.add(f"B2:B{lignes_dates + 1}")

    feuille_personnes = classeur.create_sheet(FEUILLE_PERSONNES)
    _entetes(feuille_personnes, ENTETE_PERSONNES, (32, 10))
    feuille_personnes["A1"].comment = Comment(
        "Un nom par ligne, sans doublon (majuscules et accents comparés).", "Prototype V5"
    )
    feuille_personnes["B1"].comment = Comment(
        "Nombre entier de gardes. La somme doit égaler le nombre de créneaux.", "Prototype V5"
    )
    valide_quota = DataValidation(
        type="whole", operator="between", formula1="0", formula2="999", allow_blank=True
    )
    valide_quota.error = "Entrez un nombre entier entre 0 et 999."
    valide_quota.errorTitle = "Nombre de gardes invalide"
    feuille_personnes.add_data_validation(valide_quota)
    valide_quota.add(f"B2:B{lignes_personnes + 1}")

    mode_emploi = classeur.create_sheet("Mode d'emploi")
    for numero, texte in enumerate(MODE_EMPLOI, start=1):
        cellule = mode_emploi.cell(row=numero, column=1, value=texte)
        if numero == 1:
            cellule.font = Font(bold=True, size=13)
    mode_emploi.column_dimensions["A"].width = 100

    temporaire = cible.with_name(cible.name + ".tmp")
    try:
        classeur.save(temporaire)
        os.replace(temporaire, cible)
    finally:
        temporaire.unlink(missing_ok=True)
    return cible


def _entetes(feuille, titres: tuple[str, ...], largeurs: tuple[int, ...]) -> None:
    for index, (titre, largeur) in enumerate(zip(titres, largeurs), start=1):
        cellule = feuille.cell(row=1, column=index, value=titre)
        cellule.fill = FOND_ENTETE
        cellule.font = POLICE_ENTETE
        cellule.alignment = Alignment(horizontal="center", vertical="center")
        feuille.column_dimensions[cellule.column_letter].width = largeur
    feuille.freeze_panes = "A2"
    feuille.row_dimensions[1].height = 22
