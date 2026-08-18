"""
DiDi CX Quality Analyst — Performance Dashboard
Deliverable 1 — Business Case Selection Process
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Config ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DiDi CX Performance Dashboard",
    page_icon="🟠",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

DIDI_ORANGE = "#FF6600"
DIDI_DARK = "#1A1A1A"
DIDI_WHITE = "#FFFFFF"
STATUS_COLORS = {"green": "#28a745", "amber": "#ffc107", "red": "#dc3545"}

QA_GOAL = 85
CSAT_GOAL = 85
RECONTACT_GOAL = 5.44


@st.cache_data(ttl=300)
def load_table(name: str) -> pd.DataFrame:
    path = DATA_DIR / f"{name}.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=300)
def load_metadata() -> dict:
    path = DATA_DIR / "metadata.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}


def status_emoji(status: str) -> str:
    return {"green": "🟢", "amber": "🟡", "red": "🔴"}.get(status, "⚪")


def kpi_card(label: str, value: float, goal: float, status: str, unit: str = ""):
    color = STATUS_COLORS.get(status, DIDI_DARK)
    suffix = unit if unit != "score" else ""
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {DIDI_DARK} 0%, #2d2d2d 100%);
            border-left: 5px solid {DIDI_ORANGE};
            border-radius: 10px;
            padding: 20px 24px;
            margin-bottom: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        ">
            <div style="color: #aaa; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">
                {label}
            </div>
            <div style="color: {DIDI_WHITE}; font-size: 36px; font-weight: 700; margin: 8px 0;">
                {value:.2f}{suffix}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #888; font-size: 13px;">Goal: {goal}{suffix}</span>
                <span style="
                    background: {color}; color: white;
                    padding: 3px 12px; border-radius: 20px;
                    font-size: 12px; font-weight: 600;
                ">{status.upper()}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_plotly_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        font=dict(family="Segoe UI, Arial", color=DIDI_DARK),
        plot_bgcolor=DIDI_WHITE,
        paper_bgcolor=DIDI_WHITE,
        colorway=[DIDI_ORANGE, DIDI_DARK, "#FF8533", "#666666", "#FFB380"],
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def goal_line(value: float, label: str = "Goal") -> dict:
    return dict(
        type="line",
        yref="y",
        y0=value,
        y1=value,
        line=dict(color=STATUS_COLORS["green"], width=2, dash="dash"),
        annotation_text=f"{label}: {value}",
        annotation_position="right",
    )


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align:center; padding: 16px 0;">
            <span style="font-size: 28px; font-weight: 800; color: {DIDI_ORANGE};">DiDi</span>
            <div style="font-size: 11px; color: #888; margin-top: 4px;">CX Performance Dashboard</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "QA Analysis",
            "CSAT / VOC",
            "Recontact",
            "Combined Insights",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**Filters**")

    qa_detail = load_table("qa_detail")
    csat_cr = load_table("csat_by_cr")

    channels = ["All"] + sorted(qa_detail["Channel"].dropna().unique().tolist()) if len(qa_detail) else ["All"]
    countries = ["All"] + sorted(qa_detail["Country"].dropna().unique().tolist()) if len(qa_detail) else ["All"]
    crs = (
        ["All"]
        + sorted(qa_detail["CR_Lv4"].dropna().unique().tolist())[:50]
        if len(qa_detail)
        else ["All"]
    )

    sel_channel = st.selectbox("Channel", channels)
    sel_country = st.selectbox("Country", countries)
    sel_cr = st.selectbox("Contact Reason (CR Lv4)", crs)

    st.divider()
    st.caption("Data source: Business Case.xlsx · Week W19")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


def filter_qa(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if sel_channel != "All":
        out = out[out["Channel"] == sel_channel]
    if sel_country != "All":
        out = out[out["Country"] == sel_country]
    if sel_cr != "All":
        out = out[out["CR_Lv4"] == sel_cr]
    return out


# ── Load data ──────────────────────────────────────────────────────────────
kpi = load_table("kpi_summary")
qa_by_channel = load_table("qa_by_channel")
qa_by_cr = load_table("qa_by_cr")
qa_attrs = load_table("qa_attributes")
csat_by_channel = load_table("csat_by_channel")
csat_by_cr = load_table("csat_by_cr")
csat_by_bt = load_table("csat_by_business_type")
rc_by_cr = load_table("recontact_by_cr")
rc_by_channel = load_table("recontact_by_channel")
combined = load_table("combined_analysis")
voc = load_table("voc_sample")
qa_detail_f = filter_qa(qa_detail)
meta = load_metadata()

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="
        background: {DIDI_DARK}; color: white;
        padding: 20px 28px; border-radius: 12px;
        margin-bottom: 24px;
        border-bottom: 4px solid {DIDI_ORANGE};
    ">
        <h1 style="margin:0; font-size: 24px; color: white;">
            CX Service Operations — Weekly Performance
        </h1>
        <p style="margin: 6px 0 0; color: #aaa; font-size: 14px;">
            Delivery · Food · Week W19 · Phone & Live Chat
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════
if page == "Overview":
    st.subheader("Executive KPIs vs. Goals")

    if len(kpi):
        c1, c2, c3 = st.columns(3)
        with c1:
            row = kpi[kpi["Metric"] == "QA Score"].iloc[0]
            kpi_card("QA Score", row["Value"], row["Goal"], row["Status"], row["Unit"])
        with c2:
            row = kpi[kpi["Metric"] == "CSAT"].iloc[0]
            kpi_card("CSAT", row["Value"], row["Goal"], row["Status"], "%")
        with c3:
            row = kpi[kpi["Metric"] == "Recontact Rate"].iloc[0]
            kpi_card("Recontact Rate", row["Value"], row["Goal"], row["Status"], "%")

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("#### QA Score by Channel")
        if len(qa_by_channel):
            fig = px.bar(
                qa_by_channel,
                x="Channel",
                y="QA_Score",
                color="Status",
                color_discrete_map=STATUS_COLORS,
                text="QA_Score",
            )
            fig.add_hline(y=QA_GOAL, line_dash="dash", line_color="green",
                          annotation_text=f"Goal: {QA_GOAL}")
            fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
            st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

    with col_r:
        st.markdown("#### CSAT by Channel")
        if len(csat_by_channel):
            fig = px.bar(
                csat_by_channel,
                x="Channel",
                y="CSAT_Pct",
                color="Status",
                color_discrete_map=STATUS_COLORS,
                text="CSAT_Pct",
            )
            fig.add_hline(y=CSAT_GOAL, line_dash="dash", line_color="green",
                          annotation_text=f"Goal: {CSAT_GOAL}%")
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

    col_l2, col_r2 = st.columns(2)

    with col_l2:
        st.markdown("#### Top 10 CRs — Lowest QA Score")
        cr_filtered = qa_by_cr.copy()
        if sel_channel != "All":
            cr_filtered = cr_filtered[cr_filtered["Channel"] == sel_channel]
        top_bad = cr_filtered.nsmallest(10, "QA_Score")
        st.dataframe(
            top_bad[["CR_Lv4", "Channel", "QA_Score", "Audits", "Status"]],
            hide_index=True,
            use_container_width=True,
        )

    with col_r2:
        st.markdown("#### Top 10 CRs — Highest Recontact Rate")
        rc_top = rc_by_cr.nlargest(10, "Recontact_Rate")
        st.dataframe(
            rc_top[["CR Lv4", "Recontact_Rate", "Recontact_Volume", "Contacts", "Status"]],
            hide_index=True,
            use_container_width=True,
        )

    st.info(
        "**Key finding:** CSAT is below goal (79.95% vs 85%) while QA score exceeds goal. "
        "This gap suggests quality audits may not fully capture drivers of customer dissatisfaction — "
        "see Combined Insights for CRs where all three metrics underperform."
    )

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: QA ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "QA Analysis":
    st.subheader("Quality Assurance Analysis")

    tab1, tab2, tab3 = st.tabs(["By Channel", "Attribute Defects", "By Contact Reason"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            if len(qa_by_channel):
                for _, row in qa_by_channel.iterrows():
                    kpi_card(
                        f"QA — {row['Channel']}",
                        row["QA_Score"],
                        QA_GOAL,
                        row["Status"],
                        "score",
                    )
        with c2:
            if len(qa_detail_f):
                fig = px.histogram(
                    qa_detail_f,
                    x="QA_Score",
                    color="Channel",
                    nbins=20,
                    barmode="overlay",
                    opacity=0.75,
                )
                fig.add_vline(x=QA_GOAL, line_dash="dash", line_color="green")
                st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

    with tab2:
        st.markdown("#### Defect Concentration by QA Attribute")
        st.caption("Identifies which attributes drive the greatest impact on QA score")

        attr_filtered = qa_attrs.copy()
        if sel_channel != "All":
            attr_filtered = attr_filtered[attr_filtered["Channel"] == sel_channel]

        c1, c2 = st.columns(2)
        for channel in attr_filtered["Channel"].unique():
            subset = attr_filtered[attr_filtered["Channel"] == channel].head(8)
            with c1 if channel == "Phone" else c2:
                st.markdown(f"**{channel}** — Top Failing Attributes")
                fig = px.bar(
                    subset.sort_values("Fail_Rate_Pct"),
                    x="Fail_Rate_Pct",
                    y="Attribute",
                    orientation="h",
                    color="Is_Critical",
                    color_discrete_map={True: STATUS_COLORS["red"], False: DIDI_ORANGE},
                    text="Fail_Rate_Pct",
                )
                fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                fig.update_layout(showlegend=True, height=400)
                st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

        st.markdown("#### Full Attribute Fail Table")
        st.dataframe(
            attr_filtered.sort_values("Fail_Rate_Pct", ascending=False),
            hide_index=True,
            use_container_width=True,
        )

    with tab3:
        st.markdown("#### QA Performance by Contact Reason (CR Lv4)")
        cr_data = qa_by_cr.copy()
        if sel_channel != "All":
            cr_data = cr_data[cr_data["Channel"] == sel_channel]
        cr_data = cr_data.sort_values("QA_Score")

        fig = px.bar(
            cr_data.head(20),
            x="QA_Score",
            y="CR_Lv4",
            orientation="h",
            color="Status",
            color_discrete_map=STATUS_COLORS,
            hover_data=["Audits", "Critical_Fails"],
        )
        fig.add_vline(x=QA_GOAL, line_dash="dash", line_color="green")
        fig.update_layout(height=600, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

        st.dataframe(
            cr_data[["CR_Lv4", "Channel", "QA_Score", "Audits", "Critical_Fails", "Status", "Gap_vs_Goal"]],
            hide_index=True,
            use_container_width=True,
        )

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: CSAT / VOC
# ═══════════════════════════════════════════════════════════════════════════
elif page == "CSAT / VOC":
    st.subheader("Customer Satisfaction & Voice of Customer")

    if len(csat_by_channel):
        overall_csat = (
            csat_by_channel["Satisfied_CNT"].sum()
            / csat_by_channel["Feedback_CNT"].sum()
            * 100
        )
        status = "green" if overall_csat >= CSAT_GOAL else ("amber" if overall_csat >= CSAT_GOAL - 5 else "red")
        kpi_card("Overall CSAT", overall_csat, CSAT_GOAL, status, "%")

    tab1, tab2, tab3 = st.tabs(["By Dimension", "By CR Lv4", "Voice of Customer"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**CSAT by Channel**")
            if len(csat_by_channel):
                fig = px.bar(
                    csat_by_channel, x="Channel", y="CSAT_Pct",
                    color="Status", color_discrete_map=STATUS_COLORS, text="CSAT_Pct",
                )
                fig.add_hline(y=CSAT_GOAL, line_dash="dash", line_color="green")
                fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

        with c2:
            st.markdown("**CSAT by Business Type**")
            if len(csat_by_bt):
                fig = px.bar(
                    csat_by_bt, x="Business Type Name", y="CSAT_Pct",
                    color="Status", color_discrete_map=STATUS_COLORS, text="CSAT_Pct",
                )
                fig.add_hline(y=CSAT_GOAL, line_dash="dash", line_color="green")
                fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

    with tab2:
        st.markdown("#### CSAT by Contact Reason — Bottom 20")
        csat_cr_sorted = csat_by_cr.sort_values("CSAT_Pct")
        fig = px.bar(
            csat_cr_sorted.head(20),
            x="CSAT_Pct",
            y="CR Lv4",
            orientation="h",
            color="Status",
            color_discrete_map=STATUS_COLORS,
            hover_data=["Feedback_CNT"],
        )
        fig.add_vline(x=CSAT_GOAL, line_dash="dash", line_color="green")
        fig.update_layout(height=600, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

    with tab3:
        st.markdown("#### Voice of Customer — Dissatisfaction Comments")
        st.caption("Sample of open-text feedback from unsatisfied customers")

        voc_display = voc.copy()
        if sel_cr != "All":
            voc_display = voc_display[voc_display["CR Lv4"] == sel_cr]

        for _, row in voc_display.head(15).iterrows():
            st.markdown(
                f"""
                <div style="
                    border-left: 3px solid {DIDI_ORANGE};
                    padding: 10px 16px; margin-bottom: 10px;
                    background: #fafafa; border-radius: 0 8px 8px 0;
                ">
                    <div style="font-size: 12px; color: #888;">
                        {row.get('CR Lv4', 'N/A')} · {row.get('Channel', '')} · {row.get('Country Code', '')}
                    </div>
                    <div style="font-size: 14px; margin-top: 4px;">"{row.get('open_question', '')}"</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: RECONTACT
# ═══════════════════════════════════════════════════════════════════════════
elif page == "Recontact":
    st.subheader("Recontact Analysis — First Contact Resolution")

    if len(kpi):
        row = kpi[kpi["Metric"] == "Recontact Rate"].iloc[0]
        kpi_card("Overall Recontact Rate", row["Value"], row["Goal"], row["Status"], "%")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Recontact Rate by Channel")
        if len(rc_by_channel):
            fig = px.bar(
                rc_by_channel,
                x=rc_by_channel.columns[0],
                y="Recontact_Rate",
                color="Status",
                color_discrete_map=STATUS_COLORS,
                text="Recontact_Rate",
            )
            fig.add_hline(y=RECONTACT_GOAL, line_dash="dash", line_color="green",
                          annotation_text=f"Goal: {RECONTACT_GOAL}%")
            fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
            st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

    with c2:
        st.markdown("#### Volume: Contacts vs Recontacts (Top 10 CRs)")
        rc_top = rc_by_cr.nlargest(10, "Recontact_Volume")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Contacts", x=rc_top["CR Lv4"], y=rc_top["Contacts"],
            marker_color=DIDI_DARK,
        ))
        fig.add_trace(go.Bar(
            name="Recontacts", x=rc_top["CR Lv4"], y=rc_top["Recontact_Volume"],
            marker_color=DIDI_ORANGE,
        ))
        fig.update_layout(barmode="group", xaxis_tickangle=-45, height=400)
        st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

    st.markdown("#### All Contact Reasons — Recontact Rate")
    rc_sorted = rc_by_cr.sort_values("Recontact_Rate", ascending=False)
    fig = px.scatter(
        rc_sorted,
        x="Contacts",
        y="Recontact_Rate",
        size="Recontact_Volume",
        color="Status",
        color_discrete_map=STATUS_COLORS,
        hover_name="CR Lv4",
        size_max=40,
    )
    fig.add_hline(y=RECONTACT_GOAL, line_dash="dash", line_color="green")
    fig.update_layout(height=500)
    st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

    st.dataframe(
        rc_sorted[["CR Lv4", "Recontact_Rate", "Recontact_Volume", "Contacts", "Status", "Gap_vs_Goal"]],
        hide_index=True,
        use_container_width=True,
    )

# ═══════════════════════════════════════════════════════════════════════════
# PAGE: COMBINED INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "Combined Insights":
    st.subheader("Cross-Metric Analysis")
    st.caption("Contact reasons where QA, CSAT, and Recontact signals converge")

    high_risk = combined[combined["Risk_Flags"] >= 2].sort_values("Risk_Flags", ascending=False)

    st.markdown(f"#### 🔴 High-Risk CRs — {len(high_risk)} contact reasons flagged on 2+ metrics")

    if len(high_risk):
        for _, row in high_risk.head(8).iterrows():
            qa_val = f"{row['QA_Score']:.1f}" if pd.notna(row.get("QA_Score")) else "N/A"
            csat_val = f"{row['CSAT_Pct']:.1f}%" if pd.notna(row.get("CSAT_Pct")) else "N/A"
            rc_val = f"{row['Recontact_Rate']:.2f}%" if pd.notna(row.get("Recontact_Rate")) else "N/A"

            st.markdown(
                f"""
                <div style="
                    border: 1px solid #eee; border-radius: 10px;
                    padding: 16px 20px; margin-bottom: 12px;
                    border-left: 5px solid {DIDI_ORANGE};
                ">
                    <div style="font-weight: 700; font-size: 16px; color: {DIDI_DARK};">
                        {row.get('CR_Lv4_Name', 'Unknown CR')}
                    </div>
                    <div style="display: flex; gap: 24px; margin-top: 10px; font-size: 14px;">
                        <span>{status_emoji(row.get('QA_Status','na'))} QA: <b>{qa_val}</b></span>
                        <span>{status_emoji(row.get('CSAT_Status','na'))} CSAT: <b>{csat_val}</b></span>
                        <span>{status_emoji(row.get('RC_Status','na'))} Recontact: <b>{rc_val}</b></span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    st.markdown("#### Correlation Matrix — QA vs CSAT vs Recontact (by CR Lv4)")
    corr_data = combined.dropna(subset=["QA_Score", "CSAT_Pct", "Recontact_Rate"])
    if len(corr_data) > 5:
        corr = corr_data[["QA_Score", "CSAT_Pct", "Recontact_Rate"]].corr()
        fig = px.imshow(
            corr,
            text_auto=".2f",
            color_continuous_scale=[[0, DIDI_DARK], [0.5, DIDI_WHITE], [1, DIDI_ORANGE]],
            zmin=-1,
            zmax=1,
        )
        st.plotly_chart(apply_plotly_theme(fig), use_container_width=True)

        st.markdown(
            f"""
            **Interpretation:** QA Score and CSAT show a correlation of
            **{corr.loc['QA_Score', 'CSAT_Pct']:.2f}** —
            {"confirming that audit quality aligns with customer satisfaction."
             if corr.loc['QA_Score', 'CSAT_Pct'] > 0.3
             else "suggesting a disconnect between audit scores and customer perception."}
            Recontact Rate vs CSAT: **{corr.loc['CSAT_Pct', 'Recontact_Rate']:.2f}**.
            """
        )

    st.markdown("#### Full Combined Analysis Table")
    st.dataframe(
        combined.sort_values("Risk_Flags", ascending=False),
        hide_index=True,
        use_container_width=True,
    )

# ── Footer ─────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "DiDi CX Quality Analyst Business Case · Confidential · "
    f"QA Audits: {meta.get('total_qa_audits', '—'):,} · "
    f"CSAT Responses: {meta.get('total_csat_feedback', '—'):,} · "
    f"Contacts: {meta.get('total_contacts', '—'):,}"
)
