from __future__ import annotations

import sys

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from .main_window import MainWindow
from .styles import DARK_STYLESHEET, dark_palette


def _pick_font(app: QApplication) -> None:
    families = set(QFontDatabase.families())
    for name in ("Helvetica Neue", "Arial", "DejaVu Sans", "Noto Sans"):
        if name in families:
            app.setFont(QFont(name, 12))
            return


def apply_theme(app: QApplication) -> None:
    """Applique le thème sombre de façon cohérente aux widgets et dialogues."""
    app.setStyle("Fusion")
    _pick_font(app)
    app.setPalette(dark_palette())
    app.setStyleSheet(DARK_STYLESHEET)


def main(argv: list[str] | None = None) -> int:
    app = QApplication.instance() or QApplication(argv or sys.argv)
    app.setApplicationName("Gardes radiologues")
    app.setOrganizationName("Projet gardes")
    apply_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
