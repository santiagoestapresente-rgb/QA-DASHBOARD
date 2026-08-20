"""
Verify that the DAX inside the Word deliverables is still copy-paste safe.

A single typographic quote turns a working measure into a syntax error, and the
failure is silent: the .docx looks fine and only breaks once someone pastes it into
Power BI. This compares every fenced code block in the Markdown source against the
monospaced paragraphs of the generated .docx, character by character, and separately
scans for the substitutions that a Word round-trip would introduce.

Run it after scripts/build_docs.py.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PBI = Path(__file__).resolve().parent.parent / "powerbi"
CODE_FONT = "Consolas"
CODE_BG_HEX = "F5F6F8"  # shading md_to_docx applies to code-block paragraphs only

PAIRS = [
    (PBI / "DAX_Measures.md", PBI / "Medidas DAX.docx"),
    (PBI / "GUIA_DE_ARMADO.md", PBI / "Guia de armado - Power BI.docx"),
]

# Quote substitutions break DAX wherever they appear, because they replace the
# straight quotes that delimit string literals.
FATAL = {
    "\u2018": "left single quote",
    "\u2019": "right single quote / apostrophe",
    "\u201a": "single low quote",
    "\u201c": "left double quote",
    "\u201d": "right double quote",
    "\u201e": "double low quote",
}

# These only break DAX outside a string literal. Inside one they are just text, and
# the model uses an en dash on purpose in the period label.
FATAL_OUTSIDE_STRINGS = {
    "\u2013": "en dash",
    "\u2014": "em dash",
    "\u2026": "ellipsis",
    "\u00a0": "non-breaking space",
}

STRING_LITERAL = re.compile(r'"[^"]*"')


def md_code_lines(path: Path) -> list[str]:
    """Every line inside a fenced code block, in document order."""
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    inside = False
    for line in lines:
        if line.strip().startswith("```"):
            inside = not inside
            continue
        if inside:
            out.append(line.rstrip())
    return out


def docx_code_lines(path: Path) -> list[str]:
    """Every code-block paragraph of the document, in document order.

    Identified by the shading md_to_docx applies to code blocks. Checking the font
    is not enough: a bullet whose whole text is an inline `code` span is also fully
    monospaced, and the import list in the guide is thirteen of those.
    """
    doc = Document(path)
    out: list[str] = []
    for paragraph in doc.paragraphs:
        if not paragraph.runs:
            continue
        p_pr = paragraph._p.pPr
        if p_pr is None:
            continue
        shading = p_pr.find(qn("w:shd"))
        if shading is None or shading.get(qn("w:fill")) != CODE_BG_HEX:
            continue
        if all(run.font.name == CODE_FONT for run in paragraph.runs):
            out.append(paragraph.text.rstrip())
    return out


def scan_characters(lines: list[str], label: str) -> int:
    findings = 0
    for number, line in enumerate(lines, start=1):
        outside_strings = STRING_LITERAL.sub('""', line)
        checks = [(FATAL, line), (FATAL_OUTSIDE_STRINGS, outside_strings)]
        for table, haystack in checks:
            for char, name in table.items():
                if char in haystack:
                    findings += 1
                    print(f"    FAIL  {label} line {number}: {name} ({char!r})")
                    print(f"          {line.strip()[:100]}")
    return findings


def main() -> int:
    failures = 0

    for md_path, docx_path in PAIRS:
        print(f"\n{docx_path.name}")
        if not docx_path.exists():
            print("    FAIL  the .docx does not exist; run scripts/build_docs.py first")
            failures += 1
            continue

        md_lines = md_code_lines(md_path)
        dx_lines = docx_code_lines(docx_path)
        # Blank lines inside a block are written as a single space by md_to_docx.
        dx_norm = ["" if line.strip() == "" else line for line in dx_lines]
        md_norm = ["" if line.strip() == "" else line for line in md_lines]

        print(f"    {len(md_norm)} code lines in the Markdown, {len(dx_norm)} in the Word file")

        if len(md_norm) != len(dx_norm):
            print("    FAIL  line counts differ, so the .docx is out of date or the parser missed a block")
            failures += 1
        else:
            mismatches = [
                (index, a, b) for index, (a, b) in enumerate(zip(md_norm, dx_norm), start=1) if a != b
            ]
            if mismatches:
                failures += 1
                print(f"    FAIL  {len(mismatches)} code lines differ from the Markdown source")
                for index, a, b in mismatches[:10]:
                    print(f"          line {index}")
                    print(f"            md   {a!r}")
                    print(f"            docx {b!r}")
            else:
                print("    OK    every code line matches the Markdown source exactly")

        bad = scan_characters(dx_norm, "docx code")
        bad += scan_characters(md_norm, "md code")
        if bad:
            failures += 1
        else:
            print("    OK    no typographic quotes, and no stray dashes outside string literals")

        quotes = sum(line.count('"') for line in dx_norm)
        print(f"    {quotes} straight double quotes preserved inside the code blocks")

    print()
    if failures:
        print(f"{failures} problem(s) found. The DAX in the Word files is not safe to copy.")
        return 1
    print("The DAX in both Word files is byte-identical to the Markdown and safe to paste.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
