from pathlib import Path
import re
t = Path("dashboard_v2/frontend/assets/app.js").read_text(encoding="utf-8")
print("funcs", re.findall(r"function ([A-Za-z0-9_]+)", t))
print("chRow", t.count("chRow"))
print("getIds", re.findall(r"getElementById\('([^']+)'\)|getElementById\(\"([^\"]+)\"\)", t))
html = Path("dashboard_v2/frontend/index.html").read_text(encoding="utf-8")
print("html view", "id=\"view\"" in html, "id='view'" in html)
print("js view str", '"view"' in t, "'view'" in t)
print("RENDER", re.findall(r"RENDER[\s\S]{0,400}", t)[:1])
