import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from modules.data_loader import load_all_data

d = load_all_data()
a, c, r = d["fact_audits"], d["fact_csat"], d["fact_recontact"]
print("AUDITS cols", list(a.columns))
print("tenure cohort:\n", a.groupby("Tenure_Cohort").agg(n=("Audit_ID","count"), qa=("Score_Pct","mean")).to_string())
print("tenure raw:\n", a["Tenure_Raw"].value_counts(dropna=False).to_string())
print("audit channel:\n", a["Channel"].value_counts().to_string())
print("csat channel:\n", c["Channel"].value_counts().head(20).to_string() if "Channel" in c.columns else "NO CHANNEL")
print("csat cols sample", [x for x in c.columns if "ten" in x.lower() or "chan" in x.lower() or "agent" in x.lower()])
print("rc cols", [x for x in r.columns if "ten" in x.lower() or "chan" in x.lower()])
print("rc channel:\n", r["standard_channel_name"].value_counts().head(15).to_string() if "standard_channel_name" in r.columns else r.columns.tolist())
