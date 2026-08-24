"""Build the reusable DiDi CX visual template system as a Canva-importable PPTX.

Placeholder content only. No business data, no analysis, no real figures.
Five layouts: cover, executive summary (KPI cards), data overview (table),
key insight (callout), action plan (table).
"""

from __future__ import annotations

import os
import sys

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from didi_deck import (  # noqa: E402
    BAND_H, BAND_RULE_H, CONTENT_W, COVER_CAP, COVER_SUB, GREY_LINE, GREY_PANEL,
    GREY_SERIES, GREY_SOFT, GREY_TEXT, INK, MARGIN, ORANGE, ROOT, STATUS, SH, SW,
    WHITE, blank, build_mark, configure_widescreen, content_slide, data_table,
    dot, didi_mark, header_band, icon_bars, icon_bulb, icon_calendar, icon_globe,
    icon_people, icon_ring, icon_trend, kpi_card, line, oval, panel, rect,
    round_rect, status_badge, text,
)
from pptx.enum.dml import MSO_LINE_DASH_STYLE  # noqa: E402

OUT_DIR = os.path.join(ROOT, "entregable 2", "template")
OUT_PPTX = os.path.join(OUT_DIR, "DiDi_CX_Template_System.pptx")

SUBTITLE = "[Section subtitle or date range]"


def slide_cover(prs):
    s = blank(prs)
    rect(s, 0, 0, SW, SH, fill=INK)

    mark, word_w = 0.62, 1.30
    lx = (SW - (mark + 0.16 + word_w)) / 2
    didi_mark(s, lx, 1.79, mark)
    text(s, lx + mark + 0.16, 1.79, word_w, mark, "DiDi",
         size=30, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)

    text(s, MARGIN, 2.78, CONTENT_W, 0.75, "[Presentation title goes here]",
         size=33, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    text(s, MARGIN, 3.63, CONTENT_W, 0.35, "[Business case subtitle goes here]",
         size=15, color=COVER_SUB, align=PP_ALIGN.CENTER)
    rect(s, (SW - 1.0) / 2, 4.28, 1.0, 0.035, fill=ORANGE)

    trio = [(icon_calendar, "[Date range]"), (icon_globe, "[Geography / Region]"),
            (icon_people, "[Prepared for]")]
    for (draw, caption), cx in zip(trio, [SW / 2 - 3.25, SW / 2, SW / 2 + 3.25]):
        draw(s, cx, 5.85, 0.50)
        text(s, cx - 1.5, 6.32, 3.0, 0.3, caption,
             size=10, color=COVER_CAP, align=PP_ALIGN.CENTER)
    return s


def slide_exec_summary(prs):
    s = content_slide(prs, "[Executive summary]", SUBTITLE)

    cards = [("green", "On goal", "+X.X% vs [target or prior]", True),
             ("amber", "Within 5 points", "+X.X% vs [target or prior]", True),
             ("red", "More than 5 points off", "-X.X% vs [target or prior]", False)]
    gap = 0.22
    cw = (CONTENT_W - 2 * gap) / 3
    for i, (status, chip, delta, up) in enumerate(cards):
        kpi_card(s, MARGIN + i * (cw + gap), 1.38, cw, 1.70,
                 "[KPI label]", "XX.X%", delta, status, chip, up=up)

    px, py, ph = MARGIN, 3.30, 3.62
    km_w = 2.72
    pw = CONTENT_W - km_w - gap
    panel(s, px, py, pw, ph, "[Chart title goes here]")

    legend = [("Series 1", ORANGE, None), ("Series 2", GREY_SERIES, None),
              ("Series 3", GREY_SERIES, MSO_LINE_DASH_STYLE.DASH)]
    lx = px + pw - 3.55
    for label, color, dash in legend:
        line(s, lx, py + 0.32, lx + 0.34, py + 0.32, color=color, width=1.5, dash=dash)
        text(s, lx + 0.42, py + 0.21, 0.85, 0.22, label, size=8.5, color=GREY_TEXT)
        lx += 1.18

    plot_l, plot_r = px + 0.78, px + pw - 0.28
    plot_t, plot_b = py + 0.72, py + ph - 0.62
    for pct in (100, 75, 50, 25, 0):
        gy = plot_b - (pct / 100) * (plot_b - plot_t)
        line(s, plot_l, gy, plot_r, gy, color=GREY_LINE)
        text(s, px + 0.18, gy - 0.10, 0.52, 0.2, f"{pct}%",
             size=8, color=GREY_SOFT, align=PP_ALIGN.RIGHT)

    series = [([62, 70, 66, 74, 68, 78, 72, 80], ORANGE, 2.0, None),
              ([48, 52, 50, 46, 54, 44, 50, 52], GREY_SERIES, 1.25, None),
              ([35, 32, 38, 30, 36, 28, 34, 30], GREY_SERIES, 1.25,
               MSO_LINE_DASH_STYLE.DASH)]
    step = (plot_r - plot_l) / 7
    for values, color, width, dash in series:
        pts = [(plot_l + i * step, plot_b - (v / 100) * (plot_b - plot_t))
               for i, v in enumerate(values)]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            line(s, x1, y1, x2, y2, color=color, width=width, dash=dash)

    for i in range(8):
        bx = plot_l + i * step - 0.44
        round_rect(s, bx, plot_b + 0.16, 0.88, 0.26, radius=0.04,
                   fill=WHITE, line=GREY_LINE)
        text(s, bx, plot_b + 0.16, 0.88, 0.26, f"[Period {i + 1}]", size=7.5,
             color=GREY_TEXT, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    kx = px + pw + gap
    panel(s, kx, py, km_w, ph, "[Key metrics]")
    for i, draw in enumerate([icon_bars, icon_ring, icon_trend]):
        ry = py + 0.72 + i * 0.96
        oval(s, kx + 0.22, ry, 0.54, 0.54, fill=GREY_PANEL)
        draw(s, kx + 0.49, ry + 0.27, 0.28)
        text(s, kx + 0.90, ry + 0.02, 1.6, 0.2, "[Metric label]", size=8.5, color=GREY_TEXT)
        text(s, kx + 0.90, ry + 0.20, 1.6, 0.3, "XX", size=16, bold=True, color=INK)
        text(s, kx + 0.90, ry + 0.50, 1.6, 0.2, "[vs prior]", size=7.5, color=GREY_SOFT)
    return s


def slide_data_overview(prs):
    s = content_slide(prs, "[Data overview]", SUBTITLE)
    cols = [("[Column 1]", 2.40), ("[Column 2]", 2.40), ("[Column 3]", 2.40),
            ("[Column 4]", 2.40), ("[Status]", 2.733)]
    cycle = [("On goal", "green"), ("Within 5 points", "amber"),
             ("More than 5 points off", "red")]
    rows = [[f"[Item {i + 1}]", "[Placeholder]", "[Placeholder]", "[Placeholder]",
             cycle[i % 3]] for i in range(7)]
    data_table(s, MARGIN, 1.45, cols, rows, header_h=0.44, row_h=0.66,
               status_cols=(4,), size=8.5, header_size=9)
    return s


def slide_key_insight(prs):
    s = content_slide(prs, "[Key insight]", SUBTITLE)
    bx, by, bw, bh = 1.10, 1.85, SW - 2.20, 4.40
    rect(s, bx, by, bw, bh, fill=GREY_PANEL)
    rect(s, bx, by, 0.042, bh, fill=ORANGE)
    icon_bulb(s, bx + 1.40, by + bh / 2, 1.55)
    text(s, bx + 2.75, by + 1.62, bw - 3.50, 0.45, "[Insight headline goes here]",
         size=22, bold=True, color=INK)
    text(s, bx + 2.75, by + 2.30, bw - 3.50, 0.80,
         "[Key takeaway or conclusion goes here in one or two lines "
         "as a placeholder for the final insight.]",
         size=12, color=GREY_TEXT, line_spacing=1.35)
    return s


def slide_action_plan(prs):
    s = content_slide(prs, "[Action plan]", SUBTITLE)
    cols = [("[What]", 4.60), ("[Who]", 2.90), ("[When]", 2.60), ("[Status]", 2.233)]
    cycle = [("On track", "green"), ("At risk", "amber"), ("Off track", "red")]
    rows = [["[Action item placeholder]", "[Owner placeholder]",
             "[Due date placeholder]", cycle[i % 3]] for i in range(5)]
    data_table(s, MARGIN, 1.70, cols, rows, header_h=0.44, row_h=0.85,
               status_cols=(3,), size=8.5, header_size=9)
    return s


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    build_mark()

    prs = Presentation()
    configure_widescreen(prs)

    slide_cover(prs)
    slide_exec_summary(prs)
    slide_data_overview(prs)
    slide_key_insight(prs)
    slide_action_plan(prs)

    prs.save(OUT_PPTX)
    print(f"OK -> {OUT_PPTX}")


if __name__ == "__main__":
    main()
