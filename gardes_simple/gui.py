"""Interface minimale (tkinter) : choisir le classeur, cliquer, lire le rapport."""

from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from . import gabarit
from .pipeline import Issue, traiter

TITRE = "RAD Gardes — prototype V5"
COULEUR_OK = "#1a7f37"
COULEUR_REFUS = "#b42318"
COULEUR_NEUTRE = "#4b5563"


class Fenetre(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(TITRE)
        self.geometry("900x640")
        self.minsize(760, 520)
        self._chemin = tk.StringVar()
        self._issue: Issue | None = None
        self._construire()

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #

    def _construire(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        entete = tk.Frame(self, padx=18, pady=14)
        entete.grid(row=0, column=0, sticky="ew")
        tk.Label(
            entete, text="Attribution des gardes", font=("Helvetica", 20, "bold")
        ).pack(anchor="w")
        tk.Label(
            entete,
            text="Un classeur Excel simple : des dates, des noms, un nombre de gardes par personne.",
            font=("Helvetica", 11),
            fg=COULEUR_NEUTRE,
        ).pack(anchor="w")

        fichiers = tk.Frame(self, padx=18)
        fichiers.grid(row=1, column=0, sticky="ew")
        fichiers.columnconfigure(1, weight=1)
        tk.Label(fichiers, text="Classeur d'entrée").grid(row=0, column=0, sticky="w", padx=(0, 8))
        tk.Entry(fichiers, textvariable=self._chemin).grid(row=0, column=1, sticky="ew")
        ttk.Button(fichiers, text="Parcourir…", command=self._parcourir).grid(
            row=0, column=2, padx=(8, 0)
        )
        ttk.Button(fichiers, text="Modèle vierge…", command=self._creer_modele).grid(
            row=0, column=3, padx=(8, 0)
        )

        actions = tk.Frame(self, padx=18, pady=12)
        actions.grid(row=2, column=0, sticky="ew")
        self._bouton_lancer = ttk.Button(
            actions, text="Lancer le calcul", command=self._lancer
        )
        self._bouton_lancer.pack(side="left")
        self._bouton_ouvrir = ttk.Button(
            actions, text="Ouvrir le résultat", command=self._ouvrir, state="disabled"
        )
        self._bouton_ouvrir.pack(side="left", padx=(8, 0))
        self._statut = tk.Label(actions, text="Prêt.", font=("Helvetica", 11), fg=COULEUR_NEUTRE)
        self._statut.pack(side="left", padx=(14, 0))

        cadre = tk.Frame(self, padx=18)
        cadre.grid(row=3, column=0, sticky="nsew", pady=(0, 16))
        cadre.rowconfigure(0, weight=1)
        cadre.columnconfigure(0, weight=1)
        self._texte = scrolledtext.ScrolledText(
            cadre, wrap="none", font=("Menlo", 11), padx=10, pady=10
        )
        self._texte.grid(row=0, column=0, sticky="nsew")
        self._texte.configure(state="disabled")

        self._afficher(
            "1. Choisissez le classeur d'entrée (ou créez un « Modèle vierge »).\n"
            "2. Cliquez sur « Lancer le calcul ».\n\n"
            "Le programme refuse tout classeur qui ne correspond pas exactement au format :\n"
            "feuilles « Dates » (Date, Créneau) et « Personnes » (Nom, Gardes)."
        )
        self._chemin.trace_add("write", lambda *_: self._statut.configure(text="Prêt.", fg=COULEUR_NEUTRE))

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def _parcourir(self) -> None:
        chemin = filedialog.askopenfilename(
            title="Choisir le classeur d'entrée",
            filetypes=[("Classeur Excel", "*.xlsx")],
        )
        if chemin:
            self._chemin.set(chemin)

    def _creer_modele(self) -> None:
        chemin = filedialog.asksaveasfilename(
            title="Enregistrer le modèle vierge",
            defaultextension=".xlsx",
            initialfile="gardes-in-vide.xlsx",
            filetypes=[("Classeur Excel", "*.xlsx")],
        )
        if not chemin:
            return
        try:
            ecrit = gabarit.ecrire_modele(chemin)
        except OSError as exc:
            messagebox.showerror(TITRE, f"Écriture impossible :\n{exc}")
            return
        self._afficher(
            f"Modèle vierge écrit :\n{ecrit}\n\n"
            "Remplissez la feuille « Dates » (une ligne par créneau) et la feuille\n"
            "« Personnes » (nom + nombre exact de gardes), puis relancez le calcul."
        )

    def _lancer(self) -> None:
        texte = self._chemin.get().strip()
        if not texte:
            messagebox.showwarning(TITRE, "Choisissez d'abord un classeur d'entrée.")
            return
        self._bouton_lancer.state(["disabled"])
        self._statut.configure(text="Calcul en cours…", fg=COULEUR_NEUTRE)
        self.update_idletasks()
        try:
            issue = traiter(Path(texte))
        except OSError as exc:
            messagebox.showerror(
                TITRE,
                f"Écriture impossible :\n{exc}\n\n"
                "Fermez le classeur s'il est ouvert dans Excel, puis relancez.",
            )
            self._statut.configure(text="Écriture impossible.", fg=COULEUR_REFUS)
            return
        except Exception as exc:  # noqa: BLE001 — imprévu : on l'affiche, on ne le masque pas
            messagebox.showerror(TITRE, f"Erreur inattendue :\n{exc}")
            self._statut.configure(text="Erreur.", fg=COULEUR_REFUS)
            return
        finally:
            self._bouton_lancer.state(["!disabled"])

        self._issue = issue
        self._afficher(issue.rapport)
        couleur = COULEUR_OK if issue.ok else COULEUR_REFUS
        self._statut.configure(text=issue.resume, fg=couleur)
        self._bouton_ouvrir.state(["!disabled"] if issue.xlsx else ["disabled"])

    def _ouvrir(self) -> None:
        if self._issue is None or self._issue.xlsx is None:
            return
        cible = str(self._issue.xlsx)
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", cible])
            elif sys.platform.startswith("win"):
                os.startfile(cible)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", cible])
        except OSError as exc:
            messagebox.showerror(TITRE, f"Ouverture impossible :\n{exc}")

    # ------------------------------------------------------------------ #
    # Affichage
    # ------------------------------------------------------------------ #

    def _afficher(self, contenu: str) -> None:
        self._texte.configure(state="normal")
        self._texte.delete("1.0", "end")
        self._texte.insert("1.0", contenu)
        self._texte.configure(state="disabled")


def main() -> int:
    try:
        fenetre = Fenetre()
    except tk.TclError as exc:
        print(f"Pas d'affichage graphique disponible : {exc}", file=sys.stderr)
        print("Utilisez : python3 -m gardes_simple --entree FICHIER.xlsx", file=sys.stderr)
        return 1
    fenetre.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
