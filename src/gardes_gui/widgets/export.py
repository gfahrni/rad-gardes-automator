from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .common import Card, MetricCard, SectionHeader


class ExportView(QWidget):
    restart_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._xlsx: Path | None = None
        self._report: Path | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        layout.addWidget(
            SectionHeader(
                "6. Export",
                "Planning rempli et rapport. Les fichiers sources ne sont jamais "
                "modifiés. Un run par période, sans reprise d'un planning précédent.",
            )
        )

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(12)
        self.metrics = {
            "names": MetricCard("Noms écrits"),
            "empty": MetricCard("Trous restants"),
            "fixed": MetricCard("Fixes préservées"),
            "red": MetricCard("Rouges forcés"),
        }
        for i, card in enumerate(self.metrics.values()):
            metrics.addWidget(card, 0, i)
        layout.addLayout(metrics)

        paths_card = Card()
        self.xlsx_label = QLabel("")
        self.report_label = QLabel("")
        self.xlsx_label.setWordWrap(True)
        self.report_label.setWordWrap(True)
        paths_card.layout.addWidget(QLabel("Fichiers produits"))
        paths_card.layout.addWidget(self.xlsx_label)
        paths_card.layout.addWidget(self.report_label)

        buttons = QHBoxLayout()
        self.open_xlsx = QPushButton("Ouvrir le planning")
        self.open_report = QPushButton("Ouvrir le rapport")
        self.open_folder = QPushButton("Ouvrir le dossier")
        buttons.addWidget(self.open_xlsx)
        buttons.addWidget(self.open_report)
        buttons.addWidget(self.open_folder)
        paths_card.layout.addLayout(buttons)
        layout.addWidget(paths_card)

        report_card = Card()
        report_card.layout.addWidget(QLabel("Rapport"))
        self.report_view = QPlainTextEdit()
        self.report_view.setReadOnly(True)
        report_card.layout.addWidget(self.report_view)
        layout.addWidget(report_card, 1)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self.restart_button = QPushButton("Nouveau run")
        self.restart_button.setObjectName("primary")
        footer.addWidget(self.restart_button)
        layout.addLayout(footer)

        self.open_xlsx.clicked.connect(lambda: self._open(self._xlsx))
        self.open_report.clicked.connect(lambda: self._open(self._report))
        self.open_folder.clicked.connect(self._open_folder)
        self.restart_button.clicked.connect(self.restart_requested)

    def populate(
        self,
        xlsx: str | Path,
        report: str | Path,
        report_text: str,
        attribution: dict,
    ) -> None:
        self._xlsx = Path(xlsx)
        self._report = Path(report)
        objective = attribution.get("objective", {})
        counts = attribution.get("counts", {})
        self.metrics["names"].set_value(counts.get("filled", "?"))
        self.metrics["empty"].set_value(counts.get("empty", "?"))
        self.metrics["fixed"].set_value(counts.get("fixed", "?"))
        self.metrics["red"].set_value(objective.get("red_forced", "?"))
        self.xlsx_label.setText(f"Planning rempli : {self._xlsx}")
        self.report_label.setText(f"Rapport : {self._report}")
        self.report_view.setPlainText(report_text)

    def _open(self, path: Path | None) -> None:
        if path is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _open_folder(self) -> None:
        folder = self._xlsx.parent if self._xlsx else None
        if folder is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def clear(self) -> None:
        self._xlsx = None
        self._report = None
        self.xlsx_label.clear()
        self.report_label.clear()
        self.report_view.clear()
        for card in self.metrics.values():
            card.set_value("—")
