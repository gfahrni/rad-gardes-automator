from __future__ import annotations

from pathlib import Path

from gardes.errors import GardesError
from gardes.jsonio import write_json
from gardes.step1_pdf import parse_pdf, validate_calcul, write_calcul
from gardes.step2_planning import parse_planning, write_planning_json
from gardes.step3_wishes import parse_wishes, write_wishes
from gardes.step4_solve import solve_attribution
from gardes.step5_excel import write_excel
from gardes.step5_report import render_report, write_report

from .state import PipelineState


class PipelineController:
    """Orchestration sans Qt, réutilisable par la GUI et les tests."""

    def __init__(self, state: PipelineState | None = None):
        self.state = state or PipelineState()

    # ------------------------------------------------------------------ entrées
    def set_inputs(
        self,
        pdf: str | Path,
        planning: str | Path,
        wishes: str | Path,
        workdir: str | Path,
    ) -> None:
        pdf, planning, wishes = Path(pdf), Path(planning), Path(wishes)
        for label, path in (("PDF", pdf), ("planning", planning), ("souhaits", wishes)):
            if not path.exists():
                raise GardesError(f"Fichier {label} introuvable : {path}", code="file_missing")
        workdir = Path(workdir)
        workdir.mkdir(parents=True, exist_ok=True)
        self.state = PipelineState(
            pdf_path=pdf,
            planning_path=planning,
            wishes_path=wishes,
            workdir=workdir,
        )

    def _require_inputs(self) -> None:
        if not self.state.has_inputs():
            raise GardesError("Choisis les trois fichiers d'entrée.", code="inputs_missing")

    # ------------------------------------------------------------------ étapes
    def scan_planning(self) -> dict:
        self._require_inputs()
        assert self.state.planning_path is not None
        planning = parse_planning(self.state.planning_path)
        write_planning_json(planning, self.state.planning_json)
        self.state.planning = planning
        self.state.reset_downstream("planning")
        return planning

    def build_calcul(self) -> dict:
        self._require_inputs()
        if self.state.planning is None:
            self.scan_planning()
        assert self.state.pdf_path is not None and self.state.planning_path is not None
        calcul = parse_pdf(
            self.state.pdf_path,
            planning_path=self.state.planning_path,
        )
        write_calcul(calcul, self.state.calcul_json)
        self.state.calcul = calcul
        self.state.calcul_validated = False
        self.state.reset_downstream("calcul")
        return calcul

    def validate_people(self, people: list[dict] | None = None) -> dict:
        if self.state.calcul is None:
            raise GardesError("Le calcul des gardes n'est pas encore chargé.", code="calcul_missing")
        if people is not None:
            self.state.calcul["people"] = people
        calcul = validate_calcul(self.state.calcul)
        write_calcul(calcul, self.state.calcul_json)
        self.state.calcul = calcul
        self.state.calcul_validated = True
        self.state.reset_downstream("calcul")
        self.state.calcul = calcul
        self.state.calcul_validated = True
        return calcul

    def scan_wishes(self) -> dict:
        if self.state.calcul is None or not self.state.calcul_validated:
            raise GardesError("Valide d'abord la liste des personnes.", code="calcul_not_validated")
        if self.state.planning is None:
            raise GardesError("Le planning n'est pas scanné.", code="planning_missing")
        assert self.state.wishes_path is not None
        wishes = parse_wishes(self.state.wishes_path, self.state.calcul, self.state.planning)
        write_wishes(wishes, self.state.wishes_json)
        self.state.wishes = wishes
        self.state.reset_downstream("wishes")
        self.state.wishes = wishes
        return wishes

    def solve(self) -> dict:
        if self.state.calcul is None or self.state.planning is None or self.state.wishes is None:
            raise GardesError("Les étapes précédentes ne sont pas terminées.", code="pipeline_incomplete")
        attribution = solve_attribution(
            self.state.calcul,
            self.state.planning,
            self.state.wishes,
            input_paths={
                "calcul": self.state.calcul_json,
                "planning": self.state.planning_json,
                "souhaits": self.state.wishes_json,
            },
        )
        write_json(self.state.attribution_json, attribution)
        self.state.attribution = attribution
        return attribution

    def export(
        self,
        out_xlsx: str | Path | None = None,
        report: str | Path | None = None,
    ) -> tuple[Path, Path]:
        if self.state.attribution is None or self.state.calcul is None or self.state.planning is None:
            raise GardesError("L'attribution n'est pas encore calculée.", code="attribution_missing")
        out_xlsx = Path(out_xlsx) if out_xlsx else self.state.output_xlsx
        report = Path(report) if report else self.state.report_txt
        assert self.state.planning_path is not None
        write_excel(
            planning_xlsx=self.state.planning_path,
            planning=self.state.planning,
            attribution=self.state.attribution,
            out_xlsx=out_xlsx,
            calcul=self.state.calcul,
        )
        write_report(
            report,
            render_report(
                planning=self.state.planning,
                attribution=self.state.attribution,
                calcul=self.state.calcul,
            ),
        )
        return out_xlsx, report

    # ------------------------------------------------------------------ tests
    def run_auto(self) -> dict:
        """Pipeline complet sans interaction, pour les tests."""
        self.scan_planning()
        self.build_calcul()
        self.validate_people(self.state.calcul["people"] if self.state.calcul else None)
        self.scan_wishes()
        return self.solve()
