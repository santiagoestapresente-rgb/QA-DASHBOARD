"""Render every chart used by the Deliverable 2 deck, from the live data pipeline."""

from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config  # noqa: E402
from cr_labels import cr_label  # noqa: E402
from modules.data_loader import load_all_data  # noqa: E402
from modules import kpis as K  # noqa: E402
from modules import executive_engine as EE  # noqa: E402
from modules.resolution_csat import resolution_story  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "entregable 2", "deck", "charts")

ORANGE = "#FF6600"
INK = "#1A1A1A"
GREEN = "#16A34A"
AMBER = "#F59E0B"
RED = "#E11D2E"
GREY = "#9AA0A6"
GREY_DARK = "#4B5563"
GRID = "#E5E7EB"
PANEL = "#F4F5F6"

plt.rcParams.update({
    "font.family": ["Inter", "Segoe UI", "DejaVu Sans"],
    "axes.edgecolor": GRID,
    "axes.labelcolor": GREY_DARK,
    "text.color": INK,
    "xtick.color": GREY_DARK,
    "ytick.color": GREY_DARK,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})


def _clean(ax, spines=("top", "right")):
    for sp in spines:
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=0, labelsize=8.5)
    ax.set_axisbelow(True)
    return ax


def _save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=200, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print(f"  {name}")
    return path


def _ellipsis(s, n):
    s = str(s)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def _wrap(s, n=22):
    words, lines, cur = str(s).split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= n:
            cur = f"{cur} {w}".strip()
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return "\n".join([ln for ln in lines if ln])


GREEN_TINT = "#E9F7EF"
AMBER_TINT = "#FEF4E4"
RED_TINT = "#FDECEE"


def _csat_tone(v):
    gap = 85.0 - float(v)
    if gap <= 0:
        return GREEN, GREEN_TINT
    if gap <= 5:
        return AMBER, AMBER_TINT
    return RED, RED_TINT


def _res_tone(v):
    v = float(v)
    if v >= 70:
        return GREEN, GREEN_TINT
    if v > 50:
        return AMBER, AMBER_TINT
    return RED, RED_TINT


def _metric_chip(ax, x, y, w, h, label, value, tone_fn):
    fg, _bg = tone_fn(value)
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.28",
                                fc=fg, ec=fg, lw=0.6))
    ax.text(x + w / 2, y + h / 2, f"{value:.0f}% {label}",
            ha="center", va="center", fontsize=6.2, fontweight="bold", color="white")


def _node_title(node, width_chars):
    lines = _wrap(cr_label(node["name"]), width_chars).split("\n")
    if len(lines) > 2:
        lines = [lines[0], _ellipsis(lines[1], width_chars)]
    return "\n".join(lines)


def _node_box(ax, x, y, w, h, node, is_lv4=False):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0,rounding_size=0.4",
        fc="white", ec=ORANGE if is_lv4 else GRID, lw=1.35 if is_lv4 else 0.9))
    ax.text(x + w / 2, y + h - 0.38, _node_title(node, 16 if is_lv4 else 13),
            ha="center", va="top", fontsize=6.8 if is_lv4 else 6.1,
            fontweight="bold", color=INK, linespacing=1.15)
    pill_h = 1.48
    gap = 0.10
    pill_w = (w - 0.48 - gap) / 2
    py = y + 0.20
    _metric_chip(ax, x + 0.20, py, pill_w, pill_h, "Res", node["pct_res"], _res_tone)
    _metric_chip(ax, x + 0.20 + pill_w + gap, py, pill_w, pill_h,
                 "CSAT", node["csat"], _csat_tone)


def chart_cr_tree(story, name):
    """Contact reason (Lv4) → its sub-reasons, traffic-light Resolved and CSAT."""
    fig, ax = plt.subplots(figsize=(13.3, 4.55))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    ax.text(0.4, 98.2, "Contact reason  →  its sub-reasons",
            fontsize=10.6, fontweight="bold", color=INK, va="top")
    ax.text(0.4, 93.8,
            "Orange = the contact reason. Grey = the sub-reasons.  "
            "CSAT 85 or above is green. Under 80 is red.  Closed 70% or above is green. 50% or below is red.",
            fontsize=6.8, color=GREY_DARK, va="top")

    panels = [
        (0.5, 48.9, "These reasons can close. CSAT of the reason is 85 or above",
         story.get("tree_close") or [], GREEN),
        (50.7, 48.7, "These reasons cannot close. They pull CSAT down",
         story.get("tree_block") or [], RED),
    ]
    for x0, width, title, branches, rim in panels:
        ax.add_patch(FancyBboxPatch((x0, 1.5), width, 89.4,
                                    boxstyle="round,pad=0.18,rounding_size=0.65",
                                    fc=PANEL, ec=rim, lw=1.25))
        ax.text(x0 + 0.55, 88.6, title, fontsize=8.0, fontweight="bold", color=INK, va="top")
        ax.text(x0 + 0.55, 84.7, "Contact reason", fontsize=5.8, color=ORANGE,
                fontweight="bold", va="top")
        ax.text(x0 + 17.6, 84.7, "Sub-reasons", fontsize=5.8, color=GREY_DARK,
                fontweight="bold", va="top")
        n = max(len(branches), 1)
        band = 74.5 / n
        pw, ph = 16.2, 7.05
        for i, br in enumerate(branches):
            top = 82.4 - i * band
            py = top - ph
            _node_box(ax, x0 + 0.55, py, pw, ph, br, is_lv4=True)
            kids = br.get("children") or []
            mid_y = py + ph / 2
            if not kids:
                ax.text(x0 + pw + 1.6, mid_y, "No sub-reason in this sample",
                        fontsize=6.3, color=GREY_DARK, va="center")
                continue
            cw = min(9.2, (width - pw - 3.2) / len(kids) - 0.45)
            cw = max(cw, 8.2)
            ch = 6.75
            for j, kid in enumerate(kids):
                kx = x0 + pw + 2.2 + j * (cw + 0.45)
                ky = mid_y - ch / 2
                ax.plot([x0 + 0.55 + pw, kx], [mid_y, ky + ch / 2], color=GREY, lw=0.9)
                _node_box(ax, kx, ky, cw, ch, kid, is_lv4=False)

    return _save(fig, name)


# --------------------------------------------------------------------- charts


def chart_pareto(df, cat_col, count_col, name, title, vital_label="80% of defects",
                 ylabel="Fails", top_n=10):
    d = df.copy().head(top_n).reset_index(drop=True)
    total = df[count_col].sum()
    d["cum"] = d[count_col].cumsum() / total * 100
    crit = (
        d["Is_Critical"].fillna(False).astype(bool)
        if "Is_Critical" in d.columns else pd.Series(False, index=d.index)
    )

    fig, ax = plt.subplots(figsize=(7.6, 4.1))
    x = np.arange(len(d))
    colors = [ORANGE if i == 0 else "#F7A76C" if i < 3 else "#C9CCD1"
              for i in range(len(d))]
    edges = [RED if bool(c) else "none" for c in crit]
    lws = [1.7 if bool(c) else 0.0 for c in crit]
    ax.bar(x, d[count_col], color=colors, edgecolor=edges, linewidth=lws,
           width=0.68, zorder=3)
    ax.set_xticks(x)
    # Single-line labels only: a wrapped second line drifts sideways when rotated
    # and collides with the neighbouring category. ★ marks a critical attribute.
    labels = [
        f"{cr_label(v, 32)} ★" if bool(c) else cr_label(v, 34)
        for v, c in zip(d[cat_col], crit)
    ]
    ax.set_xticklabels(labels, fontsize=7.0, rotation=25, ha="right",
                       rotation_mode="anchor")
    ax.set_ylabel(ylabel, fontsize=8.5)
    ax.set_ylim(0, d[count_col].max() * 1.16)
    ax.grid(axis="x", visible=False)
    _clean(ax)

    for xi, v in zip(x, d[count_col]):
        ax.text(xi, v + d[count_col].max() * 0.025, f"{int(v):,}", ha="center",
                fontsize=8, color=INK, fontweight="bold")

    ax2 = ax.twinx()
    ax2.plot(x, d["cum"], color=INK, lw=1.6, marker="o", ms=3.5, zorder=4)
    ax2.axhline(80, color=RED, lw=1.0, ls="--", zorder=2)
    ax2.text(len(d) - 0.45, 82.5, vital_label, fontsize=7.5, color=RED, ha="right")
    ax2.set_ylim(0, 118)
    ax2.set_ylabel("Cumulative %", fontsize=8.5)
    ax2.grid(False)
    _clean(ax2, spines=("top",))
    for xi, v in zip(x, d["cum"]):
        ax2.text(xi, v + 5.5, f"{v:.0f}%", ha="center", fontsize=7.0, color=GREY_DARK,
                 zorder=6,
                 bbox=dict(boxstyle="round,pad=0.16", fc="white", ec="none", alpha=0.92))

    if bool(crit.any()):
        ax.legend(
            handles=[
                Patch(facecolor="white", edgecolor=RED, linewidth=1.6,
                      label="★ critical (score = 0)"),
            ],
            loc="upper right", frameon=False, fontsize=7.2,
        )
    ax.set_title(title, fontsize=10.5, fontweight="bold", color=INK, loc="left", pad=10)
    return _save(fig, name)


def _channel_short(value):
    s = str(value).strip().casefold()
    if "phone" in s:
        return "Phone"
    if "chat" in s:
        return "Chat"
    return str(value)


def chart_pareto_defects(errors, name, title):
    """Combined fails, but each bar is one channel. Critical attributes are marked."""
    g = (
        errors.groupby(["Error_Category", "Channel", "Is_Critical"], dropna=False)
        .size()
        .reset_index(name="Cantidad")
        .sort_values("Cantidad", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    total = max(int(len(errors)), 1)
    g["cum"] = g["Cantidad"].cumsum() / total * 100
    g["ch"] = g["Channel"].map(_channel_short)
    g["Label"] = [
        f"{cat} · {ch}{' ★' if bool(crit) else ''}"
        for cat, ch, crit in zip(g["Error_Category"], g["ch"], g["Is_Critical"])
    ]

    fig, ax = plt.subplots(figsize=(7.6, 4.1))
    x = np.arange(len(g))
    fills = [ORANGE if ch == "Phone" else "#8B9198" for ch in g["ch"]]
    edges = [RED if bool(c) else "none" for c in g["Is_Critical"]]
    lws = [1.7 if bool(c) else 0.0 for c in g["Is_Critical"]]
    ax.bar(x, g["Cantidad"], color=fills, edgecolor=edges, linewidth=lws,
           width=0.68, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(g["Label"].tolist(), fontsize=6.6, rotation=28,
                       ha="right", rotation_mode="anchor")
    ax.set_ylabel("Fails", fontsize=8.5)
    ax.set_ylim(0, g["Cantidad"].max() * 1.18)
    ax.grid(axis="x", visible=False)
    _clean(ax)

    for xi, v in zip(x, g["Cantidad"]):
        ax.text(xi, v + g["Cantidad"].max() * 0.025, f"{int(v):,}", ha="center",
                fontsize=8, color=INK, fontweight="bold")

    ax2 = ax.twinx()
    ax2.plot(x, g["cum"], color=INK, lw=1.6, marker="o", ms=3.5, zorder=4)
    ax2.axhline(80, color=RED, lw=1.0, ls="--", zorder=2)
    ax2.text(len(g) - 0.45, 82.5, "80% of defects", fontsize=7.5, color=RED, ha="right")
    ax2.set_ylim(0, 118)
    ax2.set_ylabel("Cumulative %", fontsize=8.5)
    ax2.grid(False)
    _clean(ax2, spines=("top",))
    for xi, v in zip(x, g["cum"]):
        ax2.text(xi, v + 5.5, f"{v:.0f}%", ha="center", fontsize=7.0, color=GREY_DARK,
                 zorder=6,
                 bbox=dict(boxstyle="round,pad=0.16", fc="white", ec="none", alpha=0.92))

    ax.legend(
        handles=[
            Patch(facecolor=ORANGE, edgecolor="none", label="Phone"),
            Patch(facecolor="#8B9198", edgecolor="none", label="Chat"),
            Patch(facecolor="white", edgecolor=RED, linewidth=1.6, label="★ critical (score = 0)"),
        ],
        loc="upper right", frameon=False, fontsize=7.0,
    )
    ax.set_title(title, fontsize=10.2, fontweight="bold", color=INK, loc="left", pad=10)
    return _save(fig, name)


def chart_run(spc, name, title, ylabel, lower_better=False):
    d = spc.copy()
    d["Date"] = pd.to_datetime(d["Date"])
    # Portrait-ish: these three sit side by side in one third of a slide each.
    fig, ax = plt.subplots(figsize=(6.8, 4.2))

    cl, ucl, lcl, goal = d["CL"].iloc[0], d["UCL"].iloc[0], d["LCL"].iloc[0], d["Goal"].iloc[0]
    d0, d1 = d["Date"].min(), d["Date"].max()
    ax.axhspan(lcl, ucl, xmax=0.845, color=PANEL, zorder=0)
    for value, color, style, lw in [(cl, INK, "-", 1.2), (ucl, GREY, "--", 1.0),
                                    (lcl, GREY, "--", 1.0), (goal, RED, ":", 1.4)]:
        ax.plot([d0, d1], [value, value], color=color, ls=style, lw=lw, zorder=2)

    ax.plot(d["Date"], d["Value"], color=ORANGE, lw=1.7, marker="o", ms=4,
            mfc="white", mec=ORANGE, mew=1.3, zorder=4)

    out = d[d["Beyond_Limits"]]
    if len(out):
        ax.scatter(out["Date"], out["Value"], s=70, facecolor=RED, edgecolor="white",
                   zorder=5, linewidth=1.2)

    span = max(d["Value"].max(), ucl, goal) - min(d["Value"].min(), lcl, goal)
    pad = span * 0.14
    ax.set_ylim(min(d["Value"].min(), lcl, goal) - pad,
                max(d["Value"].max(), ucl, goal) + pad)

    for value, label, color in [(cl, f"CL {cl:.2f}", INK), (ucl, f"UCL {ucl:.2f}", GREY),
                                (lcl, f"LCL {lcl:.2f}", GREY),
                                (goal, f"Goal {goal:.2f}", RED)]:
        ax.annotate(label, xy=(d1, value), xytext=(7, 0), textcoords="offset points",
                    va="center", fontsize=7.4, color=color, fontweight="bold")

    ax.set_ylabel(ylabel, fontsize=8.5)
    ax.grid(axis="x", visible=False)
    span_days = (d1 - d0).days or 1
    ax.set_xlim(d0, d1 + pd.Timedelta(days=max(4, round(span_days * 0.18))))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
    _clean(ax)
    ax.set_title(title, fontsize=10.5, fontweight="bold", color=INK, loc="left", pad=10)
    return _save(fig, name)


def chart_hist_qa(audits, name):
    h = K.qa_score_histogram(audits)
    fig, ax = plt.subplots(figsize=(6.4, 3.5))
    colors = [RED if s == 0 else AMBER if s < 85 else ORANGE if s < 100 else GREEN
              for s in h["QA_Score"]]
    bars = ax.bar([str(int(s)) for s in h["QA_Score"]], h["Audits"], color=colors,
                  width=0.62, zorder=3)
    for b, n, p in zip(bars, h["Audits"], h["Share_Pct"]):
        ax.text(b.get_x() + b.get_width() / 2, n + 40, f"{int(n)}\n{p}%", ha="center",
                fontsize=8, color=INK, fontweight="bold", linespacing=1.3)
    ax.set_xlabel("QA score obtained", fontsize=8.5)
    ax.set_ylabel("Audits", fontsize=8.5)
    ax.set_ylim(0, h["Audits"].max() * 1.22)
    ax.grid(axis="x", visible=False)
    _clean(ax)
    ax.set_title("QA score distribution: most audits sit at 0 or 100",
                 fontsize=10.5, fontweight="bold", color=INK, loc="left", pad=10)
    return _save(fig, name)


def chart_scatter_qa_csat(scatter, corr, name):
    d = scatter.dropna(subset=["QA_Score", "CSAT_Pct"])
    d = d[d["QA_N"] >= 3]
    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    sizes = np.clip(d["Feedback"].fillna(20) / 12, 18, 320)
    ax.scatter(d["QA_Score"], d["CSAT_Pct"], s=sizes, color=ORANGE, alpha=0.55,
               edgecolor="white", linewidth=0.8, zorder=3)

    z = np.polyfit(d["QA_Score"], d["CSAT_Pct"], 1)
    xs = np.linspace(d["QA_Score"].min(), d["QA_Score"].max(), 40)
    ax.plot(xs, np.polyval(z, xs), color=INK, lw=1.4, ls="--", zorder=4)

    ax.axhline(config.CSAT_GOAL, color=RED, lw=1.0, ls=":", zorder=2)
    ax.axvline(config.QA_GOAL, color=RED, lw=1.0, ls=":", zorder=2)
    ax.text(config.QA_GOAL + 0.4, 3, "QA goal 85", fontsize=7.2, color=RED)
    ax.text(d["QA_Score"].min(), config.CSAT_GOAL + 2, "CSAT goal 85", fontsize=7.2,
            color=RED)

    row = corr[corr["Pair"] == "QA vs CSAT"].iloc[0]
    ax.text(0.02, 0.06,
            f"r = {row['Pearson_r']:.3f}   R² = {row['R2']:.3f}   n = {int(row['N_CR'])} CRs\n"
            f"QA explains {row['R2'] * 100:.1f}% of CSAT variation",
            transform=ax.transAxes, fontsize=8.2, color=INK, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.45", fc=PANEL, ec=GRID, lw=0.8))

    ax.set_xlabel("QA score by contact reason (CR Lv4)", fontsize=8.5)
    ax.set_ylabel("CSAT %", fontsize=8.5)
    _clean(ax)
    ax.set_title("QA does not tell you if the customer will be happy", fontsize=10.5,
                 fontweight="bold", color=INK, loc="left", pad=10)
    return _save(fig, name)


def chart_bar_status(df, cat_col, val_col, goal, name, title, xlabel,
                     lower_better=False, n_col=None, width=6.6, height=3.6):
    d = df.copy()
    fig, ax = plt.subplots(figsize=(width, height))
    y = np.arange(len(d))[::-1]

    def status(v):
        gap = (goal - v) if not lower_better else (v - goal)
        if gap <= 0:
            return GREEN
        return AMBER if gap <= 5 else RED

    colors = [status(v) for v in d[val_col]]
    ax.barh(y, d[val_col], color=colors, height=0.62, zorder=3)
    ax.axvline(goal, color=INK, lw=1.3, ls="--", zorder=4)
    ax.text(goal, len(d) - 0.25, f" Goal {goal:g}", fontsize=7.8, color=INK,
            fontweight="bold", va="top")

    labels = []
    for _, r in d.iterrows():
        lab = _wrap(cr_label(r[cat_col]), 34)
        if n_col:
            lab += f"  (n={int(r[n_col]):,})"
        labels.append(lab)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    xmax = max(d[val_col].max(), goal) * 1.16
    for yi, v in zip(y, d[val_col]):
        crosses_goal = v + xmax * 0.075 > goal and v < goal
        if crosses_goal:
            ax.text(v - xmax * 0.012, yi, f"{v:.1f}", va="center", ha="right",
                    fontsize=8.2, color="white", fontweight="bold")
        else:
            ax.text(v + xmax * 0.012, yi, f"{v:.1f}", va="center",
                    fontsize=8.2, color=INK, fontweight="bold")

    ax.set_xlim(0, xmax)
    ax.set_xlabel(xlabel, fontsize=8.5)
    ax.grid(axis="y", visible=False)
    _clean(ax)
    ax.set_title(title, fontsize=10.5, fontweight="bold", color=INK, loc="left", pad=10)
    return _save(fig, name)


def chart_stars(csat, name):
    s = K.csat_by_star_rating(csat)
    order = ["5 Stars", "4 Stars", "3 Stars", "2 Stars", "1 Star"]
    s = s.set_index("Rating").loc[[r for r in order if r in set(s["Rating"])]].reset_index()
    colors = [GREEN, GREEN, AMBER, RED, RED]
    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    y = np.arange(len(s))[::-1]
    ax.barh(y, s["Pct"], color=colors[:len(s)], height=0.6, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(s["Rating"], fontsize=8.5)
    for yi, (p, c) in enumerate(zip(s["Pct"], s["Count"])):
        ax.text(p + 1.2, y[yi], f"{p}%   ({int(c):,})", va="center", fontsize=8.2,
                color=INK, fontweight="bold")
    ax.set_xlim(0, s["Pct"].max() * 1.30)
    ax.set_xlabel("Share of surveys", fontsize=8.5)
    ax.grid(axis="y", visible=False)
    _clean(ax)
    ax.set_title("Most ratings are 1 star or 5 stars (blended Phone + Chat)", fontsize=10.5,
                 fontweight="bold", color=INK, loc="left", pad=10)
    return _save(fig, name)


def chart_weekly(weekly, name):
    d = weekly.dropna(subset=["QA_Score"]).copy()
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    x = np.arange(len(d))
    ax.plot(x, d["QA_Score"], color=ORANGE, lw=2.2, marker="o", ms=5, label="QA score")
    ax.plot(x, d["CSAT_Score"], color=INK, lw=1.8, marker="s", ms=4.5, label="CSAT %")
    ax.axhline(85, color=RED, lw=1.1, ls=":", zorder=1)
    ax.text(len(d) - 0.05, 85.8, "Goal 85", fontsize=7.5, color=RED, ha="right")
    for xi, (q, c) in enumerate(zip(d["QA_Score"], d["CSAT_Score"])):
        ax.text(xi, q + 1.4, f"{q:.1f}", ha="center", fontsize=8, color=ORANGE,
                fontweight="bold")
        ax.text(xi, c - 2.6, f"{c:.1f}", ha="center", fontsize=8, color=INK,
                fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(d["Week"], fontsize=8.5)
    ax.set_ylim(72, 100)
    ax.set_ylabel("%", fontsize=8.5)
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, fontsize=8.5, loc="lower left", ncol=2,
              bbox_to_anchor=(0, 1.02))
    _clean(ax)

    ax2 = ax.twinx()
    ax2.bar(x, d["Recontact_Rate"], color="#DCDFE3", width=0.34, zorder=0)
    ax2.set_ylim(0, 18)
    ax2.set_ylabel("Recontact %", fontsize=8.5)
    ax2.grid(False)
    _clean(ax2, spines=("top",))
    for xi, v in zip(x, d["Recontact_Rate"]):
        ax2.text(xi, v + 0.25, f"{v:.2f}", ha="center", fontsize=7.4, color=GREY_DARK)
    return _save(fig, name)


def chart_channel(ch, name):
    d = ch[ch["Segment"] != "Overall"].copy()
    metrics = [("QA_Score", "QA score", 85, False),
               ("CSAT_Score", "CSAT %", 85, False),
               ("Recontact_Rate", "Recontact %", 5.44, True)]
    fig, axes = plt.subplots(1, 3, figsize=(7.8, 3.0))
    for ax, (col, label, goal, lower) in zip(axes, metrics):
        vals = d[col].values
        colors = []
        for v in vals:
            gap = (v - goal) if lower else (goal - v)
            colors.append(GREEN if gap <= 0 else AMBER if gap <= 5 else RED)
        x = np.arange(len(d))
        ax.bar(x, vals, color=colors, width=0.55, zorder=3)
        ax.axhline(goal, color=INK, lw=1.2, ls="--", zorder=4)
        ax.set_xticks(x)
        ax.set_xticklabels(d["Segment"], fontsize=8)
        ax.set_title(label, fontsize=9.5, fontweight="bold", color=INK, pad=8)
        for xi, v in zip(x, vals):
            ax.text(xi, v + max(vals) * 0.03, f"{v:.1f}", ha="center", fontsize=8.4,
                    color=INK, fontweight="bold")
        ax.set_ylim(0, max(max(vals), goal) * 1.25)
        ax.grid(axis="x", visible=False)
        _clean(ax)
    fig.tight_layout()
    return _save(fig, name)


def chart_auditor_outcome(audits, name):
    d = K.qa_auditor_outcome(audits)
    d = d[d["n"] >= 50].copy()
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    y = np.arange(len(d))[::-1]
    colors = [RED if "Unresolved" in o or "Abandoned" in o else GREEN
              for o in d["Auditor_Outcome"]]
    ax.barh(y, d["QA_Score"], color=colors, height=0.6, zorder=3)
    ax.axvline(85, color=INK, lw=1.3, ls="--", zorder=4)
    ax.text(85, len(d) - 0.3, " QA goal 85", fontsize=7.8, color=INK, fontweight="bold",
            va="top")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{o}  (n={int(n):,})" for o, n in zip(d["Auditor_Outcome"], d["n"])],
                       fontsize=8.3)
    for yi, v in zip(y, d["QA_Score"]):
        # Keep the value clear of the goal rule at 85.
        if 82 < v + 6 and v < 85:
            ax.text(v - 1.2, yi, f"{v:.2f}", va="center", ha="right", fontsize=8.4,
                    color="white", fontweight="bold")
        else:
            ax.text(v + 1.4, yi, f"{v:.2f}", va="center", fontsize=8.4, color=INK,
                    fontweight="bold")
    ax.set_xlim(0, 112)
    ax.set_xlabel("Average QA score", fontsize=8.5)
    ax.grid(axis="y", visible=False)
    _clean(ax)
    ax.set_title("Cases that never closed score the highest on QA",
                 fontsize=10.5, fontweight="bold", color=INK, loc="left", pad=10)
    return _save(fig, name)


def chart_recontact_scope(rc, name):
    d = K.recontact_by_scope(rc)
    fig, ax = plt.subplots(figsize=(6.4, 2.9))
    x = np.arange(len(d))
    colors = [AMBER if v <= 5.44 + 5 else RED for v in d["Rate"]]
    ax.bar(x, d["Rate"], color=colors, width=0.52, zorder=3)
    ax.axhline(5.44, color=INK, lw=1.3, ls="--", zorder=4)
    ax.text(len(d) - 0.4, 5.9, "Goal 5.44%", fontsize=7.8, color=INK, fontweight="bold",
            ha="right")
    ax.set_xticks(x)
    ax.set_xticklabels([_wrap(s, 20) for s in d["Scope"]], fontsize=8.2)
    for xi, (v, c) in enumerate(zip(d["Rate"], d["Contacts"])):
        ax.text(xi, v + 0.5, f"{v:.2f}%", ha="center", fontsize=9, color=INK,
                fontweight="bold")
        ax.text(xi, v + 1.5, f"{int(c):,} contacts", ha="center", fontsize=7.2,
                color=GREY_DARK)
    ax.set_ylim(0, d["Rate"].max() * 1.35)
    ax.set_ylabel("Recontact rate", fontsize=8.5)
    ax.grid(axis="x", visible=False)
    _clean(ax)
    ax.set_title("5.83% is global. 15.56% is Phone + Chat only", fontsize=10.5,
                 fontweight="bold", color=INK, loc="left", pad=10)
    return _save(fig, name)


def chart_voc(voc, name):
    d = voc.head(7)
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    y = np.arange(len(d))[::-1]
    colors = [RED if i < 2 else ORANGE if i < 4 else "#C9CCD1" for i in range(len(d))]
    ax.barh(y, d["Pct"], color=colors, height=0.62, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels([_wrap(t, 26) for t in d["Theme"]], fontsize=8.3)
    for yi, (p, m) in enumerate(zip(d["Pct"], d["Mentions"])):
        ax.text(p + 0.4, y[yi], f"{p}%  ({int(m)})", va="center", fontsize=8.2,
                color=INK, fontweight="bold")
    ax.set_xlim(0, d["Pct"].max() * 1.32)
    ax.set_xlabel("Share of 1–3★ comments", fontsize=8.5)
    ax.grid(axis="y", visible=False)
    _clean(ax)
    ax.set_title("What detractors complain about", fontsize=10.5,
                 fontweight="bold", color=INK, loc="left", pad=10)
    return _save(fig, name)


def chart_quartiles(qa_bands, csat_bands, name):
    """Quartile means for QA and CSAT side by side, with each band's range."""
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.4))
    panels = [(axes[0], qa_bands, "QA score", 85.0, "Agents with ≥5 audits"),
              (axes[1], csat_bands, "CSAT %", 85.0, "Agents with ≥20 surveys")]

    for ax, bands, label, goal, sub in panels:
        keys = ["Q1", "Q2", "Q3", "Q4"]
        means = [bands["bands"][k]["mean"] for k in keys]
        los = [bands["bands"][k]["lo"] for k in keys]
        his = [bands["bands"][k]["hi"] for k in keys]
        ns = [bands["bands"][k]["n"] for k in keys]
        x = np.arange(4)

        colors = [GREEN if m >= goal else AMBER if m >= goal - 5 else RED for m in means]
        ax.vlines(x, los, his, color="#D8DBDF", lw=7, zorder=2)
        ax.scatter(x, means, s=110, color=colors, zorder=4, edgecolor="white",
                   linewidth=1.4)
        ax.axhline(goal, color=INK, lw=1.2, ls="--", zorder=3)
        ax.text(1.5, goal + 1.6, f"goal {goal:.0f}", ha="center", va="bottom",
                fontsize=7, color=INK, zorder=5,
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none"))

        for xi, (m, lo, hi, n) in enumerate(zip(means, los, his, ns)):
            ax.text(xi, m + 4.5, f"{m:.1f}", ha="center", fontsize=8.6, color=INK,
                    fontweight="bold")
            ax.text(xi, lo - 6.5, f"{lo:.0f}–{hi:.0f}", ha="center", fontsize=6.8,
                    color=GREY_DARK)

        ax.set_xticks(x)
        ax.set_xticklabels([f"{k}\nn={n}" for k, n in zip(keys, ns)], fontsize=8)
        ax.set_ylim(20, 108)
        ax.set_ylabel(label, fontsize=8.5)
        ax.set_title(f"{label} by agent quartile", fontsize=9.8, fontweight="bold",
                     color=INK, loc="left", pad=16)
        ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=7.4, color=GREY_DARK)
        ax.grid(axis="x", visible=False)
        _clean(ax)

    fig.tight_layout()
    return _save(fig, name)


def chart_supervisors(sup, name):
    """Supervisor QA against supervisor CSAT — the disconnect at team level."""
    d = sup.dropna(subset=["CSAT_Score"]).copy()
    d = d[d["n"] >= 20]
    fig, ax = plt.subplots(figsize=(7.0, 4.0))

    sizes = np.clip(d["n"] * 1.5, 40, 420)
    colors = []
    for _, r in d.iterrows():
        qa_ok, csat_ok = r["QA_Score"] >= 85, r["CSAT_Score"] >= 85
        colors.append(GREEN if qa_ok and csat_ok else AMBER if qa_ok else RED)
    ax.scatter(d["QA_Score"], d["CSAT_Score"], s=sizes, color=colors, alpha=0.62,
               edgecolor="white", linewidth=1.1, zorder=3)

    ax.axhline(85, color=RED, lw=1.1, ls=":", zorder=2)
    ax.axvline(85, color=RED, lw=1.1, ls=":", zorder=2)

    flag = d[(d["CSAT_Score"] <= 78) | (d["QA_Score"] <= 88) | (d["CSAT_Score"] >= 85)]
    for _, r in flag.iterrows():
        ax.annotate(r["Supervisor_ID"].replace("Supervisor ", "S"),
                    xy=(r["QA_Score"], r["CSAT_Score"]), xytext=(0, -14),
                    textcoords="offset points", ha="center", fontsize=7.2,
                    color=INK, fontweight="bold")

    n_csat_ok = int((d["CSAT_Score"] >= 85).sum())
    n_qa_ok = int((d["QA_Score"] >= 85).sum())
    ax.text(0.985, 0.94,
            f"{n_qa_ok} of {len(d)} teams pass QA. Only {n_csat_ok} passes CSAT",
            transform=ax.transAxes, ha="right", fontsize=8.4, color=INK,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.42", fc=PANEL, ec=GRID, lw=0.8))

    ax.set_xlabel("Team QA score", fontsize=8.5)
    ax.set_ylabel("Team CSAT %", fontsize=8.5)
    ax.set_ylim(66, 92)
    _clean(ax)
    ax.set_title("Supervisor teams: QA is green. CSAT is not. Bubble size is audits",
                 fontsize=10.5, fontweight="bold", color=INK, loc="left", pad=10)
    return _save(fig, name)


def chart_fishbone(name, story=None):
    """Ishikawa laid out so each bone owns an exclusive horizontal band of text."""
    story = story or {}
    nr = int(story.get("n_not_resolved") or 699)
    fol = int(story.get("n_followed_nr") or 527)
    themes = story.get("nr_themes") or {}
    policy = int(themes.get("policy_blocked") or 0)
    tools = int(themes.get("tools_system") or 0)
    r2 = story.get("cr_r2")
    r2_txt = f"{r2:.2f}" if r2 is not None else "0.64"

    fig, ax = plt.subplots(figsize=(13.2, 5.0))
    ax.set_xlim(-13, 101)
    ax.set_ylim(13, 97)
    ax.axis("off")

    # Ribs lean back towards the tail: each one meets the spine to the right of
    # its own tip, so the whole skeleton points at the effect on the right.
    spine_y, bone_h, spacing = 50, 27.0, 22.0
    x_tip_off = 12.0
    bases = [30.0, 30.0 + spacing, 30.0 + 2 * spacing]
    spine_end = bases[-1] + 4

    ax.annotate("", xy=(spine_end, spine_y), xytext=(2, spine_y),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=2.4))

    ex, ew = spine_end + 0.5, 100 - (spine_end + 0.5)
    ax.add_patch(FancyBboxPatch((ex, spine_y - 12), ew, 24,
                                boxstyle="round,pad=0.4,rounding_size=1.2",
                                fc=INK, ec=ORANGE, lw=2.2))
    ax.text(ex + ew / 2, spine_y + 6.5, "WHAT THE CUSTOMER FEELS", ha="center", va="center",
            fontsize=6.6, color=ORANGE, fontweight="bold")
    ax.text(ex + ew / 2, spine_y - 2.5, "CSAT 79.95%\nRecontact 5.83%\nQA still 94.14",
            ha="center", va="center", fontsize=8.4, color="white", fontweight="bold",
            linespacing=1.55)

    bones = [
        ("THE SCORECARD", True, 0, [
            "QA scores how the agent talked, not whether the case closed",
            f"Followed process, did not solve: QA still 96.87 (n=527)",
            f"QA vs CSAT R² 0.023 (almost no link). Closed vs CSAT R² {r2_txt}",
        ]),
        ("THE PROCESS", True, 1, [
            f"{fol} of {nr} unsolved cases still followed process",
            f"5-whys: policy blocked {policy}, tools blocked {tools}",
            "The fix sits on the contact reason, not the agent",
        ]),
        ("THE AGENTS", True, 2, [
            "One agent produced 2.7% of all unhappy surveys this month",
            "Tenure over 1 year is the only group below goal (83.97)",
            "Bottom QA group: 42 agents. Average 82.4",
        ]),
        ("WHAT THE AGENT SEES", False, 0, [
            "Phone already scores correct info. Fail it and QA goes to 0",
            "Chat does not score that at all",
            "Agents cannot see order status. That reason: 13,014 repeats",
        ]),
        ("THE CHANNELS", False, 1, [
            "Live Chat customers come back 15.99%. Phone 13.47%",
            "5.83% is global (all 12 channels). Self Help is 67% of that mix at 1.22%",
            "15.56% is human channels only: Phone + Chat",
        ]),
        ("WHY THEY CALL", False, 2, [
            "Antifraud customers come back 24–28% of the time",
            "'order status & delays' comes back 19.34% of the time",
            "This report is Delivery only",
        ]),
    ]

    for label, upper, idx, causes in bones:
        sign = 1 if upper else -1
        x_base = bases[idx]
        x_tip = x_base - x_tip_off
        tip_y = spine_y + sign * bone_h
        ax.plot([x_base, x_tip], [spine_y, tip_y], color=ORANGE, lw=2.0,
                solid_capstyle="round")

        ax.text(x_tip, tip_y + sign * 4.0, label, fontsize=8.4, fontweight="bold",
                color=INK, ha="center", va="bottom" if upper else "top", zorder=6,
                bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="none"))

        fracs = [0.34, 0.62, 0.90]
        for cause, frac in zip(causes, fracs):
            cx = x_base - frac * x_tip_off
            cy = spine_y + sign * frac * bone_h
            ax.plot([cx, cx - 4.0], [cy, cy], color=GREY, lw=0.9)
            ax.text(cx - 5.0, cy, _wrap(cause, 32), fontsize=6.6, color=GREY_DARK,
                    ha="right", va="center", linespacing=1.35)

    ax.text(-13, 96, "Why the customer comes back even when QA says the interaction was good",
            fontsize=11, fontweight="bold", color=INK, va="top")
    return _save(fig, name)


def chart_flowchart(name):
    fig, ax = plt.subplots(figsize=(13.6, 3.3))
    ax.set_xlim(0, 100)
    ax.set_ylim(-6, 40)
    ax.axis("off")

    steps = [
        ("1. Audit\nthe interaction", "Phone: 12 attributes.\nChat: 8. Never mixed.", "#FFF1E8"),
        ("2. Did we close\nthe case?", "Already on the form.\nThe auditor answers it.", "#FFE3CF"),
        ("3. Name the\ncontact reason", "The reason and its\nsub-reason.", "#FFD4B5"),
        ("4. Send\nthe fix", "Policy and tools,\nor coaching.", "#FFC59C"),
        ("5. Check CSAT\nof that reason", "Official CSAT of that\nreason, next week.", "#FFB682"),
    ]
    w, h, gap = 16.0, 17.0, 4.4
    x = 2.0
    for title, detail, fill in steps:
        box = FancyBboxPatch((x, 13), w, h, boxstyle="round,pad=0.3,rounding_size=1.0",
                             fc=fill, ec=ORANGE, lw=1.4)
        ax.add_patch(box)
        ax.text(x + w / 2, 26.5, title, ha="center", va="center", fontsize=8.8,
                fontweight="bold", color=INK, linespacing=1.4)
        ax.text(x + w / 2, 18.5, detail, ha="center", va="center", fontsize=7.4,
                color=GREY_DARK, linespacing=1.45)
        if x + w + gap < 96:
            ax.add_patch(FancyArrowPatch((x + w + 0.5, 21.5), (x + w + gap - 0.5, 21.5),
                                         arrowstyle="-|>", mutation_scale=13,
                                         color=INK, lw=1.4))
        x += w + gap

    ax.add_patch(FancyArrowPatch((90, 12.2), (10, 12.2), arrowstyle="-|>",
                                 mutation_scale=13, color=GREY, lw=1.2,
                                 connectionstyle="arc3,rad=-0.16", ls="--"))
    ax.text(50, -4.2, "Then look at next week's CSAT for that reason. Adjust the audit sample if needed.",
            ha="center", fontsize=7.6, color=GREY_DARK, style="italic")
    ax.text(2, 38, "What we will do: report close-rate by contact reason. Score correct info on Chat.",
            fontsize=10.2, fontweight="bold", color=INK, va="top")
    return _save(fig, name)


def main():
    print("Loading data...")
    data = load_all_data()
    a, e, c, r = (data["fact_audits"], data["fact_errors"],
                  data["fact_csat"], data["fact_recontact"])
    os.makedirs(OUT, exist_ok=True)
    print("Rendering charts:")

    # Pareto family
    chart_pareto_defects(e, "pareto_defects.png",
                         "12 Phone + 8 Chat attributes. Orange = Phone. Grey = Chat. ★ = critical")
    ph_e = e[K.channel_match(e["Channel"], "Phone")]
    ph_a = a[K.channel_match(a["Channel"], "Phone")]
    chart_pareto(K.top_failing_attributes(ph_e, ph_a, top_n=10), "Error_Category",
                 "Fail_Count", "pareto_phone.png",
                 "Phone: Time management is 64% of defects. ★ = critical")
    lc_e = e[K.channel_match(e["Channel"], "Live Chat")]
    lc_a = a[K.channel_match(a["Channel"], "Live Chat")]
    chart_pareto(K.top_failing_attributes(lc_e, lc_a, top_n=10), "Error_Category",
                 "Fail_Count", "pareto_chat.png",
                 "Live Chat: greeting leads. ★ = critical (correct info is not scored)")

    rc_cr = K.recontact_by_cr(r, top_n=10, csat=c)
    chart_pareto(rc_cr, "CR_Lv4", "Recontacts", "pareto_recontact.png",
                 "Repeats: 3 contact reasons drive 47% of all come-backs",
                 vital_label="80% of repeats", ylabel="Repeat contacts")

    # Run / control charts
    chart_run(K.qa_control_daily(a), "run_qa.png",
              "QA score: daily individuals chart", "QA score")
    chart_run(K.csat_control_daily(c), "run_csat.png",
              "CSAT blended: every day is stable. Every day is below goal", "CSAT %")
    chart_run(K.recontact_control_daily(r), "run_recontact.png",
              "Recontact: last week under 5.44%. Month still above", "Recontact %",
              lower_better=True)

    # Distribution, correlation, breakdowns
    chart_hist_qa(a, "hist_qa.png")
    scatter = K.cr_level_metrics(a, c, r)
    chart_scatter_qa_csat(scatter, K.cr_correlation_summary(scatter),
                          "scatter_qa_csat.png")
    chart_channel(K.channel_performance(a, c, r), "channel_compare.png")
    chart_weekly(K.weekly_kpi_table(a, c, r), "weekly_trend.png")
    chart_auditor_outcome(a, "bar_auditor_outcome.png")
    chart_stars(c, "bar_stars.png")
    chart_voc(K.voc_themes_negative(c, top_n=7), "bar_voc.png")
    chart_recontact_scope(r, "bar_rc_scope.png")

    bt = K.csat_by_business_type(c)
    bt = bt[bt["Feedback"] >= 1000].sort_values("CSAT_Score")
    chart_bar_status(bt, "Business_Type", "CSAT_Score", config.CSAT_GOAL,
                     "bar_business_type.png",
                     "CSAT by Business Type (blended): every line of business is below goal",
                     "CSAT %", n_col="Feedback", height=2.6)

    qa_cr = K.qa_score_by_cr(a, top_n=8, min_n=3).head(8)
    chart_bar_status(qa_cr, "CR_Lv4", "QA_Score", config.QA_GOAL,
                     "bar_qa_by_cr.png",
                     "Lowest QA scores by contact reason (blended Phone + Chat)",
                     "QA score", n_col="N", width=6.8, height=3.8)

    # People cuts
    qa_bands = K.quartile_band_summary(K.qa_agent_quartiles(a, min_n=5))
    csat_bands = K.quartile_band_summary(K.csat_agent_quartiles(c, a, min_n=20))
    chart_quartiles(qa_bands, csat_bands, "quartiles.png")
    chart_supervisors(K.supervisor_overview(a, c, min_n=5), "supervisor_scatter.png")

    story = resolution_story(a, c)
    chart_cr_tree(story, "cr_subcr_tree.png")
    chart_fishbone("fishbone.png", story)
    chart_flowchart("flowchart.png")

    print(f"\nDone -> {OUT}")


if __name__ == "__main__":
    main()
