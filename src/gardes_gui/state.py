from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .paths import default_workdir


@dataclass
class PipelineState:
    pdf_path: Path | None = None
    planning_path: Path | None = None
    wishes_path: Path | None = None
    workdir: Path = field(default_factory=default_workdir)

    planning: dict | None = None
    calcul: dict | None = None
    wishes: dict | None = None
    attribution: dict | None = None

    calcul_validated: bool = False
    warnings: list[str] = field(default_factory=list)

    @property
    def planning_json(self) -> Path:
        return self.workdir / "gardes-a-remplir.json"

    @property
    def calcul_json(self) -> Path:
        return self.workdir / "calcul-gardes.json"

    @property
    def wishes_json(self) -> Path:
        return self.workdir / "souhaits-gardes.json"

    @property
    def attribution_json(self) -> Path:
        return self.workdir / "attribution-gardes.json"

    @property
    def output_xlsx(self) -> Path:
        return self.workdir / "planning-rempli.xlsx"

    @property
    def report_txt(self) -> Path:
        return self.workdir / "rapport.txt"

    def has_inputs(self) -> bool:
        return all(
            p is not None and p.exists() for p in (self.pdf_path, self.planning_path, self.wishes_path)
        )

    def reset_data(self) -> None:
        self.planning = None
        self.calcul = None
        self.wishes = None
        self.attribution = None
        self.calcul_validated = False
        self.warnings.clear()

    def reset_downstream(self, after: str) -> None:
        """Invalide les données en aval d'une étape."""
        order = ["planning", "calcul", "wishes", "attribution"]
        if after not in order:
            return
        idx = order.index(after)
        for name in order[idx + 1 :]:
            setattr(self, name, None)
        if idx < order.index("wishes"):
            self.calcul_validated = False

    def reset_all(self) -> None:
        self.pdf_path = None
        self.planning_path = None
        self.wishes_path = None
        self.workdir = default_workdir()
        self.reset_data()
