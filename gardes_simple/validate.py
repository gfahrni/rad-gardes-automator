"""Lecture et validation stricte du classeur d'entrée.

Règle du prototype : tout écart au format documenté est un **refus explicite**.
Le programme ne devine jamais, ne corrige jamais, ne complète jamais.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from .modele import RACCOURCIS, Creneau, Entree, Personne, fmt

FEUILLE_DATES = "Dates"
FEUILLE_PERSONNES = "Personnes"
FEUILLES_IGNOREES = {"Mode d'emploi"}
ENTETE_DATES = ("Date", "Créneau")
ENTETE_PERSONNES = ("Nom", "Gardes")
LIGNES_MAX = 5000


@dataclass
class Lecture:
    """Résultat d'une lecture : entrée valide, ou liste de problèmes."""

    entree: Entree | None = None
    problemes: list[str] = field(default_factory=list)
    avertissements: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.entree is not None and not self.problemes


def lire(chemin: str | Path) -> Lecture:
    """Lit le classeur et renvoie une entrée valide ou la liste des refus."""
    fichier = Path(chemin)
    if not fichier.exists():
        return Lecture(problemes=[f"Fichier introuvable : {fichier}"])
    if fichier.suffix.lower() != ".xlsx":
        return Lecture(
            problemes=[
                f"Extension attendue : « .xlsx » (trouvé « {fichier.suffix or 'aucune'} »)."
            ]
        )
    try:
        classeur = load_workbook(fichier, data_only=False)
    except Exception as exc:  # noqa: BLE001 — classeur corrompu, protégé, mauvais zip…
        return Lecture(problemes=[f"Classeur illisible : {exc}"])
    try:
        return _lire_classeur(classeur)
    finally:
        classeur.close()


def _lire_classeur(classeur) -> Lecture:
    noms = list(classeur.sheetnames)
    problemes: list[str] = []
    avertissements: list[str] = []

    for attendu in (FEUILLE_DATES, FEUILLE_PERSONNES):
        if attendu not in noms:
            problemes.append(
                f"Feuille « {attendu} » absente (feuilles trouvées : "
                f"{', '.join(f'« {n} »' for n in noms) or 'aucune'})."
            )
    if problemes:
        return Lecture(problemes=problemes, avertissements=avertissements)

    for nom in noms:
        if nom not in (FEUILLE_DATES, FEUILLE_PERSONNES) and nom not in FEUILLES_IGNOREES:
            avertissements.append(f"Feuille « {nom} » ignorée.")

    creneaux, pb, av = _lire_dates(classeur[FEUILLE_DATES])
    problemes += pb
    avertissements += av

    personnes, pb, av = _lire_personnes(classeur[FEUILLE_PERSONNES])
    problemes += pb
    avertissements += av

    if problemes:
        return Lecture(problemes=problemes, avertissements=avertissements)

    entree = Entree(creneaux=creneaux, personnes=personnes)
    pb, av = _verifier_coherence(entree)
    problemes += pb
    avertissements += av
    if problemes:
        return Lecture(entree=entree, problemes=problemes, avertissements=avertissements)
    return Lecture(entree=entree, avertissements=avertissements)


# --------------------------------------------------------------------------- #
# Feuilles
# --------------------------------------------------------------------------- #


def _lire_dates(feuille) -> tuple[list[Creneau], list[str], list[str]]:
    problemes: list[str] = []
    avertissements: list[str] = []
    _verifier_entete(feuille, ENTETE_DATES, FEUILLE_DATES, problemes)
    _verifier_colonnes(feuille, len(ENTETE_DATES), FEUILLE_DATES, problemes)
    if not _verifier_taille(feuille, FEUILLE_DATES, problemes):
        return [], problemes, avertissements

    creneaux: list[Creneau] = []
    vus: dict[tuple[date, str], int] = {}
    for ligne in _lignes_remplies(feuille, len(ENTETE_DATES)):
        numero = ligne[0].row
        jour = _jour(ligne[0], numero, problemes, avertissements)
        moment = _moment(ligne[1], numero, problemes)
        if jour is None or moment is None:
            continue
        cle = (jour, moment)
        if cle in vus:
            problemes.append(
                f"Dates, ligne {numero} : doublon {fmt(jour)} {moment} "
                f"(déjà déclaré ligne {vus[cle]})."
            )
            continue
        vus[cle] = numero
        creneaux.append(Creneau(jour=jour, moment=moment))

    if not creneaux and not problemes:
        problemes.append(
            "Feuille « Dates » : aucun créneau. Ajoutez une ligne par créneau "
            "(date + Matin/Soir)."
        )
    return creneaux, problemes, avertissements


def _lire_personnes(feuille) -> tuple[list[Personne], list[str], list[str]]:
    problemes: list[str] = []
    avertissements: list[str] = []
    _verifier_entete(feuille, ENTETE_PERSONNES, FEUILLE_PERSONNES, problemes)
    _verifier_colonnes(feuille, len(ENTETE_PERSONNES), FEUILLE_PERSONNES, problemes)
    if not _verifier_taille(feuille, FEUILLE_PERSONNES, problemes):
        return [], problemes, avertissements

    personnes: list[Personne] = []
    vus: dict[str, int] = {}
    for ligne in _lignes_remplies(feuille, len(ENTETE_PERSONNES)):
        numero = ligne[0].row
        nom_cellule, quota_cellule = ligne[0], ligne[1]
        nom = _texte(nom_cellule.value)
        if nom is None:
            problemes.append(f"Personnes, ligne {numero} : le nom est vide.")
            continue
        quota = _quota(quota_cellule, numero, problemes)
        if quota is None:
            continue
        cle = " ".join(nom.casefold().split())
        if cle in vus:
            problemes.append(
                f"Personnes, ligne {numero} : « {nom} » existe déjà "
                f"(ligne {vus[cle]})."
            )
            continue
        vus[cle] = numero
        personnes.append(Personne(nom=nom, quota=quota))

    if not personnes and not problemes:
        problemes.append(
            "Feuille « Personnes » : aucune personne. Ajoutez au moins un nom "
            "avec son nombre de gardes."
        )
    return personnes, problemes, avertissements


# --------------------------------------------------------------------------- #
# Cohérence globale
# --------------------------------------------------------------------------- #


def _verifier_coherence(entree: Entree) -> tuple[list[str], list[str]]:
    problemes: list[str] = []
    avertissements: list[str] = []

    total_creneaux = entree.total
    total_quotas = sum(p.quota for p in entree.personnes)
    if total_creneaux != total_quotas:
        ecart = total_creneaux - total_quotas
        if ecart > 0:
            detail = f"il manque {ecart} garde(s) dans la colonne « Gardes »"
        else:
            detail = f"{-ecart} garde(s) de trop dans la colonne « Gardes »"
        problemes.append(
            f"Somme des gardes ({total_quotas}) ≠ nombre de créneaux "
            f"({total_creneaux}) : {detail}."
        )

    jours = entree.jours
    par_jour = entree.creneaux_par_jour()
    for jour in jours:
        nombre = len(par_jour[jour])
        if nombre > len(entree.personnes):
            problemes.append(
                f"{fmt(jour)} : {nombre} créneaux pour {len(entree.personnes)} "
                "personne(s) — une personne ne peut pas faire deux gardes le même jour."
            )

    for personne in entree.personnes:
        if personne.quota > len(jours):
            problemes.append(
                f"« {personne.nom} » : {personne.quota} gardes demandées mais "
                f"seulement {len(jours)} dates (une garde maximum par jour)."
            )
        if personne.quota == 0:
            avertissements.append(
                f"« {personne.nom} » a 0 garde : cette personne ne sera jamais placée."
            )
    return problemes, avertissements


# --------------------------------------------------------------------------- #
# Cellules
# --------------------------------------------------------------------------- #


def _texte(valeur) -> str | None:
    if isinstance(valeur, str) and valeur.strip():
        return valeur.strip()
    return None


def _vide(valeur) -> bool:
    return valeur is None or (isinstance(valeur, str) and not valeur.strip())


def _formule(cellule) -> bool:
    return cellule.data_type == "f"


def _verifier_entete(feuille, attendus, nom_feuille, problemes: list[str]) -> None:
    for index, attendu in enumerate(attendus, start=1):
        valeur = _texte(feuille.cell(row=1, column=index).value)
        if valeur is None or valeur.casefold() != attendu.casefold():
            trouve = "vide" if valeur is None else f"« {valeur} »"
            problemes.append(
                f"{nom_feuille}, cellule {get_column_letter(index)}1 : en-tête "
                f"attendu « {attendu} », trouvé {trouve}."
            )


def _verifier_colonnes(feuille, nb_colonnes, nom_feuille, problemes: list[str]) -> None:
    if feuille.max_column <= nb_colonnes:
        return
    for ligne in feuille.iter_rows(
        min_row=1, min_col=nb_colonnes + 1, max_col=feuille.max_column
    ):
        for cellule in ligne:
            if not _vide(cellule.value):
                problemes.append(
                    f"{nom_feuille} : la colonne {cellule.column_letter} doit rester "
                    f"vide (trouvé « {cellule.value} » en {cellule.coordinate})."
                )
                return


def _verifier_taille(feuille, nom_feuille: str, problemes: list[str]) -> bool:
    if feuille.max_row > LIGNES_MAX:
        problemes.append(
            f"{nom_feuille} : trop de lignes ({feuille.max_row} > {LIGNES_MAX})."
        )
        return False
    return True


def _lignes_remplies(feuille, nb_colonnes):
    for ligne in feuille.iter_rows(
        min_row=2, max_row=feuille.max_row, max_col=nb_colonnes
    ):
        if all(_vide(cellule.value) for cellule in ligne):
            continue
        yield ligne


def _jour(cellule, numero: int, problemes: list[str], avertissements: list[str]) -> date | None:
    if _formule(cellule):
        problemes.append(
            f"Dates, ligne {numero} : la date ne doit pas être une formule."
        )
        return None
    valeur = cellule.value
    if valeur is None or (isinstance(valeur, str) and not valeur.strip()):
        problemes.append(f"Dates, ligne {numero} : la date est vide.")
        return None
    if isinstance(valeur, datetime):
        if valeur.time() != time(0, 0):
            avertissements.append(
                f"Dates, ligne {numero} : heure ignorée ({valeur:%H:%M})."
            )
        return valeur.date()
    if isinstance(valeur, date):
        return valeur
    if isinstance(valeur, (int, float)):
        problemes.append(
            f"Dates, ligne {numero} : nombre « {valeur} » au lieu d'une date — "
            "appliquez le format Date à la cellule."
        )
        return None
    problemes.append(
        f"Dates, ligne {numero} : « {valeur} » est du texte, pas une vraie date Excel — "
        "saisissez la date au format date (jj.mm.aaaa)."
    )
    return None


def _moment(cellule, numero: int, problemes: list[str]) -> str | None:
    if _formule(cellule):
        problemes.append(
            f"Dates, ligne {numero} : le créneau ne doit pas être une formule."
        )
        return None
    valeur = _texte(cellule.value)
    if valeur is None:
        problemes.append(
            f"Dates, ligne {numero} : le créneau est vide (attendu « Matin » ou « Soir »)."
        )
        return None
    moment = RACCOURCIS.get(valeur.casefold())
    if moment is None:
        problemes.append(
            f"Dates, ligne {numero} : créneau « {valeur} » invalide "
            "(attendu « Matin » ou « Soir »)."
        )
    return moment


def _quota(cellule, numero: int, problemes: list[str]) -> int | None:
    if _formule(cellule):
        problemes.append(
            f"Personnes, ligne {numero} : le nombre de gardes ne doit pas être une formule."
        )
        return None
    valeur = cellule.value
    if valeur is None or (isinstance(valeur, str) and not valeur.strip()):
        problemes.append(f"Personnes, ligne {numero} : le nombre de gardes est vide.")
        return None
    if isinstance(valeur, bool):
        problemes.append(
            f"Personnes, ligne {numero} : le nombre de gardes doit être un entier ≥ 0."
        )
        return None
    if isinstance(valeur, int):
        quota = valeur
    elif isinstance(valeur, float) and valeur.is_integer():
        quota = int(valeur)
    else:
        problemes.append(
            f"Personnes, ligne {numero} : « {valeur} » n'est pas un nombre entier."
        )
        return None
    if quota < 0:
        problemes.append(
            f"Personnes, ligne {numero} : le nombre de gardes est négatif ({quota})."
        )
        return None
    return quota
