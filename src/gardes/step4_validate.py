from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict
from typing import Any

from .errors import GardesError
from .models import Person, person_from_dict


def as_date(value: Any) -> dt.date:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    return dt.date.fromisoformat(str(value))


def day_map(planning: dict) -> dict[dt.date, dict]:
    return {as_date(d["date"]): d for d in planning["days"]}


def status_map(wishes: dict) -> dict[tuple[str, dt.date], str]:
    out: dict[tuple[str, dt.date], str] = {}
    for person in wishes["people"]:
        for entry in person["statuses"]:
            out[(person["name"], as_date(entry["date"]))] = entry["status"]
    return out


def candidate_people(calcul: dict) -> list[Person]:
    people = [person_from_dict(p) for p in calcul["people"]]
    return [p for p in people if p.is_candidate]


def base_work(person: Person, date: dt.date, days: dict[dt.date, dict], statuses: dict) -> int:
    if not (person.active_from <= date <= person.active_to):
        return 0
    day = days.get(date)
    if day is None:
        return 0
    if day["category"] != "workday":
        return 0
    if statuses.get((person.name, date), "neutral") == "vacation":
        return 0
    return 1


def window_starts(start: dt.date, end: dt.date) -> list[dt.date]:
    return [start + dt.timedelta(days=k) for k in range(-6, (end - start).days + 1)]


def validate_inputs(calcul: dict, planning: dict, wishes: dict) -> None:
    if not calcul.get("validated"):
        raise GardesError(
            "calcul-gardes.json n'est pas validé. Lance step1-validate après relecture.",
            code="calcul_not_validated",
        )
    p1 = calcul["period"]
    p2 = planning["period"]
    p3 = wishes["period"]
    if (p1["start"], p1["end"]) != (p2["start"], p2["end"]) or (
        p1["start"],
        p1["end"],
    ) != (p3["start"], p3["end"]):
        raise GardesError(
            "Les trois JSON ne concernent pas la même période.", code="period_mismatch"
        )
    people = [person_from_dict(p) for p in calcul["people"]]
    by_name = {p.name: p for p in people}
    if len(by_name) != len(people):
        raise GardesError("Noms en doublon dans calcul-gardes.json.", code="calcul_duplicate")
    candidates = [p for p in people if p.is_candidate]
    if not candidates:
        raise GardesError("Aucun candidat assignable.", code="no_candidate")

    slots = planning["slots"]
    holes = [s for s in slots if s["status"] == "hole"]
    fixed = [s for s in slots if s["status"] == "fixed"]
    if len({s["id"] for s in slots}) != len(slots):
        raise GardesError("Slots en doublon dans le planning.", code="slot_duplicate")
    if len({(as_date(s["date"]), s["role"]) for s in slots}) != len(slots):
        raise GardesError("Deux slots pour la même date/créneau.", code="slot_duplicate")
    for slot in slots:
        if slot["category"] not in ("weekend", "ferie"):
            raise GardesError(
                f"Catégorie invalide pour {slot['id']}: {slot['category']}.", code="slot_category"
            )
        if slot["role"] not in ("day", "evening"):
            raise GardesError(f"Rôle invalide pour {slot['id']}: {slot['role']}.", code="slot_role")
    for slot in fixed:
        if not slot.get("fixed_name"):
            raise GardesError(f"Cellule fixe sans nom : {slot['id']}.", code="fixed_without_name")
        if slot["fixed_name"] in {p.name for p in candidates}:
            raise GardesError(
                f"Contradiction : {slot['fixed_name']} est à la fois fixe et candidat.",
                code="fixed_candidate",
            )

    wish_people = {p["name"] for p in wishes["people"]}
    unknown = wish_people - set(by_name)
    if unknown:
        raise GardesError(f"Noms inconnus dans les souhaits : {sorted(unknown)}", code="wishes_unknown_name")
    missing = [p.name for p in candidates if p.name not in wish_people]
    if missing:
        raise GardesError(
            f"Candidats sans souhaits : {missing}.", code="wishes_missing_candidate"
        )
    statuses = status_map(wishes)
    for p in candidates:
        if not any((p.name, as_date(d["date"])) in statuses for d in planning["days"]):
            raise GardesError(f"Aucun statut de souhait pour {p.name}.", code="wishes_missing_status")


def validate_attribution(calcul: dict, planning: dict, wishes: dict, attribution: dict) -> None:
    """Validateur indépendant : ne recalcule rien depuis le modèle CP-SAT."""
    validate_inputs(calcul, planning, wishes)
    errors: list[str] = []
    people = [person_from_dict(p) for p in calcul["people"]]
    by_name = {p.name: p for p in people}
    candidates = {p.name: p for p in people if p.is_candidate}
    days = day_map(planning)
    statuses = status_map(wishes)
    holes = {s["id"]: s for s in planning["slots"] if s["status"] == "hole"}
    fixed = {s["id"]: s for s in planning["slots"] if s["status"] == "fixed"}

    assignments = attribution.get("assignments", [])
    empty = attribution.get("empty_holes", [])
    assigned_holes: set[str] = set()
    by_person_date: dict[tuple[str, dt.date], list[str]] = defaultdict(list)
    by_person_cat: Counter[tuple[str, str]] = Counter()
    red_count = 0
    green_count = 0
    for a in assignments:
        hid = a["hole_id"]
        if hid in assigned_holes:
            errors.append(f"Trou {hid} affecté deux fois.")
            continue
        assigned_holes.add(hid)
        slot = holes.get(hid)
        if slot is None:
            errors.append(f"Affectation sur un trou inconnu : {hid}.")
            continue
        if as_date(slot["date"]) != as_date(a["date"]) or slot["role"] != a["slot"]:
            errors.append(f"Date/créneau incohérents pour {hid}.")
        if slot["category"] != a["category"]:
            errors.append(f"Catégorie incohérente pour {hid}.")
        person = a["person"]
        if person not in by_name:
            errors.append(f"Personne inconnue : {person}.")
            continue
        if person not in candidates:
            errors.append(f"Personne non assignable affectée : {person}.")
        p = by_name.get(person)
        if p is not None:
            date = as_date(a["date"])
            if not (p.active_from <= date <= p.active_to):
                errors.append(f"{person} affecté hors activité le {date}.")
            if statuses.get((person, date)) == "vacation":
                errors.append(f"{person} affecté en vacances le {date}.")
            by_person_date[(person, date)].append(hid)
            by_person_cat[(person, a["category"])] += 1
            st = statuses.get((person, date), "neutral")
            if bool(a.get("forced_red")) != (st == "non_dispo"):
                errors.append(f"forced_red incohérent pour {hid} / {person}.")
            if st == "non_dispo":
                red_count += 1
            if st == "volunteer":
                green_count += 1
    for key, values in by_person_date.items():
        if len(values) > 1:
            errors.append(f"{key[0]} a deux gardes le {key[1]}.")
    for person, p in candidates.items():
        for cat, quota in (("weekend", p.weekend_quota), ("ferie", p.holiday_quota)):
            if by_person_cat[(person, cat)] > quota:
                errors.append(
                    f"Quota {cat} dépassé pour {person} : {by_person_cat[(person, cat)]} > {quota}."
                )

    # Règle des 6 jours.
    for person, p in candidates.items():
        for start in window_starts(as_date(calcul["period"]["start"]), as_date(calcul["period"]["end"])):
            window = {start + dt.timedelta(days=k) for k in range(7)}
            base = sum(base_work(p, d, days, statuses) for d in window)
            assigned = sum(
                1
                for (name, d), _ in by_person_date.items()
                if name == person and d in window
            )
            if base + assigned > 6:
                errors.append(
                    f"Règle des 6 jours violée pour {person} sur {start}..{start + dt.timedelta(days=6)} "
                    f"({base + assigned} jours travaillés)."
                )
                break

    # Couverture et compteurs.
    if assigned_holes | {h["hole_id"] for h in empty} != set(holes):
        errors.append("Les affectations + trous vides ne couvrent pas exactement tous les trous.")
    if assigned_holes & {h["hole_id"] for h in empty}:
        errors.append("Un trou est à la fois affecté et vide.")
    if any(h["hole_id"] in fixed for h in empty):
        errors.append("Un trou vide référence une cellule fixe.")

    counts = attribution.get("counts", {})
    expected_counts = {
        "holes": len(holes),
        "filled": len(assignments),
        "empty": len(empty),
        "fixed": len(fixed),
        "weekend_holes": sum(1 for s in holes.values() if s["category"] == "weekend"),
        "ferie_holes": sum(1 for s in holes.values() if s["category"] == "ferie"),
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            errors.append(f"Compteur {key} : {counts.get(key)} != {expected}.")
    objective = attribution.get("objective", {})
    if objective.get("coverage") != len(assignments):
        errors.append("objectif.coverage incohérent.")
    if objective.get("red_forced") != red_count:
        errors.append("objectif.red_forced incohérent.")
    if objective.get("green") != green_count:
        errors.append("objectif.green incohérent.")
    red_forced = attribution.get("red_forced", [])
    if len(red_forced) != red_count:
        errors.append("red_forced ne correspond pas aux affectations rouges.")

    # Quotas restants.
    quotas = {q["person"]: q for q in attribution.get("quotas", [])}
    if set(quotas) != set(candidates):
        errors.append("La liste des quotas ne correspond pas aux candidats.")
    for person, p in candidates.items():
        q = quotas.get(person)
        if q is None:
            continue
        for cat, initial in (("weekend", p.weekend_quota), ("ferie", p.holiday_quota)):
            assigned = by_person_cat[(person, cat)]
            block = q.get(cat, {})
            if (
                block.get("initial") != initial
                or block.get("assigned") != assigned
                or block.get("remaining") != initial - assigned
            ):
                errors.append(f"Quota {cat} incohérent pour {person}.")

    if errors:
        raise GardesError(
            "Validation indépendante échouée :\n- " + "\n- ".join(errors),
            code="attribution_invalid",
            details={"errors": errors},
        )
