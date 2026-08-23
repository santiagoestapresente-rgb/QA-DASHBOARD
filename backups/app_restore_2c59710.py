"""
DiDi CX — Executive Quality Dashboard
Power BI layout · Business Case analytics only
"""

from __future__ import annotations

from html import escape as html_escape
from pathlib import Path
from urllib.parse import quote
import time

import streamlit as st
import pandas as pd

from config import (
    CHART_COLORS,
    COUNTRY_FROM_ISO3,
    COUNTRY_NAMES,
    CSAT_GOAL,
    DIDI_CARD,
    DIDI_CARD_BORDER,
    DIDI_DARK,
    DIDI_FILTER,
    DIDI_GRAY,
    DIDI_MUTED,
    DIDI_NAVY,
    DIDI_ORANGE,
    DIDI_SIDEBAR,
    DIDI_TEXT,
    DIDI_WHITE,
    LABEL_GROUPS,
    LABELS,
    QA_GOAL,
    RANKING_CSAT_MIN_N,
    RANKING_QA_MIN_N,
    CR_COMBO_TOP_N,
    CR_COMBO_MIN_QA_N,
    SUPERVISOR_GAP_MIN_N,
    RECONTACT_GOAL,
    SUPERVISOR_Q4_SHARE_ALERT,
    STATUS_COLORS,
    TENURE_SOURCE_ORDER,
    THEME_DEFAULTS,
    apply_ui_overrides,
    clear_ui_overrides,
    load_ui_overrides,
    save_ui_overrides,
)
import modules.dashboard_charts as _dash_charts
from modules.dashboard_charts import (
    CHART_CFG,
    control_i_chart,
    cr_group_hbar,
    critical_split_chart,
    csat_star_chart,
    kpi_combo_by_cr,
    fail_count_by_cr_chart,
    pareto_dual_axis,
    qa_by_cr_chart,
    qa_aht_scatter,
    aht_metric_scatter,
    qa_aht_combo,
    qa_channel_compare_chart,
    qa_csat_scatter,
    score_volume_combo,
    grouped_qa_csat_chart,
    channel_kpi_combo,
    hbar_score_chart,
    voc_bar_chart,
    manner_pie_chart,
    share_donut_chart,
    count_stack_chart,
    is_pareto_remainder_label,
    corr_r_bars,
    multimetric_risk_chart,
    qa_histogram_chart,
    csat_histogram_chart,
    qa_recontact_scatter,
    csat_recontact_scatter,
    recontact_scope_chart,
    sparkbar_fig,
    sparkline_fig,
    spark_hbar_fig,
    spark_donut_fig,
    spark_r_fig,
    square_pie_fig,
    top_failing_attributes_chart,
    weekly_kpi_chart,
    americas_map_chart,
    recontact_channel_combo_chart,
    recontact_cr_combo_chart,
    quartile_count_chart,
    supervisor_gap_chart,
    supervisor_mix_chart,
    taxonomy_coverage_chart,
)
from modules.chart_notes import (
    aht_outcome_notes,
    attr_notes,
    combined_notes,
    pareto_notes,
    qa_rc_chart_notes,
    rc_scope_notes,
    scatter_notes,
    voc_notes,
    csat_tenure_notes,
)
from modules.alerts import (
    agents_for_supervisor,
    annotate_watch_pipeline,
    make_agent_ticket,
    make_csat_ticket,
    make_qa_ticket,
    people_watchlist,
    qa_coaching_queue,
    recontact_ops_table,
)
from modules.micro_insights import (
    attr_chip,
    channel_chip,
    combined_chip,
    csat_chip,
    fcr_scope_chip,
    gap_chip,
    pareto_chip,
    qa_chip,
    aht_overlap_empty_text,
    r_explain,
    rate_chip,
    scatter_chip,
    tenure_chip,
    voc_chip,
    weekly_chip,
)
from modules.data_loader import load_all_data
from modules.executive_engine import (
    build_executive_brief,
    combined_operational_analysis,
    csat_segmentation,
    generate_action_plan,
    qa_channel_breakdown,
    requester_performance,
    period_volume_delta,
)
from modules.kpis import (
    agent_scores,
    channel_performance,
    attach_cr_group,
    cr_correlation_summary,
    cr_join_coverage,
    CR_UNMAPPED,
    cr_group_lookup,
    cr_group_metrics,
    cr_level_metrics,
    split_cr_combo_view,
    parse_cr_fallback_label,
    map_cr_group,
    channel_match,
    cr_match,
    normalize_channel_label,
    critical_fail_stats,
    csat_unsatisfied_by_cr,
    csat_score_by_cr,
    csat_by_supervisor,
    csat_by_business_type,
    csat_by_star_rating,
    csat_by_user_tenure,
    voc_all_comments,
    filter_csat_by_supervisor,
    filter_csat_by_agent,
    filter_csat_by_tenure,
    fail_event_totals,
    csat_control_daily,
    daily_metrics_trend,
    daily_volume_series,
    cut_csat_recontact_for_weeks,
    calendar_days_in_scope,
    filter_by_calendar_day,
    analysis_date_span,
    kpi_summary,
    kpi_by_channel,
    market_performance,
    qa_aht_by_cr,
    qa_aht_by_channel,
    qa_aht_summary,
    supervisor_overview,
    csat_supervisor_mapping,
    cr_finest_volume,
    cr_taxonomy_coverage,
    gap_pareto_frame,
    tenure_qa_overview,
    tenure_csat_overview,
    agents_below_qa_goal,
    qa_agent_roster,
    qa_agent_fail_concentrators,
    csat_agent_roster,
    CSAT_UNMAPPED_SUPERVISOR,
    AHT_CR_MIN_AUDITS,
    qa_agent_quartiles,
    csat_agent_quartiles,
    quartile_band_summary,
    supervisor_quartile_mix,
    aht_joined_outcomes,
    aht_correlation_summary,
    qa_by_audit_type,
    qa_by_special_project,
    qa_by_tenure,
    qa_channel_dispersion,
    qa_control_daily,
    qa_fails_by_cr,
    qa_fails_by_cr_group,
    qa_auditor_outcome,
    auditor_resolution_summary,
    qa_process_adherence_summary,
    qa_dissatisfaction_split,
    qa_dissatisfaction_owner,
    qa_dissatisfaction_subreason,
    qa_repeat_48h,
    qa_repeat_48h_by_channel,
    qa_auditor_quotes,
    REPEAT_48H_ORDER,
    qa_score_by_cr,
    qa_score_histogram,
    csat_score_histogram,
    recontact_by_cr,
    recontact_by_std_channel,
    recontact_channel_table,
    recontact_by_cr_group,
    contact_volume_by_cr,
    recontact_by_scope,
    recontact_control_daily,
    recontact_dilution_stats,
    recontact_rate,
    scoring_method_stats,
    slice_coverage_table,
    top_failing_attributes,
    voc_themes_negative,
    volume_totals,
    weekly_kpi_table,
    weekly_trends,
    _vs_goal_status,
)

_APP_DIR = Path(__file__).resolve().parent
_DIDI_FAVICON = _APP_DIR / "assets" / "didi_favicon.png"

st.set_page_config(
    page_title="DiDi CX Quality Dashboard",
    page_icon=str(_DIDI_FAVICON) if _DIDI_FAVICON.exists() else "🟠",
    layout="wide",
    initial_sidebar_state="expanded",
)

THEME_PICKERS = (
    ("navy", "App background"),
    ("sidebar", "Sidebar"),
    ("card", "Cards"),
    ("orange", "Accent"),
    ("text", "Text"),
)


def _hex_color(value: object, fallback: str) -> str:
    if isinstance(value, str) and value.startswith("#") and len(value) in (4, 7):
        return value
    return fallback


def _hex_rgb(value: str, fallback: str = "255, 102, 0") -> str:
    raw = str(value or "").strip().lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6:
        return fallback
    try:
        r, g, b = int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
    except ValueError:
        return fallback
    return f"{r}, {g}, {b}"


_STALE_DARK_SURFACES = {"#0a0e1a", "#0c1220", "#151c2c"}
_STALE_LIGHT_TEXT = {"#f8fafc", "#ffffff", "#fff"}


def _is_broken_theme(value: object, key: str = "") -> bool:
    """Streamlit color_picker defaults to #000000 when first mounted without value=."""
    if not isinstance(value, str):
        return True
    raw = value.strip().lower()
    if raw in {"", "#000", "#000000", "black"}:
        return True
    if key in {"navy", "sidebar", "card"} and raw in _STALE_DARK_SURFACES:
        return True
    if key == "text" and raw in _STALE_LIGHT_TEXT:
        return True
    return False


def init_labels() -> None:
    applied = apply_ui_overrides()
    for key, value in applied["labels"].items():
        sk = f"lbl_{key}"
        stored = st.session_state.get(sk)
        allow_blank = key in {"overview_insight", "overview_action", "overview_hypothesis", "qa_story"}
        if not allow_blank and (not isinstance(stored, str) or not stored.strip()):
            st.session_state[sk] = value
        else:
            st.session_state.setdefault(sk, value)
    for key, value in applied["theme"].items():
        sk = f"theme_{key}"
        if _is_broken_theme(st.session_state.get(sk)):
            st.session_state[sk] = value
        else:
            st.session_state.setdefault(sk, value)


def L(key: str) -> str:
    ss_key = f"lbl_{key}"
    if ss_key in st.session_state:
        stored = st.session_state[ss_key]
        if isinstance(stored, str) and stored.strip():
            return stored
        builtin = str(LABELS.get(key, key))
        if builtin:
            return builtin
        return stored
    file_labels = load_ui_overrides().get("labels") or {}
    if isinstance(file_labels.get(key), str):
        return file_labels[key]
    return str(LABELS.get(key, key))


def runtime_theme() -> dict:
    theme = dict(apply_ui_overrides()["theme"])
    for key, default in THEME_DEFAULTS.items():
        raw = st.session_state.get(f"theme_{key}")
        if _is_broken_theme(raw, key):
            st.session_state[f"theme_{key}"] = theme.get(key, default)
            theme[key] = theme.get(key, default)
        else:
            theme[key] = _hex_color(raw, theme.get(key, default))
    return theme


def apply_chart_theme(theme: dict) -> None:
    """Keep Plotly panel colors in sync without restarting Streamlit."""
    text = theme["text"]
    card = theme["card"]
    _dash_charts.DIDI_ORANGE = theme["orange"]
    _dash_charts.DIDI_TEXT = text
    _dash_charts.DIDI_CARD = card
    _dash_charts.PAPER = card
    _dash_charts.TICK = text
    _dash_charts.GRID = "rgba(26,26,26,0.10)"
    _dash_charts.LINE = "rgba(26,26,26,0.16)"
    _dash_charts.LEGEND_BOTTOM["font"]["color"] = text
    _dash_charts.LEGEND_TOP["font"]["color"] = text


init_labels()
_THEME = runtime_theme()
DIDI_NAVY = _THEME["navy"]
DIDI_SIDEBAR = _THEME["sidebar"]
DIDI_CARD = _THEME["card"]
DIDI_ORANGE = _THEME["orange"]
DIDI_TEXT = _THEME["text"]
apply_chart_theme(_THEME)
_ORANGE_RGB = _hex_rgb(DIDI_ORANGE)

# Streamlit 1.61 `st.html("<style>…</style>")` is treated as style-only, sent to
# the event container WITHOUT unsafe_allow_javascript, then DOMPurify strips the
# <style> tag. Inject CSS via markdown and a non-style-only st.html payload.
# Do not use class name kpi-card (smoke test treats it as a leak).
_TILE = DIDI_CARD
_GRAD_PAGE = (
    f"radial-gradient(ellipse 90% 55% at 6% -8%, rgba({_ORANGE_RGB},.10), transparent 52%), "
    f"linear-gradient(180deg, {DIDI_WHITE} 0%, {DIDI_NAVY} 55%, {DIDI_GRAY} 100%)"
)
_GRAD_SIDE = DIDI_SIDEBAR
_GRAD_CARD = DIDI_CARD
_GRAD_ORANGE = DIDI_ORANGE
_GRAD_TITLE = DIDI_DARK
_GRAD_BLUE = DIDI_DARK


def _nav_mask(inner: str) -> str:
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
        "stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>"
        f"{inner}</svg>"
    )
    return f'url("data:image/svg+xml,{quote(svg)}")'


_NAV_HOME = _nav_mask(
    '<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/>'
)
_NAV_PIE = _nav_mask(
    '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/>'
    '<path d="M22 12A10 10 0 0 0 12 2v10z"/>'
)
_NAV_SMILE = _nav_mask(
    '<circle cx="12" cy="12" r="9"/>'
    '<path d="M8 14s1.5 2 4 2 4-2 4-2"/>'
    '<path d="M9 9h.01M15 9h.01"/>'
)
_NAV_PHONE = _nav_mask(
    '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 '
    '19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 '
    '2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27'
    'a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/>'
)
_NAV_BELL = _nav_mask(
    '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>'
    '<path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>'
)
_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp, .stMarkdown, .stCaption, button, input, textarea {{
    font-family: Inter, "Segoe UI", system-ui, sans-serif !important;
}}
html {{
    zoom: 0.8;
}}
.stApp {{
    background: {DIDI_NAVY};
    background-image: {_GRAD_PAGE};
    background-attachment: fixed;
    color: {DIDI_TEXT};
}}
/* Overlay toasts: pin the keyed dock itself (Streamlit puts st-key-* on the
   block, not inside stElementContainer, so :has() on that testid never fired). */
[class*="st-key-didi_toast_dock"] {{
    position: fixed !important;
    top: 4.75rem !important;
    right: 1.15rem !important;
    left: auto !important;
    z-index: 2147483000 !important;
    width: min(380px, calc(100vw - 24px)) !important;
    max-width: 380px !important;
    height: auto !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    flex: 0 0 auto !important;
    align-self: flex-end !important;
}}
[data-testid="stElementContainer"]:has([class*="st-key-didi_toast_dock"]),
[data-testid="stVerticalBlockBorderWrapper"]:has(> [class*="st-key-didi_toast_dock"]) {{
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
    border: none !important;
    background: transparent !important;
}}
[class*="st-key-didi_toast_dock"] [data-testid="stVerticalBlock"] {{
    gap: 8px !important;
}}
[class*="st-key-didi_toast_item"] {{
    background: linear-gradient(180deg, #24344F 0%, #151C2C 100%) !important;
    border: 1px solid rgba(242, 169, 0, .45) !important;
    border-left: 4px solid {STATUS_COLORS["amber"]} !important;
    border-radius: 12px !important;
    box-shadow: 0 10px 28px rgba(0,0,0,.42), 0 1px 0 rgba(255,255,255,.08) !important;
    padding: 0.8rem 0.55rem 1.15rem 0.9rem !important;
    margin: 0 !important;
    width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    overflow: visible !important;
    contain: none !important;
    box-sizing: border-box !important;
}}
[class*="st-key-didi_toast_item"]:has(.didi-toast--shake) {{
    animation: didi-toast-in 0.48s cubic-bezier(.22,.9,.35,1) both;
}}
[class*="st-key-didi_toast_item"] [data-testid="stVerticalBlockBorderWrapper"],
[class*="st-key-didi_toast_item"] [data-testid="stVerticalBlock"],
[class*="st-key-didi_toast_item"] [data-testid="stHorizontalBlock"],
[class*="st-key-didi_toast_item"] [data-testid="stColumn"],
[class*="st-key-didi_toast_item"] [data-testid="stColumn"] > div,
[class*="st-key-didi_toast_item"] [data-testid="stElementContainer"],
[class*="st-key-didi_toast_item"] [data-testid="stMarkdown"],
[class*="st-key-didi_toast_item"] [data-testid="stMarkdownContainer"] {{
    gap: 0 !important;
    height: auto !important;
    max-height: none !important;
    min-height: 0 !important;
    overflow: visible !important;
    contain: none !important;
}}
section.main [class*="st-key-didi_toast_item"] [data-testid="stHorizontalBlock"] {{
    gap: 0.35rem !important;
    align-items: flex-start !important;
}}
section.main [class*="st-key-didi_toast_item"] [data-testid="stColumn"] > div {{
    flex: 0 1 auto !important;
    height: auto !important;
}}
section.main [class*="st-key-didi_toast_item"] [data-testid="stMarkdownContainer"] > p {{
    margin: 0 !important;
    line-height: inherit !important;
}}
[class*="st-key-didi_toast_item"] button {{
    min-height: 28px !important;
    min-width: 28px !important;
    height: 28px !important;
    padding: 0 !important;
    font-size: 1.05rem !important;
    line-height: 1 !important;
    border-radius: 8px !important;
    background: rgba(255,255,255,.06) !important;
    color: #E2E8F0 !important;
    border: 1px solid rgba(255,255,255,.14) !important;
}}
[class*="st-key-didi_toast_item"] button:hover {{
    background: rgba({_ORANGE_RGB},.28) !important;
    border-color: {DIDI_ORANGE} !important;
    color: #FFFFFF !important;
}}
.didi-toast {{
    display: block; overflow: visible; padding: 0 0.15rem 0.15rem 0;
}}
.didi-toast-kicker {{
    color: {STATUS_COLORS["amber"]}; font-size: 10px; font-weight: 700;
    letter-spacing: .12em; text-transform: uppercase; margin: 0 0 6px;
    display: block; line-height: 1.3;
}}
.didi-toast-body {{
    color: #E8EEF6; font-size: 0.8rem; line-height: 1.55; margin: 0; font-weight: 500;
    display: block; overflow: visible; padding-bottom: 0.35rem;
    white-space: normal; overflow-wrap: anywhere;
}}
@keyframes didi-toast-in {{
    0% {{ transform: translateX(120%); opacity: 0; }}
    100% {{ transform: translateX(0); opacity: 1; }}
}}
@keyframes didi-toast-out {{
    to {{ transform: translateX(120%); opacity: 0; visibility: hidden; pointer-events: none; }}
}}
#didi-toast-live {{
    position: fixed !important;
    top: 4.75rem !important;
    right: 1.15rem !important;
    z-index: 2147483000 !important;
    width: min(380px, calc(100vw - 24px));
    display: flex;
    flex-direction: column;
    gap: 8px;
    animation: didi-toast-in 0.48s cubic-bezier(.22,.9,.35,1) both,
               didi-toast-out 0.35s 7.65s forwards;
}}
.didi-toast-card {{
    position: relative;
    background: linear-gradient(180deg, #24344F 0%, #151C2C 100%);
    border: 1px solid rgba(242, 169, 0, .45);
    border-left: 4px solid {STATUS_COLORS["amber"]};
    border-radius: 12px;
    box-shadow: 0 10px 28px rgba(0,0,0,.42), 0 1px 0 rgba(255,255,255,.08);
    padding: 0.8rem 2.4rem 1.05rem 0.9rem;
}}
.didi-toast-x {{
    position: absolute; top: 8px; right: 8px;
    width: 28px; height: 28px; padding: 0;
    border-radius: 8px; cursor: pointer;
    background: rgba(255,255,255,.06);
    color: #E2E8F0; border: 1px solid rgba(255,255,255,.14);
    font-size: 1.05rem; line-height: 1;
}}
.didi-toast-x:hover {{
    background: rgba({_ORANGE_RGB},.28);
    border-color: {DIDI_ORANGE};
    color: #FFFFFF;
}}
div[data-testid="stHtml"]:has(#didi-toast-live) {{
    height: 0 !important; min-height: 0 !important; margin: 0 !important;
    padding: 0 !important; overflow: visible !important;
}}
.didi-toast-sr {{
    position: absolute !important; width: 1px !important; height: 1px !important;
    overflow: hidden !important; clip: rect(0,0,0,0) !important;
}}
section.main [data-testid="stVerticalBlock"] {{
    gap: 0.8rem !important;
}}
section.main [data-testid="stHorizontalBlock"] {{
    gap: 0.85rem !important;
    align-items: stretch !important;
}}
section.main [data-testid="stColumn"] {{
    display: flex !important;
    flex-direction: column !important;
}}
section.main [data-testid="stColumn"] > div {{
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 auto !important;
    height: 100%;
    width: 100%;
}}
section.main [class*="st-key-didi_tile"] [data-testid="stVerticalBlock"],
section.main [class*="st-key-didi_panel"] [data-testid="stVerticalBlock"],
section.main [class*="st-key-didi_rcard"] [data-testid="stVerticalBlock"],
section.main [class*="st-key-didi_head"] [data-testid="stVerticalBlock"],
section.main [class*="st-key-didi_action"] [data-testid="stVerticalBlock"],
section.main [class*="st-key-didi_alert"] [data-testid="stVerticalBlock"],
section.main [class*="st-key-didi_watch"] [data-testid="stVerticalBlock"],
section.main [class*="st-key-didi_sup"] [data-testid="stVerticalBlock"] {{
    gap: 0.32rem !important;
}}
section.main [data-testid="stCaptionContainer"] {{
    margin: 0 !important;
    padding: 0 !important;
}}
section.main [data-testid="stCaptionContainer"] p {{
    margin: 0 !important;
    line-height: 1.4 !important;
    color: {DIDI_MUTED} !important;
    font-size: 0.8rem !important;
}}
section.main [data-testid="stDataFrame"],
section.main [data-testid="stDataFrameResizable"] {{
    margin: 0 !important;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid {DIDI_DARK} !important;
    border-top: 3px solid {DIDI_ORANGE} !important;
    background: {DIDI_DARK} !important;
}}
section.main [data-testid="stDataFrame"] [class*="header"],
section.main [data-testid="stDataFrame"] [role="columnheader"],
section.main [data-testid="stDataFrameResizable"] [role="columnheader"] {{
    background: {DIDI_DARK} !important;
    color: {DIDI_WHITE} !important;
}}
section.main [data-testid="stAlert"] {{
    margin: 0 !important;
}}
.didi-col-kicker {{
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {DIDI_TEXT};
    border-left: 3px solid {DIDI_ORANGE};
    padding: 0.12rem 0 0.28rem 0.55rem;
    margin: 0 0 0.55rem;
}}
section.main [data-testid="stMarkdownContainer"] {{
    margin: 0 !important;
}}
section.main [data-testid="stMarkdownContainer"] > p {{
    margin: 0 0 0.55rem;
}}
section.main [data-testid="stMarkdownContainer"] > p:last-child {{
    margin-bottom: 0;
}}
section.main [data-testid="stMarkdownContainer"]:has(.didi-kpi-banner-wrap) > p,
section.main [data-testid="stMarkdownContainer"]:has(.didi-note) > p,
section.main [data-testid="stMarkdownContainer"]:has(.didi-rbox) > p,
section.main [data-testid="stMarkdownContainer"]:has(.didi-ops-strip) > p,
section.main [data-testid="stMarkdownContainer"]:has(.didi-flow) > p,
section.main [data-testid="stMarkdownContainer"]:has(.didi-head-top) > p {{
    margin: 0 !important;
}}

section[data-testid="stSidebar"] {{
    background: {DIDI_SIDEBAR} !important;
    background-image: {_GRAD_SIDE} !important;
    width: 268px !important;
    border-right: 1px solid {DIDI_CARD_BORDER} !important;
}}
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{
    color: {DIDI_MUTED} !important; font-size: 11px !important; font-weight: 600 !important;
    text-transform: uppercase; letter-spacing: .06em;
}}
section[data-testid="stSidebar"] [data-testid="stSelectbox"] span,
section[data-testid="stSidebar"] [data-testid="stMultiSelect"] span,
section[data-testid="stSidebar"] [data-baseweb="select"] * {{
    color: {DIDI_MUTED} !important;
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] {{
    width: 100% !important;
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] [data-testid="stRadio"],
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] [data-testid="stRadio"] > div,
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"],
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] > div {{
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] {{
    display: flex !important; flex-direction: column !important; gap: 6px !important;
    align-items: stretch !important;
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] label {{
    display: grid !important;
    grid-template-columns: 18px minmax(0, 1fr) !important;
    align-items: center !important;
    column-gap: 10px !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    background: {DIDI_WHITE} !important;
    border: 1px solid {DIDI_CARD_BORDER} !important;
    border-radius: 10px !important;
    padding: 10px 12px 10px 14px !important;
    margin: 0 !important;
    min-height: 42px;
    cursor: pointer;
    text-align: left !important;
    transition: background .15s ease, border-color .15s ease, filter .15s ease;
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] label:hover {{
    background: {DIDI_GRAY} !important;
    border-color: rgba({_ORANGE_RGB},.4) !important;
    filter: brightness(0.92);
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] label:has(input:checked) {{
    border-color: {DIDI_ORANGE} !important;
    background: linear-gradient(180deg, rgba({_ORANGE_RGB},.38) 0%, rgba({_ORANGE_RGB},.16) 100%) !important;
    filter: none;
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] label:has(input:checked):hover {{
    background: linear-gradient(180deg, rgba({_ORANGE_RGB},.46) 0%, rgba({_ORANGE_RGB},.20) 100%) !important;
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] label input {{
    position: absolute !important; opacity: 0 !important;
    width: 0 !important; height: 0 !important; pointer-events: none !important;
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] [data-baseweb="radio"],
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] label > *:not(input):not(:has(p)) {{
    display: none !important;
    width: 0 !important; height: 0 !important; overflow: hidden !important;
    position: absolute !important;
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] label > div:has(p) {{
    display: block !important;
    grid-column: 2 !important;
    grid-row: 1 !important;
    width: 100% !important;
    margin: 0 !important;
    text-align: left !important;
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] p {{
    color: {DIDI_TEXT} !important; font-size: 13.5px !important; font-weight: 650 !important;
    text-transform: none !important; letter-spacing: 0.01em !important;
    text-align: left !important; margin: 0 !important;
    width: 100% !important; display: block !important;
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] label:has(input:checked) p {{
    color: #FFFFFF !important;
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] > label::before,
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] > div > label::before {{
    content: "";
    grid-column: 1;
    grid-row: 1;
    width: 18px; height: 18px;
    background-color: {DIDI_TEXT};
    -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat;
    -webkit-mask-position: center; mask-position: center;
    -webkit-mask-size: contain; mask-size: contain;
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] > label:nth-of-type(1)::before,
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] > div:nth-of-type(1) label::before {{
    -webkit-mask-image: {_NAV_HOME}; mask-image: {_NAV_HOME};
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] > label:nth-of-type(2)::before,
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] > div:nth-of-type(2) label::before {{
    -webkit-mask-image: {_NAV_PIE}; mask-image: {_NAV_PIE};
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] > label:nth-of-type(3)::before,
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] > div:nth-of-type(3) label::before {{
    -webkit-mask-image: {_NAV_SMILE}; mask-image: {_NAV_SMILE};
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] > label:nth-of-type(4)::before,
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] > div:nth-of-type(4) label::before {{
    -webkit-mask-image: {_NAV_PHONE}; mask-image: {_NAV_PHONE};
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] > label:nth-of-type(5)::before,
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] > div:nth-of-type(5) label::before {{
    -webkit-mask-image: {_NAV_BELL}; mask-image: {_NAV_BELL};
}}
section[data-testid="stSidebar"] [class*="st-key-didi_nav"] div[role="radiogroup"] label:has(input:checked)::before {{
    background-color: {DIDI_WHITE};
}}
section[data-testid="stSidebar"] .stCaption, section[data-testid="stSidebar"] small {{
    color: {DIDI_FILTER} !important;
}}
section[data-testid="stSidebar"] [data-testid="stExpander"] {{
    background: {DIDI_WHITE} !important;
    border: 1px solid {DIDI_CARD_BORDER} !important;
    border-radius: 10px !important;
    margin-bottom: 0.35rem;
}}
section[data-testid="stSidebar"] [data-testid="stExpander"] summary p,
section[data-testid="stSidebar"] [data-testid="stExpander"] p {{
    color: {DIDI_TEXT} !important; font-size: 12px !important; font-weight: 600 !important;
}}

/* Filled tiles — scoped to keyed containers only (global border wrappers
   painted tables/metrics black when theme keys got reset to #000000). */
section.main [class*="st-key-didi_tile"],
section.main [class*="st-key-didi_panel"],
section.main [class*="st-key-didi_insight"],
section.main [class*="st-key-didi_action"],
section.main [class*="st-key-didi_alert"] {{
    background: {_GRAD_CARD} !important;
    background-color: {DIDI_CARD} !important;
    border: 1px solid {DIDI_CARD_BORDER} !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 0 rgba(255,255,255,.8), 0 8px 20px rgba(26,26,26,.06);
    padding: 0.85rem 1rem 0.95rem;
    margin-bottom: 0;
    height: 100%;
    box-sizing: border-box;
}}
section.main [class*="st-key-didi_tile"] {{
    min-height: 236px;
}}
section.main [class*="st-key-didi_qa_fail_grid"] {{
    height: 100%;
    min-height: 0;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}}
section.main [class*="st-key-didi_qa_fail_grid"] > div,
section.main [class*="st-key-didi_qa_fail_grid"] [data-testid="stVerticalBlock"] {{
    height: 100% !important;
    min-height: 0 !important;
    flex: 1 1 auto !important;
    gap: 0.85rem !important;
}}
section.main [class*="st-key-didi_qa_fail_grid"] [data-testid="stHorizontalBlock"] {{
    flex: 1 1 0 !important;
    min-height: 0 !important;
}}
section.main [class*="st-key-didi_qa_fail_grid"] [class*="st-key-didi_tile"] {{
    min-height: 0 !important;
    height: 100%;
}}
section.main [class*="st-key-didi_tile_green"] {{
    box-shadow: inset 5px 0 0 {STATUS_COLORS["green"]}, 0 1px 0 rgba(255,255,255,.07), 0 12px 28px rgba(0,0,0,.32) !important;
}}
section.main [class*="st-key-didi_tile_amber"] {{
    box-shadow: inset 5px 0 0 {STATUS_COLORS["amber"]}, 0 1px 0 rgba(255,255,255,.07), 0 12px 28px rgba(0,0,0,.32) !important;
}}
section.main [class*="st-key-didi_tile_red"] {{
    box-shadow: inset 5px 0 0 {STATUS_COLORS["red"]}, 0 1px 0 rgba(255,255,255,.07), 0 12px 28px rgba(0,0,0,.32) !important;
}}
section.main [class*="st-key-didi_tile_sm"] {{
    min-height: 156px;
    padding: 0.55rem 0.8rem 0.65rem;
}}
section.main [class*="st-key-didi_tile_sm"] [data-testid="stMetricValue"] {{
    font-size: 1.28rem !important;
}}
section.main [class*="st-key-didi_tile_sm"] [data-testid="stPlotlyChart"] {{
    min-height: 64px !important;
    max-height: 72px !important;
}}
section.main [class*="st-key-didi_tile"] > div,
section.main [class*="st-key-didi_tile"] > div > div,
section.main [class*="st-key-didi_panel"] > div,
section.main [class*="st-key-didi_panel"] > div > div,
section.main [class*="st-key-didi_insight"] > div,
section.main [class*="st-key-didi_insight"] > div > div,
section.main [class*="st-key-didi_tile"] [data-testid="stVerticalBlock"],
section.main [class*="st-key-didi_tile"] [data-testid="stElementContainer"],
section.main [class*="st-key-didi_tile"] [data-testid="stMetric"],
section.main [class*="st-key-didi_tile"] [data-testid="stCaptionContainer"],
section.main [class*="st-key-didi_tile"] [data-testid="stPlotlyChart"],
section.main [class*="st-key-didi_tile"] [data-testid="stPlotlyChart"] > div,
section.main [class*="st-key-didi_rcard"] [data-testid="stVerticalBlock"],
section.main [class*="st-key-didi_rcard"] [data-testid="stElementContainer"],
section.main [class*="st-key-didi_rcard"] [data-testid="stMetric"],
section.main [class*="st-key-didi_rcard"] [data-testid="stCaptionContainer"],
section.main [class*="st-key-didi_rcard"] [data-testid="stPlotlyChart"],
section.main [class*="st-key-didi_rcard"] [data-testid="stPlotlyChart"] > div,
section.main [class*="st-key-didi_panel"] [data-testid="stVerticalBlock"],
section.main [class*="st-key-didi_panel"] [data-testid="stElementContainer"],
section.main [class*="st-key-didi_insight"] [data-testid="stVerticalBlock"],
section.main [class*="st-key-didi_insight"] [data-testid="stElementContainer"],
section.main [class*="st-key-didi_action"] > div,
section.main [class*="st-key-didi_action"] > div > div,
section.main [class*="st-key-didi_action"] [data-testid="stVerticalBlock"],
section.main [class*="st-key-didi_action"] [data-testid="stElementContainer"] {{
    background: transparent !important;
    background-color: transparent !important;
}}
section.main [class*="st-key-didi_tile"] [data-testid="stPlotlyChart"] {{
    min-height: 80px !important;
    max-height: 88px !important;
}}
section.main [class*="st-key-didi_rcard"] {{
    min-height: 248px;
    text-align: center;
    background: transparent !important;
    background-color: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
    padding: 0;
    margin-bottom: 0;
    height: 100%;
}}
section.main [class*="st-key-didi_rcard"] [data-testid="stVerticalBlockBorderWrapper"] {{
    background: {DIDI_WHITE} !important;
    background-color: {DIDI_WHITE} !important;
    border: 1px solid {DIDI_CARD_BORDER} !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 0 rgba(255,255,255,.8), 0 8px 20px rgba(26,26,26,.06);
    padding: 0.85rem 1rem 0.95rem;
    height: 100%;
    box-sizing: border-box;
}}
section.main [class*="st-key-didi_rcard_on"] [data-testid="stVerticalBlockBorderWrapper"],
section.main [class*="st-key-didi_rcard"]:has(.didi-rcard-flag--on) [data-testid="stVerticalBlockBorderWrapper"] {{
    border-color: rgba({_ORANGE_RGB},.88) !important;
    box-shadow: 0 0 0 1px rgba({_ORANGE_RGB},.28), 0 12px 28px rgba(0,0,0,.32);
}}
section.main [class*="st-key-didi_tile_green"] [data-testid="stMetricValue"],
[class*="st-key-didi_tile_green"] [data-testid="stMetricValue"] {{
    color: {STATUS_COLORS["green"]} !important;
}}
section.main [class*="st-key-didi_tile_amber"] [data-testid="stMetricValue"],
[class*="st-key-didi_tile_amber"] [data-testid="stMetricValue"] {{
    color: {STATUS_COLORS["amber"]} !important;
}}
section.main [class*="st-key-didi_tile_red"] [data-testid="stMetricValue"],
[class*="st-key-didi_tile_red"] [data-testid="stMetricValue"] {{
    color: {STATUS_COLORS["red"]} !important;
}}
section.main [class*="st-key-didi_rcard"] [data-testid="stPlotlyChart"] {{
    min-height: 110px !important;
    max-height: 160px !important;
}}
/* Preview-card titles are Streamlit buttons. Match .didi-panel-title fill.
   Do not require section.main — Streamlit 1.61 uses stMain, not class "main". */
[class*="st-key-didi_rcard"] button,
[class*="st-key-didi_rcard"] [data-testid^="stBaseButton"],
[class*="st-key-didi_rcard"] [data-testid^="stBaseButton"] > div,
[class*="st-key-pvbtn"] button,
[class*="st-key-pvbtn"] [data-testid^="stBaseButton"],
[class*="st-key-pvbtn"] [data-testid^="stBaseButton"] > div,
section.main [class*="st-key-didi_rcard"] button,
section.main [class*="st-key-didi_rcard"] [data-testid^="stBaseButton"],
section.main [class*="st-key-didi_rcard"] [data-testid^="stBaseButton"] > div,
section.main [class*="st-key-pvbtn"] button,
section.main [class*="st-key-pvbtn"] [data-testid^="stBaseButton"],
section.main [class*="st-key-pvbtn"] [data-testid^="stBaseButton"] > div,
section[data-testid="stMain"] [class*="st-key-didi_rcard"] button,
section[data-testid="stMain"] [class*="st-key-didi_rcard"] [data-testid^="stBaseButton"],
section[data-testid="stMain"] [class*="st-key-pvbtn"] button,
section[data-testid="stMain"] [class*="st-key-pvbtn"] [data-testid^="stBaseButton"] {{
    background-image: none !important;
    background: {DIDI_DARK} !important;
    background-color: {DIDI_DARK} !important;
    border: 1px solid {DIDI_DARK} !important;
    border-bottom: 3px solid {DIDI_ORANGE} !important;
    border-radius: 8px !important;
    box-shadow: 0 6px 14px rgba(0,0,0,.22) !important;
    color: {DIDI_WHITE} !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    letter-spacing: .01em;
    text-transform: none;
    text-align: center !important;
    justify-content: center !important;
    padding: 0.42rem 0.7rem !important;
    min-height: 2.45rem !important;
    height: auto !important;
    white-space: normal !important;
    line-height: 1.25 !important;
}}
[class*="st-key-didi_rcard"][class*="btnpie"] button,
[class*="st-key-didi_rcard"][class*="btnscope"] button,
[class*="st-key-didi_rcard"][class*="btnch"] button,
[class*="st-key-didi_rcard"][class*="btncr"] button,
[class*="st-key-didi_rcard"][class*="btngroup"] button,
[class*="st-key-didi_rcard"][class*="btndaily"] button,
[class*="st-key-didi_rcard"][class*="btnscat"] button {{
    background-image: none !important;
    background: {DIDI_DARK} !important;
    background-color: {DIDI_DARK} !important;
    box-shadow: 0 6px 14px rgba(0,0,0,.22) !important;
}}
[class*="st-key-didi_rcard"] button:hover,
[class*="st-key-didi_rcard"] [data-testid^="stBaseButton"]:hover,
[class*="st-key-pvbtn"] button:hover,
[class*="st-key-pvbtn"] [data-testid^="stBaseButton"]:hover,
section.main [class*="st-key-didi_rcard"] button:hover,
section.main [class*="st-key-pvbtn"] button:hover,
section[data-testid="stMain"] [class*="st-key-didi_rcard"] button:hover,
section[data-testid="stMain"] [class*="st-key-pvbtn"] button:hover {{
    background: {DIDI_ORANGE} !important;
    background-color: {DIDI_ORANGE} !important;
    border-color: {DIDI_ORANGE} !important;
    border-bottom: 3px solid {DIDI_DARK} !important;
    color: #FFFFFF !important;
    filter: none;
    box-shadow: 0 8px 18px rgba({_ORANGE_RGB}, .35) !important;
    cursor: pointer;
}}
[class*="st-key-didi_rcard"] button:hover p,
[class*="st-key-pvbtn"] button:hover p,
section.main [class*="st-key-didi_rcard"] button:hover p,
section[data-testid="stMain"] [class*="st-key-didi_rcard"] button:hover p {{
    color: #FFFFFF !important;
}}
section.main [class*="st-key-didi_rcard"] [data-testid="stVerticalBlockBorderWrapper"]:hover {{
    border-color: {DIDI_ORANGE} !important;
    box-shadow: 0 0 0 1px rgba({_ORANGE_RGB},.35), 0 12px 28px rgba(0,0,0,.14);
}}
[class*="st-key-didi_rcard"] button p,
[class*="st-key-pvbtn"] button p,
[class*="st-key-didi_rcard"] [data-testid^="stBaseButton"] p,
[class*="st-key-pvbtn"] [data-testid^="stBaseButton"] p,
section.main [class*="st-key-didi_rcard"] button p,
section.main [class*="st-key-pvbtn"] button p {{
    font-weight: 700 !important;
    text-transform: none !important;
    letter-spacing: .01em !important;
    font-size: 0.76rem !important;
    text-align: center !important;
    white-space: normal !important;
    line-height: 1.25 !important;
    color: #FFFFFF !important;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}
section.main [class*="st-key-didi_rcard"] [data-testid="stMetric"],
section.main [class*="st-key-didi_rcard"] [data-testid="stMetric"] > div {{
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
}}

[data-testid="stMetricValue"] {{
    font-size: 1.7rem !important; font-weight: 600 !important;
    color: {DIDI_TEXT} !important; letter-spacing: -0.03em; line-height: 1.15 !important;
    font-family: Inter, "Segoe UI", system-ui, sans-serif !important;
}}
[data-testid="stMetricLabel"] {{
    color: {DIDI_MUTED} !important; text-transform: uppercase; letter-spacing: .08em;
    font-size: 0.68rem !important; font-weight: 500 !important;
}}
[data-testid="stMetricDelta"] {{ font-size: 0.78rem !important; font-weight: 500 !important; }}

h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
    color: {DIDI_TEXT} !important; font-family: Inter, "Segoe UI", system-ui, sans-serif !important;
    font-weight: 600 !important; letter-spacing: -0.02em;
}}
.main .stMarkdown, .main p {{ color: {DIDI_TEXT}; }}
section.main div[data-testid="stExpander"] {{
    background: {_GRAD_CARD} !important; border-radius: 12px; border: 1px solid {DIDI_CARD_BORDER};
    margin: 0 !important;
}}
section.main [data-testid="stExpander"] details summary,
section.main [data-testid="stExpander"] [data-testid="stExpanderHeader"] {{
    background-image: none !important;
    background-color: {DIDI_DARK} !important;
    color: {DIDI_WHITE} !important;
    border-radius: 8px !important;
    border-bottom: 3px solid {DIDI_ORANGE} !important;
    padding: 0.45rem 0.75rem !important;
}}
section.main [data-testid="stExpander"] details summary p,
section.main [data-testid="stExpander"] [data-testid="stExpanderHeader"] p {{
    color: {DIDI_WHITE} !important;
    font-weight: 700 !important;
}}

button[kind="primary"],
[data-testid="stBaseButton-primary"] {{
    background: {DIDI_ORANGE} !important; color: {DIDI_WHITE} !important;
    border: none !important; font-weight: 700 !important;
    transition: filter .15s ease, transform .15s ease !important;
}}
button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover {{
    filter: brightness(0.9);
}}
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-header"] {{
    transition: background .15s ease, filter .15s ease, border-color .15s ease !important;
}}
[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stBaseButton-header"]:hover {{
    filter: brightness(0.88);
    border-color: rgba({_ORANGE_RGB},.45) !important;
}}

.didi-wordmark {{
    display: inline-flex; align-items: center; justify-content: center;
    background: {DIDI_ORANGE}; color: {DIDI_WHITE};
    font-weight: 700; font-size: 1.2rem; letter-spacing: .14em;
    padding: 0.52rem 1.05rem; border-radius: 10px; line-height: 1; flex-shrink: 0;
    box-shadow: 0 4px 14px rgba({_ORANGE_RGB},.28);
}}
.didi-head-top {{
    display: flex; flex-direction: row; align-items: stretch;
    gap: 18px; width: 100%; flex-wrap: wrap;
}}
.didi-head-titlebox {{
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    text-align: center;
    flex: 1.15 1 320px;
    width: auto;
    min-width: 260px;
    margin: 0;
    padding: 22px 28px 20px;
    background: {DIDI_DARK};
    border: 1px solid {DIDI_DARK};
    border-bottom: 3px solid {DIDI_ORANGE};
    border-radius: 14px;
    box-sizing: border-box;
    box-shadow: 0 10px 28px rgba(0,0,0,.34);
}}
.didi-head-titlebox .didi-wordmark {{
    font-size: 1.05rem; padding: 0.44rem 0.95rem; letter-spacing: .16em; margin: 0 0 12px;
    background: {DIDI_ORANGE}; color: {DIDI_WHITE}; box-shadow: none;
}}
.didi-head-title {{
    font-size: 1.85rem; font-weight: 800; color: {DIDI_WHITE};
    letter-spacing: .06em; line-height: 1.12; margin: 0; text-transform: uppercase;
    text-align: center;
}}
.didi-head-sub {{
    font-size: 0.9rem; color: rgba(255,255,255,.82); margin: 10px 0 0; font-weight: 400;
    text-align: center; letter-spacing: .02em;
}}
.didi-head-meta {{
    display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
    margin: 12px 0 0; color: {DIDI_ORANGE}; font-size: 0.84rem; font-weight: 600;
}}
.didi-head-meta svg {{ width: 15px; height: 15px; flex-shrink: 0; }}
.didi-head-meta-split {{
    width: 1px; height: 12px; background: rgba({_ORANGE_RGB},.45); flex-shrink: 0;
}}
.didi-head-right {{
    display: flex; flex-direction: column; align-items: stretch; justify-content: flex-start;
    gap: 8px; flex: 1 1 300px; min-width: 280px; margin: 0;
}}
.didi-head-updated {{
    display: flex; align-items: center; justify-content: flex-end; gap: 6px;
    color: {DIDI_MUTED}; font-size: 0.72rem; font-weight: 500;
}}
.didi-head-updated svg {{ width: 13px; height: 13px; }}
.didi-targets-box {{
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 12px;
    background: {DIDI_DARK};
    border: 1px solid {DIDI_DARK};
    border-bottom: 3px solid {DIDI_ORANGE};
    border-radius: 14px;
    padding: 16px 18px 18px;
    min-width: 0;
    width: 100%;
    flex: 1;
    box-sizing: border-box;
    box-shadow: 0 10px 28px rgba(0,0,0,.34);
}}
.didi-targets-kicker {{
    color: {DIDI_WHITE}; font-size: 11px; font-weight: 700;
    letter-spacing: .14em; text-transform: uppercase; margin: 0;
    width: 100%; text-align: center;
}}
.didi-targets {{
    display: flex; align-items: center; justify-content: center;
    gap: 22px; flex-wrap: wrap; width: 100%;
}}
.didi-targets-legend {{
    display: flex; align-items: center; justify-content: center;
    gap: 8px 20px; flex-wrap: wrap; width: 100%;
    padding-top: 10px;
    border-top: 1px solid rgba(255,255,255,.18);
}}
.didi-targets-legend .didi-light-item {{
    color: rgba(255,255,255,.82); font-size: 0.74rem;
}}
.didi-tgt {{
    display: flex; align-items: center; gap: 10px;
    font-size: 1.02rem; font-weight: 600; white-space: nowrap;
    color: {DIDI_WHITE};
}}
.didi-tgt-ico {{
    width: 32px; height: 32px; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    background: rgba(255,255,255,.1);
    color: {DIDI_WHITE};
    border: 1px solid rgba({_ORANGE_RGB},.55);
}}
.didi-tgt-ico svg {{ width: 16px; height: 16px; }}
.didi-page {{
    font-size: 0.72rem; font-weight: 600; color: {DIDI_ORANGE};
    letter-spacing: .12em; text-transform: uppercase; margin: 0;
}}
section.main [class*="st-key-didi_head"] {{
    background: {_GRAD_CARD} !important;
    background-color: {DIDI_CARD} !important;
    border: 1px solid {DIDI_CARD_BORDER} !important;
    border-radius: 16px !important;
    box-shadow: 0 8px 20px rgba(26,26,26,.06);
    padding: 1.15rem 1.35rem 1.1rem !important;
    margin: 0;
}}
section.main [class*="st-key-didi_head"] > div,
section.main [class*="st-key-didi_head"] > div > div,
section.main [class*="st-key-didi_head"] [data-testid="stVerticalBlock"],
section.main [class*="st-key-didi_head"] [data-testid="stElementContainer"] {{
    background: transparent !important;
    background-color: transparent !important;
}}
.didi-kpi-banner-wrap {{
    display: flex; justify-content: center; width: 100%;
    margin: 0.35rem 0 0.1rem;
}}
.didi-kpi-banner {{
    display: inline-block;
    background: {DIDI_DARK};
    border: 1px solid {DIDI_DARK};
    border-bottom: 3px solid {DIDI_ORANGE};
    border-radius: 10px;
    padding: 8px 22px;
    color: {DIDI_WHITE};
    font-size: 0.92rem;
    font-weight: 700;
    letter-spacing: .02em;
    text-align: center;
    line-height: 1.25;
    box-shadow: 0 8px 18px rgba(0,0,0,.28);
}}
.didi-rule-h {{
    display: flex;
    align-items: center;
    gap: 14px;
    width: 100%;
    margin: 1.4rem 0 0.75rem;
}}
.didi-rule-h::before,
.didi-rule-h::after {{
    content: "";
    flex: 1;
    height: 1px;
    background: rgba(26,26,26,.16);
}}
.didi-rule-h span {{
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: .14em;
    text-transform: uppercase;
    color: {DIDI_MUTED};
    white-space: nowrap;
}}
.didi-section {{
    margin: 1.45rem 0 0.7rem; padding-bottom: 0;
    border-bottom: none;
}}
.didi-section-box,
.didi-section-box--01,
.didi-section-box--02,
.didi-section-box--03,
.didi-section-box--04,
.didi-section-box--05,
.didi-section-box--06,
.didi-section-box--07 {{
    border-radius: 12px;
    padding: 13px 16px 14px;
    text-align: center;
    width: 100%;
    box-sizing: border-box;
    border: 1px solid {DIDI_DARK};
    background: {DIDI_DARK};
    box-shadow: 0 8px 22px rgba(0,0,0,.28);
    border-bottom: 3px solid {DIDI_ORANGE};
}}
.didi-section-kicker,
.didi-section-box--01 .didi-section-kicker,
.didi-section-box--02 .didi-section-kicker,
.didi-section-box--03 .didi-section-kicker,
.didi-section-box--05 .didi-section-kicker,
.didi-section-box--06 .didi-section-kicker {{
    color: rgba(255,255,255,.88); font-size: 10px; font-weight: 700;
    letter-spacing: .1em; text-transform: uppercase; margin: 0;
    text-align: center; width: 100%;
}}
.didi-section-title {{
    color: #FFFFFF; font-size: 1.12rem; font-weight: 700;
    letter-spacing: -0.02em; margin: 3px 0 0;
    text-align: center; width: 100%;
}}
.didi-section-hint {{
    color: rgba(255,255,255,.84); font-size: 0.78rem; margin: 5px 0 0;
    text-align: center; width: 100%; line-height: 1.35;
}}
.didi-insight {{
    border-left: 4px solid {DIDI_ORANGE};
    padding: 2px 2px 2px 12px;
}}
.didi-insight--ok {{ border-left-color: #3DDC82; }}
.didi-insight--warn {{ border-left-color: #F2A900; }}
.didi-insight--off {{ border-left-color: #F07167; }}
.didi-insight-kicker {{
    color: #F07167; font-size: 11px; font-weight: 700;
    letter-spacing: .1em; text-transform: uppercase; margin: 0 0 8px;
}}
.didi-insight--ok .didi-insight-kicker {{ color: #3DDC82; }}
.didi-insight--warn .didi-insight-kicker {{ color: #F2A900; }}
.didi-insight--off .didi-insight-kicker {{ color: #F07167; }}
.didi-insight-body {{
    color: {DIDI_TEXT}; font-size: 0.95rem; line-height: 1.45; margin: 0 0 10px; font-weight: 500;
}}
.didi-insight-hyp {{
    color: {DIDI_MUTED}; font-size: 0.78rem; margin: 8px 0 0; line-height: 1.4;
}}
.didi-flag {{
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 600; letter-spacing: .04em;
    padding: 4px 8px; border-radius: 999px; margin: 0 6px 6px 0;
    background: rgba(255,255,255,.06); color: {DIDI_TEXT};
}}

.didi-side-banner {{
    background: {DIDI_DARK};
    border: 1px solid {DIDI_DARK};
    border-bottom: 3px solid {DIDI_ORANGE};
    border-radius: 12px;
    padding: 14px 14px 13px;
    text-align: center;
    margin: 0.1rem 0 0.85rem;
    box-shadow: 0 8px 18px rgba(0,0,0,.28);
    width: 100%;
    box-sizing: border-box;
}}
.didi-side-banner .didi-wordmark {{
    margin: 0 0 10px; font-size: 0.78rem; padding: 0.32rem 0.62rem; letter-spacing: .12em;
    display: inline-flex;
    background: {DIDI_ORANGE}; color: {DIDI_WHITE}; box-shadow: none;
}}
.didi-side-banner-title {{
    color: {DIDI_WHITE}; font-size: 1.05rem; font-weight: 700;
    letter-spacing: -0.03em; line-height: 1.25;
}}
.didi-side-banner-sub {{
    color: rgba(255,255,255,.82); font-size: 0.75rem; font-weight: 500;
    margin: 6px 0 0; letter-spacing: .01em;
}}
.didi-corr-notes {{
    color: {DIDI_MUTED}; font-size: 0.82rem; line-height: 1.5;
    margin: 0.45rem 0 0; padding-left: 1.15rem;
}}
.didi-corr-notes li {{ margin: 0.22rem 0; }}
.didi-notes-kicker {{
    color: {DIDI_ORANGE}; font-size: 11px; font-weight: 700;
    letter-spacing: .08em; text-transform: uppercase; margin: 0.7rem 0 0.15rem;
}}
.didi-notes {{
    color: {DIDI_TEXT}; font-size: 0.86rem; line-height: 1.48;
    margin: 0 0 0.15rem; padding-left: 1.15rem;
}}
.didi-notes li {{ margin: 0.28rem 0; }}
.didi-panel-title {{
    text-align: center; font-weight: 700; font-size: 0.95rem;
    color: {DIDI_WHITE}; margin: 0 0 0.55rem;
    width: 100%; display: block;
    background: {DIDI_DARK};
    border: 1px solid {DIDI_DARK};
    border-bottom: 3px solid {DIDI_ORANGE};
    border-radius: 8px;
    padding: 0.42rem 0.7rem;
    box-shadow: 0 6px 14px rgba(0,0,0,.22);
}}
.didi-panel-sub {{
    text-align: center; width: 100%; display: block;
    color: {DIDI_MUTED}; font-size: 0.78rem; margin: 0 0 0.55rem;
}}
section.main [class*="st-key-didi_panel"] p.didi-panel-title,
section.main [class*="st-key-didi_panel"] p.didi-panel-sub {{
    text-align: center !important;
}}
[class*="st-key-didi_tile"] p.didi-panel-title,
section.main [class*="st-key-didi_tile"] p.didi-panel-title,
section[data-testid="stMain"] [class*="st-key-didi_tile"] p.didi-panel-title {{
    text-align: center !important;
    color: {DIDI_WHITE} !important;
}}
[class*="st-key-didi_tile"] p.didi-panel-title,
section.main [class*="st-key-didi_tile"] p.didi-panel-title,
section[data-testid="stMain"] [class*="st-key-didi_tile"] p.didi-panel-title {{
    margin: 0 0 0.45rem !important;
    white-space: normal;
    line-height: 1.25;
    box-sizing: border-box;
    font-weight: 700 !important;
}}
[class*="st-key-didi_tile"] [data-testid="stMarkdownContainer"]:has(p.didi-panel-title),
section.main [class*="st-key-didi_tile"] [data-testid="stMarkdownContainer"]:has(p.didi-panel-title),
section[data-testid="stMain"] [class*="st-key-didi_tile"] [data-testid="stMarkdownContainer"]:has(p.didi-panel-title) {{
    width: 100% !important;
    text-align: center !important;
}}
[class*="st-key-didi_tile_sm"] p.didi-panel-title,
section.main [class*="st-key-didi_tile_sm"] p.didi-panel-title,
section[data-testid="stMain"] [class*="st-key-didi_tile_sm"] p.didi-panel-title {{
    font-size: 0.82rem;
    padding: 0.34rem 0.55rem;
}}
.didi-tile-help {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.05em;
    height: 1.05em;
    margin-left: 0.4rem;
    border: 1.5px solid rgba(255,255,255,.55);
    border-radius: 50%;
    font-size: 0.72rem;
    font-weight: 700;
    line-height: 1;
    vertical-align: 0.08em;
    cursor: help;
    color: {DIDI_WHITE};
}}
[class*="st-key-didi_tile"] [data-testid="stMetricLabel"],
section.main [class*="st-key-didi_tile"] [data-testid="stMetricLabel"],
section[data-testid="stMain"] [class*="st-key-didi_tile"] [data-testid="stMetricLabel"] {{
    display: none !important;
}}
.didi-mkt-stack {{
    display: flex; flex-direction: column; gap: 0.55rem;
}}
.didi-mkt-box {{
    background: {DIDI_CARD};
    border: 1px solid {DIDI_CARD_BORDER};
    border-radius: 10px;
    overflow: hidden;
}}
.didi-mkt-box-title {{
    background: {DIDI_DARK};
    color: {DIDI_WHITE};
    border-bottom: 3px solid {DIDI_ORANGE};
    font-size: 0.82rem;
    font-weight: 700;
    text-align: center;
    padding: 0.38rem 0.6rem;
    margin: 0;
}}
.didi-mkt-row {{
    display: grid;
    grid-template-columns: 10px minmax(0, 1fr) auto auto;
    gap: 0.4rem;
    align-items: center;
    padding: 0.32rem 0.7rem;
    border-top: 1px solid {DIDI_CARD_BORDER};
    font-size: 0.82rem;
}}
.didi-mkt-row.is-on {{
    background: rgba(255,102,0,0.10);
}}
.didi-mkt-dot {{
    width: 8px; height: 8px; border-radius: 50%; display: inline-block;
}}
.didi-mkt-name {{
    color: {DIDI_TEXT}; font-weight: 650; overflow: hidden;
    text-overflow: ellipsis; white-space: nowrap;
}}
.didi-mkt-n {{ color: {DIDI_MUTED}; font-size: 0.72rem; }}
.didi-mkt-val {{
    color: {DIDI_TEXT}; font-weight: 700;
    font-variant-numeric: tabular-nums; white-space: nowrap;
}}
.didi-mkt-foot {{
    color: {DIDI_MUTED};
    font-size: 0.72rem;
    padding: 0.35rem 0.7rem 0.5rem;
    line-height: 1.35;
    margin: 0;
    border-top: 1px solid {DIDI_CARD_BORDER};
}}
.didi-action {{
    border-left: 4px solid {DIDI_ORANGE};
    padding: 2px 2px 2px 12px;
}}
.didi-action-kicker {{
    color: {DIDI_WHITE}; font-size: 0.82rem; font-weight: 700;
    letter-spacing: .04em; text-transform: none; margin: 0 0 10px;
    background: {DIDI_DARK};
    border: 1px solid {DIDI_DARK};
    border-bottom: 3px solid {DIDI_ORANGE};
    border-radius: 8px;
    padding: 0.42rem 0.7rem;
    text-align: center;
}}

section[data-testid="stSidebar"] [class*="st-key-flt_period"],
section[data-testid="stSidebar"] [class*="st-key-flt_filters"],
section[data-testid="stSidebar"] [class*="st-key-flt_qa"],
section[data-testid="stSidebar"] [class*="st-key-flt_csat"] {{
    background: {DIDI_WHITE} !important;
    border: 1px solid {DIDI_CARD_BORDER} !important;
    border-radius: 12px !important;
    padding: 0.2rem 0.4rem 0.45rem;
    margin-bottom: 0.5rem;
    width: 100% !important;
    box-sizing: border-box !important;
    transition: background .15s ease, border-color .15s ease, filter .15s ease;
}}
section[data-testid="stSidebar"] [class*="st-key-flt_period"] {{
    border-left: 3px solid #3D7AB5 !important;
}}
section[data-testid="stSidebar"] [class*="st-key-flt_filters"] {{
    border-left: 3px solid {DIDI_ORANGE} !important;
}}
section[data-testid="stSidebar"] [class*="st-key-flt_qa"] {{
    border-left: 3px solid #2E9B57 !important;
}}
section[data-testid="stSidebar"] [class*="st-key-flt_csat"] {{
    border-left: 3px solid #8B7CF6 !important;
}}
section[data-testid="stSidebar"] [class*="st-key-flt_period"]:hover,
section[data-testid="stSidebar"] [class*="st-key-flt_filters"]:hover,
section[data-testid="stSidebar"] [class*="st-key-flt_qa"]:hover,
section[data-testid="stSidebar"] [class*="st-key-flt_csat"]:hover {{
    background: {DIDI_GRAY} !important;
    border-color: rgba({_ORANGE_RGB},.35) !important;
    filter: brightness(0.94);
}}
section[data-testid="stSidebar"] [class*="st-key-flt_period"] [data-testid="stExpander"],
section[data-testid="stSidebar"] [class*="st-key-flt_filters"] [data-testid="stExpander"],
section[data-testid="stSidebar"] [class*="st-key-flt_qa"] [data-testid="stExpander"],
section[data-testid="stSidebar"] [class*="st-key-flt_csat"] [data-testid="stExpander"] {{
    background: transparent !important;
    border: none !important;
    margin-bottom: 0;
}}
section[data-testid="stSidebar"] [data-testid="stExpander"] summary {{
    border-radius: 8px;
    transition: background .15s ease;
}}
section[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {{
    background: rgba(0,0,0,.22) !important;
}}
section[data-testid="stSidebar"] [data-baseweb="select"] {{
    transition: background .15s ease, border-color .15s ease !important;
}}
section[data-testid="stSidebar"] [data-baseweb="select"]:hover {{
    border-color: rgba({_ORANGE_RGB},.45) !important;
    background: {DIDI_GRAY} !important;
}}
section[data-testid="stSidebar"] [data-testid="stCheckbox"] label:hover,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"]:hover {{
    filter: brightness(0.92);
}}
section[data-testid="stSidebar"] [class*="st-key-reset_"] button {{
    background: {DIDI_ORANGE} !important;
    color: {DIDI_WHITE} !important;
    border: 1px solid {DIDI_ORANGE} !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    width: 100% !important;
    box-sizing: border-box !important;
    transition: background .15s ease, filter .15s ease !important;
}}
section[data-testid="stSidebar"] [class*="st-key-reset_"] button:hover {{
    background: #E85A00 !important;
    filter: brightness(0.96);
    color: {DIDI_WHITE} !important;
}}
section.main [class*="st-key-didi_action"] {{
    background: {DIDI_WHITE} !important;
    border: 1px solid {DIDI_CARD_BORDER} !important;
    border-left: 4px solid {DIDI_ORANGE} !important;
    border-radius: 12px !important;
    padding: 0.85rem 1rem 0.95rem;
    margin-bottom: 0;
}}
section.main [class*="st-key-didi_tile"] {{
    text-align: center;
}}
section.main [class*="st-key-didi_tile"] [data-testid="stMetric"],
section.main [class*="st-key-didi_tile"] [data-testid="stMetric"] > div {{
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
}}
[data-testid="stMetricValue"],
[data-testid="stMetricLabel"],
[data-testid="stMetricDelta"] {{
    justify-content: center !important;
    text-align: center !important;
    width: 100%;
}}
section.main [class*="st-key-didi_tile"] [data-testid="stCaptionContainer"] {{
    text-align: center;
}}
section.main [class*="st-key-didi_panel"] [data-testid="stCaptionContainer"] {{
    text-align: center;
}}
.didi-side-pages-head {{
    text-align: left;
    width: 100%;
    margin: 0.2rem 0 0.55rem;
    padding: 0.1rem 2px 0.5rem;
    border-bottom: 1px solid rgba(255,255,255,.12);
}}
.didi-side-kicker {{
    color: {DIDI_TEXT} !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    letter-spacing: .16em !important;
    text-transform: uppercase !important;
    margin: 0 !important;
    text-align: left !important;
    line-height: 1.2 !important;
}}

header[data-testid="stHeader"] {{
    visibility: visible !important;
    background: transparent !important;
    height: 3rem;
}}
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {{
    visibility: visible !important;
    display: flex !important;
    opacity: 1 !important;
    z-index: 1000000 !important;
    background: {DIDI_CARD} !important;
    border: 1px solid {DIDI_CARD_BORDER} !important;
    border-radius: 8px !important;
    color: {DIDI_TEXT} !important;
}}
#MainMenu, footer {{ visibility: hidden; }}
.didi-chip {{
    display: flex; align-items: center; gap: 8px; flex: 1; min-width: 210px;
    background: {_TILE}; border: 1px solid {DIDI_CARD_BORDER}; border-radius: 10px;
    padding: 10px 12px;
}}
.didi-chip-dot {{
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; background: currentColor;
}}
.didi-chip-name {{
    color: {DIDI_MUTED}; font-size: 10px; font-weight: 600;
    letter-spacing: .08em; text-transform: uppercase;
}}
.didi-chip-val {{
    color: {DIDI_TEXT}; font-size: 1.05rem; font-weight: 600;
    letter-spacing: -0.02em; margin-left: auto;
}}
.didi-chip-vs {{ color: {DIDI_MUTED}; font-size: 11px; }}
.didi-chip-state {{ font-size: 10px; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; }}
.didi-chip--ok {{ color: #3DDC82; border-color: rgba(61,220,130,.28); }}
.didi-chip--warn {{ color: #F2A900; border-color: rgba(242,169,0,.32); }}
.didi-chip--off {{ color: #F07167; border-color: rgba(240,113,103,.38); }}
.didi-chip--neutral {{ color: {DIDI_MUTED}; }}
.didi-light-legend {{
    display: flex; flex-wrap: wrap; gap: 14px 22px;
    margin: 0; padding: 0;
}}
.didi-light-item {{
    display: inline-flex; align-items: center; gap: 7px;
    color: {DIDI_MUTED}; font-size: 0.78rem; font-weight: 550;
}}
.didi-light-dot {{
    width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0;
}}
.didi-light-tag {{
    display: inline-flex; align-items: center; gap: 6px;
    margin: 0.05rem 0 0.1rem; font-size: 0.72rem; font-weight: 650;
    letter-spacing: .04em; text-transform: uppercase;
}}
.didi-light-tag span {{
    width: 8px; height: 8px; border-radius: 50%; display: inline-block;
}}
.didi-light-tag--green {{ color: {STATUS_COLORS["green"]}; }}
.didi-light-tag--green span {{ background: {STATUS_COLORS["green"]}; }}
.didi-light-tag--amber {{ color: {STATUS_COLORS["amber"]}; }}
.didi-light-tag--amber span {{ background: {STATUS_COLORS["amber"]}; }}
.didi-light-tag--red {{ color: {STATUS_COLORS["red"]}; }}
.didi-light-tag--red span {{ background: {STATUS_COLORS["red"]}; }}
.didi-note {{
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    font-size: 0.80rem;
    line-height: 1.28;
    font-weight: 550;
    padding: 0.42rem 0.65rem;
    border-radius: 8px;
    margin: 0;
    max-width: 100%;
}}
.didi-note--off {{
    background: rgba(240,113,103,.12);
    color: #9F1239;
    border: 1px solid rgba(240,113,103,.28);
}}
.didi-note--ok {{
    background: rgba(46,155,87,.12);
    color: #166534;
    border: 1px solid rgba(46,155,87,.28);
}}
.didi-note--info {{
    background: rgba(46,111,190,.10);
    color: #1E4E8C;
    border: 1px solid rgba(46,111,190,.28);
}}
.didi-rbox {{
    text-align: left;
    background: {DIDI_GRAY};
    border: 1px solid {DIDI_CARD_BORDER};
    border-radius: 10px;
    padding: 0.7rem 0.85rem;
    margin: 0.2rem 0 0;
}}
.didi-rbox strong {{
    display: block;
    font-weight: 700;
    color: {DIDI_TEXT};
    font-size: 0.82rem;
    margin: 0 0 0.28rem;
}}
.didi-rbox p {{
    margin: 0;
    color: {DIDI_MUTED};
    font-size: 0.80rem;
    line-height: 1.35;
}}
.didi-qpill {{
    display: flex; width: 100%; height: 10px; border-radius: 99px;
    overflow: hidden; background: {DIDI_GRAY}; margin: 6px 0 4px;
    border: 1px solid {DIDI_CARD_BORDER};
}}
.didi-qpill > span {{ display: block; height: 100%; min-width: 0; }}
.didi-qpill-legend {{
    display: flex; flex-wrap: wrap; gap: 8px;
    color: {DIDI_MUTED}; font-size: 0.64rem; font-weight: 650;
    margin: 0 0 0.35rem;
}}
.didi-qbadge {{
    display: inline-flex; align-items: center;
    border-radius: 99px; padding: 2px 8px;
    font-size: 0.64rem; font-weight: 800; letter-spacing: .06em;
}}
.didi-qbadge--Q1 {{ background: rgba(46,155,87,.14); color: #166534; }}
.didi-qbadge--Q2 {{ background: rgba(46,111,190,.14); color: #1E4E8C; }}
.didi-qbadge--Q3 {{ background: rgba(242,169,0,.16); color: #8A6200; }}
.didi-qbadge--Q4 {{ background: rgba(214,69,69,.14); color: #9F1239; }}
.didi-qcol {{
    background: {DIDI_WHITE};
    border: 1px solid {DIDI_CARD_BORDER};
    border-radius: 10px;
    padding: 8px 10px;
    min-height: 120px;
}}
.didi-qcol-h {{
    margin: 0 0 6px;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: .04em;
}}
.didi-qcol--Q1 {{ border-top: 3px solid {STATUS_COLORS["green"]}; }}
.didi-qcol--Q2 {{ border-top: 3px solid {STATUS_COLORS["blue"]}; }}
.didi-qcol--Q3 {{ border-top: 3px solid {STATUS_COLORS["amber"]}; }}
.didi-qcol--Q4 {{ border-top: 3px solid {STATUS_COLORS["red"]}; }}
.didi-qcol ul {{
    margin: 0; padding: 0; list-style: none;
    color: {DIDI_TEXT}; font-size: 0.72rem; line-height: 1.4;
}}
.didi-qcol li {{ margin: 0 0 2px; overflow-wrap: anywhere; }}
.didi-qcol-more {{ color: {DIDI_MUTED}; font-weight: 650; }}
.didi-qrange {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin: 0 0 10px;
}}
.didi-qrange-card {{
    background: {DIDI_WHITE};
    border: 1px solid {DIDI_CARD_BORDER};
    border-radius: 10px;
    padding: 8px 10px 10px;
}}
.didi-qrange-card--Q1 {{ border-top: 3px solid {STATUS_COLORS["green"]}; }}
.didi-qrange-card--Q2 {{ border-top: 3px solid {STATUS_COLORS["blue"]}; }}
.didi-qrange-card--Q3 {{ border-top: 3px solid {STATUS_COLORS["amber"]}; }}
.didi-qrange-card--Q4 {{ border-top: 3px solid {STATUS_COLORS["red"]}; }}
.didi-qrange-k {{
    margin: 0;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: .04em;
    text-transform: uppercase;
}}
.didi-qrange-v {{
    margin: 4px 0 2px;
    font-size: 0.92rem;
    font-weight: 800;
    color: {DIDI_TEXT};
    line-height: 1.25;
}}
.didi-qrange-s {{
    margin: 0;
    font-size: 0.7rem;
    color: {DIDI_MUTED};
    font-weight: 600;
}}
.didi-coach-copy {{
    color: {DIDI_TEXT}; font-size: 0.86rem; font-weight: 600;
    line-height: 1.4; margin: 0 0 8px;
}}
.didi-rcard-flag {{ display: none; }}
.didi-hub-flag {{
    background: rgba(214,69,69,.10);
    border: 1px solid rgba(214,69,69,.35);
    border-radius: 8px;
    color: #9F1239;
    font-size: 0.74rem;
    font-weight: 650;
    line-height: 1.35;
    padding: 6px 8px;
    margin: 0 0 0.45rem;
}}
.didi-hub-muted {{
    color: {DIDI_MUTED}; font-size: 0.74rem; line-height: 1.35; margin: 0 0 0.35rem;
}}
.didi-alert-title {{
    font-weight: 700;
    font-size: 0.95rem;
    color: {DIDI_WHITE};
    margin: 0 0 0.45rem;
    background: {DIDI_DARK};
    border: 1px solid {DIDI_DARK};
    border-bottom: 3px solid {DIDI_ORANGE};
    border-radius: 8px;
    padding: 0.42rem 0.7rem;
    text-align: center;
}}
.didi-alert-finding {{
    color: {DIDI_TEXT};
    font-size: 0.86rem;
    line-height: 1.4;
    margin: 0 0 0.45rem;
}}
.didi-alert-meta {{
    color: {DIDI_MUTED};
    font-size: 0.80rem;
    line-height: 1.4;
    margin: 0 0 0.2rem;
}}
section.main [class*="st-key-didi_alert_red"] {{
    border-left: 4px solid #F07167 !important;
}}
section.main [class*="st-key-didi_alert_amber"] {{
    border-left: 4px solid #F2A900 !important;
}}
.didi-ops-strip {{
    display: flex; align-items: stretch; justify-content: space-between;
    gap: 10px; flex-wrap: wrap; width: 100%;
    margin: 0 0 0.85rem;
}}
.didi-ops-pill {{
    flex: 1 1 180px;
    display: flex; align-items: center; justify-content: space-between;
    gap: 10px;
    background: {DIDI_WHITE};
    border: 1px solid {DIDI_CARD_BORDER};
    border-radius: 10px;
    padding: 8px 12px;
    min-height: 44px;
}}
.didi-ops-pill strong {{
    color: {DIDI_TEXT}; font-size: 0.92rem; font-weight: 700;
}}
.didi-ops-pill span {{
    color: {DIDI_MUTED}; font-size: 0.72rem; font-weight: 600;
}}
.didi-ops-dot {{
    width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
}}
.didi-watch-group {{
    display: flex; align-items: center; gap: 8px;
    margin: 0.7rem 0 0.4rem;
    padding: 8px 12px;
    border-radius: 8px;
    background: {DIDI_GRAY};
    border: 1px solid {DIDI_CARD_BORDER};
}}
.didi-watch-group--QA {{
    background: rgba(46,155,87,.10);
    border-color: rgba(46,155,87,.22);
}}
.didi-watch-group--CSAT {{
    background: rgba(46,111,190,.10);
    border-color: rgba(46,111,190,.22);
}}
.didi-watch-group-dot {{
    width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0;
}}
.didi-watch-group-name {{
    color: {DIDI_TEXT}; font-size: 0.78rem; font-weight: 800;
    letter-spacing: .06em; text-transform: uppercase;
}}
.didi-watch-group-n {{
    color: {DIDI_MUTED}; font-size: 0.74rem; font-weight: 650;
}}
.didi-watch-sub {{
    margin: 0.15rem 0 0.35rem;
    color: {DIDI_MUTED};
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: .04em;
    text-transform: uppercase;
}}
.didi-coach {{
    display: flex; align-items: flex-start; justify-content: space-between;
    gap: 10px; margin: 0;
}}
.didi-coach-main {{ min-width: 0; flex: 1; }}
.didi-coach-name {{
    margin: 0;
    color: {DIDI_TEXT};
    font-size: 0.92rem;
    font-weight: 800;
    line-height: 1.25;
}}
.didi-coach-score {{
    margin: 0;
    color: {DIDI_TEXT};
    font-size: 1.28rem;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.02em;
    flex-shrink: 0;
    white-space: nowrap;
}}
.didi-coach-meta {{
    margin: 3px 0 0;
    color: {DIDI_MUTED};
    font-size: 0.72rem;
    font-weight: 600;
    line-height: 1.35;
}}
.didi-watch-top {{
    display: flex; align-items: flex-start; justify-content: space-between;
    gap: 10px; margin: 0 0 6px;
}}
.didi-watch-what {{
    color: {DIDI_TEXT}; font-size: 0.86rem; font-weight: 650;
    line-height: 1.4; margin: 0; white-space: normal; overflow-wrap: anywhere;
}}
.didi-watch-vol {{
    color: {DIDI_ORANGE}; font-size: 1.05rem; font-weight: 800;
    line-height: 1.2; flex-shrink: 0; white-space: nowrap;
}}
.didi-watch-who {{
    color: {DIDI_MUTED}; font-size: 0.75rem; font-weight: 500;
    margin: 0 0 8px; line-height: 1.35;
}}
.didi-watch-flags {{
    display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 8px;
}}
.didi-watch-badge {{
    display: inline-flex; align-items: center;
    border-radius: 99px; padding: 2px 8px;
    font-size: 0.64rem; font-weight: 800; letter-spacing: .06em;
    text-transform: uppercase;
}}
.didi-watch-badge--top {{
    background: rgba(214,69,69,.12); color: #9F1239;
    border: 1px solid rgba(214,69,69,.35);
}}
.didi-watch-badge--linked {{
    background: rgba(242,169,0,.14); color: #8A6200;
    border: 1px solid rgba(242,169,0,.35);
}}
.didi-watch-badge--green {{
    background: rgba(46,155,87,.12); color: #166534;
    border: 1px solid rgba(46,155,87,.35);
}}
.didi-watch-badge--amber {{
    background: rgba(242,169,0,.14); color: #8A6200;
    border: 1px solid rgba(242,169,0,.35);
}}
.didi-watch-badge--red {{
    background: rgba(214,69,69,.12); color: #9F1239;
    border: 1px solid rgba(214,69,69,.35);
}}
.didi-watch-meta {{
    display: flex; align-items: center; justify-content: space-between;
    gap: 8px; margin: 2px 0 8px;
    color: {DIDI_MUTED}; font-size: 0.72rem;
}}
.didi-vol {{
    position: relative; flex: 1; height: 8px; border-radius: 99px;
    background: {DIDI_GRAY}; overflow: hidden; min-width: 48px;
}}
.didi-vol > span {{
    display: block; height: 100%; border-radius: 99px;
    background: {STATUS_COLORS["red"]};
}}
.didi-vol--qa > span {{ background: {CHART_COLORS["qa"]}; }}
.didi-vol--csat > span {{ background: {CHART_COLORS["csat"]}; }}
.didi-vol--recontact > span {{ background: {CHART_COLORS["recontact"]}; }}
.didi-sup-head {{
    font-weight: 700; font-size: 0.86rem; color: #FFFFFF;
    margin: 0 0 0.4rem; border-radius: 8px; padding: 0.38rem 0.6rem;
    text-align: center;
}}
.didi-sup-head--red {{
    background: linear-gradient(180deg, #C23B3B 0%, #8E1F1F 100%);
    border: 1px solid rgba(255,140,140,.35);
}}
.didi-sup-head--amber {{
    background: linear-gradient(180deg, #D4A017 0%, #9A6B00 100%);
    border: 1px solid rgba(255,210,120,.35);
}}
.didi-sup-head--green, .didi-sup-head--ok {{
    background: linear-gradient(180deg, #2E9B57 0%, #1B6B3A 100%);
    border: 1px solid rgba(134,239,172,.35);
}}
.didi-sup-find {{
    color: {DIDI_TEXT}; font-size: 0.78rem; margin: 0 0 0.4rem; line-height: 1.35;
    text-align: center;
}}
.didi-agent-wrap {{
    display: flex; flex-wrap: wrap; gap: 6px; justify-content: center;
    margin: 0 0 0.45rem;
}}
.didi-agent-chip {{
    display: inline-flex; align-items: center;
    background: {DIDI_GRAY}; border: 1px solid {DIDI_CARD_BORDER};
    border-radius: 99px; padding: 3px 8px;
    color: {DIDI_TEXT}; font-size: 0.72rem; font-weight: 650;
}}
.didi-flow {{
    display: flex; align-items: center; justify-content: center;
    gap: 8px; flex-wrap: wrap; width: 100%;
    margin: 0 0 0.7rem;
}}
.didi-flow-step {{
    background: {DIDI_WHITE};
    border: 1px solid {DIDI_CARD_BORDER};
    border-radius: 10px; padding: 8px 12px;
    color: {DIDI_TEXT}; font-size: 0.78rem; font-weight: 650;
    text-align: center;
}}
.didi-flow-arrow {{
    color: {DIDI_ORANGE}; font-size: 1rem; font-weight: 800;
}}
section.main [class*="st-key-didi_watch"] {{
    height: auto !important;
    overflow: visible !important;
    margin-bottom: 0.28rem !important;
}}
section.main [class*="st-key-didi_watch"] [data-testid="stVerticalBlock"] {{
    gap: 0.12rem !important;
}}
section.main [class*="st-key-didi_watch"] [data-testid="stButton"] {{
    width: 100% !important;
}}
section.main [class*="st-key-didi_watch"] button {{
    text-align: center !important;
    justify-content: center !important;
    white-space: nowrap !important;
    min-height: 34px !important;
    padding: 6px 12px !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    color: {DIDI_WHITE} !important;
    background: {DIDI_ORANGE} !important;
    border: 1px solid {DIDI_ORANGE} !important;
    border-radius: 8px !important;
}}
section.main [class*="st-key-didi_watch"] button:hover {{
    filter: brightness(0.94);
}}
section.main [class*="st-key-didi_watch_on"] {{
    border-color: {DIDI_ORANGE} !important;
}}
section.main [class*="st-key-didi_watch_on"] button {{
    color: {DIDI_ORANGE} !important;
    background: {DIDI_WHITE} !important;
    border: 2px solid {DIDI_ORANGE} !important;
}}
section.main [class*="st-key-didi_watch_red"],
section.main [class*="st-key-didi_watch_on_red"] {{
    border-left: 4px solid {STATUS_COLORS["red"]} !important;
}}
section.main [class*="st-key-didi_watch_amber"],
section.main [class*="st-key-didi_watch_on_amber"] {{
    border-left: 4px solid {STATUS_COLORS["amber"]} !important;
}}
section.main [class*="st-key-didi_sup_"] button,
section.main [class*="st-key-didi_sup_"] [data-testid="stDownloadButton"] button {{
    min-height: 32px !important; padding: 4px 8px !important; font-size: 12px !important;
}}
section.main [class*="st-key-didi_sup_on"] {{
    border-color: {STATUS_COLORS["amber"]} !important;
    box-shadow: 0 0 0 1px {STATUS_COLORS["amber"]};
}}
section.main [class*="st-key-didi_sup_red"],
section.main [class*="st-key-didi_sup_on_red"] {{
    border-left: 4px solid {STATUS_COLORS["red"]} !important;
}}
section.main [class*="st-key-didi_sup_amber"],
section.main [class*="st-key-didi_sup_on_amber"] {{
    border-left: 4px solid {STATUS_COLORS["amber"]} !important;
}}
section.main [class*="st-key-didi_sup_green"],
section.main [class*="st-key-didi_sup_on_green"],
section.main [class*="st-key-didi_sup_ok"],
section.main [class*="st-key-didi_sup_on_ok"] {{
    border-left: 4px solid {STATUS_COLORS["green"]} !important;
}}
section.main [class*="st-key-didi_flow"] button {{
    width: 100% !important; min-height: 40px !important;
    white-space: normal !important; font-size: 0.78rem !important;
    font-weight: 650 !important;
}}
.didi-rbox {{
    text-align: left;
    background: {DIDI_GRAY};
    border: 1px solid {DIDI_CARD_BORDER};
    border-radius: 10px;
    padding: 0.7rem 0.85rem;
    margin: 0.2rem 0 0;
}}
.didi-rbox strong {{
    display: block;
    font-weight: 700;
    color: {DIDI_TEXT};
    font-size: 0.82rem;
    margin: 0 0 0.28rem;
}}
.didi-rbox p {{
    margin: 0;
    color: {DIDI_MUTED};
    font-size: 0.80rem;
    line-height: 1.35;
}}
.didi-alert-title {{
    font-weight: 700;
    font-size: 0.95rem;
    color: #FFFFFF;
    margin: 0 0 0.45rem;
    background: {DIDI_DARK};
    border: 1px solid {DIDI_DARK};
    border-bottom: 3px solid {DIDI_ORANGE};
    border-radius: 8px;
    padding: 0.42rem 0.7rem;
    text-align: center;
}}
.didi-alert-finding {{
    color: {DIDI_TEXT};
    font-size: 0.86rem;
    line-height: 1.4;
    margin: 0 0 0.45rem;
}}
.didi-alert-meta {{
    color: {DIDI_MUTED};
    font-size: 0.80rem;
    line-height: 1.4;
    margin: 0 0 0.2rem;
}}
section.main [class*="st-key-didi_alert_red"] {{
    border-left: 4px solid #F07167 !important;
}}
section.main [class*="st-key-didi_alert_amber"] {{
    border-left: 4px solid #F2A900 !important;
}}

.didi-side-brand .didi-wordmark {{
    font-size: 0.78rem; padding: 0.32rem 0.55rem; letter-spacing: .06em;
}}

div[data-testid="stPlotlyChart"] {{ margin: 0; }}
.js-plotly-plot .selectlayer,
.js-plotly-plot .zoomlayer {{
    pointer-events: none !important;
}}
/* Popup — Streamlit 1.61 is NOT Baseweb. Overlay is .stDialog[data-testid=stDialog]
   (flex, full viewport). The white panel is its first child (emotion e1mymz5c1)
   with width: theme.sizes.dialogLargeWidth = 80rem. [role=dialog] is the INNER
   wrapper (e1mymz5c2), so width rules on [role=dialog] left a ~880px chart
   left-aligned inside an 80rem panel. Size the PANEL, fill the inner column,
   and center Plotly if the SVG stays fixed-pixel. */
div[data-testid="stDialog"] > div,
section[data-testid="stDialog"] > div,
.stDialog > div,
div[data-testid="stDialog"] [class*="e1mymz5c1"],
div[data-testid="stModal"] > div,
[data-baseweb="modal"],
[data-baseweb="modal"] > div {{
    position: relative !important;
    width: min(92vw, 960px) !important;
    min-width: min(92vw, 560px) !important;
    max-width: 96vw !important;
    height: min(86vh, 760px) !important;
    min-height: 420px !important;
    max-height: 94vh !important;
    margin-left: auto !important;
    margin-right: auto !important;
    padding: 32px !important;
    box-sizing: border-box !important;
    background: {DIDI_WHITE} !important;
    border: 1px solid {DIDI_CARD_BORDER} !important;
    border-radius: 14px !important;
    overflow: auto !important;
}}
.didi-dialog-grip {{
    position: fixed !important;
    width: 28px;
    height: 28px;
    cursor: nwse-resize;
    z-index: 2147483646;
    touch-action: none;
    pointer-events: auto;
}}
.didi-dialog-grip::before,
.didi-dialog-grip::after {{
    content: "";
    position: absolute;
    right: 0;
    bottom: 0;
    border-style: solid;
    border-color: transparent;
    border-right-color: {DIDI_ORANGE};
    border-bottom-color: {DIDI_ORANGE};
}}
.didi-dialog-grip::before {{
    width: 16px; height: 16px;
    border-width: 0 3px 3px 0;
}}
.didi-dialog-grip::after {{
    width: 9px; height: 9px;
    border-width: 0 3px 3px 0;
}}
div[data-testid="stDialog"] [role="dialog"],
div[data-testid="stDialog"] [class*="e1mymz5c2"],
div[data-testid="stModal"] [role="dialog"] {{
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    box-sizing: border-box !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
}}
div[data-testid="stDialog"] [slot="title"],
div[data-testid="stDialog"] [class*="e1mymz5c4"],
div[data-testid="stModal"] [slot="title"] {{
    position: relative !important;
    display: block !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    padding: 0 2.75rem 0.85rem 2.75rem !important;
    margin: 0 !important;
    text-align: center !important;
}}
div[data-testid="stDialog"] [slot="title"] p,
div[data-testid="stDialog"] [slot="title"] [data-testid="stHeading"],
div[data-testid="stDialog"] [slot="title"] [data-testid="stMarkdownContainer"],
div[data-testid="stDialog"] [slot="title"] [data-testid="stMarkdownContainer"] p,
div[data-testid="stDialog"] [class*="e1mymz5c4"] p,
div[data-testid="stDialog"] [class*="e1mymz5c4"] [data-testid="stHeading"],
div[data-testid="stDialog"] [class*="e1mymz5c4"] [data-testid="stMarkdownContainer"],
div[data-testid="stDialog"] [class*="e1mymz5c4"] [data-testid="stMarkdownContainer"] p {{
    width: 100% !important;
    text-align: center !important;
    justify-content: center !important;
    margin: 0 !important;
}}
div[data-testid="stDialog"] button[kind="headerNoPadding"],
div[data-testid="stDialog"] button[kind="header"],
div[data-testid="stDialog"] [aria-label="Close"],
div[data-testid="stDialog"] [aria-label="Close dialog"] {{
    position: absolute !important;
    top: 18px !important;
    right: 18px !important;
    z-index: 2 !important;
}}
div[data-testid="stDialog"] [class*="e1mymz5c5"] {{
    padding: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}}
div[data-testid="stDialog"] [data-testid="stVerticalBlock"],
div[data-testid="stDialog"] [data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stDialog"] [data-testid="stElementContainer"],
div[data-testid="stDialog"] [data-testid="element-container"],
div[data-testid="stDialog"] [data-testid="stExpander"],
div[data-testid="stDialog"] [data-testid="stCaptionContainer"],
div[data-testid="stDialog"] [data-testid="stMarkdown"],
div[data-testid="stDialog"] [class*="st-key-didi_dialog_body"] {{
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    margin-left: auto !important;
    margin-right: auto !important;
}}
div[data-testid="stDialog"] [class*="st-key-didi_dialog_body"] {{
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    padding: 0 !important;
}}
div[data-testid="stDialog"] [data-testid="stPlotlyChart"] {{
    width: 100% !important;
    max-width: 100% !important;
    display: flex !important;
    justify-content: center !important;
    box-sizing: border-box !important;
}}
div[data-testid="stDialog"] [data-testid="stPlotlyChart"] > div,
div[data-testid="stDialog"] .js-plotly-plot,
div[data-testid="stDialog"] .plot-container,
div[data-testid="stDialog"] .svg-container {{
    width: 100% !important;
    max-width: 100% !important;
    margin-left: auto !important;
    margin-right: auto !important;
    box-sizing: border-box !important;
}}
div[data-testid="stDialog"] .didi-dialog-n,
div[data-testid="stDialog"] .didi-note,
div[data-testid="stDialog"] [data-testid="stExpander"] {{
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}}
div[data-testid="stDialog"] .didi-dialog-n {{
    margin: 0 0 0.35rem;
    font-size: 0.82rem;
    color: {DIDI_MUTED};
    font-weight: 600;
}}
div[data-testid="stDialog"] .didi-note {{
    font-size: 0.92rem;
    font-weight: 650;
    line-height: 1.4;
    color: {DIDI_TEXT} !important;
    background: {DIDI_GRAY} !important;
    border: none !important;
    border-left: 4px solid {DIDI_ORANGE} !important;
    border-radius: 0 8px 8px 0 !important;
    padding: 0.65rem 0.9rem !important;
    margin: 0 0 0.85rem !important;
    -webkit-line-clamp: unset;
    display: block;
    overflow: visible;
}}
div[data-testid="stDialog"] .didi-note--off {{
    border-left-color: {STATUS_COLORS["red"]} !important;
}}
div[data-testid="stDialog"] .didi-note--ok {{
    border-left-color: {STATUS_COLORS["green"]} !important;
}}
div[data-testid="stDialog"] .didi-note--info {{
    border-left-color: {STATUS_COLORS["blue"]} !important;
}}
[class*="st-key-didi_below_"] {{
    background: #FFF4EC !important;
    border: 1.5px solid {DIDI_ORANGE} !important;
    border-radius: 10px !important;
    padding: 0.35rem 0.7rem 0.15rem !important;
    margin: 0 0 0.55rem !important;
}}
[class*="st-key-didi_below_"] [data-testid="stWidgetLabel"] p,
[class*="st-key-didi_below_"] label p {{
    font-weight: 700 !important;
    color: {DIDI_DARK} !important;
}}
#didi-theme-sync {{ display: none !important; height: 0 !important; }}
div[data-testid="stHtml"]:has(#didi-theme-sync) {{
    height: 0 !important; min-height: 0 !important; margin: 0 !important;
    padding: 0 !important; overflow: hidden !important;
}}
"""
st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)
st.html(
    "<div id='didi-theme-sync'></div>"
    "<script>"
    "(function(){"
    "try{document.documentElement.style.zoom='0.8';}catch(e){}"
    "if(window.__didiDialogGrip)return;"
    "window.__didiDialogGrip=true;"
    "var MIN_W=560,MIN_H=420;"
    "var activeEl=null,grip=null;"
    "var resizePlots=function(root){"
    "if(!window.Plotly||!Plotly.Plots)return;"
    "var plots=(root&&root.querySelectorAll&&root!==document)"
    "?root.querySelectorAll('.js-plotly-plot')"
    ":document.querySelectorAll('[data-testid=\"stDialog\"] .js-plotly-plot,.stDialog .js-plotly-plot');"
    "plots.forEach(function(p){try{Plotly.Plots.resize(p);}catch(e){}});"
    "};"
    "var findPanel=function(){"
    "var dlg=document.querySelector('[data-testid=\"stDialog\"], .stDialog');"
    "if(!dlg)return null;"
    "var kids=Array.prototype.slice.call(dlg.children||[]);"
    "return kids.find(function(k){return k.offsetWidth>240&&k.offsetHeight>200;})||kids[0]||null;"
    "};"
    "var placeGrip=function(){"
    "if(!grip)return;"
    "if(!activeEl||!activeEl.isConnected){grip.style.display='none';return;}"
    "var r=activeEl.getBoundingClientRect();"
    "if(r.width<40||r.height<40){grip.style.display='none';return;}"
    "grip.style.display='block';"
    "grip.style.left=Math.round(r.right-24)+'px';"
    "grip.style.top=Math.round(r.bottom-24)+'px';"
    "};"
    "var ensureGrip=function(){"
    "if(grip)return grip;"
    "grip=document.createElement('div');"
    "grip.className='didi-dialog-grip';"
    "grip.title='Drag the orange corner to resize';"
    "grip.setAttribute('aria-label','Drag to resize');"
    "document.body.appendChild(grip);"
    "grip.addEventListener('pointerdown',function(ev){"
    "if(!activeEl)return;"
    "ev.preventDefault();ev.stopPropagation();"
    "var startX=ev.clientX,startY=ev.clientY;"
    "var startW=activeEl.offsetWidth,startH=activeEl.offsetHeight;"
    "try{grip.setPointerCapture(ev.pointerId);}catch(e){}"
    "var move=function(e){"
    "var maxW=Math.round(window.innerWidth*0.96);"
    "var maxH=Math.round(window.innerHeight*0.94);"
    "var w=Math.max(MIN_W,Math.min(maxW,startW+(e.clientX-startX)));"
    "var h=Math.max(MIN_H,Math.min(maxH,startH+(e.clientY-startY)));"
    "activeEl.style.setProperty('width',w+'px','important');"
    "activeEl.style.setProperty('height',h+'px','important');"
    "activeEl.style.setProperty('max-width','96vw','important');"
    "activeEl.style.setProperty('max-height','94vh','important');"
    "placeGrip();"
    "resizePlots(activeEl);"
    "};"
    "var up=function(){"
    "grip.removeEventListener('pointermove',move);"
    "grip.removeEventListener('pointerup',up);"
    "grip.removeEventListener('pointercancel',up);"
    "placeGrip();"
    "resizePlots(activeEl);"
    "};"
    "grip.addEventListener('pointermove',move);"
    "grip.addEventListener('pointerup',up);"
    "grip.addEventListener('pointercancel',up);"
    "});"
    "return grip;"
    "};"
    "var scan=function(){"
    "var el=findPanel();"
    "activeEl=el;"
    "if(el){ensureGrip();placeGrip();resizePlots(el);}"
    "else if(grip){grip.style.display='none';}"
    "};"
    "new MutationObserver(scan).observe(document.body,{childList:true,subtree:true});"
    "window.addEventListener('resize',function(){placeGrip();resizePlots(document);});"
    "setTimeout(scan,50);setTimeout(scan,200);setTimeout(scan,500);"
    "})();"
    "</script>",
    unsafe_allow_javascript=True,
)


@st.cache_data(show_spinner=False)
def get_data():
    """Cached once per app process — packaged snapshot is static."""
    return load_all_data()


def filter_opts(s: pd.Series) -> list[str]:
    return sorted(s.dropna().astype(str).str.strip().replace("", pd.NA).dropna().unique().tolist())


def _country_opts() -> list[str]:
    qa = filter_opts(audits_all["Country"]) if audits_all is not None and "Country" in audits_all.columns else []
    cs = (
        filter_opts(csat_all["Country Code"])
        if csat_all is not None and "Country Code" in csat_all.columns
        else []
    )
    preferred = ["MX", "CO", "CR", "PE", "DO", "PA"]
    seen = set(qa) | set(cs)
    return [c for c in preferred if c in seen] + sorted(c for c in seen if c not in preferred)


def _country_label(code: str) -> str:
    if code == "All":
        return "All"
    name = COUNTRY_NAMES.get(code, code)
    return f"{name} ({code})" if name != code else code


def apply_filters(audits, errors, csat, recontact, f, audits_all):
    a, e = audits.copy(), errors.copy()
    c, r = csat.copy(), recontact.copy()

    weeks_sel = f.get("weeks")
    if not weeks_sel:
        return a.iloc[0:0].copy(), e.iloc[0:0].copy(), c.iloc[0:0].copy(), r.iloc[0:0].copy()

    a, e = a[a["Week"].isin(weeks_sel)], e[e["Week"].isin(weeks_sel)]
    all_week_labels = audits_all["Week"].dropna().astype(str).unique().tolist() if "Week" in audits_all.columns else []
    c, r = cut_csat_recontact_for_weeks(c, r, weeks_sel, all_week_labels)

    day = f.get("day") or "All"
    if day != "All":
        a = filter_by_calendar_day(a, day)
        e = filter_by_calendar_day(e, day)
        c = filter_by_calendar_day(c, day)
        r = filter_by_calendar_day(r, day)

    if f["lob"] != "All":
        a, e = a[a["LOB"] == f["lob"]], e[e["LOB"] == f["lob"]]

    if f["channel"] != "All":
        if "Channel" in a.columns:
            a = a[channel_match(a["Channel"], f["channel"])]
        if "Channel" in e.columns:
            e = e[channel_match(e["Channel"], f["channel"])]
        if "Channel" in c.columns:
            c = c[channel_match(c["Channel"], f["channel"])]
        if "standard_channel_name" in r.columns:
            r = r[channel_match(r["standard_channel_name"], f["channel"])]
        elif "Channel" in r.columns:
            r = r[channel_match(r["Channel"], f["channel"])]

    if f["country"] != "All":
        a = a[a["Country"] == f["country"]]
        if "Country Code" in c.columns:
            c = c[c["Country Code"] == f["country"]]
        # Recontact region_name is always SSL — market is not a real cut there.

    if f.get("cr_lv1", "All") != "All":
        lookup = f.get("cr_lookup") or {}

        def _in_group(s: pd.Series) -> pd.Series:
            return map_cr_group(s, lookup) == f["cr_lv1"]

        if "CR_Lv4" in a.columns:
            a = a[_in_group(a["CR_Lv4"])]
        if "CR_Lv4" in c.columns:
            c = c[_in_group(c["CR_Lv4"])]
        if "CR_Lv4" in r.columns:
            r = r[_in_group(r["CR_Lv4"])]

    if f["cr"] != "All":
        if "CR_Lv4" in a.columns:
            a = a[cr_match(a["CR_Lv4"], f["cr"])]
        if "CR_Lv4" in e.columns:
            e = e[cr_match(e["CR_Lv4"], f["cr"])]
        if "CR_Lv4" in c.columns:
            c = c[cr_match(c["CR_Lv4"], f["cr"])]
        if "CR_Lv4" in r.columns:
            r = r[cr_match(r["CR_Lv4"], f["cr"])]

    sub_cr = f.get("sub_cr", "All")
    if sub_cr != "All":
        if "SUB_CR" in a.columns:
            a = a[cr_match(a["SUB_CR"], sub_cr)]
        if "SUB_CR" in e.columns:
            e = e[cr_match(e["SUB_CR"], sub_cr)]
        if "SUB_CR" in c.columns:
            c = c[cr_match(c["SUB_CR"], sub_cr)]
        if "SUB_CR" in r.columns and r["SUB_CR"].notna().any():
            r = r[cr_match(r["SUB_CR"], sub_cr)]

    if f.get("audit_type", "All") != "All" and "Type_of_audit" in a.columns:
        a = a[a["Type_of_audit"] == f["audit_type"]]

    if f.get("special_project", "All") != "All" and "Special_project" in a.columns:
        a = a[a["Special_project"] == f["special_project"]]

    if f.get("business_type", "All") != "All":
        bt = f["business_type"]
        cr_keys: set[str] = set()
        if "Business_Type" in c.columns:
            hit = c[c["Business_Type"] == bt]
            if "CR_Lv4" in hit.columns:
                cr_keys = set(hit["CR_Lv4"].dropna().astype(str).str.strip().str.casefold()) - {"", "nan"}
            c = hit
        if cr_keys:
            def _in_bt(s: pd.Series) -> pd.Series:
                return s.astype(str).str.strip().str.casefold().isin(cr_keys)
            if "CR_Lv4" in a.columns:
                a = a[_in_bt(a["CR_Lv4"])]
            if "CR_Lv4" in e.columns:
                e = e[_in_bt(e["CR_Lv4"])]

    if f.get("requester", "All") != "All" and "Requester" in a.columns:
        a, e = a[a["Requester"] == f["requester"]], e[e["Requester"] == f["requester"]]

    if f.get("tenure", "All") != "All" and "Tenure_Cohort" in a.columns:
        a = a[a["Tenure_Cohort"] == f["tenure"]]
        c = filter_csat_by_tenure(c, audits_all, f["tenure"])

    if f.get("supervisor", "All") != "All":
        if "Supervisor_ID" in a.columns:
            a = a[a["Supervisor_ID"] == f["supervisor"]]
        c = filter_csat_by_supervisor(c, audits_all, f["supervisor"])

    if f.get("agent", "All") != "All":
        want = str(f["agent"]).strip()
        if "Agent_ID" in a.columns:
            a = a[a["Agent_ID"].astype(str).str.strip() == want]
        c = filter_csat_by_agent(c, want)

    if "Audit_ID" in e.columns:
        e = e[e["Audit_ID"].isin(a["Audit_ID"])]

    return a, e, c, r


def _wow(delta, arrow):
    if delta is None:
        return "—", "off"
    if arrow == "▲":
        return f"{arrow} {abs(delta):.1f}%", "normal"
    if arrow == "▼":
        return f"{arrow} {abs(delta):.1f}%", "inverse"
    return f"{arrow} {abs(delta):.1f}%", "off"


def _fmt(v, digits: int = 1, suffix: str = "") -> str:
    if v is None:
        return "—"
    try:
        if pd.isna(v):
            return "—"
    except (TypeError, ValueError):
        pass
    try:
        return f"{float(v):.{digits}f}{suffix}"
    except (TypeError, ValueError):
        return "—"


def _cell_str(value, default: str = "") -> str:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    if text.casefold() in {"", "nan", "none", "<na>", "nat"}:
        return default
    return text


def _as_bool(value) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    return bool(value)


def _spark_series(daily: pd.DataFrame, col: str) -> tuple[list, list]:
    if daily.empty or col not in daily.columns:
        return [], []
    sub = daily.dropna(subset=[col]).copy()
    if sub.empty:
        return [], []
    vals = sub[col].astype(float).tolist()
    labels = pd.to_datetime(sub["Date"]).dt.strftime("%b %d").tolist() if "Date" in sub.columns else []
    return vals, labels


def _vs(v, digits: int = 1) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    arrow = "▲" if v > 0.05 else ("▼" if v < -0.05 else "→")
    return f"{arrow} {v:+.{digits}f}"


def _goal_delta(value, goal, *, lower_better: bool = False, digits: int = 1):
    """Signed gap vs goal. Streamlit arrows follow the sign; color flips when lower is better."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None, "off"
    gap = float(value) - float(goal)
    return f"{gap:+.{digits}f} vs {goal:g} goal", ("inverse" if lower_better else "normal")


def _n_delta(row, *cols: str, unit: str = "audits") -> str | None:
    if row is None:
        return None
    for col in cols:
        if col == "Gap_Impact":
            continue
        if col in row.index and pd.notna(row[col]):
            return f"{int(row[col]):,} {unit}"
    return None


def _n_supervisor_teams_under_min(audits: pd.DataFrame, min_n: int = 5) -> int:
    if audits is None or audits.empty or "Supervisor_ID" not in audits.columns:
        return 0
    return int((audits.groupby("Supervisor_ID").size() < min_n).sum())


def _supervisor_n_caption(
    n_bar: int,
    n_filter: int,
    n_teams_under_min: int,
    *,
    lowest_first: bool = False,
    min_n: int = 5,
) -> str:
    leftover = max(int(n_filter) - int(n_bar), 0)
    floor = max(int(min_n), 1)
    lead = f"Every supervisor with ≥ {floor} audit{'s' if floor != 1 else ''}"
    if lowest_first:
        lead += ", lowest QA first"
    if floor > 1:
        lead += ". The cutoff is for score reliability, not a lost sample. "
    else:
        lead += ". See all is on — small samples are included. "
    body = (
        f"N on the chart is the {int(n_bar):,} audits on these bars · "
        f"{int(n_filter):,} in this filter"
    )
    if leftover <= 0:
        return lead + body + "."
    audit_word = "audit" if leftover == 1 else "audits"
    if n_teams_under_min > 0:
        team_word = "team" if n_teams_under_min == 1 else "teams"
        extra = (
            f". {leftover:,} {audit_word} sit with "
            f"{n_teams_under_min} {team_word} under {floor} audits."
        )
    else:
        extra = f". {leftover:,} {audit_word} sit with teams under {floor} audits."
    return lead + body + extra


def _last_spc(df: pd.DataFrame):
    if df is None or df.empty or "Value" not in df.columns:
        return None
    s = df["Value"].dropna()
    return float(s.iloc[-1]) if not s.empty else None


_didi_box_n = 0


def _next_didi_key(prefix: str) -> str:
    """Stable-per-run key so Streamlit 1.61 emits class st-key-{prefix}_N for CSS fill."""
    global _didi_box_n
    _didi_box_n += 1
    return f"{prefix}_{_didi_box_n}"


def panel(title: str | None = None, subtitle: str | None = None, *, key: str | None = None):
    box = st.container(border=True, key=key or _next_didi_key("didi_panel"))
    if title:
        box.markdown(f"<p class='didi-panel-title'>{html_escape(title)}</p>", unsafe_allow_html=True)
    return box


def _fmt_kpi_pct(value, digits: int = 2) -> str:
    if value is None:
        return "—"
    try:
        if pd.isna(value):
            return "—"
    except Exception:
        return "—"
    return f"{float(value):.{digits}f}%"


def _market_box_html(
    title: str,
    rows: list[dict],
    footnote: str | None = None,
    selected: str | None = None,
) -> str:
    parts = [f'<div class="didi-mkt-box"><p class="didi-mkt-box-title">{html_escape(title)}</p>']
    if not rows:
        parts.append('<p class="didi-mkt-foot">No market in the current filter.</p></div>')
        return "".join(parts)
    for row in rows:
        code = str(row.get("code") or "")
        on = " is-on" if selected and code == selected else ""
        color = row.get("color") or STATUS_COLORS["neutral"]
        parts.append(
            f'<div class="didi-mkt-row{on}">'
            f'<span class="didi-mkt-dot" style="background:{html_escape(str(color))}"></span>'
            f'<span class="didi-mkt-name">{html_escape(str(row.get("name") or code))}</span>'
            f'<span class="didi-mkt-n">{html_escape(str(row.get("n") or ""))}</span>'
            f'<span class="didi-mkt-val">{html_escape(str(row.get("value") or "—"))}</span>'
            f"</div>"
        )
    if footnote:
        parts.append(f'<p class="didi-mkt-foot">{html_escape(footnote)}</p>')
    parts.append("</div>")
    return "".join(parts)


def render_chip(item: dict | str | None, *, tone: str = "info", icon: str = "") -> None:
    if not item:
        return
    if isinstance(item, dict):
        text = str(item.get("text") or "").strip()
        tone = item.get("tone") or tone
        icon = item.get("icon") or icon
    else:
        text = str(item).strip()
    if not text:
        return
    words = text.split()
    if len(words) > 22:
        text = " ".join(words[:22])
    cls = {"risk": "off", "ok": "ok", "info": "info"}.get(tone, "info")
    st.markdown(
        f'<div class="didi-note didi-note--{cls}">{html_escape(text)}</div>',
        unsafe_allow_html=True,
    )


def render_notes(items) -> None:
    if items is None:
        return
    if isinstance(items, (dict, str)):
        render_chip(items)
        return
    for item in items:
        if item:
            render_chip(item)
            return


def render_r_box(r, n, pair: str, *, surveys: int | None = None, audits: int | None = None) -> None:
    info = r_explain(r, n, pair, surveys=surveys, audits=audits)
    st.markdown(
        f'<div class="didi-rbox"><strong>{html_escape(info["title"])}</strong>'
        f'<p>{html_escape(info["body"])}</p></div>',
        unsafe_allow_html=True,
    )


def render_quartile_pill(q1: float, q2: float, q3: float, q4: float) -> None:
    def _pct(value) -> float:
        try:
            if value is None or pd.isna(value):
                return 0.0
            return max(0.0, float(value))
        except (TypeError, ValueError):
            return 0.0

    parts = [
        (_pct(q1), STATUS_COLORS["green"], "Q1"),
        (_pct(q2), STATUS_COLORS["blue"], "Q2"),
        (_pct(q3), STATUS_COLORS["amber"], "Q3"),
        (_pct(q4), STATUS_COLORS["red"], "Q4"),
    ]
    total = sum(p[0] for p in parts) or 1.0
    bars = "".join(
        f'<span style="width:{max(0.0, v / total * 100):.1f}%;background:{color}" title="{lab} {v:.0f}%"></span>'
        for v, color, lab in parts
    )
    legend = " ".join(
        f'<span><span class="didi-qbadge didi-qbadge--{lab}">{lab}</span> {v:.0f}%</span>'
        for v, _c, lab in parts
    )
    st.markdown(
        f'<div class="didi-qpill">{bars}</div><div class="didi-qpill-legend">{legend}</div>',
        unsafe_allow_html=True,
    )


def render_quartile_range_cards(summary: dict, *, metric: str) -> None:
    """Mini cards with the actual score bands used for Q1–Q4 in this filter."""
    bands = (summary or {}).get("bands") or {}
    roles = {
        "Q1": "Top 25% · highest scores",
        "Q2": "Next 25%",
        "Q3": "Next 25%",
        "Q4": "Bottom 25% · lowest scores",
    }
    cards = []
    for q in ("Q1", "Q2", "Q3", "Q4"):
        info = bands.get(q) or {}
        lo, hi = info.get("lo"), info.get("hi")
        if lo is None or hi is None:
            rng = "—"
        elif abs(float(hi) - float(lo)) < 0.05:
            rng = f"{float(lo):.1f}%"
        else:
            rng = f"{float(lo):.1f}–{float(hi):.1f}%"
        n = int(info.get("n") or 0)
        cards.append(
            f'<div class="didi-qrange-card didi-qrange-card--{q}">'
            f'<p class="didi-qrange-k">{q} · {html_escape(metric)}</p>'
            f'<p class="didi-qrange-v">{html_escape(rng)}</p>'
            f'<p class="didi-qrange-s">{html_escape(roles[q])} · {n} agents</p>'
            "</div>"
        )
    st.markdown(
        '<div class="didi-qrange">' + "".join(cards) + "</div>"
        '<p class="didi-qrange-s" style="margin:0 0 8px">'
        "Equal-count split of ranked agents in this filter. "
        "Q1 is the top quarter by score, Q4 the bottom quarter. "
        "The edges move when you change the filter — they are not the 85 goal."
        "</p>",
        unsafe_allow_html=True,
    )


def render_quartile_bands(summary: dict) -> None:
    bands = (summary or {}).get("bands") or {}
    cols = st.columns(4)
    for col, q in zip(cols, ("Q1", "Q2", "Q3", "Q4")):
        info = bands.get(q) or {"n": 0, "names": []}
        n = int(info.get("n") or 0)
        names = list(info.get("names") or [])
        items = "".join(f"<li>{html_escape(str(name))}</li>" for name in names)
        extra = n - len(names)
        more = f'<li class="didi-qcol-more">+{extra} more</li>' if extra > 0 else ""
        empty = "<li>—</li>" if n == 0 else ""
        with col:
            st.markdown(
                f'<div class="didi-qcol didi-qcol--{q}"><p class="didi-qcol-h">{q} · {n}</p>'
                f"<ul>{items}{more}{empty}</ul></div>",
                unsafe_allow_html=True,
            )


def _below_target_toggle(key: str, *, goal: float, metric: str) -> None:
    with st.container(key=f"didi_below_{key}"):
        st.toggle(
            f"Below {goal:g}% only",
            key=key,
            help=f"On = {metric} under the {goal:g} target. Off = every slice in this filter.",
        )


def _below_on(key: str) -> bool:
    return bool(st.session_state.get(key, False))


def _render_csat_unmapped_note(stats: dict) -> None:
    if not stats or not int(stats.get("n_surveys") or 0):
        return
    pct = float(stats.get("pct_unmapped") or 0)
    n_un = int(stats.get("n_unmapped") or 0)
    n_map = int(stats.get("n_mapped") or 0)
    st.caption(
        f"{pct:.1f}% of CSAT surveys (n={n_un:,}) could not be mapped to a QA-audited supervisor. "
        "These are excluded from supervisor-level conclusions and shown separately."
    )
    show_df(pd.DataFrame({
        "Slice": ["Mapped to a QA supervisor", "Unmapped — no matching QA agent"],
        "Surveys": [n_map, n_un],
        "% of surveys": [f"{100.0 - pct:.1f}%", f"{pct:.1f}%"],
    }))
    st.caption(
        "Possible causes: (a) new agents not yet audited in QA, "
        "(b) ID mismatch between CSAT and QA, "
        "(c) channels or shifts outside audit scope."
    )


_DIALOG_SIZE_CSS = {
    "Default": ("min(92vw, 960px)", "min(86vh, 760px)"),
    "Wide": ("min(96vw, 1400px)", "min(90vh, 900px)"),
    "Full": ("min(98vw, 1800px)", "94vh"),
}


def _dialog_size_control(state_key: str) -> None:
    """Clickable size presets — CSS resize:both cannot override Streamlit's !important panel rules."""
    choice = st.segmented_control(
        "Popup size",
        options=list(_DIALOG_SIZE_CSS),
        default="Default",
        key=f"didi_dlg_size_{state_key}",
        help="Default / Wide / Full. You can also drag the orange corner.",
        label_visibility="collapsed",
        width="stretch",
    )
    w, h = _DIALOG_SIZE_CSS.get(choice or "Default", _DIALOG_SIZE_CSS["Default"])
    st.markdown(
        f"""<style>
        div[data-testid="stDialog"] > div,
        section[data-testid="stDialog"] > div,
        .stDialog > div,
        div[data-testid="stDialog"] [class*="e1mymz5c1"] {{
            width: {w} !important;
            height: {h} !important;
            max-width: 98vw !important;
            max-height: 96vh !important;
        }}
        </style>""",
        unsafe_allow_html=True,
    )


def render_corr_scatter(
    title: str,
    fig,
    *,
    key: str,
    drill: str = "cr",
    caption: str | None = None,
    r_args: tuple | None = None,
    r_kwargs: dict | None = None,
) -> None:
    with panel(title):
        _plotly_chart(fig, key=key, drill=drill)
        if caption:
            st.caption(caption)
        elif drill:
            st.caption("Click a point to filter to that contact reason Lv4 (detail).")
        if r_args:
            render_r_box(*r_args, **(r_kwargs or {}))


def _agent_initials(name: object) -> str:
    parts = str(name or "").strip().split()
    if not parts:
        return "?"
    if len(parts) >= 2:
        return (parts[0][:1] + parts[-1][:3]).upper()
    return parts[0][:3].upper()


def _sup_tone(team_qa, n_agents: int) -> str:
    n = int(n_agents or 0)
    qa = float(team_qa) if team_qa is not None and pd.notna(team_qa) else None
    if n >= 3 or (qa is not None and qa < QA_GOAL - 5):
        return "red"
    if n >= 1 or (qa is not None and qa < QA_GOAL):
        return "amber"
    return "green"


def render_ticket_card(ticket, tickets_key: str) -> None:
    with st.container(border=True, key=_next_didi_key("didi_alert_amber")):
        st.markdown(f'<p class="didi-alert-title">{html_escape(ticket.id)} · {html_escape(ticket.title)}</p>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="didi-alert-finding">{html_escape(ticket.desk)} · Owner: {html_escape(ticket.owner)} · '
            f'Due {html_escape(ticket.due)} · {html_escape(ticket.volume)}</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p class="didi-alert-meta"><strong>Follow-up:</strong> {html_escape(ticket.follow_up)}</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p class="didi-alert-meta"><strong>Status:</strong> {html_escape(ticket.status)}</p>',
            unsafe_allow_html=True,
        )
        statuses = ["Open", "Coaching booked", "Waiting on supervisor", "Closed"]
        new_status = st.selectbox(
            "Update status",
            statuses,
            index=statuses.index(ticket.status) if ticket.status in statuses else 0,
            key=f"st_{ticket.id}_{_fn}",
            label_visibility="collapsed",
        )
        if new_status != ticket.status:
            ticket.status = new_status
        st.download_button(
            "Email draft",
            data=ticket.email_body,
            file_name=f"{ticket.id}_email.txt",
            mime="text/plain",
            key=f"em_{ticket.id}_{_fn}",
        )


def _col_kicker(text: str) -> None:
    st.markdown(f'<div class="didi-col-kicker">{html_escape(text)}</div>', unsafe_allow_html=True)


def render_kpi(label, value, delta=None, delta_color="off", help_text=None, spark=None, spark_key=None, caption=None, size="primary", traffic=None, traffic_label=True):
    prefix = "didi_tile" if size == "primary" else "didi_tile_sm"
    tone = traffic if traffic in {"green", "amber", "red"} else "neutral"
    tile_key = f"{prefix}_{tone}_{spark_key}" if spark_key else _next_didi_key(f"{prefix}_{tone}")
    with st.container(border=True, key=tile_key):
        help_mark = (
            f'<span class="didi-tile-help" title="{html_escape(help_text)}">?</span>'
            if help_text else ""
        )
        st.markdown(
            f"<p class='didi-panel-title'>{html_escape(label)}{help_mark}</p>",
            unsafe_allow_html=True,
        )
        st.metric(
            label, value, delta=delta, delta_color=delta_color,
            help=help_text, label_visibility="collapsed",
        )
        if traffic_label and tone in {"green", "amber", "red"}:
            tag = {"green": "On goal", "amber": "Within 5 points", "red": "More than 5 points off"}[tone]
            st.markdown(
                f'<p class="didi-light-tag didi-light-tag--{tone}"><span></span>{html_escape(tag)}</p>',
                unsafe_allow_html=True,
            )
        if caption:
            st.caption(caption)
        if spark is not None:
            st.plotly_chart(spark, width="stretch", config=CHART_CFG, key=spark_key)


def _fmt_qa(v) -> str:
    return "—" if v is None else f"{v:.1f}%"


def render_resolution_kpi(spark_key: str) -> None:
    """Secondary tile: auditor-judged case resolution. Not FCR, not the QA score."""
    res = auditor_resolution_summary(audits)
    caption = (
        f"{L('caption_resolution')}  \n"
        f"Official QA: resolved {_fmt_qa(res.get('qa_resolved'))} · "
        f"not resolved {_fmt_qa(res.get('qa_not_resolved'))}."
    )
    if not res["n_assessed"] or res["rate"] is None:
        render_kpi(
            L("kpi_resolution"), "—",
            "No assessed resolution in this filter",
            "off",
            help_text=L("note_resolution"),
            caption=caption,
            traffic_label=False,
            size="secondary",
            spark_key=spark_key,
        )
        return
    render_kpi(
        L("kpi_resolution"),
        f"{res['rate']:.1f}%",
        f"{res['n_resolved']:,} resolved · {res['n_not_resolved']:,} not resolved",
        "off",
        help_text=L("note_resolution"),
        caption=caption,
        spark=spark_hbar_fig(
            ["Resolved", "Not resolved"],
            [float(res["n_resolved"]), float(res["n_not_resolved"])],
        ),
        spark_key=spark_key,
        traffic_label=False,
        size="secondary",
    )


def render_abandoned_kpi(spark_key: str) -> None:
    """Secondary tile: caller abandoned the interaction. Not recontact."""
    res = auditor_resolution_summary(audits)
    caption = (
        "Auditor option: user abandoned. Excluded from resolution rate. Not recontact.  \n"
        f"Official QA: abandoned {_fmt_qa(res.get('qa_abandoned'))} · "
        f"assessed {_fmt_qa(res.get('qa_assessed'))}."
    )
    if not res["n_audits"] or res["abandon_rate"] is None:
        render_kpi(
            L("kpi_abandoned"), "—",
            "No audits in this filter",
            "off",
            help_text=L("note_abandoned"),
            caption=caption,
            traffic_label=False,
            size="secondary",
            spark_key=spark_key,
        )
        return
    render_kpi(
        L("kpi_abandoned"),
        f"{res['abandon_rate']:.1f}%",
        f"{res['n_abandoned']:,} of {res['n_audits']:,} audits had the caller abandon the interaction",
        "off",
        help_text=L("note_abandoned"),
        caption=caption,
        spark=spark_hbar_fig(
            ["Abandoned", "Assessed"],
            [float(res["n_abandoned"]), float(res["n_assessed"])],
        ),
        spark_key=spark_key,
        traffic_label=False,
        size="secondary",
    )


def render_unresolved_owner_kpi(spark_key: str) -> None:
    """Among not-resolved audits: process followed vs agent missed the process."""
    res = auditor_resolution_summary(audits)
    caption = (
        f"{L('caption_unresolved_process')}  \n"
        f"Official QA: process followed {_fmt_qa(res.get('qa_unres_process'))} · "
        f"process not followed {_fmt_qa(res.get('qa_unres_agent'))}."
    )
    if not res["n_not_resolved"] or res["pct_unres_process"] is None:
        render_kpi(
            L("kpi_unresolved_process"), "—",
            "No not-resolved audits in this filter",
            "off",
            help_text=L("note_unresolved_process"),
            caption=caption,
            traffic_label=False,
            size="secondary",
            spark_key=spark_key,
        )
        return
    render_kpi(
        L("kpi_unresolved_process"),
        f"{res['pct_unres_process']:.1f}%",
        f"{res['n_unres_process']:,} of {res['n_not_resolved']:,} not-resolved audits followed process",
        "off",
        help_text=L("note_unresolved_process"),
        caption=caption,
        spark=spark_hbar_fig(
            ["Process followed", "Process not followed"],
            [float(res["n_unres_process"]), float(res["n_unres_agent"])],
        ),
        spark_key=spark_key,
        traffic_label=False,
        size="secondary",
    )


def _fail_light(n, *, critical: bool) -> str:
    """Lower-is-better fail counts: 0 is the only green."""
    try:
        val = float(n or 0)
    except (TypeError, ValueError):
        val = 0
    if val <= 0:
        return "green"
    return "red" if critical else "amber"


def show_df(df: pd.DataFrame) -> None:
    if df is None or df.empty:
        return
    try:
        st.dataframe(_status_style(df), hide_index=True, width="stretch")
    except Exception:
        st.dataframe(df, hide_index=True, width="stretch")


def _pareto_tail_extra(
    df: pd.DataFrame,
    name_col: str,
    count_col: str,
    *,
    grain: str,
    volume_label: str,
) -> None:
    """Explain the last Pareto bar: leftover after the 80% vital few, not a cause."""
    from modules.kpis import PARETO_VITAL_PCT, pareto_named_and_tail

    if df is None or df.empty or name_col not in df.columns or count_col not in df.columns:
        return
    named, tail, vital = pareto_named_and_tail(df, count_col)
    n_all = int(len(named) + len(tail))
    if tail.empty:
        st.caption(
            f"{n_all} {grain} in this filter — the named bars already cover "
            f"{int(PARETO_VITAL_PCT):.0f}% (or everything)."
        )
        return
    n_more = int(len(tail))
    n_named = int(len(named))
    vol = float(pd.to_numeric(tail[count_col], errors="coerce").fillna(0).sum())
    tot = float(pd.to_numeric(df[count_col], errors="coerce").fillna(0).sum())
    tail_pct = (vol / tot * 100) if tot else 0.0
    if n_named >= vital:
        st.caption(
            f"Work the {n_named} named bars — they reach {int(PARETO_VITAL_PCT):.0f}% of {volume_label}. "
            f"Remaining reasons is the leftover {tail_pct:.0f}% across {n_more} other {grain} "
            f"({vol:,.0f}) — not one cause. "
            "Click a named bar to filter; the last bar does not filter."
        )
    else:
        st.caption(
            f"{int(PARETO_VITAL_PCT):.0f}% takes {vital} {grain}; the chart names {n_named} so labels stay readable. "
            f"Remaining reasons is {n_more} other {grain} totalling {vol:,.0f}. "
            "Click a named bar to filter; the last bar does not filter."
        )
    shown = tail[[name_col, count_col]].copy().rename(columns={
        name_col: grain,
        count_col: volume_label[:1].upper() + volume_label[1:],
    })
    if "CSAT_Score" in tail.columns:
        shown["CSAT %"] = tail["CSAT_Score"].values
    with st.expander(f"Leftover {min(20, n_more)} of {n_more} {grain} after the {int(PARETO_VITAL_PCT):.0f}% cut"):
        show_df(shown.head(20))


def show_fail_attr_table(df: pd.DataFrame) -> None:
    """CRITICAL vs Non-critical attribute fails — heatmap-style table."""
    if df is None or df.empty:
        st.caption("No attribute fails in this filter.")
        return
    work = df.copy()
    if "Kind" in work.columns:
        work["_k"] = work["Kind"].astype(str).map(lambda v: 0 if v == "CRITICAL" else 1)
        ascending = [True]
        cols = ["_k"]
        if "Fails" in work.columns:
            cols.append("Fails")
            ascending.append(False)
        work = work.sort_values(cols, ascending=ascending).drop(columns="_k")
    keep = [c for c in ("Kind", "Attribute", "Fails") if c in work.columns]
    if keep:
        work = work[keep]
    crit_row, non_row = "#F8D4D0", "#DCE8F6"
    crit_fg, non_fg = "#7A1610", "#1B3A63"

    def row_tint(row):
        kind = str(row.get("Kind") or "")
        if kind == "CRITICAL":
            return [f"background-color: {crit_row}; color: {crit_fg}"] * len(row)
        return [f"background-color: {non_row}; color: {non_fg}"] * len(row)

    def kind_cell(val):
        raw = str(val)
        if raw == "CRITICAL":
            return f"background-color: {STATUS_COLORS['red']}; color: #FFFFFF; font-weight: 700; text-align: center"
        return (
            f"background-color: {STATUS_COLORS['blue']}; color: #FFFFFF; "
            "font-weight: 650; text-align: center"
        )

    styler = work.style
    styler = styler.set_table_styles(
        [
            {
                "selector": "th.col_heading",
                "props": [
                    ("background-color", DIDI_DARK),
                    ("color", DIDI_WHITE),
                    ("font-weight", "700"),
                    ("border-bottom", f"2px solid {DIDI_ORANGE}"),
                ],
            },
        ],
        overwrite=False,
    )
    styler = styler.apply(row_tint, axis=1)
    if "Kind" in work.columns:
        styler = styler.map(kind_cell, subset=["Kind"])
    if "Fails" in work.columns:
        try:
            styler = styler.background_gradient(subset=["Fails"], cmap="Reds")
        except Exception:
            pass
    st.dataframe(styler, hide_index=True, width="stretch")


def channel_mix_display(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    for col in ("Contacts", "Repeats"):
        if col in out.columns:
            out[col] = out[col].map(lambda v: f"{int(v):,}" if pd.notna(v) else "—")
    if "Rate %" in out.columns:
        out["Rate %"] = out["Rate %"].map(lambda v: f"{v:.2f}" if pd.notna(v) else "—")
    for col in ("Share of contacts %", "Share of repeats %"):
        if col in out.columns:
            out[col] = out[col].map(lambda v: f"{v:.1f}" if pd.notna(v) else "—")
    if "vs 5.44" in out.columns:
        out["vs 5.44"] = out["vs 5.44"].map(lambda v: f"{v:+.2f}" if pd.notna(v) else "—")
    return out


GOOD_HEX = "#3DDC82"
BAD_HEX = "#F07167"
WARN_HEX = "#F2A900"
MUTE_HEX = "#5C6570"

_HIGHER_RATE = {
    "qa", "qa score", "csat", "csat score", "fcr", "fcr",
}
_LOWER_RATE = {
    "recontact", "rc", "rate", "rate %", "critical %",
}
_VS_HIGHER = {
    "qa vs goal", "qa vs 85", "vs 85", "csat vs 85", "csat vs goal", "vs goal", "qa wow", "csat wow",
}
_VS_LOWER = {
    "rc vs goal", "vs 5.44", "rc wow",
}


def _parse_num(value) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = str(value).replace(",", "").replace("%", "").replace("pp", "").replace("points", "")
    text = text.replace("▲", "").replace("▼", "").replace("→", "").strip()
    if not text or text == "—":
        return None
    token = text.split()[-1]
    try:
        return float(token.replace("+", ""))
    except ValueError:
        return None


def _status_style(df: pd.DataFrame):
    good, bad, warn, mute = GOOD_HEX, BAD_HEX, WARN_HEX, MUTE_HEX

    def paint(col: str, val):
        key = col.strip().lower()
        n = _parse_num(val)
        raw = str(val).strip().lower() if val is not None else ""
        if key == "priority":
            if raw in {"high", "alta"}:
                return f"color: {bad}; font-weight: 600"
            if raw in {"medium", "media"}:
                return f"color: {warn}; font-weight: 600"
            if raw in {"low", "baja"}:
                return f"color: {good}; font-weight: 600"
            return ""
        if key == "severity":
            if "critical" in raw and "non" not in raw:
                return f"color: {bad}; font-weight: 600"
            return f"color: {mute}"
        if n is None:
            return ""
        if key in _VS_HIGHER:
            if n >= 0:
                return f"color: {good}; font-weight: 600"
            if n >= -5:
                return f"color: {warn}; font-weight: 600"
            return f"color: {bad}; font-weight: 600"
        if key in _VS_LOWER:
            if n <= 0:
                return f"color: {good}; font-weight: 600"
            if n <= 5:
                return f"color: {warn}; font-weight: 600"
            return f"color: {bad}; font-weight: 600"
        if key in _HIGHER_RATE:
            if n >= 85:
                return f"color: {good}; font-weight: 600"
            if n >= 80:
                return f"color: {warn}; font-weight: 600"
            return f"color: {bad}; font-weight: 600"
        if key in _LOWER_RATE:
            goal = 5.0 if key == "critical %" else 5.44
            if n <= goal:
                return f"color: {good}; font-weight: 600"
            if n <= goal + 5:
                return f"color: {warn}; font-weight: 600"
            return f"color: {bad}; font-weight: 600"
        return ""

    styler = df.style
    styler = styler.set_table_styles(
        [
            {
                "selector": "th.col_heading",
                "props": [
                    ("background-color", DIDI_DARK),
                    ("color", DIDI_WHITE),
                    ("font-weight", "700"),
                    ("border-bottom", f"2px solid {DIDI_ORANGE}"),
                ],
            },
            {
                "selector": "th.row_heading, th.blank",
                "props": [
                    ("background-color", DIDI_DARK),
                    ("color", DIDI_WHITE),
                ],
            },
        ],
        overwrite=False,
    )
    for col in df.columns:
        styler = styler.map(lambda v, c=col: paint(c, v), subset=[col])
    return styler


with st.spinner("Loading Business Case data…"):
    try:
        data = get_data()
    except Exception as exc:
        st.error(
            "Business Case data could not be loaded. Expected the packaged snapshot "
            "in `data/packaged/` or the source workbook in `data/`.\n\n"
            f"Details: {exc}"
        )
        st.stop()

audits_all = data["fact_audits"]
errors_all = data["fact_errors"]
csat_all = data["fact_csat"]
rc_all = data["fact_recontact"]

if "fn" not in st.session_state:
    st.session_state.fn = 0
_fn = st.session_state.fn

_PENDING_SIDEBAR_FILTER = "_pending_sidebar_filter"


def _filter_widget_key(dim: str) -> str:
    keys = {
        "channel": f"flt_ch_{_fn}",
        "country": f"flt_cty_{_fn}",
        "lob": f"flt_lob_{_fn}",
        "cr_lv1": f"flt_cr1_{_fn}",
        "requester": f"flt_req_{_fn}",
        "tenure": f"flt_ten_{_fn}",
        "supervisor": f"flt_sup_{_fn}",
        "agent": f"flt_agent_{_fn}",
        "audit_type": f"flt_audt_{_fn}",
        "special_project": f"flt_sp_{_fn}",
        "business_type": f"flt_bt_{_fn}",
        "weeks": f"flt_weeks_{_fn}",
        "day": f"flt_day_{_fn}",
    }
    if dim == "cr":
        lv1 = st.session_state.get(f"flt_cr1_{_fn}", "All")
        return f"flt_cr_{_fn}_{lv1}"
    if dim == "sub_cr":
        lv1 = st.session_state.get(f"flt_cr1_{_fn}", "All")
        cr = st.session_state.get(f"flt_cr_{_fn}_{lv1}", "All")
        return f"flt_subcr_{_fn}_{lv1}_{cr}"
    return keys[dim]


def _apply_pending_sidebar_filters() -> None:
    """Replay hub/chart filter clicks before sidebar widgets mount."""
    pending = st.session_state.pop(_PENDING_SIDEBAR_FILTER, None)
    if not pending:
        return
    dim = pending["dim"]
    value = pending.get("value")
    mode = pending.get("mode", "set")
    if mode == "weeks_single":
        week_key = _filter_widget_key("weeks")
        current = [str(x) for x in (st.session_state.get(week_key) or [])]
        target = str(value)
        st.session_state[week_key] = list(weeks) if current == [target] else [target]
        return
    if mode == "cr_toggle":
        cr_all_key = f"flt_cr_{_fn}_All"
        current = str(st.session_state.get(cr_all_key) or st.session_state.get(_filter_widget_key("cr")) or "All")
        st.session_state[f"flt_cr1_{_fn}"] = "All"
        st.session_state[cr_all_key] = "All" if current == str(value) else str(value)
        st.session_state[f"flt_subcr_{_fn}_All_All"] = "All"
        return
    if mode == "sub_cr_toggle":
        sub_key = f"flt_subcr_{_fn}_All_All"
        current = str(st.session_state.get(sub_key) or st.session_state.get(_filter_widget_key("sub_cr")) or "All")
        st.session_state[f"flt_cr1_{_fn}"] = "All"
        st.session_state[f"flt_cr_{_fn}_All"] = "All"
        st.session_state[sub_key] = "All" if current == str(value) else str(value)
        return
    widget_key = _filter_widget_key(dim)
    if value is None or str(value) == "All":
        st.session_state[widget_key] = "All"
        if dim == "supervisor" or pending.get("clear_agent"):
            st.session_state[_filter_widget_key("agent")] = "All"
        return
    if mode == "toggle":
        current = str(st.session_state.get(widget_key) or "All")
        if dim == "channel":
            current = normalize_channel_label(current) if current not in (None, "All") else current
            value = normalize_channel_label(value)
        st.session_state[widget_key] = "All" if current == str(value) else str(value)
    else:
        current = st.session_state.get(widget_key, "All")
        if dim == "channel":
            current = normalize_channel_label(current) if current not in (None, "All") else current
            value = normalize_channel_label(value)
        if str(current) == str(value):
            if pending.get("clear_if_same"):
                st.session_state[widget_key] = "All"
            return
        st.session_state[widget_key] = value
    if dim == "supervisor" and str(st.session_state.get(widget_key)) != "All":
        st.session_state[_filter_widget_key("agent")] = "All"


def _copy_sidebar_filter_state(old_fn: int, new_fn: int) -> None:
    """Carry sidebar filter values when bumping fn (same pattern as Reset filters)."""
    for prefix in (
        "flt_weeks", "flt_day", "flt_ch", "flt_cty", "flt_lob", "flt_cr1",
        "flt_req", "flt_ten", "flt_sup", "flt_agent", "flt_audt", "flt_sp", "flt_bt",
    ):
        old_key = f"{prefix}_{old_fn}"
        if old_key in st.session_state:
            st.session_state[f"{prefix}_{new_fn}"] = st.session_state[old_key]
    lv1 = st.session_state.get(f"flt_cr1_{old_fn}", "All")
    old_cr = f"flt_cr_{old_fn}_{lv1}"
    if old_cr in st.session_state:
        st.session_state[f"flt_cr_{new_fn}_{lv1}"] = st.session_state[old_cr]
    cr_val = st.session_state.get(old_cr, "All")
    old_sub = f"flt_subcr_{old_fn}_{lv1}_{cr_val}"
    if old_sub in st.session_state:
        st.session_state[f"flt_subcr_{new_fn}_{lv1}_{cr_val}"] = st.session_state[old_sub]
    old_page = st.session_state.get(f"page_{old_fn}")
    if old_page is not None:
        st.session_state[f"page_{new_fn}"] = old_page
    for prefix in (
        "tickets", "hub_q4_only", "watch_pipe",
        "ov_preview", "qa_preview", "csat_preview", "rc_preview",
        "qa_agent_view", "csat_agent_view",
        "csat_sup_below85", "qa_cr_below", "qa_sub_below", "qa_agent_below",
        "qa_sup_below", "csat_lv1_below", "csat_lv4_below", "csat_sub_below",
        "csat_agent_below",
    ):
        old_key = f"{prefix}_{old_fn}"
        if old_key in st.session_state:
            st.session_state[f"{prefix}_{new_fn}"] = st.session_state[old_key]


cr_lookup = cr_group_lookup(csat_all)
cr_lv1_opts = sorted({v for v in cr_lookup.values() if v and str(v).strip()} | {CR_UNMAPPED})


def _cr_detail_opts(lv1: str) -> list[str]:
    parts = [df["CR_Lv4"] for df in (audits_all, csat_all, rc_all) if "CR_Lv4" in df.columns]
    if not parts:
        return []
    s = pd.concat(parts, ignore_index=True)
    if lv1 != "All":
        s = s[map_cr_group(s, cr_lookup) == lv1]
    return filter_opts(s)


def _sub_cr_opts(lv1: str, lv4: str) -> list[str]:
    parts = []
    for df in (audits_all, csat_all):
        if df is None or df.empty or "SUB_CR" not in df.columns:
            continue
        work = df
        if lv4 != "All" and "CR_Lv4" in work.columns:
            work = work[cr_match(work["CR_Lv4"], lv4)]
        elif lv1 != "All" and "CR_Lv4" in work.columns:
            work = work[map_cr_group(work["CR_Lv4"], cr_lookup) == lv1]
        parts.append(work["SUB_CR"])
    if not parts:
        return []
    return filter_opts(pd.concat(parts, ignore_index=True))


weeks = sorted(audits_all["Week"].dropna().astype(str).unique())
page_preview = st.session_state.get(f"page_{_fn}", "Overview")
NAV_KEYS = ["Overview", "QA Score", "CSAT", "Recontact", "Alerts"]
NAV_LABELS = {
    "Overview": L("page_overview"),
    "QA Score": L("page_qa"),
    "CSAT": L("page_csat"),
    "Recontact": L("page_recontact"),
    "Alerts": L("page_alerts"),
}
if len(weeks) >= 2:
    week_span = f"{weeks[0]}–{weeks[-1]}"
elif weeks:
    week_span = str(weeks[0])
else:
    week_span = "—"

_apply_pending_sidebar_filters()

with st.sidebar:
    st.markdown(
        '<div class="didi-side-banner">'
        '<span class="didi-wordmark">DiDi</span>'
        '<div class="didi-side-banner-title">CX Quality Dashboard</div>'
        f'<p class="didi-side-banner-sub">{html_escape(NAV_LABELS.get(str(page_preview), str(page_preview)))} · {html_escape(week_span)}</p>'
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="didi-side-pages-head"><p class="didi-side-kicker">Pages</p></div>',
        unsafe_allow_html=True,
    )
    with st.container(key="didi_nav"):
        page = st.radio(
            "Pages",
            NAV_KEYS,
            format_func=lambda p: NAV_LABELS.get(p, p),
            label_visibility="collapsed",
            key=f"page_{_fn}",
        )
    present = set(audits_all["Tenure_Cohort"].dropna().astype(str)) if "Tenure_Cohort" in audits_all.columns else set()
    tenure_opts = [t for t in TENURE_SOURCE_ORDER if t in present]
    extra = sorted(x for x in present if x not in set(tenure_opts) and x != "Unknown")
    tenure_opts = tenure_opts + extra + (["Unknown"] if "Unknown" in present else [])
    with st.container(border=True, key="flt_period"):
        with st.expander("Period & channel", expanded=True):
            sel_weeks = st.multiselect(
                "Week",
                weeks,
                default=weeks,
                key=f"flt_weeks_{_fn}",
                help="ISO week. All weeks on = official May snapshot. CSAT and recontact use their own calendar, not QA audit weekdays.",
            )
            day_opts = calendar_days_in_scope(audits_all, csat_all, rc_all, sel_weeks, weeks) if sel_weeks else []
            sel_day = st.selectbox(
                "Day",
                ["All"] + day_opts,
                format_func=lambda v: "All days" if v == "All" else pd.Timestamp(v).strftime("%b %d"),
                key=f"flt_day_{_fn}",
                help="Cuts QA, CSAT and recontact to this calendar date on each source’s own Fecha. Leave All days for the week selection only.",
            )
            sel_channel = st.selectbox(
                "Channel",
                ["All"] + filter_opts(audits_all["Channel"]),
                key=f"flt_ch_{_fn}",
                help="Phone and Live Chat — the QA/CSAT channels. Recontact’s 12-channel mix is the table on the Recontact page.",
            )
    with st.container(border=True, key="flt_filters"):
        with st.expander("Filters", expanded=False):
            sel_country = st.selectbox(
                "Market / Country",
                ["All"] + _country_opts(),
                format_func=_country_label,
                key=f"flt_cty_{_fn}",
                help="Cuts QA and CSAT. Recontact has no market (region is always SSL).",
            )
            sel_lob = st.selectbox("LOB", ["All"] + filter_opts(audits_all["LOB"]), key=f"flt_lob_{_fn}")
            sel_cr_lv1 = st.selectbox(
                L("filter_cr_lv1"),
                ["All"] + cr_lv1_opts,
                key=f"flt_cr1_{_fn}",
                help="Contact reason Lv1 (group) comes from the CSAT hierarchy. QA and Recontact inherit it via the contact reason Lv4 (detail) name.",
            )
            sel_cr = st.selectbox(
                L("filter_cr"),
                ["All"] + _cr_detail_opts(sel_cr_lv1),
                key=f"flt_cr_{_fn}_{sel_cr_lv1}",
                help="Contact reason Lv4 (detail) is the most specific reason name on the hierarchy above SUB_CR.",
            )
            sel_sub_cr = st.selectbox(
                L("filter_sub_cr"),
                ["All"] + _sub_cr_opts(sel_cr_lv1, sel_cr),
                key=f"flt_subcr_{_fn}_{sel_cr_lv1}_{sel_cr}",
                help="Finest contact reason. Cuts QA and CSAT. Recontact has no native SUB_CR, so this filter does not change the recontact KPI.",
            )
            sel_requester = st.selectbox(
                "Requester Type", ["All"] + filter_opts(audits_all["Requester"]), key=f"flt_req_{_fn}",
            )
            sel_tenure = st.selectbox(
                "Agent tenure (QA only)",
                ["All"] + tenure_opts,
                key=f"flt_ten_{_fn}",
                help="Cuts QA by the Excel Tenure field. CSAT is cut to agents with that QA tenure (name match). Recontact has no tenure.",
            )
            sel_supervisor = st.selectbox(
                "Supervisor",
                ["All"] + filter_opts(audits_all["Supervisor_ID"])[:80],
                key=f"flt_sup_{_fn}",
                help="Cuts QA by Supervisor_ID. Cuts CSAT to that supervisor’s agents (CSAT agent name matched to QA). Recontact has no supervisor.",
            )
            agent_pre = dict(
                weeks=sel_weeks, day=sel_day, channel=sel_channel, lob=sel_lob,
                cr=sel_cr, cr_lv1=sel_cr_lv1, sub_cr=sel_sub_cr, requester=sel_requester,
                country=sel_country, tenure=sel_tenure, supervisor=sel_supervisor,
                audit_type="All", special_project="All", business_type="All",
                agent="All", cr_lookup=cr_lookup,
            )
            agent_src, _, _, _ = apply_filters(
                audits_all, errors_all, csat_all, rc_all, agent_pre, audits_all,
            )
            agent_opts = (
                ["All"] + filter_opts(agent_src["Agent_ID"])
                if agent_src is not None and not agent_src.empty and "Agent_ID" in agent_src.columns
                else ["All"]
            )
            sel_agent = st.selectbox(
                "Agent",
                agent_opts,
                key=f"flt_agent_{_fn}",
                help="Cuts QA by Agent_ID. Cuts CSAT to surveys whose agent name matches that QA Agent_ID. Recontact has no agent field.",
            )
            st.caption("Click a bar or point on an open chart to set that filter. Reset filters clears it.")
    with st.container(border=True, key="flt_qa"):
        with st.expander("QA filters", expanded=False):
            audit_opts = filter_opts(audits_all["Type_of_audit"]) if "Type_of_audit" in audits_all.columns else []
            sel_audit_type = st.selectbox(
                "Type of audit", ["All"] + audit_opts, key=f"flt_audt_{_fn}",
                help="Cuts QA audits only.",
            )
            special_opts = filter_opts(audits_all["Special_project"]) if "Special_project" in audits_all.columns else []
            sel_special = st.selectbox(
                "Special project", ["All"] + special_opts, key=f"flt_sp_{_fn}",
                help="Cuts QA audits only.",
            )
    with st.container(border=True, key="flt_csat"):
        with st.expander("CSAT filters", expanded=False):
            bt_opts = filter_opts(csat_all["Business_Type"]) if "Business_Type" in csat_all.columns else []
            sel_business = st.selectbox(
                "Business type", ["All"] + bt_opts, key=f"flt_bt_{_fn}",
                help="Cuts CSAT natively. QA is cut to contact reason Lv4 names that carry this Business Type in CSAT. Recontact is not cut.",
            )

    if st.button("Reset filters", type="primary", key=f"reset_{_fn}", width="stretch"):
        st.session_state.fn += 1
        st.rerun()
    st.toggle(
        "Edit labels",
        key="edit_labels",
        help="Change titles, notes, and theme colors. Click Save to keep them after refresh.",
    )

if st.session_state.get("_last_nav_page") != page:
    for k in list(st.session_state.keys()):
        if isinstance(k, str) and "_preview_" in k:
            st.session_state[k] = None
    st.session_state["_last_nav_page"] = page

if not sel_weeks:
    st.warning("Select at least one week in the sidebar.")
    st.stop()

filters = dict(
    weeks=sel_weeks, day=sel_day, channel=sel_channel, lob=sel_lob, cr=sel_cr, cr_lv1=sel_cr_lv1,
    sub_cr=sel_sub_cr, requester=sel_requester, country=sel_country,
    tenure=sel_tenure, supervisor=sel_supervisor, agent=sel_agent,
    audit_type=sel_audit_type, special_project=sel_special, business_type=sel_business,
    cr_lookup=cr_lookup,
)

audits, errors, csat, recontact = apply_filters(
    audits_all, errors_all, csat_all, rc_all, filters, audits_all,
)
scope_filters = {**filters, "channel": "All"}
_, _, _, rc_scope_src = apply_filters(audits_all, errors_all, csat_all, rc_all, scope_filters, audits_all)

# Score-by-slice charts default to every row (n ≥ 1). Each chart has its own below-target toggle.
_qa_cr_below_k = f"qa_cr_below_{_fn}"
_qa_sub_below_k = f"qa_sub_below_{_fn}"
_qa_agent_below_k = f"qa_agent_below_{_fn}"
_qa_sup_below_k = f"qa_sup_below_{_fn}"
_csat_lv1_below_k = f"csat_lv1_below_{_fn}"
_csat_lv4_below_k = f"csat_lv4_below_{_fn}"
_csat_sub_below_k = f"csat_sub_below_{_fn}"
_csat_agent_below_k = f"csat_agent_below_{_fn}"
_csat_sup_below_k = f"csat_sup_below85_{_fn}"

summary = kpi_summary(audits, csat, recontact)
trends = weekly_trends(audits)
daily = daily_metrics_trend(audits, csat, recontact)
volumes = volume_totals(audits, csat, recontact)
vol_delta = period_volume_delta(audits, csat, recontact, sel_weeks)
rc_rate = recontact_rate(recontact) if not recontact.empty else 0.0
vol_series = daily_volume_series(audits, csat, recontact)
disp = qa_channel_dispersion(audits)
rc_scope = recontact_by_scope(rc_scope_src)
dilution = recontact_dilution_stats(rc_scope_src)
score_method = scoring_method_stats(audits_all)
crit = critical_fail_stats(audits, errors)

ch_perf = channel_performance(audits, csat, recontact)
tenure_qa = qa_by_tenure(audits)
qa_special = qa_by_special_project(audits)
qa_audit_type = qa_by_audit_type(audits)
qa_aht = qa_aht_by_channel(audits)
aht_points = qa_aht_by_cr(audits)
aht_cr_lv1 = qa_aht_by_cr(audits, cat_col="CR_Lv1", lookup=cr_lookup, by_channel=False)
aht_cr_lv4 = qa_aht_by_cr(audits, cat_col="CR_Lv4", by_channel=False)
aht_cr_sub = qa_aht_by_cr(audits, cat_col="SUB_CR", by_channel=False)
aht_joined = aht_joined_outcomes(audits, csat, recontact)
aht_corr = aht_correlation_summary(aht_joined)
csat_unsat = csat_unsatisfied_by_cr(csat)
csat_unsat_sub = csat_unsatisfied_by_cr(csat, cat_col="SUB_CR")
csat_scr_lv1 = csat_score_by_cr(
    csat, level="lv1", lookup=cr_lookup, min_n=1, top_n=None,
    below_goal_only=_below_on(_csat_lv1_below_k),
)
csat_scr_lv4 = csat_score_by_cr(
    csat, level="lv4", min_n=1, top_n=None,
    below_goal_only=_below_on(_csat_lv4_below_k),
)
csat_scr_sub = csat_score_by_cr(
    csat, level="sub", min_n=1, top_n=None,
    below_goal_only=_below_on(_csat_sub_below_k),
)
csat_scr_sup = csat_by_supervisor(
    csat, audits, min_n=1, top_n=None,
    below_goal_only=_below_on(_csat_sup_below_k),
)
rc_vol_lv1 = contact_volume_by_cr(recontact, level="lv1", lookup=cr_lookup, top_n=8)
rc_vol_lv4 = contact_volume_by_cr(recontact, level="lv4", top_n=8)
csat_bt = csat_by_business_type(csat)
agents = agent_scores(audits)
csat_ten = csat_by_user_tenure(csat)
slices = kpi_by_channel(audits, csat, recontact)
coverage = slice_coverage_table()
req_perf = requester_performance(audits, csat, recontact)
ov_sup = supervisor_overview(audits, csat, min_n=1)
ov_ten_qa = tenure_qa_overview(audits)
ov_ten_csat = tenure_csat_overview(audits, csat)
ov_agents_gap = agents_below_qa_goal(
    audits, min_n=1, below_goal_only=False,
)
rank_filters = {**filters, "supervisor": "All", "agent": "All"}
if sel_supervisor == "All" and sel_agent == "All":
    audits_rank, csat_rank = audits, csat
else:
    audits_rank, _, csat_rank, _ = apply_filters(
        audits_all, errors_all, csat_all, rc_all, rank_filters, audits_all,
    )
qa_q_agents = qa_agent_quartiles(audits_rank, min_n=RANKING_QA_MIN_N)
csat_q_agents = csat_agent_quartiles(csat_rank, audits_rank, min_n=RANKING_CSAT_MIN_N)
_sup_kpis = ov_sup if sel_supervisor == "All" else supervisor_overview(audits_rank, csat_rank)
qa_mix = supervisor_quartile_mix(qa_q_agents, _sup_kpis)
csat_mix = supervisor_quartile_mix(csat_q_agents, _sup_kpis)
qa_q_sum = quartile_band_summary(qa_q_agents)
csat_q_sum = quartile_band_summary(csat_q_agents)
sup_qa_gap = gap_pareto_frame(ov_sup, "Supervisor_ID", "QA_Score", "n", QA_GOAL)
sup_csat_gap = gap_pareto_frame(ov_sup, "Supervisor_ID", "CSAT_Score", "Feedback", CSAT_GOAL)
ten_qa_gap = gap_pareto_frame(ov_ten_qa, "Tenure_Cohort", "QA_Score", "n", QA_GOAL)
ten_csat_gap = gap_pareto_frame(ov_ten_csat, "Tenure_Cohort", "CSAT_Score", "Feedback", CSAT_GOAL)
combined = combined_operational_analysis(audits, csat, recontact)
ch_qa = qa_channel_breakdown(audits, errors)
top_attr = top_failing_attributes(errors, audits, top_n=12)
crit_errors = (
    errors[errors["Is_Critical"].astype(bool)]
    if not errors.empty and "Is_Critical" in errors.columns
    else pd.DataFrame()
)
crit_attr = (
    top_failing_attributes(crit_errors, audits, top_n=10)
    if not crit_errors.empty else pd.DataFrame()
)
qa_cr = qa_score_by_cr(
    audits, top_n=None, min_n=1, below_goal_only=_below_on(_qa_cr_below_k),
)
qa_sub = qa_score_by_cr(
    audits, top_n=None, min_n=1, cat_col="SUB_CR", below_goal_only=_below_on(_qa_sub_below_k),
)
rc_cr = recontact_by_cr(recontact, top_n=12)
rc_sub = recontact_by_cr(recontact, top_n=12, cat_col="SUB_CR", csat=csat)
rc_ch_vol = recontact_by_std_channel(recontact)
if not rc_ch_vol.empty:
    rc_ch_vol = rc_ch_vol.copy()
    rc_ch_vol["Cat"] = rc_ch_vol["Cat"].map(normalize_channel_label)
rc_ch_tbl = recontact_channel_table(recontact)
qa_cr_fails = qa_fails_by_cr(errors)
qa_sub_fails = qa_fails_by_cr(errors, cat_col="SUB_CR")
qa_cr_groups = qa_fails_by_cr_group(errors, cr_lookup)
rc_cr_groups = recontact_by_cr_group(recontact, cr_lookup)
qa_cr_pair = attach_cr_group(qa_cr_fails, cr_lookup)
rc_cr_pair = attach_cr_group(rc_cr, cr_lookup)
stars = csat_by_star_rating(csat)
_STAR_HI = ("5 Stars", "4 Stars")
_STAR_LO = ("3 Stars", "2 Stars", "1 Star")
_stars_hi = stars[stars["Rating"].astype(str).isin(_STAR_HI)].copy() if not stars.empty else stars
_stars_lo = stars[stars["Rating"].astype(str).isin(_STAR_LO)].copy() if not stars.empty else stars
_star_hi = int(pd.to_numeric(_stars_hi["Count"], errors="coerce").fillna(0).sum()) if not _stars_hi.empty else 0
_star_lo = int(pd.to_numeric(_stars_lo["Count"], errors="coerce").fillna(0).sum()) if not _stars_lo.empty else 0
_star_n = int(pd.to_numeric(stars["Count"], errors="coerce").fillna(0).sum()) if not stars.empty else 0
voc = voc_themes_negative(csat)
comments = voc_all_comments(csat)
csat_seg = csat_segmentation(csat, top_n=None, min_n=1)
scatter_df = cr_level_metrics(audits, csat, recontact)
lv1_metrics = cr_group_metrics(audits, csat, recontact, cr_lookup)
weekly = weekly_kpi_table(audits, csat, recontact)
qa_spc = qa_control_daily(audits)
csat_spc = csat_control_daily(csat)
rc_spc = recontact_control_daily(recontact)
hist_qa = qa_score_histogram(audits)
hist_csat = csat_score_histogram(csat)
corr_tbl = cr_correlation_summary(scatter_df)
corr_cov = cr_join_coverage(audits, csat, recontact)
actions = generate_action_plan(combined, ch_perf, top_attr, rc_cr, summary, rc_rate, channel=sel_channel)
brief = build_executive_brief(
    summary, rc_rate, audits, errors, csat, recontact,
    combined, ch_perf, top_attr, rc_cr, voc, actions,
    channel=sel_channel,
)

start_d, end_d = analysis_date_span(
    [audits_all, csat_all, rc_all], sel_weeks, weeks,
)
if sel_day != "All":
    day_ts = pd.Timestamp(sel_day)
    start_d, end_d = day_ts, day_ts
    date_label = day_ts.strftime("%b %d, %Y")
elif not audits.empty or not csat.empty or not recontact.empty:
    date_label = f"{start_d.strftime('%b %d')} – {end_d.strftime('%b %d, %Y')}"
else:
    date_label = "—"
n_weeks = len(sel_weeks) if sel_weeks else 0
week_phrase = (
    "1-Day Analysis" if sel_day != "All"
    else (f"{n_weeks} Week Analysis" if n_weeks != 1 else "1 Week Analysis")
)


def _active_filters_label(f: dict) -> str:
    skip = {"cr_lookup"}
    names = {
        "weeks": "Weeks",
        "day": "Day",
        "channel": "Channel",
        "lob": "LOB",
        "cr": L("filter_cr"),
        "cr_lv1": L("filter_cr_lv1"),
        "sub_cr": L("filter_sub_cr"),
        "requester": "Requester",
        "country": "Market",
        "tenure": "Tenure",
        "supervisor": "Supervisor",
        "agent": "Agent",
        "audit_type": "Type of audit",
        "special_project": "Special project",
        "business_type": "Business type",
    }
    parts: list[str] = []
    all_weeks = set(audits_all["Week"].dropna().astype(str).unique()) if "Week" in audits_all.columns else set()
    for k, v in f.items():
        if k in skip or isinstance(v, dict):
            continue
        if k == "weeks":
            selected = [str(x) for x in (v or [])]
            if not selected or set(selected) == all_weeks:
                continue
            parts.append(f"{names[k]}: {', '.join(selected)}")
            continue
        if v in ("All", [], None, "") or v is False:
            continue
        if isinstance(v, list):
            parts.append(f"{names.get(k, k)}: {', '.join(str(x) for x in v)}")
        else:
            parts.append(f"{names.get(k, k)}: {v}")
    return ", ".join(parts) or "All data"


active_label = _active_filters_label(filters)
slice_lead = (
    "On the selected period:"
    if active_label == "All data"
    else f"On this slice ({active_label}):"
)

qa_vs = f"{summary['qa_score'] - QA_GOAL:+.2f} points vs goal"
cs_vs = f"{summary['csat'] - CSAT_GOAL:+.2f} points vs goal"
rc_vs = f"{rc_rate - RECONTACT_GOAL:+.2f} points vs goal"
qa_day = _last_spc(qa_spc)
csat_day = _last_spc(csat_spc)
rc_day = _last_spc(rc_spc)
qa_day_delta, qa_day_color = _goal_delta(qa_day, QA_GOAL, digits=1)
csat_day_delta, csat_day_color = _goal_delta(csat_day, CSAT_GOAL, digits=1)
rc_day_delta, rc_day_color = _goal_delta(rc_day, RECONTACT_GOAL, lower_better=True, digits=2)
qa_light = _vs_goal_status(summary["qa_score"], QA_GOAL, True)
cs_light = _vs_goal_status(summary["csat"], CSAT_GOAL, True)
rc_light = _vs_goal_status(rc_rate, RECONTACT_GOAL, False)
fcr_rate = 100.0 - rc_rate
fcr_vs = "No business-case target"
_aud = rc_scope[rc_scope["Scope_Key"] == "audited"] if not rc_scope.empty and "Scope_Key" in rc_scope.columns else pd.DataFrame()
fcr_audited = (100.0 - float(_aud.iloc[0]["Rate"])) if not _aud.empty and pd.notna(_aud.iloc[0].get("Rate")) else None
sh_share = dilution.get("share") if isinstance(dilution, dict) else None
rc_repeats = int(recontact["Recontact Volume"].sum()) if not recontact.empty and "Recontact Volume" in recontact.columns else None

qa_spark_vals, qa_spark_lbl = _spark_series(daily, "QA_Score")
if not qa_spark_vals and not trends.empty:
    qa_spark_vals, qa_spark_lbl = trends["QA_Score"].tolist(), trends.get("Week", pd.Series(dtype=str)).astype(str).tolist()
csat_spark_vals, csat_spark_lbl = _spark_series(daily, "CSAT_Score")
rc_spark_vals, rc_spark_lbl = _spark_series(daily, "Recontact_Rate")
fcr_spark_vals = [None if v is None or pd.isna(v) else 100 - float(v) for v in (rc_spark_vals or [])]
c_txt, c_dcol = _wow(vol_delta.get("contacts_delta"), vol_delta.get("contacts_arrow", "→"))
r_txt, r_dcol = _wow(vol_delta.get("recontacts_delta"), vol_delta.get("recontacts_arrow", "→"))
s_txt, s_dcol = _wow(vol_delta.get("surveys_delta"), vol_delta.get("surveys_arrow", "→"))
e_txt, e_dcol = _wow(vol_delta.get("evals_delta"), vol_delta.get("evals_arrow", "→"))
qa_disp = disp["alert"] if disp["alert"] else None


def qa_story_text() -> str:
    override = L("qa_story").strip()
    if override:
        return override
    score = summary["qa_score"]
    gap = score - QA_GOAL
    if gap >= 0:
        status = f"QA score is {score:.1f}%, {gap:+.1f} points vs the 85 goal."
    else:
        status = f"QA score is {score:.1f}%, {abs(gap):.1f} points below the 85 goal."
    move = ""
    if not weekly.empty and "QA_WoW_pp" in weekly.columns:
        last = weekly.dropna(subset=["QA_Score"]).tail(1)
        if not last.empty and pd.notna(last.iloc[0].get("QA_WoW_pp")):
            w = float(last.iloc[0]["QA_WoW_pp"])
            move = f" Last week vs the week before: {w:+.1f} points."
    where = ""
    if not top_attr.empty:
        row = top_attr.iloc[0]
        where = (
            f" Defects concentrate in '{row['Error_Category']}' "
            f"({row['Pct_Of_Fails']:.1f}% of attribute fails)."
        )
    return f"{slice_lead} {status}{move}{where}".strip()


def pair_display(df: pd.DataFrame, count_col: str, count_label: str, extra: dict | None = None) -> pd.DataFrame:
    if df.empty:
        return df
    out = {
        L("col_cr_detail"): df["CR_Lv4"].astype(str),
        L("col_cr_group"): df["CR_Lv1"].astype(str) if "CR_Lv1" in df.columns else "—",
        count_label: df[count_col].map(lambda v: f"{int(v):,}" if pd.notna(v) else "—"),
    }
    if "Pct" in df.columns:
        out["Share"] = df["Pct"].map(lambda v: f"{v:.1f}%")
    if extra:
        out.update(extra)
    return pd.DataFrame(out)

PAGE_TITLES = {
    "Overview": L("page_overview"),
    "QA Score": L("page_qa"),
    "CSAT": L("page_csat"),
    "Recontact": L("page_recontact"),
    "Alerts": L("page_alerts"),
}

if st.session_state.get("edit_labels"):
    with st.sidebar:
        st.divider()
        st.caption("EDIT LABELS — Save to keep after refresh")
        if st.session_state.pop("_ui_saved", False):
            st.success("Saved. Titles and colors stay after you refresh the page.")
        for group, keys in LABEL_GROUPS.items():
            with st.expander(group, expanded=False):
                for key in keys:
                    st.text_input(key.replace("_", " "), key=f"lbl_{key}")
        st.text_area("Overview insight (blank = generated)", key="lbl_overview_insight")
        st.text_area("Overview action (blank = generated)", key="lbl_overview_action")
        st.text_area("Overview hypothesis (blank = generated)", key="lbl_overview_hypothesis")
        with st.expander("Theme colors", expanded=False):
            for key, caption in THEME_PICKERS:
                pk = f"pick_{key}"
                if pk not in st.session_state or _is_broken_theme(st.session_state.get(pk)):
                    current = st.session_state.get(f"theme_{key}", THEME_DEFAULTS[key])
                    st.session_state[pk] = (
                        THEME_DEFAULTS[key] if _is_broken_theme(current) else current
                    )
                chosen = st.color_picker(caption, key=pk)
                if not _is_broken_theme(chosen):
                    st.session_state[f"theme_{key}"] = chosen
        st.caption("Titles, notes, and colors persist. Chart size and position cannot be dragged (Streamlit is not Power BI).")
        save_col, reset_col = st.columns(2)
        with save_col:
            if st.button("Save", type="primary", width="stretch"):
                labels = {
                    key: str(st.session_state.get(f"lbl_{key}", LABELS[key]))
                    for key in LABELS
                }
                theme = {
                    key: (
                        THEME_DEFAULTS[key]
                        if _is_broken_theme(st.session_state.get(f"theme_{key}"))
                        else str(st.session_state.get(f"theme_{key}", THEME_DEFAULTS[key]))
                    )
                    for key in THEME_DEFAULTS
                }
                save_ui_overrides(labels, theme)
                st.session_state["_ui_saved"] = True
                st.rerun()
        with reset_col:
            if st.button("Reset to defaults", width="stretch"):
                clear_ui_overrides()
                for key in list(st.session_state.keys()):
                    if key.startswith("lbl_") or key.startswith("theme_") or key.startswith("pick_"):
                        del st.session_state[key]
                st.rerun()


def _traffic(value, goal: float, lower_better: bool = False) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "neutral"
    status = _vs_goal_status(value, goal, higher_is_better=not lower_better)
    return {"green": "ok", "amber": "warn", "red": "off"}.get(status, "neutral")


def _svg_icon(name: str) -> str:
    paths = {
        "calendar": (
            '<rect x="3" y="5" width="18" height="16" rx="2"/>'
            '<path d="M8 3v4M16 3v4M3 11h18"/>'
        ),
        "clock": (
            '<circle cx="12" cy="12" r="9"/>'
            '<path d="M12 7v6l4 2"/>'
        ),
        "trend": '<path d="M4 16l5-5 4 4 7-8M15 7h5v5"/>',
        "frown": (
            '<circle cx="12" cy="12" r="9"/>'
            '<path d="M8 10h.01M16 10h.01M8 16c1.2-1.3 2.6-2 4-2s2.8.7 4 2"/>'
        ),
        "users": (
            '<path d="M16 19v-1.5a3.5 3.5 0 0 0-3.5-3.5h-5A3.5 3.5 0 0 0 4 17.5V19"/>'
            '<circle cx="9.5" cy="7.5" r="3"/>'
            '<path d="M20 19v-1.2a3 3 0 0 0-2.2-2.9"/>'
            '<circle cx="16.5" cy="8" r="2.2"/>'
        ),
    }
    return (
        f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        f'{paths[name]}</svg>'
    )


def _target_item(label: str, icon: str) -> str:
    return (
        f'<div class="didi-tgt">'
        f'<span class="didi-tgt-ico">{_svg_icon(icon)}</span>'
        f"<span>{html_escape(label)}</span></div>"
    )


def _light_legend_html() -> str:
    return (
        '<div class="didi-targets-legend">'
        f'<span class="didi-light-item"><span class="didi-light-dot" style="background:{STATUS_COLORS["green"]}"></span>On goal</span>'
        f'<span class="didi-light-item"><span class="didi-light-dot" style="background:{STATUS_COLORS["amber"]}"></span>Within 5 points</span>'
        f'<span class="didi-light-item"><span class="didi-light-dot" style="background:{STATUS_COLORS["red"]}"></span>More than 5 points off</span>'
        "</div>"
    )


def render_header(title: str) -> None:
    as_of = end_d.strftime("%b %d, %Y") if not audits.empty else "—"
    n = n_weeks if n_weeks else 0
    week_txt = f"{n}-Week Performance Analysis" if n != 1 else "1-Week Performance Analysis"
    top = (
        '<div class="didi-head-top">'
        '<div class="didi-head-titlebox">'
        '<span class="didi-wordmark">DiDi</span>'
        '<div class="didi-head-title">CX Quality Dashboard</div>'
        '<p class="didi-head-sub">Customer Experience Quality · Service Operations</p>'
        '</div>'
        '<div class="didi-head-right">'
        f'<div class="didi-head-updated">{_svg_icon("clock")}'
        f"<span>Last updated: {html_escape(as_of)}</span></div>"
        '<div class="didi-targets-box">'
        '<div class="didi-targets-kicker">Targets</div>'
        '<div class="didi-targets">'
        + _target_item(f"QA Score ≥ {QA_GOAL:g}%", "trend")
        + _target_item(f"CSAT ≥ {CSAT_GOAL:g}%", "frown")
        + _target_item(f"Recontact ≤ {RECONTACT_GOAL:g}%", "users")
        + "</div>"
        + _light_legend_html()
        + "</div></div></div>"
        f'<div class="didi-head-meta"><div class="didi-page">{html_escape(title)}</div>'
        f'{_svg_icon("calendar")}<span>{html_escape(date_label)}</span>'
        '<span class="didi-head-meta-split"></span>'
        f"<span>{html_escape(week_txt)}</span></div>"
    )
    with st.container(key=_next_didi_key("didi_head")):
        st.markdown(top, unsafe_allow_html=True)


def render_banner(title: str) -> None:
    st.markdown(
        f'<div class="didi-kpi-banner-wrap"><div class="didi-kpi-banner">{html_escape(title)}</div></div>',
        unsafe_allow_html=True,
    )


def render_rule_heading(title: str) -> None:
    st.markdown(
        f'<div class="didi-rule-h"><span>{html_escape(title)}</span></div>',
        unsafe_allow_html=True,
    )


def render_section(kicker: str, title: str, hint: str | None = None) -> None:
    render_banner(title)


def drill(title: str, *, expanded: bool = False):
    return st.expander(title, expanded=expanded)


def _filter_allowed(dim: str) -> set[str] | None:
    if dim == "channel":
        return set(filter_opts(audits_all["Channel"]))
    if dim == "supervisor":
        return set(filter_opts(audits_all["Supervisor_ID"]))
    if dim == "agent":
        return {str(x) for x in agent_opts if str(x) != "All"}
    if dim == "cr_lv1":
        return set(cr_lv1_opts)
    if dim == "cr":
        return set(_cr_detail_opts("All"))
    if dim == "sub_cr":
        return set(_sub_cr_opts("All", "All"))
    if dim == "requester":
        return set(filter_opts(audits_all["Requester"])) if "Requester" in audits_all.columns else set()
    if dim == "tenure":
        return set(tenure_opts)
    if dim == "audit_type":
        return set(filter_opts(audits_all["Type_of_audit"])) if "Type_of_audit" in audits_all.columns else set()
    if dim == "special_project":
        return set(filter_opts(audits_all["Special_project"])) if "Special_project" in audits_all.columns else set()
    if dim == "business_type":
        return set(filter_opts(csat_all["Business_Type"])) if "Business_Type" in csat_all.columns else set()
    if dim == "weeks":
        return {str(w) for w in weeks}
    if dim == "day":
        return set(day_opts)
    if dim == "country":
        return set(_country_opts())
    if dim == "lob":
        return set(filter_opts(audits_all["LOB"]))
    return None


def _canonical_filter_value(raw: str, allowed: set[str] | None) -> str | None:
    text = " ".join(str(raw).replace("\n", " ").split()).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return None
    candidates = [text]
    for prefix in ("Agent ", "Supervisor "):
        if text.startswith(prefix):
            stripped = text[len(prefix):].strip()
            if stripped:
                candidates.append(stripped)
            break

    def _match(value: str) -> str | None:
        if allowed is None:
            return value
        if value in allowed:
            return value
        iso = COUNTRY_FROM_ISO3.get(value.upper())
        if iso and iso in allowed:
            return iso
        name_fold = {n.casefold(): code for code, n in COUNTRY_NAMES.items()}
        named = name_fold.get(value.casefold())
        if named and named in allowed:
            return named
        fold = {a.casefold(): a for a in allowed}
        hit = fold.get(value.casefold())
        if hit:
            return hit
        if allowed:
            norm = normalize_channel_label(value)
            hit = fold.get(norm.casefold())
            if hit:
                return hit
        return None

    for candidate in candidates:
        hit = _match(candidate)
        if hit:
            return hit
    return None


def _click_category(event) -> str | None:
    try:
        points = list(event.selection.points or [])
    except Exception:
        return None
    if not points:
        return None
    pt = points[0]
    if not isinstance(pt, dict):
        try:
            pt = dict(pt)
        except Exception:
            return None
    skip_names = {
        "CRITICAL", "Non-critical", "Cumulative %", "QA", "CSAT", "Recontact",
        "Average", "Upper usual range", "Lower usual range",
        "Goal 5.44", "Rate %", "Repeats", "Contacts",
        "Trend", "Contact reasons", "AHT (min)",
    }

    def _as_label(value, *, allow_int: bool = False) -> str | None:
        if value is None or isinstance(value, (bool, dict)):
            return None
        if isinstance(value, (int, float)) or type(value).__name__ in {"int64", "int32", "float64"}:
            if not allow_int:
                return None
            try:
                num = float(value)
            except Exception:
                return None
            if not num.is_integer():
                return None
            return str(int(num))
        try:
            if pd.isna(value):
                return None
        except Exception:
            pass
        text = str(value).strip()
        if not text or "<br>" in text or text.startswith("<"):
            return None
        if text in skip_names:
            return None
        return " ".join(text.replace("\n", " ").split()) or None

    cd = pt.get("customdata")
    if isinstance(cd, (list, tuple)):
        label = _as_label(cd[0] if cd else None)
        if label:
            return label
    else:
        label = _as_label(cd)
        if label:
            return label
    for key in ("location", "hovertext", "label", "legendgroup"):
        label = _as_label(pt.get(key))
        if label:
            return label
    for key in ("x", "y"):
        label = _as_label(pt.get(key))
        if label:
            return label
    x = pt.get("x")
    ts = pd.to_datetime(x, errors="coerce")
    if pd.notna(ts):
        return ts.strftime("%Y-%m-%d")
    return None


def _apply_chart_filter(event, *, chart_key: str, dim: str) -> None:
    try:
        points = list(event.selection.points or [])
    except Exception:
        points = []
    sig = repr(points)
    prev_key = f"{chart_key}_drill_sig"
    if sig == st.session_state.get(prev_key):
        return
    st.session_state[prev_key] = sig
    if not points:
        return
    raw = _click_category(event)
    if not raw:
        return
    if is_pareto_remainder_label(raw):
        return
    parsed = parse_cr_fallback_label(raw)
    if parsed:
        parent, parent_dim = parsed
        if parent_dim != dim:
            allowed_p = _filter_allowed(parent_dim)
            value_p = _canonical_filter_value(parent, allowed_p)
            if value_p:
                if parent_dim == "cr":
                    st.session_state[_PENDING_SIDEBAR_FILTER] = {
                        "dim": "cr", "value": value_p, "mode": "cr_toggle",
                    }
                    st.rerun(scope="app")
                    return
                if parent_dim == "sub_cr":
                    st.session_state[_PENDING_SIDEBAR_FILTER] = {
                        "dim": "sub_cr", "value": value_p, "mode": "sub_cr_toggle",
                    }
                    st.rerun(scope="app")
                    return
                if parent_dim == "cr_lv1":
                    st.session_state[_PENDING_SIDEBAR_FILTER] = {
                        "dim": "cr_lv1", "value": value_p, "mode": "toggle",
                    }
                    st.rerun(scope="app")
                    return
        raw = parent
    allowed = _filter_allowed(dim)
    value = _canonical_filter_value(raw, allowed)
    if not value:
        return
    if dim == "weeks":
        st.session_state[_PENDING_SIDEBAR_FILTER] = {"dim": "weeks", "value": value, "mode": "weeks_single"}
        st.rerun(scope="app")
        return
    if dim == "cr":
        st.session_state[_PENDING_SIDEBAR_FILTER] = {"dim": "cr", "value": value, "mode": "cr_toggle"}
        st.rerun(scope="app")
        return
    if dim == "sub_cr":
        st.session_state[_PENDING_SIDEBAR_FILTER] = {"dim": "sub_cr", "value": value, "mode": "sub_cr_toggle"}
        st.rerun(scope="app")
        return
    widget_key = _filter_widget_key(dim)
    current = st.session_state.get(widget_key, "All")
    if dim == "channel":
        current = normalize_channel_label(current) if current not in (None, "All") else current
        value = normalize_channel_label(value)
    if str(current) == str(value):
        if dim == "country":
            st.session_state[_PENDING_SIDEBAR_FILTER] = {"dim": dim, "value": "All"}
            st.rerun(scope="app")
        return
    st.session_state[_PENDING_SIDEBAR_FILTER] = {"dim": dim, "value": value}
    st.rerun(scope="app")


def _set_people_filter(dim: str, value: str | None) -> None:
    """Hub buttons cannot mutate an existing widget key — bump fn like Reset filters."""
    old_fn = int(st.session_state.fn)
    new_fn = old_fn + 1
    st.session_state.fn = new_fn
    _copy_sidebar_filter_state(old_fn, new_fn)
    sup_key = f"flt_sup_{new_fn}"
    agent_key = f"flt_agent_{new_fn}"
    if dim == "supervisor":
        if not value or str(value) == "All":
            st.session_state[sup_key] = "All"
            st.session_state[agent_key] = "All"
        else:
            current = str(st.session_state.get(sup_key) or "All")
            st.session_state[sup_key] = "All" if current == str(value) else str(value)
            st.session_state[agent_key] = "All"
    elif dim == "agent":
        if not value or str(value) == "All":
            st.session_state[agent_key] = "All"
        else:
            current = str(st.session_state.get(agent_key) or "All")
            st.session_state[agent_key] = "All" if current == str(value) else str(value)
    st.rerun()


def _plotly_chart(fig, *, key: str, drill: str | None = None, **kwargs):
    """Plotly chart; when `drill` is set, a click writes that sidebar filter and reruns."""
    if fig is not None and drill:
        try:
            fig.update_layout(clickmode="event+select")
        except Exception:
            pass
    plot_kwargs = dict(width="stretch", config=CHART_CFG, key=key, theme=None)
    plot_kwargs.update(kwargs)
    if drill:
        plot_kwargs["on_select"] = "rerun"
        plot_kwargs["selection_mode"] = "points"
    event = st.plotly_chart(fig, **plot_kwargs)
    if drill:
        _apply_chart_filter(event, chart_key=key, dim=drill)
    return event


_DIALOG_CHART_CFG = {**CHART_CFG, "responsive": True}


def _pop_n_annotation(fig):
    """Lift N out of Plotly so it cannot collide with the legend inside the popup."""
    if fig is None:
        return fig, None
    anns = list(fig.layout.annotations or [])
    n_bits = []
    keep = []
    for ann in anns:
        name = getattr(ann, "name", None)
        if name and str(name).startswith("didi_n"):
            bit = str(getattr(ann, "text", "") or "").replace("<br>", " · ").strip()
            if bit:
                n_bits.append(bit)
        else:
            keep.append(ann)
    fig.update_layout(annotations=keep)
    return fig, " · ".join(n_bits) if n_bits else None


def _fit_dialog_fig(fig, *, n_lifted: bool = False):
    """Let Plotly fill the dialog: autosize, no fixed layout.width (that locked ~700–880px)."""
    if fig is None:
        return fig
    prev = fig.layout.margin
    top = int(prev.t) if prev is not None and prev.t is not None else 56
    bottom = int(prev.b) if prev is not None and prev.b is not None else 56
    left = int(prev.l) if prev is not None and prev.l is not None else 56
    right = int(prev.r) if prev is not None and prev.r is not None else 56
    if n_lifted:
        top = max(52, top - 48)
    fig.update_layout(
        autosize=True,
        margin=dict(
            l=left,
            r=max(right, 56),
            t=top,
            b=max(bottom, 48),
        ),
    )
    fig.layout.width = None
    return fig


def _dismiss_preview_dialog() -> None:
    key = st.session_state.pop("_preview_dialog_key", None)
    if key:
        st.session_state[key] = None


def _fill_preview_dialog(chosen: dict, state_key: str) -> None:
    toolbar = chosen.get("toolbar")
    if callable(toolbar):
        t_left, t_right = st.columns([3, 2], vertical_alignment="center")
        with t_left:
            toolbar()
        with t_right:
            _dialog_size_control(state_key)
    else:
        _dialog_size_control(state_key)
    extra = chosen.get("extra")
    fig = chosen.get("fig")
    if callable(fig):
        fig = fig()
    drill_dim = chosen.get("drill")
    below_key = chosen.get("below_key")
    suffix = f"_b{int(_below_on(below_key))}" if below_key else ""
    size_tag = str(st.session_state.get(f"didi_dlg_size_{state_key}") or "Default")[:1]
    full_key = f"{state_key}_full{suffix}_{size_tag}"
    lead = chosen.get("insight")
    if callable(lead):
        lead = lead()
    if lead:
        render_chip(lead)
    n_text = None
    if fig is not None and chosen.get("kind") != "pie":
        fig, n_text = _pop_n_annotation(fig)
        fig = _fit_dialog_fig(fig, n_lifted=bool(n_text))
    if n_text:
        st.markdown(f'<p class="didi-dialog-n">{html_escape(n_text)}</p>', unsafe_allow_html=True)
    if chosen.get("kind") == "pie":
        table = chosen.get("table")
        pie_fig = square_pie_fig(fig) if fig is not None else fig
        pie_fig = _fit_dialog_fig(pie_fig)
        if table is not None and not getattr(table, "empty", True):
            pie_col, tbl_col = st.columns([1.05, 1])
            with pie_col:
                _plotly_chart(
                    pie_fig, key=full_key, drill=drill_dim, config=_DIALOG_CHART_CFG,
                )
                if drill_dim:
                    st.caption("Click a slice to apply that filter.")
                if callable(extra):
                    extra()
            with tbl_col:
                st.markdown("<p class='didi-panel-title'>QA fail type and attribute</p>", unsafe_allow_html=True)
                show_fail_attr_table(table)
            return
        _plotly_chart(pie_fig, key=full_key, drill=drill_dim, config=_DIALOG_CHART_CFG)
        if drill_dim:
            st.caption("Click a slice to apply that filter.")
        if callable(extra):
            extra()
        return
    _plotly_chart(fig, key=full_key, drill=drill_dim, config=_DIALOG_CHART_CFG)
    if drill_dim:
        st.caption("Click a bar or point to apply that filter.")
    if callable(extra):
        extra()


def _show_preview_dialog(chosen: dict, state_key: str) -> None:
    """Modal window for the open preview chart — same overlay idea as a popup."""
    st.session_state["_preview_dialog_key"] = state_key
    title = str(chosen.get("title") or "Chart")

    @st.dialog(title, width="large", on_dismiss=_dismiss_preview_dialog)
    def _body() -> None:
        with st.container(
            key="didi_dialog_body",
            width="stretch",
            horizontal_alignment="center",
        ):
            _fill_preview_dialog(chosen, state_key)

    _body()


@st.fragment
def _preview_board_fragment(items: list[dict], state_key: str, columns: int) -> None:
    """Cards stay on the page. Title clicks open the chart in a modal; only this fragment reruns."""
    if state_key not in st.session_state:
        st.session_state[state_key] = None
    for i in range(0, len(items), columns):
        chunk = items[i:i + columns]
        cols = st.columns(columns)
        for col, item in zip(cols, chunk):
            item_id = item["id"]
            open_id = st.session_state.get(state_key)
            is_on = open_id == item_id
            btn = item.get("btn") or "def"
            with col:
                with st.container(border=True, key=f"didi_rcard_{btn}_{item_id}"):
                    st.markdown(
                        f'<span class="didi-rcard-flag didi-rcard-flag--{"on" if is_on else "off"}"></span>',
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        f"{item['title']}  (click to open)",
                        key=f"pvbtn_{item_id}",
                        width="stretch",
                        help="Open the full chart",
                    ):
                        st.session_state[state_key] = None if is_on else item_id
                        st.rerun(scope="fragment")
                    st.metric(
                        item["title"],
                        item.get("value") or "—",
                        delta=item.get("delta"),
                        delta_color=item.get("delta_color") or "off",
                        label_visibility="collapsed",
                    )
                    spark = item.get("spark")
                    if spark is not None:
                        st.plotly_chart(
                            spark, width="stretch", config=CHART_CFG,
                            key=f"{state_key}_{item_id}_mini", theme=None,
                        )
    open_id = st.session_state.get(state_key)
    chosen = next((item for item in items if item["id"] == open_id), None)
    if chosen is None:
        return
    _show_preview_dialog(chosen, state_key)


def render_preview_board(items: list[dict], *, state_key: str, columns: int = 2) -> None:
    """KPI-style cards in pairs. Open/close is a fragment rerun so filters and KPIs do not recompute."""
    with st.container(key=f"didi_pvboard_{state_key}"):
        _preview_board_fragment(items, state_key, columns)


def aht_corr_display(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    return pd.DataFrame({
        "Pair": df["Pair"],
        "Slice": df["Slice"],
        "R²": df["Pearson_r"].map(lambda v: "—" if pd.isna(v) else f"{float(v)**2:.2f}"),
        "Direction": df["Pearson_r"].map(
            lambda v: "—" if pd.isna(v) else ("negative" if float(v) < 0 else ("flat" if abs(float(v)) < 0.05 else "positive"))
        ),
        "N (shared contact reason Lv4 (detail))": df["N_CR"].astype(int),
    })


def render_aht_quality_block(chart_prefix: str, *, include_qa_scatter: bool = True) -> None:
    """Handle-time scatters + R². Association only."""
    n_surveys = volumes.get("surveys")
    n_audits = volumes.get("evaluations")
    qa_r, qa_n = _pair_r(aht_corr, "AHT vs QA", "All")
    cs_r, cs_n = _pair_r(aht_corr, "AHT vs CSAT", "All")
    rc_r, rc_n = _pair_r(aht_corr, "AHT vs Recontact", "All")

    def _aht_scatter_row(title: str, fig, key: str, r_args, r_kwargs=None):
        with panel():
            st.markdown(f"**{title}**")
            _plotly_chart(fig, key=key, drill="cr")
            st.caption("Click a point to filter to that contact reason Lv4 (detail).")
            render_r_box(*r_args, **(r_kwargs or {}))

    if include_qa_scatter:
        _aht_scatter_row(
            "QA vs AHT",
            qa_aht_scatter(aht_points),
            f"{chart_prefix}_qa",
            (qa_r, qa_n, "QA vs handle time"),
            {"audits": n_audits},
        )
        with panel():
            st.markdown("**AHT correlations**")
            st.plotly_chart(corr_r_bars(aht_corr), width="stretch", config=CHART_CFG, key=f"{chart_prefix}_r")
            render_notes(aht_outcome_notes(aht_corr, scope=slice_lead, channel=sel_channel))
    _aht_scatter_row(
        "CSAT vs AHT",
        aht_metric_scatter(
            aht_joined, "CSAT_Pct",
            y_title="CSAT %",
            title="CSAT vs AHT",
            y_goal=CSAT_GOAL,
            empty_text=aht_overlap_empty_text(
                cs_n, "CSAT", surveys=n_surveys, audits=n_audits,
                min_audits=AHT_CR_MIN_AUDITS,
            ),
        ),
        f"{chart_prefix}_csat",
        (cs_r, cs_n, "CSAT vs handle time"),
        {"surveys": n_surveys, "audits": n_audits},
    )
    _aht_scatter_row(
        "Recontact vs AHT",
        aht_metric_scatter(
            aht_joined, "Recontact_Rate",
            y_title="Recontact rate %",
            title="Recontact vs AHT",
            y_goal=RECONTACT_GOAL,
            lower_better=True,
            empty_text=aht_overlap_empty_text(
                rc_n, "recontact", audits=n_audits, min_audits=AHT_CR_MIN_AUDITS,
            ),
        ),
        f"{chart_prefix}_rc",
        (rc_r, rc_n, "Recontact vs handle time"),
        {"audits": n_audits},
    )
    if not include_qa_scatter:
        with panel():
            st.plotly_chart(corr_r_bars(aht_corr), width="stretch", config=CHART_CFG, key=f"{chart_prefix}_r")
            render_notes(aht_outcome_notes(aht_corr, scope=slice_lead, channel=sel_channel))


_TOAST_HOLD_S = 8.0


def render_filter_effects() -> None:
    msgs: list[str] = []
    if sel_day != "All":
        day_lbl = pd.Timestamp(sel_day).strftime("%b %d")
        msgs.append(
            f"Day = {day_lbl}. QA, CSAT and recontact are all cut to this calendar date "
            "on each source’s own Fecha. QA may have no audits that day."
        )
    if sel_channel != "All":
        msgs.append(
            f"Channel = {sel_channel}. QA, CSAT and recontact are all cut to this channel. "
            "Recontact is this channel's rate, not the official 12-channel mix."
        )
    if sel_country != "All":
        msgs.append(
            f"Market = {sel_country} cuts QA and CSAT. Recontact has no country field "
            "(region is always SSL), so the recontact KPI is not cut by market."
        )
    if sel_lob != "All":
        msgs.append(f"LOB = {sel_lob} cuts QA only. CSAT and recontact have no LOB field.")
    if sel_tenure != "All":
        msgs.append(f"Agent tenure = {sel_tenure} cuts QA only. CSAT and recontact stay on the other active filters.")
    if sel_supervisor != "All":
        msgs.append(
            "Supervisor cuts QA and CSAT. CSAT keeps surveys whose agent name matches that supervisor’s QA agents. Recontact is not cut."
        )
    if sel_agent != "All":
        msgs.append(
            f"Agent = {sel_agent} cuts QA and CSAT. CSAT keeps surveys whose agent name matches this QA Agent_ID. Recontact is not cut."
        )
    if sel_audit_type != "All":
        msgs.append("Type of audit cuts QA only.")
    if sel_special != "All":
        msgs.append("Special project cuts QA only.")
    if sel_business != "All":
        msgs.append("Business type cuts CSAT only.")
    if sel_cr_lv1 != "All":
        msgs.append(
            f"Contact reason Lv1 (group) = {sel_cr_lv1}. QA and recontact inherit the group via the contact reason Lv4 (detail) name."
        )
    if sel_cr != "All":
        msgs.append(f"Contact reason Lv4 (detail) = {sel_cr}. All three sources are cut to this name.")
    if sel_sub_cr != "All":
        msgs.append(
            f"Contact reason SUB_CR (finest) = {sel_sub_cr}. Cuts QA and CSAT. Recontact is not cut."
        )
    sig = tuple(msgs)
    if sig != st.session_state.get("filter_fx_sig"):
        st.session_state["filter_fx_sig"] = sig
        st.session_state["filter_fx_shown_at"] = time.monotonic()
    if not msgs:
        return
    started = float(st.session_state.get("filter_fx_shown_at") or 0)
    if started and (time.monotonic() - started) >= _TOAST_HOLD_S:
        return
    st.markdown(
        f'<span class="didi-toast-sr">{html_escape(" ".join(msgs))}</span>',
        unsafe_allow_html=True,
    )
    sig_key = html_escape("|".join(msgs))
    cards = []
    for msg in msgs:
        cards.append(
            '<div class="didi-toast-card">'
            '<button type="button" class="didi-toast-x" aria-label="Close">×</button>'
            '<div class="didi-toast-kicker">Filter</div>'
            f'<div class="didi-toast-body">{html_escape(msg)}</div>'
            "</div>"
        )
    st.html(
        f'<div id="didi-toast-live" data-sig="{sig_key}">'
        + "".join(cards)
        + "</div>"
        "<script>"
        "(function(){"
        "var el=document.getElementById('didi-toast-live');"
        "if(!el)return;"
        "var sig=el.getAttribute('data-sig')||'';"
        "var key='didi_toast_dismissed';"
        "if(sessionStorage.getItem(key)===sig){el.remove();return;}"
        "var hide=function(){try{sessionStorage.setItem(key,sig);}catch(e){}"
        "if(el&&el.parentNode)el.remove();};"
        "el.querySelectorAll('.didi-toast-x').forEach(function(b){b.addEventListener('click',hide);});"
        "setTimeout(hide,8000);"
        "})();"
        "</script>",
        unsafe_allow_javascript=True,
    )


def render_insight_bar() -> None:
    render_notes(qa_chip(summary["qa_score"]))
    render_notes(csat_chip(summary["csat"]))
    if brief.worst_cr and brief.worst_cr != "—":
        render_notes({"text": f"Focus contact reason Lv4 (detail): {str(brief.worst_cr)[:28]}.", "tone": "risk"})


def render_action_panel() -> None:
    with st.container(border=True, key=_next_didi_key("didi_action")):
        st.markdown(
            f'<div class="didi-action">'
            f'<div class="didi-action-kicker">{html_escape(L("panel_actions"))}</div>'
            "</div>",
            unsafe_allow_html=True,
        )
        acts = action_display(actions)
        if acts.empty:
            st.caption("No actions generated.")
        else:
            show_df(acts)


def corr_findings(tbl: pd.DataFrame) -> pd.DataFrame:
    if tbl.empty:
        return tbl
    rows = []
    for _, row in tbl.iterrows():
        pair = str(row.get("Pair", ""))
        r = row.get("Pearson_r")
        n = row.get("N_CR")
        n_txt = int(n) if pd.notna(n) else "—"
        if pd.isna(r):
            n_val = int(n) if pd.notna(n) else 0
            meaning = (
                f"Need at least 5 shared contact reason Lv4 (detail) names to compute R². "
                f"This pair currently has {n_val} in the active filter."
            )
            finding = (
                "Not shown. The two sources do not share enough contact reason Lv4 (detail) names after the current filter. "
                "The KPI cards still use this filter; this row is only the association test."
            )
        else:
            r2 = float(r) ** 2
            mag = abs(float(r))
            if mag < 0.20:
                strength = "Very weak"
            elif mag < 0.40:
                strength = "Weak"
            elif mag < 0.60:
                strength = "Moderate"
            else:
                strength = "Strong"
            direction = "positive" if r > 0 else "negative"
            meaning = (
                f"{strength} {direction} link (R²={r2:.2f}). "
                f"N={n_txt} contact reason Lv4 (detail) values appear in both series. "
                "N is not surveys and not audits."
            )
            if pair == "QA vs CSAT":
                if mag < 0.30:
                    finding = "QA and CSAT barely move together at reason level. Raising the audit score may not lift CSAT."
                elif r > 0:
                    finding = "Reasons with higher QA tend to have higher CSAT."
                else:
                    finding = "Reasons with higher QA tend to have lower CSAT — quality vs experience are splitting."
            elif pair == "QA vs Recontact":
                if r < -0.20:
                    finding = "Lower-QA reasons tend to come back more. Defects and repeats share drivers."
                elif mag < 0.20:
                    finding = "QA and recontact are not tightly linked at reason level."
                else:
                    finding = (
                        "Higher QA with higher recontact — on Channel = All this is often a mix effect "
                        "(Self Help vs Phone/Chat). On a single channel it is a real reason-level pattern."
                    )
            else:
                if r < -0.20:
                    finding = "Lower CSAT reasons tend to recontact more."
                elif mag < 0.20:
                    finding = "CSAT and recontact are only loosely related at reason level."
                else:
                    finding = "Higher CSAT with higher recontact — likely a mix/volume effect, not a simple quality story."
        rows.append({
            "Pair": pair,
            "R²": f"{float(r)**2:.2f}" if pd.notna(r) else "—",
            "N": n_txt,
            "What R² and N mean": meaning,
            "Finding": finding,
        })
    return pd.DataFrame(rows)


def render_r_n_meaning(*, chart_key: str = "qa_corr_r_full") -> None:
    corr_plot = corr_tbl.copy() if corr_tbl is not None else pd.DataFrame()
    if not corr_plot.empty and "Slice" not in corr_plot.columns:
        corr_plot["Slice"] = "Lv4"
    with st.expander("What R² and N mean"):
        st.plotly_chart(
            corr_r_bars(corr_plot), width="stretch", config=CHART_CFG,
            key=chart_key, theme=None,
        )
        cov = pd.DataFrame({
            "Source in this filter": [
                f"QA (contact reason Lv4 (detail) with ≥ {corr_cov['min_qa']} audits)",
                "CSAT",
                "Recontact",
            ],
            "Distinct contact reason Lv4 (detail)": [corr_cov["qa_n"], corr_cov["csat_n"], corr_cov["rc_n"]],
            "Shared with the other KPIs": [
                f"QA and CSAT {corr_cov['qa_csat']} · QA and recontact {corr_cov['qa_rc']}",
                f"QA and CSAT {corr_cov['qa_csat']} · CSAT and recontact {corr_cov['csat_rc']}",
                f"QA and recontact {corr_cov['qa_rc']} · CSAT and recontact {corr_cov['csat_rc']}",
            ],
        })
        show_df(cov)
        show_df(corr_findings(corr_tbl))


def weekly_display() -> pd.DataFrame:
    if weekly.empty:
        return weekly
    out = pd.DataFrame({
        "Week": weekly.get("Week"),
        "QA": weekly["QA_Score"].map(lambda v: _fmt(v, 1)) if "QA_Score" in weekly else None,
        "vs 85": weekly["QA_vs_Goal"].map(lambda v: _vs(v, 1)) if "QA_vs_Goal" in weekly else None,
        "QA WoW": weekly["QA_WoW_pp"].map(lambda v: _vs(v, 1)) if "QA_WoW_pp" in weekly else None,
        "CSAT": weekly["CSAT_Score"].map(lambda v: _fmt(v, 1)) if "CSAT_Score" in weekly else None,
        "CSAT vs 85": weekly["CSAT_vs_Goal"].map(lambda v: _vs(v, 1)) if "CSAT_vs_Goal" in weekly else None,
        "CSAT WoW": weekly["CSAT_WoW_pp"].map(lambda v: _vs(v, 1)) if "CSAT_WoW_pp" in weekly else None,
        "RC": weekly["Recontact_Rate"].map(lambda v: _fmt(v, 2)) if "Recontact_Rate" in weekly else None,
        "vs 5.44": weekly["Recontact_vs_Goal"].map(lambda v: _vs(v, 2)) if "Recontact_vs_Goal" in weekly else None,
        "RC WoW": weekly["Recontact_WoW_pp"].map(lambda v: _vs(v, 2)) if "Recontact_WoW_pp" in weekly else None,
    })
    return out


def perf_display(df: pd.DataFrame, segment_col: str = "Segment") -> pd.DataFrame:
    if df.empty:
        return df
    out = {
        segment_col: df["Segment"],
        "QA Score": df["QA_Score"].map(lambda v: _fmt(v, 1, "%")),
        "QA vs goal": df["QA_Score_vs"].map(lambda v: _vs(v)),
        "CSAT": df["CSAT_Score"].map(lambda v: _fmt(v, 1, "%")),
        "CSAT vs goal": df["CSAT_Score_vs"].map(lambda v: _vs(v)),
        "Recontact": df["Recontact_Rate"].map(lambda v: _fmt(v, 2, "%")),
        "RC vs goal": df["Recontact_Rate_vs"].map(lambda v: _vs(v, 2)),
    }
    if "QA_N" in df.columns:
        out["n"] = df["QA_N"].map(lambda v: f"{int(v):,}" if pd.notna(v) else "—")
    if "QA_Share" in df.columns:
        out["Share"] = df["QA_Share"].map(lambda v: _fmt(v, 1, "%"))
    return pd.DataFrame(out)


def ov_supervisor_display(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    top = df

    def _fb(v):
        return f"{int(v):,}" if pd.notna(v) else "—"

    return pd.DataFrame({
        "Supervisor": top["Supervisor_ID"],
        "QA Score": top["QA_Score"].map(lambda v: _fmt(v, 1, "%")),
        "QA vs 85": top["QA_Score"].map(lambda v: _vs(v - QA_GOAL) if pd.notna(v) else "—"),
        "AHT min": top["AHT_min"].map(lambda v: _fmt(v, 1)),
        "CSAT": top["CSAT_Score"].map(lambda v: _fmt(v, 1, "%")),
        "CSAT vs 85": top["CSAT_Score"].map(lambda v: _vs(v - CSAT_GOAL) if pd.notna(v) else "—"),
        "Recontact": "—",
        "Agents": top["Agents"].map(lambda v: int(v) if pd.notna(v) else 0),
        "Audits": top["n"].map(lambda v: int(v) if pd.notna(v) else 0),
        "Surveys": top["Feedback"].map(_fb) if "Feedback" in top.columns else "—",
    })


def agents_tenure_display(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    top = df
    tenure = top["Tenure_Cohort"] if "Tenure_Cohort" in top.columns else "—"
    supervisor = top["Supervisor_ID"] if "Supervisor_ID" in top.columns else "—"
    return pd.DataFrame({
        "Agent": top["Agent_ID"],
        "Tenure": tenure,
        "Supervisor": supervisor,
        "QA": top["QA_Score"].map(lambda v: _fmt(v, 1, "%")),
        "vs 85": top["QA_Score"].map(lambda v: _vs(v - QA_GOAL) if pd.notna(v) else "—"),
        "n": top["n"].map(lambda v: int(v) if pd.notna(v) else 0),
    })


def qa_agent_roster_display(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    tenure = df["Tenure_Cohort"] if "Tenure_Cohort" in df.columns else "—"
    return pd.DataFrame({
        "Supervisor": df["Supervisor_ID"],
        "Agent": df["Agent_ID"],
        "QA": df["QA_Score"].map(lambda v: _fmt(v, 1, "%")),
        "vs 85": df["QA_Score"].map(lambda v: _vs(v - QA_GOAL) if pd.notna(v) else "—"),
        "Attribute fails": df["Fail_Count"].map(lambda v: int(v) if pd.notna(v) else 0),
        "Fail share": df["Fail_Share"].map(lambda v: _fmt(v, 1, "%") if pd.notna(v) else "—"),
        "Critical %": df["Fatal_Rate"].map(lambda v: _fmt(v, 1, "%") if pd.notna(v) else "—"),
        "Audits": df["Audit_Count"].map(lambda v: int(v) if pd.notna(v) else 0),
        "Tenure": tenure,
    })


def csat_agent_roster_display(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    return pd.DataFrame({
        "Supervisor": df["Supervisor_ID"],
        "Agent": df["Agent"],
        "CSAT": df["CSAT_Score"].map(lambda v: _fmt(v, 1, "%")),
        "vs 85": df["CSAT_Score"].map(lambda v: _vs(v - CSAT_GOAL) if pd.notna(v) else "—"),
        "Unsatisfied": df["Unsatisfied"].map(lambda v: int(v) if pd.notna(v) else 0),
        "Unsat share": df["Unsat_Share"].map(lambda v: _fmt(v, 1, "%") if pd.notna(v) else "—"),
        "Surveys": df["Feedback"].map(lambda v: int(v) if pd.notna(v) else 0),
    })


def _gap_fig(
    frame: pd.DataFrame,
    title: str,
    value_title: str,
    sample_unit: str = "audits",
    universe_n: int | None = None,
):
    if frame is None or frame.empty:
        src = pd.DataFrame()
    else:
        keep = [
            c for c in ("Cat", "Gap_Impact", "n", "N", "Feedback", "Audits",
                        "Audit_Count", "QA_Evaluations", "Contacts")
            if c in frame.columns
        ]
        src = frame[keep].head(10)
    return pareto_dual_axis(
        src if not src.empty else pd.DataFrame(),
        "Cat", "Gap_Impact",
        title=title, value_title=value_title,
        sample_unit=sample_unit,
        universe_n=universe_n,
    )


def _gap_spark(frame: pd.DataFrame):
    if frame is None or frame.empty:
        return None
    top = frame.head(5)
    return spark_hbar_fig(top["Cat"].astype(str).tolist(), top["Gap_Impact"].fillna(0).tolist())


def _gap_card_delta(frame: pd.DataFrame, unit: str) -> str:
    """Card delta: top name + real volume, never Gap_Impact labeled as audits."""
    if frame is None or frame.empty:
        return "All ≥ 85"
    top = frame.iloc[0]
    name = str(top["Cat"])[:36]
    vol_col = next(
        (c for c in ("n", "Feedback", "Audits", "Audit_Count", "QA_Evaluations", "Contacts")
         if c in frame.columns),
        None,
    )
    if vol_col and pd.notna(top[vol_col]):
        return f"{name} · {int(top[vol_col]):,} {unit}"
    return name


def _pair_r(tbl: pd.DataFrame, pair: str, slice_name: str | None = None):
    if tbl is None or tbl.empty or "Pair" not in tbl.columns:
        return None, 0
    sub = tbl[tbl["Pair"] == pair]
    if slice_name and "Slice" in sub.columns:
        hit = sub[sub["Slice"] == slice_name]
        if not hit.empty:
            sub = hit
    if sub.empty:
        return None, 0
    row = sub.iloc[0]
    n = int(row["N_CR"]) if "N_CR" in row and pd.notna(row["N_CR"]) else 0
    r = row["Pearson_r"] if "Pearson_r" in row else None
    return (float(r) if pd.notna(r) else None), n


def combo_display(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    rows = df.head(8)
    return pd.DataFrame({
        L("col_cr_detail"): rows["CR_Lv4"].astype(str),
        "Pattern": rows["Pattern"],
        "QA": rows["QA_Score"].map(lambda v: _fmt(v, 1, "%")),
        "QA vs goal": rows["QA_vs"].map(lambda v: _vs(v)),
        "Audits": rows["QA_N"].map(lambda v: f"{int(v):,}" if pd.notna(v) else "—"),
        "CSAT": rows["CSAT_Score"].map(lambda v: _fmt(v, 1, "%")),
        "Surveys": rows["Feedback"].map(lambda v: f"{int(v):,}" if pd.notna(v) else "—"),
        "Recontact": rows["Recontact_Rate"].map(lambda v: _fmt(v, 2, "%")),
        "Contacts": rows["Contacts"].map(lambda v: f"{int(v):,}" if pd.notna(v) else "—"),
    })


def action_display(items) -> pd.DataFrame:
    if not items:
        return pd.DataFrame()
    return pd.DataFrame([
        {
            "Finding": it.finding,
            "Action": it.action,
            "Owner": it.owner,
            "Priority": it.priority,
            "Timeline": it.timeline,
        }
        for it in items
    ])


def attr_display(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["Severity"] = out["Is_Critical"].map(lambda v: "CRITICAL" if v else "Non-critical")
    out["Attribute"] = out["Error_Category"].astype(str).str[:36]
    out["Fails"] = out["Fail_Count"].astype(int)
    out["% of fails"] = out["Pct_Of_Fails"].map(lambda v: f"{v:.1f}%")
    out["Impact on QA (points)"] = out["Impact_pp"].map(lambda v: f"{v:.2f}")
    return out[["Attribute", "Severity", "Fails", "% of fails", "Impact on QA (points)"]]


def render_methodology() -> None:
    official = score_method["official"] if score_method else summary["qa_score"]
    source = score_method["source"] if score_method else 86.90
    gap = score_method["gap"] if score_method else round(official - source, 2)
    agree = score_method["agreement"] if score_method else None
    agree_txt = f"{agree:.2f}%" if agree is not None else "not available in this snapshot"
    with st.expander("Notes on methodology — scoring, typing, and recontact rate"):
        st.markdown(
            f"""
The **official QA Score on this dashboard is {official:.2f}%**, calculated from the
business-case rule: start at 100, any **critical** fail scores **0**, each non-critical fail
deducts 10 points. Phone attributes are columns W–AH; Live Chat are AI–AP. They are
never mixed in one score. N/A (value 2) is excluded. That is the number in the KPI card.

The Excel QA tab also carries `Score_end_user`, a **source rubric** that weights
attributes and penalizes process adherence. Its average is **{source:.2f}%**
({gap:+.2f} points vs the official score). The two series coincide on {agree_txt} of
audits. Both beat the 85% goal; this dashboard reports the business-case score.

**Incorrect contact-reason typing is 9.72%**, not 47.20%. Comparing `CR_registrada`
and `CR_correcta` as raw text inflates the figure: 37.48 pp of that gap is only a
difference in capitalization.

**Recontact rate is always a ratio of sums** (Σ Recontact Volume / Σ Contacts), never
an average of row-level rates.
"""
        )


def render_channel_qa(ch: str, data: dict) -> None:
    st.markdown(f"**{ch}**")
    if not data or data.get("qa_score") is None:
        st.caption(
            "No audits in the current filter. Phone (W–AH) and Live Chat (AI–AP) are scored separately."
        )
        return
    ch_aud = audits[audits["Channel"] == ch] if "Channel" in audits.columns else audits
    ch_err = errors[errors["Channel"] == ch] if "Channel" in errors.columns else errors
    ch_crit = critical_fail_stats(ch_aud, ch_err)
    st.metric("QA Score", f"{data['qa_score']:.1f}%", delta=f"{data['qa_vs']:+.1f} points vs goal")
    st.caption(
        f"{ch_crit['pct_fatal']:.1f}% of {ch} audits have a CRITICAL fail (scored 0). "
        f"{ch_crit['n_crit_fails']:,} CRITICAL fails · {ch_crit['n_noncrit_fails']:,} Non-critical fails."
    )
    top_attrs = data.get("top_attrs", pd.DataFrame())
    if not getattr(top_attrs, "empty", True):
        show_df(attr_display(top_attrs))
    worst_cr = data.get("worst_cr", pd.DataFrame())
    if not getattr(worst_cr, "empty", True):
        st.caption("Lowest-scoring contact reason Lv4 (detail) names")
        show_df(pd.DataFrame({
            L("col_cr_detail"): worst_cr["CR_Lv4"].astype(str).str[:40],
            "QA": worst_cr["QA_Score"].map(lambda v: f"{v:.1f}%"),
        }))


render_header(PAGE_TITLES.get(page, page))
render_filter_effects()

if page == "Overview":
    top1 = rc_vol_lv1.iloc[0] if not rc_vol_lv1.empty else None
    top4 = rc_vol_lv4.iloc[0] if not rc_vol_lv4.empty else None
    top_sub = None
    sub_spark_names, sub_spark_vals = [], []
    if csat is not None and not csat.empty and "SUB_CR" in csat.columns and "Feedback CNT" in csat.columns:
        _sub_vol = (
            csat.groupby(csat["SUB_CR"].astype(str).str.strip(), dropna=False)["Feedback CNT"]
            .sum()
            .sort_values(ascending=False)
        )
        _sub_vol = _sub_vol[_sub_vol > 0]
        if not _sub_vol.empty:
            _sub_total = float(_sub_vol.sum())
            top_sub = (
                str(_sub_vol.index[0]),
                int(_sub_vol.iloc[0]),
                float(_sub_vol.iloc[0] / _sub_total * 100) if _sub_total else 0.0,
            )
            sub_spark_names = [str(x)[:28] for x in _sub_vol.head(5).index]
            sub_spark_vals = [float(v) for v in _sub_vol.head(5).tolist()]

    ov1, ov_rest = st.columns([1, 2], gap="medium")
    with ov1:
        _col_kicker("CX Quality Performance")
        render_kpi(
            L("kpi_qa"), f"{summary['qa_score']:.2f}%", qa_vs, "normal",
            spark=sparkline_fig(qa_spark_vals, CHART_COLORS["qa"], qa_spark_lbl, "%", "QA %"),
            spark_key="ov_spark_qa",
            caption=qa_disp,
            traffic=qa_light,
        )
        render_kpi(
            L("kpi_csat"), f"{summary['csat']:.2f}%", cs_vs, "normal",
            spark=sparkline_fig(csat_spark_vals, CHART_COLORS["csat"], csat_spark_lbl, "%", "CSAT %"),
            spark_key="ov_spark_csat",
            traffic=cs_light,
        )
        render_kpi(
            L("kpi_crit_fails"), f"{crit['n_crit_fails']:,}",
            f"{crit['pct_fails_critical']:.1f}% of attribute fails", "off",
            traffic=_fail_light(crit["n_crit_fails"], critical=True),
            traffic_label=False,
            size="secondary",
        )
        render_kpi(
            L("kpi_noncrit_fails"),
            f"{crit['n_noncrit_fails']:,}",
            f"{crit['pct_fails_noncritical']:.1f}% of attribute fails",
            "off",
            traffic=_fail_light(crit["n_noncrit_fails"], critical=False),
            traffic_label=False,
            size="secondary",
        )
        aht_sum = qa_aht_summary(audits)
        if aht_sum["aht_min"] is not None:
            render_kpi(
                L("kpi_aht"),
                f"{aht_sum['aht_min']:.1f} min",
                f"median {aht_sum['aht_p50_min']:.1f} min · {aht_sum['n']:,} audits",
                "off",
                help_text=L("note_aht"),
                traffic_label=False,
                size="secondary",
            )
        else:
            render_kpi(
                L("kpi_aht"),
                "—",
                "No Duration in this filter",
                "off",
                help_text=L("note_aht"),
                traffic_label=False,
                size="secondary",
            )
        render_resolution_kpi("ov_spark_resolution")
        render_unresolved_owner_kpi("ov_spark_unresolved")
    with ov_rest:
        ov2, ov3 = st.columns(2, gap="medium")
        with ov2:
            _col_kicker("Operational Flow & Volumes")
            render_kpi(
                L("kpi_contacts"), f"{volumes['contacts']:,}", c_txt, c_dcol,
                spark=sparkbar_fig(vol_series["contacts"] or [volumes["contacts"]], CHART_COLORS["blue"],
                                   vol_series.get("contacts_labels") or None, "", "Contacts"),
                spark_key="ov_spark_contacts",
                size="secondary",
            )
            render_kpi(
                L("kpi_surveys"), f"{volumes['surveys']:,}", s_txt, s_dcol,
                spark=sparkbar_fig(vol_series["surveys"] or [volumes["surveys"]], CHART_COLORS["csat"],
                                   vol_series.get("surveys_labels") or None, "", "Surveys"),
                spark_key="ov_spark_surveys",
                size="secondary",
            )
            render_kpi(
                L("kpi_evals"), f"{volumes['evaluations']:,}", e_txt, e_dcol,
                spark=sparkbar_fig(vol_series["evals"] or [volumes["evaluations"]], CHART_COLORS["blue"],
                                   vol_series.get("evals_labels") or None, "", "Audits"),
                spark_key="ov_spark_evals",
                size="secondary",
            )
            render_kpi(
                L("kpi_recontacts"), f"{volumes.get('recontacts', 0):,}", r_txt, r_dcol,
                spark=sparkbar_fig(
                    vol_series.get("recontacts") or [volumes.get("recontacts", 0)],
                    CHART_COLORS["recontact"],
                    vol_series.get("recontacts_labels") or None, "", "Repeats",
                ),
                spark_key="ov_spark_repeats",
                caption="Σ Recontact Volume · numerator of the official rate.",
                size="secondary",
            )
            render_abandoned_kpi("ov_spark_abandoned")
        with ov3:
            _col_kicker("Customer Efficiency & Sentiment")
            render_kpi(
                L("kpi_recontact"), f"{rc_rate:.2f}%", rc_vs, "inverse",
                spark=sparkline_fig(rc_spark_vals, CHART_COLORS["recontact"], rc_spark_lbl, "%", "Rate %"),
                spark_key="ov_spark_rc",
                traffic=rc_light,
            )
            star_l, star_r = st.columns(2, gap="small")
            with star_l:
                render_kpi(
                    "4–5 star surveys",
                    f"{_star_hi:,}",
                    (
                        f"{(_star_hi / _star_n * 100):.1f}% of surveys"
                        if _star_n else "% of surveys rated 4 or 5 stars"
                    ),
                    "off",
                    spark=spark_donut_fig(
                        _stars_hi["Rating"].astype(str).tolist(),
                        _stars_hi["Count"].fillna(0).tolist(),
                    ) if not _stars_hi.empty else None,
                    spark_key="ov_spark_stars_hi",
                    size="secondary",
                )
            with star_r:
                render_kpi(
                    "1–3 star surveys",
                    f"{_star_lo:,}",
                    (
                        f"{(_star_lo / _star_n * 100):.1f}% of surveys"
                        if _star_n else "surveys rated 1 to 3 stars"
                    ),
                    "off",
                    spark=spark_donut_fig(
                        _stars_lo["Rating"].astype(str).tolist(),
                        _stars_lo["Count"].fillna(0).tolist(),
                    ) if not _stars_lo.empty else None,
                    spark_key="ov_spark_stars_lo",
                    size="secondary",
                )
            cr_l, cr_r = st.columns(2, gap="small")
            with cr_l:
                render_kpi(
                    "Contact reason Lv1",
                    f"{int(top1['Contacts']):,}" if top1 is not None else "—",
                    (
                        f"{str(top1['CR_Lv1'])[:36]} · {float(top1['Pct']):.1f}% of contacts"
                        if top1 is not None else None
                    ),
                    "off",
                    spark=spark_hbar_fig(
                        rc_vol_lv1.head(5)["CR_Lv1"].astype(str).tolist(),
                        rc_vol_lv1.head(5)["Contacts"].fillna(0).tolist(),
                    ) if not rc_vol_lv1.empty else None,
                    spark_key="ov_spark_cr1",
                    size="secondary",
                )
            with cr_r:
                render_kpi(
                    "Contact reason Lv4",
                    f"{int(top4['Contacts']):,}" if top4 is not None else "—",
                    (
                        f"{str(top4['CR_Lv4'])[:36]} · {float(top4['Pct']):.1f}% of contacts"
                        if top4 is not None else None
                    ),
                    "off",
                    spark=spark_hbar_fig(
                        rc_vol_lv4.head(5)["CR_Lv4"].astype(str).tolist(),
                        rc_vol_lv4.head(5)["Contacts"].fillna(0).tolist(),
                    ) if not rc_vol_lv4.empty else None,
                    spark_key="ov_spark_cr4",
                    size="secondary",
                )
            render_kpi(
                "Contact reason SUB_CR",
                f"{int(top_sub[1]):,}" if top_sub is not None else "—",
                (
                    f"{top_sub[0][:36]} · {top_sub[2]:.1f}% of surveys"
                    if top_sub is not None else "Finest contact reason on CSAT"
                ),
                "off",
                spark=spark_hbar_fig(sub_spark_names, sub_spark_vals) if sub_spark_vals else None,
                spark_key="ov_spark_sub",
                size="secondary",
            )
            _pie_names, _pie_vals = [], []
            if rc_ch_vol is not None and not rc_ch_vol.empty and "Contacts" in rc_ch_vol.columns:
                _ch_key = rc_ch_vol["Cat"].map(normalize_channel_label)
                for _ch in ("Phone", "Live Chat"):
                    _n = int(pd.to_numeric(rc_ch_vol.loc[_ch_key.eq(_ch), "Contacts"], errors="coerce").fillna(0).sum())
                    if _n > 0:
                        _pie_names.append(_ch)
                        _pie_vals.append(_n)
            _pie_total = int(sum(_pie_vals))
            _pie_caption = "Phone and Live Chat contacts · not the 12-channel mix"
            if _pie_total and len(_pie_vals) >= 2:
                _pie_caption = (
                    f"Phone {_pie_vals[0] / _pie_total * 100:.0f}% · "
                    f"Live Chat {_pie_vals[1] / _pie_total * 100:.0f}% of Phone+Chat"
                )
            elif _pie_total and len(_pie_names) == 1:
                _pie_caption = f"{_pie_names[0]} · 100% of Phone+Chat in this filter"
            render_kpi(
                "Contact number by channel",
                f"{_pie_total:,}" if _pie_total else "—",
                _pie_caption,
                "off",
                spark=spark_donut_fig(
                    _pie_names,
                    _pie_vals,
                    legend=True,
                    colors=[
                        CHART_COLORS["qa"] if n == "Phone" else CHART_COLORS["csat"]
                        for n in _pie_names
                    ],
                ) if _pie_vals else None,
                spark_key="ov_spark_ch_pie",
                size="secondary",
            )

        render_rule_heading("Week by week")
        with panel("Week-over-week trend"):
            _plotly_chart(
                weekly_kpi_chart(weekly, height=240),
                key="ov_weekly_full",
                drill="weeks",
            )
            st.caption(
                "QA and CSAT on the left axis, official recontact on the right. "
                "Click a week to filter."
            )

    n_filter_audits = int(len(audits)) if audits is not None else 0
    n_filter_surveys = (
        int(pd.to_numeric(csat["Feedback CNT"], errors="coerce").fillna(0).sum())
        if csat is not None and not csat.empty and "Feedback CNT" in csat.columns
        else 0
    )
    fig_ov_combo_head, fig_ov_combo_tail = split_cr_combo_view(
        scatter_df, top_n=CR_COMBO_TOP_N,
        min_qa_n=CR_COMBO_MIN_QA_N, min_csat_n=RANKING_CSAT_MIN_N,
    )
    fig_ov_combo = kpi_combo_by_cr(
        fig_ov_combo_head, "CR_Lv4",
        title="Performance by contact reason Lv4 (detail)",
        grain="contact reasons Lv4 (detail)",
        top_n=CR_COMBO_TOP_N,
        horizontal=True,
        min_qa_n=CR_COMBO_MIN_QA_N,
        min_csat_n=RANKING_CSAT_MIN_N,
    )
    fig_ov_combo_lv1 = kpi_combo_by_cr(
        lv1_metrics, "CR_Lv1",
        title="Performance by contact reason Lv1 (group)",
        grain="contact reasons Lv1 (group)",
    )

    def extra_ov_sup() -> None:
        n_bar = int(ov_sup["n"].sum()) if not ov_sup.empty and "n" in ov_sup.columns else 0
        st.caption(_supervisor_n_caption(
            n_bar, n_filter_audits, _n_supervisor_teams_under_min(audits, 1),
            min_n=1,
        ))
        render_notes(gap_chip(sup_qa_gap, "supervisor QA"))
        if not ov_sup.empty:
            with st.expander("Supervisor names and volumes"):
                show_df(ov_supervisor_display(ov_sup))

    def extra_ov_weekly() -> None:
        render_notes(weekly_chip(weekly))
        if not weekly.empty:
            with st.expander("Week-over-week numbers"):
                show_df(weekly_display())

    def extra_ov_ch() -> None:
        render_notes(channel_chip(ch_perf))
        if len(req_perf) > 1:
            _plotly_chart(channel_kpi_combo(req_perf), key="ov_req_combo", drill="requester")
            st.caption("Click a requester bar to apply that filter.")

    if sel_country == "All":
        mkt_audits, mkt_csat = audits, csat
    else:
        mkt_audits, _, mkt_csat, _ = apply_filters(
            audits_all, errors_all, csat_all, rc_all,
            {**filters, "country": "All"}, audits_all,
        )
    mkt = market_performance(mkt_audits, mkt_csat, recontact)
    sel_mkt = None if sel_country == "All" else str(sel_country)

    def _mkt_rows(score_col: str, n_col: str, status_col: str, unit: str) -> list[dict]:
        rows: list[dict] = []
        if mkt.empty:
            return rows
        for _, row in mkt.iterrows():
            score = row.get(score_col)
            if pd.isna(score):
                continue
            n_val = int(row[n_col]) if n_col in mkt.columns and pd.notna(row.get(n_col)) else 0
            status = str(row.get(status_col) or "neutral")
            rows.append({
                "code": str(row.get("Country") or ""),
                "name": str(row.get("Country_Name") or row.get("Country") or ""),
                "n": f"{n_val:,} {unit}" if n_val else "",
                "value": _fmt_kpi_pct(score),
                "color": STATUS_COLORS.get(status, STATUS_COLORS["neutral"]),
            })
        return rows

    qa_rows = _mkt_rows("QA_Score", "QA_N", "QA_Score_status", "audits")
    cs_rows = _mkt_rows("CSAT_Score", "CSAT_N", "CSAT_Score_status", "surveys")
    rc_rows = [{
        "code": "SSL",
        "name": "SSL (all markets)",
        "n": "",
        "value": _fmt_kpi_pct(rc_rate),
        "color": STATUS_COLORS.get(rc_light, STATUS_COLORS["neutral"]),
    }]
    mkt_html = (
        '<div class="didi-mkt-stack">'
        + _market_box_html(
            "QA by market", qa_rows,
            footnote="Official QA · mean of audit scores. Goal ≥ 85. DO and PA have no QA.",
            selected=sel_mkt,
        )
        + _market_box_html(
            "CSAT by market", cs_rows,
            footnote="% of surveys rated 4 or 5 stars. Goal ≥ 85%.",
            selected=sel_mkt,
        )
        + _market_box_html(
            "Recontact (SSL)", rc_rows,
            footnote="No country field — region is always SSL. This is the official mix, not a by-market rate.",
        )
        + "</div>"
        )

    render_rule_heading("Performance trends")
    ov_tr_l, ov_tr_r = st.columns(2, gap="medium")
    with ov_tr_l:
        with panel("QA score by day"):
            _plotly_chart(control_i_chart(qa_spc, "Target 85"), key="ov_spc_full", drill="day")
            st.caption("Click a day to apply that filter.")
    with ov_tr_r:
        with panel("QA score histogram"):
            st.plotly_chart(
                qa_histogram_chart(hist_qa) if hist_qa is not None else qa_histogram_chart(pd.DataFrame()),
                width="stretch", config=CHART_CFG, key="ov_hist_full", theme=None,
            )
            st.caption(f"{crit['n_fatal']:,} audits scored 0 · N = {crit['n_audits']:,} audits")

    render_banner(L("section_market"))
    map_col, box_col = st.columns([1.35, 1], gap="medium")
    with map_col:
        with panel("Americas"):
            _plotly_chart(
                americas_map_chart(mkt, selected=sel_mkt),
                key="ov_americas",
                drill="country",
            )
            st.caption(
                "Fill is QA where the market is audited, CSAT for CSAT-only markets (DO, PA). "
                "Click a country to filter. Click again to clear."
            )
    with box_col:
        st.markdown(mkt_html, unsafe_allow_html=True)

    render_banner(L("section_combined"))
    with panel("Performance by contact reason Lv1 (group)"):
        _plotly_chart(fig_ov_combo_lv1, key="ov_combo_lv1", drill="cr_lv1")
        st.caption(
            "Official QA (mean of audit scores), CSAT (4★+5★ / surveys), and recontact "
            "(Σ repeats / Σ contacts) at contact reason Lv1 (group). "
            "QA and recontact inherit Lv1 from the CSAT hierarchy via the Lv4 name. "
            "These are not the same ticket."
        )
    with panel("Performance by contact reason Lv4 (detail)"):
        _plotly_chart(fig_ov_combo, key="ov_combo_lv4", drill="cr")
        st.caption(
            f"Top {CR_COMBO_TOP_N} by survey/contact volume. "
            f"QA bars need ≥{CR_COMBO_MIN_QA_N} audits; CSAT bars need ≥{RANKING_CSAT_MIN_N} surveys. "
            "Sorted by volume, not by the raw file order. Recontact is in the hover, not a third bar. "
            "Click a reason to filter."
        )
        if not fig_ov_combo_tail.empty:
            with st.expander(
                f"Lower-volume contact reasons ({len(fig_ov_combo_tail)} not in the chart)"
            ):
                tail = fig_ov_combo_tail.copy()
                show = pd.DataFrame({"Contact reason Lv4": tail["CR_Lv4"].astype(str)})
                if "QA_Score" in tail.columns:
                    show["QA %"] = tail["QA_Score"].round(1)
                if "QA_N" in tail.columns:
                    show["Audits"] = tail["QA_N"]
                if "CSAT_Score" in tail.columns:
                    show["CSAT %"] = tail["CSAT_Score"].round(1)
                elif "CSAT_Pct" in tail.columns:
                    show["CSAT %"] = tail["CSAT_Pct"].round(1)
                if "Feedback" in tail.columns:
                    show["Surveys"] = tail["Feedback"]
                if "Recontact_Rate" in tail.columns:
                    show["Recontact %"] = tail["Recontact_Rate"].round(2)
                if "Contacts" in tail.columns:
                    show["Contacts"] = tail["Contacts"]
                show_df(show)
                st.caption(
                    "Held out because n is below the chart floor, or the reason is outside the top "
                    f"{CR_COMBO_TOP_N} by volume. Official KPIs at the top of the page still use every row."
                )

    cr_cov = cr_taxonomy_coverage(csat)
    cr_finest = cr_finest_volume(csat, top_n=12)
    cov_col, fine_col = st.columns(2, gap="medium")
    with cov_col:
        with panel("Contact reason classification coverage"):
            st.plotly_chart(
                taxonomy_coverage_chart(cr_cov),
                width="stretch", config=CHART_CFG, key="ov_cr_cover", theme=None,
            )
            st.caption(
                "Share of CSAT surveys that still land in Other / Not mapped at each grain. "
                "When Lv4 and SUB_CR are both Other, that slice cannot be drilled."
            )
    with fine_col:
        with panel("Top contact reasons (SUB_CR)"):
            _plotly_chart(
                pareto_dual_axis(
                    cr_finest, "Cat", "Feedback",
                    title="Top contact reasons (SUB_CR)",
                    value_title="Surveys",
                    sample_unit="surveys",
                ) if not cr_finest.empty else pareto_dual_axis(
                    pd.DataFrame(), "Cat", "Feedback",
                    title="Top contact reasons (SUB_CR)",
                ),
                key="ov_cr_finest",
            )
            st.caption(
                "CSAT survey volume at SUB_CR (finest grain). "
                "If SUB_CR is Other, the bar uses the parent Lv4; if Lv4 is also Other, it uses Lv3. "
                "Not a Lv3-only or Lv4-only chart."
            )

    csat_map = csat_supervisor_mapping(csat, audits)
    n_qa_thin = (
        int((pd.to_numeric(ov_sup["n"], errors="coerce").fillna(0) < SUPERVISOR_GAP_MIN_N).sum())
        if not ov_sup.empty and "n" in ov_sup.columns else 0
    )
    n_cs_thin = (
        int((pd.to_numeric(ov_sup["Feedback"], errors="coerce").fillna(0) < SUPERVISOR_GAP_MIN_N).sum())
        if not ov_sup.empty and "Feedback" in ov_sup.columns else 0
    )
    gqa, gcs = st.columns(2)
    with gqa:
        with panel("Supervisor QA impact Pareto"):
            _plotly_chart(
                supervisor_gap_chart(
                    ov_sup, "Supervisor_ID", "QA_Score", "n",
                    goal=QA_GOAL, title="Supervisor QA impact Pareto", unit="audits",
                    min_n=SUPERVISOR_GAP_MIN_N,
                ),
                key="ov_gap_qa",
                drill="supervisor",
            )
            st.caption(
                f"Bars are gap × audits (how far below 85, weighted by sample). "
                f"The cumulative line shows how much of the deficit the top teams explain. "
                f"{n_qa_thin} supervisor(s) with n < {SUPERVISOR_GAP_MIN_N} audits are held out as insufficient sample. "
                "Click a supervisor to filter."
            )
        render_preview_board(
            [
                {
                    "id": "ov_sup", "btn": "btnch",
                    "title": "Supervisors: QA vs CSAT",
                    "value": f"{ov_sup.iloc[0]['QA_Score']:.1f}%" if not ov_sup.empty else "—",
                    "delta": _n_delta(ov_sup.iloc[0] if not ov_sup.empty else None, "n", unit="audits"),
                    "spark": spark_hbar_fig(
                        ov_sup.head(5)["Supervisor_ID"].astype(str).tolist(),
                        ov_sup.head(5)["QA_Score"].fillna(0).tolist(), unit="%",
                    ) if not ov_sup.empty else None,
                    "fig": lambda: grouped_qa_csat_chart(
                        ov_sup if not ov_sup.empty else ov_sup,
                        "Supervisor_ID", n_col="n", title="Supervisor QA vs CSAT",
                        top_n=None,
                        universe_n=n_filter_audits or None,
                    ),
                    "extra": extra_ov_sup, "drill": "supervisor",
                },
                {
                    "id": "ov_ch", "btn": "btnch",
                    "title": "QA, CSAT and recontact by channel",
                    "value": f"{ch_perf.iloc[0]['Recontact_Rate']:.2f}%" if not ch_perf.empty and pd.notna(ch_perf.iloc[0].get("Recontact_Rate")) else "—",
                    "delta": str(ch_perf.iloc[0]["Segment"])[:42] if not ch_perf.empty else None,
                    "spark": spark_hbar_fig(
                        ch_perf[ch_perf["Segment"] != "Overall"].head(5)["Segment"].astype(str).tolist(),
                        ch_perf[ch_perf["Segment"] != "Overall"].head(5)["Recontact_Rate"].fillna(0).tolist(), unit="%",
                    ) if not ch_perf.empty and (ch_perf["Segment"] != "Overall").any() else None,
                    "fig": lambda: channel_kpi_combo(ch_perf),
                    "extra": extra_ov_ch, "drill": "channel",
                },
            ],
            state_key=f"ov_preview_{_fn}",
            columns=1,
        )
    with gcs:
        with panel("Supervisor CSAT impact Pareto"):
            n_cs = "Feedback" if not ov_sup.empty and "Feedback" in ov_sup.columns else "n"
            _plotly_chart(
                supervisor_gap_chart(
                    ov_sup, "Supervisor_ID", "CSAT_Score", n_cs,
                    goal=CSAT_GOAL, title="Supervisor CSAT impact Pareto", unit="surveys",
                    min_n=SUPERVISOR_GAP_MIN_N,
                ),
                key="ov_gap_csat",
                drill="supervisor",
            )
            st.caption(
                f"Bars are gap × surveys. A 5-point miss on 4,000 surveys outranks an 85-point miss on n=1. "
                f"{n_cs_thin} supervisor(s) with n < {SUPERVISOR_GAP_MIN_N} mapped surveys are held out. "
                "Click a supervisor to filter."
            )
            _render_csat_unmapped_note(csat_map)

    aht_note = (
        "Bars are official QA (mean of audit scores). The line is mean QA Duration in minutes. "
        "Handle time is from audits only — CSAT has no AHT field. Not an official KPI. "
        f"A slice needs ≥{AHT_CR_MIN_AUDITS} audits with Duration."
    )
    with panel("QA and AHT by contact reason Lv1 (group)"):
        _plotly_chart(
            qa_aht_combo(
                aht_cr_lv1, "CR_Lv1",
                title="QA and AHT by contact reason Lv1 (group)",
                top_n=None,
            ),
            key="ov_aht_lv1",
            drill="cr_lv1",
        )
        st.caption(aht_note + " Click a reason to filter.")
    with panel("QA and AHT by contact reason Lv4 (detail)"):
        _plotly_chart(
            qa_aht_combo(
                aht_cr_lv4, "CR_Lv4",
                title="QA and AHT by contact reason Lv4 (detail)",
                top_n=CR_COMBO_TOP_N,
            ),
            key="ov_aht_lv4",
            drill="cr",
        )
        st.caption(aht_note + " Click a reason to filter.")
    with panel("QA and AHT by contact reason SUB_CR"):
        _plotly_chart(
            qa_aht_combo(
                aht_cr_sub, "SUB_CR",
                title="QA and AHT by contact reason SUB_CR",
                top_n=CR_COMBO_TOP_N,
            ),
            key="ov_aht_sub",
            drill="sub_cr",
        )
        st.caption(
            aht_note
            + " If SUB_CR is Other, the bar uses the parent Lv4. Click a reason to filter."
        )
    with st.expander("Week-over-week numbers"):
        show_df(weekly_display())

    with drill(L("panel_actions")):
        render_insight_bar()
        render_action_panel()

    with drill("How the data is sliced"):
        st.markdown("The three sources are **not a single table**. A filter only applies where the column exists.")
        show_df(coverage)
        st.markdown(
            "**Channel:** QA is Phone + Live Chat. Recontact has 12 channels (Self Help dominates the official 5.83%). "
            "When Channel = All, QA is the audited mix and recontact is all 12.\n\n"
            "**Market:** QA and CSAT yes. Recontact region is always SSL — the Market filter does not cut recontact.\n\n"
            "**Supervisor:** QA and CSAT. CSAT uses agent name matched to QA Agent_ID, then that agent’s supervisor. Recontact has no supervisor.\n\n"
            "**Agent:** QA and CSAT. CSAT keeps surveys whose agent name matches the QA Agent_ID. Recontact has no agent field.\n\n"
            "**Contact reason Lv1 (group):** native on CSAT. QA and Recontact inherit it via the contact reason Lv4 (detail) name.\n\n"
            "**Contact reason Lv4 (detail):** all three sources.\n\n"
            "**Tenure:** QA uses the Excel `Tenure` field. CSAT is joined to that same agent tenure by agent name. The CSAT `user_tenure` field is not used. Recontact has none.\n\n"
            "**Business Type:** native on CSAT. QA is cut to contact reason Lv4 names that carry that Business Type in CSAT. Recontact is not cut.\n\n"
            "**Day:** all three sources, each on its own Fecha. QA may have no audits on a CSAT/recontact calendar day."
        )

elif page == "QA Score":
    render_banner(L("section_qa"))
    src_attr = top_attr.rename(columns={"Fail_Count": "Count", "Error_Category": "Cat"}) if not top_attr.empty else top_attr
    src_crit = crit_attr.rename(columns={"Fail_Count": "Count", "Error_Category": "Cat"}) if not crit_attr.empty else crit_attr
    src_qa_cr = qa_cr_fails.rename(columns={"Fail_Count": "Count", "CR_Lv4": "Cat"}) if not qa_cr_fails.empty else qa_cr_fails
    src_qa_sub = qa_sub_fails.rename(columns={"Fail_Count": "Count", "SUB_CR": "Cat"}) if not qa_sub_fails.empty else qa_sub_fails
    qa_roster = qa_agent_roster(audits, errors, min_n=1)
    n_roster = 0 if qa_roster.empty else len(qa_roster)
    n_roster_below = (
        0 if qa_roster.empty else int((qa_roster["QA_Score"] < QA_GOAL).sum())
    )
    qa_fail_top = qa_agent_fail_concentrators(errors, audits)
    n_fail_events, n_fail_audits = fail_event_totals(errors)
    fail_n_note = f"{n_fail_audits:,} audits" if n_fail_audits else None
    fail_kw = dict(
        value_title="Attribute fails",
        sample_unit="attribute fails",
        universe_n=n_fail_events or None,
        n_note=fail_n_note,
    )
    n_filter_audits_qa = int(len(audits)) if audits is not None else 0
    if audits.empty:
        qa_sup_all = pd.DataFrame()
    else:
        qa_sup_all = (
            audits.groupby("Supervisor_ID", as_index=False)
            .agg(QA_Score=("Score_Pct", "mean"), n=("Audit_ID", "count"),
                 Fatal_Rate=("Fatal_Flag", "mean"), Agents=("Agent_ID", "nunique"))
            .sort_values("QA_Score")
        )
    qa_sup = (
        qa_sup_all[qa_sup_all["QA_Score"] < QA_GOAL]
        if (not qa_sup_all.empty and _below_on(_qa_sup_below_k))
        else qa_sup_all
    )
    ch_names, ch_vals = [], []
    for _ch in ("Phone", "Live Chat"):
        _d = ch_qa.get(_ch) or {}
        if _d.get("qa_score") is not None:
            ch_names.append(_ch)
            ch_vals.append(float(_d["qa_score"]))
    aht_r_qa, aht_n_qa = _pair_r(aht_corr, "AHT vs QA", "All")
    if aht_r_qa is None:
        aht_r_qa, aht_n_qa = _pair_r(aht_corr, "QA vs AHT", "All")

    def extra_qa_ch() -> None:
        if len(ch_vals) >= 2:
            low_i = 0 if ch_vals[0] <= ch_vals[1] else 1
            high_i = 1 - low_i
            gap = abs(ch_vals[0] - ch_vals[1])
            tone = "risk" if ch_vals[low_i] < QA_GOAL else "info"
            render_notes({
                "text": (
                    f"{ch_names[low_i]} QA {ch_vals[low_i]:.1f}% is {gap:.1f} points "
                    f"below {ch_names[high_i]}."
                ),
                "tone": tone,
            })
            return
        if ch_vals:
            render_notes(qa_chip(ch_vals[0]))
            return
        render_notes({"text": "No Phone or Live Chat audits in this filter.", "tone": "info"})

    def extra_qa_crit() -> None:
        share = crit.get("pct_fails_critical")
        if share is None:
            render_notes({"text": "No CRITICAL vs Non-critical split in this filter.", "tone": "info"})
            return
        render_notes({"text": f"{float(share):.1f}% of QA fails are CRITICAL.", "tone": "risk"})

    def extra_qa_crit_p() -> None:
        st.caption("CRITICAL attribute fails only. Share is of all attribute fails in this filter.")

    def extra_qa_attr() -> None:
        st.caption(
            "Bars count attribute-fail events. One audit can contribute more than one fail. "
            f"This filter: {n_fail_events:,} attribute fails · {n_fail_audits:,} audits."
        )

    def extra_qa_cr() -> None:
        frame = qa_score_by_cr(
            audits, top_n=None, min_n=1, below_goal_only=_below_on(_qa_cr_below_k),
        )
        if frame.empty:
            render_notes({
                "text": (
                    "No contact reason Lv4 (detail) below QA 85 in this filter."
                    if _below_on(_qa_cr_below_k)
                    else "No contact reason Lv4 (detail) QA scores in this filter."
                ),
                "tone": "info",
            })
            return
        row = frame.iloc[0]
        n = int(row["N"]) if "N" in row and pd.notna(row["N"]) else None
        tone = "risk" if float(row["QA_Score"]) < QA_GOAL else "info"
        n_txt = f" on {n:,} audits" if n is not None else ""
        render_notes({
            "text": f"Lowest bar is {float(row['QA_Score']):.1f}%{n_txt}.",
            "tone": tone,
        })
        st.caption("Official QA is still the mean of Score_Pct. Toggle below 85% only vs every contact reason with ≥1 audit.")

    def extra_qa_sub() -> None:
        frame = qa_score_by_cr(
            audits, top_n=None, min_n=1, cat_col="SUB_CR",
            below_goal_only=_below_on(_qa_sub_below_k),
        )
        if frame.empty:
            render_notes({
                "text": (
                    "No contact reason SUB_CR (finest) below QA 85 in this filter."
                    if _below_on(_qa_sub_below_k)
                    else "No contact reason SUB_CR (finest) QA scores in this filter."
                ),
                "tone": "info",
            })
            return
        row = frame.iloc[0]
        n = int(row["N"]) if "N" in row and pd.notna(row["N"]) else None
        tone = "risk" if float(row["QA_Score"]) < QA_GOAL else "info"
        n_txt = f" on {n:,} audits" if n is not None else ""
        render_notes({
            "text": f"Lowest bar is {float(row['QA_Score']):.1f}%{n_txt}.",
            "tone": tone,
        })
        st.caption(
            "Finest contact reason on QA (auditor-corrected SUB_CR). "
            "Other / Non sub cr falls back to the parent Lv4. Official QA is still the mean of Score_Pct."
        )

    def extra_qa_aht() -> None:
        render_r_box(aht_r_qa, aht_n_qa, "QA vs handle time", audits=volumes.get("evaluations"))
        st.caption(
            "The All bar is not Phone R² plus Chat R². It is one association on the pooled Phone+Chat cloud. "
            "Phone calls are longer by nature, so All can look strongly positive while each channel is flat or negative. "
            "Coach the channel rows, not All."
        )
        render_aht_quality_block("qa_aht", include_qa_scatter=False)

    fig_qa_crit_p = pareto_dual_axis(
        src_crit if not src_crit.empty else pd.DataFrame(),
        "Cat", "Count", title="CRITICAL fails by attribute",
        critical_col="Is_Critical",
        value_title="Attribute fails",
        sample_unit="attribute fails",
        universe_n=int(len(crit_errors)) if crit_errors is not None and not crit_errors.empty else None,
        n_note=(
            f"{int(crit_errors['Audit_ID'].nunique()):,} audits"
            if crit_errors is not None and not crit_errors.empty and "Audit_ID" in crit_errors.columns
            else None
        ),
    )

    def extra_qa_lv1() -> None:
        render_notes(pareto_chip(qa_cr_groups, "CR_Lv1", "Fail_Count", "QA fails") if not qa_cr_groups.empty else {"text": "No contact reason Lv1 (group) fail rows.", "tone": "info"})
        pair = pair_display(qa_cr_pair, "Fail_Count", "Fails")
        if not pair.empty:
            with st.expander("Contact reason Lv4 (detail) inside each Lv1 (group)"):
                show_df(pair)

    def extra_qa_cr_p() -> None:
        st.caption(
            "Pareto of attribute-fail events by contact reason Lv4 (detail). "
            "Phone and Live Chat keep their own attributes."
        )
        _pareto_tail_extra(
            src_qa_cr, "Cat", "Count",
            grain="Lv4 reasons", volume_label="attribute fails",
        )

    def extra_qa_sub_p() -> None:
        st.caption(
            "Pareto of attribute-fail events by contact reason SUB_CR (finest). "
            "If SUB_CR is Other or Non sub cr, the bar uses the parent Lv4 "
            "labeled like 'reason Lv4 (other SUB_CR)'."
        )
        _pareto_tail_extra(
            src_qa_sub, "Cat", "Count",
            grain="SUB_CRs", volume_label="attribute fails",
        )

    def extra_qa_agents() -> None:
        st.caption(
            f"N = {n_filter_audits_qa:,} audits. Official QA is the mean of Score_Pct. "
            "Toggle below 85% only vs every agent with ≥1 audit in this filter."
        )
        if qa_fail_top.empty and qa_roster.empty:
            render_notes({
                "text": "No agent with a QA fail or ≥ 1 audit in this filter.",
                "tone": "info",
            })
            return
        top = qa_fail_top.iloc[0] if not qa_fail_top.empty else None
        top_txt = ""
        if top is not None and int(top.get("Fail_Count") or 0) > 0:
            uniq = int(top["Unique_Fail_Audits"]) if "Unique_Fail_Audits" in top.index and pd.notna(top["Unique_Fail_Audits"]) else None
            uniq_txt = f", {uniq} unique audit{'s' if uniq != 1 else ''} with a fail" if uniq is not None else ""
            n_attr = int(top["N_Attributes"]) if "N_Attributes" in top.index and pd.notna(top["N_Attributes"]) else None
            attr_txt = f", {n_attr} attribute{'s' if n_attr != 1 else ''}" if n_attr is not None else ""
            top_txt = (
                f" Most attribute-fail events sit with {top['Agent_ID']} "
                f"({int(top['Fail_Count']):,} events, {float(top['Fail_Share']):.1f}% of attribute fails"
                f"{uniq_txt}{attr_txt})."
            )
        roster_txt = (
            f"{n_roster_below} of {n_roster} agents in this filter are below QA 85. "
            "The table is grouped by supervisor."
        ) if n_roster else "No agents in this filter."
        render_notes({
            "text": f"{roster_txt}{top_txt}",
            "tone": "risk" if n_roster_below else "ok",
        })
        if qa_roster.empty:
            return
        shown = qa_roster
        if _below_on(_qa_agent_below_k):
            shown = qa_roster[qa_roster["QA_Score"] < QA_GOAL]
        if shown.empty:
            st.caption("No agent below QA 85 in this filter.")
            return
        st.caption(
            "Supervisor repeats on purpose — that is the team. Worst team first, then attribute-fail events. "
            "Fail share is of every attribute fail in this filter, including agents not in the table."
        )
        show_df(qa_agent_roster_display(shown))

    def extra_qa_sup() -> None:
        n_bar = int(qa_sup["n"].sum()) if not qa_sup.empty and "n" in qa_sup.columns else 0
        st.caption(_supervisor_n_caption(
            n_bar, n_filter_audits_qa, _n_supervisor_teams_under_min(audits, 1),
            lowest_first=True,
            min_n=1,
        ))

    qa_cs_r, qa_cs_n = _pair_r(corr_tbl, "QA vs CSAT")
    qa_rc_r, qa_rc_n = _pair_r(corr_tbl, "QA vs Recontact")
    ch_vol_names, ch_vol_vals = [], []
    for _ch in ("Phone", "Live Chat"):
        _d = ch_qa.get(_ch) or {}
        n_ch = int(_d.get("audit_count") or 0)
        if n_ch:
            ch_vol_names.append(_ch)
            ch_vol_vals.append(n_ch)
    fail_list = pd.DataFrame()
    if errors is not None and not errors.empty and "Error_Category" in errors.columns:
        fl = errors.copy()
        if "Is_Critical" in fl.columns:
            fl["Kind"] = fl["Is_Critical"].fillna(False).astype(bool).map({True: "CRITICAL", False: "Non-critical"})
        else:
            fl["Kind"] = "Fail"
        fail_list = (
            fl.groupby(["Kind", "Error_Category"], as_index=False)
            .size()
            .rename(columns={"size": "Fails", "Error_Category": "Attribute"})
            .sort_values(["Kind", "Fails"], ascending=[True, False])
        )
    qa_agents_plot = qa_roster.copy() if not qa_roster.empty else qa_roster
    if not qa_agents_plot.empty and _below_on(_qa_agent_below_k):
        qa_agents_plot = qa_agents_plot[qa_agents_plot["QA_Score"] < QA_GOAL]

    q1, q2, q3 = st.columns(3, gap="medium")
    with q1:
        render_kpi(
            L("kpi_qa"), f"{summary['qa_score']:.2f}%", qa_vs, "normal",
            spark=sparkline_fig(qa_spark_vals, CHART_COLORS["qa"], qa_spark_lbl, "%", "QA %"),
            spark_key="qa_spark_qa",
            caption=qa_disp,
            traffic=qa_light,
        )
    with q2:
        render_kpi(
            L("kpi_evals"), f"{volumes['evaluations']:,}", e_txt, e_dcol,
            spark=sparkbar_fig(vol_series["evals"] or [volumes["evaluations"]], CHART_COLORS["blue"],
                               vol_series.get("evals_labels") or None, "", "Audits"),
            spark_key="qa_spark_evals",
        )
    with q3:
        render_kpi(
            "QA by Special project",
            f"{qa_special.iloc[0]['QA_Score']:.1f}%" if not qa_special.empty else "—",
            _n_delta(qa_special.iloc[0] if not qa_special.empty else None, "n", unit="audits"),
            "off",
            spark=spark_hbar_fig(
                qa_special.head(5)["Special_project"].astype(str).tolist(),
                qa_special.head(5)["QA_Score"].fillna(0).tolist(), unit="%",
            ) if not qa_special.empty else None,
            spark_key="qa_spark_special",
        )

    render_rule_heading("Audits summary")
    as1, as2, as3, as4 = st.columns(4, gap="medium")
    with as1:
        render_kpi(
            L("kpi_critical_rate"), f"{crit['pct_fatal']:.1f}%",
            f"{crit['n_fatal']:,} of {crit['n_audits']:,} audits scored 0",
            "off",
            help_text=L("note_crit_kpi"),
            traffic=_fail_light(crit["n_fatal"], critical=True),
            traffic_label=False,
            size="secondary",
        )
    with as2:
        render_kpi(
            L("kpi_audits_noncrit"), f"{crit['pct_audits_noncrit']:.1f}%",
            f"{crit['n_audits_noncrit']:,} of {crit['n_audits']:,} audits",
            "off",
            help_text=L("note_noncrit_audits"),
            traffic=_fail_light(crit["n_audits_noncrit"], critical=False),
            traffic_label=False,
            size="secondary",
        )
    with as3:
        render_kpi(
            L("kpi_crit_fails"), f"{crit['n_crit_fails']:,}",
            f"{crit['pct_fails_critical']:.1f}% of attribute fails", "off",
            traffic=_fail_light(crit["n_crit_fails"], critical=True),
            traffic_label=False,
            size="secondary",
        )
    with as4:
        render_kpi(
            L("kpi_audits_any_fail"), f"{crit['pct_audits_any_fail']:.1f}%",
            f"{crit['n_audits_any_fail']:,} of {crit['n_audits']:,} audits",
            "off",
            help_text=L("note_any_fail_audits"),
            caption="Unique evaluations with ≥1 attribute fail — not the number of fail marks.",
            traffic=_fail_light(
                crit["n_audits_any_fail"],
                critical=bool(crit.get("n_fatal")),
            ),
            traffic_label=False,
            size="secondary",
        )
    as5, as_right = st.columns([1, 3], gap="medium")
    with as5:
        render_kpi(
            L("kpi_noncrit_fails"),
            f"{crit['n_noncrit_fails']:,}",
            f"{crit['pct_fails_noncritical']:.1f}% of attribute fails",
            "off",
            traffic=_fail_light(crit["n_noncrit_fails"], critical=False),
            traffic_label=False,
            size="secondary",
            spark_key="qa_spark_noncrit_n",
        )
        render_resolution_kpi("qa_spark_resolution")
        render_unresolved_owner_kpi("qa_spark_unresolved")
    with as_right:
        as6, as7, as8 = st.columns(3, gap="medium")
        with as6:
            render_kpi(
                "Audit volume by channel",
                f"{sum(ch_vol_vals):,}" if ch_vol_vals else "—",
                "Phone vs Live Chat audits",
                "off",
                spark=spark_donut_fig(ch_vol_names, ch_vol_vals) if ch_vol_vals else None,
                spark_key="qa_spark_ch_vol",
                size="secondary",
            )
        with as7:
            render_kpi(
                "QA score by channel",
                f"{ch_vals[0]:.1f}%" if ch_vals else "—",
                ch_names[0] if ch_names else None,
                "off",
                spark=spark_hbar_fig(ch_names, ch_vals, unit="%") if ch_vals else None,
                spark_key="qa_spark_ch_score",
                size="secondary",
            )
        with as8:
            render_kpi(
                "QA by Type of audit",
                f"{qa_audit_type.iloc[0]['QA_Score']:.1f}%" if not qa_audit_type.empty else "—",
                _n_delta(qa_audit_type.iloc[0] if not qa_audit_type.empty else None, "n", unit="audits"),
                "off",
                spark=spark_hbar_fig(
                    qa_audit_type.head(5)["Type_of_audit"].astype(str).tolist(),
                    qa_audit_type.head(5)["QA_Score"].fillna(0).tolist(), unit="%",
                ) if not qa_audit_type.empty else None,
                spark_key="qa_spark_type",
                size="secondary",
            )
        with panel("QA by day"):
            _plotly_chart(
                control_i_chart(qa_spc, "Target 85", height=260),
                key="qa_spc_full",
                drill="day",
            )
            st.caption("Click a day to apply that filter.")

    render_rule_heading("Performance trends")
    with panel("QA score histogram"):
        st.plotly_chart(
            qa_histogram_chart(hist_qa) if hist_qa is not None else qa_histogram_chart(pd.DataFrame()),
            width="stretch", config=CHART_CFG, key="qa_hist_full", theme=None,
        )
        st.caption(f"{crit['n_fatal']:,} audits scored 0 · N = {crit['n_audits']:,} audits")

    render_rule_heading("Detail by category")
    det_l, det_r = st.columns(2, gap="medium")
    with det_l:
        with panel("QA by Special project"):
            _plotly_chart(
                score_volume_combo(
                    qa_special if not qa_special.empty else pd.DataFrame(
                        columns=["Special_project", "QA_Score", "n"]
                    ),
                    "Special_project", "QA_Score", "n",
                    goal=QA_GOAL, title="QA by Special project",
                    score_title="QA %", vol_title="Audits", bar_color=CHART_COLORS["qa"],
                ),
                key="qa_special_full",
                drill="special_project",
            )
            st.caption("Click a bar to apply that filter.")
    with det_r:
        with panel("QA by Type of audit"):
            _plotly_chart(
                score_volume_combo(
                    qa_audit_type if not qa_audit_type.empty else pd.DataFrame(
                        columns=["Type_of_audit", "QA_Score", "n"]
                    ),
                    "Type_of_audit", "QA_Score", "n",
                    goal=QA_GOAL, title="QA by Type of audit",
                    score_title="QA %", vol_title="Audits", bar_color=CHART_COLORS["qa"],
                ),
                key="qa_type_full",
                drill="audit_type",
            )
            st.caption("Click a bar to apply that filter.")

    sc1, sc2 = st.columns(2)
    with sc1:
        render_corr_scatter(
            "QA vs CSAT",
            qa_csat_scatter(scatter_df),
            key="qa_qacs_full",
            r_args=(qa_cs_r, qa_cs_n, "QA vs CSAT"),
            r_kwargs={"surveys": volumes.get("surveys"), "audits": volumes.get("evaluations")},
        )
    with sc2:
        render_corr_scatter(
            "QA vs recontact",
            qa_recontact_scatter(scatter_df),
            key="qa_qarc_full",
            r_args=(qa_rc_r, qa_rc_n, "QA vs recontact"),
            r_kwargs={"audits": volumes.get("evaluations")},
        )
    render_r_n_meaning()

    render_preview_board(
        [
            {
                "id": "qa_crit", "kind": "pie", "btn": "btnpie",
                "title": "CRITICAL vs Non-critical",
                "value": f"{crit['pct_fails_critical']:.1f}%",
                "delta": f"{crit['n_crit_fails']:,} CRITICAL fails",
                "spark": spark_donut_fig(
                    ["CRITICAL", "Non-critical"],
                    [crit["n_crit_fails"], crit["n_noncrit_fails"]],
                    legend=True,
                ),
                "fig": critical_split_chart(crit["n_crit_fails"], crit["n_noncrit_fails"]),
                "extra": extra_qa_crit,
                "table": fail_list,
            },
            {
                "id": "qa_crit_p", "btn": "btncr",
                "title": "CRITICAL fails by attribute",
                "value": f"{crit_attr.iloc[0]['Pct_Of_Fails']:.1f}%" if not crit_attr.empty else "—",
                "delta": _n_delta(crit_attr.iloc[0] if not crit_attr.empty else None, "Fail_Count", "Count", unit="fails"),
                "spark": spark_hbar_fig(
                    crit_attr.head(5)["Error_Category"].tolist(),
                    crit_attr.head(5)["Pct_Of_Fails"].fillna(0).tolist(), unit="%",
                ) if not crit_attr.empty else None,
                "fig": fig_qa_crit_p,
                "extra": extra_qa_crit_p,
            },
            {
                "id": "qa_attr", "btn": "btncr",
                "title": "QA fails by attribute",
                "value": f"{top_attr.iloc[0]['Pct_Of_Fails']:.1f}%" if not top_attr.empty else "—",
                "delta": _n_delta(top_attr.iloc[0] if not top_attr.empty else None, "Fail_Count", "Count", unit="fails"),
                "spark": spark_hbar_fig(
                    top_attr.head(5)["Error_Category"].tolist(), top_attr.head(5)["Pct_Of_Fails"].fillna(0).tolist(), unit="%",
                ) if not top_attr.empty else None,
                "fig": pareto_dual_axis(
                    src_attr if not src_attr.empty else pd.DataFrame(),
                    "Cat", "Count", title="QA fails by attribute",
                    critical_col="Is_Critical", **fail_kw,
                ),
                "extra": extra_qa_attr,
            },
            {
                "id": "qa_cr", "btn": "btncr",
                "title": "QA by contact reason Lv4 (detail)",
                "value": f"{qa_cr.iloc[0]['QA_Score']:.1f}%" if not qa_cr.empty else "—",
                "delta": _n_delta(qa_cr.iloc[0] if not qa_cr.empty else None, "N", unit="audits"),
                "spark": spark_hbar_fig(
                    qa_cr.head(5)["CR_Lv4"].tolist(), qa_cr.head(5)["QA_Score"].fillna(0).tolist(), unit="%",
                ) if not qa_cr.empty else None,
                "fig": lambda: qa_by_cr_chart(
                    qa_score_by_cr(
                        audits, top_n=None, min_n=1,
                        below_goal_only=_below_on(_qa_cr_below_k),
                    ),
                ),
                "toolbar": lambda: _below_target_toggle(_qa_cr_below_k, goal=QA_GOAL, metric="QA"),
                "below_key": _qa_cr_below_k,
                "extra": extra_qa_cr,
                "drill": "cr",
            },
            {
                "id": "qa_sub", "btn": "btncr",
                "title": "QA by contact reason SUB_CR (finest)",
                "value": f"{qa_sub.iloc[0]['QA_Score']:.1f}%" if not qa_sub.empty else "—",
                "delta": _n_delta(qa_sub.iloc[0] if not qa_sub.empty else None, "N", unit="audits"),
                "spark": spark_hbar_fig(
                    qa_sub.head(5)["SUB_CR"].tolist(), qa_sub.head(5)["QA_Score"].fillna(0).tolist(), unit="%",
                ) if not qa_sub.empty else None,
                "fig": lambda: qa_by_cr_chart(
                    qa_score_by_cr(
                        audits, top_n=None, min_n=1, cat_col="SUB_CR",
                        below_goal_only=_below_on(_qa_sub_below_k),
                    ),
                    cat_col="SUB_CR", grain="contact reason SUB_CR (finest)",
                ),
                "toolbar": lambda: _below_target_toggle(_qa_sub_below_k, goal=QA_GOAL, metric="QA"),
                "below_key": _qa_sub_below_k,
                "extra": extra_qa_sub,
                "drill": "sub_cr",
            },
            {
                "id": "qa_lv1", "btn": "btngroup",
                "title": "QA fails by contact reason Lv1 (group)",
                "value": f"{qa_cr_groups.iloc[0]['Pct']:.1f}%" if not qa_cr_groups.empty else "—",
                "delta": _n_delta(qa_cr_groups.iloc[0] if not qa_cr_groups.empty else None, "Fail_Count", unit="fails"),
                "spark": spark_hbar_fig(
                    qa_cr_groups.head(5)["CR_Lv1"].tolist(), qa_cr_groups.head(5)["Pct"].fillna(0).tolist(), unit="%",
                ) if not qa_cr_groups.empty else None,
                "fig": cr_group_hbar(
                    qa_cr_groups, "CR_Lv1", "Fail_Count", "Pct", "Attribute fails",
                    title="QA fails by contact reason Lv1 (group)",
                    universe_n=n_fail_events or None,
                    n_note=fail_n_note,
                    sample_unit="attribute fails",
                ),
                "extra": extra_qa_lv1,
                "drill": "cr_lv1",
            },
            {
                "id": "qa_cr_p", "btn": "btncr",
                "title": "QA fail Pareto by contact reason Lv4",
                "value": f"{qa_cr_fails.iloc[0]['Fail_Count']:,.0f}" if not qa_cr_fails.empty else "—",
                "delta": _n_delta(qa_cr_fails.iloc[0] if not qa_cr_fails.empty else None, "Fail_Count", unit="fails"),
                "spark": spark_hbar_fig(
                    qa_cr_fails.head(5)["CR_Lv4"].tolist(), qa_cr_fails.head(5)["Fail_Count"].fillna(0).tolist(),
                ) if not qa_cr_fails.empty else None,
                "fig": lambda: pareto_dual_axis(
                    src_qa_cr if not src_qa_cr.empty else pd.DataFrame(),
                    "Cat", "Count",
                    title="QA fail Pareto by contact reason Lv4 (detail)",
                    bucket_other=True,
                    **fail_kw,
                ),
                "extra": extra_qa_cr_p,
                "drill": "cr",
            },
            {
                "id": "qa_sub_p", "btn": "btncr",
                "title": "QA fail Pareto by SUB_CR",
                "value": f"{qa_sub_fails.iloc[0]['Fail_Count']:,.0f}" if not qa_sub_fails.empty else "—",
                "delta": _n_delta(qa_sub_fails.iloc[0] if not qa_sub_fails.empty else None, "Fail_Count", unit="fails"),
                "spark": spark_hbar_fig(
                    qa_sub_fails.head(5)["SUB_CR"].tolist(), qa_sub_fails.head(5)["Fail_Count"].fillna(0).tolist(),
                ) if not qa_sub_fails.empty else None,
                "fig": lambda: pareto_dual_axis(
                    src_qa_sub if not src_qa_sub.empty else pd.DataFrame(),
                    "Cat", "Count",
                    title="QA fail Pareto by contact reason SUB_CR (finest)",
                    bucket_other=True,
                    **fail_kw,
                ),
                "extra": extra_qa_sub_p,
                "drill": "sub_cr",
            },
            {
                "id": "qa_ten", "btn": "btngroup",
                "title": "QA by agent tenure",
                "value": f"{tenure_qa.iloc[0]['QA_Score']:.1f}%" if not tenure_qa.empty else "—",
                "delta": _n_delta(tenure_qa.iloc[0] if not tenure_qa.empty else None, "QA_Evaluations", "n", unit="audits"),
                "spark": spark_hbar_fig(
                    tenure_qa.head(5)["Tenure_Cohort"].astype(str).tolist(), tenure_qa.head(5)["QA_Score"].fillna(0).tolist(), unit="%",
                ) if not tenure_qa.empty else None,
                "fig": score_volume_combo(
                    tenure_qa, "Tenure_Cohort", "QA_Score", "QA_Evaluations",
                    goal=QA_GOAL, title="QA by agent tenure",
                    score_title="QA %", vol_title="Audits", bar_color=CHART_COLORS["qa"],
                ) if not tenure_qa.empty else score_volume_combo(
                    pd.DataFrame(columns=["Tenure_Cohort", "QA_Score", "QA_Evaluations"]),
                    "Tenure_Cohort", "QA_Score", "QA_Evaluations",
                    goal=QA_GOAL, title="QA by agent tenure",
                    score_title="QA %", vol_title="Audits", bar_color=CHART_COLORS["qa"],
                ),
                "insight": tenure_chip(tenure_qa, "QA_Score", "Tenure_Cohort", QA_GOAL),
                "drill": "tenure",
            },
            {
                "id": "qa_agents", "btn": "btndaily",
                "title": "QA by agent",
                "value": f"{n_roster_below} / {n_roster}" if n_roster else "0",
                "delta": "below 85" if _below_on(_qa_agent_below_k) else "all agents in this filter",
                "spark": spark_hbar_fig(
                    qa_agents_plot.nsmallest(5, "QA_Score")["Agent_ID"].astype(str).tolist(),
                    qa_agents_plot.nsmallest(5, "QA_Score")["QA_Score"].fillna(0).tolist(),
                    unit="%",
                ) if not qa_agents_plot.empty else None,
                "fig": lambda: hbar_score_chart(
                    (
                        qa_roster[qa_roster["QA_Score"] < QA_GOAL]
                        if (not qa_roster.empty and _below_on(_qa_agent_below_k))
                        else qa_roster
                    ),
                    "Agent_ID", "QA_Score", "Audit_Count",
                    title="QA by agent",
                    extra_col="Supervisor_ID" if not qa_roster.empty and "Supervisor_ID" in qa_roster.columns else None,
                    universe_n=n_filter_audits_qa or None,
                ),
                "toolbar": lambda: _below_target_toggle(_qa_agent_below_k, goal=QA_GOAL, metric="QA"),
                "below_key": _qa_agent_below_k,
                "extra": extra_qa_agents,
                "drill": "agent",
            },
            {
                "id": "qa_sup", "btn": "btnch",
                "title": "QA by supervisor",
                "value": f"{qa_sup.iloc[0]['QA_Score']:.1f}%" if not qa_sup.empty else "—",
                "delta": _n_delta(qa_sup.iloc[0] if not qa_sup.empty else None, "n", unit="audits"),
                "spark": spark_hbar_fig(
                    qa_sup.head(5)["Supervisor_ID"].astype(str).tolist(), qa_sup.head(5)["QA_Score"].fillna(0).tolist(), unit="%",
                ) if not qa_sup.empty else None,
                "fig": lambda: hbar_score_chart(
                    (
                        qa_sup_all[qa_sup_all["QA_Score"] < QA_GOAL]
                        if (not qa_sup_all.empty and _below_on(_qa_sup_below_k))
                        else qa_sup_all
                    ),
                    "Supervisor_ID", "QA_Score", "n",
                    title="QA by supervisor",
                    universe_n=n_filter_audits_qa or None,
                ),
                "toolbar": lambda: _below_target_toggle(_qa_sup_below_k, goal=QA_GOAL, metric="QA"),
                "below_key": _qa_sup_below_k,
                "extra": extra_qa_sup,
                "drill": "supervisor",
            },
            {
                "id": "qa_aht", "btn": "btnscat",
                "title": "Handle time vs quality",
                "value": f"{float(aht_r_qa)**2:.2f}" if aht_r_qa is not None else "—",
                "delta": f"N = {aht_n_qa} shared Lv4" if aht_n_qa else None,
                "spark": spark_r_fig(aht_r_qa),
                "fig": qa_aht_scatter(aht_points),
                "extra": extra_qa_aht,
                "drill": "cr",
            },
        ],
        state_key=f"qa_preview_{_fn}",
        columns=2,
    )

    has_notes = (
        audits is not None
        and not audits.empty
        and "Auditor_Outcome" in audits.columns
        and "Dissatisfaction_Flag" in audits.columns
    )
    if has_notes:
        qa_outcome = qa_auditor_outcome(audits)
        qa_proc = qa_process_adherence_summary(audits)
        qa_dissat = qa_dissatisfaction_split(audits)
        qa_owner = qa_dissatisfaction_owner(audits)
        qa_sub_r = qa_dissatisfaction_subreason(audits)
        qa_48h = qa_repeat_48h(audits)
        qa_48h_ch = qa_repeat_48h_by_channel(audits)
        qa_quotes = qa_auditor_quotes(audits)
        n_yes = int(qa_dissat.loc[qa_dissat["Dissatisfaction_Flag"].eq("Yes"), "n"].sum()) if not qa_dissat.empty else 0
        pct_yes = float(qa_dissat.loc[qa_dissat["Dissatisfaction_Flag"].eq("Yes"), "Pct"].sum()) if not qa_dissat.empty else 0.0
        n_rep = int(qa_48h.loc[qa_48h["Repeat_48h"].eq("Repeat (≥2)"), "n"].sum()) if not qa_48h.empty else 0
        pct_rep = (n_rep / int(len(audits)) * 100) if len(audits) else 0.0
        dissat_colors = [
            STATUS_COLORS["red"] if str(v) == "Yes" else ("#64748B" if str(v) == "No" else STATUS_COLORS["amber"])
            for v in (qa_dissat["Dissatisfaction_Flag"].tolist() if not qa_dissat.empty else [])
        ]

        def extra_qa_outcome() -> None:
            st.caption(L("sub_qa_outcome"))
            st.caption(L("note_qa_notes"))

        def extra_qa_dissat() -> None:
            st.caption(L("sub_qa_dissat"))
            if not qa_owner.empty:
                _plotly_chart(
                    cr_group_hbar(
                        qa_owner, "Dissatisfaction_Owner", "n", "Pct", "Audits",
                        title="Dissatisfaction owner",
                        sample_unit="audits",
                    ),
                    key=f"qa_notes_owner_{_fn}",
                    config=_DIALOG_CHART_CFG,
                )
            if not qa_sub_r.empty:
                _plotly_chart(
                    cr_group_hbar(
                        qa_sub_r, "Dissatisfaction_Subreason", "n", "Pct", "Audits",
                        title="Dissatisfaction sub-reason",
                        sample_unit="audits",
                    ),
                    key=f"qa_notes_sub_{_fn}",
                    config=_DIALOG_CHART_CFG,
                )
            if qa_quotes.empty:
                st.caption("No auditor notes on dissatisfied audits in this filter.")
            else:
                st.caption(
                    "Sample notes on dissatisfied audits. 5-whys text is AI-generated and is not a dissatisfaction rate."
                )
                show_df(qa_quotes)

        def extra_qa_48h() -> None:
            st.caption(L("sub_qa_48h"))
            if not qa_48h_ch.empty:
                _plotly_chart(
                    count_stack_chart(
                        qa_48h_ch, "Repeat_48h", "Channel", "n",
                        title="Same-CR contacts in last 48h by channel",
                        cat_order=list(REPEAT_48H_ORDER),
                        series_order=["Phone", "Live Chat"],
                    ),
                    key=f"qa_notes_48h_ch_{_fn}",
                    config=_DIALOG_CHART_CFG,
                )
            st.caption(
                "Repeat (≥2) is the only bucket that means a prior same-CR contact. "
                "Do not compare this share with official recontact."
            )

        render_rule_heading(L("panel_qa_notes"))
        st.caption(L("note_qa_notes"))
        render_preview_board(
            [
                {
                    "id": "qa_outcome", "btn": "btnch",
                    "title": L("panel_qa_outcome"),
                    "value": f"{qa_proc['pct_not_followed']:.1f}%",
                    "delta": f"{qa_proc['n_not_followed']:,} did not follow process",
                    "spark": spark_hbar_fig(
                        qa_outcome["Auditor_Outcome"].tolist(),
                        qa_outcome["n"].fillna(0).tolist(),
                    ) if not qa_outcome.empty else None,
                    "fig": score_volume_combo(
                        qa_outcome, "Auditor_Outcome", "QA_Score", "n",
                        goal=QA_GOAL, title="QA by solution and process",
                        score_title="QA %", vol_title="Audits",
                        bar_color=CHART_COLORS["qa"],
                        sample_unit="audits",
                    ),
                    "extra": extra_qa_outcome,
                },
                {
                    "id": "qa_dissat", "kind": "pie", "btn": "btnpie",
                    "title": L("panel_qa_dissat"),
                    "value": f"{pct_yes:.1f}%",
                    "delta": f"{n_yes:,} of {int(len(audits)):,} audits",
                    "spark": spark_donut_fig(
                        qa_dissat["Dissatisfaction_Flag"].tolist(),
                        qa_dissat["n"].fillna(0).tolist(),
                        legend=True,
                        colors=dissat_colors,
                    ) if not qa_dissat.empty else None,
                    "fig": share_donut_chart(
                        qa_dissat, "Dissatisfaction_Flag", "n",
                        title="Auditor-tagged dissatisfaction",
                        colors=dissat_colors,
                    ),
                    "extra": extra_qa_dissat,
                },
                {
                    "id": "qa_48h", "btn": "btndaily",
                    "title": L("panel_qa_48h"),
                    "value": f"{pct_rep:.1f}%",
                    "delta": f"{n_rep:,} repeat (≥2)",
                    "spark": spark_hbar_fig(
                        qa_48h["Repeat_48h"].tolist(),
                        qa_48h["n"].fillna(0).tolist(),
                    ) if not qa_48h.empty else None,
                    "fig": score_volume_combo(
                        qa_48h, "Repeat_48h", "QA_Score", "n",
                        goal=QA_GOAL, title="QA by same-CR contacts in last 48h",
                        score_title="QA %", vol_title="Audits",
                        bar_color=CHART_COLORS["qa"],
                        sample_unit="audits",
                    ),
                    "extra": extra_qa_48h,
                },
            ],
            state_key=f"qa_notes_{_fn}",
            columns=3,
        )

    render_methodology()

elif page == "CSAT":
    render_banner(L("section_csat"))
    ck1, ck2, ck3, ck4 = st.columns(4, gap="medium")
    with ck1:
        render_kpi(
            L("kpi_csat"), f"{summary['csat']:.2f}%", cs_vs, "normal",
            spark=sparkline_fig(csat_spark_vals, CHART_COLORS["csat"], csat_spark_lbl, "%", "CSAT %"),
            spark_key="csat_spark",
            traffic=cs_light,
        )
    with ck2:
        render_kpi(
            L("kpi_surveys"), f"{volumes['surveys']:,}", s_txt, s_dcol,
            spark=sparkbar_fig(vol_series["surveys"] or [volumes["surveys"]], CHART_COLORS["blue"],
                               vol_series.get("surveys_labels") or None, "", "Surveys"),
            spark_key="csat_spark_vol",
        )
    with ck3:
        render_kpi(
            "4–5 star surveys",
            f"{_star_hi:,}",
            (
                f"{(_star_hi / _star_n * 100):.1f}% of surveys"
                if _star_n else "% of surveys rated 4 or 5 stars"
            ),
            "off",
            spark=spark_donut_fig(
                _stars_hi.sort_values("Count", ascending=False)["Rating"].astype(str).tolist(),
                _stars_hi.sort_values("Count", ascending=False)["Count"].fillna(0).tolist(),
            ) if not _stars_hi.empty else None,
            spark_key="csat_spark_stars_hi",
        )
    with ck4:
        render_kpi(
            "1–3 star surveys",
            f"{_star_lo:,}",
            (
                f"{(_star_lo / _star_n * 100):.1f}% of surveys"
                if _star_n else "surveys rated 1 to 3 stars"
            ),
            "off",
            spark=spark_donut_fig(
                _stars_lo.sort_values("Count", ascending=False)["Rating"].astype(str).tolist(),
                _stars_lo.sort_values("Count", ascending=False)["Count"].fillna(0).tolist(),
            ) if not _stars_lo.empty else None,
            spark_key="csat_spark_stars_lo",
        )
    csat_below = (
        float(hist_csat.loc[hist_csat["CSAT_Score"] < CSAT_GOAL, "Share_Pct"].sum())
        if not hist_csat.empty else None
    )
    csat_day_col, csat_hist_col = st.columns(2, gap="medium")
    with csat_day_col:
        with panel("CSAT by day"):
            _plotly_chart(control_i_chart(csat_spc, "Target 85"), key="csat_spc_full", drill="day")
            st.caption("Click a day to apply that filter.")
    with csat_hist_col:
        with panel("CSAT score histogram"):
            st.plotly_chart(
                csat_histogram_chart(hist_csat) if hist_csat is not None and not hist_csat.empty else csat_histogram_chart(pd.DataFrame()),
                width="stretch", config=CHART_CFG, key="csat_hist_full", theme=None,
            )
            st.caption(
                (
                    f"{csat_below:.0f}% of surveys below 85 · N = {volumes['surveys']:,} surveys"
                    if csat_below is not None else f"N = {volumes['surveys']:,} surveys"
                )
            )

    render_banner("Customer comments")
    st.caption(
        f"{comments['n_real']:,} surveys with a readable open_question comment. "
        "Positive vs negative uses that full set. Themes use only the 1–3★ surveys that left a comment."
    )
    if comments["n_real"] <= 0:
        st.caption("No comments with text in this filter.")
    else:
        pie_col, theme_col = st.columns(2)
        with pie_col:
            with panel("Positive vs negative"):
                st.plotly_chart(
                    square_pie_fig(manner_pie_chart(
                        comments["polarity"],
                        "Positive vs negative",
                        colors=[
                            "#D64545" if s == "Negative" else "#2E9B57"
                            for s in comments["polarity"]["Slice"].astype(str)
                        ],
                    )),
                    width="stretch", config=CHART_CFG, key=f"voc_polarity_{_fn}", theme=None,
                )
                st.caption(
                    f"{comments['n_negative']:,} negative · {comments['n_positive']:,} positive "
                    f"of {comments['n_real']:,} surveys with comments. "
                    f"{comments['n_from_text']:,} from the words; stars only if the text is unclear. "
                    "The Other placeholder is skipped."
                )
        with theme_col:
            with panel("Themes in 1–3 star comments"):
                if voc.empty:
                    st.caption("No classifiable 1–3★ comments in this filter.")
                else:
                    st.plotly_chart(
                        voc_bar_chart(voc), width="stretch", config=CHART_CFG,
                        key=f"voc_themes_{_fn}", theme=None,
                    )
                    render_notes(voc_chip(voc))
                    low = int(voc.iloc[0]["Total_Low"]) if "Total_Low" in voc.columns else 0
                    surveys = int(voc.iloc[0]["Total_Low_Surveys"]) if "Total_Low_Surveys" in voc.columns else 0
                    tagged = int(voc.iloc[0]["Total_Tagged"]) if "Total_Tagged" in voc.columns else 0
                    if surveys > 0:
                        st.caption(
                            f"{low:,} of {surveys:,} 1–3★ surveys left a comment. "
                            f"{tagged:,} of those comments had a classifiable theme."
                        )
                    elif low > 0 and tagged < low:
                        st.caption(f"{tagged:,} of {low:,} 1–3★ comments had a classifiable theme.")

    ten_plot = ov_ten_csat.copy()
    if not ten_plot.empty and "Tenure_Cohort" in ten_plot.columns:
        ten_plot = ten_plot.rename(columns={"Tenure_Cohort": "Tenure"})
    csat_rc_r, csat_rc_n = _pair_r(corr_tbl, "CSAT vs Recontact")
    aht_cs_r, aht_cs_n = _pair_r(aht_corr, "AHT vs CSAT", "All")
    csat_roster = csat_agent_roster(csat, audits, min_n=1)
    n_csat_roster = 0 if csat_roster.empty else len(csat_roster)
    n_csat_below = (
        0 if csat_roster.empty else int((csat_roster["CSAT_Score"] < CSAT_GOAL).sum())
    )
    csat_agents_plot = csat_roster.copy() if not csat_roster.empty else csat_roster
    if not csat_agents_plot.empty and _below_on(_csat_agent_below_k):
        csat_agents_plot = csat_agents_plot[csat_agents_plot["CSAT_Score"] < CSAT_GOAL]

    def extra_csat_seg() -> None:
        if csat_seg.empty:
            render_notes({"text": "Not enough surveys to segment CSAT.", "tone": "info"})
            return
        worst = csat_seg.sort_values("CSAT_Score").iloc[0]
        render_notes(rate_chip(worst["Segment"], float(worst["CSAT_Score"]), CSAT_GOAL, lower_better=False))

    def extra_csat_agents() -> None:
        st.caption(
            "Official CSAT by agent · 4★+5★ / surveys. "
            "Toggle below 85% only vs every agent with ≥1 survey in this filter."
        )
        if csat_roster.empty:
            render_notes({
                "text": "No CSAT agents in this filter.",
                "tone": "info",
            })
            return
        mapped = int((~csat_roster["Supervisor_ID"].eq(CSAT_UNMAPPED_SUPERVISOR)).sum())
        n_floor = "≥1 survey"
        render_notes({
            "text": (
                f"{n_csat_below} of {n_csat_roster} agents with {n_floor} are below CSAT 85. "
                f"{mapped} match a QA supervisor."
            ),
            "tone": "risk" if n_csat_below else "ok",
        })
        shown = csat_roster
        if _below_on(_csat_agent_below_k):
            shown = csat_roster[csat_roster["CSAT_Score"] < CSAT_GOAL]
        if shown.empty:
            st.caption(
                "No agent below CSAT 85 in this filter."
            )
            return
        st.caption(
            "Official CSAT is 4★+5★ / Feedback CNT (ratio of sums). "
            "Supervisor is the QA Supervisor_ID matched by agent name (Agent 238 and 238 are the same person). "
            "CSAT has no native supervisor field — remaining unmatched agents stay as Not mapped to a QA supervisor."
        )
        show_df(csat_agent_roster_display(shown))

    def _csat_sup_plot() -> pd.DataFrame:
        frame = csat_by_supervisor(
            csat, audits, min_n=1, top_n=None,
            below_goal_only=_below_on(_csat_sup_below_k),
        )
        if frame.empty or "Supervisor_ID" not in frame.columns:
            return frame
        return frame.loc[~frame["Supervisor_ID"].eq(CSAT_UNMAPPED_SUPERVISOR)].copy()

    def extra_csat_sup() -> None:
        below = _below_on(_csat_sup_below_k)
        st.caption(
            "Official CSAT by supervisor · agent name matched to QA. "
            + (
                "Filter on: every mapped supervisor below CSAT 85% with ≥1 survey."
                if below else "Every mapped supervisor with ≥1 survey is shown."
            )
            + " Unmapped surveys are not mixed into the red bars."
        )
        _render_csat_unmapped_note(csat_supervisor_mapping(csat, audits))

    def extra_csat_cr(level: str) -> None:
        grain = {
            "lv1": "Lv1 (group)",
            "lv4": "Lv4 (detail)",
            "sub": "SUB_CR (finest)",
        }.get(level, level)
        st.caption(
            f"Official CSAT by contact reason {grain} · 4★+5★ / surveys. "
            "N is all star ratings in the slices on this chart (the CSAT denominator). "
            "It is not the unsatisfied count — that is the Pareto. "
            "If this grain is Other, the bar uses the parent reason "
            "(for example Cancellation rules Lv3 (other lv4)). "
            "Toggle below 85% only vs every contact reason with ≥1 survey."
        )

    def extra_csat_pareto_lv4() -> None:
        st.caption(
            "Unsatisfied = Feedback − 4★/5★ surveys. "
            "If Lv4 is Other but Lv3 is specific, the bar is labeled like "
            "'Cancellation rules Lv3 (other lv4)'. "
            "Other at Lv1-Lv4 (no parent) means this file has Other at every contact-reason level "
            "for those surveys — there is no Lv3 to show."
        )
        _pareto_tail_extra(
            csat_unsat, "CR_Lv4", "Unsatisfied",
            grain="Lv4 reasons", volume_label="unsatisfied surveys",
        )

    def extra_csat_pareto_sub() -> None:
        st.caption(
            "N is 1–3★ surveys only (Feedback − 4★/5★) across every SUB_CR in the filter, "
            "including slices still on goal. That is why it will not match CSAT by SUB_CR, "
            "whose N is all star ratings in the bars on that chart. "
            "If SUB_CR is Other, the bar shows the parent Lv4 as 'reason Lv4 (other SUB_CR)'."
        )
        _pareto_tail_extra(
            csat_unsat_sub, "SUB_CR", "Unsatisfied",
            grain="SUB_CRs", volume_label="unsatisfied surveys",
        )

    csc1, csc2 = st.columns(2)
    with csc1:
        render_corr_scatter(
            "CSAT vs handle time",
            aht_metric_scatter(
                aht_joined, "CSAT_Pct", y_title="CSAT %", title="CSAT vs AHT",
                y_goal=CSAT_GOAL,
                empty_text=aht_overlap_empty_text(
                    aht_cs_n, "CSAT",
                    surveys=volumes.get("surveys"),
                    audits=volumes.get("evaluations"),
                    min_audits=AHT_CR_MIN_AUDITS,
                ),
            ),
            key="csat_aht_full",
            r_args=(aht_cs_r, aht_cs_n, "CSAT vs handle time"),
            r_kwargs={"surveys": volumes.get("surveys"), "audits": volumes.get("evaluations")},
        )
    with csc2:
        render_corr_scatter(
            "CSAT vs recontact",
            csat_recontact_scatter(scatter_df),
            key="csat_csrc_full",
            r_args=(csat_rc_r, csat_rc_n, "CSAT vs recontact"),
            r_kwargs={"surveys": volumes.get("surveys")},
        )

    render_preview_board(
        [
            {
                "id": "csat_ten", "btn": "btngroup",
                "title": "CSAT by agent tenure",
                "value": f"{ten_plot.iloc[0]['CSAT_Score']:.1f}%" if not ten_plot.empty else "—",
                "delta": _n_delta(ten_plot.iloc[0] if not ten_plot.empty else None, "Feedback", unit="surveys"),
                "spark": spark_hbar_fig(
                    ten_plot.head(5)["Tenure"].tolist(), ten_plot.head(5)["CSAT_Score"].fillna(0).tolist(), unit="%",
                ) if not ten_plot.empty else None,
                "fig": score_volume_combo(
                    ten_plot if not ten_plot.empty else pd.DataFrame(columns=["Tenure", "CSAT_Score", "Feedback"]),
                    "Tenure", "CSAT_Score", "Feedback",
                    goal=CSAT_GOAL, title="CSAT by agent tenure",
                    score_title="CSAT %", vol_title="Surveys", bar_color=CHART_COLORS["csat"],
                ),
                "insight": tenure_chip(ten_plot, "CSAT_Score", "Tenure", CSAT_GOAL),
                "extra": lambda: st.caption(
                    "Agent tenure from QA, matched by CSAT agent name to QA Agent_ID. "
                    "Surveys whose agent has no QA tenure stay out of this chart."
                ),
                "drill": "tenure",
            },
            {
                "id": "csat_agents", "btn": "btndaily",
                "title": "CSAT by agent",
                "value": f"{n_csat_below} / {n_csat_roster}" if n_csat_roster else "0",
                "delta": "below 85" if _below_on(_csat_agent_below_k) else "all agents in this filter",
                "spark": spark_hbar_fig(
                    csat_agents_plot.head(5)["Agent"].astype(str).tolist(),
                    csat_agents_plot.head(5)["CSAT_Score"].fillna(0).tolist(),
                    unit="%",
                ) if not csat_agents_plot.empty else None,
                "fig": lambda: score_volume_combo(
                    (
                        csat_roster[csat_roster["CSAT_Score"] < CSAT_GOAL]
                        if (not csat_roster.empty and _below_on(_csat_agent_below_k))
                        else csat_roster
                    ) if not csat_roster.empty else pd.DataFrame(columns=["Agent", "CSAT_Score", "Feedback"]),
                    "Agent", "CSAT_Score", "Feedback",
                    goal=CSAT_GOAL, title="CSAT by agent",
                    score_title="CSAT %", vol_title="Surveys", bar_color=CHART_COLORS["csat"],
                    force_horizontal=True,
                ),
                "toolbar": lambda: _below_target_toggle(_csat_agent_below_k, goal=CSAT_GOAL, metric="CSAT"),
                "below_key": _csat_agent_below_k,
                "extra": extra_csat_agents,
                "drill": "agent",
            },
            {
                "id": "csat_sup", "btn": "btnch",
                "title": "CSAT by supervisor",
                "value": f"{csat_scr_sup.iloc[0]['CSAT_Score']:.1f}%" if not csat_scr_sup.empty else "—",
                "delta": _n_delta(csat_scr_sup.iloc[0] if not csat_scr_sup.empty else None, "Feedback", unit="surveys"),
                "spark": spark_hbar_fig(
                    csat_scr_sup.head(5)["Supervisor_ID"].astype(str).tolist(),
                    csat_scr_sup.head(5)["CSAT_Score"].fillna(0).tolist(),
                    unit="%",
                ) if not csat_scr_sup.empty else None,
                "fig": lambda: score_volume_combo(
                    _csat_sup_plot(),
                    "Supervisor_ID", "CSAT_Score", "Feedback",
                    goal=CSAT_GOAL, title="CSAT by supervisor",
                    score_title="CSAT %", vol_title="Surveys", bar_color=CHART_COLORS["csat"],
                    force_horizontal=True,
                ),
                "toolbar": lambda: _below_target_toggle(_csat_sup_below_k, goal=CSAT_GOAL, metric="CSAT"),
                "below_key": _csat_sup_below_k,
                "extra": extra_csat_sup,
                "drill": "supervisor",
            },
            {
                "id": "csat_lv1", "btn": "btngroup",
                "title": "CSAT by contact reason Lv1",
                "value": f"{csat_scr_lv1.iloc[0]['CSAT_Score']:.1f}%" if not csat_scr_lv1.empty else "—",
                "delta": _n_delta(csat_scr_lv1.iloc[0] if not csat_scr_lv1.empty else None, "Feedback", unit="surveys"),
                "spark": spark_hbar_fig(
                    csat_scr_lv1.head(5)["CR_Lv1"].astype(str).tolist(),
                    csat_scr_lv1.head(5)["CSAT_Score"].fillna(0).tolist(),
                    unit="%",
                ) if not csat_scr_lv1.empty else None,
                "fig": lambda: score_volume_combo(
                    csat_score_by_cr(
                        csat, level="lv1", lookup=cr_lookup, min_n=1, top_n=None,
                        below_goal_only=_below_on(_csat_lv1_below_k),
                    ) if not csat.empty else pd.DataFrame(columns=["CR_Lv1", "CSAT_Score", "Feedback"]),
                    "CR_Lv1", "CSAT_Score", "Feedback",
                    goal=CSAT_GOAL, title="CSAT by contact reason Lv1 (group)",
                    score_title="CSAT %", vol_title="Surveys", bar_color=CHART_COLORS["csat"],
                    force_horizontal=True,
                ),
                "toolbar": lambda: _below_target_toggle(_csat_lv1_below_k, goal=CSAT_GOAL, metric="CSAT"),
                "below_key": _csat_lv1_below_k,
                "extra": lambda: extra_csat_cr("lv1"),
                "drill": "cr_lv1",
            },
            {
                "id": "csat_lv4", "btn": "btncr",
                "title": "CSAT by contact reason Lv4",
                "value": f"{csat_scr_lv4.iloc[0]['CSAT_Score']:.1f}%" if not csat_scr_lv4.empty else "—",
                "delta": _n_delta(csat_scr_lv4.iloc[0] if not csat_scr_lv4.empty else None, "Feedback", unit="surveys"),
                "spark": spark_hbar_fig(
                    csat_scr_lv4.head(5)["CR_Lv4"].astype(str).tolist(),
                    csat_scr_lv4.head(5)["CSAT_Score"].fillna(0).tolist(),
                    unit="%",
                ) if not csat_scr_lv4.empty else None,
                "fig": lambda: score_volume_combo(
                    csat_score_by_cr(
                        csat, level="lv4", min_n=1, top_n=None,
                        below_goal_only=_below_on(_csat_lv4_below_k),
                    ) if not csat.empty else pd.DataFrame(columns=["CR_Lv4", "CSAT_Score", "Feedback"]),
                    "CR_Lv4", "CSAT_Score", "Feedback",
                    goal=CSAT_GOAL, title="CSAT by contact reason Lv4 (detail)",
                    score_title="CSAT %", vol_title="Surveys", bar_color=CHART_COLORS["csat"],
                    force_horizontal=True,
                ),
                "toolbar": lambda: _below_target_toggle(_csat_lv4_below_k, goal=CSAT_GOAL, metric="CSAT"),
                "below_key": _csat_lv4_below_k,
                "extra": lambda: extra_csat_cr("lv4"),
                "drill": "cr",
            },
            {
                "id": "csat_sub", "btn": "btncr",
                "title": "CSAT by contact reason SUB_CR",
                "value": f"{csat_scr_sub.iloc[0]['CSAT_Score']:.1f}%" if not csat_scr_sub.empty else "—",
                "delta": _n_delta(csat_scr_sub.iloc[0] if not csat_scr_sub.empty else None, "Feedback", unit="surveys"),
                "spark": spark_hbar_fig(
                    csat_scr_sub.head(5)["SUB_CR"].astype(str).tolist(),
                    csat_scr_sub.head(5)["CSAT_Score"].fillna(0).tolist(),
                    unit="%",
                ) if not csat_scr_sub.empty else None,
                "fig": lambda: score_volume_combo(
                    csat_score_by_cr(
                        csat, level="sub", min_n=1, top_n=None,
                        below_goal_only=_below_on(_csat_sub_below_k),
                    ) if not csat.empty else pd.DataFrame(columns=["SUB_CR", "CSAT_Score", "Feedback"]),
                    "SUB_CR", "CSAT_Score", "Feedback",
                    goal=CSAT_GOAL, title="CSAT by contact reason SUB_CR (finest)",
                    score_title="CSAT %", vol_title="Surveys", bar_color=CHART_COLORS["csat"],
                    force_horizontal=True,
                    sample_unit="surveys (all star ratings)",
                ),
                "toolbar": lambda: _below_target_toggle(_csat_sub_below_k, goal=CSAT_GOAL, metric="CSAT"),
                "below_key": _csat_sub_below_k,
                "extra": lambda: extra_csat_cr("sub"),
                "drill": "sub_cr",
            },
            {
                "id": "csat_pareto_lv4", "btn": "btncr",
                "title": "CSAT unsatisfied Pareto · Lv4",
                "value": f"{int(csat_unsat.iloc[0]['Unsatisfied']):,}" if not csat_unsat.empty else "—",
                "delta": str(csat_unsat.iloc[0]["CR_Lv4"])[:36] if not csat_unsat.empty else None,
                "spark": spark_hbar_fig(
                    csat_unsat.head(5)["CR_Lv4"].astype(str).tolist(),
                    csat_unsat.head(5)["Unsatisfied"].fillna(0).tolist(),
                ) if not csat_unsat.empty else None,
                "fig": lambda: pareto_dual_axis(
                    csat_unsat.rename(columns={"CR_Lv4": "Cat"}) if not csat_unsat.empty else pd.DataFrame(),
                    "Cat", "Unsatisfied",
                    title="CSAT unsatisfied Pareto by contact reason Lv4 (detail)",
                    value_title="Unsatisfied surveys",
                    sample_unit="unsatisfied (1–3★) surveys",
                    universe_n=int(csat_unsat["Unsatisfied"].sum()) if not csat_unsat.empty else None,
                    bucket_other=True,
                ),
                "extra": extra_csat_pareto_lv4,
                "drill": "cr",
            },
            {
                "id": "csat_pareto_sub", "btn": "btncr",
                "title": "CSAT unsatisfied Pareto · SUB_CR",
                "value": f"{int(csat_unsat_sub.iloc[0]['Unsatisfied']):,}" if not csat_unsat_sub.empty else "—",
                "delta": str(csat_unsat_sub.iloc[0]["SUB_CR"])[:36] if not csat_unsat_sub.empty else None,
                "spark": spark_hbar_fig(
                    csat_unsat_sub.head(5)["SUB_CR"].astype(str).tolist(),
                    csat_unsat_sub.head(5)["Unsatisfied"].fillna(0).tolist(),
                ) if not csat_unsat_sub.empty else None,
                "fig": lambda: pareto_dual_axis(
                    csat_unsat_sub.rename(columns={"SUB_CR": "Cat"}) if not csat_unsat_sub.empty else pd.DataFrame(),
                    "Cat", "Unsatisfied",
                    title="CSAT unsatisfied Pareto by contact reason SUB_CR (finest)",
                    value_title="Unsatisfied surveys",
                    sample_unit="unsatisfied (1–3★) surveys",
                    universe_n=int(csat_unsat_sub["Unsatisfied"].sum()) if not csat_unsat_sub.empty else None,
                    bucket_other=True,
                ),
                "extra": extra_csat_pareto_sub,
                "drill": "sub_cr",
            },
            {
                "id": "csat_bt", "btn": "btnscope",
                "title": "CSAT by Business Type",
                "value": f"{csat_bt.iloc[0]['CSAT_Score']:.1f}%" if not csat_bt.empty else "—",
                "delta": _n_delta(csat_bt.iloc[0] if not csat_bt.empty else None, "Feedback", unit="surveys"),
                "spark": spark_hbar_fig(
                    csat_bt.head(5)["Business_Type"].astype(str).tolist(), csat_bt.head(5)["CSAT_Score"].fillna(0).tolist(), unit="%",
                ) if not csat_bt.empty else None,
                "fig": score_volume_combo(
                    csat_bt if not csat_bt.empty else pd.DataFrame(columns=["Business_Type", "CSAT_Score", "Feedback"]),
                    "Business_Type", "CSAT_Score", "Feedback",
                    goal=CSAT_GOAL, title="CSAT by Business Type",
                    score_title="CSAT %", vol_title="Surveys", bar_color=CHART_COLORS["csat"],
                ),
                "drill": "business_type",
            },
        ],
        state_key=f"csat_preview_{_fn}",
        columns=2,
    )

elif page == "Recontact":
    render_banner(L("section_recontact"))
    rk1, rk2, rk3, rk4 = st.columns(4)
    with rk1:
        render_kpi(
            L("kpi_recontact"), f"{rc_rate:.2f}%", rc_vs, "inverse",
            spark=sparkline_fig(rc_spark_vals, CHART_COLORS["recontact"], rc_spark_lbl, "%", "Rate %"),
            spark_key="rc_spark",
            traffic=rc_light,
        )
    with rk2:
        render_kpi(
            L("kpi_fcr"), f"{fcr_rate:.2f}%",
            fcr_vs,
            "off",
            spark=sparkline_fig(fcr_spark_vals, CHART_COLORS["qa"], rc_spark_lbl, "%", "FCR %"),
            spark_key="rc_spark_fcr",
            help_text="FCR is 100 minus this page’s recontact rate. The business case scores recontact (≤5.44%), not FCR.",
            caption="Companion to recontact. No CX Quality target.",
        )
    with rk3:
        render_kpi(
            L("kpi_contacts"), f"{volumes['contacts']:,}", c_txt, c_dcol,
            spark=sparkbar_fig(vol_series["contacts"] or [volumes["contacts"]], CHART_COLORS["blue"],
                               vol_series.get("contacts_labels") or None, "", "Contacts"),
            spark_key="rc_spark_vol",
        )
    with rk4:
        render_kpi(
            L("kpi_recontacts"), f"{volumes.get('recontacts', 0):,}", r_txt, r_dcol,
            spark=sparkbar_fig(
                vol_series.get("recontacts") or [volumes.get("recontacts", 0)],
                CHART_COLORS["recontact"],
                vol_series.get("recontacts_labels") or None, "", "Repeats",
            ),
            spark_key="rc_spark_repeats",
            caption="Σ Recontact Volume · numerator of the official rate.",
        )

    with panel("Recontact by day"):
        _plotly_chart(control_i_chart(rc_spc, "Target 5.44"), key="rc_spc_full", drill="day")
        st.caption("Click a day to apply that filter.")

    render_banner(L("panel_rc_channel"))
    with panel("Contacts, repeats, and rate by channel"):
        if rc_ch_tbl.empty:
            st.caption("No recontact rows in this filter.")
        else:
            _plotly_chart(
                recontact_channel_combo_chart(rc_ch_tbl),
                key="rc_ch_combo",
                drill="channel",
            )
            st.caption("Click a channel bar to apply that filter. Rate is Repeats / Contacts (ratio of sums), not an average of the Rate % column.")
            show_df(channel_mix_display(rc_ch_tbl))
            st.caption(
                "Official recontact is Σ Repeats / Σ Contacts across these rows. Do not average the Rate % column. "
                "Self Help is most of the contacts at a low rate, so the official mix is not the Phone or Live Chat rate. "
                "Only Phone and Live Chat also appear in QA and CSAT. FCR is 100 minus this mix — there is no FCR target."
            )

    src_rc = rc_cr.rename(columns={"Recontacts": "Count", "CR_Lv4": "Cat"}) if not rc_cr.empty else rc_cr
    rc_universe = (
        int(pd.to_numeric(recontact["Recontact Volume"], errors="coerce").fillna(0).sum())
        if recontact is not None and not recontact.empty and "Recontact Volume" in recontact.columns
        else 0
    )
    fig_rc_cr_combo = recontact_cr_combo_chart(rc_cr, bar_color=CHART_COLORS["blue"])
    fig_rc_sub = recontact_cr_combo_chart(
        rc_sub, cat_col="SUB_CR",
        title="Repeated contacts and rate by contact reason SUB_CR",
        bar_color=CHART_COLORS["blue"],
    )
    fig_rc_lv1 = recontact_cr_combo_chart(
        rc_cr_groups, cat_col="CR_Lv1",
        title="Recontact by contact reason Lv1 (group)",
        bar_color=CHART_COLORS["blue"],
    )
    fig_rc_scope = recontact_scope_chart(rc_scope if sel_channel == "All" else pd.DataFrame())
    fig_rc_ch = (
        pareto_dual_axis(
            rc_ch_vol, "Cat", "Count", title="Repeat volume by channel",
            value_title="Repeats", sample_unit="repeats",
            universe_n=rc_universe or None,
        )
        if not rc_ch_vol.empty else pareto_dual_axis(pd.DataFrame(), "Cat", "Count", title="Repeat volume by channel")
    )
    fig_rc_spc = control_i_chart(rc_spc, "Target 5.44")
    fig_rc_aht = aht_metric_scatter(
        aht_joined, "Recontact_Rate",
        y_title="Recontact rate %",
        title="Recontact vs AHT",
        y_goal=RECONTACT_GOAL,
        lower_better=True,
        empty_text=aht_overlap_empty_text(
            int(aht_joined[["AHT_min", "Recontact_Rate"]].dropna().shape[0])
            if aht_joined is not None and not aht_joined.empty
            and "AHT_min" in aht_joined.columns and "Recontact_Rate" in aht_joined.columns
            else 0,
            "recontact",
            audits=volumes.get("evaluations"),
            min_audits=AHT_CR_MIN_AUDITS,
        ),
    )

    mix_top = rc_cr.iloc[0] if not rc_cr.empty else None
    sub_top = rc_sub.iloc[0] if not rc_sub.empty else None
    ch_top = rc_ch_vol.iloc[0] if not rc_ch_vol.empty else None
    lv1_top = rc_cr_groups.iloc[0] if not rc_cr_groups.empty else None
    sh_share = dilution.get("share") if isinstance(dilution, dict) else None

    def _pair_r(tbl: pd.DataFrame, pair: str, slice_name: str | None = None):
        if tbl is None or tbl.empty or "Pair" not in tbl.columns:
            return None, 0
        sub = tbl[tbl["Pair"] == pair]
        if slice_name and "Slice" in sub.columns:
            hit = sub[sub["Slice"] == slice_name]
            if not hit.empty:
                sub = hit
        if sub.empty:
            return None, 0
        row = sub.iloc[0]
        n = int(row["N_CR"]) if "N_CR" in row and pd.notna(row["N_CR"]) else 0
        r = row["Pearson_r"] if "Pearson_r" in row else None
        return (float(r) if pd.notna(r) else None), n

    qa_r, qa_n = _pair_r(corr_tbl, "QA vs Recontact")
    aht_r, aht_n = _pair_r(aht_corr, "AHT vs Recontact", "All")

    def extra_rc_donut() -> None:
        st.caption("Bars are Σ Recontact Volume. The line is Σ Repeats / Σ Contacts for that contact reason Lv4 (detail), not an average of row rates.")
        render_notes(pareto_chip(rc_cr, "CR_Lv4", "Recontacts", "repeat volume") if not rc_cr.empty else None)

    def extra_rc_sub() -> None:
        st.caption(
            "Recontact has no SUB_CR field. Bars are the official Lv4 repeat volume "
            "split by CSAT survey mix inside that Lv4. The rate is still Σ Repeats / Σ Contacts "
            "at Lv4 (ratio of sums), not a new formula. If SUB_CR is Other, the bar uses the parent Lv4."
        )
        render_notes(pareto_chip(rc_sub, "SUB_CR", "Recontacts", "repeat volume") if not rc_sub.empty else None)

    def extra_rc_scope() -> None:
        render_notes(fcr_scope_chip(
            fcr_rate, fcr_audited if sel_channel == "All" else None, sh_share, rc_repeats,
        ))

    def extra_rc_ch() -> None:
        if ch_top is None:
            render_notes({"text": "No channel rows in this filter.", "tone": "info"})
            return
        share = (float(ch_top["Count"]) / float(rc_ch_vol["Count"].sum()) * 100) if rc_ch_vol["Count"].sum() else 0
        render_notes({"text": f"{ch_top['Cat']} is {share:.0f}% of recontact volume.", "tone": "risk"})

    def extra_rc_cr() -> None:
        render_notes(pareto_chip(src_rc if src_rc is not None else pd.DataFrame(), "Cat", "Count", "recontacts"))

    def extra_rc_lv1() -> None:
        extra = None
        if not rc_cr_pair.empty and "Recontact_Rate" in rc_cr_pair.columns:
            extra = {
                "Rate": rc_cr_pair["Recontact_Rate"].map(lambda v: f"{v:.2f}%" if pd.notna(v) else "—"),
            }
        pair = pair_display(rc_cr_pair, "Recontacts", "Volume", extra)
        if not pair.empty:
            with st.expander("Contact reason Lv4 (detail) inside each Lv1 (group)"):
                show_df(pair)

    def extra_rc_aht() -> None:
        render_r_box(aht_r, aht_n, "AHT vs recontact")

    scope_names, scope_vals = [], []
    if sel_channel == "All" and not rc_scope.empty:
        scope_names = ["Official", "Excl. Self Help", "Phone + Chat"]
        scope_vals = [float(v) if pd.notna(v) else 0.0 for v in rc_scope.sort_values("Scope_Order")["Rate"].head(3)]

    render_preview_board(
        [
            {
                "id": "rc_donut",
                "btn": "btncr",
                "title": L("panel_rc_donut"),
                "value": f"{mix_top['Pct']:.1f}%" if mix_top is not None else "—",
                "delta": _n_delta(mix_top, "Recontacts", unit="repeats"),
                "spark": spark_hbar_fig(
                    rc_cr.head(5)["CR_Lv4"].tolist(),
                    rc_cr.head(5)["Recontacts"].fillna(0).tolist(),
                ) if not rc_cr.empty else None,
                "fig": fig_rc_cr_combo,
                "extra": extra_rc_donut,
                "drill": "cr",
            },
            {
                "id": "rc_sub",
                "btn": "btncr",
                "title": L("panel_rc_sub"),
                "value": f"{sub_top['Pct']:.1f}%" if sub_top is not None else "—",
                "delta": _n_delta(sub_top, "Recontacts", unit="repeats"),
                "spark": spark_hbar_fig(
                    rc_sub.head(5)["SUB_CR"].astype(str).tolist(),
                    rc_sub.head(5)["Recontacts"].fillna(0).tolist(),
                ) if not rc_sub.empty else None,
                "fig": fig_rc_sub,
                "extra": extra_rc_sub,
                "drill": "sub_cr",
            },
            {
                "id": "rc_scope",
                "btn": "btnscope",
                "title": L("panel_rc_scope"),
                "value": f"{rc_rate:.2f}%",
                "delta": rc_vs,
                "delta_color": "inverse",
                "spark": spark_hbar_fig(scope_names, scope_vals, unit="%") if scope_vals else None,
                "fig": fig_rc_scope,
                "extra": extra_rc_scope,
            },
            {
                "id": "rc_ch_pareto",
                "btn": "btnch",
                "title": L("panel_rc_channel_pareto"),
                "value": f"{(float(ch_top['Count']) / float(rc_ch_vol['Count'].sum()) * 100):.1f}%" if ch_top is not None and rc_ch_vol["Count"].sum() else "—",
                "delta": _n_delta(ch_top, "Count", unit="repeats"),
                "spark": spark_hbar_fig(
                    rc_ch_vol.head(5)["Cat"].tolist(),
                    (rc_ch_vol.head(5)["Count"] / rc_ch_vol["Count"].sum() * 100).tolist(),
                    unit="%",
                ) if not rc_ch_vol.empty else None,
                "fig": fig_rc_ch,
                "extra": extra_rc_ch,
                "drill": "channel",
            },
            {
                "id": "rc_cr_lv1",
                "btn": "btngroup",
                "title": L("panel_cr_group_rc"),
                "value": f"{lv1_top['Pct']:.1f}%" if lv1_top is not None else "—",
                "delta": _n_delta(lv1_top, "Recontacts", "Contacts", unit="repeats"),
                "spark": spark_hbar_fig(
                    rc_cr_groups.head(5)["CR_Lv1"].tolist(), rc_cr_groups.head(5)["Pct"].tolist(), unit="%",
                ) if not rc_cr_groups.empty else None,
                "fig": fig_rc_lv1,
                "extra": extra_rc_lv1,
                "drill": "cr_lv1",
            },
            {
                "id": "rc_aht",
                "btn": "btnscat",
                "title": L("panel_aht_rc"),
                "value": f"{float(aht_r)**2:.2f}" if aht_r is not None else "—",
                "delta": f"N = {aht_n} shared Lv4" if aht_n else None,
                "spark": spark_r_fig(aht_r),
                "fig": fig_rc_aht,
                "extra": extra_rc_aht,
                "drill": "cr",
            },
        ],
        state_key=f"rc_preview_{_fn}",
        columns=2,
    )

elif page == "Alerts":
    tickets_key = f"tickets_{_fn}"
    if tickets_key not in st.session_state:
        st.session_state[tickets_key] = []
    tickets = st.session_state[tickets_key]
    q4_key = f"hub_q4_only_{_fn}"
    pipe_key = f"watch_pipe_{_fn}"
    pipe_filter = st.session_state.get(pipe_key)

    def _next_ticket_n() -> int:
        return len(tickets) + 1

    qa_q = qa_coaching_queue(agents_below_qa_goal(audits, min_n=RANKING_QA_MIN_N, below_goal_only=True))
    team_view = sel_supervisor != "All"
    qa_agents_view = qa_q_agents.copy() if qa_q_agents is not None and not qa_q_agents.empty else pd.DataFrame()
    csat_agents_view = csat_q_agents.copy() if csat_q_agents is not None and not csat_q_agents.empty else pd.DataFrame()
    if team_view and not qa_agents_view.empty:
        qa_agents_view = qa_agents_view[qa_agents_view["Supervisor_ID"].astype(str) == str(sel_supervisor)]
    if team_view and not csat_agents_view.empty:
        csat_agents_view = csat_agents_view[csat_agents_view["Supervisor_ID"].astype(str) == str(sel_supervisor)]
    qa_sum_view = quartile_band_summary(qa_agents_view) if team_view else qa_q_sum
    csat_sum_view = quartile_band_summary(csat_agents_view) if team_view else csat_q_sum

    people = people_watchlist(
        qa_mix, csat_mix, qa_q_agents, csat_q_agents,
        q4_only=bool(st.session_state.get(q4_key)),
        q4_share_alert=SUPERVISOR_Q4_SHARE_ALERT,
    )
    watch = annotate_watch_pipeline(people, tickets)
    shown = watch
    if not watch.empty and pipe_filter in {"active", "progress", "closed"}:
        shown = watch[watch["Pipeline"] == pipe_filter]
    n_active = 0 if watch.empty else int((watch["Pipeline"] == "active").sum())
    n_prog = sum(1 for t in tickets if t.status != "Closed")
    n_closed = sum(1 for t in tickets if t.status == "Closed")
    desk_hex = {
        "QA": CHART_COLORS["qa"],
        "CSAT": CHART_COLORS["csat"],
        "Recontact": CHART_COLORS["recontact"],
    }

    qa_floor = f"n≥{RANKING_QA_MIN_N} audits"
    cs_floor = f"n≥{RANKING_CSAT_MIN_N} surveys"
    h1, h2, h3 = st.columns(3)
    with h1:
        render_kpi(
            "QA · Q4",
            f"Q4 · {int(qa_sum_view.get('q4') or 0)} agents",
            caption=(
                f"{int(qa_sum_view.get('q4') or 0)} of {int(qa_sum_view.get('ranked') or 0)} "
                f"ranked agents ({qa_floor}) in the bottom 25% of this filter."
            ),
            spark=sparkbar_fig(
                [int((qa_sum_view.get("bands") or {}).get(q, {}).get("n") or 0) for q in ("Q1", "Q2", "Q3", "Q4")],
                STATUS_COLORS["red"], ["Q1", "Q2", "Q3", "Q4"], "", "Agents",
            ),
            spark_key="hub_spark_qa_q",
            size="secondary",
        )
    with h2:
        render_kpi(
            "CSAT · Q4",
            f"Q4 · {int(csat_sum_view.get('q4') or 0)} agents",
            caption=(
                f"{int(csat_sum_view.get('q4') or 0)} of {int(csat_sum_view.get('ranked') or 0)} "
                f"ranked agents ({cs_floor}) in the bottom 25% of this filter."
            ),
            spark=sparkbar_fig(
                [int((csat_sum_view.get("bands") or {}).get(q, {}).get("n") or 0) for q in ("Q1", "Q2", "Q3", "Q4")],
                CHART_COLORS["csat"], ["Q1", "Q2", "Q3", "Q4"], "", "Agents",
            ),
            spark_key="hub_spark_cs_q",
            size="secondary",
        )
    with h3:
        render_kpi(
            L("kpi_recontact"), f"{rc_rate:.2f}%", rc_vs, "inverse",
            traffic=rc_light,
            size="secondary",
            caption="Operation-level only. Recontact has no agent or supervisor field.",
        )
    st.caption(
        "Q4 = bottom 25% of this filter, even if every score is above 85. "
        "Quartile edges move with the filter — they are not the 85 goal. "
        "Official QA (mean Score_Pct) and CSAT (4★+5★ / Feedback) on the operation strip "
        "are team/operation means. Talent mix is who sits in each band. "
        "Recontact / FCR are not scored by agent."
    )

    render_banner("Who is in each quartile")
    qleft, qright = st.columns(2)
    with qleft:
        with panel("QA agents"):
            _plotly_chart(
                quartile_count_chart(qa_sum_view, title="QA agents by quartile"),
                key="hub_qa_qcount",
            )
            render_quartile_range_cards(qa_sum_view, metric="QA")
            render_quartile_bands(qa_sum_view)
            st.caption("Q1 is the top 25% of official QA in this filter. Names are a sample of each band.")
    with qright:
        with panel("CSAT agents"):
            _plotly_chart(
                quartile_count_chart(csat_sum_view, title="CSAT agents by quartile"),
                key="hub_cs_qcount",
            )
            render_quartile_range_cards(csat_sum_view, metric="CSAT")
            render_quartile_bands(csat_sum_view)
            st.caption("Official CSAT is 4★+5★ / Feedback (ratio of sums). No recontact-by-agent chart.")

    render_banner("Supervisor talent mix")
    st.toggle(
        "Q4-heavy teams only",
        key=q4_key,
        help="Supervisors with a high share of company-Q4 agents, or in the worst talent-mix quartile.",
    )
    q4_only = bool(st.session_state.get(q4_key))
    mix_view = qa_mix.copy() if qa_mix is not None and not qa_mix.empty else pd.DataFrame()
    if not mix_view.empty and q4_only:
        mix_view = mix_view[
            mix_view["Requires_Review"].fillna(False).astype(bool)
            | mix_view["Talent_Quartile"].astype(str).eq("Q4")
        ]
    if team_view and not mix_view.empty:
        mix_view = mix_view[mix_view["Supervisor_ID"].astype(str) == str(sel_supervisor)]

    if team_view:
        st.caption(
            f"Team {sel_supervisor}: agents placed in company QA quartiles (this filter). "
            "Official team QA can still be on goal when several agents sit in Q4."
        )
        if st.button("← All supervisors", key=f"hub_back_sup_{_fn}", width="stretch"):
            _set_people_filter("supervisor", None)
        if qa_agents_view.empty:
            st.caption("No ranked QA agents for this supervisor in the current filter.")
        else:
            band_cols = st.columns(4)
            for col, q in zip(band_cols, ("Q1", "Q2", "Q3", "Q4")):
                sub = qa_agents_view[qa_agents_view["Quartile"].astype(str).eq(q)]
                with col:
                    st.markdown(
                        f'<p class="didi-qcol-h">{q} · {len(sub)}</p>',
                        unsafe_allow_html=True,
                    )
                    if sub.empty:
                        st.caption("—")
                        continue
                    for _, row in sub.head(8).iterrows():
                        agent = _cell_str(row.get("Agent_ID"), "—")
                        qa_txt = _fmt(row.get("QA_Score"), 1, "%")
                        on = str(sel_agent) == agent
                        tone = "red" if q == "Q4" else ("amber" if q == "Q3" else "green")
                        with st.container(border=True, key=_next_didi_key(f"didi_sup_{tone}")):
                            st.markdown(
                                f'<p class="didi-sup-head didi-sup-head--{tone}">{html_escape(agent)}</p>',
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                f'<p class="didi-sup-find">QA {qa_txt} · {_cell_str(row.get("QA_n"), "0")} audits</p>',
                                unsafe_allow_html=True,
                            )
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.button(
                                    "Clear agent" if on else "Open agent",
                                    key=f"hub_ag_{agent}_{_fn}",
                                    width="stretch",
                                ):
                                    _set_people_filter("agent", None if on else agent)
                            with b2:
                                draft = make_agent_ticket(agent, pd.Series(row), max(_next_ticket_n(), 1))
                                if st.button("🎫 Create ticket", key=f"tk_ag_{agent}_{_fn}", width="stretch"):
                                    tickets.append(make_agent_ticket(agent, pd.Series(row), _next_ticket_n()))
                                    st.session_state[tickets_key] = tickets
                                    st.rerun()
                                st.download_button(
                                    "✉️ Email draft",
                                    data=draft.email_body,
                                    file_name=f"{agent.replace(' ', '_')}_coaching.txt",
                                    mime="text/plain",
                                    key=f"em_ag_{agent}_{_fn}",
                                    width="stretch",
                                )
                    extra_n = int(len(sub) - 8)
                    if extra_n > 0:
                        st.caption(f"+{extra_n} more in {q}")
    else:
        st.caption(
            "Each bar is that TL’s ranked agents split into company Q1–Q4 (Option A talent mix). "
            "Click a supervisor to see the team. Official QA/CSAT means are separate from this mix."
        )
        _plotly_chart(
            supervisor_mix_chart(mix_view, title="QA talent mix by supervisor"),
            key="hub_qa_mix",
            drill="supervisor",
        )
        if not mix_view.empty:
            top = mix_view.head(4)
            for _, row in top.iterrows():
                sup = _cell_str(row.get("Supervisor_ID"), "—")
                n_q4 = int(row.get("Q4_Agents") or 0)
                n_ranked = int(row.get("Ranked_Agents") or 0)
                review = _as_bool(row.get("Requires_Review"))
                qa_txt = _fmt(row.get("QA_Score"), 1, "%")
                cs_txt = _fmt(row.get("CSAT_Score"), 1, "%")
                tone = "red" if review or _cell_str(row.get("Talent_Quartile")) == "Q4" else "amber"
                team = agents_for_supervisor(qa_q_agents, sup)
                qrow = qa_q[qa_q["Supervisor_ID"].astype(str) == sup] if not qa_q.empty else pd.DataFrame()
                with st.container(border=True, key=_next_didi_key(f"didi_sup_{tone}")):
                    st.markdown(
                        f'<p class="didi-sup-head didi-sup-head--{tone}">{html_escape(sup)}</p>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<p class="didi-coach-copy">{html_escape(sup)}: {n_q4} of {n_ranked} ranked '
                        "agents are in company Q4 (bottom 25%). Official QA for the team can still be on goal.</p>",
                        unsafe_allow_html=True,
                    )
                    render_quartile_pill(
                        row.get("Q1_pct"), row.get("Q2_pct"),
                        row.get("Q3_pct"), row.get("Q4_pct"),
                    )
                    st.markdown(
                        f'<p class="didi-hub-muted">Official QA {qa_txt} · CSAT {cs_txt} · '
                        f"talent mix is not the contractual KPI.</p>",
                        unsafe_allow_html=True,
                    )
                    if review:
                        share = _fmt(row.get("Q4_Share"), 0, "%")
                        st.markdown(
                            '<div class="didi-hub-flag">'
                            f"{html_escape(share)} of this TL’s ranked agents "
                            "are in company Q4. Auto-tickets need manager review."
                            "</div>",
                            unsafe_allow_html=True,
                        )
                    if st.button("Open team", key=f"hub_sup_{sup}_{_fn}", width="stretch"):
                        _set_people_filter("supervisor", sup)
                    b1, b2 = st.columns(2)
                    src = qrow.iloc[0] if not qrow.empty else pd.Series({
                        "Agents": n_ranked,
                        "Audits": int(row.get("n") or 0),
                        "Worst_QA": team["QA_Score"].min() if not team.empty and "QA_Score" in team.columns else None,
                        "Feedback": row.get("Feedback"),
                        "CSAT_Score": row.get("CSAT_Score"),
                        "Ranked_Agents": n_ranked,
                    })
                    with b1:
                        if review:
                            st.caption("Ticket locked — manager review.")
                        elif st.button("🎫 Create ticket", key=f"tk_qa_{sup}_{_fn}", width="stretch"):
                            if _as_bool(row.get("CSAT_below")) and not _as_bool(row.get("QA_below")):
                                tickets.append(make_csat_ticket(sup, src, team, _next_ticket_n()))
                            else:
                                tickets.append(make_qa_ticket(sup, src, team, _next_ticket_n()))
                            st.session_state[tickets_key] = tickets
                            st.rerun()
                    with b2:
                        if review:
                            st.caption("Email after review.")
                        else:
                            draft = (
                                make_csat_ticket(sup, src, team, max(_next_ticket_n(), 1))
                                if _as_bool(row.get("CSAT_below")) and not _as_bool(row.get("QA_below"))
                                else make_qa_ticket(sup, src, team, max(_next_ticket_n(), 1))
                            )
                            st.download_button(
                                "✉️ Email draft",
                                data=draft.email_body,
                                file_name=f"{sup.replace(' ', '_')}_coaching.txt",
                                mime="text/plain",
                                key=f"em_qa_{sup}_{_fn}",
                                width="stretch",
                            )
        else:
            st.caption("No supervisor with enough ranked agents in this filter.")

    render_banner("Coaching queue")
    st.caption(
        "Red border = below the 85 goal. Amber = on goal, but in the bottom 25% of this filter. "
        "Click Focus to open that supervisor or agent."
    )
    people_shown = shown[shown["Desk"].isin(["QA", "CSAT"])] if not shown.empty else shown
    if people_shown is None or people_shown.empty:
        st.caption("No QA/CSAT coaching rows for the current filter.")
    else:
        def _coach_html(row: pd.Series, desk: str) -> str:
            kind = _cell_str(row.get("Kind") or row.get("Focus_Kind"), "agent")
            name = _cell_str(row.get("Owner"), "—")
            score_txt = _fmt(row.get("Score"), 1, "%")
            sup = _cell_str(row.get("Supervisor_ID"))
            sample_n = int(row.get("Sample_N") or row.get("Volume") or 0)
            unit = "audits" if desk == "QA" else "surveys"
            pts = None
            score_n = pd.to_numeric(row.get("Score"), errors="coerce")
            if pd.notna(score_n):
                goal = QA_GOAL if desk == "QA" else CSAT_GOAL
                gap = goal - float(score_n)
                if gap > 0:
                    pts = (
                        f"{round(gap):.0f} pts below goal"
                        if abs(gap - round(gap)) < 0.05
                        else f"{gap:.1f} pts below goal"
                    )
            if kind == "supervisor":
                n_q4 = int(row.get("Q4_N") or row.get("Volume") or 0)
                n_ranked = int(row.get("Ranked_N") or 0)
                mix = f"{n_q4} of {n_ranked} ranked in the bottom 25%"
                why = f"{pts} · {mix}" if pts else f"Team mean on goal · {mix}"
                n_txt = f"n={sample_n} {unit}" if sample_n else ""
                meta = " · ".join(p for p in (why, n_txt) if p)
            else:
                why = (
                    f"{pts} · bottom 25% of this filter"
                    if pts
                    else "Above goal · bottom 25% of this filter"
                )
                who = sup if sup else "no supervisor"
                n_txt = f"n={sample_n} {unit}" if sample_n else ""
                meta = " · ".join(p for p in (why, who, n_txt) if p)
            return (
                '<div class="didi-coach">'
                '<div class="didi-coach-main">'
                f'<p class="didi-coach-name">{html_escape(name)}</p>'
                f'<p class="didi-coach-meta">{html_escape(meta)}</p>'
                "</div>"
                f'<p class="didi-coach-score">{html_escape(score_txt)}</p>'
                "</div>"
            )

        def _render_coach_row(row: pd.Series, desk: str, idx: object) -> None:
            kind = _cell_str(row.get("Focus_Kind"))
            key = _cell_str(row.get("Focus_Key"))
            selected = (
                (kind == "supervisor" and str(sel_supervisor) == key)
                or (kind == "agent" and str(sel_agent) == key)
            )
            score_n = pd.to_numeric(row.get("Score"), errors="coerce")
            goal = QA_GOAL if desk == "QA" else CSAT_GOAL
            below = _as_bool(row.get("Below_Goal")) or (
                pd.notna(score_n) and float(score_n) < goal
            )
            tone = "red" if below else "amber"
            box = f"didi_watch_{'on_' if selected else ''}{tone}"
            with st.container(border=True, key=_next_didi_key(box)):
                body, action = st.columns([4.4, 1.15], vertical_alignment="center")
                with body:
                    st.markdown(_coach_html(row, desk), unsafe_allow_html=True)
                with action:
                    if st.button(
                        "Clear" if selected else "Focus coaching",
                        key=f"watch_{desk}_{idx}_{_fn}",
                        width="stretch",
                    ):
                        dim = "supervisor" if kind == "supervisor" else "agent"
                        _set_people_filter(dim, None if selected else key)

        for desk in ("QA", "CSAT"):
            grp = people_shown[people_shown["Desk"] == desk].copy()
            if grp.empty:
                continue
            hex_d = desk_hex.get(desk, STATUS_COLORS["neutral"])
            n_agents = int(len(grp))
            st.markdown(
                f'<div class="didi-watch-group didi-watch-group--{html_escape(desk)}">'
                f'<span class="didi-watch-group-dot" style="background:{hex_d}"></span>'
                f'<span class="didi-watch-group-name">{html_escape(desk)}</span>'
                f'<span class="didi-watch-group-n">· {n_agents} '
                f'{"agent" if n_agents == 1 else "agents"}</span>'
                "</div>",
                unsafe_allow_html=True,
            )
            scores = pd.to_numeric(grp["Score"], errors="coerce")
            goal = QA_GOAL if desk == "QA" else CSAT_GOAL
            if "Below_Goal" in grp.columns:
                below_mask = grp["Below_Goal"].map(_as_bool)
            else:
                below_mask = scores < goal
            grp = grp.assign(_gap=scores - goal, _below=below_mask)
            grp = grp.sort_values(["_below", "_gap"], ascending=[False, True])
            below_g = grp[grp["_below"].fillna(False)]
            lag_g = grp[~grp["_below"].fillna(False)]
            if not below_g.empty and not lag_g.empty:
                st.markdown(
                    '<p class="didi-watch-sub">Below company goal</p>',
                    unsafe_allow_html=True,
                )
            for i, row in below_g.iterrows():
                _render_coach_row(row, desk, i)
            if not below_g.empty and not lag_g.empty:
                st.markdown(
                    '<p class="didi-watch-sub">On goal · bottom 25%</p>',
                    unsafe_allow_html=True,
                )
            for i, row in lag_g.iterrows():
                _render_coach_row(row, desk, i)

    render_banner("Recontact — operations")
    st.caption(
        "Recontact has no supervisor, agent, tenure, or country field (region is always SSL). "
        "This block is the official rate versus 5.44, plus contact-reason Lv4 alerts — not people cards."
    )
    rc1, rc2 = st.columns([1, 2])
    with rc1:
        render_kpi(
            L("kpi_recontact"), f"{rc_rate:.2f}%", rc_vs, "inverse",
            traffic=rc_light,
            size="secondary",
            caption="Σ Recontact Volume / Σ Contacts. FCR is 100 − this rate; no FCR target.",
        )
    with rc2:
        rc_ops = recontact_ops_table(rc_cr)
        if rc_ops.empty:
            st.caption("No contact-reason recontact rows off the 5.44 goal in this filter.")
        else:
            show_df(pd.DataFrame({
                "Contact reason Lv4 (detail)": rc_ops["Contact reason Lv4 (detail)"],
                "Repeats": rc_ops["Repeats"].map(lambda v: f"{int(v):,}"),
                "Rate %": rc_ops["Rate %"].map(lambda v: f"{v:.2f}" if pd.notna(v) else "—"),
                "vs 5.44": rc_ops["vs 5.44"].map(lambda v: f"{v:+.2f}" if pd.notna(v) else "—"),
            }))

    render_banner("Ticket tracker")
    st.caption("Click a stage to filter the coaching queue. Click again to show all.")
    f1, f2, f3 = st.columns(3)
    with f1:
        with st.container(key=_next_didi_key("didi_flow")):
            if st.button(
                f"Active alerts: {n_active}",
                key=f"pipe_active_{_fn}",
                width="stretch",
                type="primary" if pipe_filter == "active" else "secondary",
            ):
                st.session_state[pipe_key] = None if pipe_filter == "active" else "active"
                st.rerun()
    with f2:
        with st.container(key=_next_didi_key("didi_flow")):
            if st.button(
                f"In progress / notified: {n_prog}",
                key=f"pipe_prog_{_fn}",
                width="stretch",
                type="primary" if pipe_filter == "progress" else "secondary",
            ):
                st.session_state[pipe_key] = None if pipe_filter == "progress" else "progress"
                st.rerun()
    with f3:
        with st.container(key=_next_didi_key("didi_flow")):
            if st.button(
                f"Closed / coached: {n_closed}",
                key=f"pipe_closed_{_fn}",
                width="stretch",
                type="primary" if pipe_filter == "closed" else "secondary",
            ):
                st.session_state[pipe_key] = None if pipe_filter == "closed" else "closed"
                st.rerun()
    if not tickets:
        st.caption("Create a ticket from a coaching card to move work through this flow. Email is a draft — the Excel has no addresses.")
    else:
        tcols = st.columns(min(3, len(tickets)))
        for i, ticket in enumerate(tickets):
            with tcols[i % len(tcols)]:
                render_ticket_card(ticket, tickets_key)

