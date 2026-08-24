"""Render the companion guide markdown to a branded, printable PDF.

Supports only the markdown subset used by the guide: headings, paragraphs,
blockquotes, bullets, checkboxes, pipe tables, rules and **bold** runs.
"""

from __future__ import annotations

import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, KeepTogether, PageTemplate, Paragraph,
    Spacer, Table, TableStyle,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "entregable 2", "Companion_Guide.md")
OUT = os.path.join(ROOT, "entregable 2", "Companion_Guide.pdf")

ORANGE = colors.HexColor("#FF6600")
INK = colors.HexColor("#1A1A1A")
GREY = colors.HexColor("#4B5563")
GREY_LINE = colors.HexColor("#E5E7EB")
GREY_ROW = colors.HexColor("#F7F8F9")
PANEL = colors.HexColor("#F4F5F6")

FONTS = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")


def register_fonts():
    faces = [("Body", "arial.ttf"), ("Body-Bold", "arialbd.ttf")]
    try:
        for name, fn in faces:
            pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, fn)))
        pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold")
        return "Body", "Body-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


F, FB = register_fonts()

S = {
    "h1": ParagraphStyle("h1", fontName=FB, fontSize=21, leading=25, textColor=INK,
                         spaceAfter=2),
    "h3sub": ParagraphStyle("h3sub", fontName=F, fontSize=11.5, leading=15,
                            textColor=GREY, spaceAfter=14),
    "h2": ParagraphStyle("h2", fontName=FB, fontSize=13.5, leading=17, textColor=INK,
                         spaceBefore=16, spaceAfter=7),
    "body": ParagraphStyle("body", fontName=F, fontSize=9.6, leading=13.6,
                           textColor=GREY, alignment=TA_LEFT, spaceAfter=6),
    "quote": ParagraphStyle("quote", fontName=FB, fontSize=11, leading=15.5,
                            textColor=INK, leftIndent=12, spaceAfter=4),
    "bullet": ParagraphStyle("bullet", fontName=F, fontSize=9.6, leading=13.4,
                             textColor=GREY, leftIndent=13, bulletIndent=2,
                             spaceAfter=3),
    "cell": ParagraphStyle("cell", fontName=F, fontSize=8.3, leading=11.2,
                           textColor=GREY),
    "cellhead": ParagraphStyle("cellhead", fontName=FB, fontSize=8.3, leading=11.2,
                               textColor=colors.white),
}


def inline(s):
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"\*\*(.+?)\*\*", r'<font name="%s" color="#1A1A1A">\1</font>' % FB, s)
    s = re.sub(r"\*(.+?)\*", r"<i>\1</i>", s)
    s = re.sub(r"`(.+?)`", r"\1", s)
    return s


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def build_table(rows, width):
    head, body = rows[0], rows[1:]
    n = len(head)
    # Share the width in proportion to how much text each column actually holds,
    # clamped so a one-character column still fits its header.
    weights = []
    for j in range(n):
        longest = max([len(head[j])] + [len(r[j]) for r in body if j < len(r)])
        weights.append(min(max(longest, 6), 46))
    total = sum(weights)
    widths = [width * w / total for w in weights]

    data = [[Paragraph(inline(c), S["cellhead"]) for c in head]]
    data += [[Paragraph(inline(c), S["cell"]) for c in r] for r in body]

    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, GREY_LINE),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), GREY_ROW))
    t.setStyle(TableStyle(style))
    return t


def parse(md, width):
    flow, i, lines = [], 0, md.split("\n")
    while i < len(lines):
        ln = lines[i]
        stripped = ln.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and \
                set(lines[i + 1].replace("|", "").replace(" ", "")) <= {"-", ":"}:
            rows = [split_row(lines[i])]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            flow += [Spacer(1, 3), build_table(rows, width), Spacer(1, 9)]
            continue

        if stripped.startswith("### "):
            flow.append(Paragraph(inline(stripped[4:]), S["h3sub"]))
        elif stripped.startswith("## "):
            flow.append(KeepTogether([
                Paragraph(inline(stripped[3:]), S["h2"]),
                HRFlowable(width=42, thickness=2.2, color=ORANGE, spaceBefore=1,
                           spaceAfter=8, hAlign="LEFT"),
            ]))
        elif stripped.startswith("# "):
            flow.append(Paragraph(inline(stripped[2:]), S["h1"]))
        elif stripped.startswith("---"):
            flow.append(HRFlowable(width="100%", thickness=0.6, color=GREY_LINE,
                                   spaceBefore=8, spaceAfter=4))
        elif stripped.startswith("> "):
            quote = [stripped[2:]]
            while i + 1 < len(lines) and lines[i + 1].strip().startswith("> "):
                i += 1
                quote.append(lines[i].strip()[2:])
            body = Paragraph(inline(" ".join(quote)), S["quote"])
            t = Table([[body]], colWidths=[width], hAlign="LEFT")
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), PANEL),
                ("LINEBEFORE", (0, 0), (0, -1), 3, ORANGE),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ]))
            flow += [Spacer(1, 3), t, Spacer(1, 9)]
        elif stripped.startswith("- "):
            item = stripped[2:]
            marker = "\u25a1" if item.startswith("[ ] ") else "\u2013"
            if item.startswith("[ ] "):
                item = item[4:]
            while i + 1 < len(lines) and lines[i + 1].startswith("  ") and \
                    lines[i + 1].strip() and not lines[i + 1].strip().startswith("-"):
                i += 1
                item += " " + lines[i].strip()
            flow.append(Paragraph(inline(item), S["bullet"], bulletText=marker))
        else:
            para = [stripped]
            while i + 1 < len(lines) and lines[i + 1].strip() and \
                    not re.match(r"^\s*([#>|-]|- )", lines[i + 1]):
                i += 1
                para.append(lines[i].strip())
            flow.append(Paragraph(inline(" ".join(para)), S["body"]))
        i += 1
    return flow


def decorate(canvas, doc):
    canvas.saveState()
    w, h = LETTER
    canvas.setFillColor(ORANGE)
    canvas.rect(0, h - 10, w, 10, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor("#9AA0A6"))
    canvas.setFont(F, 7.5)
    canvas.drawString(0.75 * inch, 0.5 * inch,
                      "DiDi Global — CX Service Operations   |   Companion guide, "
                      "Entregable 2   |   Internal use only")
    canvas.drawRightString(w - 0.75 * inch, 0.5 * inch, str(doc.page))
    canvas.restoreState()


def main():
    with open(SRC, encoding="utf-8") as fh:
        md = fh.read()

    w, h = LETTER
    frame = Frame(0.75 * inch, 0.75 * inch, w - 1.5 * inch, h - 1.55 * inch, id="f")
    doc = BaseDocTemplate(OUT, pagesize=LETTER, title="Companion Guide — Entregable 2",
                          author="CX Service Operations")
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=decorate)])
    doc.build(parse(md, w - 1.5 * inch))
    print(f"OK -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())
