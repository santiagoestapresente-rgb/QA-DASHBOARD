"""
Forensic validation 05 — CR hierarchy, key normalisation across the three tabs,
and general data-quality edge cases.
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unicodedata
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


# ── normalisation variants -----------------------------------------------------
def k_raw(v) -> str:
    return "UNKNOWN" if pd.isna(v) else str(v)


def k_model(v) -> str:
    """Exactly what build_powerbi_model.norm_key does: trim, collapse ws, casefold."""
    if pd.isna(v):
        return "UNKNOWN"
    t = re.sub(r"\s+", " ", str(v)).strip()
    return t.casefold() if t else "UNKNOWN"


def k_strong(v) -> str:
    """Stronger: model key + accent stripping + punctuation removal."""
    if pd.isna(v):
        return "UNKNOWN"
    t = re.sub(r"\s+", " ", str(v)).strip().casefold()
    t = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip() or "UNKNOWN"


def main() -> None:
    qa = pd.read_excel(SRC, sheet_name="QA")
    cs = pd.read_excel(SRC, sheet_name="CSAT")
    rc = pd.read_excel(SRC, sheet_name="Recontact")
    for d in (qa, cs, rc):
        d.columns = [str(c).strip().replace("\ufeff", "") for c in d.columns]

    qa_cr = qa["CR_correcta"].fillna(qa["CR_registrada"])

    hr("6.1 CR Lv4 — WHAT EACH TAB ACTUALLY CARRIES")
    print(f"  QA        : CR_registrada ({qa['CR_registrada'].nunique()} distinct), "
          f"CR_correcta ({qa['CR_correcta'].nunique()} distinct)")
    print(f"              coalesced CR_correcta->CR_registrada: {qa_cr.nunique()} distinct, "
          f"{int(qa_cr.isna().sum())} nulls")
    print(f"  CSAT      : 'CR Lv4' {cs['CR Lv4'].nunique()} distinct, {int(cs['CR Lv4'].isna().sum())} nulls")
    print(f"  Recontact : 'CR Lv4' {rc['CR Lv4'].nunique()} distinct, {int(rc['CR Lv4'].isna().sum())} nulls")
    print(f"\n  Rows where CR_correcta != CR_registrada in QA: "
          f"{int((qa['CR_correcta'] != qa['CR_registrada']).sum()):,} "
          f"({(qa['CR_correcta'] != qa['CR_registrada']).mean()*100:.2f}%)  "
          f"-> mis-tagging rate by agents")

    hr("6.2 KEY OVERLAP UNDER THREE NORMALISATION STRATEGIES")
    for label, fn in [("RAW (exact string)", k_raw),
                      ("MODEL norm_key (trim+collapse+casefold)", k_model),
                      ("STRONG (+ accents + punctuation)", k_strong)]:
        A = set(qa_cr.dropna().map(fn))
        B = set(cs["CR Lv4"].dropna().map(fn))
        C = set(rc["CR Lv4"].dropna().map(fn))
        print(f"\n  --- {label}")
        print(f"      distinct keys  QA={len(A)}  CSAT={len(B)}  Recontact={len(C)}  union={len(A|B|C)}")
        print(f"      QA n CSAT      = {len(A & B)}")
        print(f"      QA n Recontact = {len(A & C)}")
        print(f"      CSAT n Recon   = {len(B & C)}")
        print(f"      in all three   = {len(A & B & C)}")

    hr("6.3 WHAT DOES CASEFOLDING ACTUALLY RECOVER? (raw vs model key)")
    for name, s in [("QA", qa_cr), ("CSAT", cs["CR Lv4"]), ("Recontact", rc["CR Lv4"])]:
        raw = set(s.dropna().astype(str))
        norm = set(s.dropna().map(k_model))
        print(f"  {name:10s} raw distinct={len(raw):>4}  after casefold={len(norm):>4}  "
              f"collapsed={len(raw)-len(norm)}")
        # show the collapsed groups
        grp: dict = {}
        for v in raw:
            grp.setdefault(k_model(v), set()).add(v)
        multi = {k: v for k, v in grp.items() if len(v) > 1}
        for k, v in list(multi.items())[:10]:
            print(f"       '{k}' <- {sorted(v)}")

    hr("6.4 WHAT WOULD STRONGER NORMALISATION RECOVER ON TOP? (model key vs strong key)")
    allv = pd.concat([qa_cr.dropna(), cs["CR Lv4"].dropna(), rc["CR Lv4"].dropna()])
    grp2: dict = {}
    for v in set(allv.astype(str)):
        grp2.setdefault(k_strong(v), set()).add(k_model(v))
    extra = {k: v for k, v in grp2.items() if len(v) > 1}
    print(f"  Groups that STRONG normalisation would merge but the model keeps separate: {len(extra)}")
    for k, v in list(extra.items())[:25]:
        print(f"    '{k}' <- {sorted(v)}")
    if not extra:
        print("  NONE — casefold+trim is already sufficient for this dataset.")

    hr("6.5 UNMATCHED CR Lv4 — WHICH ONES AND HOW MUCH VOLUME DO THEY CARRY")
    A = set(qa_cr.dropna().map(k_model))
    B = set(cs["CR Lv4"].dropna().map(k_model))
    C = set(rc["CR Lv4"].dropna().map(k_model))
    qa_only = A - B - C
    print(f"  QA CR keys absent from BOTH CSAT and Recontact: {len(qa_only)} of {len(A)}")
    qk = qa_cr.map(k_model)
    print(f"    audits affected: {int(qk.isin(qa_only).sum()):,} of {len(qa):,} "
          f"({qk.isin(qa_only).mean()*100:.1f}%)")
    print(f"    sample: {sorted(qa_only)[:15]}")

    print(f"\n  QA keys present in CSAT: {len(A & B)}/{len(A)}  -> audits covered: "
          f"{int(qk.isin(B).sum()):,} ({qk.isin(B).mean()*100:.1f}%)")
    print(f"  QA keys present in Recontact: {len(A & C)}/{len(A)} -> audits covered: "
          f"{int(qk.isin(C).sum()):,} ({qk.isin(C).mean()*100:.1f}%)")
    tri = A & B & C
    print(f"  QA keys in all three: {len(tri)} -> audits covered: "
          f"{int(qk.isin(tri).sum()):,} ({qk.isin(tri).mean()*100:.1f}%)")

    cs_key = cs["CR Lv4"].map(k_model)
    rc_key = rc["CR Lv4"].map(k_model)
    print(f"\n  CSAT feedback volume on keys shared by all three: "
          f"{int(cs.loc[cs_key.isin(tri), 'Feedback CNT'].sum()):,} of "
          f"{int(cs['Feedback CNT'].sum()):,} "
          f"({cs.loc[cs_key.isin(tri),'Feedback CNT'].sum()/cs['Feedback CNT'].sum()*100:.1f}%)")
    print(f"  Recontact contacts on keys shared by all three: "
          f"{int(rc.loc[rc_key.isin(tri), 'Contacts'].sum()):,} of {int(rc['Contacts'].sum()):,} "
          f"({rc.loc[rc_key.isin(tri),'Contacts'].sum()/rc['Contacts'].sum()*100:.1f}%)")

    hr("6.6 LOB -> CR Lv1 -> CR Lv4 HIERARCHY RECONSTRUCTION")
    print(f"  LOB column exists in QA only: values = {qa['LOB'].unique().tolist()}")
    print(f"  CSAT has 'Business Line' = {cs['Business Line'].unique().tolist()} and "
          f"'Modality' = {cs['Modality'].unique().tolist()}")
    print(f"  Recontact has 'Modality' = {rc['Modality'].unique().tolist()} — no LOB/Business Line")
    print(f"\n  CR Lv1 availability:")
    print(f"    QA        : NO CR Lv1 column (only CR_registrada / CR_correcta = Lv4 grain)")
    print(f"    CSAT      : YES, {cs['CR Lv1'].nunique()} values -> {sorted(cs['CR Lv1'].unique())}")
    print(f"    Recontact : NO CR Lv1 column (starts at cr_lv2_name, {rc['cr_lv2_name'].nunique()} values)")

    # Can a Lv4 -> Lv1 map be built from CSAT and applied to QA / Recontact?
    lv1map = (cs.assign(k=cs_key)[["k", "CR Lv1"]].dropna()
              .groupby("k")["CR Lv1"].agg(lambda s: s.mode().iloc[0]))
    ambiguous = (cs.assign(k=cs_key).groupby("k")["CR Lv1"].nunique())
    print(f"\n  Lv4 -> Lv1 map derivable from CSAT: {len(lv1map)} keys")
    print(f"    keys mapping to MORE THAN ONE CR Lv1 (ambiguous): {int((ambiguous > 1).sum())}")
    if (ambiguous > 1).sum():
        for k in ambiguous[ambiguous > 1].index[:10]:
            print(f"       '{k}' -> {sorted(cs.loc[cs_key == k, 'CR Lv1'].unique())}")
    print(f"\n  Applying that map:")
    print(f"    QA audits that get a CR Lv1        : {int(qk.isin(lv1map.index).sum()):,} / {len(qa):,} "
          f"({qk.isin(lv1map.index).mean()*100:.1f}%)")
    print(f"    Recontact contacts that get Lv1    : "
          f"{int(rc.loc[rc_key.isin(lv1map.index),'Contacts'].sum()):,} / {int(rc['Contacts'].sum()):,} "
          f"({rc.loc[rc_key.isin(lv1map.index),'Contacts'].sum()/rc['Contacts'].sum()*100:.1f}%)")

    hr("6.7 WHAT THE EXPORTED dim_cr ACTUALLY DID")
    try:
        dc = read_model_sheet("dim_cr")
        print(f"  dim_cr rows: {len(dc):,}")
        print(f"  Coverage split: {dc['Coverage'].value_counts().to_dict()}")
        print(f"  In_QA={int(dc['In_QA'].sum())}  In_CSAT={int(dc['In_CSAT'].sum())}  "
              f"In_Recontact={int(dc['In_Recontact'].sum())}")
        print(f"  CR_Lv1 == 'Not mapped': {int((dc['CR_Lv1'] == 'Not mapped').sum())} of {len(dc)} "
              f"({(dc['CR_Lv1']=='Not mapped').mean()*100:.1f}%)")
        print(f"  CR_Lv2 == 'Not mapped': {int((dc['CR_Lv2'] == 'Not mapped').sum())}")
        print(f"  CR_Lv3 == 'Not mapped': {int((dc['CR_Lv3'] == 'Not mapped').sum())}")
        print(f"\n  Union of normalised keys computed independently: {len(A | B | C)}  "
              f"vs dim_cr rows {len(dc)}  match={len(A|B|C) == len(dc)}")
        # how many QA audits land on a 'Not mapped' Lv1
        notmapped = set(dc.loc[dc["CR_Lv1"] == "Not mapped", "CR_Key"])
        print(f"  QA audits whose CR has no CR Lv1: {int(qk.isin(notmapped).sum()):,} "
              f"({qk.isin(notmapped).mean()*100:.1f}%)")
        fa = read_model_sheet("fact_audit")
        print(f"  fact_audit CR_Key values not in dim_cr: "
              f"{len(set(fa['CR_Key']) - set(dc['CR_Key']))}")
    except Exception as e:
        print(f"  Could not read dim_cr: {e}")

    hr("6.8 CHANNEL KEY CONSISTENCY ACROSS TABS")
    print(f"  QA Channel            : {sorted(qa['Channel'].dropna().unique())}")
    print(f"  CSAT Consolidated Ch. : {sorted(cs['Consolidated Channel.'].dropna().unique())}")
    print(f"  Recontact std channel : {sorted(rc['standard_channel_name'].dropna().unique())}")
    a = set(qa["Channel"].dropna().map(k_model))
    b = set(cs["Consolidated Channel."].dropna().map(k_model))
    c = set(rc["standard_channel_name"].dropna().map(k_model))
    print(f"\n  After norm_key: QA={sorted(a)}")
    print(f"                  CSAT={sorted(b)}")
    print(f"  QA keys resolved in CSAT: {a <= b}   QA keys resolved in Recontact: {a <= c}")

    hr("6.9 COUNTRY CONSISTENCY")
    print(f"  QA Country      : {sorted(qa['Country'].dropna().unique())}")
    print(f"  CSAT Country    : {sorted(cs['Country Code'].dropna().unique())}")
    print(f"  Recontact region: {sorted(rc['region_name'].dropna().unique())}  <- no country")
    qc, cc = set(qa["Country"].dropna()), set(cs["Country Code"].dropna())
    print(f"  In QA not in CSAT: {sorted(qc - cc)}   In CSAT not in QA: {sorted(cc - qc)}")

    # ── 7. data quality ------------------------------------------------------
    hr("7.1 QA TAB — DUPLICATES")
    print(f"  Exact full-row duplicates: {int(qa.duplicated().sum()):,}")
    key_cols = ["fecha", "Evaluado", "Channel", "CR_correcta", "Fecha_fuente_interaccion", "Duration"]
    d = qa.duplicated(subset=key_cols, keep=False)
    print(f"  Duplicated on {key_cols}: {int(d.sum()):,} rows")
    if d.sum():
        print(qa.loc[d, key_cols + ["Score_end_user"]].sort_values(key_cols).head(12).to_string(index=False))

    hr("7.2 QA TAB — NULLS IN KEY FIELDS")
    for c in ["fecha", "Fecha_fuente_interaccion", "Evaluado", "Supervisor", "Channel",
              "Country", "LOB", "CR_registrada", "CR_correcta", "Tenure",
              "Fecha_ingreso_CSR", "Duration", "Week", "Type_of_audit"]:
        n = int(qa[c].isna().sum())
        flag = "  <-- " if n else ""
        print(f"  {c:28s} nulls={n:>5}{flag}")
    nullagent = qa[qa["Evaluado"].isna()]
    print(f"\n  Rows with a NULL agent: {len(nullagent)}")
    if len(nullagent):
        print(nullagent[["fecha", "Channel", "Supervisor", "Country", "Score_end_user"]].to_string(index=False))

    hr("7.3 QA TAB — DATES")
    f = pd.to_datetime(qa["fecha"])
    fi = pd.to_datetime(qa["Fecha_fuente_interaccion"])
    ing = pd.to_datetime(qa["Fecha_ingreso_CSR"])
    print(f"  fecha (audit date)  min={f.min()}  max={f.max()}  distinct={f.nunique()}")
    print(f"  Fecha_fuente_inter. min={fi.min()}  max={fi.max()}")
    print(f"  Fecha_ingreso_CSR   min={ing.min()}  max={ing.max()}  nulls={int(ing.isna().sum())}")
    print(f"\n  Audits where the interaction happened AFTER the audit date: "
          f"{int((fi > f).sum()):,}")
    print(f"  Audits where the agent's hire date is AFTER the audit date: "
          f"{int((ing > f).sum()):,}")
    lag = (f - fi).dt.days
    print(f"  Audit lag (days between interaction and audit): min={lag.min()} "
          f"max={lag.max()} median={lag.median()}")
    print(f"    negative lags: {int((lag < 0).sum())}   lag > 30 days: {int((lag > 30).sum())}")

    print(f"\n  Week column vs ISO week of 'fecha':")
    iso = "W" + f.dt.isocalendar()["week"].astype(int).astype(str)
    print(f"    matches: {int((qa['Week'].astype(str) == iso).sum()):,} / {len(qa):,}")
    mismatch = qa[qa["Week"].astype(str) != iso]
    if len(mismatch):
        print(mismatch[["fecha", "Week"]].assign(iso=iso[mismatch.index]).head(10).to_string(index=False))

    print(f"\n  Month column values: {qa['Month'].value_counts().to_dict()}  "
          f"<-- two spellings for the same month")

    print(f"\n  Date coverage per tab:")
    print(f"    QA        : {f.min().date()} .. {f.max().date()}  ({f.nunique()} distinct days)")
    print(f"    CSAT      : {pd.to_datetime(cs['pt(天)']).min().date()} .. "
          f"{pd.to_datetime(cs['pt(天)']).max().date()}")
    print(f"    Recontact : {pd.to_datetime(rc['Date(天)']).min().date()} .. "
          f"{pd.to_datetime(rc['Date(天)']).max().date()}")
    qa_days = set(f.dt.date)
    all_days = set(pd.date_range(f.min(), f.max()).date)
    print(f"    Days inside the QA window with NO audits: {len(all_days - qa_days)} "
          f"-> {sorted(all_days - qa_days)}")

    hr("7.4 QA TAB — SENTINEL / SUSPICIOUS VALUES")
    print(f"  Duration nulls={int(qa['Duration'].isna().sum())}  min={qa['Duration'].min()}  "
          f"max={qa['Duration'].max()}  zeros={int((qa['Duration'] == 0).sum())}  "
          f"negatives={int((qa['Duration'] < 0).sum())}")
    print(f"  Tenure raw values: {qa['Tenure'].value_counts().to_dict()}")
    print(f"  Type_of_audit    : {qa['Type_of_audit'].value_counts().to_dict()}")
    print(f"  Block_type       : {qa['Block_type'].value_counts().to_dict()}")
    print(f"  Requester        : {qa['Requester'].value_counts().to_dict()}")
    for c in ["CR_registrada", "CR_correcta", "SUB_CR_correcta"]:
        s = qa[c].dropna().astype(str)
        sentinel = s[s.str.strip().str.lower().isin(["other", "n/a", "na", "-", ".", "none", "non sub cr"])]
        print(f"  {c:20s} sentinel-ish values: {int(len(sentinel)):>5} "
              f"({sentinel.str.lower().value_counts().head(5).to_dict()})")
        ws = s[s != s.str.strip()]
        print(f"  {' ':20s} values with leading/trailing whitespace: {len(ws)}")

    hr("7.5 AGENT KEY CONSISTENCY (QA 'Evaluado' vs CSAT 'Agent name')")
    qa_agents = set(qa["Evaluado"].dropna().astype(str).str.strip())
    cs_agents = set(cs["Agent name"].dropna().astype(str).str.strip())
    print(f"  QA distinct agents  : {len(qa_agents)}")
    print(f"  CSAT distinct agents: {len(cs_agents)}")
    print(f"  Intersection        : {len(qa_agents & cs_agents)}")
    print(f"  Sample QA agents    : {sorted(qa_agents)[:5]}")
    print(f"  Sample CSAT agents  : {sorted(cs_agents)[:5]}")
    print(f"  -> agent-level joins between QA and CSAT are "
          f"{'POSSIBLE' if len(qa_agents & cs_agents) > 0 else 'IMPOSSIBLE'}")

    hr("7.6 THE 151 LIVE CHAT AUDITS WITH NO FAILS BUT Score_end_user = 0")
    cols = list(qa.columns)
    CHAT = [str(c) for c in cols[34:42]]
    PHONE = [str(c) for c in cols[22:34]]
    nf = qa[(qa["Channel"] == "Live Chat") & (qa[CHAT] == 1).sum(axis=1).eq(0)
            & (qa["Score_end_user"] == 0)]
    print(f"  Rows: {len(nf)}")
    print(f"  Type_of_audit: {nf['Type_of_audit'].value_counts().to_dict()}")
    print(f"  Block_type   : {nf['Block_type'].value_counts().to_dict()}")
    print(f"  Country      : {nf['Country'].value_counts().to_dict()}")
    print(f"  Attribute value distribution on their own (Live Chat) range:")
    vc: dict = {}
    for c in CHAT:
        for k, v in nf[c].value_counts().to_dict().items():
            vc[k] = vc.get(k, 0) + v
    print(f"     {vc}")
    print(f"  se_presento_insatisfaccion_en_la_interaccion_human: "
          f"{nf['se_presento_insatisfaccion_en_la_interaccion_human'].value_counts().to_dict()}")
    print(f"  Se_le_brindo_solucion_a_la_solicitud:")
    print(nf["Se_le_brindo_solucion_a_la_solicitud"].value_counts().to_string())
    print(f"\n  Compare with ALL Live Chat audits that have 0 fails and Score_end_user = 100:")
    ok = qa[(qa["Channel"] == "Live Chat") & (qa[CHAT] == 1).sum(axis=1).eq(0)
            & (qa["Score_end_user"] == 100)]
    print(f"  Rows: {len(ok)}   Type_of_audit: {ok['Type_of_audit'].value_counts().to_dict()}")
    print(ok["Se_le_brindo_solucion_a_la_solicitud"].value_counts().to_string())

    hr("8. CONTROL TOTALS — FINAL INDEPENDENT RESTATEMENT")
    def is_crit(c): return "critical" in c.lower()
    sc = []
    for _, r in qa.iterrows():
        at = PHONE if r["Channel"] == "Phone" else CHAT
        crit = any(r[c] == 1 for c in at if is_crit(c))
        nc = sum(1 for c in at if not is_crit(c) and r[c] == 1)
        sc.append(0.0 if crit else max(0.0, 100.0 - 10 * nc))
    qa_score = float(np.mean(sc))
    csat_v = (cs["Questionnaires With Star Level =4"].sum()
              + cs["Questionnaires With Star Level =5"].sum()) / cs["Feedback CNT"].sum() * 100
    rc_v = rc["Recontact Volume"].sum() / rc["Contacts"].sum() * 100
    print(f"  QA Score       claimed 94.14 | independent {qa_score:.4f} -> {round(qa_score,2)}  "
          f"{'MATCH' if round(qa_score,2)==94.14 else 'MISMATCH'}")
    print(f"  CSAT Score     claimed 79.95 | independent {csat_v:.4f} -> {round(csat_v,2)}  "
          f"{'MATCH' if round(csat_v,2)==79.95 else 'MISMATCH'}")
    print(f"  Recontact Rate claimed  5.83 | independent {rc_v:.4f} -> {round(rc_v,2)}  "
          f"{'MATCH' if round(rc_v,2)==5.83 else 'MISMATCH'}")
    try:
        ct = read_model_sheet("Control_Totals")
        print(f"\n  Control_Totals sheet in the exported model:")
        print(ct.to_string(index=False))
    except Exception as e:
        print(f"  Could not read Control_Totals: {e}")


if __name__ == "__main__":
    main()
