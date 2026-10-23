from __future__ import annotations


class GardesError(Exception):
    """Erreur métier bloquante.

    Le programme ne devine jamais et ne corrige jamais silencieusement :
    toute incohérence remonte ici avec un message lisible.
    """

    def __init__(self, message: str, *, code: str = "error", details: dict | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        if self.code and self.code != "error":
            return f"[{self.code}] {self.message}"
        return self.message
