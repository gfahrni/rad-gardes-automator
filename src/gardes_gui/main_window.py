from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QCloseEvent, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from gardes.errors import GardesError

from .controller import PipelineController
from .paths import default_workdir, examples_dir
from .widgets.common import Card, FileRow, MetricCard, SectionHeader
from .workers import RunWorker


class MainWindow(QMainWindow):
    """Écran unique V7 : trois fichiers, un clic, deux sorties."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Gardes radiologues — V7")
        self.resize(1040, 860)
        self.controller = PipelineController(persist=False)
        self.worker: RunWorker | None = None
        self.last_xlsx: Path | None = None
        self.last_report: Path | None = None

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 14, 24, 14)
        titles = QVBoxLayout()
        titles.setSpacing(2)
        title = QLabel("Gardes radiologues")
        title.setObjectName("appTitle")
        subtitle = QLabel("V7 — trois fichiers, un clic, le planning et le rapport")
        subtitle.setObjectName("appSubtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header_layout.addLayout(titles)
        header_layout.addStretch(1)
        root.addWidget(header)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        layout.addWidget(
            SectionHeader(
                "Nouveau run",
                "Choisis le PDF des gardes, le planning Excel et les souhaits Excel. "
                "L'application valide et calcule tout en une fois.",
            )
        )

        inputs = Card()
        inputs.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.pdf_row = FileRow("PDF des gardes", "exemple-calcul-gardes.pdf")
        self.planning_row = FileRow("Planning Excel", "exemple-planning-vide.xlsx")
        self.wishes_row = FileRow("Souhaits Excel", "exemple-souhaits-garde.xlsx")
        self.workdir_row = FileRow("Dossier de sortie", str(default_workdir()), directory=True)
        self.workdir_row.set_path(str(default_workdir()))
        for row in (self.pdf_row, self.planning_row, self.wishes_row, self.workdir_row):
            inputs.layout.addWidget(row)

        note = QLabel(
            "Le dossier de sortie est créé si besoin. Le résultat y est écrit : "
            "planning-rempli.xlsx et rapport.txt."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        inputs.layout.addWidget(note)
        layout.addWidget(inputs)

        actions = QHBoxLayout()
        self.examples_button = QPushButton("Charger les exemples")
        self.run_button = QPushButton("Lancer")
        self.run_button.setObjectName("primary")
        actions.addWidget(self.examples_button)
        actions.addStretch(1)
        actions.addWidget(self.run_button)
        layout.addLayout(actions)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(6)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status_label = QLabel("Prêt.")
        self.status_label.setObjectName("muted")
        layout.addWidget(self.status_label)

        self.result_card = Card()
        self.result_card.setVisible(False)
        result_titles = QHBoxLayout()
        result_title = QLabel("Résultat")
        result_title.setObjectName("sectionTitle")
        result_titles.addWidget(result_title)
        result_titles.addStretch(1)
        self.open_folder_button = QPushButton("Ouvrir le dossier")
        result_titles.addWidget(self.open_folder_button)
        self.result_card.layout.addLayout(result_titles)

        metrics = QHBoxLayout()
        self.coverage_metric = MetricCard("Couverture")
        self.red_metric = MetricCard("Rouges")
        self.green_metric = MetricCard("Verts")
        self.hole_metric = MetricCard("Trous restants")
        for metric in (
            self.coverage_metric,
            self.red_metric,
            self.green_metric,
            self.hole_metric,
        ):
            metrics.addWidget(metric)
        self.result_card.layout.addLayout(metrics)

        self.report_view = QPlainTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setMinimumHeight(180)
        self.report_view.setPlaceholderText("Le rapport s'affiche ici après le calcul.")
        self.result_card.layout.addWidget(self.report_view, 1)

        self.result_hint = QLabel("")
        self.result_hint.setObjectName("muted")
        self.result_hint.setWordWrap(True)
        self.result_card.layout.addWidget(self.result_hint)

        result_actions = QHBoxLayout()
        self.open_xlsx_button = QPushButton("Ouvrir le planning rempli")
        self.open_report_button = QPushButton("Ouvrir le rapport")
        result_actions.addWidget(self.open_xlsx_button)
        result_actions.addWidget(self.open_report_button)
        result_actions.addStretch(1)
        self.result_card.layout.addLayout(result_actions)

        layout.addWidget(self.result_card, 1)
        root.addWidget(content, 1)
        self.setCentralWidget(central)

        # Signaux
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
        self.run_button.clicked.connect(self.start_run)
        self.open_folder_button.clicked.connect(self.open_folder)
        self.open_xlsx_button.clicked.connect(lambda: self._open(self.last_xlsx))
        self.open_report_button.clicked.connect(lambda: self._open(self.last_report))

        self.statusBar().showMessage("Prêt.")

    # ------------------------------------------------------------------ fichiers
    def _start_directory(self) -> str:
        documents = Path.home() / "Documents"
        return str(documents if documents.is_dir() else Path.home())

    def _pick_file(self, row: FileRow, title: str, file_filter: str) -> None:
        start = row.path()
        if start:
            path = Path(start)
            start = str(path.parent if path.is_file() else path)
        else:
            start = self._start_directory()
        selected, _ = QFileDialog.getOpenFileName(
            self,
            title,
            start,
            file_filter,
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if selected:
            row.set_path(selected)

    def _pick_directory(self) -> None:
        start = self.workdir_row.path() or str(default_workdir())
        path = Path(start)
        if not path.is_dir():
            start = self._start_directory()
        selected = QFileDialog.getExistingDirectory(
            self,
            "Choisir le dossier de sortie",
            start,
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if selected:
            self.workdir_row.set_path(selected)

    def load_examples(self) -> None:
        examples = examples_dir()
        files = {
            "pdf": examples / "exemple-calcul-gardes.pdf",
            "planning": examples / "exemple-planning-vide.xlsx",
            "wishes": examples / "exemple-souhaits-garde.xlsx",
        }
        missing = [str(path) for path in files.values() if not path.exists()]
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
        self._clear_result()
        self.status_label.setText("Exemples chargés. Clique sur « Lancer ».")

    # ------------------------------------------------------------------ run
    def _read_inputs(self) -> tuple[str, str, str, str] | None:
        pdf = self.pdf_row.path()
        planning = self.planning_row.path()
        wishes = self.wishes_row.path()
        workdir = self.workdir_row.path()
        if not all((pdf, planning, wishes, workdir)):
            QMessageBox.warning(
                self,
                "Fichiers manquants",
                "Choisis le PDF, le planning, les souhaits et le dossier de sortie.",
            )
            return None
        return pdf, planning, wishes, workdir

    def _prepare_run(self) -> bool:
        values = self._read_inputs()
        if values is None:
            return False
        self.controller = PipelineController(persist=False)
        try:
            self.controller.set_inputs(*values)
        except Exception as exc:  # noqa: BLE001
            self._error("Fichiers d'entrée", exc)
            return False
        self._clear_result()
        return True

    def start_run(self) -> None:
        if self.worker is not None:
            return
        if not self._prepare_run():
            return
        self._set_busy(True)
        self.status_label.setText("Calcul en cours…")
        self.worker = RunWorker(self.controller, self)
        self.worker.completed.connect(self._on_completed)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def _on_completed(self, payload: dict) -> None:
        self._show_result(payload)
        self.status_label.setText(
            f"Terminé — {payload['xlsx']}"
        )

    def _on_failed(self, message: str) -> None:
        self._set_busy(False)
        self._error("Calcul impossible", message)
        self.status_label.setText("Erreur — corrige les fichiers puis réessaie.")

    def _on_worker_finished(self) -> None:
        self._set_busy(False)
        if self.worker is not None:
            self.worker.deleteLater()
            self.worker = None

    def _show_result(self, payload: dict) -> None:
        attribution = payload["attribution"]
        objective = attribution.get("objective", {})
        counts = attribution.get("counts", {})
        coverage = objective.get("coverage", 0)
        holes = counts.get("holes", 0)
        self.coverage_metric.set_value(f"{coverage}/{holes}")
        self.red_metric.set_value(str(objective.get("red_forced", 0)))
        self.green_metric.set_value(str(objective.get("green", 0)))
        self.hole_metric.set_value(str(counts.get("empty", 0)))
        self.report_view.setPlainText(payload.get("report_text", ""))
        self.last_xlsx = Path(payload["xlsx"])
        self.last_report = Path(payload["report"])
        self.result_hint.setText(f"Écrit dans : {self.last_xlsx.parent}")
        self.result_card.setVisible(True)

    def _clear_result(self) -> None:
        self.result_card.setVisible(False)
        self.report_view.clear()
        self.result_hint.setText("")
        self.last_xlsx = None
        self.last_report = None

    def _set_busy(self, busy: bool) -> None:
        for row in (self.pdf_row, self.planning_row, self.wishes_row, self.workdir_row):
            row.line_edit.setEnabled(not busy)
            row.button.setEnabled(not busy)
        self.examples_button.setEnabled(not busy)
        self.run_button.setEnabled(not busy)
        self.run_button.setText("Calcul en cours…" if busy else "Lancer")
        self.progress.setVisible(busy)
        if busy:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()

    # ------------------------------------------------------------------ sorties
    def _open(self, path: Path | None) -> None:
        if path is None or not path.exists():
            QMessageBox.warning(self, "Fichier introuvable", "Le fichier n'existe pas encore.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def open_folder(self) -> None:
        if self.last_xlsx is not None and self.last_xlsx.parent.exists():
            self._open(self.last_xlsx.parent)
        else:
            self._open(Path(self.workdir_row.path() or default_workdir()))

    def _error(self, title: str, exc: Exception | str) -> None:
        message = str(exc)
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Critical)
        box.setWindowTitle(title)
        box.setText(message.splitlines()[0] if message else title)
        details = message if "\n" in message else ""
        if isinstance(exc, GardesError) and exc.details.get("errors"):
            details = "\n".join(exc.details["errors"])
        if details:
            box.setDetailedText(details)
        box.exec()

    # ------------------------------------------------------------------ tests
    def load_inputs(
        self,
        pdf: str,
        planning: str,
        wishes: str,
        workdir: str,
    ) -> None:
        self.pdf_row.set_path(str(pdf))
        self.planning_row.set_path(str(planning))
        self.wishes_row.set_path(str(wishes))
        self.workdir_row.set_path(str(workdir))

    def run_now(self) -> None:
        """Exécution synchrone, pour les tests."""
        if not self._prepare_run():
            return
        attribution, out_xlsx, report = self.controller.run_complete()
        payload = {
            "attribution": attribution,
            "xlsx": str(out_xlsx),
            "report": str(report),
            "report_text": Path(report).read_text(encoding="utf-8"),
        }
        self._show_result(payload)
        self.status_label.setText(f"Terminé — {payload['xlsx']}")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.information(
                self,
                "Calcul en cours",
                "Attends la fin du calcul avant de fermer l'application.",
            )
            event.ignore()
            return
        super().closeEvent(event)
