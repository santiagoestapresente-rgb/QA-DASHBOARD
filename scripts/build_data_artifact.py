"""
Build the packaged parquet snapshot consumed by the dashboard at runtime.

Reads `data/Business Case.xlsx`, rebuilds the fact/dimension model and writes one
zstd-compressed parquet file per table into `data/packaged/`. Those files are
versioned in the repo so the app runs on Streamlit Community Cloud with no
dependency on any path outside the project.

Usage:
    python scripts/build_data_artifact.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import PACKAGED_DIR  # noqa: E402
from modules.data_loader import build_from_source, load_packaged, write_packaged  # noqa: E402
from modules.kpis import avg_qa_score, overall_csat, overall_fcr  # noqa: E402

# Control totals for the full dataset (Business Case, all weeks).
EXPECTED = {"qa": 94.14, "csat": 79.95, "recontact": 5.83}
TOLERANCE = 0.01


def control_totals(data: dict) -> dict[str, float]:
    return {
        "qa": round(avg_qa_score(data["fact_audits"]), 2),
        "csat": round(overall_csat(data["fact_csat"]), 2),
        "recontact": round(100 - overall_fcr(data["fact_recontact"]), 2),
    }


def main() -> int:
    print("Reading source workbook and rebuilding the model...")
    data = build_from_source()

    print("\nRows per table:")
    for name, df in data.items():
        print(f"  {name:18} {len(df):>7,} rows x {len(df.columns):>2} cols")

    sizes = write_packaged(data)
    total = sum(sizes.values())
    print(f"\nWritten to {PACKAGED_DIR}:")
    for name, size in sizes.items():
        print(f"  {name + '.parquet':30} {size / 1024:>9,.1f} KB")
    print(f"  {'TOTAL':30} {total / 1024 / 1024:>9,.2f} MB")

    print("\nRe-reading the snapshot and checking control totals:")
    reloaded = load_packaged()
    actual = control_totals(reloaded)
    ok = True
    for key, expected in EXPECTED.items():
        got = actual[key]
        match = abs(got - expected) <= TOLERANCE
        ok = ok and match
        print(f"  {key:10} expected {expected:>7.2f}  got {got:>7.2f}  {'OK' if match else 'MISMATCH'}")

    for name, df in reloaded.items():
        if len(df) != len(data[name]):
            print(f"  ROW COUNT MISMATCH in {name}: {len(data[name])} -> {len(df)}")
            ok = False

    print("\n" + ("Snapshot built and verified." if ok else "Snapshot built BUT verification FAILED."))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
