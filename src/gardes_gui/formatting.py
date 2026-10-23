from __future__ import annotations

from typing import Any

STATUS_LABELS = {
    "volunteer": "Volontaire",
    "vacation": "Vacances / formation",
    "non_dispo": "Non dispo",
    "neutral": "Neutre",
}

CATEGORY_LABELS = {
    "weekend": "Week-end",
    "ferie": "Férié",
    "workday": "Travaillé",
}

SLOT_LABELS = {"day": "Jour", "evening": "Soir"}


def slot_label(role: str) -> str:
    return SLOT_LABELS.get(role, role)


def category_label(category: str) -> str:
    return CATEGORY_LABELS.get(category, category)


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def yes_no(value: Any) -> str:
    return "oui" if value else "non"


def fmt_date(value: Any) -> str:
    if value is None:
        return ""
    return str(value)[:10]


def fmt_path(value: Any) -> str:
    return str(value) if value else ""


def metric_ratio(numerator: int, denominator: int) -> str:
    return f"{numerator}/{denominator}"
