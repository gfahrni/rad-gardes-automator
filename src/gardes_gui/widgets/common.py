from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class MetricCard(QFrame):
    def __init__(self, label: str, value: str = "—", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(78)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        self.value_label = QLabel(value)
        self.value_label.setObjectName("metricValue")
        self.label = QLabel(label)
        self.label.setObjectName("metricLabel")
        layout.addWidget(self.value_label)
        layout.addWidget(self.label)
        layout.addStretch(1)

    def set_value(self, value: str) -> None:
        self.value_label.setText(str(value))


class Card(QFrame):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("card")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 14, 16, 14)
        self.layout.setSpacing(10)


class SectionHeader(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.title = QLabel(title)
        self.title.setObjectName("sectionTitle")
        self.subtitle = QLabel(subtitle)
        self.subtitle.setObjectName("sectionSubtitle")
        self.subtitle.setWordWrap(True)
        layout.addWidget(self.title)
        if subtitle:
            layout.addWidget(self.subtitle)

    def set_subtitle(self, text: str) -> None:
        self.subtitle.setText(text)


class FileRow(QWidget):
    def __init__(
        self,
        label: str,
        placeholder: str,
        *,
        directory: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.directory = directory
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        title = QLabel(label)
        title.setMinimumWidth(110)
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.button = QPushButton("Choisir…" if directory else "Parcourir…")
        layout.addWidget(title)
        layout.addWidget(self.line_edit, 1)
        layout.addWidget(self.button)

    def path(self) -> str:
        return self.line_edit.text().strip()

    def set_path(self, value: str) -> None:
        self.line_edit.setText(value)


def make_table(
    headers: list[str],
    *,
    editable: bool = False,
    stretch_last: bool = True,
    sorting: bool = False,
) -> QTableWidget:
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)
    table.setWordWrap(False)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    table.setEditTriggers(
        QTableWidget.EditTrigger.DoubleClicked
        | QTableWidget.EditTrigger.EditKeyPressed
        if editable
        else QTableWidget.EditTrigger.NoEditTriggers
    )
    table.setSortingEnabled(sorting)
    header = table.horizontalHeader()
    header.setStretchLastSection(stretch_last)
    header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    return table


def set_item(
    table: QTableWidget,
    row: int,
    col: int,
    value: object,
    *,
    editable: bool = False,
    align_right: bool = False,
    background: str | None = None,
    tooltip: str | None = None,
) -> QTableWidgetItem:
    item = QTableWidgetItem("" if value is None else str(value))
    flags = item.flags()
    if editable:
        flags |= Qt.ItemFlag.ItemIsEditable
    else:
        flags &= ~Qt.ItemFlag.ItemIsEditable
    item.setFlags(flags)
    if align_right:
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    if background:
        item.setBackground(QColor(background))
    if tooltip:
        item.setToolTip(tooltip)
    table.setItem(row, col, item)
    return item


def fill_rows(table: QTableWidget, rows: Iterable[list[object]]) -> None:
    rows = list(rows)
    sorting = table.isSortingEnabled()
    if sorting:
        table.setSortingEnabled(False)
    table.setRowCount(len(rows))
    for r, values in enumerate(rows):
        for c, value in enumerate(values):
            set_item(table, r, c, value)
    if sorting:
        table.setSortingEnabled(True)
