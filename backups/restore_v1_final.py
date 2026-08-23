"""Restore the Streamlit v1 final dashboard (animated KPI tiles, 100% zoom).

Usage, from the repo root:

    python backups/restore_v1_final.py

Overwrites app.py, modules/dashboard_charts.py, and .streamlit/config.toml only.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent / "v1_final"


def main() -> None:
    if not (SRC / "app.py").exists():
        raise SystemExit(f"Missing backup at {SRC}")
    shutil.copy2(SRC / "app.py", ROOT / "app.py")
    shutil.copy2(SRC / "dashboard_charts.py", ROOT / "modules" / "dashboard_charts.py")
    shutil.copy2(SRC / "config.toml", ROOT / ".streamlit" / "config.toml")
    print("Restored Streamlit v1 final from backups/v1_final/.")
    print("Restart Streamlit to load it.")


if __name__ == "__main__":
    main()
