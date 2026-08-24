"""Resolved vs CSAT: ecological contrast (not QA-of-slice vs CSAT).

X = auditor resolution RATE (and process-followed RATE).
Y = official CSAT of the same CR / agent / channel.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from modules.data_loader import load_all_data
from modules.kpis import (
    association_r2,
    auditor_resolution_summary,
    avg_qa_score,
    channel_match,
    cr_level_metrics,
    normalize_channel_label,
    overall_csat,
    recontact_rate,
)

PY = r"C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe"


def _assoc(x: pd.Series, y: pd.Series) -> dict:
    sub = pd.DataFrame({"x": x, "y": y}).dropna()
    n = int(len(sub))
    if n < 5:
        return {"n": n, "r": np.nan, "r2": np.nan, "sign": "—", "note": "n<5 withheld"}
    r = sub["x"].corr(sub["y"])
    r2 = association_r2(r)
    if pd.isna(r):
        return {"n": n, "r": np.nan, "r2": np.nan, "sign": "—", "note": "corr nan"}
    sign = "+" if float(r) > 0 else ("0" if abs(float(r)) < 1e-9 else "-")
    return {
        "n": n,
        "r": round(float(r), 3),
        "r2": r2,
        "sign": sign,
        "note": "",
        "x_mean": round(float(sub["x"].mean()), 2),
        "y_mean": round(float(sub["y"].mean()), 2),
    }


def _fmt(row: dict) -> str:
    if pd.isna(row.get("r2")):
        return f"n={row['n']}  R²=—  ({row.get('note', '')})"
    return f"n={row['n']}  R²={row['r2']:.3f}  r={row['r']:+.3f}  sign={row['sign']}"


def _halves(df: pd.DataFrame, xcol: str, ycol: str, wcol: str | None = None) -> dict:
    sub = df[[xcol, ycol] + ([wcol] if wcol else [])].dropna()
    n = int(len(sub))
    if n < 4:
        return {"n": n, "note": "too few for halves"}
    med = float(sub[xcol].median())
    lo = sub[sub[xcol] <= med]
    hi = sub[sub[xcol] > med]
    out = {
        "n": n,
        "median_x": round(med, 2),
        "n_lo": int(len(lo)),
        "n_hi": int(len(hi)),
        "mean_y_lo": round(float(lo[ycol].mean()), 2) if len(lo) else np.nan,
        "mean_y_hi": round(float(hi[ycol].mean()), 2) if len(hi) else np.nan,
    }
    if wcol and wcol in sub.columns:
        def wmean(g):
            w = pd.to_numeric(g[wcol], errors="coerce").fillna(0)
            if w.sum() <= 0:
                return np.nan
            return float(np.average(g[ycol], weights=w))
        out["wmean_y_lo"] = round(wmean(lo), 2) if len(lo) else np.nan
        out["wmean_y_hi"] = round(wmean(hi), 2) if len(hi) else np.nan
    out["delta_mean"] = round(out["mean_y_hi"] - out["mean_y_lo"], 2) if pd.notna(out["mean_y_hi"]) else np.nan
    return out


def _tertiles(df: pd.DataFrame, xcol: str, ycol: str) -> dict:
    sub = df[[xcol, ycol]].dropna()
    n = int(len(sub))
    if n < 9:
        return {"n": n, "note": "too few for tertiles"}
    try:
        bins = pd.qcut(sub[xcol], 3, labels=["T1_low", "T2", "T3_high"], duplicates="drop")
    except ValueError:
        return {"n": n, "note": "qcut failed (ties)"}
    g = sub.groupby(bins, observed=True)[ycol].agg(["mean", "count"])
    out = {"n": n}
    for lab, row in g.iterrows():
        out[f"{lab}_n"] = int(row["count"])
        out[f"{lab}_csat"] = round(float(row["mean"]), 2)
    if "T1_low_csat" in out and "T3_high_csat" in out:
        out["delta_T3_T1"] = round(out["T3_high_csat"] - out["T1_low_csat"], 2)
    return out


def filter_ch(df: pd.DataFrame, col: str, label: str) -> pd.DataFrame:
    if df is None or df.empty or col not in df.columns:
        return df.iloc[0:0] if df is not None else pd.DataFrame()
    return df[channel_match(df[col], label)].copy()


def rc_channel_col(rc: pd.DataFrame) -> str | None:
    for c in ("standard_channel_name", "Channel", "channel"):
        if c in rc.columns:
            return c
    return None


def process_filled(p: pd.Series) -> pd.Series:
    s = p.astype("string").str.strip()
    return s.isin(["Followed process", "Did not follow process"])


def resolution_frame(audits: pd.DataFrame, grain: str) -> pd.DataFrame:
    """One row per CR or agent with resolution / process rates among assessed."""
    work = audits.copy()
    if grain == "cr":
        work["_key"] = work["CR_Lv4"].astype(str).str.strip().str.casefold()
        name_col = "CR_Lv4"
    else:
        work["_key"] = work["Agent_ID"].astype("string").str.strip().str.casefold()
        name_col = "Agent_ID"
    s = work["Solution_Provided"].astype("string").str.strip()
    p = work["Process_Adherence"].astype("string").str.strip()
    assessed = s.isin(["Resolved", "Not resolved"])
    followed_filled = process_filled(p)
    work["_resolved"] = (s.eq("Resolved") & assessed).astype(int)
    work["_assessed"] = assessed.astype(int)
    work["_followed"] = (p.eq("Followed process") & followed_filled).astype(int)
    work["_proc_n"] = followed_filled.astype(int)
    work["_good"] = (s.eq("Resolved") & p.eq("Followed process") & assessed).astype(int)
    work["_qa"] = pd.to_numeric(work["Score_Pct"], errors="coerce")
    g = work.groupby("_key", as_index=False).agg(
        Name=(name_col, "first"),
        QA_N=("Audit_ID", "count"),
        QA_Score=("_qa", "mean"),
        n_assessed=("_assessed", "sum"),
        n_resolved=("_resolved", "sum"),
        n_proc=("_proc_n", "sum"),
        n_followed=("_followed", "sum"),
        n_good=("_good", "sum"),
    )
    g["pct_resolved"] = np.where(g["n_assessed"] > 0, g["n_resolved"] / g["n_assessed"] * 100, np.nan)
    g["pct_followed"] = np.where(g["n_proc"] > 0, g["n_followed"] / g["n_proc"] * 100, np.nan)
    g["pct_good"] = np.where(g["n_assessed"] > 0, g["n_good"] / g["n_assessed"] * 100, np.nan)
    return g


def csat_cr_frame(csat: pd.DataFrame) -> pd.DataFrame:
    work = csat.copy()
    work["_key"] = work["CR_Lv4"].astype(str).str.strip().str.casefold()
    g = work.groupby("_key", as_index=False).agg(
        Feedback=("Feedback CNT", "sum"),
        Satisfied=("Satisfied_CNT", "sum"),
    )
    g["CSAT_Pct"] = np.where(g["Feedback"] > 0, g["Satisfied"] / g["Feedback"] * 100, np.nan)
    return g


def csat_agent_frame(csat: pd.DataFrame, min_fb: int) -> pd.DataFrame:
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


def merge_and_report(res: pd.DataFrame, csat_g: pd.DataFrame, min_qa: int, tag: str) -> pd.DataFrame:
    m = res.merge(csat_g, on="_key", how="inner")
    m = m[m["QA_N"] >= int(min_qa)]
    print(f"\n--- {tag}  joined n={len(m)} (after QA_N>={min_qa}) ---")
    if m.empty:
        print("  empty")
        return m
    for xcol, xlabel in (
        ("pct_resolved", "Resolution rate vs CSAT"),
        ("pct_followed", "Process-followed rate vs CSAT"),
        ("pct_good", "Resolved+followed % of assessed vs CSAT"),
    ):
        row = _assoc(m[xcol], m["CSAT_Pct"])
        print(f"  {xlabel:44s}  {_fmt(row)}")
        h = _halves(m, xcol, "CSAT_Pct", "Feedback" if "Feedback" in m.columns else None)
        t = _tertiles(m, xcol, "CSAT_Pct")
        if "mean_y_lo" in h:
            extra = ""
            if "wmean_y_lo" in h:
                extra = f"  | survey-weighted CSAT lo={h['wmean_y_lo']} hi={h['wmean_y_hi']}"
            print(
                f"    halves (median {xcol}={h['median_x']}): "
                f"low n={h['n_lo']} CSAT={h['mean_y_lo']}  vs  "
                f"high n={h['n_hi']} CSAT={h['mean_y_hi']}  Δ={h['delta_mean']}{extra}"
            )
        if "T1_low_csat" in t:
            print(
                f"    tertiles: T1={t['T1_low_csat']} (n={t['T1_low_n']})  "
                f"T2={t.get('T2_csat', '—')} (n={t.get('T2_n', '—')})  "
                f"T3={t['T3_high_csat']} (n={t['T3_high_n']})  ΔT3-T1={t.get('delta_T3_T1')}"
            )
        elif t.get("note"):
            print(f"    tertiles: {t['note']} n={t['n']}")
    # Also QA of these groups as side note
    qa_row = _assoc(m["pct_resolved"], m["QA_Score"])
    print(f"  (side) Resolution rate vs official QA           {_fmt(qa_row)}")
    if "Name" in m.columns and tag.endswith(" CR"):
        show = m[["Name", "QA_N", "n_assessed", "pct_resolved", "CSAT_Pct", "Feedback"]].copy()
        show = show.sort_values("pct_resolved")
        if len(show) > 12:
            print("  lowest-resolution CRs:")
            print(show.head(6).to_string(index=False, max_colwidth=48))
            print("  highest-resolution CRs:")
            print(show.tail(6).to_string(index=False, max_colwidth=48))
        else:
            print("  points (low→high resolution):")
            print(show.to_string(index=False, max_colwidth=48))
    return m


def look_like_id(name: str) -> bool:
    n = name.lower()
    keys = (
        "ticket", "case", "interaction", "session", "contact_id", "contact id",
        "id_ticket", "id_caso", "id_interaccion", "id_interaction",
        "unique_id", "uuid", "survey_id", "audit_id", "worksheet",
        "record_id", "row_id", "conversation", "chat_id", "call_id",
        "order_id", "trip_id", "uid",
    )
    return any(k in n for k in keys)


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    data = load_all_data()
    audits = data["fact_audits"].copy()
    csat = data["fact_csat"].copy()
    rc = data["fact_recontact"].copy()
    rc_ch = rc_channel_col(rc)

    print("=" * 78)
    print("1. JOIN KEYS: can an audit attach to that customer's CSAT?")
    print("=" * 78)
    print("\nfact_audits columns:")
    print(" ", list(audits.columns))
    print("\nfact_csat columns:")
    print(" ", list(csat.columns))
    print("\nfact_recontact columns:")
    print(" ", list(rc.columns))

    a_ids = [c for c in audits.columns if look_like_id(c)]
    c_ids = [c for c in csat.columns if look_like_id(c)]
    print("\nID-like audit cols:", a_ids or "(none besides Audit_ID synthetic)")
    print("ID-like csat cols:", c_ids or "(none)")

    print("\nSample audits row (non-score fields):")
    skip = [c for c in audits.columns if str(c).startswith("atributo_") or "Score" in str(c)]
    show_a = [c for c in audits.columns if c not in skip][:40]
    print(audits[show_a].head(2).to_string())
    print("\nSample csat row:")
    print(csat.head(2).to_string()[:4000])

    print("\nCSAT grain check: Feedback CNT stats")
    fb = pd.to_numeric(csat["Feedback CNT"], errors="coerce")
    print(f"  rows={len(csat):,}  Feedback sum={int(fb.sum()):,}  "
          f"mean/row={fb.mean():.2f}  median={fb.median():.1f}  "
          f"pct rows with Feedback==1={(fb.eq(1).mean()*100):.1f}%")
    print("  CSAT is already aggregated (agent × CR × channel × date × stars). "
          "No ticket/case/interaction id on either fact.")

    shared = set(audits.columns) & set(csat.columns)
    print("\nShared column names:", sorted(shared))

    # date+agent overlap
    if "Fecha" in audits.columns and "Fecha" in csat.columns:
        a_dates = pd.to_datetime(audits["Fecha"], errors="coerce").dt.normalize()
        c_dates = pd.to_datetime(csat["Fecha"], errors="coerce").dt.normalize()
        print(f"  audit date range: {a_dates.min()} .. {a_dates.max()}")
        print(f"  csat date range:  {c_dates.min()} .. {c_dates.max()}")

    a_agents = set(audits["Agent_ID"].astype(str).str.strip().str.casefold())
    c_agents = set(csat["Agent name"].astype(str).str.strip().str.casefold()) if "Agent name" in csat.columns else set()
    print(f"  unique audit agents={len(a_agents)}  csat agents={len(c_agents)}  "
          f"name overlap={len(a_agents & c_agents)}")

    print("\nCONCLUSION: no ticket/case/interaction id on either fact.")
    print("Cannot say 'this resolved ticket's survey was 5 stars'.")
    print("All CSAT contrasts below are ecological (channel / CR / agent)")
    print("unless a fuzzy date+agent(+CR+channel) join is 1:1 enough — checked next.")

    print("\n--- Fuzzy grain: Fecha + Agent + Channel + CR_Lv4 ---")
    a2 = audits.copy()
    a2["_d"] = pd.to_datetime(a2["Fecha"], errors="coerce").dt.normalize()
    a2["_ag"] = a2["Agent_ID"].astype(str).str.strip().str.casefold()
    a2["_ch"] = a2["Channel"].map(normalize_channel_label)
    a2["_cr"] = a2["CR_Lv4"].astype(str).str.strip().str.casefold()
    a2["_k4"] = a2["_d"].astype(str) + "|" + a2["_ag"] + "|" + a2["_ch"] + "|" + a2["_cr"]
    a2["_k3"] = a2["_d"].astype(str) + "|" + a2["_ag"] + "|" + a2["_ch"]
    a2["_k2"] = a2["_d"].astype(str) + "|" + a2["_ag"]

    c2 = csat.copy()
    c2["_d"] = pd.to_datetime(c2["Fecha"], errors="coerce").dt.normalize()
    c2["_ag"] = c2["Agent name"].astype(str).str.strip().str.casefold()
    c2["_ch"] = c2["Channel"].map(normalize_channel_label)
    c2["_cr"] = c2["CR_Lv4"].astype(str).str.strip().str.casefold()
    c2["_k4"] = c2["_d"].astype(str) + "|" + c2["_ag"] + "|" + c2["_ch"] + "|" + c2["_cr"]
    c2["_k3"] = c2["_d"].astype(str) + "|" + c2["_ag"] + "|" + c2["_ch"]
    c2["_k2"] = c2["_d"].astype(str) + "|" + c2["_ag"]
    c2["_fb"] = pd.to_numeric(c2["Feedback CNT"], errors="coerce").fillna(0)
    c2["_sat"] = pd.to_numeric(c2["Satisfied_CNT"], errors="coerce").fillna(0)
    c2["_s4"] = pd.to_numeric(c2["Questionnaires With Star Level =4"], errors="coerce").fillna(0)
    c2["_s5"] = pd.to_numeric(c2["Questionnaires With Star Level =5"], errors="coerce").fillna(0)

    def grain_report(label, a_key, c_key):
        a_vc = a2[a_key].value_counts()
        c_vc = c2[c_key].value_counts()
        shared = set(a_vc.index) & set(c_vc.index)
        a_only1 = int((a_vc.loc[list(shared)] == 1).sum()) if shared else 0
        c_only1 = int((c_vc.loc[list(shared)] == 1).sum()) if shared else 0
        both1 = 0
        if shared:
            both1 = int(((a_vc.loc[list(shared)] == 1) & (c_vc.loc[list(shared)] == 1)).sum())
        print(f"  {label}")
        print(f"    audit keys={a_vc.size:,}  csat keys={c_vc.size:,}  overlap={len(shared):,}")
        print(f"    among overlap: audit 1:1={a_only1:,}  csat 1:1={c_only1:,}  both 1:1={both1:,}")
        print(f"    audit keys with >1 row among overlap: {int((a_vc.loc[list(shared)] > 1).sum()) if shared else 0}")
        print(f"    csat keys with >1 row among overlap: {int((c_vc.loc[list(shared)] > 1).sum()) if shared else 0}")
        return shared, both1

    grain_report("date+agent", "_k2", "_k2")
    grain_report("date+agent+channel", "_k3", "_k3")
    shared4, both1_4 = grain_report("date+agent+channel+CR", "_k4", "_k4")

    # Strict 1:1 date+agent+channel+CR join among assessed audits
    a_vc4 = a2["_k4"].value_counts()
    c_vc4 = c2["_k4"].value_counts()
    one_one = (a_vc4 == 1) & (c_vc4.reindex(a_vc4.index).fillna(0) == 1)
    keys_11 = set(a_vc4.index[one_one.fillna(False)])
    a11 = a2[a2["_k4"].isin(keys_11)].copy()
    c11 = (
        c2[c2["_k4"].isin(keys_11)]
        .groupby("_k4", as_index=False)
        .agg(Feedback=("_fb", "sum"), Satisfied=("_sat", "sum"), s4=("_s4", "sum"), s5=("_s5", "sum"))
    )
    j = a11.merge(c11, on="_k4", how="inner")
    s = j["Solution_Provided"].astype("string").str.strip()
    assessed = j[s.isin(["Resolved", "Not resolved"])].copy()
    print(f"\n  Strict 1:1 date+agent+channel+CR joins: {len(j):,} audits")
    print(f"  of which assessed (Resolved/Not resolved): {len(assessed):,}")
    print(f"  share of all audits: {len(j)/len(audits)*100:.1f}%")
    if len(assessed):
        def slice_csat(mask, label):
            sub = assessed.loc[mask]
            fb = float(sub["Feedback"].sum())
            sat = float(sub["Satisfied"].sum())
            csat_pct = sat / fb * 100 if fb else np.nan
            qa = float(pd.to_numeric(sub["Score_Pct"], errors="coerce").mean()) if len(sub) else np.nan
            print(
                f"    {label:22s} n={len(sub):5d}  surveys={int(fb):5d}  "
                f"CSAT={csat_pct:6.2f}  QA={qa:6.2f}"
            )
        slice_csat(assessed["Solution_Provided"].astype("string").str.strip().eq("Resolved"), "Resolved")
        slice_csat(assessed["Solution_Provided"].astype("string").str.strip().eq("Not resolved"), "Not resolved")
        p = assessed["Process_Adherence"].astype("string").str.strip()
        slice_csat(
            assessed["Solution_Provided"].astype("string").str.strip().eq("Resolved") & p.eq("Followed process"),
            "Resolved+followed",
        )
        for ch in ("Phone", "Live Chat"):
            subch = assessed[assessed["_ch"] == ch]
            if subch.empty:
                continue
            print(f"    -- 1:1 join within {ch} n={len(subch)}")
            for lab, msk in (
                ("Resolved", subch["Solution_Provided"].astype("string").str.strip().eq("Resolved")),
                ("Not resolved", subch["Solution_Provided"].astype("string").str.strip().eq("Not resolved")),
            ):
                ss = subch.loc[msk]
                fb = float(ss["Feedback"].sum())
                sat = float(ss["Satisfied"].sum())
                pct = sat / fb * 100 if fb else float("nan")
                print(f"       {lab:16s} n={len(ss):3d}  CSAT={pct:6.2f}")
        print("  CAVEAT: even 1:1 on date+agent+channel+CR is NOT ticket-level.")
        print("  Same agent can handle several customers on the same CR the same day;")
        print("  the survey is not proven to be the audited interaction.")
        print("  n is a convenience sample of unique keys, biased toward low-volume CRs.")

    print("\n" + "=" * 78)
    print("2. CHANNEL MIX: resolution rate vs official CSAT / QA / recontact")
    print("=" * 78)
    rows = []
    for ch in ("Phone", "Live Chat"):
        a = filter_ch(audits, "Channel", ch)
        c = filter_ch(csat, "Channel", ch)
        r = filter_ch(rc, rc_ch, ch) if rc_ch else rc.iloc[0:0]
        res = auditor_resolution_summary(a)
        p = a["Process_Adherence"].astype("string").str.strip() if "Process_Adherence" in a.columns else pd.Series(dtype="string")
        filled = process_filled(p)
        n_fol = int((p.eq("Followed process") & filled).sum())
        n_fill = int(filled.sum())
        pct_fol = round(n_fol / n_fill * 100, 2) if n_fill else None
        rows.append({
            "Channel": ch,
            "n_audits": int(len(a)),
            "n_assessed": res["n_assessed"],
            "pct_resolved": res["rate"],
            "pct_followed": pct_fol,
            "n_proc_filled": n_fill,
            "QA": round(float(avg_qa_score(a)), 2) if len(a) else None,
            "CSAT": round(float(overall_csat(c)), 2) if len(c) else None,
            "CSAT_surveys": int(pd.to_numeric(c["Feedback CNT"], errors="coerce").fillna(0).sum()) if len(c) else 0,
            "Recontact": round(float(recontact_rate(r)), 2) if len(r) else None,
            "RC_contacts": int(pd.to_numeric(r["Contacts"], errors="coerce").fillna(0).sum()) if len(r) and "Contacts" in r.columns else 0,
        })
    tbl = pd.DataFrame(rows)
    print(tbl.to_string(index=False))
    print("\nPooled (all channels in snapshot):")
    res_all = auditor_resolution_summary(audits)
    print(f"  audits={len(audits):,}  assessed={res_all['n_assessed']:,}  "
          f"% resolved={res_all['rate']}  QA={avg_qa_score(audits):.2f}  "
          f"CSAT={overall_csat(csat):.2f}  RC={recontact_rate(rc):.2f}")

    print("\n" + "=" * 78)
    print("3–4. ECOLOGICAL: resolution RATE / process RATE vs official CSAT")
    print("Floors: CR QA_N>=3; Agent QA_N>=5 and CSAT surveys>=20")
    print("X = % Resolved among assessed (Abandoned excluded from denom)")
    print("Y = official CSAT of that CR/agent (ratio of sums) — NOT sliced by resolution")
    print("=" * 78)

    csat_cr = csat_cr_frame(csat)
    csat_ag = csat_agent_frame(csat, 20)

    print("\n### GRAIN = CR Lv4")
    res_cr = resolution_frame(audits, "cr")
    merge_and_report(res_cr, csat_cr, 3, "Pooled CR")
    for ch in ("Phone", "Live Chat"):
        a = filter_ch(audits, "Channel", ch)
        c = filter_ch(csat, "Channel", ch)
        merge_and_report(resolution_frame(a, "cr"), csat_cr_frame(c), 3, f"{ch} CR")

    print("\n### GRAIN = Agent (Agent_ID ↔ Agent name, casefold)")
    res_ag = resolution_frame(audits, "agent")
    merge_and_report(res_ag, csat_ag, 5, "Pooled Agent")
    for ch in ("Phone", "Live Chat"):
        a = filter_ch(audits, "Channel", ch)
        c = filter_ch(csat, "Channel", ch)
        merge_and_report(
            resolution_frame(a, "agent"),
            csat_agent_frame(c, 20),
            5,
            f"{ch} Agent",
        )

    print("\n" + "=" * 78)
    print("5. SIDE NOTE — official QA (Score_Pct) of resolution slices")
    print("This is auditor QA, NOT customer CSAT.")
    print("=" * 78)
    res = auditor_resolution_summary(audits)
    print(f"  Resolved     n={res['n_resolved']:,}  QA={res['qa_resolved']}")
    print(f"  Not resolved n={res['n_not_resolved']:,}  QA={res['qa_not_resolved']}")
    print(f"  Abandoned    n={res['n_abandoned']:,}  QA={res['qa_abandoned']}")
    print(f"  Assessed     n={res['n_assessed']:,}  QA={res['qa_assessed']}")
    for ch in ("Phone", "Live Chat"):
        a = filter_ch(audits, "Channel", ch)
        rch = auditor_resolution_summary(a)
        print(f"  {ch}: resolved QA={rch['qa_resolved']} (n={rch['n_resolved']})  "
              f"not resolved QA={rch['qa_not_resolved']} (n={rch['n_not_resolved']})")

    # Process QA too
    p = audits["Process_Adherence"].astype("string").str.strip()
    s = audits["Solution_Provided"].astype("string").str.strip()
    for label, mask in (
        ("Followed process", p.eq("Followed process")),
        ("Did not follow process", p.eq("Did not follow process")),
        ("Resolved + followed", s.eq("Resolved") & p.eq("Followed process")),
        ("Resolved, no process", s.eq("Resolved") & p.eq("Did not follow process")),
        ("Unresolved + process", s.eq("Not resolved") & p.eq("Followed process")),
        ("Unresolved, no process", s.eq("Not resolved") & p.eq("Did not follow process")),
    ):
        vals = pd.to_numeric(audits.loc[mask, "Score_Pct"], errors="coerce").dropna()
        print(f"  {label:28s} n={int(mask.sum()):5d}  QA={vals.mean():6.2f}" if len(vals) else f"  {label}: n=0")

    print("\n" + "=" * 78)
    print("6. TICKET-LEVEL JOIN")
    print("=" * 78)
    print("No ticket/case/interaction id on fact_audits or fact_csat.")
    print("CSAT rows are already aggregates (Feedback CNT often >1).")
    print("True within-interaction CSAT contrast is NOT computable.")

    print("\n" + "=" * 78)
    print("DASHBOARD: what already exists")
    print("=" * 78)
    print("auditor_resolution_summary → KPI tiles: resolution rate, abandoned,")
    print("  unresolved-process split, plus official QA of those slices as caption.")
    print("QA page: Auditor_Outcome bar (QA Score by outcome combo) — still QA, not CSAT.")
    print("No chart of resolution RATE vs CSAT at CR/agent.")
    print("Association charts on the dashboard are QA vs CSAT / QA vs recontact,")
    print("  not % resolved vs CSAT.")


if __name__ == "__main__":
    main()
