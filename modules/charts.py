"""
Gráficos Plotly — títulos y ejes en español, diseño claro para no expertos.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import (
    CSAT_GOAL,
    DIDI_DARK,
    DIDI_ORANGE,
    DIDI_WHITE,
    QA_GOAL,
    RECONTACT_GOAL,
    STATUS_COLORS,
)

__all__ = [
    "qa_trend_by_week",
    "fatal_rate_by_week",
    "qa_by_channel",
    "pareto_simple",
    "agents_below_goal",
    "qa_by_cr",
    "csat_by_channel",
    "csat_by_cr",
    "recontact_by_cr",
    "supervisor_scores",
    "correlation_heatmap",
    "scatter_kpi",
]


def apply_theme(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        font=dict(family="Inter, Segoe UI, sans-serif", color=DIDI_DARK, size=13),
        plot_bgcolor=DIDI_WHITE,
        paper_bgcolor=DIDI_WHITE,
        margin=dict(l=56, r=40, t=72, b=56),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="left", x=0),
    )
    fig.update_xaxes(gridcolor="#F1F5F9", linecolor="#E2E8F0", title_font=dict(size=13))
    fig.update_yaxes(gridcolor="#F1F5F9", linecolor="#E2E8F0", title_font=dict(size=13))
    return fig


def qa_trend_by_week(trends: pd.DataFrame) -> go.Figure:
    """Evolución del score QA semana a semana."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trends["Week"], y=trends["QA_Score"],
        mode="lines+markers+text",
        name="Score QA",
        line=dict(color=DIDI_ORANGE, width=3),
        marker=dict(size=10),
        text=trends["QA_Score"].round(1),
        textposition="top center",
    ))
    fig.add_hline(y=QA_GOAL, line_dash="dash", line_color=STATUS_COLORS["green"],
                  annotation_text=f"Meta: {QA_GOAL}")
    fig.update_layout(
        title="¿Cómo evoluciona la calidad semana a semana?",
        xaxis_title="Semana",
        yaxis_title="Score QA (0–100)",
        yaxis=dict(range=[max(0, trends["QA_Score"].min() - 10), 105]),
    )
    return apply_theme(fig, height=400)


def fatal_rate_by_week(trends: pd.DataFrame) -> go.Figure:
    """Errores críticos por semana."""
    fig = go.Figure(go.Bar(
        x=trends["Week"], y=trends["Fatal_Rate"],
        marker_color=STATUS_COLORS["red"], opacity=0.85,
        text=trends["Fatal_Rate"].round(1),
        texttemplate="%{text}%",
        textposition="outside",
    ))
    fig.update_layout(
        title="¿Qué % de llamadas/chats tuvo un error crítico?",
        xaxis_title="Semana",
        yaxis_title="% con error crítico",
    )
    return apply_theme(fig, height=380)


def qa_by_channel(audits: pd.DataFrame) -> go.Figure:
    g = audits.groupby("Channel").agg(Score=("Score_Pct", "mean"), Audits=("Audit_ID", "count")).reset_index()
    g["Score"] = g["Score"].round(1)
    colors = [STATUS_COLORS["green"] if s >= QA_GOAL else STATUS_COLORS["red"] for s in g["Score"]]
    fig = go.Figure(go.Bar(
        x=g["Channel"], y=g["Score"], marker_color=colors,
        text=g["Score"], texttemplate="%{text}", textposition="outside",
    ))
    fig.add_hline(y=QA_GOAL, line_dash="dash", line_color=STATUS_COLORS["green"],
                  annotation_text=f"Meta {QA_GOAL}")
    fig.update_layout(
        title="Score QA por canal (Phone vs Live Chat)",
        xaxis_title="Canal",
        yaxis_title="Score QA promedio",
        yaxis=dict(range=[0, 105]),
    )
    return apply_theme(fig, height=380)


def pareto_simple(pareto: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Pareto clásico vertical — barras azules + línea acumulada al 100%."""
    from modules.kpis import pareto_for_display

    if pareto.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sin datos de errores", showarrow=False)
        return apply_theme(fig)

    df = pareto_for_display(pareto, top_n)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=df["Error_Category"], y=df["Cantidad"], name="Frecuencia",
               marker_color="#1B2A4A", text=df["Cantidad"], textposition="outside"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=df["Error_Category"], y=df["Acumulado_Pct"], name="% Acumulado",
                   mode="lines+markers", line=dict(color=DIDI_ORANGE, width=2.5),
                   marker=dict(size=8, symbol="square", color=DIDI_ORANGE)),
        secondary_y=True,
    )
    fig.update_xaxes(title="Atributo", tickangle=-25)
    fig.update_yaxes(title="Número de fallas", secondary_y=False)
    fig.update_yaxes(title="% Acumulado", secondary_y=True, range=[0, 105], ticksuffix="%")
    fig.update_layout(title="Diagrama de Pareto — Errores más frecuentes",
                      legend=dict(orientation="h", y=1.12))
    return apply_theme(fig, height=420)


def correlation_heatmap(corr: pd.DataFrame) -> go.Figure:
    labels = {"QA_Score": "Score QA", "CSAT_Pct": "CSAT %", "FCR_Pct": "FCR %",
              "Recontact_Rate": "Recontacto %"}
    if corr.empty:
        fig = go.Figure()
        fig.add_annotation(text="Datos insuficientes", showarrow=False)
        return apply_theme(fig)
    corr = corr.rename(index=labels, columns=labels)
    fig = px.imshow(corr, text_auto=".2f", aspect="auto",
                    color_continuous_scale=[[0, DIDI_DARK], [0.5, "#FFF"], [1, DIDI_ORANGE]],
                    zmin=-1, zmax=1)
    fig.update_layout(title="Correlación entre métricas (por motivo de contacto)")
    return apply_theme(fig, height=360)


def scatter_kpi(df: pd.DataFrame, x: str, y: str, x_title: str, y_title: str, title: str) -> go.Figure:
    if df.empty or len(df) < 3:
        fig = go.Figure()
        fig.add_annotation(text="Datos insuficientes para este análisis", showarrow=False)
        return apply_theme(fig)
    fig = px.scatter(
        df, x=x, y=y, hover_name="CR_Lv4", size="QA_N" if "QA_N" in df.columns else None,
        color_discrete_sequence=[DIDI_ORANGE], opacity=0.75,
    )
    fig.update_traces(marker=dict(size=12, line=dict(width=1, color="white")))
    fig.update_layout(title=title, xaxis_title=x_title, yaxis_title=y_title)
    return apply_theme(fig, height=400)


def agents_below_goal(agents: pd.DataFrame, top_n: int = 15) -> go.Figure:
    reliable = agents[agents["Reliable"]].nsmallest(top_n, "QA_Score")
    if reliable.empty:
        fig = go.Figure()
        fig.add_annotation(text="No hay agentes con muestra suficiente (n≥5)", showarrow=False)
        return apply_theme(fig)

    colors = [STATUS_COLORS["red"] if s < QA_GOAL else STATUS_COLORS["amber"] for s in reliable["QA_Score"]]
    fig = go.Figure(go.Bar(
        x=reliable["QA_Score"], y=reliable["Agent_ID"],
        orientation="h", marker_color=colors,
        text=reliable["QA_Score"], textposition="outside",
    ))
    fig.add_vline(x=QA_GOAL, line_dash="dash", line_color=STATUS_COLORS["green"],
                  annotation_text=f"Meta {QA_GOAL}")
    fig.update_layout(
        title=f"Agentes con peor score (mín. 5 auditorías)",
        xaxis_title="Score QA",
        yaxis=dict(categoryorder="total ascending"),
    )
    return apply_theme(fig, height=max(400, top_n * 28))


def qa_by_cr(audits: pd.DataFrame, top_n: int = 15) -> go.Figure:
    g = audits.groupby("CR_Lv4").agg(Score=("Score_Pct", "mean"), N=("Audit_ID", "count")).reset_index()
    g = g[g["N"] >= 3].nsmallest(top_n, "Score")
    g["Score"] = g["Score"].round(1)
    fig = go.Figure(go.Bar(
        x=g["Score"], y=g["CR_Lv4"], orientation="h",
        marker_color=[STATUS_COLORS["red"] if s < QA_GOAL else STATUS_COLORS["green"] for s in g["Score"]],
        text=g["Score"], textposition="outside",
    ))
    fig.add_vline(x=QA_GOAL, line_dash="dash", line_color=STATUS_COLORS["green"])
    fig.update_layout(
        title="Motivos de contacto (CR) con peor calidad QA",
        xaxis_title="Score QA",
        yaxis=dict(categoryorder="total ascending"),
    )
    return apply_theme(fig, height=460)


def csat_by_channel(csat: pd.DataFrame) -> go.Figure:
    g = csat.groupby("Channel").agg(
        Feedback=("Feedback CNT", "sum"), Satisfied=("Satisfied_CNT", "sum")
    ).reset_index()
    g["CSAT"] = (g["Satisfied"] / g["Feedback"] * 100).round(1)
    colors = [STATUS_COLORS["green"] if s >= CSAT_GOAL else STATUS_COLORS["red"] for s in g["CSAT"]]
    fig = go.Figure(go.Bar(
        x=g["Channel"], y=g["CSAT"], marker_color=colors,
        text=g["CSAT"], texttemplate="%{text}%", textposition="outside",
    ))
    fig.add_hline(y=CSAT_GOAL, line_dash="dash", line_color=STATUS_COLORS["green"],
                  annotation_text=f"Meta {CSAT_GOAL}%")
    fig.update_layout(
        title="Satisfacción del cliente (CSAT) por canal",
        xaxis_title="Canal",
        yaxis_title="CSAT %",
        yaxis=dict(range=[0, 100]),
    )
    return apply_theme(fig, height=380)


def csat_by_cr(csat: pd.DataFrame, top_n: int = 15) -> go.Figure:
    g = csat.groupby("CR_Lv4").agg(
        Feedback=("Feedback CNT", "sum"), Satisfied=("Satisfied_CNT", "sum")
    ).reset_index()
    g = g[g["Feedback"] >= 10]
    g["CSAT"] = (g["Satisfied"] / g["Feedback"] * 100).round(1)
    g = g.nsmallest(top_n, "CSAT")
    fig = go.Figure(go.Bar(
        x=g["CSAT"], y=g["CR_Lv4"], orientation="h",
        marker_color=[STATUS_COLORS["red"] if s < CSAT_GOAL else STATUS_COLORS["green"] for s in g["CSAT"]],
        text=g["CSAT"], texttemplate="%{text}%", textposition="outside",
    ))
    fig.add_hline(x=CSAT_GOAL, line_dash="dash", line_color=STATUS_COLORS["green"])
    fig.update_layout(
        title="Motivos de contacto con peor satisfacción del cliente",
        xaxis_title="CSAT %",
        yaxis=dict(categoryorder="total ascending"),
    )
    return apply_theme(fig, height=460)


def recontact_by_cr(recontact: pd.DataFrame, top_n: int = 15) -> go.Figure:
    g = (
        recontact.groupby("CR_Lv4")
        .agg(Contacts=("Contacts", "sum"), Recontacts=("Recontact Volume", "sum"))
        .reset_index()
    )
    g = g[g["Contacts"] >= 30]
    g["Rate"] = (g["Recontacts"] / g["Contacts"] * 100).round(2)
    g = g.nlargest(top_n, "Rate")
    colors = [STATUS_COLORS["red"] if r > RECONTACT_GOAL else STATUS_COLORS["green"] for r in g["Rate"]]
    fig = go.Figure(go.Bar(
        x=g["Rate"], y=g["CR_Lv4"], orientation="h",
        marker_color=colors,
        text=g["Rate"], texttemplate="%{text}%", textposition="outside",
    ))
    fig.add_vline(x=RECONTACT_GOAL, line_dash="dash", line_color=STATUS_COLORS["green"],
                  annotation_text=f"Meta {RECONTACT_GOAL}%")
    fig.update_layout(
        title="Motivos donde el cliente vuelve a contactar (recontacto)",
        xaxis_title="Tasa de recontacto %",
        yaxis=dict(categoryorder="total ascending"),
    )
    return apply_theme(fig, height=460)


def supervisor_scores(audits: pd.DataFrame) -> go.Figure:
    g = (
        audits.groupby("Supervisor_ID")
        .agg(Score=("Score_Pct", "mean"), Audits=("Audit_ID", "count"))
        .reset_index()
    )
    g = g[g["Audits"] >= 5].sort_values("Score")
    g["Score"] = g["Score"].round(1)
    fig = go.Figure(go.Bar(
        x=g["Score"], y=g["Supervisor_ID"], orientation="h",
        marker_color=[STATUS_COLORS["green"] if s >= QA_GOAL else STATUS_COLORS["red"] for s in g["Score"]],
        text=g["Score"], textposition="outside",
    ))
    fig.add_vline(x=QA_GOAL, line_dash="dash", line_color=STATUS_COLORS["green"])
    fig.update_layout(
        title="Score QA promedio por supervisor",
        xaxis_title="Score QA",
        yaxis=dict(categoryorder="total ascending"),
    )
    return apply_theme(fig, height=max(400, len(g) * 22))
