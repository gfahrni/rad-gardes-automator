from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from .controller import PipelineController


class SolveWorker(QThread):
    solved = Signal(dict)
    failed = Signal(str)

    def __init__(self, controller: PipelineController, parent=None):
        super().__init__(parent)
        self.controller = controller

    def run(self) -> None:  # noqa: D401 - thread entry point
        try:
            self.solved.emit(self.controller.solve())
        except Exception as exc:  # noqa: BLE001 - remonte le message à l'UI
            self.failed.emit(str(exc))
