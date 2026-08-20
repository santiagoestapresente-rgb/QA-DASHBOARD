"""Probe Excel vs parquet CR labels for Spanish vs English."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "data" / "Business Case.xlsx"
PKG = ROOT / "data" / "packaged"

SPANISH_RE = re.compile(
    r"[áéíóúñÁÉÍÓÚÑ]|pedido|reembolso|cancelaci|informaci|retraso|"
    r"dañad|incompleto|robado|repartidor|mensajero|estado del|"
    r"solicitud|usuario no|orden no|cuenta rob",
    re.I,
)


def dump(name: str, s: pd.Series) -> None:
    raw = s
    s = s.dropna().astype(str)
    vals = s.drop_duplicates()
    spanish = [v for v in vals if SPANISH_RE.search(v)]
    print(f"\n=== {name} nunique={vals.nunique()} nulls={int(raw.isna().sum())} ===")
    print(f"  spanish-ish: {len(spanish)} of {vals.nunique()}")
    print("  first 15 unique:")
    for v in vals.head(15):
        print("   ", repr(v))
    if spanish:
        print("  SPANISH-ISH samples:")
        for v in spanish[:25]:
            print("   ", repr(v))


def main() -> None:
    qa = pd.read_excel(XLSX, sheet_name="QA")
    cs = pd.read_excel(XLSX, sheet_name="CSAT")
    rc = pd.read_excel(XLSX, sheet_name="Recontact")
    for d in (qa, cs, rc):
        d.columns = [str(c).strip().replace("\ufeff", "") for c in d.columns]

    print("QA CR cols:", [c for c in qa.columns if "CR" in str(c).upper()])
    print("CSAT CR cols:", [c for c in cs.columns if "CR" in str(c).upper()])
    print("RC CR cols:", [c for c in rc.columns if "CR" in str(c).upper() or "cr_" in str(c)])

    dump("QA CR_registrada", qa["CR_registrada"])
    dump("QA CR_correcta", qa["CR_correcta"])
    if "SUB_CR_registrada" in qa.columns:
        dump("QA SUB_CR_registrada", qa["SUB_CR_registrada"])
    if "SUB_CR_correcta" in qa.columns:
        dump("QA SUB_CR_correcta", qa["SUB_CR_correcta"])
    dump("CSAT CR Lv1", cs["CR Lv1"])
    dump("CSAT CR Lv2", cs["CR Lv2"])
    dump("CSAT CR Lv3", cs["CR Lv3"])
    dump("CSAT CR Lv4", cs["CR Lv4"])
    if "Sub CR" in cs.columns:
        dump("CSAT Sub CR", cs["Sub CR"])
    dump("RC CR Lv4", rc["CR Lv4"])
    dump("RC cr_lv2_name", rc["cr_lv2_name"])
    dump("RC cr_lv3_name", rc["cr_lv3_name"])

    both = qa[["CR_registrada", "CR_correcta"]].dropna()
    diff = both[
        both["CR_registrada"].astype(str).str.strip()
        != both["CR_correcta"].astype(str).str.strip()
    ]
    print("\n=== CR_correcta vs CR_registrada ===")
    print("rows different (raw):", len(diff), "of", len(both))
    print("sample pairs:")
    for _, r in diff.head(20).iterrows():
        print("  reg=", repr(r["CR_registrada"]))
        print("  cor=", repr(r["CR_correcta"]))
        print()

    print("\n=== parquet vs excel QA coalesced ===")
    audits = pd.read_parquet(PKG / "fact_audits.parquet")
    coalesced = qa["CR_correcta"].fillna(qa["CR_registrada"]).astype(str)
    print("excel coalesced sample 15:", coalesced.drop_duplicates().head(15).tolist())
    print("parquet CR_Lv4 sample 15:", audits["CR_Lv4"].dropna().astype(str).drop_duplicates().head(15).tolist())


if __name__ == "__main__":
    main()
