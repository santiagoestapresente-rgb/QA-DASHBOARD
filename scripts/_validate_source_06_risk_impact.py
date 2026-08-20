"""
Forensic validation 06 — quantify the impact of every interpretation risk found,
and audit the exported model's own Validation / Assumptions sheets.
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


def main() -> None:
    qa = pd.read_excel(SRC, sheet_name="QA")
    cs = pd.read_excel(SRC, sheet_name="CSAT")
    rc = pd.read_excel(SRC, sheet_name="Recontact")
    for d in (qa, cs, rc):
        d.columns = [str(c).strip().replace("\ufeff", "") for c in d.columns]

    cols = list(qa.columns)
    PHONE = [str(c) for c in cols[22:34]]
    CHAT = [str(c) for c in cols[34:42]]

    def is_crit(c): return "critical" in c.lower()

    hr("R1. IS THE 'N/A EXCLUDED' RULE EVER ACTUALLY EXERCISED?")
    tot2 = int((qa[PHONE + CHAT] == 2).sum().sum())
    foreign2 = int((qa.loc[qa["Channel"] == "Phone", CHAT] == 2).sum().sum()
                   + (qa.loc[qa["Channel"] == "Live Chat", PHONE] == 2).sum().sum())
    print(f"  Total cells with value 2 (N/A) : {tot2:,}")
    print(f"  Of those, in the FOREIGN channel range: {foreign2:,}")
    print(f"  N/A cells inside an audit's OWN channel range: {tot2 - foreign2:,}")
    print(f"\n  -> In this dataset '2' means 'attribute belongs to the other channel',")
    print(f"     never 'not applicable to this interaction'. Every audit grades 100% of")
    print(f"     its own channel's attributes (Phone 12/12, Live Chat 8/8).")
    print(f"     The N/A-exclusion rule is therefore inert: removing it would not change")
    print(f"     a single score, PROVIDED the channel filter stays in place.")

    print(f"\n  What if someone dropped the channel filter and scored all 20 attributes?")
    naive = []
    for _, r in qa.iterrows():
        at = PHONE + CHAT
        crit = any(r[c] == 1 for c in at if is_crit(c))
        nc = sum(1 for c in at if not is_crit(c) and r[c] == 1)
        naive.append(0.0 if crit else max(0.0, 100.0 - 10 * nc))
    print(f"     QA Score would be {np.mean(naive):.4f} (vs 94.1423) "
          f"-> delta {np.mean(naive) - 94.142276:+.4f} pp")
    print(f"     (identical here only because foreign cells are all 2 and 2 is excluded;")
    print(f"      if N/A were NOT excluded the whole model would collapse)")

    hr("R2. QA SCORE — THE BUSINESS-CASE RULE vs THE SOURCE'S OWN Score_end_user")
    sc, srcs = [], qa["Score_end_user"]
    for _, r in qa.iterrows():
        at = PHONE if r["Channel"] == "Phone" else CHAT
        crit = any(r[c] == 1 for c in at if is_crit(c))
        nc = sum(1 for c in at if not is_crit(c) and r[c] == 1)
        sc.append(0.0 if crit else max(0.0, 100.0 - 10 * nc))
    sc = np.array(sc)
    print(f"  Business-case rule (what we ship) : {sc.mean():.4f}   vs goal 85 -> +{sc.mean()-85:.2f} pp")
    print(f"  Source Score_end_user column      : {srcs.mean():.4f}   vs goal 85 -> +{srcs.mean()-85:.2f} pp")
    print(f"  Gap                               : {sc.mean()-srcs.mean():+.4f} pp")
    print(f"\n  Narrative impact: 'comfortably above target (+9.1pp)' vs")
    print(f"                    'barely above target (+1.9pp)'.")
    print(f"\n  Implied per-attribute deduction in Score_end_user (single-fail rows):")
    ded = {}
    for _, r in qa.iterrows():
        at = PHONE if r["Channel"] == "Phone" else CHAT
        f = [c for c in at if r[c] == 1]
        if len(f) == 1 and not is_crit(f[0]) and r["Score_end_user"] > 0:
            ded.setdefault(f[0], []).append(100 - r["Score_end_user"])
    for k, v in sorted(ded.items(), key=lambda x: -len(x[1])):
        print(f"    -{int(np.median(v)):>3} pts  (n={len(v):>3}, values={sorted(set(v))})  {k}")
    print(f"\n  -> the source uses a WEIGHTED rubric (-3, -5, -15, -20, -30 pts per attribute),")
    print(f"     not the flat -10 stated in the business case. Both cannot be right.")

    hr("R3. THE 151 'ALL PASS BUT SCORE 0' AUDITS")
    nf = qa[(qa["Channel"] == "Live Chat") & ((qa[CHAT] == 1).sum(axis=1) == 0)
            & (qa["Score_end_user"] == 0)]
    ok = qa[(qa["Channel"] == "Live Chat") & ((qa[CHAT] == 1).sum(axis=1) == 0)
            & (qa["Score_end_user"] == 100)]
    bad_proc = "no siguió el proceso"
    a = nf["Se_le_brindo_solucion_a_la_solicitud"].astype(str).str.contains(bad_proc).mean()
    b = ok["Se_le_brindo_solucion_a_la_solicitud"].astype(str).str.contains(bad_proc).mean()
    print(f"  Audits with every attribute passing but Score_end_user = 0 : {len(nf)}")
    print(f"    share flagged 'el agente no siguió el proceso' : {a*100:.1f}%")
    print(f"  Audits with every attribute passing and Score_end_user = 100: {len(ok)}")
    print(f"    share flagged 'el agente no siguió el proceso' : {b*100:.1f}%")
    print(f"\n  -> the source's 0 is driven by process-adherence criteria that are NOT")
    print(f"     represented in columns W-AP. Any score rebuilt only from W-AP will miss them.")
    print(f"  Impact if these 151 audits were scored 0 instead of 100 under our rule:")
    alt = sc.copy()
    alt[nf.index] = 0.0
    print(f"     QA Score would be {alt.mean():.4f} (vs {sc.mean():.4f}) "
          f"-> {alt.mean()-sc.mean():+.4f} pp")

    hr("R4. RECONTACT — DENOMINATOR SCOPE vs THE 5.44% GOAL")
    tot_c, tot_v = rc["Contacts"].sum(), rc["Recontact Volume"].sum()
    print(f"  All 12 channels (what we report): {tot_v/tot_c*100:.4f} %  "
          f"[contacts {tot_c:,}]")
    g = rc.groupby("standard_channel_name").agg(C=("Contacts", "sum"),
                                                V=("Recontact Volume", "sum"))
    g["share_of_contacts_%"] = (g["C"] / tot_c * 100).round(2)
    g["rate_%"] = (g["V"] / g["C"] * 100).round(2)
    print(g.sort_values("C", ascending=False).to_string())
    sh = rc[rc["standard_channel_name"] == "SELF HELP"]
    print(f"\n  SELF HELP alone is {sh['Contacts'].sum()/tot_c*100:.1f}% of the denominator "
          f"at a {sh['Recontact Volume'].sum()/sh['Contacts'].sum()*100:.2f}% rate.")
    ex = rc[rc["standard_channel_name"] != "SELF HELP"]
    print(f"  Excluding SELF HELP          : {ex['Recontact Volume'].sum()/ex['Contacts'].sum()*100:.4f} %")
    hu = rc[rc["standard_channel_name"].isin(["PHONE", "LIVE CHAT"])]
    print(f"  Human-agent channels only    : {hu['Recontact Volume'].sum()/hu['Contacts'].sum()*100:.4f} %")
    print(f"\n  -> 5.83% vs the 5.44% goal is a 0.39pp miss, but the number is dominated by")
    print(f"     self-service. On the channels QA actually audits the rate is 15.56%.")
    print(f"     Which scope the 5.44% goal refers to is an assumption that must be stated.")

    hr("R5. RECONTACT — IMPOSSIBLE ROWS (Recontact Volume > Contacts)")
    bad = rc[rc["Recontact Volume"] > rc["Contacts"]]
    print(f"  Rows: {len(bad)}  ({len(bad)/len(rc)*100:.2f}% of rows)")
    print(f"  Contacts in them        : {int(bad['Contacts'].sum()):,}")
    print(f"  Recontact Volume in them: {int(bad['Recontact Volume'].sum()):,}")
    print(f"  Excess volume (V - C)   : {int((bad['Recontact Volume']-bad['Contacts']).sum()):,}")
    print(f"  Channel mix: {bad['standard_channel_name'].value_counts().to_dict()}")
    zc = rc[(rc["Contacts"] == 0)]
    print(f"\n  Rows with Contacts == 0 : {len(zc)}  "
          f"(carrying {int(zc['Recontact Volume'].sum()):,} recontacts with a zero denominator)")
    print(f"  -> a per-row rate on these is undefined/infinite; the global ratio-of-sums")
    print(f"     absorbs them safely, but any per-row average or per-row rate would break.")
    clean = rc[rc["Recontact Volume"] <= rc["Contacts"]]
    print(f"\n  Rate excluding the impossible rows: "
          f"{clean['Recontact Volume'].sum()/clean['Contacts'].sum()*100:.4f} % "
          f"(vs {tot_v/tot_c*100:.4f} %) -> "
          f"{clean['Recontact Volume'].sum()/clean['Contacts'].sum()*100 - tot_v/tot_c*100:+.4f} pp")
    print(f"  -> materially irrelevant to the headline, but it proves 'Contacts' and")
    print(f"     'Recontact Volume' are NOT measured on the same base for every row.")

    hr("R6. CSAT — EXACT DUPLICATE ROWS")
    dup = cs[cs.duplicated(keep=False)]
    stars45 = ["Questionnaires With Star Level =4", "Questionnaires With Star Level =5"]
    print(f"  Exact full-row duplicates      : {int(cs.duplicated().sum()):,} "
          f"({cs.duplicated().mean()*100:.2f}% of rows)")
    print(f"  Rows involved in a duplicate set: {len(dup):,}")
    print(f"  Feedback CNT they carry        : {int(dup['Feedback CNT'].sum()):,} of "
          f"{int(cs['Feedback CNT'].sum()):,}")
    base = cs[stars45].sum().sum() / cs["Feedback CNT"].sum() * 100
    ded2 = cs.drop_duplicates()
    alt2 = ded2[stars45].sum().sum() / ded2["Feedback CNT"].sum() * 100
    print(f"  CSAT as reported               : {base:.4f} %")
    print(f"  CSAT if duplicates de-duped    : {alt2:.4f} %  -> {alt2-base:+.4f} pp")
    print(f"\n  Feedback CNT distribution on duplicate rows: "
          f"{dup['Feedback CNT'].value_counts().head().to_dict()}")
    print(f"  -> the tab is a survey-level extract where Feedback CNT is almost always 1;")
    print(f"     two customers giving the same rating on the same day/agent/CR produce")
    print(f"     byte-identical rows. De-duplicating would DELETE real surveys.")
    print(f"     KEEPING them (current behaviour) is the correct choice.")

    hr("R7. CSAT — 'Total Feedback CNT' NAMING")
    print(f"  The business case calls the denominator 'Total Feedback CNT'.")
    print(f"  The actual column in the workbook is 'Feedback CNT' (there is no column")
    print(f"  literally named 'Total Feedback CNT').")
    print(f"  Evidence the two are the same thing:")
    st = [f"Questionnaires With Star Level ={i}" for i in range(1, 6)]
    print(f"    SUM(star 1..5) = {int(cs[st].sum().sum()):,}")
    print(f"    SUM(Feedback CNT) = {int(cs['Feedback CNT'].sum()):,}")
    print(f"    equal on every single row: {bool((cs[st].sum(axis=1) == cs['Feedback CNT']).all())}")
    print(f"    'Deliver CNT' = {int(cs['Deliver CNT'].sum()):,} -> surveys SENT, not answered.")
    print(f"    Response rate = {cs['Feedback CNT'].sum()/cs['Deliver CNT'].sum()*100:.2f} %")
    print(f"  -> the model uses the right column.")

    hr("R8. THE EXPORTED MODEL'S OWN Validation / Assumptions SHEETS")
    try:
        v = read_model_sheet("Validation")
        print(v.to_string(index=False))
        print(f"\n  Checks REVIEW/failing: {int((v['Result'] != 'PASS').sum())}")
    except Exception as e:
        print(f"  Validation: {e}")
    try:
        a = read_model_sheet("Assumptions")
        print("\n--- Assumptions sheet ---")
        for _, r in a.iterrows():
            print(f"  [{r['Topic']}] {r['Note']}")
    except Exception as e:
        print(f"  Assumptions: {e}")

    hr("R9. FACT/DIM REFERENTIAL INTEGRITY (independent re-check)")
    try:
        fa = read_model_sheet("fact_audit")
        fc = read_model_sheet("fact_csat")
        fr = read_model_sheet("fact_recontact")
        fat = read_model_sheet("fact_audit_attribute")
        dch = read_model_sheet("dim_channel")
        dcr = read_model_sheet("dim_cr")
        dco = read_model_sheet("dim_country")
        dd = read_model_sheet("dim_date")
        dat = read_model_sheet("dim_attribute")
        dag = read_model_sheet("dim_agent")
        pairs = [
            ("fact_audit.Channel_Key", set(fa["Channel_Key"]), "dim_channel", set(dch["Channel_Key"])),
            ("fact_csat.Channel_Key", set(fc["Channel_Key"]), "dim_channel", set(dch["Channel_Key"])),
            ("fact_recontact.Channel_Key", set(fr["Channel_Key"]), "dim_channel", set(dch["Channel_Key"])),
            ("fact_recontact.Prev_Channel_Key", set(fr["Prev_Channel_Key"]), "dim_channel", set(dch["Channel_Key"])),
            ("fact_audit.CR_Key", set(fa["CR_Key"]), "dim_cr", set(dcr["CR_Key"])),
            ("fact_csat.CR_Key", set(fc["CR_Key"]), "dim_cr", set(dcr["CR_Key"])),
            ("fact_recontact.CR_Key", set(fr["CR_Key"]), "dim_cr", set(dcr["CR_Key"])),
            ("fact_audit.Country_Code", set(fa["Country_Code"].dropna()), "dim_country", set(dco["Country_Code"])),
            ("fact_csat.Country_Code", set(fc["Country_Code"].dropna()), "dim_country", set(dco["Country_Code"])),
            ("fact_audit.Date", set(pd.to_datetime(fa["Date"])), "dim_date", set(pd.to_datetime(dd["Date"]))),
            ("fact_csat.Date", set(pd.to_datetime(fc["Date"])), "dim_date", set(pd.to_datetime(dd["Date"]))),
            ("fact_recontact.Date", set(pd.to_datetime(fr["Date"])), "dim_date", set(pd.to_datetime(dd["Date"]))),
            ("fact_audit_attribute.Attribute_Key", set(fat["Attribute_Key"]), "dim_attribute", set(dat["Attribute_Key"])),
            ("fact_audit.Agent_ID", set(fa["Agent_ID"]), "dim_agent", set(dag["Agent_ID"].astype(str))),
        ]
        for name, child, dname, parent in pairs:
            orphans = child - parent
            print(f"  {name:38s} -> {dname:14s} orphans={len(orphans)} "
                  f"{sorted(map(str, orphans))[:3] if orphans else ''}")
        print(f"\n  fact_audit_attribute rows: {len(fat):,}")
        exp = int((qa['Channel'] == 'Phone').sum() * 12 + (qa['Channel'] == 'Live Chat').sum() * 8)
        print(f"  Expected (audits x own-channel attributes): {exp:,}  match={len(fat)==exp}")
        print(f"  Is_Fail sum: {int(fat['Is_Fail'].sum()):,}  "
              f"vs raw 1s inside own-channel ranges: "
              f"{int((qa.loc[qa['Channel']=='Phone', PHONE]==1).sum().sum() + (qa.loc[qa['Channel']=='Live Chat', CHAT]==1).sum().sum()):,}")
        print(f"  Result distribution: {fat['Result'].value_counts().to_dict()}")
    except Exception as e:
        print(f"  Integrity check failed: {e}")


if __name__ == "__main__":
    main()
