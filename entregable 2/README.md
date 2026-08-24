# Deliverable 2 — Weekly Performance Report

CX Service Operations · Delivery LOB · May 2026 (W19–W22)

## What to open

| File | Use |
|------|-----|
| `Entregable_2_Weekly_Performance_Report.pdf` | The submission copy. 32 slides, 16:9. |
| `deck/Entregable_2_Weekly_Performance_Report.pptx` | Source deck. Import into Canva to edit. |
| `deck/preview/` | One PNG per slide, for a quick visual pass. |
| `Companion_Guide.pdf` | Study guide: the thesis, the ten numbers, the slide-by-slide script and the hard questions with answers. |
| `template/DiDi_CX_Template_System.pptx` | The empty visual system the report is built on. |

## Structure

The deck follows the report structure required by section 4 of the business case.

| Slides | Section |
|--------|---------|
| 1–2 | Cover, scope, data sources and assumptions (check sheet) |
| 3–6 | Executive summary, two paths, the critical finding, control charts |
| 7–12 | QA analysis by channel (Phone, Live Chat) and by CR Lv4 |
| 13–15 | CSAT and voice of the customer |
| 16–18 | Recontact analysis |
| 19–21 | People: agent quartiles, outliers and the supervisor coaching queue |
| 22–27 | Combined analysis, closure vs CSAT, 5 whys, Ishikawa, proposed control |
| 28–32 | Action plans by Business Type, channel and governance, matrix, recommendation |

Numeric cells are colour-coded against their goal (green at or above, amber within
5 points, red beyond) so a table can be read as a heatmap. Status badges keep the
word next to the colour, so the coding never depends on colour alone.

The action plans rate **problem severity** — how bad the underlying gap is — not the
progress of an action, since none of them has started.

## Quality tools used

Check sheet, Pareto chart (defects, Phone, Live Chat, recontact), histogram,
individuals control charts (QA, CSAT, recontact), scatter diagram with
correlation, Ishikawa diagram and a process flowchart.

## Regenerating

Every number is read from the same pipeline that feeds the dashboard, so the two
deliverables cannot disagree. Rebuild in order:

```powershell
py -3.11 scripts/build_e2_charts.py            # renders charts to entregable 2/deck/charts
py -3.11 scripts/build_entregable2_deck.py     # assembles the deck
py -3.11 scripts/build_companion_guide_pdf.py  # renders Companion_Guide.md to PDF
```

`scripts/didi_deck.py` holds the shared visual system (brand tokens, KPI cards,
tables, callouts, section dividers) used by both this report and the empty
template.
