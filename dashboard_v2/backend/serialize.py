"""JSON-safe conversion for KPI frames. Does not change formulas."""

from __future__ import annotations

import math

import pandas as pd


def clean(v):
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
    if isinstance(v, (pd.Timestamp,)):
        return v.strftime("%Y-%m-%d")
    return v


def records(df: pd.DataFrame, limit: int | None = None) -> list[dict]:
    if df is None or df.empty:
        return []
    work = df.head(int(limit)) if limit is not None else df
    out = []
    for _, row in work.iterrows():
        out.append({str(k): clean(v) for k, v in row.to_dict().items()})
    return out


def traffic(value: float | None, goal: float, *, higher: bool) -> str:
    if value is None:
        return "neutral"
    diff = (value - goal) if higher else (goal - value)
    if diff >= 0:
        return "green"
    if diff >= -5:
        return "amber"
    return "red"
