from __future__ import annotations

from openpyxl.cell.cell import Cell

STATUS_GREEN = "FF00FF00"
STATUS_CYAN = "FF00FFFF"
STATUS_RED = "FFFF0000"
WHITE = "FFFFFFFF"

# Thème Office standard (index OOXML : 0 = lt1, 1 = dk1, 2 = lt2, 3 = dk2,
# 4..9 = accents, 10 = hlink, 11 = folHlink).
THEME_RGB: dict[int, str] = {
    0: "FFFFFFFF",
    1: "FF000000",
    2: "FFEEECE1",
    3: "FF1F497D",
    4: "FF4F81BD",
    5: "FFC0504D",
    6: "FF9BBB59",
    7: "FF8064A2",
    8: "FF4BACC6",
    9: "FFF79646",
    10: "FF0000FF",
    11: "FF800080",
}


def normalize_rgb(rgb: str | None) -> str | None:
    if rgb is None:
        return None
    value = str(rgb).upper()
    if len(value) == 6:
        value = "FF" + value
    if len(value) == 8:
        return value
    return None


def read_fill(cell: Cell) -> tuple[str | None, str]:
    """Retourne (rgb normalisé ou None, description brute)."""
    fill = cell.fill
    if fill is None or fill.fill_type != "solid":
        return None, "none"
    color = fill.start_color
    if color is None:
        return None, "none"
    if color.type == "rgb":
        rgb = normalize_rgb(color.rgb)
        return rgb, rgb or "rgb?"
    if color.type == "theme":
        base = THEME_RGB.get(int(color.theme))
        if base is None:
            return None, f"theme{color.theme}"
        return base, f"theme{color.theme}"
    if color.type == "indexed":
        return None, f"indexed{color.indexed}"
    return None, str(color.type)


def is_white(rgb: str | None) -> bool:
    return rgb == WHITE


def is_gray(rgb: str | None) -> bool:
    if not rgb or len(rgb) != 8:
        return False
    r, g, b = int(rgb[2:4], 16), int(rgb[4:6], 16), int(rgb[6:8], 16)
    return r == g == b


def is_neutral(rgb: str | None, base_rgb: str | None) -> bool:
    """Neutre : pas de fond, fond de ligne, blanc ou gris."""
    return rgb is None or rgb == base_rgb or is_white(rgb) or is_gray(rgb)


def status_from_rgb(rgb: str | None) -> str | None:
    if rgb == STATUS_GREEN:
        return "volunteer"
    if rgb == STATUS_CYAN:
        return "vacation"
    if rgb == STATUS_RED:
        return "non_dispo"
    return None


def is_known_color(rgb: str | None, base_rgb: str | None) -> bool:
    return is_neutral(rgb, base_rgb) or status_from_rgb(rgb) is not None
