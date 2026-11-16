"""Attribution exacte des créneaux : flot maximal, puis lissage des jours voisins.

Contraintes (dures) :
- chaque créneau reçoit exactement une personne ;
- chaque personne fait exactement le nombre de gardes de la colonne « Gardes » ;
- une personne au maximum une garde par date.

Le problème est un b-matching biparti : un flot entier le résout en temps
polynomial, donc pas de recherche arborescente qui explose. Ensuite une passe
déterministe de permutations cherche à casser les gardes sur deux jours
consécutifs (repos), sans jamais changer les quotas.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import date, timedelta

from .modele import MOMENTS, Creneau, Entree

UN_JOUR = timedelta(days=1)


class Infaisable(Exception):
    """Les quotas ne peuvent pas être satisfaits avec ces dates."""


@dataclass
class Resultat:
    """Attribution retenue."""

    attributions: list[tuple[Creneau, str]]
    paires_consecutives: int
    jours_par_personne: dict[str, list[date]]


# --------------------------------------------------------------------------- #
# Flot maximal (Dinic, entier)
# --------------------------------------------------------------------------- #


class _Flot:
    def __init__(self, taille: int) -> None:
        self.g: list[list[list[int]]] = [[] for _ in range(taille)]

    def arete(self, u: int, v: int, capacite: int) -> tuple[int, int]:
        iu, iv = len(self.g[u]), len(self.g[v])
        self.g[u].append([v, capacite, iv])
        self.g[v].append([u, 0, iu])
        return (u, iu)

    def flux(self, arete: tuple[int, int]) -> int:
        u, iu = arete
        v, _, iv = self.g[u][iu]
        return self.g[v][iv][1]

    def max_flux(self, source: int, puits: int) -> int:
        total = 0
        while True:
            niveau = [-1] * len(self.g)
            niveau[source] = 0
            file = deque([source])
            while file:
                u = file.popleft()
                for v, capacite, _ in self.g[u]:
                    if capacite > 0 and niveau[v] < 0:
                        niveau[v] = niveau[u] + 1
                        file.append(v)
            if niveau[puits] < 0:
                return total
            curseur = [0] * len(self.g)
            while True:
                pousse = self._pousser(source, puits, 10**9, niveau, curseur)
                if not pousse:
                    break
                total += pousse

    def _pousser(self, u: int, puits: int, limite: int, niveau, curseur) -> int:
        if u == puits:
            return limite
        aretes = self.g[u]
        while curseur[u] < len(aretes):
            arete = aretes[curseur[u]]
            v, capacite, inverse = arete
            if capacite > 0 and niveau[v] == niveau[u] + 1:
                pousse = self._pousser(
                    v, puits, min(limite, capacite), niveau, curseur
                )
                if pousse:
                    arete[1] -= pousse
                    self.g[v][inverse][1] += pousse
                    return pousse
            curseur[u] += 1
        return 0


# --------------------------------------------------------------------------- #
# Résolution
# --------------------------------------------------------------------------- #


def resoudre(entree: Entree, lisser: bool = True) -> Resultat:
    """Renvoie l'attribution exacte, ou lève :class:`Infaisable`."""
    noms = entree.noms
    quotas = entree.quotas
    jours = entree.jours
    par_jour = entree.creneaux_par_jour()

    base_jour = 1
    base_personne = base_jour + len(jours)
    source = 0
    puits = base_personne + len(noms)
    flot = _Flot(puits + 1)

    for index, jour in enumerate(jours):
        flot.arete(source, base_jour + index, len(par_jour[jour]))

    aretes: dict[tuple[int, int], tuple[int, int]] = {}
    for index in range(len(jours)):
        for index_personne in range(len(noms)):
            aretes[(index, index_personne)] = flot.arete(
                base_jour + index, base_personne + index_personne, 1
            )
    for index_personne, nom in enumerate(noms):
        flot.arete(base_personne + index_personne, puits, quotas[nom])

    debit = flot.max_flux(source, puits)
    if debit != entree.total:
        manquants = entree.total - debit
        satures = [nom for nom in noms if quotas[nom] >= len(jours)]
        detail = ""
        if satures:
            detail = (
                " Personnes déjà au maximum (une garde par date) : "
                + ", ".join(satures)
                + "."
            )
        raise Infaisable(
            f"Attribution exacte impossible : {manquants} créneau(x) sur "
            f"{entree.total} ne peuvent pas être placés sans dépasser un quota."
            f"{detail} Ajoutez des dates, ou réduisez un quota."
        )

    plan: dict[str, set[date]] = {nom: set() for nom in noms}
    for index, jour in enumerate(jours):
        for index_personne, nom in enumerate(noms):
            if flot.flux(aretes[(index, index_personne)]) == 1:
                plan[nom].add(jour)

    if lisser:
        _lisser(plan)

    attributions = _attributions(entree, plan)
    return Resultat(
        attributions=attributions,
        paires_consecutives=sum(_paires(jours_du_nom) for jours_du_nom in plan.values()),
        jours_par_personne={nom: sorted(jours_du_nom) for nom, jours_du_nom in plan.items()},
    )


def _attributions(
    entree: Entree, plan: dict[str, set[date]]
) -> list[tuple[Creneau, str]]:
    """Place les noms sur Matin/Soir.

    Priorité au matin : une personne qui a fait le soir la veille n'est prise
    qu'en dernier recours. Ensuite on équilibre le nombre de matins.
    """
    par_jour = entree.creneaux_par_jour()
    matins = {nom: 0 for nom in entree.noms}
    soirs_veille: dict[date, set[str]] = {}
    resultat: list[tuple[Creneau, str]] = []
    for jour in entree.jours:
        creneaux = sorted(par_jour[jour], key=lambda c: MOMENTS.index(c.moment))
        veille = soirs_veille.get(jour - UN_JOUR, set())
        presents = sorted(
            (nom for nom in entree.noms if jour in plan[nom]),
            key=lambda nom: (nom in veille, matins[nom], nom),
        )
        if len(presents) != len(creneaux):  # défense : ne devrait jamais arriver
            raise Infaisable(
                f"Incohérence interne le {jour} : {len(presents)} personne(s) "
                f"pour {len(creneaux)} créneau(x)."
            )
        du_jour: list[tuple[Creneau, str]] = []
        for creneau, nom in zip(creneaux, presents):
            du_jour.append((creneau, nom))
            resultat.append((creneau, nom))
            if creneau.moment == "Matin":
                matins[nom] += 1
        soirs_veille[jour] = {nom for creneau, nom in du_jour if creneau.moment == "Soir"}
    return resultat


# --------------------------------------------------------------------------- #
# Lissage : éviter deux jours consécutifs pour la même personne
# --------------------------------------------------------------------------- #


def _paires(jours_du_nom: set[date]) -> int:
    return sum(1 for jour in jours_du_nom if jour + UN_JOUR in jours_du_nom)


def _voisin(jours_du_nom: set[date], jour: date) -> bool:
    return (jour - UN_JOUR) in jours_du_nom or (jour + UN_JOUR) in jours_du_nom


def _lisser(plan: dict[str, set[date]], iterations_max: int = 500) -> int:
    """Échange des dates entre deux personnes pour casser les jours voisins."""
    echanges = 0
    for _ in range(iterations_max):
        trouve = False
        for a in sorted(plan):
            for jour_a in sorted(plan[a]):
                if not _voisin(plan[a], jour_a):
                    continue
                for b in sorted(plan):
                    if b == a:
                        continue
                    for jour_b in sorted(plan[b]):
                        if jour_b == jour_a or not _voisin(plan[b], jour_b):
                            continue
                        if jour_b in plan[a] or jour_a in plan[b]:
                            continue
                        avant = _paires(plan[a]) + _paires(plan[b])
                        nouveau_a = (plan[a] - {jour_a}) | {jour_b}
                        nouveau_b = (plan[b] - {jour_b}) | {jour_a}
                        apres = _paires(nouveau_a) + _paires(nouveau_b)
                        if apres < avant:
                            plan[a], plan[b] = nouveau_a, nouveau_b
                            echanges += 1
                            trouve = True
                            break
                    if trouve:
                        break
                if trouve:
                    break
            if trouve:
                break
        if not trouve:
            break
    return echanges
