from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..formatting import category_label, slot_label
from .common import Card, MetricCard, SectionHeader, fill_rows, make_table


class AttributionView(QWidget):
    export_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        layout.addWidget(
            SectionHeader(
                "5. Attribution",
                "Résultat CP-SAT : couverture maximale, puis rouges minimisés, "
                "puis verts maximisés. Un trou peut rester vide et être rapporté.",
            )
        )

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(12)
        self.metrics = {
            "coverage": MetricCard("Couverture"),
            "red": MetricCard("Rouges forcés"),
            "green": MetricCard("Verts"),
            "empty": MetricCard("Trous restants"),
            "fixed": MetricCard("Fixes"),
            "solver": MetricCard("Statut solveur"),
        }
        for i, card in enumerate(self.metrics.values()):
            metrics.addWidget(card, i // 3, i % 3)
        layout.addLayout(metrics)

        self.tabs = QTabWidget()
        self.assign_table = make_table(
            ["Date", "Créneau", "Catégorie", "Personne", "Cellule", "Rouge"],
            sorting=True,
        )
        self.empty_table = make_table(["Date", "Créneau", "Catégorie", "Raisons"])
        self.red_table = make_table(["Date", "Créneau", "Personne", "Raison"])
        self.quota_table = make_table(
            [
                "Personne",
                "WE init.",
                "WE attr.",
                "WE reste",
                "Fériés init.",
                "Fériés attr.",
                "Fériés reste",
            ]
        )
        self.solver_text = QPlainTextEdit()
        self.solver_text.setReadOnly(True)

        for table in (self.assign_table, self.empty_table, self.red_table, self.quota_table):
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.tabs.addTab(self.assign_table, "Affectations")
        self.tabs.addTab(self.empty_table, "Trous")
        self.tabs.addTab(self.red_table, "Rouges")
        self.tabs.addTab(self.quota_table, "Quotas")
        self.tabs.addTab(self.solver_text, "Solveur / avertissements")

        card = Card()
        card.layout.addWidget(self.tabs)
        layout.addWidget(card, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.export_button = QPushButton("Exporter le planning")
        self.export_button.setObjectName("primary")
        buttons.addWidget(self.export_button)
        layout.addLayout(buttons)
        self.export_button.clicked.connect(self.export_requested)

    def populate(self, attribution: dict) -> None:
        objective = attribution.get("objective", {})
        counts = attribution.get("counts", {})
        solver = attribution.get("solver", {})
        self.metrics["coverage"].set_value(
            f"{objective.get('coverage', '?')}/{counts.get('holes', '?')}"
        )
        self.metrics["red"].set_value(objective.get("red_forced", "?"))
        self.metrics["green"].set_value(objective.get("green", "?"))
        self.metrics["empty"].set_value(counts.get("empty", "?"))
        self.metrics["fixed"].set_value(counts.get("fixed", "?"))
        self.metrics["solver"].set_value(solver.get("status", "?"))

        assignments = sorted(
            attribution.get("assignments", []),
            key=lambda a: (a["date"], 0 if a["slot"] == "day" else 1),
        )
        fill_rows(
            self.assign_table,
            [
                [
                    a["date"],
                    slot_label(a["slot"]),
                    category_label(a["category"]),
                    a["person"],
                    a.get("cell", ""),
                    "oui" if a.get("forced_red") else "",
                ]
                for a in assignments
            ],
        )
        self.assign_table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        fill_rows(
            self.empty_table,
            [
                [
                    h["date"],
                    slot_label(h["slot"]),
                    category_label(h["category"]),
                    "; ".join(
                        f"{r.get('person')}: {r.get('reason')}"
                        + (f" ({r.get('window')})" if r.get("window") else "")
                        for r in h.get("reasons", [])
                    ),
                ]
                for h in attribution.get("empty_holes", [])
            ],
        )
        fill_rows(
            self.red_table,
            [
                [r.get("date", ""), slot_label(r.get("slot", "")), r.get("person", ""), r.get("reason", "")]
                for r in attribution.get("red_forced", [])
            ],
        )
        fill_rows(
            self.quota_table,
            [
                [
                    q["person"],
                    q["weekend"]["initial"],
                    q["weekend"]["assigned"],
                    q["weekend"]["remaining"],
                    q["ferie"]["initial"],
                    q["ferie"]["assigned"],
                    q["ferie"]["remaining"],
                ]
                for q in attribution.get("quotas", [])
            ],
        )
        info = [
            f"Solveur : {solver.get('name', '?')} {solver.get('version', '')}",
            f"Statut : {solver.get('status', '?')}",
            f"Workers : {solver.get('num_search_workers', '?')}",
            f"Seed : {solver.get('random_seed', '?')}",
            f"Temps : {solver.get('wall_time_s', '?')} s",
            "",
        ]
        warnings = attribution.get("warnings", [])
        info.append("Avertissements :")
        if warnings:
            info.extend(f"- {w}" for w in warnings)
        else:
            info.append("Aucun.")
        self.solver_text.setPlainText("\n".join(info))

    def clear(self) -> None:
        for card in self.metrics.values():
            card.set_value("—")
        for table in (self.assign_table, self.empty_table, self.red_table, self.quota_table):
            table.setRowCount(0)
        self.solver_text.clear()
