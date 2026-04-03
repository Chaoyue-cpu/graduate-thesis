#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

shopt -s nullglob

for tex in [0-9][0-9]_*.tex; do
  latexmk -xelatex -interaction=nonstopmode -halt-on-error "$tex"
done

for pdf in [0-9][0-9]_*.pdf; do
  base="${pdf%.pdf}"
  pdftoppm -png -r 300 "$pdf" "$base"
  if [[ -f "${base}-1.png" ]]; then
    mv -f "${base}-1.png" "${base}.png"
  fi
done
