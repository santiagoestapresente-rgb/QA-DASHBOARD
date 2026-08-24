import sys

sys.path.insert(0, r"C:\Users\PC\Documents\DIDI")
from modules.data_loader import load_all_data
from modules.kpis import csat_unsatisfied_by_cr, QA_GOAL

d = load_all_data()
a, e, c = d["fact_audits"], d["fact_errors"], d["fact_csat"]

print("=== QA: audits below 85 by CR ===")
a = a.copy()
a["_cr"] = a["CR_Lv4"].astype("string").str.strip()
below = a[a["Score_Pct"] < 85]
n_below = len(below)
print("below-goal audits", n_below, "of", len(a), f"({n_below/len(a)*100:.1f}%)")
g = (
    below.groupby("_cr")
    .agg(n_below=("Audit_ID", "count"), qa=("Score_Pct", "mean"))
    .reset_index()
    .sort_values("n_below", ascending=False)
)
g["share"] = (g["n_below"] / n_below * 100).round(1)
g["cum"] = g["share"].cumsum().round(1)
print(g.head(10).to_string(index=False))
print("top3 share", g.head(3)["share"].sum(), "top5", g.head(5)["share"].sum())

print("\n=== QA: attribute fails by CR ===")
e = e.copy()
e["_cr"] = e["CR_Lv4"].astype("string").str.strip()
fe = (
    e.groupby("_cr")
    .size()
    .reset_index(name="fails")
    .sort_values("fails", ascending=False)
)
fe["share"] = (fe["fails"] / fe["fails"].sum() * 100).round(1)
fe["cum"] = fe["share"].cumsum().round(1)
print("total fails", int(fe["fails"].sum()))
print(fe.head(10).to_string(index=False))
print("top3", fe.head(3)["share"].sum(), "top5", fe.head(5)["share"].sum())

print("\n=== QA: lowest score (min n=3) vs volume ===")
low = (
    a.groupby("_cr")
    .agg(n=("Audit_ID", "count"), qa=("Score_Pct", "mean"))
    .reset_index()
)
low = low[low["n"] >= 3].sort_values("qa")
print(low.head(8).to_string(index=False))

print("\n=== QA below-goal by channel x CR (top) ===")
for ch in ("Phone", "Live Chat"):
    sub = below[below["Channel"] == ch]
    gg = sub.groupby("_cr").size().reset_index(name="n").sort_values("n", ascending=False)
    gg["share"] = (gg["n"] / len(sub) * 100).round(1)
    print(ch, "below", len(sub))
    print(gg.head(5).to_string(index=False))

print("\n=== CSAT unsatisfied volume ===")
u = csat_unsatisfied_by_cr(c)
tot_u = u["Unsatisfied"].sum()
tot_f = u["Feedback"].sum()
u = u.copy()
u["ushare"] = (u["Unsatisfied"] / tot_u * 100).round(1)
u["cum"] = u["ushare"].cumsum().round(1)
print("unsatisfied", int(tot_u), "surveys in these CRs", int(tot_f))
print(u.head(10)[["CR_Lv4", "CSAT_Score", "Feedback", "Unsatisfied", "ushare", "cum"]].to_string(index=False))
print("top3", u.head(3)["ushare"].sum(), "top5", u.head(5)["ushare"].sum())

print("\n=== CSAT worst rate (min 100 surveys) ===")
u2 = u[u["Feedback"] >= 100].sort_values("CSAT_Score")
print(u2.head(8)[["CR_Lv4", "CSAT_Score", "Feedback", "Unsatisfied", "ushare"]].to_string(index=False))
