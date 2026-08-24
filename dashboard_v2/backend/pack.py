"""Page payloads for dashboard v2. Calls v1 KPI functions only."""

from __future__ import annotations

import inspect

import numpy as np
import pandas as pd

from config import COUNTRY_ISO3, CSAT_GOAL, QA_GOAL, RECONTACT_GOAL
from modules import kpis as K

from dashboard_v2.backend.serialize import clean, records


def _fn(*names, required: bool = True):
    for n in names:
        f = getattr(K, n, None)
        if callable(f):
            return f
    if required:
        raise AttributeError(f"modules.kpis has none of {names}")
    return None


_KW = {
    "top_n": ("top_n", "top_n", "n"),
    "cat_col": ("cat_col", "cat_col", "grain"),
    "lookup": ("lookup", "lookup"),
    "by_channel": ("by_channel", "by_channel"),
    "min_n": ("min_n", "min_n"),
    "level": ("level",),
    "csat": ("csat",),
}


def _call(names: tuple[str, ...], *args, required: bool = True, **kwargs):
    fn = _fn(*names, required=required)
    if fn is None:
        return pd.DataFrame()
    params = inspect.signature(fn).parameters
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
        return fn(*args, **kwargs)
    extra = {}
    for key, val in kwargs.items():
        if key in params:
            extra[key] = val
            continue
        for alt in _KW.get(key, ()):
            if alt in params:
                extra[alt] = val
                break
    return fn(*args, **extra)


def _hist(series: pd.Series, bins: int = 18) -> dict:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return {"x": [], "y": []}
    counts, edges = np.histogram(s, bins=bins)
    centers = ((edges[:-1] + edges[1:]) / 2).round(1).tolist()
    return {"x": centers, "y": [int(v) for v in counts.tolist()]}


def _csat_hist(csat: pd.DataFrame) -> dict:
    """Frequency histogram of CSAT % (or Score_Pct), 5-point bins 0–100."""
    raw = _call(("csat_score_histogram", "csat_score_histogram"), csat, required=False)
    lookup: dict[int, int] = {}
    if raw is not None and not getattr(raw, "empty", True):
        xcol = next((c for c in ("CSAT_Score", "Score") if c in raw.columns), raw.columns[0])
        ycol = next((c for c in ("Surveys", "Count", "n") if c in raw.columns), raw.columns[1] if len(raw.columns) > 1 else raw.columns[0])
        for _, row in raw.iterrows():
            try:
                lookup[int(round(float(row[xcol])))] = int(pd.to_numeric(row[ycol], errors="coerce") or 0)
            except (TypeError, ValueError):
                continue
    elif csat is not None and not csat.empty:
        col = next((c for c in ("CSAT_Pct", "Score_Pct", "CSAT_Score") if c in csat.columns), None)
        if col:
            filled = _hist(csat[col], bins=20)
            return filled
    xs = list(range(0, 101, 5))
    return {"x": xs, "y": [int(lookup.get(x, 0)) for x in xs]}


def _csat_daily(daily: pd.DataFrame, csat: pd.DataFrame) -> list[dict]:
    if daily is not None and not daily.empty and "CSAT_Score" in daily.columns:
        d = daily.loc[pd.to_numeric(daily["CSAT_Score"], errors="coerce").notna(), ["Date", "CSAT_Score"]]
        if not d.empty:
            return records(d)
    ctrl = _dates(_call(("csat_control_daily", "csat_control_daily"), csat, required=False))
    if ctrl is not None and not ctrl.empty and "Value" in ctrl.columns:
        out = ctrl[["Date", "Value"]].rename(columns={"Value": "CSAT_Score"})
        return records(out)
    return []


def _dates(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty or "Date" not in df.columns:
        return df if df is not None else pd.DataFrame()
    out = df.copy()
    out["Date"] = pd.to_datetime(out["Date"]).dt.strftime("%Y-%m-%d")
    return out


def _phone_chat(rc: pd.DataFrame) -> dict:
    tbl = _call(("recontact_channel_table", "recontact_channel_table"), rc)
    names, vals = [], []
    if tbl is not None and not tbl.empty and "Channel" in tbl.columns:
        key = tbl["Channel"].astype(str).str.strip().str.casefold()
        for name in ("Phone", "Live Chat"):
            n = int(pd.to_numeric(tbl.loc[key.eq(name.casefold()), "Contacts"], errors="coerce").fillna(0).sum())
            if n:
                names.append(name)
                vals.append(n)
    return {"names": names, "vals": vals, "n": int(sum(vals))}


def _score_col(audits: pd.DataFrame) -> str:
    for c in ("Score_Pct", "Score_Pct", "Score"):
        if c in audits.columns:
            return c
    return "Score_Pct"


def _qa_by_lob(audits: pd.DataFrame) -> list[dict]:
    avg = _fn("avg_qa_score", "avg_qa_score")
    if audits is None or audits.empty or "LOB" not in audits.columns:
        return []
    rows = []
    for lob, g in audits.groupby("LOB", dropna=False):
        rows.append({"LOB": str(lob), "QA_Score": clean(round(float(avg(g)), 2)), "n": int(len(g))})
    rows.sort(key=lambda r: r["n"], reverse=True)
    return rows


def _agents_summary(audits: pd.DataFrame) -> dict:
    agents = _call(("agent_scores", "agent_scores"), audits)
    empty = {"n": 0, "avg_qa": None, "bottom10_avg": None, "thin_n": 0, "low": [], "high": [], "unreliable": 0, "min_n": 5}
    if agents is None or agents.empty:
        return empty
    n_col = "Audit_Count" if "Audit_Count" in agents.columns else ("n" if "n" in agents.columns else None)
    rel_col = "Reliable" if "Reliable" in agents.columns else None
    score = pd.to_numeric(agents["QA_Score"], errors="coerce")
    n = int(len(agents))
    k = max(1, int(round(n * 0.1)))
    bottom = agents.assign(_qa=score).nsmallest(k, "_qa")
    thin = 0
    if n_col:
        thin = int((pd.to_numeric(agents[n_col], errors="coerce").fillna(0) < 5).sum())
    unreliable = int((~agents[rel_col]).sum()) if rel_col else 0
    reliable = agents[agents[rel_col]] if rel_col else agents
    low = reliable.sort_values("QA_Score").head(12) if not reliable.empty else reliable
    high = reliable.sort_values("QA_Score", ascending=False).head(8) if not reliable.empty else reliable
    return {
        "n": n,
        "avg_qa": clean(round(float(score.mean()), 2)) if score.notna().any() else None,
        "bottom10_avg": clean(round(float(pd.to_numeric(bottom["QA_Score"], errors="coerce").mean()), 2)) if not bottom.empty else None,
        "thin_n": thin,
        "low": records(low),
        "high": records(high),
        "unreliable": unreliable,
        "min_n": 5,
    }


def _clean_obj(x):
    if isinstance(x, dict):
        return {k: _clean_obj(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_clean_obj(v) for v in x]
    return clean(x)


def _head(df, n: int = 12):
    if df is None or getattr(df, "empty", True):
        return []
    return records(df.head(n) if len(df) > n else df)


def _lookup(csat) -> dict:
    val = _call(("cr_group_lookup", "cr_group_lookup"), csat)
    return val if isinstance(val, dict) else {}


def _res_block(audits) -> dict:
    res = _call(("auditor_resolution_summary", "auditor_resolution_summary"), audits) or {}
    return {
        "rate": clean(res.get("rate")),
        "n_resolved": int(res.get("n_resolved") or 0),
        "n_not_resolved": int(res.get("n_not_resolved") or 0),
        "n_assessed": int(res.get("n_assessed") or 0),
        "abandon_rate": clean(res.get("abandon_rate")),
        "n_abandoned": int(res.get("n_abandoned") or 0),
        "n_audits": int(res.get("n_audits") or 0),
        "n_unres_process": int(res.get("n_unres_process") or 0),
        "n_unres_agent": int(res.get("n_unres_agent") or 0),
    }


def _aht_by(audits, grain: str, lookup=None, by_channel: bool = False):
    fn = _fn("qa_aht_by_cr", "qa_aht_by_cr")
    params = inspect.signature(fn).parameters
    kw = {}
    if "cat_col" in params:
        kw["cat_col"] = grain
    if lookup is not None:
        if "lookup" in params:
            kw["lookup"] = lookup
    if "by_channel" in params:
        kw["by_channel"] = by_channel
    return fn(audits, **kw)


def _corr_block(audits, csat, rc) -> dict:
    """Serialize v1 correlation frames. No new KPI math."""
    scatter = _call(("cr_level_metrics",), audits, csat, rc, required=False)
    corr = _call(("cr_correlation_summary",), scatter, required=False)
    aht = _aht_by(audits, "CR_Lv4", by_channel=True)
    if (
        aht is not None and not getattr(aht, "empty", True)
        and scatter is not None and not getattr(scatter, "empty", True)
        and "CR_Lv4" in aht.columns and "CR_Lv4" in scatter.columns
    ):
        keep = [c for c in ("CR_Lv4", "CSAT_Pct", "Recontact_Rate", "Feedback") if c in scatter.columns]
        aht = aht.merge(scatter[keep].drop_duplicates("CR_Lv4"), on="CR_Lv4", how="left")
    aht_corr = _call(("aht_correlation_summary",), aht, required=False)
    pts = scatter
    if pts is not None and not getattr(pts, "empty", True):
        pts = pts.head(120)
    aht_pts = aht
    if aht_pts is not None and not getattr(aht_pts, "empty", True):
        aht_pts = aht_pts.head(120)
    return {
        "cr": records(pts),
        "corr": records(corr),
        "aht": records(aht_pts),
        "aht_corr": records(aht_corr),
    }


def _agent_hists(agents: pd.DataFrame) -> dict:
    empty = {"qa": {"x": [], "y": []}, "n": {"x": [], "y": []}}
    if agents is None or getattr(agents, "empty", True):
        return empty
    score = pd.to_numeric(agents["QA_Score"], errors="coerce") if "QA_Score" in agents.columns else pd.Series(dtype=float)
    n_col = "Audit_Count" if "Audit_Count" in agents.columns else ("QA_n" if "QA_n" in agents.columns else ("n" if "n" in agents.columns else None))
    counts = pd.to_numeric(agents[n_col], errors="coerce") if n_col else pd.Series(dtype=float)
    return {"qa": _hist(score, bins=12), "n": _hist(counts, bins=8)}


def _band_counts(bands: dict) -> list[dict]:
    raw = (bands or {}).get("bands") or {}
    return [{"q": q, "n": int((raw.get(q) or {}).get("n") or 0)} for q in ("Q1", "Q2", "Q3", "Q4")]


def overview_pack(audits, errors, csat, rc, kpis: dict, weekly: list[dict], csat_all: pd.DataFrame) -> dict:
    finest = _call(("cr_finest_volume", "cr_finest_volume"), csat, top_n=None)
    bars = finest.head(10) if finest is not None and not finest.empty else finest
    named_n = int(bars["Feedback"].sum()) if bars is not None and not bars.empty and "Feedback" in bars.columns else 0
    top_attr = _call(("top_failing_attributes", "top_failing_attributes", "top_failing_attributes"), errors, audits, top_n=40)
    top_rc = _call(("recontact_by_cr",), rc, top_n=6, csat=csat)
    stars = _call(("csat_by_star_rating", "csat_by_star_rating"), csat)
    hi = lo = 0
    if stars is not None and not stars.empty and "Rating" in stars.columns:
        hi = int(stars.loc[stars["Rating"].isin(["5 Stars", "4 Stars"]), "Count"].sum())
        lo = int(stars.loc[stars["Rating"].isin(["3 Stars", "2 Stars", "1 Star"]), "Count"].sum())
    lookup = _call(("cr_group_lookup", "cr_group_lookup"), csat_all)
    lv1 = _call(("contact_volume_by_cr", "contact_volume_by_cr"), rc, level="lv1", lookup=lookup, top_n=8)
    lv4 = _call(("contact_volume_by_cr", "contact_volume_by_cr"), rc, level="lv4", top_n=8)
    aht = _call(("qa_aht_summary", "qa_aht_summary"), audits) or {}
    top_sub = None
    if finest is not None and not finest.empty:
        top = finest.iloc[0]
        cat = top["Cat"] if "Cat" in finest.columns else top.iloc[0]
        fb = int(top["Feedback"]) if "Feedback" in finest.columns else 0
        top_sub = {
            "name": str(cat),
            "n": fb,
            "pct": round(float(fb) / kpis["surveys"] * 100, 1) if kpis["surveys"] else 0.0,
        }
    markets = records(_call(("market_performance", "market_performance"), audits, csat, rc))
    for row in markets:
        iso = COUNTRY_ISO3.get(str(row.get("Country") or "").strip())
        row["iso3"] = iso
        row["ISO3"] = iso
    sup = _call(("supervisor_overview", "supervisor_overview"), audits, csat, min_n=5)
    if sup is not None and not sup.empty:
        sup = sup.copy()
        sup["QA_Gap"] = (QA_GOAL - pd.to_numeric(sup["QA_Score"], errors="coerce")).clip(lower=0)
        n = pd.to_numeric(sup["n"], errors="coerce").fillna(0)
        sup["QA_Impact"] = (sup["QA_Gap"] * n).round(1)
        if "CSAT_Score" in sup.columns:
            sup["CSAT_Gap"] = (CSAT_GOAL - pd.to_numeric(sup["CSAT_Score"], errors="coerce")).clip(lower=0)
            fb = pd.to_numeric(sup["Feedback"], errors="coerce").fillna(0) if "Feedback" in sup.columns else n
            sup["CSAT_Impact"] = (sup["CSAT_Gap"] * fb).round(1)
        sup = sup.sort_values("QA_Impact", ascending=False)
    aht_lv1 = _aht_by(audits, "CR_Lv1", lookup)
    aht_lv4 = _aht_by(audits, "CR_Lv4")
    aht_sub = _aht_by(audits, "SUB_CR")
    daily = _dates(_call(("daily_metrics_trend", "daily_metrics_trend"), audits, csat, rc))
    score_col = _score_col(audits)
    biz = _call(("csat_by_business_type",), csat, required=False)
    agents = _agents_summary(audits)
    by_ch = _call(("channel_performance", "channel_performance"), audits, csat, rc)
    if by_ch is not None and not getattr(by_ch, "empty", True) and csat is not None and not csat.empty and "Channel" in csat.columns:
        fb = "Feedback CNT" if "Feedback CNT" in csat.columns else None
        if fb:
            match = _fn("channel_match", required=False)
            ns = []
            for _, row in by_ch.iterrows():
                label = str(row.get("Segment") or "")
                if match and label in {"Phone", "Live Chat"}:
                    ns.append(int(pd.to_numeric(csat.loc[match(csat["Channel"], label), fb], errors="coerce").fillna(0).sum()))
                else:
                    ns.append(None)
            by_ch = by_ch.copy()
            by_ch["CSAT_N"] = ns
    return {
        "by_channel": records(by_ch),
        "by_market": markets,
        "weekly": weekly,
        "daily": records(daily),
        "volumes": _call(("daily_volume_series", "daily_volume_series"), audits, csat, rc),
        "hist_qa": _hist(audits[score_col] if not audits.empty and score_col in audits.columns else pd.Series(dtype=float)),
        "crit": {k: clean(v) for k, v in (_call(("critical_fail_stats", "critical_fail_stats"), audits, errors) or {}).items()},
        "aht": {
            "aht_min": clean(aht.get("aht_min") or aht.get("aht_min")),
            "aht_p50_min": clean(aht.get("aht_p50_min") or aht.get("aht_p50_min")),
            "n": int(aht.get("n") or 0),
        },
        "resolution": _res_block(audits),
        "stars": {"hi": hi, "lo": lo, "n": kpis["surveys"], "rows": records(stars)},
        "cr_lv1": records(lv1),
        "cr_lv4": records(lv4),
        "top_sub": top_sub,
        "phone_chat": _phone_chat(rc),
        "subcr": {"official_n": kpis["surveys"], "named_n": named_n, "bars": records(bars)},
        "taxonomy": records(_call(("cr_taxonomy_coverage", "cr_taxonomy_coverage"), csat)),
        "supervisors": records(sup.head(12) if sup is not None and not sup.empty else sup),
        "aht_lv1": records(aht_lv1.head(12) if aht_lv1 is not None and not aht_lv1.empty else aht_lv1),
        "aht_lv4": records(aht_lv4.head(12) if aht_lv4 is not None and not aht_lv4.empty else aht_lv4),
        "aht_sub": records(aht_sub.head(12) if aht_sub is not None and not aht_sub.empty else aht_sub),
        "failing": records(top_attr),
        "rc_reasons": records(top_rc.head(5) if top_rc is not None and not top_rc.empty else top_rc),
        "qa_by_lob": _qa_by_lob(audits),
        "csat_by_biz": records(biz),
        "agents": agents,
        "channels": records(_call(("recontact_channel_table", "recontact_channel_table"), rc)),
        "corr": _corr_block(audits, csat, rc),
        "goals": {"qa": QA_GOAL, "csat": CSAT_GOAL, "recontact": RECONTACT_GOAL},
    }


def qa_pack(audits, errors, csat, rc, weekly: list[dict]) -> dict:
    daily = _dates(_call(("daily_metrics_trend", "daily_metrics_trend"), audits, csat, rc))
    score_col = _score_col(audits)
    failing = _call(("top_failing_attributes", "top_failing_attributes", "top_failing_attributes"), errors, audits, top_n=40)
    pareto_src = _call(("pareto_errors_simple", "pareto_errors_simple"), errors)
    lookup = _lookup(csat)
    roster = _call(("qa_agent_roster", "qa_agent_roster"), audits, errors)
    quartiles = _call(("qa_agent_quartiles", "qa_agent_quartiles"), audits)
    bands_fn = _fn("quartile_band_summary", required=False)
    aht_lv4 = _aht_by(audits, "CR_Lv4")
    aht_sub = _aht_by(audits, "SUB_CR")
    control = _call(("qa_control_daily", "qa_control_daily"), audits)
    return {
        "weekly": records(_call(("weekly_trends", "weekly_trends"), audits)),
        "daily": records(daily),
        "hist": _hist(audits[score_col] if not audits.empty and score_col in audits.columns else pd.Series(dtype=float)),
        "failing": records(failing),
        "pareto": records(pareto_src),
        "by_cr": records(_call(("qa_score_by_cr", "qa_score_by_cr"), audits, top_n=12, min_n=3)),
        "fails_lv4": records(_call(("qa_fails_by_cr",), errors, top_n=10, cat_col="CR_Lv4")),
        "fails_sub": records(_call(("qa_fails_by_cr",), errors, top_n=10, cat_col="SUB_CR")),
        "fails_lv1": records(_call(("qa_fails_by_cr_group",), errors, lookup)),
        "tenure": records(_call(("tenure_qa_overview", "tenure_qa_overview"), audits)),
        "special": records(_call(("qa_by_special_project", "qa_by_special_project"), audits)),
        "audit_type": records(_call(("qa_by_audit_type", "qa_by_audit_type"), audits)),
        "by_channel": records(_call(("channel_performance", "channel_performance"), audits, csat, rc)),
        "crit": {k: clean(v) for k, v in (_call(("critical_fail_stats", "critical_fail_stats"), audits, errors) or {}).items()},
        "volumes": _call(("daily_volume_series", "daily_volume_series"), audits, csat, rc),
        "spark_weekly": weekly,
        "resolution": _res_block(audits),
        "qa_by_lob": _qa_by_lob(audits),
        "agents": _agents_summary(audits),
        "roster": _head(roster, 40),
        "quartiles": _head(quartiles, 40),
        "qa_bands": _clean_obj(bands_fn(quartiles) if bands_fn is not None else {}),
        "aht": {k: clean(v) if not isinstance(v, (list, dict)) else v for k, v in (_call(("qa_aht_summary", "qa_aht_summary"), audits) or {}).items()},
        "aht_lv4": _head(aht_lv4, 12),
        "aht_sub": _head(aht_sub, 12),
        "aht_channel": records(_call(("qa_aht_by_channel", "qa_aht_by_channel"), audits)),
        "control": records(_dates(control)),
        "corr": _corr_block(audits, csat, rc),
    }


def csat_pack(audits, csat, rc, kpis: dict, weekly: list[dict]) -> dict:
    finest = _call(("cr_finest_volume", "cr_finest_volume"), csat, top_n=None)
    bars = finest.head(10) if finest is not None and not finest.empty else finest
    voc = _call(("voc_all_comments", "voc_all_comments"), csat) or {}
    daily = _dates(_call(("daily_metrics_trend", "daily_metrics_trend"), audits, csat, rc))
    stars = _call(("csat_by_star_rating", "csat_by_star_rating"), csat)
    hi = lo = 0
    if stars is not None and not stars.empty and "Rating" in stars.columns:
        hi = int(stars.loc[stars["Rating"].isin(["5 Stars", "4 Stars"]), "Count"].sum())
        lo = int(stars.loc[stars["Rating"].isin(["3 Stars", "2 Stars", "1 Star"]), "Count"].sum())
    pol = voc.get("polarity") if isinstance(voc, dict) else None
    biz = _call(("csat_by_business_type",), csat, required=False)
    lookup = _lookup(csat)
    return {
        "stars": records(stars),
        "hi": hi,
        "lo": lo,
        "voc": records(_call(("voc_themes_negative", "voc_themes_negative"), csat, top_n=8)),
        "comments": {
            "n_real": int(voc.get("n_real") or voc.get("n_real") or 0),
            "n_positive": int(voc.get("n_positive") or voc.get("n_positive") or 0),
            "n_negative": int(voc.get("n_negative") or voc.get("n_negative") or 0),
            "polarity": records(pol) if isinstance(pol, pd.DataFrame) else [],
        },
        "daily": records(daily),
        "csat_daily": _csat_daily(daily, csat),
        "hist": _csat_hist(csat),
        "subcr": {
            "official_n": kpis["surveys"],
            "named_n": int(bars["Feedback"].sum()) if bars is not None and not bars.empty and "Feedback" in bars.columns else 0,
            "bars": records(bars),
        },
        "spark_weekly": weekly,
        "volumes": _call(("daily_volume_series", "daily_volume_series"), audits, csat, rc),
        "by_channel": records(_call(("channel_performance", "channel_performance"), audits, csat, rc)),
        "csat_by_biz": records(biz),
        "taxonomy": records(_call(("cr_taxonomy_coverage", "cr_taxonomy_coverage"), csat)),
        "by_cr_lv4": records(_call(("csat_score_by_cr",), csat, level="lv4")),
        "by_cr_lv1": records(_call(("csat_score_by_cr",), csat, level="lv1", lookup=lookup)),
        "vol_lv4": records(_call(("csat_volume_by_cr",), csat, level="lv4")),
        "vol_lv1": records(_call(("csat_volume_by_cr",), csat, level="lv1", lookup=lookup)),
        "unsat_cr": records(_call(("csat_unsatisfied_by_cr",), csat)),
        "supervisors": records(_call(("csat_by_supervisor",), csat, audits)),
        "control": records(_dates(_call(("csat_control_daily", "csat_control_daily"), csat))),
        "corr": _corr_block(audits, csat, rc),
    }


def recontact_pack(audits, csat, rc, weekly: list[dict]) -> dict:
    daily = _dates(_call(("daily_metrics_trend", "daily_metrics_trend"), audits, csat, rc))
    lookup = _lookup(csat)
    fcr_fn = _fn("overall_fcr", required=False)
    return {
        "dilution": {k: clean(v) for k, v in (_call(("recontact_dilution_stats", "recontact_dilution_stats"), rc) or {}).items()},
        "channels": records(_call(("recontact_channel_table", "recontact_channel_table"), rc)),
        "by_cr": records(_call(("recontact_by_cr",), rc, top_n=10, csat=csat)),
        "by_lv1": records(_call(("recontact_by_cr_group",), rc, lookup)),
        "by_sub": records(_call(("recontact_by_cr",), rc, top_n=10, cat_col="SUB_CR", csat=csat)),
        "daily": records(daily),
        "spark_weekly": weekly,
        "volumes": _call(("daily_volume_series", "daily_volume_series"), audits, csat, rc),
        "phone_chat": _phone_chat(rc),
        "control": records(_dates(_call(("recontact_control_daily", "recontact_control_daily"), rc))),
        "fcr": clean(fcr_fn(rc)) if fcr_fn is not None and rc is not None and not rc.empty else None,
        "goal": RECONTACT_GOAL,
        "corr": _corr_block(audits, csat, rc),
    }


def alerts_pack(audits, errors=None, csat=None) -> dict:
    out = _agents_summary(audits)
    qa_q = _call(("qa_agent_quartiles", "qa_agent_quartiles"), audits)
    csat_q = _call(("csat_agent_quartiles",), csat if csat is not None else pd.DataFrame(), audits, required=False)
    bands_fn = _fn("quartile_band_summary", required=False)
    roster = _call(("qa_agent_roster", "qa_agent_roster"), audits, errors)
    conc = _call(("qa_agent_fail_concentrators",), errors if errors is not None else pd.DataFrame(), audits, required=False)
    mix = _call(("supervisor_quartile_mix",), qa_q, required=False)
    qa_bands = _clean_obj(bands_fn(qa_q) if bands_fn is not None else {})
    csat_bands = _clean_obj(bands_fn(csat_q) if bands_fn is not None else {})
    out.update({
        "qa_quartiles": _head(qa_q, 40),
        "csat_quartiles": _head(csat_q, 40),
        "qa_bands": qa_bands,
        "csat_bands": csat_bands,
        "q_counts": _band_counts(qa_bands),
        "hists": _agent_hists(qa_q),
        "roster": _head(roster, 40),
        "concentrators": _head(conc, 15),
        "supervisor_mix": _head(mix, 12),
    })
    return out
