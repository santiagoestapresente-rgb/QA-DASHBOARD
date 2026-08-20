"""
Action recommendations — derived from source Excel data only.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from config import CSAT_GOAL, MIN_SAMPLE_SIZE, QA_GOAL, RECONTACT_GOAL


@dataclass
class Recommendation:
    priority: str  # Alta, Media
    kpi: str       # general, qa, csat, recontact
    finding: str
    action: str
    owner: str


def generate_recommendations(
    audits: pd.DataFrame,
    errors: pd.DataFrame,
    csat: pd.DataFrame,
    recontact: pd.DataFrame,
    cr_impact: pd.DataFrame,
) -> list[Recommendation]:
    recs: list[Recommendation] = []
    if audits.empty:
        return recs

    qa_avg = audits["Score_Pct"].mean()
    fatal_rate = audits["Fatal_Flag"].mean() * 100

    # ── QA ────────────────────────────────────────────────────────────────
    if qa_avg < QA_GOAL:
        recs.append(Recommendation(
            priority="Alta", kpi="qa",
            finding=f"El score QA promedio cerró en {qa_avg:.1f}%, {QA_GOAL - qa_avg:.1f} puntos bajo la meta.",
            action="Enfocar calibración en los atributos del checklist con mayor tasa de fallo.",
            owner="QA Lead",
        ))

    if fatal_rate > 5:
        recs.append(Recommendation(
            priority="Alta", kpi="qa",
            finding=f"El {fatal_rate:.1f}% de las interacciones auditadas registró al menos un error crítico.",
            action="Reforzar protocolo en atributos críticos — un solo fallo deja el score en cero.",
            owner="Supervisores",
        ))

    if not errors.empty:
        top_err = (
            errors.groupby(["Error_Category", "Is_Critical"])
            .size().reset_index(name="Cantidad")
            .sort_values("Cantidad", ascending=False)
        )
        if len(top_err):
            row = top_err.iloc[0]
            recs.append(Recommendation(
                priority="Alta", kpi="qa",
                finding=f"'{row['Error_Category']}' concentra {row['Cantidad']} fallas — el atributo más repetido del periodo.",
                action=f"Incluir '{row['Error_Category']}' como tema principal en la próxima sesión de capacitación.",
                owner="QA Analyst",
            ))

    agent_qa = (
        audits.groupby(["Agent_ID", "Supervisor_ID"])
        .agg(Score=("Score_Pct", "mean"), Audits=("Audit_ID", "count"))
        .reset_index()
    )
    low_agents = agent_qa[(agent_qa["Score"] < QA_GOAL) & (agent_qa["Audits"] >= MIN_SAMPLE_SIZE)]
    if len(low_agents):
        names = ", ".join(low_agents.nsmallest(5, "Score")["Agent_ID"].tolist())
        recs.append(Recommendation(
            priority="Media", kpi="qa",
            finding=f"{len(low_agents)} agentes con muestra confiable (n≥{MIN_SAMPLE_SIZE}) están bajo meta.",
            action=f"Agendar feedback 1:1 con: {names}.",
            owner="Supervisores",
        ))

    sup_stats = (
        audits.groupby("Supervisor_ID")
        .agg(Fatal_Rate=("Fatal_Flag", "mean"), Audits=("Audit_ID", "count"))
        .reset_index()
    )
    sup_stats = sup_stats[sup_stats["Audits"] >= 10]
    if len(sup_stats) > 1:
        avg_fatal = sup_stats["Fatal_Rate"].mean()
        for _, s in sup_stats[sup_stats["Fatal_Rate"] > avg_fatal * 1.3].head(2).iterrows():
            recs.append(Recommendation(
                priority="Media", kpi="qa",
                finding=f"El equipo de {s['Supervisor_ID']} muestra {s['Fatal_Rate']*100:.1f}% de errores críticos, por encima del promedio ({avg_fatal*100:.1f}%).",
                action="Revisión de casos críticos del equipo y sesión de calibración con el supervisor.",
                owner="QA Lead",
            ))

    # ── CSAT ──────────────────────────────────────────────────────────────
    if not csat.empty and csat["Feedback CNT"].sum() > 0:
        csat_pct = csat["Satisfied_CNT"].sum() / csat["Feedback CNT"].sum() * 100
        if csat_pct < CSAT_GOAL:
            recs.append(Recommendation(
                priority="Alta", kpi="csat",
                finding=f"Solo el {csat_pct:.1f}% de clientes calificó 4–5 estrellas. La brecha vs meta es de {CSAT_GOAL - csat_pct:.1f} pp.",
                action="Cruzar los motivos de contacto de peor CSAT con comentarios abiertos para identificar fricciones.",
                owner="CX Operations",
            ))
            worst_cr = (
                csat.groupby("CR_Lv4")
                .agg(Feedback=("Feedback CNT", "sum"), Satisfied=("Satisfied_CNT", "sum"))
                .reset_index()
            )
            worst_cr["CSAT"] = (worst_cr["Satisfied"] / worst_cr["Feedback"] * 100).round(1)
            worst_cr = worst_cr[worst_cr["Feedback"] >= 10].nsmallest(3, "CSAT")
            if len(worst_cr):
                crs = ", ".join(worst_cr["CR_Lv4"].tolist())
                recs.append(Recommendation(
                    priority="Media", kpi="csat",
                    finding=f"Los clientes califican peor cuando contactan por: {crs}.",
                    action="Validar script, tiempos de espera y resolución en esos flujos.",
                    owner="Process Owner",
                ))

    # ── Recontact ─────────────────────────────────────────────────────────
    if not recontact.empty and recontact["Contacts"].sum() > 0:
        rc_rate = recontact["Recontact Volume"].sum() / recontact["Contacts"].sum() * 100
        if rc_rate > RECONTACT_GOAL:
            recs.append(Recommendation(
                priority="Alta", kpi="recontact",
                finding=f"El {rc_rate:.2f}% de los contactos termina en recontacto — {rc_rate - RECONTACT_GOAL:.2f} pp sobre la meta.",
                action="Priorizar auditorías en interacciones de motivos con alta tasa de recontacto.",
                owner="Operations",
            ))
            rc_cr = (
                recontact.groupby("CR_Lv4")
                .agg(Contacts=("Contacts", "sum"), Recontacts=("Recontact Volume", "sum"))
                .reset_index()
            )
            rc_cr["Rate"] = (rc_cr["Recontacts"] / rc_cr["Contacts"] * 100).round(2)
            worst = rc_cr[rc_cr["Contacts"] >= 50].nlargest(3, "Rate")
            if len(worst):
                crs = ", ".join(worst["CR_Lv4"].tolist())
                recs.append(Recommendation(
                    priority="Media", kpi="recontact",
                    finding=f"Los clientes vuelven a contactar con más frecuencia por: {crs}.",
                    action="Verificar que el agente confirme resolución y documente correctamente la gestión.",
                    owner="QA + Supervisores",
                ))

    # ── General (cross-metric) ────────────────────────────────────────────
    if qa_avg >= QA_GOAL and not csat.empty and csat["Feedback CNT"].sum() > 0:
        csat_pct = csat["Satisfied_CNT"].sum() / csat["Feedback CNT"].sum() * 100
        if csat_pct < CSAT_GOAL:
            recs.append(Recommendation(
                priority="Alta", kpi="general",
                finding=f"La operación cumple QA ({qa_avg:.1f}%) pero el CSAT ({csat_pct:.1f}%) no — hay una desconexión entre calidad auditada y percepción del cliente.",
                action="Recalibrar criterios de auditoría y revisar variables fuera del control del agente (tiempos, políticas, compensaciones).",
                owner="CX Leadership",
            ))

    if not cr_impact.empty and not audits.empty:
        qa_cr = audits.groupby("CR_Lv4").agg(QA=("Score_Pct", "mean")).reset_index()
        merged = qa_cr.merge(cr_impact, on="CR_Lv4", how="inner")
        bad = merged[
            (merged["QA"] < QA_GOAL)
            & (merged["CSAT_Pct"] < CSAT_GOAL)
            & (merged["Recontact_Rate"] > RECONTACT_GOAL)
        ]
        if len(bad):
            crs = ", ".join(bad.nlargest(3, "Recontact_Rate")["CR_Lv4"].tolist())
            recs.append(Recommendation(
                priority="Alta", kpi="general",
                finding=f"{crs} presentan baja calidad QA, bajo CSAT y alto recontacto simultáneamente.",
                action="Tratar como hotspots operativos: revisión end-to-end de proceso, script y capacitación.",
                owner="CX Leadership",
            ))

    order = {"Alta": 0, "Media": 1}
    return sorted(recs, key=lambda r: order.get(r.priority, 9))


def filter_by_kpi(recs: list[Recommendation], kpi: str) -> list[Recommendation]:
    if kpi == "general":
        return [r for r in recs if r.kpi == "general"]
    return [r for r in recs if r.kpi == kpi]
