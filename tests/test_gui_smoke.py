from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QPalette

from gardes_gui.app import apply_theme
from gardes_gui.main_window import MainWindow


def test_main_window_full_flow(
    qapp, pdf: Path, planning_xlsx: Path, wishes_xlsx: Path, tmp_path: Path
) -> None:
    window = MainWindow()
    assert window.stack.count() == 6
    assert window.stack.currentIndex() == 0

    window.load_inputs(
        str(pdf),
        str(planning_xlsx),
        str(wishes_xlsx),
        str(tmp_path / "run"),
    )
    assert window.stack.currentIndex() == 1
    assert window.planning_view.metrics["holes"].value_label.text() == "88"

    window.go_to_credit()
    assert window.stack.currentIndex() == 2
    assert window.credit_view.table.rowCount() == 12
    assert window.credit_view.metrics["people"].value_label.text() == "12"
    assert window.credit_view.metrics["weekend"].value_label.text() == "82"
    assert window.credit_view.metrics["ferie"].value_label.text() == "8"

    window.validate_credit()
    assert window.stack.currentIndex() == 3
    assert window.wishes_view.metrics["people"].value_label.text() == "14"
    assert window.wishes_view.metrics["volunteer"].value_label.text() == "227"

    window.solve_now()
    assert window.stack.currentIndex() == 4
    assert window.attribution_view.metrics["coverage"].value_label.text() == "87/88"
    assert window.attribution_view.metrics["red"].value_label.text() == "3"
    assert window.attribution_view.metrics["green"].value_label.text() == "74"

    window.export_now()
    assert window.stack.currentIndex() == 5
    assert window.export_view.metrics["names"].value_label.text() == "87"
    assert window.export_view.metrics["empty"].value_label.text() == "1"
    assert "RAPPORT DE GARDES" in window.export_view.report_view.toPlainText()
    window.close()


def test_solve_in_thread(
    qapp, pdf: Path, planning_xlsx: Path, wishes_xlsx: Path, tmp_path: Path
) -> None:
    window = MainWindow()
    window.load_inputs(
        str(pdf),
        str(planning_xlsx),
        str(wishes_xlsx),
        str(tmp_path / "run"),
    )
    window.go_to_credit()
    window.validate_credit()
    window.on_solve()
    assert window.worker is not None
    assert window.worker.wait(20_000)
    qapp.processEvents()
    assert window.stack.currentIndex() == 4
    assert window.attribution_view.metrics["coverage"].value_label.text() == "87/88"
    window.close()


def test_credit_table_contains_only_assignable_people(
    qapp, pdf: Path, planning_xlsx: Path, wishes_xlsx: Path, tmp_path: Path
) -> None:
    window = MainWindow()
    window.load_inputs(
        str(pdf),
        str(planning_xlsx),
        str(wishes_xlsx),
        str(tmp_path / "run"),
    )
    window.go_to_credit()
    table = window.credit_view.table
    names = {table.item(row, 0).text() for row in range(table.rowCount())}
    assert len(names) == 12
    assert "Lambert" in names
    assert "Moreau" not in names  # pré-rempli
    assert "Aubert" not in names  # urgentiste
    assert "Jost" not in names  # quota 0
    assert "Schwarz" not in names
    # Lambert : 4 samedis, 4 dimanches, 0 férié, période complète.
    assert table.item(0, 0).text() == "Lambert"
    assert table.item(0, 1).text() == "4"
    assert table.item(0, 2).text() == "4"
    assert table.item(0, 3).text() == "0"
    assert table.item(0, 4).text() == "—"
    window.close()


def test_dark_theme_is_applied(qapp) -> None:
    apply_theme(qapp)
    assert qapp.palette().color(QPalette.ColorRole.Window).name() == "#0f1115"
    assert qapp.palette().color(QPalette.ColorRole.WindowText).name() == "#e6e9ef"
    assert "#0f1115" in qapp.styleSheet()
    assert "#3b82f6" in qapp.styleSheet()
