"""
DiDi CX QA Business Case — Data Processing Pipeline
Calculates QA, CSAT, and Recontact metrics per business case definitions.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "Business Case.xlsx"
if not SOURCE.exists():
    SOURCE = Path(r"c:\Users\PC\Downloads\Business Case.xlsx")
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── Goals ──────────────────────────────────────────────────────────────────
QA_GOAL = 85
CSAT_GOAL = 85
RECONTACT_GOAL = 5.44

# ── QA attribute columns (0-indexed from Excel headers) ─────────────────────
PHONE_ATTRS = [
    "Critical_atributo_actitud_de_servicio_end_user",
    "Critical_atributo_compensaciones_reembolsos_end_user",
    "atributo_comunicacion_efectiva_end_user",
    "atributo_escucha_activa_end_user",
    "Critical_atributo_informacion_completa_y_correcta_end_user",
    "atributo_manejo_del_lenguaje_end_user",
    "atributo_manejo_del_tiempo_end_user",
    "Critical_atributo_negacion_de_servicio_end_user",
    "atributo_nombre_de_usuario_end_user",
    "atributo_personalizacion_de_la_interaccion_end_user",
    "atributo_presentacion_end_user",
    "Critical_atributo_rudeza_con_el_usuario_end_user",
]

LIVECHAT_ATTRS = [
    "Critical_Objetividad_del_chat",
    "Critical_Disponibilidad_del_servicio",
    "Saludo_e_identificacion",
    "Calidad_del_sondeo",
    "Recurrencia_de_informacion",
    "Actitud_de_servicio",
    "Personalizacion",
    "Calidad_de_comunicacion",
]

DIDI_ORANGE = "#FF6600"
DIDI_DARK = "#1A1A1A"
DIDI_WHITE = "#FFFFFF"


def is_critical(col: str) -> bool:
    return "critical" in col.lower()


def calc_qa_score(row: pd.Series, attr_cols: list[str]) -> float:
    """Calculate QA score per business case rules."""
    for col in attr_cols:
        val = row.get(col)
        if pd.isna(val) or val == 2:
            continue
        if is_critical(col) and val == 1:
            return 0.0

    fails = 0
    for col in attr_cols:
        val = row.get(col)
        if pd.isna(val) or val == 2:
            continue
        if not is_critical(col) and val == 1:
            fails += 1

    return max(0.0, 100.0 - fails * 10)


def status_color(value: float, goal: float, higher_is_better: bool = True) -> str:
    """Return green/amber/red status per PDF rules."""
    if higher_is_better:
        diff = value - goal
        if diff >= 0:
            return "green"
        if diff >= -5:
            return "amber"
        return "red"
    else:
        diff = value - goal
        if diff <= 0:
            return "green"
        if diff <= 5:
            return "amber"
        return "red"


def clean_attr_name(col: str) -> str:
    """Human-readable attribute label."""
    name = col.replace("_end_user", "").replace("Critical_", "").replace("Critical ", "")
    name = name.replace("atributo_", "").replace("_", " ").title()
    return name


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    qa = pd.read_excel(SOURCE, sheet_name="QA")
    csat = pd.read_excel(SOURCE, sheet_name="CSAT")
    recontact = pd.read_excel(SOURCE, sheet_name="Recontact")
    return qa, csat, recontact


def process_qa(qa: pd.DataFrame) -> pd.DataFrame:
    qa = qa.copy()
    qa["CR_Lv4"] = qa["CR_correcta"].fillna(qa["CR_registrada"])
    qa["Business_Type"] = "Food"  # Only Delivery/ Food in QA data

    scores = []
    for _, row in qa.iterrows():
        attrs = PHONE_ATTRS if row["Channel"] == "Phone" else LIVECHAT_ATTRS
        scores.append(calc_qa_score(row, attrs))
    qa["QA_Score_Calc"] = scores

    # Use calculated score; flag mismatches with provided score
    qa["Score_Mismatch"] = (
        qa["Score_end_user"].notna()
        & (qa["Score_end_user"] != qa["QA_Score_Calc"])
    )
    qa["QA_Score"] = qa["QA_Score_Calc"]

    return qa


def process_csat(csat: pd.DataFrame) -> pd.DataFrame:
    csat = csat.copy()
    csat.columns = [c.strip().replace("\ufeff", "") for c in csat.columns]
    csat.rename(columns={"Consolidated Channel.": "Channel"}, inplace=True)

    star_cols = [c for c in csat.columns if "Star Level" in c]
    csat["Satisfied_CNT"] = csat["Questionnaires With Star Level =4"] + csat[
        "Questionnaires With Star Level =5"
    ]
    csat["Unsatisfied_CNT"] = (
        csat["Questionnaires With Star Level =1"]
        + csat["Questionnaires With Star Level =2"]
        + csat["Questionnaires With Star Level =3"]
    )
    csat["CSAT_Pct"] = np.where(
        csat["Feedback CNT"] > 0,
        csat["Satisfied_CNT"] / csat["Feedback CNT"] * 100,
        np.nan,
    )
    csat["Has_VOC"] = csat["open_question"].notna() & (
        csat["open_question"].astype(str).str.strip() != ""
    )
    return csat


def process_recontact(recontact: pd.DataFrame) -> pd.DataFrame:
    rc = recontact.copy()
    rc.columns = [c.strip().replace("\ufeff", "") for c in rc.columns]
    rc.rename(columns={"region_name": "Country", "customer_type": "User_Type"}, inplace=True)
    rc["Recontact_Rate"] = np.where(
        rc["Contacts"] > 0,
        rc["Recontact Volume"] / rc["Contacts"] * 100,
        np.nan,
    )
    return rc


def build_kpi_summary(qa: pd.DataFrame, csat: pd.DataFrame, rc: pd.DataFrame) -> pd.DataFrame:
    qa_avg = qa["QA_Score"].mean()
    csat_pct = csat["Satisfied_CNT"].sum() / csat["Feedback CNT"].sum() * 100
    rc_rate = rc["Recontact Volume"].sum() / rc["Contacts"].sum() * 100

    rows = [
        {
            "Metric": "QA Score",
            "Value": round(qa_avg, 2),
            "Goal": QA_GOAL,
            "Gap": round(qa_avg - QA_GOAL, 2),
            "Status": status_color(qa_avg, QA_GOAL, True),
            "Unit": "score",
        },
        {
            "Metric": "CSAT",
            "Value": round(csat_pct, 2),
            "Goal": CSAT_GOAL,
            "Gap": round(csat_pct - CSAT_GOAL, 2),
            "Status": status_color(csat_pct, CSAT_GOAL, True),
            "Unit": "%",
        },
        {
            "Metric": "Recontact Rate",
            "Value": round(rc_rate, 2),
            "Goal": RECONTACT_GOAL,
            "Gap": round(rc_rate - RECONTACT_GOAL, 2),
            "Status": status_color(rc_rate, RECONTACT_GOAL, False),
            "Unit": "%",
        },
    ]
    return pd.DataFrame(rows)


def build_qa_by_dimension(qa: pd.DataFrame, dim: str, include_channel: bool = True) -> pd.DataFrame:
    group_cols = [dim]
    if include_channel and dim != "Channel":
        group_cols.append("Channel")
    g = (
        qa.groupby(group_cols, dropna=False)
        .agg(
            QA_Score=("QA_Score", "mean"),
            Audits=("QA_Score", "count"),
            Critical_Fails=("QA_Score", lambda x: (x == 0).sum()),
        )
        .reset_index()
    )
    g["QA_Score"] = g["QA_Score"].round(2)
    g["Status"] = g["QA_Score"].apply(lambda v: status_color(v, QA_GOAL, True))
    g["Gap_vs_Goal"] = (g["QA_Score"] - QA_GOAL).round(2)
    return g.sort_values("QA_Score")


def build_attribute_fails(qa: pd.DataFrame) -> pd.DataFrame:
    records = []
    for channel, attrs in [("Phone", PHONE_ATTRS), ("Live Chat", LIVECHAT_ATTRS)]:
        subset = qa[qa["Channel"] == channel]
        total = len(subset)
        for col in attrs:
            applicable = subset[col].isin([0, 1])
            fail_cnt = (subset.loc[applicable, col] == 1).sum()
            app_cnt = applicable.sum()
            records.append(
                {
                    "Channel": channel,
                    "Attribute": clean_attr_name(col),
                    "Attribute_Raw": col,
                    "Is_Critical": is_critical(col),
                    "Fail_Count": int(fail_cnt),
                    "Applicable_Count": int(app_cnt),
                    "Fail_Rate_Pct": round(fail_cnt / app_cnt * 100, 2) if app_cnt else 0,
                }
            )
    df = pd.DataFrame(records)
    return df.sort_values(["Channel", "Fail_Rate_Pct"], ascending=[True, False])


def build_csat_by_dimension(csat: pd.DataFrame, dim: str) -> pd.DataFrame:
    g = (
        csat.groupby(dim, dropna=False)
        .agg(
            Feedback_CNT=("Feedback CNT", "sum"),
            Satisfied_CNT=("Satisfied_CNT", "sum"),
        )
        .reset_index()
    )
    g["CSAT_Pct"] = (g["Satisfied_CNT"] / g["Feedback_CNT"] * 100).round(2)
    g["Status"] = g["CSAT_Pct"].apply(lambda v: status_color(v, CSAT_GOAL, True))
    g["Gap_vs_Goal"] = (g["CSAT_Pct"] - CSAT_GOAL).round(2)
    return g.sort_values("CSAT_Pct")


def build_recontact_by_cr(rc: pd.DataFrame) -> pd.DataFrame:
    g = (
        rc.groupby("CR Lv4", dropna=False)
        .agg(Contacts=("Contacts", "sum"), Recontact_Volume=("Recontact Volume", "sum"))
        .reset_index()
    )
    g["Recontact_Rate"] = (g["Recontact_Volume"] / g["Contacts"] * 100).round(2)
    g["Status"] = g["Recontact_Rate"].apply(
        lambda v: status_color(v, RECONTACT_GOAL, False)
    )
    g["Gap_vs_Goal"] = (g["Recontact_Rate"] - RECONTACT_GOAL).round(2)
    return g.sort_values("Recontact_Rate", ascending=False)


def build_combined_analysis(
    qa: pd.DataFrame, csat: pd.DataFrame, rc: pd.DataFrame
) -> pd.DataFrame:
    qa_cr = (
        qa.groupby("CR_Lv4")
        .agg(QA_Score=("QA_Score", "mean"), QA_Audits=("QA_Score", "count"))
        .reset_index()
        .rename(columns={"CR_Lv4": "CR_Lv4_Name"})
    )
    csat_cr = (
        csat.groupby("CR Lv4")
        .agg(Feedback_CNT=("Feedback CNT", "sum"), Satisfied_CNT=("Satisfied_CNT", "sum"))
        .reset_index()
        .rename(columns={"CR Lv4": "CR_Lv4_Name"})
    )
    csat_cr["CSAT_Pct"] = (
        csat_cr["Satisfied_CNT"] / csat_cr["Feedback_CNT"] * 100
    ).round(2)

    rc_cr = (
        rc.groupby("CR Lv4")
        .agg(Contacts=("Contacts", "sum"), Recontact_Volume=("Recontact Volume", "sum"))
        .reset_index()
        .rename(columns={"CR Lv4": "CR_Lv4_Name"})
    )
    rc_cr["Recontact_Rate"] = (
        rc_cr["Recontact_Volume"] / rc_cr["Contacts"] * 100
    ).round(2)

    merged = qa_cr.merge(csat_cr, on="CR_Lv4_Name", how="outer").merge(
        rc_cr, on="CR_Lv4_Name", how="outer"
    )
    merged["QA_Status"] = merged["QA_Score"].apply(
        lambda v: status_color(v, QA_GOAL, True) if pd.notna(v) else "na"
    )
    merged["CSAT_Status"] = merged["CSAT_Pct"].apply(
        lambda v: status_color(v, CSAT_GOAL, True) if pd.notna(v) else "na"
    )
    merged["RC_Status"] = merged["Recontact_Rate"].apply(
        lambda v: status_color(v, RECONTACT_GOAL, False) if pd.notna(v) else "na"
    )
    merged["Risk_Flags"] = merged.apply(
        lambda r: sum(
            [
                r["QA_Status"] == "red",
                r["CSAT_Status"] == "red",
                r["RC_Status"] == "red",
            ]
        ),
        axis=1,
    )
    return merged.sort_values("Risk_Flags", ascending=False)


def build_voc_sample(csat: pd.DataFrame, n: int = 200) -> pd.DataFrame:
    voc = csat[csat["Has_VOC"]].copy()
    voc = voc[voc["Unsatisfied_CNT"] > 0].head(n)
    return voc[
        [
            "CR Lv4",
            "Channel",
            "Business Type Name",
            "Country Code",
            "open_question",
            "CSAT_Pct",
            "Feedback CNT",
        ]
    ]


def build_qa_detail(qa: pd.DataFrame) -> pd.DataFrame:
    """Row-level QA for dashboard drill-down."""
    return qa[
        [
            "Channel",
            "LOB",
            "Country",
            "Requester",
            "CR_Lv4",
            "Evaluado",
            "Supervisor",
            "Tenure",
            "QA_Score",
            "Duration",
            "Week",
        ]
    ].copy()


def main() -> dict:
    print("Loading raw data...")
    qa_raw, csat_raw, rc_raw = load_raw()

    print("Processing QA...")
    qa = process_qa(qa_raw)
    mismatch_rate = qa["Score_Mismatch"].mean() * 100
    print(f"  QA score validation: {mismatch_rate:.1f}% mismatch with source column")

    print("Processing CSAT...")
    csat = process_csat(csat_raw)

    print("Processing Recontact...")
    rc = process_recontact(rc_raw)

    print("Building summary tables...")
    tables = {
        "kpi_summary": build_kpi_summary(qa, csat, rc),
        "qa_by_channel": build_qa_by_dimension(qa, "Channel", include_channel=False),
        "qa_by_cr": build_qa_by_dimension(qa, "CR_Lv4"),
        "qa_by_country": build_qa_by_dimension(qa, "Country"),
        "qa_by_agent": build_qa_by_dimension(qa, "Evaluado"),
        "qa_attributes": build_attribute_fails(qa),
        "csat_by_channel": build_csat_by_dimension(csat, "Channel"),
        "csat_by_cr": build_csat_by_dimension(csat, "CR Lv4"),
        "csat_by_business_type": build_csat_by_dimension(csat, "Business Type Name"),
        "csat_by_country": build_csat_by_dimension(csat, "Country Code"),
        "recontact_by_cr": build_recontact_by_cr(rc),
        "combined_analysis": build_combined_analysis(qa, csat, rc),
        "qa_detail": build_qa_detail(qa),
        "voc_sample": build_voc_sample(csat),
    }

    # Fix recontact_by_channel - need proper grouping
    rc_ch = (
        rc.groupby("standard_channel_name", dropna=False)
        .agg(Contacts=("Contacts", "sum"), Recontact_Volume=("Recontact Volume", "sum"))
        .reset_index()
    )
    rc_ch["Recontact_Rate"] = (rc_ch["Recontact_Volume"] / rc_ch["Contacts"] * 100).round(2)
    rc_ch["Status"] = rc_ch["Recontact_Rate"].apply(
        lambda v: status_color(v, RECONTACT_GOAL, False)
    )
    rc_ch["Gap_vs_Goal"] = (rc_ch["Recontact_Rate"] - RECONTACT_GOAL).round(2)
    tables["recontact_by_channel"] = rc_ch

    print("Saving outputs...")
    for name, df in tables.items():
        path = DATA_DIR / f"{name}.csv"
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  {path.name}: {len(df)} rows")

    # Master Excel for Google Sheets / manual editing
    excel_path = DATA_DIR / "DiDi_CX_Dashboard_Data.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        for name, df in tables.items():
            sheet = name[:31]
            df.to_excel(writer, sheet_name=sheet, index=False)

    metadata = {
        "qa_goal": QA_GOAL,
        "csat_goal": CSAT_GOAL,
        "recontact_goal": RECONTACT_GOAL,
        "qa_mismatch_pct": round(mismatch_rate, 2),
        "total_qa_audits": len(qa),
        "total_csat_feedback": int(csat["Feedback CNT"].sum()),
        "total_contacts": int(rc["Contacts"].sum()),
        "total_recontacts": int(rc["Recontact Volume"].sum()),
    }
    (DATA_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2))

    print("\n=== KPI Summary ===")
    print(tables["kpi_summary"].to_string(index=False))
    return metadata


if __name__ == "__main__":
    main()
