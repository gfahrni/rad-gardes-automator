from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QPalette

from gardes_gui.app import apply_theme
from gardes_gui.main_window import MainWindow
from gardes_gui.paths import default_workdir


def test_simple_window_defaults(qapp) -> None:
    window = MainWindow()
    assert window.pdf_row.path() == ""
    assert window.planning_row.path() == ""
    assert window.wishes_row.path() == ""
    assert window.workdir_row.path() == str(default_workdir())
    assert Path(window._start_directory()) == Path(window.workdir_row.path())
    assert window.result_card.isHidden()
    window.close()


def test_load_examples_and_run(
    qapp, pdf: Path, planning_xlsx: Path, wishes_xlsx: Path, tmp_path: Path
) -> None:
    window = MainWindow()
    window.load_examples()
    assert window.pdf_row.path().endswith("exemple-calcul-gardes.pdf")
    assert window.planning_row.path().endswith("exemple-planning-vide.xlsx")
    assert window.wishes_row.path().endswith("exemple-souhaits-garde.xlsx")
    assert window.workdir_row.path() == str(default_workdir())

    workdir = tmp_path / "run"
    window.load_inputs(str(pdf), str(planning_xlsx), str(wishes_xlsx), str(workdir))
    window.run_now()

    assert not window.result_card.isHidden()
    assert window.coverage_metric.value_label.text() == "87/88"
    assert window.red_metric.value_label.text() == "3"
    assert window.green_metric.value_label.text() == "74"
    assert window.hole_metric.value_label.text() == "1"
    assert "RAPPORT DE GARDES" in window.report_view.toPlainText()
    assert (workdir / "planning-rempli.xlsx").exists()
    assert (workdir / "rapport.txt").exists()
    # V7 n'écrit que les deux sorties demandées, pas les JSON intermédiaires.
    assert {p.name for p in workdir.iterdir()} == {"planning-rempli.xlsx", "rapport.txt"}
    window.close()


def test_run_in_thread(
    qapp, pdf: Path, planning_xlsx: Path, wishes_xlsx: Path, tmp_path: Path
) -> None:
    window = MainWindow()
    window.load_inputs(
        str(pdf),
        str(planning_xlsx),
        str(wishes_xlsx),
        str(tmp_path / "run"),
    )
    window.start_run()
    assert window.worker is not None
    assert window.worker.wait(30_000)
    for _ in range(3):
        qapp.processEvents()
    assert window.worker is None
    assert not window.result_card.isHidden()
    assert window.coverage_metric.value_label.text() == "87/88"
    assert window.run_button.isEnabled()
    window.close()


def test_dark_theme_is_applied(qapp) -> None:
    apply_theme(qapp)
    assert qapp.palette().color(QPalette.ColorRole.Window).name() == "#0f1115"
    assert qapp.palette().color(QPalette.ColorRole.WindowText).name() == "#e6e9ef"
    assert "#0f1115" in qapp.styleSheet()
    assert "#3b82f6" in qapp.styleSheet()
