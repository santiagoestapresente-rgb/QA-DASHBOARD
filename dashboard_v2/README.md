# DiDi CX Dashboard v2.0

Separate from the Streamlit v1 app (`app.py`). Official QA / CSAT / recontact
formulas stay in `modules/kpis.py` — this folder only serves them over HTTP
and renders a native browser UI so filters can animate without a full rerun.

## Run locally

From the **repo root**:

```bat
C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe -m pip install -r dashboard_v2\backend\requirements.txt
C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe -m uvicorn dashboard_v2.backend.main:app --reload --port 8000
```

Open http://127.0.0.1:8000

## What is in this first slice

- Overview KPIs (QA, CSAT, recontact, volumes) from the same packaged snapshot
- Channel filter: All / Phone / Live Chat — numbers count up in the browser
- Channel comparison chart via Plotly.js (`Plotly.react`, no page reload)
- Control totals on Market=All must stay QA **94.14** · CSAT **79.95** · RC **5.83**

## What is not migrated yet

QA detail, CSAT VOC, Recontact Paretos, Performance Hub, dialogs, and the rest
of the Streamlit pages. Add them as more `/api/...` endpoints plus frontend
views, still calling `modules/kpis.py`.

The live Streamlit Cloud app remains v1 until you choose to replace it.
