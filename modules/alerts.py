"""Ops desk: ranked queues, tickets, and email drafts from official KPIs.

No SMTP and no addresses in the Excel — tickets stay in the session and
the email is a draft the manager can send from Outlook.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

import pandas as pd

from config import CSAT_GOAL, QA_GOAL, RECONTACT_GOAL
from modules.kpis import _vs_goal_status

WATCH_DESK_ORDER = ("QA", "CSAT", "Recontact")


def _clip(name: object, n: int = 42) -> str:
    text = " ".join(str(name).split())
    return text[:n] + ("…" if len(text) > n else "")


def _fmt(v, digits: int = 1) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return f"{float(v):.{digits}f}"


@dataclass
class Ticket:
    id: str
    desk: str
    title: str
    owner: str
    follow_up: str
    due: str
    status: str
    volume: str
    email_to: str
    email_body: str
    snippet: list[str] = field(default_factory=list)


def qa_coaching_queue(agents_gap: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    """Supervisors to notify: their agents below QA 85, ranked by audit gap."""
    if agents_gap is None or agents_gap.empty or "Supervisor_ID" not in agents_gap.columns:
        return pd.DataFrame()
    g = (
        agents_gap.groupby("Supervisor_ID", as_index=False)
        .agg(
            Agents=("Agent_ID", "nunique"),
            Audits=("n", "sum") if "n" in agents_gap.columns else ("Agent_ID", "count"),
            Worst_QA=("QA_Score", "min"),
            Gap_Impact=("Gap_Impact", "sum"),
        )
        .sort_values("Gap_Impact", ascending=False)
        .head(top_n)
    )
    g["Worst_QA"] = g["Worst_QA"].round(1)
    g["Gap_Impact"] = g["Gap_Impact"].round(0)
    return g


def agents_for_supervisor(agents_gap: pd.DataFrame, supervisor: str) -> pd.DataFrame:
    if agents_gap is None or agents_gap.empty:
        return pd.DataFrame()
    if "Supervisor_ID" not in agents_gap.columns:
        return pd.DataFrame()
    sub = agents_gap[agents_gap["Supervisor_ID"].astype(str) == str(supervisor)].copy()
    agent_col = "Agent_ID" if "Agent_ID" in sub.columns else ("Agent" if "Agent" in sub.columns else None)
    sort_col = "QA_Score" if "QA_Score" in sub.columns else (agent_col or sub.columns[0])
    cols = [c for c in (
        "Agent_ID", "Agent", "QA_Score", "CSAT_Score", "n", "QA_n", "CSAT_n",
        "Tenure_Cohort", "Gap_Impact", "Ranking_Index", "Quartile", "AHT_min",
        "Sample_OK", "QA_below", "CSAT_below",
    ) if c in sub.columns]
    if not cols:
        return sub
    return sub[cols].sort_values(sort_col)


def _as_bool(value) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    return bool(value)


def _score_num(value) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _pts_below(score: float | None, goal: float) -> str | None:
    if score is None:
        return None
    gap = float(goal) - float(score)
    if gap <= 0:
        return None
    if abs(gap - round(gap)) < 0.05:
        return f"{round(gap):.0f} pts below goal"
    return f"{gap:.1f} pts below goal"


def people_watchlist(
    qa_mix: pd.DataFrame,
    csat_mix: pd.DataFrame | None = None,
    qa_agents: pd.DataFrame | None = None,
    csat_agents: pd.DataFrame | None = None,
    *,
    q4_only: bool = False,
    q4_share_alert: float = 40.0,
) -> pd.DataFrame:
    """Coaching queue: one English sentence per row. Talent mix ≠ official KPI.

    Recontact is not on this table — it has no agent or supervisor field.
    """
    rows = []

    def _score_txt(value) -> str:
        if value is None:
            return "—"
        try:
            if pd.isna(value):
                return "—"
            return f"{float(value):.1f}"
        except (TypeError, ValueError):
            return "—"

    sup = qa_mix.copy() if qa_mix is not None and not qa_mix.empty else pd.DataFrame()
    if not sup.empty:
        if q4_only:
            review = sup["Requires_Review"].astype(bool) if "Requires_Review" in sup.columns else False
            q4_flag = sup["Talent_Quartile"].astype(str).eq("Q4") if "Talent_Quartile" in sup.columns else False
            sup = sup[review | q4_flag]
        for _, row in sup.head(8).iterrows():
            n_q4 = int(row.get("Q4_Agents") or 0)
            n_ranked = int(row.get("Ranked_Agents") or 0)
            owner = str(row.get("Supervisor_ID") or "")
            qa_txt = _score_txt(row.get("QA_Score"))
            score = _score_num(row.get("QA_Score"))
            below = bool(score is not None and score < QA_GOAL)
            pts = _pts_below(score, QA_GOAL)
            mix = f"{n_q4} of {n_ranked} ranked agents in the bottom 25% of this filter"
            why = f"{pts} · {mix}" if pts else f"team mean on goal · {mix}"
            issue = f"{owner} — QA {qa_txt}% ({why})"
            rows.append({
                "Desk": "QA",
                "Issue": issue,
                "Owner": owner,
                "Volume": n_q4,
                "Score": row.get("QA_Score"),
                "Sample_N": int(row.get("n") or 0),
                "Ranked_N": n_ranked,
                "Q4_N": n_q4,
                "Below_Goal": below,
                "Kind": "supervisor",
                "Follow-up": "Leadership audit / coaching",
                "Focus_Kind": "supervisor",
                "Focus_Key": owner,
                "Supervisor_ID": owner,
                "Requires_Review": _as_bool(row.get("Requires_Review")),
            })

    cs_mix = csat_mix.copy() if csat_mix is not None and not csat_mix.empty else pd.DataFrame()
    if not cs_mix.empty:
        if q4_only:
            review = cs_mix["Requires_Review"].astype(bool) if "Requires_Review" in cs_mix.columns else False
            q4_flag = cs_mix["Talent_Quartile"].astype(str).eq("Q4") if "Talent_Quartile" in cs_mix.columns else False
            cs_mix = cs_mix[review | q4_flag]
        seen = {r["Owner"] for r in rows}
        for _, row in cs_mix.head(6).iterrows():
            owner = str(row.get("Supervisor_ID") or "")
            if owner in seen:
                continue
            n_q4 = int(row.get("Q4_Agents") or 0)
            share = row.get("Q4_Share")
            try:
                share_n = 0.0 if share is None or pd.isna(share) else float(share)
            except (TypeError, ValueError):
                share_n = 0.0
            if n_q4 <= 0 and share_n < float(q4_share_alert):
                continue
            n_ranked = int(row.get("Ranked_Agents") or 0)
            cs_txt = _score_txt(row.get("CSAT_Score"))
            score = _score_num(row.get("CSAT_Score"))
            below = bool(score is not None and score < CSAT_GOAL)
            pts = _pts_below(score, CSAT_GOAL)
            mix = f"{n_q4} of {n_ranked} ranked agents in the bottom 25% of this filter"
            why = f"{pts} · {mix}" if pts else f"team mean on goal · {mix}"
            issue = f"{owner} — CSAT {cs_txt}% ({why})"
            rows.append({
                "Desk": "CSAT",
                "Issue": issue,
                "Owner": owner,
                "Volume": n_q4,
                "Score": row.get("CSAT_Score"),
                "Sample_N": int(row.get("Feedback") or 0),
                "Ranked_N": n_ranked,
                "Q4_N": n_q4,
                "Below_Goal": below,
                "Kind": "supervisor",
                "Follow-up": "First-contact script coaching",
                "Focus_Kind": "supervisor",
                "Focus_Key": owner,
                "Supervisor_ID": owner,
                "Requires_Review": _as_bool(row.get("Requires_Review")),
            })

    def _agent_rows(frame: pd.DataFrame, desk: str, score_col: str, n_col: str) -> None:
        if frame is None or frame.empty or "Quartile" not in frame.columns:
            return
        work = frame.copy()
        work["Quartile"] = work["Quartile"].astype(str)
        work = work[work["Quartile"].eq("Q4")]
        if work.empty:
            return
        goal = QA_GOAL if desk == "QA" else CSAT_GOAL
        sort_col = score_col if score_col in work.columns else work.columns[0]
        work = work.sort_values(sort_col, ascending=True)
        for _, row in work.head(8).iterrows():
            agent = str(row.get("Agent_ID") or row.get("Agent") or "")
            if not agent:
                continue
            score_txt = _score_txt(row.get(score_col))
            score = _score_num(row.get(score_col))
            below = bool(score is not None and score < goal)
            pts = _pts_below(score, goal)
            why = f"{pts} · bottom 25% of this filter" if pts else "above goal, but bottom 25% of this filter"
            sup = str(row.get("Supervisor_ID") or "")
            issue = (
                f"{agent} — {desk} {score_txt}% ({why.split(' · ')[0]}) · "
                f"{sup or 'no supervisor'}"
            )
            rows.append({
                "Desk": desk,
                "Issue": issue,
                "Owner": agent,
                "Volume": int(row.get(n_col) or 0),
                "Score": row.get(score_col),
                "Sample_N": int(row.get(n_col) or 0),
                "Below_Goal": below,
                "Kind": "agent",
                "Follow-up": "Coaching session",
                "Focus_Kind": "agent",
                "Focus_Key": agent,
                "Supervisor_ID": sup,
                "Requires_Review": False,
            })

    _agent_rows(qa_agents, "QA", "QA_Score", "QA_n")
    _agent_rows(csat_agents, "CSAT", "CSAT_Score", "CSAT_n")

    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    order = {desk: i for i, desk in enumerate(WATCH_DESK_ORDER)}
    out["_desk_ord"] = out["Desk"].map(order).fillna(99)
    return (
        out.sort_values(["_desk_ord", "Volume"], ascending=[True, False])
        .drop(columns=["_desk_ord"])
        .reset_index(drop=True)
    )


def recontact_ops_table(rc_cr: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Contact-reason recontact alerts. Not people — recontact has no agent/supervisor."""
    if rc_cr is None or rc_cr.empty:
        return pd.DataFrame()
    src = rc_cr.copy()
    rate = pd.to_numeric(src.get("Recontact_Rate"), errors="coerce")
    src = src[rate.notna() & (rate > RECONTACT_GOAL)]
    if src.empty:
        src = rc_cr.head(top_n).copy()
    else:
        src = src.sort_values("Recontact_Rate", ascending=False).head(top_n)
    vol_col = "Recontacts" if "Recontacts" in src.columns else None
    rows = []
    for _, row in src.iterrows():
        rows.append({
            "Contact reason Lv4 (detail)": " ".join(str(row.get("CR_Lv4", "")).split()),
            "Repeats": int(row[vol_col]) if vol_col and pd.notna(row.get(vol_col)) else 0,
            "Rate %": row.get("Recontact_Rate"),
            "vs 5.44": (
                float(row["Recontact_Rate"]) - RECONTACT_GOAL
                if pd.notna(row.get("Recontact_Rate")) else None
            ),
        })
    return pd.DataFrame(rows)


def csat_volume_queue(csat_unsat: pd.DataFrame, voc: pd.DataFrame, top_n: int = 6) -> pd.DataFrame:
    """Unsatisfied survey volume by contact reason Lv4, plus the leading 1–3 star theme."""
    rows = []
    if csat_unsat is not None and not csat_unsat.empty:
        src = csat_unsat.head(top_n)
        for _, row in src.iterrows():
            rows.append({
                "Desk": "CSAT",
                "Item": str(row.get("CR_Lv4", "")),
                "Grain": "Contact reason Lv4 (detail)",
                "Volume": int(row.get("Unsatisfied", 0) or 0),
                "Score": row.get("CSAT_Score"),
                "Owner": "CX Operations",
                "Follow_up": "Review 1–3 star comments and the first-contact script",
            })
    if voc is not None and not voc.empty:
        top = voc.iloc[0]
        rows.append({
            "Desk": "CSAT",
            "Item": str(top.get("Theme", "")),
            "Grain": "1–3 star comment theme",
            "Volume": int(top["Mentions"] if "Mentions" in voc.columns else 0),
            "Score": None,
            "Owner": "CX Operations",
            "Follow_up": "Sample comments and map them to a contact reason Lv4 (detail)",
        })
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("Volume", ascending=False)


def recontact_volume_queue(rc_cr: pd.DataFrame, top_n: int = 6) -> pd.DataFrame:
    if rc_cr is None or rc_cr.empty:
        return pd.DataFrame()
    src = rc_cr.head(top_n).copy()
    vol_col = "Recontacts" if "Recontacts" in src.columns else None
    rows = []
    for _, row in src.iterrows():
        rows.append({
            "Desk": "Recontact",
            "Item": str(row.get("CR_Lv4", "")),
            "Grain": "Contact reason Lv4 (detail)",
            "Volume": int(row[vol_col]) if vol_col else 0,
            "Score": row.get("Recontact_Rate"),
            "Owner": "Operations lead",
            "Follow_up": "Fix the first-contact path for this contact reason Lv4 (detail)",
        })
    return pd.DataFrame(rows)


def _watch_light(desk: str, score) -> str | None:
    if score is None or (isinstance(score, float) and pd.isna(score)):
        return None
    try:
        value = float(score)
    except (TypeError, ValueError):
        return None
    if desk == "Recontact":
        return _vs_goal_status(value, RECONTACT_GOAL, False)
    if desk == "CSAT":
        return _vs_goal_status(value, CSAT_GOAL, True)
    return _vs_goal_status(value, QA_GOAL, True)


def watchlist_table(
    qa_queue: pd.DataFrame,
    csat_q: pd.DataFrame,
    rc_q: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for _, row in (qa_queue.head(5) if qa_queue is not None and not qa_queue.empty else pd.DataFrame()).iterrows():
        score = row.get("Worst_QA")
        rows.append({
            "Desk": "QA",
            "Issue": f"{int(row['Agents'])} agents below QA 85",
            "Owner": str(row["Supervisor_ID"]),
            "Volume": int(row["Audits"]),
            "Score": score,
            "Light": _watch_light("QA", score),
            "Follow-up": "Coaching session",
            "Focus_Kind": "supervisor",
            "Focus_Key": str(row["Supervisor_ID"]),
        })
    if csat_q is not None and not csat_q.empty:
        for _, top in csat_q.head(4).iterrows():
            grain = str(top.get("Grain") or "")
            item = " ".join(str(top["Item"]).split())
            lv4 = "Lv4" in grain
            score = top.get("Score")
            rows.append({
                "Desk": "CSAT",
                "Issue": f"{grain}: {item}",
                "Owner": str(top["Owner"]),
                "Volume": int(top["Volume"]),
                "Score": score,
                "Light": _watch_light("CSAT", score),
                "Follow-up": str(top["Follow_up"]),
                "Focus_Kind": "cr_lv4" if lv4 else "theme",
                "Focus_Key": str(top["Item"]),
            })
    if rc_q is not None and not rc_q.empty:
        for _, top in rc_q.head(3).iterrows():
            item = " ".join(str(top["Item"]).split())
            score = top.get("Score")
            rows.append({
                "Desk": "Recontact",
                "Issue": f"Contact reason Lv4 (detail): {item}",
                "Owner": str(top["Owner"]),
                "Volume": int(top["Volume"]),
                "Score": score,
                "Light": _watch_light("Recontact", score),
                "Follow-up": str(top["Follow_up"]),
                "Focus_Kind": "cr_lv4",
                "Focus_Key": str(top["Item"]),
            })
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    order = {desk: i for i, desk in enumerate(WATCH_DESK_ORDER)}
    out["_desk_ord"] = out["Desk"].map(order).fillna(99)
    return (
        out.sort_values(["_desk_ord", "Volume"], ascending=[True, False])
        .drop(columns=["_desk_ord"])
        .reset_index(drop=True)
    )


def watch_pipeline_status(row: pd.Series, tickets: list) -> str:
    """active = no ticket yet; progress = open ticket; closed = ticket closed."""
    key = str(row.get("Focus_Key") or "").strip().casefold()
    desk = str(row.get("Desk") or "").strip().casefold()
    if not key:
        return "active"
    hits = []
    for ticket in tickets or []:
        if str(getattr(ticket, "desk", "")).strip().casefold() != desk:
            continue
        blob = f"{getattr(ticket, 'owner', '')} {getattr(ticket, 'title', '')}".casefold()
        if key in blob:
            hits.append(ticket)
    if not hits:
        return "active"
    if all(str(getattr(t, "status", "")) == "Closed" for t in hits):
        return "closed"
    return "progress"


def annotate_watch_pipeline(watch: pd.DataFrame, tickets: list) -> pd.DataFrame:
    if watch is None or watch.empty:
        return watch if watch is not None else pd.DataFrame()
    out = watch.copy()
    out["Pipeline"] = [watch_pipeline_status(row, tickets) for _, row in out.iterrows()]
    return out


def supervisors_for_cr_lv4(
    audits: pd.DataFrame,
    csat: pd.DataFrame,
    cr_lv4: str,
) -> list[str]:
    """QA supervisors whose agents appear on this contact reason Lv4 (detail)."""
    key = str(cr_lv4 or "").strip().casefold()
    if not key:
        return []
    found: set[str] = set()
    if audits is not None and not audits.empty and "CR_Lv4" in audits.columns and "Supervisor_ID" in audits.columns:
        hit = audits["CR_Lv4"].astype(str).str.strip().str.casefold().eq(key)
        found.update(audits.loc[hit, "Supervisor_ID"].astype(str))
    if csat is not None and not csat.empty and "CR_Lv4" in csat.columns and "Agent name" in csat.columns:
        from modules.kpis import _agent_supervisor_map
        amap = _agent_supervisor_map(audits)
        hit = csat["CR_Lv4"].astype(str).str.strip().str.casefold().eq(key)
        names = csat.loc[hit, "Agent name"].astype(str).str.strip().str.casefold()
        found.update(str(amap[n]) for n in names if n in amap)
    return sorted(found)


def email_draft(*, to_line: str, subject: str, body_lines: list[str]) -> str:
    return "\n".join(
        [
            f"To: {to_line}",
            f"Subject: {subject}",
            "",
            *body_lines,
            "",
            "Please confirm the coaching or process review date and close the ticket when done.",
            "",
            "— DiDi CX Quality desk",
        ]
    )


def make_qa_ticket(supervisor: str, queue_row: pd.Series, agents: pd.DataFrame, seq: int) -> Ticket:
    n = int(queue_row.get("Agents", 0) or 0)
    audits = int(queue_row.get("Audits", 0) or 0)
    worst = queue_row.get("Worst_QA")
    due = (date.today() + timedelta(days=7)).isoformat()
    lines = [
        f"{supervisor} has {n} agents below QA 85 on {audits:,} audits.",
        f"Lowest agent QA in this team: {_fmt(worst)}%.",
        "Required follow-up: one coaching session this week, then a re-audit sample.",
        "",
        "Agents below 85:",
    ]
    snippet = []
    if agents is not None and not agents.empty:
        for _, row in agents.head(12).iterrows():
            line = f"  {row['Agent_ID']}: QA {_fmt(row['QA_Score'])}% · {int(row.get('n', 0) or 0)} audits"
            if "Tenure_Cohort" in agents.columns:
                line += f" · {row['Tenure_Cohort']}"
            lines.append(line)
            snippet.append(line.strip())
    to_line = f"Operations manager / {supervisor}"
    subject = f"[CX QA] Coaching required — {supervisor} · {n} agents below 85"
    return Ticket(
        id=f"CX-{seq:03d}",
        desk="QA",
        title=f"Coach {n} agents under {supervisor}",
        owner=str(supervisor),
        follow_up="Coaching session + re-audit",
        due=due,
        status="Open",
        volume=f"{audits:,} audits",
        email_to=to_line,
        email_body=email_draft(to_line=to_line, subject=subject, body_lines=lines),
        snippet=snippet,
    )


def make_csat_ticket(supervisor: str, queue_row: pd.Series, agents: pd.DataFrame, seq: int) -> Ticket:
    n = int(queue_row.get("Agents", queue_row.get("Ranked_Agents", 0)) or 0)
    surveys = int(queue_row.get("Feedback", 0) or 0)
    csat = queue_row.get("CSAT_Score")
    due = (date.today() + timedelta(days=7)).isoformat()
    lines = [
        f"{supervisor} is below CSAT 85 on {surveys:,} surveys of mapped agents.",
        f"Team CSAT: {_fmt(csat)}%. Official CSAT is 4★+5★ / Feedback CNT (ratio of sums).",
        "Required follow-up: coaching on the first-contact script and a comment sample.",
        "",
        "Agents below CSAT 85 (20+ surveys):",
    ]
    snippet = []
    if agents is not None and not agents.empty:
        shown = agents
        if "CSAT_below" in shown.columns:
            shown = shown[shown["CSAT_below"].astype(bool)]
        for _, row in shown.head(12).iterrows():
            name = row.get("Agent_ID") or row.get("Agent")
            line = (
                f"  {name}: CSAT {_fmt(row.get('CSAT_Score'))}% · "
                f"{int(row.get('CSAT_n') or row.get('Feedback') or 0)} surveys"
            )
            lines.append(line)
            snippet.append(line.strip())
    to_line = f"Operations manager / {supervisor}"
    subject = f"[CX CSAT] Coaching required — {supervisor} · CSAT {_fmt(csat)}%"
    return Ticket(
        id=f"CX-{seq:03d}",
        desk="CSAT",
        title=f"CSAT coaching — {supervisor}",
        owner=str(supervisor),
        follow_up="Coaching session + comment sample",
        due=due,
        status="Open",
        volume=f"{surveys:,} surveys",
        email_to=to_line,
        email_body=email_draft(to_line=to_line, subject=subject, body_lines=lines),
        snippet=snippet,
    )


def make_agent_ticket(agent: str, row: pd.Series, seq: int) -> Ticket:
    qa = row.get("QA_Score")
    cs = row.get("CSAT_Score")
    sup = str(row.get("Supervisor_ID") or "supervisor")
    q = str(row.get("Quartile") or "")
    due = (date.today() + timedelta(days=7)).isoformat()
    lines = [
        f"{agent} ({q or 'unranked'}) reports to {sup}.",
        f"QA {_fmt(qa)}% on {int(row.get('QA_n') or row.get('n') or 0)} audits. "
        f"CSAT {_fmt(cs)}% on {int(row.get('CSAT_n') or 0)} surveys.",
        f"Ranking index {_fmt(row.get('Ranking_Index'))} "
        "(0.50 QA + 0.30 CSAT + 0.20 AHT percentile — not a contractual KPI).",
        "Required follow-up: one coaching session this week.",
    ]
    to_line = f"Operations manager / {sup}"
    subject = f"[CX QA] Coaching required — {agent} · {q or 'below goal'}"
    return Ticket(
        id=f"CX-{seq:03d}",
        desk="QA",
        title=f"Coach {agent}",
        owner=str(agent),
        follow_up="Coaching session",
        due=due,
        status="Open",
        volume=f"{int(row.get('QA_n') or row.get('n') or 0)} audits",
        email_to=to_line,
        email_body=email_draft(to_line=to_line, subject=subject, body_lines=lines),
        snippet=lines,
    )


def make_volume_ticket(row: pd.Series, seq: int) -> Ticket:
    desk = str(row["Desk"])
    item = str(row["Item"])
    grain = str(row["Grain"])
    owner = str(row["Owner"])
    follow = str(row["Follow_up"])
    vol = int(row["Volume"])
    due = (date.today() + timedelta(days=7)).isoformat()
    score = row.get("Score")
    score_txt = f" Score {_fmt(score, 2)}%." if score is not None and pd.notna(score) else ""
    lines = [
        f"{desk} queue: {grain} '{item}' is the highest-volume case in this filter ({vol:,}).{score_txt}",
        f"Required follow-up: {follow}.",
    ]
    to_line = owner
    subject = f"[CX {desk}] {_clip(item, 40)} · volume {vol:,}"
    return Ticket(
        id=f"CX-{seq:03d}",
        desk=desk,
        title=f"{desk}: {_clip(item, 36)}",
        owner=owner,
        follow_up=follow,
        due=due,
        status="Open",
        volume=f"{vol:,}",
        email_to=to_line,
        email_body=email_draft(to_line=to_line, subject=subject, body_lines=lines),
        snippet=lines,
    )
