"""Short, data-driven reading notes for dashboard charts and tables."""

from __future__ import annotations

import pandas as pd

from config import CSAT_GOAL, QA_GOAL, RECONTACT_GOAL
from modules.kpis import add_pareto_cumulative


def _fmt(v, digits: int = 1, suffix: str = "") -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return f"{float(v):.{digits}f}{suffix}"


def _top_name(series: pd.Series) -> str:
    if series is None or series.empty:
        return "the top item"
    return str(series.iloc[0])[:48]


def _lead(scope: str) -> str:
    return f"{scope} " if scope else ""


def pareto_notes(df: pd.DataFrame, cat_col: str, count_col: str, unit: str, scope: str = "") -> list[str]:
    if df is None or df.empty or cat_col not in df.columns or count_col not in df.columns:
        return [f"{_lead(scope)}No volume in the current filter, so there is no concentration pattern to read.".strip()]
    p = add_pareto_cumulative(df.sort_values(count_col, ascending=False).head(10), count_col)
    total = float(p[count_col].sum())
    top = p.iloc[0]
    share = float(top["Cum_Pct"]) if len(p) == 1 else float(top[count_col]) / total * 100 if total else 0
    label = unit
    if count_col == "Gap_Impact" or "weighted" in (unit or "").lower() or "gap ×" in (unit or "").lower():
        label = "weighted deficit"
        vol_col = next((c for c in ("n", "Feedback", "Audits", "Audit_Count", "Contacts") if c in p.columns), None)
        if vol_col:
            vol = int(pd.to_numeric(p[vol_col], errors="coerce").sum())
            vol_unit = "surveys" if vol_col == "Feedback" else ("contacts" if vol_col == "Contacts" else "audits")
            return [
                f"{_lead(scope)}'{top[cat_col]}' holds {_fmt(top[count_col], 0)} {label} "
                f"({share:.0f}% of the deficit shown). N = {vol:,} {vol_unit} on the plotted bars.".strip(),
            ]
    return [
        f"{_lead(scope)}'{top[cat_col]}' holds {_fmt(top[count_col], 0)} {label} "
        f"({share:.0f}% of the volume shown).".strip(),
    ]


def scorecard_notes(
    summary: dict,
    rc_rate: float,
    dilution: dict | None = None,
    scope: str = "",
    channel: str = "All",
) -> list[str]:
    lead = f"{scope} " if scope else ""
    notes = []
    qa = summary.get("qa_score")
    csat = summary.get("csat")
    if qa is not None:
        gap = qa - QA_GOAL
        notes.append(
            f"{lead}Official QA is {_fmt(qa, 1)}%, {gap:+.1f} pp vs the 85 goal. "
            + ("The operation is beating the audit target, so QA is not the headline risk."
               if gap >= 0 else "QA is the first gap to close on the audit side.")
        )
        lead = ""
    if csat is not None:
        gap = csat - CSAT_GOAL
        notes.append(
            f"{lead}CSAT is {_fmt(csat, 1)}%, {gap:+.1f} pp vs 85%. "
            + ("Customers are scoring below the satisfied-share goal; 4★ and 5★ volume is the lever."
               if gap < 0 else "CSAT is on the right side of the goal in this filter.")
        )
        lead = ""
    gap_rc = rc_rate - RECONTACT_GOAL
    rc_label = "Recontact on this channel" if channel not in (None, "All", "") else "Official recontact"
    notes.append(
        f"{lead}{rc_label} is {_fmt(rc_rate, 2)}%, {gap_rc:+.2f} pp vs 5.44%. "
        + ("Repeat contacts are above target." if gap_rc > 0 else "Repeat contacts are inside the target.")
    )
    if channel in (None, "All", "") and dilution and pd.notna(dilution.get("share")):
        notes.append(
            f"Self Help is about {dilution['share']:.0f}% of contacts and pulls the official rate down. "
            "Phone and Live Chat rates will look worse than Overall whenever Channel = All."
        )
    elif channel not in (None, "All", ""):
        notes.append(
            f"This recontact figure is {channel} only. It is not the official 12-channel mix, "
            "so it should not be compared to Overall 5.83%."
        )
    return notes[:4]


def weekly_notes(weekly: pd.DataFrame, scope: str = "") -> list[str]:
    lead = f"{scope} " if scope else ""
    if weekly is None or weekly.empty:
        return [f"{lead}There are no weekly rows in this filter, so the trend cannot be read.".strip()]
    last = weekly.dropna(how="all").tail(1).iloc[0]
    notes = []
    missing = []
    if pd.notna(last.get("QA_Score")):
        wow = last.get("QA_WoW_pp")
        extra = f" Week-over-week {float(wow):+.1f} pp." if pd.notna(wow) else ""
        notes.append(
            f"{lead}Latest QA week is {_fmt(last['QA_Score'], 1)}% vs the 85 goal.{extra} "
            "A four-week run is a management trend, not a control-chart sample."
        )
        lead = ""
    else:
        missing.append("QA")
    if pd.notna(last.get("CSAT_Score")):
        notes.append(
            f"{lead}Latest CSAT week is {_fmt(last['CSAT_Score'], 1)}% vs 85%. "
            "CSAT uses a ratio of sums, so a small-volume week can jump without a process change."
        )
        lead = ""
    else:
        missing.append("CSAT")
    if pd.notna(last.get("Recontact_Rate")):
        notes.append(
            f"{lead}Latest recontact week is {_fmt(last['Recontact_Rate'], 2)}% vs 5.44%. "
            "If this stays above target while QA stays high, the repeat-contact drivers are not the same as audit defects."
        )
    else:
        missing.append("recontact")
    if missing:
        notes.append(
            f"{', '.join(missing).capitalize()} has no weekly point in the latest week of this filter. "
            "The line is omitted when a source has no rows — it is not a missing KPI definition."
        )
    return notes


def channel_notes(ch_perf: pd.DataFrame, channel: str = "All") -> list[str]:
    if ch_perf is None or ch_perf.empty:
        return ["No channel split in this filter."]
    rows = ch_perf[ch_perf["Segment"] != "Overall"] if "Segment" in ch_perf.columns else ch_perf
    notes = []
    if not rows.empty and "QA_Score" in rows.columns and rows["QA_Score"].notna().any():
        worst = rows.loc[rows["QA_Score"].idxmin()]
        best = rows.loc[rows["QA_Score"].idxmax()]
        notes.append(
            f"{worst['Segment']} has the lower QA ({_fmt(worst['QA_Score'], 1)}%) vs "
            f"{best['Segment']} at {_fmt(best['QA_Score'], 1)}%. Phone and Live Chat use different attributes, so this is two operations, not one mix."
        )
    if not rows.empty and "Recontact_Rate" in rows.columns and rows["Recontact_Rate"].notna().any():
        high = rows.loc[rows["Recontact_Rate"].idxmax()]
        extra = (
            f"{high['Segment']} recontact is {_fmt(high['Recontact_Rate'], 2)}% on that channel alone."
        )
        if channel in (None, "All", ""):
            extra += " Do not compare that number to Overall 5.83% without remembering Self Help volume."
        else:
            extra += f" Channel is already {channel}, so this is not diluted by Self Help."
        notes.append(extra)
    if not rows.empty and "CSAT_Score" in rows.columns and rows["CSAT_Score"].notna().any():
        low = rows.loc[rows["CSAT_Score"].idxmin()]
        notes.append(
            f"{low['Segment']} CSAT is {_fmt(low['CSAT_Score'], 1)}% vs the 85% goal. "
            "If QA is fine on the same channel, the customer score is pointing at resolution or product, not only script adherence."
        )
    return notes[:3]


def combined_notes(combined: pd.DataFrame, scope: str = "") -> list[str]:
    if combined is None or combined.empty:
        return [f"{_lead(scope)}No contact reason Lv4 (detail) currently fails on more than one official metric.".strip()]
    row = combined.iloc[0]
    notes = [
        f"{_lead(scope)}'{row['CR_Lv4']}' is the top multi-metric risk ({row.get('Pattern', 'mixed pattern')}). "
        f"QA {_fmt(row.get('QA_Score'), 1)}%, CSAT {_fmt(row.get('CSAT_Score'), 1)}%, "
        f"recontact {_fmt(row.get('Recontact_Rate'), 2)}%. Treat this as a shared driver, not three separate tickets.".strip()
    ]
    if len(combined) > 1:
        notes.append(
            f"{len(combined)} reasons show up on more than one metric. "
            "Work them in table order; the first rows concentrate the operational risk."
        )
    notes.append(
        "This join is at contact reason Lv4 (detail) only where the same name exists in the sources. Association, not proof of cause."
    )
    return notes


def qa_rc_chart_notes(df: pd.DataFrame, scope: str = "") -> list[str]:
    """How to read the QA vs recontact scatter — axes and who sits where, not a thesis."""
    if df is None or df.empty or "QA_Score" not in df.columns or "Recontact_Rate" not in df.columns:
        return [
            f"{_lead(scope)}This chart only plots contact reason Lv4 (detail) names that exist in both QA and Recontact. Nothing to plot in this filter.".strip(),
        ]
    sub = df.dropna(subset=["QA_Score", "Recontact_Rate"])
    n = int(len(sub))
    if n == 0:
        return [
            f"{_lead(scope)}No contact reason Lv4 (detail) currently has both an official QA score and an official recontact rate.".strip(),
        ]
    notes = [
        f"{_lead(scope)}X is official QA for that contact reason Lv4 (detail). Y is official recontact for the same name. Left = weaker QA. Up = more repeats.".strip(),
        f"{n} reasons appear in both sources. A name that exists in only one source is not on this chart.",
    ]
    zone = sub[(sub["QA_Score"] < QA_GOAL) & (sub["Recontact_Rate"] > RECONTACT_GOAL)]
    name_col = "CR_Lv4" if "CR_Lv4" in sub.columns else None
    if not zone.empty and name_col:
        row = zone.sort_values("Recontact_Rate", ascending=False).iloc[0]
        notes.append(
            f"Top-left of the goal lines is the first list to open. "
            f"Highest recontact in that zone: '{row[name_col]}' "
            f"(QA {_fmt(row['QA_Score'], 1)}%, recontact {_fmt(row['Recontact_Rate'], 2)}%)."
        )
    elif not zone.empty:
        notes.append(
            f"{len(zone)} of these reasons sit below QA 85 and above recontact 5.44. Those are the first names to open."
        )
    else:
        notes.append(
            "No plotted reason is currently both below QA 85 and above recontact 5.44. Read the axes for whoever is closest to those lines."
        )
    return notes


def scatter_notes(df: pd.DataFrame, x: str, y: str, pair: str, scope: str = "") -> list[str]:
    lead = f"{scope} " if scope else ""
    if df is None or df.empty or x not in df.columns or y not in df.columns:
        return [
            f"{lead}There are no contact reason Lv4 (detail) names with both {pair} in this filter.".strip(),
            "The scatter only plots reasons that exist in both sources under the same Lv4 name. It is not a time trend.",
        ]
    sub = df[[x, y]].dropna()
    n = int(sub.shape[0])
    if n < 5:
        return [
            f"{lead}Only {n} contact reason Lv4 (detail) name(s) have both {pair} after the current filter.".strip(),
            "Pearson r is withheld below 5 shared reasons so two or three names cannot look like a relationship.",
            "Widen Channel, Market, or contact reason Lv4 (detail) if you need the association read. The KPI cards above still use the filtered totals.",
        ]
    r = sub.corr().iloc[0, 1]
    if pd.isna(r):
        return [f"{lead}{pair} has no linear read in this filter.".strip()]
    mag = abs(float(r))
    if mag < 0.25:
        link = f"{pair} barely move together (r={float(r):.2f}, N={n}). Fixing one will not automatically fix the other."
    elif r > 0:
        link = f"{pair} move in the same direction (r={float(r):.2f}, N={n}). Higher X tends to come with higher Y at reason level."
    else:
        link = f"{pair} move in opposite directions (r={float(r):.2f}, N={n}). The drivers are splitting, not reinforcing."
    return [
        f"{lead}{link}".strip(),
        "Each point is one contact reason Lv4 (detail), not a survey and not an agent. This is association, not cause.",
    ]


def corr_coverage_notes(coverage: dict, corr: pd.DataFrame, scope: str = "") -> list[str]:
    lead = f"{scope} " if scope else ""
    qa_n = int(coverage.get("qa_n") or 0)
    csat_n = int(coverage.get("csat_n") or 0)
    rc_n = int(coverage.get("rc_n") or 0)
    min_qa = int(coverage.get("min_qa") or 3)
    notes = [
        f"{lead}This is not a daily trend. Each observation is a contact reason Lv4 (detail) name that appears in more than one source.".strip(),
        (
            f"In this filter, QA has {qa_n} Lv4 names with at least {min_qa} audits, "
            f"CSAT has {csat_n} names, and recontact has {rc_n} names. "
            f"Shared names: QA and CSAT {coverage.get('qa_csat', 0)}, "
            f"QA and recontact {coverage.get('qa_rc', 0)}, "
            f"CSAT and recontact {coverage.get('csat_rc', 0)}, "
            f"all three {coverage.get('all_three', 0)}."
        ),
        (
            "Pearson r needs at least 5 shared names for that pair. "
            "r near 0 means the two KPIs do not move together at reason level. "
            "N is the count of shared Lv4 names, not surveys and not audits."
        ),
    ]
    if corr is not None and not corr.empty and corr["Pearson_r"].isna().all():
        notes.append(
            "No pair currently has 5 shared names, so r is withheld. "
            "The KPI scorecard above is still valid — this table is only the association read. "
            "Set Channel back to All, or drop Market / contact-reason cuts, to bring overlapping names back."
        )
    return notes


def aht_notes(points: pd.DataFrame, by_channel: pd.DataFrame, scope: str = "", channel: str = "All") -> list[str]:
    notes = []
    if by_channel is not None and not by_channel.empty:
        parts = [
            f"{r.Channel}: {_fmt(r.AHT_min, 1)} min AHT, QA {_fmt(r.QA_Score, 1)}%"
            for r in by_channel.itertuples()
        ]
        if channel not in (None, "All", "") and len(parts) == 1:
            notes.append(
                f"{_lead(scope)}Handle time on {channel} is {parts[0]}. "
                "Do not compare this AHT to the other channel's typical handle.".strip()
            )
        else:
            notes.append(
                f"{_lead(scope)}Handle time is not comparable across channels. ".strip()
                + "; ".join(parts) + ". "
                "Phone being longer is expected; it is not, by itself, a QA fail."
            )
    if points is None or len(points) < 5:
        notes.append("Not enough contact reason Lv4 (detail) rows with Duration to compute a stable QA–AHT link.")
        return notes
    r = points[["AHT_min", "QA_Score"]].corr().iloc[0, 1]
    long = points.sort_values("AHT_min", ascending=False).iloc[0]
    if pd.notna(r) and abs(float(r)) < 0.20:
        notes.append(
            f"At reason level, AHT and QA barely move together (r={float(r):.2f}). "
            "Longer calls are not a reliable explanation for the audit score in this filter."
        )
    elif pd.notna(r) and r < 0:
        notes.append(
            f"Longer AHT tends to sit with lower QA (r={float(r):.2f}). "
            "That is a pressure hypothesis: check time-management and information-complete fails on those reasons, not a proven cause."
        )
    elif pd.notna(r):
        notes.append(
            f"Longer AHT does not track with worse QA here (r={float(r):.2f}). "
            "Do not use average handle time as the primary quality lever in this slice."
        )
    tail = (
        f"Review that reason on this {channel} slice."
        if channel not in (None, "All", "")
        else "Review that reason on Phone separately from Live Chat."
    )
    notes.append(
        f"Longest average handle in the scatter is '{long['CR_Lv4']}' at {_fmt(long['AHT_min'], 1)} min "
        f"(QA {_fmt(long['QA_Score'], 1)}%, n={int(long['n'])}). {tail}"
    )
    return notes[:3]


def aht_outcome_notes(
    corr: pd.DataFrame,
    scope: str = "",
    channel: str = "All",
) -> list[str]:
    """Floor read of AHT vs CSAT / recontact. Channel rows first — All is a mix effect."""
    notes: list[str] = []

    def _r(pair: str, slice_name: str) -> tuple[float | None, int]:
        if corr is None or corr.empty:
            return None, 0
        hit = corr[(corr["Pair"] == pair) & (corr["Slice"] == slice_name)]
        if hit.empty or pd.isna(hit.iloc[0]["Pearson_r"]):
            n = int(hit.iloc[0]["N_CR"]) if not hit.empty else 0
            return None, n
        return float(hit.iloc[0]["Pearson_r"]), int(hit.iloc[0]["N_CR"])

    slices = [channel] if channel not in (None, "All", "") else ["Phone", "Live Chat"]
    phone_csat, _ = _r("AHT vs CSAT", "Phone")
    chat_csat, _ = _r("AHT vs CSAT", "Live Chat")
    phone_rc, _ = _r("AHT vs Recontact", "Phone")
    chat_rc, _ = _r("AHT vs Recontact", "Live Chat")
    all_qa, _ = _r("AHT vs QA", "All")

    if "Phone" in slices and phone_csat is not None and phone_csat > 0.20:
        notes.append(
            f"Phone: longer AHT sits with higher CSAT (r={phone_csat:+.2f}). "
            "Rushing the call is the risk — extra handle is not the CSAT problem on this channel."
        )
    elif "Phone" in slices and phone_csat is not None and phone_csat < -0.20:
        notes.append(
            f"Phone: longer AHT sits with lower CSAT (r={phone_csat:+.2f}). "
            "Those reasons are already stuck — coach the process, not speed."
        )
    if "Live Chat" in slices and chat_csat is not None and chat_csat < -0.15:
        notes.append(
            f"Live Chat: longer threads sit with lower CSAT (r={chat_csat:+.2f}). "
            "A long chat is usually an unresolved ticket, not thorough service."
        )
    if "Phone" in slices and phone_rc is not None and phone_rc < -0.20:
        notes.append(
            f"Phone: longer AHT sits with fewer repeats (r={phone_rc:+.2f}). "
            "Cutting handle time there can cost first-contact resolution."
        )
    if "Live Chat" in slices and chat_rc is not None and abs(chat_rc) < 0.20:
        notes.append(
            f"Live Chat: AHT and recontact barely move together (r={chat_rc:+.2f}). "
            "FCR work is the contact reason Lv4 (detail), not chat length."
        )
    all_csat, _ = _r("AHT vs CSAT", "All")
    all_rc, _ = _r("AHT vs Recontact", "All")
    if channel in (None, "All", "") and all_qa is not None and abs(all_qa) > 0.25:
        notes.append(
            f"Pooled AHT vs QA looks strong (r={all_qa:+.2f}) because Phone and Live Chat "
            "are different operations. Coach each channel, not the All bar."
        )
    if channel in (None, "All", "") and all_csat is not None and all_csat < -0.20:
        notes.append(
            f"Pooled AHT vs CSAT is negative (r={all_csat:+.2f}), but Phone is the opposite. "
            "Do not cut handle time as a CSAT lever until you split the channel."
        )
    if channel in (None, "All", "") and all_rc is not None and abs(all_rc) < 0.15:
        notes.append(
            f"Pooled AHT vs recontact is almost flat (r={all_rc:+.2f}). "
            "Phone still shows longer calls with fewer repeats — that FCR trade-off is hidden in All."
        )
    if not notes:
        notes.append(
            f"{_lead(scope)}AHT vs outcomes is weak in this filter. "
            "Handle time is not the first lever — open the reason-level Paretos.".strip()
        )
    return notes[:4]


def attr_notes(top_attr: pd.DataFrame, crit: dict, scope: str = "") -> list[str]:
    if top_attr is None or top_attr.empty:
        return [f"{_lead(scope)}No attribute fails in this filter.".strip()]
    row = top_attr.iloc[0]
    notes = [
        f"{_lead(scope)}'{row['Error_Category']}' accounts for {_fmt(row.get('Pct_Of_Fails'), 1)}% of attribute fails "
        f"({int(row['Fail_Count']):,} counts). Coaching should name this attribute, not 'quality in general'.".strip()
    ]
    if "Is_Critical" in top_attr.columns and bool(row.get("Is_Critical")):
        notes.append(
            "The top bar is a CRITICAL attribute. Any fail here zeroes the audit, so it outranks higher-volume non-critical misses."
        )
    notes.append(
        f"{crit.get('n_fatal', 0):,} audits scored 0 because of a critical fail "
        f"({_fmt(crit.get('pct_fatal'), 1)}% of audits). That pile at 0 in the histogram is this mechanism, not a separate KPI."
    )
    return notes


def stars_notes(stars: pd.DataFrame, csat: float, scope: str = "") -> list[str]:
    if stars is None or stars.empty:
        return [f"{_lead(scope)}No star-rating mix in this filter.".strip()]
    high = stars[stars["Rating"].isin(["5 Stars", "4 Stars"])]["Pct"].sum()
    low = stars[stars["Rating"].isin(["1 Star", "2 Stars", "3 Stars"])]["Pct"].sum()
    return [
        f"{_lead(scope)}CSAT is {_fmt(csat, 1)}%. That is 4★+5★ as a share of surveys ({_fmt(high, 1)}%), not an average star. The 85% goal is that share.".strip(),
        f"1★–3★ are {_fmt(low, 1)}% of surveys. The unsatisfied Pareto on this page already ranks that volume by contact reason Lv4 (detail) — that list is the CSAT worklist.",
    ]


def voc_notes(voc: pd.DataFrame, scope: str = "") -> list[str]:
    if voc is None or voc.empty:
        return [f"{_lead(scope)}No classifiable 1★–3★ comments in this filter.".strip()]
    top = voc.iloc[0]
    return [
        f"{_lead(scope)}'{top['Theme']}' leads the 1★–3★ comments ({_fmt(top['Pct'], 1)}% of tagged mentions).".strip(),
        "These are open comments from unsatisfied surveys. Match the theme to the contact reason Lv4 (detail) Pareto before treating it as the CSAT driver.",
    ]


def csat_tenure_notes(df: pd.DataFrame, scope: str = "") -> list[str]:
    if df is None or df.empty:
        return [f"{_lead(scope)}No CSAT tenure mix in this filter.".strip()]
    by = {
        str(r["CSAT_Agent_Tenure"]).strip().lower(): r
        for _, r in df.iterrows()
    }
    notes = []
    nest = by.get("nesting")
    nh = by.get("new_hire")
    if nest is not None and nh is not None:
        notes.append(
            f"{_lead(scope)}Nesting CSAT is {_fmt(nest['CSAT_Score'], 1)}% "
            f"({int(nest['Feedback']):,} surveys) vs new_hire {_fmt(nh['CSAT_Score'], 1)}% "
            f"({int(nh['Feedback']):,}). Nesting still has real-time support on the interaction. "
            "new_hire is the first stretch in production alone — learning curve, solo handling, and that is where CSAT dips.".strip()
        )
    other = by.get("other")
    if other is not None:
        notes.append(
            f"'other' is {_fmt(other['CSAT_Score'], 1)}% on {int(other['Feedback']):,} surveys. "
            "Most volume sits there, so it still moves the official CSAT."
        )
    tenured = by.get("tenured")
    if tenured is not None:
        notes.append(
            f"Tenured is {_fmt(tenured['CSAT_Score'], 1)}% on {int(tenured['Feedback']):,} surveys."
        )
    return notes[:3]


def rc_scope_notes(dilution: dict, rc_rate: float, channel: str = "All") -> list[str]:
    if channel not in (None, "All", ""):
        return [
            f"Channel is {channel}. Recontact is {_fmt(rc_rate, 2)}% on this channel alone vs a 5.44% target.",
            "The Self Help dilution story only applies when Channel = All. It is not happening inside this slice.",
            "If the action is 'fix recontact', the work on this page is this channel's first-contact resolution — not the 12-channel mix.",
        ]
    sh = dilution.get("share") if dilution else None
    sh_rate = dilution.get("rate") if dilution else None
    notes = [
        f"The official recontact KPI remains {_fmt(rc_rate, 2)}% on all 12 channels vs a 5.44% target."
    ]
    if sh is not None and pd.notna(sh):
        notes.append(
            f"Self Help is {sh:.0f}% of contacts"
            + (f" at {_fmt(sh_rate, 2)}%" if sh_rate is not None and pd.notna(sh_rate) else "")
            + ". That mix is why Overall looks closer to target than Phone or Live Chat."
        )
    notes.append(
        "If the action is 'fix recontact', specify the channel set. Overall and Phone+Chat are different problems."
    )
    return notes


def spc_notes(spc: pd.DataFrame, metric: str, goal: float, lower_better: bool = False, scope: str = "") -> list[str]:
    if spc is None or spc.empty:
        return [f"{_lead(scope)}Not enough daily {metric} points to show typical variation.".strip()]
    n_out = int(spc["Beyond_Limits"].sum()) if "Beyond_Limits" in spc.columns else 0
    last = spc.sort_values("Date").iloc[-1]
    side = "above" if last["Value"] > goal else "below"
    if lower_better:
        miss = last["Value"] > goal
    else:
        miss = last["Value"] < goal
    notes = [
        f"{_lead(scope)}The latest {metric} day is {_fmt(last['Value'], 2 if lower_better else 1)}%, {side} the {goal:g} goal. ".strip()
        + (" The process is missing the target even if most days look 'in control'." if miss
           else " The latest day is on the right side of the goal.")
    ]
    notes.append(
        f"{n_out} day(s) sit outside typical day-to-day variation (red). "
        "In-control is not the same as on-goal: a stable miss is still a miss."
    )
    return notes
