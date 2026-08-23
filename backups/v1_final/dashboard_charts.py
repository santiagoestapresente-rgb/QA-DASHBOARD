"""Executive CX Quality Dashboard — Plotly charts."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import (
    CHART_COLORS,
    COUNTRY_ISO3,
    COUNTRY_NAMES,
    CSAT_GOAL,
    DIDI_CARD,
    DIDI_MUTED,
    DIDI_ORANGE,
    DIDI_TEXT,
    QA_GOAL,
    RANKING_CSAT_MIN_N,
    CR_COMBO_MIN_QA_N,
    RECONTACT_GOAL,
    STATUS_COLORS,
    TENURE_SOURCE_ORDER,
)

FONT = 'Inter, "Segoe UI", system-ui, sans-serif'
CHART_CFG = {"displayModeBar": False, "responsive": True}
TICK = "#1A1A1A"
GRID = "rgba(26,26,26,0.10)"
LINE = "rgba(26,26,26,0.16)"
PAPER = DIDI_CARD


def _goal_status(value, goal: float, higher_is_better: bool = True) -> str:
    """Business-case light: green on goal, amber within 5 points, red beyond."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "neutral"
    diff = float(value) - float(goal) if higher_is_better else float(goal) - float(value)
    if diff >= 0:
        return "green"
    if diff >= -5:
        return "amber"
    return "red"


def _status_hex(value, goal: float, higher_is_better: bool = True) -> str:
    return STATUS_COLORS.get(_goal_status(value, goal, higher_is_better), STATUS_COLORS["neutral"])


VOLUME_LINE = "#475569"
# Percentage score axis. Labels sit outside the bar; extra right margin covers them.
SCORE_LABEL_MAX = 100

_TRAFFIC_LEGEND = (
    ("On goal", STATUS_COLORS["green"]),
    ("Within 5 points", STATUS_COLORS["amber"]),
    ("More than 5 points off", STATUS_COLORS["red"]),
)


def _add_traffic_legend(fig: go.Figure, *, secondary_y: bool | None = None) -> None:
    """Dummy traces so the legend matches the 3-state bar colors."""
    for name, color in _TRAFFIC_LEGEND:
        tr = go.Bar(
            x=[None], y=[None], name=name,
            marker_color=color, hoverinfo="skip", showlegend=True,
        )
        if secondary_y is None:
            fig.add_trace(tr)
        else:
            fig.add_trace(tr, secondary_y=secondary_y)


def _tenure_rank(value: object) -> int:
    raw = str(value or "").strip().replace("–", "-").replace("—", "-").casefold()
    rank = {
        str(k).replace("–", "-").replace("—", "-").casefold(): i
        for i, k in enumerate(list(TENURE_SOURCE_ORDER) + ["Unknown"])
    }
    return rank.get(raw, 99)


def _is_tenure_col(cat_col: str) -> bool:
    return "tenure" in str(cat_col).casefold()


def _sort_tenure_plot(plot: pd.DataFrame, cat_col: str) -> pd.DataFrame:
    if plot is None or plot.empty or not _is_tenure_col(cat_col):
        return plot
    out = plot.copy()
    out["_tord"] = out[cat_col].map(_tenure_rank)
    return out.sort_values("_tord", kind="mergesort").drop(columns="_tord")


LEGEND_BOTTOM = dict(
    orientation="h", y=-0.22, x=0.5, xanchor="center",
    font=dict(size=10, color=DIDI_TEXT), bgcolor="rgba(0,0,0,0)",
)
LEGEND_TOP = dict(
    orientation="h", y=1.02, x=0.5, xanchor="center", yanchor="bottom",
    font=dict(size=10, color=DIDI_TEXT), bgcolor="rgba(0,0,0,0)",
)


def _hex_lerp(start: str, end: str, t: float) -> str:
    t = min(1.0, max(0.0, float(t)))

    def _rgb(hex_color: str) -> tuple[int, int, int]:
        h = hex_color.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    r1, g1, b1 = _rgb(start)
    r2, g2, b2 = _rgb(end)
    return f"#{int(r1 + (r2 - r1) * t):02x}{int(g1 + (g2 - g1) * t):02x}{int(b1 + (b2 - b1) * t):02x}"


def _bar_gradient(n: int, start: str = "#163A66", end: str = "#8FCBFF") -> list[str]:
    if n <= 1:
        return [start]
    return [_hex_lerp(start, end, i / (n - 1)) for i in range(n)]


def _wrap_label(text: object, width: int = 42, max_lines: int = 3) -> str:
    s = str(text).strip()
    if len(s) <= width:
        return s
    words = s.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if len(trial) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return "<br>".join(lines[: max(1, max_lines)])


def _hbar_height(n: int, row: int = 32, base: int = 110) -> int:
    return max(300, base + max(int(n), 1) * row)


def _split_view_universe(
    sample: int | None,
    unit: str,
    universe_n: int | None,
    extra_note: str | None = None,
) -> tuple[int | None, str, str | None]:
    """When bars are a subset, N is the plotted volume and the filter total sits in the note."""
    note = extra_note
    if (
        sample is not None
        and universe_n is not None
        and int(universe_n) > 0
        and int(universe_n) != int(sample)
    ):
        if unit and "in view" not in unit:
            unit = f"{unit} in view"
        uni = f"{int(universe_n):,} in filter"
        note = f"{note} · {uni}" if note else uni
    return sample, unit, note
DONUT_PALETTE = [
    CHART_COLORS["blue"], "#2E9B57", "#D64545",
    "#7A8BA0", "#C5D0DC", "#F2A900", "#5B8DEF", DIDI_ORANGE,
]


def _blank_null_axis_titles(fig: go.Figure) -> None:
    """Plotly.js prints 'undefined' when an axis/layout title is JSON null."""
    fig.update_layout(title=dict(text=""))
    try:
        fig.layout.title.text = ""
    except Exception:
        pass
    axes = []
    try:
        axes.extend(list(fig.select_xaxes()))
        axes.extend(list(fig.select_yaxes()))
    except Exception:
        pass
    for axis in axes:
        text = axis.title.text if axis.title is not None else None
        if text is None or str(text) in {"None", "undefined"}:
            axis.update(title_text="")
    anns = fig.layout.annotations
    if anns:
        for ann in anns:
            if ann.text is None or str(ann.text) in {"None", "undefined"}:
                ann.text = ""


def _sum_n(df: pd.DataFrame | None, *cols: str) -> int | None:
    if df is None or getattr(df, "empty", True):
        return None
    for col in cols:
        if col in df.columns:
            total = pd.to_numeric(df[col], errors="coerce").sum()
            if pd.notna(total):
                return int(total)
    return None


def _len_n(df: pd.DataFrame | None) -> int | None:
    if df is None or getattr(df, "empty", True):
        return None
    return int(len(df))


_VOLUME_COLS = (
    "n", "N", "Audits", "Audit_Count", "QA_Evaluations",
    "Feedback", "Surveys", "Contacts",
)


def _volume_col(df: pd.DataFrame, count_col: str) -> str | None:
    for col in _VOLUME_COLS:
        if col in df.columns and col != count_col:
            return col
    return None


def _vol_label(vol_col: str) -> str:
    if vol_col in ("Feedback", "Surveys"):
        return "Surveys"
    if vol_col == "Contacts":
        return "Contacts"
    if vol_col == "Recontacts":
        return "Repeats"
    return "Audits"


def _volume_unit(vol_col: str | None, sample_unit: str | None = None) -> str:
    if vol_col in ("Feedback", "Surveys"):
        return "surveys"
    if vol_col == "Contacts":
        return "contacts"
    if vol_col == "Recontacts":
        return "repeats"
    if sample_unit:
        return sample_unit
    return "audits"


def _is_weighted_gap(
    count_col: str,
    value_title: str | None = None,
    title: str | None = None,
) -> bool:
    """True when bars are gap × volume, not a raw audit/survey/contact count."""
    if count_col == "Gap_Impact":
        return True
    blob = f"{value_title or ''} {title or ''}".lower()
    combo = f"{value_title or ''}{title or ''}"
    return "×" in combo or "points below" in blob or "weighted deficit" in blob


def _unit_from_title(title: str | None, value_title: str | None = None) -> str:
    blob = f"{title or ''} {value_title or ''}".lower()
    combo = f"{title or ''}{value_title or ''}"
    # gap × volume is a composite, not a count of audits/surveys.
    if "×" in combo or "points below" in blob or "weighted deficit" in blob:
        return "weighted deficit"
    if "audit" in blob:
        return "audits"
    if "unsatisfied" in blob or "survey" in blob:
        return "surveys"
    if "fail" in blob:
        return "fails"
    if "repeat" in blob or "recontact" in blob:
        return "repeats"
    if "comment" in blob:
        return "comments"
    if "contact" in blob:
        return "contacts"
    if "gap" in blob or "impact" in blob:
        return "weighted deficit"
    if value_title:
        return str(value_title).strip().lower()
    return "rows"


def _n_for_panel(
    df: pd.DataFrame | None,
    value_col: str,
    *,
    title: str | None = None,
    value_title: str | None = None,
    sample_unit: str | None = None,
) -> tuple[int | None, str, str | None]:
    """N for _panel: real volume, never sum(gap × n) labeled as audits/surveys."""
    if df is None or getattr(df, "empty", True) or not value_col:
        return None, sample_unit or "", None
    if _is_weighted_gap(value_col, value_title, title):
        weighted = _sum_n(df, value_col)
        vol_col = _volume_col(df, value_col)
        if vol_col:
            sample = _sum_n(df, vol_col)
            unit = _volume_unit(vol_col, sample_unit)
            note = f"weighted deficit {weighted:,}" if weighted is not None else None
            return sample, unit, note
        return weighted, "weighted deficit", None
    sample = _sum_n(df, value_col)
    unit = sample_unit or _unit_from_title(title, value_title)
    return sample, unit, None


def _panel(
    fig: go.Figure,
    height: int = 280,
    title: str | None = None,
    n: int | float | None = None,
    n_unit: str = "",
    n_note: str | None = None,
) -> go.Figure:
    """Theme the figure. Streamlit panel titles name the chart — inner Plotly titles sit on the legend."""
    prev = fig.layout.margin
    left = int(prev.l) if prev is not None and prev.l is not None else 48
    right = int(prev.r) if prev is not None and prev.r is not None else 48
    bottom = int(prev.b) if prev is not None and prev.b is not None else 72
    top = int(prev.t) if prev is not None and prev.t is not None else 16
    legend_y = None
    try:
        if fig.layout.legend is not None and fig.layout.legend.y is not None:
            legend_y = float(fig.layout.legend.y)
    except Exception:
        legend_y = None
    if legend_y is not None and legend_y >= 0.95:
        top = max(top, 52)
    bottom = max(bottom, 56)
    right = max(right, 48)
    left = max(left, 48)
    sample = None
    try:
        if n is not None and pd.notna(n) and int(n) >= 0 and n_unit:
            sample = int(n)
    except (TypeError, ValueError):
        sample = None
    n_lines: list[str] = []
    if sample is not None and sample > 0:
        n_lines.append(f"N = {sample:,} {n_unit}".strip())
        if n_note:
            n_lines.append(str(n_note).strip())
        # N sits on its own row(s) above the legend so they cannot print on top of each other.
        top = max(top, 56 + 20 * len(n_lines) + 36)
        fig.update_layout(
            legend=dict(
                orientation="h", y=1.0, yanchor="bottom",
                x=0.5, xanchor="center",
                font=dict(size=10, color=DIDI_TEXT),
                bgcolor="rgba(0,0,0,0)",
                tracegroupgap=16,
                itemsizing="constant",
            )
        )
    fig.update_layout(
        font=dict(family=FONT, size=11, color=DIDI_TEXT),
        paper_bgcolor=PAPER,
        plot_bgcolor=PAPER,
        margin=dict(l=left, r=right, t=top, b=bottom),
        height=height + 8,
        autosize=True,
        legend_font=dict(color=DIDI_TEXT),
        legend_bgcolor="rgba(0,0,0,0)",
        title=dict(text=""),
        dragmode=False,
    )
    fig.update_traces(cliponaxis=False, selector=dict(type="bar"))
    fig.update_xaxes(
        showgrid=False, linecolor=LINE, tickfont=dict(size=10, color=TICK),
        title_font=dict(color=TICK), zeroline=False,
        automargin=True,
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=GRID, linecolor=LINE,
        tickfont=dict(size=10, color=TICK), title_font=dict(color=TICK), zeroline=False,
        automargin=True,
    )
    if n_lines:
        # Legend occupies ~20px just above the plot; N rows sit above that.
        for i, line in enumerate(n_lines):
            fig.add_annotation(
                text=line,
                xref="paper", yref="paper",
                x=0.5, y=1,
                xanchor="center", yanchor="bottom",
                yshift=36 + 18 * (len(n_lines) - 1 - i),
                showarrow=False,
                font=dict(size=11, color=DIDI_MUTED),
                name="didi_n" if i == 0 else f"didi_n_{i}",
                align="center",
            )
    _blank_null_axis_titles(fig)
    return fig


def sparkline_fig(
    values: list[float],
    color: str = CHART_COLORS["blue"],
    labels: list[str] | None = None,
    unit: str = "",
    y_title: str = "",
) -> go.Figure:
    fig = go.Figure()
    clean = [v for v in values if v is not None and pd.notna(v)]
    if not clean:
        fig.add_annotation(text="No daily points", showarrow=False, font=dict(size=10, color=DIDI_MUTED))
        return _mini(fig, labeled=True)
    xs = labels if labels and len(labels) == len(values) else list(range(1, len(values) + 1))
    fig.add_trace(go.Scatter(
        x=xs, y=values, mode="lines+markers",
        line=dict(color=color, width=2), marker=dict(size=4, color=color),
        hovertemplate="%{x}<br>%{y:.1f}" + unit + "<extra></extra>",
    ))
    fig.update_layout(margin=dict(l=8, r=8, t=4, b=18))
    return _mini(fig, labeled=True)


def sparkbar_fig(
    values: list[float],
    color: str = CHART_COLORS["blue"],
    labels: list[str] | None = None,
    unit: str = "",
    y_title: str = "",
) -> go.Figure:
    fig = go.Figure()
    if not values:
        fig.add_annotation(text="No daily points", showarrow=False, font=dict(size=10, color=DIDI_MUTED))
        return _mini(fig, labeled=True)
    xs = labels if labels and len(labels) == len(values) else list(range(1, len(values) + 1))
    fig.add_trace(go.Bar(
        x=xs, y=values, marker_color=color,
        hovertemplate="%{x}<br>%{y:,.0f}" + unit + "<extra></extra>",
    ))
    fig.update_layout(margin=dict(l=8, r=8, t=4, b=18))
    return _mini(fig, labeled=True)


def _spark_card(fig: go.Figure, height: int = 118, margin: dict | None = None, *, legend: bool = False) -> go.Figure:
    fill = PAPER or DIDI_CARD
    fig.update_layout(
        height=height,
        margin=margin or dict(l=4, r=8, t=4, b=4),
        paper_bgcolor=fill,
        plot_bgcolor=fill,
        showlegend=legend,
        title=dict(text=""),
        font=dict(family=FONT, size=10, color=DIDI_TEXT),
    )
    _blank_null_axis_titles(fig)
    return fig


def _spark_label(name: object, width: int = 22) -> str:
    return _wrap_label(name, width, max_lines=2)


def _spark_hbar_text(value: float, unit: str) -> str:
    """Percents keep one decimal; volume counts are integers with thousands separators."""
    if unit == "%":
        return f"{value:.1f}{unit}"
    return f"{int(round(value)):,}{unit}"


def spark_hbar_fig(
    names: list[str],
    values: list[float],
    color: str | None = None,
    unit: str = "",
) -> go.Figure:
    """Horizontal ranking built for KPI cards — one line per bar, no rotated labels."""
    fig = go.Figure()
    if not names or not values:
        fig.add_annotation(text="No data", showarrow=False, font=dict(size=10, color=DIDI_MUTED))
        return _spark_card(fig)
    labels = [_spark_label(n) for n in names[:5]]
    full = [" ".join(str(n).split()) for n in names[:5]]
    vals = [float(v) if v is not None and pd.notna(v) else 0.0 for v in list(values)[: len(labels)]]
    y = list(reversed(labels))
    x = list(reversed(vals))
    hover = list(reversed(full[: len(labels)]))
    colors = _bar_gradient(len(x)) if color is None else [color] * len(x)
    x_hover = "%{x:.1f}" if unit == "%" else "%{x:,.0f}"
    fig.add_trace(go.Bar(
        y=y, x=x, orientation="h",
        marker=dict(color=list(reversed(colors)) if color is None else colors, line=dict(width=0)),
        text=[_spark_hbar_text(v, unit) for v in x],
        textposition="outside",
        textfont=dict(size=9, color=DIDI_TEXT),
        cliponaxis=False,
        customdata=hover,
        hovertemplate="%{customdata}<br>" + x_hover + unit + "<extra></extra>",
    ))
    xmax = max(x) if x else 1.0
    fig.update_xaxes(
        visible=False, range=[0, xmax * 1.38 if xmax > 0 else 1],
        title_text="", showgrid=False,
    )
    fig.update_yaxes(
        title_text="", automargin=True, tickfont=dict(size=10, color=TICK),
        ticksuffix="", showgrid=False,
    )
    fig.update_layout(bargap=0.22)
    return _spark_card(fig, height=132, margin=dict(l=8, r=42, t=4, b=4))


def spark_donut_fig(
    names: list[str],
    values: list[float],
    *,
    legend: bool = False,
    colors: list[str] | None = None,
) -> go.Figure:
    """Ring mix for a KPI card — optional tiny legend under the ring."""
    fig = go.Figure()
    if not names or not values:
        fig.add_annotation(text="No data", showarrow=False, font=dict(size=10, color=DIDI_MUTED))
        return _spark_card(fig)
    labels = list(names)[:6]
    star_fill = {
        "5 Stars": CHART_COLORS["blue"],
        "4 Stars": "#2E9B57",
        "3 Stars": STATUS_COLORS["amber"],
        "2 Stars": "#E85D4C",
        "1 Star": STATUS_COLORS["red"],
    }
    fills = colors or [
        star_fill.get(str(n), DONUT_PALETTE[i % len(DONUT_PALETTE)])
        for i, n in enumerate(labels)
    ]
    fig.add_trace(go.Pie(
        labels=[_spark_label(n, 28) for n in labels],
        values=[float(v) if v is not None and pd.notna(v) else 0.0 for v in list(values)[:6]],
        hole=0.62,
        marker=dict(
            colors=fills[: len(labels)],
            line=dict(color=PAPER or DIDI_CARD, width=1.5),
        ),
        textinfo="none",
        hovertemplate="%{label}<br>%{percent}<extra></extra>",
        showlegend=legend,
        sort=False,
        direction="clockwise",
    ))
    if legend:
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h", y=-0.08, x=0.5, xanchor="center",
                font=dict(size=9, color=DIDI_TEXT), bgcolor="rgba(0,0,0,0)",
                itemwidth=30,
            ),
        )
        return _spark_card(fig, height=148, margin=dict(l=8, r=8, t=6, b=28), legend=True)
    return _spark_card(fig, margin=dict(l=8, r=8, t=8, b=8))


def spark_r_fig(r: float | None) -> go.Figure:
    """R² as a 0…1 bar, colored by the sign of Pearson r."""
    fig = go.Figure()
    has = r is not None and not (isinstance(r, float) and pd.isna(r))
    try:
        has = has and pd.notna(r)
    except (TypeError, ValueError):
        has = False
    val = float(r) ** 2 if has else 0.0
    sign = float(r) if has else 0.0
    color = DIDI_ORANGE if sign >= 0 else STATUS_COLORS["red"]
    fig.add_trace(go.Bar(
        x=[val], y=["R²"], orientation="h",
        marker_color=color,
        width=0.42,
        hovertemplate="R² = %{x:.2f}<extra></extra>",
    ))
    fig.add_vline(x=0, line_color=LINE, line_width=1)
    fig.update_xaxes(
        range=[0, 1], tickvals=[0, 0.5, 1], title_text="",
        tickfont=dict(size=9, color=TICK), showgrid=False, zeroline=False,
    )
    fig.update_yaxes(visible=False, title_text="")
    return _spark_card(fig, height=110, margin=dict(l=8, r=8, t=10, b=22))


def _mini(fig: go.Figure, labeled: bool = False) -> go.Figure:
    # Same opaque fill as KPI tiles; fixed height so Overview sparklines align.
    fill = PAPER or DIDI_CARD
    fig.update_layout(
        height=80,
        margin=dict(l=10, r=8, t=6, b=20) if labeled else dict(l=4, r=4, t=4, b=4),
        paper_bgcolor=fill, plot_bgcolor=fill,
        showlegend=False,
        title=dict(text=""),
        yaxis_title="",
        font=dict(family=FONT, size=10, color=DIDI_TEXT),
    )
    _blank_null_axis_titles(fig)
    if labeled:
        fig.update_xaxes(
            showgrid=False, tickfont=dict(size=8, color=TICK), nticks=4, tickangle=0,
        )
        fig.update_yaxes(
            showgrid=True, gridcolor=GRID, tickfont=dict(size=8, color=TICK), nticks=3,
        )
    else:
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
    return fig


def preview_fig(fig: go.Figure, height: int = 128) -> go.Figure:
    """Compact copy of a panel chart for the click-to-expand preview tiles."""
    mini = go.Figure(fig)
    mini.update_layout(
        height=height,
        showlegend=False,
        margin=dict(l=8, r=10, t=8, b=18),
        title=dict(text=""),
    )
    mini.update_xaxes(title_text="", showticklabels=False, ticks="", nticks=4)
    mini.update_yaxes(title_text="", tickfont=dict(size=8, color=TICK), nticks=3)
    try:
        mini.update_traces(text=None, selector=dict(type="bar"))
    except Exception:
        pass
    try:
        mini.update_traces(textinfo="none", selector=dict(type="pie"))
    except Exception:
        pass
    if mini.data and mini.layout.annotations:
        mini.layout.annotations = ()
    _blank_null_axis_titles(mini)
    return mini


def critical_split_chart(n_crit: int, n_non: int) -> go.Figure:
    if n_crit + n_non <= 0:
        fig = go.Figure()
        fig.add_annotation(text="No attribute fails in the current filter", showarrow=False)
        return _panel(fig, 220, title="Critical vs non-critical QA fails")
    fig = go.Figure(go.Pie(
        labels=["CRITICAL", "Non-critical"],
        values=[n_crit, n_non],
        hole=0.58,
        marker=dict(colors=[STATUS_COLORS["red"], "#64748B"], line=dict(color=PAPER, width=1)),
        textinfo="label+percent",
        textfont=dict(size=11, color=DIDI_TEXT),
        hovertemplate="%{label}<br>%{value:,} fails (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center", font=dict(size=11, color=DIDI_TEXT), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=8, r=8, t=8, b=48),
    )
    return _panel(fig, 220, title="Critical vs non-critical QA fails", n=n_crit + n_non, n_unit="fails")


def manner_pie_chart(
    df: pd.DataFrame,
    title: str,
    *,
    colors: list[str] | None = None,
) -> go.Figure:
    if df is None or df.empty or "Slice" not in df.columns or "Surveys" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No comments with text in this filter", showarrow=False)
        return _panel(fig, 220, title=title)
    labels = df["Slice"].astype(str).tolist()
    values = pd.to_numeric(df["Surveys"], errors="coerce").fillna(0).tolist()
    if sum(values) <= 0:
        fig = go.Figure()
        fig.add_annotation(text="No comments with text in this filter", showarrow=False)
        return _panel(fig, 220, title=title)
    palette = colors or DONUT_PALETTE[: len(labels)]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.58,
        marker=dict(colors=palette, line=dict(color=PAPER, width=1)),
        textinfo="percent",
        textfont=dict(size=11, color=DIDI_TEXT),
        hovertemplate="%{label}<br>%{value:,.0f} surveys (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h", y=-0.16, x=0.5, xanchor="center",
            font=dict(size=11, color=DIDI_TEXT), bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=8, r=8, t=8, b=52),
    )
    return _panel(fig, 220, title=title, n=int(sum(values)), n_unit="surveys with comments")


def metrics_trend_daily(df: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if df.empty:
        fig.add_annotation(text="No trend data for selected period", showarrow=False)
        return _panel(fig, 260, title="Daily KPI trend")

    x = df["Date"].dt.strftime("%b %d")
    if "QA_Score" in df.columns and _finite(df["QA_Score"]):
        fig.add_trace(go.Scatter(
            x=x, y=df["QA_Score"], name="QA Score", mode="lines+markers",
            line=dict(color=CHART_COLORS["qa"], width=2), marker=dict(size=4),
        ), secondary_y=False)
    if "CSAT_Score" in df.columns and _finite(df["CSAT_Score"]):
        fig.add_trace(go.Scatter(
            x=x, y=df["CSAT_Score"], name="CSAT Score", mode="lines+markers",
            line=dict(color=CHART_COLORS["csat"], width=2), marker=dict(size=4),
        ), secondary_y=False)
    if "Recontact_Rate" in df.columns and _finite(df["Recontact_Rate"]):
        fig.add_trace(go.Scatter(
            x=x, y=df["Recontact_Rate"], name="Recontact Rate", mode="lines+markers",
            line=dict(color=CHART_COLORS["recontact"], width=2), marker=dict(size=4),
        ), secondary_y=True)

    fig.add_hline(y=QA_GOAL, line_dash="dot", line_color=DIDI_MUTED, line_width=1, secondary_y=False)
    fig.add_hline(y=RECONTACT_GOAL, line_dash="dot", line_color=DIDI_MUTED, line_width=1, secondary_y=True)
    fig.update_yaxes(title_text="%", range=[0, 100], secondary_y=False)
    fig.update_yaxes(
        title_text="Recontact %",
        range=_rc_axis(df, "Recontact_Rate") if "Recontact_Rate" in df.columns else (0, 10),
        secondary_y=True,
    )
    fig.update_layout(legend=LEGEND_BOTTOM)
    return _panel(fig, 260, title="Daily KPI trend", n=_len_n(df), n_unit="days")


def recontact_by_cr_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No recontact data in the current filter", showarrow=False)
        return _panel(fig, 320, title="Recontact rate by contact reason Lv4 (detail)")

    df = df.sort_values("Recontact_Rate", ascending=True).tail(8)
    labels = [_wrap_label(x, 40) for x in df["CR_Lv4"]]
    colors = [_status_hex(r, RECONTACT_GOAL, False) for r in df["Recontact_Rate"]]

    fig = go.Figure(go.Bar(
        y=labels, x=df["Recontact_Rate"], orientation="h",
        marker_color=colors,
        text=[f"{v:.1f}%" for v in df["Recontact_Rate"]],
        textposition="outside", textfont=dict(size=9, color=DIDI_TEXT),
        hovertemplate="%{y}<br>%{x:.2f}%<extra></extra>",
    ))
    fig.add_vline(x=RECONTACT_GOAL, line_dash="dash", line_color=DIDI_MUTED, line_width=1)
    fig.update_layout(
        xaxis_title="Recontact rate %",
        yaxis_title="",
        margin=dict(l=220, r=56, t=12, b=40),
    )
    return _panel(
        fig, _hbar_height(len(df), 34, 100),
        title="Recontact rate by contact reason Lv4 (detail)",
        n=_sum_n(df, "Contacts"), n_unit="contacts",
    )


def square_pie_fig(fig: go.Figure, size: int = 420) -> go.Figure:
    """Centered pie/donut: legend under the ring, no full-width stretch."""
    out = go.Figure(fig)
    n_anns = [ann for ann in (out.layout.annotations or []) if getattr(ann, "name", None) == "didi_n"]
    out.update_traces(
        textinfo="percent",
        textposition="inside",
        insidetextorientation="horizontal",
        textfont=dict(size=11, color=DIDI_TEXT),
        selector=dict(type="pie"),
    )
    out.update_layout(
        height=size,
        autosize=True,
        showlegend=True,
        legend=dict(
            orientation="h", y=-0.14, x=0.5, xanchor="center",
            font=dict(size=10, color=DIDI_TEXT), bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=8, r=8, t=48, b=96),
        title=dict(text=""),
    )
    _blank_null_axis_titles(out)
    if n_anns:
        keep = [ann for ann in (out.layout.annotations or []) if getattr(ann, "name", None) == "didi_n"]
        if not keep:
            out.layout.annotations = tuple(list(out.layout.annotations or []) + n_anns)
    return out


def recontact_donut(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data", showarrow=False)
        return _panel(fig, 220, title="Recontact mix by contact reason Lv4 (detail)")

    labels = [_wrap_label(x, 28) for x in df["CR_Lv4"]]
    fig = go.Figure(go.Pie(
        labels=labels, values=df["Recontacts"], hole=0.58,
        marker=dict(colors=DONUT_PALETTE[: len(df)]),
        textinfo="percent", textposition="outside", textfont=dict(size=9, color=DIDI_TEXT),
        customdata=df["CR_Lv4"].astype(str),
        hovertemplate="%{customdata}<br>%{value:,.0f} recontacts (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="v", y=0.5, x=1.02, font=dict(size=9, color=DIDI_TEXT), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=8, r=110, t=8, b=8),
    )
    return _panel(
        fig, 220, title="Recontact mix by contact reason Lv4 (detail)",
        n=_sum_n(df, "Recontacts"), n_unit="repeats",
    )


def recontact_scope_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No scope data", showarrow=False)
        return _panel(fig, 170, title="Official mix vs Phone + Chat")

    df = df.sort_values("Scope_Order") if "Scope_Order" in df.columns else df
    colors = [_status_hex(r, RECONTACT_GOAL, False) for r in df["Rate"]]
    labels = [_wrap_label(x, 26, max_lines=2) for x in df["Scope"]]
    fig = go.Figure(go.Bar(
        y=labels, x=df["Rate"], orientation="h",
        marker_color=colors,
        text=[
            f"{v:.2f}% · {int(c):,}" if pd.notna(c) else (f"{v:.2f}%" if pd.notna(v) else "—")
            for v, c in zip(df["Rate"], df["Contacts"] if "Contacts" in df.columns else [None] * len(df))
        ],
        textposition="outside", textfont=dict(size=9, color=DIDI_TEXT),
        cliponaxis=False,
        customdata=df["Contacts"] if "Contacts" in df.columns else None,
        hovertemplate="%{y}<br>%{x:.2f}%<br>%{customdata:,} contacts<extra></extra>",
    ))
    fig.add_vline(x=RECONTACT_GOAL, line_dash="dash", line_color=DIDI_MUTED, line_width=1)
    xmax = max(18.0, float(pd.to_numeric(df["Rate"], errors="coerce").max() or 0) * 1.28)
    fig.update_layout(
        xaxis=dict(title="Recontact Rate %", range=[0, xmax]),
        yaxis=dict(title="", autorange="reversed"),
        margin=dict(l=168, r=64, t=12, b=36),
    )
    official = df.iloc[0]["Contacts"] if "Contacts" in df.columns and not df.empty else None
    return _panel(fig, 170, title="Official mix vs Phone + Chat", n=official, n_unit="contacts")


def top_failing_attributes_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No defect data", showarrow=False)
        return _panel(fig, 280, title="QA fails by attribute")

    df = df.sort_values("Fail_Count", ascending=True)
    colors = [
        CHART_COLORS["critical"] if row.get("Is_Critical") else CHART_COLORS["bar"]
        for _, row in df.iterrows()
    ]
    fig = go.Figure(go.Bar(
        y=df["Error_Category"], x=df["Pct_Of_Fails"], orientation="h",
        marker_color=colors,
        text=[f"{v:.1f}%" for v in df["Pct_Of_Fails"]],
        textposition="outside", textfont=dict(size=9, color=DIDI_TEXT),
    ))
    fig.update_layout(xaxis_title="% of total fails", yaxis_title="", margin=dict(l=160, r=48, t=12, b=36))
    return _panel(
        fig, _hbar_height(len(df), 30, 90), title="QA fails by attribute",
        n=_sum_n(df, "Fail_Count"), n_unit="fails",
    )


def qa_by_cr_chart(
    df: pd.DataFrame,
    *,
    cat_col: str = "CR_Lv4",
    grain: str = "contact reason Lv4 (detail)",
) -> go.Figure:
    title = f"QA score by {grain}"
    if df.empty or cat_col not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text=f"No {grain} scores in the current filter", showarrow=False)
        return _panel(fig, 320, title=title)

    labels = [_wrap_label(x, 36, max_lines=2) for x in df[cat_col]]
    colors = [_status_hex(s, QA_GOAL, True) for s in df["QA_Score"]]
    n_vals = pd.to_numeric(df["N"], errors="coerce") if "N" in df.columns else pd.Series([np.nan] * len(df))
    vs_txt = [
        f"{v:.1f}  n={int(n):,}" if pd.notna(n) else (f"{v:.1f}" if pd.notna(v) else "—")
        for v, n in zip(df["QA_Score"], n_vals)
    ]
    fig = go.Figure(go.Bar(
        y=labels, x=df["QA_Score"], orientation="h", marker_color=colors,
        text=vs_txt, textposition="outside", textfont=dict(size=9, color=DIDI_TEXT),
        cliponaxis=False,
        customdata=np.column_stack([
            df[cat_col].astype(str).to_numpy(),
            n_vals.fillna(0).to_numpy(),
            pd.to_numeric(df["vs_goal"], errors="coerce").fillna(0).to_numpy() if "vs_goal" in df.columns else np.zeros(len(df)),
        ]),
        hovertemplate="%{customdata[0]}<br>QA %{x:.1f}%<br>Audits %{customdata[1]:.0f}<br>vs 85 %{customdata[2]:+.1f}<extra></extra>",
    ))
    fig.add_vline(x=QA_GOAL, line_dash="dash", line_color=DIDI_MUTED)
    fig.update_layout(
        xaxis=dict(range=[0, SCORE_LABEL_MAX], title="QA score %"),
        margin=dict(l=220, r=96, t=12, b=40),
    )
    return _panel(
        fig, _hbar_height(len(df), 34, 110), title=title,
        n=_sum_n(df, "N", "n", "Audits"), n_unit="audits",
    )


def _pair_scatter(df: pd.DataFrame, x: str, y: str) -> pd.DataFrame:
    if df is None or df.empty or x not in df.columns or y not in df.columns:
        return pd.DataFrame()
    keep = [x, y] + (["CR_Lv4"] if "CR_Lv4" in df.columns else [])
    if "Feedback" in df.columns:
        keep.append("Feedback")
    return df[keep].dropna(subset=[x, y])


def _add_ols_trendline(fig: go.Figure, x, y) -> None:
    """Dashed OLS fit through the plotted points. Distinct from dotted goal lines."""
    xs = pd.to_numeric(pd.Series(list(x)), errors="coerce")
    ys = pd.to_numeric(pd.Series(list(y)), errors="coerce")
    mask = xs.notna() & ys.notna()
    if int(mask.sum()) < 2:
        return
    xv = xs[mask].to_numpy(dtype=float)
    yv = ys[mask].to_numpy(dtype=float)
    if np.unique(xv).size < 2:
        return
    try:
        slope, intercept = np.polyfit(xv, yv, 1)
    except (np.linalg.LinAlgError, ValueError):
        return
    x0, x1 = float(np.min(xv)), float(np.max(xv))
    fig.add_trace(go.Scatter(
        x=[x0, x1],
        y=[slope * x0 + intercept, slope * x1 + intercept],
        mode="lines",
        name="Trend",
        line=dict(color=DIDI_ORANGE, width=1.8, dash="dash"),
        hoverinfo="skip",
        showlegend=False,
    ))


def qa_csat_scatter(df: pd.DataFrame) -> go.Figure:
    plot = _pair_scatter(df, "QA_Score", "CSAT_Pct")
    if plot.empty:
        n = 0
        fig = go.Figure()
        fig.add_annotation(
            text=f"Only {n} contact reason Lv4 (detail) name(s) have both QA and CSAT in this filter",
            showarrow=False,
        )
        return _panel(fig, 260, title="Correlation QA vs CSAT")

    size_col = "Feedback" if "Feedback" in plot.columns else None
    sizes = (np.clip(plot[size_col] / 80, 8, 28) if size_col else 9)
    fig = go.Figure(go.Scatter(
        x=plot["QA_Score"], y=plot["CSAT_Pct"], mode="markers",
        marker=dict(size=sizes, color=CHART_COLORS["blue"], opacity=0.85),
        customdata=plot["CR_Lv4"].astype(str) if "CR_Lv4" in plot.columns else None,
        hovertext=plot["CR_Lv4"] if "CR_Lv4" in plot.columns else None,
        hoverinfo="text+x+y",
        name="Contact reasons",
    ))
    _add_ols_trendline(fig, plot["QA_Score"], plot["CSAT_Pct"])
    fig.add_hline(y=CSAT_GOAL, line_dash="dot", line_color=DIDI_MUTED)
    fig.add_vline(x=QA_GOAL, line_dash="dot", line_color=DIDI_MUTED)
    fig.update_layout(
        xaxis_title="QA Score %", yaxis_title="CSAT %",
        margin=dict(l=56, r=28, t=16, b=56),
    )
    return _panel(
        fig, 260, title="Correlation QA vs CSAT",
        n=_len_n(plot), n_unit="contact reasons Lv4 (detail)",
    )


def _finite(series) -> bool:
    if series is None:
        return False
    return bool(pd.to_numeric(series, errors="coerce").notna().any())


def _pct_axis(df: pd.DataFrame, cols: list[str], goal: float = 85.0) -> tuple[float, float]:
    vals: list[float] = []
    for col in cols:
        if col in df.columns:
            vals.extend(pd.to_numeric(df[col], errors="coerce").dropna().tolist())
    if not vals:
        return 70.0, 100.0
    lo = min(vals + [goal]) - 6
    hi = max(vals + [goal, 100.0]) + 3
    return max(0.0, lo), min(110.0, hi)


def _rc_axis(df: pd.DataFrame, col: str = "Recontact_Rate") -> tuple[float, float]:
    if col not in df.columns:
        return 0.0, 12.0
    vals = pd.to_numeric(df[col], errors="coerce").dropna()
    peak = float(vals.max()) if not vals.empty else RECONTACT_GOAL
    return 0.0, max(8.0, RECONTACT_GOAL * 1.35, peak * 1.18)


def weekly_kpi_chart(df: pd.DataFrame, *, height: int = 360) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No weekly data in the current filter", showarrow=False)
        return _panel(fig, min(height, 280), title="Week-over-week trend")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if "QA_Score" in df.columns and _finite(df["QA_Score"]):
        fig.add_trace(go.Scatter(
            x=df["Week"], y=df["QA_Score"], name="QA", mode="lines+markers",
            line=dict(color=CHART_COLORS["qa"], width=2),
            connectgaps=True,
            customdata=df["Week"].astype(str),
            hovertemplate="%{customdata}<br>%{y:.1f}<extra></extra>",
        ), secondary_y=False)
    if "CSAT_Score" in df.columns and _finite(df["CSAT_Score"]):
        fig.add_trace(go.Scatter(
            x=df["Week"], y=df["CSAT_Score"], name="CSAT", mode="lines+markers",
            line=dict(color=CHART_COLORS["csat"], width=2),
            connectgaps=True,
            customdata=df["Week"].astype(str),
            hovertemplate="%{customdata}<br>%{y:.1f}<extra></extra>",
        ), secondary_y=False)
    plotted_rc = "Recontact_Rate" in df.columns and _finite(df["Recontact_Rate"])
    if plotted_rc:
        fig.add_trace(go.Scatter(
            x=df["Week"], y=df["Recontact_Rate"], name="Recontact", mode="lines+markers",
            line=dict(color=CHART_COLORS["recontact"], width=2),
            connectgaps=True,
            customdata=df["Week"].astype(str),
            hovertemplate="%{customdata}<br>%{y:.2f}<extra></extra>",
        ), secondary_y=True)
    lo, hi = _pct_axis(df, ["QA_Score", "CSAT_Score"])
    fig.add_hline(y=QA_GOAL, line_dash="dot", line_color=DIDI_MUTED, secondary_y=False)
    fig.update_yaxes(title_text="QA / CSAT %", range=[lo, hi], tickformat=".1f", secondary_y=False)
    if plotted_rc:
        _, rc_hi = _rc_axis(df)
        fig.add_hline(y=RECONTACT_GOAL, line_dash="dot", line_color=DIDI_MUTED, secondary_y=True)
        fig.update_yaxes(title_text="Recontact %", range=[0, rc_hi], tickformat=".2f", secondary_y=True)
    else:
        fig.update_yaxes(title_text="Recontact %", visible=False, secondary_y=True)
    compact = height <= 260
    if compact:
        fig.update_layout(legend=LEGEND_TOP, margin=dict(l=40, r=40, t=36, b=28))
        return _panel(fig, height, title="Week-over-week trend")
    fig.update_layout(legend=LEGEND_TOP, margin=dict(l=56, r=56, t=52, b=48))
    return _panel(fig, height, title="Week-over-week trend", n=_len_n(df), n_unit="weeks")


def control_i_chart(
    df: pd.DataFrame,
    title_goal: str,
    chart_title: str | None = None,
    *,
    height: int = 380,
) -> go.Figure:
    compact = height <= 280
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Not enough daily points to show typical variation", showarrow=False)
        return _panel(fig, min(height, 280) if compact else 340, title=chart_title)
    fig = go.Figure()
    colors = [STATUS_COLORS["red"] if flag else CHART_COLORS["blue"] for flag in df["Beyond_Limits"]]
    hover = []
    for _, row in df.iterrows():
        stamp = pd.to_datetime(row["Date"]).strftime("%b %d") if pd.notna(row["Date"]) else ""
        note = " — outside typical day-to-day variation" if bool(row["Beyond_Limits"]) else ""
        hover.append(f"{stamp}<br>{row['Value']:.2f}{note}")
    day_ids = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["Value"], mode="lines+markers", name="Daily value",
        line=dict(color=CHART_COLORS["blue"], width=2),
        marker=dict(color=colors, size=7 if not compact else 6),
        hovertext=hover, hoverinfo="text",
        customdata=day_ids,
    ))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["CL"], mode="lines", name="Average",
                             line=dict(color=DIDI_MUTED, width=1.4)))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["UCL"], mode="lines", name="Upper usual range",
                             line=dict(color="#F07167", width=1.4, dash="dot")))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["LCL"], mode="lines", name="Lower usual range",
                             line=dict(color="#F07167", width=1.4, dash="dot")))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Goal"], mode="lines", name=title_goal,
                             line=dict(color=STATUS_COLORS["green"], width=1.6, dash="dash")))
    vals = []
    for col in ("Value", "CL", "UCL", "LCL", "Goal"):
        if col in df.columns:
            vals.extend(pd.to_numeric(df[col], errors="coerce").dropna().tolist())
    y_lo, y_hi = 0.0, 100.0
    if vals:
        lo, hi = min(vals), max(vals)
        gap = max(0.8, (hi - lo) * 0.08)
        y_lo, y_hi = lo - gap, hi + gap
    nticks = 5 if compact else 6
    if compact:
        fig.update_layout(
            legend=LEGEND_TOP,
            margin=dict(l=40, r=28, t=36, b=36),
            yaxis=dict(title="", range=[y_lo, y_hi], tickformat=".1f", nticks=nticks),
        )
        fig = _panel(fig, height, title=chart_title)
    else:
        fig.update_layout(
            legend=LEGEND_TOP,
            margin=dict(l=48, r=28, t=56, b=48),
            yaxis=dict(title="", range=[y_lo, y_hi], tickformat=".1f", nticks=nticks),
        )
        fig = _panel(fig, height, title=chart_title, n=_len_n(df), n_unit="days")
    fig.update_yaxes(range=[y_lo, y_hi], tickformat=".1f", title_text="", nticks=nticks)
    return fig


def qa_histogram_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No QA scores", showarrow=False)
        return _panel(fig, 240, title="QA score distribution")
    colors = [
        STATUS_COLORS["red"] if int(x) == 0 else CHART_COLORS["bar"]
        for x in df["QA_Score"]
    ]
    fig = go.Figure(go.Bar(
        x=df["QA_Score"], y=df["Audits"], marker_color=colors,
        text=df["Audits"], textposition="outside", textfont=dict(size=9, color=DIDI_TEXT),
    ))
    fig.add_vline(x=QA_GOAL, line_dash="dash", line_color=STATUS_COLORS["green"])
    fig.update_layout(
        xaxis_title="QA Score",
        yaxis_title="Audits",
        margin=dict(l=56, r=28, t=28, b=56),
        yaxis=dict(rangemode="tozero"),
    )
    fig.update_traces(cliponaxis=False)
    return _panel(fig, 280, title="QA score distribution", n=_sum_n(df, "Audits"), n_unit="audits")


def csat_histogram_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No CSAT scores", showarrow=False)
        return _panel(fig, 360, title="CSAT score histogram")
    scores = pd.to_numeric(df["CSAT_Score"], errors="coerce")
    surveys = pd.to_numeric(df["Surveys"], errors="coerce").fillna(0)
    peak = float(surveys.max()) if len(surveys) else 0.0
    colors = [
        STATUS_COLORS["red"] if float(x) < CSAT_GOAL else CHART_COLORS["blue"]
        for x in scores
    ]
    labels = [
        f"{int(v):,}" if peak and v >= max(peak * 0.08, 1) else ""
        for v in surveys
    ]
    fig = go.Figure(go.Bar(
        x=scores, y=surveys, marker_color=colors,
        text=labels,
        textposition="outside", textfont=dict(size=11, color=DIDI_TEXT),
        hovertemplate="CSAT %{x:.0f}%<br>%{y:,.0f} surveys<extra></extra>",
        width=3.2,
    ))
    fig.add_vline(x=CSAT_GOAL, line_dash="dash", line_color=STATUS_COLORS["green"], line_width=2)
    y_hi = peak * 1.16 if peak else 1
    fig.update_layout(
        xaxis=dict(title="CSAT %", range=[-4, 104], dtick=20),
        yaxis=dict(title="Surveys", range=[0, y_hi], rangemode="tozero", tickformat=","),
        margin=dict(l=56, r=28, t=28, b=56),
        showlegend=False,
    )
    fig.update_traces(cliponaxis=False)
    fig = _panel(fig, 380, title="CSAT score histogram")
    fig.update_xaxes(title_text="CSAT %", range=[-4, 104], dtick=20)
    fig.update_yaxes(title_text="Surveys", range=[0, y_hi], tickformat=",")
    fig.update_layout(showlegend=False)
    return fig


def _pareto_remainder_label(existing, n_more: int | None = None) -> str:
    """Tail bucket name that never collides with a real category such as taxonomy Other."""
    taken = {str(v).strip().casefold() for v in existing.dropna()}
    bases = (
        (f"Remaining reasons ({n_more} more)" if n_more else "Remaining reasons"),
        "Remaining reasons",
        "All remaining categories",
        "Rest of categories",
    )
    for label in bases:
        if label.casefold() not in taken:
            return label
    return "Remaining reasons *"


def is_pareto_remainder_label(value: object) -> bool:
    text = str(value or "").strip().casefold()
    return text.startswith("remaining reasons") or text.startswith("all remaining") or text.startswith("rest of categories")


def pareto_dual_axis(
    df: pd.DataFrame,
    cat_col: str,
    count_col: str,
    title: str = "Pareto analysis",
    value_title: str = "Count",
    critical_col: str | None = None,
    sample_unit: str | None = None,
    universe_n: int | None = None,
    n_note: str | None = None,
    bucket_other: bool = False,
) -> go.Figure:
    """Classic vertical Pareto: descending bars, value on the left, cumulative % on the right.

    When `count_col` is a weighted gap (gap × volume), N is the sum of evaluations
    on the plotted bars — never the sum of gap × n labeled as audits.
    Zero-count rows are omitted so they cannot steal axis space or N.
    Cumulative % is of the full fail/volume universe, not only the plotted bars.
    With `bucket_other`, named bars run until ~80% of that universe (capped), and
    Remaining reasons is the leftover tail — not a fixed top 10.
    """
    from modules.kpis import (
        PARETO_MAX_NAMED,
        PARETO_VITAL_PCT,
        add_pareto_cumulative,
        pareto_named_and_tail,
    )
    if df is None or df.empty or cat_col not in df.columns or count_col not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No data for this ranking", showarrow=False)
        return _panel(fig, 360, title=title)

    work = df.copy()
    work[count_col] = pd.to_numeric(work[count_col], errors="coerce").fillna(0)
    work = work[work[count_col] > 0]
    if work.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data for this ranking", showarrow=False)
        return _panel(fig, 360, title=title)

    gap = _is_weighted_gap(count_col, value_title, title)
    universe = (
        float(universe_n)
        if universe_n is not None and not gap and float(universe_n) > 0
        else float(work[count_col].sum())
    )
    ranked = work.sort_values(count_col, ascending=False)
    remainder_name = None
    n_more = 0
    n_cats = int(len(ranked))
    vital_n = n_cats
    named_n = n_cats
    if bucket_other:
        named, tail, vital_n = pareto_named_and_tail(
            ranked, count_col, pct=PARETO_VITAL_PCT, max_named=PARETO_MAX_NAMED, universe=universe,
        )
        named_n = int(len(named))
        if not tail.empty:
            n_more = int(len(tail))
            extra = {c: pd.NA for c in named.columns}
            remainder_name = _pareto_remainder_label(named[cat_col], n_more=n_more)
            extra[cat_col] = remainder_name
            extra[count_col] = float(pd.to_numeric(tail[count_col], errors="coerce").fillna(0).sum())
            ranked = pd.concat([named, pd.DataFrame([extra])], ignore_index=True)
        else:
            ranked = named
        p = add_pareto_cumulative(ranked, count_col, universe=universe)
    else:
        p = add_pareto_cumulative(
            ranked.head(10),
            count_col,
            universe=universe,
        )
    if remainder_name:
        is_rem = p[cat_col].astype(str).eq(remainder_name)
        p = pd.concat([p.loc[~is_rem], p.loc[is_rem]], ignore_index=True)
        vals = pd.to_numeric(p[count_col], errors="coerce").fillna(0)
        total = float(universe) if universe and float(universe) > 0 else float(vals.sum())
        p["Cum_Count"] = vals.cumsum()
        p["Cum_Pct"] = np.where(total > 0, (p["Cum_Count"] / total * 100).round(1), 0.0)
    n = len(p)
    xs = np.arange(n)
    labels = [_wrap_label(v, 22, max_lines=3) for v in p[cat_col]]
    counts = p[count_col].astype(float)
    cum = p["Cum_Pct"].astype(float)
    y_max = float(counts.max()) * 1.28 if counts.max() > 0 else 1
    long_labels = bool(p[cat_col].astype(str).str.len().max() > 18)
    crowded = n >= 6
    if n >= 8:
        tick_angle = -75
    elif crowded or long_labels:
        tick_angle = -48
    else:
        tick_angle = 0
    tick_size = 9 if crowded else 10
    bottom = 176 if long_labels else (148 if crowded else 108)
    hit = np.where(cum.to_numpy() >= 80)[0]
    cut = int(hit[0]) if len(hit) else n - 1

    vol_col = _volume_col(p, count_col)
    src = p if gap else work
    sample, unit, auto_note = _n_for_panel(
        src, count_col, title=title, value_title=value_title, sample_unit=sample_unit,
    )
    if not gap:
        if universe_n is not None and int(universe_n) > 0:
            sample = int(universe_n)
        elif sample is None:
            sample = int(universe)
        if sample_unit:
            unit = sample_unit
        if n_note:
            auto_note = n_note
    elif n_note:
        auto_note = n_note if auto_note is None else auto_note
    if n_more > 0:
        if named_n >= vital_n:
            rest_note = (
                f"{named_n} named bars reach {int(PARETO_VITAL_PCT):.0f}% · "
                f"last bar = {n_more} more reasons (leftover ~{100 - int(PARETO_VITAL_PCT):.0f}%)"
            )
        else:
            rest_note = (
                f"{int(PARETO_VITAL_PCT):.0f}% takes {vital_n} reasons · showing {named_n} · "
                f"last bar = {n_more} more combined"
            )
        auto_note = f"{auto_note} · {rest_note}" if auto_note else rest_note
    sample, unit, n_note = _split_view_universe(sample, unit, universe_n, auto_note)

    has_crit = bool(critical_col and critical_col in p.columns)
    if has_crit:
        crit_flag = p[critical_col].fillna(False).astype(bool).tolist()
        colors = [
            _hex_lerp("#7A1212", "#F07167", i / max(n - 1, 1)) if flag
            else _hex_lerp("#163A66", "#8FCBFF", i / max(n - 1, 1))
            for i, flag in enumerate(crit_flag)
        ]
        hover = [
            f"{name}<br>{'CRITICAL' if flag else 'Non-critical'}<br>{value_title}: {val:,.0f}"
            for name, flag, val in zip(p[cat_col].astype(str), crit_flag, counts)
        ]
    else:
        colors = _bar_gradient(n)
        hover = [f"{name}<br>{value_title}: {val:,.0f}" for name, val in zip(p[cat_col].astype(str), counts)]
    if remainder_name and n_more > 0:
        hover = [
            (
                h + f"<br>{n_more} reasons combined — not a contact reason"
                if str(name) == remainder_name
                else h
            )
            for h, name in zip(hover, p[cat_col].astype(str))
        ]
    if vol_col:
        vol_name = _vol_label(vol_col)
        vols = pd.to_numeric(p[vol_col], errors="coerce")
        hover = [
            h + (f"<br>{vol_name}: {int(v):,}" if pd.notna(v) else "")
            for h, v in zip(hover, vols)
        ]
    if "Rate" in p.columns:
        rates = p["Rate"].tolist()
        contacts = p["Contacts"].tolist() if "Contacts" in p.columns else [None] * n
        hover = [
            h + (f"<br>Rate: {rate:.2f}%" if pd.notna(rate) else "")
            + (f"<br>Contacts: {int(con):,}" if con is not None and pd.notna(con) else "")
            for h, rate, con in zip(hover, rates, contacts)
        ]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=xs, y=counts, name=value_title, width=0.72, showlegend=not has_crit,
        marker=dict(color=colors, line=dict(color="#F4F7FB", width=1.2)),
        hovertemplate="%{customdata[1]}<extra></extra>",
        customdata=np.column_stack([
            p[cat_col].astype(str).to_numpy(),
            np.asarray(hover, dtype=object),
        ]),
    ), secondary_y=False)
    if has_crit:
        fig.add_trace(go.Bar(x=[None], y=[None], name="CRITICAL", marker=dict(color="#D64545"), hoverinfo="skip"), secondary_y=False)
        if any(not flag for flag in crit_flag):
            fig.add_trace(go.Bar(x=[None], y=[None], name="Non-critical", marker=dict(color="#2E6FBE"), hoverinfo="skip"), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=np.concatenate([[-0.5], xs + 0.5]),
        y=np.concatenate([[0.0], cum.to_numpy()]),
        name="Cumulative %",
        mode="lines+markers",
        line=dict(color=DIDI_ORANGE, width=2.5),
        marker=dict(size=8, symbol="square", color=DIDI_ORANGE),
        hovertemplate="Cumulative %{y:.1f}%<extra></extra>",
    ), secondary_y=True)
    fig.add_vline(
        x=cut + 0.5, line_dash="dot", line_color=DIDI_ORANGE, line_width=2,
    )
    fig.add_hline(y=80, line_dash="dot", line_color="rgba(255,102,0,0.45)", secondary_y=True)

    fig.update_layout(
        bargap=0.22,
        bargroupgap=0.08,
        legend=LEGEND_TOP,
        margin=dict(l=56, r=72, t=56, b=bottom),
    )
    fig.update_xaxes(
        title_text="",
        tickmode="array", tickvals=list(xs), ticktext=labels,
        tickangle=tick_angle,
        tickfont=dict(size=tick_size, color=TICK),
        range=[-0.6, n - 0.4],
        showgrid=False,
        automargin=True,
    )
    fig.update_yaxes(title_text=value_title, range=[0, y_max], showgrid=True, secondary_y=False)
    fig.update_yaxes(
        title_text="Cumulative %", range=[0, 105], ticksuffix="%",
        showgrid=False, secondary_y=True,
    )
    fig = _panel(fig, 500, title=title, n=sample, n_unit=unit, n_note=n_note)
    fig.update_xaxes(
        tickmode="array", tickvals=list(xs), ticktext=labels,
        tickangle=tick_angle,
        tickfont=dict(size=tick_size, color=TICK),
        range=[-0.6, n - 0.4],
        showgrid=False,
        automargin=True,
    )
    fig.update_yaxes(title_text=value_title, range=[0, y_max], showgrid=True, secondary_y=False)
    fig.update_yaxes(
        title_text="Cumulative %", range=[0, 105], ticksuffix="%",
        showgrid=False, secondary_y=True,
    )
    return fig


def qa_channel_compare_chart(ch_qa: dict) -> go.Figure:
    rows = []
    for ch in ("Phone", "Live Chat"):
        data = ch_qa.get(ch) or {}
        if data.get("qa_score") is None:
            continue
        rows.append({
            "Channel": ch,
            "QA": float(data["qa_score"]),
            "n": data.get("audit_count") or 0,
            "pct_fatal": data.get("pct_fatal"),
            "n_crit": data.get("n_crit_fails") or 0,
            "n_non": data.get("n_noncrit_fails") or 0,
        })
    if not rows:
        fig = go.Figure()
        fig.add_annotation(text="No Phone or Live Chat audits in this filter", showarrow=False)
        return _panel(fig, 320, title="Official QA by channel")
    frame = pd.DataFrame(rows)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=frame["Channel"], y=frame["QA"], name="QA",
        marker_color=[_status_hex(v, QA_GOAL, True) for v in frame["QA"]],
        width=0.42,
        text=[f"{v:.1f}%" for v in frame["QA"]],
        textposition="outside",
        textfont=dict(size=12, color=DIDI_TEXT),
        cliponaxis=False,
        customdata=np.column_stack([
            frame["n"].to_numpy(),
            frame["n_crit"].to_numpy(),
            frame["n_non"].to_numpy(),
        ]),
        hovertemplate=(
            "%{x}<br>QA %{y:.1f}%<br>Audits %{customdata[0]:,.0f}"
            "<br>CRITICAL fails %{customdata[1]:,.0f}"
            "<br>Non-critical fails %{customdata[2]:,.0f}<extra></extra>"
        ),
    ), secondary_y=False)
    if frame["pct_fatal"].notna().any():
        fig.add_trace(go.Scatter(
            x=frame["Channel"], y=frame["pct_fatal"], name="% audits scored 0",
            mode="lines+markers",
            line=dict(color=VOLUME_LINE, width=2.2),
            marker=dict(size=7, color=VOLUME_LINE, line=dict(width=1.2, color="#FFFFFF")),
            hovertemplate="%{x}<br>CRITICAL fail rate %{y:.1f}%<br>Audits %{customdata:,.0f}<extra></extra>",
            customdata=frame["n"],
        ), secondary_y=True)
    fig.add_hline(y=QA_GOAL, line_dash="dash", line_color=DIDI_MUTED)
    _add_traffic_legend(fig, secondary_y=False)
    fatal_max = float(pd.to_numeric(frame["pct_fatal"], errors="coerce").max() or 0)
    fig.update_yaxes(title_text="QA score %", range=[0, SCORE_LABEL_MAX], secondary_y=False)
    fig.update_yaxes(
        title_text="% audits scored 0",
        range=[0, max(12.0, fatal_max * 1.45)],
        ticksuffix="%",
        showgrid=False,
        secondary_y=True,
    )
    fig.update_layout(
        xaxis=dict(title=""),
        legend=LEGEND_TOP,
        margin=dict(l=56, r=64, t=52, b=48),
        bargap=0.42,
    )
    return _panel(fig, 360, title="Official QA by channel", n=_sum_n(frame, "n"), n_unit="audits")


def cr_group_hbar(
    df: pd.DataFrame,
    name_col: str,
    value_col: str,
    pct_col: str | None = None,
    x_title: str = "Count",
    title: str = "Contact reason Lv1 (group)",
    universe_n: int | None = None,
    n_note: str | None = None,
    sample_unit: str | None = None,
) -> go.Figure:
    if df.empty or name_col not in df.columns or value_col not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No group data in the current filter", showarrow=False)
        return _panel(fig, 260, title=title)
    plot = df.copy()
    plot[value_col] = pd.to_numeric(plot[value_col], errors="coerce").fillna(0)
    plot = plot[plot[value_col] > 0].sort_values(value_col, ascending=True)
    if plot.empty:
        fig = go.Figure()
        fig.add_annotation(text="No group data in the current filter", showarrow=False)
        return _panel(fig, 260, title=title)
    labels = [_wrap_label(x, 28) for x in plot[name_col]]
    if pct_col and pct_col in plot.columns:
        text = [f"{v:,.0f}  ({p:.1f}%)" for v, p in zip(plot[value_col], plot[pct_col])]
    else:
        text = [f"{v:,.0f}" if pd.notna(v) else "—" for v in plot[value_col]]
    fig = go.Figure(go.Bar(
        y=labels, x=plot[value_col], orientation="h",
        marker_color=CHART_COLORS["bar"],
        text=text, textposition="outside", textfont=dict(size=9, color=DIDI_TEXT),
        cliponaxis=False,
        customdata=plot[name_col].astype(str),
        hovertemplate="%{customdata}<br>%{x:,}<extra></extra>",
    ))
    xmax = float(pd.to_numeric(plot[value_col], errors="coerce").max() or 0)
    fig.update_layout(
        xaxis=dict(title=x_title, range=[0, xmax * 1.32 if xmax else 1]),
        yaxis_title="",
        margin=dict(l=180, r=88, t=12, b=48),
    )
    sample, unit, auto_note = _n_for_panel(
        plot, value_col, title=title, value_title=x_title, sample_unit=sample_unit,
    )
    if universe_n is not None and int(universe_n) > 0 and not _is_weighted_gap(value_col, x_title, title):
        sample = int(universe_n)
        if sample_unit:
            unit = sample_unit
        if n_note:
            auto_note = n_note
    elif n_note and not _is_weighted_gap(value_col, x_title, title):
        auto_note = n_note
    return _panel(
        fig, _hbar_height(len(plot), 36, 90), title=title,
        n=sample, n_unit=unit, n_note=auto_note,
    )


def qa_recontact_scatter(df: pd.DataFrame) -> go.Figure:
    plot = _pair_scatter(df, "QA_Score", "Recontact_Rate")
    if plot.empty:
        n = 0
        fig = go.Figure()
        fig.add_annotation(
            text=f"Only {n} contact reason Lv4 (detail) name(s) have both QA and recontact in this filter",
            showarrow=False,
        )
        return _panel(fig, 260, title="Correlation QA vs Recontact")
    fig = go.Figure(go.Scatter(
        x=plot["QA_Score"], y=plot["Recontact_Rate"], mode="markers",
        marker=dict(size=9, color=CHART_COLORS["recontact"], opacity=0.85),
        customdata=plot["CR_Lv4"].astype(str) if "CR_Lv4" in plot.columns else None,
        hovertext=plot["CR_Lv4"] if "CR_Lv4" in plot.columns else None,
        hoverinfo="text+x+y",
        name="Contact reasons",
    ))
    _add_ols_trendline(fig, plot["QA_Score"], plot["Recontact_Rate"])
    fig.add_vline(x=QA_GOAL, line_dash="dot", line_color=DIDI_MUTED)
    fig.add_hline(y=RECONTACT_GOAL, line_dash="dot", line_color=DIDI_MUTED)
    fig.update_layout(
        xaxis_title="QA Score %", yaxis_title="Recontact Rate %",
        margin=dict(l=56, r=28, t=16, b=56),
    )
    return _panel(
        fig, 260, title="Correlation QA vs Recontact",
        n=_len_n(plot), n_unit="contact reasons Lv4 (detail)",
    )


def csat_recontact_scatter(df: pd.DataFrame) -> go.Figure:
    plot = _pair_scatter(df, "CSAT_Pct", "Recontact_Rate")
    if plot.empty:
        n = 0
        fig = go.Figure()
        fig.add_annotation(
            text=f"Only {n} contact reason Lv4 (detail) name(s) have both CSAT and recontact in this filter",
            showarrow=False,
        )
        return _panel(fig, 260, title="Correlation CSAT vs Recontact")
    names = plot["CR_Lv4"].astype(str) if "CR_Lv4" in plot.columns else pd.Series([""] * len(plot))
    size_col = "Feedback" if "Feedback" in plot.columns else None
    sizes = (np.clip(plot[size_col] / 80, 8, 28) if size_col else 10)
    fig = go.Figure(go.Scatter(
        x=plot["CSAT_Pct"], y=plot["Recontact_Rate"],
        mode="markers",
        marker=dict(size=sizes, color=CHART_COLORS["csat"], opacity=0.88,
                    line=dict(width=0.6, color="#FFFFFF")),
        customdata=names,
        hovertemplate="%{customdata}<br>CSAT %{x:.1f}%<br>Recontact %{y:.2f}%<extra></extra>",
        name="Lv4 (detail)",
        showlegend=False,
        cliponaxis=False,
    ))
    _add_ols_trendline(fig, plot["CSAT_Pct"], plot["Recontact_Rate"])
    fig.add_vline(x=CSAT_GOAL, line_dash="dot", line_color=DIDI_MUTED)
    fig.add_hline(y=RECONTACT_GOAL, line_dash="dot", line_color=DIDI_MUTED)
    fig.update_layout(
        xaxis_title="CSAT %", yaxis_title="Recontact Rate %",
        margin=dict(l=56, r=88, t=28, b=56),
    )
    return _panel(
        fig, 420, title="Correlation CSAT vs Recontact",
        n=_len_n(plot), n_unit="contact reasons Lv4 (detail)",
    )


def csat_star_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No CSAT data", showarrow=False)
        return _panel(fig, 200, title="CSAT by star rating")

    color_map = {
        "5 Stars": STATUS_COLORS["green"],
        "4 Stars": STATUS_COLORS["green"],
        "3 Stars": STATUS_COLORS["amber"],
        "2 Stars": STATUS_COLORS["red"],
        "1 Star": STATUS_COLORS["red"],
    }
    fills = [color_map.get(str(r), STATUS_COLORS["neutral"]) for r in df["Rating"]]
    counts = pd.to_numeric(df["Count"], errors="coerce") if "Count" in df.columns else pd.Series([np.nan] * len(df))
    fig = go.Figure(go.Bar(
        y=df["Rating"], x=df["Pct"], orientation="h", marker_color=fills,
        text=[
            f"{v:.1f}% · {int(c):,}" if pd.notna(c) else f"{v:.1f}%"
            for v, c in zip(df["Pct"], counts)
        ],
        textposition="outside", textfont=dict(size=9, color=DIDI_TEXT),
        customdata=counts.fillna(0),
        hovertemplate="%{y}<br>%{x:.1f}% · %{customdata:,.0f} surveys<extra></extra>",
    ))
    fig.update_layout(xaxis_title="% of Surveys", margin=dict(l=68, r=88, t=8, b=24))
    return _panel(fig, 220, title="CSAT by star rating", n=_sum_n(df, "Count"), n_unit="surveys")


def aht_metric_scatter(
    df: pd.DataFrame,
    y_col: str,
    *,
    y_title: str,
    title: str,
    y_goal: float | None = None,
    lower_better: bool = False,
    empty_text: str = (
        "0 shared contact reason Lv4 (detail) names have both handle time and this KPI"
    ),
) -> go.Figure:
    """AHT (minutes) vs a KPI at contact reason Lv4 (detail), colored by channel."""
    plot = df.copy() if df is not None and not df.empty else pd.DataFrame()
    if not plot.empty and y_col in plot.columns and "AHT_min" in plot.columns:
        plot = plot.dropna(subset=["AHT_min", y_col])
    else:
        plot = pd.DataFrame()
    if plot.empty:
        fig = go.Figure()
        fig.add_annotation(text=empty_text, showarrow=False)
        return _panel(fig, 280, title=title)

    fig = go.Figure()
    channels = plot["Channel"].dropna().astype(str).unique().tolist() if "Channel" in plot.columns else [None]
    palette = {"Phone": CHART_COLORS["qa"], "Live Chat": CHART_COLORS["csat"]}
    nmax = float(plot["n"].max()) if "n" in plot.columns and plot["n"].max() else 1.0
    for ch in channels:
        sub = plot[plot["Channel"].astype(str) == ch] if ch is not None else plot
        if sub.empty:
            continue
        sizes = (
            np.clip(sub["n"] / nmax * 18 + 7, 8, 22)
            if "n" in sub.columns else 10
        )
        hover_name = sub["CR_Lv4"].astype(str) if "CR_Lv4" in sub.columns else sub.index.astype(str)
        n_vals = sub["n"] if "n" in sub.columns else pd.Series([""] * len(sub), index=sub.index)
        fig.add_trace(go.Scatter(
            x=sub["AHT_min"], y=sub[y_col], mode="markers",
            name=str(ch) if ch is not None else y_title,
            marker=dict(
                size=sizes,
                color=palette.get(str(ch), CHART_COLORS["blue"]),
                opacity=0.85,
                line=dict(width=0.8, color="#F4F7FB"),
            ),
            customdata=np.stack([hover_name, n_vals], axis=1),
            hovertemplate=(
                "%{customdata[0]}<br>AHT %{x:.1f} min<br>"
                + y_title + " %{y:.1f}<br>n=%{customdata[1]}<extra></extra>"
            ),
        ))
    _add_ols_trendline(fig, plot["AHT_min"], plot[y_col])
    if y_goal is not None:
        fig.add_hline(y=y_goal, line_dash="dot", line_color=DIDI_MUTED)
    yvals = pd.to_numeric(plot[y_col], errors="coerce")
    if lower_better:
        lo, hi = _rc_axis(plot, y_col)
        yaxis = dict(range=[lo, hi])
    else:
        lo = max(0.0, float(yvals.min()) - 8) if yvals.notna().any() else 0.0
        yaxis = dict(range=[lo, 105])
    fig.update_layout(
        xaxis_title="AHT (minutes)",
        yaxis_title=y_title,
        legend=dict(
            orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom",
            font=dict(size=10, color=DIDI_TEXT), bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=56, r=28, t=56, b=48),
        yaxis=yaxis,
        dragmode=False,
    )
    return _panel(
        fig, 320, title=title,
        n=_len_n(plot), n_unit="contact reasons Lv4 (detail)",
    )


def qa_aht_scatter(df: pd.DataFrame) -> go.Figure:
    """QA score vs handle time. Each point is a contact reason Lv4 (detail), optionally split by channel."""
    return aht_metric_scatter(
        df, "QA_Score",
        y_title="QA score %",
        title="QA score vs AHT by contact reason Lv4 (detail)",
        y_goal=QA_GOAL,
        empty_text="0 contact reason Lv4 (detail) names have QA Duration in this filter",
    )


def score_volume_combo(
    df: pd.DataFrame,
    cat_col: str,
    score_col: str,
    vol_col: str,
    *,
    goal: float | None = None,
    title: str | None = None,
    score_title: str = "Score %",
    vol_title: str = "Volume",
    higher_better: bool = True,
    bar_color: str | None = None,
    force_horizontal: bool = False,
    sample_unit: str | None = None,
    n_note: str | None = None,
) -> go.Figure:
    """Bars = KPI (one color, matches legend), line = volume. Long names go horizontal."""
    if df is None or df.empty or cat_col not in df.columns or score_col not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No data in the current filter", showarrow=False)
        return _panel(fig, 320, title=title)
    plot = df.dropna(subset=[score_col]).copy().reset_index(drop=True)
    if plot.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data in the current filter", showarrow=False)
        return _panel(fig, 320, title=title)
    plot = _sort_tenure_plot(plot, cat_col)
    n = len(plot)
    scores = pd.to_numeric(plot[score_col], errors="coerce")
    vols = pd.to_numeric(plot[vol_col], errors="coerce") if vol_col in plot.columns else pd.Series([np.nan] * n)
    names = plot[cat_col].astype(str)
    long = bool(force_horizontal or ((not _is_tenure_col(cat_col)) and (names.str.len().max() > 22 or n > 7)))
    solid = bar_color or CHART_COLORS.get("csat") or "#F2A900"

    if long:
        if not _is_tenure_col(cat_col):
            plot = plot.assign(_s=scores, _v=vols).sort_values("_s", ascending=True)
        else:
            plot = plot.assign(_s=scores, _v=vols)
        labels = [_wrap_label(x, 34, max_lines=2) for x in plot[cat_col]]
        fills = (
            [_status_hex(v, goal, higher_better) for v in plot["_s"]]
            if goal is not None else solid
        )
        fig = go.Figure(go.Bar(
            y=labels, x=plot["_s"], orientation="h", name=score_title,
            showlegend=goal is None,
            marker_color=fills,
            text=[
                f"{s:.1f}% · {int(v):,}" if pd.notna(v) else (f"{s:.1f}%" if pd.notna(s) else "—")
                for s, v in zip(plot["_s"], plot["_v"])
            ],
            textposition="outside", textfont=dict(size=10, color=DIDI_TEXT),
            cliponaxis=False,
            customdata=np.column_stack([
                plot[cat_col].astype(str).to_numpy(),
                plot["_v"].fillna(0).to_numpy(),
            ]),
            hovertemplate=(
                "%{customdata[0]}<br>" + score_title + " %{x:.1f}%<br>"
                + vol_title + " %{customdata[1]:,.0f}<extra></extra>"
            ),
        ))
        if goal is not None:
            fig.add_vline(x=goal, line_dash="dash", line_color=DIDI_MUTED)
            _add_traffic_legend(fig)
        fig.update_layout(
            xaxis=dict(title=score_title, range=[0, SCORE_LABEL_MAX]),
            yaxis=dict(title="", autorange="reversed" if _is_tenure_col(cat_col) else True),
            showlegend=True,
            legend=LEGEND_TOP,
            margin=dict(l=200, r=96, t=48, b=40),
        )
        sample, unit, auto_note = _n_for_panel(
            plot, vol_col, title=title, value_title=vol_title,
            sample_unit=sample_unit,
        )
        return _panel(
            fig, _hbar_height(n, 32, 90), title=title,
            n=sample, n_unit=unit, n_note=n_note or auto_note,
        )

    xs = list(range(n))
    labels = [_wrap_label(x, 16) for x in names]
    fills = (
        [_status_hex(v, goal, higher_better) for v in scores]
        if goal is not None else solid
    )
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=xs, y=scores, name=score_title,
        showlegend=goal is None,
        marker_color=fills,
        text=[f"{v:.1f}%" if pd.notna(v) else "" for v in scores],
        textposition="outside",
        textfont=dict(size=11, color=DIDI_TEXT),
        cliponaxis=False,
        customdata=np.column_stack([names.to_numpy(), vols.fillna(0).to_numpy()]),
        hovertemplate="%{customdata[0]}<br>" + score_title + " %{y:.1f}%<br>" + vol_title + " %{customdata[1]:,.0f}<extra></extra>",
    ), secondary_y=False)
    if vols.notna().any():
        fig.add_trace(go.Scatter(
            x=xs, y=vols, name=vol_title, mode="lines+markers",
            line=dict(color=VOLUME_LINE, width=2.2),
            marker=dict(size=6, color=VOLUME_LINE, line=dict(width=1.2, color="#FFFFFF")),
            hovertemplate=vol_title + " %{y:,.0f}<extra></extra>",
        ), secondary_y=True)
    if goal is not None:
        fig.add_hline(y=goal, line_dash="dash", line_color=DIDI_MUTED, annotation_text=f"Goal {goal:g}")
        _add_traffic_legend(fig, secondary_y=False)
    fig.update_xaxes(
        tickmode="array", tickvals=xs, ticktext=labels,
        tickangle=0 if n <= 6 else -25,
        title="",
    )
    fig.update_yaxes(title_text=score_title, range=[0, SCORE_LABEL_MAX], secondary_y=False)
    fig.update_yaxes(title_text=vol_title, showgrid=False, rangemode="tozero", secondary_y=True)
    fig.update_layout(
        legend=LEGEND_TOP,
        margin=dict(l=56, r=56, t=56, b=72),
        bargap=0.35,
    )
    sample, unit, auto_note = _n_for_panel(
        plot, vol_col, title=title, value_title=vol_title,
        sample_unit=sample_unit,
    )
    return _panel(fig, 340, title=title, n=sample, n_unit=unit, n_note=n_note or auto_note)


def grouped_qa_csat_chart(
    df: pd.DataFrame,
    cat_col: str,
    *,
    qa_col: str = "QA_Score",
    csat_col: str = "CSAT_Score",
    n_col: str | None = "n",
    title: str = "QA and CSAT",
    top_n: int | None = 10,
    universe_n: int | None = None,
    n_note: str | None = None,
) -> go.Figure:
    if df is None or df.empty or cat_col not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No rows in the current filter", showarrow=False)
        return _panel(fig, 340, title=title)
    plot = df.head(int(top_n)).copy() if top_n is not None else df.copy()
    labels = [_wrap_label(x, 16) for x in plot[cat_col]]
    fig = go.Figure()
    if qa_col in plot.columns:
        fig.add_trace(go.Bar(
            x=labels, y=plot[qa_col], name="QA",
            marker_color=CHART_COLORS["qa"],
            customdata=plot[cat_col].astype(str),
            hovertemplate="%{customdata}<br>QA %{y:.1f}%<extra></extra>",
        ))
    if csat_col in plot.columns:
        fig.add_trace(go.Bar(
            x=labels, y=plot[csat_col], name="CSAT",
            marker_color=CHART_COLORS["csat"],
            customdata=plot[cat_col].astype(str),
            hovertemplate="%{customdata}<br>CSAT %{y:.1f}%<extra></extra>",
        ))
    fig.add_hline(y=QA_GOAL, line_dash="dash", line_color=DIDI_MUTED, annotation_text="Goal 85")
    fig.update_layout(
        barmode="group",
        yaxis=dict(title="Score %", range=[0, 108]),
        xaxis=dict(title="", tickangle=-20),
        legend=LEGEND_TOP,
        margin=dict(l=56, r=28, t=52, b=110),
        bargap=0.28,
    )
    if n_col:
        sample, unit, auto_note = _n_for_panel(plot, n_col, title=title, sample_unit="audits")
    else:
        sample, unit, auto_note = _len_n(plot), "audits", None
    if n_note:
        auto_note = n_note
    sample, unit, auto_note = _split_view_universe(sample, unit, universe_n, auto_note)
    return _panel(fig, 360, title=title, n=sample, n_unit=unit, n_note=auto_note)


def channel_kpi_combo(df: pd.DataFrame) -> go.Figure:
    """QA + CSAT bars, recontact as a line. Overall is a mix, not a third channel."""
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No channel mix in this filter", showarrow=False)
        return _panel(fig, 340, title="QA, CSAT and recontact by channel")
    plot = df.copy()
    overall = plot[plot["Segment"].astype(str).eq("Overall")] if "Segment" in plot.columns else plot.iloc[0:0]
    channels = plot[~plot["Segment"].astype(str).eq("Overall")] if "Segment" in plot.columns else plot
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if channels.empty:
        fig.add_annotation(text="No Phone / Live Chat rows in this filter", showarrow=False)
        return _panel(fig, 340, title="QA, CSAT and recontact by channel")
    fig.add_trace(go.Bar(
        x=channels["Segment"], y=channels["QA_Score"], name="QA",
        marker_color=CHART_COLORS["qa"],
        customdata=channels["Segment"].astype(str),
        hovertemplate="%{customdata}<br>QA %{y:.1f}%<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Bar(
        x=channels["Segment"], y=channels["CSAT_Score"], name="CSAT",
        marker_color=CHART_COLORS["csat"],
        customdata=channels["Segment"].astype(str),
        hovertemplate="%{customdata}<br>CSAT %{y:.1f}%<extra></extra>",
    ), secondary_y=False)
    if "Recontact_Rate" in channels.columns and channels["Recontact_Rate"].notna().any():
        fig.add_trace(go.Scatter(
            x=channels["Segment"], y=channels["Recontact_Rate"], name="Recontact",
            mode="lines+markers",
            line=dict(color=CHART_COLORS["recontact"], width=2.6),
            marker=dict(size=9),
            customdata=channels["Segment"].astype(str),
            hovertemplate="%{customdata}<br>Recontact %{y:.2f}%<extra></extra>",
        ), secondary_y=True)
    fig.add_hline(y=QA_GOAL, line_dash="dash", line_color=DIDI_MUTED)
    fig.update_yaxes(title_text="QA / CSAT %", range=[0, SCORE_LABEL_MAX], secondary_y=False)
    fig.update_yaxes(title_text="Recontact %", range=_rc_axis(channels), showgrid=False, secondary_y=True)
    top_pad = 52
    if not overall.empty:
        row = overall.iloc[0]
        qa_txt = f"{float(row['QA_Score']):.1f}%" if pd.notna(row.get("QA_Score")) else "—"
        cs_txt = f"{float(row['CSAT_Score']):.1f}%" if pd.notna(row.get("CSAT_Score")) else "—"
        rc_txt = f"{float(row['Recontact_Rate']):.2f}%" if pd.notna(row.get("Recontact_Rate")) else "—"
        fig.add_annotation(
            text=f"Overall mix (not a channel): QA {qa_txt} · CSAT {cs_txt} · Recontact {rc_txt}",
            xref="paper", yref="paper", x=0.5, y=1.16, showarrow=False,
            font=dict(size=11, color=DIDI_MUTED),
        )
        top_pad = 72
    fig.update_layout(
        barmode="group",
        legend=LEGEND_TOP,
        margin=dict(l=56, r=56, t=top_pad, b=48),
        bargap=0.28,
    )
    return _panel(
        fig, 360, title="QA, CSAT and recontact by channel",
        n=_sum_n(channels, "QA_N", "n"), n_unit="audits",
    )


def hbar_score_chart(
    df: pd.DataFrame,
    name_col: str,
    score_col: str,
    n_col: str,
    *,
    goal: float = QA_GOAL,
    title: str = "Score",
    extra_col: str | None = None,
    universe_n: int | None = None,
    n_note: str | None = None,
    sample_unit: str = "audits",
) -> go.Figure:
    if df is None or df.empty or name_col not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No rows below goal in this filter", showarrow=False)
        return _panel(fig, 300, title=title)
    plot = df.sort_values(score_col, ascending=True).copy()
    labels = [_wrap_label(x, 28, max_lines=2) for x in plot[name_col]]
    n = len(plot)
    colors = [_status_hex(v, goal, True) for v in plot[score_col]]
    extra = plot[extra_col] if extra_col and extra_col in plot.columns else pd.Series([""] * n)
    n_vals = pd.to_numeric(plot[n_col], errors="coerce") if n_col in plot.columns else pd.Series([np.nan] * n)
    fig = go.Figure(go.Bar(
        y=labels, x=plot[score_col], orientation="h",
        marker=dict(color=colors, line=dict(color="#F4F7FB", width=1)),
        text=[
            f"{v:.1f}%  n={int(nv):,}" if pd.notna(nv) else f"{v:.1f}%"
            for v, nv in zip(plot[score_col], n_vals)
        ],
        textposition="outside", textfont=dict(size=10, color=DIDI_TEXT),
        cliponaxis=False,
        customdata=np.column_stack([
            plot[name_col].astype(str).to_numpy(),
            n_vals.fillna(0).to_numpy(),
            extra.astype(str).to_numpy(),
        ]),
        hovertemplate="%{customdata[0]}<br>Score %{x:.1f}%<br>n %{customdata[1]:.0f}<br>%{customdata[2]}<extra></extra>",
    ))
    fig.add_vline(x=goal, line_dash="dash", line_color=DIDI_MUTED)
    _add_traffic_legend(fig)
    fig.update_layout(
        xaxis=dict(title="QA %", range=[0, SCORE_LABEL_MAX]),
        yaxis=dict(title=""),
        showlegend=True,
        legend=LEGEND_TOP,
        margin=dict(l=180, r=96, t=52, b=40),
    )
    sample, unit, auto_note = _n_for_panel(
        plot, n_col, title=title, sample_unit=sample_unit,
    )
    if n_note:
        auto_note = n_note
    sample, unit, auto_note = _split_view_universe(sample, unit, universe_n, auto_note)
    return _panel(
        fig, _hbar_height(n, 28, 90), title=title,
        n=sample, n_unit=unit, n_note=auto_note,
    )


def voc_bar_chart(df: pd.DataFrame) -> go.Figure:
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No classifiable 1★–3★ comments", showarrow=False)
        return _panel(fig, 280, title="Themes in 1–3★ comments")
    plot = df.sort_values("Mentions", ascending=True)
    n_low = int(plot["Total_Low"].iloc[0]) if "Total_Low" in plot.columns and pd.notna(plot["Total_Low"].iloc[0]) else int(plot["Mentions"].sum())
    fig = go.Figure(go.Bar(
        y=[_wrap_label(x, 32, max_lines=2) for x in plot["Theme"]],
        x=plot["Pct"],
        orientation="h",
        marker_color=_bar_gradient(len(plot), "#7A3B00", "#F2A900"),
        text=[f"{int(m):,} of {n_low:,}" for m in plot["Mentions"]],
        textposition="outside", textfont=dict(size=10, color=DIDI_TEXT),
        cliponaxis=False,
        customdata=np.column_stack([
            plot["Theme"].astype(str).to_numpy(),
            plot["Mentions"].to_numpy(),
            np.full(len(plot), n_low),
        ]),
        hovertemplate="%{customdata[0]}<br>%{customdata[1]:,.0f} of %{customdata[2]:,.0f} 1–3★ surveys with comments (%{x:.1f}%)<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="% of 1–3★ surveys with comments", yaxis_title="",
        margin=dict(l=180, r=72, t=12, b=40),
    )
    return _panel(
        fig, _hbar_height(len(plot), 30, 80), title="Themes in 1–3★ comments",
        n=n_low, n_unit="1–3★ surveys with comments",
    )


def corr_r_bars(df: pd.DataFrame, title: str = "R²") -> go.Figure:
    if df is None or df.empty or "Pearson_r" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No overlapping names for R²", showarrow=False)
        return _panel(fig, 260, title=title)
    plot = df.copy()
    if "Slice" not in plot.columns:
        plot["Slice"] = "Lv4"
    if "R2" not in plot.columns:
        plot["R2"] = pd.to_numeric(plot["Pearson_r"], errors="coerce") ** 2
    plot["Label"] = plot["Pair"].astype(str) + " · " + plot["Slice"].astype(str)
    plot = plot.sort_values("R2", ascending=True)

    def _pair_color(pair: object, r) -> str:
        try:
            if pd.notna(r) and float(r) < 0:
                return STATUS_COLORS["red"]
        except (TypeError, ValueError):
            pass
        p = str(pair)
        if "QA" in p:
            return CHART_COLORS["qa"]
        if "CSAT" in p:
            return CHART_COLORS["csat"]
        return CHART_COLORS["recontact"]

    colors = [_pair_color(p, r) for p, r in zip(plot["Pair"], plot["Pearson_r"])]
    labels = []
    for r2, r in zip(plot["R2"], plot["Pearson_r"]):
        if pd.isna(r2):
            labels.append("—")
            continue
        if pd.notna(r) and abs(float(r)) >= 0.05:
            side = "−" if float(r) < 0 else "+"
            labels.append(f"{float(r2):.2f} {side}")
        else:
            labels.append(f"{float(r2):.2f}")
    fig = go.Figure(go.Bar(
        y=[_wrap_label(x, 28) for x in plot["Label"]],
        x=plot["R2"],
        orientation="h",
        name="R²",
        showlegend=False,
        marker_color=colors,
        text=labels,
        textposition="outside", textfont=dict(size=10, color=DIDI_TEXT),
        cliponaxis=False,
        customdata=plot["N_CR"] if "N_CR" in plot.columns else None,
        hovertemplate="%{y}<br>R² %{x:.2f}<br>N %{customdata}<extra></extra>",
    ))
    for name, color in (
        ("QA", CHART_COLORS["qa"]),
        ("CSAT", CHART_COLORS["csat"]),
        ("Recontact", CHART_COLORS["recontact"]),
    ):
        fig.add_trace(go.Bar(
            x=[0], y=[plot["Label"].iloc[0]],
            orientation="h", name=name,
            marker_color=color,
            showlegend=True,
            visible="legendonly",
            hoverinfo="skip",
        ))
    fig.update_layout(
        xaxis=dict(title="R²", range=[-0.02, 1.15]),
        yaxis_title="",
        legend=LEGEND_TOP,
        margin=dict(l=200, r=64, t=52, b=40),
        showlegend=True,
    )
    return _panel(fig, _hbar_height(len(plot), 28, 100), title=title)


def qa_aht_combo(
    df: pd.DataFrame,
    cat_col: str,
    *,
    title: str | None = None,
    top_n: int | None = 12,
) -> go.Figure:
    """QA bars + AHT (minutes) line at a contact-reason or channel grain. Association only."""
    empty = go.Figure()
    empty.add_annotation(text="No Duration in this filter", showarrow=False)
    if df is None or df.empty or cat_col not in df.columns or "QA_Score" not in df.columns or "AHT_min" not in df.columns:
        return _panel(empty, 320, title=title)
    plot = df.copy()
    plot["QA_Score"] = pd.to_numeric(plot["QA_Score"], errors="coerce")
    plot["AHT_min"] = pd.to_numeric(plot["AHT_min"], errors="coerce")
    plot = plot.dropna(subset=["QA_Score", "AHT_min"])
    if "n" in plot.columns:
        plot = plot.sort_values("n", ascending=False)
    if top_n is not None:
        plot = plot.head(int(top_n))
    if plot.empty:
        return _panel(empty, 320, title=title)
    n = len(plot)
    names = plot[cat_col].astype(str)
    labels = [_wrap_label(x, 18) for x in names]
    crowded = n >= 6
    tick_angle = -55 if crowded else 0
    hover = [
        f"{name}<br>QA {qa:.1f}%<br>AHT {aht:.1f} min"
        + (f"<br>{int(nn):,} audits" if pd.notna(nn) else "")
        for name, qa, aht, nn in zip(
            names,
            plot["QA_Score"],
            plot["AHT_min"],
            plot["n"] if "n" in plot.columns else [np.nan] * n,
        )
    ]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=labels, y=plot["QA_Score"], name="QA",
        marker_color=CHART_COLORS["qa"],
        text=[f"{v:.1f}%" for v in plot["QA_Score"]],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(size=11, color="#FFFFFF"),
        customdata=np.column_stack([names.to_numpy(), np.asarray(hover, dtype=object)]),
        hovertemplate="%{customdata[1]}<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=labels, y=plot["AHT_min"], name="AHT (min)",
        mode="lines+markers",
        line=dict(color=DIDI_ORANGE, width=2.5),
        marker=dict(size=9, color=DIDI_ORANGE),
        customdata=np.column_stack([names.to_numpy(), np.asarray(hover, dtype=object)]),
        hovertemplate="%{customdata[1]}<extra></extra>",
    ), secondary_y=True)
    fig.add_hline(y=QA_GOAL, line_dash="dash", line_color=DIDI_MUTED, secondary_y=False)
    aht_hi = max(8.0, float(plot["AHT_min"].max() or 0) * 1.25)
    fig.update_yaxes(title_text="QA %", range=[0, 108], secondary_y=False)
    fig.update_yaxes(title_text="AHT (min)", range=[0, aht_hi], showgrid=False, secondary_y=True)
    fig.update_xaxes(tickangle=tick_angle, tickfont=dict(size=10 if crowded else 11))
    fig.update_layout(
        legend=LEGEND_TOP,
        margin=dict(l=56, r=56, t=52, b=120 if crowded else 48),
        bargap=0.32,
    )
    return _panel(fig, 360, title=title, n=_sum_n(plot, "n", "Audits"), n_unit="audits")


def aht_channel_combo(df: pd.DataFrame, title: str | None = None) -> go.Figure:
    return qa_aht_combo(df, "Channel", title=title, top_n=None)


def kpi_combo_by_cr(
    df: pd.DataFrame,
    cat_col: str,
    *,
    title: str,
    grain: str = "contact reasons",
    top_n: int = 12,
    horizontal: bool = False,
    min_qa_n: int = CR_COMBO_MIN_QA_N,
    min_csat_n: int = RANKING_CSAT_MIN_N,
    min_rc_n: int = RANKING_CSAT_MIN_N,
) -> go.Figure:
    """Grouped QA + CSAT bars at a contact-reason grain. Thin samples are not drawn."""
    empty = go.Figure()
    empty.add_annotation(text="No contact-reason KPI rows in this filter", showarrow=False)
    if df is None or df.empty or cat_col not in df.columns:
        return _panel(empty, 320, title=title)
    plot = df.copy()
    for col in ("QA_Score", "CSAT_Score", "CSAT_Pct", "Recontact_Rate", "QA_N", "Feedback", "Contacts"):
        if col in plot.columns:
            plot[col] = pd.to_numeric(plot[col], errors="coerce")
    if "CSAT_Score" not in plot.columns and "CSAT_Pct" in plot.columns:
        plot["CSAT_Score"] = plot["CSAT_Pct"]
    if "QA_N" in plot.columns and "QA_Score" in plot.columns:
        plot.loc[plot["QA_N"].fillna(0) < min_qa_n, "QA_Score"] = np.nan
    if "Feedback" in plot.columns and "CSAT_Score" in plot.columns:
        plot.loc[plot["Feedback"].fillna(0) < min_csat_n, "CSAT_Score"] = np.nan
    if "Contacts" in plot.columns and "Recontact_Rate" in plot.columns:
        plot.loc[plot["Contacts"].fillna(0) < min_rc_n, "Recontact_Rate"] = np.nan
    vol = None
    for cand in ("Feedback", "Contacts", "QA_N"):
        if cand in plot.columns:
            vol = cand
            break
    if vol:
        plot = plot.sort_values(vol, ascending=False)
    if top_n:
        plot = plot.head(int(top_n))
    qa_ok = plot["QA_Score"].notna() if "QA_Score" in plot.columns else pd.Series(False, index=plot.index)
    cs_ok = plot["CSAT_Score"].notna() if "CSAT_Score" in plot.columns else pd.Series(False, index=plot.index)
    plot = plot.loc[qa_ok | cs_ok].copy()
    if plot.empty:
        return _panel(empty, 320, title=title)
    names = plot[cat_col].astype(str)
    rc = pd.to_numeric(plot["Recontact_Rate"], errors="coerce") if "Recontact_Rate" in plot.columns else None
    long = bool(horizontal or names.str.len().max() > 18 or len(plot) > 8)
    if long:
        plot = plot.iloc[::-1]
        labels = [_wrap_label(x, 34, max_lines=2) for x in plot[cat_col]]
        names = plot[cat_col].astype(str)
        rc = pd.to_numeric(plot["Recontact_Rate"], errors="coerce") if "Recontact_Rate" in plot.columns else None
        hover_rc = [f"{v:.1f}%" if pd.notna(v) else "—" for v in rc] if rc is not None else ["—"] * len(plot)
        fig = go.Figure()
        if "QA_Score" in plot.columns and plot["QA_Score"].notna().any():
            fig.add_trace(go.Bar(
                y=labels, x=plot["QA_Score"], orientation="h", name="QA",
                marker_color=CHART_COLORS["qa"],
                customdata=np.column_stack([names.to_numpy(), np.asarray(hover_rc, dtype=object)]),
                hovertemplate="%{customdata[0]}<br>QA %{x:.1f}%<br>Recontact %{customdata[1]}<extra></extra>",
            ))
        if "CSAT_Score" in plot.columns and plot["CSAT_Score"].notna().any():
            fig.add_trace(go.Bar(
                y=labels, x=plot["CSAT_Score"], orientation="h", name="CSAT",
                marker_color=CHART_COLORS["csat"],
                customdata=np.column_stack([names.to_numpy(), np.asarray(hover_rc, dtype=object)]),
                hovertemplate="%{customdata[0]}<br>CSAT %{x:.1f}%<br>Recontact %{customdata[1]}<extra></extra>",
            ))
        fig.add_vline(x=QA_GOAL, line_dash="dash", line_color=DIDI_MUTED)
        fig.update_layout(
            barmode="group",
            xaxis=dict(title="QA / CSAT %", range=[0, SCORE_LABEL_MAX]),
            yaxis=dict(title=""),
            legend=LEGEND_TOP,
            margin=dict(l=200, r=72, t=52, b=40),
            dragmode=False,
        )
        return _panel(
            fig, _hbar_height(len(plot), 28, 90), title=title,
            n=_len_n(plot), n_unit=grain,
        )
    labels = [_wrap_label(x, 22, max_lines=2) for x in plot[cat_col]]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if "QA_Score" in plot.columns and plot["QA_Score"].notna().any():
        fig.add_trace(go.Bar(
            x=labels, y=plot["QA_Score"], name="QA",
            marker_color=CHART_COLORS["qa"],
            customdata=names,
            hovertemplate="%{customdata}<br>QA %{y:.1f}%<extra></extra>",
        ), secondary_y=False)
    if "CSAT_Score" in plot.columns and plot["CSAT_Score"].notna().any():
        fig.add_trace(go.Bar(
            x=labels, y=plot["CSAT_Score"], name="CSAT",
            marker_color=CHART_COLORS["csat"],
            customdata=names,
            hovertemplate="%{customdata}<br>CSAT %{y:.1f}%<extra></extra>",
        ), secondary_y=False)
    if "Recontact_Rate" in plot.columns and plot["Recontact_Rate"].notna().any():
        fig.add_trace(go.Scatter(
            x=labels, y=plot["Recontact_Rate"], name="Recontact",
            mode="lines+markers",
            line=dict(color=DIDI_ORANGE, width=2.5),
            marker=dict(size=8, color=DIDI_ORANGE),
            customdata=names,
            hovertemplate="%{customdata}<br>Recontact %{y:.2f}%<extra></extra>",
        ), secondary_y=True)
        fig.add_hline(y=RECONTACT_GOAL, line_dash="dot", line_color=DIDI_MUTED, secondary_y=True)
        fig.update_yaxes(title_text="Recontact %", range=_rc_axis(plot), showgrid=False, secondary_y=True)
    fig.add_hline(y=QA_GOAL, line_dash="dash", line_color=DIDI_MUTED)
    fig.update_yaxes(title_text="QA / CSAT %", range=[0, SCORE_LABEL_MAX], secondary_y=False)
    fig.update_xaxes(title_text="", tickangle=-32, tickfont=dict(size=10))
    fig.update_layout(
        barmode="group",
        legend=LEGEND_TOP,
        margin=dict(l=56, r=64, t=56, b=120),
        bargap=0.28,
        dragmode=False,
    )
    return _panel(fig, 460, title=title, n=_len_n(plot), n_unit=grain)


def supervisor_gap_chart(
    df: pd.DataFrame,
    name_col: str,
    score_col: str,
    n_col: str,
    *,
    goal: float,
    title: str,
    unit: str = "audits",
    min_n: int = 20,
) -> go.Figure:
    """Pareto of gap × volume. Low-n rows are held out so a single audit cannot dominate."""
    from modules.kpis import gap_pareto_frame

    empty = go.Figure()
    empty.add_annotation(text="No supervisor below goal with a reliable sample", showarrow=False)
    if df is None or df.empty or name_col not in df.columns or score_col not in df.columns:
        return _panel(empty, 300, title=title)
    work = df.copy()
    if n_col in work.columns:
        work = work[pd.to_numeric(work[n_col], errors="coerce").fillna(0) >= int(min_n)]
    frame = gap_pareto_frame(work, name_col, score_col, n_col, goal)
    if frame.empty:
        return _panel(empty, 300, title=title)
    sample_n = int(pd.to_numeric(frame[n_col], errors="coerce").fillna(0).sum()) if n_col in frame.columns else None
    value_title = f"Weighted deficit (gap × {unit})"
    return pareto_dual_axis(
        frame, "Cat", "Gap_Impact",
        title=title,
        value_title=value_title,
        sample_unit=unit,
        universe_n=sample_n,
    )


def taxonomy_coverage_chart(df: pd.DataFrame) -> go.Figure:
    """100% stacked bar: classified vs Other at each contact-reason grain."""
    title = "Contact reason classification coverage"
    if df is None or df.empty or "Level" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No contact-reason coverage in this filter", showarrow=False)
        return _panel(fig, 280, title=title)
    plot = df.iloc[::-1].copy()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=plot["Level"], x=plot["Classified_Pct"], orientation="h", name="Classified",
        marker_color=STATUS_COLORS["green"],
        text=[f"{v:.1f}%" for v in plot["Classified_Pct"]],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=11, color="#FFFFFF"),
        customdata=np.column_stack([
            plot["Level"].astype(str),
            plot["Other_N"].to_numpy() if "Other_N" in plot.columns else np.zeros(len(plot)),
            plot["Total_N"].to_numpy() if "Total_N" in plot.columns else np.zeros(len(plot)),
        ]),
        hovertemplate="%{customdata[0]}<br>Classified %{x:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=plot["Level"], x=plot["Other_Pct"], orientation="h", name="Other / unclassified",
        marker_color="#94A3B8",
        text=[f"{v:.1f}%" if v >= 3 else "" for v in plot["Other_Pct"]],
        textposition="inside",
        textfont=dict(size=11, color=DIDI_TEXT),
        customdata=np.column_stack([
            plot["Level"].astype(str),
            plot["Other_N"].to_numpy() if "Other_N" in plot.columns else np.zeros(len(plot)),
            plot["Total_N"].to_numpy() if "Total_N" in plot.columns else np.zeros(len(plot)),
        ]),
        hovertemplate=(
            "%{customdata[0]}<br>Other %{x:.1f}%"
            "<br>%{customdata[1]:,.0f} of %{customdata[2]:,.0f} surveys<extra></extra>"
        ),
    ))
    fig.update_layout(
        barmode="stack",
        xaxis=dict(title="% of CSAT surveys", range=[0, 100], ticksuffix="%"),
        yaxis=dict(title=""),
        legend=LEGEND_TOP,
        margin=dict(l=140, r=40, t=56, b=40),
        bargap=0.32,
    )
    n_total = int(plot["Total_N"].iloc[0]) if "Total_N" in plot.columns and len(plot) else None
    return _panel(fig, 280, title=title, n=n_total, n_unit="surveys")


def fail_count_by_cr_chart(
    df: pd.DataFrame,
    cat_col: str = "CR_Lv4",
    *,
    grain: str = "contact reason Lv4 (detail)",
) -> go.Figure:
    """Attribute-fail counts by contact reason — all reasons, not a truncated Pareto."""
    title = f"QA fails by {grain}"
    if df is None or df.empty or cat_col not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No attribute fails in this filter", showarrow=False)
        return _panel(fig, 320, title=title)
    count_col = "Fail_Count" if "Fail_Count" in df.columns else ("Count" if "Count" in df.columns else None)
    if count_col is None:
        fig = go.Figure()
        fig.add_annotation(text="No attribute fails in this filter", showarrow=False)
        return _panel(fig, 320, title=title)
    plot = df.copy()
    plot[count_col] = pd.to_numeric(plot[count_col], errors="coerce").fillna(0)
    plot = plot[plot[count_col] > 0].sort_values(count_col, ascending=True)
    if plot.empty:
        fig = go.Figure()
        fig.add_annotation(text="No attribute fails in this filter", showarrow=False)
        return _panel(fig, 320, title=title)
    labels = [_wrap_label(x, 36, max_lines=2) for x in plot[cat_col]]
    fig = go.Figure(go.Bar(
        y=labels, x=plot[count_col], orientation="h",
        marker_color=DIDI_ORANGE,
        text=[f"{int(v):,}" for v in plot[count_col]],
        textposition="outside",
        textfont=dict(size=10, color=DIDI_TEXT),
        cliponaxis=False,
        customdata=plot[cat_col].astype(str),
        hovertemplate="%{customdata}<br>Attribute fails %{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        xaxis=dict(title="Attribute fails"),
        yaxis=dict(title=""),
        margin=dict(l=200, r=72, t=48, b=40),
        showlegend=False,
    )
    return _panel(
        fig, _hbar_height(len(plot), 26, 90), title=title,
        n=int(plot[count_col].sum()), n_unit="attribute fails",
    )


def multimetric_risk_chart(df: pd.DataFrame) -> go.Figure:
    return kpi_combo_by_cr(
        df, "CR_Lv4",
        title="Contact reason Lv4 (detail) — QA, CSAT, and recontact",
        grain="contact reasons Lv4 (detail)",
    )


def recontact_channel_combo_chart(df: pd.DataFrame) -> go.Figure:
    """Contacts + repeats bars, official rate line. Rate is Repeats/Contacts, never an average."""
    if df is None or df.empty or "Channel" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No recontact rows in this filter", showarrow=False)
        return _panel(fig, 360, title="Contacts, repeats, and rate by channel")
    plot = df.copy()
    plot = plot[~plot["Channel"].astype(str).str.startswith("All 12")].copy()
    if plot.empty:
        fig = go.Figure()
        fig.add_annotation(text="No recontact rows in this filter", showarrow=False)
        return _panel(fig, 360, title="Contacts, repeats, and rate by channel")
    labels = [_wrap_label(x, 14) for x in plot["Channel"]]
    names = plot["Channel"].astype(str)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=labels, y=plot["Contacts"], name="Contacts",
        marker_color=CHART_COLORS["blue"],
        customdata=names,
        hovertemplate="%{customdata}<br>Contacts %{y:,.0f}<extra></extra>",
    ), secondary_y=False)
    if "Repeats" in plot.columns:
        fig.add_trace(go.Bar(
            x=labels, y=plot["Repeats"], name="Repeats",
            marker_color=CHART_COLORS["recontact"],
            customdata=names,
            hovertemplate="%{customdata}<br>Repeats %{y:,.0f}<extra></extra>",
        ), secondary_y=False)
    rate_col = "Rate %" if "Rate %" in plot.columns else None
    if rate_col:
        fig.add_trace(go.Scatter(
            x=labels, y=plot[rate_col], name="Rate %",
            mode="lines+markers",
            line=dict(color=DIDI_ORANGE, width=2.6),
            marker=dict(size=8),
            customdata=names,
            hovertemplate="%{customdata}<br>Rate %{y:.2f}%<extra></extra>",
        ), secondary_y=True)
        fig.add_trace(go.Scatter(
            x=labels, y=[RECONTACT_GOAL] * len(plot), name="Goal 5.44",
            mode="lines",
            line=dict(color=DIDI_MUTED, width=1.5, dash="dash"),
            hovertemplate="Goal 5.44%<extra></extra>",
        ), secondary_y=True)
        fig.update_yaxes(
            title_text="Rate %",
            range=_rc_axis(plot.rename(columns={rate_col: "Recontact_Rate"})),
            showgrid=False,
            secondary_y=True,
        )
    fig.update_yaxes(title_text="Volume", secondary_y=False)
    fig.update_xaxes(title_text="Channel", tickangle=-28, tickfont=dict(size=10))
    fig.update_layout(
        barmode="group",
        legend=LEGEND_TOP,
        margin=dict(l=56, r=56, t=52, b=88),
        bargap=0.28,
    )
    return _panel(
        fig, 400, title="Contacts, repeats, and rate by channel",
        n=_sum_n(plot, "Contacts"), n_unit="contacts",
    )


def recontact_cr_combo_chart(
    df: pd.DataFrame,
    *,
    cat_col: str = "CR_Lv4",
    title: str = "Repeats and rate by contact reason Lv4 (detail)",
    bar_color: str | None = None,
) -> go.Figure:
    """Repeat volume bars + official rate line. Rate is ratio of sums."""
    if df is None or df.empty or cat_col not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No recontact rows in this filter", showarrow=False)
        return _panel(fig, 380, title=title)
    plot = df.copy()
    vol_col = "Recontacts" if "Recontacts" in plot.columns else ("Count" if "Count" in plot.columns else None)
    if vol_col is None:
        fig = go.Figure()
        fig.add_annotation(text="No recontact rows in this filter", showarrow=False)
        return _panel(fig, 380, title=title)
    plot = plot[pd.to_numeric(plot[vol_col], errors="coerce").fillna(0) > 0].copy()
    if plot.empty:
        fig = go.Figure()
        fig.add_annotation(text="No recontact rows in this filter", showarrow=False)
        return _panel(fig, 380, title=title)
    labels = [_wrap_label(x, 18) for x in plot[cat_col]]
    names = plot[cat_col].astype(str)
    rates = pd.to_numeric(plot["Recontact_Rate"], errors="coerce") if "Recontact_Rate" in plot.columns else pd.Series([None] * len(plot))
    contacts = pd.to_numeric(plot["Contacts"], errors="coerce").fillna(0) if "Contacts" in plot.columns else pd.Series([0] * len(plot))
    repeats = pd.to_numeric(plot[vol_col], errors="coerce").fillna(0)
    hover_cd = list(zip(names.tolist(), rates.tolist(), contacts.tolist(), repeats.tolist()))
    fill = bar_color or DIDI_ORANGE
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=labels, y=plot[vol_col], name="Repeats",
        marker_color=fill,
        customdata=hover_cd,
        hovertemplate=(
            "%{customdata[0]}<br>Repeats %{y:,.0f}"
            "<br>Contacts %{customdata[2]:,.0f}"
            "<br>Rate %{customdata[1]:.2f}%<extra></extra>"
        ),
    ), secondary_y=False)
    if "Recontact_Rate" in plot.columns and plot["Recontact_Rate"].notna().any():
        fig.add_trace(go.Scatter(
            x=labels, y=plot["Recontact_Rate"], name="Rate %",
            mode="lines+markers",
            line=dict(color=DIDI_ORANGE, width=2.6),
            marker=dict(size=8),
            customdata=hover_cd,
            hovertemplate=(
                "%{customdata[0]}<br>Rate %{y:.2f}%"
                "<br>Repeats %{customdata[3]:,.0f}"
                "<br>Contacts %{customdata[2]:,.0f}<extra></extra>"
            ),
        ), secondary_y=True)
        fig.add_trace(go.Scatter(
            x=labels, y=[RECONTACT_GOAL] * len(plot), name="Goal 5.44",
            mode="lines",
            line=dict(color=DIDI_MUTED, width=1.5, dash="dash"),
            hovertemplate="Goal 5.44%<extra></extra>",
        ), secondary_y=True)
        fig.update_yaxes(
            title_text="Rate %",
            range=_rc_axis(plot),
            showgrid=False,
            secondary_y=True,
        )
    fig.update_yaxes(title_text="Repeats", secondary_y=False)
    fig.update_xaxes(title_text="Contact reason", tickangle=-32, tickfont=dict(size=10))
    fig.update_layout(
        legend=LEGEND_TOP,
        margin=dict(l=56, r=56, t=52, b=110),
        bargap=0.32,
    )
    n_contacts = _sum_n(plot, "Contacts")
    note = f"{n_contacts:,} contacts in view" if n_contacts else None
    return _panel(
        fig, 420, title=title,
        n=_sum_n(plot, vol_col), n_unit="repeats", n_note=note,
    )


def americas_map_chart(df: pd.DataFrame, selected: str | None = None) -> go.Figure:
    """Choropleth of SSL markets. Fill is QA where audited, else CSAT. Recontact has no country."""
    fig = go.Figure()
    if df is None or df.empty or "Country" not in df.columns:
        fig.add_annotation(
            text="No market in the current filter",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=13, color=DIDI_MUTED),
        )
        fig.update_layout(
            height=528, paper_bgcolor=PAPER, plot_bgcolor=PAPER,
            margin=dict(l=0, r=0, t=8, b=0),
            font=dict(family=FONT, size=11, color=DIDI_TEXT),
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        return fig

    work = df.copy()
    work["iso3"] = work["Country"].map(COUNTRY_ISO3)
    work = work[work["iso3"].notna()].copy()
    if work.empty:
        return americas_map_chart(pd.DataFrame(), selected)

    fill = work["QA_Score"].where(work["QA_Score"].notna(), work["CSAT_Score"]) if "CSAT_Score" in work.columns else work["QA_Score"]
    hover: list[str] = []
    custom: list[str] = []
    for _, row in work.iterrows():
        code = str(row["Country"])
        name = row["Country_Name"] if "Country_Name" in work.columns and pd.notna(row.get("Country_Name")) else COUNTRY_NAMES.get(code, code)
        qa = row["QA_Score"] if "QA_Score" in work.columns else np.nan
        cs = row["CSAT_Score"] if "CSAT_Score" in work.columns else np.nan
        qa_n = int(row["QA_N"]) if "QA_N" in work.columns and pd.notna(row["QA_N"]) else 0
        cs_n = int(row["CSAT_N"]) if "CSAT_N" in work.columns and pd.notna(row["CSAT_N"]) else 0
        qa_txt = f"{qa:.2f}% · {qa_n:,} audits" if pd.notna(qa) else "no QA in this market"
        cs_txt = f"{cs:.2f}% · {cs_n:,} surveys" if pd.notna(cs) else "no CSAT in this market"
        hover.append(
            f"<b>{name} ({code})</b><br>"
            f"QA {qa_txt}<br>"
            f"CSAT {cs_txt}<br>"
            "Recontact: SSL mix (no market field)"
        )
        custom.append(code)

    locations = work["iso3"].tolist()
    selectedpoints = None
    if selected:
        iso = COUNTRY_ISO3.get(str(selected).strip())
        if iso in locations:
            selectedpoints = [locations.index(iso)]

    fig.add_trace(go.Choropleth(
        locations=locations,
        z=pd.to_numeric(fill, errors="coerce"),
        locationmode="ISO-3",
        colorscale=[
            [0.0, "#D64545"],
            [0.42, "#F2A900"],
            [0.70, "#2E9B57"],
            [1.0, "#1B7A42"],
        ],
        zmin=70,
        zmax=100,
        marker_line_color="#FFFFFF",
        marker_line_width=0.9,
        colorbar=dict(
            title=dict(text="QA / CSAT %", font=dict(size=10, color=DIDI_TEXT)),
            tickfont=dict(size=10, color=DIDI_TEXT),
            thickness=10,
            len=0.52,
            x=0.0,
            xanchor="left",
            y=0.48,
            bgcolor="rgba(255,255,255,0.85)",
        ),
        customdata=[[c] for c in custom],
        hovertext=hover,
        hovertemplate="%{hovertext}<extra></extra>",
        selectedpoints=selectedpoints,
        autocolorscale=False,
        showscale=True,
    ))
    fig.update_geos(
        visible=False,
        resolution=50,
        showcountries=True,
        countrycolor="#D0D5DC",
        showland=True,
        landcolor="#F5F6F8",
        showocean=True,
        oceancolor="#FFFFFF",
        showlakes=False,
        showframe=False,
        bgcolor="#FFFFFF",
        lataxis_range=[-56, 33],
        lonaxis_range=[-118, -34],
        projection_type="natural earth",
        fitbounds=False,
    )
    fig.update_layout(
        height=528,
        paper_bgcolor=PAPER,
        plot_bgcolor=PAPER,
        margin=dict(l=0, r=0, t=4, b=0),
        font=dict(family=FONT, size=11, color=DIDI_TEXT),
        dragmode=False,
        clickmode="event+select",
    )
    n_mkt = int(len(work))
    fig.add_annotation(
        text=f"N = {n_mkt} market{'s' if n_mkt != 1 else ''}",
        xref="paper", yref="paper",
        x=1, y=1, xanchor="right", yanchor="bottom", yshift=2,
        showarrow=False,
        font=dict(size=11, color=DIDI_MUTED),
    )
    return fig


_Q_ORDER = ("Q1", "Q2", "Q3", "Q4")
_Q_COLORS = {
    "Q1": STATUS_COLORS["green"],
    "Q2": STATUS_COLORS["blue"],
    "Q3": STATUS_COLORS["amber"],
    "Q4": STATUS_COLORS["red"],
}


def quartile_count_chart(
    summary: dict | None,
    *,
    title: str = "Agents by quartile",
    unit: str = "agents",
) -> go.Figure:
    """Four columns Q1–Q4. Q1 is the top 25% of this filter."""
    bands = (summary or {}).get("bands") or {}
    counts = [int((bands.get(q) or {}).get("n") or 0) for q in _Q_ORDER]
    fig = go.Figure()
    if not any(counts):
        fig.add_annotation(text="Not enough agents in this filter to split quartiles.", showarrow=False)
        return _panel(fig, 220, title=title)
    hover_names = []
    for q in _Q_ORDER:
        names = (bands.get(q) or {}).get("names") or []
        hover_names.append(", ".join(str(n) for n in names[:8]) or "—")
    fig.add_trace(go.Bar(
        x=list(_Q_ORDER),
        y=counts,
        marker_color=[_Q_COLORS[q] for q in _Q_ORDER],
        text=[str(v) for v in counts],
        textposition="outside",
        cliponaxis=False,
        customdata=hover_names,
        hovertemplate="%{x}: %{y} " + unit + "<br>%{customdata}<extra></extra>",
    ))
    fig.update_layout(
        yaxis=dict(title=unit.title(), rangemode="tozero"),
        xaxis=dict(title=""),
        margin=dict(l=48, r=24, t=16, b=40),
        showlegend=False,
    )
    ranked = int((summary or {}).get("ranked") or sum(counts))
    return _panel(fig, 240, title=title, n=ranked, n_unit=unit)


def supervisor_mix_chart(
    df: pd.DataFrame,
    *,
    title: str = "Supervisor talent mix",
    top_n: int = 12,
) -> go.Figure:
    """Stacked % of each TL’s agents in company Q1–Q4. Click a bar to open that team."""
    fig = go.Figure()
    if df is None or df.empty or "Supervisor_ID" not in df.columns:
        fig.add_annotation(text="No supervisor with ranked agents in this filter.", showarrow=False)
        return _panel(fig, 220, title=title)
    plot = df.copy()
    if "Q4_Share" in plot.columns:
        plot = plot.sort_values("Q4_Share", ascending=False)
    plot = plot.head(int(top_n))
    labels = plot["Supervisor_ID"].astype(str).tolist()
    for q in _Q_ORDER:
        col = f"{q}_pct"
        vals = pd.to_numeric(plot[col], errors="coerce").fillna(0).tolist() if col in plot.columns else [0] * len(plot)
        fig.add_trace(go.Bar(
            name=q,
            y=labels,
            x=vals,
            orientation="h",
            marker_color=_Q_COLORS[q],
            customdata=plot["Supervisor_ID"].astype(str).to_numpy(),
            hovertemplate="%{customdata}<br>" + q + " %{x:.0f}%<extra></extra>",
        ))
    fig.update_layout(
        barmode="stack",
        xaxis=dict(title="% of ranked agents", range=[0, 100]),
        yaxis=dict(title="", autorange="reversed"),
        legend=LEGEND_BOTTOM,
        margin=dict(l=120, r=28, t=16, b=56),
    )
    return _panel(
        fig, _hbar_height(len(plot), 28, 90), title=title,
        n=_len_n(plot), n_unit="supervisors",
    )


# Legacy aliases
def sparkline(values, color=DIDI_ORANGE):
    return sparkline_fig(list(values) if values is not None else [], color)


def pareto_chart(pareto, top_n=8):
    from modules.kpis import pareto_for_display
    if pareto.empty:
        return pareto_dual_axis(pd.DataFrame(), "Cat", "Count")
    df = pareto_for_display(pareto, top_n).rename(columns={"Error_Category": "Cat", "Cantidad": "Count"})
    return pareto_dual_axis(df, "Cat", "Count")


def share_donut_chart(
    df: pd.DataFrame,
    name_col: str,
    value_col: str,
    *,
    title: str,
    colors: list[str] | None = None,
    sample_unit: str = "audits",
) -> go.Figure:
    empty = go.Figure()
    empty.add_annotation(text="No rows in the current filter", showarrow=False)
    if df is None or df.empty or name_col not in df.columns or value_col not in df.columns:
        return _panel(empty, 220, title=title)
    plot = df.copy()
    plot[value_col] = pd.to_numeric(plot[value_col], errors="coerce").fillna(0)
    plot = plot[plot[value_col] > 0]
    if plot.empty:
        return _panel(empty, 220, title=title)
    labels = plot[name_col].astype(str).tolist()
    values = plot[value_col].tolist()
    fills = colors or DONUT_PALETTE[: len(labels)]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.58,
        marker=dict(colors=fills[: len(labels)], line=dict(color=PAPER, width=1)),
        textinfo="label+percent",
        textfont=dict(size=11, color=DIDI_TEXT),
        hovertemplate="%{label}<br>%{value:,.0f} " + sample_unit + " (%{percent})<extra></extra>",
        sort=False,
    ))
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h", y=-0.18, x=0.5, xanchor="center",
            font=dict(size=11, color=DIDI_TEXT), bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=8, r=8, t=8, b=48),
    )
    return _panel(fig, 220, title=title, n=int(plot[value_col].sum()), n_unit=sample_unit)


def count_stack_chart(
    df: pd.DataFrame,
    cat_col: str,
    series_col: str,
    value_col: str = "n",
    *,
    title: str,
    cat_order: list[str] | None = None,
    series_order: list[str] | None = None,
    sample_unit: str = "audits",
) -> go.Figure:
    empty = go.Figure()
    empty.add_annotation(text="No rows in the current filter", showarrow=False)
    if df is None or df.empty or cat_col not in df.columns or series_col not in df.columns:
        return _panel(empty, 280, title=title)
    plot = df.copy()
    plot[value_col] = pd.to_numeric(plot[value_col], errors="coerce").fillna(0)
    cats = cat_order or plot.groupby(cat_col)[value_col].sum().sort_values(ascending=False).index.tolist()
    series = series_order or plot.groupby(series_col)[value_col].sum().sort_values(ascending=False).index.tolist()
    fig = go.Figure()
    palette = [CHART_COLORS["blue"], DIDI_ORANGE, STATUS_COLORS.get("amber", "#C9A227"), "#64748B"]
    for i, name in enumerate(series):
        sub = plot[plot[series_col].astype(str) == str(name)]
        lookup = dict(zip(sub[cat_col].astype(str), sub[value_col]))
        ys = [float(lookup.get(str(c), 0)) for c in cats]
        fig.add_trace(go.Bar(
            name=str(name),
            x=[_wrap_label(c, 18) for c in cats],
            y=ys,
            marker_color=palette[i % len(palette)],
            hovertemplate="%{x}<br>" + str(name) + " %{y:,.0f}<extra></extra>",
        ))
    fig.update_layout(
        barmode="stack",
        yaxis=dict(title=sample_unit.title(), rangemode="tozero"),
        xaxis=dict(title=""),
        legend=LEGEND_TOP,
        margin=dict(l=56, r=28, t=52, b=64),
        bargap=0.35,
    )
    return _panel(fig, 300, title=title, n=int(plot[value_col].sum()), n_unit=sample_unit)


pareto_horizontal = pareto_chart
team_score_bars = qa_by_cr_chart
score_distribution_donut = recontact_donut
heatmap_dow_channel = metrics_trend_daily
scatter_corr = qa_csat_scatter
trend_with_target = metrics_trend_daily
