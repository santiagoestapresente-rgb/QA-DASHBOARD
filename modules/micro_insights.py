"""Micro-insights for dashboard cards — Excel figures only, ≤15 words."""

from __future__ import annotations

import pandas as pd

from config import CSAT_GOAL, QA_GOAL, RECONTACT_GOAL


def _fmt(v, digits: int = 1) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return f"{float(v):.{digits}f}"


def _clip(name: object, n: int = 36) -> str:
    text = " ".join(str(name).split())
    if len(text) <= n:
        return text
    cut = text[: max(n - 1, 1)]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut + "…"


def chip(text: str, tone: str = "info", icon: str = "") -> dict:
    return {"text": text, "tone": tone, "icon": icon}


def fcr_scope_chip(
    fcr_official: float,
    fcr_audited: float | None,
    sh_share: float | None,
    repeats: int | None = None,
) -> dict:
    if fcr_audited is None:
        return chip(
            f"Official FCR {_fmt(fcr_official, 2)}% is 100 minus recontact. No FCR target.",
            "info",
        )
    share = f"{sh_share:.0f}%" if sh_share is not None and pd.notna(sh_share) else "—"
    return chip(
        f"Phone+Chat FCR {_fmt(fcr_audited, 1)}%. Official {_fmt(fcr_official, 1)}% includes Self Help ({share}).",
        "risk",
    )


def qa_chip(qa: float) -> dict:
    gap = qa - QA_GOAL
    if gap >= 0:
        return chip(f"QA {_fmt(qa)}% beats the 85 audit goal ({gap:+.1f} points).", "ok")
    return chip(f"QA {_fmt(qa)}% is {abs(gap):.1f} points below the 85 goal.", "risk")


def csat_chip(csat: float) -> dict:
    gap = csat - CSAT_GOAL
    if gap >= 0:
        return chip(f"CSAT {_fmt(csat)}% meets the 4 or 5 star share goal.", "ok")
    return chip(f"CSAT {_fmt(csat)}% is {abs(gap):.1f} points below the 85% goal.", "risk")


def pareto_chip(df: pd.DataFrame, cat_col: str, count_col: str, unit: str) -> dict:
    if df is None or df.empty or cat_col not in df.columns or count_col not in df.columns:
        return chip("No volume in this filter.", "info")
    p = df.sort_values(count_col, ascending=False)
    total = float(p[count_col].sum())
    top = p.iloc[0]
    share = float(top[count_col]) / total * 100 if total else 0
    label = unit
    if count_col == "Gap_Impact" or "weighted" in (unit or "").lower():
        label = "weighted deficit"
    return chip(
        f"{_clip(top[cat_col], 36)}: {share:.0f}% of {label}.",
        "risk" if share >= 20 else "info",
    )


def rate_chip(name: object, rate: float, goal: float, lower_better: bool = True) -> dict:
    miss = rate > goal if lower_better else rate < goal
    if miss:
        return chip(f"{_clip(name, 36)} at {_fmt(rate, 2)}% vs {goal:g} goal.", "risk")
    return chip(f"{_clip(name, 36)} at {_fmt(rate, 2)}% vs {goal:g} goal.", "ok")


def attr_chip(df: pd.DataFrame, crit: dict | None = None) -> dict:
    if df is None or df.empty:
        return chip("No attribute fails in this filter.", "info")
    top = df.iloc[0]
    name = _clip(top.get("Error_Category", top.iloc[0]), 36)
    share = top.get("Pct_Of_Fails")
    crit_n = (crit or {}).get("n_crit_fails")
    if share is not None and pd.notna(share):
        return chip(f"{name} is {float(share):.0f}% of QA fails.", "risk")
    if crit_n:
        return chip(f"{int(crit_n):,} CRITICAL fails zero the audit score.", "risk")
    return chip(f"Top fail: {name}.", "risk")


def voc_chip(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return chip("No 1–3 star comment themes in this filter.", "info")
    top = df.iloc[0]
    n = top["Mentions"] if "Mentions" in top else top.get("n", top.iloc[1])
    low = top["Total_Low"] if "Total_Low" in top and pd.notna(top["Total_Low"]) else None
    theme = str(top.get("Theme") or "")
    short = {
        "Refund / compensation not received": "refunds",
        "Driver behavior": "driver behavior",
        "Long wait time": "long waits",
        "No solution provided": "no solution",
        "Agent attitude": "agent attitude",
        "Order / trip issues": "order or trip issues",
    }.get(theme, theme.split("/")[0].strip().lower())
    if low and int(low) > 0:
        pct = int(n) / int(low) * 100
        return chip(f"{int(n):,} of {int(low):,} 1–3★ comments are about {short} ({pct:.0f}%).", "risk")
    return chip(f"{int(n):,} of the 1–3 star comments are about {short}.", "risk")


def scatter_chip(r: float | None, n: int, pair: str) -> dict:
    if r is None or pd.isna(r) or n < 5:
        return chip(
            f"{pair}: {int(n)} shared Lv4 name(s); R² needs ≥5 names, not surveys.",
            "info",
        )
    r2 = float(r) ** 2
    mag = abs(float(r))
    if mag < 0.20:
        return chip(f"{pair} R²={r2:.2f} — almost no relationship (N={n}).", "info")
    side = "negative" if float(r) < 0 else "positive"
    tone = "risk" if mag >= 0.40 else "info"
    return chip(f"{pair} R²={r2:.2f} ({side}) on {n} shared Lv4.", tone)


def aht_overlap_empty_text(
    n_shared: int,
    other: str,
    *,
    surveys: int | None = None,
    audits: int | None = None,
    min_audits: int = 3,
) -> str:
    """Plot annotation when CSAT/QA/recontact vs handle time has no points."""
    bits = []
    if surveys is not None:
        bits.append(f"{int(surveys):,} surveys")
    if audits is not None:
        bits.append(f"{int(audits):,} QA audits")
    lead = ("; ".join(bits) + ". ") if bits else ""
    return (
        f"{lead}Each point is a shared contact reason Lv4 (detail) name, not a survey. "
        f"Handle time is mean QA Duration (≥{int(min_audits)} audits). "
        f"This filter has {int(n_shared)} name(s) with both handle time and {other}."
    )


def r_explain(
    r: float | None,
    n: int,
    pair: str,
    *,
    surveys: int | None = None,
    audits: int | None = None,
) -> dict:
    """Short box copy for association scatters. Lead with R²; sign comes from r."""
    title = "What R² means"
    n_val = int(n) if n is not None and pd.notna(n) else 0
    if r is None or pd.isna(r) or n_val < 5:
        bits = []
        if surveys is not None:
            bits.append(f"{int(surveys):,} surveys")
        if audits is not None:
            bits.append(f"{int(audits):,} QA audits")
        lead = ("; ".join(bits) + ". ") if bits else ""
        handle = ""
        if "handle" in pair.lower() or "aht" in pair.lower():
            handle = (
                " Handle time is mean QA Duration at that name, not a CSAT field."
            )
        return {
            "title": title,
            "body": (
                f"{lead}{pair}: {n_val} shared contact reason Lv4 (detail) name(s) "
                "have both values. R² needs at least 5 shared names — not 5 surveys."
                f"{handle}"
            ),
        }
    r2 = float(r) ** 2
    mag = abs(float(r))
    if mag < 0.20:
        strength = "almost no relationship"
    elif mag < 0.40:
        strength = "a weak relationship"
    elif mag < 0.60:
        strength = "a moderate relationship"
    else:
        strength = "a strong relationship"
    move = ""
    if mag >= 0.05:
        move = (
            " The slope is positive: when one goes up, the other tends to go up."
            if float(r) > 0
            else " The slope is negative: when one goes up, the other tends to go down."
        )
    return {
        "title": title,
        "body": (
            f"R² is {r2:.2f} on {n} contact reason Lv4 (detail) names — {strength}.{move} "
            "R² is the share of one score that a straight line in the other can explain."
        ),
    }


def combined_chip(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return chip("No contact reason Lv4 (detail) fails more than one KPI.", "info")
    row = df.iloc[0]
    name = _clip(row["CR_Lv4"], 36)
    bits = []
    if row.get("low_qa"):
        bits.append(f"QA {_fmt(row.get('QA_Score'))}%")
    if row.get("low_csat"):
        bits.append(f"CSAT {_fmt(row.get('CSAT_Score'))}%")
    if row.get("high_rc"):
        bits.append(f"recontact {_fmt(row.get('Recontact_Rate'), 2)}%")
    detail = " and ".join(bits) if bits else str(row.get("Pattern") or "off goal")
    return chip(f"Lv4 {name}: {detail}.", "risk")


def weekly_chip(weekly: pd.DataFrame) -> dict:
    if weekly is None or weekly.empty:
        return chip("No weekly rows in this filter.", "info")
    last = weekly.dropna(how="all").tail(1).iloc[0]
    csat = last.get("CSAT_Score")
    rc = last.get("Recontact_Rate")
    if pd.notna(csat) and float(csat) < CSAT_GOAL:
        return chip(f"Latest CSAT week {_fmt(csat)}% — still below 85.", "risk")
    if pd.notna(rc) and float(rc) > RECONTACT_GOAL:
        return chip(f"Latest recontact week {_fmt(rc, 2)}% vs 5.44.", "risk")
    qa = last.get("QA_Score")
    if pd.notna(qa):
        return chip(f"Latest QA week {_fmt(qa)}% vs the 85 goal.", "info")
    return chip("Latest week has incomplete KPI coverage.", "info")


def channel_chip(df: pd.DataFrame) -> dict:
    if df is None or df.empty or "Recontact_Rate" not in df.columns:
        return chip("No channel KPI rows in this filter.", "info")
    sub = df[df["Segment"].astype(str).str.lower() != "overall"] if "Segment" in df.columns else df
    if sub.empty:
        sub = df
    row = sub.sort_values("Recontact_Rate", ascending=False).iloc[0]
    return chip(
        f"{row['Segment']} recontact {_fmt(row['Recontact_Rate'], 2)}% vs 5.44.",
        "risk" if float(row["Recontact_Rate"]) > RECONTACT_GOAL else "ok",
    )


def gap_chip(df: pd.DataFrame, unit: str) -> dict:
    if df is None or df.empty:
        return chip(f"No {unit} gap vs goal in this filter.", "ok")
    top = df.iloc[0]
    return chip(f"{_clip(top['Cat'], 36)} is the largest {unit} weighted deficit.", "risk")


def tenure_chip(df: pd.DataFrame, score_col: str, name_col: str, goal: float) -> dict:
    if df is None or df.empty or score_col not in df.columns:
        return chip("No tenure rows in this filter.", "info")
    row = df.sort_values(score_col).iloc[0]
    val = float(row[score_col])
    name = _clip(row[name_col], 36)
    if val < goal:
        return chip(f"{name} at {_fmt(val)}% — furthest from {goal:g}.", "risk")
    return chip(f"Every tenure band is at or above {goal:g}.", "ok")
