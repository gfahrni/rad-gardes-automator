from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from gardes.errors import GardesError

from .controller import PipelineController
from .state import PipelineState
from .widgets.attribution import AttributionView
from .widgets.credit import CreditGardesView
from .widgets.export import ExportView
from .widgets.planning import PlanningView
from .widgets.welcome import WelcomeView
from .widgets.wishes import WishesView
from .workers import SolveWorker

STEP_LABELS = [
    "1. Fichiers",
    "2. Planning",
    "3. Crédit de Gardes",
    "4. Souhaits",
    "5. Attribution",
    "6. Export",
]
STEP_HINTS = [
    "Choisis les trois documents de référence.",
    "Vérifie le planning et ses pré-remplis.",
    "Valide les crédits de gardes du run.",
    "Vérifie les souhaits.",
    "Analyse l'attribution.",
    "Récupère le planning et le rapport.",
]


class StepSidebar(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(210)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(2)
        title = QLabel("ÉTAPES")
        title.setObjectName("muted")
        title.setContentsMargins(14, 0, 0, 8)
        layout.addWidget(title)
        self.labels: list[QLabel] = []
        for label in STEP_LABELS:
            item = QLabel(label)
            item.setObjectName("stepItem")
            layout.addWidget(item)
            self.labels.append(item)
        layout.addStretch(1)
        footer = QLabel("V4 — thème sombre")
        footer.setObjectName("muted")
        footer.setContentsMargins(14, 8, 14, 0)
        footer.setWordWrap(True)
        layout.addWidget(footer)

    def set_current(self, index: int) -> None:
        for i, label in enumerate(self.labels):
            label.setProperty("active", i == index)
            label.setProperty("done", i < index)
            label.style().unpolish(label)
            label.style().polish(label)
            label.update()


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Gardes radiologues — V4")
        self.resize(1240, 820)
        self.controller = PipelineController()
        self.worker: SolveWorker | None = None
        self._busy = False

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
        self.title = QLabel("Gardes radiologues")
        self.title.setObjectName("appTitle")
        self.subtitle = QLabel("Hiver 2026/2027 — un run complet par période")
        self.subtitle.setObjectName("appSubtitle")
        titles.addWidget(self.title)
        titles.addWidget(self.subtitle)
        header_layout.addLayout(titles)
        header_layout.addStretch(1)
        self.restart_header = QPushButton("Recommencer")
        header_layout.addWidget(self.restart_header)
        root.addWidget(header)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        self.sidebar = StepSidebar()
        body.addWidget(self.sidebar)
        self.stack = QStackedWidget()
        self.welcome_view = WelcomeView()
        self.planning_view = PlanningView()
        self.credit_view = CreditGardesView()
        self.wishes_view = WishesView()
        self.attribution_view = AttributionView()
        self.export_view = ExportView()
        for view in (
            self.welcome_view,
            self.planning_view,
            self.credit_view,
            self.wishes_view,
            self.attribution_view,
            self.export_view,
        ):
            self.stack.addWidget(view)
        body.addWidget(self.stack, 1)
        root.addLayout(body, 1)
        self.setCentralWidget(central)

        self.welcome_view.start_requested.connect(self.on_start)
        self.planning_view.next_requested.connect(self.on_planning_next)
        self.credit_view.reload_requested.connect(self.on_reload)
        self.credit_view.validate_requested.connect(self.on_credit_validate)
        self.wishes_view.solve_requested.connect(self.on_solve)
        self.attribution_view.export_requested.connect(self.on_export)
        self.export_view.restart_requested.connect(self.on_restart)
        self.restart_header.clicked.connect(self.on_restart)

        self.statusBar().showMessage("Prêt.")
        self.show_step(0)

    # ------------------------------------------------------------------ navigation
    def show_step(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.sidebar.set_current(index)
        self.subtitle.setText(
            f"Hiver 2026/2027 — {STEP_HINTS[index]}"
        )

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
        self.statusBar().showMessage("Erreur — corrige les données puis réessaie.")

    # ------------------------------------------------------------------ actions
    def on_start(
        self,
        pdf: str,
        planning: str,
        wishes: str,
        workdir: str,
    ) -> None:
        try:
            self.controller.set_inputs(pdf, planning, wishes, workdir)
            data = self.controller.scan_planning()
            self.planning_view.populate(data)
            self.show_step(1)
            self.statusBar().showMessage(
                f"Planning scanné : {data['counts']['holes']} trous, "
                f"{data['counts']['fixed']} fixes."
            )
        except Exception as exc:  # noqa: BLE001
            self._error("Impossible de scanner le planning", exc)

    def on_planning_next(self) -> None:
        try:
            calcul = self.controller.build_calcul()
            self.credit_view.populate(calcul)
            self.show_step(2)
            self.statusBar().showMessage(
                f"Crédits chargés : {len(calcul['candidates'])} personnes assignables."
            )
        except Exception as exc:  # noqa: BLE001
            self._error("Impossible de lire le PDF", exc)

    def on_reload(self) -> None:
        try:
            calcul = self.controller.build_calcul()
            self.credit_view.populate(calcul)
            self.statusBar().showMessage("Crédits rechargés depuis le PDF.")
        except Exception as exc:  # noqa: BLE001
            self._error("Impossible de recharger le PDF", exc)

    def on_credit_validate(self) -> None:
        try:
            self.controller.validate_people()
            wishes = self.controller.scan_wishes()
            self.wishes_view.populate(wishes)
            self.show_step(3)
            self.statusBar().showMessage(
                f"Souhaits lus : {wishes['counts']['people']} personnes, "
                f"{wishes['counts']['dates']} dates."
            )
        except Exception as exc:  # noqa: BLE001
            self._error("Validation impossible", exc)

    def on_solve(self) -> None:
        if self.worker is not None:
            return
        self._busy = True
        self.wishes_view.solve_button.setEnabled(False)
        self.statusBar().showMessage("Résolution CP-SAT en cours…")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.worker = SolveWorker(self.controller, self)
        self.worker.solved.connect(self._on_solved)
        self.worker.failed.connect(self._on_solve_failed)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def _on_solved(self, attribution: dict) -> None:
        self.attribution_view.populate(attribution)
        self.show_step(4)
        self.statusBar().showMessage(
            "Attribution calculée : "
            f"{attribution['objective']['coverage']}/{attribution['counts']['holes']} "
            f"couverts, {attribution['objective']['red_forced']} rouges."
        )

    def _on_solve_failed(self, message: str) -> None:
        self._error("Résolution impossible", message)

    def _on_worker_finished(self) -> None:
        if self._busy:
            QApplication.restoreOverrideCursor()
            self._busy = False
        self.wishes_view.solve_button.setEnabled(True)
        if self.worker is not None:
            self.worker.deleteLater()
            self.worker = None

    def on_export(self) -> None:
        try:
            out_xlsx, report = self.controller.export()
            report_text = Path(report).read_text(encoding="utf-8")
            self.export_view.populate(
                out_xlsx, report, report_text, self.controller.state.attribution or {}
            )
            self.show_step(5)
            self.statusBar().showMessage(f"Export terminé : {out_xlsx}")
        except Exception as exc:  # noqa: BLE001
            self._error("Export impossible", exc)

    def on_restart(self) -> None:
        if self.worker is not None:
            QMessageBox.information(
                self,
                "Calcul en cours",
                "Attends la fin de la résolution avant de recommencer.",
            )
            return
        has_data = any(
            x is not None
            for x in (
                self.controller.state.planning,
                self.controller.state.calcul,
                self.controller.state.wishes,
                self.controller.state.attribution,
            )
        )
        if has_data:
            answer = QMessageBox.question(
                self,
                "Recommencer",
                "Recommencer un run depuis les fichiers ? L'état courant sera perdu.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.controller = PipelineController()
        for view in (
            self.planning_view,
            self.credit_view,
            self.wishes_view,
            self.attribution_view,
            self.export_view,
        ):
            if hasattr(view, "clear"):
                view.clear()
        self.show_step(0)
        self.statusBar().showMessage("Prêt pour un nouveau run.")

    # ------------------------------------------------------------------ test hooks
    def load_inputs(
        self,
        pdf: str,
        planning: str,
        wishes: str,
        workdir: str,
    ) -> None:
        self.on_start(pdf, planning, wishes, workdir)

    def go_to_credit(self) -> None:
        self.on_planning_next()

    def validate_credit(self) -> None:
        self.on_credit_validate()

    def solve_now(self) -> None:
        attribution = self.controller.solve()
        self.attribution_view.populate(attribution)
        self.show_step(4)

    def export_now(self) -> None:
        self.on_export()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.worker is not None:
            self.worker.wait(10_000)
        super().closeEvent(event)
