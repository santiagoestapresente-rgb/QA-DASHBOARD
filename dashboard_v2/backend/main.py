"""DiDi CX Dashboard v2 API — same KPI formulas as Streamlit v1."""

from __future__ import annotations

import math
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import (  # noqa: E402
    CSAT_GOAL,
    QA_GOAL,
    RECONTACT_GOAL,
)
from modules.data_loader import load_all_data  # noqa: E402
from modules.kpis import (  # noqa: E402
    channel_match,
    kpi_by_channel,
    kpi_summary,
    recontact_rate,
)

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"

app = FastAPI(title="DiDi CX Dashboard v2", version="2.0.0")


def _clean(v):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if hasattr(v, "item"):
        try:
            return v.item()
        except Exception:
            pass
    return v


def _traffic(value: float | None, goal: float, *, higher: bool) -> str:
    if value is None:
        return "neutral"
    diff = (value - goal) if higher else (goal - value)
    if diff >= 0:
        return "green"
    if diff >= -5:
        return "amber"
    return "red"


@lru_cache(maxsize=1)
def _data() -> dict[str, pd.DataFrame]:
    return load_all_data()


def _slice(channel: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    data = _data()
    audits, csat, rc = data["fact_audits"].copy(), data["fact_csat"].copy(), data["fact_recontact"].copy()
    if channel and channel != "All":
        if "Channel" in audits.columns:
            audits = audits[channel_match(audits["Channel"], channel)]
        if "Channel" in csat.columns:
            csat = csat[channel_match(csat["Channel"], channel)]
        col = "standard_channel_name" if "standard_channel_name" in rc.columns else "Channel"
        if col in rc.columns:
            rc = rc[channel_match(rc[col], channel)]
    return audits, csat, rc


@app.get("/api/overview")
def overview(channel: str = Query("All")):
    audits, csat, rc = _slice(channel)
    summary = kpi_summary(audits, csat, rc)
    qa = _clean(summary.get("qa_score"))
    csat_v = _clean(summary.get("csat"))
    rc_v = round(recontact_rate(rc), 2) if not rc.empty else None
    contacts = int(rc["Contacts"].sum()) if not rc.empty and "Contacts" in rc.columns else 0
    surveys = int(csat["Feedback CNT"].sum()) if not csat.empty and "Feedback CNT" in csat.columns else 0
    by_ch = kpi_by_channel(audits, csat, rc)
    channels = []
    if not by_ch.empty:
        for _, row in by_ch.iterrows():
            channels.append({k: _clean(v) for k, v in row.to_dict().items()})
    return {
        "channel": channel,
        "goals": {"qa": QA_GOAL, "csat": CSAT_GOAL, "recontact": RECONTACT_GOAL},
        "kpis": {
            "qa": qa,
            "qa_n": int(summary.get("audit_count") or 0),
            "qa_traffic": _traffic(qa, QA_GOAL, higher=True),
            "csat": csat_v,
            "csat_n": surveys,
            "csat_traffic": _traffic(csat_v, CSAT_GOAL, higher=True),
            "recontact": rc_v,
            "recontact_n": contacts,
            "recontact_traffic": _traffic(rc_v, RECONTACT_GOAL, higher=False),
            "surveys": surveys,
            "contacts": contacts,
        },
        "by_channel": channels,
    }


if FRONTEND.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND / "assets"), name="assets")

    @app.get("/")
    def index():
        return FileResponse(FRONTEND / "index.html")
