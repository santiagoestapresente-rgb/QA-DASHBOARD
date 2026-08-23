"""Restore the last stable dashboard (commit 2c59710: 80% zoom, before live-filter CSS).

Usage, from the repo root:

    python backups/restore_dashboard.py

This overwrites app.py and .streamlit/config.toml only. It does not touch
KPI formulas, data files, or git history.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent


def main() -> None:
    src_app = HERE / "app_restore_2c59710.py"
    src_cfg = HERE / "config_restore_2c59710.toml"
    if not src_app.exists() or not src_cfg.exists():
        raise SystemExit("Backup files missing next to this script.")
    shutil.copy2(src_app, ROOT / "app.py")
    shutil.copy2(src_cfg, ROOT / ".streamlit" / "config.toml")
    print("Restored app.py and .streamlit/config.toml from 2c59710.")
    print("Restart Streamlit to load the restored files.")


if __name__ == "__main__":
    main()
