"""Generate the Word deliverables from the Markdown sources in powerbi/."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from md_to_docx import convert  # noqa: E402

PBI = Path(__file__).resolve().parent.parent / "powerbi"

DOCS = [
    {
        "md": PBI / "GUIA_DE_ARMADO.md",
        "docx": PBI / "Guia de armado - Power BI.docx",
        "title": "Guía de armado del dashboard",
        "subtitle": "Construcción del CX Quality Dashboard en Power BI  ·  Business Case DiDi",
        "footer": "Guía de armado — DiDi CX Quality Dashboard",
    },
    {
        "md": PBI / "DAX_Measures.md",
        "docx": PBI / "Medidas DAX.docx",
        "title": "Medidas DAX",
        "subtitle": "Capa de cálculo del CX Quality Dashboard  ·  Business Case DiDi",
        "footer": "Medidas DAX — DiDi CX Quality Dashboard",
    },
]


def main() -> None:
    locked = []
    for spec in DOCS:
        if not spec["md"].exists():
            print(f"SKIP  {spec['md'].name} no existe")
            continue
        target = spec["docx"]
        try:
            convert(spec["md"], target, spec["title"], spec["subtitle"], spec["footer"])
        except PermissionError:
            # Word keeps an exclusive lock while the file is open. Write next to it
            # so the regenerated content is not lost.
            target = target.with_name(f"{target.stem} (actualizado){target.suffix}")
            convert(spec["md"], target, spec["title"], spec["subtitle"], spec["footer"])
            locked.append(spec["docx"])
        size_kb = target.stat().st_size / 1024
        print(f"OK    {target.name}  ({size_kb:,.0f} KB)")

    for path in locked:
        print(f"\nAVISO  {path.name} estaba abierto en Word y no se pudo sobrescribir.")
        print(f"       Cierra el archivo y vuelve a ejecutar, o usa la version '(actualizado)'.")


if __name__ == "__main__":
    main()
