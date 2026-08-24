from pathlib import Path
import re

js = Path("dashboard_v2/frontend/assets/app.js").read_text(encoding="utf-8")
html = Path("dashboard_v2/frontend/index.html").read_text(encoding="utf-8")
css = Path("dashboard_v2/frontend/assets/app.css").read_text(encoding="utf-8")
print("JS_LEN", len(js), "HTML_LEN", len(html), "CSS_LEN", len(css))
ids = re.findall(r"getElementById\(['\"]([^'\"]+)", js)
print("JS_IDS", ids)
html_ids = re.findall(r'id="([^"]+)"', html)
print("HTML_IDS", html_ids)
for pat in ["k.", "g.", "o.", "data.", "state.", "m.", "ag.", "q.", "c.", "r.", "a."]:
    hits = sorted(set(re.findall(re.escape(pat) + r"([A-Za-z0-9_]+)", js)))
    print(pat, hits)
print("--- HTML cache ---")
for line in html.splitlines():
    if "app.css" in line or "app.js" in line:
        print(line)
print("--- JS field samples ---")
for needle in [
    "qa_n",
    "csat_n",
    "recontact_n",
    "slice_note",
    "by_channel",
    "QA_Score",
    "CSAT_Score",
    "QA_N",
    "Error_Category",
    "Fail_Count",
    "CR_Lv4",
    "Recontact_Rate",
    "qa_by_lob",
    "csat_by_biz",
    "bottom10_avg",
    "thin_n",
    "business_types",
    "as_of",
]:
    print(needle, js.count(needle), [hex(ord(c)) for c in needle])
