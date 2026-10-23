from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from gardes.errors import GardesError
from gardes.step1_pdf import parse_pdf, validate_calcul
from gardes.step2_planning import parse_planning
from gardes.step3_wishes import parse_wishes
from gardes.step4_solve import solve_attribution
from gardes.step4_validate import validate_attribution, validate_inputs


@pytest.fixture(scope="module")
def inputs(pdf: Path, planning_xlsx: Path, wishes_xlsx: Path):
    calcul = validate_calcul(parse_pdf(pdf, planning_path=planning_xlsx))
    planning = parse_planning(planning_xlsx)
    wishes = parse_wishes(wishes_xlsx, calcul, planning)
    return calcul, planning, wishes


def test_reference_objectives(inputs) -> None:
    calcul, planning, wishes = inputs
    attribution = solve_attribution(calcul, planning, wishes)
    assert attribution["objective"] == {"coverage": 87, "red_forced": 3, "green": 74}
    assert attribution["counts"] == {
        "holes": 88,
        "filled": 87,
        "empty": 1,
        "fixed": 24,
        "weekend_holes": 80,
        "ferie_holes": 8,
    }
    assert attribution["solver"]["status"] == "OPTIMAL"
    assert attribution["solver"]["name"] == "ortools-cpsat"
    assert len(attribution["empty_holes"]) == 1
    assert attribution["empty_holes"][0]["category"] == "ferie"
    assert len(attribution["red_forced"]) == 3


def test_attribution_is_valid(inputs) -> None:
    calcul, planning, wishes = inputs
    attribution = solve_attribution(calcul, planning, wishes)
    validate_attribution(calcul, planning, wishes, attribution)


def test_determinism(inputs) -> None:
    calcul, planning, wishes = inputs
    a1 = solve_attribution(calcul, planning, wishes)
    a2 = solve_attribution(calcul, planning, wishes)

    def norm(a: dict) -> dict:
        b = json.loads(json.dumps(a))
        b["solver"].pop("wall_time_s", None)
        return b

    assert norm(a1) == norm(a2)


def test_no_assignment_on_fixed_or_vacation(inputs) -> None:
    calcul, planning, wishes = inputs
    attribution = solve_attribution(calcul, planning, wishes)
    fixed_cells = {s["cell"] for s in planning["slots"] if s["status"] == "fixed"}
    assert not ({a["cell"] for a in attribution["assignments"]} & fixed_cells)
    statuses = {
        (p["name"], s["date"]): s["status"]
        for p in wishes["people"]
        for s in p["statuses"]
    }
    for a in attribution["assignments"]:
        assert statuses[(a["person"], a["date"])] != "vacation"


def test_all_holes_are_accounted(inputs) -> None:
    calcul, planning, wishes = inputs
    attribution = solve_attribution(calcul, planning, wishes)
    hole_ids = {s["id"] for s in planning["slots"] if s["status"] == "hole"}
    assigned = {a["hole_id"] for a in attribution["assignments"]}
    empty = {h["hole_id"] for h in attribution["empty_holes"]}
    assert assigned | empty == hole_ids
    assert not (assigned & empty)


def test_quotas_and_reds_consistent(inputs) -> None:
    calcul, planning, wishes = inputs
    attribution = solve_attribution(calcul, planning, wishes)
    quotas = {q["person"]: q for q in attribution["quotas"]}
    assert len(quotas) == 12
    for q in quotas.values():
        for cat in ("weekend", "ferie"):
            block = q[cat]
            assert block["assigned"] + block["remaining"] == block["initial"]
            assert block["remaining"] >= 0
    reds = [a for a in attribution["assignments"] if a["forced_red"]]
    assert len(reds) == len(attribution["red_forced"])


def test_non_validated_calcul_is_rejected(inputs) -> None:
    calcul, planning, wishes = inputs
    broken = copy.deepcopy(calcul)
    broken["validated"] = False
    with pytest.raises(GardesError, match="pas validé"):
        validate_inputs(broken, planning, wishes)


def test_fixed_candidate_contradiction_is_rejected(inputs) -> None:
    calcul, planning, wishes = inputs
    broken = copy.deepcopy(planning)
    fixed_slot = next(s for s in broken["slots"] if s["status"] == "fixed")
    fixed_slot["fixed_name"] = "Lefebvre"
    with pytest.raises(GardesError, match="à la fois fixe et candidat"):
        validate_inputs(calcul, broken, wishes)
