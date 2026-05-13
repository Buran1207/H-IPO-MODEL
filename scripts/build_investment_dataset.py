from __future__ import annotations

# This script is intentionally lightweight. The Streamlit app recalculates dynamic
# lock-up status and custom scores at runtime. For a full refresh, update the
# source CSVs under deploy_data/ and rerun the free quote/path scripts, then
# redeploy the repository.

from pathlib import Path
import pandas as pd

BASE = Path("deploy_data")

def read_csv(path):
    for enc in ("utf-8-sig", "utf-8", "gb18030", "big5"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            pass
    return pd.read_csv(path)

def main():
    src = BASE / "ipo_investment_decision_scored.csv"
    if not src.exists():
        pool = BASE / "ipo_decision_pool.csv"
        if not pool.exists():
            raise SystemExit("Missing deploy_data/ipo_decision_pool.csv")
        df = read_csv(pool)
        df.to_csv(src, index=False, encoding="utf-8-sig")
    print(f"Ready: {src}")

if __name__ == "__main__":
    main()
