"""Deliverable 2 — Weekly Performance Report, built on the DiDi CX template system.

Every figure is read from the same pipeline that feeds the dashboard, so the deck
and the dashboard can never disagree.
"""

from __future__ import annotations

import os
import sys

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import config  # noqa: E402
from modules.data_loader import load_all_data  # noqa: E402
from modules import kpis as K  # noqa: E402
from modules import executive_engine as EE  # noqa: E402
from modules import alerts as A  # noqa: E402
from modules.resolution_csat import resolution_story  # noqa: E402

from cr_labels import cr_label  # noqa: E402
from didi_deck import (  # noqa: E402
    CONTENT_W, COVER_CAP, COVER_SUB, GREY_CELL, GREY_LINE, GREY_PANEL, GREY_SOFT,
    GREY_TEXT, INK, MARGIN, ORANGE, ROOT, SH, STATUS, SW, WHITE, blank, build_mark,
    bullets, callout, cause_chain, configure_widescreen, content_slide, data_table, didi_mark,
    footnote, icon_calendar, icon_globe, icon_people, kpi_card, panel, picture,
    rect, section_slide, status_badge, text, apply_sheet_numbers,
)

CHARTS = os.path.join(ROOT, "entregable 2", "deck", "charts")
OUT_DIR = os.path.join(ROOT, "entregable 2", "deck")
OUT_PPTX = os.path.join(OUT_DIR, "Entregable_2_Weekly_Performance_Report.pptx")

FOOTER = "DiDi Global, CX Service Operations   |   Confidential. Internal use only"
BODY_TOP = 1.32
BODY_BOT = 6.95


def chart(name):
    return os.path.join(CHARTS, name)


def st(value, goal, lower_better=False):
    gap = (value - goal) if lower_better else (goal - value)
    if gap <= 0:
        return "green"
    return "amber" if gap <= 5 else "red"


def st_res(value):
    if value >= 70:
        return "green"
    if value > 50:
        return "amber"
    return "red"


def pp(value, digits=2):
    return f"+{value:.{digits}f}" if value >= 0 else f"{value:.{digits}f}"


def csat_cell(val):
    """Heat cell for a CSAT %, or an em dash when that channel has no surveys."""
    if val is None:
        return ("—", None)
    try:
        v = float(val)
    except (TypeError, ValueError):
        return ("—", None)
    if v != v:
        return ("—", None)
    return (f"{v:.1f}%", st(v, 85))


def chat_qa_pair(D, decimals=2):
    """Official Chat QA vs the what-if if process-fails scored 0. Not the same number."""
    cur = f"{D['ch'].loc['Live Chat', 'QA_Score']:.{decimals}f}"
    adj = f"{D['chat_qa_if_noproc0']:.{decimals}f}"
    return (f"Current Chat QA: {cur}. "
            f"Adjusted QA under proposed scoring: {adj}")


def closure_csat_line(D):
    """Association, not causation. R² 0.64 is strong; it does not prove closing causes CSAT."""
    return ("Closure is strongly associated with CSAT and is a more meaningful "
            "indicator of customer outcome than current QA.")


def channel_close_stats(audits, channel):
    """Auditor solution on assessed contacts. Not FCR. Abandoned stays out of the close rate."""
    sub = audits[audits["Channel"] == channel]
    s = sub["Solution_Provided"].astype("string").str.strip()
    proc_col = "Process_Followed" if "Process_Followed" in sub.columns else (
        "Process_Adherence" if "Process_Adherence" in sub.columns else None
    )
    p = sub[proc_col].astype("string").str.strip() if proc_col else None
    n = int(len(sub))
    resolved = int(s.eq("Resolved").sum())
    not_resolved = int(s.eq("Not resolved").sum())
    abandoned = int(s.eq("Abandoned").sum())
    assessed = resolved + not_resolved
    unres_process = 0
    if p is not None and not_resolved:
        unres_process = int((s.eq("Not resolved") & p.eq("Followed process")).sum())
    return {
        "n": n,
        "resolved": resolved,
        "not_resolved": not_resolved,
        "abandoned": abandoned,
        "assessed": assessed,
        "close_pct": round(100 * resolved / assessed, 1) if assessed else None,
        "unres_pct": round(100 * not_resolved / assessed, 1) if assessed else None,
        "abandon_pct": round(100 * abandoned / n, 1) if n else None,
        "unres_process": unres_process,
    }


def close_ten_line(D):
    """Plain-language close rates. 9 of 10 / 6 of 10. Not FCR."""
    p, c = D["close"]["Phone"], D["close"]["Live Chat"]
    return (f"Among assessed contacts (auditor solution, not FCR), Phone closes about 9 of 10 "
            f"({p['close_pct']:.1f}%) and Chat about 6 of 10 ({c['close_pct']:.1f}%). "
            f"{c['unres_process']} of {c['not_resolved']} unresolved chats followed process.")


def slide(prs, title, subtitle, tag=""):
    s = content_slide(prs, title, subtitle, tag)
    footnote(s, FOOTER)
    return s


# =============================================================================
#  Slides
# =============================================================================


def s_cover(prs, D):
    s = blank(prs)
    rect(s, 0, 0, SW, SH, fill=INK)
    mark, word_w = 0.62, 1.30
    lx = (SW - (mark + 0.16 + word_w)) / 2
    didi_mark(s, lx, 1.62, mark)
    text(s, lx + mark + 0.16, 1.62, word_w, mark, "DiDi", size=30, bold=True,
         color=WHITE, anchor=MSO_ANCHOR.MIDDLE)

    text(s, MARGIN, 2.62, CONTENT_W, 0.75, "Weekly Performance Report",
         size=36, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    text(s, MARGIN, 3.52, CONTENT_W, 0.35,
         "CX Service Operations  ·  Delivery LOB  ·  Phone and Live Chat",
         size=15, color=COVER_SUB, align=PP_ALIGN.CENTER)
    rect(s, (SW - 1.0) / 2, 4.16, 1.0, 0.035, fill=ORANGE)
    text(s, MARGIN, 4.42, CONTENT_W, 0.30,
         "Deliverable 2: CX Quality Analyst business case",
         size=11, color=COVER_CAP, align=PP_ALIGN.CENTER)

    trio = [(icon_calendar, "1–31 May 2026  ·  W19–W22"),
            (icon_globe, "MX  ·  CO  ·  CR  ·  PE"),
            (icon_people, "Prepared for CX Leadership")]
    for (draw, caption), cx in zip(trio, [SW / 2 - 3.25, SW / 2, SW / 2 + 3.25]):
        draw(s, cx, 5.72, 0.50)
        text(s, cx - 1.7, 6.19, 3.4, 0.3, caption, size=10, color=COVER_CAP,
             align=PP_ALIGN.CENTER)
    return s


def s_scope(prs, D):
    s = slide(prs, "Scope, data and assumptions",
              "What this report is built on", "00")
    cols = [("Source", 2.05), ("Grain: one row is…", 3.25), ("Volume", 1.35),
            ("Period", 1.55), ("What it answers", 4.13)]
    rows = [
        ["QA audits", "One audited interaction", f"{D['vols']['evaluations']:,}",
         "4–29 May", "QA score, attribute defects, channel"],
        ["QA attribute fails", "One failed attribute in an audit",
         f"{D['crit']['total_fails']:,}", "4–29 May", "Pareto of defects, critical vs non-critical"],
        ["CSAT surveys", "One survey answer", f"{D['vols']['surveys']:,}",
         "1–31 May", "CSAT %, star mix, verbatim comments"],
        ["Recontact", "One contact-reason / channel / day",
         f"{D['vols']['contacts']:,}", "1–31 May", "Recontact rate, repeat volume by reason"],
    ]
    data_table(s, MARGIN, BODY_TOP + 0.08, cols, rows, header_h=0.42, row_h=0.52,
               size=8.5)

    y = BODY_TOP + 0.08 + 0.42 + 4 * 0.52 + 0.30
    text(s, MARGIN, y, 5.9, 0.26, "How we treated the data",
         size=11, bold=True, color=INK)
    bullets(s, MARGIN, y + 0.38, 5.9, [
        "If an attribute is N/A (value 2), we drop it from both the top and the bottom of the score.",
        "One fail on a Critical attribute sends the interaction score to 0.",
        "Phone is scored on 12 attributes. Live Chat on 8. Never mixed. Official QA does not use the solution/process dropdown.",
        "CSAT and recontact are one ratio for the month. Not an average of daily averages.",
        "Agents with fewer than 5 audits do not appear in individual rankings.",
    ], size=9.5, gap=0.32)

    text(s, 6.90, y, 5.94, 0.26, "What this report does not cover",
         size=11, bold=True, color=INK)
    bullets(s, 6.90, y + 0.38, 5.94, [
        f"Delivery is the only line of business in the data. Cuts by LOB collapse to Business Type.",
        f"QA covers {D['ch'].loc['Phone', 'QA_Share']:.1f}% Phone and "
        f"{D['ch'].loc['Live Chat', 'QA_Share']:.1f}% Live Chat. Phone is under-sampled.",
        f"Recontact covers 12 channels. Only Phone and Live Chat are also audited.",
        f"QA and CSAT share {D['cov']['qa_csat']} contact reasons. The link between them uses only those.",
        "Surveys cover the full month. Audits start on 4 May (W19).",
    ], size=9.5, gap=0.32)
    return s


def s_exec_summary(prs, D):
    s = slide(prs, "Executive summary", "Performance against goal  ·  May 2026", "01")
    su, rc = D["summary"], D["rc_rate"]

    cards = [
        ("QA SCORE", f"{su['qa_score']:.2f}", f"{pp(su['qa_score'] - 85)} pp vs 85 goal",
         st(su["qa_score"], 85), "On goal", True),
        ("CSAT (BLENDED)", f"{su['csat']:.2f}%", f"{pp(su['csat'] - 85)} pp vs 85% goal",
         st(su["csat"], 85), "More than 5 points off", False),
        ("RECONTACT (GLOBAL)", f"{rc:.2f}%", f"{pp(rc - 5.44)} pp vs 5.44% goal",
         st(rc, 5.44, lower_better=True), "Within 5 points", False),
    ]
    gap = 0.22
    cw = (8.55 - 2 * gap) / 3
    for i, (label, value, delta, status, chip, up) in enumerate(cards):
        kpi_card(s, MARGIN + i * (cw + gap), BODY_TOP, cw, 1.72, label, value, delta,
                 status, chip, value_size=27, up=up)

    kx = MARGIN + 8.55 + gap
    kw = CONTENT_W - 8.55 - gap
    panel(s, kx, BODY_TOP, kw, 1.72, "Week in volume")
    stats = [(f"{D['vols']['contacts']:,}", "customer contacts"),
             (f"{D['vols']['surveys']:,}", "CSAT surveys"),
             (f"{D['vols']['evaluations']:,}", "QA audits")]
    for i, (v, lab) in enumerate(stats):
        yy = BODY_TOP + 0.55 + i * 0.38
        text(s, kx + 0.24, yy, 1.5, 0.26, v, size=12, bold=True, color=INK)
        text(s, kx + 1.80, yy + 0.03, 1.9, 0.24, lab, size=8.5, color=GREY_TEXT)

    y = BODY_TOP + 2.00
    text(s, MARGIN, y, 7.55, 0.26, "The 10-second read", size=11,
         bold=True, color=INK)
    text(s, MARGIN, y + 0.36, 7.55, 3.1, [
        [("Two of three metrics missed goal. ", {"bold": True, "color": INK}),
         (f"QA was strong at {su['qa_score']:.2f}, while blended CSAT was below target at "
          f"{su['csat']:.2f}% (Phone {D['ch'].loc['Phone', 'CSAT_Score']:.1f}%, "
          f"Chat {D['ch'].loc['Live Chat', 'CSAT_Score']:.1f}%). Recontact was {rc:.2f}%, "
          f"slightly above the 5.44% goal, although the final week improved to "
          f"{D['weekly'].iloc[-1]['Recontact_Rate']:.2f}%.",
          {})],
        [("High QA does not necessarily mean a good customer outcome. ", {"bold": True, "color": INK}),
         (f"Across {D['cov']['qa_csat']} shared contact reasons, QA and CSAT have almost no "
          f"relationship (R² = {D['corr_qa_csat']['R2']:.3f}). Live Chat scores "
          f"{D['ch'].loc['Live Chat', 'QA_Score']:.1f} on QA but only "
          f"{D['ch'].loc['Live Chat', 'CSAT_Score']:.1f}% on CSAT, while Phone scores "
          f"{D['ch'].loc['Phone', 'QA_Score']:.1f} on QA and "
          f"{D['ch'].loc['Phone', 'CSAT_Score']:.1f}% on CSAT.",
          {})],
        [("Two gaps stand out in the scorecard. ", {"bold": True, "color": ORANGE}),
         (f"First, {D['unres_proc_n']:,} audits followed process but did not resolve the case, "
          f"yet still averaged {D['unres_proc_score']:.2f} QA. We should keep the agent score "
          f"but also track whether the case was closed. Second, Chat does not treat correct "
          f"information as a critical attribute. As a result, {D['chat_noproc_n100']:,} of "
          f"{D['chat_noproc_n']:,} process-fail chats still score 100. Under the proposed "
          f"scoring change, Chat QA would fall to {D['chat_qa_if_noproc0']:.2f}.",
          {})],
    ], size=10.5, color=GREY_CELL, line_spacing=1.30, space_after=8)

    panel(s, 8.45, y, CONTENT_W - 7.95, 3.55, "Status legend")
    bullets(s, 8.67, y + 0.62, 4.20, [
        [("Green ", {"bold": True, "color": INK}), (": at or above goal.", {})],
        [("Amber ", {"bold": True, "color": INK}), (": within 5 points of goal.", {})],
        [("Red ", {"bold": True, "color": INK}), (": more than 5 points off goal.", {})],
    ], size=9.5, gap=0.30)
    text(s, 8.67, y + 1.62, 4.20, 1.7,
         f"QA is measured against 85. CSAT against 85%. Recontact against 5.44%, and lower "
         f"is better. That 5.44% goal is on the global rate (all channels). "
         f"Built on {D['vols']['evaluations']:,} audits, "
         f"{D['vols']['surveys']:,} surveys and {D['vols']['contacts']:,} contacts.",
         size=9.5, color=GREY_TEXT, line_spacing=1.34)
    return s


def _rc_rate(D, wanted):
    g = D["rc_cr"]
    if g is None or g.empty:
        return None
    key = str(wanted).strip().casefold()
    hit = g[g["CR_Lv4"].astype(str).str.strip().str.casefold().eq(key)]
    if hit.empty:
        return None
    return float(hit.iloc[0]["Recontact_Rate"])


def s_two_paths(prs, D):
    R = D["res"]
    themes = R.get("nr_followed_themes") or {}
    pol = int(themes.get("policy_blocked") or 0)
    tools = int(themes.get("tools_system") or 0)
    assessed = R["n_resolved"] + R["n_not_resolved"]
    close_pct = 100 * R["n_resolved"] / assessed if assessed else 0
    followed_pct = 100 * R["n_followed_nr"] / R["n_not_resolved"] if R["n_not_resolved"] else 0
    a_rows = R.get("cr_a") or []
    a_csats = [r["csat"] for r in a_rows[:4] if r.get("csat") is not None]
    a_lo, a_hi = (min(a_csats), max(a_csats)) if a_csats else (None, None)
    a_names = "Wrong / damaged / inedible / incomplete order"
    green_rc = [v for v in (
        _rc_rate(D, "wrong order"),
        _rc_rate(D, "damaged order"),
        _rc_rate(D, "incomplete order"),
        _rc_rate(D, "inedible order"),
    ) if v is not None]
    r2_close = R.get("cr_r2")
    r2_txt = f"{r2_close:.2f}" if r2_close is not None else "—"

    s = slide(
        prs, "Two paths after the same QA step",
        f"QA scores step 2. CSAT scores step 4. Recontact is step 5. "
        f"Close vs CSAT R² {r2_txt}  ·  QA vs CSAT R² {D['corr_qa_csat']['R2']:.3f}",
        "04",
    )
    picture(s, chart("cx_two_paths.png"), MARGIN, BODY_TOP, CONTENT_W, 3.08)

    y = BODY_TOP + 3.12
    text(s, MARGIN, y, CONTENT_W, 0.22, "What May shows on each path",
         size=10.5, bold=True, color=INK)
    green_csat = (f"{a_names}: {a_lo:.0f}–{a_hi:.0f}% CSAT"
                  if a_lo is not None else "Closeable reasons sit above the 85% CSAT goal")
    green_rc_txt = (
        f"Those reasons: {min(green_rc):.1f}–{max(green_rc):.1f}% recontact"
        if green_rc else "Closeable reasons sit near or under the 5.44% goal"
    )
    cols = [(" ", 1.42), ("If policy / tools allow it", 5.45),
            ("If they do not", 5.46)]
    rows = [
        ["Step 2 · QA",
         f"{D['res_proc_n']:,} audits resolved + followed process · QA {D['res_proc_score']:.2f}",
         f"{D['unres_proc_n']:,} audits not resolved + followed process · QA {D['unres_proc_score']:.2f}"],
        ["Step 3 · Close",
         f"Closed {R['n_resolved']:,} of {assessed:,} assessed ({close_pct:.1f}%)",
         f"{followed_pct:.1f}% of not-resolved still followed process · {pol:,} policy + {tools:,} tools"],
        ["Step 4 · CSAT",
         green_csat,
         f"Order status & delays: {D['os_csat']:.1f}% CSAT despite QA {D['os_qa']:.1f}"],
        ["Step 5 · Recontact",
         green_rc_txt,
         f"Order status & delays: {D['os_rc']:.2f}% ({D['os_repeats']:,} repeats) · human {D['rc_audited']:.2f}%"],
    ]
    data_table(s, MARGIN, y + 0.26, cols, rows, header_h=0.34, row_h=0.42,
               size=8, header_size=8, bold_first=True)
    text(s, MARGIN, y + 0.26 + 0.34 + 4 * 0.42 + 0.06, CONTENT_W, 0.20,
         "CSAT is the official ratio of that contact reason, not a ticket score. "
         "Both paths can score green on QA. Only the close path lines up with CSAT and recontact.",
         size=8, color=GREY_TEXT)
    return s


def s_critical(prs, D):
    s = slide(prs, "The finding that needs a decision",
              "We are scoring the conversation. The customer is scoring the result.", "01")
    cause_chain(s, MARGIN, BODY_TOP, CONTENT_W, [
        ("Customer has a problem", ""),
        ("Agent follows the process", "QA"),
        ("The process cannot close it", ""),
        ("Customer is unsatisfied", "CSAT"),
        ("Contacts us again", "Recontact"),
    ], h=0.68)
    callout(s, MARGIN, BODY_TOP + 0.78, CONTENT_W, 1.05,
            "QA stays high even when the case is not resolved",
            f"The agent followed process, but the case was not resolved. These "
            f"{D['unres_proc_n']:,} audits still averaged {D['unres_proc_score']:.2f} QA. "
            f"Keep the agent score, but also track closure. Chat has a second gap: correct "
            f"information is not scored as a critical attribute. As a result, "
            f"{D['chat_noproc_n100']:,} of {D['chat_noproc_n']:,} process-fail chats still "
            f"score 100. Under the proposed scoring, Chat QA would be "
            f"{D['chat_qa_if_noproc0']:.2f}. Overall, {D['perfect_share']:.1f}% of audits "
            f"currently score exactly 100.",
            size_head=13, size_body=10)

    y = BODY_TOP + 1.92
    picture(s, chart("bar_auditor_outcome.png"), MARGIN, y, 6.55, 2.60)
    picture(s, chart("scatter_qa_csat.png"), MARGIN + 6.72, y, 6.11, 2.60)

    y2 = y + 2.72
    text(s, MARGIN, y2, 6.4, 0.24, "What the audits show", size=10.5,
         bold=True, color=INK)
    bullets(s, MARGIN, y2 + 0.34, 6.4, [
        f"{D['unres_proc_n']:,} audits followed process but did not resolve the case, yet still averaged {D['unres_proc_score']:.2f} QA.",
        f"{D['chat_noproc_n100']:,} of {D['chat_noproc_n']:,} process-fail chats still score 100.",
        f"Under the proposed scoring, Chat QA would be {D['chat_qa_if_noproc0']:.2f}, below the 85 goal.",
    ], size=9.5, gap=0.30)

    text(s, MARGIN + 6.72, y2, 6.1, 0.24, "Does higher QA mean better customer outcomes?", size=10.5,
         bold=True, color=INK)
    bullets(s, MARGIN + 6.72, y2 + 0.34, 6.1, [
        f"The link between QA and CSAT is {D['corr_qa_csat']['Pearson_r']:.3f} across {D['cov']['qa_csat']} contact reasons.",
        f"R² is {D['corr_qa_csat']['R2']:.3f}. QA explains {D['corr_qa_csat']['R2'] * 100:.1f}% of how CSAT varies. Almost none.",
        "CSAT is much more closely related to whether the case was resolved than to whether the agent followed the current QA process. Adding the Chat attribute would improve measurement, but would not directly improve CSAT.",
    ], size=9.5, gap=0.30)
    return s


def s_control(prs, D):
    s = slide(prs, "Was this a noisy month, or is this the process?",
              "One point per day. Whole month.", "01")
    y = BODY_TOP + 0.10
    w = (CONTENT_W - 0.36) / 3
    for i, (img, cap) in enumerate([
        ("run_qa.png", "QA: one dip on 6 May. Otherwise steady"),
        ("run_csat.png", "CSAT blended: steady. Every day below goal"),
        ("run_recontact.png", "Recontact global: last week under goal. Month still amber"),
    ]):
        x = MARGIN + i * (w + 0.18)
        picture(s, chart(img), x, y, w, 2.55)
        text(s, x, y + 2.64, w, 0.24, cap, size=9, bold=True, color=INK,
             align=PP_ALIGN.CENTER)

    y2 = y + 3.12
    callout(s, MARGIN, y2, CONTENT_W, 1.95,
            "Blended CSAT remained below goal throughout the month",
            [f"All {D['csat_days']} days stayed within the normal control limits "
             f"({D['csat_lcl']:.2f}–{D['csat_ucl']:.2f}), but every day remained below the 85% CSAT goal. "
             f"This suggests a consistent process issue rather than a single bad day or agent. "
             f"QA had one notable dip on 6 May ({D['qa_low']:.2f}), while recontact improved "
             f"during the final week to {D['weekly'].iloc[-1]['Recontact_Rate']:.2f}% "
             f"(month still {D['rc_rate']:.2f}%, above the 5.44% goal).",
             "CSAT is more likely to improve when agents have a clear way to resolve the issue—"
             "for example, approving a refund, seeing an ETA, or escalating through a defined path. "
             "Coaching alone is unlikely to shift a result that stayed below goal for all 31 days."],
            size_head=13, size_body=10)
    return s


def s_qa_channel(prs, D):
    s = slide(prs, "QA analysis by channel",
              "Phone and Live Chat scored on their own lists. Never mixed.", "02")
    picture(s, chart("channel_compare.png"), MARGIN, BODY_TOP, 7.15, 2.62)

    cols = [("Channel", 1.30), ("QA", 0.70), ("vs 85", 0.75), ("Audits", 0.85),
            ("Status", 1.15)]
    rows = []
    for name in ("Phone", "Live Chat"):
        r = D["ch"].loc[name]
        stat = st(r["QA_Score"], 85)
        rows.append([name, (f"{r['QA_Score']:.2f}", stat), pp(r["QA_Score"] - 85, 2),
                     f"{int(r['QA_N']):,}", badge(stat)])
    data_table(s, 7.90, BODY_TOP + 0.10, cols, rows, header_h=0.40, row_h=0.52,
               status_cols=(4,), heat_cols=(1,), align_right=(1, 2, 3),
               bold_first=True)

    text(s, 7.90, BODY_TOP + 1.66, 5.0, 0.24, "Why Phone is below the QA goal", size=10.5,
         bold=True, color=INK)
    bullets(s, 7.90, BODY_TOP + 2.00, 5.0, [
        "Phone handles a higher share of complex issues such as refunds, charges and undelivered orders.",
        f"Critical attributes fail in {D['ch_break']['Phone']['pct_fatal']:.2f}% of Phone audits, "
        f"compared with {D['ch_break']['Live Chat']['pct_fatal']:.2f}% in Chat.",
        f"Phone represents only {D['ch'].loc['Phone', 'QA_Share']:.1f}% of audits, so its lower score has limited impact on the overall QA result.",
    ], size=9.5, gap=0.32)

    y2 = BODY_TOP + 2.92
    callout(s, MARGIN, y2, CONTENT_W, 1.42,
            "Phone is below goal, while Chat represents most of the QA sample.",
            f"Phone QA is {D['ch'].loc['Phone', 'QA_Score']:.2f}, "
            f"{abs(D['ch'].loc['Phone', 'QA_Score'] - 85):.2f} points below goal. Chat is "
            f"{D['ch'].loc['Live Chat', 'QA_Score']:.2f} and represents "
            f"{D['ch'].loc['Live Chat', 'QA_Share']:.1f}% of audits, which drives the overall QA score to "
            f"{D['summary']['qa_score']:.2f}. Chat also uses a less stringent approach because "
            f"correct information is not currently a critical attribute. Under the proposed scoring, "
            f"Chat QA would be {D['chat_qa_if_noproc0']:.2f}. Despite the lower QA score, Phone has "
            f"higher CSAT than Chat ({D['ch'].loc['Phone', 'CSAT_Score']:.2f}% vs. "
            f"{D['ch'].loc['Live Chat', 'CSAT_Score']:.2f}%). {close_ten_line(D)}",
            size_head=13, size_body=10)
    return s


def s_qa_phone(prs, D):
    s = slide(prs, "QA analysis: Phone",
              f"{int(D['ch'].loc['Phone', 'QA_N']):,} audits  ·  12 attributes  ·  "
              f"score {D['ch'].loc['Phone', 'QA_Score']:.2f} vs 85 goal", "02")
    picture(s, chart("pareto_phone.png"), MARGIN, BODY_TOP, 7.05, 3.35)

    x = 7.80
    text(s, x, BODY_TOP + 0.02, 5.05, 0.24, "Contact reasons with the lowest QA",
         size=10.5, bold=True, color=INK)
    cols = [("Contact reason (CR Lv4)", 2.90), ("QA", 0.55), ("n", 0.42),
            ("Status", 1.10)]
    rows = []
    for _, r in D["qa_cr_phone"].head(5).iterrows():
        stat = st(r["QA_Score"], 85)
        rows.append([_short(r["CR_Lv4"], 40), (f"{r['QA_Score']:.1f}", stat),
                     f"{int(r['N'])}", badge(stat)])
    data_table(s, x, BODY_TOP + 0.36, cols, rows, header_h=0.36, row_h=0.46,
               status_cols=(3,), heat_cols=(1,), align_right=(1, 2), size=8)

    y = BODY_TOP + 0.36 + 0.36 + 5 * 0.46 + 0.26
    text(s, x, y, 5.05, 0.24, "What is driving these low scores", size=10.5, bold=True, color=INK)
    bullets(s, x, y + 0.34, 5.05, [
        "These five reasons mainly involve disputed charges or undelivered orders. Agents often depend on system information before they can move forward.",
        "Time management is the main issue, followed by complete and correct information.",
        "Because that attribute is critical, a failure reduces the score to 0.",
        "Calls can run long without giving the customer a clear next step.",
    ], size=9.5, gap=0.32)

    y2 = BODY_TOP + 3.52
    text(s, MARGIN, y2, 7.05, 0.24, "What this chart is saying", size=10.5, bold=True,
         color=INK)
    ph = D["attr_phone"]
    bullets(s, MARGIN, y2 + 0.34, 7.05, [
        f"Time management accounts for {ph.iloc[0]['Pct_Of_Fails']:.1f}% of Phone defects "
        f"({int(ph.iloc[0]['Fail_Count'])} fails). This month: system-check script at the start of money and undelivered calls; escalate if no data in 2 minutes.",
        f"Complete and correct information adds another {int(ph.iloc[1]['Fail_Count'])} fails "
        f"and has a larger score impact ({abs(ph.iloc[1]['Impact_pp']):.2f} pp) because it is critical. This month: 1-page job aid for undelivered and refund CRs; coach those audits.",
        f"Together, these two attributes represent "
        f"{ph.iloc[0]['Pct_Of_Fails'] + ph.iloc[1]['Pct_Of_Fails']:.1f}% of Phone defects. Month 1 Phone work is these two attributes only.",
    ], size=9.5, gap=0.32)
    return s


def s_qa_chat(prs, D):
    s = slide(prs, "QA analysis: Live Chat",
              f"{int(D['ch'].loc['Live Chat', 'QA_N']):,} audits  ·  8 attributes  ·  "
              f"official score {D['ch'].loc['Live Chat', 'QA_Score']:.2f} vs 85 goal", "02")
    picture(s, chart("pareto_chat.png"), MARGIN, BODY_TOP, 7.05, 3.35)

    x = 7.80
    text(s, x, BODY_TOP + 0.02, 5.05, 0.24, "Contact reasons with the lowest QA",
         size=10.5, bold=True, color=INK)
    cols = [("Contact reason (CR Lv4)", 2.90), ("QA", 0.55), ("n", 0.42),
            ("Status", 1.10)]
    rows = []
    for _, r in D["qa_cr_chat"].head(5).iterrows():
        stat = st(r["QA_Score"], 85)
        rows.append([_short(r["CR_Lv4"], 40), (f"{r['QA_Score']:.1f}", stat),
                     f"{int(r['N'])}", badge(stat)])
    data_table(s, x, BODY_TOP + 0.36, cols, rows, header_h=0.36, row_h=0.46,
               status_cols=(3,), heat_cols=(1,), align_right=(1, 2), size=8)

    y = BODY_TOP + 0.36 + 0.36 + 5 * 0.46 + 0.26
    text(s, x, y, 5.05, 0.24, "What is driving the gap", size=10.5, bold=True, color=INK)
    bullets(s, x, y + 0.34, 5.05, [
        "Chat does not currently treat complete and correct information as a critical attribute, unlike Phone.",
        f"As a result, {D['chat_noproc_n100']:,} of {D['chat_noproc_n']:,} process-fail chats still score 100.",
        f"Under the proposed scoring, Chat QA would be {D['chat_qa_if_noproc0']:.2f}, below the 85 goal.",
    ], size=9.5, gap=0.32)

    y2 = BODY_TOP + 3.52
    text(s, MARGIN, y2, 7.05, 0.24, "What this chart is saying", size=10.5, bold=True,
         color=INK)
    lc = D["attr_chat"]
    bullets(s, MARGIN, y2 + 0.34, 7.05, [
        f"Greeting and identification account for {lc.iloc[0]['Pct_Of_Fails']:.1f}% of Chat defects, "
        f"followed by service attitude at {lc.iloc[1]['Pct_Of_Fails']:.1f}%. This month: mandatory open-chat greeting/ID macro, and next-step macros on stuck CRs.",
        f"Service availability has the largest score impact among these defects because it is critical "
        f"({int(lc.iloc[2]['Fail_Count'])} fails, {abs(lc.iloc[2]['Impact_pp']):.2f} pp). This month: WFM/Chat Ops on queue, wrap-up, and not leaving the chat hanging.",
        "The current Chat form also does not check whether the agent used the knowledge base or provided correct information. That is a measurement change, separate from this month's defect correction.",
    ], size=9.5, gap=0.32)
    return s


def s_qa_defects(prs, D):
    s = slide(prs, "QA analysis: where the defects are",
              "20 attributes scored (12 Phone, 8 Chat). Official QA never mixes them. This chart is a blended view.",
              "02")
    picture(s, chart("pareto_defects.png"), MARGIN, BODY_TOP, 7.10, 3.55)
    picture(s, chart("hist_qa.png"), 7.85, BODY_TOP + 0.10, 5.00, 3.05)

    y = BODY_TOP + 3.30
    text(s, 7.85, y, 5.00, 0.24, "How the scores are distributed", size=10.5, bold=True,
         color=INK)
    bullets(s, 7.85, y + 0.34, 5.00, [
        f"{D['perfect_share']:.1f}% of audits score exactly 100, while "
        f"{D['zero_share']:.1f}% score 0 because of a critical failure.",
        "Very few audits fall between these two extremes, making the current scale behave more like pass/fail than a continuous score.",
    ], size=9.5, gap=0.30)

    y2 = BODY_TOP + 3.72
    text(s, MARGIN, y2, 7.10, 0.24, "What this chart is saying", size=10.5, bold=True, color=INK)
    bullets(s, MARGIN, y2 + 0.34, 7.10, [
        f"7 bars make {D['vital_pct']:.1f}% of all {D['crit']['total_fails']:,} fails. "
        f"That is not 7 of 20 attributes: Phone and Chat lists are separate (12 + 8).",
        "Orange is Phone. Grey is Chat. ★ is critical: one fail zeroes that audit. "
        "Phone criticals: complete information, refunds, denial, rudeness, service attitude. "
        "Chat criticals: service availability, chat objectivity.",
        "Time management (Phone, not critical) is the volume leader. "
        "Complete and correct information (Phone, critical) is fewer fails but costs more score. "
        "Month 1: Phone time management and complete information; Chat greeting, attitude, and availability.",
    ], size=9.5, gap=0.32)
    return s


def s_defect_focus(prs, D):
    ph = D["attr_phone"]
    lc = D["attr_chat"]
    s = slide(prs, "QA analysis: where we concentrate this month",
              "Correct the defects we already score. Chat information accuracy is a scoring change, separate from this list.",
              "02")
    cols = [("Defect", 2.55), ("Channel", 1.15), ("How we correct it", 5.35),
            ("Who", 1.85), ("When", 0.93)]
    rows = [
        [f"Time management ({int(ph.iloc[0]['Fail_Count'])} fails, {ph.iloc[0]['Pct_Of_Fails']:.1f}%)",
         "Phone",
         "System-check script at the start of money and undelivered calls. Escalate if no data in 2 minutes.",
         "Supervisors", "27 Jun"],
        [f"Complete and correct information ({int(ph.iloc[1]['Fail_Count'])} fails, {abs(ph.iloc[1]['Impact_pp']):.2f} pp)",
         "Phone",
         "1-page job aid for undelivered and refund CRs. Coach the agents on those audits.",
         "QA Lead + Supervisors", "27 Jun"],
        [f"Greeting and identification ({int(lc.iloc[0]['Fail_Count'])} fails, {lc.iloc[0]['Pct_Of_Fails']:.1f}%)",
         "Live Chat",
         "Mandatory open-chat greeting and identification macro.",
         "Chat Ops + QA Lead", "13 Jun"],
        [f"Service attitude ({int(lc.iloc[1]['Fail_Count'])} fails, {lc.iloc[1]['Pct_Of_Fails']:.1f}%)",
         "Live Chat",
         "Next-step macros on stuck CRs. Recalibrate attitude when the case cannot close.",
         "Chat Ops + QA Lead", "27 Jun"],
        [f"Service availability ({int(lc.iloc[2]['Fail_Count'])} fails, {abs(lc.iloc[2]['Impact_pp']):.2f} pp)",
         "Live Chat",
         "WFM and Chat Ops on queue, wrap-up, and chats left hanging. This is the Chat critical we already score.",
         "WFM + Chat Ops", "13 Jun"],
    ]
    data_table(s, MARGIN, BODY_TOP, cols, rows, header_h=0.40, row_h=0.70,
               size=8, bold_first=True)
    y = BODY_TOP + 0.40 + 5 * 0.70 + 0.16
    callout(s, MARGIN, y, CONTENT_W, 1.28,
            "This is defect correction, not a scoring change",
            f"These five attributes are already on the form. Adding Chat correct-information "
            f"as a critical is a separate scorecard change (Chat QA would read "
            f"{D['chat_qa_if_noproc0']:.2f}). It does not lift CSAT. Cases that followed "
            f"process and still did not close belong to process, not to the agent.",
            size_head=12, size_body=10)
    return s


def s_qa_fail_volume(prs, D):
    s = slide(prs, "QA analysis: lowest score vs fail volume",
              "A red score on 4 audits is not the same as 37 fails on one contact reason.",
              "03")
    text(s, MARGIN, BODY_TOP, 6.05, 0.24, "Lowest QA (rate, n ≥ 3)",
         size=10.5, bold=True, color=INK)
    cols_l = [("Contact reason", 3.35), ("QA", 0.70), ("n", 0.55), ("Start here?", 1.45)]
    rows_l = [
        ["Completed not received (market place)", "47.5", "4", "No. Too few audits."],
        ["Active order, already received", "65.8", "12", "Watch. Small n."],
        ["Completed not received (full service)", "68.2", "49", "Yes. Rate and volume."],
        ["Verbal aggression", "76.0", "5", "No. Too few audits."],
        ["Refund status and conditions", "76.4", "25", "Yes, on Phone."],
    ]
    data_table(s, MARGIN, BODY_TOP + 0.32, cols_l, rows_l, header_h=0.36, row_h=0.46,
               size=8, bold_first=True)

    text(s, 7.15, BODY_TOP, 5.70, 0.24, "Where the 518 attribute fails sit",
         size=10.5, bold=True, color=INK)
    cols_r = [("Contact reason", 3.20), ("Fails", 0.70), ("Share", 0.70), ("Below 85", 0.90)]
    rows_r = [
        ["Completed not received (full service)", "37", "7.1%", "14"],
        ["Cancel the order", "25", "4.8%", "5"],
        ["After-sales fraud review", "23", "4.4%", "—"],
        ["Cash order blocked (antifraud)", "21", "4.1%", "4"],
        ["Incomplete order", "21", "4.1%", "7"],
    ]
    data_table(s, 7.15, BODY_TOP + 0.32, cols_r, rows_r, header_h=0.36, row_h=0.46,
               size=8, bold_first=True)

    y = BODY_TOP + 0.32 + 0.36 + 5 * 0.46 + 0.22
    callout(s, MARGIN, y, CONTENT_W, 1.55,
            "Phone QA volume focus is one contact reason. Chat QA fails are spread.",
            "Completed-not-received full service is 26% of Phone audits below 85 (14 of 53) and "
            "the single largest attribute-fail pile (37 of 518). Marketplace at 47.5 QA is 4 audits. "
            "Do not start coaching there. Chat below-goal audits (80) have no CR above 8% of that pile. "
            "Chat QA work stays on attributes (greeting, attitude, availability), not on one CR.",
            size_head=13, size_body=11)
    return s


def s_csat_fail_volume(prs, D):
    s = slide(prs, "CSAT analysis: lowest score vs detractor volume",
              "15,488 unsatisfied surveys. Priority is share of that pile, not the ugliest percentage.",
              "04")
    text(s, MARGIN, BODY_TOP, 6.05, 0.24, "Worst CSAT (rate, min 100 surveys)",
         size=10.5, bold=True, color=INK)
    cols_l = [("Contact reason", 3.20), ("CSAT", 0.72), ("Surveys", 0.85), ("Share of pile", 1.20)]
    rows_l = [
        ["After-sales fraud review", "6.1%", "475", "2.9%"],
        ["Other (unmapped Business Type)", "26.5%", "558", "2.6%"],
        ["Membership program renewal", "28.6%", "248", "1.1%"],
        ["Membership program benefits", "43.1%", "109", "0.4%"],
        ["Placing an order information", "50.7%", "142", "0.5%"],
    ]
    data_table(s, MARGIN, BODY_TOP + 0.32, cols_l, rows_l, header_h=0.36, row_h=0.46,
               size=8, bold_first=True)

    text(s, 7.15, BODY_TOP, 5.70, 0.24, "Where the 15,488 unsatisfied sit",
         size=10.5, bold=True, color=INK)
    cols_r = [("Contact reason", 3.05), ("Unsat.", 0.78), ("Share", 0.70), ("CSAT", 0.72)]
    rows_r = [
        ["Order status / delay information", "3,189", "20.6%", "67.8%"],
        ["Disagrees with cancellation charge", "1,951", "12.6%", "67.4%"],
        ["Order status & delays", "1,800", "11.6%", "64.7%"],
        ["No longer wants the order", "1,229", "7.9%", "88.3%"],
        ["Refund status and conditions", "1,181", "7.6%", "67.0%"],
    ]
    data_table(s, 7.15, BODY_TOP + 0.32, cols_r, rows_r, header_h=0.36, row_h=0.46,
               size=8, bold_first=True)

    y = BODY_TOP + 0.32 + 0.36 + 5 * 0.46 + 0.22
    callout(s, MARGIN, y, CONTENT_W, 1.55,
            "CSAT focus is order status, cancellation charge and refunds. Not fraud.",
            "The two order-status reasons plus cancellation charge are 44.8% of every unsatisfied survey. "
            "Add refunds and the top five are 60.3%. After-sales fraud is 6.1% CSAT and only 2.9% of the pile. "
            "No longer wants the order is 88.3% (above goal) and still 7.9% of detractors: volume without a rate problem. "
            "Do not staff that CR. ETA and refund path are the volume unlock.",
            size_head=13, size_body=11)
    return s


def s_qa_cr(prs, D):
    s = slide(prs, "QA analysis by contact reason (CR Lv4)",
              "Blended ranking (Phone + Chat together). Official QA never mixes the two lists. At least 3 audits.", "03")
    picture(s, chart("bar_qa_by_cr.png"), MARGIN, BODY_TOP, 6.55, 3.70)

    x = 7.25
    text(s, x, BODY_TOP, 5.60, 0.24, "Lowest QA reasons (blended)", size=10.5,
         bold=True, color=INK)
    cols = [("Contact reason", 2.75), ("QA", 0.58), ("n", 0.45),
            ("Status", 1.82)]
    rows = []
    for _, r in D["qa_cr_all"].head(5).iterrows():
        stat = st(r["QA_Score"], 85)
        rows.append([_short(r["CR_Lv4"], 38), (f"{r['QA_Score']:.1f}", stat),
                     f"{int(r['N'])}", badge(stat)])
    data_table(s, x, BODY_TOP + 0.34, cols, rows, header_h=0.36, row_h=0.50,
               status_cols=(3,), heat_cols=(1,), align_right=(1, 2), size=7.8)

    y = BODY_TOP + 0.34 + 0.36 + 5 * 0.50 + 0.24
    text(s, x, y, 5.60, 0.24, "Why two numbers for the same reason", size=10.5, bold=True, color=INK)
    bullets(s, x, y + 0.34, 5.60, [
        "This slide is blended. The Phone slide and the Chat slide are not.",
        "Verbal aggression looks like 82.5 here (8 audits). Split: Chat 76.0 on 5, Phone 93.3 on 3.",
        "Undelivered full-service looks like 86.5 here (138 audits). On Phone alone it is 68.2 on 49.",
        "If you only read the blended number, a red Phone queue can look green.",
    ], size=9.5, gap=0.32)

    y2 = BODY_TOP + 3.88
    callout(s, MARGIN, y2, 6.55, 1.05,
            "Read Phone and Chat apart before you trust this blended ranking",
            "Take “order completed but not received — full service.” On Phone that is 68.2 QA "
            "from 49 audits, under the 85 goal. Blend in Chat and the same reason becomes 86.5 from "
            "138 audits, which looks fine. Chat did not fix Phone. It only diluted the average.",
            size_head=12, size_body=10)
    return s


def s_csat(prs, D):
    ph, lc = D["ch"].loc["Phone"], D["ch"].loc["Live Chat"]
    s = slide(prs, "CSAT analysis",
              f"Blended {D['summary']['csat']:.2f}% vs 85%  ·  "
              f"Phone {ph['CSAT_Score']:.2f}%  ·  Chat {lc['CSAT_Score']:.2f}%  ·  "
              f"{D['vols']['surveys']:,} surveys",
              "04")
    picture(s, chart("bar_stars.png"), MARGIN, BODY_TOP, 6.35, 2.48)
    picture(s, chart("bar_business_type.png"), MARGIN, BODY_TOP + 2.56, 6.35, 1.98)

    x = 7.10
    text(s, x, BODY_TOP, 5.75, 0.22, "Phone vs Chat vs blended", size=10.5,
         bold=True, color=INK)
    ch_cols = [("Channel", 1.70), ("CSAT", 0.78), ("Surveys", 1.12),
               ("vs 85", 0.85), ("Status", 1.28)]
    ch_rows = [
        ["Phone", csat_cell(ph["CSAT_Score"]), f"{D['csat_phone_n']:,}",
         f"{pp(ph['CSAT_Score'] - 85)} pp", badge(st(ph["CSAT_Score"], 85))],
        ["Live Chat", csat_cell(lc["CSAT_Score"]), f"{D['csat_chat_n']:,}",
         f"{pp(lc['CSAT_Score'] - 85)} pp", badge(st(lc["CSAT_Score"], 85))],
        ["Blended (official)", csat_cell(D["summary"]["csat"]),
         f"{D['vols']['surveys']:,}",
         f"{pp(D['summary']['csat'] - 85)} pp",
         badge(st(D["summary"]["csat"], 85))],
    ]
    data_table(s, x, BODY_TOP + 0.28, ch_cols, ch_rows, header_h=0.34, row_h=0.40,
               status_cols=(4,), heat_cols=(1,), align_right=(1, 2, 3),
               bold_first=True, size=8, header_size=8)

    y_cr = BODY_TOP + 0.28 + 0.34 + 3 * 0.40 + 0.16
    text(s, x, y_cr, 5.75, 0.22, "Contact reasons dragging CSAT down (blended)",
         size=10.5, bold=True, color=INK)
    cols = [("Contact reason (CR Lv4)", 2.55), ("Blended", 0.76), ("Phone", 0.72),
            ("Chat", 0.72), ("Surveys", 0.98)]
    rows = []
    for _, r in D["unsat_cr"].head(5).iterrows():
        rows.append([_short(r["CR_Lv4"], 28), csat_cell(r["CSAT_Score"]),
                     csat_cell(r["CSAT_Phone"]), csat_cell(r["CSAT_Chat"]),
                     f"{int(r['Feedback']):,}"])
    data_table(s, x, y_cr + 0.28, cols, rows, header_h=0.34, row_h=0.40,
               heat_cols=(1, 2, 3), align_right=(1, 2, 3, 4), size=7.6,
               header_size=8)

    y = y_cr + 0.28 + 0.34 + 5 * 0.40 + 0.14
    bullets(s, x, y, 5.75, [
        f"Phone is above the 85% goal. Chat is not. The official {D['summary']['csat']:.2f}% "
        f"is the blended number: Chat is what pulls it down.",
        f"Stars and Business Type on the left are also blended. "
        f"{D['star1_pct']:.1f}% of surveys are 1 star and {D['star5_pct']:.1f}% are 5 stars.",
    ], size=9, gap=0.30)
    return s


def s_voc(prs, D):
    s = slide(prs, "Voice of the customer",
              f"{D['voc_tagged']:,} classified comments from 1–3★ surveys", "04")
    picture(s, chart("bar_voc.png"), MARGIN, BODY_TOP, 6.35, 3.25)

    x = 7.10
    text(s, x, BODY_TOP, 5.75, 0.24, "What customers are telling us", size=10.5,
         bold=True, color=INK)
    text(s, x, BODY_TOP + 0.36, 5.75, 2.4, [
        [(f"{D['voc_resolution']:.1f}% of negative comments mention a missing refund or "
          f"an issue that was not resolved. ", {"bold": True, "color": INK}),
         (f"Agent attitude, which is heavily represented in QA, appears in only "
          f"{D['voc_attitude']:.1f}% of these comments.", {})],
        [("Customers are mainly describing unresolved issues rather than poor agent behaviour.",
          {})],
    ], size=10, color=GREY_CELL, line_spacing=1.32, space_after=8)

    y = BODY_TOP + 2.20
    text(s, x, y, 5.75, 0.24, "Who owns the dissatisfaction", size=10.5, bold=True,
         color=INK)
    cols = [("Owner the auditor tagged", 3.10), ("Cases", 0.85), ("Share", 0.85)]
    rows = [[r["Dissatisfaction_Owner"], f"{int(r['n'])}", f"{r['Pct']:.1f}%"]
            for _, r in D["diss_owner"].head(4).iterrows()]
    data_table(s, x, y + 0.34, cols, rows, header_h=0.36, row_h=0.44,
               align_right=(1, 2), size=8)

    y2 = BODY_TOP + 3.42
    callout(s, MARGIN, y2, 6.35, 1.50,
            "Does higher QA mean better customer outcomes?",
            f"QA versus CSAT on {D['cov']['qa_csat']} shared contact reasons: "
            f"r = {D['corr_qa_csat']['Pearson_r']:.3f}. R² = {D['corr_qa_csat']['R2']:.3f}. "
            f"QA explains {D['corr_qa_csat']['R2'] * 100:.1f}% of how CSAT varies. Almost none. "
            f"QA versus recontact: r = {D['corr_qa_rc']['Pearson_r']:.3f}. Same story. "
            f"Improving QA as we score it today would not directly improve CSAT.",
            size_head=11.5, size_body=9.5)
    return s


def s_recontact(prs, D):
    s = slide(prs, "Recontact analysis",
              f"{D['rc_rate']:.2f}% is global (all 12 channels) vs 5.44% goal  ·  "
              f"Human channels (Phone + Chat): {D['rc_audited']:.2f}%", "05")
    picture(s, chart("bar_rc_scope.png"), MARGIN, BODY_TOP, 6.20, 2.55)

    x = 6.95
    text(s, x, BODY_TOP, 5.90, 0.24, "Rate by channel: where customers contact us again",
         size=10.5, bold=True, color=INK)
    cols = [("Channel", 1.75), ("Contacts", 1.05), ("Repeats", 0.95), ("Rate", 0.75),
            ("Share of repeats", 1.40)]
    rows = []
    for _, r in D["rc_channels"].head(5).iterrows():
        rows.append([r["Channel"], f"{int(r['Contacts']):,}", f"{int(r['Repeats']):,}",
                     (f"{r['Rate %']:.2f}%", st(r["Rate %"], 5.44, lower_better=True)),
                     f"{r['Share of repeats %']:.1f}%"])
    data_table(s, x, BODY_TOP + 0.34, cols, rows, header_h=0.38, row_h=0.46,
               heat_cols=(3,), align_right=(1, 2, 3, 4), bold_first=True, size=8.2)

    y = BODY_TOP + 0.34 + 0.38 + 5 * 0.46 + 0.26
    text(s, x, y, 5.90, 0.24, "Two rates. Do not mix them.", size=10.5, bold=True, color=INK)
    bullets(s, x, y + 0.34, 5.90, [
        f"Self Help represents {D['dilution']['share']:.0f}% of contacts and has a "
        f"{D['dilution']['rate']:.2f}% recontact rate, which lowers the official business rate to {D['rc_rate']:.2f}%.",
        f"Human-assisted channels are much higher at {D['rc_audited']:.2f}%.",
        "The official metric is therefore close to goal, while the channels handled by agents remain well above it.",
    ], size=9.5, gap=0.32)

    y2 = BODY_TOP + 2.78
    callout(s, MARGIN, y2, 6.20, 2.10,
            "Self Help is heavily influencing the official recontact rate",
            f"The official recontact rate is {D['rc_rate']:.2f}%, but excluding Self Help raises it to "
            f"{D['rc_ex_sh']:.2f}%, and Phone + Live Chat alone reach {D['rc_audited']:.2f}%. "
            f"This is nearly three times the 5.44% goal. Live Chat generates "
            f"{D['rc_channels'].iloc[0]['Share of repeats %']:.1f}% of repeat contacts. "
            f"Track both figures: the official rate for business reporting and the human-channel rate for operational performance.",
            size_head=12, size_body=9.5)
    return s


def s_recontact_cr(prs, D):
    s = slide(prs, "Recontact by contact reason",
              "Where customers contact us again", "05")
    picture(s, chart("pareto_recontact.png"), MARGIN, BODY_TOP, 7.30, 3.70)

    x = 8.00
    text(s, x, BODY_TOP, 4.85, 0.24, "Highest recontact rates", size=10.5, bold=True,
         color=INK)
    cols = [("Contact reason", 1.68), ("Contacts", 0.78), ("Repeats", 0.72),
            ("Rate", 0.62), ("Status", 1.05)]
    rows = []
    for _, r in D["rc_top_rate"].iterrows():
        rows.append([_short(r["CR_Lv4"], 24), f"{int(r['Contacts']):,}",
                     f"{int(r['Recontacts']):,}",
                     (f"{r['Recontact_Rate']:.2f}%", "red"), badge("red")])
    data_table(s, x, BODY_TOP + 0.34, cols, rows, header_h=0.36, row_h=0.46,
               status_cols=(4,), heat_cols=(3,), align_right=(1, 2, 3), size=7.6)

    y = BODY_TOP + 0.34 + 0.36 + len(rows) * 0.46 + 0.08
    text(s, x, y, 4.85, 0.22,
         "Rate = repeats ÷ contacts of that reason. More repeats ≠ higher rate.",
         size=8, color=GREY_TEXT)
    y = y + 0.28
    text(s, x, y, 4.85, 0.24, "How this compares with QA and CSAT", size=10.5, bold=True,
         color=INK)
    bullets(s, x, y + 0.34, 4.85, [
        "The highest-recontact reasons are not the lowest QA reasons; several score between 93 and 98.",
        "However, they also have very low CSAT, especially order status (64.7%) and refunds (67.0%).",
        "This shows that high QA can coexist with low satisfaction and high recontact when the customer still needs to wait for a resolution.",
    ], size=9.5, gap=0.32)

    y2 = BODY_TOP + 3.88
    text(s, MARGIN, y2, 7.30, 0.24, "Where the volume sits", size=10.5, bold=True, color=INK)
    bullets(s, MARGIN, y2 + 0.34, 7.30, [
        f"Three contact reasons account for {D['rc_top3_share']:.1f}% of all repeat contacts.",
        f"“{_short(D['rc_cr'].iloc[0]['CR_Lv4'], 46)}” alone represents "
        f"{D['rc_cr'].iloc[0]['Pct']:.1f}% ({int(D['rc_cr'].iloc[0]['Recontacts']):,} repeats).",
    ], size=9.5, gap=0.32)
    return s


def s_people(prs, D):
    s = slide(prs, "Who needs attention: agent quartiles",
              f"{D['agents_ranked']} agents with at least 5 audits ranked on QA, "
              f"{D['csat_ranked']} with at least 20 surveys ranked on CSAT", "06")
    picture(s, chart("quartiles.png"), MARGIN, BODY_TOP, 6.95, 3.11)

    x = 7.55
    text(s, x, BODY_TOP, 5.30, 0.24, "The agents who sit outside the pack", size=10.5,
         bold=True, color=INK)
    cols = [("Agent", 1.05), ("QA", 0.60), ("Audits", 0.62), ("Team", 1.05),
            ("Coaching priority", 1.28)]
    rows = []
    for _, r in D["qa_gap"].head(5).iterrows():
        rows.append([r["Agent_ID"], (f"{r['QA_Score']:.1f}", st(r["QA_Score"], 85)),
                     f"{int(r['n'])}", r["Supervisor_ID"].replace("Supervisor ", "S"),
                     f"{r['Gap_Impact']:.0f}"])
    data_table(s, x, BODY_TOP + 0.34, cols, rows, header_h=0.36, row_h=0.46,
               heat_cols=(1,), align_right=(1, 2, 4), size=8, bold_first=True)
    footnote(s, FOOTER + "     ·     Coaching priority = (85 − QA) × audits, summed. Higher = coach this team/agent first. It weights a real sample, not a one-off.")

    y = BODY_TOP + 0.34 + 0.36 + 5 * 0.46 + 0.26
    text(s, x, y, 5.30, 0.24, "Where coaching should focus", size=10.5, bold=True, color=INK)
    bullets(s, x, y + 0.34, 5.30, [
        f"Focus on QA: the {D['qa_q4_n']} agents in Q4 "
        f"(mean {D['qa_q4_mean']:.1f}, range {D['qa_q4_lo']:.0f}–{D['qa_q4_hi']:.0f}).",
        f"Focus on CSAT: the {D['csat_q4_n']} agents in Q4 "
        f"(mean {D['csat_q4_mean']:.1f}%). That group is larger. Mostly different people.",
        f"{D['n_below_goal']} agents sit below the 85 QA goal. The top 5 carry "
        f"{D['gap_top5_share']:.0f}% of the total coaching priority.",
        f"'More than 1 year' is the only tenure below the QA goal ({D['tenure_worst_qa']:.2f}). "
        f"It is also the worst CSAT group ({D['tenure_worst_csat']:.1f}%).",
    ], size=9.5, gap=0.32)

    y2 = BODY_TOP + 3.28
    callout(s, MARGIN, y2, 6.95, 1.62,
            "QA shows limited differences between agents, while CSAT reveals a much wider performance gap.",
            f"Quartiles 1 to 3 sit at {D['qa_q1_mean']:.1f}, {D['qa_q2_mean']:.1f} and "
            f"{D['qa_q3_mean']:.1f}. Three quarters of the floor look the same on QA. "
            f"The same agents spread from {D['csat_q4_lo']:.1f}% to "
            f"{D['csat_q1_hi']:.1f}% on CSAT. Ranking agents by QA identifies very few meaningful differences. "
            f"CSAT reveals a much clearer group of low performers. A Chat score of 100 does not necessarily mean "
            f"the process was followed. {D['chat_n100_pct']:.0f}% of Chat audits reach the score ceiling.",
            size_head=12, size_body=9.5)
    return s


def s_supervisors(prs, D):
    s = slide(prs, "Who needs attention: supervisor view",
              f"{D['n_supervisors']} supervisors. Bubble size is audits. "
              "Teams with at least 20 audits.", "06")
    picture(s, chart("supervisor_scatter.png"), MARGIN, BODY_TOP, 6.55, 3.75)

    x = 7.25
    text(s, x, BODY_TOP, 5.60, 0.24, "Coaching queue: teams with the most agents below the QA goal",
         size=10.5, bold=True, color=INK)
    cols = [("Team", 1.05), ("Below QA 85", 1.42), ("Audits", 0.70),
            ("Worst QA", 1.05), ("Coaching priority", 1.28)]
    rows = []
    for _, r in D["coach_queue"].head(5).iterrows():
        rows.append([r["Supervisor_ID"].replace("Supervisor ", "S"),
                     f"{int(r['Agents'])}", f"{int(r['Audits'])}",
                     (f"{r['Worst_QA']:.1f}", "red"), f"{r['Gap_Impact']:.0f}"])
    data_table(s, x, BODY_TOP + 0.34, cols, rows, header_h=0.36, row_h=0.46,
               heat_cols=(3,), align_right=(1, 2, 3, 4), size=8, bold_first=True)

    y = BODY_TOP + 0.34 + 0.36 + 5 * 0.46 + 0.26
    text(s, x, y, 5.60, 0.24, "What the team view shows", size=10.5, bold=True, color=INK)
    bullets(s, x, y + 0.34, 5.60, [
        f"Five teams account for {D['coach_top5_agents']} of the {D['n_below_goal']} "
        f"agents below goal, so the coaching need is concentrated in a small number of teams rather than spread across the floor.",
        f"{D['worst_qa_sup']} is the only team below the QA goal "
        f"({D['worst_qa_sup_score']:.1f} on {D['worst_qa_sup_n']} audits).",
        f"{D['worst_csat_sup']} passes QA at {D['worst_csat_sup_qa']:.1f}. CSAT comes back at "
        f"{D['worst_csat_sup_csat']:.1f}% on {D['worst_csat_sup_n']:,} surveys. Worst of any team.",
        f"{D['mix_sup']} has {D['mix_pct']:.0f}% of its ranked agents in Q4. This suggests a team-level performance pattern rather than a single-agent issue.",
    ], size=9.5, gap=0.38)

    y2 = BODY_TOP + 3.86
    callout(s, MARGIN, y2, 6.55, 1.42,
            f"{D['worst_agent_csat']} is large enough to name on their own",
            f"{D['worst_agent_csat']} has CSAT of {D['worst_agent_csat_score']:.1f}% on "
            f"{D['worst_agent_csat_n']:,} surveys. {D['worst_agent_unsat']:,} of those customers were unsatisfied "
            f"(1–3 stars). That is {D['worst_agent_share']:.1f}% of all unsatisfied surveys in the month. "
            f"No QA audit flagged this agent.",
            size_head=11.5, size_body=9.5)
    return s


def s_combined(prs, D):
    s = slide(prs, "Combined analysis",
              "Contact reasons that miss on more than one metric (blended Phone + Chat)", "07")
    cols = [("Contact reason (CR Lv4)", 3.15), ("QA", 0.62), ("Audits", 0.62),
            ("CSAT", 0.72), ("Recontact", 0.92), ("Repeat volume", 1.00),
            ("Surveys", 0.78), ("Pattern", 2.15), ("Priority", 2.17)]
    rows = []
    for _, r in D["combined"].head(6).iterrows():
        has_csat = r["CSAT_Score"] == r["CSAT_Score"]
        csat = ((f"{r['CSAT_Score']:.1f}%", st(r["CSAT_Score"], 85)) if has_csat
                else ("n/a", None))
        surveys = f"{int(r['Feedback']):,}" if r["Feedback"] == r["Feedback"] else "n/a"
        top = r["Impact_Score"] > 2000
        rows.append([_short(r["CR_Lv4"], 42),
                     (f"{r['QA_Score']:.1f}", st(r["QA_Score"], 85)),
                     f"{int(r['QA_N']):,}",
                     csat,
                     (f"{r['Recontact_Rate']:.2f}%",
                      st(r["Recontact_Rate"], 5.44, lower_better=True)),
                     f"{int(r['Recontacts']):,}", surveys, r["Pattern"],
                     ("Act this quarter" if top else "Monitor", "red" if top else "amber")])
    data_table(s, MARGIN, BODY_TOP, cols, rows, header_h=0.42, row_h=0.50,
               status_cols=(8,), heat_cols=(1, 3, 4), align_right=(1, 2, 3, 4, 5, 6),
               size=8, bold_first=True)

    y = BODY_TOP + 0.42 + 6 * 0.50 + 0.10
    text(s, MARGIN, y, CONTENT_W, 0.22,
         "QA and CSAT columns are blended Phone + Chat. Refund status QA 90.6 is n=70 "
         "(Phone 76.4 n=25 + Chat 98.4 n=45): same contact reason, two casings in the source. "
         "Official overall QA still keeps the two attribute lists unmixed.",
         size=8, color=GREY_TEXT)
    y = y + 0.28
    callout(s, MARGIN, y, 7.55, 1.55,
            "The same pattern is visible in a single contact reason",
            f"“Order status & delays” scores {D['os_qa']:.1f} on QA, but only "
            f"{D['os_csat']:.1f}% on CSAT and has a {D['os_rc']:.2f}% recontact rate. "
            f"It generated {D['os_repeats']:,} repeat contacts during the month. "
            f"Agents follow the process, but they cannot see or change the courier ETA. "
            f"The interaction is compliant, yet the customer still has no resolution.",
            size_head=12, size_body=9.5)

    x2 = 8.30
    text(s, x2, y, 4.55, 0.24, "Who the auditor tagged as owner", size=10.5, bold=True,
         color=INK)
    bullets(s, x2, y + 0.34, 4.55, [
        f"{D['diss_process_pct']:.1f}% of tagged dissatisfaction is attributed to CX Process, "
        f"compared with {D['diss_people_pct']:.1f}% to the agent.",
        f"{D['notres_pct']:.1f}% of cases are marked “not resolution-based.”",
        f"Only {D['adherence_pct']:.1f}% are identified as process failures, and Chat QA may understate these because {D['chat_n100_pct']:.0f}% of Chat audits still score 100.",
    ], size=9.5, gap=0.36)
    return s


def _hier_rows(parents, children, n_parent=4, n_child=1):
    """CR Lv4 row then up to n_child SUB_CR rows whose parent matches."""
    rows = []
    used = set()
    for p in parents[:n_parent]:
        rows.append([
            _short(p["name"], 38),
            f"{p['pct_res']:.0f}%",
            f"{p['csat']:.1f}%",
            f"{p['n']:,}",
            f"{p['fb']:,}",
            "CR Lv4",
        ])
        n_added = 0
        key = str(p["name"]).strip().casefold()
        for ch in children:
            if n_added >= n_child:
                break
            if str(ch["parent"]).strip().casefold() != key:
                continue
            mark = (ch["name"], ch["parent"])
            if mark in used:
                continue
            used.add(mark)
            rows.append([
                "    " + _short(ch["name"], 34),
                f"{ch['pct_res']:.0f}%",
                f"{ch['csat']:.1f}%",
                f"{ch['n']:,}",
                f"{ch['fb']:,}",
                "SUB_CR",
            ])
            n_added += 1
    return rows


def s_resolution_csat(prs, D):
    R = D["res"]
    s = slide(prs, "Where we can close the case, CSAT is higher",
              "By contact reason and its sub-reasons. Same green / amber / red as the rest of the deck.",
              "07")
    r2 = R["cr_r2"]
    r2_txt = f"{r2:.2f}" if r2 is not None else "—"
    callout(s, MARGIN, BODY_TOP, CONTENT_W, 0.64,
            "Look at the type of issue, not only the agent.",
            f"Orange is the contact reason. Grey is the sub-reason. "
            f"Across {R['cr_n']} contact reasons (at least 3 audits and 20 surveys), "
            f"closure rate has a strong relationship with CSAT "
            f"(r = +{R['cr_r']:.2f}; R² = {r2_txt}). By comparison, QA and CSAT have almost no "
            f"relationship (R² = {D['corr_qa_csat']['R2']:.3f}).",
            size_head=12, size_body=9.2)

    picture(s, chart("cr_subcr_tree.png"), MARGIN, BODY_TOP + 0.70, CONTENT_W, 3.12)

    def heat_parents(nodes):
        rows = []
        for p in nodes[:4]:
            rows.append([
                _short(p["name"], 28),
                (f"{p['pct_res']:.0f}%", st_res(p["pct_res"])),
                (f"{p['csat']:.1f}%", st(p["csat"], 85)),
                f"{p['n']:,}",
                f"{p['fb']:,}",
            ])
        return rows

    y = BODY_TOP + 3.88
    cols = [("Contact reason (Lv4)", 2.70), ("Resolved", 0.75), ("CSAT", 0.70),
            ("Audits", 0.68), ("Surveys", 0.72)]
    text(s, MARGIN, y, 5.55, 0.18, "Reasons with higher closure rates", size=10, bold=True, color=INK)
    data_table(s, MARGIN, y + 0.20, cols, heat_parents(R["cr_a"]),
               header_h=0.26, row_h=0.26, heat_cols=(1, 2), align_right=(1, 2, 3, 4),
               size=7.6, bold_first=True)

    x2 = 7.15
    text(s, x2, y, 5.70, 0.18, "Reasons with lower closure rates", size=10, bold=True, color=INK)
    data_table(s, x2, y + 0.20, cols, heat_parents(R["cr_b"]),
               header_h=0.26, row_h=0.26, heat_cols=(1, 2), align_right=(1, 2, 3, 4),
               size=7.6, bold_first=True)

    y2 = 6.68
    bits = []
    fd = R.get("fraud_csat") or {}
    if fd.get("csat") is not None:
        bits.append(
            f"After-sales fraud CSAT {fd['csat']:.1f}% is {fd['sat']:,} satisfied / "
            f"{fd['fb']:,} surveys ({fd['ones']:,} ones). That is real. Not a small-sample fluke."
        )
    if R["cr_c"]:
        c0 = R["cr_c"][0]
        bits.append(
            f"One exception remains: “{_short(c0['name'], 36)}” has a {c0['pct_res']:.0f}% closure rate "
            f"but only {c0['csat']:.1f}% CSAT on {c0['fb']:,} surveys, showing that closure alone "
            f"does not explain every customer outcome."
        )
    if bits:
        text(s, MARGIN, y2, CONTENT_W, 0.32, "  ".join(bits), size=8.5, color=GREY_TEXT)
    n_all = fd.get("n_all")
    n_ass = fd.get("n_assessed")
    n_ab = fd.get("n_abandoned")
    if n_all and n_ass and n_all != n_ass:
        footnote(
            s,
            f"{FOOTER}     ·     Audits on this slide = Resolved or Not resolved. "
            f"After-sales fraud: {n_ass} assessed, {n_ab} Abandoned, {n_all} in Combined analysis.",
        )
    return s


def s_five_whys(prs, D):
    R = D["res"]
    s = slide(prs, "5 whys: why we could not close, and what closing actually was",
              f"What the auditor wrote in the 5-whys  ·  {R['n_not_resolved']:,} not closed  ·  "
              f"{R['n_resolved']:,} closed  ·  not a KPI",
              "07")

    nr = R["nr_themes"]
    rs = R["res_themes"]
    nr_mix = R.get("csat_nr_crmix") or {}
    res_mix = R.get("csat_resolved_crmix") or {}
    nr_csat = nr_mix.get("csat")
    res_csat = res_mix.get("csat")
    nr_head = [
        [(f"Cases that could not be closed  ·  n = {R['n_not_resolved']:,}  ·  "
          f"{R['n_followed_nr']:,} still followed process", {"bold": True, "size": 11})],
        [(f"CSAT of these contact reasons is {nr_csat:.1f}%. Not those tickets. Audits and surveys do not share a ticket ID."
          if nr_csat is not None else
          "No CSAT join for this group at ticket level.",
          {"bold": False, "size": 9, "color": GREY_TEXT})],
    ]
    text(s, MARGIN, BODY_TOP, 6.05, 0.44, nr_head, size=11, color=INK)
    cols = [("Why it did not close", 3.15), ("Audits", 0.85), ("Share", 0.80),
            ("Of those, followed process", 1.25)]
    nr_order = [
        ("policy_blocked", "Policy blocked refund / close"),
        ("tools_system", "No tool — must escalate"),
        ("other", "Other / unclear"),
        ("no_analysis", "No analysis (“No aplica”)"),
        ("fraud_review", "Fraud named in the text"),
        ("courier_store", "Courier / store / restaurant"),
        ("placeholder", "Model: no low CSAT to analyse"),
        ("delay_eta", "Delay / ETA (undercounted)"),
        ("agent_miss", "Agent missed the process"),
    ]
    tot_nr = max(R["n_not_resolved"], 1)
    fol = R["nr_followed_themes"]
    rows = []
    for key, label in nr_order:
        n = int(nr.get(key, 0))
        if n == 0:
            continue
        rows.append([label, f"{n:,}", f"{n / tot_nr * 100:.0f}%",
                     f"{int(fol.get(key, 0)):,}"])
    data_table(s, MARGIN, BODY_TOP + 0.48, cols, rows,
               header_h=0.30, row_h=0.29, align_right=(1, 2, 3), size=8)

    res_head = [
        [(f"Cases that were closed  ·  n = {R['n_resolved']:,}  ·  how they were resolved",
          {"bold": True, "size": 11})],
        [(f"CSAT of these contact reasons is {res_csat:.1f}%. Not those tickets. Audits and surveys do not share a ticket ID."
          if res_csat is not None else
          "No CSAT join for this group at ticket level.",
          {"bold": False, "size": 9, "color": GREY_TEXT})],
    ]
    text(s, 7.55, BODY_TOP, 5.30, 0.44, res_head, size=11, color=INK)
    res_order = [
        ("refund_confirmed", "Confirmed a refund or compensation"),
        ("explained_process", "Explained / confirmed the process"),
        ("tools_or_report", "Used a tool or filed a report"),
        ("other", "Other / unclear"),
        ("no_analysis", "No analysis (“No aplica”)"),
        ("cancelled", "Cancellation processed"),
        ("placeholder", "Model: no low CSAT to analyse"),
    ]
    tot_rs = max(R["n_resolved"], 1)
    rrows = []
    for key, label in res_order:
        n = int(rs.get(key, 0))
        if n == 0:
            continue
        rrows.append([label, f"{n:,}", f"{n / tot_rs * 100:.0f}%"])
    data_table(s, 7.55, BODY_TOP + 0.48,
               [("What closing was", 3.20), ("Audits", 0.85), ("Share", 0.80)],
               rrows, header_h=0.30, row_h=0.29, align_right=(1, 2), size=8)

    y = 5.48
    qp = R.get("nr_quote_policy") or {}
    qt = R.get("nr_quote_tools") or {}
    qr = R.get("res_quote_refund") or {}
    callout(s, MARGIN, y, 6.05, 1.35,
            "The main blockers are policy and tools, not agent greetings.",
            f"Policy: {qp.get('text', '')[:210]} "
            f"Tools: {qt.get('text', '')[:160]}",
            size_head=11, size_body=8.5)
    callout(s, 7.55, y, 5.30, 1.35,
            "When cases are closed, the resolution usually involves a refund, an explanation, or a tool",
            f"{(qr.get('text') or R.get('res_quote_explained', {}).get('text') or '')[:320]}",
            size_head=11, size_body=8.5)
    return s


def s_fishbone(prs, D):
    s = slide(prs, "Why customers contact us again even when QA is green",
              "Fishbone. Six buckets. Every line has a number.", "07")
    picture(s, chart("fishbone.png"), MARGIN, BODY_TOP - 0.06, CONTENT_W, 4.62)
    callout(s, MARGIN, BODY_TOP + 4.66, CONTENT_W, 1.05,
            "The key takeaway",
            f"The scorecard measures how the interaction was handled, while CSAT reflects the customer outcome. "
            f"That is why QA is {D['summary']['qa_score']:.2f} while blended CSAT is {D['summary']['csat']:.2f}%, "
            f"with almost no relationship between them (R² = {D['corr_qa_csat']['R2']:.3f}). "
            f"Of {D['res']['n_not_resolved']:,} cases marked as not closed, "
            f"{D['res']['n_followed_nr']:,} still followed process. The main barriers identified are policy and tools. "
            f"The priority should therefore be fixing the contact reason, not only coaching agent behaviour.",
            size_head=11.5, size_body=9.5)
    return s


def s_control_plan(prs, D):
    s = slide(prs, "What we will do next",
              "Connect QA with the customer outcome", "07")
    picture(s, chart("flowchart.png"), MARGIN, BODY_TOP, CONTENT_W, 2.95)

    y = BODY_TOP + 3.06
    text(s, MARGIN, y, 6.20, 0.24, "What changes", size=10.5, bold=True, color=INK)
    bullets(s, MARGIN, y + 0.34, 6.20, [
        f"Report auditor closure next to QA, by channel and contact reason (not FCR). {close_ten_line(D)} Green if 70%+ closure and 85%+ CSAT.",
        "Assign each improvement to the relevant contact reason. The Dissatisfaction_Owner field only appears in about 4% of audits, so it should not be used as the primary ownership map.",
        "This month: correct Pareto defects we already score (Phone time management and complete information; Chat greeting, attitude, availability). That is operational, not a form change.",
        f"Separately, add correct information as a Chat critical so the scorecard stops inflating (Chat QA would read {D['chat_qa_if_noproc0']:.2f}). That does not lift CSAT. Track official CSAT on targeted contact reasons.",
    ], size=9.5, gap=0.34)

    text(s, 7.10, y, 5.75, 0.24, "How we will know it worked", size=10.5, bold=True,
         color=INK)
    cols = [("Measure", 2.20), ("Today", 1.05), ("Target", 1.05), ("Horizon", 1.45)]
    r2_res = D["res"]["cr_r2"]
    rows = [
        ["QA vs CSAT (R²)", (f"R² {D['corr_qa_csat']['R2']:.2f}", "red"),
         "R² 0.25 or above", "2 quarters"],
        ["Close-rate vs CSAT (R²)", (f"R² {r2_res:.2f}" if r2_res is not None else "—", "green"),
         "Keep 0.50 or above", "ongoing"],
        ["CSAT", (f"{D['summary']['csat']:.2f}%", "red"), "85.0%", "2 quarters"],
        ["Recontact (human: Phone + Chat)", (f"{D['rc_audited']:.2f}%", "red"), "10.0%", "1 quarter"],
        ["Auditor close rate Phone / Chat",
         (f"{D['close']['Phone']['close_pct']:.1f}% / {D['close']['Live Chat']['close_pct']:.1f}%", "red"),
         "90% / 75%", "1 quarter"],
    ]
    data_table(s, 7.10, y + 0.34, cols, rows, header_h=0.36, row_h=0.40,
               heat_cols=(1,), align_right=(1, 2), size=8.2, bold_first=True)
    return s


def _chat_rc(D):
    row = D["rc_channels"].iloc[0]
    return float(row["Rate %"]), float(row["Share of repeats %"])


def _phone_undelivered_fs(D):
    q = D["qa_cr_phone"]
    hit = q[q["CR_Lv4"].astype(str).str.contains("full service", case=False, na=False)]
    r = hit.iloc[0] if len(hit) else q.iloc[3]
    return float(r["QA_Score"]), int(r["N"])


def _phone_marketplace_cr(D):
    r = D["qa_cr_phone"].iloc[0]
    return float(r["QA_Score"]), int(r["N"])


def actions_bt(D):
    """Business-Type actions. `kpis` drives the coverage check, nothing else."""
    bt = D["bt"].set_index("Business_Type")
    os_rc = D["os_rc"]
    fs_qa, fs_n = _phone_undelivered_fs(D)
    mp_qa, mp_n = _phone_marketplace_cr(D)
    return [
        {"scope": "Food",
         "evidence": f"CSAT {bt.loc['Food', 'CSAT_Score']:.2f}% on "
                     f"{int(bt.loc['Food', 'Feedback']):,} surveys; order status repeats "
                     f"at {os_rc:.2f}%",
         "action": "Add a live courier ETA to the agent console so customers receive a verifiable status.",
         "short": "Live courier ETA in the agent console",
         "why": (f"Order status & delays: QA {D['os_qa']:.1f}, CSAT {D['os_csat']:.1f}%, "
                 f"recontact {os_rc:.2f}%, {D['os_repeats']:,} repeats. "
                 f"This is the Chat 6-of-10 close gap, not a staffing gap."),
         "kind": "Outcome",
         "who": "CX Ops + Product", "when": "30 Jun", "severity": "Critical",
         "kpis": ("CSAT", "Recontact")},
        {"scope": "Full Service",
         "evidence": f"CSAT {bt.loc['Full Service', 'CSAT_Score']:.2f}%, the lowest of the "
                     f"volume lines; undelivered orders audit at {fs_qa:.1f} on {fs_n} audits",
         "action": "Give Phone agents limited same-call refund authority for eligible undelivered orders",
         "short": "Same-call refund authority for undelivered orders",
         "why": (f"Phone undelivered full-service QA is {fs_qa:.1f} (n={fs_n}). "
                 f"Agents wait on a refund they cannot approve. Phone already closes about 9 of 10 assessed; this attacks the remaining 1 and the Chat refund pile."),
         "kind": "Outcome",
         "who": "CX Ops + Finance", "when": "15 Jul", "severity": "Critical",
         "kpis": ("QA", "CSAT")},
        {"scope": "Market Place",
         "evidence": f"CSAT {bt.loc['Market Place', 'CSAT_Score']:.2f}% on "
                     f"{int(bt.loc['Market Place', 'Feedback']):,} surveys; worst Phone QA reason "
                     f"({mp_qa:.1f}) but on only {mp_n} audits",
         "action": "Define a clear merchant-escalation SLA and script for “completed but not "
                   "received.” Low confidence: run 20+ audits on this reason before "
                   "committing merchant-side resources",
         "short": "Merchant SLA for completed-not-received (validate n first)",
         "why": f"Phone QA {mp_qa:.1f} on n={mp_n}. Too few audits to treat as a proven process yet.",
         "kind": "Outcome",
         "who": "Merchant Ops", "when": "15 Jul", "severity": "High",
         "kpis": ("QA", "CSAT")},
        {"scope": "All Business Types",
         "evidence": f"Refund or compensation not received is {D['voc_top_pct']:.1f}% of "
                     f"negative verbatims",
         "action": "Send an automatic notification whenever refund status changes",
         "short": "Automatic refund-status notifications",
         "why": f"{D['voc_resolution']:.1f}% of negative comments are unresolved refunds or unsolved issues, not agent attitude ({D['voc_attitude']:.1f}%).",
         "kind": "Outcome",
         "who": "Product + CX Ops", "when": "31 Jul", "severity": "High",
         "kpis": ("CSAT", "Recontact")},
        {"scope": "Data quality",
         "evidence": f"'Other' Business Type holds {int(bt.loc['Other', 'Feedback']):,} "
                     f"surveys at {bt.loc['Other', 'CSAT_Score']:.1f}% CSAT",
         "action": "Fix the CR-to-Business-Type mapping so detractors are correctly classified",
         "short": "Fix CR to Business Type mapping",
         "why": f"'Other' CSAT is {bt.loc['Other', 'CSAT_Score']:.1f}% on {int(bt.loc['Other', 'Feedback']):,} surveys. That mix hides real detractors.",
         "kind": "Data",
         "who": "CX Analytics", "when": "20 Jun", "severity": "Moderate",
         "kpis": ("CSAT",)},
    ]


def actions_channel(D):
    chat_rate, chat_share = _chat_rc(D)
    r2 = D["res"]["cr_r2"]
    r2_txt = f"{r2:.2f}" if r2 is not None else "—"
    return [
        {"scope": "Phone",
         "action": "Increase Phone QA coverage to at least 30%",
         "short": "Increase Phone QA coverage to 30%",
         "evidence": f"Phone is {D['ch'].loc['Phone', 'QA_Share']:.1f}% of audits and the "
                     f"only channel below goal",
         "why": f"Phone QA {D['ch'].loc['Phone', 'QA_Score']:.2f} on only {D['ch'].loc['Phone', 'QA_Share']:.1f}% of audits. The blend is Chat-weighted.",
         "kind": "Measure",
         "who": "QA Lead", "when": "13 Jun", "severity": "Critical", "kpis": ("QA",)},
        {"scope": "Phone",
         "action": "Coach Time Management: system-check script at start; escalate if no data in 2 minutes",
         "short": "Coach Phone Time Management",
         "evidence": f"{D['attr_phone'].iloc[0]['Pct_Of_Fails']:.1f}% of Phone defects, "
                     f"{int(D['attr_phone'].iloc[0]['Fail_Count'])} fails",
         "why": f"Time management is {D['attr_phone'].iloc[0]['Pct_Of_Fails']:.1f}% of Phone defects ({int(D['attr_phone'].iloc[0]['Fail_Count'])} fails).",
         "kind": "Coach",
         "who": "Supervisors", "when": "27 Jun", "severity": "High", "kpis": ("QA",)},
        {"scope": "People",
         "action": f"Run weekly coaching for the {D['qa_q4_n']} QA-Q4 agents, starting with "
                   f"the five teams with the highest concentration",
         "short": f"Weekly coaching for {D['qa_q4_n']} QA-Q4 agents",
         "evidence": f"{D['n_below_goal']} agents below the QA goal; "
                     f"{D['coach_queue'].iloc[0]['Supervisor_ID']} alone carries three",
         "why": f"{D['qa_q4_n']} agents in QA Q4; {D['n_below_goal']} below goal. This lifts QA, not CSAT.",
         "kind": "Coach",
         "who": "Supervisors + QA Lead", "when": "20 Jun", "severity": "High",
         "kpis": ("QA",)},
        {"scope": "Live Chat",
         "action": "Add a Chat critical attribute for correct information, aligned with Phone",
         "short": "Chat critical: correct information",
         "evidence": f"{D['chat_noproc_n']} chats did not follow process; "
                     f"{D['chat_noproc_n100']} still score 100. {chat_qa_pair(D)}",
         "why": f"{D['chat_noproc_n100']} of {D['chat_noproc_n']} process-fail chats still score 100. Proposed Chat QA {D['chat_qa_if_noproc0']:.2f}. Measurement only — does not lift CSAT.",
         "kind": "Measure",
         "who": "QA Lead", "when": "30 Jun", "severity": "Critical", "kpis": ("QA",)},
        {"scope": "Live Chat",
         "action": (f"Do not add Chat headcount. Chat closes about 6 of 10 assessed "
                    f"({D['close']['Live Chat']['close_pct']:.1f}%); "
                    f"{D['close']['Live Chat']['unres_process']} of "
                    f"{D['close']['Live Chat']['not_resolved']} unresolved chats followed process."),
         "short": "Do not add Chat headcount (6 of 10 close; process-followed gap)",
         "evidence": (f"Abandon {D['close']['Live Chat']['abandon_pct']:.1f}% vs Phone "
                      f"{D['close']['Phone']['abandon_pct']:.1f}%. Chat is {chat_share:.1f}% of repeats."),
         "why": (f"Phone closes about 9 of 10 assessed ({D['close']['Phone']['close_pct']:.1f}%). "
                 f"Staffing Chat will not close cases the process already blocked."),
         "kind": "Constraint",
         "who": "CX Ops", "when": "15 Jul", "severity": "Critical", "kpis": ("Recontact",)},
        {"scope": "QA governance",
         "action": (f"Report auditor closure weekly by channel (Phone "
                    f"{D['close']['Phone']['close_pct']:.1f}%, Chat "
                    f"{D['close']['Live Chat']['close_pct']:.1f}%) and assign an owner to every unclosed case. Not FCR."),
         "short": "Weekly closure by channel + owner on unclosed cases",
         "evidence": (f"The field is already on the form. "
                      f"{D['close']['Live Chat']['unres_process']} Chat and "
                      f"{D['close']['Phone']['unres_process']} Phone unresolved cases followed process."),
         "why": f"{D['unres_proc_n']:,} followed process and did not close (QA {D['unres_proc_score']:.2f}). Closure vs CSAT R² {r2_txt}; QA vs CSAT R² {D['corr_qa_csat']['R2']:.3f}.",
         "kind": "Measure",
         "who": "QA Lead + CX Head", "when": "31 Jul", "severity": "Critical",
         "kpis": ("QA", "CSAT")},
        {"scope": "QA governance",
         "action": "Report QA and recontact weekly by channel, including Phone+Chat vs the official global rate",
         "short": "Weekly QA and recontact by channel (human vs global)",
         "evidence": "Blended figures hid a 13-point channel gap and a 10-point recontact gap",
         "why": f"Official recontact {D['rc_rate']:.2f}% vs human {D['rc_audited']:.2f}%. Phone QA {D['ch'].loc['Phone', 'QA_Score']:.2f} vs Chat {D['ch'].loc['Live Chat', 'QA_Score']:.2f}. Do not mix them.",
         "kind": "Measure",
         "who": "CX Analytics", "when": "13 Jun", "severity": "Moderate",
         "kpis": ("QA", "Recontact")},
    ]


SEVERITY = {"Critical": "red", "High": "amber", "Moderate": "green"}


def s_actions_bt(prs, D):
    s = slide(prs, "Action plan by Business Type",
              "Delivery is the only line of business in the data. Plans are cut by Business Type.",
              "08")
    cols = [("Business Type", 1.50), ("Evidence", 3.45), ("What must change", 3.30),
            ("Who", 1.60), ("When", 0.93), ("Problem severity", 1.55)]
    rows = [[a["scope"], a["evidence"], a["action"], a["who"], a["when"],
             (a["severity"], SEVERITY[a["severity"]])] for a in actions_bt(D)]
    data_table(s, MARGIN, BODY_TOP, cols, rows, header_h=0.42, row_h=0.86,
               status_cols=(5,), size=8, bold_first=True)

    y = BODY_TOP + 0.42 + 5 * 0.86 + 0.26
    text(s, MARGIN, y, CONTENT_W, 0.24,
         "Severity rates how large the gap is. None of these actions has started yet.", size=9, color=GREY_TEXT)
    text(s, MARGIN, y + 0.28, CONTENT_W, 0.24,
         [[("Market Place. ", {"bold": True, "color": INK}),
           (f"That case rests on a contact reason with only {_phone_marketplace_cr(D)[1]} audits, the same "
            "low-volume reason flagged as unreliable in the Phone QA section. Validate with "
            "more audits before committing resources.", {})]],
         size=9, color=GREY_CELL)

    footnote(s, FOOTER + "     ·     Owners are role-level; names to be confirmed with CX "
             "Leadership at the weekly review.")
    return s


def coverage_check(s, x, y, w, h, actions, current):
    """Three lines: does each KPI have actions and a named accountable owner?"""
    panel(s, x, y, w, h)
    text(s, x + 0.24, y + 0.16, w - 0.48, 0.24,
         "Tagged actions — one action can serve two KPIs. Unique list is on the matrix.",
         size=8.5, bold=True, color=INK)

    cw = [1.42, 1.08, 1.02, 1.65]
    ry = y + 0.50
    for label, (value, status), count, owner in [
        (k, current[k], sum(1 for a in actions if k in a["kpis"]), o)
        for k, o in (("QA", "QA Lead"), ("CSAT", "CX Ops"), ("Recontact", "CX Ops"))
    ]:
        color, tint = STATUS[status]
        cx = x + 0.24
        rect(s, cx, ry + 0.055, 0.075, 0.155, fill=color)
        text(s, cx + 0.16, ry - 0.02, cw[0], 0.26, label, size=9, bold=True, color=INK,
             anchor=MSO_ANCHOR.MIDDLE)
        cx += cw[0]
        text(s, cx, ry - 0.02, cw[1], 0.26, value, size=9, bold=True, color=color,
             anchor=MSO_ANCHOR.MIDDLE)
        cx += cw[1]
        text(s, cx, ry - 0.02, cw[2], 0.26, f"{count} actions", size=9, color=GREY_CELL,
             anchor=MSO_ANCHOR.MIDDLE)
        cx += cw[2]
        text(s, cx, ry - 0.02, cw[3], 0.26, owner, size=9, color=GREY_CELL,
             anchor=MSO_ANCHOR.MIDDLE)
        ry += 0.27


def s_actions_channel(prs, D):
    s = slide(prs, "Action plan by channel, people and governance",
              "Owner, deadline and the severity of the problem behind each action", "08")
    cols = [("Scope", 1.30), ("What must change", 3.90), ("Why now", 3.20),
            ("Who", 1.50), ("When", 0.88), ("Problem severity", 1.55)]
    acts = actions_channel(D)
    rows = [[a["scope"], a["action"], a["evidence"], a["who"], a["when"],
             (a["severity"], SEVERITY[a["severity"]])] for a in acts]
    data_table(s, MARGIN, BODY_TOP, cols, rows, header_h=0.40, row_h=0.50,
               status_cols=(5,), size=8, bold_first=True)

    y = BODY_TOP + 0.40 + len(rows) * 0.50 + 0.30
    all_acts = actions_bt(D) + acts
    current = {
        "QA": (f"{D['summary']['qa_score']:.2f}", st(D["summary"]["qa_score"], 85)),
        "CSAT": (f"{D['summary']['csat']:.2f}%", st(D["summary"]["csat"], 85)),
        "Recontact": (f"{D['rc_rate']:.2f}%", st(D["rc_rate"], 5.44, lower_better=True)),
    }
    coverage_check(s, MARGIN, y, 5.55, 1.32, all_acts, current)

    callout(s, MARGIN + 5.83, y, CONTENT_W - 5.83, 1.32,
            "Fix what we measure vs what the customer gets",
            "Phone closes about 9 of 10 assessed contacts; Chat about 6 of 10. "
            "Do not staff Chat for that gap: most unresolved chats followed process. "
            "ETA and refunds change the outcome. Pareto coaching and the Chat critical change the scorecard. Do not mix those.",
            size_head=11, size_body=9)
    return s


def s_action_matrix(prs, D):
    """One row per unique action. KPI marks + why. Stops the 8/7/4 double-count confusion."""
    s = slide(prs, "Action matrix by KPI",
              "Each action once. Outcome changes the customer result. Measure changes the scorecard.",
              "08")
    acts = actions_bt(D) + actions_channel(D)
    cols = [("What we will do", 3.50), ("Why", 4.60), ("Type", 1.05),
            ("QA", 0.55), ("CSAT", 0.70), ("RC", 0.55), ("Who", 1.40)]
    rows = []
    for a in acts:
        k = set(a["kpis"])
        rows.append([
            a["short"],
            a["why"],
            a["kind"],
            ("Yes", "green") if "QA" in k else ("—", None),
            ("Yes", "green") if "CSAT" in k else ("—", None),
            ("Yes", "green") if "Recontact" in k else ("—", None),
            a["who"],
        ])
    data_table(s, MARGIN, BODY_TOP, cols, rows, header_h=0.32, row_h=0.38,
               heat_cols=(3, 4, 5), size=7.2, header_size=8, bold_first=False)
    y = BODY_TOP + 0.32 + len(rows) * 0.38 + 0.10
    n = len(acts)
    n_qa = sum(1 for a in acts if "QA" in a["kpis"])
    n_csat = sum(1 for a in acts if "CSAT" in a["kpis"])
    n_rc = sum(1 for a in acts if "Recontact" in a["kpis"])
    text(s, MARGIN, y, CONTENT_W, 0.32,
         f"{n} unique actions. Tagged {n_qa} to QA, {n_csat} to CSAT, {n_rc} to Recontact "
         f"(a shared action counts in more than one column). "
         f"Coach = agent skill. Outcome = customer result. Measure = how we score. "
         f"Constraint = what we will not do.",
         size=8.5, color=GREY_TEXT)
    return s


def s_recommendation(prs, D):
    su = D["summary"]
    r2 = D["res"]["cr_r2"]
    r2_txt = f"{r2:.2f}" if r2 is not None else "—"
    s = slide(prs, "The recommendation",
              "Process compliance looks healthy. Customer outcome does not.", "08")
    callout(
        s, MARGIN, BODY_TOP, CONTENT_W, 2.48,
        "What this month is telling us",
        f"Our operation looks healthy when we measure agent process compliance "
        f"(QA {su['qa_score']:.2f}), but the customer outcome tells a different story. "
        f"Blended CSAT is {su['csat']:.2f}% against 85% (Phone {D['ch'].loc['Phone', 'CSAT_Score']:.1f}%, "
        f"Chat {D['ch'].loc['Live Chat', 'CSAT_Score']:.1f}%), and human-channel recontact is "
        f"{D['rc_audited']:.2f}%, nearly three times the 5.44% goal. "
        f"The largest gaps sit in contact reasons where agents cannot close the case: "
        f"policy, tooling, or no visibility. "
        f"The priority is not simply more coaching. Measure resolution. "
        f"Correct this month's scored defects. Fix the QA scoring gaps. "
        f"Give agents a way to close the highest-volume failure reasons.",
        size_head=15, size_body=13,
    )
    y = BODY_TOP + 2.68
    text(s, MARGIN, y, CONTENT_W, 0.24, "Three things to do", size=11, bold=True, color=INK)
    w = (CONTENT_W - 0.36) / 3
    items = [
        ("Measure resolution",
         f"Put % closed next to QA, by channel and contact reason. "
         f"{close_ten_line(D)} {closure_csat_line(D)} Close-rate vs CSAT: R² {r2_txt}."),
        ("Fix scored defects, then the form",
         "This month: Phone time management and complete information; Chat greeting, attitude, availability. "
         f"Then close the Chat scoring gap ({chat_qa_pair(D)}). The second number is measurement, not CSAT."),
        ("Let agents close the case",
         "Policy, tools, and visibility on the highest-volume failure reasons. "
         "Phone already closes about 9 of 10 assessed; Chat leaves about 4 of 10 open, mostly after following process. "
         "The priority is that constraint, not Chat coaching volume."),
    ]
    for i, (title, body) in enumerate(items):
        x = MARGIN + i * (w + 0.18)
        panel(s, x, y + 0.34, w, 2.20, title)
        text(s, x + 0.22, y + 0.82, w - 0.44, 1.52, body,
             size=11, color=GREY_CELL, line_spacing=1.28)
    return s


STATUS_WORD = {"green": "On goal", "amber": "Near goal", "red": "Off goal"}


def _short(value, n):
    return cr_label(value, n)


def badge(status):
    return (STATUS_WORD[status], status)


# =============================================================================
#  Facts
# =============================================================================


def gather():
    data = load_all_data()
    a, e, c, r = (data["fact_audits"], data["fact_errors"],
                  data["fact_csat"], data["fact_recontact"])

    summary = K.kpi_summary(a, c, r)
    ch = K.channel_performance(a, c, r).set_index("Segment")
    scatter = K.cr_level_metrics(a, c, r)
    corr = K.cr_correlation_summary(scatter).set_index("Pair")
    combined = EE.combined_operational_analysis(a, c, r)
    pareto = K.pareto_errors_simple(e)
    hist = K.qa_score_histogram(a)
    outcome = K.qa_auditor_outcome(a).set_index("Auditor_Outcome")
    stars = K.csat_by_star_rating(c).set_index("Rating")
    voc = K.voc_themes_negative(c, top_n=7)
    scope = K.recontact_by_scope(r).set_index("Scope_Key")
    rc_cr = K.recontact_by_cr(r, top_n=15, csat=c)
    csat_spc = K.csat_control_daily(c)
    qa_spc = K.qa_control_daily(a)

    vital = pareto[pareto["Acumulado_Pct"] <= 83].shape[0]
    unresolved_n = float(outcome.loc["Unresolved + process", "n"]
                         + outcome.loc["Unresolved, no process", "n"]
                         + outcome.loc["Abandoned", "n"])

    os_row = combined[combined["CR_Lv4"] == "order status & delays"].iloc[0]

    ph_e = e[K.channel_match(e["Channel"], "Phone")]
    ph_a = a[K.channel_match(a["Channel"], "Phone")]
    lc_e = e[K.channel_match(e["Channel"], "Live Chat")]
    lc_a = a[K.channel_match(a["Channel"], "Live Chat")]
    ph_c = c[K.channel_match(c["Channel"], "Phone")]
    lc_c = c[K.channel_match(c["Channel"], "Live Chat")]
    ph_csat_cr = K.csat_score_by_cr(ph_c, min_n=1, top_n=None)
    lc_csat_cr = K.csat_score_by_cr(lc_c, min_n=1, top_n=None)
    def _csat_map(df):
        if df is None or df.empty or "CR_Lv4" not in df.columns:
            return {}
        return dict(zip(
            df["CR_Lv4"].astype(str).str.strip().str.casefold(),
            df["CSAT_Score"]))
    ph_csat_map = _csat_map(ph_csat_cr)
    lc_csat_map = _csat_map(lc_csat_cr)
    unsat_cr = K.csat_unsatisfied_by_cr(c).head(8).copy()
    unsat_keys = unsat_cr["CR_Lv4"].astype(str).str.strip().str.casefold()
    unsat_cr["CSAT_Phone"] = unsat_keys.map(ph_csat_map)
    unsat_cr["CSAT_Chat"] = unsat_keys.map(lc_csat_map)

    diss = K.qa_dissatisfaction_owner(a).set_index("Dissatisfaction_Owner")
    subr = K.qa_dissatisfaction_subreason(a).set_index("Dissatisfaction_Subreason")

    # People cuts
    qa_q = K.qa_agent_quartiles(a, min_n=5)
    csat_q = K.csat_agent_quartiles(c, a, min_n=20)
    qa_b = K.quartile_band_summary(qa_q)["bands"]
    csat_b = K.quartile_band_summary(csat_q)["bands"]
    qa_gap = K.agents_below_qa_goal(a, min_n=5)
    coach = A.qa_coaching_queue(qa_gap, top_n=10)
    sup = K.supervisor_overview(a, c, min_n=5)
    sup_vol = sup[sup["n"] >= 20].dropna(subset=["CSAT_Score"])
    mix = K.supervisor_quartile_mix(qa_q)
    mix_big = mix[mix["Ranked_Agents"] >= 10].nlargest(1, "Q4_Share").iloc[0]
    worst_qa_sup = sup_vol.nsmallest(1, "QA_Score").iloc[0]
    worst_csat_sup = sup_vol.nsmallest(1, "CSAT_Score").iloc[0]
    worst_agent = K.csat_agent_unsat_concentrators(c, a, top_n=1).iloc[0]
    ten_qa = K.qa_by_tenure(a).set_index("Tenure_Cohort")
    ten_csat = K.tenure_csat_overview(a, c).set_index("Tenure_Cohort")

    people = {
        "agents_ranked": len(qa_q),
        "csat_ranked": len(csat_q),
        "n_supervisors": int(a["Supervisor_ID"].nunique()),
        "qa_gap": qa_gap,
        "n_below_goal": len(qa_gap),
        "gap_top5_share": float(qa_gap.head(5)["Gap_Impact"].sum()
                                / qa_gap["Gap_Impact"].sum() * 100),
        "coach_queue": coach,
        "coach_top5_agents": int(coach.head(5)["Agents"].sum()),
        "qa_q1_mean": qa_b["Q1"]["mean"], "qa_q2_mean": qa_b["Q2"]["mean"],
        "qa_q3_mean": qa_b["Q3"]["mean"], "qa_q4_mean": qa_b["Q4"]["mean"],
        "qa_q4_n": qa_b["Q4"]["n"], "qa_q4_lo": qa_b["Q4"]["lo"],
        "qa_q4_hi": qa_b["Q4"]["hi"],
        "csat_q4_n": csat_b["Q4"]["n"], "csat_q4_mean": csat_b["Q4"]["mean"],
        "csat_q4_lo": csat_b["Q4"]["lo"], "csat_q1_hi": csat_b["Q1"]["hi"],
        "tenure_worst_qa": float(ten_qa.loc["More than 1 year", "QA_Score"]),
        "tenure_worst_csat": float(ten_csat.loc["More than 1 year", "CSAT_Score"]),
        "worst_qa_sup": worst_qa_sup["Supervisor_ID"],
        "worst_qa_sup_score": float(worst_qa_sup["QA_Score"]),
        "worst_qa_sup_n": int(worst_qa_sup["n"]),
        "worst_csat_sup": worst_csat_sup["Supervisor_ID"],
        "worst_csat_sup_qa": float(worst_csat_sup["QA_Score"]),
        "worst_csat_sup_csat": float(worst_csat_sup["CSAT_Score"]),
        "worst_csat_sup_n": int(worst_csat_sup["Feedback"]),
        "mix_sup": mix_big["Supervisor_ID"],
        "mix_pct": float(mix_big["Q4_Share"]),
        "worst_agent_csat": worst_agent["Agent"],
        "worst_agent_csat_score": float(worst_agent["CSAT_Score"]),
        "worst_agent_csat_n": int(worst_agent["Feedback"]),
        "worst_agent_unsat": int(worst_agent["Unsatisfied"]),
        "worst_agent_share": float(worst_agent["Unsat_Share"]),
    }

    lc_score = lc_a["Score_Pct"].astype(float)
    lc_noproc = lc_a["Process_Adherence"].eq("Did not follow process")
    lc_cf = lc_score.copy()
    lc_cf.loc[lc_noproc] = 0

    return {
        **people,
        "summary": summary,
        "rc_rate": K.recontact_rate(r),
        "vols": K.volume_totals(a, c, r),
        "crit": K.critical_fail_stats(a, e),
        "unsat": K.csat_unsat_totals(c),
        "ch": ch,
        "ch_break": EE.qa_channel_breakdown(a, e),
        "attr_phone": K.top_failing_attributes(ph_e, ph_a, top_n=6),
        "attr_chat": K.top_failing_attributes(lc_e, lc_a, top_n=6),
        "qa_cr_phone": K.qa_score_by_cr(ph_a, top_n=6, min_n=3),
        "qa_cr_chat": K.qa_score_by_cr(lc_a, top_n=6, min_n=3),
        "qa_cr_all": K.qa_score_by_cr(a, top_n=8, min_n=3),
        "cov": K.cr_join_coverage(a, c, r),
        "corr_qa_csat": corr.loc["QA vs CSAT"],
        "corr_qa_rc": corr.loc["QA vs Recontact"],
        "combined": combined,
        "weekly": K.weekly_kpi_table(a, c, r).dropna(subset=["QA_Score"]),
        "bt": K.csat_by_business_type(c),
        "unsat_cr": unsat_cr,
        "csat_phone_n": int(ph_c["Feedback CNT"].fillna(0).sum()),
        "csat_chat_n": int(lc_c["Feedback CNT"].fillna(0).sum()),
        "voc": voc,
        "voc_tagged": int(voc.iloc[0]["Total_Tagged"]),
        "voc_resolution": float(voc.iloc[0]["Pct"] + voc.iloc[1]["Pct"]),
        "voc_top_pct": float(voc.iloc[0]["Pct"]),
        "voc_attitude": float(voc[voc["Theme"].str.contains("attitude")]["Pct"].iloc[0]),
        "rc_channels": K.recontact_channel_table(r),
        "rc_cr": rc_cr,
        "rc_top_rate": rc_cr[rc_cr["Contacts"] >= 3000].nlargest(5, "Recontact_Rate"),
        "rc_top3_share": float(rc_cr.head(3)["Pct"].sum()),
        "rc_ex_sh": float(scope.loc["ex_self_help", "Rate"]),
        "rc_audited": float(scope.loc["audited", "Rate"]),
        "dilution": K.recontact_dilution_stats(r),
        "diss_owner": K.qa_dissatisfaction_owner(a),
        "diss_process_pct": float(diss.loc["CX Process", "Pct"]),
        "diss_people_pct": float(diss.loc["People (CSR)", "Pct"]),
        "notres_pct": float(subr.loc["Not resolution-based", "Pct"]),
        "adherence_pct": K.qa_process_adherence_summary(a)["pct_not_followed"],
        "unres_proc_score": float(outcome.loc["Unresolved + process", "QA_Score"]),
        "unres_proc_n": int(outcome.loc["Unresolved + process", "n"]),
        "unres_noproc_score": float(outcome.loc["Unresolved, no process", "QA_Score"]),
        "unres_noproc_n": int(outcome.loc["Unresolved, no process", "n"]),
        "res_proc_score": float(outcome.loc["Resolved + process", "QA_Score"]),
        "res_proc_n": int(outcome.loc["Resolved + process", "n"]),
        "res_noproc_n": int(outcome.loc["Resolved, no process", "n"]),
        "chat_noproc_n": int(lc_noproc.sum()),
        "chat_noproc_n100": int((lc_score[lc_noproc] == 100).sum()),
        "chat_qa_if_noproc0": float(lc_cf.mean()),
        "chat_n100_pct": float((lc_score == 100).mean() * 100),
        "unresolved_share": unresolved_n / len(a) * 100,
        "not_resolved_n": int((a["Solution_Provided"] == "Not resolved").sum()),
        "owner_n": int(a["Dissatisfaction_Owner"].notna().sum()),
        "owner_pct": float(a["Dissatisfaction_Owner"].notna().mean() * 100),
        "perfect_share": float(hist[hist["QA_Score"] == 100]["Share_Pct"].iloc[0]),
        "zero_share": float(hist[hist["QA_Score"] == 0]["Share_Pct"].iloc[0]),
        "vital_n": vital,
        "vital_pct": float(pareto.iloc[vital - 1]["Acumulado_Pct"]),
        "star1_pct": float(stars.loc["1 Star", "Pct"]),
        "star5_pct": float(stars.loc["5 Stars", "Pct"]),
        "csat_days": len(csat_spc),
        "csat_lcl": float(csat_spc["LCL"].iloc[0]),
        "csat_ucl": float(csat_spc["UCL"].iloc[0]),
        "qa_low": float(qa_spc["Value"].min()),
        "os_qa": float(os_row["QA_Score"]),
        "os_csat": float(os_row["CSAT_Score"]),
        "os_rc": float(os_row["Recontact_Rate"]),
        "os_surveys": int(os_row["Feedback"]),
        "os_contacts": int(os_row["Contacts"]),
        "os_repeats": int(os_row["Recontacts"]),
        "res": resolution_story(a, c),
        "close": {
            "Phone": channel_close_stats(a, "Phone"),
            "Live Chat": channel_close_stats(a, "Live Chat"),
        },
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    build_mark()
    D = gather()

    prs = Presentation()
    configure_widescreen(prs)

    s_cover(prs, D)
    s_scope(prs, D)
    s_exec_summary(prs, D)
    s_two_paths(prs, D)
    s_critical(prs, D)
    s_control(prs, D)

    section_slide(prs, "01", "QA analysis",
                  "Score against goal by channel and by contact reason. Then the defects behind each gap.")
    s_qa_channel(prs, D)
    s_qa_phone(prs, D)
    s_qa_chat(prs, D)
    s_qa_defects(prs, D)
    s_defect_focus(prs, D)
    s_qa_cr(prs, D)
    s_qa_fail_volume(prs, D)

    section_slide(prs, "02", "CSAT and voice of the customer",
                  "Blended CSAT against goal. Then Phone vs Chat. Who is dragging it. What detractors say.")
    s_csat(prs, D)
    s_csat_fail_volume(prs, D)
    s_voc(prs, D)

    section_slide(prs, "03", "Recontact analysis",
                  "Rate against goal. Which channels and contact reasons drive repeat contacts.")
    s_recontact(prs, D)
    s_recontact_cr(prs, D)

    section_slide(prs, "04", "People: where coaching should focus",
                  "Which agents sit outside the pack. Which teams carry the coaching load.")
    s_people(prs, D)
    s_supervisors(prs, D)

    section_slide(prs, "05", "Combined analysis and root cause",
                  "Where QA, CSAT and recontact miss on the same contact reason. Then why.")
    s_combined(prs, D)
    s_resolution_csat(prs, D)
    s_five_whys(prs, D)
    s_fishbone(prs, D)
    s_control_plan(prs, D)

    section_slide(prs, "06", "Action plans",
                  "What must change. Who owns it. When it lands.")
    s_actions_bt(prs, D)
    s_actions_channel(prs, D)
    s_action_matrix(prs, D)
    s_recommendation(prs, D)

    apply_sheet_numbers(prs)

    n_slides = len(list(prs.slides))
    import shutil
    fallback = os.path.join(os.path.dirname(OUT_DIR), "Entregable_2_LISTO.pptx")
    try:
        prs.save(OUT_PPTX)
        saved = OUT_PPTX
    except PermissionError:
        saved = fallback
        prs.save(saved)
        print(f"Original PPTX is open; wrote {saved}")
    root_copy = os.path.join(os.path.dirname(OUT_DIR), "Entregable_2_Weekly_Performance_Report.pptx")
    for dest in (root_copy, fallback):
        if os.path.abspath(dest) == os.path.abspath(saved):
            continue
        try:
            shutil.copy2(saved, dest)
        except OSError as exc:
            print(f"Could not write {dest} ({exc})")
    print(f"OK -> {saved}  ({n_slides} slides)")


if __name__ == "__main__":
    main()
