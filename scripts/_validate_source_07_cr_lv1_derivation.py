"""
Forensic validation 07 — verify the derived CR Lv1 / LOB claims in dim_cr
against the raw hierarchy in the CSAT and Recontact tabs.
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path

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


def norm(v) -> str:
    if pd.isna(v):
        return "UNKNOWN"
    t = re.sub(r"\s+", " ", str(v)).strip()
    return t.casefold() if t else "UNKNOWN"


def main() -> None:
    cs = pd.read_excel(SRC, sheet_name="CSAT")
    rc = pd.read_excel(SRC, sheet_name="Recontact")
    qa = pd.read_excel(SRC, sheet_name="QA")
    for d in (cs, rc, qa):
        d.columns = [str(c).strip().replace("\ufeff", "") for c in d.columns]

    hr("IS 'CR Lv2 -> CR Lv1' REALLY ONE-TO-ONE IN THE CSAT TAB?")
    m = cs.assign(k2=cs["CR Lv2"].map(norm)).groupby("k2")["CR Lv1"].nunique()
    print(f"  Distinct normalised CR Lv2 values in CSAT: {len(m)}")
    print(f"  Lv2 values mapping to MORE THAN ONE Lv1  : {int((m > 1).sum())}")
    if (m > 1).sum():
        for k in m[m > 1].index:
            print(f"     '{k}' -> {sorted(cs.loc[cs['CR Lv2'].map(norm) == k, 'CR Lv1'].unique())}")
    else:
        print("  -> the claim 'Lv2 maps one-to-one to Lv1 with no conflicts' HOLDS.")

    hr("HOW FAR DOES THAT PROPAGATION ACTUALLY REACH?")
    lv2_to_lv1 = (cs.assign(k2=cs["CR Lv2"].map(norm))
                  .groupby("k2")["CR Lv1"].first())
    lv4_to_lv1 = (cs.assign(k4=cs["CR Lv4"].map(norm))
                  .groupby("k4")["CR Lv1"].first())
    # Recontact supplies Lv2 for reasons absent from CSAT
    rc_lv4_to_lv2 = (rc.assign(k4=rc["CR Lv4"].map(norm))
                     .groupby("k4")["cr_lv2_name"].first().map(norm))

    qa_key = qa["CR_correcta"].fillna(qa["CR_registrada"]).map(norm)
    direct = qa_key.isin(lv4_to_lv1.index)
    via_lv2 = (~direct) & qa_key.map(rc_lv4_to_lv2).isin(lv2_to_lv1.index)
    print(f"  QA audits: {len(qa):,}")
    print(f"    Lv1 available directly from the CSAT Lv4 hierarchy : "
          f"{int(direct.sum()):,} ({direct.mean()*100:.1f}%)")
    print(f"    Lv1 recoverable via Recontact Lv2 -> CSAT Lv1      : "
          f"{int(via_lv2.sum()):,} ({via_lv2.mean()*100:.1f}%)")
    print(f"    Total with a CR Lv1                                 : "
          f"{int((direct | via_lv2).sum()):,} ({(direct | via_lv2).mean()*100:.1f}%)")
    print(f"    Still unmapped                                      : "
          f"{int((~(direct | via_lv2)).sum()):,} ({(~(direct|via_lv2)).mean()*100:.1f}%)")

    hr("CROSS-CHECK AGAINST THE EXPORTED dim_cr")
    dc = read_model_sheet("dim_cr")
    print(f"  dim_cr columns: {list(dc.columns)}")
    print(f"  rows: {len(dc)}")
    if "CR_Lv1_Source" in dc.columns:
        print(f"\n  CR_Lv1_Source distribution: {dc['CR_Lv1_Source'].value_counts().to_dict()}")
    print(f"  CR_Lv1 == 'Not mapped': {int((dc['CR_Lv1'] == 'Not mapped').sum())} of {len(dc)}")
    audited = dc[dc["In_QA"] == 1]
    print(f"  Audited reasons (In_QA=1): {len(audited)}   "
          f"with a real CR_Lv1: {int((audited['CR_Lv1'] != 'Not mapped').sum())}")
    nm = set(dc.loc[dc["CR_Lv1"] == "Not mapped", "CR_Key"])
    print(f"  QA audits landing on a reason with no CR_Lv1: "
          f"{int(qa_key.isin(nm).sum()):,} ({qa_key.isin(nm).mean()*100:.1f}%)")

    # verify each mapped Lv1 in dim_cr agrees with the raw CSAT hierarchy
    chk = dc[dc["CR_Key"].isin(lv4_to_lv1.index)].copy()
    chk["expected"] = chk["CR_Key"].map(lv4_to_lv1)
    bad = chk[chk["CR_Lv1"] != chk["expected"]]
    print(f"\n  Reasons whose dim_cr CR_Lv1 contradicts the raw CSAT hierarchy: {len(bad)}")
    if len(bad):
        print(bad[["CR_Key", "CR_Lv1", "expected"]].to_string(index=False))

    if "LOB" in dc.columns:
        hr("dim_cr[LOB] CLAIM")
        print(f"  LOB values in dim_cr: {dc['LOB'].value_counts(dropna=False).to_dict()}")
        print(f"  LOB values in the QA tab: {qa['LOB'].unique().tolist()}")
        print(f"  Reasons NOT present in QA (In_QA=0): {int((dc['In_QA'] == 0).sum())}")
        print(f"    their LOB values: "
              f"{dc.loc[dc['In_QA'] == 0, 'LOB'].value_counts(dropna=False).to_dict()}")
        print(f"  -> QA only contains LOB='Delivery', so any LOB assigned to a reason that")
        print(f"     never appears in QA is an inference, not a source fact.")


if __name__ == "__main__":
    main()
