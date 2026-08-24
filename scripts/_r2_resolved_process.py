"""One-off: R² of audit slices (resolution × process) vs CSAT / recontact.

Reproduces dashboard association method: Pearson r via Series.corr,
R² via modules.kpis.association_r2, withheld if n < 5 shared units.
CR grain matches cr_level_metrics (QA_N >= 3). Agent grain uses
Agent_ID ↔ CSAT 'Agent name' casefold match.

Not official KPI correlation. Ecological at agent/CR/week grain.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from config import CONTROL_TOTALS, MIN_SAMPLE_SIZE, RANKING_CSAT_MIN_N
from modules.data_loader import load_all_data
from modules.kpis import (
    association_r2,
    avg_qa_score,
    channel_match,
    cr_correlation_summary,
    cr_level_metrics,
    iso_week_label,
    normalize_channel_label,
    overall_csat,
    recontact_rate,
)


def _assoc(x: pd.Series, y: pd.Series) -> dict:
    sub = pd.DataFrame({"x": x, "y": y}).dropna()
    n = int(len(sub))
    if n < 5:
        return {"n": n, "r": np.nan, "r2": np.nan, "sign": "—", "note": "n<5 withheld"}
    r = sub["x"].corr(sub["y"])
    r2 = association_r2(r)
    if pd.isna(r):
        return {"n": n, "r": np.nan, "r2": np.nan, "sign": "—", "note": "corr nan"}
    sign = "+" if r > 0 else ("0" if abs(r) < 1e-9 else "-")
    return {"n": n, "r": round(float(r), 3), "r2": r2, "sign": sign, "note": ""}


def _fmt(row: dict) -> str:
    if pd.isna(row["r2"]):
        return f"n={row['n']}  R²=—  ({row['note']})"
    return f"n={row['n']}  R²={row['r2']:.3f}  r={row['r']:+.3f}  sign={row['sign']}"


def slice_mask(audits: pd.DataFrame, name: str) -> pd.Series:
    s = audits["Solution_Provided"].astype("string").str.strip()
    p = audits["Process_Adherence"].astype("string").str.strip()
    if name == "resolved_followed":
        return s.eq("Resolved") & p.eq("Followed process")
    if name == "resolved_all":
        return s.eq("Resolved")
    if name == "not_resolved":
        return s.eq("Not resolved")
    if name == "not_resolved_no_process":
        return s.eq("Not resolved") & p.eq("Did not follow process")
    if name == "all":
        return pd.Series(True, index=audits.index)
    raise KeyError(name)


SLICES = [
    ("resolved_followed", "Resolved + followed process"),
    ("resolved_all", "Resolved (all)"),
    ("not_resolved", "Not resolved"),
    ("not_resolved_no_process", "Not resolved + did not follow process"),
    ("all", "All audits (baseline)"),
]


def cr_assoc(audits_slice: pd.DataFrame, csat: pd.DataFrame, rc: pd.DataFrame) -> dict:
    scatter = cr_level_metrics(audits_slice, csat, rc)
    tbl = cr_correlation_summary(scatter)
    out = {}
    for _, row in tbl.iterrows():
        pair = str(row["Pair"])
        n = int(row["N_CR"])
        r = row["Pearson_r"]
        r2 = row["R2"]
        if pd.isna(r):
            out[pair] = {"n": n, "r": np.nan, "r2": np.nan, "sign": "—", "note": "n<5 withheld" if n < 5 else "corr nan"}
        else:
            sign = "+" if r > 0 else ("0" if abs(r) < 1e-9 else "-")
            out[pair] = {"n": n, "r": float(r), "r2": float(r2), "sign": sign, "note": ""}
    return out


def agent_csat_frame(csat: pd.DataFrame, min_fb: int) -> pd.DataFrame:
    work = csat.copy()
    work["_ak"] = work["Agent name"].astype("string").str.strip()
    work = work[work["_ak"].notna() & work["_ak"].ne("") & work["_ak"].str.casefold().ne("nan")]
    work["_fb"] = pd.to_numeric(work["Feedback CNT"], errors="coerce").fillna(0)
    work["_sat"] = pd.to_numeric(work["Satisfied_CNT"], errors="coerce").fillna(0)
    work["_key"] = work["_ak"].str.casefold()
    g = work.groupby("_key", as_index=False).agg(
        Feedback=("_fb", "sum"), Satisfied=("_sat", "sum")
    )
    g = g[g["Feedback"] >= int(min_fb)]
    g["CSAT_Pct"] = np.where(g["Feedback"] > 0, g["Satisfied"] / g["Feedback"] * 100, np.nan)
    return g


def agent_qa_frame(audits: pd.DataFrame, min_n: int) -> pd.DataFrame:
    work = audits.copy()
    work["_key"] = work["Agent_ID"].astype("string").str.strip().str.casefold()
    g = work.groupby("_key", as_index=False).agg(
        QA_Score=("Score_Pct", "mean"), QA_N=("Audit_ID", "count")
    )
    return g[g["QA_N"] >= int(min_n)]


def week_assoc(audits_slice: pd.DataFrame, csat: pd.DataFrame, rc: pd.DataFrame) -> dict:
    if audits_slice.empty:
        return {"QA vs CSAT": _assoc(pd.Series(dtype=float), pd.Series(dtype=float)),
                "QA vs Recontact": _assoc(pd.Series(dtype=float), pd.Series(dtype=float))}
    qa = audits_slice.copy()
    qa["Week"] = qa["Week"].astype(str) if "Week" in qa.columns else iso_week_label(qa["Fecha"])
    qa_w = qa.groupby("Week", as_index=False).agg(QA_Score=("Score_Pct", "mean"), QA_N=("Audit_ID", "count"))

    cs = csat.copy()
    cs["Week"] = iso_week_label(cs["Fecha"])
    csat_w = cs.groupby("Week", as_index=False).agg(
        Satisfied=("Satisfied_CNT", "sum"), Feedback=("Feedback CNT", "sum")
    )
    csat_w["CSAT_Pct"] = np.where(
        csat_w["Feedback"] > 0, csat_w["Satisfied"] / csat_w["Feedback"] * 100, np.nan
    )

    rcw = rc.copy()
    rcw["Week"] = iso_week_label(rcw["Fecha"])
    rc_w = rcw.groupby("Week", as_index=False).agg(
        Recontacts=("Recontact Volume", "sum"), Contacts=("Contacts", "sum")
    )
    rc_w["Recontact_Rate"] = np.where(
        rc_w["Contacts"] > 0, rc_w["Recontacts"] / rc_w["Contacts"] * 100, np.nan
    )

    m = qa_w.merge(csat_w, on="Week", how="inner").merge(rc_w, on="Week", how="left")
    return {
        "QA vs CSAT": _assoc(m["QA_Score"], m["CSAT_Pct"]),
        "QA vs Recontact": _assoc(m["QA_Score"], m["Recontact_Rate"]),
        "weeks": sorted(m["Week"].astype(str).tolist()),
        "qa_n_by_week": dict(zip(qa_w["Week"].astype(str), qa_w["QA_N"].astype(int))),
    }


def filter_channel(df: pd.DataFrame, col: str, label: str) -> pd.DataFrame:
    if df is None or df.empty or col not in df.columns:
        return df.iloc[0:0] if df is not None else pd.DataFrame()
    return df[channel_match(df[col], label)]


def main() -> None:
    data = load_all_data()
    audits = data["fact_audits"].copy()
    csat = data["fact_csat"].copy()
    rc = data["fact_recontact"].copy()

    print("=" * 72)
    print("UNIVERSE CHECK (should match CONTROL_TOTALS)")
    print("=" * 72)
    qa_all = avg_qa_score(audits)
    csat_all = overall_csat(csat)
    rc_all = recontact_rate(rc)
    print(f"QA {qa_all:.2f}%  n={len(audits):,}  (control {CONTROL_TOTALS['qa']} · {CONTROL_TOTALS['evaluations']})")
    fb = int(pd.to_numeric(csat["Feedback CNT"], errors="coerce").fillna(0).sum())
    print(f"CSAT {csat_all:.2f}%  surveys={fb:,}  (control {CONTROL_TOTALS['csat']} · {CONTROL_TOTALS['surveys']})")
    contacts = int(pd.to_numeric(rc["Contacts"], errors="coerce").fillna(0).sum())
    print(f"Recontact {rc_all:.2f}%  contacts={contacts:,}  (control {CONTROL_TOTALS['recontact']} · {CONTROL_TOTALS['contacts']})")

    print("\n" + "=" * 72)
    print("COLUMNS")
    print("=" * 72)
    for col in ("Solution_Provided", "Process_Adherence", "Auditor_Outcome", "Score_Pct",
                "Agent_ID", "CR_Lv4", "Channel", "Week", "Fecha"):
        print(f"  audits.{col}: {'YES' if col in audits.columns else 'NO'}")
    print(f"  csat Agent name: {'YES' if 'Agent name' in csat.columns else 'NO'}")
    print(f"  csat CR_Lv4: {'YES' if 'CR_Lv4' in csat.columns else 'NO'}")
    print(f"  csat Channel: {'YES' if 'Channel' in csat.columns else 'NO'}")
    rc_ch = "standard_channel_name" if "standard_channel_name" in rc.columns else (
        "Channel" if "Channel" in rc.columns else None
    )
    print(f"  rc channel col: {rc_ch}")
    print(f"  rc has agent: {any('agent' in c.lower() for c in rc.columns)}")
    print(f"  rc columns sample: {list(rc.columns)[:20]}")

    print("\n" + "=" * 72)
    print("CROSSTAB Solution_Provided x Process_Adherence")
    print("=" * 72)
    ct = pd.crosstab(
        audits["Solution_Provided"].astype("string").str.strip().fillna("(null)"),
        audits["Process_Adherence"].astype("string").str.strip().fillna("(null)"),
        margins=True,
    )
    print(ct.to_string())
    print("\nAuditor_Outcome counts:")
    print(audits["Auditor_Outcome"].astype("string").str.strip().value_counts(dropna=False).to_string())

    s = audits["Solution_Provided"].astype("string").str.strip()
    p = audits["Process_Adherence"].astype("string").str.strip()
    resolved = s.eq("Resolved")
    print("\nProcess_Adherence on Resolved rows:")
    print(p[resolved].value_counts(dropna=False).to_string())
    blank_res = int((resolved & ~p.isin(["Followed process", "Did not follow process", "Abandoned"])).sum())
    print(f"Resolved with process not followed/did-not-follow: {blank_res}")
    print(f"Resolved AND Followed process: {int((resolved & p.eq('Followed process')).sum())}")
    print(f"Resolved AND Did not follow process: {int((resolved & p.eq('Did not follow process')).sum())}")
    print(f"Not resolved AND Followed process: {int((s.eq('Not resolved') & p.eq('Followed process')).sum())}")
    print(f"Not resolved AND Did not follow process: {int((s.eq('Not resolved') & p.eq('Did not follow process')).sum())}")
    print(f"Abandoned: {int(s.eq('Abandoned').sum())}")

    print("\nMean official QA (Score_Pct) by slice:")
    for key, label in SLICES:
        m = slice_mask(audits, key)
        n = int(m.sum())
        qa = float(pd.to_numeric(audits.loc[m, "Score_Pct"], errors="coerce").mean()) if n else np.nan
        print(f"  {label:42s}  n={n:5d}  QA={qa:6.2f}%" if n else f"  {label:42s}  n=0")

    print("\nBy channel × Solution_Provided:")
    audits["_ch"] = audits["Channel"].map(normalize_channel_label)
    print(pd.crosstab(audits["_ch"], s.fillna("(null)"), margins=True).to_string())

    print("\n" + "=" * 72)
    print("GRAIN: CR Lv4  (cr_level_metrics QA_N>=3, R² if n>=5 shared names)")
    print("CSAT/recontact are the SAME CR's official ratio-of-sums — not sliced.")
    print("QA_Score is mean Score_Pct of the AUDIT SLICE only.")
    print("=" * 72)
    for key, label in SLICES:
        m = slice_mask(audits, key)
        sub = audits.loc[m]
        print(f"\n-- {label}  (audits in slice={len(sub):,}) --")
        if sub.empty:
            print("  empty slice")
            continue
        assoc = cr_assoc(sub, csat, rc)
        for pair in ("QA vs CSAT", "QA vs Recontact"):
            print(f"  {pair:20s}  {_fmt(assoc.get(pair, {'n': 0, 'r': np.nan, 'r2': np.nan, 'sign': '—', 'note': 'missing'}))}")

    print("\n" + "=" * 72)
    print("GRAIN: CR Lv4 × Channel (Phone-only vs Chat-only; do not mix official QA)")
    print("=" * 72)
    for ch in ("Phone", "Live Chat"):
        a_ch = filter_channel(audits, "Channel", ch)
        c_ch = filter_channel(csat, "Channel", ch)
        r_ch = filter_channel(rc, rc_ch, ch) if rc_ch else rc.iloc[0:0]
        print(f"\n### Channel = {ch}  audits={len(a_ch):,}  csat rows={len(c_ch):,}  rc rows={len(r_ch):,}")
        for key, label in SLICES:
            sub = a_ch.loc[slice_mask(a_ch, key)]
            if sub.empty:
                print(f"  {label:42s}  empty")
                continue
            assoc = cr_assoc(sub, c_ch, r_ch)
            qa_cs = _fmt(assoc.get("QA vs CSAT", {"n": 0, "r": np.nan, "r2": np.nan, "sign": "—", "note": "missing"}))
            qa_rc = _fmt(assoc.get("QA vs Recontact", {"n": 0, "r": np.nan, "r2": np.nan, "sign": "—", "note": "missing"}))
            print(f"  {label:42s}  CSAT {qa_cs}  |  RC {qa_rc}")

    print("\n" + "=" * 72)
    print("GRAIN: Agent  (QA Agent_ID ↔ CSAT 'Agent name'; recontact HAS NO AGENT)")
    print(f"min QA n = {MIN_SAMPLE_SIZE} (roster); min CSAT Feedback = {RANKING_CSAT_MIN_N}")
    print("Also shown: looser min QA n=3 / min CSAT fb=1 (join floor only).")
    print("=" * 72)
    csat_strict = agent_csat_frame(csat, RANKING_CSAT_MIN_N)
    csat_loose = agent_csat_frame(csat, 1)
    for min_qa, csat_ag, tag in (
        (MIN_SAMPLE_SIZE, csat_strict, f"strict QA>={MIN_SAMPLE_SIZE} CSAT>={RANKING_CSAT_MIN_N}"),
        (3, csat_loose, "loose QA>=3 CSAT>=1"),
    ):
        print(f"\n### Agent join ({tag})")
        for key, label in SLICES:
            sub = audits.loc[slice_mask(audits, key)]
            if sub.empty:
                print(f"  {label:42s}  empty")
                continue
            qa_ag = agent_qa_frame(sub, min_qa)
            mrg = qa_ag.merge(csat_ag, on="_key", how="inner")
            row = _assoc(mrg["QA_Score"], mrg["CSAT_Pct"])
            print(f"  {label:42s}  vs CSAT  {_fmt(row)}  (agents in slice w/ min n={len(qa_ag)})")

    print("\n" + "=" * 72)
    print("GRAIN: Week  (ISO week; n typically ~4 → R² withheld)")
    print("=" * 72)
    for key, label in SLICES:
        sub = audits.loc[slice_mask(audits, key)]
        w = week_assoc(sub, csat, rc)
        extra = ""
        if "weeks" in w:
            extra = f"  weeks={w['weeks']}"
        print(f"  {label:42s}  CSAT {_fmt(w['QA vs CSAT'])}  |  RC {_fmt(w['QA vs Recontact'])}{extra}")

    print("\n" + "=" * 72)
    print("GRAIN: Channel as 2-point series — NOT computed (n=2 < 5).")
    print("Use CR-within-channel above instead.")
    print("=" * 72)

    # How much of baseline CR QA↔CSAT is this slice?
    print("\n" + "=" * 72)
    print("SLICE SHARE OF AUDITS (for interpreting ecological R²)")
    print("=" * 72)
    n_all = len(audits)
    for key, label in SLICES:
        n = int(slice_mask(audits, key).sum())
        print(f"  {label:42s}  {n:5d}  ({n / n_all * 100:5.1f}%)")


if __name__ == "__main__":
    main()
