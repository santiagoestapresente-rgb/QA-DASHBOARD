"""
Forensic validation 02 — QA scoring recomputed from scratch.

Deliberately does NOT import modules.kpis / modules.data_loader / config.
Attribute ranges are taken by POSITION from the raw workbook (W..AH, AI..AP).
"""

from __future__ import annotations

import sys
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
    """Read from a snapshot copy: the model file is being rewritten in parallel."""
    import shutil
    import tempfile
    tmp = Path(tempfile.gettempdir()) / "_didi_model_snapshot.xlsx"
    if not tmp.exists() or tmp.stat().st_mtime < MODEL.stat().st_mtime:
        shutil.copy2(MODEL, tmp)
    return pd.read_excel(tmp, sheet_name=sheet, engine="openpyxl")


def main() -> None:
    qa = pd.read_excel(SRC, sheet_name="QA")
    cols = list(qa.columns)
    PHONE = [str(c) for c in cols[22:34]]   # W(23)..AH(34)
    CHAT = [str(c) for c in cols[34:42]]    # AI(35)..AP(42)
    ATTRS = PHONE + CHAT

    print(f"QA rows: {len(qa):,}   Phone attrs: {len(PHONE)}   Chat attrs: {len(CHAT)}")

    # ── 1. Cell value hygiene ────────────────────────────────────────────────
    hr("1. RAW VALUES IN ATTRIBUTE CELLS (all 20 columns, both ranges)")
    allvals: dict = {}
    for c in ATTRS:
        vc = qa[c].value_counts(dropna=False).to_dict()
        for k, v in vc.items():
            allvals[k] = allvals.get(k, 0) + v
    print("Global value distribution across all attribute cells:")
    for k in sorted(allvals, key=lambda x: str(x)):
        print(f"   value={k!r:>8}  count={allvals[k]:,}")
    bad = {k: v for k, v in allvals.items() if k not in (0, 1, 2)}
    print(f"\nUnexpected values (not 0/1/2, incl. NaN/text): {bad if bad else 'NONE'}")
    print(f"Total NaN cells in attribute block: {int(qa[ATTRS].isna().sum().sum())}")
    nonnum = {c: int(pd.to_numeric(qa[c], errors='coerce').isna().sum() - qa[c].isna().sum()) for c in ATTRS}
    print(f"Non-numeric text cells per column: {{k:v for k,v in nonnum if v}} -> "
          f"{ {k: v for k, v in nonnum.items() if v} or 'NONE'}")

    # ── 2. Channel hygiene ───────────────────────────────────────────────────
    hr("2. CHANNEL COLUMN")
    print(qa["Channel"].value_counts(dropna=False).to_string())
    print(f"\nNull / blank channel rows: {int(qa['Channel'].isna().sum())}")
    other = qa[~qa["Channel"].isin(["Phone", "Live Chat"])]
    print(f"Rows whose Channel is neither 'Phone' nor 'Live Chat': {len(other)}")
    if len(other):
        print(other["Channel"].value_counts().to_string())

    # ── 3. Cross-channel contamination ───────────────────────────────────────
    hr("3. CROSS-CHANNEL CONTAMINATION (values present in the OTHER channel's range)")
    for label, own, foreign in [("Phone", PHONE, CHAT), ("Live Chat", CHAT, PHONE)]:
        sub = qa[qa["Channel"] == label]
        f = sub[foreign]
        o = sub[own]
        print(f"\n--- {label} rows: {len(sub):,}")
        print(f"    Foreign-range value counts (should be all N/A=2 if clean):")
        vc: dict = {}
        for c in foreign:
            for k, v in f[c].value_counts(dropna=False).to_dict().items():
                vc[k] = vc.get(k, 0) + v
        for k in sorted(vc, key=lambda x: str(x)):
            print(f"       value={k!r:>6}  {vc[k]:,}")
        graded_foreign = (f != 2).any(axis=1) & f.notna().any(axis=1)
        print(f"    Rows with ANY non-N/A value in the foreign range: {int(graded_foreign.sum())}")
        pass_foreign = (f == 0).any(axis=1)
        fail_foreign = (f == 1).any(axis=1)
        print(f"      ...of which have a PASS(0) in foreign range: {int(pass_foreign.sum())}")
        print(f"      ...of which have a FAIL(1) in foreign range: {int(fail_foreign.sum())}")
        all_na_own = (o == 2).all(axis=1)
        print(f"    Rows where the OWN range is 100% N/A: {int(all_na_own.sum())}")

    # ── 4. Independent scoring ───────────────────────────────────────────────
    hr("4. INDEPENDENT RECOMPUTATION OF QA SCORE")

    def is_crit(c: str) -> bool:
        return "critical" in c.lower()

    recomputed = []
    for idx, row in qa.iterrows():
        ch = row["Channel"]
        if ch == "Phone":
            attrs = PHONE
        elif ch == "Live Chat":
            attrs = CHAT
        else:
            recomputed.append({"idx": idx, "score": np.nan, "crit_fail": np.nan,
                               "nc_fails": np.nan, "evaluated": np.nan, "note": "channel not mapped"})
            continue
        crit_fail = 0
        nc_fails = 0
        evaluated = 0
        for c in attrs:
            v = row[c]
            if pd.isna(v) or v == 2:
                continue
            evaluated += 1
            if v == 1:
                if is_crit(c):
                    crit_fail = 1
                else:
                    nc_fails += 1
        score = 0.0 if crit_fail else max(0.0, 100.0 - 10.0 * nc_fails)
        recomputed.append({"idx": idx, "score": score, "crit_fail": crit_fail,
                           "nc_fails": nc_fails, "evaluated": evaluated, "note": ""})

    rec = pd.DataFrame(recomputed).set_index("idx")
    qa2 = qa.join(rec)
    qa2["Audit_ID"] = np.arange(1, len(qa2) + 1)

    print(f"Mean recomputed QA Score        : {rec['score'].mean():.6f}")
    print(f"Rounded (2dp)                   : {round(rec['score'].mean(), 2)}")
    print(f"Rows scored                     : {int(rec['score'].notna().sum()):,}")
    print(f"Rows unscored (channel unmapped): {int(rec['score'].isna().sum()):,}")
    print(f"\nScore distribution:")
    print(rec["score"].value_counts().sort_index(ascending=False).to_string())
    print(f"\nCritical fail rate: {rec['crit_fail'].mean()*100:.4f}%  "
          f"({int(rec['crit_fail'].sum())} audits)")

    # ── 5. Edge cases ────────────────────────────────────────────────────────
    hr("5. EDGE CASES")
    all_na = qa2[qa2["evaluated"] == 0]
    print(f"A) Interactions where EVERY applicable attribute is N/A: {len(all_na)}")
    if len(all_na):
        print(f"   Score assigned to them by our rule: {sorted(all_na['score'].unique())}")
        print(f"   Their channel mix: {all_na['Channel'].value_counts().to_dict()}")
        print(f"   Their Score_end_user (source col V): {sorted(all_na['Score_end_user'].unique())[:20]}")
        print(f"   Impact if excluded -> mean would be "
              f"{qa2[qa2['evaluated'] > 0]['score'].mean():.4f} instead of {rec['score'].mean():.4f}")

    both = qa2[(qa2["crit_fail"] == 1) & (qa2["nc_fails"] > 0)]
    print(f"\nB) Interactions with BOTH a critical fail and >=1 non-critical fail: {len(both)}")
    print(f"   All forced to 0? {set(both['score'].unique()) == {0.0} if len(both) else 'n/a'}")
    if len(both):
        print(both[["Audit_ID", "Channel", "crit_fail", "nc_fails", "score", "Score_end_user"]].head(10).to_string(index=False))

    many = qa2[qa2["nc_fails"] > 10]
    print(f"\nC) Interactions with MORE THAN 10 non-critical fails (would go negative): {len(many)}")
    print(f"   Max non-critical fails observed on a single audit: {int(rec['nc_fails'].max())}")
    print(f"   Distribution of non-critical fail counts:")
    print(rec["nc_fails"].value_counts().sort_index().to_string())

    print(f"\nD) Rows with channel not Phone/Live Chat or blank: {int(rec['score'].isna().sum())}")

    # ── 6. Compare with source Score_end_user (column V) ─────────────────────
    hr("6. COMPARISON AGAINST THE SOURCE'S OWN SCORE COLUMN (V = Score_end_user)")
    print("The source workbook already ships a per-interaction score. Comparing:")
    src_score = qa2["Score_end_user"]
    print(f"\nSource Score_end_user  mean: {src_score.mean():.4f}   "
          f"min: {src_score.min()}  max: {src_score.max()}  distinct: {src_score.nunique()}")
    print(f"Our recomputed score   mean: {rec['score'].mean():.4f}")
    print(f"Difference in means: {rec['score'].mean() - src_score.mean():+.4f} pp")
    print(f"\nTop 25 values of Score_end_user:")
    print(src_score.value_counts().sort_index(ascending=False).head(25).to_string())
    print(f"\nValues of Score_end_user that are NOT multiples of 10: "
          f"{sorted(set(src_score[src_score % 10 != 0].unique()))[:40]}")
    print(f"Count of rows where Score_end_user is not a multiple of 10: {int((src_score % 10 != 0).sum())}")
    exact = (qa2["score"] == src_score).sum()
    print(f"\nRows where our score == Score_end_user: {exact:,} / {len(qa2):,} "
          f"({exact/len(qa2)*100:.2f}%)")
    diffs = qa2[qa2["score"] != src_score]
    print(f"Rows where they differ: {len(diffs):,}")
    print("\nExamples of rows where they differ:")
    print(diffs[["Audit_ID", "Channel", "crit_fail", "nc_fails", "evaluated",
                 "score", "Score_end_user"]].head(15).to_string(index=False))
    print("\nBreakdown of disagreement by channel:")
    print(diffs.groupby("Channel").size().to_string())

    # ── 7. Compare with the exported model ───────────────────────────────────
    hr("7. ROW-BY-ROW COMPARISON AGAINST fact_audit[QA_Score] IN THE EXPORTED MODEL")
    fa = read_model_sheet("fact_audit")
    print(f"fact_audit rows: {len(fa):,}  (QA source rows: {len(qa2):,})")
    if len(fa) != len(qa2):
        print("!! ROW COUNT MISMATCH")

    merged = qa2[["Audit_ID", "Channel", "score", "crit_fail", "nc_fails",
                  "evaluated", "Score_end_user"]].merge(
        fa[["Audit_ID", "QA_Score", "Has_Critical_Fail", "NonCritical_Fails",
            "Attributes_Evaluated", "Channel_Key"]],
        on="Audit_ID", how="outer", indicator=True)
    print(f"Merge indicator: {merged['_merge'].value_counts().to_dict()}")

    merged["delta"] = merged["QA_Score"] - merged["score"]
    mism_real = merged[(merged["delta"].abs() > 1e-9) | (merged["QA_Score"].isna() != merged["score"].isna())]
    print(f"\nRows where model QA_Score differs from our independent score: {len(mism_real):,}")
    if len(mism_real):
        print(mism_real.head(25).to_string(index=False))

    for c_ours, c_model in [("crit_fail", "Has_Critical_Fail"),
                            ("nc_fails", "NonCritical_Fails"),
                            ("evaluated", "Attributes_Evaluated")]:
        d = merged[merged[c_ours].fillna(-999) != merged[c_model].fillna(-999)]
        print(f"Rows where {c_ours} != {c_model}: {len(d):,}")

    print(f"\nModel mean QA_Score : {fa['QA_Score'].mean():.6f}  -> rounded {round(fa['QA_Score'].mean(),2)}")
    print(f"Ours  mean QA_Score : {rec['score'].mean():.6f}  -> rounded {round(rec['score'].mean(),2)}")
    print(f"CONTROL TOTAL 94.14 CONFIRMED? {round(rec['score'].mean(),2) == 94.14}")

    # ── 8. Alternative scoring interpretations ───────────────────────────────
    hr("8. SENSITIVITY: ALTERNATIVE DEFENSIBLE INTERPRETATIONS OF THE QA SCORE")
    base = rec["score"].mean()
    alt_excl_allna = qa2[qa2["evaluated"] > 0]["score"].mean()
    print(f"a) Current rule (all rows, all-N/A rows score 100)       : {base:.4f}")
    print(f"b) Excluding rows where 0 attributes were evaluated      : {alt_excl_allna:.4f}  "
          f"(delta {alt_excl_allna-base:+.4f})")

    # weighted-by-attribute alternative (pass rate)
    passrate = []
    for _, r in qa2.iterrows():
        attrs = PHONE if r["Channel"] == "Phone" else CHAT if r["Channel"] == "Live Chat" else None
        if attrs is None:
            passrate.append(np.nan)
            continue
        vals = [r[c] for c in attrs if not pd.isna(r[c]) and r[c] != 2]
        passrate.append(np.nan if not vals else sum(1 for v in vals if v == 0) / len(vals) * 100)
    print(f"c) Pure attribute pass-rate (NOT the business case rule)  : {np.nanmean(passrate):.4f}")
    print(f"d) Using the source's own Score_end_user column           : {src_score.mean():.4f}")

    # per-channel
    hr("9. QA SCORE BY CHANNEL (our recomputation)")
    print(qa2.groupby("Channel").agg(
        n=("Audit_ID", "count"),
        mean_score=("score", "mean"),
        crit_rate=("crit_fail", "mean"),
        mean_src_score=("Score_end_user", "mean"),
        mean_evaluated=("evaluated", "mean"),
    ).round(4).to_string())


if __name__ == "__main__":
    main()
