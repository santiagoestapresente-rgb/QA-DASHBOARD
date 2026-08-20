"""
Build the Power BI star-schema model from Business Case.xlsx.

Output: powerbi/DiDi_CX_PowerBI_Model.xlsx — one sheet per table.

Modelling decisions (all documented in the Assumptions sheet of the output):
  - QA Score is pre-calculated per audit using the Business Case rules so the
    measure layer in Power BI stays simple and auditable.
  - CR Lv4, Channel and Country values are normalised into surrogate keys
    because the three source tabs spell them differently.
  - Attribute results are fully unpivoted (pass / fail / N-A) so fail rate can
    be calculated against attributes actually evaluated, not against total fails.
  - The source score column (Score_end_user) is carried alongside our own
    QA_Score so the two methods can be shown side by side. QA_Score remains the
    official figure because it is the one the Business Case rules produce.
  - Recontact rows carry a data-quality flag, and dim_recontact_scope lets the
    rate be read at three channel scopes without replacing the official total.
  - Every figure quoted in the Assumptions sheet is recomputed at build time by
    forensic_facts() so the documentation cannot drift from the data.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (  # noqa: E402
    CSAT_GOAL,
    LIVECHAT_ATTRS,
    PHONE_ATTRS,
    QA_GOAL,
    RECONTACT_GOAL,
)
from modules.data_loader import _source_path, clean_attr_name, is_critical  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent.parent / "powerbi"
OUT_FILE = OUT_DIR / "DiDi_CX_PowerBI_Model.xlsx"

COUNTRY_NAMES = {
    "MX": "Mexico",
    "CO": "Colombia",
    "CR": "Costa Rica",
    "PE": "Peru",
    "DO": "Dominican Republic",
    "PA": "Panama",
}

TENURE_COHORT_MAP = {
    "New hire": "0-1 months",
    "Tenure (De 30 a 90 dias)": "1-3 months",
    "Tenure (De 30 a 90 días)": "1-3 months",
    "Tenure (De 3 a 6 Meses)": "3-6 months",
    "Tenure (De 6 a 12 Meses)": "6-12 months",
    "Tenure (Mas de 1 año)": "12+ months",
}

# Keyword rules used to classify open_question text into VOC themes.
VOC_THEME_RULES: list[tuple[str, list[str]]] = [
    ("Refund / compensation", ["reembols", "refund", "compens", "devoluc", "devolv", "mi dinero", "cobro", "cobrar"]),
    ("No solution provided", ["no resolv", "no solucion", "no me ayud", "no me dieron", "no sirven", "no ayud", "sin solucion"]),
    ("Long wait time", ["espera", "demor", "tard", "lento", "mucho tiempo"]),
    ("Agent attitude", ["actitud", "pesimo servicio", "pésimo servicio", "mal trato", "groser", "amable", "malo el servicio"]),
    ("Driver / courier behavior", ["conductor", "driver", "repartidor", "courier", "motorizado"]),
    ("Order / delivery issue", ["pedido", "orden", "order", "entrega", "producto", "restaurante"]),
    ("App / technical issue", ["app", "aplicacion", "aplicación", "error", "no funciona", "falla"]),
]


def norm_key(value: object) -> str:
    """Canonical key: trimmed, collapsed whitespace, casefolded."""
    if pd.isna(value):
        return "UNKNOWN"
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text.casefold() if text else "UNKNOWN"


def display_name(series: pd.Series) -> str:
    """Most frequent original spelling for a normalised key."""
    cleaned = series.dropna().astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    cleaned = cleaned[cleaned != ""]
    return cleaned.mode().iloc[0] if not cleaned.empty else "Unknown"


def classify_voc(text: object) -> str:
    if pd.isna(text):
        return "Not classified"
    lower = str(text).strip().casefold()
    if lower in ("", "other", "nan", ".", "-"):
        return "Not classified"
    for theme, keywords in VOC_THEME_RULES:
        if any(k in lower for k in keywords):
            return theme
    return "Other (free text)"


def process_adherence(series: pd.Series) -> np.ndarray:
    """Split the QA 'was a solution provided' answer into process adherence.

    The source column mixes two questions in one sentence: whether the request was
    solved and whether the agent followed the process. Only the second half is
    relevant here, because it is the dimension the source score penalises and the
    attribute grid (columns W-AP) does not represent.
    """
    text = series.astype(str).str.casefold()
    not_followed = text.str.contains("no siguió el proceso") | text.str.contains("no siguio el proceso")
    followed = text.str.contains("sí siguió el proceso") | text.str.contains("si siguio el proceso")
    return np.select(
        [not_followed, followed],
        ["Did not follow process", "Followed process"],
        default="Not assessed",
    )


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    path = _source_path()
    print(f"Reading {path}")
    qa = pd.read_excel(path, sheet_name="QA")
    csat = pd.read_excel(path, sheet_name="CSAT")
    rc = pd.read_excel(path, sheet_name="Recontact")
    for df in (qa, csat, rc):
        df.columns = [str(c).strip().replace("\ufeff", "") for c in df.columns]
    return qa, csat, rc


# ── QA scoring ────────────────────────────────────────────────────────────────

def score_audits(qa: pd.DataFrame) -> pd.DataFrame:
    """Apply Business Case QA rules per audit, keeping the components visible."""
    out = pd.DataFrame(index=qa.index)
    out["QA_Score"] = np.nan
    out["Has_Critical_Fail"] = 0
    out["NonCritical_Fails"] = 0
    out["Attributes_Evaluated"] = 0

    for channel, attrs in [("Phone", PHONE_ATTRS), ("Live Chat", LIVECHAT_ATTRS)]:
        mask = qa["Channel"] == channel
        if not mask.any():
            continue
        block = qa.loc[mask, attrs]
        # 2 = N/A -> excluded from the calculation entirely
        evaluated = block.replace(2, np.nan)

        crit_cols = [c for c in attrs if is_critical(c)]
        non_cols = [c for c in attrs if not is_critical(c)]

        critical_fail = (evaluated[crit_cols] == 1).any(axis=1) if crit_cols else pd.Series(False, index=block.index)
        non_fails = (evaluated[non_cols] == 1).sum(axis=1) if non_cols else pd.Series(0, index=block.index)

        out.loc[mask, "Has_Critical_Fail"] = critical_fail.astype(int)
        out.loc[mask, "NonCritical_Fails"] = non_fails
        out.loc[mask, "Attributes_Evaluated"] = evaluated.notna().sum(axis=1)
        out.loc[mask, "QA_Score"] = np.where(critical_fail, 0.0, np.maximum(0.0, 100.0 - non_fails * 10))

    return out


def unpivot_attributes(qa: pd.DataFrame) -> pd.DataFrame:
    """One row per audit x attribute, including passes and N/A."""
    parts = []
    for channel, attrs in [("Phone", PHONE_ATTRS), ("Live Chat", LIVECHAT_ATTRS)]:
        sub = qa[qa["Channel"] == channel]
        if sub.empty:
            continue
        melted = sub.melt(
            id_vars=["Audit_ID", "Date", "Week", "Agent_ID", "Channel_Key", "CR_Key"],
            value_vars=attrs,
            var_name="Attribute_Key",
            value_name="Raw_Value",
        )
        parts.append(melted)

    if not parts:
        return pd.DataFrame()

    out = pd.concat(parts, ignore_index=True)
    out = out[out["Raw_Value"].notna()].copy()
    out["Result"] = out["Raw_Value"].map({0: "Pass", 1: "Fail", 2: "N/A"}).fillna("Unknown")
    out["Is_Fail"] = (out["Raw_Value"] == 1).astype(int)
    out["Is_Evaluated"] = (out["Raw_Value"] != 2).astype(int)
    out["Is_Critical"] = out["Attribute_Key"].map(is_critical).astype(int)
    return out.drop(columns=["Raw_Value"])


# ── Dimensions ────────────────────────────────────────────────────────────────

def build_dim_date(*frames: pd.Series) -> pd.DataFrame:
    all_dates = pd.concat([pd.to_datetime(f).dropna() for f in frames])
    start, end = all_dates.min().normalize(), all_dates.max().normalize()
    dates = pd.date_range(start, end, freq="D")

    dim = pd.DataFrame({"Date": dates})
    iso = dim["Date"].dt.isocalendar()
    dim["Year"] = dim["Date"].dt.year
    dim["Month_Number"] = dim["Date"].dt.month
    dim["Month_Name"] = dim["Date"].dt.strftime("%B")
    dim["Week"] = "W" + iso["week"].astype(int).astype(str)
    dim["Week_Number"] = iso["week"].astype(int)
    dim["Day_Number"] = dim["Date"].dt.day
    dim["Day_Name"] = dim["Date"].dt.strftime("%A")
    dim["Day_Of_Week"] = dim["Date"].dt.dayofweek + 1
    dim["Is_Weekend"] = (dim["Date"].dt.dayofweek >= 5).astype(int)
    dim["Date_Label"] = dim["Date"].dt.strftime("%b %d")
    return dim


def build_dim_channel(qa: pd.DataFrame, csat: pd.DataFrame, rc: pd.DataFrame) -> pd.DataFrame:
    sources = {
        "QA": qa["Channel"],
        "CSAT": csat["Consolidated Channel."],
        "Recontact": rc["standard_channel_name"],
        # The previous-contact channel adds values the other columns never show
        # (notably 'Other'), and every one of them must resolve to the dimension.
        "Recontact_Prev": rc["prev_standard_channel_name"],
    }
    flag_of = {
        "QA": "Has_QA",
        "CSAT": "Has_CSAT",
        "Recontact": "Has_Recontact",
        "Recontact_Prev": "Has_Recontact_Prev",
    }
    blank = {v: 0 for v in flag_of.values()}
    rows: dict[str, dict] = {}
    for source, series in sources.items():
        for raw in series.dropna().unique():
            key = norm_key(raw)
            row = rows.setdefault(key, {"Channel_Key": key, **blank})
            row[flag_of[source]] = 1

    dim = pd.DataFrame(rows.values())
    dim["Channel_Name"] = dim["Channel_Key"].str.title().replace({"Gptbot": "GPTBot", "Helpmecx": "HelpMeCX"})
    dim["QA_Coverage"] = np.where(dim["Has_QA"] == 1, "Audited", "Not audited")
    cols = [
        "Channel_Key", "Channel_Name", "QA_Coverage",
        "Has_QA", "Has_CSAT", "Has_Recontact", "Has_Recontact_Prev",
    ]
    return dim[cols].sort_values("Channel_Name")


def build_dim_cr(qa: pd.DataFrame, csat: pd.DataFrame, rc: pd.DataFrame) -> pd.DataFrame:
    frames = []
    frames.append(pd.DataFrame({"Raw": qa["CR_Lv4_Raw"], "Src": "QA"}))
    frames.append(pd.DataFrame({"Raw": csat["CR Lv4"], "Src": "CSAT"}))
    frames.append(pd.DataFrame({"Raw": rc["CR Lv4"], "Src": "Recontact"}))
    stacked = pd.concat(frames, ignore_index=True).dropna(subset=["Raw"])
    stacked["CR_Key"] = stacked["Raw"].map(norm_key)

    dim = (
        stacked.groupby("CR_Key")
        .agg(CR_Lv4=("Raw", display_name))
        .reset_index()
    )
    for src in ("QA", "CSAT", "Recontact"):
        present = set(stacked.loc[stacked["Src"] == src, "CR_Key"])
        dim[f"In_{src}"] = dim["CR_Key"].isin(present).astype(int)

    # Hierarchy is only present in the CSAT and Recontact tabs
    csat_h = csat.assign(CR_Key=csat["CR Lv4"].map(norm_key))[["CR_Key", "CR Lv1", "CR Lv2", "CR Lv3"]]
    csat_h = csat_h.dropna(subset=["CR_Key"]).groupby("CR_Key").first().reset_index()
    csat_h.columns = ["CR_Key", "CR_Lv1", "CR_Lv2", "CR_Lv3"]

    rc_h = rc.assign(CR_Key=rc["CR Lv4"].map(norm_key))[["CR_Key", "cr_lv2_name", "cr_lv3_name"]]
    rc_h = rc_h.dropna(subset=["CR_Key"]).groupby("CR_Key").first().reset_index()
    rc_h.columns = ["CR_Key", "CR_Lv2_RC", "CR_Lv3_RC"]

    dim = dim.merge(csat_h, on="CR_Key", how="left").merge(rc_h, on="CR_Key", how="left")
    dim["CR_Lv2"] = dim["CR_Lv2"].fillna(dim["CR_Lv2_RC"])
    dim["CR_Lv3"] = dim["CR_Lv3"].fillna(dim["CR_Lv3_RC"])

    # The QA tab carries no CR Lv1, so reasons only audited in QA arrive unmapped.
    # Lv2 -> Lv1 is one-to-one in the CSAT hierarchy, which lets the level be
    # propagated to any reason whose Lv2 is known. Ambiguous Lv2 values are skipped.
    dim["CR_Lv1_Source"] = np.where(dim["CR_Lv1"].notna(), "CSAT hierarchy", None)
    known = dim[dim["CR_Lv1"].notna() & dim["CR_Lv2"].notna()]
    lv2_to_lv1 = (
        known.groupby("CR_Lv2")["CR_Lv1"]
        .agg(lambda s: s.iloc[0] if s.nunique() == 1 else None)
        .dropna()
    )
    derived = dim["CR_Lv1"].isna() & dim["CR_Lv2"].isin(lv2_to_lv1.index)
    dim.loc[derived, "CR_Lv1"] = dim.loc[derived, "CR_Lv2"].map(lv2_to_lv1)
    dim.loc[derived, "CR_Lv1_Source"] = "Derived from CR Lv2"
    dim["CR_Lv1_Source"] = dim["CR_Lv1_Source"].fillna("Not mapped")

    dim["CR_Lv1"] = dim["CR_Lv1"].fillna("Not mapped")
    dim["CR_Lv2"] = dim["CR_Lv2"].fillna("Not mapped")
    dim["CR_Lv3"] = dim["CR_Lv3"].fillna("Not mapped")

    # Top level of the LOB -> CR Lv1 -> CR Lv4 grouping required by the brief.
    qa_lob = (
        qa.dropna(subset=["LOB"])
        .groupby("CR_Key")
        .agg(LOB=("LOB", display_name))
        .reset_index()
    )
    dim = dim.merge(qa_lob, on="CR_Key", how="left")
    dim["LOB"] = dim["LOB"].fillna("Not audited in QA")

    dim["Coverage"] = np.where(
        (dim["In_QA"] + dim["In_CSAT"] + dim["In_Recontact"]) == 3,
        "All three metrics",
        "Partial coverage",
    )
    cols = [
        "CR_Key", "LOB", "CR_Lv1", "CR_Lv2", "CR_Lv3", "CR_Lv4",
        "CR_Lv1_Source", "In_QA", "In_CSAT", "In_Recontact", "Coverage",
    ]
    return dim[cols].sort_values(["LOB", "CR_Lv1", "CR_Lv4"])


def build_dim_country(qa: pd.DataFrame, csat: pd.DataFrame) -> pd.DataFrame:
    codes = sorted(
        set(qa["Country"].dropna().astype(str)) | set(csat["Country Code"].dropna().astype(str))
    )
    return pd.DataFrame({
        "Country_Code": codes,
        "Country_Name": [COUNTRY_NAMES.get(c, c) for c in codes],
    })


def build_dim_attribute() -> pd.DataFrame:
    rows = []
    for channel, attrs in [("Phone", PHONE_ATTRS), ("Live Chat", LIVECHAT_ATTRS)]:
        for col in attrs:
            rows.append({
                "Attribute_Key": col,
                "Attribute_Name": clean_attr_name(col),
                "Channel_Scope": channel,
                "Is_Critical": int(is_critical(col)),
                "Severity": "Critical (score = 0)" if is_critical(col) else "Non-critical (-10 pts)",
                "Point_Deduction": 100 if is_critical(col) else 10,
            })
    return pd.DataFrame(rows)


def build_dim_agent(qa: pd.DataFrame, audits: pd.DataFrame) -> pd.DataFrame:
    base = (
        qa.groupby("Agent_ID")
        .agg(
            Supervisor_ID=("Supervisor", "first"),
            Tenure_Raw=("Tenure", "first"),
            Hire_Date=("Fecha_ingreso_CSR", "first"),
        )
        .reset_index()
    )
    base["Tenure_Cohort"] = base["Tenure_Raw"].map(TENURE_COHORT_MAP).fillna("Not mapped")
    counts = audits.groupby("Agent_ID").agg(Total_Audits=("Audit_ID", "count")).reset_index()
    return base.merge(counts, on="Agent_ID", how="left")


def build_dim_goal() -> pd.DataFrame:
    return pd.DataFrame([
        {"Metric": "QA Score", "Goal": QA_GOAL, "Direction": "Higher is better", "Unit": "%",
         "Amber_Band_pp": 5, "Definition": "100 pts base; critical fail = 0; each non-critical fail = -10; N/A excluded"},
        {"Metric": "CSAT Score", "Goal": CSAT_GOAL, "Direction": "Higher is better", "Unit": "%",
         "Amber_Band_pp": 5, "Definition": "(4-star + 5-star responses) / Feedback CNT"},
        {"Metric": "Recontact Rate", "Goal": RECONTACT_GOAL, "Direction": "Lower is better", "Unit": "%",
         "Amber_Band_pp": 5, "Definition": "Recontact Volume / Contacts"},
    ])


def build_dim_voc_rules() -> pd.DataFrame:
    return pd.DataFrame([
        {"Theme": theme, "Keywords": ", ".join(words)}
        for theme, words in VOC_THEME_RULES
    ] + [
        {"Theme": "Other (free text)", "Keywords": "free text that matched no rule"},
        {"Theme": "Not classified", "Keywords": "blank or placeholder value 'Other'"},
    ])


def build_dim_recontact_scope() -> pd.DataFrame:
    """Disconnected table that drives the recontact rate at three channel scopes.

    It has no relationship to any fact table on purpose: the measure switches on
    Scope_Key and rebuilds the channel filter itself, so the three readings can sit
    in one visual without touching the official total.
    """
    return pd.DataFrame([
        {"Scope_Key": "all", "Scope_Order": 1,
         "Scope_Name": "Los 12 canales (oficial)",
         "Channels_Included": "Every channel in the Recontact tab, self-service and bots included",
         "Is_Official": 1},
        {"Scope_Key": "ex_self_help", "Scope_Order": 2,
         "Scope_Name": "Excluyendo Self Help",
         "Channels_Included": "Every channel except Self Help",
         "Is_Official": 0},
        {"Scope_Key": "audited", "Scope_Order": 3,
         "Scope_Name": "Solo Phone + Live Chat",
         "Channels_Included": "The two channels QA audits (dim_channel[Has_QA] = 1)",
         "Is_Official": 0},
    ])


# ── Forensic facts ────────────────────────────────────────────────────────────

def forensic_facts(
    qa_raw: pd.DataFrame,
    csat_raw: pd.DataFrame,
    qa: pd.DataFrame,
    fact_recontact: pd.DataFrame,
    dim_cr: pd.DataFrame,
) -> dict:
    """Recompute every figure quoted in the Assumptions sheet.

    Keeping this in the build means the documentation is regenerated from the data
    on every run instead of carrying numbers that were true once.
    """
    f: dict = {}
    process_col = "Se_le_brindo_solucion_a_la_solicitud"

    # ---- QA dispersion between channels -------------------------------------
    by_channel = qa.groupby("Channel")["QA_Score"].agg(["count", "mean"])
    f["qa_overall"] = qa["QA_Score"].mean()
    f["qa_phone"] = by_channel.loc["Phone", "mean"]
    f["qa_chat"] = by_channel.loc["Live Chat", "mean"]
    f["n_phone"] = int(by_channel.loc["Phone", "count"])
    f["n_chat"] = int(by_channel.loc["Live Chat", "count"])
    f["chat_share"] = f["n_chat"] / len(qa) * 100
    f["qa_simple_avg"] = by_channel["mean"].mean()
    f["phone_gap"] = f["qa_phone"] - QA_GOAL

    # ---- The value 2 is the other channel's block, not a real N/A ------------
    all_attrs = PHONE_ATTRS + LIVECHAT_ATTRS
    f["na_total"] = int((qa_raw[all_attrs] == 2).sum().sum())
    f["na_expected"] = f["n_phone"] * len(LIVECHAT_ATTRS) + f["n_chat"] * len(PHONE_ATTRS)
    f["na_inside_own_channel"] = sum(
        int((qa_raw.loc[qa_raw["Channel"] == channel, attrs] == 2).sum().sum())
        for channel, attrs in [("Phone", PHONE_ATTRS), ("Live Chat", LIVECHAT_ATTRS)]
    )

    # ---- Source score column (Score_end_user) -------------------------------
    src = qa_raw["Score_end_user"]
    f["src_mean"] = src.mean()
    f["src_agreement"] = (qa["QA_Score"] == src).mean() * 100
    f["src_differing"] = int((qa["QA_Score"] != src).sum())
    f["src_gap"] = f["src_mean"] - QA_GOAL
    chat_clean = qa_raw[(qa_raw["Channel"] == "Live Chat") & (qa_raw[LIVECHAT_ATTRS].eq(0).all(axis=1))]
    zeros = chat_clean[chat_clean["Score_end_user"] == 0]
    hundreds = chat_clean[chat_clean["Score_end_user"] == 100]
    f["chat_all_pass"] = len(chat_clean)
    f["chat_all_pass_zero"] = len(zeros)
    f["zero_not_followed"] = (process_adherence(zeros[process_col]) == "Did not follow process").mean() * 100
    f["hundred_not_followed"] = (
        (process_adherence(hundreds[process_col]) == "Did not follow process").mean() * 100
    )
    assessed = qa["Process_Adherence"] != "Not assessed"
    f["process_not_followed"] = (
        (qa["Process_Adherence"] == "Did not follow process").sum() / assessed.sum() * 100
    )

    # ---- Recontact scope and dilution ---------------------------------------
    contacts = fact_recontact.groupby("Channel_Key")["Contacts"].sum()
    volume = fact_recontact.groupby("Channel_Key")["Recontact_Volume"].sum()
    f["rc_all"] = volume.sum() / contacts.sum() * 100
    ex_self = fact_recontact[fact_recontact["Channel_Key"] != "self help"]
    f["rc_ex_self_help"] = ex_self["Recontact_Volume"].sum() / ex_self["Contacts"].sum() * 100
    audited = fact_recontact[fact_recontact["Channel_Key"].isin(["phone", "live chat"])]
    f["rc_audited"] = audited["Recontact_Volume"].sum() / audited["Contacts"].sum() * 100
    f["self_help_share"] = contacts.get("self help", 0) / contacts.sum() * 100
    f["self_help_rate"] = volume.get("self help", 0) / contacts.get("self help", 1) * 100
    f["rc_audited_gap"] = f["rc_audited"] - RECONTACT_GOAL

    # ---- Recontact anomalies ------------------------------------------------
    exceeds = fact_recontact["Recontact_Volume"] > fact_recontact["Contacts"]
    f["rc_exceeds"] = int(exceeds.sum())
    f["rc_exceeds_channels"] = ", ".join(
        sorted(fact_recontact.loc[exceeds, "Channel_Key"].unique())
    )
    f["rc_zero_contacts"] = int((fact_recontact["Contacts"] == 0).sum())
    # A zero-contact row with any recontact volume satisfies both conditions, so the
    # flagged total is smaller than the sum of the two counts.
    f["rc_flagged"] = int((fact_recontact["Data_Quality_Flag"] != "OK").sum())
    f["rc_both_conditions"] = (
        f["rc_exceeds"] + f["rc_zero_contacts"] - f["rc_flagged"]
    )
    clean = fact_recontact[fact_recontact["Data_Quality_Flag"] == "OK"]
    f["rc_clean"] = clean["Recontact_Volume"].sum() / clean["Contacts"].sum() * 100
    f["rc_anomaly_delta"] = f["rc_clean"] - f["rc_all"]
    f["rc_mean_of_ratios"] = (
        (fact_recontact["Recontact_Volume"] / fact_recontact["Contacts"])
        .replace([np.inf, -np.inf], np.nan)
        .mean() * 100
    )

    # ---- CSAT duplicates and denominator ------------------------------------
    stars = [f"Questionnaires With Star Level ={i}" for i in range(1, 6)]
    involved = csat_raw.duplicated(keep=False)
    f["csat_rows"] = len(csat_raw)
    f["csat_dup_redundant"] = int(csat_raw.duplicated().sum())
    f["csat_dup_redundant_pct"] = csat_raw.duplicated().mean() * 100
    f["csat_dup_involved"] = int(involved.sum())
    f["csat_dup_responses"] = int(csat_raw.loc[involved, "Feedback CNT"].sum())
    f["csat_dup_all_single"] = bool((csat_raw.loc[involved, "Feedback CNT"] == 1).all())
    satisfied = csat_raw[stars[3]].sum() + csat_raw[stars[4]].sum()
    feedback = csat_raw["Feedback CNT"].sum()
    f["csat_overall"] = satisfied / feedback * 100
    dedup = csat_raw.drop_duplicates()
    f["csat_dedup"] = (
        (dedup[stars[3]].sum() + dedup[stars[4]].sum()) / dedup["Feedback CNT"].sum() * 100
    )
    f["csat_dedup_delta"] = f["csat_dedup"] - f["csat_overall"]
    f["csat_star_sum_matches"] = int((csat_raw[stars].sum(axis=1) == csat_raw["Feedback CNT"]).sum())
    f["csat_has_total_col"] = "Total Feedback CNT" in csat_raw.columns

    # ---- VOC placeholder ----------------------------------------------------
    open_q = csat_raw["open_question"].astype(str).str.strip().str.casefold()
    f["voc_placeholder"] = (open_q == "other").mean() * 100

    # ---- Contact reason typing ----------------------------------------------
    f["retyped"] = int(qa["Is_Retyped_CR"].sum())
    f["retyped_pct"] = qa["Is_Retyped_CR"].mean() * 100
    spelling = qa["CR_Typing_Status"] == "Same reason, different spelling"
    f["spelling_only"] = int(spelling.sum())
    f["spelling_only_pct"] = spelling.mean() * 100
    f["raw_string_diff_pct"] = f["retyped_pct"] + f["spelling_only_pct"]
    f["qa_retyped"] = qa.loc[qa["Is_Retyped_CR"] == 1, "QA_Score"].mean()
    f["qa_typed_right"] = qa.loc[qa["Is_Retyped_CR"] == 0, "QA_Score"].mean()

    # ---- Linkage of QA to the other two tabs --------------------------------
    unmapped = set(dim_cr.loc[dim_cr["CR_Lv1"] == "Not mapped", "CR_Key"])
    f["audits_without_lv1"] = qa["CR_Key"].isin(unmapped).mean() * 100
    csat_keys = set(csat_raw["CR Lv4"].map(norm_key))
    f["audits_without_csat"] = (~qa["CR_Key"].isin(csat_keys)).mean() * 100

    return f


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    qa_raw, csat_raw, rc_raw = load_raw()

    # ---- fact_audit ----------------------------------------------------------
    qa = qa_raw.copy()
    qa["Audit_ID"] = np.arange(1, len(qa) + 1)
    qa["Date"] = pd.to_datetime(qa["fecha"]).dt.normalize()
    qa["Agent_ID"] = qa["Evaluado"].fillna("Unknown").astype(str).str.strip()
    qa["Supervisor"] = qa["Supervisor"].fillna("Unknown").astype(str).str.strip()
    qa["CR_Lv4_Raw"] = qa["CR_correcta"].fillna(qa["CR_registrada"])
    qa["CR_Key"] = qa["CR_Lv4_Raw"].map(norm_key)
    qa["Channel_Key"] = qa["Channel"].map(norm_key)

    scores = score_audits(qa)
    qa = pd.concat([qa, scores], axis=1)

    # The source workbook ships its own per-interaction score in column V. It is
    # carried through so the two methods can be compared in the report, but it is
    # never used to compute the headline number: QA_Score is the official one
    # because it is what the Business Case rules produce.
    qa["Source_Score_End_User"] = qa["Score_end_user"]
    qa["Score_Matches_Source"] = (qa["QA_Score"] == qa["Source_Score_End_User"]).astype(int)

    # Whether the agent followed the process is assessed in its own QA question and
    # is not represented anywhere in the attribute grid. It is the dimension that
    # explains most of the gap against the source score.
    qa["Process_Adherence"] = process_adherence(qa["Se_le_brindo_solucion_a_la_solicitud"])

    # Contact reason typing accuracy. Comparing the raw strings overstates the
    # problem badly because the two columns disagree on capitalisation constantly,
    # so the flag is built on the normalised keys and the spelling-only cases are
    # kept as their own category instead of being counted as mistyping.
    registered_key = qa["CR_registrada"].map(norm_key)
    correct_key = qa["CR_correcta"].map(norm_key)
    qa["CR_Registered_Raw"] = (
        qa["CR_registrada"].fillna("Unknown").astype(str)
        .str.replace(r"\s+", " ", regex=True).str.strip()
    )
    qa["Is_Retyped_CR"] = (registered_key != correct_key).astype(int)
    qa["CR_Typing_Status"] = np.select(
        [
            registered_key != correct_key,
            qa["CR_registrada"].astype(str).str.strip() != qa["CR_correcta"].astype(str).str.strip(),
        ],
        ["Retyped to a different reason", "Same reason, different spelling"],
        default="Registered correctly",
    )

    fact_audit = qa[[
        "Audit_ID", "Date", "Week", "Agent_ID", "Supervisor", "LOB", "Channel_Key",
        "Country", "CR_Key", "Requester", "Type_of_audit", "Duration", "Tenure",
        "QA_Score", "Has_Critical_Fail", "NonCritical_Fails", "Attributes_Evaluated",
        "Source_Score_End_User", "Score_Matches_Source", "Process_Adherence",
        "CR_Registered_Raw", "Is_Retyped_CR", "CR_Typing_Status",
    ]].rename(columns={
        "Supervisor": "Supervisor_ID",
        "Country": "Country_Code",
        "Type_of_audit": "Audit_Type",
        "Tenure": "Tenure_Raw",
    })
    fact_audit["Meets_QA_Goal"] = (fact_audit["QA_Score"] >= QA_GOAL).astype(int)

    # ---- fact_audit_attribute -----------------------------------------------
    fact_attr = unpivot_attributes(qa)

    # ---- fact_csat -----------------------------------------------------------
    csat = csat_raw.copy()
    csat["Date"] = pd.to_datetime(csat["pt(天)"]).dt.normalize()
    csat["Channel_Key"] = csat["Consolidated Channel."].map(norm_key)
    csat["CR_Key"] = csat["CR Lv4"].map(norm_key)
    star_cols = {f"Star_{i}": f"Questionnaires With Star Level ={i}" for i in range(1, 6)}
    for new, old in star_cols.items():
        csat[new] = csat[old].fillna(0).astype(int)
    csat["Satisfied_CNT"] = csat["Star_4"] + csat["Star_5"]
    csat["Unsatisfied_CNT"] = csat["Star_1"] + csat["Star_2"] + csat["Star_3"]
    csat["VOC_Theme"] = csat["open_question"].map(classify_voc)
    csat["VOC_Text"] = csat["open_question"].astype(str).str.slice(0, 200)
    csat["Is_Negative_Survey"] = (csat["Unsatisfied_CNT"] > 0).astype(int)

    fact_csat = csat[[
        "Date", "Channel_Key", "Country Code", "CR_Key", "User Type", "Business Line",
        "Business Type Name", "Agent name", "Feedback CNT", "Deliver CNT",
        "Star_1", "Star_2", "Star_3", "Star_4", "Star_5",
        "Satisfied_CNT", "Unsatisfied_CNT", "VOC_Theme", "VOC_Text", "Is_Negative_Survey",
    ]].rename(columns={
        "Country Code": "Country_Code",
        "User Type": "User_Type",
        "Business Line": "Business_Line",
        "Business Type Name": "Business_Type",
        "Agent name": "Agent_Name",
        "Feedback CNT": "Feedback_CNT",
        "Deliver CNT": "Deliver_CNT",
    })

    # ---- fact_recontact ------------------------------------------------------
    # Built before the other dimensions because it needs the channel labels.
    dim_channel = build_dim_channel(qa_raw, csat_raw, rc_raw)

    rc = rc_raw.copy()
    rc["Date"] = pd.to_datetime(rc["Date(天)"]).dt.normalize()
    rc["Channel_Key"] = rc["standard_channel_name"].map(norm_key)
    rc["Prev_Channel_Key"] = rc["prev_standard_channel_name"].map(norm_key)
    rc["CR_Key"] = rc["CR Lv4"].map(norm_key)

    # Where the customer came from before recontacting. Carried as plain text
    # rather than a second relationship to dim_channel so the prev-vs-current
    # matrix stays readable without juggling an inactive role-playing dimension.
    channel_label = dict(zip(dim_channel["Channel_Key"], dim_channel["Channel_Name"]))
    rc["Prev_Channel_Name"] = rc["Prev_Channel_Key"].map(channel_label).fillna("Unknown")
    rc["Channel_Switch"] = np.where(
        rc["Prev_Channel_Key"] == rc["Channel_Key"], "Same channel", "Switched channel"
    )
    rc["Is_Cross_Channel"] = (rc["Prev_Channel_Key"] != rc["Channel_Key"]).astype(int)
    rc["Contact_Route"] = rc["Prev_Channel_Name"] + " to " + rc["Channel_Key"].map(channel_label).fillna("Unknown")

    # Two impossible states exist in the source. They are flagged rather than
    # dropped so the official total stays reproducible, and the flag lets the rate
    # be recalculated without them to show how little they move the number.
    rc["Data_Quality_Flag"] = np.select(
        [rc["Contacts"] == 0, rc["Recontact Volume"] > rc["Contacts"]],
        ["Zero contacts recorded", "Recontact volume exceeds contacts"],
        default="OK",
    )

    fact_recontact = rc[[
        "Date", "Channel_Key", "Prev_Channel_Key", "Prev_Channel_Name", "Contact_Route",
        "Channel_Switch", "Is_Cross_Channel", "CR_Key", "customer_type",
        "Modality", "region_name", "Contacts", "Recontact Volume", "Data_Quality_Flag",
    ]].rename(columns={
        "customer_type": "User_Type",
        "region_name": "Region_Raw",
        "Recontact Volume": "Recontact_Volume",
    })

    # ---- dimensions ----------------------------------------------------------
    dim_date = build_dim_date(qa["Date"], csat["Date"], rc["Date"])
    dim_cr = build_dim_cr(qa, csat_raw, rc_raw)
    dim_country = build_dim_country(qa_raw, csat_raw)
    dim_attribute = build_dim_attribute()
    dim_agent = build_dim_agent(qa, fact_audit)
    dim_goal = build_dim_goal()
    dim_voc = build_dim_voc_rules()
    dim_rc_scope = build_dim_recontact_scope()

    facts = forensic_facts(qa_raw, csat_raw, qa, fact_recontact, dim_cr)

    # ---- integrity checks ----------------------------------------------------
    checks = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"Check": name, "Result": "PASS" if passed else "REVIEW", "Detail": detail})

    qa_mean = fact_audit["QA_Score"].mean()
    csat_pct = fact_csat["Satisfied_CNT"].sum() / fact_csat["Feedback_CNT"].sum() * 100
    rc_pct = fact_recontact["Recontact_Volume"].sum() / fact_recontact["Contacts"].sum() * 100

    check("QA Score computed for every audit", fact_audit["QA_Score"].notna().all(),
          f"{fact_audit['QA_Score'].isna().sum()} audits without score")
    check("Audit week matches ISO week of audit date",
          bool((qa["Week"].astype(str) == "W" + qa["Date"].dt.isocalendar()["week"].astype(int).astype(str)).all()),
          "Week column in the QA tab equals ISO week derived from the date")
    check("Channel keys resolve to dim_channel",
          set(fact_audit["Channel_Key"]).issubset(set(dim_channel["Channel_Key"])), "fact_audit -> dim_channel")
    check("CR keys resolve to dim_cr",
          set(fact_audit["CR_Key"]).issubset(set(dim_cr["CR_Key"])), "fact_audit -> dim_cr")
    check("Dates covered by dim_date",
          set(fact_csat["Date"]).issubset(set(dim_date["Date"])), "fact_csat -> dim_date")
    check("Recontact has no usable country", rc["region_name"].nunique() == 1,
          f"region_name distinct values: {list(rc['region_name'].unique())}")
    check("Previous channel keys resolve to dim_channel",
          set(fact_recontact["Prev_Channel_Key"]).issubset(set(dim_channel["Channel_Key"])),
          "fact_recontact[Prev_Channel_Key] -> dim_channel")
    qa_crs = dim_cr[dim_cr["In_QA"] == 1]
    check("CR Lv1 available for the reasons audited in QA",
          (qa_crs["CR_Lv1"] != "Not mapped").mean() >= 0.70,
          f"{int((qa_crs['CR_Lv1'] != 'Not mapped').sum())} of {len(qa_crs)} audited reasons "
          f"resolve to a CR Lv1")
    check("LOB present for every audited reason",
          (dim_cr.loc[dim_cr["In_QA"] == 1, "LOB"] != "Not audited in QA").all(),
          "dim_cr[LOB] populated from the QA tab")
    check("Value 2 never appears inside an audit's own channel block",
          facts["na_inside_own_channel"] == 0,
          f"{facts['na_total']:,} cells hold the value 2 and all of them belong to the other "
          f"channel's attribute block (expected {facts['na_expected']:,})")
    check("Source score column carried without loss",
          fact_audit["Source_Score_End_User"].notna().all(),
          f"Score_end_user mean {facts['src_mean']:.2f} vs our {facts['qa_overall']:.2f}; "
          f"agreement {facts['src_agreement']:.2f}%")
    ok_rows = fact_recontact["Data_Quality_Flag"] == "OK"
    check("Recontact anomalies isolated by the data-quality flag",
          bool((fact_recontact.loc[ok_rows, "Contacts"] > 0).all()
               and (fact_recontact.loc[ok_rows, "Recontact_Volume"]
                    <= fact_recontact.loc[ok_rows, "Contacts"]).all()),
          f"{facts['rc_exceeds']} rows with volume > contacts ({facts['rc_exceeds_channels']}) and "
          f"{facts['rc_zero_contacts']} rows with zero contacts, {facts['rc_flagged']} distinct "
          f"rows in total; excluding them moves the rate {facts['rc_anomaly_delta']:+.2f} pp")
    check("Overall QA Score reconciles with the channel mix",
          abs((facts["qa_phone"] * facts["n_phone"] + facts["qa_chat"] * facts["n_chat"])
              / (facts["n_phone"] + facts["n_chat"]) - facts["qa_overall"]) < 0.01,
          f"Phone {facts['qa_phone']:.2f} ({facts['phone_gap']:+.2f} pp vs goal) and Live Chat "
          f"{facts['qa_chat']:.2f} weight to the overall {facts['qa_overall']:.2f}; Live Chat is "
          f"{facts['chat_share']:.1f}% of the sample, so the average sits near its value")
    check("Recontact rate reconciles across the three channel scopes",
          round(fact_recontact["Recontact_Volume"].sum()
                / fact_recontact["Contacts"].sum() * 100, 2) == round(facts["rc_all"], 2),
          f"all channels {facts['rc_all']:.2f}%, excluding Self Help "
          f"{facts['rc_ex_self_help']:.2f}%, audited channels only {facts['rc_audited']:.2f}%; "
          f"Self Help is {facts['self_help_share']:.1f}% of the denominator at "
          f"{facts['self_help_rate']:.2f}%")
    check("CSAT star levels reconcile with the Feedback CNT denominator",
          facts["csat_star_sum_matches"] == facts["csat_rows"],
          f"sum of the five star columns equals Feedback CNT on all {facts['csat_rows']:,} rows; "
          f"no column named 'Total Feedback CNT' exists in the tab")

    summary = pd.DataFrame([
        {"Metric": "QA Score", "Scope": "All audits (official)", "Value": round(qa_mean, 2),
         "Goal": QA_GOAL, "Variance_pp": round(qa_mean - QA_GOAL, 2)},
        {"Metric": "QA Score", "Scope": f"Phone (n={facts['n_phone']:,})",
         "Value": round(facts["qa_phone"], 2), "Goal": QA_GOAL,
         "Variance_pp": round(facts["phone_gap"], 2)},
        {"Metric": "QA Score", "Scope": f"Live Chat (n={facts['n_chat']:,})",
         "Value": round(facts["qa_chat"], 2), "Goal": QA_GOAL,
         "Variance_pp": round(facts["qa_chat"] - QA_GOAL, 2)},
        {"Metric": "QA Score", "Scope": "Source column Score_end_user (reference only)",
         "Value": round(facts["src_mean"], 2), "Goal": QA_GOAL,
         "Variance_pp": round(facts["src_gap"], 2)},
        {"Metric": "CSAT Score", "Scope": "All surveys (official)", "Value": round(csat_pct, 2),
         "Goal": CSAT_GOAL, "Variance_pp": round(csat_pct - CSAT_GOAL, 2)},
        {"Metric": "Recontact Rate", "Scope": "All 12 channels (official)", "Value": round(rc_pct, 2),
         "Goal": RECONTACT_GOAL, "Variance_pp": round(rc_pct - RECONTACT_GOAL, 2)},
        {"Metric": "Recontact Rate", "Scope": "Excluding Self Help",
         "Value": round(facts["rc_ex_self_help"], 2), "Goal": RECONTACT_GOAL,
         "Variance_pp": round(facts["rc_ex_self_help"] - RECONTACT_GOAL, 2)},
        {"Metric": "Recontact Rate", "Scope": "Phone + Live Chat (audited channels)",
         "Value": round(facts["rc_audited"], 2), "Goal": RECONTACT_GOAL,
         "Variance_pp": round(facts["rc_audited_gap"], 2)},
    ])

    assumptions = pd.DataFrame([
        # ---- Method ---------------------------------------------------------
        {"Topic": "QA scoring",
         "Note": "Score pre-calculated per audit: 100 base, critical fail forces 0, "
                 "each non-critical fail -10, attributes marked 2 excluded. This is the rule "
                 "stated in the Business Case and it is applied literally.",
         "Impact": f"Produces the official QA Score of {facts['qa_overall']:.2f}."},
        {"Topic": "Attribute scope",
         "Note": "Phone uses columns W-AH (12 attributes) and Live Chat uses columns AI-AP "
                 "(8 attributes). The two sets are never mixed.",
         "Impact": "None. Explains the empty cells in the attribute-by-channel matrix."},
        {"Topic": "Rate measures use a ratio of sums",
         "Note": "Every rate in the model divides a sum by a sum, never averages per-row ratios. "
                 "The Recontact tab is pre-aggregated into buckets of unequal size, so averaging "
                 f"the per-row ratios would return {facts['rc_mean_of_ratios']:.2f}% instead of "
                 f"{facts['rc_all']:.2f}%. QA Score is the exception on purpose: there the unit of "
                 "analysis is the audit, so a straight average of per-audit scores is correct.",
         "Impact": f"Avoids a {facts['rc_mean_of_ratios'] - facts['rc_all']:+.2f} pp error on the "
                   f"recontact rate."},

        # ---- Finding 1: channel dispersion in QA ----------------------------
        {"Topic": "QA dispersion between channels",
         "Note": f"The overall QA Score of {facts['qa_overall']:.2f} is above goal, but the two "
                 f"audited channels are far apart: Live Chat {facts['qa_chat']:.2f} "
                 f"(n={facts['n_chat']:,}) against Phone {facts['qa_phone']:.2f} "
                 f"(n={facts['n_phone']:,}), which is {abs(facts['phone_gap']):.2f} pp below the "
                 f"goal of {QA_GOAL:.0f}. Live Chat is {facts['chat_share']:.1f}% of the sample, so "
                 "the volume-weighted average sits close to the Live Chat value and hides Phone. "
                 f"An unweighted average of the two channels would be {facts['qa_simple_avg']:.2f}.",
         "Impact": "None on the reported number. Surfaced through [Worst Channel Alert], the "
                   "dispersion indicator on the QA card and the executive insight engine."},
        {"Topic": "Phone audit coverage",
         "Note": f"Phone carries only {facts['n_phone']:,} of the {len(fact_audit):,} audits "
                 f"({100 - facts['chat_share']:.1f}%), so its score moves on a much smaller sample "
                 "than Live Chat and its confidence interval is correspondingly wider.",
         "Impact": "None. Argues for rebalancing the audit sample, not for adjusting the score."},

        # ---- Finding 2: recontact scope -------------------------------------
        {"Topic": "Recontact channels",
         "Note": "Recontact covers 12 channels including self-service and bots. QA only audits "
                 "Phone and Live Chat, so channel comparisons against QA are limited to those two.",
         "Impact": "None. Sets the boundary for any combined QA / recontact reading."},
        {"Topic": "Recontact scope and self-service dilution",
         "Note": f"The official rate of {facts['rc_all']:.2f}% is computed over all 12 channels. "
                 f"Self Help alone contributes {facts['self_help_share']:.1f}% of the denominator "
                 f"at a rate of just {facts['self_help_rate']:.2f}%, which pulls the total down. "
                 f"Excluding Self Help the rate is {facts['rc_ex_self_help']:.2f}%, and restricted "
                 f"to the QA-audited channels it is {facts['rc_audited']:.2f}% "
                 f"({facts['rc_audited_gap']:+.2f} pp against the {RECONTACT_GOAL}% goal). "
                 "Reading the headline as 'barely above goal' is only correct if the goal was "
                 "itself defined over all channels including bots and self-service, which the "
                 "Business Case does not state.",
         "Impact": f"None on the reported number; {facts['rc_all']:.2f}% remains the KPI. The other "
                   "two readings are exposed as context through dim_recontact_scope."},
        {"Topic": "Recontact goal basis",
         "Note": f"The Business Case gives a single recontact goal of {RECONTACT_GOAL}% without "
                 "stating which channels it covers. The model compares every scope against that "
                 "same goal and labels the scope explicitly rather than inventing a second goal.",
         "Impact": "None. Flagged so the goal's scope can be confirmed with the process owner."},
        {"Topic": "Recontact data anomalies",
         "Note": f"{facts['rc_exceeds']} rows report a recontact volume larger than the contact "
                 f"count, all of them on {facts['rc_exceeds_channels']}, and "
                 f"{facts['rc_zero_contacts']} rows report zero contacts. Both are impossible "
                 f"states and together they cover {facts['rc_flagged']} distinct rows, because "
                 f"{facts['rc_both_conditions']} rows meet both at once. They are flagged in "
                 "fact_recontact[Data_Quality_Flag] rather than dropped, so the official total "
                 "stays reproducible from the source. The flag labels a row with zero contacts as "
                 "such even when its volume also exceeds the count, so that label holds fewer rows "
                 "than the raw condition count.",
         "Impact": f"Excluding both would move the rate to {facts['rc_clean']:.2f}% "
                   f"({facts['rc_anomaly_delta']:+.2f} pp). Left in."},
        {"Topic": "Recontact market",
         "Note": "region_name is 'SSL' on every row, so Recontact cannot be filtered by country. "
                 "The market slicer only affects QA and CSAT.",
         "Impact": "None on the numbers. Limits the country view to two of the three metrics."},
        {"Topic": "Previous channel",
         "Note": "The Recontact tab records the channel of the prior contact. Prev_Channel_Name, "
                 "Contact_Route and Channel_Switch expose it so cross-channel escalation can be "
                 "measured; 'Other' only ever appears as a previous channel.",
         "Impact": "None. Enables the route analysis."},

        # ---- Finding 3: the source's own score ------------------------------
        {"Topic": "Source score column Score_end_user",
         "Note": f"Column V of the QA tab already holds a per-interaction score averaging "
                 f"{facts['src_mean']:.2f}, against {facts['qa_overall']:.2f} for our "
                 f"recalculation. The two agree on {facts['src_agreement']:.2f}% of rows and "
                 f"differ on {facts['src_differing']}. We recalculate because the Business Case "
                 "specifies a flat -10 per non-critical fail, and the source does not use that "
                 "rule. Both figures clear the goal: "
                 f"{facts['src_gap']:+.2f} pp for the source against "
                 f"{facts['qa_overall'] - QA_GOAL:+.2f} pp for ours. QA_Score is the official "
                 "measure; the source value is carried in fact_audit[Source_Score_End_User] for "
                 "side-by-side comparison only.",
         "Impact": "None on the reported number. Anticipates the question of why the two differ."},
        {"Topic": "Source scoring rubric",
         "Note": "Reverse-engineered from rows with exactly one non-critical fail, the source "
                 "weights each attribute instead of deducting a flat 10: -3 nombre_de_usuario; "
                 "-5 presentacion, Saludo_e_identificacion, Personalizacion; -15 "
                 "Actitud_de_servicio, Calidad_del_sondeo, Recurrencia_de_informacion; -20 "
                 "manejo_del_tiempo, Calidad_de_comunicacion; -30 comunicacion_efectiva. Critical "
                 "fails force 0 in both methods, with a handful of Live Chat exceptions scored 25.",
         "Impact": "None. Explains the direction of the gap: weighted deductions are harsher on "
                   "average than a flat -10, so the source score comes out lower."},
        {"Topic": "Process adherence is scored outside the attribute grid",
         "Note": f"{facts['chat_all_pass_zero']} Live Chat audits pass all 8 attributes yet the "
                 f"source scores them 0. Of those, {facts['zero_not_followed']:.1f}% are marked as "
                 "'the agent did not follow the process' in the separate QA question, against "
                 f"{facts['hundred_not_followed']:.1f}% among the "
                 f"{facts['chat_all_pass'] - facts['chat_all_pass_zero']:,} all-pass audits the "
                 "source scores 100. The source therefore penalises process adherence, which is "
                 "not represented in columns W-AP, so no score rebuilt from those columns alone "
                 "can reproduce it. The dimension is exposed as "
                 f"fact_audit[Process_Adherence]; {facts['process_not_followed']:.1f}% of the "
                 "audits where it was assessed did not follow the process.",
         "Impact": "None on the reported number. This is the substantive reason the two scores "
                   "cannot be reconciled attribute by attribute."},
        {"Topic": "The value 2 is not a real N/A",
         "Note": f"All {facts['na_total']:,} cells holding the value 2 are exactly the other "
                 f"channel's attribute block ({facts['n_phone']:,} Phone audits x "
                 f"{len(LIVECHAT_ATTRS)} Live Chat attributes plus {facts['n_chat']:,} Live Chat "
                 f"audits x {len(PHONE_ATTRS)} Phone attributes). Not one audit marks 2 inside its "
                 "own channel's block, so in this dataset 2 means 'belongs to the other channel', "
                 "not 'did not apply to this interaction'. Every audit grades 100% of the "
                 "attributes in scope for its channel.",
         "Impact": "None. Confirms the denominator of [Attribute Fail Rate] is the full attribute "
                   "list of the channel, with no partial evaluations to account for."},

        # ---- CSAT ------------------------------------------------------------
        {"Topic": "CSAT duplicate rows",
         "Note": f"{facts['csat_dup_redundant']:,} rows "
                 f"({facts['csat_dup_redundant_pct']:.2f}%) are redundant copies inside "
                 f"{facts['csat_dup_involved']:,} byte-identical rows carrying "
                 f"{facts['csat_dup_responses']:,} responses, every one of them with "
                 "Feedback CNT = 1. They are kept because they are genuine surveys from different "
                 "customers that happen to share day, agent, contact reason and rating; nothing in "
                 "the tab identifies a respondent, so identical rows are expected rather than a "
                 "loading error.",
         "Impact": f"Deduplicating would give {facts['csat_dedup']:.2f}% "
                   f"({facts['csat_dedup_delta']:+.2f} pp). Not applied."},
        {"Topic": "CSAT denominator naming",
         "Note": "The Business Case PDF calls the denominator 'Total Feedback CNT' but the column "
                 f"in the tab is named 'Feedback CNT' and no column with the PDF's name exists. "
                 "They are the same thing: the five star-level columns sum exactly to Feedback CNT "
                 f"on all {facts['csat_star_sum_matches']:,} rows.",
         "Impact": "None. Confirms the denominator choice behind the "
                   f"{facts['csat_overall']:.2f}% CSAT."},
        {"Topic": "VOC themes",
         "Note": f"open_question is the placeholder 'Other' on {facts['voc_placeholder']:.1f}% of "
                 f"rows, so the voice-of-customer analysis rests on the remaining "
                 f"{100 - facts['voc_placeholder']:.1f}%. Themes are derived by keyword matching on "
                 "the free-text answers; the rules are listed in dim_voc_theme.",
         "Impact": "None on the numbers. Theme volumes are not a census of complaints and should "
                   "be read as shares within the commented subset."},

        # ---- Contact reasons and linkage -------------------------------------
        {"Topic": "CR Lv4 keys",
         "Note": "Source tabs spell the same reason with different casing (e.g. 'Account Stolen' "
                 "vs 'Account stolen'). CR_Key is the case-folded value; CR_Lv4 keeps the most "
                 "frequent spelling.",
         "Impact": "Prevents the same reason being split into several rows."},
        {"Topic": "Contact reason typing accuracy",
         "Note": f"CR_registrada and CR_correcta hold different raw strings on "
                 f"{facts['raw_string_diff_pct']:.2f}% of audits, but "
                 f"{facts['spelling_only_pct']:.2f}% of that is capitalisation only. Comparing the "
                 f"normalised keys, {facts['retyped']:,} audits ({facts['retyped_pct']:.2f}%) were "
                 "genuinely retyped to a different contact reason. fact_audit[CR_Typing_Status] "
                 "keeps the three cases apart so the spelling noise is never reported as "
                 f"mistyping. Retyped audits score {facts['qa_retyped']:.2f} against "
                 f"{facts['qa_typed_right']:.2f} for the rest.",
         "Impact": f"None on the reported number. The defensible mistyping rate is "
                   f"{facts['retyped_pct']:.2f}%, not {facts['raw_string_diff_pct']:.2f}%."},
        {"Topic": "CR coverage",
         "Note": f"{int((dim_cr['Coverage'] == 'All three metrics').sum())} of {len(dim_cr)} "
                 "contact reasons exist in all three tabs. Combined analysis is only valid on "
                 "those.",
         "Impact": "Sets the filter for the QA-versus-CSAT scatter."},
        {"Topic": "QA to CSAT linkage",
         "Note": f"{facts['audits_without_csat']:.1f}% of audits have no counterpart contact reason "
                 f"in the CSAT tab and {facts['audits_without_lv1']:.1f}% resolve to no CR Lv1, so "
                 "the combined QA / CSAT reading covers most but not all of the audited volume.",
         "Impact": "None on the individual metrics. Bounds how much of QA can be tied to CSAT."},
        {"Topic": "CR Lv1 derivation",
         "Note": "The QA tab has no CR Lv1. Lv2 maps one-to-one to Lv1 in the CSAT hierarchy with "
                 "no conflicts, so Lv1 is propagated to reasons whose Lv2 is known. CR_Lv1_Source "
                 "records whether the value came from CSAT directly or was derived, and reasons "
                 "that resolve to neither stay as 'Not mapped' instead of being assigned a guess.",
         "Impact": f"Leaves {facts['audits_without_lv1']:.1f}% of audits without a CR Lv1 level."},

        # ---- Structural limits ----------------------------------------------
        {"Topic": "Requester type",
         "Note": "Every row in all three tabs is 'Customer'. Rider / Driver / Merchant "
                 "segmentation is not possible with this dataset.",
         "Impact": "None. The requester breakdown returns a single row by design."},
        {"Topic": "LOB",
         "Note": "The QA tab only contains the Delivery line of business, so the top level of the "
                 "LOB - CR Lv1 - CR Lv4 hierarchy has a single value. Business Type in the CSAT "
                 "tab does vary (Food, Full Service, Market Place, Pickup, Other) and is the "
                 "dimension used for action plans by business line.",
         "Impact": "None. The LOB level exists to honour the requested hierarchy."},
        {"Topic": "Date coverage",
         "Note": "QA covers 4 May - 29 May; CSAT and Recontact cover 1 May - 31 May. Daily trends "
                 "will show QA gaps on days without audits.",
         "Impact": "None. Explains the breaks in the QA trend line."},
    ])

    # ---- write ---------------------------------------------------------------
    OUT_DIR.mkdir(exist_ok=True)
    tables = {
        "fact_audit": fact_audit,
        "fact_audit_attribute": fact_attr,
        "fact_csat": fact_csat,
        "fact_recontact": fact_recontact,
        "dim_date": dim_date,
        "dim_channel": dim_channel,
        "dim_cr": dim_cr,
        "dim_country": dim_country,
        "dim_agent": dim_agent,
        "dim_attribute": dim_attribute,
        "dim_goal": dim_goal,
        "dim_voc_theme": dim_voc,
        "dim_recontact_scope": dim_rc_scope,
        "Assumptions": assumptions,
        "Validation": pd.DataFrame(checks),
        "Control_Totals": summary,
    }

    with pd.ExcelWriter(OUT_FILE, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as writer:
        for name, df in tables.items():
            df.to_excel(writer, sheet_name=name, index=False)

    print(f"\nWrote {OUT_FILE}")
    for name, df in tables.items():
        print(f"  {name:24s} {len(df):>7,} rows x {len(df.columns)} cols")

    print("\nControl totals")
    print(summary.to_string(index=False))
    print("\nValidation")
    print(pd.DataFrame(checks).to_string(index=False))

    print("\nForensic findings carried into the Assumptions sheet")
    print(f"  1. QA by channel      Phone {facts['qa_phone']:.2f} ({facts['phone_gap']:+.2f} pp vs goal, "
          f"n={facts['n_phone']:,}) | Live Chat {facts['qa_chat']:.2f} (n={facts['n_chat']:,}) "
          f"| overall {facts['qa_overall']:.2f}")
    print(f"  2. Recontact scope    all {facts['rc_all']:.2f}% | ex Self Help "
          f"{facts['rc_ex_self_help']:.2f}% | audited only {facts['rc_audited']:.2f}%  "
          f"(Self Help = {facts['self_help_share']:.1f}% of denominator at {facts['self_help_rate']:.2f}%)")
    print(f"  3. Scoring method     ours {facts['qa_overall']:.2f} vs source "
          f"{facts['src_mean']:.2f} | agreement {facts['src_agreement']:.2f}% | "
          f"{facts['src_differing']} rows differ")
    print(f"     CR typing          {facts['retyped_pct']:.2f}% genuinely retyped, "
          f"{facts['spelling_only_pct']:.2f}% spelling only "
          f"({facts['raw_string_diff_pct']:.2f}% raw-string difference)")
    print(f"     Process adherence  {facts['process_not_followed']:.1f}% of assessed audits did not "
          f"follow the process")


if __name__ == "__main__":
    main()
