"""Rapports texte : refus, échec d'attribution, succès."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from .modele import Entree
from .solve import Resultat
from .sortie import date_min_max
from .validate import Lecture

TITRE = "RAD Gardes — V5"


def _entete(chemin: Path) -> list[str]:
    return [TITRE, f"Entrée : {chemin}", ""]


def _avertissements(lignes: list[str], avertissements: list[str]) -> None:
    if not avertissements:
        return
    lignes.append("")
    lignes.append("Avertissements (non bloquants) :")
    for message in avertissements:
        lignes.append(f"  - {message}")


def rapport_refus(chemin: Path, lecture: Lecture) -> str:
    lignes = _entete(chemin)
    lignes.append("REFUS — le classeur ne respecte pas le format attendu.")
    lignes.append("")
    lignes.append(f"{len(lecture.problemes)} problème(s) :")
    for numero, probleme in enumerate(lecture.problemes, start=1):
        lignes.append(f"  {numero}. {probleme}")
    _avertissements(lignes, lecture.avertissements)
    lignes += [
        "",
        "Aucun fichier n'a été écrit.",
        "Corrigez le classeur, puis relancez.",
        "Format attendu : voir README.md (ou le bouton « Modèle vierge »).",
    ]
    return "\n".join(lignes) + "\n"


def rapport_infaisable(chemin: Path, entree: Entree, message: str) -> str:
    lignes = _entete(chemin)
    lignes.append("ÉCHEC — aucune attribution exacte n'existe pour ces quotas.")
    lignes.append("")
    lignes.append(message)
    lignes.append("")
    lignes.append(
        f"Rappel : {entree.total} créneaux, {len(entree.jours)} date(s), "
        f"{len(entree.personnes)} personne(s)."
    )
    lignes += ["", "Aucun fichier n'a été écrit.", "Ajustez les dates ou les quotas, puis relancez."]
    return "\n".join(lignes) + "\n"


def rapport_succes(
    chemin: Path,
    entree: Entree,
    resultat: Resultat,
    xlsx: Path,
    texte: Path,
    avertissements: list[str] | None = None,
) -> str:
    total = entree.total
    attribues = len(resultat.attributions)
    taux = 100.0 * attribues / total if total else 0.0
    quotas = entree.quotas
    comptes = Counter(nom for _, nom in resultat.attributions)
    matins = Counter(nom for creneau, nom in resultat.attributions if creneau.moment == "Matin")
    soirs = Counter(nom for creneau, nom in resultat.attributions if creneau.moment == "Soir")
    respectes = sum(1 for nom, quota in quotas.items() if comptes[nom] == quota)

    lignes = _entete(chemin)
    lignes.append(f"Créneaux : {total} sur {len(entree.jours)} date(s) ({date_min_max(entree.jours)}).")
    lignes.append(f"Personnes : {len(entree.personnes)}.")
    lignes.append(
        "Quotas : "
        + " + ".join(str(personne.quota) for personne in entree.personnes)
        + f" = {sum(quotas.values())}."
    )
    lignes.append("")
    lignes.append("RÉSULTAT : OK")
    lignes.append(f"Taux de réussite : {taux:.0f} % ({attribues}/{total} créneaux attribués).")
    lignes.append(f"Quotas respectés : {respectes}/{len(quotas)} personnes.")
    lignes.append(f"Jours consécutifs : {resultat.paires_consecutives} paire(s).")
    lignes.append("")
    lignes.append("Détail par personne :")
    for personne in entree.personnes:
        lignes.append(
            f"  {personne.nom:<24} {comptes[personne.nom]:>2}/{personne.quota:<2} "
            f"(matins {matins[personne.nom]}, soirs {soirs[personne.nom]})"
        )
    _avertissements(lignes, avertissements or [])
    lignes += ["", "Fichiers écrits :", f"  {xlsx}", f"  {texte}"]
    return "\n".join(lignes) + "\n"
