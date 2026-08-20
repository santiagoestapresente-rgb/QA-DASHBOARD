"""
Cross-check the exported Power BI model against the Streamlit calculation layer.

Reads powerbi/DiDi_CX_PowerBI_Model.xlsx and recomputes the headline metrics from
the flat tables, then compares them with modules.kpis on the same source data.
Any drift means the two deliverables would tell different stories.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import CSAT_GOAL, QA_GOAL, RECONTACT_GOAL  # noqa: E402
from modules.data_loader import load_all_data  # noqa: E402
from modules.kpis import (  # noqa: E402
    channel_performance,
    csat_by_star_rating,
    top_failing_attributes,
)

MODEL = Path(__file__).resolve().parent.parent / "powerbi" / "DiDi_CX_PowerBI_Model.xlsx"
TOL = 0.05  # percentage points

results: list[dict] = []


def compare(label: str, powerbi_value: float | None, streamlit_value: float | None) -> None:
    if powerbi_value is None or streamlit_value is None or pd.isna(powerbi_value) or pd.isna(streamlit_value):
        results.append({"Check": label, "PowerBI": powerbi_value, "Streamlit": streamlit_value,
                        "Diff": None, "Status": "SKIP"})
        return
    diff = abs(powerbi_value - streamlit_value)
    results.append({
        "Check": label,
        "PowerBI": round(powerbi_value, 3),
        "Streamlit": round(streamlit_value, 3),
        "Diff": round(diff, 4),
        "Status": "MATCH" if diff <= TOL else "DRIFT",
    })


print(f"Reading model: {MODEL.name}")
audit = pd.read_excel(MODEL, sheet_name="fact_audit")
attr = pd.read_excel(MODEL, sheet_name="fact_audit_attribute")
csat_m = pd.read_excel(MODEL, sheet_name="fact_csat")
rc_m = pd.read_excel(MODEL, sheet_name="fact_recontact")
dim_attr = pd.read_excel(MODEL, sheet_name="dim_attribute")

print("Reading Streamlit data layer")
data = load_all_data()
audits_s, errors_s = data["fact_audits"], data["fact_errors"]
csat_s, rc_s = data["fact_csat"], data["fact_recontact"]

# ── Headline metrics ──────────────────────────────────────────────────────────
compare("QA Score overall", audit["QA_Score"].mean(), audits_s["Score_Pct"].mean())
compare(
    "CSAT Score overall",
    csat_m["Satisfied_CNT"].sum() / csat_m["Feedback_CNT"].sum() * 100,
    csat_s["Satisfied_CNT"].sum() / csat_s["Feedback CNT"].sum() * 100,
)
compare(
    "Recontact Rate overall",
    rc_m["Recontact_Volume"].sum() / rc_m["Contacts"].sum() * 100,
    rc_s["Recontact Volume"].sum() / rc_s["Contacts"].sum() * 100,
)

# ── Volumes ───────────────────────────────────────────────────────────────────
compare("QA evaluations", len(audit), len(audits_s))
compare("Total surveys", csat_m["Feedback_CNT"].sum(), csat_s["Feedback CNT"].sum())
compare("Total contacts", rc_m["Contacts"].sum(), rc_s["Contacts"].sum())

# ── Channel level ─────────────────────────────────────────────────────────────
ch_s = channel_performance(audits_s, csat_s, rc_s).set_index("Segment")
for label, key in [("Phone", "phone"), ("Live Chat", "live chat")]:
    pb_qa = audit.loc[audit["Channel_Key"] == key, "QA_Score"].mean()
    compare(f"QA Score — {label}", pb_qa, ch_s.loc[label, "QA_Score"])

    cs = csat_m[csat_m["Channel_Key"] == key]
    pb_cs = cs["Satisfied_CNT"].sum() / cs["Feedback_CNT"].sum() * 100 if cs["Feedback_CNT"].sum() else None
    compare(f"CSAT — {label}", pb_cs, ch_s.loc[label, "CSAT_Score"])

    rcx = rc_m[rc_m["Channel_Key"] == key]
    pb_rc = rcx["Recontact_Volume"].sum() / rcx["Contacts"].sum() * 100 if rcx["Contacts"].sum() else None
    compare(f"Recontact — {label}", pb_rc, ch_s.loc[label, "Recontact_Rate"])

# ── Critical fail rate ────────────────────────────────────────────────────────
compare(
    "Critical fail rate",
    audit["Has_Critical_Fail"].mean() * 100,
    audits_s["Fatal_Flag"].mean() * 100,
)

# ── Attribute defects ─────────────────────────────────────────────────────────
pb_fails = (
    attr.merge(dim_attr[["Attribute_Key", "Attribute_Name"]], on="Attribute_Key")
    .groupby("Attribute_Name")["Is_Fail"].sum()
    .sort_values(ascending=False)
)
st_fails = errors_s.groupby("Error_Category").size().sort_values(ascending=False)

compare("Total attribute fails", pb_fails.sum(), st_fails.sum())

for name in st_fails.head(5).index:
    compare(f"Fails — {name}", pb_fails.get(name), float(st_fails.get(name)))

pb_top = list(pb_fails.head(5).index)
st_top = list(st_fails.head(5).index)
results.append({
    "Check": "Top 5 defect ranking identical",
    "PowerBI": " > ".join(x[:14] for x in pb_top),
    "Streamlit": " > ".join(x[:14] for x in st_top),
    "Diff": None,
    "Status": "MATCH" if pb_top == st_top else "DRIFT",
})

# ── Star distribution ─────────────────────────────────────────────────────────
stars_s = csat_by_star_rating(csat_s).set_index("Rating")
star_map = {"5 Stars": "Star_5", "4 Stars": "Star_4", "3 Stars": "Star_3",
            "2 Stars": "Star_2", "1 Star": "Star_1"}
total_feedback = csat_m["Feedback_CNT"].sum()
for label, col in star_map.items():
    compare(f"Share — {label}", csat_m[col].sum() / total_feedback * 100, stars_s.loc[label, "Pct"])

# ── Referential integrity of the exported model ───────────────────────────────
dim_cr = pd.read_excel(MODEL, sheet_name="dim_cr")
dim_channel = pd.read_excel(MODEL, sheet_name="dim_channel")
dim_date = pd.read_excel(MODEL, sheet_name="dim_date")

integrity = [
    ("fact_audit.CR_Key -> dim_cr", set(audit["CR_Key"]) <= set(dim_cr["CR_Key"])),
    ("fact_csat.CR_Key -> dim_cr", set(csat_m["CR_Key"].dropna()) <= set(dim_cr["CR_Key"])),
    ("fact_recontact.CR_Key -> dim_cr", set(rc_m["CR_Key"].dropna()) <= set(dim_cr["CR_Key"])),
    ("fact_csat.Channel_Key -> dim_channel", set(csat_m["Channel_Key"]) <= set(dim_channel["Channel_Key"])),
    ("fact_recontact.Channel_Key -> dim_channel", set(rc_m["Channel_Key"]) <= set(dim_channel["Channel_Key"])),
    ("fact_audit_attribute.Audit_ID -> fact_audit", set(attr["Audit_ID"]) <= set(audit["Audit_ID"])),
    ("dim_cr.CR_Key unique", dim_cr["CR_Key"].is_unique),
    ("dim_channel.Channel_Key unique", dim_channel["Channel_Key"].is_unique),
    ("dim_date.Date unique", dim_date["Date"].is_unique),
    ("fact_audit.Audit_ID unique", audit["Audit_ID"].is_unique),
]
for name, ok in integrity:
    results.append({"Check": name, "PowerBI": "", "Streamlit": "", "Diff": None,
                    "Status": "MATCH" if ok else "DRIFT"})

# ── Report ────────────────────────────────────────────────────────────────────
report = pd.DataFrame(results)
print("\n" + report.to_string(index=False))

drift = report[report["Status"] == "DRIFT"]
skipped = report[report["Status"] == "SKIP"]
print(f"\n{len(report[report['Status'] == 'MATCH'])} matched, {len(drift)} drifted, {len(skipped)} skipped")

if not drift.empty:
    print("\nDRIFT DETECTED:")
    print(drift.to_string(index=False))
    sys.exit(1)

print("\nModel is consistent with the Streamlit calculation layer.")
