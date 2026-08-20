"""
KPI calculation engine — all business rules documented inline.
"""

from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd

from config import (
    COMPOSITE_WEIGHTS,
    CSAT_GOAL,
    MIN_SAMPLE_SIZE,
    QA_GOAL,
    RANKING_CSAT_MIN_N,
    RANKING_INDEX_WEIGHTS,
    RANKING_QA_MIN_N,
    RECONTACT_GOAL,
    SUPERVISOR_Q4_SHARE_ALERT,
    TENURE_SOURCE_ORDER,
)


def fatal_error_rate(audits: pd.DataFrame) -> float:
    """
    Fatal Error Rate = (# audits with Fatal_Flag=1) / total audits × 100.

    A fatal error (critical attribute fail) sets QA score to 0 for that audit.
    It is NOT independent — it fully nullifies the interaction score.
    """
    if audits.empty:
        return 0.0
    return audits["Fatal_Flag"].mean() * 100


def critical_fail_stats(audits: pd.DataFrame, errors: pd.DataFrame) -> dict:
    """
    Two different questions — do not mix them.

    pct_fatal: share of *audits* with Fatal_Flag (any critical fail → score 0).
    fail split: share of *attribute-fail rows* that are Critical vs Non-critical.
    n_audits_noncrit / n_audits_any_fail: distinct Audit_IDs with those fail types.
    """
    n_audits = int(len(audits))
    n_fatal = 0
    if n_audits and "Fatal_Flag" in audits.columns:
        n_fatal = int(pd.to_numeric(audits["Fatal_Flag"], errors="coerce").fillna(0).sum())
    pct_fatal = round(n_fatal / n_audits * 100, 2) if n_audits else 0.0

    n_crit = n_non = 0
    n_audits_noncrit = n_audits_any_fail = 0
    if not errors.empty and "Is_Critical" in errors.columns:
        flag = errors["Is_Critical"].fillna(False).astype(bool)
        n_crit = int(flag.sum())
        n_non = int((~flag).sum())
        if "Audit_ID" in errors.columns:
            n_audits_any_fail = int(errors["Audit_ID"].nunique())
            n_audits_noncrit = int(errors.loc[~flag, "Audit_ID"].nunique())
    elif not errors.empty and "Audit_ID" in errors.columns:
        n_audits_any_fail = int(errors["Audit_ID"].nunique())
        n_audits_noncrit = n_audits_any_fail
    total_fails = n_crit + n_non
    return {
        "n_audits": n_audits,
        "n_fatal": n_fatal,
        "pct_fatal": pct_fatal,
        "n_crit_fails": n_crit,
        "n_noncrit_fails": n_non,
        "total_fails": total_fails,
        "pct_fails_critical": round(n_crit / total_fails * 100, 1) if total_fails else 0.0,
        "pct_fails_noncritical": round(n_non / total_fails * 100, 1) if total_fails else 0.0,
        "n_audits_noncrit": n_audits_noncrit,
        "n_audits_any_fail": n_audits_any_fail,
        "pct_audits_noncrit": round(n_audits_noncrit / n_audits * 100, 1) if n_audits else 0.0,
        "pct_audits_any_fail": round(n_audits_any_fail / n_audits * 100, 1) if n_audits else 0.0,
    }


def avg_qa_score(audits: pd.DataFrame) -> float:
    """QA Score = simple average of individual audit scores (0–100 scale)."""
    if audits.empty:
        return 0.0
    return audits["Score_Pct"].mean()


def overall_csat(csat: pd.DataFrame) -> float:
    """CSAT % = (4★ + 5★ responses) / total feedback × 100."""
    if csat.empty:
        return 0.0
    total = csat["Feedback CNT"].sum()
    if total == 0:
        return 0.0
    satisfied = csat["Satisfied_CNT"].sum()
    return satisfied / total * 100


def ratio_of_sums(numerator: pd.Series, denominator: pd.Series) -> float:
    """Rate as sum(num) / sum(den) × 100. Never average row-level ratios."""
    den = denominator.sum()
    if den == 0:
        return float("nan")
    return float(numerator.sum() / den * 100)


def recontact_rate(recontact: pd.DataFrame) -> float:
    """Official recontact rate: Σ Recontact Volume / Σ Contacts × 100."""
    if recontact.empty:
        return 0.0
    val = ratio_of_sums(recontact["Recontact Volume"], recontact["Contacts"])
    return 0.0 if pd.isna(val) else val


def overall_fcr(recontact: pd.DataFrame) -> float:
    """
    FCR (First Contact Resolution) = 100 − Recontact Rate.
    Recontact Rate = total recontacts / total contacts × 100 (ratio of sums).
    """
    if recontact.empty:
        return 0.0
    return 100 - recontact_rate(recontact)


def composite_quality_index(qa: float, csat: float, fcr: float) -> float:
    """
    Optional Composite Quality Index (0–100):
      CQI = (QA × 0.50) + (CSAT × 0.30) + (FCR × 0.20)

    Weights documented in config.COMPOSITE_WEIGHTS.
    Not the agent ranking index — that mix has no FCR (recontact has no agent).
    """
    w = COMPOSITE_WEIGHTS
    return qa * w["qa"] + csat * w["csat"] + fcr * w["fcr"]


def wow_delta(current: float, previous: float) -> tuple[float, str]:
    """Week-over-week change. Returns (delta_pct, arrow)."""
    if previous == 0:
        return 0.0, "→"
    delta = ((current - previous) / abs(previous)) * 100
    arrow = "↑" if delta > 0.5 else ("↓" if delta < -0.5 else "→")
    return round(delta, 1), arrow


def weekly_trends(audits: pd.DataFrame) -> pd.DataFrame:
    """QA Score and Fatal Rate by week for trend/control charts."""
    g = (
        audits.groupby("Week", sort=True)
        .agg(
            QA_Score=("Score_Pct", "mean"),
            Fatal_Rate=("Fatal_Flag", "mean"),
            Audit_Count=("Audit_ID", "count"),
        )
        .reset_index()
    )
    g["Fatal_Rate"] = (g["Fatal_Rate"] * 100).round(2)
    g["QA_Score"] = g["QA_Score"].round(2)

    mean_score = g["QA_Score"].mean()
    std_score = g["QA_Score"].std()
    g["UCL"] = round(mean_score + 2 * std_score, 2)
    g["LCL"] = round(max(0, mean_score - 2 * std_score), 2)
    g["Mean"] = round(mean_score, 2)
    return g


def daily_trends(audits: pd.DataFrame) -> pd.DataFrame:
    g = (
        audits.groupby(audits["Fecha"].dt.date)
        .agg(
            QA_Score=("Score_Pct", "mean"),
            Fatal_Rate=("Fatal_Flag", "mean"),
            Audit_Count=("Audit_ID", "count"),
        )
        .reset_index()
        .rename(columns={"Fecha": "Date"})
    )
    g["Fatal_Rate"] = (g["Fatal_Rate"] * 100).round(2)
    g["QA_Score"] = g["QA_Score"].round(2)
    return g


def agent_scores(audits: pd.DataFrame) -> pd.DataFrame:
    g = (
        audits.groupby(["Agent_ID", "Supervisor_ID"])
        .agg(
            QA_Score=("Score_Pct", "mean"),
            Fatal_Rate=("Fatal_Flag", "mean"),
            Audit_Count=("Audit_ID", "count"),
        )
        .reset_index()
    )
    g["QA_Score"] = g["QA_Score"].round(2)
    g["Fatal_Rate"] = (g["Fatal_Rate"] * 100).round(2)
    g["Reliable"] = g["Audit_Count"] >= MIN_SAMPLE_SIZE
    g["Status"] = g["QA_Score"].apply(_score_alert)
    return g.sort_values("QA_Score")


def supervisor_heatmap_data(audits: pd.DataFrame) -> pd.DataFrame:
    return (
        audits.groupby(["Supervisor_ID", "Agent_ID"])
        .agg(QA_Score=("Score_Pct", "mean"), Audit_Count=("Audit_ID", "count"))
        .reset_index()
        .assign(QA_Score=lambda d: d["QA_Score"].round(1))
    )


def pareto_errors_simple(errors: pd.DataFrame) -> pd.DataFrame:
    """
    Pareto clásico por frecuencia real de errores en auditorías.
    Cantidad = veces que falló el atributo · Acumulado = regla 80/20.
    """
    if errors.empty:
        return pd.DataFrame()

    df = (
        errors.groupby(["Error_Category", "Is_Critical"])
        .size()
        .reset_index(name="Cantidad")
        .sort_values("Cantidad", ascending=False)
    )
    total = df["Cantidad"].sum()
    df["Porcentaje"] = (df["Cantidad"] / total * 100).round(1)
    df["Acumulado_Pct"] = df["Porcentaje"].cumsum().round(1)
    df["Tipo"] = df["Is_Critical"].map({True: "Crítico", False: "No crítico"})
    return df


def pareto_for_display(pareto: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    """
    Top N categorías + bucket 'Otros' para que el acumulado llegue a 100%.
    """
    if pareto.empty:
        return pareto

    if "Is_Critical" in pareto.columns:
        sorted_df = (
            pareto.groupby("Error_Category", as_index=False)["Cantidad"]
            .sum()
            .sort_values("Cantidad", ascending=False)
            .reset_index(drop=True)
        )
    else:
        sorted_df = pareto.sort_values("Cantidad", ascending=False).reset_index(drop=True)

    full_total = sorted_df["Cantidad"].sum()

    rows: list[dict] = []
    for _, r in sorted_df.head(top_n).iterrows():
        rows.append({"Error_Category": r["Error_Category"], "Cantidad": int(r["Cantidad"])})

    rest = int(sorted_df.iloc[top_n:]["Cantidad"].sum()) if len(sorted_df) > top_n else 0
    if rest > 0:
        rows.append({"Error_Category": "Otros", "Cantidad": rest})

    out = pd.DataFrame(rows)
    out["Porcentaje"] = (out["Cantidad"] / full_total * 100).round(1)
    out["Acumulado_Pct"] = out["Porcentaje"].cumsum().round(1)
    out.loc[out.index[-1], "Acumulado_Pct"] = 100.0
    return out


def pareto_errors_by_channel(errors: pd.DataFrame) -> pd.DataFrame:
    if errors.empty:
        return pd.DataFrame()
    return (
        errors.groupby(["Channel", "Error_Category", "Is_Critical"])
        .size()
        .reset_index(name="Cantidad")
        .sort_values("Cantidad", ascending=False)
    )


def pareto_errors_impact(
    errors: pd.DataFrame,
    cr_impact: pd.DataFrame,
    audits: pd.DataFrame,
) -> pd.DataFrame:
    """
    Pareto weighted by operational impact, not just frequency.

    Impact Score = Fail_Count × Severity × CSAT_Gap_Factor × FCR_Gap_Factor

    CSAT_Gap_Factor = max(1, (85 − avg_CSAT_of_CRs_with_this_error) / 10)
    FCR_Gap_Factor  = max(1, (recontact_rate_of_CR − 5.44) / 5)

    This ensures high-frequency low-impact errors rank lower than
    errors that correlate with CSAT/FCR degradation.
    """
    if errors.empty:
        return pd.DataFrame()

    err_cr = (
        errors.groupby(["Error_Category", "Is_Critical", "CR_Lv4"])
        .agg(Fail_Count=("Audit_ID", "count"))
        .reset_index()
    )

    cr_imp = cr_impact.set_index("CR_Lv4") if not cr_impact.empty else pd.DataFrame()

    impact_rows = []
    for (cat, critical), grp in err_cr.groupby(["Error_Category", "Is_Critical"]):
        total_fails = grp["Fail_Count"].sum()
        severity = 3.0 if critical else 1.0

        csat_gaps, fcr_gaps = [], []
        for _, row in grp.iterrows():
            cr = row["CR_Lv4"]
            if cr in cr_imp.index:
                csat_val = cr_imp.loc[cr, "CSAT_Pct"]
                if pd.notna(csat_val):
                    csat_gaps.append(max(1.0, (CSAT_GOAL - csat_val) / 10))
                rc_val = cr_imp.loc[cr, "Recontact_Rate"]
                if pd.notna(rc_val):
                    fcr_gaps.append(max(1.0, (rc_val - RECONTACT_GOAL) / 5))

        csat_factor = np.mean(csat_gaps) if csat_gaps else 1.0
        fcr_factor = np.mean(fcr_gaps) if fcr_gaps else 1.0
        impact = total_fails * severity * csat_factor * fcr_factor

        impact_rows.append(
            {
                "Error_Category": cat,
                "Is_Critical": critical,
                "Fail_Count": total_fails,
                "Severity": severity,
                "CSAT_Impact_Factor": round(csat_factor, 2),
                "FCR_Impact_Factor": round(fcr_factor, 2),
                "Impact_Score": round(impact, 1),
            }
        )

    df = pd.DataFrame(impact_rows).sort_values("Impact_Score", ascending=False)
    df["Cumulative_Pct"] = (df["Impact_Score"].cumsum() / df["Impact_Score"].sum() * 100).round(1)
    return df


def cr_level_metrics(
    audits: pd.DataFrame, csat: pd.DataFrame, recontact: pd.DataFrame
) -> pd.DataFrame:
    """One row per contact reason Lv4 (detail). Outer join so a filter that
    removes one source does not blank the other pairs."""

    def _key(frame: pd.DataFrame, col: str = "CR_Lv4") -> pd.Series:
        return frame[col].astype(str).str.strip().str.casefold()

    frames: list[pd.DataFrame] = []

    if not audits.empty and "CR_Lv4" in audits.columns:
        qa = audits.copy()
        qa["_key"] = _key(qa)
        qa_cr = (
            qa.groupby("_key", as_index=False)
            .agg(CR_Lv4=("CR_Lv4", "first"), QA_Score=("Score_Pct", "mean"), QA_N=("Audit_ID", "count"))
        )
        qa_cr = qa_cr[qa_cr["QA_N"] >= 3]
        frames.append(qa_cr)

    if not csat.empty and "CR_Lv4" in csat.columns:
        cs = csat.copy()
        cs["_key"] = _key(cs)
        csat_cr = (
            cs.groupby("_key", as_index=False)
            .agg(
                CR_Lv4_csat=("CR_Lv4", "first"),
                Feedback=("Feedback CNT", "sum"),
                Satisfied=("Satisfied_CNT", "sum"),
            )
        )
        csat_cr["CSAT_Pct"] = np.where(
            csat_cr["Feedback"] > 0,
            csat_cr["Satisfied"] / csat_cr["Feedback"] * 100,
            np.nan,
        )
        frames.append(csat_cr)

    if not recontact.empty and "CR_Lv4" in recontact.columns:
        rc = recontact.copy()
        rc["_key"] = _key(rc)
        rc_cr = (
            rc.groupby("_key", as_index=False)
            .agg(
                CR_Lv4_rc=("CR_Lv4", "first"),
                Contacts=("Contacts", "sum"),
                Recontacts=("Recontact Volume", "sum"),
            )
        )
        rc_cr["Recontact_Rate"] = np.where(
            rc_cr["Contacts"] > 0,
            rc_cr["Recontacts"] / rc_cr["Contacts"] * 100,
            np.nan,
        )
        frames.append(rc_cr)

    if not frames:
        return pd.DataFrame()

    merged = frames[0]
    for extra in frames[1:]:
        merged = merged.merge(extra, on="_key", how="outer")
    if "CR_Lv4" in merged.columns:
        name = merged["CR_Lv4"]
    else:
        name = pd.Series(np.nan, index=merged.index)
    for alt in ("CR_Lv4_csat", "CR_Lv4_rc"):
        if alt in merged.columns:
            name = name.fillna(merged[alt])
    merged["CR_Lv4"] = name
    drop = [c for c in ("_key", "CR_Lv4_csat", "CR_Lv4_rc") if c in merged.columns]
    return merged.drop(columns=drop)


def cr_join_coverage(
    audits: pd.DataFrame, csat: pd.DataFrame, recontact: pd.DataFrame, min_qa: int = 3,
) -> dict:
    """How many Lv4 names sit in each source, and how many names are shared."""

    def _names(df: pd.DataFrame) -> set[str]:
        if df is None or df.empty or "CR_Lv4" not in df.columns:
            return set()
        return set(df["CR_Lv4"].dropna().astype(str).str.strip().str.casefold())

    qa_n = pd.Series(dtype=int)
    if not audits.empty and "CR_Lv4" in audits.columns:
        qa_n = audits.groupby(audits["CR_Lv4"].astype(str).str.strip().str.casefold())["Audit_ID"].count()
        qa = set(qa_n[qa_n >= min_qa].index)
    else:
        qa = set()
    cs = _names(csat)
    rc = _names(recontact)
    return {
        "min_qa": min_qa,
        "qa_n": len(qa),
        "csat_n": len(cs),
        "rc_n": len(rc),
        "qa_csat": len(qa & cs),
        "qa_rc": len(qa & rc),
        "csat_rc": len(cs & rc),
        "all_three": len(qa & cs & rc),
    }


def correlation_matrix(audits: pd.DataFrame, csat: pd.DataFrame, recontact: pd.DataFrame) -> pd.DataFrame:
    """Agent/CR-level correlation between QA, CSAT proxy, and FCR proxy."""
    qa_cr = audits.groupby("CR_Lv4").agg(QA_Score=("Score_Pct", "mean")).reset_index()

    csat_cr = (
        csat.groupby("CR_Lv4")
        .apply(lambda g: g["Satisfied_CNT"].sum() / g["Feedback CNT"].sum() * 100 if g["Feedback CNT"].sum() else np.nan)
        .reset_index(name="CSAT_Pct")
    )

    rc = (
        recontact.groupby("CR_Lv4")
        .agg(Recontacts=("Recontact Volume", "sum"), Contacts=("Contacts", "sum"))
        .reset_index()
    )
    rc["FCR_Pct"] = np.where(
        rc["Contacts"] > 0,
        100 - rc["Recontacts"] / rc["Contacts"] * 100,
        np.nan,
    )

    merged = qa_cr.merge(csat_cr, on="CR_Lv4").merge(rc, on="CR_Lv4").dropna()
    if len(merged) < 3:
        return pd.DataFrame()
    return merged[["QA_Score", "CSAT_Pct", "FCR_Pct"]].corr().round(3)


def kpi_summary(audits: pd.DataFrame, csat: pd.DataFrame, recontact: pd.DataFrame) -> dict:
    qa = avg_qa_score(audits)
    fatal = fatal_error_rate(audits)
    csat_val = overall_csat(csat)
    fcr = overall_fcr(recontact)
    cqi = composite_quality_index(qa, csat_val, fcr)

    weeks = sorted(audits["Week"].unique())
    prev_qa, prev_fatal = qa, fatal
    if len(weeks) >= 2:
        last, prev = weeks[-1], weeks[-2]
        last_aud = audits[audits["Week"] == last]
        prev_aud = audits[audits["Week"] == prev]
        qa_delta, qa_arrow = wow_delta(avg_qa_score(last_aud), avg_qa_score(prev_aud))
        fatal_delta, fatal_arrow = wow_delta(
            fatal_error_rate(last_aud), fatal_error_rate(prev_aud)
        )
    else:
        qa_delta, qa_arrow = 0.0, "→"
        fatal_delta, fatal_arrow = 0.0, "→"

    return {
        "qa_score": round(qa, 2),
        "fatal_rate": round(fatal, 2),
        "csat": round(csat_val, 2),
        "fcr": round(fcr, 2),
        "cqi": round(cqi, 2),
        "audit_count": len(audits),
        "agent_count": audits["Agent_ID"].nunique(),
        "qa_delta": qa_delta,
        "qa_arrow": qa_arrow,
        "fatal_delta": fatal_delta,
        "fatal_arrow": fatal_arrow,
    }


def _score_alert(score: float) -> str:
    from config import QA_AMBER, QA_GREEN, QA_RED
    if score >= QA_GREEN:
        return "green"
    if score >= QA_AMBER:
        return "amber"
    if score >= QA_RED:
        return "amber"
    return "red"


# ── Executive dashboard helpers ────────────────────────────────────────────

def _vs_goal_status(value: float, goal: float, higher_is_better: bool = True) -> str:
    diff = value - goal if higher_is_better else goal - value
    if diff >= 0:
        return "green"
    if diff >= -5:
        return "amber"
    return "red"


def week_date_range(audits: pd.DataFrame, weeks: list[str]) -> tuple[pd.Timestamp, pd.Timestamp]:
    sub = audits[audits["Week"].isin(weeks)] if weeks else audits
    if sub.empty:
        return pd.Timestamp.today(), pd.Timestamp.today()
    return sub["Fecha"].min(), sub["Fecha"].max()


def iso_week_nums(weeks: list[str] | tuple[str, ...] | None) -> set[int]:
    """W19 / 19 → ISO week 19."""
    nums: set[int] = set()
    for w in weeks or []:
        m = re.search(r"(\d+)", str(w))
        if m:
            nums.add(int(m.group(1)))
    return nums


def selected_weeks_are_all(selected, all_weeks) -> bool:
    sel = {str(w) for w in (selected or [])}
    full = {str(w) for w in (all_weeks or [])}
    return bool(sel) and bool(full) and sel == full


def cut_csat_recontact_for_weeks(
    csat: pd.DataFrame,
    recontact: pd.DataFrame,
    weeks_sel,
    all_weeks,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    CSAT and recontact follow the Date filter on their own calendar, not QA
    audit weekdays. With every QA week selected, keep the official snapshot
    (77,266 surveys / 5.83 recontact), including 1–3 May and 31 May.
    """
    if selected_weeks_are_all(weeks_sel, all_weeks):
        return csat, recontact
    return filter_by_iso_weeks(csat, weeks_sel), filter_by_iso_weeks(recontact, weeks_sel)


def filter_by_iso_weeks(df: pd.DataFrame, weeks: list[str], date_col: str = "Fecha") -> pd.DataFrame:
    """Cut CSAT / recontact on their own calendar weeks, not QA audit weekdays."""
    if df.empty or date_col not in df.columns:
        return df
    nums = iso_week_nums(weeks)
    if not nums:
        return df.iloc[0:0].copy()
    iso = pd.to_datetime(df[date_col], errors="coerce").dt.isocalendar().week.astype("Int64")
    return df[iso.isin(nums)]


def calendar_days_in_scope(
    audits: pd.DataFrame,
    csat: pd.DataFrame,
    recontact: pd.DataFrame,
    weeks_sel,
    all_weeks,
) -> list[str]:
    """Calendar dates (YYYY-MM-DD) in the selected weeks, union of the three sources."""
    if not weeks_sel:
        return []
    if selected_weeks_are_all(weeks_sel, all_weeks):
        frames = [audits, csat, recontact]
    else:
        a = audits
        if audits is not None and not audits.empty and "Week" in audits.columns:
            a = audits[audits["Week"].astype(str).isin([str(w) for w in weeks_sel])]
        frames = [a, filter_by_iso_weeks(csat, weeks_sel), filter_by_iso_weeks(recontact, weeks_sel)]
    days: set = set()
    for df in frames:
        if df is None or df.empty or "Fecha" not in df.columns:
            continue
        ser = pd.to_datetime(df["Fecha"], errors="coerce").dt.date.dropna()
        days.update(ser.tolist())
    return [d.isoformat() for d in sorted(days)]


def filter_by_calendar_day(df: pd.DataFrame, day: str, date_col: str = "Fecha") -> pd.DataFrame:
    """Cut one source to a single calendar date on its own Fecha."""
    if not day or str(day) == "All" or df is None or df.empty or date_col not in df.columns:
        return df if df is not None else pd.DataFrame()
    target = pd.to_datetime(day, errors="coerce")
    if pd.isna(target):
        return df
    want = target.date()
    return df[pd.to_datetime(df[date_col], errors="coerce").dt.date == want]


def analysis_date_span(
    frames: list[pd.DataFrame],
    weeks_sel,
    all_weeks,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Header period: full snapshot when every QA week is on, else those ISO weeks."""
    usable = [df for df in frames if df is not None and not df.empty and "Fecha" in df.columns]
    if not usable:
        return pd.Timestamp.today(), pd.Timestamp.today()
    if selected_weeks_are_all(weeks_sel, all_weeks):
        mins = [pd.to_datetime(df["Fecha"]).min() for df in usable]
        maxs = [pd.to_datetime(df["Fecha"]).max() for df in usable]
        return min(mins), max(maxs)
    nums = iso_week_nums(weeks_sel)
    dates: list[pd.Timestamp] = []
    for df in usable:
        iso = pd.to_datetime(df["Fecha"], errors="coerce").dt.isocalendar().week.astype("Int64")
        sub = df.loc[iso.isin(nums), "Fecha"]
        if not sub.empty:
            dates.append(pd.to_datetime(sub).min())
            dates.append(pd.to_datetime(sub).max())
    if not dates:
        return pd.to_datetime(usable[0]["Fecha"]).min(), pd.to_datetime(usable[0]["Fecha"]).max()
    return min(dates), max(dates)


def filter_csat_by_period(csat: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    if csat.empty or "Fecha" not in csat.columns:
        return csat
    mask = (csat["Fecha"] >= start) & (csat["Fecha"] <= end + pd.Timedelta(days=1))
    return csat[mask]


def filter_recontact_by_period(recontact: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    if recontact.empty or "Fecha" not in recontact.columns:
        return recontact
    mask = (recontact["Fecha"] >= start) & (recontact["Fecha"] <= end + pd.Timedelta(days=1))
    return recontact[mask]


def volume_totals(audits: pd.DataFrame, csat: pd.DataFrame, recontact: pd.DataFrame) -> dict:
    return {
        "contacts": int(recontact["Contacts"].sum()) if not recontact.empty else 0,
        "recontacts": (
            int(pd.to_numeric(recontact["Recontact Volume"], errors="coerce").fillna(0).sum())
            if not recontact.empty and "Recontact Volume" in recontact.columns
            else 0
        ),
        "surveys": int(csat["Feedback CNT"].sum()) if not csat.empty else 0,
        "evaluations": len(audits),
    }


def daily_metrics_trend(
    audits: pd.DataFrame,
    csat: pd.DataFrame,
    recontact: pd.DataFrame,
) -> pd.DataFrame:
    """Daily QA, CSAT and Recontact for combined trend chart."""
    frames = []
    if not audits.empty:
        qa_d = (
            audits.groupby(audits["Fecha"].dt.date)
            .agg(QA_Score=("Score_Pct", "mean"))
            .reset_index()
            .rename(columns={"Fecha": "Date"})
        )
        frames.append(qa_d.set_index("Date"))

    if not csat.empty and "Fecha" in csat.columns:
        csat_d = (
            csat.groupby(csat["Fecha"].dt.date)
            .apply(lambda g: g["Satisfied_CNT"].sum() / g["Feedback CNT"].sum() * 100
                   if g["Feedback CNT"].sum() else np.nan)
            .reset_index(name="CSAT_Score")
            .rename(columns={"Fecha": "Date"})
        )
        frames.append(csat_d.set_index("Date"))

    if not recontact.empty and "Fecha" in recontact.columns:
        rc_d = (
            recontact.groupby(recontact["Fecha"].dt.date)
            .apply(lambda g: g["Recontact Volume"].sum() / g["Contacts"].sum() * 100
                   if g["Contacts"].sum() else np.nan)
            .reset_index(name="Recontact_Rate")
            .rename(columns={"Fecha": "Date"})
        )
        frames.append(rc_d.set_index("Date"))

    if not frames:
        return pd.DataFrame(columns=["Date", "QA_Score", "CSAT_Score", "Recontact_Rate"])

    merged = pd.concat(frames, axis=1).reset_index()
    merged["Date"] = pd.to_datetime(merged["Date"])
    return merged.sort_values("Date").reset_index(drop=True)


def channel_performance(
    audits: pd.DataFrame,
    csat: pd.DataFrame,
    recontact: pd.DataFrame,
) -> pd.DataFrame:
    """QA / CSAT / Recontact by channel + overall row."""
    rows: list[dict] = []

    channel_map_csat = {"Phone": "Phone", "Live Chat": "Live Chat", "Chat": "Live Chat"}
    channel_map_rc = {"Phone": "Phone", "Live Chat": "Live Chat", "Chat": "Live Chat"}

    channels = [("Phone", "PHONE"), ("Live Chat", "LIVE CHAT")]
    for label, _token in channels:
        qa_sub = audits[channel_match(audits["Channel"], label)] if "Channel" in audits.columns else audits.iloc[0:0]
        qa_val = qa_sub["Score_Pct"].mean() if not qa_sub.empty else np.nan

        if "Channel" in csat.columns and not csat.empty:
            cs = csat[channel_match(csat["Channel"], label)]
            csat_val = cs["Satisfied_CNT"].sum() / cs["Feedback CNT"].sum() * 100 if cs["Feedback CNT"].sum() else np.nan
        else:
            csat_val = np.nan

        rc_col = "standard_channel_name" if "standard_channel_name" in recontact.columns else (
            "Channel" if "Channel" in recontact.columns else None
        )
        if rc_col and not recontact.empty:
            rc = recontact[channel_match(recontact[rc_col], label)]
            rc_val = recontact_rate(rc) if not rc.empty and rc["Contacts"].sum() else np.nan
        else:
            rc_val = np.nan

        qa_n = int(len(qa_sub))
        if qa_n == 0 and pd.isna(qa_val) and pd.isna(csat_val) and pd.isna(rc_val):
            continue
        rows.append({
            "Segment": label, "QA_Score": qa_val, "CSAT_Score": csat_val,
            "Recontact_Rate": rc_val, "QA_N": qa_n,
        })

    qa_all = audits["Score_Pct"].mean()
    csat_all = csat["Satisfied_CNT"].sum() / csat["Feedback CNT"].sum() * 100 if not csat.empty and csat["Feedback CNT"].sum() else np.nan
    rc_all = recontact_rate(recontact) if not recontact.empty else np.nan
    rows.append({
        "Segment": "Overall", "QA_Score": qa_all, "CSAT_Score": csat_all,
        "Recontact_Rate": rc_all, "QA_N": int(len(audits)),
    })

    df = pd.DataFrame(rows)
    for col, goal, hib in [
        ("QA_Score", QA_GOAL, True),
        ("CSAT_Score", CSAT_GOAL, True),
        ("Recontact_Rate", RECONTACT_GOAL, False),
    ]:
        df[f"{col}_vs"] = df[col].apply(lambda v: round(v - goal, 2) if pd.notna(v) else np.nan)
        df[f"{col}_status"] = df[col].apply(lambda v: _vs_goal_status(v, goal, hib) if pd.notna(v) else "neutral")
    total_n = df.loc[df["Segment"] != "Overall", "QA_N"].sum()
    df["QA_Share"] = df.apply(
        lambda r: round(r["QA_N"] / total_n * 100, 1) if r["Segment"] != "Overall" and total_n else (100.0 if r["Segment"] == "Overall" else np.nan),
        axis=1,
    )
    body = df[df["Segment"] != "Overall"].sort_values("QA_Score", ascending=True)
    overall = df[df["Segment"] == "Overall"]
    return pd.concat([body, overall], ignore_index=True)


def market_performance(
    audits: pd.DataFrame,
    csat: pd.DataFrame,
    recontact: pd.DataFrame,
) -> pd.DataFrame:
    """QA / CSAT by market (country). Recontact has no country field — always SSL."""
    from config import COUNTRY_NAMES

    csat_country_col = "Country Code" if csat is not None and not csat.empty and "Country Code" in csat.columns else None
    qa_codes = (
        set(audits["Country"].dropna().astype(str).str.strip())
        if audits is not None and not audits.empty and "Country" in audits.columns
        else set()
    )
    csat_codes = (
        set(csat[csat_country_col].dropna().astype(str).str.strip())
        if csat_country_col
        else set()
    )
    countries = sorted(qa_codes | csat_codes)
    rows: list[dict] = []

    for country in countries:
        if audits is not None and not audits.empty and "Country" in audits.columns:
            qa_sub = audits[audits["Country"].astype(str).str.strip() == country]
        else:
            qa_sub = pd.DataFrame()
        qa_val = qa_sub["Score_Pct"].mean() if qa_sub is not None and not qa_sub.empty and "Score_Pct" in qa_sub.columns else np.nan
        qa_n = int(len(qa_sub)) if qa_sub is not None and not qa_sub.empty else 0

        if csat_country_col:
            cs = csat[csat[csat_country_col].astype(str).str.strip() == country]
            csat_n = int(pd.to_numeric(cs["Feedback CNT"], errors="coerce").fillna(0).sum()) if not cs.empty and "Feedback CNT" in cs.columns else 0
            csat_val = (
                cs["Satisfied_CNT"].sum() / cs["Feedback CNT"].sum() * 100
                if csat_n and cs["Feedback CNT"].sum()
                else np.nan
            )
        else:
            csat_val = np.nan
            csat_n = 0

        rows.append({
            "Segment": country,
            "Country": country,
            "Country_Name": COUNTRY_NAMES.get(country, country),
            "QA_Score": qa_val,
            "CSAT_Score": csat_val,
            "Recontact_Rate": np.nan,
            "QA_N": qa_n,
            "CSAT_N": csat_n,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    for col, goal, hib in [
        ("QA_Score", QA_GOAL, True),
        ("CSAT_Score", CSAT_GOAL, True),
        ("Recontact_Rate", RECONTACT_GOAL, False),
    ]:
        df[f"{col}_vs"] = df[col].apply(lambda v: round(v - goal, 2) if pd.notna(v) else np.nan)
        df[f"{col}_status"] = df[col].apply(lambda v: _vs_goal_status(v, goal, hib) if pd.notna(v) else "neutral")
    return df.sort_values("Country_Name").reset_index(drop=True)


def recontact_by_cr(recontact: pd.DataFrame, top_n: int = 6) -> pd.DataFrame:
    if recontact.empty:
        return pd.DataFrame()
    g = (
        recontact.groupby("CR_Lv4")
        .agg(Recontacts=("Recontact Volume", "sum"), Contacts=("Contacts", "sum"))
        .reset_index()
    )
    g["Pct"] = (g["Recontacts"] / g["Recontacts"].sum() * 100).round(1)
    g["Recontact_Rate"] = np.where(
        g["Contacts"] > 0,
        (g["Recontacts"] / g["Contacts"] * 100).round(2),
        np.nan,
    )
    return g.sort_values("Recontacts", ascending=False).head(top_n)


def contact_volume_by_cr(
    recontact: pd.DataFrame,
    *,
    level: str = "lv4",
    lookup: dict | None = None,
    top_n: int = 10,
) -> pd.DataFrame:
    """Share of official Contacts by contact reason. Not CSAT surveys, not repeat volume."""
    if recontact is None or recontact.empty or "CR_Lv4" not in recontact.columns:
        return pd.DataFrame()
    if "Contacts" not in recontact.columns:
        return pd.DataFrame()
    work = recontact.copy()
    if level == "lv1":
        work["_cat"] = map_cr_group(work["CR_Lv4"], lookup or {})
        cat_name = "CR_Lv1"
    else:
        work["_cat"] = work["CR_Lv4"].astype(str).str.strip()
        cat_name = "CR_Lv4"
    work = work[work["_cat"].astype(str).str.strip().ne("") & work["_cat"].astype(str).str.casefold().ne("nan")]
    if work.empty:
        return pd.DataFrame()
    g = (
        work.groupby("_cat", dropna=False)
        .agg(
            Contacts=("Contacts", "sum"),
            Recontacts=("Recontact Volume", "sum") if "Recontact Volume" in work.columns else ("Contacts", "sum"),
        )
        .reset_index()
        .rename(columns={"_cat": cat_name})
    )
    g = g[pd.to_numeric(g["Contacts"], errors="coerce").fillna(0) > 0]
    if g.empty:
        return g
    total = float(g["Contacts"].sum())
    g["Pct"] = (g["Contacts"] / total * 100).round(1) if total else 0.0
    g = g.sort_values("Contacts", ascending=False)
    if top_n is not None:
        g = g.head(int(top_n))
    return g.reset_index(drop=True)


def recontact_by_std_channel(recontact: pd.DataFrame) -> pd.DataFrame:
    """Recontact volume by standard_channel_name. Official rate is still the 12-channel mix."""
    col = "standard_channel_name"
    if recontact.empty or col not in recontact.columns:
        return pd.DataFrame()
    g = (
        recontact.groupby(col, dropna=False)
        .agg(Count=("Recontact Volume", "sum"), Contacts=("Contacts", "sum"))
        .reset_index()
        .rename(columns={col: "Cat"})
    )
    g["Rate"] = np.where(g["Contacts"] > 0, (g["Count"] / g["Contacts"] * 100).round(2), np.nan)
    return g.sort_values("Count", ascending=False)


def recontact_channel_table(recontact: pd.DataFrame) -> pd.DataFrame:
    """One row per recontact channel plus an official-mix total. Ratio of sums, never averaged."""
    raw = recontact_by_std_channel(recontact)
    if raw.empty:
        return pd.DataFrame()
    total_contacts = float(raw["Contacts"].sum())
    total_repeats = float(raw["Count"].sum())
    rows = []
    for _, row in raw.iterrows():
        key = str(row["Cat"]).strip().upper()
        contacts = float(row["Contacts"]) if pd.notna(row["Contacts"]) else 0.0
        repeats = float(row["Count"]) if pd.notna(row["Count"]) else 0.0
        rate = float(row["Rate"]) if pd.notna(row.get("Rate")) else float("nan")
        if key == SELF_HELP_CHANNEL:
            role, in_qa = "Self-service", "No"
        elif key in AUDITED_RC_CHANNELS:
            role, in_qa = "Audited", "Yes"
        else:
            role, in_qa = "Other", "No"
        rows.append({
            "Channel": normalize_channel_label(row["Cat"]),
            "Contacts": int(contacts),
            "Repeats": int(repeats),
            "Rate %": None if pd.isna(rate) else round(rate, 2),
            "Share of contacts %": round(contacts / total_contacts * 100, 1) if total_contacts else 0.0,
            "Share of repeats %": round(repeats / total_repeats * 100, 1) if total_repeats else 0.0,
            "vs 5.44": None if pd.isna(rate) else round(rate - RECONTACT_GOAL, 2),
            "Also in QA / CSAT": in_qa,
            "Role": role,
        })
    official_rate = (total_repeats / total_contacts * 100) if total_contacts else float("nan")
    rows.append({
        "Channel": "All 12 (official mix)",
        "Contacts": int(total_contacts),
        "Repeats": int(total_repeats),
        "Rate %": None if pd.isna(official_rate) else round(official_rate, 2),
        "Share of contacts %": 100.0 if total_contacts else 0.0,
        "Share of repeats %": 100.0 if total_repeats else 0.0,
        "vs 5.44": None if pd.isna(official_rate) else round(official_rate - RECONTACT_GOAL, 2),
        "Also in QA / CSAT": "Mix",
        "Role": "Official KPI",
    })
    return pd.DataFrame(rows)


def top_failing_attributes(
    errors: pd.DataFrame,
    audits: pd.DataFrame,
    top_n: int = 8,
) -> pd.DataFrame:
    if errors.empty or audits.empty:
        return pd.DataFrame()

    overall_qa = audits["Score_Pct"].mean()
    total_fails = len(errors)
    total_audits = len(audits)

    agg = errors.groupby("Error_Category").agg(
        Fail_Count=("Audit_ID", "count"),
        Audit_IDs=("Audit_ID", lambda x: set(x)),
        Is_Critical=("Is_Critical", "any"),
    ).reset_index()

    impacts = []
    for _, row in agg.iterrows():
        ids = row["Audit_IDs"]
        score_when_fail = audits[audits["Audit_ID"].isin(ids)]["Score_Pct"].mean()
        fail_share = row["Fail_Count"] / total_fails * 100
        impact_pp = (overall_qa - score_when_fail) * (len(ids) / total_audits)
        impacts.append({
            "Error_Category": row["Error_Category"],
            "Fail_Count": row["Fail_Count"],
            "Pct_Of_Fails": round(fail_share, 1),
            "Impact_pp": round(-abs(impact_pp), 2),
            "Is_Critical": bool(row["Is_Critical"]),
        })

    df = pd.DataFrame(impacts).sort_values("Fail_Count", ascending=False).head(top_n)
    return df


def qa_score_by_cr(audits: pd.DataFrame, top_n: int | None = 10, min_n: int = 3) -> pd.DataFrame:
    """Official QA (mean of Score_Pct) by contact reason Lv4. Lowest scores first."""
    if audits.empty:
        return pd.DataFrame()
    g = (
        audits.groupby("CR_Lv4")
        .agg(QA_Score=("Score_Pct", "mean"), N=("Audit_ID", "count"))
        .reset_index()
    )
    if min_n:
        g = g[g["N"] >= int(min_n)]
    if g.empty:
        return g
    g["QA_Score"] = g["QA_Score"].round(1)
    g["vs_goal"] = (g["QA_Score"] - QA_GOAL).round(1)
    g["status"] = g["QA_Score"].apply(lambda v: _vs_goal_status(v, QA_GOAL, True))
    g = g.sort_values("QA_Score", ascending=True)
    if top_n is not None:
        g = g.head(int(top_n))
    return g.reset_index(drop=True)


CR_UNMAPPED = "Not mapped"


def cr_group_lookup(csat: pd.DataFrame) -> dict[str, str]:
    """Contact-reason group (Lv1) keyed by casefolded detail (Lv4), from CSAT.

    QA and Recontact do not carry a group column. This is a lookup from real
    CSAT columns, not a new KPI. Unmapped details stay ``Not mapped``.
    """
    if csat.empty or "CR_Lv4" not in csat.columns:
        return {}
    lv1_col = "CR_Lv1" if "CR_Lv1" in csat.columns else ("CR Lv1" if "CR Lv1" in csat.columns else None)
    if lv1_col is None:
        return {}
    tmp = pd.DataFrame({
        "k": csat["CR_Lv4"].astype(str).str.strip().str.casefold(),
        "g": csat[lv1_col].astype(str).str.strip(),
    })
    tmp = tmp[tmp["k"].ne("") & tmp["g"].ne("") & tmp["g"].str.lower().ne("nan")]
    if tmp.empty:
        return {}
    return (
        tmp.groupby("k")["g"]
        .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0])
        .to_dict()
    )


def map_cr_group(series: pd.Series, lookup: dict[str, str]) -> pd.Series:
    keys = series.astype(str).str.strip().str.casefold()
    mapped = keys.map(lookup)
    blank = mapped.isna() | (mapped.astype(str).str.strip() == "")
    return mapped.mask(blank, CR_UNMAPPED)


def qa_fails_by_cr(errors: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
    """Attribute-fail counts by contact-reason detail. Not a new KPI formula."""
    if errors.empty or "CR_Lv4" not in errors.columns:
        return pd.DataFrame()
    g = errors.groupby("CR_Lv4", as_index=False).agg(Fail_Count=("Audit_ID", "count"))
    total = float(g["Fail_Count"].sum())
    g["Pct"] = (g["Fail_Count"] / total * 100).round(1) if total else 0.0
    return g.sort_values("Fail_Count", ascending=False).head(top_n).reset_index(drop=True)


def qa_fails_by_cr_group(errors: pd.DataFrame, lookup: dict[str, str]) -> pd.DataFrame:
    """Attribute-fail counts by contact-reason group (CSAT Lv1 lookup)."""
    if errors.empty or "CR_Lv4" not in errors.columns:
        return pd.DataFrame()
    df = errors.copy()
    df["CR_Lv1"] = map_cr_group(df["CR_Lv4"], lookup)
    g = df.groupby("CR_Lv1", as_index=False).agg(Fail_Count=("Audit_ID", "count"))
    total = float(g["Fail_Count"].sum())
    g["Pct"] = (g["Fail_Count"] / total * 100).round(1) if total else 0.0
    return g.sort_values("Fail_Count", ascending=False).reset_index(drop=True)


def recontact_by_cr_group(recontact: pd.DataFrame, lookup: dict[str, str]) -> pd.DataFrame:
    """Official recontact (ratio of sums) sliced by contact-reason group."""
    if recontact.empty or "CR_Lv4" not in recontact.columns:
        return pd.DataFrame()
    df = recontact.copy()
    df["CR_Lv1"] = map_cr_group(df["CR_Lv4"], lookup)
    g = (
        df.groupby("CR_Lv1")
        .agg(Recontacts=("Recontact Volume", "sum"), Contacts=("Contacts", "sum"))
        .reset_index()
    )
    total = float(g["Recontacts"].sum())
    g["Pct"] = (g["Recontacts"] / total * 100).round(1) if total else 0.0
    g["Recontact_Rate"] = np.where(
        g["Contacts"] > 0,
        (g["Recontacts"] / g["Contacts"] * 100).round(2),
        np.nan,
    )
    return g.sort_values("Recontacts", ascending=False).reset_index(drop=True)


def attach_cr_group(df: pd.DataFrame, lookup: dict[str, str], lv4_col: str = "CR_Lv4") -> pd.DataFrame:
    if df.empty or lv4_col not in df.columns:
        return df
    out = df.copy()
    out["CR_Lv1"] = map_cr_group(out[lv4_col], lookup)
    return out


def csat_by_star_rating(csat: pd.DataFrame) -> pd.DataFrame:
    if csat.empty:
        return pd.DataFrame()
    star_cols = {
        "5 Stars": "Questionnaires With Star Level =5",
        "4 Stars": "Questionnaires With Star Level =4",
        "3 Stars": "Questionnaires With Star Level =3",
        "2 Stars": "Questionnaires With Star Level =2",
        "1 Star": "Questionnaires With Star Level =1",
    }
    rows = []
    total = csat["Feedback CNT"].sum()
    for label, col in star_cols.items():
        cnt = csat[col].sum() if col in csat.columns else 0
        rows.append({"Rating": label, "Count": int(cnt), "Pct": round(cnt / total * 100, 1) if total else 0})
    return pd.DataFrame(rows)


VOC_THEME_RULES: list[tuple[str, list[str]]] = [
    ("Refund / compensation not received", ["reembolso", "refund", "compens", "devol", "dinero", "cobro"]),
    ("Driver behavior", ["conductor", "driver", "repat", "grosero", "mal educado", "repartidor", "motorizado"]),
    ("Long wait time", ["espera", "demora", "tardo", "demor", "mucho tiempo", "lento"]),
    ("No solution provided", [
        "no resolv", "no resuelv", "no solucion", "no me solucion", "solucionaron",
        "no me ayud", "no me dieron", "no me dio", "no sirven", "no sirvi",
        "no me resolv", "no hubo soluc", "no se resolv", "sin solucion",
        "no me atend", "no ayudan", "no responden",
    ]),
    ("Agent attitude", ["actitud", "pesimo servicio", "mal trato", "groser", "prepotente"]),
    ("Order / trip issues", ["pedido", "orden", "viaje", "trip", "order", "entrega"]),
    ("Poor service", ["pesimo", "mal servicio", "horrible", "ladron", "estafa", "robaron", " me rob", "terrible"]),
]
VOC_PRAISE_RULES: list[tuple[str, list[str]]] = [
    ("Thanks", ["gracias"]),
    ("Good service / attention", [
        "excelente", "exelente", "buen servicio", "buena atenci", "buenas atenci",
        "muy buen", "muy bien", " amable", "atent", "perfecto", "todo bien",
        "eficiente", "10/10", "profesional", "rapido", " bien ", " bueno ", " buena ",
        "increible", "me sirvi",
    ]),
]


def _fold_voc(text: str) -> str:
    raw = unicodedata.normalize("NFKD", str(text).lower())
    return "".join(ch for ch in raw if not unicodedata.combining(ch))


def _voc_blob(text: str) -> str:
    return f" {_fold_voc(text)} "


def _classify_voc(text: str) -> str | None:
    if not text or str(text).strip().lower() in ("other", "nan", ""):
        return None
    folded = _fold_voc(text).strip()
    if folded in {"mal", "muy mal", "pesimo", "horrible", "terrible"}:
        return "Poor service"
    blob = _voc_blob(text)
    for theme, keywords in VOC_THEME_RULES:
        if any(_fold_voc(k) in blob for k in keywords):
            return theme
    return None


def _classify_comment(text: str) -> str | None:
    """Negative theme first, then praise. None = still a real comment, unclassified."""
    hit = _classify_voc(text)
    if hit:
        return hit
    if not text or str(text).strip().lower() in ("other", "nan", ""):
        return None
    folded = _fold_voc(text).strip()
    if folded in {"mal", "muy mal", "pesimo", "horrible", "terrible"}:
        return "Poor service"
    if folded in {"bien", "muy bien", "bueno", "buena", "perfecto", "increible"}:
        return "Good service / attention"
    blob = _voc_blob(text)
    for theme, keywords in VOC_PRAISE_RULES:
        if any(_fold_voc(k) in blob for k in keywords):
            return theme
    return None


def _real_comment_mask(s: pd.Series) -> pd.Series:
    strip = s.astype(str).str.strip()
    cf = strip.str.casefold()
    return s.notna() & ~cf.isin(_VOC_PLACEHOLDER) & ~strip.str.fullmatch(r"[\d.,]+", na=False)


def voc_themes_negative(csat: pd.DataFrame, top_n: int = 6) -> pd.DataFrame:
    """Themes from 1–3★ surveys that left a real comment. Not the all-comment pie."""
    if csat.empty:
        return pd.DataFrame()

    star_cols = [
        "Questionnaires With Star Level =1",
        "Questionnaires With Star Level =2",
        "Questionnaires With Star Level =3",
    ]
    present = [c for c in star_cols if c in csat.columns]
    if present:
        neg = csat[present].sum(axis=1)
        low_mask = neg > 0
    else:
        neg = pd.Series(1, index=csat.index)
        low_mask = pd.Series(False, index=csat.index)
    n_low_surveys = int(neg.sum()) if present else 0
    low = csat.loc[low_mask].copy()
    if low.empty:
        return pd.DataFrame()
    low["Neg"] = neg.loc[low.index].astype(float)
    if "open_question" in low.columns:
        low = low.loc[_real_comment_mask(low["open_question"])].copy()
    if low.empty:
        return pd.DataFrame()

    low["Theme"] = low["open_question"].astype(str).map(_classify_voc)
    themed = low[low["Theme"].notna()]
    if themed.empty:
        return pd.DataFrame()

    n_low = int(low["Neg"].sum())
    n_tagged = int(themed["Neg"].sum())
    g = themed.groupby("Theme", as_index=False).agg(
        Mentions=("Neg", "sum"),
        Rows=("Theme", "size"),
    )
    g["Mentions"] = g["Mentions"].round(0).astype(int)
    g["Total_Low"] = n_low
    g["Total_Low_Surveys"] = n_low_surveys
    g["Total_Tagged"] = n_tagged
    g["Pct"] = (g["Mentions"] / n_low * 100).round(1) if n_low else 0.0
    g["Pct_Tagged"] = (g["Mentions"] / n_tagged * 100).round(1) if n_tagged else 0.0
    return g.sort_values("Mentions", ascending=False).head(top_n)


_POS_THEMES = {name for name, _ in VOC_PRAISE_RULES}


def _comment_polarity(text: str) -> str | None:
    """Positive / Negative from the comment text. None if the text is unclear."""
    theme = _classify_comment(text)
    if theme is None:
        return None
    return "Positive" if theme in _POS_THEMES else "Negative"


def voc_all_comments(csat: pd.DataFrame, top_n: int = 7) -> dict:
    """All surveys with a readable comment (Other skipped), split positive vs negative."""
    empty = {
        "polarity": pd.DataFrame(),
        "n_real": 0,
        "n_positive": 0,
        "n_negative": 0,
        "n_from_text": 0,
    }
    if csat is None or csat.empty or "open_question" not in csat.columns:
        return empty
    work = csat.loc[_real_comment_mask(csat["open_question"])].copy()
    if work.empty:
        return empty
    work["_fb"] = pd.to_numeric(work.get("Feedback CNT", 1), errors="coerce").fillna(1)
    neg_cols = [
        "Questionnaires With Star Level =1",
        "Questionnaires With Star Level =2",
        "Questionnaires With Star Level =3",
    ]
    pos_cols = [
        "Questionnaires With Star Level =4",
        "Questionnaires With Star Level =5",
    ]
    work["_neg"] = work[neg_cols].sum(axis=1) if all(c in work.columns for c in neg_cols) else 0
    work["_pos"] = work[pos_cols].sum(axis=1) if all(c in work.columns for c in pos_cols) else 0
    work["_text"] = work["open_question"].astype(str).map(_comment_polarity)
    n_from_text = int(work.loc[work["_text"].notna(), "_fb"].sum())
    star = pd.Series(pd.NA, index=work.index, dtype=object)
    star = star.mask(work["_neg"] > 0, "Negative")
    star = star.mask(work["_pos"] > 0, "Positive")
    work["_pol"] = work["_text"].fillna(star)
    n_real = int(work["_fb"].sum())
    n_pos = int(work.loc[work["_pol"] == "Positive", "_fb"].sum())
    n_neg = int(work.loc[work["_pol"] == "Negative", "_fb"].sum())
    polarity = pd.DataFrame({
        "Slice": ["Negative", "Positive"],
        "Surveys": [n_neg, n_pos],
    })
    polarity = polarity[polarity["Surveys"] > 0]
    return {
        "polarity": polarity,
        "n_real": n_real,
        "n_positive": n_pos,
        "n_negative": n_neg,
        "n_from_text": n_from_text,
    }


_VOC_PLACEHOLDER = {"other", "nan", "none", "", "-", ".", "null", "<na>", "<n/a>"}
_RE_DRIVER = re.compile(r"repartidor|conductor|\bdriver\b|motorizado|courier", re.I)
_RE_AGENT_CUE = re.compile(
    r"quien me atendi|me atendi[oó]|representante|asesor|\bagente\b|soporte|\bchat\b|telefonista",
    re.I,
)
_RE_NEGATION = re.compile(
    r"nada groser|no (?:fue|es|era) groser|no fue maltrato|no me trato mal",
    re.I,
)
_RE_UNRESOLVED = re.compile(
    r"no resolv|no (?:me )?solucion|no me ayud|no me dieron|sin solucion|no sirven",
    re.I,
)
_RE_MANNER_NEG = re.compile(
    r"mal trato|malos tratos|trato (?:horrible|p[eé]simo)|"
    r"groser[oa]|me (?:alz[oó]|alzo) la voz|descort[eé]s|prepotente|"
    r"me colg[oó]|cerrar el chat|maleducad|irrespet|me (?:trato|trat[oó]) mal",
    re.I,
)
_RE_RESPECT = re.compile(r"falta de respeto", re.I)
_RE_MANNER_POS = re.compile(
    r"\bamable\b|excelente atenci|muy buena atenci|buena atenci|"
    r"muy buen servicio|buen servicio|\batent[oa]\b|profesional|emp[aá]tic",
    re.I,
)


def _clip_comment(text: object, n: int = 160) -> str:
    raw = " ".join(str(text or "").split())
    if len(raw) <= n:
        return raw
    cut = raw[: max(n - 1, 1)]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut + "…"


def _agent_supervisor_map(audits: pd.DataFrame) -> dict[str, str]:
    if audits is None or audits.empty or "Agent_ID" not in audits.columns:
        return {}
    if "Supervisor_ID" not in audits.columns:
        return {}
    tmp = audits[["Agent_ID", "Supervisor_ID"]].copy()
    tmp["_k"] = tmp["Agent_ID"].astype(str).str.strip().str.casefold()
    tmp = tmp[tmp["_k"].ne("") & tmp["_k"].ne("nan")]
    if tmp.empty:
        return {}
    first = tmp.groupby("_k", as_index=False).agg(Supervisor_ID=("Supervisor_ID", "first"))
    return dict(zip(first["_k"], first["Supervisor_ID"].astype(str)))


def filter_csat_by_supervisor(
    csat: pd.DataFrame,
    audits: pd.DataFrame,
    supervisor: str,
) -> pd.DataFrame:
    """Cut CSAT to agents that belong to a QA supervisor (name match to Agent_ID)."""
    if csat is None or csat.empty:
        return csat if csat is not None else pd.DataFrame()
    if not supervisor or str(supervisor) == "All":
        return csat
    amap = _agent_supervisor_map(audits)
    if not amap or "Agent name" not in csat.columns:
        return csat.iloc[0:0].copy()
    mapped = csat["Agent name"].astype(str).str.strip().str.casefold().map(amap)
    return csat[mapped.astype(str) == str(supervisor)].copy()


def filter_csat_by_agent(csat: pd.DataFrame, agent: str) -> pd.DataFrame:
    """Cut CSAT to surveys whose agent name matches a QA Agent_ID."""
    if csat is None or csat.empty:
        return csat if csat is not None else pd.DataFrame()
    if not agent or str(agent).strip() in {"", "All"}:
        return csat
    if "Agent name" not in csat.columns:
        return csat.iloc[0:0].copy()
    want = str(agent).strip().casefold()
    names = csat["Agent name"].astype(str).str.strip().str.casefold()
    return csat[names == want].copy()


def fail_event_totals(errors: pd.DataFrame) -> tuple[int, int]:
    """Attribute-fail events and unique audits with ≥1 fail. Same grain as the attribute Pareto."""
    if errors is None or errors.empty:
        return 0, 0
    n_events = int(len(errors))
    n_audits = int(errors["Audit_ID"].nunique()) if "Audit_ID" in errors.columns else 0
    return n_events, n_audits


def csat_unsat_totals(csat: pd.DataFrame) -> int:
    """Unsatisfied survey volume (Feedback − 4★/5★) in the current CSAT filter."""
    if csat is None or csat.empty:
        return 0
    if "Feedback CNT" not in csat.columns or "Satisfied_CNT" not in csat.columns:
        return 0
    fb = pd.to_numeric(csat["Feedback CNT"], errors="coerce").fillna(0)
    sat = pd.to_numeric(csat["Satisfied_CNT"], errors="coerce").fillna(0)
    return int((fb - sat).clip(lower=0).sum())


def _agent_sort_num(value: object) -> int:
    m = re.search(r"(\d+)", str(value or ""))
    return int(m.group(1)) if m else 10**9


def _manner_flags(text: object) -> tuple[bool, bool, bool]:
    """Return (lowlight, highlight, unresolved_only)."""
    raw = str(text or "").strip()
    if raw.casefold() in _VOC_PLACEHOLDER:
        return False, False, False
    if _RE_NEGATION.search(raw):
        low = False
    else:
        driver = bool(_RE_DRIVER.search(raw))
        agent = bool(_RE_AGENT_CUE.search(raw))
        person = bool(_RE_MANNER_NEG.search(raw))
        respect = bool(_RE_RESPECT.search(raw))
        low = (person and (agent or not driver)) or (respect and agent)
    hi = bool(_RE_MANNER_POS.search(raw))
    unresolved = bool(_RE_UNRESOLVED.search(raw))
    return low, hi, unresolved and not low


def csat_agent_manner(
    csat: pd.DataFrame,
    audits: pd.DataFrame,
    *,
    min_mentions: int = 2,
    top_n: int = 6,
) -> dict:
    """Repeat agent-manner complaints from CSAT open_question.

    Only agents that also appear in QA (so they have a supervisor). Outcome
    comments and driver/courier grosero without an agent cue are held out.
    Repeat = the same mapped agent appears in 2+ manner-complaint surveys.
    """
    empty = {
        "repeat_mix": pd.DataFrame(),
        "agent_repeat": pd.DataFrame(),
        "comments": pd.DataFrame(),
        "n_lowlight": 0,
        "n_highlight": 0,
        "n_repeat": 0,
        "n_once": 0,
        "repeat_pct": 0.0,
        "n_unresolved_held_out": 0,
        "n_unmapped": 0,
    }
    if csat is None or csat.empty or "open_question" not in csat.columns or "Agent name" not in csat.columns:
        return empty

    work = csat.copy()
    work["_fb"] = pd.to_numeric(work.get("Feedback CNT", 1), errors="coerce").fillna(1)
    neg_cols = [
        "Questionnaires With Star Level =1",
        "Questionnaires With Star Level =2",
        "Questionnaires With Star Level =3",
    ]
    pos_cols = [
        "Questionnaires With Star Level =4",
        "Questionnaires With Star Level =5",
    ]
    work["_neg"] = work[neg_cols].sum(axis=1) if all(c in work.columns for c in neg_cols) else 0
    work["_pos"] = work[pos_cols].sum(axis=1) if all(c in work.columns for c in pos_cols) else 0
    flags = work["open_question"].map(_manner_flags)
    work["_low"] = flags.map(lambda t: bool(t[0])) & (work["_neg"] > 0)
    work["_hi"] = flags.map(lambda t: bool(t[1])) & (work["_pos"] > 0)
    work["_held"] = flags.map(lambda t: bool(t[2])) & (work["_neg"] > 0)
    n_held = int(work.loc[work["_held"], "_fb"].sum())

    amap = _agent_supervisor_map(audits)
    work["_agent"] = work["Agent name"].astype(str).str.strip()
    work["_akey"] = work["_agent"].str.casefold()
    work["_sup"] = work["_akey"].map(amap)
    n_unmapped = int(work["_sup"].isna().sum())
    work = work[work["_sup"].notna()].copy()
    if work.empty:
        out = dict(empty)
        out["n_unresolved_held_out"] = n_held
        out["n_unmapped"] = n_unmapped
        return out

    n_low = int(work.loc[work["_low"], "_fb"].sum())
    n_hi = int(work.loc[work["_hi"], "_fb"].sum())
    low = work.loc[work["_low"]]
    agent_n = low.groupby("_akey")["_fb"].sum() if not low.empty else pd.Series(dtype=float)
    repeat_keys = set(agent_n[agent_n >= min_mentions].index)
    work["_repeat"] = work["_low"] & work["_akey"].isin(repeat_keys)
    n_repeat = int(work.loc[work["_repeat"], "_fb"].sum())
    n_once = max(n_low - n_repeat, 0)
    repeat_pct = round(100.0 * n_repeat / n_low, 1) if n_low else 0.0

    repeat_mix = pd.DataFrame({
        "Slice": ["Repeat (same agent 2+)", "One-off"],
        "Surveys": [n_repeat, n_once],
    })
    repeat_mix = repeat_mix[repeat_mix["Surveys"] > 0]

    agent_repeat = pd.DataFrame()
    if repeat_keys:
        g = (
            work.loc[work["_repeat"]]
            .groupby("_agent", as_index=False)
            .agg(Surveys=("_fb", "sum"))
            .sort_values("Surveys", ascending=False)
        )
        g["Surveys"] = g["Surveys"].round(0).astype(int)
        head = g.head(top_n)
        rest = int(g.iloc[top_n:]["Surveys"].sum()) if len(g) > top_n else 0
        rows = [{"Slice": r["_agent"], "Surveys": int(r["Surveys"])} for r in head.to_dict("records")]
        if rest > 0:
            rows.append({"Slice": "Other agents", "Surveys": rest})
        agent_repeat = pd.DataFrame(rows)

    comments = pd.DataFrame()
    tagged = work.loc[work["_repeat"]]
    if not tagged.empty:
        comments = pd.DataFrame({
            "Supervisor": tagged["_sup"].to_numpy(),
            "Agent": tagged["_agent"].to_numpy(),
            "open_question": tagged["open_question"].astype(str).str.strip().map(
                lambda t: _clip_comment(t, 220)
            ).to_numpy(),
        }).head(40)

    return {
        "repeat_mix": repeat_mix,
        "agent_repeat": agent_repeat,
        "comments": comments,
        "n_lowlight": n_low,
        "n_highlight": n_hi,
        "n_repeat": n_repeat,
        "n_once": n_once,
        "repeat_pct": repeat_pct,
        "n_unresolved_held_out": n_held,
        "n_unmapped": n_unmapped,
    }


def executive_insight(
    summary: dict,
    rc_rate: float,
    top_attr: pd.DataFrame,
    top_rc_cr: pd.DataFrame,
) -> str:
    parts = []
    if rc_rate > RECONTACT_GOAL:
        cr_hint = ""
        if not top_rc_cr.empty:
            cr_hint = f" Focus on {top_rc_cr.iloc[0]['CR_Lv4']} ({top_rc_cr.iloc[0]['Pct']:.1f}% of recontacts)."
        parts.append(
            f"Recontact rate above goal ({rc_rate:.2f}% vs ≤{RECONTACT_GOAL}%) indicates a First Contact Resolution opportunity.{cr_hint}"
        )
    if summary["qa_score"] < QA_GOAL:
        parts.append(f"QA score at {summary['qa_score']:.1f}% is below the {QA_GOAL}% target — prioritize calibration on failing attributes.")
    elif not top_attr.empty:
        parts.append(
            f"Top failing attribute '{top_attr.iloc[0]['Error_Category']}' drives {top_attr.iloc[0]['Pct_Of_Fails']:.1f}% of defects — include in next coaching cycle."
        )
    if summary["csat"] < CSAT_GOAL:
        parts.append(f"CSAT at {summary['csat']:.1f}% remains below the {CSAT_GOAL}% goal — review VOC themes in negative feedback.")
    if not parts:
        parts.append("All key metrics are within target for the selected period. Maintain coaching focus on top defect drivers.")
    return " ".join(parts)


AUDITED_RC_CHANNELS = ("PHONE", "LIVE CHAT")
SELF_HELP_CHANNEL = "SELF HELP"


def qa_channel_dispersion(audits: pd.DataFrame) -> dict:
    """
    Surface the channel that the global QA average hides.

    Alert is empty when every audited channel meets the goal and spread < 5 pp,
    so the KPI card stays clean on a healthy period.
    """
    empty = {
        "alert": "", "color": "neutral", "below": 0, "worst_channel": "—",
        "worst_qa": None, "worst_n": 0, "worst_vs": None, "spread": 0.0,
        "largest_share": 0.0, "global_meets": True, "tooltip": "",
        "channels": pd.DataFrame(),
    }
    if audits.empty or "Channel" not in audits.columns:
        return empty

    g = (
        audits.groupby("Channel", dropna=True)
        .agg(QA_Score=("Score_Pct", "mean"), N=("Audit_ID", "count"))
        .reset_index()
    )
    g = g[g["N"] > 0]
    if g.empty:
        return empty

    g["vs_goal"] = g["QA_Score"] - QA_GOAL
    g["Share"] = g["N"] / g["N"].sum() * 100
    worst = g.loc[g["QA_Score"].idxmin()]
    best = g.loc[g["QA_Score"].idxmax()]
    spread = float(best["QA_Score"] - worst["QA_Score"])
    below = int((g["QA_Score"] < QA_GOAL).sum())
    largest_share = float(g["Share"].max())
    global_qa = float(audits["Score_Pct"].mean())

    tooltip = "  |  ".join(
        f"{row['Channel']}: {row['QA_Score']:.1f}% (n={int(row['N']):,}, "
        f"{row['vs_goal']:+.1f} points vs goal)"
        for _, row in g.sort_values("QA_Score").iterrows()
    )

    alert, color = "", "neutral"
    if below > 0:
        alert = f"⚠ {worst['Channel']} {worst['QA_Score']:.1f}%"
        color = "red"
    elif spread >= 5:
        alert = f"⚠ {spread:.1f} pp between channels"
        color = "amber"

    return {
        "alert": alert,
        "color": color,
        "below": below,
        "worst_channel": str(worst["Channel"]),
        "worst_qa": round(float(worst["QA_Score"]), 2),
        "worst_n": int(worst["N"]),
        "worst_vs": round(float(worst["vs_goal"]), 1),
        "spread": round(spread, 2),
        "largest_share": round(largest_share, 1),
        "global_meets": global_qa >= QA_GOAL,
        "tooltip": tooltip,
        "channels": g,
    }


def recontact_by_scope(recontact: pd.DataFrame) -> pd.DataFrame:
    """
    Official rate vs diluted scopes. Always ratio of sums.

    Scopes are fixed comparisons (all channels / excl. Self Help / audited only)
    so the visual does not follow the Channel sidebar filter.
    """
    if recontact.empty or "Contacts" not in recontact.columns:
        return pd.DataFrame()

    ch = (
        recontact["standard_channel_name"].astype(str).str.strip().str.upper()
        if "standard_channel_name" in recontact.columns
        else pd.Series("", index=recontact.index)
    )
    scopes = [
        ("all", "All 12 channels (official)", recontact),
        ("ex_self_help", "Excluding Self Help", recontact[ch != SELF_HELP_CHANNEL]),
        ("audited", "Phone + Live Chat only", recontact[ch.isin(AUDITED_RC_CHANNELS)]),
    ]
    rows = []
    for i, (key, name, sub) in enumerate(scopes, start=1):
        contacts = float(sub["Contacts"].sum()) if not sub.empty else 0.0
        rate = recontact_rate(sub) if not sub.empty else float("nan")
        rows.append({
            "Scope_Key": key,
            "Scope": name,
            "Scope_Order": i,
            "Rate": round(rate, 2) if pd.notna(rate) else np.nan,
            "Contacts": int(contacts),
            "vs_goal": round(rate - RECONTACT_GOAL, 2) if pd.notna(rate) else np.nan,
        })
    return pd.DataFrame(rows)


def recontact_dilution_stats(recontact: pd.DataFrame) -> dict:
    """Self Help weight and rate — context for the official KPI, not a replacement."""
    empty = {"share": 0.0, "rate": float("nan"), "n_channels": 0}
    if recontact.empty or "standard_channel_name" not in recontact.columns:
        return empty
    ch = recontact["standard_channel_name"].astype(str).str.strip().str.upper()
    total = recontact["Contacts"].sum()
    sh = recontact[ch == SELF_HELP_CHANNEL]
    n_ch = ch.nunique()
    return {
        "share": round(sh["Contacts"].sum() / total * 100, 1) if total else 0.0,
        "rate": round(recontact_rate(sh), 2) if not sh.empty else float("nan"),
        "n_channels": int(n_ch),
    }


def scoring_method_stats(audits: pd.DataFrame) -> dict | None:
    """Official business-case score vs the Excel Score_end_user rubric."""
    if audits.empty or "Source_Score_End_User" not in audits.columns:
        return None
    src = pd.to_numeric(audits["Source_Score_End_User"], errors="coerce")
    ours = pd.to_numeric(audits["Score_Pct"], errors="coerce")
    valid = src.notna() & ours.notna()
    if not valid.any():
        return None
    official = float(ours[valid].mean())
    source = float(src[valid].mean())
    agree = float((ours[valid] == src[valid]).mean() * 100)
    return {
        "official": round(official, 2),
        "source": round(source, 2),
        "gap": round(official - source, 2),
        "agreement": round(agree, 2),
        "n": int(valid.sum()),
        "official_vs_goal": round(official - QA_GOAL, 2),
        "source_vs_goal": round(source - QA_GOAL, 2),
    }


def daily_volume_series(
    audits: pd.DataFrame,
    csat: pd.DataFrame,
    recontact: pd.DataFrame,
) -> dict[str, list]:
    """Daily volumes for KPI bar charts (values + date labels)."""
    out: dict[str, list] = {
        "evals": [], "evals_labels": [],
        "surveys": [], "surveys_labels": [],
        "contacts": [], "contacts_labels": [],
        "recontacts": [], "recontacts_labels": [],
    }

    def _labels(idx) -> list[str]:
        return [pd.Timestamp(x).strftime("%b %d") for x in idx]

    if not audits.empty:
        s = audits.groupby(audits["Fecha"].dt.date).size().astype(float)
        out["evals"] = s.tolist()
        out["evals_labels"] = _labels(s.index)
    if not csat.empty and "Fecha" in csat.columns and "Feedback CNT" in csat.columns:
        s = csat.groupby(csat["Fecha"].dt.date)["Feedback CNT"].sum().astype(float)
        out["surveys"] = s.tolist()
        out["surveys_labels"] = _labels(s.index)
    if not recontact.empty and "Fecha" in recontact.columns:
        s = recontact.groupby(recontact["Fecha"].dt.date)["Contacts"].sum().astype(float)
        out["contacts"] = s.tolist()
        out["contacts_labels"] = _labels(s.index)
        if "Recontact Volume" in recontact.columns:
            r = recontact.groupby(recontact["Fecha"].dt.date)["Recontact Volume"].sum().astype(float)
            out["recontacts"] = r.tolist()
            out["recontacts_labels"] = _labels(r.index)
    return out


def iso_week_label(dates: pd.Series) -> pd.Series:
    """Match the QA tab Week convention: W + ISO week number."""
    iso = pd.to_datetime(dates, errors="coerce").dt.isocalendar()
    return "W" + iso.week.astype("Int64").astype(str)


def _wow_pp(current: pd.Series) -> pd.Series:
    return (current - current.shift(1)).round(2)


def weekly_kpi_table(
    audits: pd.DataFrame,
    csat: pd.DataFrame,
    recontact: pd.DataFrame,
) -> pd.DataFrame:
    """
    One row per ISO week for QA, CSAT and Recontact.

    CSAT and recontact are ratio-of-sums. WoW is percentage points vs the previous
    week. Four weeks is enough for a management trend, not for SPC on this grain.
    """
    frames: list[pd.DataFrame] = []

    if not audits.empty:
        week_col = audits["Week"].astype(str) if "Week" in audits.columns else iso_week_label(audits["Fecha"])
        qa = (
            audits.assign(Week=week_col)
            .groupby("Week", sort=True)
            .agg(
                QA_Score=("Score_Pct", "mean"),
                QA_Evaluations=("Audit_ID", "count"),
                Week_Start=("Fecha", "min"),
                Week_End=("Fecha", "max"),
            )
            .reset_index()
        )
        frames.append(qa.set_index("Week"))

    if not csat.empty and "Fecha" in csat.columns:
        cs = csat.copy()
        cs["Week"] = iso_week_label(cs["Fecha"])
        csat_w = (
            cs.groupby("Week")
            .agg(Satisfied=("Satisfied_CNT", "sum"), Feedback=("Feedback CNT", "sum"))
            .reset_index()
        )
        csat_w["CSAT_Score"] = np.where(
            csat_w["Feedback"] > 0,
            csat_w["Satisfied"] / csat_w["Feedback"] * 100,
            np.nan,
        )
        frames.append(csat_w.set_index("Week")[["CSAT_Score", "Feedback"]])

    if not recontact.empty and "Fecha" in recontact.columns:
        rc = recontact.copy()
        rc["Week"] = iso_week_label(rc["Fecha"])
        rc_w = (
            rc.groupby("Week")
            .agg(Recontacts=("Recontact Volume", "sum"), Contacts=("Contacts", "sum"))
            .reset_index()
        )
        rc_w["Recontact_Rate"] = np.where(
            rc_w["Contacts"] > 0,
            rc_w["Recontacts"] / rc_w["Contacts"] * 100,
            np.nan,
        )
        frames.append(rc_w.set_index("Week")[["Recontact_Rate", "Contacts", "Recontacts"]])

    if not frames:
        return pd.DataFrame()

    out = pd.concat(frames, axis=1)
    out.index.name = "Week"
    out = out.reset_index()

    def _week_key(w: object) -> int:
        try:
            return int(str(w).replace("W", ""))
        except ValueError:
            return 0

    out = out.sort_values("Week", key=lambda s: s.map(_week_key)).reset_index(drop=True)
    out["QA_Goal"] = QA_GOAL
    out["CSAT_Goal"] = CSAT_GOAL
    out["Recontact_Goal"] = RECONTACT_GOAL
    if "QA_Score" in out.columns:
        out["QA_vs_Goal"] = (out["QA_Score"] - QA_GOAL).round(1)
        out["QA_WoW_pp"] = _wow_pp(out["QA_Score"]).round(1)
        out["QA_Status"] = out["QA_Score"].apply(lambda v: _vs_goal_status(v, QA_GOAL, True) if pd.notna(v) else "neutral")
        out["QA_Score"] = out["QA_Score"].round(1)
    if "CSAT_Score" in out.columns:
        out["CSAT_vs_Goal"] = (out["CSAT_Score"] - CSAT_GOAL).round(1)
        out["CSAT_WoW_pp"] = _wow_pp(out["CSAT_Score"]).round(1)
        out["CSAT_Status"] = out["CSAT_Score"].apply(lambda v: _vs_goal_status(v, CSAT_GOAL, True) if pd.notna(v) else "neutral")
        out["CSAT_Score"] = out["CSAT_Score"].round(1)
    if "Recontact_Rate" in out.columns:
        out["Recontact_vs_Goal"] = (out["Recontact_Rate"] - RECONTACT_GOAL).round(2)
        out["Recontact_WoW_pp"] = _wow_pp(out["Recontact_Rate"])
        out["Recontact_Status"] = out["Recontact_Rate"].apply(
            lambda v: _vs_goal_status(v, RECONTACT_GOAL, False) if pd.notna(v) else "neutral"
        )
        out["Recontact_Rate"] = out["Recontact_Rate"].round(2)
    return out


def individuals_control_chart(dates: pd.Series, values: pd.Series, goal: float, higher_is_better: bool) -> pd.DataFrame:
    """
    I-MR control chart. Use daily grain — this dataset has only four weeks.

    UCL/LCL = mean ± 2.66 × MR-bar. A point can be in control and still miss the goal.
    """
    df = pd.DataFrame({"Date": pd.to_datetime(dates), "Value": pd.to_numeric(values, errors="coerce")})
    df = df.dropna().sort_values("Date").reset_index(drop=True)
    if df.empty:
        return df
    df["MR"] = df["Value"].diff().abs()
    mr_bar = float(df["MR"].iloc[1:].mean()) if len(df) > 1 else 0.0
    cl = float(df["Value"].mean())
    ucl = cl + 2.66 * mr_bar
    lcl = max(0.0, cl - 2.66 * mr_bar)
    df["CL"] = round(cl, 2)
    df["UCL"] = round(ucl, 2)
    df["LCL"] = round(lcl, 2)
    df["Goal"] = goal
    df["MR_bar"] = round(mr_bar, 3)
    df["Beyond_Limits"] = (df["Value"] > ucl) | (df["Value"] < lcl)
    df["Misses_Goal"] = df["Value"] < goal if higher_is_better else df["Value"] > goal
    df["Value"] = df["Value"].round(2)
    return df


def qa_control_daily(audits: pd.DataFrame) -> pd.DataFrame:
    if audits.empty:
        return pd.DataFrame()
    g = audits.groupby(audits["Fecha"].dt.date)["Score_Pct"].mean()
    return individuals_control_chart(pd.Series(pd.to_datetime(g.index)), pd.Series(g.to_numpy()), QA_GOAL, True)


def csat_control_daily(csat: pd.DataFrame) -> pd.DataFrame:
    if csat.empty or "Fecha" not in csat.columns:
        return pd.DataFrame()
    g = csat.groupby(csat["Fecha"].dt.date).agg(sat=("Satisfied_CNT", "sum"), fb=("Feedback CNT", "sum"))
    rate = (g["sat"] / g["fb"] * 100).replace([np.inf, -np.inf], np.nan).dropna()
    return individuals_control_chart(pd.Series(pd.to_datetime(rate.index)), pd.Series(rate.to_numpy()), CSAT_GOAL, True)


def recontact_control_daily(recontact: pd.DataFrame) -> pd.DataFrame:
    if recontact.empty or "Fecha" not in recontact.columns:
        return pd.DataFrame()
    g = recontact.groupby(recontact["Fecha"].dt.date).agg(vol=("Recontact Volume", "sum"), contacts=("Contacts", "sum"))
    rate = (g["vol"] / g["contacts"] * 100).replace([np.inf, -np.inf], np.nan).dropna()
    return individuals_control_chart(pd.Series(pd.to_datetime(rate.index)), pd.Series(rate.to_numpy()), RECONTACT_GOAL, False)


def qa_score_histogram(audits: pd.DataFrame) -> pd.DataFrame:
    if audits.empty:
        return pd.DataFrame()
    counts = audits["Score_Pct"].round(0).value_counts().sort_index()
    total = counts.sum()
    return pd.DataFrame({
        "QA_Score": counts.index.astype(int),
        "Audits": counts.values,
        "Share_Pct": (counts.values / total * 100).round(1),
    })


def csat_score_histogram(csat: pd.DataFrame, bin_size: int = 5) -> pd.DataFrame:
    """Spread of slice CSAT % weighted by Feedback CNT. Official CSAT stays 4★+5★ / Feedback."""
    if csat.empty or "CSAT_Pct" not in csat.columns or "Feedback CNT" not in csat.columns:
        return pd.DataFrame()
    df = csat.loc[csat["Feedback CNT"] > 0, ["CSAT_Pct", "Feedback CNT"]].dropna()
    if df.empty:
        return pd.DataFrame()
    bins = (np.floor(df["CSAT_Pct"] / bin_size) * bin_size).clip(lower=0, upper=100).astype(int)
    g = (
        df.assign(CSAT_Score=bins)
        .groupby("CSAT_Score", as_index=False)
        .agg(Surveys=("Feedback CNT", "sum"))
    )
    total = float(g["Surveys"].sum())
    g["Share_Pct"] = np.where(total > 0, (g["Surveys"] / total * 100).round(1), 0.0)
    return g.sort_values("CSAT_Score")


def add_pareto_cumulative(
    df: pd.DataFrame,
    count_col: str,
    universe: float | None = None,
) -> pd.DataFrame:
    if df.empty or count_col not in df.columns:
        return df
    out = df.sort_values(count_col, ascending=False).copy()
    vals = pd.to_numeric(out[count_col], errors="coerce").fillna(0)
    out[count_col] = vals
    total = float(universe) if universe is not None and float(universe) > 0 else float(vals.sum())
    out["Cum_Count"] = vals.cumsum()
    out["Cum_Pct"] = np.where(total > 0, (out["Cum_Count"] / total * 100).round(1), 0.0)
    return out.reset_index(drop=True)


def cr_correlation_summary(scatter: pd.DataFrame) -> pd.DataFrame:
    """Pearson r at CR Lv4. One row per pair, even when N is below 5."""
    pairs = [
        ("QA_Score", "CSAT_Pct", "QA vs CSAT"),
        ("QA_Score", "Recontact_Rate", "QA vs Recontact"),
        ("CSAT_Pct", "Recontact_Rate", "CSAT vs Recontact"),
    ]
    if scatter is None or scatter.empty:
        return pd.DataFrame([
            {"Pair": label, "Pearson_r": np.nan, "N_CR": 0}
            for _, _, label in pairs
        ])
    rows = []
    for a, b, label in pairs:
        if a not in scatter.columns or b not in scatter.columns:
            rows.append({"Pair": label, "Pearson_r": np.nan, "N_CR": 0})
            continue
        sub = scatter[[a, b]].dropna()
        n = int(len(sub))
        if n < 5:
            rows.append({"Pair": label, "Pearson_r": np.nan, "N_CR": n})
            continue
        r = sub[a].corr(sub[b])
        rows.append({
            "Pair": label,
            "Pearson_r": round(float(r), 3) if pd.notna(r) else np.nan,
            "N_CR": n,
        })
    return pd.DataFrame(rows)


TENURE_COHORT_ORDER = list(TENURE_SOURCE_ORDER) + ["Unknown"]


def normalize_channel_label(value: object) -> str:
    raw = str(value).strip()
    key = raw.upper()
    if key in {"PHONE"}:
        return "Phone"
    if key in {"LIVE CHAT", "LIVECHAT", "CHAT"}:
        return "Live Chat"
    if key in {"SELF HELP"}:
        return "Self Help"
    if key in {"GPTBOT"}:
        return "GPTBot"
    if key in {"HELP CENTER"}:
        return "Help Center"
    return raw.title() if raw else "Unknown"


def channel_match(series: pd.Series, wanted: str) -> pd.Series:
    """Match Phone / PHONE / Live Chat / LIVE CHAT without mixing other RC channels."""
    want = normalize_channel_label(wanted)
    return series.map(normalize_channel_label) == want


def cr_match(series: pd.Series, wanted: str) -> pd.Series:
    return series.astype(str).str.strip().str.casefold() == str(wanted).strip().casefold()


def slice_coverage_table() -> pd.DataFrame:
    """What can actually be cut in each source — so filters are not a black box."""
    return pd.DataFrame(
        [
            {
                "Dimension": "Channel",
                "QA": "Yes — Phone, Live Chat only (the audited channels)",
                "CSAT": "Yes — mostly Phone and Live Chat (labels PHONE / LIVE CHAT)",
                "Recontact": "Yes — 12 channels. Self Help is 67% of contacts",
            },
            {
                "Dimension": "Tenure",
                "QA": "Yes — agent tenure from the QA tab (5 cohorts)",
                "CSAT": "Different field: user_tenure (new_hire / nesting / tenured / other). 81% is other",
                "Recontact": "No — the tab has no tenure column",
            },
            {
                "Dimension": "Week",
                "QA": "W19–W22",
                "CSAT": "W18–W22",
                "Recontact": "W18–W22",
            },
            {
                "Dimension": "Day",
                "QA": "Yes — audit Fecha",
                "CSAT": "Yes — survey Fecha",
                "Recontact": "Yes — contact Fecha",
            },
            {
                "Dimension": "Country / Market",
                "QA": "Yes — CO, CR, MX, PE",
                "CSAT": "Yes — those plus DO, PA (Country Code)",
                "Recontact": "No — region is always SSL. Market does not cut recontact.",
            },
            {
                "Dimension": "Contact reason Lv1 (group)",
                "QA": "Mapped from CSAT by Lv4 detail name. Unmapped = Not mapped.",
                "CSAT": "Yes — native CR_Lv1",
                "Recontact": "Mapped from CSAT by Lv4 detail name.",
            },
            {
                "Dimension": "Contact reason Lv4 (detail)",
                "QA": "Yes — CR_Lv4",
                "CSAT": "Yes — CR_Lv4",
                "Recontact": "Yes — CR_Lv4",
            },
            {
                "Dimension": "Type of audit",
                "QA": "Yes",
                "CSAT": "No",
                "Recontact": "No",
            },
            {
                "Dimension": "Special project",
                "QA": "Yes",
                "CSAT": "No",
                "Recontact": "No",
            },
            {
                "Dimension": "Business type",
                "QA": "No",
                "CSAT": "Yes",
                "Recontact": "No",
            },
            {
                "Dimension": "Supervisor",
                "QA": "Yes — Supervisor_ID",
                "CSAT": "Yes — agent name matched to QA Agent_ID, then that agent’s supervisor",
                "Recontact": "No — the tab has no agent or supervisor",
            },
            {
                "Dimension": "Agent",
                "QA": "Yes — Agent_ID",
                "CSAT": "Yes — agent name matched to QA Agent_ID",
                "Recontact": "No — the tab has no agent or supervisor",
            },
        ]
    )


def qa_by_special_project(audits: pd.DataFrame) -> pd.DataFrame:
    if audits.empty or "Special_project" not in audits.columns:
        return pd.DataFrame()
    g = (
        audits.groupby("Special_project", dropna=False)
        .agg(QA_Score=("Score_Pct", "mean"), n=("Audit_ID", "count"),
             Fatal_Rate=("Fatal_Flag", "mean"), AHT_sec=("Duration", "mean"))
        .reset_index()
    )
    g["QA_Score"] = g["QA_Score"].round(2)
    g["QA_vs_Goal"] = (g["QA_Score"] - QA_GOAL).round(2)
    g["Fatal_Rate"] = (g["Fatal_Rate"] * 100).round(1)
    g["AHT_min"] = (g["AHT_sec"] / 60).round(1)
    return g.sort_values("n", ascending=False)


def qa_by_audit_type(audits: pd.DataFrame) -> pd.DataFrame:
    col = "Type_of_audit" if "Type_of_audit" in audits.columns else "Auditor_ID"
    if audits.empty or col not in audits.columns:
        return pd.DataFrame()
    g = (
        audits.groupby(col, dropna=False)
        .agg(QA_Score=("Score_Pct", "mean"), n=("Audit_ID", "count"),
             Fatal_Rate=("Fatal_Flag", "mean"))
        .reset_index()
        .rename(columns={col: "Type_of_audit"})
    )
    g["QA_Score"] = g["QA_Score"].round(2)
    g["QA_vs_Goal"] = (g["QA_Score"] - QA_GOAL).round(2)
    g["Fatal_Rate"] = (g["Fatal_Rate"] * 100).round(1)
    return g.sort_values("n", ascending=False)


def qa_aht_by_channel(audits: pd.DataFrame) -> pd.DataFrame:
    if audits.empty or "Duration" not in audits.columns:
        return pd.DataFrame()
    g = (
        audits.groupby("Channel", dropna=False)
        .agg(QA_Score=("Score_Pct", "mean"), n=("Audit_ID", "count"),
             AHT_sec=("Duration", "mean"), AHT_p50=("Duration", "median"))
        .reset_index()
    )
    g["QA_Score"] = g["QA_Score"].round(2)
    g["AHT_min"] = (g["AHT_sec"] / 60).round(1)
    g["AHT_p50_min"] = (g["AHT_p50"] / 60).round(1)
    return g.sort_values("n", ascending=False)


def supervisor_overview(audits: pd.DataFrame, csat: pd.DataFrame, min_n: int = 5) -> pd.DataFrame:
    """Compact supervisor snapshot for Overview: QA + AHT from audits, CSAT via agent name.

    Recontact has no supervisor or agent field — it is not on this table.
    CSAT is surveys of agents that also appear in QA, mapped to that agent's supervisor.
    """
    if audits.empty or "Supervisor_ID" not in audits.columns:
        return pd.DataFrame()
    qa = audits.copy()
    if "Agent_ID" not in qa.columns:
        qa["Agent_ID"] = ""
    if "Duration" in qa.columns:
        qa["Duration"] = pd.to_numeric(qa["Duration"], errors="coerce")
    else:
        qa["Duration"] = np.nan
    g = (
        qa.groupby("Supervisor_ID", as_index=False)
        .agg(
            QA_Score=("Score_Pct", "mean"),
            n=("Audit_ID", "count"),
            AHT_sec=("Duration", "mean"),
            Agents=("Agent_ID", "nunique"),
        )
    )
    if min_n:
        g = g[g["n"] >= int(min_n)]
    if g.empty:
        return g
    g["QA_Score"] = g["QA_Score"].round(1)
    g["AHT_min"] = (g["AHT_sec"] / 60).round(1)

    agent_key = qa["Agent_ID"].astype(str).str.strip().str.casefold()
    agent_sup = (
        qa.assign(_agent=agent_key)
        .groupby("_agent", as_index=False)
        .agg(Supervisor_ID=("Supervisor_ID", "first"))
    )
    amap = dict(zip(agent_sup["_agent"], agent_sup["Supervisor_ID"]))

    csat_map = pd.DataFrame(columns=["Supervisor_ID", "CSAT_Score", "Feedback"])
    if not csat.empty and "Agent name" in csat.columns and "Feedback CNT" in csat.columns:
        cs = csat.copy()
        cs["_sup"] = cs["Agent name"].astype(str).str.strip().str.casefold().map(amap)
        cs = cs[cs["_sup"].notna()]
        if not cs.empty:
            csat_map = (
                cs.groupby("_sup", as_index=False)
                .agg(Satisfied=("Satisfied_CNT", "sum"), Feedback=("Feedback CNT", "sum"))
                .rename(columns={"_sup": "Supervisor_ID"})
            )
            csat_map["CSAT_Score"] = np.where(
                csat_map["Feedback"] > 0,
                (csat_map["Satisfied"] / csat_map["Feedback"] * 100).round(1),
                np.nan,
            )
    out = g.merge(csat_map[["Supervisor_ID", "CSAT_Score", "Feedback"]], on="Supervisor_ID", how="left")
    return out.sort_values("n", ascending=False)


def _gap_impact(score, n, goal: float) -> float:
    if pd.isna(score) or pd.isna(n) or float(n) <= 0:
        return 0.0
    return float(max(0.0, goal - float(score)) * float(n))


def gap_pareto_frame(
    df: pd.DataFrame,
    cat_col: str,
    score_col: str,
    n_col: str,
    goal: float,
) -> pd.DataFrame:
    """Pareto input: only rows below `goal`. Bar = volume × pp below goal."""
    if df is None or df.empty or cat_col not in df.columns:
        return pd.DataFrame()
    need = {score_col, n_col}
    if not need.issubset(df.columns):
        return pd.DataFrame()
    out = df[[cat_col, score_col, n_col]].copy()
    out["Gap_Impact"] = [
        _gap_impact(s, n, goal) for s, n in zip(out[score_col], out[n_col])
    ]
    out = out[out["Gap_Impact"] > 0.01].sort_values("Gap_Impact", ascending=False)
    return out.rename(columns={cat_col: "Cat"})


def tenure_qa_overview(audits: pd.DataFrame) -> pd.DataFrame:
    if audits.empty or "Tenure_Cohort" not in audits.columns:
        return pd.DataFrame()
    g = (
        audits.groupby("Tenure_Cohort", as_index=False)
        .agg(
            QA_Score=("Score_Pct", "mean"),
            n=("Audit_ID", "count"),
            Agents=("Agent_ID", "nunique") if "Agent_ID" in audits.columns else ("Audit_ID", "nunique"),
        )
    )
    g["QA_Score"] = g["QA_Score"].round(1)
    return g


def tenure_csat_overview(audits: pd.DataFrame, csat: pd.DataFrame) -> pd.DataFrame:
    """CSAT by the agent's QA tenure. Not the CSAT tab user_tenure field."""
    if (
        audits.empty or csat.empty
        or "Tenure_Cohort" not in audits.columns
        or "Agent_ID" not in audits.columns
        or "Agent name" not in csat.columns
        or "Feedback CNT" not in csat.columns
    ):
        return pd.DataFrame()
    amap = (
        audits.assign(_a=audits["Agent_ID"].astype(str).str.strip().str.casefold())
        .groupby("_a", as_index=False)
        .agg(Tenure_Cohort=("Tenure_Cohort", "first"))
    )
    lookup = dict(zip(amap["_a"], amap["Tenure_Cohort"]))
    cs = csat.copy()
    cs["_ten"] = cs["Agent name"].astype(str).str.strip().str.casefold().map(lookup)
    cs = cs[cs["_ten"].notna()]
    if cs.empty:
        return pd.DataFrame()
    g = (
        cs.groupby("_ten", as_index=False)
        .agg(Satisfied=("Satisfied_CNT", "sum"), Feedback=("Feedback CNT", "sum"))
        .rename(columns={"_ten": "Tenure_Cohort"})
    )
    g["CSAT_Score"] = np.where(
        g["Feedback"] > 0,
        (g["Satisfied"] / g["Feedback"] * 100).round(1),
        np.nan,
    )
    return g


def agents_below_qa_goal(
    audits: pd.DataFrame,
    min_n: int = 5,
    *,
    below_goal_only: bool = True,
) -> pd.DataFrame:
    """Agents with official QA. Default: enough audits and under 85, for coaching.

    Set below_goal_only=False to keep agents on or above goal (See all slices).
    """
    if audits.empty or "Agent_ID" not in audits.columns:
        return pd.DataFrame()
    group = ["Agent_ID"]
    if "Supervisor_ID" in audits.columns:
        group.append("Supervisor_ID")
    g = (
        audits.groupby(group, as_index=False)
        .agg(QA_Score=("Score_Pct", "mean"), n=("Audit_ID", "count"))
    )
    if "Tenure_Cohort" in audits.columns:
        ten = (
            audits.groupby("Agent_ID", as_index=False)
            .agg(Tenure_Cohort=("Tenure_Cohort", "first"))
        )
        g = g.merge(ten, on="Agent_ID", how="left")
    else:
        g["Tenure_Cohort"] = "Unknown"
    if min_n:
        g = g[g["n"] >= int(min_n)]
    if g.empty:
        return g
    g["QA_Score"] = g["QA_Score"].round(1)
    g["Gap_Impact"] = (QA_GOAL - g["QA_Score"]).clip(lower=0) * g["n"]
    if below_goal_only:
        g = g[g["Gap_Impact"] > 0.01]
        return g.sort_values("Gap_Impact", ascending=False)
    return g.sort_values("QA_Score", ascending=True)


def qa_agent_roster(
    audits: pd.DataFrame,
    errors: pd.DataFrame | None = None,
    min_n: int = MIN_SAMPLE_SIZE,
) -> pd.DataFrame:
    """Every agent with enough audits: QA, fail volume, grouped for supervisor coaching.

    Rank: worst team QA first, then attribute-fail count inside the team.
    Agents with fewer than min_n audits stay out — the score is too noisy.
    """
    if audits is None or audits.empty or "Agent_ID" not in audits.columns:
        return pd.DataFrame()
    group = ["Agent_ID"]
    if "Supervisor_ID" in audits.columns:
        group.append("Supervisor_ID")
    agg = {
        "QA_Score": ("Score_Pct", "mean"),
        "Audit_Count": ("Audit_ID", "count"),
    }
    if "Fatal_Flag" in audits.columns:
        agg["Fatal_Rate"] = ("Fatal_Flag", "mean")
    g = audits.groupby(group, as_index=False).agg(**agg)
    if "Tenure_Cohort" in audits.columns:
        ten = audits.groupby("Agent_ID", as_index=False).agg(Tenure_Cohort=("Tenure_Cohort", "first"))
        g = g.merge(ten, on="Agent_ID", how="left")
    else:
        g["Tenure_Cohort"] = "Unknown"
    g["Fail_Count"] = 0
    g["Crit_Fails"] = 0
    if errors is not None and not errors.empty and "Agent_ID" in errors.columns:
        fails = errors.copy()
        fails["_ak"] = fails["Agent_ID"].astype(str).str.strip().str.casefold()
        f_keys = ["_ak"]
        # Same grain as the roster row (agent × supervisor). Agent-only merge
        # stamped one agent's events onto every supervisor split of that agent.
        if "Supervisor_ID" in group and "Supervisor_ID" in fails.columns:
            f_keys.append("Supervisor_ID")
        f_agg = {"Fail_Count": ("Audit_ID", "count")}
        if "Is_Critical" in fails.columns:
            f_agg["Crit_Fails"] = ("Is_Critical", "sum")
        f = fails.groupby(f_keys, as_index=False).agg(**f_agg)
        g["_ak"] = g["Agent_ID"].astype(str).str.strip().str.casefold()
        g = g.drop(columns=["Fail_Count", "Crit_Fails"], errors="ignore").merge(
            f, on=f_keys, how="left",
        )
        g = g.drop(columns=["_ak"])
    if "Fail_Count" not in g.columns:
        g["Fail_Count"] = 0
    if "Crit_Fails" not in g.columns:
        g["Crit_Fails"] = 0
    g["Fail_Count"] = pd.to_numeric(g.get("Fail_Count"), errors="coerce").fillna(0).astype(int)
    g["Crit_Fails"] = pd.to_numeric(g.get("Crit_Fails"), errors="coerce").fillna(0).astype(int)
    g = g[g["Audit_Count"] >= int(min_n)]
    if g.empty:
        return g
    g["QA_Score"] = g["QA_Score"].round(1)
    if "Fatal_Rate" in g.columns:
        g["Fatal_Rate"] = (pd.to_numeric(g["Fatal_Rate"], errors="coerce") * 100).round(1)
    else:
        g["Fatal_Rate"] = 0.0
    # Share of every attribute-fail event in this filter, including agents
    # below min_n who are not on this roster.
    universe = (
        float(len(errors))
        if errors is not None and not errors.empty
        else float(g["Fail_Count"].sum())
    )
    g["Fail_Share"] = (g["Fail_Count"] / universe * 100).round(1) if universe else 0.0
    g["Gap_Impact"] = (QA_GOAL - g["QA_Score"]).clip(lower=0) * g["Audit_Count"]
    if "Supervisor_ID" not in g.columns:
        g["Supervisor_ID"] = "Unknown"
    team = g.groupby("Supervisor_ID", as_index=False).agg(
        Team_QA=("QA_Score", "mean"),
        Team_Fails=("Fail_Count", "sum"),
        Team_Agents=("Agent_ID", "nunique"),
    )
    team["Team_QA"] = team["Team_QA"].round(1)
    g = g.merge(team, on="Supervisor_ID", how="left")
    return g.sort_values(
        ["Team_QA", "Fail_Count", "QA_Score"],
        ascending=[True, False, True],
    ).reset_index(drop=True)


def qa_agent_fail_concentrators(
    errors: pd.DataFrame,
    audits: pd.DataFrame | None = None,
    top_n: int | None = None,
) -> pd.DataFrame:
    """Agents ranked by attribute-fail events — same grain as the attribute Pareto.

    Fail_Count = error rows (one audit with two failed attributes counts twice).
    Unique_Fail_Audits = distinct audits with ≥1 fail. No n≥5 cutoff: concentration
    of fails is not a QA-score sample. Zero-fail agents are omitted.
    """
    if errors is None or errors.empty or "Agent_ID" not in errors.columns:
        return pd.DataFrame()
    work = errors.copy()
    work["_ak"] = work["Agent_ID"].astype(str).str.strip()
    work = work[work["_ak"].ne("") & work["_ak"].str.casefold().ne("nan")]
    if work.empty:
        return pd.DataFrame()
    f_agg: dict[str, tuple[str, str]] = {
        "Fail_Count": ("Audit_ID", "count"),
        "Unique_Fail_Audits": ("Audit_ID", "nunique"),
    }
    if "Error_Category" in work.columns:
        f_agg["N_Attributes"] = ("Error_Category", "nunique")
    if "Is_Critical" in work.columns:
        f_agg["Crit_Fails"] = ("Is_Critical", "sum")
    g = work.groupby("Agent_ID", as_index=False).agg(**f_agg)
    g["Fail_Count"] = pd.to_numeric(g["Fail_Count"], errors="coerce").fillna(0).astype(int)
    g = g[g["Fail_Count"] > 0]
    if g.empty:
        return g
    universe = float(len(errors))
    g["Fail_Share"] = (g["Fail_Count"] / universe * 100).round(1) if universe else 0.0
    if audits is not None and not audits.empty and "Agent_ID" in audits.columns:
        a_agg: dict[str, tuple[str, str]] = {"Audit_Count": ("Audit_ID", "count")}
        if "Score_Pct" in audits.columns:
            a_agg["QA_Score"] = ("Score_Pct", "mean")
        a = audits.groupby("Agent_ID", as_index=False).agg(**a_agg)
        if "QA_Score" in a.columns:
            a["QA_Score"] = a["QA_Score"].round(1)
        g = g.merge(a, on="Agent_ID", how="left")
    if "Audit_Count" not in g.columns:
        g["Audit_Count"] = g["Unique_Fail_Audits"]
    g["Unique_Fail_Audits"] = pd.to_numeric(g["Unique_Fail_Audits"], errors="coerce").fillna(0).astype(int)
    g["_ord"] = g["Agent_ID"].map(_agent_sort_num)
    g = (
        g.sort_values(["Fail_Count", "Unique_Fail_Audits", "_ord"], ascending=[False, False, True])
        .drop(columns=["_ord"])
        .reset_index(drop=True)
    )
    if top_n is not None:
        g = g.head(int(top_n)).reset_index(drop=True)
    return g


def csat_agent_unsat_concentrators(
    csat: pd.DataFrame,
    audits: pd.DataFrame | None = None,
    top_n: int | None = None,
) -> pd.DataFrame:
    """Agents ranked by unsatisfied survey volume — same grain as the CR unsat Pareto.

    No 20-survey cutoff. Zero-unsat agents are omitted. Share is of every 1–3★
    survey in this filter, including agents not on the score roster.
    """
    if csat is None or csat.empty or "Agent name" not in csat.columns:
        return pd.DataFrame()
    if "Feedback CNT" not in csat.columns or "Satisfied_CNT" not in csat.columns:
        return pd.DataFrame()
    work = csat.copy()
    work["_ak"] = work["Agent name"].astype(str).str.strip()
    work = work[work["_ak"].ne("") & work["_ak"].str.casefold().ne("nan")]
    if work.empty:
        return pd.DataFrame()
    work["_fb"] = pd.to_numeric(work["Feedback CNT"], errors="coerce").fillna(0)
    work["_sat"] = pd.to_numeric(work["Satisfied_CNT"], errors="coerce").fillna(0)
    work["_key"] = work["_ak"].str.casefold()
    g = (
        work.groupby("_key", as_index=False)
        .agg(Agent=("_ak", "first"), Feedback=("_fb", "sum"), Satisfied=("_sat", "sum"))
    )
    g["Unsatisfied"] = (g["Feedback"] - g["Satisfied"]).clip(lower=0).astype(int)
    g = g[g["Unsatisfied"] > 0]
    if g.empty:
        return g
    universe = float(g["Unsatisfied"].sum())
    g["Unsat_Share"] = (g["Unsatisfied"] / universe * 100).round(1) if universe else 0.0
    g["CSAT_Score"] = np.where(
        g["Feedback"] > 0,
        (g["Satisfied"] / g["Feedback"] * 100).round(1),
        np.nan,
    )
    amap = _agent_supervisor_map(audits) if audits is not None else {}
    g["Supervisor_ID"] = g["_key"].map(amap)
    g["Supervisor_ID"] = g["Supervisor_ID"].fillna(CSAT_UNMAPPED_SUPERVISOR)
    g["_ord"] = g["Agent"].map(_agent_sort_num)
    g = (
        g.drop(columns=["_key"])
        .sort_values(["Unsatisfied", "_ord"], ascending=[False, True])
        .drop(columns=["_ord"])
        .reset_index(drop=True)
    )
    if top_n is not None:
        g = g.head(int(top_n)).reset_index(drop=True)
    return g


CSAT_UNMAPPED_SUPERVISOR = "Not mapped to a QA supervisor"


def csat_agent_roster(
    csat: pd.DataFrame,
    audits: pd.DataFrame,
    min_n: int = 20,
) -> pd.DataFrame:
    """Every agent with enough surveys: official CSAT (4★+5★ / Feedback), grouped by QA supervisor.

    Concentration = unsatisfied survey volume (Feedback − satisfied), not a new formula.
    Agent name is matched to QA Agent_ID; unmatched agents stay in their own group.
    """
    if csat is None or csat.empty or "Agent name" not in csat.columns:
        return pd.DataFrame()
    if "Feedback CNT" not in csat.columns or "Satisfied_CNT" not in csat.columns:
        return pd.DataFrame()
    work = csat.copy()
    work["_ak"] = work["Agent name"].astype(str).str.strip()
    work = work[work["_ak"].ne("") & work["_ak"].str.casefold().ne("nan")]
    if work.empty:
        return pd.DataFrame()
    work["_fb"] = pd.to_numeric(work["Feedback CNT"], errors="coerce").fillna(0)
    work["_sat"] = pd.to_numeric(work["Satisfied_CNT"], errors="coerce").fillna(0)
    work["_key"] = work["_ak"].str.casefold()
    g = (
        work.groupby("_key", as_index=False)
        .agg(Agent=("_ak", "first"), Feedback=("_fb", "sum"), Satisfied=("_sat", "sum"))
    )
    g["Unsatisfied"] = (g["Feedback"] - g["Satisfied"]).clip(lower=0).astype(int)
    universe_u = float(g["Unsatisfied"].sum())
    g = g[g["Feedback"] >= int(min_n)]
    if g.empty:
        return g
    g["CSAT_Score"] = np.where(
        g["Feedback"] > 0,
        (g["Satisfied"] / g["Feedback"] * 100).round(1),
        np.nan,
    )
    g["Gap_Impact"] = (CSAT_GOAL - g["CSAT_Score"]).clip(lower=0) * g["Feedback"]
    g["Unsat_Share"] = (g["Unsatisfied"] / universe_u * 100).round(1) if universe_u else 0.0
    amap = _agent_supervisor_map(audits)
    g["Supervisor_ID"] = g["_key"].map(amap)
    g["Supervisor_ID"] = g["Supervisor_ID"].fillna(CSAT_UNMAPPED_SUPERVISOR)
    team = g.groupby("Supervisor_ID", as_index=False).agg(
        Team_Unsat=("Unsatisfied", "sum"),
        Team_Agents=("Agent", "nunique"),
        Team_Feedback=("Feedback", "sum"),
        Team_Satisfied=("Satisfied", "sum"),
    )
    team["Team_CSAT"] = np.where(
        team["Team_Feedback"] > 0,
        (team["Team_Satisfied"] / team["Team_Feedback"] * 100).round(1),
        np.nan,
    )
    g = g.merge(
        team[["Supervisor_ID", "Team_CSAT", "Team_Unsat", "Team_Agents"]],
        on="Supervisor_ID",
        how="left",
    )
    g["_unmapped"] = g["Supervisor_ID"].eq(CSAT_UNMAPPED_SUPERVISOR).astype(int)
    return (
        g.drop(columns=["_key"])
        .sort_values(
            ["_unmapped", "Team_CSAT", "Unsatisfied", "CSAT_Score"],
            ascending=[True, True, False, True],
        )
        .drop(columns=["_unmapped"])
        .reset_index(drop=True)
    )


# Same floor as cr_level_metrics QA_N ≥ 3. An 8-audit cut blanks supervisor × Phone
# slices (e.g. Supervisor 1 Phone: 27 audits, max 7 per Lv4) even when CSAT has
# thousands of surveys. Pearson r is still withheld until 5 shared names.
AHT_CR_MIN_AUDITS = 3


def qa_aht_by_cr(audits: pd.DataFrame, min_n: int = AHT_CR_MIN_AUDITS) -> pd.DataFrame:
    """Official QA vs Duration (seconds → minutes) at contact-reason Lv4. Association only."""
    if audits.empty or "Duration" not in audits.columns or "CR_Lv4" not in audits.columns:
        return pd.DataFrame()
    df = audits.copy()
    df["Duration"] = pd.to_numeric(df["Duration"], errors="coerce")
    df = df[df["Duration"] > 0].dropna(subset=["Score_Pct", "CR_Lv4"])
    if df.empty:
        return pd.DataFrame()
    keys = ["CR_Lv4", "Channel"] if "Channel" in df.columns else ["CR_Lv4"]
    g = (
        df.groupby(keys, dropna=False)
        .agg(QA_Score=("Score_Pct", "mean"), AHT_sec=("Duration", "mean"), n=("Audit_ID", "count"))
        .reset_index()
    )
    g = g[g["n"] >= min_n]
    if g.empty:
        return g
    g["QA_Score"] = g["QA_Score"].round(1)
    g["AHT_min"] = (g["AHT_sec"] / 60).round(1)
    return g.sort_values("n", ascending=False)


def aht_joined_outcomes(
    audits: pd.DataFrame, csat: pd.DataFrame, recontact: pd.DataFrame,
    min_n: int = AHT_CR_MIN_AUDITS,
) -> pd.DataFrame:
    """QA Duration (minutes) at CR Lv4 + channel, left-joined to CSAT and recontact.

    Join is the Lv4 name on the same channel — not the same contact. Phone and
    Live Chat stay unmixed. Handle time is QA Duration; CSAT has no AHT field.
    Official KPI formulas are unchanged.
    """
    aht = qa_aht_by_cr(audits, min_n=min_n)
    if aht.empty:
        return aht
    out = aht.copy()
    out["CR_key"] = out["CR_Lv4"].astype(str).str.strip().str.casefold()
    if "Channel" in out.columns:
        out["Channel"] = out["Channel"].map(normalize_channel_label)
    else:
        out["Channel"] = "Unknown"

    if not csat.empty and "CR_Lv4" in csat.columns and "Feedback CNT" in csat.columns:
        cs = csat[csat["CR_Lv4"].notna()].copy()
        cs["CR_key"] = cs["CR_Lv4"].astype(str).str.strip().str.casefold()
        cs["_ch"] = (
            cs["Channel"].map(normalize_channel_label)
            if "Channel" in cs.columns
            else "Unknown"
        )
        csat_g = (
            cs.groupby(["CR_key", "_ch"], as_index=False)
            .agg(Satisfied=("Satisfied_CNT", "sum"), Feedback=("Feedback CNT", "sum"))
        )
        csat_g["CSAT_Pct"] = np.where(
            csat_g["Feedback"] > 0,
            (csat_g["Satisfied"] / csat_g["Feedback"] * 100).round(1),
            np.nan,
        )
        out = out.merge(
            csat_g[["CR_key", "_ch", "CSAT_Pct", "Feedback"]],
            left_on=["CR_key", "Channel"],
            right_on=["CR_key", "_ch"],
            how="left",
        )
        out = out.drop(columns=["_ch"], errors="ignore")

    rc_ch = None
    if not recontact.empty and "CR_Lv4" in recontact.columns:
        if "standard_channel_name" in recontact.columns:
            rc_ch = "standard_channel_name"
        elif "Channel" in recontact.columns:
            rc_ch = "Channel"
    if rc_ch is not None and "Recontact Volume" in recontact.columns and "Contacts" in recontact.columns:
        rc = recontact[recontact["CR_Lv4"].notna()].copy()
        rc["CR_key"] = rc["CR_Lv4"].astype(str).str.strip().str.casefold()
        rc["_ch"] = rc[rc_ch].map(normalize_channel_label)
        rc_g = (
            rc.groupby(["CR_key", "_ch"], as_index=False)
            .agg(Recontacts=("Recontact Volume", "sum"), Contacts=("Contacts", "sum"))
        )
        rc_g["Recontact_Rate"] = np.where(
            rc_g["Contacts"] > 0,
            (rc_g["Recontacts"] / rc_g["Contacts"] * 100).round(2),
            np.nan,
        )
        out = out.merge(
            rc_g[["CR_key", "_ch", "Recontact_Rate", "Contacts"]],
            left_on=["CR_key", "Channel"],
            right_on=["CR_key", "_ch"],
            how="left",
        )
        out = out.drop(columns=["_ch"], errors="ignore")

    return out.drop(columns=["CR_key"], errors="ignore")


def aht_correlation_summary(df: pd.DataFrame, min_n: int = 5) -> pd.DataFrame:
    """Pearson r of AHT vs QA / CSAT / recontact. Always returns rows; r only if N ≥ min_n.

    'All' is the pooled Phone+Chat cloud. Read channel rows first — Phone handle
    is longer by nature, so the pooled r can be misleading on its own.
    """
    pairs = [
        ("QA_Score", "AHT vs QA"),
        ("CSAT_Pct", "AHT vs CSAT"),
        ("Recontact_Rate", "AHT vs Recontact"),
    ]
    slices: list[tuple[str, pd.DataFrame]] = []
    if df is not None and not df.empty:
        slices.append(("All", df))
        if "Channel" in df.columns:
            for ch, g in df.groupby("Channel", dropna=False):
                slices.append((str(ch) if pd.notna(ch) else "Unknown", g))
    else:
        slices.append(("All", pd.DataFrame()))

    rows = []
    for y, label in pairs:
        for slice_name, sub in slices:
            if sub is None or sub.empty or y not in sub.columns or "AHT_min" not in sub.columns:
                rows.append({"Pair": label, "Slice": slice_name, "Pearson_r": np.nan, "N_CR": 0})
                continue
            pair = sub[["AHT_min", y]].dropna()
            n = int(len(pair))
            if n < min_n:
                rows.append({"Pair": label, "Slice": slice_name, "Pearson_r": np.nan, "N_CR": n})
                continue
            r = pair["AHT_min"].corr(pair[y])
            rows.append({
                "Pair": label,
                "Slice": slice_name,
                "Pearson_r": round(float(r), 3) if pd.notna(r) else np.nan,
                "N_CR": n,
            })
    return pd.DataFrame(rows)


def _csat_cr_base(
    csat: pd.DataFrame,
    *,
    level: str = "lv4",
    lookup: dict | None = None,
) -> pd.DataFrame:
    """Official CSAT (4★+5★ / Feedback) grouped by contact reason. Not a new formula."""
    if csat is None or csat.empty or "Feedback CNT" not in csat.columns or "Satisfied_CNT" not in csat.columns:
        return pd.DataFrame()
    work = csat.copy()
    if level == "lv1":
        if "CR_Lv1" in work.columns:
            work["_cat"] = work["CR_Lv1"].astype(str).str.strip()
        elif lookup and "CR_Lv4" in work.columns:
            work["_cat"] = map_cr_group(work["CR_Lv4"], lookup)
        else:
            return pd.DataFrame()
        cat_name = "CR_Lv1"
    else:
        if "CR_Lv4" not in work.columns:
            return pd.DataFrame()
        work["_cat"] = work["CR_Lv4"].astype(str).str.strip()
        cat_name = "CR_Lv4"
    work = work[work["_cat"].ne("") & work["_cat"].str.casefold().ne("nan")]
    if work.empty:
        return pd.DataFrame()
    g = (
        work.groupby("_cat", dropna=False)
        .agg(
            Satisfied=("Satisfied_CNT", "sum"),
            Feedback=("Feedback CNT", "sum"),
        )
        .reset_index()
        .rename(columns={"_cat": cat_name})
    )
    g["CSAT_Score"] = np.where(
        g["Feedback"] > 0,
        (g["Satisfied"] / g["Feedback"] * 100).round(1),
        np.nan,
    )
    return g


def csat_score_by_cr(
    csat: pd.DataFrame,
    *,
    level: str = "lv4",
    lookup: dict | None = None,
    min_n: int = 20,
    top_n: int | None = 12,
) -> pd.DataFrame:
    """Official CSAT by contact reason. Default: lowest scores with enough surveys."""
    g = _csat_cr_base(csat, level=level, lookup=lookup)
    if g.empty:
        return g
    g = g[g["Feedback"] >= int(min_n)]
    if g.empty:
        return g
    g = g.sort_values("CSAT_Score", ascending=True)
    if top_n is not None:
        g = g.head(int(top_n))
    return g.reset_index(drop=True)


def csat_volume_by_cr(
    csat: pd.DataFrame,
    *,
    level: str = "lv4",
    lookup: dict | None = None,
    top_n: int = 10,
) -> pd.DataFrame:
    """Survey volume by contact reason (Feedback CNT). Score is still 4★+5★ / Feedback."""
    g = _csat_cr_base(csat, level=level, lookup=lookup)
    if g.empty:
        return g
    g = g[g["Feedback"] > 0]
    if g.empty:
        return g
    total = float(g["Feedback"].sum())
    g["Pct"] = (g["Feedback"] / total * 100).round(1) if total else 0.0
    g = g.sort_values("Feedback", ascending=False)
    if top_n is not None:
        g = g.head(int(top_n))
    return g.reset_index(drop=True)


def csat_by_supervisor(
    csat: pd.DataFrame,
    audits: pd.DataFrame | None = None,
    min_n: int = 20,
    top_n: int | None = 12,
) -> pd.DataFrame:
    """Official CSAT by QA supervisor (agent name → Agent_ID). Lowest score first."""
    if csat is None or csat.empty or "Agent name" not in csat.columns:
        return pd.DataFrame()
    if "Feedback CNT" not in csat.columns or "Satisfied_CNT" not in csat.columns:
        return pd.DataFrame()
    work = csat.copy()
    work["_ak"] = work["Agent name"].astype(str).str.strip()
    work = work[work["_ak"].ne("") & work["_ak"].str.casefold().ne("nan")]
    if work.empty:
        return pd.DataFrame()
    work["_fb"] = pd.to_numeric(work["Feedback CNT"], errors="coerce").fillna(0)
    work["_sat"] = pd.to_numeric(work["Satisfied_CNT"], errors="coerce").fillna(0)
    work["_key"] = work["_ak"].str.casefold()
    amap = _agent_supervisor_map(audits) if audits is not None else {}
    work["Supervisor_ID"] = work["_key"].map(amap).fillna(CSAT_UNMAPPED_SUPERVISOR)
    g = (
        work.groupby("Supervisor_ID", as_index=False)
        .agg(Satisfied=("_sat", "sum"), Feedback=("_fb", "sum"), Agents=("_ak", "nunique"))
    )
    g = g[g["Feedback"] >= int(min_n)]
    if g.empty:
        return g
    g["CSAT_Score"] = np.where(
        g["Feedback"] > 0,
        (g["Satisfied"] / g["Feedback"] * 100).round(1),
        np.nan,
    )
    g = g.sort_values("CSAT_Score", ascending=True)
    if top_n is not None:
        g = g.head(int(top_n))
    return g.reset_index(drop=True)


def csat_unsatisfied_by_cr(csat: pd.DataFrame) -> pd.DataFrame:
    """Unsatisfied survey volume (Feedback − 4★/5★) by contact reason Lv4. Not a new CSAT formula."""
    if csat.empty or "CR_Lv4" not in csat.columns or "Feedback CNT" not in csat.columns:
        return pd.DataFrame()
    g = (
        csat.groupby("CR_Lv4", dropna=False)
        .agg(Feedback=("Feedback CNT", "sum"), Satisfied=("Satisfied_CNT", "sum"))
        .reset_index()
    )
    g["Unsatisfied"] = (g["Feedback"] - g["Satisfied"]).clip(lower=0)
    g = g[g["Unsatisfied"] > 0]
    if g.empty:
        return g
    g["CSAT_Score"] = np.where(g["Feedback"] > 0, (g["Satisfied"] / g["Feedback"] * 100).round(1), np.nan)
    return g.sort_values("Unsatisfied", ascending=False)


def csat_by_business_type(csat: pd.DataFrame) -> pd.DataFrame:
    col = "Business_Type" if "Business_Type" in csat.columns else "Business Type Name"
    if csat.empty or col not in csat.columns:
        return pd.DataFrame()
    g = (
        csat.groupby(col, dropna=False)
        .agg(Satisfied=("Satisfied_CNT", "sum"), Feedback=("Feedback CNT", "sum"))
        .reset_index()
        .rename(columns={col: "Business_Type"})
    )
    g["CSAT_Score"] = np.where(g["Feedback"] > 0, (g["Satisfied"] / g["Feedback"] * 100).round(2), np.nan)
    g["CSAT_vs_Goal"] = (g["CSAT_Score"] - CSAT_GOAL).round(2)
    return g.sort_values("Feedback", ascending=False)


def qa_by_tenure(audits: pd.DataFrame) -> pd.DataFrame:
    if audits.empty or "Tenure_Cohort" not in audits.columns:
        return pd.DataFrame()
    g = (
        audits.groupby("Tenure_Cohort", dropna=False)
        .agg(QA_Score=("Score_Pct", "mean"), QA_Evaluations=("Audit_ID", "count"))
        .reset_index()
    )
    g["QA_Score"] = g["QA_Score"].round(2)
    g["QA_Goal"] = QA_GOAL
    g["QA_vs_Goal"] = (g["QA_Score"] - QA_GOAL).round(2)
    g["QA_Status"] = g["QA_Score"].apply(lambda v: _vs_goal_status(v, QA_GOAL, True))
    g["Applies_To"] = "QA only — CSAT/Recontact cannot use this tenure"
    order = {k: i for i, k in enumerate(TENURE_COHORT_ORDER)}
    g["_ord"] = g["Tenure_Cohort"].map(order).fillna(99)
    return g.sort_values(["_ord", "QA_Evaluations"], ascending=[True, False]).drop(columns="_ord")


def csat_by_user_tenure(csat: pd.DataFrame) -> pd.DataFrame:
    """CSAT agent-tenure field from the CSAT tab — not the same taxonomy as QA Tenure."""
    if csat.empty or "user_tenure" not in csat.columns:
        return pd.DataFrame()
    g = csat.copy()
    g["CSAT_Agent_Tenure"] = g["user_tenure"].astype(str).str.strip().str.lower()
    out = (
        g.groupby("CSAT_Agent_Tenure")
        .agg(Satisfied=("Satisfied_CNT", "sum"), Feedback=("Feedback CNT", "sum"))
        .reset_index()
    )
    out["CSAT_Score"] = np.where(out["Feedback"] > 0, (out["Satisfied"] / out["Feedback"] * 100).round(2), np.nan)
    out["CSAT_Goal"] = CSAT_GOAL
    out["CSAT_vs_Goal"] = (out["CSAT_Score"] - CSAT_GOAL).round(2)
    out["Applies_To"] = "CSAT only — do not join to QA Tenure_Cohort"
    return out.sort_values("Feedback", ascending=False)


def kpi_by_channel(audits: pd.DataFrame, csat: pd.DataFrame, recontact: pd.DataFrame) -> pd.DataFrame:
    """One row per channel with whichever KPIs that channel actually has."""
    rows: list[dict] = []

    qa_ch = {}
    if not audits.empty:
        for ch, sub in audits.groupby("Channel"):
            qa_ch[normalize_channel_label(ch)] = {
                "QA_Score": round(float(sub["Score_Pct"].mean()), 2),
                "QA_Evaluations": int(len(sub)),
            }

    csat_ch = {}
    if not csat.empty and "Channel" in csat.columns:
        tmp = csat.copy()
        tmp["Channel_Norm"] = tmp["Channel"].map(normalize_channel_label)
        g = tmp.groupby("Channel_Norm").agg(sat=("Satisfied_CNT", "sum"), fb=("Feedback CNT", "sum"))
        for ch, row in g.iterrows():
            csat_ch[ch] = {
                "CSAT_Score": round(row["sat"] / row["fb"] * 100, 2) if row["fb"] else np.nan,
                "Surveys": int(row["fb"]),
            }

    rc_ch = {}
    if not recontact.empty and "standard_channel_name" in recontact.columns:
        tmp = recontact.copy()
        tmp["Channel_Norm"] = tmp["standard_channel_name"].map(normalize_channel_label)
        g = tmp.groupby("Channel_Norm").agg(vol=("Recontact Volume", "sum"), contacts=("Contacts", "sum"))
        for ch, row in g.iterrows():
            rc_ch[ch] = {
                "Recontact_Rate": round(row["vol"] / row["contacts"] * 100, 2) if row["contacts"] else np.nan,
                "Contacts": int(row["contacts"]),
                "Recontacts": int(row["vol"]),
            }

    channels = sorted(set(qa_ch) | set(csat_ch) | set(rc_ch), key=lambda x: (x not in {"Phone", "Live Chat"}, x))
    for ch in channels:
        row = {"Channel": ch, "Has_QA": ch in qa_ch, "Has_CSAT": ch in csat_ch, "Has_Recontact": ch in rc_ch}
        row.update(qa_ch.get(ch, {"QA_Score": np.nan, "QA_Evaluations": 0}))
        row.update(csat_ch.get(ch, {"CSAT_Score": np.nan, "Surveys": 0}))
        row.update(rc_ch.get(ch, {"Recontact_Rate": np.nan, "Contacts": 0, "Recontacts": 0}))
        if pd.notna(row.get("QA_Score")):
            row["QA_vs_Goal"] = round(row["QA_Score"] - QA_GOAL, 2)
        if pd.notna(row.get("CSAT_Score")):
            row["CSAT_vs_Goal"] = round(row["CSAT_Score"] - CSAT_GOAL, 2)
        if pd.notna(row.get("Recontact_Rate")):
            row["Recontact_vs_Goal"] = round(row["Recontact_Rate"] - RECONTACT_GOAL, 2)
        rows.append(row)
    return pd.DataFrame(rows)


def weekly_by_channel(audits: pd.DataFrame, csat: pd.DataFrame, recontact: pd.DataFrame) -> pd.DataFrame:
    """Week × Channel so Looker/Streamlit can filter without mixing grains."""
    parts: list[pd.DataFrame] = []
    if not audits.empty:
        qa = (
            audits.assign(Channel=audits["Channel"].map(normalize_channel_label))
            .groupby(["Week", "Channel"], as_index=False)
            .agg(QA_Score=("Score_Pct", "mean"), QA_Evaluations=("Audit_ID", "count"))
        )
        qa["QA_Score"] = qa["QA_Score"].round(2)
        parts.append(qa)
    if not csat.empty and "Fecha" in csat.columns and "Channel" in csat.columns:
        cs = csat.copy()
        cs["Week"] = iso_week_label(cs["Fecha"])
        cs["Channel"] = cs["Channel"].map(normalize_channel_label)
        csat_w = cs.groupby(["Week", "Channel"], as_index=False).agg(
            Satisfied=("Satisfied_CNT", "sum"), Feedback=("Feedback CNT", "sum")
        )
        csat_w["CSAT_Score"] = np.where(
            csat_w["Feedback"] > 0, (csat_w["Satisfied"] / csat_w["Feedback"] * 100).round(2), np.nan
        )
        parts.append(csat_w[["Week", "Channel", "CSAT_Score", "Feedback", "Satisfied"]])
    if not recontact.empty and "Fecha" in recontact.columns and "standard_channel_name" in recontact.columns:
        rc = recontact.copy()
        rc["Week"] = iso_week_label(rc["Fecha"])
        rc["Channel"] = rc["standard_channel_name"].map(normalize_channel_label)
        rc_w = rc.groupby(["Week", "Channel"], as_index=False).agg(
            Recontacts=("Recontact Volume", "sum"), Contacts=("Contacts", "sum")
        )
        rc_w["Recontact_Rate"] = np.where(
            rc_w["Contacts"] > 0, (rc_w["Recontacts"] / rc_w["Contacts"] * 100).round(2), np.nan
        )
        parts.append(rc_w[["Week", "Channel", "Recontact_Rate", "Contacts", "Recontacts"]])
    if not parts:
        return pd.DataFrame()
    out = parts[0]
    for p in parts[1:]:
        out = out.merge(p, on=["Week", "Channel"], how="outer")
    out["QA_Goal"] = QA_GOAL
    out["CSAT_Goal"] = CSAT_GOAL
    out["Recontact_Goal"] = RECONTACT_GOAL
    return out.sort_values(["Week", "Channel"]).reset_index(drop=True)


def qa_weekly_by_tenure(audits: pd.DataFrame) -> pd.DataFrame:
    if audits.empty or "Tenure_Cohort" not in audits.columns:
        return pd.DataFrame()
    g = (
        audits.groupby(["Week", "Channel", "Tenure_Cohort"], as_index=False)
        .agg(QA_Score=("Score_Pct", "mean"), QA_Evaluations=("Audit_ID", "count"))
    )
    g["QA_Score"] = g["QA_Score"].round(2)
    g["QA_Goal"] = QA_GOAL
    g["QA_vs_Goal"] = (g["QA_Score"] - QA_GOAL).round(2)
    g["Applies_To"] = "QA only"
    return g.sort_values(["Week", "Channel", "Tenure_Cohort"]).reset_index(drop=True)


def assign_equal_quartiles(series: pd.Series, *, higher_is_better: bool = True) -> pd.Series:
    """Split the current population into 4 equal groups. Q1 = top 25%.

    Edges are not fixed at 85. Ties use pandas qcut (duplicate edges dropped).
    Fewer than four distinct values collapse bins (Q2 if everyone is tied).
    """
    s = pd.to_numeric(series, errors="coerce")
    out = pd.Series(pd.NA, index=series.index, dtype="object")
    valid = s.dropna()
    if valid.empty:
        return out
    work = -valid if higher_is_better else valid
    if work.nunique() < 2:
        out.loc[valid.index] = "Q2"
        return out
    try:
        codes = pd.qcut(work, 4, labels=False, duplicates="drop")
    except ValueError:
        out.loc[valid.index] = "Q2"
        return out
    codes_s = pd.to_numeric(pd.Series(codes, index=valid.index), errors="coerce").dropna()
    try:
        codes_s = codes_s.round().astype(int)
    except (TypeError, ValueError):
        out.loc[valid.index] = "Q2"
        return out
    n_bins = int(codes_s.nunique())
    if n_bins <= 1:
        out.loc[valid.index] = "Q2"
        return out
    if n_bins == 4:
        mapping = {0: "Q1", 1: "Q2", 2: "Q3", 3: "Q4"}
    elif n_bins == 3:
        mapping = {0: "Q1", 1: "Q2", 2: "Q4"}
    elif n_bins == 2:
        mapping = {0: "Q1", 1: "Q4"}
    else:
        mapping = {i: "Q4" if i == n_bins - 1 else ("Q1" if i == 0 else "Q2") for i in range(n_bins)}
    out.loc[codes_s.index] = codes_s.map(mapping)
    return out


def _empty_quartile_frame(*extra: str) -> pd.DataFrame:
    cols = ["Agent_ID", "Supervisor_ID", "Quartile", *extra]
    return pd.DataFrame(columns=list(dict.fromkeys(cols)))


def qa_agent_quartiles(audits: pd.DataFrame, min_n: int = RANKING_QA_MIN_N) -> pd.DataFrame:
    """Official QA (mean Score_Pct) with qcut quartiles on the current filter.

    Q4 is the bottom 25% of agents who meet `min_n` audits — not a 85 cutoff.
    """
    roster = qa_agent_roster(audits, None, min_n=min_n)
    if roster is None or roster.empty:
        return _empty_quartile_frame("QA_Score", "QA_n")
    out = roster.copy()
    out["QA_n"] = pd.to_numeric(out.get("Audit_Count"), errors="coerce").fillna(0).astype(int)
    out["Quartile"] = assign_equal_quartiles(out["QA_Score"], higher_is_better=True)
    keep = [c for c in (
        "Agent_ID", "Supervisor_ID", "Tenure_Cohort", "QA_Score", "QA_n", "Quartile",
    ) if c in out.columns]
    return out[keep].reset_index(drop=True)


def csat_agent_quartiles(
    csat: pd.DataFrame,
    audits: pd.DataFrame,
    min_n: int = RANKING_CSAT_MIN_N,
) -> pd.DataFrame:
    """Official CSAT (4★+5★ / Feedback, ratio of sums) with qcut on this filter."""
    roster = csat_agent_roster(csat, audits, min_n=min_n)
    if roster is None or roster.empty:
        return _empty_quartile_frame("CSAT_Score", "CSAT_n")
    out = roster.copy()
    if "Agent_ID" not in out.columns:
        out["Agent_ID"] = out["Agent"] if "Agent" in out.columns else ""
    out["CSAT_n"] = pd.to_numeric(out.get("Feedback"), errors="coerce").fillna(0).astype(int)
    out["Quartile"] = assign_equal_quartiles(out["CSAT_Score"], higher_is_better=True)
    keep = [c for c in (
        "Agent_ID", "Agent", "Supervisor_ID", "CSAT_Score", "CSAT_n", "Quartile",
    ) if c in out.columns]
    return out[keep].reset_index(drop=True)


def quartile_band_summary(
    df: pd.DataFrame,
    *,
    name_col: str = "Agent_ID",
    n_names: int = 5,
) -> dict:
    """Counts and a few names per Q1–Q4. Safe on empty / NA quartile columns."""
    bands = {q: {"n": 0, "names": []} for q in ("Q1", "Q2", "Q3", "Q4")}
    empty = {"ranked": 0, "q4": 0, "bands": bands}
    if df is None or df.empty or "Quartile" not in df.columns:
        return empty
    work = df.copy()
    work["Quartile"] = work["Quartile"].astype(str)
    ranked = work[work["Quartile"].isin(("Q1", "Q2", "Q3", "Q4"))]
    if ranked.empty:
        return empty
    label_col = name_col if name_col in ranked.columns else (
        "Agent_ID" if "Agent_ID" in ranked.columns else (
            "Agent" if "Agent" in ranked.columns else None
        )
    )
    for q in bands:
        sub = ranked[ranked["Quartile"] == q]
        bands[q]["n"] = int(len(sub))
        if label_col:
            bands[q]["names"] = [str(v) for v in sub[label_col].astype(str).head(int(n_names)).tolist()]
    return {"ranked": int(len(ranked)), "q4": bands["Q4"]["n"], "bands": bands}


def supervisor_quartile_mix(
    agents: pd.DataFrame,
    supervisor_kpis: pd.DataFrame | None = None,
    *,
    q4_share_alert: float = SUPERVISOR_Q4_SHARE_ALERT,
) -> pd.DataFrame:
    """Option A talent mix: share of each TL's agents in company Q1–Q4.

    Quartiles are the company (current-filter) bands already on `agents`.
    Official team QA/CSAT attach for context — they are not the talent mix.
    """
    if agents is None or agents.empty or "Supervisor_ID" not in agents.columns:
        return pd.DataFrame()
    if "Quartile" not in agents.columns:
        return pd.DataFrame()
    work = agents.copy()
    work["Quartile"] = work["Quartile"].astype(str)
    work = work[work["Quartile"].isin(("Q1", "Q2", "Q3", "Q4"))]
    if work.empty:
        return pd.DataFrame()
    rows = []
    for sup, team in work.groupby("Supervisor_ID"):
        n = int(len(team))
        n_q1 = int((team["Quartile"] == "Q1").sum())
        n_q2 = int((team["Quartile"] == "Q2").sum())
        n_q3 = int((team["Quartile"] == "Q3").sum())
        n_q4 = int((team["Quartile"] == "Q4").sum())
        rows.append({
            "Supervisor_ID": str(sup),
            "Ranked_Agents": n,
            "Q1_n": n_q1, "Q2_n": n_q2, "Q3_n": n_q3, "Q4_n": n_q4,
            "Q1_pct": round(n_q1 / n * 100, 1) if n else 0.0,
            "Q2_pct": round(n_q2 / n * 100, 1) if n else 0.0,
            "Q3_pct": round(n_q3 / n * 100, 1) if n else 0.0,
            "Q4_pct": round(n_q4 / n * 100, 1) if n else 0.0,
            "Q4_Share": round(n_q4 / n * 100, 1) if n else 0.0,
            "Q4_Agents": n_q4,
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["Talent_Quartile"] = assign_equal_quartiles(out["Q4_Share"], higher_is_better=False)
    out["Requires_Review"] = (
        (out["Q4_Share"] >= float(q4_share_alert))
        | (out["Talent_Quartile"].astype(str) == "Q4")
    )
    if supervisor_kpis is not None and not supervisor_kpis.empty and "Supervisor_ID" in supervisor_kpis.columns:
        extra = supervisor_kpis.copy()
        extra["Supervisor_ID"] = extra["Supervisor_ID"].astype(str)
        keep = [c for c in (
            "Supervisor_ID", "QA_Score", "CSAT_Score", "n", "Feedback", "Agents", "AHT_min",
        ) if c in extra.columns]
        out = out.merge(extra[keep], on="Supervisor_ID", how="left")
    if "QA_Score" in out.columns:
        out["QA_below"] = pd.to_numeric(out["QA_Score"], errors="coerce") < QA_GOAL
    if "CSAT_Score" in out.columns:
        out["CSAT_below"] = pd.to_numeric(out["CSAT_Score"], errors="coerce") < CSAT_GOAL
    return out.sort_values(
        ["Requires_Review", "Q4_Share", "Ranked_Agents"],
        ascending=[False, False, False],
    ).reset_index(drop=True)


def _aht_percentile_score(duration: pd.Series) -> pd.Series:
    """Lower handle time → higher score (0–100). Percentile among this series."""
    s = pd.to_numeric(duration, errors="coerce")
    n = int(s.notna().sum())
    out = pd.Series(np.nan, index=s.index, dtype=float)
    if n == 0:
        return out
    if n == 1:
        out.loc[s.notna()] = 50.0
        return out
    rank = s.rank(method="average", ascending=True)
    out = (1.0 - (rank - 1.0) / (n - 1)) * 100.0
    return out


def agent_ranking_index(
    audits: pd.DataFrame,
    csat: pd.DataFrame,
    *,
    qa_min: int = RANKING_QA_MIN_N,
    csat_min: int = RANKING_CSAT_MIN_N,
) -> pd.DataFrame:
    """Agent ranking index: 0.50 QA + 0.30 CSAT + 0.20 AHT percentile.

    Ranking tool only — not a contractual KPI. Recontact / FCR are omitted because
    recontact has no agent, supervisor, tenure, or country field.
    Agents below QA n or CSAT n stay on the table as insufficient sample.
    Quartiles are qcut on the ranking index among agents who meet both floors
    and have a Duration (AHT). Q1 = top 25% of that population.
    """
    empty_cols = [
        "Agent_ID", "Supervisor_ID", "Tenure_Cohort", "QA_Score", "QA_n",
        "CSAT_Score", "CSAT_n", "AHT_min", "AHT_Score", "Ranking_Index",
        "Sample_OK", "Quartile",
    ]
    if audits is None or audits.empty or "Agent_ID" not in audits.columns:
        return pd.DataFrame(columns=empty_cols)

    qa = audits.copy()
    qa["_key"] = qa["Agent_ID"].astype(str).str.strip()
    qa = qa[qa["_key"].ne("") & qa["_key"].str.casefold().ne("nan")]
    if qa.empty:
        return pd.DataFrame(columns=empty_cols)
    if "Duration" in qa.columns:
        qa["Duration"] = pd.to_numeric(qa["Duration"], errors="coerce")
    else:
        qa["Duration"] = np.nan
    group = ["_fold"]
    qa["_fold"] = qa["_key"].str.casefold()
    agg = {
        "Agent_ID": ("_key", "first"),
        "QA_Score": ("Score_Pct", "mean"),
        "QA_n": ("Audit_ID", "count"),
        "AHT_sec": ("Duration", "mean"),
    }
    if "Supervisor_ID" in qa.columns:
        agg["Supervisor_ID"] = ("Supervisor_ID", "first")
    if "Tenure_Cohort" in qa.columns:
        agg["Tenure_Cohort"] = ("Tenure_Cohort", "first")
    g = qa.groupby("_fold", as_index=False).agg(**agg)
    if "Supervisor_ID" not in g.columns:
        g["Supervisor_ID"] = "Unknown"
    if "Tenure_Cohort" not in g.columns:
        g["Tenure_Cohort"] = "Unknown"
    g["QA_Score"] = pd.to_numeric(g["QA_Score"], errors="coerce").round(1)
    g["AHT_min"] = (pd.to_numeric(g["AHT_sec"], errors="coerce") / 60.0).round(1)

    csat_map = pd.DataFrame(columns=["_fold", "CSAT_Score", "CSAT_n"])
    if (
        csat is not None and not csat.empty
        and "Agent name" in csat.columns
        and "Feedback CNT" in csat.columns
        and "Satisfied_CNT" in csat.columns
    ):
        cs = csat.copy()
        cs["_fold"] = cs["Agent name"].astype(str).str.strip().str.casefold()
        cs = cs[cs["_fold"].ne("") & cs["_fold"].ne("nan")]
        if not cs.empty:
            csat_map = (
                cs.groupby("_fold", as_index=False)
                .agg(
                    Satisfied=("Satisfied_CNT", "sum"),
                    CSAT_n=("Feedback CNT", "sum"),
                )
            )
            csat_map["CSAT_Score"] = np.where(
                csat_map["CSAT_n"] > 0,
                (csat_map["Satisfied"] / csat_map["CSAT_n"] * 100).round(1),
                np.nan,
            )
            csat_map = csat_map[["_fold", "CSAT_Score", "CSAT_n"]]

    out = g.merge(csat_map, on="_fold", how="left")
    out["CSAT_n"] = pd.to_numeric(out.get("CSAT_n"), errors="coerce").fillna(0)
    out["Sample_OK"] = (
        (pd.to_numeric(out["QA_n"], errors="coerce").fillna(0) >= int(qa_min))
        & (out["CSAT_n"] >= int(csat_min))
        & pd.to_numeric(out["AHT_sec"], errors="coerce").notna()
        & pd.to_numeric(out["QA_Score"], errors="coerce").notna()
        & pd.to_numeric(out["CSAT_Score"], errors="coerce").notna()
    )
    ranked_idx = out.index[out["Sample_OK"]]
    out["AHT_Score"] = np.nan
    if len(ranked_idx):
        out.loc[ranked_idx, "AHT_Score"] = _aht_percentile_score(
            out.loc[ranked_idx, "AHT_sec"]
        ).round(1)

    w = RANKING_INDEX_WEIGHTS
    qa_s = pd.to_numeric(out["QA_Score"], errors="coerce")
    cs_s = pd.to_numeric(out["CSAT_Score"], errors="coerce")
    ah_s = pd.to_numeric(out["AHT_Score"], errors="coerce")
    out["Ranking_Index"] = np.where(
        out["Sample_OK"],
        (qa_s * w["qa"] + cs_s * w["csat"] + ah_s * w["aht"]).round(1),
        np.nan,
    )
    out["Quartile"] = pd.NA
    if out["Sample_OK"].any():
        q = assign_equal_quartiles(out.loc[out["Sample_OK"], "Ranking_Index"], higher_is_better=True)
        out.loc[q.index, "Quartile"] = q
    out["QA_below"] = pd.to_numeric(out["QA_Score"], errors="coerce") < QA_GOAL
    out["CSAT_below"] = pd.to_numeric(out["CSAT_Score"], errors="coerce") < CSAT_GOAL
    keep = [
        "Agent_ID", "Supervisor_ID", "Tenure_Cohort", "QA_Score", "QA_n",
        "CSAT_Score", "CSAT_n", "AHT_min", "AHT_Score", "Ranking_Index",
        "Sample_OK", "Quartile", "QA_below", "CSAT_below",
    ]
    return (
        out[keep]
        .sort_values(["Sample_OK", "Ranking_Index", "QA_n"], ascending=[False, True, False])
        .reset_index(drop=True)
    )


def supervisor_talent_frame(
    agent_rank: pd.DataFrame,
    supervisor_kpis: pd.DataFrame | None = None,
    *,
    q4_share_alert: float = SUPERVISOR_Q4_SHARE_ALERT,
) -> pd.DataFrame:
    """Supervisor Option A: share of that TL's ranked agents in company-wide Q4.

    Option B (team mean ranking index + official QA/CSAT) is attached for context.
    Leadership flag: Q4 share ≥ `q4_share_alert` or the TL lands in Q4 of Option A.
    Recontact is not on this table.
    """
    if agent_rank is None or agent_rank.empty or "Supervisor_ID" not in agent_rank.columns:
        return pd.DataFrame()
    ranked = agent_rank[agent_rank["Sample_OK"].astype(bool)].copy()
    if ranked.empty:
        return pd.DataFrame()
    ranked["Quartile"] = ranked["Quartile"].astype(str)
    rows = []
    for sup, team in ranked.groupby("Supervisor_ID"):
        n = int(len(team))
        n_q1 = int((team["Quartile"] == "Q1").sum())
        n_q2 = int((team["Quartile"] == "Q2").sum())
        n_q3 = int((team["Quartile"] == "Q3").sum())
        n_q4 = int((team["Quartile"] == "Q4").sum())
        rows.append({
            "Supervisor_ID": str(sup),
            "Ranked_Agents": n,
            "Q1_n": n_q1, "Q2_n": n_q2, "Q3_n": n_q3, "Q4_n": n_q4,
            "Q1_pct": round(n_q1 / n * 100, 1) if n else 0.0,
            "Q2_pct": round(n_q2 / n * 100, 1) if n else 0.0,
            "Q3_pct": round(n_q3 / n * 100, 1) if n else 0.0,
            "Q4_pct": round(n_q4 / n * 100, 1) if n else 0.0,
            "Q4_Share": round(n_q4 / n * 100, 1) if n else 0.0,
            "Team_Index": round(float(team["Ranking_Index"].mean()), 1),
            "Q4_Agents": n_q4,
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["Talent_Quartile"] = assign_equal_quartiles(out["Q4_Share"], higher_is_better=False)
    out["Requires_Review"] = (
        (out["Q4_Share"] >= float(q4_share_alert))
        | (out["Talent_Quartile"].astype(str) == "Q4")
    )
    if supervisor_kpis is not None and not supervisor_kpis.empty and "Supervisor_ID" in supervisor_kpis.columns:
        extra = supervisor_kpis.copy()
        extra["Supervisor_ID"] = extra["Supervisor_ID"].astype(str)
        keep = [c for c in ("Supervisor_ID", "QA_Score", "CSAT_Score", "n", "Feedback", "Agents", "AHT_min") if c in extra.columns]
        out = out.merge(extra[keep], on="Supervisor_ID", how="left")
    out["QA_below"] = pd.to_numeric(out.get("QA_Score"), errors="coerce") < QA_GOAL
    out["CSAT_below"] = pd.to_numeric(out.get("CSAT_Score"), errors="coerce") < CSAT_GOAL
    return out.sort_values(["Requires_Review", "Q4_Share", "Team_Index"], ascending=[False, False, True]).reset_index(drop=True)

