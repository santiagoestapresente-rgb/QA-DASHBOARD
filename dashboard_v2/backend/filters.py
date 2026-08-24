"""Same filter cuts as Streamlit v1 `apply_filters`, copied here so v2 never imports app.py."""

from __future__ import annotations

import pandas as pd

from modules.kpis import (
    channel_match,
    cr_match,
    cut_csat_recontact_for_weeks,
    filter_by_calendar_day,
    filter_csat_by_agent,
    filter_csat_by_supervisor,
    filter_csat_by_tenure,
    map_cr_group,
)


def apply_filters(audits, errors, csat, recontact, f, audits_all):
    a, e = audits.copy(), errors.copy()
    c, r = csat.copy(), recontact.copy()

    weeks_sel = f.get("weeks")
    if not weeks_sel:
        return a.iloc[0:0].copy(), e.iloc[0:0].copy(), c.iloc[0:0].copy(), r.iloc[0:0].copy()

    a, e = a[a["Week"].isin(weeks_sel)], e[e["Week"].isin(weeks_sel)]
    all_week_labels = audits_all["Week"].dropna().astype(str).unique().tolist() if "Week" in audits_all.columns else []
    c, r = cut_csat_recontact_for_weeks(c, r, weeks_sel, all_week_labels)

    day = f.get("day") or "All"
    if day != "All":
        a = filter_by_calendar_day(a, day)
        e = filter_by_calendar_day(e, day)
        c = filter_by_calendar_day(c, day)
        r = filter_by_calendar_day(r, day)

    if f["lob"] != "All":
        a, e = a[a["LOB"] == f["lob"]], e[e["LOB"] == f["lob"]]

    if f["channel"] != "All":
        if "Channel" in a.columns:
            a = a[channel_match(a["Channel"], f["channel"])]
        if "Channel" in e.columns:
            e = e[channel_match(e["Channel"], f["channel"])]
        if "Channel" in c.columns:
            c = c[channel_match(c["Channel"], f["channel"])]
        if "standard_channel_name" in r.columns:
            r = r[channel_match(r["standard_channel_name"], f["channel"])]
        elif "Channel" in r.columns:
            r = r[channel_match(r["Channel"], f["channel"])]

    if f["country"] != "All":
        a = a[a["Country"] == f["country"]]
        if "Country Code" in c.columns:
            c = c[c["Country Code"] == f["country"]]

    if f.get("cr_lv1", "All") != "All":
        lookup = f.get("cr_lookup") or {}

        def _in_group(s: pd.Series) -> pd.Series:
            return map_cr_group(s, lookup) == f["cr_lv1"]

        if "CR_Lv4" in a.columns:
            a = a[_in_group(a["CR_Lv4"])]
        if "CR_Lv4" in c.columns:
            c = c[_in_group(c["CR_Lv4"])]
        if "CR_Lv4" in r.columns:
            r = r[_in_group(r["CR_Lv4"])]

    if f["cr"] != "All":
        if "CR_Lv4" in a.columns:
            a = a[cr_match(a["CR_Lv4"], f["cr"])]
        if "CR_Lv4" in e.columns:
            e = e[cr_match(e["CR_Lv4"], f["cr"])]
        if "CR_Lv4" in c.columns:
            c = c[cr_match(c["CR_Lv4"], f["cr"])]
        if "CR_Lv4" in r.columns:
            r = r[cr_match(r["CR_Lv4"], f["cr"])]

    sub_cr = f.get("sub_cr", "All")
    if sub_cr != "All":
        if "SUB_CR" in a.columns:
            a = a[cr_match(a["SUB_CR"], sub_cr)]
        if "SUB_CR" in e.columns:
            e = e[cr_match(e["SUB_CR"], sub_cr)]
        if "SUB_CR" in c.columns:
            c = c[cr_match(c["SUB_CR"], sub_cr)]
        if "SUB_CR" in r.columns and r["SUB_CR"].notna().any():
            r = r[cr_match(r["SUB_CR"], sub_cr)]

    if f.get("audit_type", "All") != "All" and "Type_of_audit" in a.columns:
        a = a[a["Type_of_audit"] == f["audit_type"]]

    if f.get("special_project", "All") != "All" and "Special_project" in a.columns:
        a = a[a["Special_project"] == f["special_project"]]

    if f.get("business_type", "All") != "All":
        bt = f["business_type"]
        cr_keys: set[str] = set()
        if "Business_Type" in c.columns:
            hit = c[c["Business_Type"] == bt]
            if "CR_Lv4" in hit.columns:
                cr_keys = set(hit["CR_Lv4"].dropna().astype(str).str.strip().str.casefold()) - {"", "nan"}
            c = hit
        if cr_keys:
            def _in_bt(s: pd.Series) -> pd.Series:
                return s.astype(str).str.strip().str.casefold().isin(cr_keys)
            if "CR_Lv4" in a.columns:
                a = a[_in_bt(a["CR_Lv4"])]
            if "CR_Lv4" in e.columns:
                e = e[_in_bt(e["CR_Lv4"])]

    if f.get("requester", "All") != "All" and "Requester" in a.columns:
        a, e = a[a["Requester"] == f["requester"]], e[e["Requester"] == f["requester"]]

    if f.get("tenure", "All") != "All" and "Tenure_Cohort" in a.columns:
        a = a[a["Tenure_Cohort"] == f["tenure"]]
        c = filter_csat_by_tenure(c, audits_all, f["tenure"])

    if f.get("supervisor", "All") != "All":
        if "Supervisor_ID" in a.columns:
            a = a[a["Supervisor_ID"] == f["supervisor"]]
        c = filter_csat_by_supervisor(c, audits_all, f["supervisor"])

    if f.get("agent", "All") != "All":
        want = str(f["agent"]).strip()
        if "Agent_ID" in a.columns:
            a = a[a["Agent_ID"].astype(str).str.strip() == want]
        c = filter_csat_by_agent(c, want)

    if "Audit_ID" in e.columns:
        e = e[e["Audit_ID"].isin(a["Audit_ID"])]

    return a, e, c, r
