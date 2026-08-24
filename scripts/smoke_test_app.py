"""
End-to-end app smoke test — runs app.py through Streamlit's test harness.

Visits Overview, QA Score, CSAT, Recontact and Alerts. Complements
`scripts/smoke_test_deploy.py`, which only covers the data layer.

Usage:
    python scripts/smoke_test_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import CONTROL_TOTALS  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

PAGES = {
    "Overview": (
        "QA Score",
        "CSAT Score",
        "Recontact Rate",
        "Total Contacts",
        "Combined Analysis",
        "Within 5 points",
        "What to do next",
        "Supervisor QA impact Pareto",
        "Supervisors: QA vs CSAT",
        "QA, CSAT and recontact by channel",
        "QA and AHT by contact reason Lv1",
        "QA and AHT by contact reason Lv4",
        "QA and AHT by contact reason SUB_CR",
        "Supervisor CSAT impact Pareto",
        "Contact reason classification coverage",
        "Top contact reasons (SUB_CR)",
        "How the data is sliced",
        "QA Agent_ID",
        "Contact reason Lv1",
        "Contact reason Lv4",
        "Contact reason SUB_CR",
        "Contact number by channel",
        "4–5 star surveys",
        "1–3 star surveys",
        "Performance trends",
        "QA score by day",
        "Week by week",
        "Lower-volume contact reasons",
        "Critical fails",
        "Non-critical fails",
        "AHT",
        "Auditor resolution rate",
        "Unresolved — process followed",
        "Abandoned interaction rate",
    ),
    "QA Score": (
        "QA overview",
        "QA score by channel",
        "Audit volume by channel",
        "Audits summary",
        "Performance trends",
        "Detail by category",
        "CRITICAL",
        "CRITICAL fails by attribute",
        "QA fails by attribute",
        "Score_end_user",
        "Audits with critical fail",
        "Audits with non-critical fails",
        "Auditor resolution rate",
        "Unresolved — process followed",
        "Audits with fails (critical and non-critical)",
        "Non-critical",
        "Phone",
        "Live Chat",
        "Special project",
        "Type of audit",
        "Handle time vs quality",
        "QA fail Pareto by contact reason Lv4",
        "contact reason Lv1",
        "QA by agent tenure",
        "SUB_CR",
        "Interaction outcome (auditor notes)",
        "Solution and process",
        "Auditor-tagged dissatisfaction",
        "Same-CR contacts in last 48h",
        "did not follow process",
    ),
    "CSAT": (
        "CSAT overview",
        "Customer comments",
        "Positive vs negative",
        "Themes in 1–3 star comments",
        "open_question",
        "CSAT by day",
        "CSAT score histogram",
        "star comments",
        "surveys with comments",
        "CSAT by contact reason Lv4",
        "SUB_CR",
        "CSAT by agent tenure",
        "Business Type",
        "4–5 star surveys",
        "1–3 star surveys",
    ),
    "Recontact": (
        "Recontact overview",
        "Repeated contacts and rate by contact reason Lv4",
        "Repeated contacts and rate by contact reason SUB_CR",
        "Official mix vs Phone + Chat",
        "Self Help",
        "Repeat volume by channel",
        "Recontact by contact reason Lv1",
        "Recontact vs handle time",
        "FCR",
        "Recontact number",
        "Contacts, repeats, and rate by channel",
        "12-channel mix",
        "Do not average",
        "No business-case target",
    ),
    "Alerts": (
        "Performance Hub",
        "Equal-count split",
        "Top 25%",
        "Supervisor talent mix",
        "Q4-heavy teams only",
        "Coaching queue",
        "Focus coaching",
        "Ticket tracker",
        "Active alerts",
    ),
}

LEAK_TOKENS = (
    '<div class="kpi-card">',
    '<div class="kpi-card',
    '&lt;div class="kpi',
    'class="kpi-card"',
    "kpi-card",
)

SPANISH_ATTR_LEAK = (
    "Manejo Del Tiempo",
    "Saludo E Identificacion",
    "Informacion Completa Y Correcta",
    "Actitud De Servicio",
    "Rudeza Con El Usuario",
)


def _annotation_text(fig) -> str:
    anns = fig.layout.annotations or []
    return " ".join(str(a.text or "") for a in anns)


def _assert_gap_n_split() -> str | None:
    """Gap Paretos must not label sum(gap × volume) as audits/surveys."""
    from modules.dashboard_charts import cr_group_hbar, pareto_dual_axis

    qa = pd.DataFrame({
        "Cat": ["A", "B"],
        "Gap_Impact": [200.0, 151.0],
        "n": [40, 57],
    })
    fig = pareto_dual_axis(
        qa, "Cat", "Gap_Impact",
        title="Supervisor QA gap",
        value_title="Weighted deficit (gap × audits)",
        sample_unit="audits",
    )
    blob = _annotation_text(fig)
    if "N = 351 audits" in blob and "weighted deficit" not in blob.lower():
        return f"QA gap Pareto labeled sum(Gap_Impact) as audits: {blob!r}"
    if "N = 97 audits" not in blob:
        return f"QA gap Pareto missing real audit N: {blob!r}"
    if "weighted deficit 351" not in blob:
        return f"QA gap Pareto missing weighted-deficit note: {blob!r}"

    csat = pd.DataFrame({
        "Cat": ["A", "B"],
        "Gap_Impact": [100.0, 50.0],
        "Feedback": [10, 20],
    })
    fig2 = pareto_dual_axis(
        csat, "Cat", "Gap_Impact",
        title="Supervisor CSAT gap",
        value_title="Weighted deficit (gap × surveys)",
        sample_unit="surveys",
    )
    blob2 = _annotation_text(fig2)
    if "N = 150 surveys" in blob2 and "weighted deficit" not in blob2.lower():
        return f"CSAT gap Pareto labeled sum(Gap_Impact) as surveys: {blob2!r}"
    if "N = 30 surveys" not in blob2:
        return f"CSAT gap Pareto missing real survey N: {blob2!r}"
    if "weighted deficit 150" not in blob2:
        return f"CSAT gap Pareto missing weighted-deficit note: {blob2!r}"

    combo = pd.DataFrame({
        "CR_Lv4": ["user request order status or delay information", "other"],
        "Recontacts": [100, 50],
        "Contacts": [1000, 2000],
        "Recontact_Rate": [10.0, 2.5],
    })
    from modules.dashboard_charts import recontact_cr_combo_chart
    fig_combo = recontact_cr_combo_chart(combo)
    blob_c = _annotation_text(fig_combo)
    if "N = 150 repeats" not in blob_c:
        return f"CR combo missing repeat N: {blob_c!r}"
    if "3,000 contacts in view" not in blob_c:
        return f"CR combo missing contacts in view: {blob_c!r}"
    names = {t.name for t in fig_combo.data}
    if "Repeats" not in names or "Rate %" not in names:
        return f"CR combo missing bar/line traces: {names}"

    fig3 = cr_group_hbar(
        qa.rename(columns={"Cat": "CR_Lv1"}),
        "CR_Lv1", "Gap_Impact", None,
        "Weighted deficit (gap × audits)",
        title="Supervisor QA gap",
    )
    blob3 = _annotation_text(fig3)
    if "N = 351 audits" in blob3 and "weighted deficit" not in blob3.lower():
        return f"Gap hbar labeled sum(Gap_Impact) as audits: {blob3!r}"
    if "N = 97 audits" not in blob3:
        return f"Gap hbar missing real audit N: {blob3!r}"

    fails = pd.DataFrame({"Cat": ["X", "Y"], "Count": [8, 2]})
    fig4 = pareto_dual_axis(fails, "Cat", "Count", title="QA fails by attribute")
    blob4 = _annotation_text(fig4)
    if "weighted deficit" in blob4.lower():
        return f"Fail Pareto incorrectly treated as weighted gap: {blob4!r}"
    if "N = 10 fails" not in blob4:
        return f"Fail Pareto should keep fail counts as N: {blob4!r}"

    long_tail = pd.DataFrame({
        "Cat": [f"R{i}" for i in range(1, 13)],
        "Count": list(range(12, 0, -1)),
    })
    fig_tail = pareto_dual_axis(long_tail, "Cat", "Count", title="CSAT unsatisfied Pareto", bucket_other=True)
    blob_tail = _annotation_text(fig_tail)
    ticks = " ".join(str(t).replace("<br>", " ") for t in (fig_tail.layout.xaxis.ticktext or []))
    if "Remaining reasons (5 more)" not in ticks:
        return f"Pareto tail should be leftover after 80%, not a fixed top 10: {ticks!r}"
    if "7 named bars reach 80%" not in blob_tail:
        return f"Pareto N note should say named bars reach 80%: {blob_tail!r}"

    zeros = pd.DataFrame({"Cat": ["Agent 26", "Agent 94"], "Count": [1, 0]})
    figz = pareto_dual_axis(zeros, "Cat", "Count", title="QA fails by agent")
    blobz = _annotation_text(figz)
    if "Agent 94" in " ".join(str(t) for t in (figz.layout.xaxis.ticktext or [])):
        return "Zero-fail agent should not appear on a fail Pareto"
    if "N = 1 fails" not in blobz:
        return f"Zero-fail rows should drop from N: {blobz!r}"

    crowded = pd.DataFrame({
        "Cat": [f"Supervisor {i}" for i in range(1, 11)],
        "Count": list(range(10, 0, -1)),
    })
    fig_c = pareto_dual_axis(crowded, "Cat", "Count", title="QA fails by supervisor")
    angle = fig_c.layout.xaxis.tickangle
    try:
        angle_v = float(angle)
    except (TypeError, ValueError):
        angle_v = 0.0
    if abs(angle_v) < 40:
        return f"Short many-bar Pareto labels should rotate, tickangle={angle!r}"
    n_ann = next(
        (a for a in (fig_c.layout.annotations or []) if getattr(a, "name", None) == "didi_n"),
        None,
    )
    if n_ann is None:
        return "Pareto missing didi_n annotation"
    if str(getattr(n_ann, "xanchor", "")) != "center":
        return f"N should be centered above the legend, xanchor={n_ann.xanchor!r}"

    return None


def _blob(at: AppTest) -> str:
    chunks: list[str] = []
    for name in (
        "markdown", "caption", "title", "header", "subheader", "text",
        "info", "warning", "success", "error",
    ):
        try:
            for el in getattr(at, name):
                chunks.append(str(getattr(el, "value", "") or ""))
        except Exception:
            pass
    try:
        for el in at.metric:
            chunks.append(el.label or "")
            chunks.append(el.value or "")
            chunks.append(el.delta or "")
            chunks.append(getattr(el, "help", "") or "")
    except Exception:
        pass
    try:
        for el in at.dataframe:
            df = el.value
            chunks.append(" ".join(map(str, df.columns)))
            chunks.append(df.astype(str).to_string())
    except Exception:
        pass
    try:
        for el in at.expander:
            chunks.append(str(getattr(el, "label", "") or ""))
    except Exception:
        pass
    try:
        for el in at.button:
            chunks.append(str(getattr(el, "label", "") or ""))
    except Exception:
        pass
    try:
        for el in at.download_button:
            chunks.append(str(getattr(el, "label", "") or ""))
    except Exception:
        pass
    try:
        for el in at.checkbox:
            chunks.append(str(getattr(el, "label", "") or ""))
    except Exception:
        pass
    try:
        for el in getattr(at, "toggle", []):
            chunks.append(str(getattr(el, "label", "") or ""))
    except Exception:
        pass
    try:
        for el in at.sidebar.checkbox:
            chunks.append(str(getattr(el, "label", "") or ""))
    except Exception:
        pass
    return "\n".join(chunks)


def _markdown_blob(at: AppTest) -> str:
    return "\n".join(m.value for m in at.markdown)


def _fail_exceptions(at: AppTest, where: str) -> str | None:
    if at.exception:
        lines = [f"EXCEPTIONS on {where}:"]
        for exc in at.exception:
            lines.append(f"  {exc.type}: {exc.message}")
            if exc.stack_trace:
                lines.append("    " + "\n    ".join(exc.stack_trace))
        return "\n".join(lines)
    if at.error:
        return f"st.error on {where}: " + "; ".join(str(e.value) for e in at.error)
    return None


def _assert_no_html_leak(at: AppTest, where: str) -> str | None:
    md = _markdown_blob(at)
    blob = _blob(at)
    for token in LEAK_TOKENS:
        if token in md or token in blob:
            return f"HTML leak on {where}: found {token!r}"
    return None


def _set_page(at: AppTest, name: str) -> None:
    radios = list(at.sidebar.radio) + list(at.radio)
    if not radios:
        raise RuntimeError("No radio widget found for page navigation")
    radios[0].set_value(name)
    at.run()


def _set_country(at: AppTest, value: str) -> None:
    boxes = list(at.sidebar.selectbox)
    country = next((b for b in boxes if "Market" in str(getattr(b, "label", ""))), None)
    if country is None:
        raise RuntimeError("Market / Country selectbox not found")
    country.set_value(value)
    at.run()


def _set_channel(at: AppTest, value: str) -> None:
    boxes = list(at.sidebar.selectbox)
    channel = next((b for b in boxes if str(getattr(b, "label", "")) == "Channel"), None)
    if channel is None:
        raise RuntimeError("Channel selectbox not found")
    channel.set_value(value)
    at.run()


def _assert_population_n() -> str | None:
    """Fail concentrators, supervisor N, and Agent-26 slice must agree with packaged facts."""
    from modules.dashboard_charts import hbar_score_chart, pareto_dual_axis
    from modules.data_loader import load_all_data
    from modules.kpis import (
        channel_match,
        cr_finest_volume,
        csat_agent_roster,
        csat_agent_unsat_concentrators,
        csat_unsat_totals,
        csat_unsatisfied_by_cr,
        fail_event_totals,
        filter_csat_by_agent,
        filter_csat_by_supervisor,
        kpi_summary,
        overall_csat,
        qa_agent_fail_concentrators,
        qa_agent_roster,
        recontact_rate,
        top_failing_attributes,
    )

    data = load_all_data()
    audits, errors, csat, rc = (
        data["fact_audits"], data["fact_errors"], data["fact_csat"], data["fact_recontact"],
    )
    summary = kpi_summary(audits, csat, rc)
    if round(float(summary["qa_score"]), 2) != CONTROL_TOTALS["qa"]:
        return f"QA drifted: {summary['qa_score']}"
    if round(float(summary["csat"]), 2) != CONTROL_TOTALS["csat"]:
        return f"CSAT drifted: {summary['csat']}"
    if round(float(recontact_rate(rc)), 2) != CONTROL_TOTALS["recontact"]:
        return f"Recontact drifted: {recontact_rate(rc)}"
    if len(audits) != CONTROL_TOTALS["evaluations"]:
        return f"Audit N drifted: {len(audits)}"
    if "Auditor_Outcome" not in audits.columns or "Dissatisfaction_Flag" not in audits.columns:
        return "fact_audits missing auditor-note columns"
    n_bad = int((audits["Process_Adherence"].astype(str) == "Did not follow process").sum())
    if n_bad != 418:
        return f"Process_Adherence did-not-follow drifted: {n_bad}"
    n_yes = int((audits["Dissatisfaction_Flag"].astype(str) == "Yes").sum())
    if n_yes != 109:
        return f"Dissatisfaction Yes drifted: {n_yes}"
    n_rep = int((audits["Repeat_48h"].astype(str) == "Repeat (≥2)").sum())
    if n_rep != 36:
        return f"Repeat 48h drifted: {n_rep}"

    g = (
        audits.groupby("Supervisor_ID", as_index=False)
        .agg(QA_Score=("Score_Pct", "mean"), n=("Audit_ID", "count"))
    )
    g5 = g[g["n"] >= 5].sort_values("QA_Score")
    head15 = int(g5.head(15)["n"].sum())
    if head15 != 1125:
        return f"Expected old 15-bar N to be 1125, got {head15}"
    fig = hbar_score_chart(g5, "Supervisor_ID", "QA_Score", "n", title="QA by supervisor", universe_n=len(audits))
    blob = _annotation_text(fig)
    if "N = 1,125" in blob:
        return f"QA by supervisor still truncated to 15 bars: {blob!r}"
    if "N = 2,456 audits in view" not in blob:
        return f"QA by supervisor should show n≥5 audits in view: {blob!r}"
    if "2,460 in filter" not in blob:
        return f"QA by supervisor missing full filter N: {blob!r}"

    aa = audits[
        (audits["Country"] == "CO")
        & (audits["Supervisor_ID"] == "Supervisor 13")
        & channel_match(audits["Channel"], "Live Chat")
    ]
    ee = errors[errors["Audit_ID"].isin(aa["Audit_ID"])]
    n_ev, n_au = fail_event_totals(ee)
    if (n_ev, n_au) != (7, 6):
        return f"CO×S13×Chat fail totals {n_ev},{n_au} expected 7,6"
    attrs = top_failing_attributes(ee, aa, top_n=12)
    conc = qa_agent_fail_concentrators(ee, aa)
    if int(attrs["Fail_Count"].sum()) != 7:
        return f"Attribute Pareto N {int(attrs['Fail_Count'].sum())}"
    if conc.empty or int(conc["Fail_Count"].sum()) != 7:
        return f"Agent concentrator N {0 if conc.empty else int(conc['Fail_Count'].sum())}"
    names = set(conc["Agent_ID"].astype(str))
    if "Agent 94" in names:
        return "Agent 94 with 0 fails appeared on the concentrator"
    if names != {"Agent 156", "Agent 26", "Agent 137", "Agent 195", "Agent 205", "Agent 206"}:
        return f"Unexpected failing agents: {sorted(names)}"
    roster = qa_agent_roster(aa, ee)
    if roster.empty or "Agent 94" not in set(roster["Agent_ID"].astype(str)):
        return "n≥5 roster should still list Agent 94 for scores"

    a26 = aa[aa["Agent_ID"].astype(str) == "Agent 26"]
    e26 = ee[ee["Audit_ID"].isin(a26["Audit_ID"])]
    n26, u26 = fail_event_totals(e26)
    if (n26, u26) != (1, 1):
        return f"Agent 26 slice should be 1 fail / 1 audit, got {n26},{u26}"
    conc26 = qa_agent_fail_concentrators(e26, a26)
    if list(conc26["Agent_ID"].astype(str)) != ["Agent 26"] or int(conc26["Fail_Count"].iloc[0]) != 1:
        return f"Agent 26 concentrator: {conc26}"

    cc = csat[csat["Country Code"] == "CO"] if "Country Code" in csat.columns else csat
    cc = cc[channel_match(cc["Channel"], "Live Chat")] if "Channel" in cc.columns else cc
    cc = filter_csat_by_supervisor(cc, audits, "Supervisor 13")
    u_all = csat_unsat_totals(cc)
    u_cr = int(csat_unsatisfied_by_cr(cc)["Unsatisfied"].sum()) if not csat_unsatisfied_by_cr(cc).empty else 0
    u_ag = csat_agent_unsat_concentrators(cc, aa)
    if u_all != u_cr:
        return f"CSAT CR unsat {u_cr} != universe {u_all}"
    if u_ag.empty or int(u_ag["Unsatisfied"].sum()) != u_all:
        return f"CSAT agent concentrator {0 if u_ag.empty else int(u_ag['Unsatisfied'].sum())} != {u_all}"
    ros = csat_agent_roster(cc, aa)
    if not ros.empty and int(ros["Unsatisfied"].sum()) > u_all:
        return "CSAT roster unsat exceeds the filter universe"
    if not u_ag.empty and int(u_ag["Unsatisfied"].sum()) != u_all:
        return f"CSAT agent concentrator {int(u_ag['Unsatisfied'].sum())} != {u_all}"
    filter_csat_by_agent(cc, "Agent 26")

    country_col = "Country Code" if "Country Code" in csat.columns else "Country"
    co = csat[csat[country_col].astype(str).str.strip() == "CO"].copy()
    n_co = int(pd.to_numeric(co["Feedback CNT"], errors="coerce").fillna(0).sum())
    if n_co != 24122:
        return f"Colombia official CSAT N drifted: {n_co} (expected 24,122)"
    if round(float(overall_csat(co)), 2) != 79.89:
        return f"Colombia official CSAT % drifted: {overall_csat(co)}"
    top12 = cr_finest_volume(co, top_n=12)
    if int(top12["Feedback"].sum()) != 15353:
        return f"Colombia SUB_CR top-12 volume drifted: {int(top12['Feedback'].sum())}"
    finest = cr_finest_volume(co, top_n=None)
    if int(finest["Feedback"].sum()) != n_co:
        return (
            f"SUB_CR finest-grain volume {int(finest['Feedback'].sum())} "
            f"!= Colombia CSAT {n_co}"
        )
    fig_cr = pareto_dual_axis(
        finest, "Cat", "Feedback",
        title="Top contact reasons (SUB_CR)",
        value_title="Surveys",
        sample_unit="surveys",
        universe_n=n_co,
        n_note=f"{int(finest['Feedback'].head(10).sum()):,} in the 10 largest reasons",
    )
    blob_cr = _annotation_text(fig_cr)
    if "N = 15,353" in blob_cr:
        return f"SUB_CR Pareto still labels top-12 volume as N: {blob_cr!r}"
    if "N = 24,122 surveys" not in blob_cr:
        return f"SUB_CR Pareto should use official Colombia CSAT N: {blob_cr!r}"
    return None


def _assert_see_all_and_scatter() -> str | None:
    """See-all drops reliability floors; trendline + stats stay on the scatter."""
    from modules.dashboard_charts import qa_csat_scatter
    from modules.kpis import (
        csat_score_by_cr,
        qa_score_by_cr,
    )
    from modules.data_loader import load_all_data

    data = load_all_data()
    audits, csat = data["fact_audits"], data["fact_csat"]
    reliable = csat_score_by_cr(csat, level="lv4", min_n=20, top_n=12)
    all_rows = csat_score_by_cr(csat, level="lv4", min_n=1, top_n=None)
    if all_rows.empty:
        return "See-all CSAT by CR Lv4 returned no rows"
    if len(all_rows) <= len(reliable):
        return (
            f"See-all CSAT by CR should include small samples "
            f"(got {len(all_rows)} vs reliable {len(reliable)})"
        )
    if int(all_rows["Feedback"].min()) < 1:
        return "See-all CSAT rows must still label n ≥ 1"
    qa_all = qa_score_by_cr(audits, top_n=None, min_n=1)
    qa_rel = qa_score_by_cr(audits, top_n=12, min_n=3)
    if len(qa_all) <= len(qa_rel):
        return f"See-all QA by CR should include small samples ({len(qa_all)} vs {len(qa_rel)})"

    fig = qa_csat_scatter(pd.DataFrame({
        "QA_Score": [80.0, 90.0, 95.0],
        "CSAT_Pct": [70.0, 82.0, 88.0],
        "CR_Lv4": ["A", "B", "C"],
        "Feedback": [30, 40, 50],
    }))
    dashes = [
        t for t in fig.data
        if getattr(t, "name", "") == "Trend"
        and str(getattr(getattr(t, "line", None), "dash", "") or "") == "dash"
    ]
    if not dashes:
        return "QA vs CSAT scatter is missing the dashed OLS trendline"
    return None


def main() -> int:
    gap_err = _assert_gap_n_split()
    if gap_err:
        print(gap_err)
        return 1
    print("Gap Pareto N split: real volume + weighted deficit (not gap×n as audits).")
    pop_err = _assert_population_n()
    if pop_err:
        print(pop_err)
        return 1
    print("Fail concentrators, supervisor N, and Agent 26 slice match packaged facts.")
    slice_err = _assert_see_all_and_scatter()
    if slice_err:
        print(slice_err)
        return 1
    print("CSAT/QA by-CR frames expand past min-n/top-n; scatter trend is present.")

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180)
    at.run()

    err = _fail_exceptions(at, "initial Overview")
    if err:
        print(err)
        return 1

    print("App executed with no exceptions.")
    print(f"  markdown blocks : {len(at.markdown)}")
    print(f"  metric cards    : {len(at.metric)}")
    print(f"  sidebar widgets : {len(at.sidebar.selectbox) + len(at.sidebar.multiselect)}")

    metrics = {str(m.label): str(m.value) for m in at.metric}
    expected_metrics = {
        "QA Score": f"{CONTROL_TOTALS['qa']:.2f}%",
        "CSAT Score": f"{CONTROL_TOTALS['csat']:.2f}%",
        "Recontact Rate": f"{CONTROL_TOTALS['recontact']:.2f}%",
        "Total Surveys": f"{CONTROL_TOTALS['surveys']:,}",
        "Total Contacts": f"{CONTROL_TOTALS['contacts']:,}",
        "QA Evaluations": f"{CONTROL_TOTALS['evaluations']:,}",
    }
    for label, expected in expected_metrics.items():
        got = metrics.get(label)
        if got != expected:
            print(f"Official {label} drifted on default filters: {got!r} (expected {expected})")
            return 1
    print(
        "  control totals  : "
        f"QA {CONTROL_TOTALS['qa']:.2f} · CSAT {CONTROL_TOTALS['csat']:.2f} · "
        f"Recontact {CONTROL_TOTALS['recontact']:.2f} · "
        f"surveys {CONTROL_TOTALS['surveys']:,} · contacts {CONTROL_TOTALS['contacts']:,} · "
        f"evals {CONTROL_TOTALS['evaluations']:,}"
    )

    for page_name, tokens in PAGES.items():
        if page_name != "Overview":
            _set_page(at, page_name)
            err = _fail_exceptions(at, page_name)
            if err:
                print(err)
                return 1
        leak = _assert_no_html_leak(at, page_name)
        if leak:
            print(leak)
            return 1
        blob = _blob(at)
        print(f"\n[{page_name}]")
        for token in tokens:
            status = "found" if token in blob else "MISSING"
            print(f"  '{token}' -> {status}")
            if status == "MISSING":
                return 1
        print("  HTML leak check -> clean")
        if page_name == "QA Score":
            for token in SPANISH_ATTR_LEAK:
                if token in blob:
                    print(f"  Spanish attribute leak: {token!r}")
                    return 1
            print("  Spanish attribute leak check -> clean")

    _set_page(at, "Overview")
    _set_country(at, "MX")
    err = _fail_exceptions(at, "Overview Market=MX")
    if err:
        print(err)
        return 1
    print("\n[Overview Market=MX] no exception")

    _set_page(at, "Overview")
    _set_channel(at, "Phone")
    err = _fail_exceptions(at, "Overview Channel=Phone")
    if err:
        print(err)
        return 1
    blob = _blob(at)
    if "Channel = Phone" not in blob:
        print("MISSING Channel = Phone banner on Overview Channel=Phone")
        return 1
    old_empty = "Need at least 5 contact reason Lv4 (detail) values present in QA, CSAT, and recontact."
    if old_empty in blob:
        print("Old terse correlation empty-state leaked on Channel=Phone")
        return 1
    rc_weekly_ok = False
    for el in at.dataframe:
        df = el.value
        cols = [str(c) for c in df.columns]
        if "RC" in cols:
            series = pd.to_numeric(df["RC"].astype(str).str.replace("%", "", regex=False), errors="coerce")
            if series.notna().any() and float(series.max()) > 8:
                rc_weekly_ok = True
                break
    if not rc_weekly_ok:
        print("Week-over-week table has no visible Phone recontact values (> 8%)")
        return 1
    print("\n[Overview Channel=Phone] recontact weekly values present, correlation copy detailed")

    print("\nAPP SMOKE TEST PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
