from pathlib import Path
p = Path("dashboard_v2/frontend/assets/app.js")
t = p.read_text(encoding="utf-8")
for i, line in enumerate(t.splitlines(), 1):
    if any(s in line for s in [
        "function titles", "function badge", "function renderOverview",
        "qa_by_lob", "csat_by_biz", "Volume", "Within", "Watch",
        "function renderQa", "function renderCsat", "function renderRecontact",
        "function renderAlerts", "function renderQuality", "function renderDefinitions",
        "SUPPORT", "download", "lob-chart", "cs-ch", "[1, 1]", "go-agents",
        "state.cr", "cr_lv1", "methodology", "Download",
    ]):
        print(f"{i:4d}|{line}")
