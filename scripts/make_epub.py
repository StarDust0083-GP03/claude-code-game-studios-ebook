#!/usr/bin/env python3
"""Build a minimal EPUB 3 from the already-rendered chapter HTML."""

from __future__ import annotations

import html
import re
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
BOOK = ROOT / "book"
OUT = ROOT / "exports" / "claude-code-game-studios.epub"
TITLE = "Claude Code 游戏工作室：从一堆提示词到一条可验收的流水线"
AUTHOR = "独立源码研究"
UID = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "ccgs-ebook-2026"))


def sections() -> list[tuple[str, str, str]]:
    summary = (BOOK / "SUMMARY.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\d+\. \[([^\]]+)\]\(chapters/([^)]+)\)", summary, re.M)
    rows += re.findall(r"^- \[([^\]]+)\]\(chapters/([^)]+)\)", summary, re.M)
    out = []
    for i, (title, filename) in enumerate(rows, 1):
        slug = filename[:-3]
        out.append((f"ch{i:02d}", title.replace("`", ""), slug))
    return out


ALLOWED = set("""p br strong em code pre ul ol li blockquote h1 h2 h3 h4 h5 h6 a
table thead tbody tr th td div span hr img section figure figcaption details summary""".split())


def clean(body: str) -> str:
    body = re.sub(r'<nav class="chapter-nav"[\s\S]*?</nav>', "", body)

    def tag(match: re.Match[str]) -> str:
        name = match.group(1).lower()
        if name not in ALLOWED:
            return html.escape(match.group(0))
        return match.group(0)

    body = re.sub(r"</?([A-Za-z][A-Za-z0-9:-]*)(?:\s[^>]*)?/?>", tag, body)
    body = re.sub(r"<br\s*>", "<br/>", body)
    body = re.sub(r"<(hr|img)([^>/]*?)\s*>", r"<\1\2/>", body)
    return body


def xhtml(title: str, body: str, css: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN" lang="zh-CN">
<head><meta charset="utf-8"/><title>{html.escape(title)}</title>
<link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>{body}</body></html>"""


def main() -> None:
    css = (WIKI / "assets" / "reader.css").read_text(encoding="utf-8")
    items = sections()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    manifest = []
    spine = []
    nav_items = []
    files: dict[str, str] = {}
    for idx, (cid, title, slug) in enumerate(items):
        source = (WIKI / "chapters" / f"{slug}.html").read_text(encoding="utf-8")
        match = re.search(r'<article class="chapter">([\s\S]*?)</article>', source)
        body = clean(match.group(1) if match else source)
        files[f"{cid}.xhtml"] = xhtml(title, body, css)
        manifest.append(f'<item id="{cid}" href="{cid}.xhtml" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{cid}"/>')
        nav_items.append(f'<li><a href="{cid}.xhtml">{html.escape(title)}</a></li>')

    files["nav.xhtml"] = xhtml("目录", f'<nav epub:type="toc" id="toc"><h1>目录</h1><ol>{"".join(nav_items)}</ol></nav>', css)
    files["nav.xhtml"] = files["nav.xhtml"].replace(
        '<html xmlns="http://www.w3.org/1999/xhtml"',
        '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"', 1)
    files["cover.xhtml"] = xhtml(
        "封面",
        f'<section class="volume-cover"><p>源码驱动的框架解剖</p><h1>Claude Code 游戏工作室</h1>'
        f'<h2>从提示词到可验收流水线</h2><p>独立源码研究 · 2026-10-31</p></section>', css)
    files["style.css"] = css
    manifest += [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>',
        '<item id="css" href="style.css" media-type="text/css"/>',
    ]
    spine = ['<itemref idref="cover"/>'] + spine
    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="uid">{UID}</dc:identifier>
<dc:title>{html.escape(TITLE)}</dc:title>
<dc:creator>{AUTHOR}</dc:creator>
<dc:language>zh-CN</dc:language>
<dc:date>2026-10-31</dc:date>
<meta property="dcterms:modified">2026-10-31T00:00:00Z</meta>
</metadata>
<manifest>
{"".join(manifest)}
</manifest>
<spine>
{"".join(spine)}
</spine>
</package>"""
    container = """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"""
    with zipfile.ZipFile(OUT, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", container, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", opf, compress_type=zipfile.ZIP_DEFLATED)
        for name, data in files.items():
            z.writestr(f"OEBPS/{name}", data, compress_type=zipfile.ZIP_DEFLATED)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes, {len(items)} sections)")


if __name__ == "__main__":
    main()
