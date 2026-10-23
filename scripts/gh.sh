#!/usr/bin/env bash
#
# Pousse le projet sur GitHub sans stocker de dossier .git dans le projet.
#
# Le dossier synchronisé par Syncthing reste un simple dossier de fichiers.
# L'historique Git vit hors du dossier, dans $RAD_GARDES_SUPPORT_DIR
# (par défaut ~/.rad-gardes-automator), et pointe sur ce dossier via
# core.worktree.
#
# Usage :
#   ./scripts/gh.sh                  # état des fichiers (défaut)
#   ./scripts/gh.sh status           # idem
#   ./scripts/gh.sh diff             # différences avec le dernier commit
#   ./scripts/gh.sh log [n]          # n derniers commits (10 par défaut)
#   ./scripts/gh.sh push [-m texte]  # commit + push sur origin/main
#   ./scripts/gh.sh pull             # récupère origin/main (fast-forward)
#
# Variables d'environnement (optionnelles) :
#   RAD_GARDES_SUPPORT_DIR  dossier de l'historique Git
#   RAD_GARDES_REMOTE       URL du dépôt distant
#   RAD_GARDES_BRANCH       branche à pousser (main)

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUPPORT_DIR="${RAD_GARDES_SUPPORT_DIR:-$HOME/.rad-gardes-automator}"
GIT_DIR="$SUPPORT_DIR/.git"
REMOTE_URL="${RAD_GARDES_REMOTE:-git@github.com:gfahrni/rad-gardes-automator.git}"
BRANCH="${RAD_GARDES_BRANCH:-main}"

usage() {
  sed -n '10,16p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

die() {
  echo "Erreur : $*" >&2
  exit 1
}

# Le dossier de travail ne doit pas contenir de .git (contrainte Syncthing).
if [[ -e "$PROJECT_DIR/.git" ]]; then
  die "$PROJECT_DIR/.git existe encore. Supprimez-le (Git est géré hors du dossier) ou utilisez git normalement."
fi

export GIT_DIR
export GIT_WORK_TREE="$PROJECT_DIR"

# Premier lancement : clone l'historique depuis GitHub dans SUPPORT_DIR, sans
# checkout (les fichiers sont déjà dans PROJECT_DIR), puis greffe le dossier
# de travail courant sur ce clone.
bootstrap() {
  [[ -f "$GIT_DIR/HEAD" ]] && return 0

  if [[ -e "$SUPPORT_DIR" ]]; then
    die "$SUPPORT_DIR existe mais n'est pas un dépôt Git valide. Supprimez-le puis relancez."
  fi

  echo "→ Historique absent : clonage de $REMOTE_URL dans $SUPPORT_DIR"
  env -u GIT_DIR -u GIT_WORK_TREE git clone --no-checkout --quiet "$REMOTE_URL" "$SUPPORT_DIR"
  git config core.worktree "$PROJECT_DIR"
  git reset --mixed --quiet
}

cmd="${1:-status}"
[[ $# -gt 0 ]] && shift

if [[ "$cmd" == "-h" || "$cmd" == "--help" || "$cmd" == "help" ]]; then
  usage
  exit 0
fi

bootstrap

case "$cmd" in
  status)
    git status --short --branch
    ;;

  diff)
    git --no-pager diff HEAD --stat
    echo
    git --no-pager diff HEAD
    ;;

  log)
    git --no-pager log --oneline -n "${1:-10}"
    ;;

  pull)
    [[ -z "$(git status --porcelain)" ]] || die "modifications locales non commitées ; poussez-les d'abord."
    git pull --ff-only origin "$BRANCH"
    ;;

  push)
    message=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        -m|--message)
          [[ $# -ge 2 ]] || die "message manquant après $1."
          message="$2"
          shift 2
          ;;
        *)
          die "option inconnue : $1"
          ;;
      esac
    done

    git add -A

    if git diff --cached --quiet; then
      echo "Aucun changement à pousser. Tout est déjà sur GitHub."
      git status --short --branch
      exit 0
    fi

    if [[ -z "$message" ]]; then
      message="Mise à jour du $(date '+%Y-%m-%d %H:%M')"
    fi

    git commit --quiet -m "$message"
    git push origin "$BRANCH"

    echo
    echo "✓ Poussé sur GitHub : $(git log --oneline -n 1)"
    ;;

  *)
    die "commande inconnue : $cmd (essayez --help)"
    ;;
esac
