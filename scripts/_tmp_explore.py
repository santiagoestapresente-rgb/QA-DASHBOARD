import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)

rc = pd.read_parquet(ROOT / "data/packaged/fact_recontact.parquet")
print("RECONTACT COLUMNS:", rc.columns.tolist())
g = (
    rc.groupby("standard_channel_name")
    .agg(contacts=("Contacts", "sum"), recontacts=("Recontact Volume", "sum"), rows=("Contacts", "size"))
)
g["rate"] = g["recontacts"] / g["contacts"] * 100
g["share"] = g["contacts"] / g["contacts"].sum() * 100
print(g.sort_values("contacts", ascending=False).round(2))
print()
print("ALL 12 CHANNELS  :", round(rc["Recontact Volume"].sum() / rc["Contacts"].sum() * 100, 2))
ex = rc[rc["standard_channel_name"].astype(str).str.upper() != "SELF HELP"]
print("EXCL SELF HELP   :", round(ex["Recontact Volume"].sum() / ex["Contacts"].sum() * 100, 2))
aud = rc[rc["standard_channel_name"].astype(str).str.upper().isin(["PHONE", "LIVE CHAT"])]
print("AUDITED (PH+LC)  :", round(aud["Recontact Volume"].sum() / aud["Contacts"].sum() * 100, 2))
print("mean-of-ratios   :", round(rc["Recontact_Rate"].mean(), 2))
print()
print("rows RcVol>Contacts:", int((rc["Recontact Volume"] > rc["Contacts"]).sum()))
print("rows Contacts==0   :", int((rc["Contacts"] == 0).sum()))
print()

au = pd.read_parquet(ROOT / "data/packaged/fact_audits.parquet")
print("AUDIT COLUMNS:", au.columns.tolist())
ch = au.groupby("Channel").agg(qa=("Score_Pct", "mean"), n=("Audit_ID", "count"))
ch["share"] = ch["n"] / ch["n"].sum() * 100
print(ch.round(2))
print("GLOBAL QA:", round(au["Score_Pct"].mean(), 2))
print()

qa_raw = pd.read_excel(ROOT / "data/Business Case.xlsx", sheet_name="QA")
cands = [c for c in qa_raw.columns if "score" in c.lower() or "proceso" in c.lower() or "process" in c.lower()]
print("QA SHEET score-ish columns:", cands)
if "Score_end_user" in qa_raw.columns:
    s = pd.to_numeric(qa_raw["Score_end_user"], errors="coerce")
    print("Score_end_user mean:", round(s.mean(), 2), "n:", int(s.notna().sum()), "zeros:", int((s == 0).sum()))
