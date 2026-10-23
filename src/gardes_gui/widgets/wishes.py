from __future__ import annotations

from collections import Counter

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .common import Card, MetricCard, SectionHeader, fill_rows, make_table


class WishesView(QWidget):
    solve_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        layout.addWidget(
            SectionHeader(
                "4. Souhaits",
                "Couleurs lues sur les 181 dates. Les erreurs bloquantes "
                "(nom inconnu, candidat absent, couleur inattendue) ont déjà arrêté l'étape.",
            )
        )

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(12)
        self.metrics = {
            "people": MetricCard("Personnes"),
            "candidates": MetricCard("Candidats"),
            "dates": MetricCard("Dates"),
            "volunteer": MetricCard("Volontaires"),
            "vacation": MetricCard("Vacances / formation"),
            "non_dispo": MetricCard("Non dispo"),
            "neutral": MetricCard("Neutres"),
        }
        for i, card in enumerate(self.metrics.values()):
            metrics.addWidget(card, i // 4, i % 4)
        layout.addLayout(metrics)

        card = Card()
        card.layout.addWidget(QLabel("Détail par personne"))
        self.table = make_table(
            ["Personne", "Candidat", "Volontaire", "Vacances", "Non dispo", "Neutre"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(260)
        card.layout.addWidget(self.table)
        layout.addWidget(card, 2)

        warn_card = Card()
        warn_card.layout.addWidget(QLabel("Avertissements"))
        self.warnings = QPlainTextEdit()
        self.warnings.setReadOnly(True)
        self.warnings.setMaximumHeight(120)
        warn_card.layout.addWidget(self.warnings)
        layout.addWidget(warn_card, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.solve_button = QPushButton("Lancer l'attribution")
        self.solve_button.setObjectName("primary")
        buttons.addWidget(self.solve_button)
        layout.addLayout(buttons)
        self.solve_button.clicked.connect(self.solve_requested)

    def populate(self, wishes: dict) -> None:
        counts = wishes.get("counts", {})
        statuses = counts.get("statuses", {})
        self.metrics["people"].set_value(counts.get("people", "—"))
        self.metrics["candidates"].set_value(counts.get("candidates", "—"))
        self.metrics["dates"].set_value(counts.get("dates", "—"))
        self.metrics["volunteer"].set_value(statuses.get("volunteer", 0))
        self.metrics["vacation"].set_value(statuses.get("vacation", 0))
        self.metrics["non_dispo"].set_value(statuses.get("non_dispo", 0))
        self.metrics["neutral"].set_value(statuses.get("neutral", 0))

        rows = []
        for person in wishes.get("people", []):
            c = Counter(entry["status"] for entry in person.get("statuses", []))
            rows.append(
                [
                    person["name"],
                    "oui" if person.get("candidate") else "non",
                    c.get("volunteer", 0),
                    c.get("vacation", 0),
                    c.get("non_dispo", 0),
                    c.get("neutral", 0),
                ]
            )
        fill_rows(self.table, rows)
        warnings = wishes.get("warnings", [])
        self.warnings.setPlainText(
            "\n".join(warnings) if warnings else "Aucun avertissement."
        )

    def clear(self) -> None:
        for card in self.metrics.values():
            card.set_value("—")
        self.table.setRowCount(0)
        self.warnings.clear()
