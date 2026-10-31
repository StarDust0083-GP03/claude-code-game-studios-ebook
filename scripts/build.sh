#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

npm ci --prefix wiki
node wiki/build.mjs
python3 scripts/make_epub.py
CHROME="${CHROME:-chromium}"
"$CHROME" --headless=new --disable-gpu --no-sandbox --no-pdf-header-footer \
  --print-to-pdf=exports/claude-code-game-studios.pdf wiki/book.html
python3 scripts/check_links.py
python3 -m unittest discover -s examples -v
echo "OK: site, EPUB, PDF, links, and example tests"
