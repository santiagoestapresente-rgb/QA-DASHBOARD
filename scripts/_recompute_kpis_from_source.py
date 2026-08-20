"""Independent KPI recompute from the source workbook.

Does NOT import modules.data_loader / modules.kpis / config scoring.
Attribute ranges taken by Excel column POSITION (W-AH Phone, AI-AP Live Chat).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(r"C:\Users\PC\Documents\DIDI")
SRC_CANDIDATES = [
    REPO / "data" / "Business Case.xlsx",
    Path(r"C:\Users\PC\Downloads\Business Case.xlsx"),
]
PACKAGED = REPO / "data" / "packaged"


def pick_src() -> Path:
    for p in SRC_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError(SRC_CANDIDATES)


def hr(t: str) -> None:
    print("\n" + "=" * 100)
    print(t)
    print("=" * 100)


def iso_week(s: pd.Series) -> pd.Series:
    iso = pd.to_datetime(s, errors="coerce").dt.isocalendar()
    return "W" + iso.week.astype("Int64").astype(str)


def is_crit(c: str) -> bool:
    return "critical" in str(c).lower()


def main() -> None:
    src = pick_src()
    print(f"SOURCE: {src}")
    print(f"mtime: {src.stat().st_mtime}")
    print(f"size:  {src.stat().st_size}")

    qa = pd.read_excel(src, sheet_name="QA")
    csat = pd.read_excel(src, sheet_name="CSAT")
    rc = pd.read_excel(src, sheet_name="Recontact")
    qa.columns = [str(c).strip().replace("\ufeff", "") for c in qa.columns]
    csat.columns = [str(c).strip().replace("\ufeff", "") for c in csat.columns]
    rc.columns = [str(c).strip().replace("\ufeff", "") for c in rc.columns]

    cols = list(qa.columns)
    PHONE = [str(c) for c in cols[22:34]]  # W..AH (1-index 23..34)
    CHAT = [str(c) for c in cols[34:42]]   # AI..AP (1-index 35..42)

    hr("0. QA TAB STRUCTURE")
    print(f"QA rows={len(qa):,}  cols={len(cols)}")
    print("First 25 columns with Excel letters:")
    for i, c in enumerate(cols[:45]):
        letter = ""
        n = i + 1
        while n:
            n, r = divmod(n - 1, 26)
            letter = chr(65 + r) + letter
        mark = ""
        if i == 21:
            mark = "  <-- likely Score_end_user (col V)"
        if i == 22:
            mark = "  <-- Phone start W"
        if i == 33:
            mark = "  <-- Phone end AH"
        if i == 34:
            mark = "  <-- Chat start AI"
        if i == 41:
            mark = "  <-- Chat end AP"
        print(f"  {letter:>3}  idx={i:02d}  {c}{mark}")
    print("\nPhone attrs:")
    for c in PHONE:
        print(f"  {'CRIT' if is_crit(c) else '    '}  {c}")
    print("Chat attrs:")
    for c in CHAT:
        print(f"  {'CRIT' if is_crit(c) else '    '}  {c}")

    # ── A. Score_end_user ──────────────────────────────────────────────────
    hr("A. Score_end_user — THE USER'S PIVOT COLUMN")
    if "Score_end_user" not in qa.columns:
        raise SystemExit("Score_end_user missing")
    seu = pd.to_numeric(qa["Score_end_user"], errors="coerce")
    print(f"n rows={len(qa):,}")
    print(f"n non-null Score_end_user={int(seu.notna().sum()):,}")
    print(f"n null Score_end_user={int(seu.isna().sum()):,}")
    print(f"min={seu.min()} max={seu.max()} nunique={seu.nunique()}")
    print(f"MEAN (pandas skipna, Excel AVERAGE equivalent) = {seu.mean():.10f}  -> {seu.mean():.2f}")
    print(f"MEAN if NaN treated as 0                       = {seu.fillna(0).mean():.10f} -> {seu.fillna(0).mean():.2f}")
    print(f"User Grand total: 86.9   match 2dp? {round(float(seu.mean()), 2) == 86.9}")

    print("\nWeek column value counts:")
    print(qa["Week"].value_counts(dropna=False).sort_index().to_string())
    print(f"\nfecha dtype sample: {qa['fecha'].head(3).tolist()}")
    qa["_iso"] = iso_week(qa["fecha"])
    print("ISO week from fecha:")
    print(qa["_iso"].value_counts(dropna=False).sort_index().to_string())
    mismatch_week = (qa["Week"].astype(str) != qa["_iso"].astype(str)).sum()
    print(f"Rows where Excel Week != ISO week from fecha: {mismatch_week}")

    user_weekly = {"W19": 85.9, "W20": 88.5, "W21": 86.2, "W22": 86.3}
    print("\n--- Score_end_user by Excel Week column ---")
    print(f"{'Week':<8} {'n':>7} {'n_nonnull':>10} {'mean':>10} {'mean_2dp':>10} {'user':>8} {'match':>6}")
    for w, g in qa.groupby("Week", dropna=False):
        m = pd.to_numeric(g["Score_end_user"], errors="coerce").mean()
        user = user_weekly.get(str(w))
        match = "" if user is None else str(round(float(m), 1) == user)
        print(f"{str(w):<8} {len(g):>7} {int(g['Score_end_user'].notna().sum()):>10} "
              f"{m:10.6f} {round(float(m),2):10.2f} {str(user):>8} {match:>6}")
    overall = seu.mean()
    print(f"{'ALL':<8} {len(qa):>7} {int(seu.notna().sum()):>10} "
          f"{overall:10.6f} {round(float(overall),2):10.2f} {'86.9':>8} "
          f"{str(round(float(overall),1)==86.9):>6}")

    print("\n--- Score_end_user by ISO week from fecha ---")
    for w, g in qa.groupby("_iso", dropna=False):
        m = pd.to_numeric(g["Score_end_user"], errors="coerce").mean()
        print(f"  {w}: n={len(g):,} mean={m:.4f} -> {round(float(m),2)}")

    print("\n--- Score_end_user BY CHANNEL ---")
    print(qa["Channel"].value_counts(dropna=False).to_string())
    for ch, g in qa.groupby("Channel", dropna=False):
        m = pd.to_numeric(g["Score_end_user"], errors="coerce")
        print(f"  {ch}: n={len(g):,} nonnull={int(m.notna().sum()):,} "
              f"mean={m.mean():.6f} -> {round(float(m.mean()),2)}")

    print("\n--- Score_end_user Week x Channel ---")
    pivot = (
        qa.assign(seu=seu)
        .pivot_table(index="Week", columns="Channel", values="seu", aggfunc="mean")
        .round(2)
    )
    print(pivot.to_string())
    cnt = qa.pivot_table(index="Week", columns="Channel", values="Score_end_user", aggfunc="count")
    print("\ncounts:")
    print(cnt.to_string())

    # ── B. Official QA Score from attributes ───────────────────────────────
    hr("B. OFFICIAL QA SCORE (PDF §3.1) — from attribute flags, NOT Score_end_user")

    scores = []
    for idx, row in qa.iterrows():
        ch = row["Channel"]
        if ch == "Phone":
            attrs = PHONE
        elif ch == "Live Chat":
            attrs = CHAT
        else:
            scores.append({"idx": idx, "score": np.nan, "fatal": np.nan,
                           "nc_fails": np.nan, "evaluated": np.nan, "channel": ch})
            continue
        fatal = 0
        nc = 0
        evaluated = 0
        for c in attrs:
            v = row[c]
            if pd.isna(v) or v == 2:
                continue
            evaluated += 1
            if v == 1:
                if is_crit(c):
                    fatal = 1
                else:
                    nc += 1
        score = 0.0 if fatal else max(0.0, 100.0 - 10.0 * nc)
        scores.append({"idx": idx, "score": score, "fatal": fatal,
                       "nc_fails": nc, "evaluated": evaluated, "channel": ch})

    rec = pd.DataFrame(scores).set_index("idx")
    qa = qa.join(rec[["score", "fatal", "nc_fails", "evaluated"]])
    qa["Audit_ID"] = np.arange(1, len(qa) + 1)

    n_scored = int(qa["score"].notna().sum())
    off_mean = float(qa["score"].mean())
    print(f"n audits={len(qa):,}  n scored={n_scored:,}  unscored={int(qa['score'].isna().sum())}")
    print(f"OFFICIAL QA mean = {off_mean:.10f}  -> {off_mean:.2f}")
    print(f"Fatal audits = {int(qa['fatal'].sum())}  rate={qa['fatal'].mean()*100:.2f}%")
    print(f"Score dist:\n{qa['score'].value_counts().sort_index(ascending=False).to_string()}")

    print("\n--- Official QA by Excel Week ---")
    print(f"{'Week':<8} {'n':>7} {'QA':>10} {'QA_2dp':>8} {'SEU':>10} {'SEU_2dp':>8} {'gap_pp':>8}")
    for w, g in qa.groupby("Week", dropna=False):
        qa_m = g["score"].mean()
        se_m = pd.to_numeric(g["Score_end_user"], errors="coerce").mean()
        print(f"{str(w):<8} {len(g):>7} {qa_m:10.6f} {round(float(qa_m),2):8.2f} "
              f"{se_m:10.6f} {round(float(se_m),2):8.2f} {qa_m-se_m:8.2f}")
    se_all = float(seu.mean())
    print(f"{'ALL':<8} {len(qa):>7} {off_mean:10.6f} {round(off_mean,2):8.2f} "
          f"{se_all:10.6f} {round(se_all,2):8.2f} {off_mean-se_all:8.2f}")

    print("\n--- Official QA vs Score_end_user BY CHANNEL ---")
    for ch, g in qa.groupby("Channel", dropna=False):
        qa_m = g["score"].mean()
        se_m = pd.to_numeric(g["Score_end_user"], errors="coerce").mean()
        print(f"  {ch}: n={len(g):,}  official QA={qa_m:.6f}->{round(float(qa_m),2)}  "
              f"SEU={se_m:.6f}->{round(float(se_m),2)}  gap={qa_m-se_m:+.2f}")

    print("\n--- Official QA Week x Channel ---")
    print(qa.pivot_table(index="Week", columns="Channel", values="score", aggfunc="mean").round(2).to_string())
    print("counts:")
    print(qa.pivot_table(index="Week", columns="Channel", values="score", aggfunc="count").to_string())

    agree = (qa["score"] == seu).mean() * 100
    print(f"\nRow agreement official==SEU: {agree:.2f}%  ({int((qa['score']==seu).sum()):,}/{len(qa):,})")
    print(f"PDF does NOT mention Score_end_user. Official formula uses attribute flags only.")

    # ── C. CSAT ────────────────────────────────────────────────────────────
    hr("C. CSAT (PDF §3.2) — DIFFERENT SHEET, NOT Score_end_user")
    print(f"CSAT rows={len(csat):,}")
    print("Columns:", list(csat.columns))
    stars4 = "Questionnaires With Star Level =4"
    stars5 = "Questionnaires With Star Level =5"
    fb_col = "Feedback CNT"
    csat["Fecha"] = pd.to_datetime(csat["pt(天)"], errors="coerce")
    csat["_iso"] = iso_week(csat["Fecha"])
    sat = csat[stars4].sum() + csat[stars5].sum()
    fb = csat[fb_col].sum()
    csat_pct = sat / fb * 100
    print(f"SUM 4-star={csat[stars4].sum():,.0f}  SUM 5-star={csat[stars5].sum():,.0f}")
    print(f"SUM satisfied (4+5)={sat:,.0f}")
    print(f"SUM Feedback CNT={fb:,.0f}")
    print(f"CSAT = {sat}/{fb} * 100 = {csat_pct:.10f} -> {csat_pct:.2f}")
    print(f"WRONG if mean of row CSAT% : "
          f"{((csat[stars4]+csat[stars5])/csat[fb_col]*100).replace([np.inf,-np.inf],np.nan).mean():.4f}")

    ch_col = "Consolidated Channel." if "Consolidated Channel." in csat.columns else "Channel"
    print(f"\nCSAT channel column: {ch_col!r}")
    print(csat[ch_col].value_counts(dropna=False).to_string())

    print("\n--- CSAT by channel (ratio of sums) ---")
    for ch, g in csat.groupby(ch_col, dropna=False):
        s = g[stars4].sum() + g[stars5].sum()
        f = g[fb_col].sum()
        print(f"  {ch}: rows={len(g):,} feedback={f:,.0f} sat={s:,.0f} CSAT={s/f*100:.2f}")

    print("\n--- CSAT by ISO week ---")
    for w, g in csat.groupby("_iso", dropna=False):
        s = g[stars4].sum() + g[stars5].sum()
        f = g[fb_col].sum()
        print(f"  {w}: rows={len(g):,} feedback={f:,.0f} sat={s:,.0f} CSAT={s/f*100:.2f}")

    print("\n--- CSAT Week x Channel ---")
    def _csat_rate(g):
        f = g[fb_col].sum()
        return (g[stars4].sum() + g[stars5].sum()) / f * 100 if f else np.nan
    wc = csat.groupby(["_iso", ch_col]).apply(_csat_rate, include_groups=False).unstack()
    print(wc.round(2).to_string())

    # ── D. Recontact ───────────────────────────────────────────────────────
    hr("D. RECONTACT (PDF §3.3)")
    print(f"Recontact rows={len(rc):,}")
    print("Columns:", list(rc.columns))
    vol = rc["Recontact Volume"].sum()
    contacts = rc["Contacts"].sum()
    rate = vol / contacts * 100
    print(f"SUM Recontact Volume={vol:,.0f}")
    print(f"SUM Contacts={contacts:,.0f}")
    print(f"Rate={vol}/{contacts}*100={rate:.10f} -> {rate:.2f}   goal=5.44")
    print(f"WRONG if mean of row rates: "
          f"{(rc['Recontact Volume']/rc['Contacts']*100).replace([np.inf,-np.inf],np.nan).mean():.4f}")

    rc["Fecha"] = pd.to_datetime(rc["Date(天)"], errors="coerce")
    rc["_iso"] = iso_week(rc["Fecha"])
    ch_rc = "standard_channel_name"
    print("\nChannels:")
    print(rc[ch_rc].value_counts(dropna=False).to_string())

    print("\n--- Recontact by channel ---")
    gch = rc.groupby(ch_rc).agg(rows=("Contacts", "size"), Contacts=("Contacts", "sum"),
                                Vol=("Recontact Volume", "sum"))
    gch["Rate"] = gch["Vol"] / gch["Contacts"] * 100
    print(gch.sort_values("Contacts", ascending=False).round(2).to_string())

    print("\n--- Recontact by ISO week ---")
    gw = rc.groupby("_iso").agg(rows=("Contacts", "size"), Contacts=("Contacts", "sum"),
                                Vol=("Recontact Volume", "sum"))
    gw["Rate"] = gw["Vol"] / gw["Contacts"] * 100
    print(gw.round(2).to_string())

    sh = rc[rc[ch_rc].astype(str).str.upper() == "SELF HELP"]
    audited = rc[rc[ch_rc].astype(str).str.upper().isin(["PHONE", "LIVE CHAT"])]
    excl_sh = rc[rc[ch_rc].astype(str).str.upper() != "SELF HELP"]
    print("\n--- Dilution scopes ---")
    for name, sub in [
        ("All channels (official)", rc),
        ("Excl Self Help", excl_sh),
        ("Phone+Live Chat only", audited),
        ("Self Help only", sh),
    ]:
        c = sub["Contacts"].sum()
        v = sub["Recontact Volume"].sum()
        print(f"  {name}: contacts={c:,.0f} vol={v:,.0f} rate={v/c*100:.2f}  share={c/contacts*100:.1f}%")

    # ── Packaged parquet comparison ────────────────────────────────────────
    hr("E. PACKAGED PARQUET vs SOURCE EXCEL (independent)")
    fa = pd.read_parquet(PACKAGED / "fact_audits.parquet")
    fc = pd.read_parquet(PACKAGED / "fact_csat.parquet")
    fr = pd.read_parquet(PACKAGED / "fact_recontact.parquet")

    print(f"packaged fact_audits n={len(fa):,}  source QA n={len(qa):,}")
    print(f"packaged fact_csat n={len(fc):,}  source CSAT n={len(csat):,}")
    print(f"packaged fact_recontact n={len(fr):,}  source RC n={len(rc):,}")

    pkg_qa = float(fa["Score_Pct"].mean())
    pkg_seu = float(pd.to_numeric(fa["Source_Score_End_User"], errors="coerce").mean()) if "Source_Score_End_User" in fa.columns else float("nan")
    print(f"\npackaged Score_Pct (official QA) mean={pkg_qa:.6f} -> {pkg_qa:.2f}")
    print(f"source independent official QA      mean={off_mean:.6f} -> {off_mean:.2f}")
    print(f"delta packaged-source QA: {pkg_qa-off_mean:+.6f}")
    print(f"packaged Source_Score_End_User mean={pkg_seu:.6f} -> {round(pkg_seu,2)}")
    print(f"source Score_end_user mean         ={se_all:.6f} -> {round(se_all,2)}")

    # row-level compare if same length
    if len(fa) == len(qa):
        delta = (fa["Score_Pct"].to_numpy() - qa["score"].to_numpy())
        n_diff = int((np.abs(delta) > 1e-9).sum())
        print(f"Row-level Score_Pct vs independent score diffs: {n_diff}")
        if n_diff:
            print("  first mismatches:", np.where(np.abs(delta) > 1e-9)[0][:10])
    else:
        print("ROW COUNT MISMATCH audits — cannot pairwise compare")

    pkg_sat = fc["Satisfied_CNT"].sum()
    pkg_fb = fc["Feedback CNT"].sum()
    pkg_csat = pkg_sat / pkg_fb * 100
    print(f"\npackaged CSAT {pkg_sat}/{pkg_fb} = {pkg_csat:.6f} -> {pkg_csat:.2f}")
    print(f"source CSAT   {sat}/{fb} = {csat_pct:.6f} -> {csat_pct:.2f}")
    print(f"delta packaged-source CSAT: {pkg_csat-csat_pct:+.6f}")
    print(f"feedback match? {int(pkg_fb)==int(fb)}  sat match? {int(pkg_sat)==int(sat)}")

    pkg_vol = fr["Recontact Volume"].sum()
    pkg_c = fr["Contacts"].sum()
    pkg_rc = pkg_vol / pkg_c * 100
    print(f"\npackaged Recontact {pkg_vol}/{pkg_c} = {pkg_rc:.6f} -> {pkg_rc:.2f}")
    print(f"source Recontact   {vol}/{contacts} = {rate:.6f} -> {rate:.2f}")
    print(f"delta packaged-source RC: {pkg_rc-rate:+.6f}")
    print(f"contacts match? {int(pkg_c)==int(contacts)}  vol match? {int(pkg_vol)==int(vol)}")

    print("\n--- packaged QA by Week vs source ---")
    if "Week" in fa.columns:
        pkg_w = fa.groupby("Week")["Score_Pct"].agg(["mean", "count"])
        src_w = qa.groupby("Week")["score"].agg(["mean", "count"])
        merged_w = pkg_w.join(src_w, lsuffix="_pkg", rsuffix="_src", how="outer")
        print(merged_w.round(6).to_string())

    print("\n--- packaged QA by Channel vs source ---")
    pkg_ch = fa.groupby("Channel")["Score_Pct"].agg(["mean", "count"])
    src_ch = qa.groupby("Channel")["score"].agg(["mean", "count"])
    print(pkg_ch.join(src_ch, lsuffix="_pkg", rsuffix="_src", how="outer").round(6).to_string())

    hr("F. VERDICT TABLE")
    print("Metric | Their pivot / Excel col | Official PDF | Our independent | Packaged | Goal")
    print(f"Score_end_user | 86.9 (their pivot) | NOT IN PDF | {se_all:.2f} | {pkg_seu:.2f} | n/a")
    print(f"QA Score | they used Score_end_user | §3.1 attributes | {off_mean:.2f} | {pkg_qa:.2f} | 85")
    print(f"CSAT | they mixed with QA? | §3.2 CSAT tab | {csat_pct:.2f} | {pkg_csat:.2f} | 85")
    print(f"Recontact | (not their pivot) | §3.3 | {rate:.2f} | {pkg_rc:.2f} | 5.44")
    print(f"\nn audits={len(qa):,}  n feedback={int(fb):,}  n contacts={int(contacts):,}")

    bug_qa = abs(pkg_qa - off_mean) > 0.005
    bug_csat = abs(pkg_csat - csat_pct) > 0.005
    bug_rc = abs(pkg_rc - rate) > 0.005
    print(f"\nBUG vs independent Excel recalc? QA={bug_qa} CSAT={bug_csat} RC={bug_rc}")
    print("If all False: packaged matches source. Do NOT switch dashboard to Score_end_user.")


if __name__ == "__main__":
    main()
