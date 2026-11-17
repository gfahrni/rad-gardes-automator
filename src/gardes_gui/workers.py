from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from .controller import PipelineController


class RunWorker(QThread):
    """Exécute le pipeline complet puis l'export dans un fil."""

    completed = Signal(dict)
    failed = Signal(str)

    def __init__(self, controller: PipelineController, parent=None):
        super().__init__(parent)
        self.controller = controller

    def run(self) -> None:  # noqa: D401 - point d'entrée du fil
        try:
            attribution, out_xlsx, report = self.controller.run_complete()
            self.completed.emit(
                {
                    "attribution": attribution,
                    "xlsx": str(out_xlsx),
                    "report": str(report),
                    "report_text": Path(report).read_text(encoding="utf-8"),
                }
            )
        except Exception as exc:  # noqa: BLE001 - remonte le message à l'UI
            self.failed.emit(str(exc))
