from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..paths import default_workdir, examples_dir
from .common import Card, FileRow, SectionHeader


class WelcomeView(QWidget):
    start_requested = Signal(str, str, str, str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        layout.addWidget(
            SectionHeader(
                "Préparer une nouvelle période",
                "Choisis les trois documents de référence. Ce run est complet : "
                "aucune reprise d'un planning précédent.",
            )
        )

        card = Card()
        self.pdf_row = FileRow("PDF des gardes", "exemple-calcul-gardes.pdf")
        self.planning_row = FileRow("Planning Excel", "exemple-planning-vide.xlsx")
        self.wishes_row = FileRow("Souhaits Excel", "exemple-souhaits-garde.xlsx")
        self.workdir_row = FileRow(
            "Dossier de sortie", str(default_workdir()), directory=True
        )
        self.workdir_row.line_edit.setText(str(default_workdir()))
        card.layout.addWidget(self.pdf_row)
        card.layout.addWidget(self.planning_row)
        card.layout.addWidget(self.wishes_row)
        card.layout.addWidget(self.workdir_row)

        note = QLabel(
            "Le planning est scanné en premier : c'est lui qui identifie les "
            "personnes pré-remplies et le pool assignable."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        card.layout.addWidget(note)

        layout.addWidget(card)
        layout.addStretch(1)

        buttons = QHBoxLayout()
        self.examples_button = QPushButton("Charger les exemples")
        self.start_button = QPushButton("Commencer")
        self.start_button.setObjectName("primary")
        buttons.addWidget(self.examples_button)
        buttons.addStretch(1)
        buttons.addWidget(self.start_button)
        layout.addLayout(buttons)

        self.pdf_row.button.clicked.connect(
            lambda: self._pick_file(self.pdf_row, "Choisir le PDF", "PDF (*.pdf)")
        )
        self.planning_row.button.clicked.connect(
            lambda: self._pick_file(
                self.planning_row, "Choisir le planning", "Excel (*.xlsx *.xlsm)"
            )
        )
        self.wishes_row.button.clicked.connect(
            lambda: self._pick_file(
                self.wishes_row, "Choisir les souhaits", "Excel (*.xlsx *.xlsm)"
            )
        )
        self.workdir_row.button.clicked.connect(self._pick_directory)
        self.examples_button.clicked.connect(self.load_examples)
        self.start_button.clicked.connect(self._start)

    # ------------------------------------------------------------------ helpers
    def _pick_file(self, row: FileRow, title: str, file_filter: str) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            row.path() or str(Path.home()),
            file_filter,
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if path:
            row.set_path(path)

    def _pick_directory(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            "Choisir le dossier de sortie",
            self.workdir_row.path() or str(Path.home()),
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if path:
            self.workdir_row.set_path(path)

    def load_examples(self) -> None:
        examples = examples_dir()
        files = {
            "pdf": examples / "exemple-calcul-gardes.pdf",
            "planning": examples / "exemple-planning-vide.xlsx",
            "wishes": examples / "exemple-souhaits-garde.xlsx",
        }
        missing = [str(p) for p in files.values() if not p.exists()]
        if missing:
            QMessageBox.warning(
                self,
                "Exemples introuvables",
                "Fichiers absents :\n" + "\n".join(missing),
            )
            return
        self.pdf_row.set_path(str(files["pdf"]))
        self.planning_row.set_path(str(files["planning"]))
        self.wishes_row.set_path(str(files["wishes"]))
        self.workdir_row.set_path(str(default_workdir()))

    def _start(self) -> None:
        pdf, planning, wishes, workdir = (
            self.pdf_row.path(),
            self.planning_row.path(),
            self.wishes_row.path(),
            self.workdir_row.path(),
        )
        if not all((pdf, planning, wishes, workdir)):
            QMessageBox.warning(
                self,
                "Fichiers manquants",
                "Choisis le PDF, le planning, les souhaits et le dossier de sortie.",
            )
            return
        self.start_requested.emit(pdf, planning, wishes, workdir)
