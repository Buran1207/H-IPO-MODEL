from __future__ import annotations

from pathlib import Path
import pandas as pd

from sampling_180d import build_price_180d_sample

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "local_exports"
DEPLOY = ROOT / "deploy_data"


def copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        df = pd.read_csv(src, encoding="utf-8-sig")
        df.to_csv(dst, index=False, encoding="utf-8-sig")
        print(f"Saved {dst} from {src}")
    else:
        print(f"Skip missing {src}")


def main() -> None:
    DEPLOY.mkdir(exist_ok=True)
    copy_if_exists(LOCAL / "ipo_projects.csv", DEPLOY / "ipo_projects.csv")
    copy_if_exists(LOCAL / "ipo_docs.csv", DEPLOY / "ipo_docs.csv")
    copy_if_exists(LOCAL / "hk_ipo_scored_public.csv", DEPLOY / "hk_ipo_scored_public.csv")
    raw_price = LOCAL / "price_daily_raw.csv"
    if raw_price.exists():
        build_price_180d_sample(raw_price, DEPLOY / "price_180d_sample.csv")
    else:
        print("Skip price_180d_sample: local_exports/price_daily_raw.csv not found")


if __name__ == "__main__":
    main()
