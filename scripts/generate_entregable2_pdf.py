"""
Entregable 2 — Weekly Performance Report (PDF)
Estructura exacta del Business Case DiDi + 7 herramientas de calidad integradas.
Sin DMAIC. Datos alineados al dashboard Streamlit.
"""

from __future__ import annotations

import json
import sys
import textwrap
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import CSAT_GOAL, QA_GOAL, RECONTACT_GOAL, CONTROL_TOTALS  # noqa: E402
from modules.data_loader import load_all_data  # noqa: E402
from modules.executive_engine import (  # noqa: E402
    build_executive_brief,
    combined_operational_analysis,
    csat_segmentation,
    generate_action_plan,
    qa_channel_breakdown,
)
from modules.kpis import (  # noqa: E402
    add_pareto_cumulative,
    channel_performance,
    cr_correlation_summary,
    cr_level_metrics,
    csat_by_business_type,
    qa_control_daily,
    qa_score_by_cr,
    qa_score_histogram,
    recontact_by_cr,
    recontact_rate,
    top_failing_attributes,
    voc_themes_negative,
)

OUT = ROOT / "entregable 2"
CHARTS = OUT / "charts"

C_ORANGE = "#FF6600"
C_DARK = "#1A1A1A"
C_WHITE = "#FFFFFF"
C_GREEN = "#2E9B57"
C_RED = "#D64545"
C_AMBER = "#F2A900"
C_BLUE = "#2E6FBE"
C_GRAY = "#666666"
C_LIGHT = "#F5F6F8"

PAGE_W, PAGE_H = A4
HEADER_H = 1.42 * cm
ORANGE_BAR_H = 0.09 * cm
SIDE_MARGIN = 1.6 * cm
TOP_MARGIN = 2.15 * cm
BOTTOM_MARGIN = 1.75 * cm

HEADER_LEFT = "DiDi Global — CX Service Operations  |  Internal Use Only"
HEADER_RIGHT = "Entregable 2 — Weekly Performance Report"
FOOTER_LEFT = "CONFIDENTIAL  ·  Internal Use Only"


def _register_brand_fonts() -> tuple[str, str]:
    segoe = Path(r"C:\Windows\Fonts\segoeui.ttf")
    segoe_bold = Path(r"C:\Windows\Fonts\segoeuib.ttf")
    if segoe.exists() and segoe_bold.exists():
        pdfmetrics.registerFont(TTFont("Brand", str(segoe)))
        pdfmetrics.registerFont(TTFont("Brand-Bold", str(segoe_bold)))
        return "Brand", "Brand-Bold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = _register_brand_fonts()

STATUS_HEX = {"green": C_GREEN, "amber": C_AMBER, "red": C_RED}

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
    "font.size": 10,
})


def vs_status(v: float, goal: float, higher: bool = True) -> str:
    d = v - goal if higher else goal - v
    if d >= 0:
        return "green"
    if d >= -5:
        return "amber"
    return "red"


def status_label(st: str) -> str:
    return {"green": "En meta", "amber": "Dentro de 5 pp", "red": "Fuera de meta (>5 pp)"}[st]


def save(fig, path: Path, dpi: int = 200):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _style_ax(ax, title, xlabel="", ylabel=""):
    ax.set_title(title, fontsize=12, fontweight="bold", loc="left", color=C_DARK, pad=10)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9, color=C_GRAY)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color=C_GRAY)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)


# ── Gráficas corregidas ───────────────────────────────────────────────────

def chart_kpi_vs_goal(qa, csat, rc, path: Path):
    metrics = [("QA Score", qa, QA_GOAL, True), ("CSAT %", csat, CSAT_GOAL, True), ("Recontact %", rc, RECONTACT_GOAL, False)]
    fig, ax = plt.subplots(figsize=(9, 3.8))
    names, vals, goals, cols = [], [], [], []
    for name, v, g, hib in metrics:
        names.append(name)
        vals.append(v)
        goals.append(g)
        cols.append(STATUS_HEX[vs_status(v, g, hib)])
    y = np.arange(len(names))
    ax.barh(y, vals, color=cols, height=0.55, edgecolor="white")
    for i, (v, g) in enumerate(zip(vals, goals)):
        ax.plot(g, i, marker="|", color=C_DARK, markersize=18, markeredgewidth=2)
        ax.text(v + 1, i, f"{v:.2f}", va="center", fontsize=10, fontweight="bold")
        ax.text(g, i - 0.32, f"Meta {g}", ha="center", fontsize=7, color=C_GRAY)
    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    _style_ax(ax, "Desempeño global vs meta contractual")
    save(fig, path)


def chart_channel_comparison(ch_perf: pd.DataFrame, path: Path):
    df = ch_perf[ch_perf["Segment"] != "Overall"].copy()
    if df.empty:
        return
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.8))
    specs = [
        ("QA Score", "QA_Score", QA_GOAL, True, C_GREEN),
        ("CSAT %", "CSAT_Score", CSAT_GOAL, True, C_BLUE),
        ("Recontact %", "Recontact_Rate", RECONTACT_GOAL, False, C_RED),
    ]
    for ax, (title, col, goal, hib, color) in zip(axes, specs):
        vals = df[col].tolist()
        segs = df["Segment"].tolist()
        bar_c = [STATUS_HEX[vs_status(v, goal, hib)] if pd.notna(v) else C_GRAY for v in vals]
        ax.bar(segs, vals, color=bar_c, width=0.55, edgecolor="white")
        ax.axhline(goal, color=C_DARK, linestyle="--", linewidth=1.2)
        ax.text(0.02, 0.95, f"Meta: {goal}", transform=ax.transAxes, fontsize=8, va="top")
        for i, v in enumerate(vals):
            if pd.notna(v):
                ax.text(i, v + 1, f"{v:.1f}", ha="center", fontsize=9)
        _style_ax(ax, title)
    fig.suptitle("Comparación Phone vs Live Chat", fontsize=13, fontweight="bold", x=0.02, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    save(fig, path)


def chart_pareto_attributes(errors, audits, path: Path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, ch in zip(axes, ["Phone", "Live Chat"]):
        sub_e = errors[errors["Channel"] == ch] if "Channel" in errors.columns else errors
        sub_a = audits[audits["Channel"] == ch]
        top = top_failing_attributes(sub_e, sub_a, top_n=6)
        if top.empty:
            ax.text(0.5, 0.5, "Sin datos", ha="center", va="center")
            ax.set_title(ch, fontweight="bold")
            continue
        p = add_pareto_cumulative(top, "Fail_Count")
        x = np.arange(len(p))
        ax.bar(x, p["Fail_Count"], color=C_ORANGE, width=0.6)
        ax2 = ax.twinx()
        ax2.plot(x, p["Cum_Pct"], "s-", color=C_DARK, linewidth=2, markersize=4)
        ax2.axhline(80, color=C_ORANGE, linestyle="--", alpha=0.6)
        ax2.set_ylim(0, 105)
        labels = [textwrap.fill(str(a), 14) for a in p["Error_Category"]]
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=6.5)
        _style_ax(ax, f"Pareto QA — {ch}", ylabel="Fallas")
        ax2.set_ylabel("Acum. %", fontsize=8)
    fig.suptitle("Herramienta 2 — Pareto: atributos con mayor concentración de defectos", fontsize=12, fontweight="bold", x=0.02, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    save(fig, path)


def chart_histogram_by_channel(audits, path: Path):
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.8), sharey=True)
    for ax, ch in zip(axes, ["Phone", "Live Chat"]):
        sub = audits[audits["Channel"] == ch]
        hist = qa_score_histogram(sub)
        if hist.empty:
            continue
        colors_b = [C_RED if s == 0 else C_BLUE for s in hist["QA_Score"]]
        ax.bar(hist["QA_Score"], hist["Audits"], width=8, color=colors_b, edgecolor="white")
        ax.axvline(QA_GOAL, color=C_GREEN, linestyle="--", linewidth=1.5)
        mean = sub["Score_Pct"].mean()
        ax.axvline(mean, color=C_DARK, linestyle=":", linewidth=1.2, label=f"Promedio {mean:.1f}")
        _style_ax(ax, f"{ch} (n={len(sub)})", "QA Score", "Auditorías")
        ax.legend(fontsize=7)
    fig.suptitle("Herramienta 3 — Histograma: distribución de QA Score por canal", fontsize=12, fontweight="bold", x=0.02, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.9])
    save(fig, path)


def chart_control_imr(audits, path: Path):
    """Carta I-MR correcta (igual que dashboard): panel I + panel MR."""
    df = qa_control_daily(audits)
    if df.empty or len(df) < 2:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, "Datos diarios insuficientes", ha="center")
        save(fig, path)
        return

    fig, (ax_i, ax_mr) = plt.subplots(2, 1, figsize=(10.5, 5.5), sharex=True, gridspec_kw={"height_ratios": [2.2, 1]})
    dates = pd.to_datetime(df["Date"])
    cl, ucl, lcl = df["CL"].iloc[0], df["UCL"].iloc[0], df["LCL"].iloc[0]

    pt_c = [C_RED if b else C_BLUE for b in df["Beyond_Limits"]]
    ax_i.plot(dates, df["Value"], color="#CCC", linewidth=1, zorder=1)
    ax_i.scatter(dates, df["Value"], c=pt_c, s=50, zorder=3, edgecolors="white", linewidth=0.8)
    ax_i.axhline(cl, color=C_DARK, linewidth=1.3, label=f"CL = {cl:.1f}")
    ax_i.axhline(ucl, color=C_RED, linestyle=":", linewidth=1.2, label=f"UCL = {ucl:.1f}")
    ax_i.axhline(lcl, color=C_RED, linestyle=":", linewidth=1.2, label=f"LCL = {lcl:.1f}")
    ax_i.axhline(QA_GOAL, color=C_GREEN, linestyle="--", linewidth=1.3, label=f"Meta QA = {QA_GOAL}")
    _style_ax(ax_i, "Herramienta 4 — Gráfico de control I-MR: QA Score diario", ylabel="QA Score")
    ax_i.legend(fontsize=7, loc="lower left", ncol=2)

    mr = df["MR"].iloc[1:]
    mr_dates = dates.iloc[1:]
    mr_bar = df["MR_bar"].iloc[0]
    mr_ucl = 3.267 * mr_bar if mr_bar else 0
    ax_mr.bar(mr_dates, mr, width=0.6, color=C_BLUE, alpha=0.8)
    ax_mr.axhline(mr_bar, color=C_DARK, linewidth=1.2, label=f"MR̄ = {mr_bar:.2f}")
    ax_mr.axhline(mr_ucl, color=C_RED, linestyle=":", linewidth=1.2, label=f"UCL-MR = {mr_ucl:.2f}")
    _style_ax(ax_mr, "Carta de rangos móviles (MR)", "Fecha", "|Δ| entre días")
    ax_mr.legend(fontsize=7, loc="upper right")
    fig.autofmt_xdate(rotation=30, ha="right")
    fig.text(0.08, 0.01, "Nota: punto rojo = variación especial del día. Estar dentro de límites ≠ cumplir meta 85.", fontsize=7.5, color=C_GRAY)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    save(fig, path)


def chart_csat_business_type(csat, path: Path):
    bt = csat_by_business_type(csat)
    bt = bt[bt["Feedback"] >= 20].sort_values("CSAT_Score")
    if bt.empty:
        return
    fig, ax = plt.subplots(figsize=(9, max(3, len(bt) * 0.55)))
    cols = [STATUS_HEX[vs_status(v, CSAT_GOAL)] for v in bt["CSAT_Score"]]
    ax.barh(bt["Business_Type"], bt["CSAT_Score"], color=cols, height=0.6)
    ax.axvline(CSAT_GOAL, color=C_GREEN, linestyle="--", linewidth=1.5, label=f"Meta {CSAT_GOAL}%")
    for _, r in bt.iterrows():
        ax.text(r["CSAT_Score"] + 0.5, r["Business_Type"], f"{r['CSAT_Score']:.1f}% (n={int(r['Feedback']):,})", va="center", fontsize=8)
    _style_ax(ax, "CSAT por Business Type (mín. 20 encuestas)", "CSAT %")
    ax.legend(fontsize=8)
    save(fig, path)


def chart_scatter_qa_csat(cr_df, path: Path):
    df = cr_df.dropna(subset=["QA_Score", "CSAT_Pct"]).copy()
    df = df[(df.get("Feedback", 0) >= 30) | (df.get("QA_N", 0) >= 5)]
    if len(df) < 4:
        return
    fig, ax = plt.subplots(figsize=(9, 5.5))
    size = np.clip(df.get("Feedback", pd.Series(50, index=df.index)).fillna(30) / 60, 25, 400)
    ax.scatter(df["QA_Score"], df["CSAT_Pct"], s=size, c=C_BLUE, alpha=0.65, edgecolors=C_DARK, linewidth=0.4)
    ax.axhline(CSAT_GOAL, color=C_GREEN, linestyle="--", linewidth=1.2, label=f"Meta CSAT {CSAT_GOAL}%")
    ax.axvline(QA_GOAL, color=C_GREEN, linestyle="--", linewidth=1.2, label=f"Meta QA {QA_GOAL}")
    ax.fill_between([QA_GOAL, 105], CSAT_GOAL, 105, alpha=0.06, color=C_GREEN, label="Cuadrante objetivo")
    worst = df.nsmallest(5, "CSAT_Pct")
    for _, r in worst.iterrows():
        ax.annotate(str(r["CR_Lv4"])[:24], (r["QA_Score"], r["CSAT_Pct"]), fontsize=6.5, xytext=(5, 5), textcoords="offset points",
                    arrowprops=dict(arrowstyle="-", color=C_GRAY, lw=0.6))
    summ = cr_correlation_summary(df.rename(columns={"CSAT_Pct": "CSAT_Pct", "Recontact_Rate": "Recontact_Rate"}))
    r_txt = ""
    if not summ.empty:
        row = summ[summ["Pair"] == "QA vs CSAT"]
        if len(row) and pd.notna(row.iloc[0]["Pearson_r"]):
            r_txt = f"Correlación Pearson r = {row.iloc[0]['Pearson_r']:.2f} (n={int(row.iloc[0]['N_CR'])} CRs)"
    _style_ax(ax, "Herramienta 5 — Dispersión QA vs CSAT por CR Lv4", "QA Score prom.", "CSAT %")
    ax.legend(fontsize=7, loc="lower right")
    if r_txt:
        ax.text(0.02, 0.02, r_txt, transform=ax.transAxes, fontsize=8, color=C_GRAY)
    save(fig, path)


def chart_pareto_recontact(rc, path: Path):
    g = recontact_by_cr(rc, top_n=8)
    if g.empty:
        return
    p = add_pareto_cumulative(g.rename(columns={"Recontacts": "Vol"}), "Vol")
    fig, ax = plt.subplots(figsize=(10, 4.2))
    x = np.arange(len(p))
    ax.bar(x, p["Vol"], color=C_ORANGE, width=0.65)
    ax2 = ax.twinx()
    ax2.plot(x, p["Cum_Pct"], "s-", color=C_DARK, linewidth=2)
    ax2.axhline(80, color=C_ORANGE, linestyle="--", alpha=0.7)
    labels = [textwrap.fill(str(c), 20) for c in p["CR_Lv4"]]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7)
    _style_ax(ax, "Pareto — CR Lv4 con mayor volumen de recontacto", ylabel="Recontactos")
    ax2.set_ylabel("Acumulado %", fontsize=9)
    save(fig, path)


def chart_combined_risk(combined, path: Path):
    df = combined.head(6).copy()
    if df.empty:
        return
    fig, ax = plt.subplots(figsize=(9, 4.5))
    y = np.arange(len(df))
    ax.barh(y, df["Impact_Score"].fillna(0), color=C_RED, alpha=0.75, height=0.55)
    ax.set_yticks(y)
    labels = [f"{str(r['CR_Lv4'])[:35]}\n{r['Pattern']}" for _, r in df.iterrows()]
    ax.set_yticklabels(labels, fontsize=7)
    ax.invert_yaxis()
    _style_ax(ax, "CR Lv4 con falla simultánea en 2+ KPIs (impacto operativo)", "Score de impacto")
    save(fig, path)


def chart_fishbone(path: Path):
    """Ishikawa legible — tabla visual de causa-efecto."""
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.text(0.2, 5.6, "Herramienta 6 — Ishikawa: por qué Order Status & Delays falla en los 3 KPIs", fontsize=12, fontweight="bold", color=C_DARK)

    effect = FancyBboxPatch((7.8, 2.2), 2.0, 1.6, boxstyle="round,pad=0.08", facecolor=C_ORANGE, edgecolor=C_DARK, lw=1.5)
    ax.add_patch(effect)
    ax.text(8.8, 3.0, "EFECTO\n\nBajo CSAT\nAlto Recontact\nQA Phone bajo\nen este cluster", ha="center", va="center", fontsize=8.5, color="white", fontweight="bold")

    ax.plot([0.8, 7.6], [3.0, 3.0], color=C_DARK, lw=2.5)

    cats = [
        (1.2, 4.8, "People", ["Coaching Phone\ninsuficiente", "Presión de AHT"]),
        (3.2, 4.8, "Process", ["Sin script FCR\npara status", "Cierre sin\nresolución"]),
        (5.2, 4.8, "Technology", ["Sin tracking\nen chat", "Info de entrega\nincompleta"]),
        (1.2, 1.2, "Policy", ["Reembolso\nconfuso", "Antifraud bloquea\ncompensación"]),
        (3.2, 1.2, "Measurement", ["QA mide script,\nno resolución", "CSAT no ligado\na FCR"]),
        (5.2, 1.2, "Environment", ["Alto volumen\nstatus/delay", "Mix Food +\nFull Service"]),
    ]
    for sx, sy, cat, causes in cats:
        ax.plot([sx, sx + 0.55], [sy, 3.0], color=C_ORANGE, lw=1.8)
        ax.add_patch(FancyBboxPatch((sx - 0.45, sy - 0.25), 1.0, 0.5, boxstyle="round,pad=0.04", facecolor=C_DARK))
        ax.text(sx, sy, cat, ha="center", va="center", fontsize=8, color="white", fontweight="bold")
        for i, c in enumerate(causes):
            t = (i + 1) / (len(causes) + 1)
            px = sx + t * 0.45
            py = sy + t * (3.0 - sy)
            ax.plot([px, px + 0.85], [py, py], color="#AAAAAA", lw=0.8)
            ax.add_patch(FancyBboxPatch((px + 0.85, py - 0.24), 1.15, 0.48, boxstyle="round,pad=0.03", facecolor="white", edgecolor="#BBBBBB"))
            ax.text(px + 1.42, py, c, ha="center", va="center", fontsize=6.5, color=C_DARK)

    save(fig, path)


def chart_flowchart(path: Path):
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.text(0.3, 9.6, "Herramienta 7 — Flujo: dónde se pierde la resolución en 1er contacto (FCR)", fontsize=12, fontweight="bold", color=C_DARK)

    steps = [
        (5, 8.8, "1. Cliente escribe/call\npor order status o delay", C_ORANGE, "white"),
        (5, 7.6, "2. Agente revisa\nherramientas de tracking", "#E8E8E8", C_DARK),
        (5, 6.4, "3. ¿Tiene info accionable\npara resolver hoy?", C_AMBER, C_DARK),
        (2.5, 5.0, "SÍ → Comunica ETA,\ncompensación o acción", C_GREEN, "white"),
        (7.5, 5.0, "NO → Respuesta genérica\n(esperar / confiar)", C_RED, "white"),
        (2.5, 3.6, "4a. Caso cerrado\nCSAT 4-5 · FCR OK", C_GREEN, "white"),
        (7.5, 3.6, "4b. Cliente recontacta\n(≈17% en estos CRs)", C_RED, "white"),
        (7.5, 2.2, "5. Segunda interacción\naún sin cierre", C_RED, "white"),
        (5, 0.9, "6. Impacto: CSAT ↓ · Recontact ↑ · QA Phone ↓", C_ORANGE, "white"),
    ]
    for x, y, txt, bg, tc in steps:
        w, h = (3.2 if "¿" not in txt else 2.8), 0.85
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.06", facecolor=bg, edgecolor=C_DARK, lw=1.2))
        ax.text(x, y, txt, ha="center", va="center", fontsize=7.5, color=tc, fontweight="bold" if bg == C_ORANGE else "normal")

    for (x1, y1, x2, y2) in [(5, 8.35, 5, 8.05), (5, 7.15, 5, 6.85), (4.2, 6.1, 2.8, 5.45), (5.8, 6.1, 7.2, 5.45),
                              (2.5, 4.55, 2.5, 4.05), (7.5, 4.55, 7.5, 4.05), (7.5, 3.15, 7.5, 2.65), (7.5, 1.75, 5.3, 1.35)]:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", color=C_DARK, lw=1.2))
    ax.text(4.0, 5.55, "SÍ", fontsize=9, color=C_GREEN, fontweight="bold")
    ax.text(5.6, 5.55, "NO", fontsize=9, color=C_RED, fontweight="bold")
    save(fig, path)


# ── Contexto de datos ─────────────────────────────────────────────────────

def load_context() -> dict:
    data = load_all_data()
    audits, errors, csat, rc = data["fact_audits"], data["fact_errors"], data["fact_csat"], data["fact_recontact"]
    summary = __import__("modules.kpis", fromlist=["kpi_summary"]).kpi_summary(audits, csat, rc)
    rc_rate = recontact_rate(rc)
    combined = combined_operational_analysis(audits, csat, rc)
    ch_break = qa_channel_breakdown(audits, errors)
    ch_perf = channel_performance(audits, csat, rc)
    top_attr = top_failing_attributes(errors, audits, top_n=8)
    rc_cr = recontact_by_cr(rc, top_n=10)
    voc = voc_themes_negative(csat, top_n=6)
    qa_worst_cr = qa_score_by_cr(audits, top_n=10)
    csat_worst = csat_segmentation(csat, top_n=8)
    cr_metrics = cr_level_metrics(audits, csat, rc)
    actions = generate_action_plan(combined, ch_perf, top_attr, rc_cr, summary, rc_rate)
    brief = build_executive_brief(summary, rc_rate, audits, errors, csat, rc, combined, ch_perf, top_attr, rc_cr, voc, actions)
    weeks = sorted(audits["Week"].dropna().unique())
    period = f"Semanas {weeks[0]}–{weeks[-1]}" if weeks else "Mayo 2025"
    return {
        "audits": audits, "errors": errors, "csat": csat, "rc": rc,
        "summary": summary, "rc_rate": rc_rate, "combined": combined,
        "ch_break": ch_break, "ch_perf": ch_perf, "top_attr": top_attr,
        "rc_cr": rc_cr, "voc": voc, "qa_worst_cr": qa_worst_cr,
        "csat_worst": csat_worst, "cr_metrics": cr_metrics,
        "actions": actions, "brief": brief, "period": period,
        "bt": csat_by_business_type(csat),
    }


def build_charts(ctx) -> dict[str, Path]:
    s, rc = ctx["summary"], ctx["rc_rate"]
    paths = {
        "kpi": CHARTS / "rpt_kpi_overview.png",
        "channel": CHARTS / "rpt_channel_compare.png",
        "pareto_attr": CHARTS / "rpt_pareto_attr.png",
        "hist": CHARTS / "rpt_histogram.png",
        "control": CHARTS / "rpt_control_imr.png",
        "csat_bt": CHARTS / "rpt_csat_business_type.png",
        "scatter": CHARTS / "rpt_scatter.png",
        "pareto_rc": CHARTS / "rpt_pareto_recontact.png",
        "combined": CHARTS / "rpt_combined_risk.png",
        "fishbone": CHARTS / "rpt_fishbone.png",
        "flow": CHARTS / "rpt_flowchart.png",
    }
    chart_kpi_vs_goal(s["qa_score"], s["csat"], rc, paths["kpi"])
    chart_channel_comparison(ctx["ch_perf"], paths["channel"])
    chart_pareto_attributes(ctx["errors"], ctx["audits"], paths["pareto_attr"])
    chart_histogram_by_channel(ctx["audits"], paths["hist"])
    chart_control_imr(ctx["audits"], paths["control"])
    chart_csat_business_type(ctx["csat"], paths["csat_bt"])
    chart_scatter_qa_csat(ctx["cr_metrics"], paths["scatter"])
    chart_pareto_recontact(ctx["rc"], paths["pareto_rc"])
    chart_combined_risk(ctx["combined"], paths["combined"])
    chart_fishbone(paths["fishbone"])
    chart_flowchart(paths["flow"])
    return paths


# ── PDF ───────────────────────────────────────────────────────────────────

class BrandedCanvas(pdfcanvas.Canvas):
    """Repeating header/footer on every page, with Page X of Y after layout."""

    def __init__(self, *args, period: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict] = []
        self._period = period

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_chrome(page_count)
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)

    def _draw_chrome(self, page_count: int):
        self.saveState()
        page_num = self._pageNumber

        self.setFillColor(colors.HexColor(C_DARK))
        self.rect(0, PAGE_H - HEADER_H, PAGE_W, HEADER_H, fill=1, stroke=0)
        self.setFillColor(colors.HexColor(C_ORANGE))
        self.rect(0, PAGE_H - HEADER_H - ORANGE_BAR_H, PAGE_W, ORANGE_BAR_H, fill=1, stroke=0)

        text_y = PAGE_H - HEADER_H / 2 - 3
        self.setFillColor(colors.HexColor(C_WHITE))
        self.setFont(FONT, 8)
        self.drawString(SIDE_MARGIN, text_y, HEADER_LEFT)
        self.setFont(FONT_BOLD, 8)
        self.drawRightString(PAGE_W - SIDE_MARGIN, text_y, HEADER_RIGHT)

        footer_line_y = 1.05 * cm
        self.setStrokeColor(colors.HexColor(C_ORANGE))
        self.setLineWidth(1.15)
        self.line(SIDE_MARGIN, footer_line_y, PAGE_W - SIDE_MARGIN, footer_line_y)

        self.setFillColor(colors.HexColor(C_DARK))
        self.setFont(FONT, 8)
        self.drawString(SIDE_MARGIN, 0.52 * cm, FOOTER_LEFT)
        if self._period:
            self.setFillColor(colors.HexColor(C_GRAY))
            self.setFont(FONT, 7.5)
            self.drawCentredString(PAGE_W / 2, 0.52 * cm, str(self._period))
        self.setFillColor(colors.HexColor(C_DARK))
        self.setFont(FONT, 8)
        self.drawRightString(PAGE_W - SIDE_MARGIN, 0.52 * cm, f"Page {page_num} of {page_count}")
        self.restoreState()


def _canvas_maker(period: str):
    class _Canvas(BrandedCanvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, period=period, **kwargs)

    return _Canvas


def _img(path: Path, w=16 * cm):
    return Image(str(path), width=w, height=w * 0.42) if path.exists() else Spacer(1, 0.1 * cm)


def _table(data, col_w, header=C_DARK):
    t = Table(data, colWidths=col_w)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(C_WHITE)),
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("FONTNAME", (0, 1), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(C_LIGHT)]),
    ]))
    return t


def _status_cell(table, row, col, st):
    table.setStyle(TableStyle([
        ("BACKGROUND", (col, row), (col, row), colors.HexColor(STATUS_HEX.get(st, C_GRAY))),
        ("TEXTCOLOR", (col, row), (col, row), colors.HexColor(C_WHITE)),
        ("FONTNAME", (col, row), (col, row), FONT_BOLD),
    ]))


def build_lob_actions(ctx) -> list[list[str]]:
    """Planes explícitos por LOB — qué, quién, cuándo."""
    bt = ctx["bt"]
    rows = []
    lob_map = {
        "Food": "Food",
        "Full Service": "Full Service",
        "Market Place": "Market Place",
        "Pickup": "Pickup",
    }
    for lob_key, lob_name in lob_map.items():
        sub = bt[bt["Business_Type"].str.contains(lob_key, case=False, na=False)] if not bt.empty else pd.DataFrame()
        cs = sub.iloc[0]["CSAT_Score"] if not sub.empty else np.nan
        st = vs_status(cs, CSAT_GOAL) if pd.notna(cs) else "amber"
        if lob_key == "Food":
            rows.append([lob_name,
                f"CSAT {cs:.1f}% ({status_label(st)})" if pd.notna(cs) else "CSAT por revisar",
                "Coaching Phone en Time management e Información completa; ampliar cobertura de auditoría Phone",
                "QA Lead + Training", "Semanas 1–2"])
        elif lob_key == "Full Service":
            rows.append([lob_name,
                f"CSAT {cs:.1f}% ({status_label(st)})" if pd.notna(cs) else "CSAT por revisar",
                "Pilot de widget de tracking en Live Chat; macros de compensación para 'order not received'",
                "Product + Ops + QA Content", "Semanas 2–4"])
        elif lob_key == "Market Place":
            rows.append([lob_name,
                f"CSAT {cs:.1f}% ({status_label(st)})" if pd.notna(cs) else "CSAT por revisar",
                "Separar scripts marketplace vs full service; capacitar en responsabilidades store vs plataforma",
                "LOB Lead + Training", "Semanas 2–3"])
        else:
            rows.append([lob_name,
                f"CSAT {cs:.1f}% ({status_label(st)})" if pd.notna(cs) else "Volumen bajo",
                "Auditoría de CR pick-up at store; revisar si el flujo CSAT aplica correctamente",
                "LOB Lead", "Semana 2"])
    rows.append(["Todos (CX Leadership)",
        f"Recontact {ctx['rc_rate']:.2f}% vs meta {RECONTACT_GOAL}%",
        "War room semanal en top 3 CRs de recontacto hasta estabilizar ≤ meta; reporte semanal a VP",
        "Director Service Ops", "Semana 1 — ongoing"])
    rows.append(["Todos (Analytics)",
        "Brecha QA global vs Phone",
        "Publicar QA por canal en el dashboard ejecutivo — no solo promedio global",
        "QA Analyst + BI", "Semana 1"])
    return rows


def build_pdf(ctx, charts, out: Path):
    s, rc, brief = ctx["summary"], ctx["rc_rate"], ctx["brief"]
    qa_st, cs_st, rc_st = vs_status(s["qa_score"], QA_GOAL), vs_status(s["csat"], CSAT_GOAL), vs_status(rc, RECONTACT_GOAL, False)

    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=SIDE_MARGIN,
        rightMargin=SIDE_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
    )
    styles = getSampleStyleSheet()
    H1 = ParagraphStyle(
        "H1", parent=styles["Heading1"], fontName=FONT_BOLD,
        textColor=colors.HexColor(C_ORANGE), fontSize=15, spaceAfter=8, spaceBefore=2, leading=18,
    )
    H2 = ParagraphStyle(
        "H2", parent=styles["Heading2"], fontName=FONT_BOLD,
        textColor=colors.HexColor(C_DARK), fontSize=11, spaceAfter=6, spaceBefore=10, leading=14,
    )
    Body = ParagraphStyle(
        "Body", parent=styles["Normal"], fontName=FONT,
        fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=6,
        textColor=colors.HexColor(C_DARK),
    )
    Bullet = ParagraphStyle("Bullet", parent=Body, leftIndent=14, bulletIndent=0, spaceAfter=4)
    Small = ParagraphStyle("Small", parent=Body, fontSize=8, textColor=colors.HexColor(C_GRAY), leading=11)
    CoverKicker = ParagraphStyle("CoverKicker", fontName=FONT, alignment=TA_CENTER, fontSize=11, textColor=colors.HexColor(C_GRAY), spaceAfter=4)
    CoverTitle = ParagraphStyle("CoverTitle", fontName=FONT_BOLD, alignment=TA_CENTER, fontSize=24, textColor=colors.HexColor(C_ORANGE), leading=28, spaceAfter=6)
    CoverSub = ParagraphStyle("CoverSub", fontName=FONT, alignment=TA_CENTER, fontSize=12, textColor=colors.HexColor(C_DARK), spaceAfter=4)
    CoverMeta = ParagraphStyle("CoverMeta", fontName=FONT, alignment=TA_CENTER, fontSize=10, textColor=colors.HexColor(C_GRAY), spaceAfter=3)

    story = []

    # Portada — header/footer already identify the document on this page too
    story.append(Spacer(1, 1.8 * cm))
    story.append(Paragraph("DiDi Global — CX Service Operations", CoverKicker))
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph("Weekly Performance Report", CoverTitle))
    story.append(Paragraph("Entregable 2 — Business Case CX Quality Analyst", CoverSub))
    story.append(Paragraph(ctx["period"], CoverMeta))
    story.append(Paragraph(datetime.now().strftime("%d %B %Y") + "  ·  CONFIDENTIAL  ·  Internal Use Only", CoverMeta))
    story.append(PageBreak())

    # ── 1 Executive Summary ──
    story.append(Paragraph("1. Executive Summary", H1))
    kpi_data = [
        ["Métrica", "Resultado", "Meta", "Brecha", "Estado"],
        ["QA Score", f"{s['qa_score']:.2f}", str(QA_GOAL), f"{s['qa_score']-QA_GOAL:+.2f} pts", status_label(qa_st)],
        ["CSAT", f"{s['csat']:.2f}%", f"{CSAT_GOAL}%", f"{s['csat']-CSAT_GOAL:+.2f} pp", status_label(cs_st)],
        ["Recontact Rate", f"{rc:.2f}%", f"{RECONTACT_GOAL}%", f"{rc-RECONTACT_GOAL:+.2f} pp", status_label(rc_st)],
    ]
    kt = _table(kpi_data, [3 * cm, 2.5 * cm, 2 * cm, 2.5 * cm, 3.5 * cm])
    _status_cell(kt, 1, 4, qa_st)
    _status_cell(kt, 2, 4, cs_st)
    _status_cell(kt, 3, 4, rc_st)
    story.append(kt)
    story.append(Spacer(1, 0.3 * cm))
    story.append(_img(charts["kpi"]))

    phone = ctx["ch_break"].get("Phone", {})
    chat = ctx["ch_break"].get("Live Chat", {})
    story.append(Paragraph(
        f"Durante {ctx['period']} se evaluaron {CONTROL_TOTALS['evaluations']:,} interacciones QA, "
        f"se recibieron {CONTROL_TOTALS['surveys']:,} encuestas CSAT y se registraron {CONTROL_TOTALS['contacts']:,} contactos "
        f"({ctx['rc']['Recontact Volume'].sum():,.0f} recontactos). "
        f"<b>QA Score global: {s['qa_score']:.2f}</b> — {status_label(qa_st)} (meta {QA_GOAL}). "
        f"<b>CSAT: {s['csat']:.2f}%</b> — {status_label(cs_st)} (meta {CSAT_GOAL}%). "
        f"<b>Recontact: {rc:.2f}%</b> — {status_label(rc_st)} (meta {RECONTACT_GOAL}%).",
        Body,
    ))
    story.append(Paragraph(
        f"La aparente salud del QA global ({s['qa_score']:.1f}%) oculta una brecha en <b>Phone ({phone.get('qa_score', '—')}%</b>, "
        f"{phone.get('qa_vs', 0):+.1f} pts vs meta), mientras Live Chat supera ampliamente ({chat.get('qa_score', '—')}%). "
        f"Paradójicamente, Phone tiene mejor CSAT ({ctx['ch_perf'][ctx['ch_perf']['Segment']=='Phone']['CSAT_Score'].iloc[0]:.1f}% estimado) "
        f"que Live Chat, que concentra el 72% del feedback y arrastra el CSAT global.",
        Body,
    ))
    story.append(Paragraph(
        f"<b>Hallazgo crítico para liderazgo:</b> el cluster de motivos de contacto "
        f"<i>order status & delays / user request order status / cancellation charge</i> concentra ~42% de los recontactos, "
        f"CSAT 64–68% y volumen masivo de VOC negativo — pese a QA verde en Live Chat (95–97). "
        f"El problema no es cumplimiento de script auditado, sino <b>resolución en primera interacción (FCR)</b>. "
        f"Acción inmediata: war room en esos 3 CRs + coaching Phone + herramientas de tracking en chat.",
        Body,
    ))
    story.append(PageBreak())

    # ── 2 QA by Channel ──
    story.append(Paragraph("2. QA Analysis — by Channel", H1))
    story.append(_img(charts["channel"]))
    ch_rows = [["Canal", "QA Score", "Audits", "Critical fails", "Estado", "Interpretación"]]
    for ch in ["Phone", "Live Chat"]:
        info = ctx["ch_break"].get(ch, {})
        top_a = info.get("top_attrs", pd.DataFrame())
        top_name = top_a.iloc[0]["Error_Category"] if not top_a.empty else "—"
        interp = f"Top fail: {top_name}" if ch == "Phone" else "Score alto; fails en saludo/actitud"
        st = info.get("qa_status", "neutral")
        ch_rows.append([
            ch, f"{info.get('qa_score', '—')}", str(info.get("audit_count", "—")),
            str(info.get("n_crit_fails", "—")), status_label(st) if st != "neutral" else "—", interp,
        ])
    story.append(_table(ch_rows, [2.2 * cm, 2 * cm, 1.8 * cm, 2 * cm, 2.5 * cm, 4 * cm]))

    story.append(Paragraph("<b>2.1 Phone</b>", H2))
    story.append(Paragraph(
        f"Phone registra QA {phone.get('qa_score', '—')}% ({status_label(phone.get('qa_status', 'amber'))}). "
        f"El atributo dominante es <b>Time management</b> (≈37% fail rate), seguido de "
        f"<b>Complete and correct information</b> (Critical, ≈8%). Hipótesis: presión de AHT en llamadas complejas "
        f"(entrega no recibida, reembolsos) compromete calidad informativa y compensaciones.",
        Body,
    ))
    story.append(Paragraph("<b>2.2 Live Chat</b>", H2))
    story.append(Paragraph(
        f"Live Chat: QA {chat.get('qa_score', '—')}% ({status_label(chat.get('qa_status', 'green'))}) en "
        f"{chat.get('audit_count', '—')} auditorías. Top fails no críticos: Greeting, Service attitude, Service availability (Critical). "
        f"A pesar del score alto, el cliente llega frustrado por demoras — el QA mide protocolo, no resolución.",
        Body,
    ))
    story.append(_img(charts["pareto_attr"]))
    story.append(_img(charts["hist"]))
    story.append(PageBreak())

    # ── 3 QA by CR Lv4 ──
    story.append(Paragraph("3. QA Analysis — by CR Lv4", H1))
    story.append(Paragraph(
        "Ranking de CR Lv4 con peor QA (mínimo 3 auditorías). Los underperformers se concentran en "
        "entrega no recibida, pedido activo ya entregado y compensaciones.",
        Body,
    ))
    cr_rows = [["CR Lv4", "QA Score", "Audits", "Estado", "Hipótesis root cause"]]
    for _, r in ctx["qa_worst_cr"].head(8).iterrows():
        hyp = "Falla Critical: info/compensación incorrecta" if r["QA_Score"] < 80 else "Casos complejos de entrega/reembolso"
        cr_rows.append([str(r["CR_Lv4"])[:40], f"{r['QA_Score']:.1f}", str(int(r["N"])), status_label(r["status"]), hyp])
    story.append(_table(cr_rows, [4.5 * cm, 2 * cm, 1.5 * cm, 2.5 * cm, 4 * cm]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(_img(charts["control"]))
    story.append(PageBreak())

    # ── 4 CSAT / VOC ──
    story.append(Paragraph("4. CSAT / VOC Analysis", H1))
    story.append(Paragraph(
        f"CSAT global <b>{s['csat']:.2f}%</b> — {status_label(cs_st)}. "
        f"Live Chat: {ctx['ch_perf'][ctx['ch_perf']['Segment']=='Live Chat']['CSAT_Score'].iloc[0]:.1f}%. "
        f"Phone: {ctx['ch_perf'][ctx['ch_perf']['Segment']=='Phone']['CSAT_Score'].iloc[0]:.1f}%.",
        Body,
    ))
    story.append(_img(charts["csat_bt"]))
    cs_rows = [["CR Lv4 / Dimensión", "CSAT %", "Encuestas", "Estado"]]
    if not ctx["csat_worst"].empty:
        for _, r in ctx["csat_worst"].head(8).iterrows():
            st = vs_status(r["CSAT_Score"], CSAT_GOAL)
            cs_rows.append([f"{r.get('Dimension','')} — {str(r.get('Segment',''))[:30]}", f"{r['CSAT_Score']:.1f}%", str(int(r["Feedback"])), status_label(st)])
    story.append(_table(cs_rows, [6 * cm, 2 * cm, 2.5 * cm, 3 * cm]))

    story.append(Paragraph("<b>Voice of the Customer — qué dicen los clientes insatisfechos:</b>", H2))
    voc_rows = [["Tema VOC", "% menciones", "Qué significa operativamente"]]
    voc_meaning = {
        "No resolution / wait": "Cliente no recibe solución concreta — solo 'espere'",
        "Refund / compensation not received": "Compensación prometida no llega — desconfianza",
        "Other": "Comentarios genéricos — requiere revisión cualitativa",
    }
    for _, r in ctx["voc"].iterrows():
        theme = str(r.get("Theme", ""))
        voc_rows.append([theme, f"{r.get('Pct', 0):.1f}%", voc_meaning.get(theme, "Driver de insatisfacción")])
    story.append(_table(voc_rows, [4 * cm, 2.5 * cm, 7 * cm]))

    story.append(Paragraph("<b>Correlación QA ↔ CSAT:</b> en CRs de alto volumen operacional, QA alto no garantiza CSAT alto — "
                           "el cliente valora resolución, no solo cumplimiento de script.", Body))
    story.append(_img(charts["scatter"]))
    story.append(PageBreak())

    # ── 5 Recontact ──
    story.append(Paragraph("5. Recontact Analysis", H1))
    story.append(Paragraph(
        f"Tasa global <b>{rc:.2f}%</b> — {status_label(rc_st)} (meta ≤{RECONTACT_GOAL}%). "
        f"Live Chat audited rate ≈16%; Phone ≈13%. Un recontacto alto indica falla de FCR.",
        Body,
    ))
    rc_rows = [["CR Lv4", "Recontact vol.", "Contactos", "Rate %", "Estado"]]
    for _, r in ctx["rc_cr"].head(8).iterrows():
        st = vs_status(r["Recontact_Rate"], RECONTACT_GOAL, False)
        rc_rows.append([str(r["CR_Lv4"])[:38], f"{int(r['Recontacts']):,}", f"{int(r['Contacts']):,}", f"{r['Recontact_Rate']:.2f}%", status_label(st)])
    story.append(_table(rc_rows, [4.5 * cm, 2.5 * cm, 2.5 * cm, 2 * cm, 2.8 * cm]))
    story.append(Paragraph(
        "<b>Relación Recontact–QA–CSAT:</b> los CRs con mayor recontacto (order status, refund, cancellation charge) "
        "presentan simultáneamente CSAT rojo. QA en Live Chat para esos CRs es verde (95–98) — "
        "confirma que el problema es resolución/FCR, no auditoría de script.",
        Body,
    ))
    story.append(_img(charts["pareto_rc"]))
    story.append(PageBreak())

    # ── 6 Combined ──
    story.append(Paragraph("6. Combined Analysis", H1))
    if not ctx["combined"].empty:
        row = ctx["combined"].iloc[0]
        story.append(Paragraph(
            f"<b>Insight integrado — {row['CR_Lv4']}:</b> {row['Pattern']}. "
            f"QA {row.get('QA_Score', float('nan')):.1f}% ({row.get('QA_vs', 0):+.1f} pts) · "
            f"CSAT {row.get('CSAT_Score', float('nan')):.1f}% ({row.get('CSAT_vs', 0):+.1f} pts) · "
            f"Recontact {row.get('Recontact_Rate', float('nan')):.2f}% ({row.get('RC_vs', 0):+.2f} pp).",
            Body,
        ))
    story.append(Paragraph(
        "Cuantificación del cluster Order Status/Delay: los 3 CRs principales representan "
        f"≈{int(ctx['rc_cr'].head(3)['Recontacts'].sum()):,} recontactos "
        f"({ctx['rc_cr'].head(3)['Recontacts'].sum()/ctx['rc']['Recontact Volume'].sum()*100:.0f}% del total). "
        "Hipótesis: agentes cumplen script auditado pero no tienen visibilidad operativa (tracking, compensación automática) "
        "para cerrar el caso en la primera interacción.",
        Body,
    ))
    story.append(_img(charts["combined"]))
    story.append(_img(charts["fishbone"]))
    story.append(_img(charts["flow"]))
    story.append(PageBreak())

    # ── 7 Action Plans ──
    story.append(Paragraph("7. Action Plans — by LOB / Business Type", H1))
    story.append(Paragraph(
        "Cada fila indica <b>qué cambiar</b>, <b>quién actúa</b> y <b>cuándo</b>. "
        "Prioridad: estabilizar CSAT y Recontact sin degradar QA global.",
        Body,
    ))
    lob_rows = [["LOB", "Hallazgo", "Qué cambiar (acción concreta)", "Responsable", "Plazo"]] + build_lob_actions(ctx)
    story.append(_table(lob_rows, [2 * cm, 3 * cm, 5.5 * cm, 2.8 * cm, 2.2 * cm]))

    story.append(Paragraph("<b>Acciones adicionales del motor analítico:</b>", H2))
    for item in ctx["actions"][:4]:
        story.append(Paragraph(f"• <b>{item.owner}</b> ({item.timeline}, {item.priority}): {item.action}", Bullet))

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Anexo — 7 Herramientas de calidad usadas en este reporte", H2))
    tools = [
        ["1", "Check Sheet", "Validación de reglas QA y totales oficiales"],
        ["2", "Pareto", "Atributos QA (Phone/Chat) y CRs de recontacto"],
        ["3", "Histograma", "Distribución QA Score por canal"],
        ["4", "Control Chart I-MR", "Variación diaria QA vs meta y límites"],
        ["5", "Scatter", "QA vs CSAT por CR Lv4"],
        ["6", "Ishikawa", "Causa-raíz cluster Order Status"],
        ["7", "Flowchart", "Punto de falla FCR"],
    ]
    story.append(_table([["#", "Herramienta", "Dónde se aplicó"]] + tools, [1 * cm, 3.5 * cm, 10 * cm]))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Supuestos: CR Lv4 = CR_correcta fillna CR_registrada · valor 2 (N/A) excluido del QA · "
        "Phone cols W–AH / Live Chat cols AI–AP · KPIs = ratio of sums (alineado dashboard y control totals).",
        Small,
    ))

    doc.build(story, canvasmaker=_canvas_maker(ctx.get("period", "")))


def main():
    OUT.mkdir(exist_ok=True)
    ctx = load_context()
    charts = build_charts(ctx)
    pdf = OUT / "Entregable_2_Weekly_Performance_Report_longform.pdf"
    build_pdf(ctx, charts, pdf)
    meta = {
        "generated": datetime.now().isoformat(),
        "pdf": str(pdf),
        "structure": "Business Case Deliverable 2 (no DMAIC)",
        "kpis": {"qa": ctx["summary"]["qa_score"], "csat": ctx["summary"]["csat"], "recontact": ctx["rc_rate"]},
        "charts": {k: str(v) for k, v in charts.items()},
    }
    (OUT / "report_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"PDF generado: {pdf}")


if __name__ == "__main__":
    main()
