"""CR / SUB_CR resolution vs CSAT plus 5-whys themes. Not an official KPI."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from modules.kpis import association_r2

_NR_RULES = [
    ("placeholder", r"no se proporcion"),
    ("fraud_review", r"fraud|anti.?fraud|revision anti"),
    ("policy_blocked", r"pol[ií]tica|no (?:era |es )?posible|no (?:se )?(?:aplica|permit)|reembolso no|no.*reembolso|no es aplicable"),
    ("tools_system", r"sistema|herramient|no conect|falla t[eé]cn|plataforma|escalar"),
    ("delay_eta", r"retras|demor|eta\b|no llega|tiempo estimado"),
    ("courier_store", r"repartidor|mensajero|tienda|restaurante|courier"),
    ("agent_miss", r"agente no (?:resolv|hizo|sigui|aplic|comprend|escuch)|no sigui[oó] el proceso"),
]

_RES_RULES = [
    ("placeholder", r"no se proporcion"),
    ("refund_confirmed", r"reembolso|compens"),
    ("explained_process", r"explic|resolvi[oó] su duda|confirm[oó]|inform[oó]"),
    ("tools_or_report", r"herramient|reporte|escal"),
    ("cancelled", r"cancel"),
]


def _fold(s: pd.Series) -> pd.Series:
    return s.astype("string").str.strip().str.casefold()


def _fold_sub(s: pd.Series) -> pd.Series:
    """Join SUB_CR labels that only differ by plural / (s)."""
    return (
        _fold(s)
        .str.replace(r"\(s\)", "", regex=True)
        .str.replace(r"\bitems\b", "item", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def _theme(text: str, rules: list[tuple[str, str]]) -> str:
    try:
        raw = "" if pd.isna(text) else str(text)
    except (TypeError, ValueError):
        raw = "" if text is None else str(text)
    raw = raw.replace("<NA>", "").strip()
    low = raw.casefold()
    if len(raw) < 40 or low.startswith("no aplica"):
        return "no_analysis"
    for name, pat in rules:
        if re.search(pat, low):
            return name
    return "other"


def _csat_grain(audits: pd.DataFrame, csat: pd.DataFrame, key: str, min_assessed: int, min_fb: int) -> pd.DataFrame:
    a = audits.copy()
    c = csat.copy()
    folder = _fold_sub if key == "SUB_CR" else _fold
    a["_k"] = folder(a[key]) if key in a.columns else _fold(a["CR_Lv4"])
    c["_k"] = folder(c[key]) if key in c.columns else _fold(c["CR_Lv4"])
    a["_sol"] = a["Solution_Provided"].astype("string").str.strip()
    assessed = a[a["_sol"].isin(["Resolved", "Not resolved"])].copy()
    assessed["res"] = assessed["_sol"].eq("Resolved").astype(int)
    g = assessed.groupby("_k").agg(
        name=(key if key in assessed.columns else "CR_Lv4", "first"),
        parent=("CR_Lv4", "first"),
        n=("Audit_ID", "count"),
        n_res=("res", "sum"),
    )
    g["n_nr"] = g["n"] - g["n_res"]
    g["pct_res"] = g["n_res"] / g["n"] * 100
    cs = c.groupby("_k").agg(
        fb=("Feedback CNT", "sum"),
        sat=("Satisfied_CNT", "sum"),
        csat_name=(key if key in c.columns else "CR_Lv4", "first"),
    )
    cs["csat"] = np.where(cs["fb"] > 0, cs["sat"] / cs["fb"] * 100, np.nan)
    m = g.join(cs, how="inner")
    m = m[(m["n"] >= min_assessed) & (m["fb"] >= min_fb)].copy()

    def bucket(row) -> str:
        if row.pct_res >= 70 and row.csat >= 85:
            return "A"
        if row.pct_res <= 50 and row.csat < 85:
            return "B"
        if row.pct_res >= 70 and row.csat < 85:
            return "C"
        return "M"

    m["bucket"] = m.apply(bucket, axis=1)
    r = float(m["pct_res"].corr(m["csat"])) if len(m) >= 5 else float("nan")
    m.attrs["r"] = r
    m.attrs["r2"] = association_r2(r) if pd.notna(r) else None
    return m


def _crmix_csat(audits: pd.DataFrame, csat: pd.DataFrame) -> dict:
    """Official CSAT of each audit's CR, averaged across audits. Not ticket CSAT."""
    a = audits.copy()
    a["_k"] = _fold(a["CR_Lv4"])
    cs = csat.copy()
    cs["_k"] = _fold(cs["CR_Lv4"])
    g = cs.groupby("_k").agg(fb=("Feedback CNT", "sum"), sat=("Satisfied_CNT", "sum"))
    g["csat"] = np.where(g["fb"] > 0, g["sat"] / g["fb"] * 100, np.nan)
    m = a.merge(g[["csat"]], left_on="_k", right_index=True, how="left")
    w = m.dropna(subset=["csat"])
    return {
        "n": int(len(a)),
        "n_with_cr": int(len(w)),
        "csat": round(float(w["csat"].mean()), 1) if len(w) else None,
    }


def _counts(series: pd.Series) -> dict[str, int]:
    return {str(k): int(v) for k, v in series.value_counts().items()}


def _quote(df: pd.DataFrame, theme: str, cue: str) -> dict | None:
    sl = df[df["_theme"].eq(theme) & df["_low"].str.contains(cue, regex=True, na=False)]
    if sl.empty:
        sl = df[df["_theme"].eq(theme)]
    if sl.empty:
        return None
    row = sl.iloc[0]
    return {
        "cr": str(row["CR_Lv4"])[:56],
        "process": str(row["Process_Adherence"]),
        "text": " ".join(str(row["Five_Whys"]).split())[:280],
    }


def _node(r) -> dict:
    return {
        "name": str(r["name"]),
        "parent": str(r["parent"]),
        "pct_res": round(float(r["pct_res"]), 1),
        "csat": round(float(r["csat"]), 1),
        "n": int(r["n"]),
        "fb": int(r["fb"]),
        "n_nr": int(r["n_nr"]),
        "bucket": str(r["bucket"]),
    }


def _rows(frame: pd.DataFrame, bucket: str, n: int) -> list[dict]:
    sl = frame[frame["bucket"].eq(bucket)].sort_values(
        ["csat", "fb"], ascending=[bucket != "A", False]
    )
    return [_node(r) for _, r in sl.head(n).iterrows()]


def _branches(parents: list[dict], sub: pd.DataFrame, max_kids: int = 3) -> list[dict]:
    out = []
    for p in parents:
        key = str(p["name"]).strip().casefold()
        kids = sub[sub["parent"].astype(str).str.strip().str.casefold().eq(key)]
        kids = kids.sort_values("fb", ascending=False)
        children = [_node(r) for _, r in kids.head(max_kids).iterrows()]
        item = dict(p)
        item["children"] = children
        out.append(item)
    return out


def resolution_story(audits: pd.DataFrame, csat: pd.DataFrame) -> dict:
    """Hierarchy + 5-whys for the Entregable 2 resolution/CSAT slides."""
    cr = _csat_grain(audits, csat, "CR_Lv4", 3, 20)
    sub = _csat_grain(audits, csat, "SUB_CR", 5, 20)
    sub_kids = _csat_grain(audits, csat, "SUB_CR", 3, 10)
    a = audits.copy()
    a["_sol"] = a["Solution_Provided"].astype("string").str.strip()
    nr = a[a["_sol"].eq("Not resolved")].copy()
    rs = a[a["_sol"].eq("Resolved")].copy()
    nr["_theme"] = nr["Five_Whys"].astype("string").fillna("").map(lambda t: _theme(t, _NR_RULES))
    rs["_theme"] = rs["Five_Whys"].astype("string").fillna("").map(lambda t: _theme(t, _RES_RULES))
    nr["_low"] = nr["Five_Whys"].astype("string").fillna("").str.casefold()
    rs["_low"] = rs["Five_Whys"].astype("string").fillna("").str.casefold()
    fol = nr[nr["Process_Adherence"].astype(str).eq("Followed process")]
    cr_a = _rows(cr, "A", 4)
    cr_b = _rows(cr, "B", 4)
    cr_c = _rows(cr, "C", 3)
    fraud_key = "after sales user fraud (under anti fraud review)"
    fraud_a = a[_fold(a["CR_Lv4"]).eq(fraud_key)] if "CR_Lv4" in a.columns else a.iloc[0:0]
    fraud_sol = fraud_a["Solution_Provided"].astype("string").str.strip()
    fraud_n_all = int(len(fraud_a))
    fraud_n_assessed = int(fraud_sol.isin(["Resolved", "Not resolved"]).sum())
    fraud_n_abandoned = int(fraud_sol.eq("Abandoned").sum())
    fc = csat[_fold(csat["CR_Lv4"]).eq(fraud_key)] if "CR_Lv4" in csat.columns else csat.iloc[0:0]
    ones_col = "Questionnaires With Star Level =1"
    fraud_fb = int(fc["Feedback CNT"].sum()) if not fc.empty else 0
    fraud_sat = int(fc["Satisfied_CNT"].sum()) if not fc.empty else 0
    fraud_ones = int(fc[ones_col].sum()) if ones_col in fc.columns and not fc.empty else 0
    return {
        "n_resolved": int((a["_sol"] == "Resolved").sum()),
        "n_not_resolved": int(len(nr)),
        "n_followed_nr": int(len(fol)),
        "cr_n": int(len(cr)),
        "cr_r2": cr.attrs.get("r2"),
        "cr_r": round(float(cr.attrs.get("r") or 0), 3),
        "sub_n": int(len(sub)),
        "sub_r2": sub.attrs.get("r2"),
        "cr_a": cr_a,
        "cr_b": cr_b,
        "cr_c": cr_c,
        "sub_a": _rows(sub, "A", 8),
        "sub_b": _rows(sub, "B", 8),
        "sub_c": _rows(sub, "C", 4),
        "tree_close": _branches(cr_a, sub_kids, max_kids=3),
        "tree_block": _branches(cr_b, sub_kids, max_kids=3),
        "csat_resolved_crmix": _crmix_csat(rs, csat),
        "csat_nr_crmix": _crmix_csat(nr, csat),
        "fraud_csat": {
            "fb": fraud_fb,
            "sat": fraud_sat,
            "ones": fraud_ones,
            "csat": round(100 * fraud_sat / fraud_fb, 1) if fraud_fb else None,
            "n_all": fraud_n_all,
            "n_assessed": fraud_n_assessed,
            "n_abandoned": fraud_n_abandoned,
        },
        "nr_themes": _counts(nr["_theme"]),
        "nr_followed_themes": _counts(fol["_theme"]),
        "res_themes": _counts(rs["_theme"]),
        "nr_quote_policy": _quote(nr, "policy_blocked", r"pol[ií]tica"),
        "nr_quote_tools": _quote(nr, "tools_system", r"herramient"),
        "res_quote_refund": _quote(rs, "refund_confirmed", r"reembolso"),
        "res_quote_explained": _quote(rs, "explained_process", r"explic"),
    }
