"""DiDi CX Dashboard v2 API.

Read-only consumer of v1 `modules/kpis.py` and packaged parquet.
Does not import app.py. Does not write Streamlit config or formulas.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import (  # noqa: E402
    CONTROL_TOTALS,
    COUNTRY_NAMES,
    CSAT_GOAL,
    QA_GOAL,
    RECONTACT_GOAL,
    TENURE_SOURCE_ORDER,
)
from modules.data_loader import load_all_data  # noqa: E402
from modules import kpis as K  # noqa: E402

from dashboard_v2.backend.filters import apply_filters  # noqa: E402
from dashboard_v2.backend import pack as P  # noqa: E402
from dashboard_v2.backend.serialize import clean, traffic  # noqa: E402

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"


def _k(*names):
    for n in names:
        fn = getattr(K, n, None)
        if callable(fn):
            return fn
    raise AttributeError(f"modules.kpis has none of {names}")


app = FastAPI(title="DiDi CX Dashboard v2", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def _data() -> dict[str, pd.DataFrame]:
    return load_all_data()


def _all_weeks() -> list[str]:
    audits = _data()["fact_audits"]
    return sorted(audits["Week"].dropna().astype(str).unique().tolist())


def _parse_weeks(raw: str | None) -> list[str]:
    all_weeks = _all_weeks()
    if not raw or raw.strip().lower() in {"all", "*"}:
        return all_weeks
    wanted = [w.strip() for w in raw.split(",") if w.strip()]
    return [w for w in wanted if w in set(all_weeks)] or all_weeks


def _opts(series: pd.Series) -> list[str]:
    return sorted(
        {
            str(v).strip()
            for v in series.dropna().tolist()
            if str(v).strip() and str(v).strip().lower() != "nan"
        }
    )


def _slice(
    *,
    weeks: list[str],
    channel: str,
    country: str,
    day: str,
    lob: str,
    cr_lv1: str,
    cr: str,
    sub_cr: str,
    tenure: str,
    business_type: str,
):
    data = _data()
    audits_all = data["fact_audits"]
    errors_all = data["fact_errors"]
    csat_all = data["fact_csat"]
    rc_all = data["fact_recontact"]
    lookup = _k("cr_group_lookup", "cr_group_lookup")(csat_all)
    f = {
        "weeks": weeks,
        "day": day or "All",
        "channel": channel or "All",
        "country": country or "All",
        "lob": lob or "All",
        "cr_lv1": cr_lv1 or "All",
        "cr": cr or "All",
        "sub_cr": sub_cr or "All",
        "requester": "All",
        "tenure": tenure or "All",
        "supervisor": "All",
        "agent": "All",
        "audit_type": "All",
        "special_project": "All",
        "business_type": business_type or "All",
        "cr_lookup": lookup,
    }
    return apply_filters(audits_all, errors_all, csat_all, rc_all, f, audits_all)


def _kpis(audits, csat, rc) -> dict:
    summary = _k("kpi_summary", "kpi_summary")(audits, csat, rc)
    vols = _k("volume_totals", "volume_totals")(audits, csat, rc)
    qa = clean(summary.get("qa_score"))
    csat_v = clean(summary.get("csat"))
    rate_fn = _k("recontact_rate", "recontact_rate")
    rc_v = round(rate_fn(rc), 2) if rc is not None and not rc.empty else None
    return {
        "qa": qa,
        "qa_n": int(summary.get("audit_count") or vols.get("evaluations") or 0),
        "qa_traffic": traffic(qa, QA_GOAL, higher=True),
        "fatal": clean(summary.get("fatal_rate")),
        "csat": csat_v,
        "csat_n": int(vols["surveys"]),
        "csat_traffic": traffic(csat_v, CSAT_GOAL, higher=True),
        "recontact": rc_v,
        "recontact_n": int(vols["contacts"]),
        "recontact_traffic": traffic(rc_v, RECONTACT_GOAL, higher=False),
        "surveys": int(vols["surveys"]),
        "contacts": int(vols["contacts"]),
        "recontacts": int(vols["recontacts"]),
        "evaluations": int(vols["evaluations"]),
        "agents": int(summary.get("agent_count") or 0),
        "fcr": clean(summary.get("fcr")),
    }


def _weekly_mix(audits, csat, rc) -> list[dict]:
    rows: dict[str, dict] = {}
    iso = _k("iso_week_label", "iso_week_label")
    csat_fn = _k("overall_csat", "overall_csat")
    rc_fn = _k("recontact_rate", "recontact_rate")
    if not audits.empty and "Week" in audits.columns:
        qa = _k("weekly_trends", "weekly_trends")(audits)
        for _, r in qa.iterrows():
            wk = str(r["Week"])
            rows.setdefault(wk, {"Week": wk})
            rows[wk]["QA_Score"] = clean(r["QA_Score"])
            rows[wk]["Audit_Count"] = clean(r.get("Audit_Count"))
    if not csat.empty and "Fecha" in csat.columns:
        tmp = csat.copy()
        tmp["_w"] = iso(tmp["Fecha"])
        for wk, g in tmp.groupby("_w"):
            key = str(wk)
            rows.setdefault(key, {"Week": key})
            rows[key]["CSAT_Score"] = round(csat_fn(g), 2)
            fb_col = "Feedback CNT" if "Feedback CNT" in g.columns else "Feedback CNT"
            rows[key]["Surveys"] = int(pd.to_numeric(g[fb_col], errors="coerce").fillna(0).sum()) if fb_col in g.columns else 0
    if not rc.empty and "Fecha" in rc.columns:
        tmp = rc.copy()
        tmp["_w"] = iso(tmp["Fecha"])
        for wk, g in tmp.groupby("_w"):
            key = str(wk)
            rows.setdefault(key, {"Week": key})
            rows[key]["Recontact_Rate"] = round(rc_fn(g), 2)
            rows[key]["Contacts"] = int(pd.to_numeric(g["Contacts"], errors="coerce").fillna(0).sum())
    return [rows[k] for k in sorted(rows)]


@app.get("/api/meta")
def meta():
    data = _data()
    audits, csat = data["fact_audits"], data["fact_csat"]
    countries = set()
    if "Country" in audits.columns:
        countries.update(_opts(audits["Country"]))
    if "Country Code" in csat.columns:
        countries.update(_opts(csat["Country Code"]))
    tenure = []
    ten_col = "Tenure_Cohort" if "Tenure_Cohort" in audits.columns else None
    if ten_col:
        present = set(_opts(audits[ten_col]))
        tenure = [t for t in TENURE_SOURCE_ORDER if t in present]
        tenure += sorted(x for x in present if x not in set(tenure) and x != "Unknown")
        if "Unknown" in present:
            tenure.append("Unknown")
    biz_col = "Business_Type" if "Business_Type" in csat.columns else (
        "Business Type Name" if "Business Type Name" in csat.columns else None
    )
    days = []
    if "Fecha" in audits.columns:
        days = sorted({pd.Timestamp(x).strftime("%Y-%m-%d") for x in pd.to_datetime(audits["Fecha"], errors="coerce").dropna()})
    return {
        "version": "2.0.0",
        "source": "v1 packaged snapshot via modules/kpis.py",
        "goals": {"qa": QA_GOAL, "csat": CSAT_GOAL, "recontact": RECONTACT_GOAL},
        "control": CONTROL_TOTALS,
        "weeks": _all_weeks(),
        "channels": ["All", "Phone", "Live Chat"],
        "countries": [{"id": "All", "label": "All markets"}]
        + [{"id": c, "label": COUNTRY_NAMES.get(c, c)} for c in sorted(countries)],
        "lobs": ["All"] + (_opts(audits["LOB"]) if "LOB" in audits.columns else []),
        "tenure": ["All"] + tenure,
        "business_types": ["All"] + (_opts(csat[biz_col]) if biz_col else []),
        "days": ["All"] + days,
        "note": "Recontact has no market field (region is always SSL).",
        "as_of": "May 2026 snapshot",
    }


@app.get("/api/dashboard")
def dashboard(
    page: str = Query("overview"),
    weeks: str = Query("all"),
    channel: str = Query("All"),
    country: str = Query("All"),
    day: str = Query("All"),
    lob: str = Query("All"),
    cr_lv1: str = Query("All"),
    cr: str = Query("All"),
    sub_cr: str = Query("All"),
    tenure: str = Query("All"),
    business_type: str = Query("All"),
):
    page = (page or "overview").strip().lower()
    week_list = _parse_weeks(weeks)
    audits, errors, csat, rc = _slice(
        weeks=week_list,
        channel=channel,
        country=country,
        day=day,
        lob=lob,
        cr_lv1=cr_lv1,
        cr=cr,
        sub_cr=sub_cr,
        tenure=tenure,
        business_type=business_type,
    )
    kpis = _kpis(audits, csat, rc)
    payload: dict = {
        "page": page,
        "filters": {
            "weeks": week_list,
            "channel": channel,
            "country": country,
            "day": day,
            "lob": lob,
            "tenure": tenure,
            "business_type": business_type,
        },
        "goals": {"qa": QA_GOAL, "csat": CSAT_GOAL, "recontact": RECONTACT_GOAL},
        "kpis": kpis,
        "slice_note": (
            f"Channel {channel} · Market {COUNTRY_NAMES.get(country, country)} · "
            + ("all weeks" if week_list == _all_weeks() else ", ".join(week_list))
        ),
    }

    weekly = _weekly_mix(audits, csat, rc)
    ov = getattr(P, "overview_pack", None) or getattr(P, "overview_pack")
    qa = getattr(P, "qa_pack", None) or getattr(P, "qa_pack")
    cs = getattr(P, "csat_pack", None) or getattr(P, "csat_pack")
    rec = getattr(P, "recontact_pack", None) or getattr(P, "recontact_pack")
    al = getattr(P, "alerts_pack", None) or getattr(P, "alerts_pack", None)

    if page in {"overview", "quality", "definitions"}:
        payload["overview"] = ov(audits, errors, csat, rc, kpis, weekly, _data()["fact_csat"])
    elif page == "qa":
        payload["qa"] = qa(audits, errors, csat, rc, weekly)
    elif page == "csat":
        payload["csat"] = cs(audits, csat, rc, kpis, weekly)
    elif page == "recontact":
        payload["recontact"] = rec(audits, csat, rc, weekly)
    elif page in {"alerts", "agents"}:
        payload["alerts"] = al(audits, errors, csat) if al else {}
        payload["qa"] = qa(audits, errors, csat, rc, weekly)
    return payload


if FRONTEND.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND / "assets"), name="assets")

    @app.get("/")
    def index():
        return FileResponse(FRONTEND / "index.html")
