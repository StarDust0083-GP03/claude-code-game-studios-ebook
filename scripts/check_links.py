#!/usr/bin/env python3
"""Check local links and referenced assets in the built wiki."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
PAGES = [WIKI / "index.html", WIKI / "search.html", WIKI / "book.html", *sorted((WIKI / "chapters").glob("*.html"))]
LINK = re.compile(r'(?:href|src)="([^"]+)"')


def target_ok(page: Path, link: str) -> bool:
    parts = urlsplit(link)
    if parts.scheme or link.startswith("#") or link.startswith("//"):
        return True
    raw = unquote(parts.path)
    if not raw:
        return True
    target = (page.parent / raw).resolve()
    try:
        target.relative_to(ROOT)
    except ValueError:
        return False
    return target.exists()


def main() -> int:
    bad = []
    for page in PAGES:
        if not page.exists():
            bad.append((page, "<missing page>"))
            continue
        for link in LINK.findall(page.read_text(encoding="utf-8")):
            if not target_ok(page, link):
                bad.append((page.relative_to(ROOT), link))
    for label, path in (("pdf", ROOT / "exports" / "claude-code-game-studios.pdf"),
                        ("epub", ROOT / "exports" / "claude-code-game-studios.epub")):
        if not path.exists():
            bad.append((Path("exports"), f"missing {label}"))
    if bad:
        for page, link in bad:
            print(f"BROKEN {page}: {link}")
        print(f"{len(bad)} broken reference(s)")
        return 1
    print(f"OK: {len(PAGES)} pages, all local links and exports resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
