"""Dump every figure Deliverable 2 needs, straight from the dashboard pipeline."""

from __future__ import annotations

import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from modules.data_loader import load_all_data
from modules import kpis as K
from modules import executive_engine as EE

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_rows", 60)


def show(title, obj):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)
    if isinstance(obj, pd.DataFrame):
        print(obj.to_string(index=False))
    else:
        print(obj)


data = load_all_data()
a, e, c, r = (data["fact_audits"], data["fact_errors"],
              data["fact_csat"], data["fact_recontact"])

show("GOALS", {"QA": config.QA_GOAL, "CSAT": config.CSAT_GOAL,
               "RECONTACT": config.RECONTACT_GOAL})

show("DATE SPAN", {
    "audits": (str(a["Fecha"].min()), str(a["Fecha"].max())),
    "csat": (str(c["Fecha"].min()), str(c["Fecha"].max())),
    "recontact": (str(r["Fecha"].min()), str(r["Fecha"].max())),
    "weeks_audits": sorted(a["Week"].dropna().unique().tolist()),
})

summary = K.kpi_summary(a, c, r)
show("KPI SUMMARY", summary)
show("RECONTACT RATE", K.recontact_rate(r))
show("VOLUMES", K.volume_totals(a, c, r))
show("CRITICAL FAIL STATS", K.critical_fail_stats(a, e))
show("CSAT UNSAT TOTAL", K.csat_unsat_totals(c))
show("FAIL EVENT TOTALS (events, audits)", K.fail_event_totals(e))

show("DIMENSIONS PRESENT", {
    "LOB": a["LOB"].value_counts().to_dict(),
    "Channel(audits)": a["Channel"].value_counts().to_dict(),
    "Business_Type(csat)": c["Business_Type"].value_counts().head(15).to_dict(),
    "Country(audits)": a["Country"].value_counts().to_dict(),
    "Requester": a["Requester"].value_counts().head(10).to_dict(),
})

show("CHANNEL PERFORMANCE", K.channel_performance(a, c, r))

ch_break = EE.qa_channel_breakdown(a, e)
for name, blob in ch_break.items():
    show(f"QA CHANNEL BREAKDOWN :: {name}", blob)

show("TOP FAILING ATTRIBUTES (ALL)", K.top_failing_attributes(e, a, top_n=12))
for chan in ("Phone", "Live Chat"):
    ce = e[K.channel_match(e["Channel"], chan)]
    ca = a[K.channel_match(a["Channel"], chan)]
    show(f"TOP FAILING ATTRIBUTES :: {chan} (n_audits={len(ca)}, n_fails={len(ce)})",
         K.top_failing_attributes(ce, ca, top_n=10))
    show(f"QA BY CR LV4 :: {chan}", K.qa_score_by_cr(ca, top_n=12, min_n=3))

show("QA BY CR LV4 (ALL, ranked)", K.qa_score_by_cr(a, top_n=20, min_n=3))
show("QA FAILS BY CR LV4", K.qa_fails_by_cr(e, top_n=15))
show("PARETO ERRORS SIMPLE", K.pareto_errors_simple(e))
show("QA HISTOGRAM", K.qa_score_histogram(a))
show("QA BY TENURE", K.qa_by_tenure(a))

show("CSAT STARS", K.csat_by_star_rating(c))
show("CSAT BY BUSINESS TYPE", K.csat_by_business_type(c))
show("CSAT BY CR LV4", K.csat_score_by_cr(c, min_n=50, top_n=15))
show("CSAT UNSATISFIED BY CR", K.csat_unsatisfied_by_cr(c).head(15))
show("VOC THEMES NEGATIVE", K.voc_themes_negative(c, top_n=8))
voc_all = K.voc_all_comments(c, top_n=8)
show("VOC ALL COMMENTS", {k: (v if not isinstance(v, pd.DataFrame) else v.to_dict("records"))
                          for k, v in voc_all.items()})

show("RECONTACT BY CR LV4", K.recontact_by_cr(r, top_n=15, csat=c))
show("RECONTACT BY SCOPE", K.recontact_by_scope(r))
show("RECONTACT CHANNEL TABLE", K.recontact_channel_table(r))
show("RECONTACT DILUTION", K.recontact_dilution_stats(r))

scatter = K.cr_level_metrics(a, c, r)
show("CR LEVEL METRICS (head 25)", scatter.head(25))
show("CR CORRELATION SUMMARY", K.cr_correlation_summary(scatter))
show("CORRELATION MATRIX", K.correlation_matrix(a, c, r))
show("CR JOIN COVERAGE", K.cr_join_coverage(a, c, r))

combined = EE.combined_operational_analysis(a, c, r)
show("COMBINED OPERATIONAL ANALYSIS", combined)

show("QA CONTROL DAILY", K.qa_control_daily(a))
show("CSAT CONTROL DAILY", K.csat_control_daily(c))
show("RECONTACT CONTROL DAILY", K.recontact_control_daily(r))
show("WEEKLY KPI TABLE", K.weekly_kpi_table(a, c, r))

show("REQUESTER PERFORMANCE", EE.requester_performance(a, c, r))
show("CSAT SEGMENTATION", EE.csat_segmentation(c, top_n=8, min_n=50))

show("QA AUDITOR OUTCOME", K.qa_auditor_outcome(a))
show("QA DISSATISFACTION OWNER", K.qa_dissatisfaction_owner(a))
show("QA DISSATISFACTION SUBREASON", K.qa_dissatisfaction_subreason(a))
show("QA REPEAT 48H", K.qa_repeat_48h(a))
show("PROCESS ADHERENCE", K.qa_process_adherence_summary(a))

ch = K.channel_performance(a, c, r)
actions = EE.generate_action_plan(combined, ch, K.top_failing_attributes(e, a),
                                  K.recontact_by_cr(r, csat=c), summary, K.recontact_rate(r))
show("GENERATED ACTION PLAN", [vars(x) for x in actions])
