"""Écriture du classeur de sortie (feuilles « Attribution » et « Synthèse »)."""

from __future__ import annotations

import os
from collections import Counter
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from .modele import MOMENTS, Entree, fmt
from .solve import Resultat

ENTETE_FILL = PatternFill("solid", fgColor="1F3864")
ENTETE_POLICE = Font(bold=True, color="FFFFFF")
BORDURE = Border(bottom=Side(style="thin", color="BFBFBF"))


def ecrire_resultat(chemin: Path, entree: Entree, resultat: Resultat) -> None:
    """Écrit le classeur de façon atomique (jamais de fichier à moitié écrit)."""
    classeur = Workbook()
    _feuille_attribution(classeur.active, resultat)
    _feuille_synthese(classeur.create_sheet("Synthèse"), entree, resultat)
    temporaire = chemin.with_name(chemin.name + ".tmp")
    try:
        classeur.save(temporaire)
        os.replace(temporaire, chemin)
    finally:
        temporaire.unlink(missing_ok=True)


def _entetes(feuille, titres: tuple[str, ...], largeurs: tuple[int, ...]) -> None:
    for index, (titre, largeur) in enumerate(zip(titres, largeurs), start=1):
        cellule = feuille.cell(row=1, column=index, value=titre)
        cellule.fill = ENTETE_FILL
        cellule.font = ENTETE_POLICE
        cellule.alignment = Alignment(horizontal="center", vertical="center")
        feuille.column_dimensions[get_column_letter(index)].width = largeur
    feuille.freeze_panes = "A2"
    feuille.row_dimensions[1].height = 22


def _feuille_attribution(feuille, resultat: Resultat) -> None:
    feuille.title = "Attribution"
    _entetes(feuille, ("Date", "Créneau", "Nom"), (13, 11, 32))
    lignes = sorted(
        resultat.attributions,
        key=lambda couple: (couple[0].jour, MOMENTS.index(couple[0].moment)),
    )
    for numero, (creneau, nom) in enumerate(lignes, start=2):
        cellule_date = feuille.cell(row=numero, column=1, value=creneau.jour)
        cellule_date.number_format = "DD.MM.YYYY"
        feuille.cell(row=numero, column=2, value=creneau.moment)
        feuille.cell(row=numero, column=3, value=nom)
        for colonne in range(1, 4):
            feuille.cell(row=numero, column=colonne).border = BORDURE
    feuille.auto_filter.ref = f"A1:C{max(1, len(lignes) + 1)}"


def _feuille_synthese(feuille, entree: Entree, resultat: Resultat) -> None:
    _entetes(
        feuille,
        ("Nom", "Gardes prévues", "Attribuées", "Écart", "Matins", "Soirs"),
        (32, 16, 12, 8, 9, 9),
    )
    comptes = Counter(nom for _, nom in resultat.attributions)
    matins = Counter(nom for creneau, nom in resultat.attributions if creneau.moment == "Matin")
    soirs = Counter(nom for creneau, nom in resultat.attributions if creneau.moment == "Soir")
    for numero, personne in enumerate(entree.personnes, start=2):
        attribue = comptes[personne.nom]
        valeurs = (
            personne.nom,
            personne.quota,
            attribue,
            attribue - personne.quota,
            matins[personne.nom],
            soirs[personne.nom],
        )
        for colonne, valeur in enumerate(valeurs, start=1):
            cellule = feuille.cell(row=numero, column=colonne, value=valeur)
            cellule.border = BORDURE
            if colonne > 1:
                cellule.alignment = Alignment(horizontal="center")


def ecrire_texte(chemin: Path, texte: str) -> None:
    """Écrit un fichier texte de façon atomique."""
    temporaire = chemin.with_name(chemin.name + ".tmp")
    try:
        temporaire.write_text(texte, encoding="utf-8")
        os.replace(temporaire, chemin)
    finally:
        temporaire.unlink(missing_ok=True)


def date_min_max(jours: list[date]) -> str:
    if not jours:
        return "—"
    return f"{fmt(min(jours))} → {fmt(max(jours))}"
