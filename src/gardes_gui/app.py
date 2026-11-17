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


def _self_test() -> int:
    """Exécute le pipeline complet sur les exemples embarqués, sans interface."""
    import tempfile
    from pathlib import Path

    from .controller import PipelineController
    from .paths import examples_dir

    examples = examples_dir()
    files = {
        "pdf": examples / "exemple-calcul-gardes.pdf",
        "planning": examples / "exemple-planning-vide.xlsx",
        "wishes": examples / "exemple-souhaits-garde.xlsx",
    }
    missing = [str(path) for path in files.values() if not path.exists()]
    if missing:
        print("Exemples manquants : " + ", ".join(missing))
        return 2

    with tempfile.TemporaryDirectory(prefix="rad-gardes-self-test-") as workdir:
        controller = PipelineController(persist=False)
        controller.set_inputs(
            files["pdf"],
            files["planning"],
            files["wishes"],
            Path(workdir),
        )
        attribution, out_xlsx, report = controller.run_complete()
        objective = attribution.get("objective", {})
        if objective.get("coverage") != 87:
            print(f"Couverture inattendue : {objective!r}")
            return 3
        if not out_xlsx.exists() or not report.exists():
            print("Sorties manquantes : planning-rempli.xlsx ou rapport.txt")
            return 4
    return 0


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv if argv is None else argv)
    if "--paths" in raw_argv:
        from pathlib import Path

        from .paths import bundle_root, default_workdir, examples_dir, user_home

        print(f"home      : {user_home()}")
        print(f"cwd       : {Path.cwd()}")
        print(f"bundle    : {bundle_root()}")
        print(f"examples  : {examples_dir()}")
        print(f"workdir   : {default_workdir()}")
        return 0
    if "--self-test" in raw_argv:
        return _self_test()

    smoke_test = "--smoke-test" in raw_argv
    qt_argv = [arg for arg in raw_argv if arg != "--smoke-test"]

    app = QApplication.instance() or QApplication(qt_argv)
    app.setApplicationName("RAD Gardes Automator")
    app.setOrganizationName("Projet gardes")
    apply_theme(app)
    window = MainWindow()
    window.show()
    if smoke_test:
        app.processEvents()
        window.close()
        return 0
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
