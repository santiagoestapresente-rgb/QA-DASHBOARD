"""
Data loader — transforms raw Business Case Excel into fact/dimension model.

Two load paths (see `load_all_data`):
  1. Packaged parquet snapshot in `data/packaged/` — versioned in the repo, so the
     dashboard runs anywhere (Streamlit Community Cloud included) with no local
     paths and no Excel parsing at startup.
  2. Fallback: rebuild from the source workbook `data/Business Case.xlsx`.
     Regenerate the snapshot with `python scripts/build_data_artifact.py`.

Fact tables:
  - fact_audits: one row per QA audit
  - fact_errors: one row per attribute fail (unpivoted)
  - fact_csat: CSAT aggregated records
  - fact_recontact: recontact records

Dimension tables:
  - dim_agents: agent master
  - dim_supervisors: supervisor master
  - dim_error_types: attribute catalog with severity
  - dim_kpis: goal definitions
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    ATTR_LABELS,
    ATTR_LABELS_FROM_DISPLAY,
    CACHE_DIR,
    LIVECHAT_ATTRS,
    PACKAGED_DIR,
    PHONE_ATTRS,
    QA_AMBER,
    QA_GOAL,
    QA_GREEN,
    QA_RED,
    SOURCE_XLSX,
    TENURE_FROM_EXCEL,
    tenure_display_label,
)

# Tables that make up the packaged snapshot, in build order.
TABLE_NAMES = (
    "fact_audits",
    "fact_errors",
    "fact_csat",
    "fact_recontact",
    "dim_agents",
    "dim_supervisors",
    "dim_error_types",
    "dim_kpis",
    "cr_impact",
)

# Display labels for the Excel Tenure field (New hire + source buckets).
TENURE_COHORT_MAP = dict(TENURE_FROM_EXCEL)


def _source_path() -> Path:
    """Source workbook: the in-repo copy, overridable via DIDI_SOURCE_XLSX."""
    override = os.environ.get("DIDI_SOURCE_XLSX", "").strip()
    if override:
        return Path(override).expanduser()
    return SOURCE_XLSX


def is_critical(col: str) -> bool:
    return "critical" in col.lower()


def clean_attr_name(col: str) -> str:
    """English display name for a QA attribute column (Excel headers are Spanish)."""
    if col in ATTR_LABELS:
        return ATTR_LABELS[col]
    if col in ATTR_LABELS_FROM_DISPLAY:
        return ATTR_LABELS_FROM_DISPLAY[col]
    name = col.replace("_end_user", "").replace("Critical_", "").replace("Critical ", "")
    return name.replace("atributo_", "").replace("_", " ").title()


def _english_error_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Map packaged Spanish attribute labels to English without rebuilding parquet."""
    if df is None or df.empty:
        return df
    out = df.copy()
    if "Error_Raw" in out.columns:
        out["Error_Category"] = out["Error_Raw"].map(clean_attr_name)
    elif "Error_Category" in out.columns:
        out["Error_Category"] = out["Error_Category"].map(
            lambda v: ATTR_LABELS_FROM_DISPLAY.get(str(v), v)
        )
    return out


def _apply_source_tenure(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    out = df.copy()
    if "Tenure_Raw" in out.columns:
        out["Tenure_Cohort"] = out["Tenure_Raw"].map(tenure_display_label)
    elif "Tenure_Cohort" in out.columns:
        out["Tenure_Cohort"] = out["Tenure_Cohort"].map(tenure_display_label)
    return out


def _apply_display_labels(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    out = dict(data)
    if "fact_errors" in out:
        out["fact_errors"] = _english_error_categories(out["fact_errors"])
    if "dim_error_types" in out:
        out["dim_error_types"] = _english_error_categories(out["dim_error_types"])
    if "fact_audits" in out:
        out["fact_audits"] = _apply_source_tenure(out["fact_audits"])
    if "dim_agents" in out:
        out["dim_agents"] = _apply_source_tenure(out["dim_agents"])
    return out


def calc_qa_score(row: pd.Series, attr_cols: list[str]) -> float:
    """
    QA Score formula (Business Case PDF):
      - Start at 100 points per interaction.
      - Critical attribute fail (value=1) → score = 0 (fatal, overrides all).
      - Non-critical fail → −10 points each (stackable).
      - N/A (value=2) → excluded from calculation.
    """
    for col in attr_cols:
        val = row.get(col)
        if pd.isna(val) or val == 2:
            continue
        if is_critical(col) and val == 1:
            return 0.0

    fails = sum(
        1
        for col in attr_cols
        if not pd.isna(row.get(col))
        and row.get(col) != 2
        and not is_critical(col)
        and row.get(col) == 1
    )
    return max(0.0, 100.0 - fails * 10)


def score_status(score: float) -> str:
    """Operational alert thresholds (prompt v2)."""
    if score >= QA_GREEN:
        return "green"
    if score >= QA_AMBER:
        return "amber"
    if score >= QA_RED:
        return "amber"
    return "red"


def goal_status(score: float, goal: float = QA_GOAL, higher_is_better: bool = True) -> str:
    """PDF submission status: green at/above, amber within 5pp, red >5pp below."""
    diff = score - goal if higher_is_better else goal - score
    if diff >= 0:
        return "green"
    if diff >= -5:
        return "amber"
    return "red"


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    path = _source_path()
    qa = pd.read_excel(path, sheet_name="QA")
    csat = pd.read_excel(path, sheet_name="CSAT")
    recontact = pd.read_excel(path, sheet_name="Recontact")
    return qa, csat, recontact


def _safe_str_series(s: pd.Series) -> pd.Series:
    """Normalize ID/label columns to clean strings (handles NaN mixed types)."""
    return s.fillna("Unknown").astype(str).str.strip().replace("", "Unknown")


def _calc_scores_vectorized(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    scores = pd.Series(100.0, index=df.index)
    fatals = pd.Series(0, index=df.index, dtype=int)

    for channel, attrs in [("Phone", PHONE_ATTRS), ("Live Chat", LIVECHAT_ATTRS)]:
        mask = df["Channel"] == channel
        if not mask.any():
            continue
        sub = df.loc[mask, attrs].replace(2, np.nan)
        crit_cols = [c for c in attrs if is_critical(c)]
        non_cols = [c for c in attrs if not is_critical(c)]

        channel_fatals = pd.Series(0, index=sub.index, dtype=int)
        if crit_cols:
            channel_fatals = (sub[crit_cols] == 1).any(axis=1).astype(int)

        fail_count = (sub[non_cols] == 1).sum(axis=1) if non_cols else pd.Series(0, index=sub.index)
        channel_scores = np.where(
            channel_fatals == 1,
            0,
            np.maximum(0, 100 - fail_count * 10),
        )

        scores.loc[mask] = channel_scores
        fatals.loc[mask] = channel_fatals.values

    return scores, fatals


def build_fact_audits(qa: pd.DataFrame) -> pd.DataFrame:
    df = qa.copy()
    df["Audit_ID"] = range(1, len(df) + 1)
    df["Fecha"] = pd.to_datetime(df["fecha"])
    df["Agent_ID"] = _safe_str_series(df["Evaluado"])
    df["Supervisor_ID"] = _safe_str_series(df["Supervisor"])
    # Both QA CR columns are English in the Business Case workbook.
    # CR_correcta is the auditor-corrected reason; use it as the display CR.
    df["CR_Lv4"] = df["CR_correcta"].fillna(df["CR_registrada"])
    df["Tenure_Raw"] = df["Tenure"]
    df["Tenure_Cohort"] = df["Tenure"].map(tenure_display_label)
    df["Auditor_ID"] = df["Type_of_audit"]
    df["Type_of_audit"] = _safe_str_series(df["Type_of_audit"])
    df["Special_project"] = (
        _safe_str_series(df["Special_project"]) if "Special_project" in df.columns
        else "Unknown"
    )

    df["Score_Pct"], df["Fatal_Flag"] = _calc_scores_vectorized(df)
    df["Score_Status"] = df["Score_Pct"].apply(score_status)
    df["Goal_Status"] = df["Score_Pct"].apply(goal_status)
    if "Score_end_user" in df.columns:
        df["Source_Score_End_User"] = pd.to_numeric(df["Score_end_user"], errors="coerce")
    else:
        df["Source_Score_End_User"] = np.nan

    return df[
        [
            "Audit_ID", "Fecha", "Week", "Agent_ID", "Supervisor_ID", "LOB",
            "Channel", "Country", "CR_Lv4", "Tenure_Raw", "Tenure_Cohort",
            "Auditor_ID", "Type_of_audit", "Special_project",
            "Score_Pct", "Fatal_Flag", "Score_Status", "Goal_Status",
            "Source_Score_End_User", "Duration", "Requester",
        ]
    ]


def build_fact_errors(qa: pd.DataFrame) -> pd.DataFrame:
    """Unpivot attribute fails — vectorized via melt."""
    qa = qa.copy()
    qa["Audit_ID"] = range(1, len(qa) + 1)
    qa["CR_Lv4"] = qa["CR_correcta"].fillna(qa["CR_registrada"])
    qa["Agent_ID"] = _safe_str_series(qa["Evaluado"])
    qa["Supervisor_ID"] = _safe_str_series(qa["Supervisor"])

    id_vars = [
        "Audit_ID", "fecha", "Week", "Agent_ID", "Supervisor_ID",
        "LOB", "Channel", "CR_Lv4",
    ]
    parts = []
    for channel, attrs in [("Phone", PHONE_ATTRS), ("Live Chat", LIVECHAT_ATTRS)]:
        sub = qa[qa["Channel"] == channel]
        if sub.empty:
            continue
        melted = sub.melt(id_vars=id_vars, value_vars=attrs, var_name="Error_Raw", value_name="val")
        fails = melted[melted["val"] == 1].copy()
        if fails.empty:
            continue
        fails["Error_Category"] = fails["Error_Raw"].map(clean_attr_name)
        fails["Is_Critical"] = fails["Error_Raw"].map(is_critical)
        fails["Severity"] = fails["Is_Critical"].map(lambda x: 3.0 if x else 1.0)
        fails["Fecha"] = pd.to_datetime(fails["fecha"])
        parts.append(fails)

    if not parts:
        return pd.DataFrame()

    out = pd.concat(parts, ignore_index=True)
    return out[
        ["Audit_ID", "Fecha", "Week", "Agent_ID", "Supervisor_ID", "LOB",
         "Channel", "CR_Lv4", "Error_Category", "Error_Raw", "Is_Critical", "Severity"]
    ]


def build_fact_csat(csat: pd.DataFrame) -> pd.DataFrame:
    df = csat.copy()
    df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]
    df.rename(columns={"Consolidated Channel.": "Channel", "pt(天)": "Fecha", "CR Lv4": "CR_Lv4"}, inplace=True)
    df["Satisfied_CNT"] = (
        df["Questionnaires With Star Level =4"] + df["Questionnaires With Star Level =5"]
    )
    df["CSAT_Pct"] = np.where(
        df["Feedback CNT"] > 0,
        df["Satisfied_CNT"] / df["Feedback CNT"] * 100,
        np.nan,
    )
    df["Has_VOC"] = df["open_question"].notna() & (df["open_question"].astype(str).str.strip() != "")
    if "Business Type Name" in df.columns:
        df["Business_Type"] = df["Business Type Name"].astype(str).str.strip()
    if "CR Lv1" in df.columns:
        df["CR_Lv1"] = df["CR Lv1"]
    return df


def build_fact_recontact(recontact: pd.DataFrame) -> pd.DataFrame:
    df = recontact.copy()
    df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]
    df.rename(
        columns={
            "region_name": "Country",
            "customer_type": "User_Type",
            "Date(天)": "Fecha",
            "CR Lv4": "CR_Lv4",
        },
        inplace=True,
    )
    df["Recontact_Rate"] = np.where(
        df["Contacts"] > 0,
        df["Recontact Volume"] / df["Contacts"] * 100,
        np.nan,
    )
    df["FCR_Pct"] = 100 - df["Recontact_Rate"]
    return df


def build_dim_agents(fact_audits: pd.DataFrame, qa: pd.DataFrame) -> pd.DataFrame:
    agent_info = (
        qa.groupby("Evaluado")
        .agg(
            Supervisor_ID=("Supervisor", "first"),
            Tenure_Raw=("Tenure", "first"),
            Tenure_Cohort=("Tenure", lambda x: tenure_display_label(x.iloc[0])),
            Fecha_Ingreso=("Fecha_ingreso_CSR", "first"),
            Total_Audits=("Evaluado", "count"),
        )
        .reset_index()
        .rename(columns={"Evaluado": "Agent_ID"})
    )
    scores = (
        fact_audits.groupby("Agent_ID")
        .agg(
            Avg_Score=("Score_Pct", "mean"),
            Fatal_Count=("Fatal_Flag", "sum"),
            Audit_Count=("Audit_ID", "count"),
        )
        .reset_index()
    )
    merged = agent_info.merge(scores, on="Agent_ID", how="left")
    merged["Reliable"] = merged["Audit_Count"] >= 5
    merged["Avg_Score"] = merged["Avg_Score"].round(2)
    return merged


def build_dim_supervisors(fact_audits: pd.DataFrame) -> pd.DataFrame:
    return (
        fact_audits.groupby("Supervisor_ID")
        .agg(
            Agent_Count=("Agent_ID", "nunique"),
            Audit_Count=("Audit_ID", "count"),
            Avg_Score=("Score_Pct", "mean"),
            Fatal_Rate=("Fatal_Flag", "mean"),
        )
        .reset_index()
        .assign(
            Avg_Score=lambda d: d["Avg_Score"].round(2),
            Fatal_Rate=lambda d: (d["Fatal_Rate"] * 100).round(2),
        )
    )


def build_dim_error_types(fact_errors: pd.DataFrame) -> pd.DataFrame:
    if fact_errors.empty:
        return pd.DataFrame()
    return (
        fact_errors.groupby(["Error_Category", "Is_Critical", "Severity", "Channel"])
        .agg(Fail_Count=("Audit_ID", "count"))
        .reset_index()
        .sort_values("Fail_Count", ascending=False)
    )


def build_dim_kpis() -> pd.DataFrame:
    from config import AUDIT_COVERAGE_GOAL, CSAT_GOAL, RECONTACT_GOAL
    return pd.DataFrame(
        [
            {"Metric": "QA Score", "Goal": QA_GOAL, "Critical_Threshold": QA_RED, "Direction": "higher"},
            {"Metric": "CSAT", "Goal": CSAT_GOAL, "Critical_Threshold": 75, "Direction": "higher"},
            {"Metric": "Recontact Rate", "Goal": RECONTACT_GOAL, "Critical_Threshold": 10, "Direction": "lower"},
            {"Metric": "Audit Coverage", "Goal": AUDIT_COVERAGE_GOAL, "Critical_Threshold": 80, "Direction": "higher"},
        ]
    )


def build_cr_impact(csat: pd.DataFrame, recontact: pd.DataFrame) -> pd.DataFrame:
    """CR-level CSAT and FCR for Pareto impact weighting (ratio of sums)."""
    csat_cr = (
        csat.groupby("CR_Lv4")
        .agg(Satisfied=("Satisfied_CNT", "sum"), Feedback_CNT=("Feedback CNT", "sum"))
        .reset_index()
    )
    csat_cr["CSAT_Pct"] = np.where(
        csat_cr["Feedback_CNT"] > 0,
        csat_cr["Satisfied"] / csat_cr["Feedback_CNT"] * 100,
        np.nan,
    )
    csat_cr = csat_cr.drop(columns=["Satisfied"])
    rc = build_fact_recontact(recontact)
    rc_cr = (
        rc.groupby("CR_Lv4")
        .agg(Recontacts=("Recontact Volume", "sum"), Contacts=("Contacts", "sum"))
        .reset_index()
    )
    rc_cr["Recontact_Rate"] = np.where(
        rc_cr["Contacts"] > 0,
        rc_cr["Recontacts"] / rc_cr["Contacts"] * 100,
        np.nan,
    )
    rc_cr["FCR_Pct"] = 100 - rc_cr["Recontact_Rate"]
    rc_cr = rc_cr.drop(columns=["Recontacts", "Contacts"])
    return csat_cr.merge(rc_cr, on="CR_Lv4", how="outer")


def build_from_source() -> dict[str, pd.DataFrame]:
    """Full model rebuild from the Business Case workbook."""
    qa_raw, csat_raw, rc_raw = load_raw()
    fact_audits = build_fact_audits(qa_raw)
    fact_errors = build_fact_errors(qa_raw)
    fact_csat = build_fact_csat(csat_raw)
    fact_recontact = build_fact_recontact(rc_raw)

    return {
        "fact_audits": fact_audits,
        "fact_errors": fact_errors,
        "fact_csat": fact_csat,
        "fact_recontact": fact_recontact,
        "dim_agents": build_dim_agents(fact_audits, qa_raw),
        "dim_supervisors": build_dim_supervisors(fact_audits),
        "dim_error_types": build_dim_error_types(fact_errors),
        "dim_kpis": build_dim_kpis(),
        "cr_impact": build_cr_impact(fact_csat, rc_raw),
    }


def packaged_files() -> dict[str, Path]:
    return {name: PACKAGED_DIR / f"{name}.parquet" for name in TABLE_NAMES}


def has_packaged_snapshot() -> bool:
    return all(p.exists() for p in packaged_files().values())


def load_packaged() -> dict[str, pd.DataFrame]:
    """Read the in-repo parquet snapshot. Raises if any table is missing."""
    return {name: pd.read_parquet(path) for name, path in packaged_files().items()}


def _parquet_ready(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cast object columns to text so parquet can type them.

    Free-text fields such as `open_question` mix strings and numbers, which arrow
    rejects. Every consumer already calls `.astype(str)` on those columns, so the
    cast is behaviour-preserving; missing values stay missing.
    """
    out = df.copy()
    for col in out.columns:
        if out[col].dtype == object:
            out[col] = out[col].astype(str).where(out[col].notna(), None)
    return out


def write_packaged(data: dict[str, pd.DataFrame]) -> dict[str, int]:
    """Write the parquet snapshot to `data/packaged/`. Returns bytes per file."""
    PACKAGED_DIR.mkdir(parents=True, exist_ok=True)
    sizes: dict[str, int] = {}
    for name, path in packaged_files().items():
        _parquet_ready(data[name]).to_parquet(
            path, engine="pyarrow", compression="zstd", index=False
        )
        sizes[name] = path.stat().st_size
    return sizes


def _read_pickle_cache(source: Path) -> dict[str, pd.DataFrame] | None:
    """Local-only accelerator for the Excel path; ignored if unusable."""
    cached, stamp = CACHE_DIR / "data.pkl", CACHE_DIR / "source_mtime.txt"
    try:
        if not (cached.exists() and stamp.exists() and source.exists()):
            return None
        if stamp.read_text().strip() != str(source.stat().st_mtime):
            return None
        import pickle

        with open(cached, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None


def _write_pickle_cache(data: dict[str, pd.DataFrame], source: Path) -> None:
    """Best effort — cloud filesystems are ephemeral and may be read-only."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        import pickle

        with open(CACHE_DIR / "data.pkl", "wb") as f:
            pickle.dump(data, f)
        if source.exists():
            (CACHE_DIR / "source_mtime.txt").write_text(str(source.stat().st_mtime))
    except Exception:
        pass


def load_all_data() -> dict[str, pd.DataFrame]:
    """
    Packaged parquet snapshot first, source workbook second.

    The snapshot ships with the repo, so cloud deployments never depend on a path
    outside the project and never parse the 77k-row Excel at startup.
    """
    if has_packaged_snapshot():
        try:
            return _apply_display_labels(load_packaged())
        except Exception:
            # Corrupt or unreadable snapshot: fall through to the workbook if we
            # have one, otherwise re-raise so the caller sees the real error.
            if not _source_path().exists():
                raise

    source = _source_path()
    if not source.exists():
        raise FileNotFoundError(
            "No data available: packaged snapshot missing from "
            f"'{PACKAGED_DIR}' and source workbook not found at '{source}'. "
            "Run 'python scripts/build_data_artifact.py' to regenerate the snapshot."
        )

    cached = _read_pickle_cache(source)
    if cached is not None:
        return _apply_display_labels(cached)

    data = build_from_source()
    _write_pickle_cache(data, source)
    return _apply_display_labels(data)
