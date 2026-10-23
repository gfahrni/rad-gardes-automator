from __future__ import annotations

import datetime as dt
from pathlib import Path

from .errors import GardesError
from .xlsx_utils import patch_workbook_cells, verify_patch


def _iso(value) -> str:
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    return str(value)


def _slots_by_cell(planning: dict) -> dict[str, dict]:
    return {slot["cell"]: slot for slot in planning["slots"]}


def validate_attribution_against_planning(
    attribution: dict,
    planning: dict,
    calcul: dict | None = None,
) -> dict[str, str]:
    slots = _slots_by_cell(planning)
    values: dict[str, str] = {}
    known_names = set(calcul.get("candidates", [])) if calcul else None
    for assignment in attribution.get("assignments", []):
        cell = assignment["cell"]
        slot = slots.get(cell)
        if slot is None:
            raise GardesError(
                f"Affectation sur une cellule inconnue du planning : {cell}.",
                code="attribution_cell",
            )
        if slot["status"] != "hole":
            raise GardesError(
                f"Affectation sur une cellule fixe {cell} : interdit.",
                code="attribution_fixed",
            )
        if _iso(slot["date"]) != _iso(assignment["date"]) or slot["role"] != assignment["slot"]:
            raise GardesError(
                f"Affectation incohérente en {cell} : {assignment['date']}/{assignment['slot']} "
                f"vs {_iso(slot['date'])}/{slot['role']}.",
                code="attribution_mismatch",
            )
        if cell in values:
            raise GardesError(f"Deux affectations sur la cellule {cell}.", code="attribution_duplicate")
        person = assignment["person"]
        if known_names is not None and person not in known_names:
            raise GardesError(
                f"Nom affecté absent de la liste validée : {person!r}.", code="attribution_name"
            )
        values[cell] = person
    return values


def write_excel(
    *,
    planning_xlsx: str | Path,
    planning: dict,
    attribution: dict,
    out_xlsx: str | Path,
    calcul: dict | None = None,
) -> dict[str, str]:
    planning_xlsx = Path(planning_xlsx)
    out_xlsx = Path(out_xlsx)
    if planning_xlsx.resolve() == out_xlsx.resolve():
        raise GardesError(
            "Le fichier de sortie doit être différent du planning source.",
            code="output_in_place",
        )
    values = validate_attribution_against_planning(attribution, planning, calcul)
    expected_count = attribution.get("counts", {}).get("filled")
    if expected_count is not None and expected_count != len(values):
        raise GardesError(
            f"Le JSON d'attribution annonce {expected_count} affectations, {len(values)} trouvées.",
            code="attribution_counts",
        )
    fixed_cells = {
        slot["cell"]: slot["fixed_name"]
        for slot in planning["slots"]
        if slot["status"] == "fixed" and slot.get("fixed_name") is not None
    }
    sheet_name = planning.get("source", {}).get("sheet", "Feuille1")
    patch_workbook_cells(planning_xlsx, out_xlsx, values, sheet_name=sheet_name)
    verify_patch(
        planning_xlsx,
        out_xlsx,
        sheet_name=sheet_name,
        expected_values=values,
        fixed_cells=fixed_cells,
    )
    return values
