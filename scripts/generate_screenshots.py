from __future__ import annotations

import os
import shutil
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from gardes_gui.app import apply_theme  # noqa: E402
from gardes_gui.main_window import MainWindow  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
OUT = ROOT / "docs" / "screenshots"


def main() -> None:
    app = QApplication.instance() or QApplication([])
    apply_theme(app)
    OUT.mkdir(parents=True, exist_ok=True)

    # Chemins neutres dans les captures : aucun nom d'utilisateur local.
    demo = Path("/tmp/gardes-demo")
    shutil.rmtree(demo, ignore_errors=True)
    (demo / "examples").mkdir(parents=True)
    for example in EXAMPLES.iterdir():
        if example.is_file():
            shutil.copy2(example, demo / "examples" / example.name)
    workdir = demo / "run"
    workdir.mkdir(parents=True, exist_ok=True)

    window = MainWindow()
    window.resize(1240, 820)
    window.welcome_view.workdir_row.set_path(str(workdir))
    window.show()
    app.processEvents()

    def shot(name: str) -> None:
        app.processEvents()
        window.grab().save(str(OUT / name))

    shot("00-welcome.png")
    window.load_inputs(
        str(demo / "examples" / "exemple-calcul-gardes.pdf"),
        str(demo / "examples" / "exemple-planning-vide.xlsx"),
        str(demo / "examples" / "exemple-souhaits-garde.xlsx"),
        str(workdir),
    )
    shot("01-planning.png")
    window.go_to_credit()
    shot("02-credit.png")
    window.validate_credit()
    shot("03-wishes.png")
    window.solve_now()
    shot("04-attribution.png")
    window.export_now()
    shot("05-export.png")
    window.close()
    shutil.rmtree(demo, ignore_errors=True)


if __name__ == "__main__":
    main()
