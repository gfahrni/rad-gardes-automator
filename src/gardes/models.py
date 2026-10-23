from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any

from .jsonio import to_jsonable

QUOTA_KEYS = (
    "sem_j",
    "sem_s",
    "ct_hosp",
    "ve_j",
    "ve_soir",
    "samedi",
    "dimanche",
    "feries",
)
CONTROL_KEYS = ("jours_poses", "a_atteindre")
ALL_QUOTA_KEYS = QUOTA_KEYS + CONTROL_KEYS

CATEGORY_WORKDAY = "workday"
CATEGORY_WEEKEND = "weekend"
CATEGORY_FERIE = "ferie"

ROLE_CDC = "cdc_weekend"
ROLE_URGENTISTE = "urgentiste_semaine"
ROLE_EXCLU = "exclu"


@dataclass
class Person:
    name: str
    role: str
    quotas: dict[str, float]
    weekend_quota: int
    holiday_quota: int
    active_from: dt.date
    active_to: dt.date
    assignable_weekend: bool
    fixed_priority: bool
    prefilled: bool = False
    notes: str = ""
    source_row: int = 0

    @property
    def is_candidate(self) -> bool:
        return self.assignable_weekend and not self.fixed_priority

    def quota(self, category: str) -> int:
        if category == CATEGORY_WEEKEND:
            return self.weekend_quota
        if category == CATEGORY_FERIE:
            return self.holiday_quota
        return 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "quotas": dict(self.quotas),
            "weekend_quota": self.weekend_quota,
            "holiday_quota": self.holiday_quota,
            "active_from": self.active_from,
            "active_to": self.active_to,
            "assignable_weekend": self.assignable_weekend,
            "fixed_priority": self.fixed_priority,
            "prefilled": self.prefilled,
            "notes": self.notes,
            "source_row": self.source_row,
        }


@dataclass
class Day:
    date: dt.date
    indicator: str
    category: str
    holiday: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "indicator": self.indicator,
            "category": self.category,
            "holiday": self.holiday,
        }


@dataclass
class Slot:
    id: str
    date: dt.date
    category: str
    role: str
    cell: str
    status: str
    fixed_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date,
            "category": self.category,
            "role": self.role,
            "cell": self.cell,
            "status": self.status,
            "fixed_name": self.fixed_name,
        }


def slot_id(date: dt.date, role: str) -> str:
    return f"{date.isoformat()}_{role}"


def _date(value: Any) -> dt.date:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    return dt.date.fromisoformat(str(value))


def person_from_dict(data: dict[str, Any]) -> Person:
    return Person(
        name=data["name"],
        role=data["role"],
        quotas={k: float(data.get("quotas", {}).get(k, 0)) for k in ALL_QUOTA_KEYS},
        weekend_quota=int(data["weekend_quota"]),
        holiday_quota=int(data["holiday_quota"]),
        active_from=_date(data["active_from"]),
        active_to=_date(data["active_to"]),
        assignable_weekend=bool(data["assignable_weekend"]),
        fixed_priority=bool(data["fixed_priority"]),
        prefilled=bool(data.get("prefilled", False)),
        notes=data.get("notes", ""),
        source_row=int(data.get("source_row", 0)),
    )


def day_from_dict(data: dict[str, Any]) -> Day:
    return Day(
        date=dt.date.fromisoformat(data["date"]),
        indicator=data["indicator"],
        category=data["category"],
        holiday=bool(data.get("holiday", False)),
    )


def slot_from_dict(data: dict[str, Any]) -> Slot:
    return Slot(
        id=data["id"],
        date=dt.date.fromisoformat(data["date"]),
        category=data["category"],
        role=data["role"],
        cell=data["cell"],
        status=data["status"],
        fixed_name=data.get("fixed_name"),
    )


def dataclass_list(values: list[Any]) -> list[dict[str, Any]]:
    return [to_jsonable(v) for v in values]
