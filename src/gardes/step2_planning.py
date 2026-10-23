from __future__ import annotations

import datetime as dt
from pathlib import Path

from .errors import GardesError
from .jsonio import generated_at, sha256_file, write_json
from .models import CATEGORY_FERIE, CATEGORY_WEEKEND, CATEGORY_WORKDAY, Day, Slot, slot_id
from .xlsx_utils import load_workbook_cached

SHEET = "Feuille1"


def classify_indicator(indicator: str, date: dt.date) -> tuple[str, bool]:
    """Retourne (catégorie, est_férié).

    L'indicateur fait foi. `fer.` est accepté tous les jours et reste férié,
    y compris le samedi/dimanche.
    """
    indicator = indicator.strip()
    weekday = date.weekday()  # 0=lundi, 5=samedi, 6=dimanche
    if indicator == "fer.":
        return CATEGORY_FERIE, True
    if indicator == "sam.":
        if weekday != 5:
            raise GardesError(
                f"Indicateur 'sam.' sur {date.isoformat()} qui n'est pas un samedi.",
                code="indicator_mismatch",
            )
        return CATEGORY_WEEKEND, False
    if indicator == "dim.":
        if weekday != 6:
            raise GardesError(
                f"Indicateur 'dim.' sur {date.isoformat()} qui n'est pas un dimanche.",
                code="indicator_mismatch",
            )
        return CATEGORY_WEEKEND, False
    if indicator == "sem.":
        if weekday >= 5:
            raise GardesError(
                f"Indicateur 'sem.' sur {date.isoformat()} qui tombe un week-end.",
                code="indicator_mismatch",
            )
        return CATEGORY_WORKDAY, False
    if indicator == "ven.":
        if weekday != 4:
            raise GardesError(
                f"Indicateur 'ven.' sur {date.isoformat()} qui n'est pas un vendredi.",
                code="indicator_mismatch",
            )
        return CATEGORY_WORKDAY, False
    raise GardesError(
        f"Indicateur inconnu {indicator!r} pour {date.isoformat()}. "
        "Valeurs attendues : sem., ven., sam., dim., fer.",
        code="indicator_unknown",
    )


def _as_date(value) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _slot_value(value, *, cell: str) -> tuple[str, str | None]:
    if value is None:
        return "hole", None
    if isinstance(value, str):
        name = value.strip()
        if name == "":
            return "hole", None
        return "fixed", name
    raise GardesError(
        f"Cellule GARDE {cell} non textuelle : {value!r}.", code="planning_cell_invalid"
    )


def _find_header_zones(ws) -> list[tuple[int, int, int]]:
    zones: list[tuple[int, int, int]] = []
    for row in range(1, ws.max_row + 1):
        for col in range(1, ws.max_column + 1):
            value = ws.cell(row, col).value
            if (
                isinstance(value, str)
                and value.strip().upper().startswith("GARDE")
                and "13H-23H" in value.upper().replace(" ", "")
            ):
                day_col = col - 1
                if day_col < 1:
                    raise GardesError(
                        f"Colonne GARDE journée introuvable à gauche de {ws.cell(row, col).coordinate}.",
                        code="planning_header_invalid",
                    )
                zones.append((row, day_col, col))
    if len(zones) != 6:
        raise GardesError(
            f"6 zones mensuelles attendues, {len(zones)} trouvées. "
            "Vérifie les en-têtes GARDE journée/soirée.",
            code="planning_zones",
        )
    return sorted(zones)


def parse_planning(path: str | Path) -> dict:
    path = Path(path)
    wb = load_workbook_cached(path)
    try:
        if SHEET not in wb.sheetnames:
            raise GardesError(f"Feuille '{SHEET}' absente du planning.", code="sheet_missing")
        ws = wb[SHEET]
        zones = _find_header_zones(ws)
        header_rows = sorted({z[0] for z in zones})
        if len(header_rows) != 2:
            raise GardesError(
                f"2 blocs de mois attendus, {len(header_rows)} trouvés.",
                code="planning_zones",
            )

        days: dict[dt.date, Day] = {}
        slots: list[Slot] = []
        for header_row, day_col, evening_col in zones:
            date_col = day_col - 4
            indicator_col = day_col + 3
            later_headers = [r for r in header_rows if r > header_row]
            block_end = (min(later_headers) - 1) if later_headers else ws.max_row
            block_end = min(block_end, ws.max_row)

            for row in range(header_row + 1, block_end + 1):
                date = _as_date(ws.cell(row, date_col).value)
                if date is None:
                    continue
                indicator_value = ws.cell(row, indicator_col).value
                if not isinstance(indicator_value, str) or not indicator_value.strip():
                    raise GardesError(
                        f"Indicateur manquant en {ws.cell(row, indicator_col).coordinate} "
                        f"pour {date.isoformat()}. Ouvre le fichier dans Excel/Sheets et sauvegarde-le "
                        "pour recalculer les formules.",
                        code="indicator_missing",
                    )
                indicator = indicator_value.strip()
                category, holiday = classify_indicator(indicator, date)
                if date in days:
                    raise GardesError(
                        f"Date {date.isoformat()} présente deux fois dans le planning.",
                        code="planning_duplicate_date",
                    )
                days[date] = Day(date=date, indicator=indicator, category=category, holiday=holiday)
                if category in (CATEGORY_WEEKEND, CATEGORY_FERIE):
                    for role, col in (("day", day_col), ("evening", evening_col)):
                        cell = ws.cell(row, col).coordinate
                        status, fixed_name = _slot_value(ws.cell(row, col).value, cell=cell)
                        slots.append(
                            Slot(
                                id=slot_id(date, role),
                                date=date,
                                category=category,
                                role=role,
                                cell=cell,
                                status=status,
                                fixed_name=fixed_name,
                            )
                        )
        if not days:
            raise GardesError("Aucun jour lu dans le planning.", code="planning_empty")
        ordered_days = sorted(days.values(), key=lambda d: d.date)
        for prev, cur in zip(ordered_days, ordered_days[1:]):
            if cur.date != prev.date + dt.timedelta(days=1):
                raise GardesError(
                    f"Calendrier non continu entre {prev.date.isoformat()} et {cur.date.isoformat()}.",
                    code="planning_gap",
                )
        slots.sort(key=lambda s: (s.date, 0 if s.role == "day" else 1))
        _check_slots(ordered_days, slots)
        holidays = [d.date for d in ordered_days if d.holiday]
        fixed_names = sorted({s.fixed_name for s in slots if s.fixed_name})
        counts = {
            "days": len(ordered_days),
            "workdays": sum(1 for d in ordered_days if d.category == CATEGORY_WORKDAY),
            "weekend_days": sum(1 for d in ordered_days if d.category == CATEGORY_WEEKEND),
            "ferie_days": sum(1 for d in ordered_days if d.category == CATEGORY_FERIE),
            "slots": len(slots),
            "holes": sum(1 for s in slots if s.status == "hole"),
            "fixed": sum(1 for s in slots if s.status == "fixed"),
            "weekend_holes": sum(
                1 for s in slots if s.status == "hole" and s.category == CATEGORY_WEEKEND
            ),
            "ferie_holes": sum(
                1 for s in slots if s.status == "hole" and s.category == CATEGORY_FERIE
            ),
            "fixed_names": fixed_names,
        }
        return {
            "schema_version": 1,
            "period": {
                "start": ordered_days[0].date.isoformat(),
                "end": ordered_days[-1].date.isoformat(),
            },
            "source": {
                "path": str(path.resolve()),
                "sha256": sha256_file(path),
                "sheet": SHEET,
                "generated_at": generated_at(),
            },
            "days": [d.to_dict() for d in ordered_days],
            "slots": [s.to_dict() for s in slots],
            "holidays": [d.isoformat() for d in holidays],
            "counts": counts,
            "warnings": [],
        }
    finally:
        wb.close()


def _check_slots(days: list[Day], slots: list[Slot]) -> None:
    by_date: dict[dt.date, set[str]] = {}
    for slot in slots:
        by_date.setdefault(slot.date, set()).add(slot.role)
    for day in days:
        if day.category in (CATEGORY_WEEKEND, CATEGORY_FERIE):
            roles = by_date.get(day.date, set())
            if roles != {"day", "evening"}:
                raise GardesError(
                    f"Créneaux incomplets pour {day.date.isoformat()} : {sorted(roles)}.",
                    code="planning_slots",
                )
        elif day.date in by_date:
            raise GardesError(
                f"Créneaux GARDE inattendus sur un jour travaillé {day.date.isoformat()}.",
                code="planning_slots",
            )


def write_planning_json(data: dict, out: str | Path) -> None:
    write_json(out, data)
