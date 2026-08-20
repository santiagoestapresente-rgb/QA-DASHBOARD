from pathlib import Path

import pandas as pd

MODEL = Path(__file__).resolve().parent.parent / "powerbi" / "DiDi_CX_PowerBI_Model.xlsx"

for sheet in ["dim_date", "fact_audit", "fact_csat", "fact_recontact"]:
    df = pd.read_excel(MODEL, sheet_name=sheet, nrows=3)
    print(f"--- {sheet} ({len(df.columns)} columnas) ---")
    for i, c in enumerate(df.columns, start=1):
        print(f"  {i:>2}. {c}")
    print()
