"""Agent and supervisor cuts needed for the People section of Deliverable 2."""

from __future__ import annotations

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from modules.data_loader import load_all_data
from modules import kpis as K
from modules import alerts as A

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_rows", 60)


def show(title, obj):
    print("\n" + "=" * 95)
    print(title)
    print("=" * 95)
    print(obj.to_string(index=False) if isinstance(obj, pd.DataFrame) else obj)


data = load_all_data()
a, e, c, r = (data["fact_audits"], data["fact_errors"],
              data["fact_csat"], data["fact_recontact"])

show("AGENT POPULATION", {
    "agents_audited": a["Agent_ID"].nunique(),
    "supervisors": a["Supervisor_ID"].nunique(),
    "audits": len(a),
    "audits_per_agent_mean": round(len(a) / a["Agent_ID"].nunique(), 2),
})

roster = K.qa_agent_roster(a, e, min_n=5)
show("QA AGENT ROSTER columns", list(roster.columns))
show("QA AGENT ROSTER (head 15)", roster.head(15))
show("QA AGENT ROSTER (tail 15 = worst)", roster.tail(15))

qa_q = K.qa_agent_quartiles(a, min_n=5)
show("QA AGENT QUARTILES columns", list(qa_q.columns))
show("QA QUARTILE COUNTS", qa_q["Quartile"].value_counts().to_dict())
bands = K.quartile_band_summary(qa_q)
show("QA QUARTILE BANDS", {k: v for k, v in bands.items() if k != "ranked"})

csat_q = K.csat_agent_quartiles(c, a, min_n=20)
show("CSAT AGENT QUARTILES columns", list(csat_q.columns))
show("CSAT QUARTILE COUNTS", csat_q["Quartile"].value_counts().to_dict())
cbands = K.quartile_band_summary(csat_q)
show("CSAT QUARTILE BANDS", {k: v for k, v in cbands.items() if k != "ranked"})

gap = K.agents_below_qa_goal(a, min_n=5)
show("AGENTS BELOW QA GOAL columns", list(gap.columns))
show("AGENTS BELOW QA GOAL", gap.head(20))

show("QA COACHING QUEUE (supervisors)", A.qa_coaching_queue(gap, top_n=10))

sup = K.supervisor_overview(a, c, min_n=5)
show("SUPERVISOR OVERVIEW columns", list(sup.columns))
show("SUPERVISOR OVERVIEW", sup)

mix = K.supervisor_quartile_mix(qa_q)
show("SUPERVISOR QUARTILE MIX columns", list(mix.columns))
show("SUPERVISOR QUARTILE MIX", mix)

show("AGENT FAIL CONCENTRATORS", K.qa_agent_fail_concentrators(e, a, top_n=12))
show("CSAT AGENT UNSAT CONCENTRATORS", K.csat_agent_unsat_concentrators(c, a, top_n=12))

show("DIM SUPERVISORS", data["dim_supervisors"].sort_values("Avg_Score").head(12))
show("DIM AGENTS describe", data["dim_agents"][["Total_Audits", "Avg_Score", "Fatal_Count"]].describe())

show("QA BY TENURE", K.qa_by_tenure(a))
show("TENURE CSAT OVERVIEW", K.tenure_csat_overview(a, c))

rank = K.agent_ranking_index(a, c)
show("AGENT RANKING INDEX columns", list(rank.columns))
show("AGENT RANKING INDEX (worst 12)", rank.tail(12))

show("CSAT SUPERVISOR MAPPING", K.csat_supervisor_mapping(c, a))
show("CSAT BY SUPERVISOR", K.csat_by_supervisor(c, a, min_n=20, top_n=12))
