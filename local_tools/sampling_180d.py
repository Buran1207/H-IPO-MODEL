from __future__ import annotations

from pathlib import Path
import pandas as pd


def _clean_code(value) -> str:
    if pd.isna(value):
        return ""
    s = str(value).strip().upper()
    if s.endswith(".HK"):
        left = s[:-3]
        return f"{int(left):04d}.HK" if left.isdigit() else s
    if s.isdigit():
        return f"{int(s):04d}.HK"
    return s


def sample_180d_for_one_stock(price_df: pd.DataFrame, listing_date=None, max_trade_days: int = 180) -> pd.DataFrame:
    """Return dense-to-sparse 180 trading-day sample for one listed IPO.

    Input columns can be Chinese or English. Expected minimum columns:
    code, trade_date, open, high, low, close, volume, amount, turnover_rate, issue_price.

    Sampling rule:
    - D0-D10: every trading day
    - D11-D30: every 2nd trading day
    - D31-D60: every 5th trading day
    - D61-D180: every 10th trading day
    """
    aliases = {
        "证券代码": "code", "股票代码": "code", "代码": "code",
        "交易日期": "trade_date", "日期": "trade_date",
        "开盘价": "open", "最高价": "high", "最低价": "low", "收盘价": "close",
        "成交量": "volume", "成交额": "amount", "换手率": "turnover_rate", "发行价": "issue_price",
    }
    df = price_df.rename(columns={c: aliases.get(c, c) for c in price_df.columns}).copy()
    if "trade_date" not in df.columns:
        raise ValueError("price_df must contain trade_date / 日期")
    df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce")
    df = df.dropna(subset=["trade_date"]).sort_values("trade_date")
    if listing_date is not None:
        listing_date = pd.to_datetime(listing_date, errors="coerce")
        if pd.notna(listing_date):
            df = df[df["trade_date"] >= listing_date]
    df = df.head(max_trade_days).reset_index(drop=True)
    df["day_offset"] = df.index

    def keep(d: int) -> bool:
        if d <= 10:
            return True
        if d <= 30:
            return (d - 10) % 2 == 0
        if d <= 60:
            return (d - 30) % 5 == 0
        return (d - 60) % 10 == 0

    out = df[df["day_offset"].map(keep)].copy()

    def bucket(d: int) -> str:
        if d <= 10:
            return "D0-D10每日"
        if d <= 30:
            return "D11-D30隔日"
        if d <= 60:
            return "D31-D60每5日"
        return "D61-D180每10日"

    out["sample_bucket"] = out["day_offset"].map(bucket)
    if "code" in out.columns:
        out["code"] = out["code"].map(_clean_code)
    if {"close", "issue_price"}.issubset(out.columns):
        out["ret_from_ipo"] = pd.to_numeric(out["close"], errors="coerce") / pd.to_numeric(out["issue_price"], errors="coerce") - 1
    if "close" in out.columns:
        close = pd.to_numeric(out["close"], errors="coerce")
        out["drawdown_from_high"] = close / close.cummax() - 1
    return out


def build_price_180d_sample(raw_price_csv: str | Path, output_csv: str | Path) -> None:
    raw = pd.read_csv(raw_price_csv, encoding="utf-8-sig")
    raw = raw.rename(columns={"证券代码": "code", "股票代码": "code", "代码": "code"})
    if "code" not in raw.columns:
        raise ValueError("raw price csv must contain code / 代码")
    pieces = []
    for code, g in raw.groupby("code"):
        pieces.append(sample_180d_for_one_stock(g))
    out = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_csv, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    # Example:
    # python local_tools/sampling_180d.py
    in_path = Path("local_exports/price_daily_raw.csv")
    out_path = Path("deploy_data/price_180d_sample.csv")
    if not in_path.exists():
        print(f"Missing {in_path}. Export raw daily prices from iFind first.")
    else:
        build_price_180d_sample(in_path, out_path)
        print(f"Saved {out_path}")
