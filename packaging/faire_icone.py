"""Génère l'icône de l'app (PNG 1024, .icns macOS, .ico Windows).

Usage : python3 packaging/faire_icone.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DOSSIER = Path(__file__).resolve().parent
FOND = (31, 56, 100, 255)
ACCENT = (59, 130, 246, 255)
BLANC = (246, 248, 252, 255)
TRAIT = (203, 213, 225, 255)


def dessiner(taille: int = 1024) -> Image.Image:
    image = Image.new("RGBA", (taille, taille), (0, 0, 0, 0))
    dessin = ImageDraw.Draw(image)

    marge = taille * 0.06
    dessin.rounded_rectangle(
        (marge, marge, taille - marge, taille - marge),
        radius=int(taille * 0.22),
        fill=FOND,
    )

    # Calendrier
    largeur = taille * 0.62
    hauteur = taille * 0.58
    gauche = (taille - largeur) / 2
    haut = taille * 0.24
    rayon = int(taille * 0.05)
    dessin.rounded_rectangle(
        (gauche, haut, gauche + largeur, haut + hauteur), radius=rayon, fill=BLANC
    )
    dessin.rounded_rectangle(
        (gauche, haut, gauche + largeur, haut + hauteur * 0.24),
        radius=rayon,
        fill=ACCENT,
    )
    dessin.rectangle(
        (gauche, haut + hauteur * 0.12, gauche + largeur, haut + hauteur * 0.24),
        fill=ACCENT,
    )

    # Deux anneaux de reliure
    for decalage in (0.24, 0.64):
        x = gauche + largeur * decalage
        dessin.rounded_rectangle(
            (x, haut - taille * 0.03, x + largeur * 0.12, haut + hauteur * 0.04),
            radius=int(taille * 0.015),
            fill=BLANC,
        )

    # Grille de jours : 4 colonnes, 3 lignes ; le dernier point est plein
    cols, lignes = 4, 3
    zone_x0 = gauche + largeur * 0.10
    zone_x1 = gauche + largeur * 0.90
    zone_y0 = haut + hauteur * 0.36
    zone_y1 = haut + hauteur * 0.90
    for ligne in range(lignes):
        for colonne in range(cols):
            cx = zone_x0 + (zone_x1 - zone_x0) * (colonne + 0.5) / cols
            cy = zone_y0 + (zone_y1 - zone_y0) * (ligne + 0.5) / lignes
            rayon_point = largeur * 0.055
            plein = (ligne, colonne) == (1, 2)
            couleur = ACCENT if plein else TRAIT
            dessin.ellipse(
                (cx - rayon_point, cy - rayon_point, cx + rayon_point, cy + rayon_point),
                fill=couleur,
            )

    # Numéro de version
    police = _police(int(taille * 0.14))
    texte = "V6"
    if police is not None:
        boite = dessin.textbbox((0, 0), texte, font=police)
        largeur_texte = boite[2] - boite[0]
        dessin.text(
            ((taille - largeur_texte) / 2, taille * 0.088), texte, font=police, fill=BLANC
        )
    return image


def _police(taille: int):
    for chemin in (
        "/System/Library/Fonts/SFNS-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ):
        try:
            return ImageFont.truetype(chemin, taille)
        except OSError:
            continue
    return None


def main() -> None:
    png = dessiner(1024)
    png.save(DOSSIER / "icone.png")

    icns = DOSSIER / "icone.icns"
    icns.parent.mkdir(parents=True, exist_ok=True)
    png.save(icns, sizes=[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)])

    png.save(DOSSIER / "icone.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("Écrit : icone.png, icone.icns, icone.ico")


if __name__ == "__main__":
    main()
