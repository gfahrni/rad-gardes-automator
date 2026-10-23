from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any

import pymupdf

from .errors import GardesError
from .jsonio import generated_at, sha256_file, write_json
from .models import (
    ALL_QUOTA_KEYS,
    QUOTA_KEYS,
    ROLE_CDC,
    ROLE_EXCLU,
    ROLE_URGENTISTE,
    Person,
    person_from_dict,
)
from .step2_planning import parse_planning

# Colonnes du PDF, exprimées par le bord droit (x1) des nombres.
# Le PDF est toujours au même format ; ces constantes sont le contrat de lecture.
COLUMN_EDGES: dict[str, int] = {
    "sem_j": 292,
    "sem_s": 331,
    "ct_hosp": 378,
    "ve_j": 418,
    "ve_soir": 457,
    "samedi": 503,
    "dimanche": 549,
    "feries": 595,
    "jours_poses": 641,
    "a_atteindre": 687,
}

NAME_X_MIN = 185
NAME_X_MAX = 270
NAME_Y_MIN = 150
NAME_Y_MAX = 535
TOLERANCE = 8
SUM_TOLERANCE = 0.01


def _column_for_x1(x1: float) -> str | None:
    best = min(COLUMN_EDGES.items(), key=lambda kv: abs(kv[1] - x1))
    return best[0] if abs(best[1] - x1) <= TOLERANCE else None


def _as_float(value: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise GardesError(f"Valeur numérique illisible dans le PDF : {value!r}", code="pdf_value") from exc


def _name_rows(words: list[tuple]) -> list[tuple[int, str, dict[str, float]]]:
    anchors = sorted(
        {
            round(w[1])
            for w in words
            if NAME_X_MIN <= w[0] <= NAME_X_MAX + 5 and NAME_Y_MIN < w[1] < NAME_Y_MAX
        }
    )
    rows: list[tuple[int, str, dict[str, float]]] = []
    for y in anchors:
        name_words = sorted(
            [w for w in words if abs(w[1] - y) <= 5 and NAME_X_MIN <= w[0] < NAME_X_MAX],
            key=lambda w: w[0],
        )
        raw_name = " ".join(str(w[4]) for w in name_words)
        raw_name = re.sub(r"\s+", " ", raw_name).strip()
        if not raw_name:
            continue
        if raw_name.startswith(("Total", "CDC", "EPT", "%")):
            continue
        if not re.search(r"[A-Za-zÀ-ÿ]", raw_name):
            continue
        if re.fullmatch(r"[\d.\s%]+", raw_name):
            continue
        values: dict[str, float] = {}
        for w in words:
            if abs(w[1] - y) > 6 or w[0] < 275:
                continue
            text = str(w[4])
            if not re.fullmatch(r"\d+(\.\d+)?", text):
                continue
            col = _column_for_x1(float(w[2]))
            if col is None:
                continue
            if col in values:
                raise GardesError(
                    f"Deux valeurs pour la colonne {col} sur la ligne PDF y={y}.",
                    code="pdf_duplicate_value",
                )
            values[col] = _as_float(text)
        rows.append((y, raw_name, values))
    rows.sort(key=lambda r: r[0])
    return rows


def _parse_total_row(words: list[tuple]) -> dict[str, float]:
    total_words = [
        w for w in words if str(w[4]).strip().lower() == "total" and 180 <= w[0] <= 215
    ]
    if not total_words:
        raise GardesError("Ligne 'Total colonnes' absente du PDF.", code="pdf_total_missing")
    y = round(total_words[0][1])
    values: dict[str, float] = {}
    for w in words:
        if abs(w[1] - y) > 4 or w[0] < 275:
            continue
        text = str(w[4])
        if not re.fullmatch(r"\d+(\.\d+)?", text):
            continue
        col = _column_for_x1(float(w[2]))
        if col is not None:
            values[col] = _as_float(text)
    for key in ("sem_j", "sem_s", "ct_hosp", "ve_j", "ve_soir", "samedi", "dimanche", "feries", "jours_poses"):
        if key not in values:
            raise GardesError(
                f"Total de la colonne {key} absent du PDF.", code="pdf_total_missing"
            )
    return values


def _split_name_note(raw: str) -> tuple[str, str]:
    if "(" not in raw:
        return raw.strip(), ""
    name, rest = raw.split("(", 1)
    note = rest.rsplit(")", 1)[0] if ")" in rest else rest
    return name.strip(), note.strip()


def _infer_year(day: int, month: int, period_start: dt.date) -> int:
    year = period_start.year if month >= 7 else period_start.year + 1
    # Si la date reconstruite est avant le début de période, on passe à l'année suivante.
    candidate = dt.date(year, month, day)
    if candidate < period_start:
        candidate = dt.date(year + 1, month, day)
    return candidate.year


def parse_note_dates(note: str, period_start: dt.date, period_end: dt.date) -> tuple[dt.date, dt.date]:
    active_from = period_start
    active_to = period_end
    m = re.search(r"d[èe]s\s*(\d{1,2})\.(\d{1,2})", note, re.IGNORECASE)
    if m:
        day, month = int(m.group(1)), int(m.group(2))
        active_from = dt.date(_infer_year(day, month, period_start), month, day)
    m = re.search(r"=>\s*(\d{1,2})\.(\d{1,2})", note)
    if m:
        day, month = int(m.group(1)), int(m.group(2))
        active_to = dt.date(_infer_year(day, month, period_start), month, day)
    if active_from > active_to:
        raise GardesError(
            f"Dates d'activité incohérentes pour la note {note!r} : "
            f"{active_from.isoformat()} > {active_to.isoformat()}.",
            code="active_dates",
        )
    return active_from, active_to


def _build_person(
    *,
    name: str,
    note: str,
    values: dict[str, float],
    role: str,
    source_row: int,
    period_start: dt.date,
    period_end: dt.date,
) -> Person:
    quotas = {key: float(values.get(key, 0.0)) for key in ALL_QUOTA_KEYS}
    weekend_quota = int(round(quotas["samedi"] + quotas["dimanche"]))
    holiday_quota = int(round(quotas["feries"]))
    active_from, active_to = parse_note_dates(note, period_start, period_end)
    assignable = role == ROLE_CDC and (weekend_quota > 0 or holiday_quota > 0)
    return Person(
        name=name,
        role=role,
        quotas=quotas,
        weekend_quota=weekend_quota,
        holiday_quota=holiday_quota,
        active_from=active_from,
        active_to=active_to,
        assignable_weekend=assignable,
        fixed_priority=False,
        prefilled=False,
        notes=note,
        source_row=source_row,
    )


def parse_pdf(
    pdf_path: str | Path,
    *,
    planning_path: str | Path | None = None,
) -> dict:
    pdf_path = Path(pdf_path)
    doc = pymupdf.open(pdf_path)
    try:
        if len(doc) != 1:
            raise GardesError(
                f"Le PDF doit contenir une seule page, {len(doc)} trouvée(s).",
                code="pdf_pages",
            )
        words = doc[0].get_text("words")
    finally:
        doc.close()
    if not words:
        raise GardesError("PDF illisible : aucun texte extractible.", code="pdf_empty")

    rows = _name_rows(words)
    if len(rows) != 30:
        raise GardesError(
            f"30 lignes de noms attendues (26 CDC + 3 urgentistes + 1 exclu), {len(rows)} trouvées.",
            code="pdf_rows",
        )
    names = [name for _, name, _ in rows]
    if len(set(names)) != len(names):
        dupes = sorted({n for n in names if names.count(n) > 1})
        raise GardesError(f"Noms en doublon dans le PDF : {dupes}", code="pdf_duplicate_name")

    # Vérifie le total général et la cohérence ligne à ligne.
    total_row = _parse_total_row(words)
    for y, raw, values in rows:
        expected = sum(values.get(k, 0.0) for k in QUOTA_KEYS)
        got = values.get("jours_poses", 0.0)
        if abs(expected - got) > SUM_TOLERANCE:
            raise GardesError(
                f"Jours posés incohérents pour {raw!r} : somme={expected}, PDF={got}.",
                code="pdf_row_total",
            )
    for key in ("sem_j", "sem_s", "ct_hosp", "ve_j", "ve_soir", "samedi", "dimanche", "feries", "jours_poses"):
        computed = sum(values.get(key, 0.0) for _, _, values in rows)
        if abs(computed - total_row[key]) > SUM_TOLERANCE:
            raise GardesError(
                f"Total de colonne {key} incohérent : calculé={computed}, PDF={total_row[key]}.",
                code="pdf_column_total",
            )

    # Période : le PDF donne les colonnes, le planning donne les dates exactes.
    if planning_path is not None:
        planning = parse_planning(planning_path)
        period_start = dt.date.fromisoformat(planning["period"]["start"])
        period_end = dt.date.fromisoformat(planning["period"]["end"])
    else:
        # Repli minimal : le titre du PDF ne donne que les mois, on utilise les notes.
        # Les appels normaux passent toujours le planning.
        period_start = dt.date(2026, 11, 1)
        period_end = dt.date(2027, 4, 30)

    people: list[Person] = []
    for index, (y, raw, values) in enumerate(rows):
        name, note = _split_name_note(raw)
        if index < 26:
            role = ROLE_CDC
        elif index < 29:
            role = ROLE_URGENTISTE
        else:
            role = ROLE_EXCLU
        people.append(
            _build_person(
                name=name,
                note=note,
                values=values,
                role=role,
                source_row=y,
                period_start=period_start,
                period_end=period_end,
            )
        )

    data = {
        "schema_version": 1,
        "period": {"start": period_start.isoformat(), "end": period_end.isoformat()},
        "source": {
            "pdf_path": str(pdf_path.resolve()),
            "pdf_sha256": sha256_file(pdf_path),
            "planning_path": str(Path(planning_path).resolve()) if planning_path else None,
            "planning_sha256": sha256_file(planning_path) if planning_path else None,
            "generated_at": generated_at(),
        },
        "validated": False,
        "people": [p.to_dict() for p in people],
        "prefilled": [],
        "candidates": [p.name for p in people if p.is_candidate],
        "totals": {
            "people": len(people),
            "cdc": sum(1 for p in people if p.role == ROLE_CDC),
            "urgentistes": sum(1 for p in people if p.role == ROLE_URGENTISTE),
            "excluded": sum(1 for p in people if p.role == ROLE_EXCLU),
            "quotas": {key: sum(float(p.quotas[key]) for p in people) for key in ALL_QUOTA_KEYS},
        },
        "warnings": [],
    }
    if planning_path is not None:
        apply_prescan(data, parse_planning(planning_path))
    return data


def apply_prescan(data: dict, planning: dict) -> None:
    """Applique le pré-scan du planning au calcul.

    Tout nom pré-rempli dans une cellule GARDE week-end/férié est marqué
    `prefilled=True`, `fixed_priority=True`, `assignable_weekend=False`.
    """
    fixed_slots = [s for s in planning["slots"] if s["status"] == "fixed"]
    if not fixed_slots:
        raise GardesError(
            "Planning vide : aucun pré-rempli. Le pool deviendrait 18 CDC, "
            "dont 6 absents des souhaits. Fournis un planning bien pré-rempli.",
            code="empty_planning",
        )
    cells_by_name: dict[str, list[str]] = {}
    for slot in fixed_slots:
        cells_by_name.setdefault(slot["fixed_name"], []).append(slot["cell"])

    by_name = {p["name"]: p for p in data["people"]}
    warnings: list[str] = data.setdefault("warnings", [])
    for name, cells in sorted(cells_by_name.items()):
        person = by_name.get(name)
        if person is None:
            raise GardesError(
                f"Nom fixe inconnu dans le planning : {name!r} ({', '.join(cells)}). "
                "Corrige l'orthographe dans le PDF ou le planning.",
                code="unknown_fixed_name",
                details={"name": name, "cells": cells},
            )
        if person["role"] == ROLE_URGENTISTE:
            raise GardesError(
                f"L'urgentiste {name!r} est pré-rempli sur un week-end/férié ({', '.join(cells)}).",
                code="urgentist_prefilled",
            )
        person["prefilled"] = True
        person["fixed_priority"] = True
        person["assignable_weekend"] = False
    data["prefilled"] = sorted(cells_by_name)
    data["candidates"] = [p["name"] for p in data["people"] if p["assignable_weekend"] and not p["fixed_priority"]]
    if not data["candidates"]:
        raise GardesError(
            "Aucun candidat assignable après pré-scan.", code="no_candidate"
        )


def validate_calcul(data: dict) -> dict:
    people = [person_from_dict(p) for p in data.get("people", [])]
    if not people:
        raise GardesError("Liste de personnes vide.", code="calcul_empty")
    names = [p.name for p in people]
    if len(set(names)) != len(names):
        raise GardesError("Noms en doublon dans calcul-gardes.json.", code="calcul_duplicate")
    period_start = dt.date.fromisoformat(data["period"]["start"])
    period_end = dt.date.fromisoformat(data["period"]["end"])
    if period_start > period_end:
        raise GardesError("Période incohérente.", code="period")
    for p, raw in zip(people, data["people"]):
        if p.active_from > p.active_to:
            raise GardesError(
                f"Dates d'activité incohérentes pour {p.name}.", code="active_dates"
            )
        # Les quotas dérivés sont recalculés : ce sont des sorties, pas des saisies.
        p.weekend_quota = int(round(p.quotas["samedi"] + p.quotas["dimanche"]))
        p.holiday_quota = int(round(p.quotas["feries"]))
        p.assignable_weekend = (
            p.role == ROLE_CDC
            and not p.prefilled
            and not p.fixed_priority
            and (p.weekend_quota > 0 or p.holiday_quota > 0)
        )
        raw["weekend_quota"] = p.weekend_quota
        raw["holiday_quota"] = p.holiday_quota
        raw["assignable_weekend"] = p.assignable_weekend
        if p.prefilled and (not p.fixed_priority or p.assignable_weekend):
            raise GardesError(
                f"Pré-rempli {p.name} marqué assignable : contradiction.", code="prefilled_assignable"
            )
        if p.role in (ROLE_URGENTISTE, ROLE_EXCLU) and p.assignable_weekend:
            raise GardesError(
                f"{p.name} ({p.role}) ne peut pas être assignable.", code="role_not_assignable"
            )
    candidates = [p for p in people if p.is_candidate]
    if not candidates:
        raise GardesError("Aucun candidat assignable.", code="no_candidate")
    data["prefilled"] = [p.name for p in people if p.prefilled]
    data["candidates"] = [p.name for p in candidates]
    data["totals"] = {
        "people": len(people),
        "cdc": sum(1 for p in people if p.role == ROLE_CDC),
        "urgentistes": sum(1 for p in people if p.role == ROLE_URGENTISTE),
        "excluded": sum(1 for p in people if p.role == ROLE_EXCLU),
        "quotas": {key: sum(float(p.quotas[key]) for p in people) for key in ALL_QUOTA_KEYS},
    }
    data["validated"] = True
    return data


def write_calcul(data: dict, out: str | Path) -> None:
    write_json(out, data)


def load_calcul(path: str | Path) -> dict:
    import json

    with open(path, encoding="utf-8") as f:
        return json.load(f)
