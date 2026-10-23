from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .common import Card, MetricCard, SectionHeader, fill_rows, make_table


class CreditGardesView(QWidget):
    """Validation en lecture seule des crédits de gardes du run."""

    validate_requested = Signal()
    reload_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        layout.addWidget(
            SectionHeader(
                "Crédit de Gardes",
                "Qui fait partie du jeu pour ce run et combien de gardes il doit "
                "faire. Seules les personnes assignables sont affichées : les "
                "pré-remplis/neuro, le nom exclu, les urgentistes et les CDC à quota "
                "nul sont exclus. Lecture seule : si une valeur est fausse, "
                "corrige le PDF puis recharge.",
            )
        )

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(12)
        self.metrics = {
            "people": MetricCard("Personnes"),
            "weekend": MetricCard("Crédits week-end"),
            "ferie": MetricCard("Crédits fériés"),
        }
        for i, card in enumerate(self.metrics.values()):
            metrics.addWidget(card, 0, i)
        layout.addLayout(metrics)

        card = Card()
        self.table = make_table(
            ["Nom", "Samedi", "Dimanche", "Fériés", "Départ / Arrivée"],
            editable=False,
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(380)
        card.layout.addWidget(self.table)

        buttons = QHBoxLayout()
        self.reload_button = QPushButton("Recharger depuis le PDF")
        self.validate_button = QPushButton("Faire valider")
        self.validate_button.setObjectName("primary")
        buttons.addWidget(self.reload_button)
        buttons.addStretch(1)
        buttons.addWidget(self.validate_button)
        card.layout.addLayout(buttons)
        layout.addWidget(card, 1)

        self.reload_button.clicked.connect(self.reload_requested)
        self.validate_button.clicked.connect(self.validate_requested)

    def populate(self, calcul: dict) -> None:
        candidates = set(calcul.get("candidates", []))
        start = dt.date.fromisoformat(str(calcul["period"]["start"]))
        end = dt.date.fromisoformat(str(calcul["period"]["end"]))
        rows: list[list[object]] = []
        total_weekend = 0
        total_ferie = 0
        for person in calcul.get("people", []):
            if person["name"] not in candidates:
                continue
            quotas = person.get("quotas", {})
            samedi = int(float(quotas.get("samedi", 0)))
            dimanche = int(float(quotas.get("dimanche", 0)))
            feries = int(float(quotas.get("feries", 0)))
            total_weekend += samedi + dimanche
            total_ferie += feries
            rows.append(
                [
                    person["name"],
                    samedi,
                    dimanche,
                    feries,
                    self._dates(person, start, end),
                ]
            )
        fill_rows(self.table, rows)
        self.metrics["people"].set_value(len(rows))
        self.metrics["weekend"].set_value(total_weekend)
        self.metrics["ferie"].set_value(total_ferie)

    @staticmethod
    def _dates(person: dict, start: dt.date, end: dt.date) -> str:
        active_from = dt.date.fromisoformat(str(person["active_from"]))
        active_to = dt.date.fromisoformat(str(person["active_to"]))
        if active_from <= start and active_to >= end:
            return "—"
        if active_from > start and active_to < end:
            return f"dès {active_from.isoformat()} → {active_to.isoformat()}"
        if active_from > start:
            return f"dès {active_from.isoformat()}"
        return f"jusqu'au {active_to.isoformat()}"

    def clear(self) -> None:
        self.table.setRowCount(0)
        for card in self.metrics.values():
            card.set_value("—")
