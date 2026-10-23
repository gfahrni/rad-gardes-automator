from __future__ import annotations

from PySide6.QtGui import QColor, QPalette

# Palette sombre « bleu nuit / ardoise ».
BG = "#0f1115"
SURFACE = "#171a21"
SURFACE_ALT = "#1d212a"
SIDEBAR = "#12151b"
HEADER = "#0d1b2a"
BORDER = "#2a303c"
TEXT = "#e6e9ef"
MUTED = "#9aa4b2"
ACCENT = "#5b9dff"
ACCENT_STRONG = "#3b82f6"
SUCCESS = "#4ade80"
DANGER = "#f87171"
WARNING = "#fbbf24"
TABLE_ALT = "#181c24"
SELECTION = "#243a5e"


def dark_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(BG))
    p.setColor(QPalette.ColorRole.WindowText, QColor(TEXT))
    p.setColor(QPalette.ColorRole.Base, QColor("#141820"))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(TABLE_ALT))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor("#202531"))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT))
    p.setColor(QPalette.ColorRole.Text, QColor(TEXT))
    p.setColor(QPalette.ColorRole.Button, QColor(SURFACE_ALT))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT))
    p.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.Link, QColor(ACCENT))
    p.setColor(QPalette.ColorRole.Highlight, QColor("#2f5fa8"))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor("#6b7280"))
    p.setColor(QPalette.ColorRole.Light, QColor(BORDER))
    p.setColor(QPalette.ColorRole.Midlight, QColor("#222834"))
    p.setColor(QPalette.ColorRole.Dark, QColor("#080a0d"))
    p.setColor(QPalette.ColorRole.Mid, QColor(SURFACE))
    p.setColor(QPalette.ColorRole.Shadow, QColor("#000000"))
    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        p.setColor(QPalette.ColorGroup.Disabled, role, QColor("#5b6472"))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor("#15181e"))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, QColor("#161a21"))
    return p


DARK_STYLESHEET = """
QMainWindow { background-color: #0f1115; }
QWidget { color: #e6e9ef; font-size: 13px; }
QFrame#header { background-color: #0d1b2a; border-bottom: 1px solid #243247; }
QLabel#appTitle { color: #f8fafc; font-size: 20px; font-weight: 700; }
QLabel#appSubtitle { color: #9fb3c8; font-size: 12px; }
QLabel#sectionTitle { color: #8ab4ff; font-size: 18px; font-weight: 700; }
QLabel#sectionSubtitle { color: #9aa4b2; }
QLabel#muted { color: #9aa4b2; }
QLabel#metricValue { color: #dbeafe; font-size: 22px; font-weight: 700; }
QLabel#metricLabel { color: #9aa4b2; font-size: 11px; }
QLabel#stepItem {
    padding: 10px 12px; color: #8b96a6;
    border-left: 4px solid transparent;
}
QLabel#stepItem[active="true"] {
    background: #1b2a41; color: #dbeafe; font-weight: 700;
    border-left: 4px solid #5b9dff;
}
QLabel#stepItem[done="true"] { color: #4ade80; }
QFrame#card {
    background: #171a21; border: 1px solid #2a303c; border-radius: 10px;
}
QFrame#sidebar { background: #12151b; border-right: 1px solid #2a303c; }

QPushButton {
    background: #1d212a; color: #e6e9ef; border: 1px solid #343b47;
    border-radius: 7px; padding: 8px 14px;
}
QPushButton:hover { background: #252b36; border-color: #46505f; }
QPushButton:pressed { background: #141820; }
QPushButton:disabled { color: #5b6472; background: #161a21; border-color: #242a33; }
QPushButton#primary {
    background: #3b82f6; color: white; border: none; font-weight: 600;
    padding: 9px 18px;
}
QPushButton#primary:hover { background: #4c8dff; }
QPushButton#primary:pressed { background: #2563eb; }
QPushButton#primary:disabled { background: #23324a; color: #6b7a8f; }
QPushButton#danger {
    color: #fca5a5; border-color: #5a2a2e; background: #2a181b;
}
QPushButton#danger:hover { background: #3a1f24; }

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background: #141820; color: #e6e9ef; border: 1px solid #343b47;
    border-radius: 6px; padding: 6px;
    selection-background-color: #2f5fa8; selection-color: white;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #5b9dff;
}
QComboBox QAbstractItemView {
    background: #1d212a; color: #e6e9ef; border: 1px solid #343b47;
    selection-background-color: #2f5fa8; selection-color: white;
}
QCheckBox { color: #e6e9ef; spacing: 8px; }
QCheckBox::indicator {
    width: 16px; height: 16px; border: 1px solid #46505f;
    border-radius: 4px; background: #141820;
}
QCheckBox::indicator:checked { background: #3b82f6; border-color: #5b9dff; }

QTableWidget {
    background: #141820; alternate-background-color: #181c24; color: #e6e9ef;
    border: 1px solid #2a303c; border-radius: 8px; gridline-color: #252b36;
    selection-background-color: #243a5e; selection-color: #f8fafc;
}
QTableWidget::item { padding: 4px; }
QTableWidget::item:selected { background: #243a5e; color: #f8fafc; }
QHeaderView::section {
    background: #202531; color: #b9c7d9; padding: 7px;
    border: none; border-bottom: 1px solid #2f3642; font-weight: 600;
}
QTableCornerButton::section { background: #202531; border: none; }

QTabWidget::pane {
    border: 1px solid #2a303c; border-radius: 8px; background: #141820;
}
QTabBar::tab {
    background: #171a21; color: #9aa4b2; padding: 8px 14px;
    border: 1px solid #2a303c; border-bottom: none;
    border-top-left-radius: 6px; border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected { background: #202531; color: #dbeafe; }
QTabBar::tab:hover { color: #e6e9ef; }

QPlainTextEdit, QTextEdit {
    background: #0f1218; color: #d6dee9; border: 1px solid #2a303c;
    border-radius: 8px; selection-background-color: #2f5fa8;
}
QProgressBar {
    background: #141820; border: 1px solid #2a303c; border-radius: 6px;
    text-align: center; color: #e6e9ef;
}
QProgressBar::chunk { background: #3b82f6; border-radius: 6px; }

QScrollBar:vertical { background: #0f1115; width: 12px; margin: 0; }
QScrollBar::handle:vertical {
    background: #39404d; min-height: 24px; border-radius: 6px;
}
QScrollBar::handle:vertical:hover { background: #4b5563; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
QScrollBar:horizontal { background: #0f1115; height: 12px; margin: 0; }
QScrollBar::handle:horizontal {
    background: #39404d; min-width: 24px; border-radius: 6px;
}
QScrollBar::handle:horizontal:hover { background: #4b5563; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }

QToolTip {
    background: #202531; color: #e6e9ef; border: 1px solid #3a414d;
    padding: 6px;
}
QMenuBar, QMenu { background: #171a21; color: #e6e9ef; }
QMenuBar::item:selected, QMenu::item:selected { background: #243a5e; }
QStatusBar { background: #0d1015; color: #9aa4b2; }

QDialog, QMessageBox { background: #171a21; color: #e6e9ef; }
QDialog QLabel, QMessageBox QLabel { color: #e6e9ef; }
QDialog QTextEdit, QDialog QPlainTextEdit,
QMessageBox QTextEdit, QMessageBox QPlainTextEdit {
    background: #0f1218; color: #d6dee9; border: 1px solid #2a303c;
}
QDialogButtonBox QPushButton, QMessageBox QPushButton { min-width: 90px; }

QAbstractItemView {
    background: #141820; color: #e6e9ef;
    selection-background-color: #243a5e; selection-color: #f8fafc;
}
QFileDialog { background: #171a21; color: #e6e9ef; }
QFileDialog QWidget { background: #171a21; color: #e6e9ef; }
QFileDialog QTreeView, QFileDialog QListView {
    background: #141820; color: #e6e9ef; alternate-background-color: #181c24;
    border: 1px solid #2a303c;
    selection-background-color: #243a5e; selection-color: #f8fafc;
}
QFileDialog QHeaderView::section {
    background: #202531; color: #b9c7d9; border: none;
}
QFileDialog QToolButton {
    background: #1d212a; border: 1px solid #343b47;
    border-radius: 5px; padding: 4px;
}
QFileDialog QToolButton:hover { background: #252b36; }
QFileDialog QComboBox, QFileDialog QLineEdit {
    background: #141820; color: #e6e9ef; border: 1px solid #343b47;
}
QFileDialog QDialogButtonBox QPushButton {
    background: #1d212a; color: #e6e9ef; border: 1px solid #343b47;
}
QFileDialog QDialogButtonBox QPushButton:hover { background: #252b36; }
"""
