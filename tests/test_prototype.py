"""Tests du prototype V5 : refus strict, attribution exacte, sorties, modèle."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta

import pytest
from openpyxl import Workbook, load_workbook

from gardes_simple import cli, gabarit
from gardes_simple.modele import Creneau, Entree, Personne
from gardes_simple.pipeline import CODE_OK, CODE_REFUS, traiter
from gardes_simple.solve import Infaisable, _lisser, _paires, resoudre
from gardes_simple.validate import lire

DATES = [date(2027, 3, 1), date(2027, 3, 2), date(2027, 3, 6), date(2027, 3, 7)]
CRENEAUX = [(jour, moment) for jour in DATES for moment in ("Matin", "Soir")]
PERSONNES = [("Muller", 3), ("Rossi", 2), ("Dupont", 2), ("Keller", 1)]


def creer(
    chemin,
    creneaux=CRENEAUX,
    personnes=PERSONNES,
    entete_dates=("Date", "Créneau"),
    entete_personnes=("Nom", "Gardes"),
):
    classeur = Workbook()
    feuille = classeur.active
    feuille.title = "Dates"
    feuille.append(list(entete_dates))
    for jour, moment in creneaux:
        feuille.append([jour, moment])
    feuille_p = classeur.create_sheet("Personnes")
    feuille_p.append(list(entete_personnes))
    for nom, quota in personnes:
        feuille_p.append([nom, quota])
    classeur.save(chemin)
    return chemin


def _jour(valeur):
    return valeur.date() if isinstance(valeur, datetime) else valeur


# --------------------------------------------------------------------------- #
# Cas nominal
# --------------------------------------------------------------------------- #


def test_traitement_ok(tmp_path):
    entree = creer(tmp_path / "gardes-in.xlsx")
    issue = traiter(entree)

    assert issue.code == CODE_OK, issue.rapport
    assert issue.xlsx is not None and issue.xlsx.exists()
    assert issue.texte is not None and issue.texte.exists()
    assert "Taux de réussite : 100 %" in issue.rapport
    assert issue.texte.read_text(encoding="utf-8") == issue.rapport

    feuille = load_workbook(issue.xlsx)["Attribution"]
    lignes = list(feuille.iter_rows(min_row=2, values_only=True))
    assert len(lignes) == len(CRENEAUX)
    assert len({(_jour(j), m) for j, m, _ in lignes}) == len(CRENEAUX)
    assert Counter(nom for _, _, nom in lignes) == Counter(dict(PERSONNES))

    par_jour: Counter = Counter()
    for jour, _, nom in lignes:
        par_jour[(_jour(jour), nom)] += 1
    assert max(par_jour.values()) == 1

    synthese = load_workbook(issue.xlsx)["Synthèse"]
    assert synthese["A1"].value == "Nom"
    ecarts = {
        ligne[0]: ligne[3]
        for ligne in synthese.iter_rows(min_row=2, values_only=True)
    }
    assert set(ecarts.values()) == {0}


def test_traitement_deterministe(tmp_path):
    entree = creer(tmp_path / "gardes-in.xlsx")
    premier = traiter(entree)
    second = traiter(entree)
    assert premier.rapport == second.rapport


def test_modele_d_emploi_ignore(tmp_path):
    modele = gabarit.ecrire_modele(tmp_path / "vide.xlsx", lignes_dates=10, lignes_personnes=10)
    lecture = lire(modele)
    assert lecture.entree is None
    assert any("aucun créneau" in probleme for probleme in lecture.problemes)
    assert lecture.avertissements == []


# --------------------------------------------------------------------------- #
# Refus explicites
# --------------------------------------------------------------------------- #


def test_refus_entete(tmp_path):
    entree = creer(
        tmp_path / "in.xlsx",
        entete_dates=("Dates", "Moment"),
        entete_personnes=("Personne", "Gardes"),
    )
    issue = traiter(entree)
    assert issue.code == CODE_REFUS
    assert "en-tête attendu « Date »" in issue.rapport
    assert "en-tête attendu « Nom »" in issue.rapport


def test_refus_feuille_absente(tmp_path):
    chemin = tmp_path / "in.xlsx"
    classeur = Workbook()
    classeur.active.title = "Dates"
    classeur.active.append(["Date", "Créneau"])
    classeur.save(chemin)
    issue = traiter(chemin)
    assert issue.code == CODE_REFUS
    assert "Feuille « Personnes » absente" in issue.rapport


def test_refus_date_texte(tmp_path):
    entree = creer(tmp_path / "in.xlsx", creneaux=[("01.03.2027", "Matin")], personnes=[("Muller", 1)])
    issue = traiter(entree)
    assert issue.code == CODE_REFUS
    assert "texte, pas une vraie date Excel" in issue.rapport


def test_refus_date_vide(tmp_path):
    entree = creer(tmp_path / "in.xlsx", creneaux=[(None, "Matin")], personnes=[("Muller", 1)])
    issue = traiter(entree)
    assert issue.code == CODE_REFUS
    assert "la date est vide" in issue.rapport


def test_refus_creneau_invalide(tmp_path):
    entree = creer(tmp_path / "in.xlsx", creneaux=[(DATES[0], "Matinée")], personnes=[("Muller", 1)])
    issue = traiter(entree)
    assert issue.code == CODE_REFUS
    assert "créneau « Matinée » invalide" in issue.rapport


def test_refus_doublon_creneau(tmp_path):
    creneaux = [(DATES[0], "Matin"), (DATES[0], "matin")]
    entree = creer(tmp_path / "in.xlsx", creneaux=creneaux, personnes=[("Muller", 2)])
    issue = traiter(entree)
    assert issue.code == CODE_REFUS
    assert "doublon" in issue.rapport


def test_refus_somme_quotas(tmp_path):
    entree = creer(tmp_path / "in.xlsx", personnes=[("Muller", 4), ("Rossi", 3)])
    issue = traiter(entree)
    assert issue.code == CODE_REFUS
    assert "Somme des gardes (7) ≠ nombre de créneaux (8)" in issue.rapport


def test_refus_nom_doublon(tmp_path):
    entree = creer(
        tmp_path / "in.xlsx", personnes=[("Muller", 4), ("  muller ", 4)]
    )
    issue = traiter(entree)
    assert issue.code == CODE_REFUS
    assert "existe déjà" in issue.rapport


def test_refus_quota_non_entier(tmp_path):
    entree = creer(tmp_path / "in.xlsx", personnes=[("Muller", 3.5), ("Rossi", 4.5)])
    issue = traiter(entree)
    assert issue.code == CODE_REFUS
    assert "n'est pas un nombre entier" in issue.rapport


def test_refus_deux_creneaux_une_personne(tmp_path):
    entree = creer(
        tmp_path / "in.xlsx",
        creneaux=[(DATES[0], "Matin"), (DATES[0], "Soir")],
        personnes=[("Muller", 2)],
    )
    issue = traiter(entree)
    assert issue.code == CODE_REFUS
    assert "deux gardes le même jour" in issue.rapport


def test_refus_colonne_en_trop(tmp_path):
    chemin = tmp_path / "in.xlsx"
    creer(chemin)
    classeur = load_workbook(chemin)
    classeur["Dates"]["C1"] = "Commentaire"
    classeur.save(chemin)
    issue = traiter(chemin)
    assert issue.code == CODE_REFUS
    assert "doit rester vide" in issue.rapport


def test_refus_extension(tmp_path):
    chemin = tmp_path / "in.xls"
    chemin.write_text("pas un classeur", encoding="utf-8")
    issue = traiter(chemin)
    assert issue.code == CODE_REFUS
    assert "Extension attendue" in issue.rapport


def test_refus_fichier_absent(tmp_path):
    issue = traiter(tmp_path / "absent.xlsx")
    assert issue.code == CODE_REFUS
    assert "Fichier introuvable" in issue.rapport


def test_aucun_fichier_ecrit_si_refus(tmp_path):
    dossier = tmp_path / "essai"
    dossier.mkdir()
    entree = creer(dossier / "in.xlsx", personnes=[("Muller", 8)])
    issue = traiter(entree)
    assert issue.code == CODE_REFUS
    assert list(dossier.glob("*-resultat.xlsx")) == []
    assert list(dossier.glob("*-rapport.txt")) == []


# --------------------------------------------------------------------------- #
# Avertissements (non bloquants)
# --------------------------------------------------------------------------- #


def test_avertissement_feuille_en_plus(tmp_path):
    entree = creer(tmp_path / "in.xlsx")
    classeur = load_workbook(entree)
    classeur.create_sheet("Notes")["A1"] = "brouillon"
    classeur.save(entree)
    issue = traiter(entree)
    assert issue.code == CODE_OK
    assert "Feuille « Notes » ignorée." in issue.rapport


def test_avertissement_heure_ignoree(tmp_path):
    entree = creer(
        tmp_path / "in.xlsx",
        creneaux=[(datetime(2027, 3, 1, 8, 30), "Matin")],
        personnes=[("Muller", 1)],
    )
    issue = traiter(entree)
    assert issue.code == CODE_OK
    assert "heure ignorée" in issue.rapport


def test_avertissement_quota_zero(tmp_path):
    entree = creer(
        tmp_path / "in.xlsx",
        creneaux=[(DATES[0], "Matin")],
        personnes=[("Muller", 1), ("Absent", 0)],
    )
    issue = traiter(entree)
    assert issue.code == CODE_OK
    assert "a 0 garde" in issue.rapport


def test_refus_classeur_vide(tmp_path):
    chemin = tmp_path / "vide.xlsx"
    Workbook().save(chemin)
    issue = traiter(chemin)
    assert issue.code == CODE_REFUS
    assert "Feuille « Dates » absente" in issue.rapport


# --------------------------------------------------------------------------- #
# Solveur
# --------------------------------------------------------------------------- #


def test_infaisable_leve_une_exception():
    entree = Entree(
        creneaux=[Creneau(DATES[0], "Matin"), Creneau(DATES[0], "Soir")],
        personnes=[Personne("Solo", 2)],
    )
    with pytest.raises(Infaisable):
        resoudre(entree)


def test_paires():
    assert _paires(set()) == 0
    assert _paires({DATES[0]}) == 0
    assert _paires({DATES[0], DATES[1]}) == 1
    trois_jours = {date(2027, 3, 1), date(2027, 3, 2), date(2027, 3, 3)}
    assert _paires(trois_jours) == 2


def test_lissage_casse_les_jours_voisins():
    plan = {"A": {DATES[0], DATES[1]}, "B": {DATES[2], DATES[3]}}
    _lisser(plan)
    assert sum(_paires(jours) for jours in plan.values()) == 0
    assert sorted(map(len, plan.values())) == [2, 2]


def test_pas_de_soir_puis_matin(tmp_path):
    veille, lendemain = date(2027, 4, 5), date(2027, 4, 6)
    entree = creer(
        tmp_path / "in.xlsx",
        creneaux=[(veille, "Matin"), (veille, "Soir"), (lendemain, "Matin")],
        personnes=[("Anna", 2), ("Bruno", 1)],
    )
    issue = traiter(entree)
    assert issue.code == CODE_OK, issue.rapport
    lignes = list(load_workbook(issue.xlsx)["Attribution"].iter_rows(min_row=2, values_only=True))
    soirs = {(_jour(jour), nom) for jour, moment, nom in lignes if moment == "Soir"}
    mauvais = [
        nom
        for jour, moment, nom in lignes
        if moment == "Matin" and (_jour(jour) - timedelta(days=1), nom) in soirs
    ]
    assert mauvais == []


# --------------------------------------------------------------------------- #
# CLI et gabarit
# --------------------------------------------------------------------------- #


def test_cli_modele(tmp_path, capsys):
    cible = tmp_path / "modele.xlsx"
    assert cli.main(["--modele", str(cible)]) == 0
    assert cible.exists()
    assert "Modèle vierge écrit" in capsys.readouterr().out


def test_cli_entree(tmp_path, capsys):
    entree = creer(tmp_path / "in.xlsx")
    assert cli.main(["--entree", str(entree)]) == 0
    sortie = capsys.readouterr().out
    assert "RÉSULTAT : OK" in sortie
    assert (tmp_path / "in-resultat.xlsx").exists()


def test_gabarit_contient_les_trois_feuilles(tmp_path):
    modele = gabarit.ecrire_modele(tmp_path / "modele.xlsx")
    classeur = load_workbook(modele)
    assert classeur.sheetnames == ["Dates", "Personnes", "Mode d'emploi"]
    assert classeur["Dates"]["A1"].value == "Date"
    assert classeur["Dates"]["B1"].value == "Créneau"
    assert classeur["Personnes"]["A1"].value == "Nom"
    assert classeur["Personnes"]["B1"].value == "Gardes"


def test_gui_se_construit():
    tk = pytest.importorskip("tkinter")
    from gardes_simple.gui import Fenetre

    try:
        fenetre = Fenetre()
    except tk.TclError:
        pytest.skip("pas d'affichage graphique disponible")
    try:
        assert fenetre.title().startswith("RAD Gardes")
    finally:
        fenetre.destroy()


def test_gui_traite_un_fichier(tmp_path):
    tk = pytest.importorskip("tkinter")
    from gardes_simple.gui import Fenetre

    entree = creer(tmp_path / "in.xlsx")
    try:
        fenetre = Fenetre()
    except tk.TclError:
        pytest.skip("pas d'affichage graphique disponible")
    try:
        fenetre.withdraw()
        fenetre._chemin.set(str(entree))
        fenetre._lancer()
        contenu = fenetre._texte.get("1.0", "end")
        assert "RÉSULTAT : OK" in contenu
        assert "100 %" in contenu
        assert fenetre._statut.cget("text").startswith("OK")
    finally:
        fenetre.destroy()
