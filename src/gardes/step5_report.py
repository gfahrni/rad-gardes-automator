from __future__ import annotations

from collections import defaultdict
from pathlib import Path


def _line(char: str = "=", width: int = 78) -> str:
    return char * width


def _fmt_slot(slot: str) -> str:
    return {"day": "jour", "evening": "soir"}.get(slot, slot)


def render_report(
    *,
    planning: dict,
    attribution: dict,
    calcul: dict | None = None,
) -> str:
    lines: list[str] = []
    period = attribution.get("period") or planning.get("period", {})
    lines.append("RAPPORT DE GARDES")
    lines.append(_line())
    lines.append(f"Période : {period.get('start')} -> {period.get('end')}")
    source = attribution.get("inputs", {})
    planning_source = planning.get("source", {}).get("path")
    if planning_source:
        lines.append(f"Planning source : {planning_source}")
    elif source:
        lines.append(f"Planning source : {source.get('planning', {}).get('path', 'n/a')}")
    solver = attribution.get("solver", {})
    lines.append(
        "Solveur : {} {} ({})".format(
            solver.get("name", "n/a"),
            solver.get("version", ""),
            solver.get("status", "n/a"),
        ).strip()
    )
    objective = attribution.get("objective", {})
    counts = attribution.get("counts", {})
    lines.append(
        "Objectif : couverture {}/{} | rouges {} | verts {}".format(
            objective.get("coverage", counts.get("filled", "?")),
            counts.get("holes", "?"),
            objective.get("red_forced", "?"),
            objective.get("green", "?"),
        )
    )
    lines.append("")
    lines.append("COMPTES")
    lines.append(_line("-"))
    for key in ("holes", "filled", "empty", "fixed", "weekend_holes", "ferie_holes"):
        if key in counts:
            lines.append(f"{key:16s} : {counts[key]}")
    lines.append("")

    assignments = sorted(
        attribution.get("assignments", []),
        key=lambda a: (a["date"], 0 if a["slot"] == "day" else 1, a.get("cell", "")),
    )
    lines.append(f"AFFECTATIONS ({len(assignments)})")
    lines.append(_line("-"))
    if not assignments:
        lines.append("Aucune.")
    for a in assignments:
        red = " [ROUGE FORCÉ]" if a.get("forced_red") else ""
        lines.append(
            f"{a['date']} | {_fmt_slot(a['slot']):5s} | {a['category']:7s} | "
            f"{a.get('cell', ''):5s} | {a['person']}{red}"
        )
    lines.append("")

    empty = sorted(attribution.get("empty_holes", []), key=lambda h: (h["date"], h["slot"]))
    lines.append(f"TROUS NON POURVUS ({len(empty)})")
    lines.append(_line("-"))
    if not empty:
        lines.append("Aucun.")
    for hole in empty:
        reasons = hole.get("reasons", [])
        reason_text = "; ".join(
            f"{r.get('person')}: {r.get('reason')}"
            + (f" ({r.get('window')})" if r.get("window") else "")
            for r in reasons
        )
        lines.append(
            f"{hole['date']} | {_fmt_slot(hole['slot']):5s} | {hole['category']:7s} | "
            f"{hole.get('hole_id', '')} | {reason_text or 'aucune raison détaillée'}"
        )
    lines.append("")

    quotas = attribution.get("quotas", [])
    lines.append(f"QUOTAS RESTANTS ({len(quotas)})")
    lines.append(_line("-"))
    if not quotas:
        lines.append("Aucun.")
    for q in quotas:
        w = q.get("weekend", {})
        f = q.get("ferie", {})
        lines.append(
            f"{q['person']:12s} | week-end {w.get('initial', '?'):>2}/{w.get('assigned', '?'):>2}/"
            f"{w.get('remaining', '?'):>2} | fériés {f.get('initial', '?'):>2}/"
            f"{f.get('assigned', '?'):>2}/{f.get('remaining', '?'):>2}"
        )
    lines.append("")

    reds = attribution.get("red_forced", [])
    lines.append(f"ROUGES FORCÉS ({len(reds)})")
    lines.append(_line("-"))
    if not reds:
        lines.append("Aucun.")
    for r in reds:
        lines.append(
            f"{r.get('date')} | {_fmt_slot(r.get('slot', '')):5s} | {r.get('person')} | "
            f"{r.get('reason', '')}"
        )
    lines.append("")

    fixed_by_name: dict[str, list[str]] = defaultdict(list)
    for slot in planning.get("slots", []):
        if slot["status"] == "fixed" and slot.get("fixed_name"):
            fixed_by_name[slot["fixed_name"]].append(slot["cell"])
    lines.append(f"PRÉ-REMPLIS NON TOUCHÉS ({len(fixed_by_name)})")
    lines.append(_line("-"))
    if not fixed_by_name:
        lines.append("Aucun.")
    for name in sorted(fixed_by_name):
        lines.append(f"{name:12s} : {', '.join(sorted(fixed_by_name[name]))}")
    lines.append("")

    warnings = list(attribution.get("warnings", []) or [])
    if not warnings:
        warnings = list((calcul or {}).get("warnings", []) or [])
    lines.append("AVERTISSEMENTS")
    lines.append(_line("-"))
    if not warnings:
        lines.append("Aucun.")
    for warning in warnings:
        lines.append(f"- {warning}")
    lines.append("")
    return "\n".join(lines)


def write_report(path: str | Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
        if not text.endswith("\n"):
            f.write("\n")
