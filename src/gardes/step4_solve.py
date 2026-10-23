from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import ortools
from ortools.sat.python import cp_model

from .errors import GardesError
from .jsonio import sha256_file
from .models import Person, person_from_dict, slot_id
from .step4_validate import (
    as_date,
    base_work,
    candidate_people,
    day_map,
    status_map,
    validate_attribution,
    validate_inputs,
    window_starts,
)

ROLE_ORDER = {"day": 0, "evening": 1}


def _input_block(path: str | Path | None) -> dict:
    if path is None:
        return {"path": None, "sha256": None}
    p = Path(path)
    return {"path": str(p.resolve()), "sha256": sha256_file(p) if p.exists() else None}


def _status(solver: cp_model.CpSolver, status: int) -> str:
    return solver.StatusName(status)


def _solve(model: cp_model.CpModel, *, time_limit: float) -> tuple[cp_model.CpSolver, int]:
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.log_search_progress = False
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        name = _status(solver, status)
        raise GardesError(
            f"CP-SAT n'a pas trouvé de solution (statut {name}). "
            "Vérifie les données ou augmente le temps limite.",
            code="solver_no_solution",
            details={"status": name},
        )
    return solver, status


def solve_attribution(
    calcul: dict,
    planning: dict,
    wishes: dict,
    *,
    input_paths: dict[str, str | Path] | None = None,
    time_limit: float = 60.0,
) -> dict:
    validate_inputs(calcul, planning, wishes)
    people = [person_from_dict(p) for p in calcul["people"]]
    candidates = [p for p in people if p.is_candidate]
    days = day_map(planning)
    statuses = status_map(wishes)
    period_start = as_date(calcul["period"]["start"])
    period_end = as_date(calcul["period"]["end"])
    holes = sorted(
        [s for s in planning["slots"] if s["status"] == "hole"],
        key=lambda s: (as_date(s["date"]), ROLE_ORDER[s["role"]]),
    )
    fixed = [s for s in planning["slots"] if s["status"] == "fixed"]
    fixed_names = {s.get("fixed_name") for s in fixed}
    if not fixed_names:
        raise GardesError("Aucun pré-rempli dans le planning.", code="empty_planning")

    # Pré-calcul du calendrier de travail et des fenêtres de 7 jours.
    base = {
        (p.name, d): base_work(p, d, days, statuses)
        for p in candidates
        for d in days
    }
    starts = window_starts(period_start, period_end)
    base_sums: dict[tuple[str, dt.date], int] = {}
    for p in candidates:
        for start in starts:
            window = {start + dt.timedelta(days=k) for k in range(7)}
            total = sum(base.get((p.name, d), 0) for d in window)
            if total > 6:
                raise GardesError(
                    f"Incohérence de calendrier pour {p.name} sur {start} : "
                    f"{total} jours travaillés hors gardes.",
                    code="base_work_overflow",
                )
            base_sums[(p.name, start)] = total

    model = cp_model.CpModel()
    hole_by_id = {h["id"]: h for h in holes}
    hidx = {h["id"]: i for i, h in enumerate(holes)}
    pidx = {p.name: i for i, p in enumerate(candidates)}
    x: dict[tuple[str, str], cp_model.IntVar] = {}
    for h in holes:
        date = as_date(h["date"])
        for p in candidates:
            if not (p.active_from <= date <= p.active_to):
                continue
            if statuses.get((p.name, date)) == "vacation":
                continue
            if p.quota(h["category"]) <= 0:
                continue
            x[(h["id"], p.name)] = model.NewBoolVar(f"x_{hidx[h['id']]}_{pidx[p.name]}")

    # 6.1 : un seul radiologue par trou.
    for h in holes:
        terms = [x[(h["id"], p.name)] for p in candidates if (h["id"], p.name) in x]
        if terms:
            model.Add(sum(terms) <= 1)

    # 6.2 : une seule garde par personne et par jour.
    for p in candidates:
        for date in days:
            terms = [
                x[(h["id"], p.name)]
                for h in holes
                if as_date(h["date"]) == date and (h["id"], p.name) in x
            ]
            if terms:
                model.Add(sum(terms) <= 1)

    # 6.3 : quotas par catégorie.
    for p in candidates:
        for cat, quota in (("weekend", p.weekend_quota), ("ferie", p.holiday_quota)):
            terms = [
                x[(h["id"], p.name)]
                for h in holes
                if h["category"] == cat and (h["id"], p.name) in x
            ]
            if terms:
                model.Add(sum(terms) <= quota)

    # 6.4 : règle des 6 jours, fenêtres de 7 jours.
    for p in candidates:
        for start in starts:
            window = {start + dt.timedelta(days=k) for k in range(7)}
            terms = [
                x[(h["id"], p.name)]
                for h in holes
                if as_date(h["date"]) in window and (h["id"], p.name) in x
            ]
            if terms:
                model.Add(sum(terms) <= 6 - base_sums[(p.name, start)])

    red_terms: list[cp_model.IntVar] = []
    green_terms: list[cp_model.IntVar] = []
    for (hid, name), var in x.items():
        date = as_date(hole_by_id[hid]["date"])
        st = statuses.get((name, date), "neutral")
        if st == "non_dispo":
            red_terms.append(var)
        elif st == "volunteer":
            green_terms.append(var)
    red_expr = sum(red_terms)
    green_expr = sum(green_terms)

    wall_time = 0.0
    statuses_solves: list[str] = []
    if x:
        model.Maximize(sum(x.values()))
        solver1, status1 = _solve(model, time_limit=time_limit)
        wall_time += solver1.WallTime()
        statuses_solves.append(_status(solver1, status1))
        coverage = int(round(solver1.ObjectiveValue()))
        model.Add(sum(x.values()) == coverage)
        model.ClearObjective()
        model.Minimize(red_expr)
        solver2, status2 = _solve(model, time_limit=time_limit)
        wall_time += solver2.WallTime()
        statuses_solves.append(_status(solver2, status2))
        red_min = int(round(solver2.ObjectiveValue()))
        model.Add(red_expr == red_min)
        model.ClearObjective()
        model.Maximize(green_expr)
        solver3, status3 = _solve(model, time_limit=time_limit)
        wall_time += solver3.WallTime()
        statuses_solves.append(_status(solver3, status3))
        green_max = int(round(solver3.ObjectiveValue()))
        selected = {
            (hid, name)
            for (hid, name), var in x.items()
            if solver3.Value(var) == 1
        }
    else:
        coverage = red_min = green_max = 0
        selected = set()
        statuses_solves = ["OPTIMAL"]

    # Vérifie que l'objectif vert annoncé correspond aux affectations extraites.
    selected_by_hole = {hid: name for hid, name in selected}
    assignments: list[dict] = []
    by_person_date: dict[str, set[dt.date]] = defaultdict(set)
    by_person_cat: Counter[tuple[str, str]] = Counter()
    for h in holes:
        hid = h["id"]
        person = selected_by_hole.get(hid)
        if person is None:
            continue
        date = as_date(h["date"])
        st = statuses.get((person, date), "neutral")
        assignments.append(
            {
                "hole_id": hid,
                "date": date.isoformat(),
                "slot": h["role"],
                "category": h["category"],
                "person": person,
                "forced_red": st == "non_dispo",
                "cell": h["cell"],
            }
        )
        by_person_date[person].add(date)
        by_person_cat[(person, h["category"])] += 1

    red_forced = [
        {
            "hole_id": a["hole_id"],
            "date": a["date"],
            "slot": a["slot"],
            "person": a["person"],
            "reason": "rouge retenu pour maximiser la couverture",
        }
        for a in assignments
        if a["forced_red"]
    ]

    empty_holes: list[dict] = []
    for h in holes:
        if h["id"] in selected_by_hole:
            continue
        date = as_date(h["date"])
        cat = h["category"]
        reasons: list[dict] = []
        for p in candidates:
            if not (p.active_from <= date <= p.active_to):
                reasons.append({"person": p.name, "reason": "outside_activity"})
                continue
            if statuses.get((p.name, date)) == "vacation":
                reasons.append({"person": p.name, "reason": "vacation"})
                continue
            if p.quota(cat) <= 0:
                reasons.append({"person": p.name, "reason": "category_quota_zero"})
                continue
            if by_person_cat[(p.name, cat)] >= p.quota(cat):
                reasons.append({"person": p.name, "reason": "quota_exhausted"})
                continue
            if date in by_person_date[p.name]:
                reasons.append({"person": p.name, "reason": "already_on_duty"})
                continue
            violated = None
            for start in starts:
                window = {start + dt.timedelta(days=k) for k in range(7)}
                if date not in window:
                    continue
                assigned_in_window = sum(
                    1 for a in assignments if a["person"] == p.name and as_date(a["date"]) in window
                )
                if base_sums[(p.name, start)] + assigned_in_window + 1 > 6:
                    violated = (start.isoformat(), (start + dt.timedelta(days=6)).isoformat())
                    break
            if violated:
                reasons.append(
                    {
                        "person": p.name,
                        "reason": "six_day_rule",
                        "window": [violated[0], violated[1]],
                    }
                )
            else:
                reasons.append({"person": p.name, "reason": "not_selected"})
        empty_holes.append(
            {
                "hole_id": h["id"],
                "date": date.isoformat(),
                "slot": h["role"],
                "category": cat,
                "reasons": reasons or [{"person": None, "reason": "no_candidate"}],
            }
        )

    quotas = []
    for p in candidates:
        quotas.append(
            {
                "person": p.name,
                "weekend": {
                    "initial": p.weekend_quota,
                    "assigned": by_person_cat[(p.name, "weekend")],
                    "remaining": p.weekend_quota - by_person_cat[(p.name, "weekend")],
                },
                "ferie": {
                    "initial": p.holiday_quota,
                    "assigned": by_person_cat[(p.name, "ferie")],
                    "remaining": p.holiday_quota - by_person_cat[(p.name, "ferie")],
                },
            }
        )

    status = "OPTIMAL" if all(s == "OPTIMAL" for s in statuses_solves) else "FEASIBLE"
    warnings: list[str] = []
    for source in (calcul, planning, wishes):
        warnings.extend(source.get("warnings", []) or [])
    if status != "OPTIMAL":
        warnings.append("Time limit atteint : résultat non prouvé optimal.")

    attribution = {
        "schema_version": 1,
        "period": dict(calcul["period"]),
        "inputs": {
            "calcul": _input_block((input_paths or {}).get("calcul")),
            "planning": _input_block((input_paths or {}).get("planning")),
            "souhaits": _input_block((input_paths or {}).get("souhaits")),
        },
        "solver": {
            "name": "ortools-cpsat",
            "version": ortools.__version__,
            "status": status,
            "num_search_workers": 1,
            "random_seed": 0,
            "wall_time_s": round(wall_time, 3),
        },
        "objective": {
            "coverage": len(assignments),
            "red_forced": len(red_forced),
            "green": sum(
                1
                for a in assignments
                if statuses.get((a["person"], as_date(a["date"]))) == "volunteer"
            ),
        },
        "assignments": assignments,
        "empty_holes": empty_holes,
        "quotas": quotas,
        "red_forced": red_forced,
        "counts": {
            "holes": len(holes),
            "filled": len(assignments),
            "empty": len(empty_holes),
            "fixed": len(fixed),
            "weekend_holes": sum(1 for h in holes if h["category"] == "weekend"),
            "ferie_holes": sum(1 for h in holes if h["category"] == "ferie"),
        },
        "warnings": warnings,
    }
    validate_attribution(calcul, planning, wishes, attribution)
    return attribution
