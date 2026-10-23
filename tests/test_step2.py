from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from gardes.errors import GardesError
from gardes.step2_planning import classify_indicator, parse_planning, write_planning_json


def test_example_counts(planning_xlsx: Path) -> None:
    data = parse_planning(planning_xlsx)
    assert data["period"] == {"start": "2026-11-01", "end": "2027-04-30"}
    counts = data["counts"]
    assert counts["days"] == 181
    assert counts["slots"] == 112
    assert counts["holes"] == 88
    assert counts["fixed"] == 24
    assert counts["weekend_holes"] == 80
    assert counts["ferie_holes"] == 8
    assert counts["weekend_days"] == 50
    assert counts["ferie_days"] == 6
    assert len(counts["fixed_names"]) == 7
    assert counts["fixed_names"] == [
        "Delacroix",
        "Deschamps",
        "El Amrani",
        "Fournier",
        "Moreau",
        "Renard",
        "Schwarz",
    ]


def test_indicators_and_january_second(planning_xlsx: Path) -> None:
    data = parse_planning(planning_xlsx)
    by_date = {d["date"]: d for d in data["days"]}
    jan2 = by_date[dt.date(2027, 1, 2)]
    assert jan2["indicator"] == "fer."
    assert jan2["category"] == "ferie"
    assert jan2["holiday"] is True
    assert "2027-01-02" in data["holidays"]
    # 6 jours marqués fer., dont le samedi 2 janvier.
    assert len(data["holidays"]) == 6


def test_slots_are_day_and_evening(planning_xlsx: Path) -> None:
    data = parse_planning(planning_xlsx)
    holes = [s for s in data["slots"] if s["status"] == "hole"]
    assert len(holes) == 88
    by_day: dict[str, set[str]] = {}
    for slot in holes:
        by_day.setdefault(slot["date"], set()).add(slot["role"])
    for roles in by_day.values():
        assert roles <= {"day", "evening"}
        assert len(roles) <= 2


def test_classify_rejects_weekend_indicator_on_weekday() -> None:
    with pytest.raises(GardesError, match="samedi"):
        classify_indicator("sam.", dt.date(2026, 11, 2))  # lundi
    with pytest.raises(GardesError, match="dimanche"):
        classify_indicator("dim.", dt.date(2026, 11, 2))
    with pytest.raises(GardesError, match="week-end"):
        classify_indicator("sem.", dt.date(2026, 11, 7))  # samedi


def test_classify_accepts_fer_on_saturday() -> None:
    category, holiday = classify_indicator("fer.", dt.date(2027, 1, 2))
    assert category == "ferie"
    assert holiday is True


def test_roundtrip_json(planning_xlsx: Path, tmp_path: Path) -> None:
    data = parse_planning(planning_xlsx)
    out = tmp_path / "gardes-a-remplir.json"
    write_planning_json(data, out)
    assert out.exists()
    import json

    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["counts"]["holes"] == 88
    assert loaded["days"][0]["date"] == "2026-11-01"
