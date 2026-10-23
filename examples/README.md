# Exemples synthétiques

Ces trois fichiers sont des **données de démonstration**. Ils ne contiennent
aucune donnée personnelle réelle : tous les noms de personnes ont été remplacés
par des noms fictifs plausibles, cohérents entre les trois documents d'entrée.

| Fichier | Rôle |
|---|---|
| `exemple-calcul-gardes.pdf` | PDF de calcul des gardes à faire par personne |
| `exemple-planning-vide.xlsx` | Planning de départ, onglet `Feuille1` |
| `exemple-souhaits-garde.xlsx` | Souhaits de garde, onglet `Feuille 1` |

## Contenu attendu

- PDF : 30 lignes (26 CDC, 3 urgentistes, 1 exclu), 181 jours, 112 créneaux
  week-end/férié.
- Planning vide : 24 cellules pré-remplies, 88 trous, 80 trous week-end,
  8 trous fériés.
- Souhaits : 14 personnes, 181 dates.
- Résultat de référence : couverture **87/88**, **3 rouges**, **74 verts**,
  **1 trou férié**.

## Nettoyage appliqué

- Suppression des feuilles inutilisées et des feuilles vides.
- Colonnes non nécessaires au moteur vidées : seules les colonnes `GARDE`
  jour/soir, les dates et les indicateurs sont conservées.
- Indicateurs de jours figés dans l'exemple, pour qu'une ouverture dans Excel
  ne modifie pas les jours fériés.
- Suppression des zones de texte, images, hyperliens, paramètres d'imprimante,
  vues personnalisées et noms d'utilisateurs dans les métadonnées.
- Suppression des lignes/colonnes de formatage au-delà de la zone utile.
- Remplacement du logo et des initiales du PDF.
- Captures d'écran générées avec des chemins neutres.

## Règle

Ne jamais ajouter de document réel, de capture d'écran réelle ou de données
nominatives dans ce dossier. Les noms présents ici sont fictifs.
