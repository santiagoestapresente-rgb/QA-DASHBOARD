import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from modules.data_loader import load_all_data

d = load_all_data()
c = d["fact_csat"]
print("user_tenure:\n", c["user_tenure"].value_counts(dropna=False).head(20).to_string())
print("nunique", c["user_tenure"].nunique())
print("sample", c["user_tenure"].dropna().head(8).tolist())
print("agent name nunique", c["Agent name"].nunique() if "Agent name" in c.columns else None)
