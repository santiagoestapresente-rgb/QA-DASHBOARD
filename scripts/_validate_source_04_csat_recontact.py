"""
Forensic validation 04 — CSAT and Recontact formulas, independently recomputed.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"C:\Users\PC\Downloads\Business Case.xlsx")
MODEL = Path(__file__).resolve().parent.parent / "powerbi" / "DiDi_CX_PowerBI_Model.xlsx"


def hr(t: str) -> None:
    print("\n" + "=" * 100)
    print(t)
    print("=" * 100)


def read_model_sheet(sheet: str) -> pd.DataFrame:
    tmp = Path(tempfile.gettempdir()) / "_didi_model_snapshot.xlsx"
    if not tmp.exists() or tmp.stat().st_mtime < MODEL.stat().st_mtime:
        shutil.copy2(MODEL, tmp)
    return pd.read_excel(tmp, sheet_name=sheet, engine="openpyxl")


def csat_checks() -> None:
    cs = pd.read_excel(SRC, sheet_name="CSAT")
    cs.columns = [str(c).strip().replace("\ufeff", "") for c in cs.columns]

    hr("CSAT — COLUMN INVENTORY / IS THERE AN EXPLICIT 'Total Feedback CNT'?")
    print(f"Rows: {len(cs):,}")
    print("Columns:", list(cs.columns))
    cand = [c for c in cs.columns if "cnt" in c.lower() or "total" in c.lower() or "feedback" in c.lower()]
    print(f"\nCandidate count/total columns: {cand}")
    print(f"'Total Feedback CNT' present verbatim? {'Total Feedback CNT' in cs.columns}")
    print(f"'Feedback CNT' present verbatim?       {'Feedback CNT' in cs.columns}")

    stars = [f"Questionnaires With Star Level ={i}" for i in range(1, 6)]
    cs["star_sum"] = cs[stars].sum(axis=1)

    hr("CSAT — DENOMINATOR: 'Feedback CNT' vs ROW COUNT vs SUM OF STARS vs 'Deliver CNT'")
    n_rows = len(cs)
    fb = cs["Feedback CNT"].sum()
    dl = cs["Deliver CNT"].sum()
    ss = cs["star_sum"].sum()
    sat = cs["Questionnaires With Star Level =4"].sum() + cs["Questionnaires With Star Level =5"].sum()
    print(f"  Row count                    : {n_rows:,}")
    print(f"  SUM(Feedback CNT)            : {fb:,}")
    print(f"  SUM(Deliver CNT)             : {dl:,}")
    print(f"  SUM(star levels 1..5)        : {ss:,}")
    print(f"  SUM(4-star + 5-star)         : {sat:,}")

    print("\n  CSAT under each denominator:")
    print(f"    (4+5) / SUM(Feedback CNT)  = {sat/fb*100:.4f} %   <-- formula used by the model")
    print(f"    (4+5) / row count          = {sat/n_rows*100:.4f} %")
    print(f"    (4+5) / SUM(star 1..5)     = {sat/ss*100:.4f} %")
    print(f"    (4+5) / SUM(Deliver CNT)   = {sat/dl*100:.4f} %")
    print(f"\n  CONTROL TOTAL 79.95 CONFIRMED (Feedback CNT denominator)? "
          f"{round(sat/fb*100, 2) == 79.95}")

    hr("CSAT — INTERNAL CONSISTENCY: does SUM(stars 1..5) equal 'Feedback CNT' per row?")
    eq = (cs["star_sum"] == cs["Feedback CNT"])
    print(f"  Rows where star_sum == Feedback CNT : {int(eq.sum()):,} ({eq.mean()*100:.2f}%)")
    print(f"  Rows where star_sum  > Feedback CNT : {int((cs['star_sum'] > cs['Feedback CNT']).sum()):,}")
    print(f"  Rows where star_sum  < Feedback CNT : {int((cs['star_sum'] < cs['Feedback CNT']).sum()):,}")
    diff = cs[~eq]
    if len(diff):
        print(f"\n  Sample of mismatching rows:")
        print(diff[["Feedback CNT", "Deliver CNT"] + stars + ["star_sum"]].head(12).to_string(index=False))
        print(f"\n  Total gap (Feedback CNT - star_sum): {int(cs['Feedback CNT'].sum() - cs['star_sum'].sum()):,}")

    hr("CSAT — STAR RATING VALUE RANGE AND NULLS")
    for c in stars:
        s = cs[c]
        print(f"  {c:38s} nulls={int(s.isna().sum()):>5}  min={s.min()}  max={s.max()}  "
              f"negatives={int((s < 0).sum())}  non-int={int((s % 1 != 0).sum())}")
    print(f"\n  There is NO per-response 'Star Rating' column; the tab is pre-aggregated into")
    print(f"  five count columns (star levels 1-5). So 'star rating outside 1-5' cannot occur")
    print(f"  by construction; the equivalent risk is a count column outside its expected range.")
    print(f"  Rows with Feedback CNT <= 0 : {int((cs['Feedback CNT'] <= 0).sum()):,}")
    print(f"  Rows with Feedback CNT null : {int(cs['Feedback CNT'].isna().sum()):,}")
    print(f"  Rows where all star counts are 0: {int((cs[stars].sum(axis=1) == 0).sum()):,}")

    hr("CSAT — DUPLICATE ROWS")
    grain = ["pt(天)", "Consolidated Channel.", "Country Code", "CR Lv4", "Sub CR",
             "Agent name", "Business Type Name", "User Type", "Customer Tag", "user_tenure"]
    print(f"  Fully identical rows (all 24 cols): {int(cs.duplicated().sum()):,}")
    print(f"  Duplicated on business grain {grain}:")
    d = cs.duplicated(subset=grain, keep=False)
    print(f"     rows involved: {int(d.sum()):,}  ({d.mean()*100:.2f}%)")
    print(f"     distinct grain combos duplicated: {cs[d].groupby(grain, dropna=False).ngroups:,}")
    print(f"  Note: rows are survey batches, so repeated grain is expected; only exact")
    print(f"        full-row duplicates would signal double counting.")
    if cs.duplicated().sum():
        dupfull = cs[cs.duplicated(keep=False)]
        print(f"\n  Feedback CNT carried by exact duplicate rows: {int(dupfull['Feedback CNT'].sum()):,}")
        dedup_sat = cs.drop_duplicates()
        s2 = (dedup_sat["Questionnaires With Star Level =4"].sum()
              + dedup_sat["Questionnaires With Star Level =5"].sum())
        f2 = dedup_sat["Feedback CNT"].sum()
        print(f"  CSAT if exact duplicates were dropped: {s2/f2*100:.4f} % "
              f"(vs {sat/fb*100:.4f} %) -> delta {s2/f2*100 - sat/fb*100:+.4f} pp")

    hr("CSAT — DATE RANGE / NULL KEYS")
    d = pd.to_datetime(cs["pt(天)"])
    print(f"  Date min: {d.min()}   max: {d.max()}   nulls: {int(d.isna().sum())}   distinct days: {d.nunique()}")
    for c in ["Consolidated Channel.", "Country Code", "CR Lv1", "CR Lv4", "Agent name", "open_question"]:
        blanks = int(cs[c].isna().sum() + (cs[c].astype(str).str.strip() == "").sum())
        print(f"  {c:26s} nulls/blanks={blanks:>6}  distinct={cs[c].nunique():>6}")
    print(f"\n  open_question == 'Other' (placeholder): "
          f"{int((cs['open_question'].astype(str).str.strip().str.lower() == 'other').sum()):,}")

    hr("CSAT — MODEL fact_csat CROSS-CHECK")
    try:
        fc = read_model_sheet("fact_csat")
        print(f"  fact_csat rows: {len(fc):,}   source rows: {len(cs):,}   match: {len(fc) == len(cs)}")
        print(f"  SUM(Feedback_CNT) model : {fc['Feedback_CNT'].sum():,}   source: {fb:,}   "
              f"match: {fc['Feedback_CNT'].sum() == fb}")
        print(f"  SUM(Satisfied_CNT) model: {fc['Satisfied_CNT'].sum():,}   source: {sat:,}   "
              f"match: {fc['Satisfied_CNT'].sum() == sat}")
        print(f"  Model CSAT: {fc['Satisfied_CNT'].sum()/fc['Feedback_CNT'].sum()*100:.4f} %")
    except Exception as e:
        print(f"  Could not read fact_csat: {e}")

    hr("CSAT — BY CHANNEL / COUNTRY (independent)")
    for key in ["Consolidated Channel.", "Country Code"]:
        g = cs.groupby(key).apply(
            lambda x: pd.Series({
                "rows": len(x),
                "feedback": x["Feedback CNT"].sum(),
                "satisfied": x["Questionnaires With Star Level =4"].sum()
                             + x["Questionnaires With Star Level =5"].sum(),
            }), include_groups=False)
        g["CSAT_%"] = (g["satisfied"] / g["feedback"] * 100).round(2)
        print(f"\n  By {key}:")
        print(g.to_string())


def recontact_checks() -> None:
    rc = pd.read_excel(SRC, sheet_name="Recontact")
    rc.columns = [str(c).strip().replace("\ufeff", "") for c in rc.columns]

    hr("RECONTACT — COLUMN INVENTORY")
    print(f"Rows: {len(rc):,}")
    print("Columns:", list(rc.columns))
    num = rc.select_dtypes(include=[np.number]).columns.tolist()
    print(f"Numeric columns (candidates for volume/denominator): {num}")

    hr("RECONTACT — RATE, INDEPENDENTLY")
    contacts = rc["Contacts"].sum()
    vol = rc["Recontact Volume"].sum()
    print(f"  SUM(Contacts)         = {contacts:,}    <- denominator used")
    print(f"  SUM(Recontact Volume) = {vol:,}         <- numerator used")
    print(f"  Row count             = {len(rc):,}")
    print(f"\n  Recontact Rate = {vol/contacts*100:.6f} %  -> rounded {round(vol/contacts*100,2)}")
    print(f"  CONTROL TOTAL 5.83 CONFIRMED? {round(vol/contacts*100,2) == 5.83}")
    print(f"\n  Alternative (wrong) denominators for reference:")
    print(f"    vol / (contacts + vol)   = {vol/(contacts+vol)*100:.4f} %")
    print(f"    mean of per-row rates    = {(rc['Recontact Volume']/rc['Contacts']).replace([np.inf,-np.inf],np.nan).mean()*100:.4f} % "
          f"(unweighted average — would be wrong)")

    hr("RECONTACT — DOUBLE AGGREGATION RISK")
    print(f"  Contacts: min={rc['Contacts'].min()} max={rc['Contacts'].max()} "
          f"mean={rc['Contacts'].mean():.2f}  -> rows are pre-aggregated buckets, not single contacts")
    print(f"  Recontact Volume: min={rc['Recontact Volume'].min()} max={rc['Recontact Volume'].max()} "
          f"mean={rc['Recontact Volume'].mean():.2f}")
    print(f"  Rows where Recontact Volume > Contacts (impossible if same denominator): "
          f"{int((rc['Recontact Volume'] > rc['Contacts']).sum()):,}")
    if (rc["Recontact Volume"] > rc["Contacts"]).sum():
        print(rc[rc["Recontact Volume"] > rc["Contacts"]].head(10).to_string(index=False))
    print(f"  Rows with Contacts == 0: {int((rc['Contacts'] == 0).sum()):,}")
    print(f"  Rows with Recontact Volume < 0 or Contacts < 0: "
          f"{int(((rc['Recontact Volume'] < 0) | (rc['Contacts'] < 0)).sum()):,}")

    grain = ["Date(天)", "standard_channel_name", "prev_standard_channel_name",
             "CR Lv4", "customer_type", "Modality", "region_name"]
    print(f"\n  Grain of the tab: {grain}")
    print(f"  Exact full-row duplicates          : {int(rc.duplicated().sum()):,}")
    dg = rc.duplicated(subset=grain, keep=False)
    print(f"  Rows duplicated on that grain      : {int(dg.sum()):,}")
    if dg.sum():
        print(f"    -> the same grain appears more than once; summing counts them all.")
        print(f"    Contacts inside duplicated grain: {int(rc[dg]['Contacts'].sum()):,}")
        agg = rc.groupby(grain, dropna=False).agg(
            Contacts=("Contacts", "sum"), Vol=("Recontact Volume", "sum")).reset_index()
        print(f"    Rate after collapsing grain: {agg['Vol'].sum()/agg['Contacts'].sum()*100:.4f} % "
              f"(identical by construction — sum is associative)")
        print(rc[dg].sort_values(grain).head(8).to_string(index=False))
    if rc.duplicated().sum():
        ded = rc.drop_duplicates()
        print(f"    Rate if EXACT duplicates dropped: "
              f"{ded['Recontact Volume'].sum()/ded['Contacts'].sum()*100:.4f} %")

    hr("RECONTACT — DIMENSIONS / DATA QUALITY")
    for c in rc.columns:
        print(f"  {c:30s} nulls={int(rc[c].isna().sum()):>6}  distinct={rc[c].nunique():>6}")
    print(f"\n  region_name values: {rc['region_name'].unique().tolist()}  "
          f"-> no country breakdown possible")
    print(f"  Channels present: {sorted(rc['standard_channel_name'].dropna().unique().tolist())}")
    d = pd.to_datetime(rc["Date(天)"])
    print(f"  Date min={d.min()} max={d.max()} distinct={d.nunique()} nulls={int(d.isna().sum())}")

    hr("RECONTACT — RATE BY CHANNEL (independent)")
    g = rc.groupby("standard_channel_name").agg(
        rows=("Contacts", "size"), Contacts=("Contacts", "sum"),
        Recontacts=("Recontact Volume", "sum")).reset_index()
    g["Rate_%"] = (g["Recontacts"] / g["Contacts"] * 100).round(2)
    print(g.sort_values("Contacts", ascending=False).to_string(index=False))
    print(f"\n  Phone + Live Chat only (the QA-audited channels):")
    sub = rc[rc["standard_channel_name"].isin(["PHONE", "LIVE CHAT"])]
    print(f"    Contacts={sub['Contacts'].sum():,}  Recontacts={sub['Recontact Volume'].sum():,}  "
          f"Rate={sub['Recontact Volume'].sum()/sub['Contacts'].sum()*100:.4f} %")

    hr("RECONTACT — MODEL fact_recontact CROSS-CHECK")
    try:
        fr = read_model_sheet("fact_recontact")
        print(f"  rows model={len(fr):,}  source={len(rc):,}  match={len(fr)==len(rc)}")
        print(f"  SUM(Contacts) model={fr['Contacts'].sum():,}  source={contacts:,}  "
              f"match={fr['Contacts'].sum()==contacts}")
        print(f"  SUM(Recontact_Volume) model={fr['Recontact_Volume'].sum():,}  source={vol:,}  "
              f"match={fr['Recontact_Volume'].sum()==vol}")
        print(f"  Model rate: {fr['Recontact_Volume'].sum()/fr['Contacts'].sum()*100:.4f} %")
    except Exception as e:
        print(f"  Could not read fact_recontact: {e}")


if __name__ == "__main__":
    csat_checks()
    recontact_checks()
