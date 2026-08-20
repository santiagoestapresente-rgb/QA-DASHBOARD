"""
Forensic validation 03 — reverse-engineer column V (Score_end_user) of the QA tab.

The source workbook already contains a per-interaction score. Our model ignores it
and recomputes from the attribute flags. This script establishes which of the two
is consistent with the Business Case rules, and what formula the source column uses.
"""

from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"C:\Users\PC\Downloads\Business Case.xlsx")


def hr(t: str) -> None:
    print("\n" + "=" * 100)
    print(t)
    print("=" * 100)


def main() -> None:
    qa = pd.read_excel(SRC, sheet_name="QA")
    cols = list(qa.columns)
    PHONE = [str(c) for c in cols[22:34]]
    CHAT = [str(c) for c in cols[34:42]]
    qa["Audit_ID"] = np.arange(1, len(qa) + 1)

    def is_crit(c: str) -> bool:
        return "critical" in c.lower()

    # per-row fail signature
    sig = []
    for _, r in qa.iterrows():
        attrs = PHONE if r["Channel"] == "Phone" else CHAT
        failed = [c for c in attrs if r[c] == 1]
        crit = [c for c in failed if is_crit(c)]
        sig.append({
            "n_fail": len(failed),
            "n_crit": len(crit),
            "n_noncrit": len(failed) - len(crit),
            "failed_set": " | ".join(sorted(failed)),
        })
    qa = pd.concat([qa, pd.DataFrame(sig, index=qa.index)], axis=1)
    qa["our_score"] = np.where(qa["n_crit"] > 0, 0.0,
                               np.maximum(0.0, 100.0 - 10.0 * qa["n_noncrit"]))

    hr("A. Score_end_user vs the fail signature")
    tab = (qa.groupby(["Channel", "n_crit", "n_noncrit"])
           .agg(rows=("Audit_ID", "count"),
                src_min=("Score_end_user", "min"),
                src_max=("Score_end_user", "max"),
                src_mean=("Score_end_user", "mean"),
                src_distinct=("Score_end_user", "nunique"),
                our_score=("our_score", "first"))
           .reset_index())
    print(tab.to_string(index=False))

    hr("B. Does a critical fail always force Score_end_user to 0 in the source?")
    crit_rows = qa[qa["n_crit"] > 0]
    print(f"Rows with >=1 critical fail: {len(crit_rows)}")
    print(f"   Score_end_user values among them: {sorted(crit_rows['Score_end_user'].unique())}")
    print(f"   ...of which Score_end_user != 0: {int((crit_rows['Score_end_user'] != 0).sum())}")
    nocrit_zero = qa[(qa["n_crit"] == 0) & (qa["Score_end_user"] == 0)]
    print(f"\nRows with NO critical fail but Score_end_user == 0: {len(nocrit_zero)}")
    if len(nocrit_zero):
        print(nocrit_zero.groupby(["Channel", "n_noncrit"]).size().to_string())
        print("\n  Sample of these rows (source says 0, our rule says otherwise):")
        print(nocrit_zero[["Audit_ID", "Channel", "n_crit", "n_noncrit",
                           "our_score", "Score_end_user", "failed_set"]].head(15).to_string(index=False))

    hr("C. Rows with ZERO fails at all — what does the source score them?")
    clean = qa[qa["n_fail"] == 0]
    print(f"Rows with no fails anywhere: {len(clean):,}")
    print(clean["Score_end_user"].value_counts().sort_index(ascending=False).to_string())
    print(f"\n  -> our rule gives all of them 100.")
    odd_clean = clean[clean["Score_end_user"] != 100]
    print(f"  -> source gives a score != 100 to {len(odd_clean):,} of them "
          f"({len(odd_clean)/len(clean)*100:.1f}%)")
    if len(odd_clean):
        print("\n  Sample:")
        print(odd_clean[["Audit_ID", "Channel", "Type_of_audit", "n_fail",
                         "our_score", "Score_end_user"]].head(15).to_string(index=False))
        print("\n  Their audit-type mix:")
        print(odd_clean.groupby(["Type_of_audit", "Score_end_user"]).size().to_string())

    hr("D. Implied per-attribute weight in the source (rows with exactly 1 non-critical fail, 0 critical)")
    one = qa[(qa["n_crit"] == 0) & (qa["n_noncrit"] == 1)]
    print(f"Rows: {len(one):,}")
    imp = (one.groupby(["Channel", "failed_set"])
           .agg(rows=("Audit_ID", "count"),
                src_scores=("Score_end_user", lambda s: dict(s.value_counts())))
           .reset_index())
    for _, r in imp.iterrows():
        print(f"\n  [{r['Channel']}] {r['failed_set']}")
        print(f"     n={r['rows']:>4}  Score_end_user distribution: {r['src_scores']}")

    hr("E. Correlation between the two scores")
    print(f"Pearson r: {qa['our_score'].corr(qa['Score_end_user']):.4f}")
    print(f"\nCross-tab our_score x Score_end_user:")
    print(pd.crosstab(qa["our_score"], qa["Score_end_user"]).to_string())

    hr("F. Verdict inputs")
    print(f"Mean our_score        : {qa['our_score'].mean():.4f}")
    print(f"Mean Score_end_user   : {qa['Score_end_user'].mean():.4f}")
    print(f"Agreement rate        : {(qa['our_score'] == qa['Score_end_user']).mean()*100:.2f}%")
    print(f"Rows where source < ours : {int((qa['Score_end_user'] < qa['our_score']).sum()):,}")
    print(f"Rows where source > ours : {int((qa['Score_end_user'] > qa['our_score']).sum()):,}")

    hr("G. Is Score_end_user consistent with 'each non-critical fail = -10 from 100'?")
    consistent = qa[(qa["n_crit"] == 0)]
    exp = 100 - 10 * consistent["n_noncrit"]
    print(f"Non-critical-only rows: {len(consistent):,}")
    print(f"   match 100-10*fails : {int((consistent['Score_end_user'] == exp).sum()):,} "
          f"({(consistent['Score_end_user'] == exp).mean()*100:.2f}%)")
    print(f"   source LOWER       : {int((consistent['Score_end_user'] < exp).sum()):,}")
    print(f"   source HIGHER      : {int((consistent['Score_end_user'] > exp).sum()):,}")


if __name__ == "__main__":
    main()
