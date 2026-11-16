"""Point d'entrée : interface graphique par défaut, ou traitement en ligne de commande."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import gabarit
from .pipeline import traiter


def _flux_surs() -> None:
    """En mode fenêtré (Windows), stdout/stderr valent None : on les neutralise."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115


def construire_analyseur() -> argparse.ArgumentParser:
    analyseur = argparse.ArgumentParser(
        prog="gardes_simple",
        description="Prototype V5 : attribution de gardes depuis un classeur Excel simple.",
    )
    analyseur.add_argument(
        "--entree", type=Path, help="classeur d'entrée à traiter (mode ligne de commande)"
    )
    analyseur.add_argument(
        "--sortie", type=Path, help="dossier de sortie (défaut : à côté de l'entrée)"
    )
    analyseur.add_argument(
        "--modele", type=Path, help="écrit un modèle vierge à ce chemin, puis s'arrête"
    )
    analyseur.add_argument("--gui", action="store_true", help="force l'interface graphique")
    return analyseur


def main(argv: list[str] | None = None) -> int:
    _flux_surs()
    arguments = construire_analyseur().parse_args(argv)

    if arguments.modele:
        try:
            chemin = gabarit.ecrire_modele(arguments.modele)
        except OSError as exc:
            print(f"Écriture impossible : {exc}", file=sys.stderr)
            return 1
        print(f"Modèle vierge écrit : {chemin}")
        return 0

    if arguments.gui:
        return _lancer_gui()

    if arguments.entree:
        try:
            issue = traiter(arguments.entree, arguments.sortie)
        except OSError as exc:
            print(f"Écriture impossible : {exc}", file=sys.stderr)
            print("Fermez le classeur s'il est ouvert dans Excel, puis relancez.", file=sys.stderr)
            return 1
        print(issue.rapport, end="")
        return issue.code

    return _lancer_gui()


def _lancer_gui() -> int:
    try:
        from . import gui
    except Exception as exc:  # noqa: BLE001 — tkinter absent (Python sans Tk)
        print(f"Interface indisponible : {exc}", file=sys.stderr)
        print("Utilisez : python3 -m gardes_simple --entree FICHIER.xlsx", file=sys.stderr)
        return 1
    return gui.main()
