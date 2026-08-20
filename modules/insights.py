"""
Rule-based insights engine — generates actionable narrative from data patterns.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from config import MIN_SAMPLE_SIZE, QA_GOAL, QA_RED, RECONTACT_GOAL
from modules.kpis import avg_qa_score, fatal_error_rate, weekly_trends


@dataclass
class Insight:
    severity: str  # critical, warning, info
    category: str
    message: str
    metric_value: float | None = None


def generate_insights(
    audits: pd.DataFrame,
    errors: pd.DataFrame,
    agents: pd.DataFrame,
    supervisors: pd.DataFrame,
    pareto: pd.DataFrame,
    csat: pd.DataFrame,
) -> list[Insight]:
    insights: list[Insight] = []

    if audits.empty:
        return [Insight("info", "Data", "No audit data available for the selected filters.")]

    overall_qa = avg_qa_score(audits)
    overall_fatal = fatal_error_rate(audits)

    # Rule 1: Overall QA below critical threshold
    if overall_qa < QA_RED:
        insights.append(Insight(
            "critical", "QA Score",
            f"QA Score ({overall_qa:.1f}%) is below critical threshold ({QA_RED}%). "
            f"Immediate calibration and coaching intervention required.",
            overall_qa,
        ))
    elif overall_qa < QA_GOAL:
        insights.append(Insight(
            "warning", "QA Score",
            f"QA Score ({overall_qa:.1f}%) is below goal ({QA_GOAL}%). "
            f"Review top failing attributes and schedule targeted coaching.",
            overall_qa,
        ))

    # Rule 2: Sustained negative trend (2+ weeks declining)
    trends = weekly_trends(audits)
    if len(trends) >= 3:
        last3 = trends["QA_Score"].tail(3).values
        if last3[2] < last3[1] < last3[0]:
            drop = last3[0] - last3[2]
            insights.append(Insight(
                "warning", "Trend",
                f"QA Score has declined for 3 consecutive weeks (−{drop:.1f} pts). "
                f"Investigate process changes or staffing shifts in recent weeks.",
                drop,
            ))

    # Rule 3: Supervisor outlier — fatal rate 15%+ above average
    if not supervisors.empty and len(supervisors) > 1:
        avg_sup_fatal = supervisors["Fatal_Rate"].mean()
        for _, sup in supervisors.iterrows():
            if sup["Fatal_Rate"] > avg_sup_fatal * 1.15 and sup["Audit_Count"] >= 10:
                top_err = _top_error_for_supervisor(errors, sup["Supervisor_ID"])
                insights.append(Insight(
                    "warning", "Supervisor",
                    f"Team of {sup['Supervisor_ID']} has Fatal Rate {sup['Fatal_Rate']:.1f}% "
                    f"({sup['Fatal_Rate'] - avg_sup_fatal:.1f}pp above average), "
                    f"driven by errors in '{top_err}'. "
                    f"Recommend supervisor-led calibration session.",
                    sup["Fatal_Rate"],
                ))

    # Rule 4: Agents with insufficient sample flagged
    unreliable = agents[~agents["Reliable"]]
    if len(unreliable) > 0:
        insights.append(Insight(
            "info", "Sample Size",
            f"{len(unreliable)} agents have fewer than {MIN_SAMPLE_SIZE} audits — "
            f"their scores are marked as unreliable and excluded from coaching prioritization.",
            len(unreliable),
        ))

    # Rule 5: Top Pareto error with high impact
    if not pareto.empty:
        top = pareto.iloc[0]
        insights.append(Insight(
            "critical" if top["Is_Critical"] else "warning",
            "Error Driver",
            f"Highest-impact error: '{top['Error_Category']}' "
            f"({top['Fail_Count']} occurrences, impact score {top['Impact_Score']:.0f}). "
            f"CSAT impact factor: {top['CSAT_Impact_Factor']}×, "
            f"FCR impact factor: {top['FCR_Impact_Factor']}×.",
            top["Impact_Score"],
        ))

    # Rule 6: CSAT divergence from QA
    if not csat.empty:
        csat_val = csat["Satisfied_CNT"].sum() / csat["Feedback CNT"].sum() * 100
        if overall_qa >= QA_GOAL and csat_val < 85:
            gap = overall_qa - csat_val
            insights.append(Insight(
                "warning", "CSAT Divergence",
                f"QA Score meets goal ({overall_qa:.1f}%) but CSAT is {csat_val:.1f}% — "
                f"a {gap:.1f}pt gap suggests audits may not capture customer-perceived quality. "
                f"Review VOC comments and recalibrate audit criteria.",
                gap,
            ))

    # Rule 7: Auditor calibration divergence
    if "Auditor_ID" in audits.columns:
        cal = audits.groupby("Auditor_ID").agg(
            Avg_Score=("Score_Pct", "mean"),
            Count=("Audit_ID", "count"),
        ).reset_index()
        cal = cal[cal["Count"] >= 20]
        if len(cal) >= 2:
            spread = cal["Avg_Score"].max() - cal["Avg_Score"].min()
            if spread > 10:
                high = cal.loc[cal["Avg_Score"].idxmax(), "Auditor_ID"]
                low = cal.loc[cal["Avg_Score"].idxmin(), "Auditor_ID"]
                insights.append(Insight(
                    "warning", "Calibration",
                    f"Auditor score spread is {spread:.1f} pts "
                    f"({high}: {cal['Avg_Score'].max():.1f} vs {low}: {cal['Avg_Score'].min():.1f}). "
                    f"Schedule calibration session between audit teams.",
                    spread,
                ))

    # Rule 8: Recontact hotspots
    from modules.kpis import overall_fcr
    # handled at CR level in app

    return sorted(insights, key=lambda x: {"critical": 0, "warning": 1, "info": 2}[x.severity])


def _top_error_for_supervisor(errors: pd.DataFrame, supervisor_id: str) -> str:
    if errors.empty:
        return "N/A"
    subset = errors[errors["Supervisor_ID"] == supervisor_id]
    if subset.empty:
        return "N/A"
    return subset["Error_Category"].value_counts().index[0]
