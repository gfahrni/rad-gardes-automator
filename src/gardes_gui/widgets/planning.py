from __future__ import annotations

from collections import defaultdict

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .common import Card, MetricCard, SectionHeader, fill_rows, make_table


class PlanningView(QWidget):
    next_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        layout.addWidget(
            SectionHeader(
                "2. Planning",
                "Scan de Feuille1. Le planning doit être bien pré-rempli : "
                "les cellules GARDE week-end/férié déjà remplies sont fixes.",
            )
        )

        self.source_label = QLabel("")
        self.source_label.setObjectName("muted")
        self.source_label.setWordWrap(True)
        layout.addWidget(self.source_label)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(12)
        metrics.setVerticalSpacing(12)
        self.metrics = {
            "days": MetricCard("Jours"),
            "slots": MetricCard("Créneaux WE/férié"),
            "holes": MetricCard("Trous à remplir"),
            "fixed": MetricCard("Cellules fixes"),
            "weekend_holes": MetricCard("Trous week-end"),
            "ferie_holes": MetricCard("Trous fériés"),
        }
        for i, card in enumerate(self.metrics.values()):
            metrics.addWidget(card, i // 3, i % 3)
        layout.addLayout(metrics)

        tables = QHBoxLayout()
        fixed_card = Card()
        fixed_card.layout.addWidget(QLabel("Pré-remplis (hors pool)"))
        self.fixed_table = make_table(["Nom", "Cellules"], editable=False)
        self.fixed_table.setMinimumHeight(190)
        fixed_card.layout.addWidget(self.fixed_table)
        tables.addWidget(fixed_card, 3)

        holidays_card = Card()
        holidays_card.layout.addWidget(QLabel("Jours marqués fer."))
        self.holidays_table = make_table(["Date"], editable=False)
        self.holidays_table.setMinimumHeight(190)
        holidays_card.layout.addWidget(self.holidays_table)
        tables.addWidget(holidays_card, 2)
        layout.addLayout(tables, 1)

        self.warnings_label = QLabel("")
        self.warnings_label.setObjectName("muted")
        self.warnings_label.setWordWrap(True)
        layout.addWidget(self.warnings_label)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.next_button = QPushButton("Continuer vers le crédit de gardes")
        self.next_button.setObjectName("primary")
        buttons.addWidget(self.next_button)
        layout.addLayout(buttons)

        self.next_button.clicked.connect(self.next_requested)

    def populate(self, planning: dict) -> None:
        source = planning.get("source", {}).get("path", "")
        self.source_label.setText(f"Source : {source}")
        counts = planning.get("counts", {})
        self.metrics["days"].set_value(counts.get("days", "—"))
        self.metrics["slots"].set_value(counts.get("slots", "—"))
        self.metrics["holes"].set_value(counts.get("holes", "—"))
        self.metrics["fixed"].set_value(counts.get("fixed", "—"))
        self.metrics["weekend_holes"].set_value(counts.get("weekend_holes", "—"))
        self.metrics["ferie_holes"].set_value(counts.get("ferie_holes", "—"))

        fixed = defaultdict(list)
        for slot in planning.get("slots", []):
            if slot["status"] == "fixed" and slot.get("fixed_name"):
                fixed[slot["fixed_name"]].append(slot["cell"])
        fill_rows(
            self.fixed_table,
            [[name, ", ".join(sorted(cells))] for name, cells in sorted(fixed.items())],
        )
        fill_rows(self.holidays_table, [[date] for date in planning.get("holidays", [])])

        warnings = planning.get("warnings", [])
        self.warnings_label.setText(
            "Avertissements :\n" + "\n".join(f"- {w}" for w in warnings)
            if warnings
            else "Aucun avertissement."
        )

    def clear(self) -> None:
        for card in self.metrics.values():
            card.set_value("—")
        self.fixed_table.setRowCount(0)
        self.holidays_table.setRowCount(0)
        self.source_label.clear()
        self.warnings_label.clear()
