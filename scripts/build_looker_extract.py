"""Looker data pack: one sheet per KPI.

Each KPI sheet is long-format. Column `Vista` picks the chart.
Filter Vista in Looker, then map Dimension / Valor / Meta.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import CSAT_GOAL, QA_GOAL, RECONTACT_GOAL  # noqa: E402
from modules.data_loader import load_all_data  # noqa: E402
from modules.kpis import (  # noqa: E402
    add_pareto_cumulative,
    avg_qa_score,
    csat_by_star_rating,
    csat_by_user_tenure,
    csat_control_daily,
    daily_metrics_trend,
    iso_week_label,
    kpi_by_channel,
    kpi_summary,
    normalize_channel_label,
    overall_csat,
    qa_by_tenure,
    qa_control_daily,
    qa_score_by_cr,
    qa_score_histogram,
    recontact_by_cr,
    recontact_by_scope,
    recontact_control_daily,
    recontact_rate,
    slice_coverage_table,
    top_failing_attributes,
    voc_themes_negative,
    volume_totals,
    weekly_by_channel,
    weekly_kpi_table,
)

OUT = ROOT / "looker" / "DiDi_CX_Looker_Data.xlsx"

COLS = [
    "Vista",
    "Como_usarlo",
    "Week",
    "Date",
    "Channel",
    "Tenure",
    "Categoria",
    "Valor",
    "Meta",
    "vs_Meta",
    "WoW_pp",
    "n",
    "Cum_Pct",
    "CL",
    "UCL",
    "LCL",
    "Beyond_Limits",
]


def _blank() -> dict:
    return {c: np.nan for c in COLS}


def _row(**kwargs) -> dict:
    r = _blank()
    r.update(kwargs)
    return r


def _datestr(v) -> str | float:
    ts = pd.to_datetime(v, errors="coerce")
    if pd.isna(ts):
        return np.nan
    return ts.strftime("%Y-%m-%d")


def _frame(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=COLS)
    for c in ["Valor", "Meta", "vs_Meta", "WoW_pp", "n", "Cum_Pct", "CL", "UCL", "LCL"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def build_qa(audits: pd.DataFrame, errors: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    qa_val = round(avg_qa_score(audits), 2)
    rows.append(_row(
        Vista="00_Scorecard",
        Como_usarlo="Scorecard: Valor = QA del periodo. Meta=85. n=evaluaciones.",
        Valor=qa_val,
        Meta=QA_GOAL,
        vs_Meta=round(qa_val - QA_GOAL, 2),
        n=len(audits),
    ))
    weekly = weekly_kpi_table(audits, pd.DataFrame(), pd.DataFrame())
    for _, r in weekly.iterrows():
        if pd.isna(r.get("QA_Score")):
            continue
        rows.append(_row(
            Vista="01_WoW_semanal",
            Como_usarlo="Linea: X=Week Y=Valor. Linea de meta=Meta. Etiqueta WoW_pp.",
            Week=r["Week"],
            Valor=r["QA_Score"],
            Meta=QA_GOAL,
            vs_Meta=r.get("QA_vs_Goal"),
            WoW_pp=r.get("QA_WoW_pp"),
            n=r.get("QA_Evaluations"),
        ))

    if not audits.empty:
        wch = (
            audits.assign(Channel=audits["Channel"].map(normalize_channel_label))
            .groupby(["Week", "Channel"], as_index=False)
            .agg(Valor=("Score_Pct", "mean"), n=("Audit_ID", "count"))
        )
        wch["Valor"] = wch["Valor"].round(2)
        for ch, g in wch.groupby("Channel"):
            g = g.sort_values("Week")
            wow = g["Valor"].diff()
            for i, r in enumerate(g.itertuples(index=False)):
                rows.append(_row(
                    Vista="02_WoW_por_canal",
                    Como_usarlo="Filtra Channel. X=Week Y=Valor. Meta=85.",
                    Week=r.Week,
                    Channel=r.Channel,
                    Valor=r.Valor,
                    Meta=QA_GOAL,
                    vs_Meta=round(r.Valor - QA_GOAL, 2),
                    WoW_pp=None if i == 0 or pd.isna(wow.iloc[i]) else round(float(wow.iloc[i]), 2),
                    n=r.n,
                ))

    daily = daily_metrics_trend(audits, pd.DataFrame(), pd.DataFrame())
    for _, r in daily.iterrows():
        if pd.isna(r.get("QA_Score")):
            continue
        rows.append(_row(
            Vista="03_Tendencia_diaria",
            Como_usarlo="X=Date Y=Valor. Meta=85.",
            Date=_datestr(r["Date"]),
            Week=iso_week_label(pd.Series([r["Date"]])).iloc[0] if pd.notna(r.get("Date")) else np.nan,
            Valor=round(float(r["QA_Score"]), 2),
            Meta=QA_GOAL,
            vs_Meta=round(float(r["QA_Score"]) - QA_GOAL, 2),
        ))

    for _, r in kpi_by_channel(audits, pd.DataFrame(), pd.DataFrame()).iterrows():
        if not r.get("Has_QA"):
            continue
        rows.append(_row(
            Vista="04_Por_canal",
            Como_usarlo="Barras: X=Channel Y=Valor. Meta=85.",
            Channel=r["Channel"],
            Valor=r["QA_Score"],
            Meta=QA_GOAL,
            vs_Meta=r.get("QA_vs_Goal"),
            n=r.get("QA_Evaluations"),
        ))

    for _, r in qa_by_tenure(audits).iterrows():
        rows.append(_row(
            Vista="05_Por_tenure_agente",
            Como_usarlo="Barras: X=Tenure Y=Valor. SOLO QA. Meta=85.",
            Tenure=r["Tenure_Cohort"],
            Categoria=r["Tenure_Raw"],
            Valor=r["QA_Score"],
            Meta=QA_GOAL,
            vs_Meta=r["QA_vs_Goal"],
            n=r["QA_Evaluations"],
        ))

    spc = qa_control_daily(audits)
    for _, r in spc.iterrows():
        rows.append(_row(
            Vista="06_Control_chart",
            Como_usarlo="Series: Date vs Valor, CL, UCL, LCL, Meta.",
            Date=_datestr(r["Date"]),
            Valor=r["Value"],
            Meta=r["Goal"],
            vs_Meta=round(float(r["Value"]) - float(r["Goal"]), 2),
            CL=r["CL"],
            UCL=r["UCL"],
            LCL=r["LCL"],
            Beyond_Limits=bool(r["Beyond_Limits"]),
        ))

    top = add_pareto_cumulative(
        top_failing_attributes(errors, audits, top_n=20).rename(columns={"Fail_Count": "Count"}),
        "Count",
    )
    for _, r in top.iterrows():
        rows.append(_row(
            Vista="07_Pareto_atributos",
            Como_usarlo="Barras Y=Categoria X=Valor(Count). Linea Cum_Pct 0-100.",
            Categoria=r["Error_Category"],
            Valor=r["Count"],
            Cum_Pct=r["Cum_Pct"],
            n=r["Count"],
        ))

    hist = qa_score_histogram(audits)
    for _, r in hist.iterrows():
        rows.append(_row(
            Vista="08_Histograma",
            Como_usarlo="Barras X=Categoria (score) Y=n.",
            Categoria=str(int(r["QA_Score"])),
            Valor=r["Audits"],
            Meta=QA_GOAL,
            n=r["Audits"],
            Cum_Pct=r["Share_Pct"],
        ))

    for _, r in qa_score_by_cr(audits, top_n=25).iterrows():
        rows.append(_row(
            Vista="09_Por_CR_Lv4",
            Como_usarlo="Barras X=Categoria (CR) Y=Valor. Meta=85.",
            Categoria=r["CR_Lv4"],
            Valor=r["QA_Score"],
            Meta=QA_GOAL,
            vs_Meta=r["vs_goal"],
            n=r["N"],
        ))

    if not errors.empty:
        g = errors.groupby(["Channel", "Error_Category"], as_index=False).size().rename(columns={"size": "Count"})
        for _, r in g.iterrows():
            rows.append(_row(
                Vista="10_Atributos_por_canal",
                Como_usarlo="Filtra Channel. Barras Categoria vs Valor.",
                Channel=r["Channel"],
                Categoria=r["Error_Category"],
                Valor=r["Count"],
                n=r["Count"],
            ))

    if not audits.empty:
        ag = (
            audits.groupby(["Agent_ID", "Channel", "Tenure_Cohort"], as_index=False)
            .agg(Valor=("Score_Pct", "mean"), n=("Audit_ID", "count"))
        )
        ag = ag[ag["n"] >= 5]
        for _, r in ag.iterrows():
            rows.append(_row(
                Vista="11_Por_agente_n5",
                Como_usarlo="Tabla/barras Categoria=Agent. Filtro Channel y Tenure.",
                Channel=r["Channel"],
                Tenure=r["Tenure_Cohort"],
                Categoria=str(r["Agent_ID"]),
                Valor=round(float(r["Valor"]), 2),
                Meta=QA_GOAL,
                vs_Meta=round(float(r["Valor"]) - QA_GOAL, 2),
                n=r["n"],
            ))

    return _frame(rows)


def build_csat(csat: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    csat_val = round(overall_csat(csat), 2)
    rows.append(_row(
        Vista="00_Scorecard",
        Como_usarlo="Scorecard: Valor = CSAT del periodo. Meta=85. n=encuestas.",
        Valor=csat_val,
        Meta=CSAT_GOAL,
        vs_Meta=round(csat_val - CSAT_GOAL, 2),
        n=int(csat["Feedback CNT"].sum()) if not csat.empty else 0,
    ))
    weekly = weekly_kpi_table(pd.DataFrame(), csat, pd.DataFrame())
    for _, r in weekly.iterrows():
        if pd.isna(r.get("CSAT_Score")):
            continue
        rows.append(_row(
            Vista="01_WoW_semanal",
            Como_usarlo="Linea X=Week Y=Valor. Meta=85. WoW_pp.",
            Week=r["Week"],
            Valor=r["CSAT_Score"],
            Meta=CSAT_GOAL,
            vs_Meta=r.get("CSAT_vs_Goal"),
            WoW_pp=r.get("CSAT_WoW_pp"),
            n=r.get("Feedback"),
        ))

    if not csat.empty and "Channel" in csat.columns:
        tmp = csat.copy()
        tmp["Week"] = iso_week_label(tmp["Fecha"])
        tmp["Channel"] = tmp["Channel"].map(normalize_channel_label)
        g = tmp.groupby(["Week", "Channel"], as_index=False).agg(
            sat=("Satisfied_CNT", "sum"), n=("Feedback CNT", "sum")
        )
        g["Valor"] = np.where(g["n"] > 0, (g["sat"] / g["n"] * 100).round(2), np.nan)
        for ch, sub in g.groupby("Channel"):
            sub = sub.sort_values("Week")
            wow = sub["Valor"].diff()
            for i, r in enumerate(sub.itertuples(index=False)):
                rows.append(_row(
                    Vista="02_WoW_por_canal",
                    Como_usarlo="Filtra Channel. X=Week Y=Valor. Meta=85.",
                    Week=r.Week,
                    Channel=r.Channel,
                    Valor=r.Valor,
                    Meta=CSAT_GOAL,
                    vs_Meta=None if pd.isna(r.Valor) else round(float(r.Valor) - CSAT_GOAL, 2),
                    WoW_pp=None if i == 0 or pd.isna(wow.iloc[i]) else round(float(wow.iloc[i]), 2),
                    n=r.n,
                ))

    daily = daily_metrics_trend(pd.DataFrame(), csat, pd.DataFrame())
    for _, r in daily.iterrows():
        if pd.isna(r.get("CSAT_Score")):
            continue
        rows.append(_row(
            Vista="03_Tendencia_diaria",
            Como_usarlo="X=Date Y=Valor. Meta=85.",
            Date=_datestr(r["Date"]),
            Valor=round(float(r["CSAT_Score"]), 2),
            Meta=CSAT_GOAL,
            vs_Meta=round(float(r["CSAT_Score"]) - CSAT_GOAL, 2),
        ))

    for _, r in kpi_by_channel(pd.DataFrame(), csat, pd.DataFrame()).iterrows():
        if not r.get("Has_CSAT"):
            continue
        rows.append(_row(
            Vista="04_Por_canal",
            Como_usarlo="Barras Channel vs Valor. Meta=85.",
            Channel=r["Channel"],
            Valor=r["CSAT_Score"],
            Meta=CSAT_GOAL,
            vs_Meta=r.get("CSAT_vs_Goal"),
            n=r.get("Surveys"),
        ))

    for _, r in csat_by_user_tenure(csat).iterrows():
        rows.append(_row(
            Vista="05_Por_tenure_CSAT",
            Como_usarlo="NO es el tenure de QA. Campo user_tenure. Barras Tenure vs Valor.",
            Tenure=r["CSAT_Agent_Tenure"],
            Valor=r["CSAT_Score"],
            Meta=CSAT_GOAL,
            vs_Meta=r["CSAT_vs_Goal"],
            n=r["Feedback"],
        ))

    spc = csat_control_daily(csat)
    for _, r in spc.iterrows():
        rows.append(_row(
            Vista="06_Control_chart",
            Como_usarlo="Date vs Valor, CL, UCL, LCL, Meta.",
            Date=_datestr(r["Date"]),
            Valor=r["Value"],
            Meta=r["Goal"],
            vs_Meta=round(float(r["Value"]) - float(r["Goal"]), 2),
            CL=r["CL"],
            UCL=r["UCL"],
            LCL=r["LCL"],
            Beyond_Limits=bool(r["Beyond_Limits"]),
        ))

    stars = csat_by_star_rating(csat)
    for _, r in stars.iterrows():
        rows.append(_row(
            Vista="07_Por_estrellas",
            Como_usarlo="Barras Categoria=1-5 star, Valor=Count o Cum_Pct=share.",
            Categoria=r["Rating"],
            Valor=r["Count"],
            n=r["Count"],
            Cum_Pct=r["Pct"],
        ))

    voc = voc_themes_negative(csat, top_n=10)
    for _, r in voc.iterrows():
        rows.append(_row(
            Vista="08_VOC_negativo",
            Como_usarlo="Barras Categoria=theme Y=Valor (menciones).",
            Categoria=r["Theme"],
            Valor=r["Mentions"],
            n=r["Mentions"],
            Cum_Pct=r["Pct"],
        ))

    if not csat.empty and "CR_Lv4" in csat.columns:
        cr = (
            csat.groupby("CR_Lv4", as_index=False)
            .agg(sat=("Satisfied_CNT", "sum"), n=("Feedback CNT", "sum"))
        )
        cr = cr[cr["n"] >= 20]
        cr["Valor"] = (cr["sat"] / cr["n"] * 100).round(2)
        for _, r in cr.sort_values("Valor").head(25).iterrows():
            rows.append(_row(
                Vista="09_Por_CR_Lv4",
                Como_usarlo="Barras CR vs Valor. Meta=85. Min 20 encuestas.",
                Categoria=r["CR_Lv4"],
                Valor=r["Valor"],
                Meta=CSAT_GOAL,
                vs_Meta=round(float(r["Valor"]) - CSAT_GOAL, 2),
                n=r["n"],
            ))

    return _frame(rows)


def build_recontact(recontact: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    rc = recontact_rate(recontact)
    n = int(recontact["Contacts"].sum()) if not recontact.empty else 0
    rows.append(_row(
        Vista="00_Scorecard",
        Como_usarlo="Scorecard: Valor = tasa oficial (ratio de sumas). Meta=5.44. Mas bajo es mejor.",
        Valor=round(rc, 2),
        Meta=RECONTACT_GOAL,
        vs_Meta=round(rc - RECONTACT_GOAL, 2),
        n=n,
    ))
    weekly = weekly_kpi_table(pd.DataFrame(), pd.DataFrame(), recontact)
    for _, r in weekly.iterrows():
        if pd.isna(r.get("Recontact_Rate")):
            continue
        rows.append(_row(
            Vista="01_WoW_semanal",
            Como_usarlo="Linea X=Week Y=Valor. Meta=5.44. Mas bajo es mejor.",
            Week=r["Week"],
            Valor=r["Recontact_Rate"],
            Meta=RECONTACT_GOAL,
            vs_Meta=r.get("Recontact_vs_Goal"),
            WoW_pp=r.get("Recontact_WoW_pp"),
            n=r.get("Contacts"),
        ))

    if not recontact.empty and "standard_channel_name" in recontact.columns:
        tmp = recontact.copy()
        tmp["Week"] = iso_week_label(tmp["Fecha"])
        tmp["Channel"] = tmp["standard_channel_name"].map(normalize_channel_label)
        g = tmp.groupby(["Week", "Channel"], as_index=False).agg(
            vol=("Recontact Volume", "sum"), n=("Contacts", "sum")
        )
        g["Valor"] = np.where(g["n"] > 0, (g["vol"] / g["n"] * 100).round(2), np.nan)
        for ch, sub in g.groupby("Channel"):
            sub = sub.sort_values("Week")
            wow = sub["Valor"].diff()
            for i, r in enumerate(sub.itertuples(index=False)):
                rows.append(_row(
                    Vista="02_WoW_por_canal",
                    Como_usarlo="Filtra Channel (Self Help vs Phone vs Live Chat). X=Week Y=Valor.",
                    Week=r.Week,
                    Channel=r.Channel,
                    Valor=r.Valor,
                    Meta=RECONTACT_GOAL,
                    vs_Meta=None if pd.isna(r.Valor) else round(float(r.Valor) - RECONTACT_GOAL, 2),
                    WoW_pp=None if i == 0 or pd.isna(wow.iloc[i]) else round(float(wow.iloc[i]), 2),
                    n=r.n,
                ))

    daily = daily_metrics_trend(pd.DataFrame(), pd.DataFrame(), recontact)
    for _, r in daily.iterrows():
        if pd.isna(r.get("Recontact_Rate")):
            continue
        rows.append(_row(
            Vista="03_Tendencia_diaria",
            Como_usarlo="X=Date Y=Valor. Meta=5.44.",
            Date=_datestr(r["Date"]),
            Valor=round(float(r["Recontact_Rate"]), 2),
            Meta=RECONTACT_GOAL,
            vs_Meta=round(float(r["Recontact_Rate"]) - RECONTACT_GOAL, 2),
        ))

    for _, r in kpi_by_channel(pd.DataFrame(), pd.DataFrame(), recontact).iterrows():
        if not r.get("Has_Recontact"):
            continue
        rows.append(_row(
            Vista="04_Por_canal",
            Como_usarlo="Barras Channel vs Valor. Meta=5.44. Self Help diluye el total.",
            Channel=r["Channel"],
            Valor=r["Recontact_Rate"],
            Meta=RECONTACT_GOAL,
            vs_Meta=r.get("Recontact_vs_Goal"),
            n=r.get("Contacts"),
        ))

    spc = recontact_control_daily(recontact)
    for _, r in spc.iterrows():
        rows.append(_row(
            Vista="05_Control_chart",
            Como_usarlo="Date vs Valor, CL, UCL, LCL, Meta.",
            Date=_datestr(r["Date"]),
            Valor=r["Value"],
            Meta=r["Goal"],
            vs_Meta=round(float(r["Value"]) - float(r["Goal"]), 2),
            CL=r["CL"],
            UCL=r["UCL"],
            LCL=r["LCL"],
            Beyond_Limits=bool(r["Beyond_Limits"]),
        ))

    pareto = add_pareto_cumulative(
        recontact_by_cr(recontact, top_n=20).rename(columns={"Recontacts": "Count"}),
        "Count",
    )
    for _, r in pareto.iterrows():
        rows.append(_row(
            Vista="06_Pareto_CR",
            Como_usarlo="Barras Categoria=CR Valor=Count. Linea Cum_Pct.",
            Categoria=r["CR_Lv4"],
            Valor=r["Count"],
            Cum_Pct=r["Cum_Pct"],
            n=r.get("Contacts"),
        ))

    for _, r in recontact_by_scope(recontact).iterrows():
        rows.append(_row(
            Vista="07_Por_alcance",
            Como_usarlo="Barras Categoria=alcance Y=Valor. Oficial vs sin Self Help vs Phone+Chat.",
            Categoria=r["Scope"],
            Valor=r["Rate"],
            Meta=RECONTACT_GOAL,
            vs_Meta=r["vs_goal"],
            n=r["Contacts"],
        ))

    return _frame(rows)


def main() -> None:
    data = load_all_data()
    audits, errors, csat, recontact = (
        data["fact_audits"], data["fact_errors"], data["fact_csat"], data["fact_recontact"],
    )
    summary = kpi_summary(audits, csat, recontact)
    rc = recontact_rate(recontact)
    vol = volume_totals(audits, csat, recontact)

    como = pd.DataFrame(
        [
            {
                "KPI_hoja": "QA",
                "Vista": "01_WoW_semanal",
                "Grafico_Looker": "Linea",
                "X": "Week",
                "Y": "Valor",
                "Meta": "Meta = 85",
            },
            {
                "KPI_hoja": "QA",
                "Vista": "02_WoW_por_canal",
                "Grafico_Looker": "Linea + filtro Channel",
                "X": "Week",
                "Y": "Valor",
                "Meta": "Meta = 85",
            },
            {
                "KPI_hoja": "QA",
                "Vista": "04_Por_canal",
                "Grafico_Looker": "Barras",
                "X": "Channel",
                "Y": "Valor",
                "Meta": "Meta = 85",
            },
            {
                "KPI_hoja": "QA",
                "Vista": "05_Por_tenure_agente",
                "Grafico_Looker": "Barras",
                "X": "Tenure",
                "Y": "Valor",
                "Meta": "Meta = 85. Solo existe en QA.",
            },
            {
                "KPI_hoja": "QA",
                "Vista": "06_Control_chart",
                "Grafico_Looker": "Series temporales",
                "X": "Date",
                "Y": "Valor + CL + UCL + LCL + Meta",
                "Meta": "Goal 85 y limites estadisticos",
            },
            {
                "KPI_hoja": "QA",
                "Vista": "07_Pareto_atributos",
                "Grafico_Looker": "Combinado barras+linea",
                "X": "Categoria",
                "Y": "Valor (barras) y Cum_Pct (linea 0-100)",
                "Meta": "—",
            },
            {
                "KPI_hoja": "CSAT",
                "Vista": "01_WoW_semanal",
                "Grafico_Looker": "Linea",
                "X": "Week",
                "Y": "Valor",
                "Meta": "Meta = 85",
            },
            {
                "KPI_hoja": "CSAT",
                "Vista": "07_Por_estrellas",
                "Grafico_Looker": "Barras",
                "X": "Categoria",
                "Y": "Valor o Cum_Pct",
                "Meta": "—",
            },
            {
                "KPI_hoja": "CSAT",
                "Vista": "08_VOC_negativo",
                "Grafico_Looker": "Barras",
                "X": "Categoria",
                "Y": "Valor",
                "Meta": "—",
            },
            {
                "KPI_hoja": "Recontact",
                "Vista": "01_WoW_semanal",
                "Grafico_Looker": "Linea",
                "X": "Week",
                "Y": "Valor",
                "Meta": "Meta = 5.44 (mas bajo es mejor)",
            },
            {
                "KPI_hoja": "Recontact",
                "Vista": "07_Por_alcance",
                "Grafico_Looker": "Barras 5.83 vs 15.56",
                "X": "Categoria",
                "Y": "Valor",
                "Meta": "Meta = 5.44",
            },
        ]
    )
    como.loc[len(como)] = {
        "KPI_hoja": "QA / CSAT / Recontact",
        "Vista": "(cualquier Vista)",
        "Grafico_Looker": "En Looker: filtra Vista = el grafico que quieras. Una fuente = una hoja KPI.",
        "X": "ver columna Como_usarlo de cada fila",
        "Y": "siempre Valor",
        "Meta": "siempre Meta",
    }

    totales = pd.DataFrame(
        [{
            "QA_Score": round(summary["qa_score"], 2),
            "QA_Goal": QA_GOAL,
            "CSAT_Score": round(summary["csat"], 2),
            "CSAT_Goal": CSAT_GOAL,
            "Recontact_Rate": round(rc, 2),
            "Recontact_Goal": RECONTACT_GOAL,
            "Contacts": vol["contacts"],
            "Surveys": vol["surveys"],
            "QA_Evaluations": vol["evaluations"],
        }]
    )

    qa = build_qa(audits, errors)
    cs = build_csat(csat)
    rec = build_recontact(recontact)

    pagina1 = weekly_by_channel(audits, csat, recontact)
    pagina1["QA_Score_Sum"] = pagina1["QA_Score"] * pagina1["QA_Evaluations"]
    pagina1_cols = [
        "Week", "Channel",
        "QA_Score", "QA_Evaluations", "QA_Score_Sum", "QA_Goal",
        "CSAT_Score", "Satisfied", "Feedback", "CSAT_Goal",
        "Recontact_Rate", "Recontacts", "Contacts", "Recontact_Goal",
    ]
    pagina1 = pagina1[[c for c in pagina1_cols if c in pagina1.columns]]

    qa_w = float(pagina1["QA_Score_Sum"].sum() / pagina1["QA_Evaluations"].sum())
    csat_w = float(pagina1["Satisfied"].sum() / pagina1["Feedback"].sum() * 100)
    rc_w = float(pagina1["Recontacts"].sum() / pagina1["Contacts"].sum() * 100)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    target = OUT
    try:
        writer_ctx = pd.ExcelWriter(target, engine="openpyxl")
        writer_ctx.__enter__()
        writer_ctx.__exit__(None, None, None)
    except PermissionError:
        target = OUT.with_name("DiDi_CX_Looker_Data_new.xlsx")
        print(f"Excel abierto: escribo {target}. Cerra el original y renombra.")
    with pd.ExcelWriter(OUT, engine="openpyxl") as writer:
        como.to_excel(writer, sheet_name="COMO_USAR", index=False)
        totales.to_excel(writer, sheet_name="TOTALES", index=False)
        pagina1.to_excel(writer, sheet_name="PAGINA1", index=False)
        slice_coverage_table().to_excel(writer, sheet_name="CORTES", index=False)
        qa.to_excel(writer, sheet_name="QA", index=False)
        cs.to_excel(writer, sheet_name="CSAT", index=False)
        rec.to_excel(writer, sheet_name="Recontact", index=False)
        for name in ("COMO_USAR", "TOTALES", "PAGINA1", "CORTES", "QA", "CSAT", "Recontact"):
            ws = writer.sheets[name]
            ws.auto_filter.ref = ws.dimensions
            ws.freeze_panes = "A2"

    print(f"Wrote {OUT}")
    print(f"QA rows {len(qa)}  CSAT rows {len(cs)}  RC rows {len(rec)}  PAGINA1 {len(pagina1)}")
    print(f"Totals {summary['qa_score']:.2f} / {summary['csat']:.2f} / {rc:.2f}")
    print(f"PAGINA1 weighted {qa_w:.2f} / {csat_w:.2f} / {rc_w:.2f}")
    print("QA vistas:", ", ".join(sorted(qa["Vista"].dropna().unique())))
    print("CSAT vistas:", ", ".join(sorted(cs["Vista"].dropna().unique())))
    print("RC vistas:", ", ".join(sorted(rec["Vista"].dropna().unique())))


if __name__ == "__main__":
    main()
