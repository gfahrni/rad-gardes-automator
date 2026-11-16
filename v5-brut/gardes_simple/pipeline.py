"""Chaîne complète : lire → valider → attribuer → écrire (ou refuser)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .rapport import rapport_infaisable, rapport_refus, rapport_succes
from .solve import Infaisable, resoudre
from .sortie import ecrire_resultat, ecrire_texte
from .validate import lire

CODE_OK = 0
CODE_REFUS = 2
CODE_IMPOSSIBLE = 3


@dataclass
class Issue:
    """Résultat d'un traitement, prêt à afficher."""

    code: int
    rapport: str
    resume: str
    xlsx: Path | None = None
    texte: Path | None = None

    @property
    def ok(self) -> bool:
        return self.code == CODE_OK


def traiter(entree: str | Path, dossier: str | Path | None = None) -> Issue:
    """Traite un classeur. N'écrit rien si le classeur est refusé ou infaisable."""
    chemin = Path(entree)
    lecture = lire(chemin)
    if lecture.problemes or lecture.entree is None:
        nombre = len(lecture.problemes)
        return Issue(
            code=CODE_REFUS,
            rapport=rapport_refus(chemin, lecture),
            resume=f"REFUS — {nombre} problème(s) dans le classeur",
        )

    donnees = lecture.entree
    try:
        resultat = resoudre(donnees)
    except Infaisable as exc:
        return Issue(
            code=CODE_IMPOSSIBLE,
            rapport=rapport_infaisable(chemin, donnees, str(exc)),
            resume="ÉCHEC — quotas impossibles avec ces dates",
        )

    cible = Path(dossier) if dossier is not None else chemin.parent
    cible.mkdir(parents=True, exist_ok=True)
    xlsx = cible / f"{chemin.stem}-resultat.xlsx"
    texte = cible / f"{chemin.stem}-rapport.txt"
    ecrire_resultat(xlsx, donnees, resultat)
    rapport = rapport_succes(
        chemin, donnees, resultat, xlsx, texte, lecture.avertissements
    )
    ecrire_texte(texte, rapport)

    attribues = len(resultat.attributions)
    total = donnees.total
    return Issue(
        code=CODE_OK,
        rapport=rapport,
        resume=f"OK — {100 * attribues / total:.0f} % ({attribues}/{total} créneaux attribués)",
        xlsx=xlsx,
        texte=texte,
    )
