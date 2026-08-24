from pathlib import Path
js = Path("dashboard_v2/frontend/assets/app.js").read_text(encoding="utf-8")
lines = js.splitlines()
for start, end in [(110, 130), (250, 430), (416, 575)]:
    print(f"\n===== {start}-{end} =====")
    for i in range(start, min(end, len(lines))+1):
        print(f"{i:4d}|{lines[i-1]}")
