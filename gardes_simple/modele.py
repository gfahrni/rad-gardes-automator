"""Objets minimaux : créneaux à remplir et personnes avec leur quota."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

MOMENTS = ("Matin", "Soir")
RACCOURCIS = {"matin": "Matin", "soir": "Soir"}


def fmt(jour: date) -> str:
    """Date lisible et non ambiguë : 01.03.2027."""
    return jour.strftime("%d.%m.%Y")


@dataclass(frozen=True)
class Creneau:
    """Un créneau à remplir : une date et un moment (Matin ou Soir)."""

    jour: date
    moment: str

    @property
    def libelle(self) -> str:
        return f"{fmt(self.jour)} {self.moment}"


@dataclass(frozen=True)
class Personne:
    """Une personne et le nombre exact de gardes qu'elle doit faire."""

    nom: str
    quota: int


@dataclass
class Entree:
    """Contenu validé du classeur d'entrée."""

    creneaux: list[Creneau]
    personnes: list[Personne]

    @property
    def total(self) -> int:
        return len(self.creneaux)

    @property
    def jours(self) -> list[date]:
        return sorted({c.jour for c in self.creneaux})

    def creneaux_par_jour(self) -> dict[date, list[Creneau]]:
        groupe: dict[date, list[Creneau]] = {}
        for creneau in self.creneaux:
            groupe.setdefault(creneau.jour, []).append(creneau)
        return groupe

    @property
    def noms(self) -> list[str]:
        return [p.nom for p in self.personnes]

    @property
    def quotas(self) -> dict[str, int]:
        return {p.nom: p.quota for p in self.personnes}
