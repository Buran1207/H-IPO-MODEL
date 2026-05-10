from __future__ import annotations

from pathlib import Path

import pandas as pd

INPUT_CANDIDATES = [
    Path("deploy_data/hk_ipo_scored_public.csv"),
    Path("hk_ipo_scored_public.csv"),
]
OUTPUT = Path("local_outputs/quote_sampling_plan.csv")


def first_existing(paths):
    for p in paths:
        if p.exists():
            return p
    raise FileNotFoundError("找不到 hk_ipo_scored_public.csv")


def clean_code(x):
    if pd.isna(x):
        return ""
    s = str(x).strip().upper()
    if s.endswith(".HK"):
        left = s[:-3]
        if left.isdigit():
            return f"{int(left):04d}.HK"
        return s
    if s.isdigit():
        return f"{int(s):04d}.HK"
    return s


def wanted_offsets():
    offsets = []
    offsets.extend(range(0, 31))       # D0-D30 daily
    offsets.extend(range(33, 91, 3))   # D31-D90 every 3 calendar days;行情接口会跳过非交易日或返回空
    offsets.extend(range(98, 181, 7))  # D91-D180 weekly
    return sorted(set(offsets))


def main():
    src = first_existing(INPUT_CANDIDATES)
    df = pd.read_csv(src, encoding="utf-8-sig")
    if "listing_date" not in df.columns or "code" not in df.columns:
        raise ValueError("输入文件必须包含 code 和 listing_date")
    df["listing_date"] = pd.to_datetime(df["listing_date"], errors="coerce")
    df["code"] = df["code"].map(clean_code)
    rows = []
    offsets = wanted_offsets()
    for _, row in df.dropna(subset=["listing_date"]).iterrows():
        for offset in offsets:
            rows.append({
                "code": row["code"],
                "name": row.get("name", ""),
                "listing_date": row["listing_date"].date().isoformat(),
                "day_offset": offset,
                "target_date": (row["listing_date"] + pd.Timedelta(days=offset)).date().isoformat(),
                "frequency_bucket": "D0-D30每日" if offset <= 30 else ("D31-D90每3日" if offset <= 90 else "D91-D180每周"),
                "fields": "open,high,low,close,volume,amount,turnover,pct_chg",
            })
    out = pd.DataFrame(rows)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"已生成 {OUTPUT}，共 {len(out)} 行")


if __name__ == "__main__":
    main()
