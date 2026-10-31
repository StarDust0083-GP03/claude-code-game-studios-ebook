#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

npm ci --prefix wiki
python3 scripts/make_diagrams.py
node wiki/build.mjs
python3 scripts/make_epub.py
CHROME="${CHROME:-chromium}"
"$CHROME" --headless=new --disable-gpu --no-sandbox --no-pdf-header-footer \
  --print-to-pdf=exports/claude-code-game-studios.pdf wiki/book.html
mkdir -p wiki/exports
cp exports/claude-code-game-studios.pdf exports/claude-code-game-studios.epub wiki/exports/
python3 scripts/check_links.py
python3 -m unittest discover -s examples -v
echo "OK: site, EPUB, PDF, links, and example tests"
