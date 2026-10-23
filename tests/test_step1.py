from __future__ import annotations

import copy
import datetime as dt
from pathlib import Path

import pytest

from gardes.errors import GardesError
from gardes.step1_pdf import (
    apply_prescan,
    load_calcul,
    parse_note_dates,
    parse_pdf,
    validate_calcul,
    write_calcul,
)


def test_pdf_counts_and_totals(pdf: Path, planning_xlsx: Path) -> None:
    data = parse_pdf(pdf, planning_path=planning_xlsx)
    assert data["totals"]["people"] == 30
    assert data["totals"]["cdc"] == 26
    assert data["totals"]["urgentistes"] == 3
    assert data["totals"]["excluded"] == 1
    quotas = data["totals"]["quotas"]
    assert quotas["samedi"] == 48
    assert quotas["dimanche"] == 52
    assert quotas["feries"] == 12
    assert quotas["jours_poses"] == 487
    assert quotas["sem_j"] == 102
    assert quotas["sem_s"] == 102
    assert quotas["ct_hosp"] == 125
    assert quotas["ve_j"] == 23
    assert quotas["ve_soir"] == 23


def test_prefilled_and_candidates(pdf: Path, planning_xlsx: Path) -> None:
    data = parse_pdf(pdf, planning_path=planning_xlsx)
    assert data["prefilled"] == [
        "Delacroix",
        "Deschamps",
        "El Amrani",
        "Fournier",
        "Moreau",
        "Renard",
        "Schwarz",
    ]
    assert data["candidates"] == [
        "Lambert",
        "Nassar",
        "Sarkissian",
        "Lefebvre",
        "Louis",
        "Mansouri",
        "Oliveira",
        "Ostermann",
        "Pereira",
        "Ribeiro",
        "Sanchez",
        "Traoré",
    ]
    people = {p["name"]: p for p in data["people"]}
    assert people["Moreau"]["fixed_priority"] is True
    assert people["Moreau"]["assignable_weekend"] is False
    assert people["Aubert"]["role"] == "urgentiste_semaine"
    assert people["Aubert"]["assignable_weekend"] is False
    assert people["Schwarz"]["role"] == "exclu"
    assert people["Schwarz"]["assignable_weekend"] is False


def test_notes_and_active_dates(pdf: Path, planning_xlsx: Path) -> None:
    data = parse_pdf(pdf, planning_path=planning_xlsx)
    people = {p["name"]: p for p in data["people"]}
    assert people["Deschamps"]["notes"] == "=> 31.1"
    assert str(people["Deschamps"]["active_to"]) == "2027-01-31"
    assert people["Delacroix"]["notes"] == "=>31.12"
    assert str(people["Delacroix"]["active_to"]) == "2026-12-31"
    assert people["Girardin"]["notes"] == "=> 31.12"
    assert str(people["Girardin"]["active_to"]) == "2026-12-31"
    assert people["Hoffmann"]["notes"] == "dès 1.1"
    assert str(people["Hoffmann"]["active_from"]) == "2027-01-01"


def test_parse_note_dates() -> None:
    start = dt.date(2026, 11, 1)
    end = dt.date(2027, 4, 30)
    assert parse_note_dates("=> 31.12", start, end) == (start, dt.date(2026, 12, 31))
    assert parse_note_dates("=> 31.1", start, end) == (start, dt.date(2027, 1, 31))
    assert parse_note_dates("dès 1.1", start, end) == (dt.date(2027, 1, 1), end)


def test_validate_and_roundtrip(pdf: Path, planning_xlsx: Path, tmp_path: Path) -> None:
    data = parse_pdf(pdf, planning_path=planning_xlsx)
    data = validate_calcul(data)
    assert data["validated"] is True
    out = tmp_path / "calcul-gardes.json"
    write_calcul(data, out)
    loaded = load_calcul(out)
    validated = validate_calcul(loaded)
    assert validated["validated"] is True
    assert len(validated["candidates"]) == 12


def _fake_planning(fixed_names: list[str]) -> dict:
    slots = []
    for i, name in enumerate(fixed_names):
        slots.append(
            {
                "id": f"2026-11-{7 + i:02d}_day",
                "date": f"2026-11-{7 + i:02d}",
                "category": "weekend",
                "role": "day",
                "cell": f"F{11 + i}",
                "status": "fixed",
                "fixed_name": name,
            }
        )
    return {"slots": slots}


def test_unknown_fixed_name_blocks(pdf: Path, planning_xlsx: Path) -> None:
    data = parse_pdf(pdf, planning_path=planning_xlsx)
    with pytest.raises(GardesError, match="Nom fixe inconnu"):
        apply_prescan(copy.deepcopy(data), _fake_planning(["Lefebvr"]))


def test_urgentist_prefilled_blocks(pdf: Path, planning_xlsx: Path) -> None:
    data = parse_pdf(pdf, planning_path=planning_xlsx)
    with pytest.raises(GardesError, match="urgentiste"):
        apply_prescan(copy.deepcopy(data), _fake_planning(["Aubert"]))


def test_empty_planning_blocks(pdf: Path, planning_xlsx: Path) -> None:
    data = parse_pdf(pdf, planning_path=planning_xlsx)
    with pytest.raises(GardesError, match="Planning vide"):
        apply_prescan(copy.deepcopy(data), {"slots": []})
