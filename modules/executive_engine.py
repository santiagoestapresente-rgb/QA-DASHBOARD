"""
Executive insight engine — combined analysis, root cause, action plan.
All outputs derived from Business Case data only.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from config import CSAT_GOAL, QA_GOAL, RECONTACT_GOAL
from modules.kpis import (
    _vs_goal_status,
    critical_fail_stats,
    qa_channel_dispersion,
    qa_score_by_cr,
    recontact_by_scope,
    recontact_rate,
    top_failing_attributes,
    filter_by_iso_weeks,
)


@dataclass
class ActionPlanItem:
    finding: str
    action: str
    owner: str
    priority: str
    timeline: str


@dataclass
class ExecutiveBrief:
    insight: str
    action: str
    hypothesis: str
    worst_metric: str
    worst_channel: str
    worst_cr: str
    top_defect: str
    top_recontact_cr: str
    top_voc_theme: str
    combined_cr: str


def combined_operational_analysis(
    audits: pd.DataFrame,
    csat: pd.DataFrame,
    recontact: pd.DataFrame,
    min_audits: int = 3,
    min_feedback: int = 10,
    min_contacts: int = 50,
) -> pd.DataFrame:
    """CR Lv4 rows where multiple KPIs fail simultaneously."""
    if audits.empty:
        return pd.DataFrame()

    qa = audits.copy()
    qa["_key"] = qa["CR_Lv4"].astype(str).str.strip().str.casefold()
    qa_cr = (
        qa.groupby("_key", as_index=False)
        .agg(CR_Lv4=("CR_Lv4", "first"), QA_Score=("Score_Pct", "mean"), QA_N=("Audit_ID", "count"))
    )
    qa_cr = qa_cr[qa_cr["QA_N"] >= min_audits]

    csat_cr = pd.DataFrame(columns=["_key", "CR_Lv4", "CSAT_Score", "Feedback"])
    if not csat.empty and "CR_Lv4" in csat.columns:
        cs = csat.copy()
        cs["_key"] = cs["CR_Lv4"].astype(str).str.strip().str.casefold()
        csat_cr = (
            cs.groupby("_key", as_index=False)
            .agg(CR_Lv4=("CR_Lv4", "first"), Feedback=("Feedback CNT", "sum"), Satisfied=("Satisfied_CNT", "sum"))
        )
        csat_cr["CSAT_Score"] = (csat_cr["Satisfied"] / csat_cr["Feedback"] * 100).round(2)
        csat_cr = csat_cr[csat_cr["Feedback"] >= min_feedback]

    rc_cr = pd.DataFrame(columns=["_key", "CR_Lv4", "Recontact_Rate", "Contacts", "Recontacts"])
    if not recontact.empty:
        rc = recontact.copy()
        rc["_key"] = rc["CR_Lv4"].astype(str).str.strip().str.casefold()
        rc_cr = (
            rc.groupby("_key", as_index=False)
            .agg(CR_Lv4=("CR_Lv4", "first"), Contacts=("Contacts", "sum"), Recontacts=("Recontact Volume", "sum"))
        )
        rc_cr["Recontact_Rate"] = (rc_cr["Recontacts"] / rc_cr["Contacts"] * 100).round(2)
        rc_cr = rc_cr[rc_cr["Contacts"] >= min_contacts]

    merged = qa_cr.merge(csat_cr[["_key", "CSAT_Score", "Feedback"]], on="_key", how="left")
    merged = merged.merge(rc_cr[["_key", "Recontact_Rate", "Contacts", "Recontacts"]], on="_key", how="left")
    merged = merged.drop(columns=["_key"])

    merged["QA_vs"] = (merged["QA_Score"] - QA_GOAL).round(1)
    merged["CSAT_vs"] = (merged["CSAT_Score"] - CSAT_GOAL).round(1)
    merged["RC_vs"] = (merged["Recontact_Rate"] - RECONTACT_GOAL).round(2)

    merged["low_qa"] = merged["QA_Score"] < QA_GOAL
    merged["low_csat"] = merged["CSAT_Score"] < CSAT_GOAL
    merged["high_rc"] = merged["Recontact_Rate"] > RECONTACT_GOAL

    def _pattern(row) -> str:
        flags = []
        if row.get("low_qa"):
            flags.append("Low QA")
        if row.get("low_csat"):
            flags.append("Low CSAT")
        if row.get("high_rc"):
            flags.append("High Recontact")
        return " + ".join(flags) if flags else "Within target"

    merged["Pattern"] = merged.apply(_pattern, axis=1)
    merged["Impact_Score"] = (
        merged["low_qa"].astype(int) * merged["QA_N"].fillna(0)
        + merged["low_csat"].astype(int) * merged["Feedback"].fillna(0) / 100
        + merged["high_rc"].astype(int) * merged["Recontacts"].fillna(0)
    )
    risk = merged[merged["Pattern"] != "Within target"].copy()
    return risk.sort_values("Impact_Score", ascending=False).head(10)


def qa_channel_breakdown(audits: pd.DataFrame, errors: pd.DataFrame) -> dict:
    """Phone vs Live Chat — score, top defects, worst CR (separate attribute sets)."""
    out: dict = {}
    for ch in ["Phone", "Live Chat"]:
        sub_a = audits[audits["Channel"] == ch]
        sub_e = errors[errors["Channel"] == ch] if "Channel" in errors.columns else pd.DataFrame()
        qa_val = sub_a["Score_Pct"].mean() if not sub_a.empty else None
        stats = critical_fail_stats(sub_a, sub_e)
        out[ch] = {
            "qa_score": round(qa_val, 1) if qa_val is not None else None,
            "qa_vs": round(qa_val - QA_GOAL, 1) if qa_val is not None else None,
            "qa_status": _vs_goal_status(qa_val, QA_GOAL, True) if qa_val is not None else "neutral",
            "top_attrs": top_failing_attributes(sub_e, sub_a, top_n=3),
            "worst_cr": qa_score_by_cr(sub_a, top_n=3),
            "audit_count": len(sub_a),
            "pct_fatal": stats["pct_fatal"],
            "n_crit_fails": stats["n_crit_fails"],
            "n_noncrit_fails": stats["n_noncrit_fails"],
        }
    return out


def requester_performance(
    audits: pd.DataFrame,
    csat: pd.DataFrame,
    recontact: pd.DataFrame,
) -> pd.DataFrame:
    """Only categories present in dataset."""
    rows: list[dict] = []
    requesters = sorted(audits["Requester"].dropna().unique().tolist()) if "Requester" in audits.columns else []
    if not requesters and "User Type" in csat.columns:
        requesters = sorted(csat["User Type"].dropna().unique().tolist())

    for req in requesters:
        qa_sub = audits[audits["Requester"] == req] if "Requester" in audits.columns else audits
        qa_val = qa_sub["Score_Pct"].mean() if not qa_sub.empty else None

        cs = csat[csat["User Type"] == req] if "User Type" in csat.columns else csat
        csat_val = cs["Satisfied_CNT"].sum() / cs["Feedback CNT"].sum() * 100 if not cs.empty and cs["Feedback CNT"].sum() else None

        rc_sub = recontact[recontact["User_Type"] == req] if "User_Type" in recontact.columns else recontact
        rc_val = recontact_rate(rc_sub) if not rc_sub.empty else None

        rows.append({
            "Segment": req,
            "QA_Score": qa_val,
            "CSAT_Score": csat_val,
            "Recontact_Rate": rc_val,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=[
            "Segment", "QA_Score", "CSAT_Score", "Recontact_Rate",
            "QA_Score_vs", "CSAT_Score_vs", "Recontact_Rate_vs",
            "QA_Score_status", "CSAT_Score_status", "Recontact_Rate_status",
        ])
    for col, goal, hib in [
        ("QA_Score", QA_GOAL, True),
        ("CSAT_Score", CSAT_GOAL, True),
        ("Recontact_Rate", RECONTACT_GOAL, False),
    ]:
        df[f"{col}_vs"] = df[col].apply(lambda v: round(v - goal, 2) if pd.notna(v) else None)
        df[f"{col}_status"] = df[col].apply(lambda v: _vs_goal_status(v, goal, hib) if pd.notna(v) else "neutral")
    return df


def csat_segmentation(csat: pd.DataFrame, top_n: int | None = 5, min_n: int = 20) -> pd.DataFrame:
    """Dimensions with meaningful CSAT variance (Channel, CR Lv4, Country)."""
    if csat.empty:
        return pd.DataFrame()

    segments: list[pd.DataFrame] = []
    dims = [
        ("Channel", "Channel"),
        ("Contact reason Lv4 (detail)", "CR_Lv4"),
        ("Country", "Country Code"),
    ]
    for label, col in dims:
        if col not in csat.columns:
            continue
        g = (
            csat.groupby(col)
            .agg(Feedback=("Feedback CNT", "sum"), Satisfied=("Satisfied_CNT", "sum"))
            .reset_index()
        )
        if min_n:
            g = g[g["Feedback"] >= int(min_n)]
        if g.empty:
            continue
        g["CSAT_Score"] = (g["Satisfied"] / g["Feedback"] * 100).round(1)
        g["vs_goal"] = (g["CSAT_Score"] - CSAT_GOAL).round(1)
        g["Dimension"] = label
        g = g.rename(columns={col: "Segment"})
        segments.append(g[["Dimension", "Segment", "CSAT_Score", "vs_goal", "Feedback"]])

    if not segments:
        return pd.DataFrame()
    all_seg = pd.concat(segments, ignore_index=True).sort_values("vs_goal")
    if top_n is not None:
        return all_seg.head(int(top_n) * 3)
    return all_seg


def period_volume_delta(
    audits_all: pd.DataFrame,
    csat_all: pd.DataFrame,
    recontact_all: pd.DataFrame,
    sel_weeks: list[str],
) -> dict:
    """WoW comparison for volume KPIs."""
    empty = {
        "contacts_delta": None, "surveys_delta": None, "evals_delta": None, "recontacts_delta": None,
        "contacts_arrow": "→", "surveys_arrow": "→", "evals_arrow": "→", "recontacts_arrow": "→",
    }
    weeks = sorted(audits_all["Week"].dropna().astype(str).unique())
    if not sel_weeks or len(weeks) < 2:
        return empty

    last = sel_weeks[-1]
    if last not in weeks:
        return empty
    idx = weeks.index(last)
    if idx == 0:
        return empty
    prev = weeks[idx - 1]

    def _evals(w):
        return len(audits_all[audits_all["Week"] == w])

    def _week_sum(df, col, week_label):
        if df.empty or col not in df.columns:
            return 0
        sub = filter_by_iso_weeks(df, [week_label])
        return float(sub[col].sum()) if not sub.empty else 0

    cur_e, prev_e = _evals(last), _evals(prev)
    evals_delta = ((cur_e - prev_e) / prev_e * 100) if prev_e else None

    cur_c = _week_sum(recontact_all, "Contacts", last)
    prev_c = _week_sum(recontact_all, "Contacts", prev)
    cur_r = _week_sum(recontact_all, "Recontact Volume", last)
    prev_r = _week_sum(recontact_all, "Recontact Volume", prev)
    cur_s = _week_sum(csat_all, "Feedback CNT", last)
    prev_s = _week_sum(csat_all, "Feedback CNT", prev)

    contacts_delta = ((cur_c - prev_c) / prev_c * 100) if prev_c else None
    recontacts_delta = ((cur_r - prev_r) / prev_r * 100) if prev_r else None
    surveys_delta = ((cur_s - prev_s) / prev_s * 100) if prev_s else None

    def _arrow(d):
        if d is None:
            return "→"
        return "▲" if d > 0.05 else ("▼" if d < -0.05 else "→")

    return {
        "contacts_delta": round(contacts_delta, 1) if contacts_delta is not None else None,
        "recontacts_delta": round(recontacts_delta, 1) if recontacts_delta is not None else None,
        "surveys_delta": round(surveys_delta, 1) if surveys_delta is not None else None,
        "evals_delta": round(evals_delta, 1) if evals_delta is not None else None,
        "contacts_arrow": _arrow(contacts_delta),
        "recontacts_arrow": _arrow(recontacts_delta),
        "surveys_arrow": _arrow(surveys_delta),
        "evals_arrow": _arrow(evals_delta),
    }


def root_cause_hypothesis(
    combined_row: pd.Series | None,
    top_attr: pd.DataFrame,
    voc: pd.DataFrame,
) -> str:
    if combined_row is None or (isinstance(combined_row, pd.Series) and combined_row.empty):
        top_a = top_attr.iloc[0]["Error_Category"] if not top_attr.empty else "top failing attributes"
        return (
            f"Elevated defect rates in '{top_a}' may be contributing to quality gaps, "
            "but no single contact reason Lv4 (detail) shows a fully confirmed multi-metric failure "
            "pattern in the current filter."
        )

    cr = combined_row["CR_Lv4"]
    bits = []
    if combined_row.get("low_qa") and not top_attr.empty:
        bits.append(f"low QA aligns with failing attributes such as '{top_attr.iloc[0]['Error_Category']}'")
    if combined_row.get("high_rc"):
        bits.append("high recontact suggests potential resolution or escalation gaps")
    if combined_row.get("low_csat") and not voc.empty:
        bits.append(f"low CSAT correlates with VOC theme '{voc.iloc[0]['Theme']}'")
    if bits:
        body = f"For '{cr}', " + "; ".join(bits) + "."
    else:
        body = f"For '{cr}', the metrics do not form a single confirmed failure pattern."
    return f"{body} This is an observable pattern only, not confirmed causality."


def generate_action_plan(
    combined: pd.DataFrame,
    ch_perf: pd.DataFrame,
    top_attr: pd.DataFrame,
    rc_cr: pd.DataFrame,
    summary: dict,
    rc_rate: float,
    channel: str = "All",
) -> list[ActionPlanItem]:
    items: list[ActionPlanItem] = []
    prefix = f"On {channel}: " if channel not in (None, "All", "") else ""

    ch_rows = ch_perf[ch_perf["Segment"] != "Overall"] if not ch_perf.empty else pd.DataFrame()
    multi_ch = len(ch_rows) > 1
    if multi_ch and not ch_rows.empty and summary["qa_score"] >= QA_GOAL:
        worst = ch_rows.loc[ch_rows["QA_Score"].idxmin()]
        if worst["QA_Score"] < QA_GOAL:
            items.append(ActionPlanItem(
                finding=(
                    f"{prefix}{worst['Segment']} QA at {worst['QA_Score']:.1f}% "
                    f"({worst['QA_Score_vs']:+.1f} points vs goal) while global QA meets the target — "
                    f"the overall average hides the gap."
                ),
                action=f"Channel-specific coaching on {worst['Segment']} checklist attributes; report QA by channel.",
                owner="QA Lead",
                priority="High",
                timeline="2 weeks",
            ))

    if not combined.empty:
        row = combined.iloc[0]
        items.append(ActionPlanItem(
            finding=(
                f"{prefix}{row['CR_Lv4']}: {row['Pattern']} — QA {row['QA_Score']:.1f}% "
                f"({row['QA_vs']:+.1f} pp), CSAT {row.get('CSAT_Score', float('nan')):.1f}% "
                f"({row.get('CSAT_vs', float('nan')):+.1f} pp), Recontact {row.get('Recontact_Rate', float('nan')):.2f}% "
                f"({row.get('RC_vs', float('nan')):+.2f} pp)."
            ),
            action="End-to-end review of resolution path, script adherence, and escalation handling for this contact reason Lv4 (detail).",
            owner="QA + Operations",
            priority="High",
            timeline="2 weeks",
        ))

    if rc_rate > RECONTACT_GOAL and not rc_cr.empty:
        top = rc_cr.iloc[0]
        items.append(ActionPlanItem(
            finding=f"{prefix}{top['CR_Lv4']} drives {top['Pct']:.1f}% of recontacts (rate {top['Recontact_Rate']:.2f}%).",
            action="Targeted calibration on first-contact resolution and case documentation for this contact reason Lv4 (detail).",
            owner="Supervisors",
            priority="High",
            timeline="2 weeks",
        ))

    if not ch_perf.empty:
        ch_rows = ch_perf[ch_perf["Segment"] != "Overall"]
        if multi_ch and not ch_rows.empty and summary["qa_score"] < QA_GOAL:
            worst = ch_rows.loc[ch_rows["QA_Score"].idxmin()]
            if worst["QA_Score"] < QA_GOAL:
                items.append(ActionPlanItem(
                    finding=f"{prefix}{worst['Segment']} QA at {worst['QA_Score']:.1f}% ({worst['QA_Score_vs']:+.1f} points vs goal) — weakest channel.",
                    action=f"Channel-specific coaching on {worst['Segment']} checklist attributes.",
                    owner="QA Lead",
                    priority="Medium",
                    timeline="3 weeks",
                ))

    if summary["csat"] < CSAT_GOAL:
        items.append(ActionPlanItem(
            finding=f"{prefix}CSAT at {summary['csat']:.1f}% is {summary['csat'] - CSAT_GOAL:.1f} pp below goal.",
            action="Review negative VOC themes and validate resolution/compensation flows.",
            owner="CX Operations",
            priority="High",
            timeline="2 weeks",
        ))

    if not top_attr.empty:
        t = top_attr.iloc[0]
        items.append(ActionPlanItem(
            finding=f"{prefix}'{t['Error_Category']}' accounts for {t['Pct_Of_Fails']:.1f}% of QA defects.",
            action=f"Include '{t['Error_Category']}' in next team calibration and monitoring.",
            owner="QA Analyst",
            priority="Medium",
            timeline="1 week",
        ))

    return items[:5]


def build_executive_brief(
    summary: dict,
    rc_rate: float,
    audits: pd.DataFrame,
    errors: pd.DataFrame,
    csat: pd.DataFrame,
    recontact: pd.DataFrame,
    combined: pd.DataFrame,
    ch_perf: pd.DataFrame,
    top_attr: pd.DataFrame,
    rc_cr: pd.DataFrame,
    voc: pd.DataFrame,
    action_items: list[ActionPlanItem],
    channel: str = "All",
) -> ExecutiveBrief:
    metrics = {
        "QA Score": abs(summary["qa_score"] - QA_GOAL),
        "CSAT Score": abs(summary["csat"] - CSAT_GOAL),
        "Recontact Rate": abs(rc_rate - RECONTACT_GOAL),
    }
    worst_metric = max(metrics, key=metrics.get)

    disp = qa_channel_dispersion(audits)
    worst_channel = disp["worst_channel"] if disp["worst_n"] else "—"

    worst_cr = "—"
    if not combined.empty:
        worst_cr = str(combined.iloc[0]["CR_Lv4"])
    elif not rc_cr.empty:
        worst_cr = str(rc_cr.iloc[0]["CR_Lv4"])

    top_defect = top_attr.iloc[0]["Error_Category"] if not top_attr.empty else "—"
    top_rc = rc_cr.iloc[0]["CR_Lv4"] if not rc_cr.empty else "—"
    top_voc = voc.iloc[0]["Theme"] if not voc.empty else "—"
    combined_cr = worst_cr

    rc_audited = float("nan")
    if not recontact.empty:
        scopes = recontact_by_scope(recontact)
        aud_row = scopes[scopes["Scope_Key"] == "audited"] if not scopes.empty else pd.DataFrame()
        if not aud_row.empty:
            rc_audited = aud_row.iloc[0]["Rate"]

    worst_attr = "—"
    if disp["worst_n"] and not errors.empty:
        worst_errs = errors[errors["Channel"] == disp["worst_channel"]] if "Channel" in errors.columns else errors
        worst_top = top_failing_attributes(worst_errs, audits[audits["Channel"] == disp["worst_channel"]], top_n=1)
        if not worst_top.empty:
            worst_attr = str(worst_top.iloc[0]["Error_Category"])

    slice_txt = f"On {channel}, " if channel not in (None, "All", "") else ""

    if disp["below"] > 0 and summary["qa_score"] >= QA_GOAL:
        insight = (
            f"{slice_txt}Global QA Score meets the goal at {summary['qa_score']:.1f}%, but "
            f"{disp['worst_channel']} is at {disp['worst_qa']:.1f}% on {disp['worst_n']:,} audits "
            f"({disp['worst_vs']:+.1f} points vs the {QA_GOAL:.0f}% goal). The overall average hides it "
            f"because the highest-volume channel accounts for {disp['largest_share']:.0f}% of the sample."
            + (f" Top failing attribute on that channel: {worst_attr}." if worst_attr != "—" else "")
        )
        action = (
            f"Open a focused coaching plan on {disp['worst_channel']} for '{worst_attr}', "
            f"and report QA by channel — not only the global average. The {disp['worst_channel']} "
            f"sample is small relative to the rest, so expand audit coverage before treating the gap as noise."
        )
    elif summary["qa_score"] < QA_GOAL:
        insight = (
            f"{slice_txt}QA Score is at {summary['qa_score']:.1f}% against a {QA_GOAL:.0f}% goal. "
            f"The weakest channel is {worst_channel} at {disp['worst_qa']:.1f}%. "
            f"Top defect driver: '{top_defect}'."
        )
        action = action_items[0].action if action_items else "Prioritize calibration on failing attributes."
    elif not combined.empty:
        row = combined.iloc[0]
        insight = (
            f"{slice_txt}{row['CR_Lv4']} represents a concentrated operational risk: "
            f"QA {row['QA_Score']:.1f}% ({row['QA_vs']:+.1f} points vs goal)"
        )
        if pd.notna(row.get("CSAT_Score")):
            insight += f", CSAT {row['CSAT_Score']:.1f}% ({row['CSAT_vs']:+.1f} points vs goal)"
        if pd.notna(row.get("Recontact_Rate")):
            insight += f", Recontact {row['Recontact_Rate']:.2f}% ({row['RC_vs']:+.2f} points vs goal)"
        insight += "."
        action = action_items[0].action if action_items else "End-to-end review of this contact reason Lv4 (detail)."
    elif rc_rate > RECONTACT_GOAL:
        if channel not in (None, "All", ""):
            insight = (
                f"On {channel}, recontact is {rc_rate:.2f}% vs the {RECONTACT_GOAL}% goal. "
                f"This is the channel rate, not the official 12-channel mix. Largest driver: {top_rc}."
            )
        else:
            audited_note = (
                f" Measured on the channels QA audits, the rate rises to {rc_audited:.2f}% "
                f"because self-service dilutes the denominator."
                if pd.notna(rc_audited) else ""
            )
            insight = (
                f"Recontact rate at {rc_rate:.2f}% exceeds the {RECONTACT_GOAL}% goal across all channels."
                f"{audited_note} Largest driver: {top_rc}."
            )
        action = action_items[0].action if action_items else "Focus FCR on top contact reason Lv4 (detail) names."
    elif summary["csat"] < CSAT_GOAL:
        insight = (
            f"{slice_txt}CSAT at {summary['csat']:.1f}% is below the {CSAT_GOAL}% target. "
            f"Top negative VOC theme: {top_voc}."
        )
        action = action_items[0].action if action_items else "Review negative VOC themes."
    else:
        insight = (
            f"{slice_txt}Primary gap: {worst_metric} furthest from target. "
            f"Top defect driver: '{top_defect}'."
        )
        action = action_items[0].action if action_items else "Maintain monitoring on top defect drivers."

    hypothesis = root_cause_hypothesis(
        combined.iloc[0] if not combined.empty else None,
        top_attr,
        voc,
    )

    return ExecutiveBrief(
        insight=insight,
        action=action,
        hypothesis=hypothesis,
        worst_metric=worst_metric,
        worst_channel=worst_channel,
        worst_cr=worst_cr,
        top_defect=top_defect,
        top_recontact_cr=top_rc,
        top_voc_theme=top_voc,
        combined_cr=combined_cr,
    )
