"""Editorial charts for the VP brief — identical canvas size, no tight-crop."""
from __future__ import annotations

import base64
import io
import re
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "DiDi_CX_Quality_Analyst_Business_Case.html"
OUT = ROOT / "brief_charts"

ORANGE = "#FF6600"
DARK = "#1A1A1A"
GREEN = "#2E9B57"
AMBER = "#F2A900"
RED = "#D64545"
BLUE = "#2E6FBE"
MUTED = "#6B6B6B"
LINE = "#E8E8E8"
GOAL = 85.0
RC_GOAL = 5.44

# Pair charts MUST share pixel size so CSS grid cells align.
PAIR = (5.55, 3.15)
FULL = (11.28, 3.35)
HBAR = (11.28, 3.55)
DPI = 160

plt.rcParams.update({
    "font.family": "Segoe UI",
    "font.size": 9,
    "axes.labelcolor": MUTED,
    "axes.edgecolor": "#D0D0D0",
    "axes.linewidth": 0.7,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.major.size": 0,
    "ytick.major.size": 0,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.grid": False,
    "legend.frameon": False,
    "legend.fontsize": 8,
})


def wrap(s: str, width: int = 28) -> str:
    return "\n".join(textwrap.wrap(str(s), width=width))


def new_fig(size):
    fig, ax = plt.subplots(figsize=size, dpi=DPI)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#D0D0D0")
    ax.spines["bottom"].set_color("#D0D0D0")
    return fig, ax


def panel(name: str, title: str, caption: str, fig) -> tuple[str, str]:
    """Fixed canvas — never bbox_inches='tight' (that is what broke alignment)."""
    fig.subplots_adjust(left=0.16, right=0.86, top=0.90, bottom=0.22)
    OUT.mkdir(exist_ok=True)
    path = OUT / f"{name}.png"
    kw = dict(dpi=DPI, facecolor="white", bbox_inches=None)
    fig.savefig(path, **kw)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", **kw)
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    html = (
        f'<figure class="panel">'
        f'<div class="panel-label">{title}</div>'
        f'<div class="panel-plot"><img src="data:image/png;base64,{b64}" alt="{title}" /></div>'
        f"<figcaption>{caption}</figcaption>"
        f"</figure>"
    )
    return name, html


def panel_hbar(name, title, caption, fig):
    fig.subplots_adjust(left=0.34, right=0.96, top=0.90, bottom=0.16)
    OUT.mkdir(exist_ok=True)
    path = OUT / f"{name}.png"
    kw = dict(dpi=DPI, facecolor="white", bbox_inches=None)
    fig.savefig(path, **kw)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", **kw)
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    html = (
        f'<figure class="panel">'
        f'<div class="panel-label">{title}</div>'
        f'<div class="panel-plot"><img src="data:image/png;base64,{b64}" alt="{title}" /></div>'
        f"<figcaption>{caption}</figcaption>"
        f"</figure>"
    )
    return name, html


def vbar(ax, labels, values, colors, ylabel, ymax, goal=None, goal_label=None, fmt="{:.2f}"):
    x = np.arange(len(labels))
    ax.bar(x, values, color=colors, width=0.44, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlim(-0.7, len(labels) - 0.3)
    ax.set_ylim(0, ymax)
    ax.set_ylabel(ylabel, fontsize=8)
    ax.yaxis.set_major_locator(MaxNLocator(5))
    if goal is not None:
        ax.axhline(goal, color=DARK, ls=(0, (4, 3)), lw=0.9, zorder=2)
        ax.annotate(
            goal_label,
            xy=(1, goal),
            xycoords=("axes fraction", "data"),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontsize=8,
            color=DARK,
            clip_on=False,
        )
    for i, v in enumerate(values):
        y_lab = v + ymax * 0.03
        if goal is not None and abs(v - goal) < ymax * 0.08:
            y_lab = max(v, goal) + ymax * 0.045
        ax.text(i, y_lab, fmt.format(v), ha="center", va="bottom",
                fontsize=9, fontweight="semibold", color=DARK)


def hbar(ax, labels, values, colors, xlabel, goal=None):
    y = np.arange(len(labels))
    ax.barh(y, values, color=colors, height=0.58, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels([wrap(l, 32) for l in labels], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel, fontsize=8)
    if goal is not None:
        ax.axvline(goal, color=DARK, ls=(0, (4, 3)), lw=0.9)
    xmax = max(values) * 1.18
    ax.set_xlim(0, xmax)
    for i, v in enumerate(values):
        label = f"{v:.1f}" if isinstance(v, float) and v < 200 else f"{int(v):,}"
        ax.text(v + xmax * 0.015, i, label, va="center", fontsize=8, color=DARK)


def exec_qa_csat():
    fig, ax = new_fig(PAIR)
    vbar(ax, ["QA Score", "CSAT"], [94.14, 79.95], [GREEN, RED],
         "Score", 110, goal=GOAL, goal_label="Goal 85")
    return panel(
        "exec_qa_csat",
        "QA and CSAT versus the 85 goal",
        "Official May snapshot. QA is +9.14 vs goal; CSAT is −5.05 (red).",
        fig,
    )


def exec_recontact():
    fig, ax = new_fig(PAIR)
    vbar(
        ax,
        ["Official\n12 channels", "Excl.\nSelf Help", "Phone +\nLive Chat"],
        [5.83, 15.19, 15.56],
        [AMBER, RED, RED],
        "Recontact rate (%)",
        20,
        goal=RC_GOAL,
        goal_label="Goal 5.44%",
        fmt="{:.2f}%",
    )
    return panel(
        "exec_recontact",
        "Recontact: official mix versus live",
        "Self Help (67% of contacts at 1.22%) holds the official rate near goal. Live channels are 15.56%.",
        fig,
    )


def weekly():
    fig, axes = plt.subplots(1, 2, figsize=FULL, dpi=DPI)
    weeks = ["W18", "W19", "W20", "W21", "W22"]
    qa = [np.nan, 92.4, 94.9, 94.2, 95.5]
    csat = [79.8, 79.2, 80.1, 81.0, 79.4]
    rc = [6.33, 6.04, 5.98, 5.81, 5.26]
    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#D0D0D0")
        ax.spines["bottom"].set_color("#D0D0D0")
    ax = axes[0]
    ax.plot(weeks, qa, "o-", color=GREEN, lw=1.8, ms=5.5, label="QA Score")
    ax.plot(weeks, csat, "o-", color=RED, lw=1.8, ms=5.5, label="CSAT")
    ax.axhline(GOAL, color=DARK, ls=(0, (4, 3)), lw=0.9)
    ax.set_ylim(74, 100)
    ax.set_ylabel("Score", fontsize=8)
    ax.legend(loc="lower right", ncol=2)
    ax = axes[1]
    ax.plot(weeks, rc, "o-", color=ORANGE, lw=1.8, ms=5.5, label="Recontact")
    ax.axhline(RC_GOAL, color=GREEN, ls=(0, (4, 3)), lw=0.9)
    ax.set_ylim(5.0, 6.8)
    ax.set_ylabel("Recontact %", fontsize=8)
    ax.legend(loc="upper right")
    fig.subplots_adjust(left=0.07, right=0.98, top=0.90, bottom=0.16, wspace=0.28)
    OUT.mkdir(exist_ok=True)
    kw = dict(dpi=DPI, facecolor="white", bbox_inches=None)
    fig.savefig(OUT / "weekly.png", **kw)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", **kw)
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    html = (
        '<figure class="panel">'
        '<div class="panel-label">Weekly trend — QA stays green; CSAT never clears 85; Recontact improves</div>'
        f'<div class="panel-plot"><img src="data:image/png;base64,{b64}" alt="Weekly trend" /></div>'
        "<figcaption>W18 has no QA audits. W22: QA 95.5, CSAT 79.4% (red), Recontact 5.26% (under goal).</figcaption>"
        "</figure>"
    )
    return "weekly", html


def channel_qa_csat():
    fig, ax = new_fig(PAIR)
    cats = ["Live Chat", "Phone"]
    x = np.arange(2)
    w = 0.34
    qa, csat = [96.01, 83.04], [77.55, 86.26]
    ax.bar(x - w / 2, qa, w, color=GREEN, label="QA Score", zorder=3)
    ax.bar(x + w / 2, csat, w, color=BLUE, label="CSAT", zorder=3)
    ax.axhline(GOAL, color=DARK, ls=(0, (4, 3)), lw=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(cats)
    ax.set_ylim(0, 112)
    ax.set_ylabel("Score", fontsize=8)
    ax.legend(loc="upper right", ncol=2)
    for i, v in enumerate(qa):
        ax.text(i - w / 2, v + 2, f"{v:.1f}", ha="center", fontsize=8, fontweight="semibold")
    for i, v in enumerate(csat):
        ax.text(i + w / 2, v + 2, f"{v:.1f}", ha="center", fontsize=8, fontweight="semibold")
    return panel(
        "channel_qa_csat",
        "Channel inversion — QA versus CSAT",
        "Chat passes the form and fails the customer. Phone is the reverse.",
        fig,
    )


def channel_rc():
    fig, ax = new_fig(PAIR)
    cats = ["Live Chat", "Phone"]
    x = np.arange(2)
    w = 0.34
    rc, fatal = [15.99, 13.47], [2.95, 13.52]
    ax.bar(x - w / 2, rc, w, color=ORANGE, label="Recontact %", zorder=3)
    ax.bar(x + w / 2, fatal, w, color=RED, label="Critical-fail audits %", zorder=3)
    ax.axhline(RC_GOAL, color=GREEN, ls=(0, (4, 3)), lw=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(cats)
    ax.set_ylim(0, 22)
    ax.set_ylabel("Rate (%)", fontsize=8)
    ax.legend(loc="upper right")
    return panel(
        "channel_rc",
        "Live recontact versus fatal QA rate",
        "Both channels miss 5.44%. Chat recontacts without fatal QA; Phone fatals at 13.5%.",
        fig,
    )


def qa_hist():
    fig, ax = new_fig(FULL)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.90, bottom=0.18)
    labels = ["0  (critical fail)", "70", "80", "90", "100"]
    vals = [110, 2, 21, 293, 2034]
    colors = [RED, MUTED, MUTED, BLUE, GREEN]
    ax.bar(labels, vals, color=colors, width=0.62, zorder=3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for x, v in zip(labels, vals):
        ax.text(x, v + 40, f"{v:,}", ha="center", fontsize=9, fontweight="semibold")
    ax.set_ylabel("Audits", fontsize=8)
    ax.set_ylim(0, 2350)
    OUT.mkdir(exist_ok=True)
    kw = dict(dpi=DPI, facecolor="white", bbox_inches=None)
    fig.savefig(OUT / "qa_hist.png", **kw)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", **kw)
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    html = (
        '<figure class="panel">'
        '<div class="panel-label">QA Score distribution — bimodal, not a mass at 94</div>'
        f'<div class="panel-plot"><img src="data:image/png;base64,{b64}" alt="QA histogram" /></div>'
        "<figcaption>n = 2,460. 82.7% score 100; 4.5% score 0. The 94.14 mean is not a typical agent.</figcaption>"
        "</figure>"
    )
    return "qa_hist", html


def _hbar_full(name, title, caption, labels, values, colors, xlabel, goal=None):
    fig, ax = new_fig(HBAR)
    hbar(ax, labels, values, colors, xlabel, goal=goal)
    return panel_hbar(name, title, caption, fig)


def phone_attrs():
    return _hbar_full(
        "phone_attrs",
        "Phone — top failing attributes",
        "n = 355. Time management is 64% of Phone fails. Complete and correct information is critical and zeros the audit.",
        ["Time management", "Complete and correct information (critical)", "User name"],
        [133, 28, 15],
        [ORANGE, RED, MUTED],
        "Fail count",
    )


def chat_attrs():
    return _hbar_full(
        "chat_attrs",
        "Live Chat — top failing attributes",
        "n = 2,105. Greeting is frequent, low impact. Service availability is the fatal Chat driver.",
        ["Greeting and identification", "Service attitude", "Service availability (critical)"],
        [96, 69, 46],
        [ORANGE, AMBER, RED],
        "Fail count",
    )


def qa_cr():
    return _hbar_full(
        "qa_cr",
        "Underperforming Contact reason Lv4 (detail) — QA, n ≥ 10",
        "Dashed line = goal 85. Highest-volume CRs (Incomplete / Inedible order) are green and omitted.",
        [
            "Order is active but customer already received it (n=12)",
            "Order appears completed, not received — full service (n=49)",
            "Refund status and conditions (n=25)",
            "Wrong order (n=20)",
        ],
        [65.8, 68.2, 76.4, 81.0],
        [RED, RED, RED, AMBER],
        "QA Score",
        goal=GOAL,
    )


def csat_stars():
    fig, ax = new_fig(PAIR)
    sizes = [58486, 3292, 1793, 942, 12753]
    colors = [GREEN, BLUE, AMBER, MUTED, RED]
    labels = ["5 Stars  75.7%", "4 Stars  4.3%", "3 Stars  2.3%", "2 Stars  1.2%", "1 Star  16.5%"]
    ax.pie(sizes, colors=colors, startangle=90,
           wedgeprops=dict(width=0.48, edgecolor="white", linewidth=1.4))
    ax.legend(labels, loc="center left", bbox_to_anchor=(0.98, 0.5), fontsize=8)
    ax.text(0, 0, "79.95%\nCSAT", ha="center", va="center", fontsize=11,
            fontweight="semibold", color=DARK)
    fig.subplots_adjust(left=0.02, right=0.62, top=0.92, bottom=0.08)
    OUT.mkdir(exist_ok=True)
    kw = dict(dpi=DPI, facecolor="white", bbox_inches=None)
    fig.savefig(OUT / "csat_stars.png", **kw)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", **kw)
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    html = (
        '<figure class="panel">'
        '<div class="panel-label">Star mix — a 1-star cliff, not 3-star drift</div>'
        f'<div class="panel-plot"><img src="data:image/png;base64,{b64}" alt="Star mix" /></div>'
        "<figcaption>Official CSAT = (4-star + 5-star) / 77,266. 12,753 surveys are 1-star.</figcaption>"
        "</figure>"
    )
    return "csat_stars", html


def csat_bt():
    fig, ax = new_fig(PAIR)
    labels = ["Food", "Full Service", "Market Place", "Other", "Pickup"]
    vals = [80.74, 79.67, 80.34, 26.52, 74.29]
    colors = [AMBER, RED, AMBER, RED, RED]
    y = np.arange(len(labels))
    ax.barh(y, vals, color=colors, height=0.58, zorder=3)
    ax.axvline(GOAL, color=DARK, ls=(0, (4, 3)), lw=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("CSAT (%)", fontsize=8)
    for i, v in enumerate(vals):
        ax.text(min(v + 1.5, 92), i, f"{v:.1f}", va="center", fontsize=8)
    fig.subplots_adjust(left=0.28, right=0.96, top=0.90, bottom=0.18)
    OUT.mkdir(exist_ok=True)
    kw = dict(dpi=DPI, facecolor="white", bbox_inches=None)
    fig.savefig(OUT / "csat_bt.png", **kw)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", **kw)
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    html = (
        '<figure class="panel">'
        '<div class="panel-label">CSAT by Business Type versus 85%</div>'
        f'<div class="panel-plot"><img src="data:image/png;base64,{b64}" alt="CSAT by Business Type" /></div>'
        "<figcaption>Food 46,071 surveys; Full Service 27,113. Other (n=558) is a taxonomy dump. Pickup n=35 is not a program.</figcaption>"
        "</figure>"
    )
    return "csat_bt", html


def csat_unsat():
    return _hbar_full(
        "csat_unsat",
        "Unsatisfied surveys by Contact reason Lv4 (detail)",
        "Red = CSAT miss (~67%). Grey = CSAT 88–89% — high volume, not the miss.",
        [
            "order status / delay info",
            "cancellation charge/debt",
            "order status & delays",
            "don't want the order",
            "refund status",
            "incomplete order",
        ],
        [3189, 1951, 1800, 1229, 1181, 874],
        [RED, RED, RED, MUTED, RED, MUTED],
        "Unsatisfied surveys",
    )


def voc():
    return _hbar_full(
        "voc",
        "VOC themes in negative comments",
        "2,749 tagged low-score comments. Customers talk about refund, no solution, and driver — outcome, not greeting.",
        [
            "Refund / compensation not received",
            "No solution provided",
            "Driver behavior",
            "Order / trip issues",
            "Long wait time",
            "Poor service",
        ],
        [754, 664, 435, 292, 237, 196],
        [ORANGE] * 6,
        "Mentions",
    )


def rc_scope():
    fig, ax = new_fig(FULL)
    fig.subplots_adjust(left=0.08, right=0.90, top=0.90, bottom=0.18)
    vbar(
        ax,
        ["All 12 channels  (official)", "Excluding Self Help", "Phone + Live Chat"],
        [5.83, 15.19, 15.56],
        [AMBER, RED, RED],
        "Recontact rate (%)",
        20,
        goal=RC_GOAL,
        goal_label="Goal 5.44%",
        fmt="{:.2f}%",
    )
    OUT.mkdir(exist_ok=True)
    kw = dict(dpi=DPI, facecolor="white", bbox_inches=None)
    fig.savefig(OUT / "rc_scope.png", **kw)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", **kw)
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    html = (
        '<figure class="panel">'
        '<div class="panel-label">Official 5.83% is Self Help dilution — live rate is 15.56%</div>'
        f'<div class="panel-plot"><img src="data:image/png;base64,{b64}" alt="Recontact scopes" /></div>'
        "<figcaption>Ratio of sums across 994,591 contacts. Rates are never averaged across rows.</figcaption>"
        "</figure>"
    )
    return "rc_scope", html


def rc_pareto():
    fig, ax = new_fig(FULL)
    labels = [
        "status / delay info",
        "order status & delays",
        "cancellation charge",
        "don't want the order",
        "incomplete order",
        "refund status",
        "cash antifraud",
    ]
    rec = np.array([13014, 7680, 6599, 6216, 4110, 2901, 1776], dtype=float)
    share = rec / rec.sum() * 100
    cum = np.cumsum(share)
    x = np.arange(len(labels))
    ax.bar(x, rec, color=ORANGE, width=0.62, zorder=3)
    ax.set_ylabel("Recontacts", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([wrap(l, 13) for l in labels], fontsize=8)
    ax2 = ax.twinx()
    ax2.spines["top"].set_visible(False)
    ax2.plot(x, cum, "o-", color=DARK, lw=1.5, ms=4.5)
    ax2.set_ylabel("Cumulative % of these 7", fontsize=8)
    ax2.set_ylim(0, 105)
    fig.subplots_adjust(left=0.08, right=0.92, top=0.90, bottom=0.22)
    OUT.mkdir(exist_ok=True)
    kw = dict(dpi=DPI, facecolor="white", bbox_inches=None)
    fig.savefig(OUT / "rc_pareto.png", **kw)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", **kw)
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    html = (
        '<figure class="panel">'
        '<div class="panel-label">Recontact volume — Contact reason Lv4 (detail)</div>'
        f'<div class="panel-plot"><img src="data:image/png;base64,{b64}" alt="Recontact Pareto" /></div>'
        "<figcaption>Top three status/charge reasons dominate. “don't want the order” is high count at a 2.20% rate (green) — not the recovery target.</figcaption>"
        "</figure>"
    )
    return "rc_pareto", html


def combined():
    fig, ax = new_fig(FULL)
    labels = ["order status\n& delays", "cancellation\ncharge/debt", "refund\nstatus", "courier\novercharged"]
    qa_vs = [12.3, 6.4, 13.4, 7.0]
    csat_vs = [-20.3, -17.6, -18.0, -10.4]
    rc_vs = [13.9, 7.52, 10.25, 3.43]
    x = np.arange(len(labels))
    w = 0.26
    ax.bar(x - w, qa_vs, w, color=GREEN, label="QA vs 85 (pp)", zorder=3)
    ax.bar(x, csat_vs, w, color=RED, label="CSAT vs 85% (pp)", zorder=3)
    ax.bar(x + w, rc_vs, w, color=ORANGE, label="Recontact vs 5.44% (pp)", zorder=3)
    ax.axhline(0, color=DARK, lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Points versus goal", fontsize=8)
    ax.legend(loc="lower left", ncol=3)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.18)
    OUT.mkdir(exist_ok=True)
    kw = dict(dpi=DPI, facecolor="white", bbox_inches=None)
    fig.savefig(OUT / "combined.png", **kw)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", **kw)
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    html = (
        '<figure class="panel">'
        '<div class="panel-label">Combined pattern: QA above goal, CSAT and Recontact below</div>'
        f'<div class="panel-plot"><img src="data:image/png;base64,{b64}" alt="Combined pattern" /></div>'
        "<figcaption>Distance to goal in percentage points. Same contact reasons pass the audit and fail the customer. Observable pattern, not proven causality.</figcaption>"
        "</figure>"
    )
    return "combined", html


def row(ids, charts):
    inner = "\n      ".join(charts[i] for i in ids)
    cls = "viz-row" if len(ids) == 2 else "viz-row single"
    return f'<div class="{cls}">\n      {inner}\n    </div>'


SLOTS = [
    ["exec_qa_csat", "exec_recontact"],
    ["weekly"],
    ["channel_qa_csat", "channel_rc"],
    ["qa_hist"],
    ["phone_attrs"],
    ["chat_attrs"],
    ["qa_cr"],
    ["csat_stars", "csat_bt"],
    ["csat_unsat"],
    ["voc"],
    ["rc_scope"],
    ["rc_pareto"],
    ["combined"],
]


def main():
    charts = dict([
        exec_qa_csat(),
        exec_recontact(),
        weekly(),
        channel_qa_csat(),
        channel_rc(),
        qa_hist(),
        phone_attrs(),
        chat_attrs(),
        qa_cr(),
        csat_stars(),
        csat_bt(),
        csat_unsat(),
        voc(),
        rc_scope(),
        rc_pareto(),
        combined(),
    ])

    html = HTML.read_text(encoding="utf-8")
    html = re.sub(r"<figure class=\"(?:chart|panel)\">.*?</figure>", "", html, flags=re.S)
    html = re.sub(r"\n[ \t]+\n", "\n", html)

    state = {"i": 0}

    def fill_viz(_match):
        idx = state["i"]
        state["i"] += 1
        if idx >= len(SLOTS):
            return _match.group(0)
        return row(SLOTS[idx], charts)

    html, n = re.subn(
        r'<div class="viz-row(?: single)?">\s*</div>',
        fill_viz,
        html,
    )
    HTML.write_text(html, encoding="utf-8")
    print("filled viz-rows", n, "expected", len(SLOTS), "used", state["i"])


if __name__ == "__main__":
    main()
