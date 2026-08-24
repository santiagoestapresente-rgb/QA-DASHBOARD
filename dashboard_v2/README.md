# DiDi CX Dashboard v2.0

Completely separate from Streamlit v1 (`app.py`). Do not run this folder
through Streamlit Cloud. Official QA / CSAT / recontact formulas stay in
`modules/kpis.py` — this app only **reads** them over HTTP and paints a native
browser UI so filters animate without a full page rewrite.

v1 on Streamlit Cloud is unchanged. Building v2 does not edit `app.py`,
`.streamlit/config.toml`, or root `requirements.txt`.

## Run locally

From the **repo root**. First time only, install v2 packages (once):

```bat
C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe -m pip install -r dashboard_v2\backend\requirements.txt
```

Then start the app:

```bat
dashboard_v2\run.bat
```

Open http://127.0.0.1:8000

Or:

```bat
C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe -m uvicorn dashboard_v2.backend.main:app --reload --port 8000
```

Open http://127.0.0.1:8000

## What is in this build

- Pages: Overview, QA Score, CSAT, Recontact, Alerts
- Live filters: Channel, Market, Week — numbers count up, charts `Plotly.react`
- Same packaged snapshot and the same `apply_filters` cuts as v1
- Control totals on Market=All / all weeks: QA **94.14** · CSAT **79.95** · RC **5.83**

## What is still thinner than v1

Advanced Streamlit-only filters (agent click-to-filter, label editor, ticket
tracker, some Performance Hub dialogs) are not cloned yet. Add them as more
query params on `/api/dashboard` without touching v1.
