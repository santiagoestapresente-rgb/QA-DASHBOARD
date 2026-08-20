"""
Deployment smoke test — run before pushing.

Checks that the dashboard's data layer works exactly as it will in the cloud:
  1. The packaged parquet snapshot exists and is the path actually used.
  2. Every module imported by app.py imports cleanly.
  3. Row counts and the three control totals match the Business Case.

Usage:
    python scripts/smoke_test_deploy.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import CONTROL_TOTALS, PACKAGED_DIR, SOURCE_XLSX  # noqa: E402
from modules.data_loader import has_packaged_snapshot, load_all_data  # noqa: E402
from modules.kpis import avg_qa_score, overall_csat, overall_fcr  # noqa: E402

EXPECTED_TOTALS = {
    "QA Score": CONTROL_TOTALS["qa"],
    "CSAT Score": CONTROL_TOTALS["csat"],
    "Recontact Rate": CONTROL_TOTALS["recontact"],
}
EXPECTED_ROWS = {
    "fact_audits": 2460,
    "fact_errors": 518,
    "fact_csat": 76754,
    "fact_recontact": 14095,
    "dim_agents": 263,
    "dim_supervisors": 31,
    "dim_error_types": 17,
    "dim_kpis": 4,
    "cr_impact": 100,
}


def check_imports() -> bool:
    """Import every runtime module app.py depends on."""
    mods = [
        "config",
        "modules.data_loader",
        "modules.kpis",
        "modules.dashboard_charts",
        "modules.executive_engine",
        "modules.insights",
        "modules.recommendations",
        "modules.charts",
    ]
    ok = True
    for mod in mods:
        try:
            __import__(mod)
            print(f"  OK       {mod}")
        except Exception as exc:
            ok = False
            print(f"  FAILED   {mod}: {exc}")
    return ok


def main() -> int:
    ok = True

    print("1) Packaged snapshot")
    packaged = has_packaged_snapshot()
    print(f"  snapshot dir : {PACKAGED_DIR}")
    print(f"  complete     : {packaged}")
    if packaged:
        size = sum(p.stat().st_size for p in PACKAGED_DIR.glob('*.parquet'))
        print(f"  total size   : {size / 1024 / 1024:.2f} MB")
    else:
        ok = False
        print("  -> The app would fall back to Excel. Run scripts/build_data_artifact.py.")
    print(f"  source xlsx  : {'present' if SOURCE_XLSX.exists() else 'absent'} (fallback only)")

    print("\n2) Runtime imports")
    ok = check_imports() and ok

    print("\n3) Data load (same call path as the app)")
    data = load_all_data()
    for name, expected in EXPECTED_ROWS.items():
        got = len(data[name])
        match = got == expected
        ok = ok and match
        print(f"  {name:18} {got:>7,} rows  (expected {expected:,})  {'OK' if match else 'MISMATCH'}")

    print("\n4) Control totals")
    actual = {
        "QA Score": round(avg_qa_score(data["fact_audits"]), 2),
        "CSAT Score": round(overall_csat(data["fact_csat"]), 2),
        "Recontact Rate": round(100 - overall_fcr(data["fact_recontact"]), 2),
    }
    for label, expected in EXPECTED_TOTALS.items():
        got = actual[label]
        match = abs(got - expected) <= 0.01
        ok = ok and match
        print(f"  {label:16} expected {expected:>7.2f}  got {got:>7.2f}  {'OK' if match else 'MISMATCH'}")

    print("\n5) Excel vs snapshot vs all-weeks filter")
    import runpy
    verify = runpy.run_path(str(ROOT / "scripts" / "verify_control_totals.py"))
    ok = (verify["main"]() == 0) and ok

    print("\n" + ("SMOKE TEST PASSED - ready to deploy." if ok else "SMOKE TEST FAILED."))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
