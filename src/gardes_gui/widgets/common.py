from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QSizePolicy,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
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
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
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
