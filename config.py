"""Central configuration — DiDi CX QA Dashboard."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
SOURCE_XLSX = DATA_DIR / "Business Case.xlsx"

# Parquet snapshot of the modelled tables, versioned in the repo so the app runs
# on any host (e.g. Streamlit Community Cloud) without the source workbook.
PACKAGED_DIR = DATA_DIR / "packaged"
# Local-only build cache; ephemeral on cloud hosts and excluded from git.
CACHE_DIR = DATA_DIR / "cache"

# ── DiDi Brand & Design System ──────────────────────────────────────────────
# Brand primaries (headers, tables, accents): orange, black, white.
DIDI_ORANGE = "#FF6600"
DIDI_DARK = "#1A1A1A"
DIDI_WHITE = "#FFFFFF"
DIDI_GRAY = "#F5F6F8"
DIDI_LIGHT_ORANGE = "#FF8533"
DIDI_NAVY = "#FFFFFF"
DIDI_SIDEBAR = "#F5F6F8"
DIDI_CARD = "#FFFFFF"
DIDI_TEXT = "#1A1A1A"
DIDI_MUTED = "#5C6570"
DIDI_FILTER = "#5C6570"
DIDI_CARD_BORDER = "#E2E5EA"

COUNTRY_NAMES = {
    "MX": "Mexico",
    "CO": "Colombia",
    "CR": "Costa Rica",
    "PE": "Peru",
    "DO": "Dominican Republic",
    "PA": "Panama",
}
COUNTRY_ISO3 = {
    "MX": "MEX",
    "CO": "COL",
    "CR": "CRI",
    "PE": "PER",
    "DO": "DOM",
    "PA": "PAN",
}
COUNTRY_FROM_ISO3 = {iso: code for code, iso in COUNTRY_ISO3.items()}

STATUS_COLORS = {
    "green": "#2E9B57",
    "amber": "#F2A900",
    "red": "#D64545",
    "neutral": "#94A3B8",
    "blue": "#2E6FBE",
}

CHART_COLORS = {
    "qa": "#2E9B57",
    "csat": "#2E6FBE",
    "recontact": "#D64545",
    "bar": "#2E6FBE",
    "blue": "#2E6FBE",
    "critical": "#D64545",
}

BORDER_COLOR = "#E2E5EA"
CARD_BORDER = DIDI_CARD_BORDER

# ── KPI Goals (Business Case PDF) ──────────────────────────────────────────
QA_GOAL = 85.0
CSAT_GOAL = 85.0
RECONTACT_GOAL = 5.44
AUDIT_COVERAGE_GOAL = 95.0  # % of target interactions audited

# Official control totals for the full May snapshot (ratio of sums, all weeks).
CONTROL_TOTALS = {
    "qa": 94.14,
    "csat": 79.95,
    "recontact": 5.83,
    "surveys": 77266,
    "contacts": 994591,
    "evaluations": 2460,
}

# ── Alert Thresholds (Operational — prompt v2) ─────────────────────────────
QA_GREEN = 90.0
QA_AMBER = 85.0
QA_RED = 75.0

MIN_SAMPLE_SIZE = 5  # min audits per agent for "reliable" score

# QA Tenure: Excel values → English labels that do not overlap.
# "New hire" stays as in the source. Do not map it to "< 3 months"
# (that bucket collided with 30–90 days / 1–3 months).
TENURE_SOURCE_ORDER = [
    "New hire",
    "30–90 days",
    "3–6 months",
    "6–12 months",
    "More than 1 year",
]
TENURE_FROM_EXCEL = {
    "New hire": "New hire",
    "Tenure (De 30 a 90 días)": "30–90 days",
    "Tenure (De 3 a 6 Meses)": "3–6 months",
    "Tenure (De 6 a 12 Meses)": "6–12 months",
    "Tenure (Mas de 1 año)": "More than 1 year",
}
# Packaged parquet still stores the old overlapping English buckets on Tenure_Cohort.
TENURE_FROM_LEGACY = {
    "< 3 months": "New hire",
    "1–3 months": "30–90 days",
    "3–6 months": "3–6 months",
    "6–12 months": "6–12 months",
    "12+ months": "More than 1 year",
    "De 30 a 90 días": "30–90 days",
    "De 3 a 6 Meses": "3–6 months",
    "De 6 a 12 Meses": "6–12 months",
    "Mas de 1 año": "More than 1 year",
}


def tenure_display_label(value) -> str:
    """Map Excel Tenure / legacy cohort names to the source labels."""
    if value is None:
        return "Unknown"
    if isinstance(value, float) and value != value:
        return "Unknown"
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "unknown"}:
        return "Unknown"
    aliases = {**TENURE_FROM_EXCEL, **TENURE_FROM_LEGACY, **{x: x for x in TENURE_SOURCE_ORDER}}
    if text in aliases:
        return aliases[text]
    return text


# ── QA Attribute Columns ───────────────────────────────────────────────────
PHONE_ATTRS = [
    "Critical_atributo_actitud_de_servicio_end_user",
    "Critical_atributo_compensaciones_reembolsos_end_user",
    "atributo_comunicacion_efectiva_end_user",
    "atributo_escucha_activa_end_user",
    "Critical_atributo_informacion_completa_y_correcta_end_user",
    "atributo_manejo_del_lenguaje_end_user",
    "atributo_manejo_del_tiempo_end_user",
    "Critical_atributo_negacion_de_servicio_end_user",
    "atributo_nombre_de_usuario_end_user",
    "atributo_personalizacion_de_la_interaccion_end_user",
    "atributo_presentacion_end_user",
    "Critical_atributo_rudeza_con_el_usuario_end_user",
]

LIVECHAT_ATTRS = [
    "Critical_Objetividad_del_chat",
    "Critical_Disponibilidad_del_servicio",
    "Saludo_e_identificacion",
    "Calidad_del_sondeo",
    "Recurrencia_de_informacion",
    "Actitud_de_servicio",
    "Personalizacion",
    "Calidad_de_comunicacion",
]

# Excel QA attribute *column names* are Spanish; cell values are 0/1/2.
# Display labels are the English reading of those headers (not a CR translation).
ATTR_LABELS = {
    'Critical_atributo_actitud_de_servicio_end_user': 'Service attitude',
    'Critical_atributo_compensaciones_reembolsos_end_user': 'Compensations and refunds',
    'atributo_comunicacion_efectiva_end_user': 'Effective communication',
    'atributo_escucha_activa_end_user': 'Active listening',
    'Critical_atributo_informacion_completa_y_correcta_end_user': 'Complete and correct information',
    'atributo_manejo_del_lenguaje_end_user': 'Language handling',
    'atributo_manejo_del_tiempo_end_user': 'Time management',
    'Critical_atributo_negacion_de_servicio_end_user': 'Service denial',
    'atributo_nombre_de_usuario_end_user': 'User name',
    'atributo_personalizacion_de_la_interaccion_end_user': 'Interaction personalization',
    'atributo_presentacion_end_user': 'Introduction',
    'Critical_atributo_rudeza_con_el_usuario_end_user': 'Rudeness toward the user',
    'Critical_Objetividad_del_chat': 'Chat objectivity',
    'Critical_Disponibilidad_del_servicio': 'Service availability',
    'Saludo_e_identificacion': 'Greeting and identification',
    'Calidad_del_sondeo': 'Probing quality',
    'Recurrencia_de_informacion': 'Information recurrence',
    'Actitud_de_servicio': 'Service attitude',
    'Personalizacion': 'Personalization',
    'Calidad_de_comunicacion': 'Communication quality',
    'Presentacion': 'Introduction',
}

ATTR_LABELS_FROM_DISPLAY = {
    'Actitud De Servicio': 'Service attitude',
    'Compensaciones Reembolsos': 'Compensations and refunds',
    'Comunicacion Efectiva': 'Effective communication',
    'Escucha Activa': 'Active listening',
    'Informacion Completa Y Correcta': 'Complete and correct information',
    'Manejo Del Lenguaje': 'Language handling',
    'Manejo Del Tiempo': 'Time management',
    'Negacion De Servicio': 'Service denial',
    'Nombre De Usuario': 'User name',
    'Personalizacion De La Interaccion': 'Interaction personalization',
    'Rudeza Con El Usuario': 'Rudeness toward the user',
    'Objetividad Del Chat': 'Chat objectivity',
    'Disponibilidad Del Servicio': 'Service availability',
    'Saludo E Identificacion': 'Greeting and identification',
    'Calidad Del Sondeo': 'Probing quality',
    'Recurrencia De Informacion': 'Information recurrence',
    'Calidad De Comunicacion': 'Communication quality',
}

# Composite Quality Index weights (optional — documented in kpis.py).
# Includes FCR. Do not use this mix at agent grain: recontact has no agent.
COMPOSITE_WEIGHTS = {"qa": 0.50, "csat": 0.30, "fcr": 0.20}

# Ranking index only — not an official KPI card. QA + CSAT + inverted AHT.
# AHT is a percentile (lower Duration = better). No FCR / recontact at agent.
RANKING_INDEX_WEIGHTS = {"qa": 0.50, "csat": 0.30, "aht": 0.20}
RANKING_QA_MIN_N = 5
RANKING_CSAT_MIN_N = 20
# Combined Lv4 chart: enough n to draw a bar, then keep the top slice by volume.
CR_COMBO_TOP_N = 15
CR_COMBO_MIN_QA_N = 10
# Supervisor gap Paretos: n below this is insufficient sample, not a ranking.
SUPERVISOR_GAP_MIN_N = 20
# Option A leadership flag: share of the supervisor's ranked agents in company Q4.
SUPERVISOR_Q4_SHARE_ALERT = 40.0

LABELS = {
    'page_overview': 'CX Quality Overview',
    'page_qa': 'QA overview',
    'page_csat': 'CSAT / Voice of the Customer',
    'page_recontact': 'Recontact Rate',
    'page_alerts': 'Performance Hub',
    'section_overview': 'KPI general overview',
    'section_alerts_contract': 'Contractual',
    'section_alerts_ops': 'Operational',
    'section_qa': 'QA overview',
    'section_csat': 'CSAT overview',
    'section_recontact': 'Recontact overview',
    'section_market': 'Performance by market',
    'section_combined': 'Combined Analysis',
    'kpi_qa': 'QA Score',
    'kpi_csat': 'CSAT Score',
    'kpi_recontact': 'Recontact Rate',
    'kpi_fcr': 'FCR (derived)',
    'kpi_contacts': 'Total Contacts',
    'kpi_recontacts': 'Recontact number',
    'kpi_surveys': 'Total Surveys',
    'kpi_evals': 'QA Evaluations',
    'kpi_critical_rate': 'Audits with critical fail',
    'kpi_crit_fails': 'Critical fails',
    'kpi_noncrit_fails': 'Non-critical fails',
    'kpi_aht': 'AHT',
    'note_aht': 'Mean QA Duration in minutes. From audits only; CSAT has no handle-time field. Not an official KPI.',
    'kpi_resolution': 'Auditor resolution rate',
    'note_resolution': (
        "Was the case resolved? Auditor judgment from the form question "
        "'Se le brindó solución a la solicitud'. "
        "Resolved ÷ (Resolved + Not resolved). Abandoned chats are excluded. "
        "This is not FCR — FCR is only 100 minus the recontact rate. "
        "It does not enter the QA score."
    ),
    'caption_resolution': 'Was the case resolved? Auditor judgment — not FCR, not part of the QA score.',
    'kpi_abandoned': 'Abandoned interaction rate',
    'note_abandoned': (
        "Share of QA audits where the auditor marked "
        "'No, pero el usuario abandonó la interacción' — the caller hung up or closed the chat. "
        "These audits are excluded from auditor resolution rate. This is not recontact."
    ),
    'kpi_unresolved_process': 'Unresolved — process followed',
    'note_unresolved_process': (
        "Among audits marked Not resolved only. Process followed = the agent did the script "
        "and still could not close the case (usually policy or tools). "
        "Did not follow process = agent-side. "
        "Named dissatisfaction owner (CX Process vs People) is filled on ~4% of audits — "
        "see QA notes; do not treat that tag as the full picture."
    ),
    'caption_unresolved_process': (
        "Of not-resolved audits: agent followed the process. The rest did not — that slice is coaching."
    ),
    'kpi_audits_noncrit': 'Audits with non-critical fails',
    'kpi_audits_any_fail': 'Audits with fails (critical and non-critical)',
    'panel_weekly': 'Weekly trend',
    'sub_weekly': 'Week-by-week QA, CSAT, and recontact vs their goals',
    'panel_channel': 'QA / CSAT / Recontact by channel',
    'sub_channel': 'Official metrics by channel',
    'panel_requester': 'By requester type',
    'panel_ov_supervisor': 'Supervisor overview',
    'sub_ov_supervisor': 'Top teams by audit volume',
    'panel_sup_qa_pareto': 'Supervisor QA gap',
    'sub_sup_qa_pareto': 'Weighted deficit (gap × audits)',
    'panel_sup_csat_pareto': 'Supervisor CSAT gap',
    'sub_sup_csat_pareto': 'Weighted deficit (gap × surveys)',
    'panel_ten_qa_pareto': 'Tenure QA gap',
    'sub_ten_qa_pareto': 'New hire, 30–90 days, 3–6 months, 6–12 months, More than 1 year',
    'panel_ten_csat_pareto': 'Tenure CSAT gap',
    'sub_ten_csat_pareto': 'Mapped to QA Tenure, not user_tenure',
    'panel_agents_tenure': 'Agents below QA 85',
    'sub_agents_tenure': 'At least 5 audits',
    'panel_combined': 'Contact reason Lv4 (detail) failing more than one metric',
    'sub_combined': 'Low QA, low CSAT, and/or high recontact',
    'panel_actions': 'What to do next',
    'panel_qa_csat': 'QA vs CSAT',
    'sub_qa_csat': 'One point per contact reason Lv4 (detail)',
    'panel_qa_rc': 'QA vs recontact',
    'sub_qa_rc': 'One point per contact reason Lv4 (detail)',
    'panel_corr': 'KPI correlations',
    'sub_corr': 'R² on shared contact reason Lv4 (detail) names',
    'insight_label': 'Key operational insight',
    'action_label': 'Recommended action',
    'panel_qa_channel': 'QA by channel',
    'sub_qa_channel': 'Phone and Live Chat',
    'panel_qa_story': 'QA scorecard',
    'panel_failing_attr': 'QA fails by attribute — CRITICAL vs Non-critical',
    'sub_failing_attr': 'CRITICAL vs Non-critical',
    'panel_crit_split': 'CRITICAL vs Non-critical distribution',
    'sub_crit_split': 'Share of attribute fails',
    'panel_qa_cr': 'QA by contact reason Lv4 (detail)',
    'sub_qa_cr': 'Average score, at least 3 audits',
    'panel_tenure': 'QA by agent tenure — New hire to 1 year+',
    'sub_tenure': 'New hire, 30–90 days, 3–6 months, 6–12 months, More than 1 year',
    'panel_pareto_attr': 'QA fails by attribute',
    'sub_pareto_attr': 'Attribute-fail events; one audit can contribute more than one fail',
    'panel_hist': 'QA score distribution',
    'sub_hist': 'Audits by score',
    'panel_qa_ichart': 'QA daily',
    'sub_qa_ichart': 'Usual range and 85 goal',
    'panel_agents': 'Agents below 85',
    'panel_special': 'QA by Special project',
    'sub_special': 'Special_project field',
    'panel_audit_type': 'QA by Type of audit',
    'sub_audit_type': 'Type_of_audit field',
    'panel_aht': 'Handle time vs QA by channel',
    'sub_aht': 'Duration in minutes',
    'panel_aht_scatter': 'QA vs AHT',
    'sub_aht_scatter': 'Contact reason Lv4 (detail), at least 3 audits',
    'panel_aht_csat': 'CSAT vs AHT',
    'sub_aht_csat': 'Same contact reason Lv4 (detail) names as QA Duration',
    'panel_aht_rc': 'Recontact vs handle time',
    'sub_aht_rc': 'Phone and Live Chat only',
    'panel_aht_corr': 'AHT correlations',
    'sub_aht_corr': 'R² at contact reason Lv4 (detail)',
    'panel_csat_pareto': 'Unsatisfied surveys by contact reason Lv4 (detail)',
    'sub_csat_pareto': '1★–3★ volume by contact reason Lv4 (detail)',
    'panel_supervisor': 'QA by supervisor',
    'sub_supervisor': 'At least 5 audits',
    'panel_pareto_cr': 'QA fails by contact reason Lv4 (detail)',
    'sub_pareto_cr': 'Attribute fails by contact reason Lv4 (detail)',
    'panel_cr_group_qa': 'QA fails by contact reason Lv1 (group)',
    'sub_cr_group_qa': 'Contact reason Lv1 (group) vs contact reason Lv4 (detail)',
    'panel_qa_notes': 'Interaction outcome (auditor notes)',
    'panel_qa_outcome': 'Solution and process',
    'sub_qa_outcome': 'Auditor tag. Not an official KPI. Official QA is still the attribute-grid score.',
    'panel_qa_dissat': 'Auditor-tagged dissatisfaction',
    'sub_qa_dissat': 'Yes/No from the auditor. Owner and sub-reason exist only when Yes.',
    'panel_qa_48h': 'Same-CR contacts in last 48h',
    'sub_qa_48h': 'Count on the audit, not official recontact. 0 is Phone-only; Live Chat never uses 0.',
    'note_qa_notes': 'Auditor notes from the QA form. They do not enter the official QA score (attribute grid, critical → 0, else −10 from 100).',
    'panel_stars': 'CSAT by star rating',
    'sub_stars': 'Share of surveys',
    'panel_voc': 'Comment themes',
    'sub_voc': 'Themes from 1–3★ comments',
    'panel_seg': 'CSAT furthest from 85%',
    'sub_seg': 'At least 20 surveys',
    'panel_csat_tenure': 'CSAT by tenure (user_tenure)',
    'sub_csat_tenure': 'Survey field user_tenure',
    'panel_csat_ichart': 'CSAT daily',
    'sub_csat_ichart': 'Usual range and 85 goal',
    'panel_csat_bt': 'CSAT by Business Type',
    'sub_csat_bt': 'CSAT tab Business Type',
    'panel_rc_donut': 'Repeated contacts and rate by contact reason Lv4 (detail)',
    'sub_rc_donut': 'Repeat volume and official rate (ratio of sums) by contact reason Lv4 (detail)',
    'panel_rc_sub': 'Repeated contacts and rate by contact reason SUB_CR',
    'sub_rc_sub': 'Repeat volume and official rate at SUB_CR. Recontact has no native SUB_CR — Lv4 volume is split by CSAT mix.',
    'panel_rc_scope': 'Official mix vs Phone + Chat',
    'sub_rc_scope': 'Official rate uses all 12 channels. Phone + Chat is the audited rate.',
    'panel_rc_pareto': 'Repeat volume by contact reason Lv4 (detail)',
    'sub_rc_pareto': 'Volume ranking by contact reason Lv4 (detail) — not the rate',
    'panel_rc_channel': '12-channel mix',
    'sub_rc_channel': 'Contacts, repeats, and rate. Official KPI is the mix, not the average.',
    'panel_rc_ichart': 'Recontact by day',
    'sub_rc_ichart': 'Usual range and 5.44 goal',
    'panel_rc_channel_pareto': 'Repeat volume by channel',
    'sub_rc_channel_pareto': 'Volume ranking across the 12-channel mix',
    'panel_cr_group_rc': 'Recontact by contact reason Lv1 (group)',
    'sub_cr_group_rc': 'Contact reason Lv1 (group) vs contact reason Lv4 (detail)',
    'note_hist': 'The pile at 0 is audits with a critical fail — that interaction scored 0.',
    'note_crit_kpi': 'Share of interactions that scored 0 due to a critical fail. Not the share of attribute fails.',
    'note_noncrit_audits': 'Share of audits with at least one non-critical attribute fail. The same audit can also have a critical fail.',
    'note_any_fail_audits': 'Unique evaluations that failed at least one attribute. Not the count of fail marks — one audit can fail more than one attribute.',
    'note_crit_split': 'A critical fail zeroes the audit. Each non-critical fail deducts 10 from 100. N/A is excluded.',
    'note_spc': 'Red points are days outside typical day-to-day variation. Staying inside that range is not the same as meeting the goal.',
    'note_cr_map': 'Contact reason Lv1 (group) comes from the CSAT hierarchy, matched by contact reason Lv4 (detail). Reasons that do not appear in CSAT are shown as Not mapped. This is a grouping of official metrics, not a new formula.',
    'filter_cr': 'Contact reason Lv4 (detail)',
    'filter_cr_lv1': 'Contact reason Lv1 (group)',
    'filter_sub_cr': 'Contact reason SUB_CR (finest)',
    'col_cr_group': 'Contact reason Lv1 (group)',
    'col_cr_detail': 'Contact reason Lv4 (detail)',
    'qa_story': '',
    'overview_insight': '',
    'overview_action': '',
    'overview_hypothesis': '',
}
LABEL_GROUPS = {
    "Page titles": ["page_overview", "page_qa", "page_csat", "page_recontact", "page_alerts"],
    "Section labels": ["section_overview", "section_qa", "section_csat", "section_recontact", "section_market", "section_combined", "section_alerts_contract", "section_alerts_ops"],
    "KPI cards": [
        "kpi_qa", "kpi_csat", "kpi_recontact", "kpi_fcr", "kpi_contacts", "kpi_recontacts", "kpi_surveys",
        "kpi_evals", "kpi_critical_rate", "kpi_crit_fails", "kpi_noncrit_fails", "kpi_aht",
        "kpi_resolution", "note_resolution", "caption_resolution",
        "kpi_abandoned", "note_abandoned",
        "kpi_unresolved_process", "note_unresolved_process", "caption_unresolved_process",
        "kpi_audits_noncrit", "kpi_audits_any_fail", "note_aht",
    ],
    "Overview panels": [
        "panel_weekly", "sub_weekly", "panel_channel", "sub_channel", "panel_requester",
        "panel_ov_supervisor", "sub_ov_supervisor",
        "panel_sup_qa_pareto", "sub_sup_qa_pareto", "panel_sup_csat_pareto", "sub_sup_csat_pareto",
        "panel_ten_qa_pareto", "sub_ten_qa_pareto", "panel_ten_csat_pareto", "sub_ten_csat_pareto",
        "panel_agents_tenure", "sub_agents_tenure",
        "panel_combined", "sub_combined", "panel_actions", "panel_qa_csat", "sub_qa_csat",
        "panel_qa_rc", "sub_qa_rc", "panel_corr", "sub_corr",
        "insight_label", "action_label",
    ],
    "QA panels": [
        "panel_qa_channel", "sub_qa_channel", "panel_qa_story", "panel_failing_attr", "sub_failing_attr",
        "panel_crit_split", "sub_crit_split", "panel_qa_cr", "sub_qa_cr",
        "panel_tenure", "sub_tenure", "panel_pareto_attr", "sub_pareto_attr",
        "panel_hist", "sub_hist", "panel_qa_ichart", "sub_qa_ichart",
        "panel_agents", "panel_special", "sub_special", "panel_audit_type", "sub_audit_type",
        "panel_aht", "sub_aht", "panel_aht_scatter", "sub_aht_scatter",
        "panel_aht_csat", "sub_aht_csat", "panel_aht_rc", "sub_aht_rc",
        "panel_aht_corr", "sub_aht_corr", "panel_supervisor", "sub_supervisor",
        "panel_pareto_cr", "sub_pareto_cr", "panel_cr_group_qa", "sub_cr_group_qa",
        "panel_qa_notes", "panel_qa_outcome", "sub_qa_outcome",
        "panel_qa_dissat", "sub_qa_dissat", "panel_qa_48h", "sub_qa_48h",
        "note_hist", "note_crit_kpi", "note_noncrit_audits", "note_any_fail_audits",
        "note_crit_split", "note_spc", "note_cr_map", "note_qa_notes",
        "qa_story",
    ],
    "CSAT panels": [
        "panel_stars", "sub_stars", "panel_voc", "sub_voc", "panel_seg", "sub_seg",
        "panel_csat_tenure", "sub_csat_tenure", "panel_csat_ichart", "sub_csat_ichart",
        "panel_csat_bt", "sub_csat_bt", "panel_csat_pareto", "sub_csat_pareto",
    ],
    "Recontact panels": [
        "panel_rc_donut", "sub_rc_donut", "panel_rc_sub", "sub_rc_sub", "panel_rc_scope", "sub_rc_scope",
        "panel_rc_pareto", "sub_rc_pareto", "panel_rc_ichart", "sub_rc_ichart",
        "panel_rc_channel_pareto", "sub_rc_channel_pareto",
        "panel_rc_channel", "sub_rc_channel", "panel_cr_group_rc", "sub_cr_group_rc",
    ],
    "Filters": ["filter_cr", "filter_cr_lv1", "filter_sub_cr", "col_cr_group", "col_cr_detail"],
}

UI_OVERRIDES_PATH = ROOT / "ui_overrides.json"

THEME_DEFAULTS = {
    "navy": DIDI_NAVY,
    "sidebar": DIDI_SIDEBAR,
    "card": DIDI_CARD,
    "orange": DIDI_ORANGE,
    "text": DIDI_TEXT,
}

_LABELS_BUILTIN = dict(LABELS)


def _is_hex_color(value: object) -> bool:
    return isinstance(value, str) and value.startswith("#")


def load_ui_overrides() -> dict:
    """Read persisted label/theme tweaks. Missing or invalid files yield empty dicts."""
    empty = {"labels": {}, "theme": {}}
    if not UI_OVERRIDES_PATH.exists():
        return empty
    try:
        data = json.loads(UI_OVERRIDES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return empty
    if not isinstance(data, dict):
        return empty
    labels = data.get("labels") if isinstance(data.get("labels"), dict) else {}
    theme = data.get("theme") if isinstance(data.get("theme"), dict) else {}
    return {"labels": labels, "theme": theme}


def save_ui_overrides(labels: dict, theme: dict) -> Path:
    """Persist known label keys and hex theme colors to ui_overrides.json."""
    cleaned_labels = {
        key: str(value) for key, value in labels.items() if key in _LABELS_BUILTIN
    }
    cleaned_theme = {
        key: value
        for key, value in theme.items()
        if key in THEME_DEFAULTS and _is_hex_color(value)
    }
    payload = {"labels": cleaned_labels, "theme": cleaned_theme}
    UI_OVERRIDES_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return UI_OVERRIDES_PATH


def clear_ui_overrides() -> None:
    """Delete persisted visual tweaks so the next load uses built-in defaults."""
    UI_OVERRIDES_PATH.unlink(missing_ok=True)


def apply_ui_overrides() -> dict:
    """Merge file overrides into LABELS and DIDI_* . Safe to call every Streamlit run."""
    global DIDI_NAVY, DIDI_SIDEBAR, DIDI_CARD, DIDI_ORANGE, DIDI_TEXT
    overrides = load_ui_overrides()
    labels = dict(_LABELS_BUILTIN)
    for key, value in overrides.get("labels", {}).items():
        if key in labels and isinstance(value, str):
            labels[key] = value
    LABELS.clear()
    LABELS.update(labels)

    theme = dict(THEME_DEFAULTS)
    for key, value in overrides.get("theme", {}).items():
        if key in theme and _is_hex_color(value):
            theme[key] = value
    DIDI_NAVY = theme["navy"]
    DIDI_SIDEBAR = theme["sidebar"]
    DIDI_CARD = theme["card"]
    DIDI_ORANGE = theme["orange"]
    DIDI_TEXT = theme["text"]
    return {"labels": labels, "theme": theme}


_OVERRIDES = apply_ui_overrides()
THEME = _OVERRIDES["theme"]
