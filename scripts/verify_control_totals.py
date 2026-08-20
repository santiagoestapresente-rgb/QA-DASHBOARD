"""
Lock official Business Case totals: Excel ↔ packaged snapshot ↔ default Date filter.

QA Score        94.14   mean of audit scores (critical fail → 0)
CSAT Score      79.95   (4★+5★) / Feedback CNT
Recontact Rate   5.83   Σ Recontact Volume / Σ Contacts
Surveys         77,266
Contacts       994,591
Evaluations      2,460
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import CONTROL_TOTALS, SOURCE_XLSX  # noqa: E402
from modules.data_loader import load_all_data  # noqa: E402
from modules.kpis import (  # noqa: E402
    avg_qa_score,
    csat_by_star_rating,
    cut_csat_recontact_for_weeks,
    overall_csat,
    recontact_rate,
    volume_totals,
)

DOWNLOADS_XLSX = Path(r"C:\Users\PC\Downloads\Business Case.xlsx")
TOL = 0.01


def _ok(label: str, got, expected, *, tol: float | None = None) -> bool:
    if tol is None:
        match = got == expected
    else:
        match = abs(float(got) - float(expected)) <= tol
    mark = "OK" if match else "MISMATCH"
    print(f"  {label:28} got {got}  expected {expected}  {mark}")
    return match


def excel_csat_rc(path: Path) -> dict:
    csat = pd.read_excel(path, sheet_name="CSAT")
    rc = pd.read_excel(path, sheet_name="Recontact")
    csat.columns = [str(c).strip().replace("\ufeff", "") for c in csat.columns]
    rc.columns = [str(c).strip().replace("\ufeff", "") for c in rc.columns]
    stars = [f"Questionnaires With Star Level ={i}" for i in range(1, 6)]
    fb = float(csat["Feedback CNT"].sum())
    sat = float(csat[stars[3]].sum() + csat[stars[4]].sum())
    contacts = float(rc["Contacts"].sum())
    vol = float(rc["Recontact Volume"].sum())
    return {
        "csat": round(sat / fb * 100, 2) if fb else None,
        "surveys": int(fb),
        "star_sum": int(csat[stars].sum().sum()),
        "recontact": round(vol / contacts * 100, 2) if contacts else None,
        "contacts": int(contacts),
    }


def main() -> int:
    ok = True
    exp = CONTROL_TOTALS
    data = load_all_data()
    audits, csat, rc = data["fact_audits"], data["fact_csat"], data["fact_recontact"]
    weeks = sorted(audits["Week"].dropna().astype(str).unique())

    print("1) Packaged snapshot vs official totals")
    vol = volume_totals(audits, csat, rc)
    ok = _ok("QA Score", round(avg_qa_score(audits), 2), exp["qa"], tol=TOL) and ok
    ok = _ok("CSAT Score", round(overall_csat(csat), 2), exp["csat"], tol=TOL) and ok
    ok = _ok("Recontact Rate", round(recontact_rate(rc), 2), exp["recontact"], tol=TOL) and ok
    ok = _ok("QA evaluations", vol["evaluations"], exp["evaluations"]) and ok
    ok = _ok("CSAT surveys", vol["surveys"], exp["surveys"]) and ok
    ok = _ok("Recontact contacts", vol["contacts"], exp["contacts"]) and ok
    stars = csat_by_star_rating(csat)
    ok = _ok("Star-rating N", int(stars["Count"].sum()), exp["surveys"]) and ok

    print("\n2) Date = all QA weeks must not clip CSAT / recontact")
    c2, r2 = cut_csat_recontact_for_weeks(csat, rc, weeks, weeks)
    ok = _ok("Surveys after all-weeks", int(c2["Feedback CNT"].sum()), exp["surveys"]) and ok
    ok = _ok("Contacts after all-weeks", int(r2["Contacts"].sum()), exp["contacts"]) and ok
    ok = _ok("CSAT after all-weeks", round(overall_csat(c2), 2), exp["csat"], tol=TOL) and ok
    ok = _ok("Recontact after all-weeks", round(recontact_rate(r2), 2), exp["recontact"], tol=TOL) and ok

    print("3) Source workbook (same formulas, independent of parquet)")
    src = DOWNLOADS_XLSX if DOWNLOADS_XLSX.exists() else SOURCE_XLSX
    if src.exists():
        print(f"  workbook: {src}")
        raw = excel_csat_rc(src)
        ok = _ok("Excel CSAT Score", raw["csat"], exp["csat"], tol=TOL) and ok
        ok = _ok("Excel surveys", raw["surveys"], exp["surveys"]) and ok
        ok = _ok("Excel star sum", raw["star_sum"], exp["surveys"]) and ok
        ok = _ok("Excel Recontact Rate", raw["recontact"], exp["recontact"], tol=TOL) and ok
        ok = _ok("Excel contacts", raw["contacts"], exp["contacts"]) and ok
    else:
        print("  workbook missing — skipped")

    print("\n" + ("CONTROL TOTALS PASSED." if ok else "CONTROL TOTALS FAILED."))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
