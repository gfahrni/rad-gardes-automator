from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .errors import GardesError
from .jsonio import load_json, write_json
from .step1_pdf import load_calcul, parse_pdf, validate_calcul, write_calcul
from .step2_planning import parse_planning, write_planning_json
from .step3_wishes import parse_wishes, write_wishes
from .step4_solve import solve_attribution
from .step4_validate import validate_attribution
from .step5_excel import write_excel
from .step5_report import render_report, write_report


def _summary(data: dict) -> str:
    return ", ".join(f"{k}={v}" for k, v in data.items() if not isinstance(v, list))


def _print_calcul_table(data: dict) -> None:
    print(f"{'Nom':18s} {'Rôle':20s} {'WE':>3s} {'FER':>3s}  {'Actif':23s}  Flags")
    print("-" * 88)
    for p in data["people"]:
        flags = []
        if p.get("prefilled"):
            flags.append("pré-rempli")
        if p.get("fixed_priority"):
            flags.append("fixe")
        if p.get("assignable_weekend"):
            flags.append("candidat")
        print(
            f"{p['name']:18s} {p['role']:20s} {p['weekend_quota']:>3d} {p['holiday_quota']:>3d}  "
            f"{p['active_from']}..{p['active_to']}  {', '.join(flags)}"
        )
    print()
    print(f"Pré-remplis exclus : {', '.join(data.get('prefilled', [])) or 'aucun'}")
    print(f"Candidats assignables ({len(data.get('candidates', []))}) : "
          f"{', '.join(data.get('candidates', [])) or 'aucun'}")


def cmd_step2(args: argparse.Namespace) -> int:
    data = parse_planning(args.planning)
    write_planning_json(data, args.out)
    print(f"Planning écrit : {args.out}")
    print(_summary(data["counts"]))
    return 0


def cmd_step1(args: argparse.Namespace) -> int:
    data = parse_pdf(args.pdf, planning_path=args.planning)
    write_calcul(data, args.out)
    _print_calcul_table(data)
    print()
    print(f"JSON écrit : {args.out} (validated=false)")
    print(
        "Relis ce JSON. Si une valeur est fausse, corrige le PDF et relance ; "
        "sinon valide avec :\n"
        f"  gardes step1-validate --json {args.out}"
    )
    return 0


def cmd_step1_validate(args: argparse.Namespace) -> int:
    data = load_calcul(args.json)
    data = validate_calcul(data)
    write_calcul(data, args.json)
    print(f"Validation OK : {args.json}")
    print(f"{len(data['people'])} personnes, {len(data['candidates'])} candidats.")
    return 0


def cmd_step3(args: argparse.Namespace) -> int:
    calcul = load_json(args.calcul)
    planning = load_json(args.planning)
    data = parse_wishes(args.wishes, calcul, planning)
    write_wishes(data, args.out)
    print(f"Souhaits écrits : {args.out}")
    print(_summary(data["counts"]))
    print(f"Avertissements : {len(data['warnings'])}")
    for warning in data["warnings"]:
        print(f"  - {warning}")
    return 0


def cmd_step4(args: argparse.Namespace) -> int:
    calcul = load_json(args.calcul)
    planning = load_json(args.planning)
    wishes = load_json(args.souhaits)
    attribution = solve_attribution(
        calcul,
        planning,
        wishes,
        input_paths={"calcul": args.calcul, "planning": args.planning, "souhaits": args.souhaits},
        time_limit=args.time_limit,
    )
    write_json(args.out, attribution)
    print(f"Attribution écrite : {args.out}")
    print(f"Objectif : {attribution['objective']}")
    print(f"Comptes : {attribution['counts']}")
    print(f"Solveur : {attribution['solver']}")
    if attribution["empty_holes"]:
        print("Trous non pourvus :")
        for hole in attribution["empty_holes"]:
            print(f"  - {hole['date']} {hole['slot']} ({hole['category']})")
    return 0


def cmd_step5(args: argparse.Namespace) -> int:
    planning = load_json(args.planning_json)
    attribution = load_json(args.attribution)
    calcul = load_json(args.calcul)
    write_excel(
        planning_xlsx=args.planning,
        planning=planning,
        attribution=attribution,
        out_xlsx=args.out,
        calcul=calcul,
    )
    text = render_report(planning=planning, attribution=attribution, calcul=calcul)
    write_report(args.report, text)
    print(f"Planning rempli : {args.out}")
    print(f"Rapport : {args.report}")
    return 0


def cmd_validate_attribution(args: argparse.Namespace) -> int:
    calcul = load_json(args.calcul)
    planning = load_json(args.planning)
    wishes = load_json(args.souhaits)
    attribution = load_json(args.attribution)
    validate_attribution(calcul, planning, wishes, attribution)
    print("Attribution valide.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    planning_path = workdir / "gardes-a-remplir.json"
    calcul_path = workdir / "calcul-gardes.json"
    wishes_path = workdir / "souhaits-gardes.json"
    attribution_path = workdir / "attribution-gardes.json"
    xlsx_path = workdir / "planning-rempli.xlsx"
    report_path = workdir / "rapport.txt"

    planning = parse_planning(args.planning)
    write_planning_json(planning, planning_path)
    print(f"[step2] {planning_path} — {_summary(planning['counts'])}")

    if args.calcul:
        calcul = load_calcul(args.calcul)
        if not calcul.get("validated"):
            raise GardesError(
                f"{args.calcul} n'est pas validé. Lance d'abord step1-validate.", code="calcul_not_validated"
            )
        calcul = validate_calcul(calcul)
    else:
        calcul = parse_pdf(args.pdf, planning_path=args.planning)
        if args.auto_validate:
            calcul = validate_calcul(calcul)
        write_calcul(calcul, calcul_path)
        print(f"[step1] {calcul_path} — {len(calcul['people'])} personnes, "
              f"{len(calcul['candidates'])} candidats")
        if not args.auto_validate:
            _print_calcul_table(calcul)
            print()
            print(
                "Validation humaine requise. Relis le JSON ; si une valeur est "
                "fausse, corrige le PDF et relance ; sinon valide avec :\n"
                f"  gardes step1-validate --json {calcul_path}\n"
                f"  gardes run --pdf {args.pdf} --planning {args.planning} "
                f"--wishes {args.wishes} --workdir {workdir} --calcul {calcul_path}"
            )
            return 0

    wishes = parse_wishes(args.wishes, calcul, planning)
    write_wishes(wishes, wishes_path)
    print(f"[step3] {wishes_path} — {_summary(wishes['counts'])}")

    attribution = solve_attribution(
        calcul,
        planning,
        wishes,
        input_paths={"calcul": calcul_path, "planning": planning_path, "souhaits": wishes_path},
        time_limit=args.time_limit,
    )
    write_json(attribution_path, attribution)
    print(f"[step4] {attribution_path} — {attribution['objective']}")

    write_excel(
        planning_xlsx=args.planning,
        planning=planning,
        attribution=attribution,
        out_xlsx=xlsx_path,
        calcul=calcul,
    )
    write_report(report_path, render_report(planning=planning, attribution=attribution, calcul=calcul))
    print(f"[step5] {xlsx_path} + {report_path}")
    print("Terminé.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gardes",
        description="Attribution automatique des gardes radiologues — V4",
    )
    sub = parser.add_subparsers(dest="command")

    p2 = sub.add_parser("step2", help="Scanner le planning Excel")
    p2.add_argument("--planning", required=True)
    p2.add_argument("--out", required=True)
    p2.set_defaults(func=cmd_step2)

    p1 = sub.add_parser("step1", help="Lire le PDF + pré-scan du planning")
    p1.add_argument("--pdf", required=True)
    p1.add_argument("--planning", required=True)
    p1.add_argument("--out", required=True)
    p1.set_defaults(func=cmd_step1)

    p1v = sub.add_parser("step1-validate", help="Valider calcul-gardes.json après relecture")
    p1v.add_argument("--json", required=True)
    p1v.set_defaults(func=cmd_step1_validate)

    p3 = sub.add_parser("step3", help="Scanner les souhaits Excel")
    p3.add_argument("--wishes", required=True)
    p3.add_argument("--calcul", required=True)
    p3.add_argument("--planning", required=True)
    p3.add_argument("--out", required=True)
    p3.set_defaults(func=cmd_step3)

    p4 = sub.add_parser("step4", help="Résoudre l'attribution (CP-SAT)")
    p4.add_argument("--calcul", required=True)
    p4.add_argument("--planning", required=True)
    p4.add_argument("--souhaits", required=True)
    p4.add_argument("--out", required=True)
    p4.add_argument("--time-limit", type=float, default=60.0)
    p4.set_defaults(func=cmd_step4)

    p5 = sub.add_parser("step5", help="Écrire le planning rempli et le rapport")
    p5.add_argument("--planning", required=True, help="Planning Excel source")
    p5.add_argument("--planning-json", required=True)
    p5.add_argument("--attribution", required=True)
    p5.add_argument("--calcul", required=True)
    p5.add_argument("--out", required=True)
    p5.add_argument("--report", required=True)
    p5.set_defaults(func=cmd_step5)

    pv = sub.add_parser("validate-attribution", help="Validation indépendante du JSON d'attribution")
    pv.add_argument("--calcul", required=True)
    pv.add_argument("--planning", required=True)
    pv.add_argument("--souhaits", required=True)
    pv.add_argument("--attribution", required=True)
    pv.set_defaults(func=cmd_validate_attribution)

    pr = sub.add_parser("run", help="Enchaîner step2 -> step1 -> step3 -> step4 -> step5")
    pr.add_argument("--pdf", required=True)
    pr.add_argument("--planning", required=True)
    pr.add_argument("--wishes", required=True)
    pr.add_argument("--workdir", default="data")
    pr.add_argument("--calcul", help="calcul-gardes.json déjà validé (saute le parsing PDF)")
    pr.add_argument("--auto-validate", action="store_true", help="CI uniquement : valide step1 sans humain")
    pr.add_argument("--time-limit", type=float, default=60.0)
    pr.set_defaults(func=cmd_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    try:
        return args.func(args) or 0
    except GardesError as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"ERREUR: fichier introuvable: {exc.filename}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - message lisible pour l'utilisateur
        print(f"ERREUR INATTENDUE: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
