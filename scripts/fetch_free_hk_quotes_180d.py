#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch free daily quotes for Hong Kong IPO stocks listed from 2024 onward.

Data priority:
1) Yahoo Finance chart API
2) Stooq CSV endpoint

Input:  deploy_data/ipo_decision_pool.csv or any CSV with code/listing_date columns
Output: deploy_data/ipo_daily_quotes_180d.csv
Logs:   deploy_data/ipo_quote_fetch_failures.csv
        deploy_data/ipo_quote_fetch_skipped.csv

This script intentionally skips:
- temporary IPO codes such as H2556.HK
- stocks with no formal numeric HK code
- listing_date before 2024-01-01
- listing_date after today
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import requests

MIN_LISTING_DATE = pd.Timestamp("2024-01-01")
TODAY = pd.Timestamp(date.today())

CODE_CANDIDATES = [
    "code", "ticker", "stock_code", "hk_code", "证券代码", "股票代码", "同花顺代码",
    "正式代码", "代码", "股份代号", "上市代码",
]
NAME_CANDIDATES = ["name", "short_name", "证券简称", "股票简称", "公司简称", "发行人", "issuer_name", "名称"]
LISTING_DATE_CANDIDATES = [
    "listing_date", "上市日期", "上市日", "挂牌日期", "首发上市日期", "上市时间",
]
ISSUE_PRICE_CANDIDATES = [
    "issue_price", "发行价", "发售价", "最终发行价", "offer_price", "招股价", "发售价格",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json,text/csv,text/plain,*/*",
}


def pick_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    cols = list(df.columns)
    lowered = {str(c).strip().lower(): c for c in cols}
    for c in candidates:
        if c in cols:
            return c
        if c.lower() in lowered:
            return lowered[c.lower()]
    # loose contains match for Chinese/English mixed headers
    for c in candidates:
        key = c.lower()
        for col in cols:
            if key and key in str(col).strip().lower():
                return col
    return None


def read_csv_smart(path: Path) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "gb18030", "gbk", "big5"]
    last_err = None
    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception as e:  # noqa: BLE001
            last_err = e
    raise RuntimeError(f"Cannot read {path}: {last_err}")


def to_number(x) -> float | None:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    s = str(x).strip()
    if not s or s in {"--", "-", "None", "nan", "NaN"}:
        return None
    s = s.replace(",", "").replace("港元", "").replace("HK$", "").replace("HKD", "").strip()
    # Range like 5.00-6.00: take right side as final only if no better field; here take first numeric token
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


def parse_date(x) -> pd.Timestamp | pd.NaT:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return pd.NaT
    s = str(x).strip()
    if not s or s in {"--", "-", "None", "nan", "NaN"}:
        return pd.NaT
    # iFind sometimes exports YYYY-MM or YYYY/MM/DD; pandas can handle most
    return pd.to_datetime(s, errors="coerce")


def normalize_hk_code(raw) -> Optional[str]:
    """Return Yahoo-style HK ticker such as 0700.HK / 9988.HK / 6610.HK."""
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return None
    s = str(raw).strip().upper().replace(" ", "")
    if not s or s in {"--", "-", "NAN", "NONE"}:
        return None
    # Temporary A1/listing application codes such as H2556.HK have no daily trading quote.
    if s.startswith("H"):
        return None
    s = s.replace(".HK", "")
    # Remove non-digits, but keep pure numeric HK code only.
    digits = re.sub(r"\D", "", s)
    if not digits:
        return None
    # Ignore RMB counters / odd 5-digit tickers unless they are standard 0xxxx codes.
    if len(digits) >= 5:
        if digits.startswith("0"):
            digits = digits[-4:]
        else:
            # Some non-standard counters such as 80011.HK are not IPO common-stock tickers.
            return None
    elif len(digits) < 4:
        digits = digits.zfill(4)
    return f"{digits}.HK"


@dataclass
class PoolRow:
    code_raw: str
    code: str
    name: str
    listing_date: pd.Timestamp
    issue_price: float | None


def load_pool(path: Path, start_min: pd.Timestamp) -> tuple[list[PoolRow], pd.DataFrame, pd.DataFrame]:
    df = read_csv_smart(path)
    code_col = pick_col(df, CODE_CANDIDATES)
    listing_col = pick_col(df, LISTING_DATE_CANDIDATES)
    name_col = pick_col(df, NAME_CANDIDATES)
    issue_col = pick_col(df, ISSUE_PRICE_CANDIDATES)

    if not code_col:
        raise ValueError(f"Cannot find code column in {path}. Columns={list(df.columns)}")
    if not listing_col:
        raise ValueError(f"Cannot find listing_date column in {path}. Columns={list(df.columns)}")

    rows: list[PoolRow] = []
    skipped = []
    for _, r in df.iterrows():
        raw = r.get(code_col)
        code = normalize_hk_code(raw)
        name = "" if not name_col else str(r.get(name_col, "") or "")
        listing_date = parse_date(r.get(listing_col))
        issue_price = to_number(r.get(issue_col)) if issue_col else None
        reason = None
        if not code:
            reason = "无正式港股交易代码/临时代码，跳过"
        elif pd.isna(listing_date):
            reason = "缺上市日期，跳过"
        elif listing_date < start_min:
            reason = f"上市日期早于{start_min.date()}，跳过"
        elif listing_date > TODAY:
            reason = "尚未上市/上市日在未来，跳过"
        if reason:
            skipped.append({
                "code_raw": raw, "normalized_code": code or "", "name": name,
                "listing_date": "" if pd.isna(listing_date) else listing_date.date().isoformat(),
                "reason": reason,
            })
            continue
        rows.append(PoolRow(str(raw), code, name, listing_date.normalize(), issue_price))

    # Deduplicate by normalized formal ticker; keep latest row info.
    dedup = {}
    for row in rows:
        dedup[row.code] = row
    return list(dedup.values()), df, pd.DataFrame(skipped)


def ts_seconds(d: pd.Timestamp) -> int:
    # Yahoo chart endpoint uses UNIX seconds.
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def fetch_yahoo(row: PoolRow, end_date: pd.Timestamp, timeout: int = 15) -> pd.DataFrame:
    period1 = ts_seconds(row.listing_date)
    period2 = ts_seconds(end_date + pd.Timedelta(days=1))
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{row.code}"
    params = {
        "period1": period1,
        "period2": period2,
        "interval": "1d",
        "events": "history",
        "includeAdjustedClose": "true",
    }
    resp = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()
    err = payload.get("chart", {}).get("error")
    if err:
        raise RuntimeError(json.dumps(err, ensure_ascii=False))
    result = payload.get("chart", {}).get("result") or []
    if not result:
        raise RuntimeError("Yahoo returned empty result")
    result0 = result[0]
    timestamps = result0.get("timestamp") or []
    quote = (result0.get("indicators", {}).get("quote") or [{}])[0]
    adj = (result0.get("indicators", {}).get("adjclose") or [{}])[0].get("adjclose", [])
    if not timestamps:
        raise RuntimeError("Yahoo returned no timestamps")
    out = pd.DataFrame({
        "date": pd.to_datetime(timestamps, unit="s", utc=True).tz_convert(None).date,
        "open": quote.get("open", []),
        "high": quote.get("high", []),
        "low": quote.get("low", []),
        "close": quote.get("close", []),
        "volume": quote.get("volume", []),
    })
    if len(adj) == len(out):
        out["adj_close"] = adj
    else:
        out["adj_close"] = out["close"]
    out = out.dropna(subset=["close"]).copy()
    if out.empty:
        raise RuntimeError("Yahoo returned rows but all close values are empty")
    out["source"] = "yahoo"
    return out


def fetch_stooq(row: PoolRow, end_date: pd.Timestamp, timeout: int = 15) -> pd.DataFrame:
    # Stooq usually uses lowercase 0700.hk format.
    symbol = row.code.lower()
    d1 = row.listing_date.strftime("%Y%m%d")
    d2 = end_date.strftime("%Y%m%d")
    url = "https://stooq.com/q/d/l/"
    params = {"s": symbol, "d1": d1, "d2": d2, "i": "d"}
    resp = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    text = resp.text.strip()
    if not text or "No data" in text or text.lower().startswith("<!doctype"):
        raise RuntimeError("Stooq returned no data")
    df = pd.read_csv(io.StringIO(text))
    if df.empty or "Date" not in df.columns:
        raise RuntimeError("Stooq CSV is empty or malformed")
    rename = {
        "Date": "date", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume",
    }
    out = df.rename(columns=rename)
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.date
    for c in ["open", "high", "low", "close", "volume"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    out = out.dropna(subset=["date", "close"]).copy()
    if out.empty:
        raise RuntimeError("Stooq returned rows but all close values are empty")
    out["adj_close"] = out["close"]
    out["source"] = "stooq"
    return out[["date", "open", "high", "low", "close", "volume", "adj_close", "source"]]


def enrich_quote_df(q: pd.DataFrame, row: PoolRow) -> pd.DataFrame:
    out = q.copy()
    out["code"] = row.code
    out["code_raw"] = row.code_raw
    out["name"] = row.name
    out["listing_date"] = row.listing_date.date().isoformat()
    out["issue_price"] = row.issue_price
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).copy()
    out["days_since_listing"] = (out["date"] - row.listing_date).dt.days
    out = out[(out["days_since_listing"] >= 0) & (out["days_since_listing"] <= 180)].copy()
    if row.issue_price and row.issue_price > 0:
        out["ret_from_issue"] = out["close"] / row.issue_price - 1
    else:
        out["ret_from_issue"] = pd.NA
    cols = [
        "code", "code_raw", "name", "listing_date", "date", "days_since_listing", "issue_price",
        "open", "high", "low", "close", "adj_close", "volume", "ret_from_issue", "source",
    ]
    for c in cols:
        if c not in out.columns:
            out[c] = pd.NA
    return out[cols].sort_values(["code", "date"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", default="deploy_data/ipo_decision_pool.csv", help="IPO pool CSV")
    parser.add_argument("--out", default="deploy_data/ipo_daily_quotes_180d.csv", help="Output quote CSV")
    parser.add_argument("--start-min", default="2024-01-01", help="Only fetch stocks listed on/after this date")
    parser.add_argument("--end", default=str(date.today()), help="Fetch until this date, default=today")
    parser.add_argument("--sleep", type=float, default=0.25, help="Sleep seconds between tickers")
    parser.add_argument("--limit", type=int, default=0, help="For testing: fetch first N tickers only")
    args = parser.parse_args()

    pool_path = Path(args.pool)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    start_min = pd.Timestamp(args.start_min)
    end_date = min(pd.Timestamp(args.end), TODAY)

    rows, original_pool, skipped = load_pool(pool_path, start_min=start_min)
    if args.limit and args.limit > 0:
        rows = rows[: args.limit]

    print(f"Pool file: {pool_path}")
    print(f"Formal listed HK tickers to fetch: {len(rows)}")
    print(f"Skipped rows: {len(skipped)}")
    print(f"Date rule: listing_date >= {start_min.date()} and <= {end_date.date()}, fetch listing date to min(listing+180D, today)")

    all_quotes = []
    failures = []
    for i, row in enumerate(rows, start=1):
        quote_end = min(row.listing_date + pd.Timedelta(days=180), end_date)
        print(f"[{i}/{len(rows)}] {row.code} {row.name} listing={row.listing_date.date()} end={quote_end.date()}", flush=True)
        got = None
        errors = []
        try:
            got = fetch_yahoo(row, quote_end)
        except Exception as e:  # noqa: BLE001
            errors.append(f"yahoo: {e}")
        if got is None or got.empty:
            try:
                got = fetch_stooq(row, quote_end)
            except Exception as e:  # noqa: BLE001
                errors.append(f"stooq: {e}")
        if got is not None and not got.empty:
            enriched = enrich_quote_df(got, row)
            if not enriched.empty:
                all_quotes.append(enriched)
                print(f"    OK {len(enriched)} rows via {enriched['source'].iloc[0]}")
            else:
                failures.append({
                    "code": row.code, "name": row.name, "listing_date": row.listing_date.date().isoformat(),
                    "reason": "source returned data but no rows within 0-180D window", "errors": " | ".join(errors),
                })
                print("    FAILED: no rows within 0-180D window")
        else:
            failures.append({
                "code": row.code, "name": row.name, "listing_date": row.listing_date.date().isoformat(),
                "reason": "all sources failed", "errors": " | ".join(errors),
            })
            print(f"    FAILED: {' | '.join(errors)[:300]}")
        time.sleep(max(args.sleep, 0))

    if all_quotes:
        final = pd.concat(all_quotes, ignore_index=True)
        final = final.drop_duplicates(subset=["code", "date"], keep="first")
        final = final.sort_values(["code", "date"])
    else:
        final = pd.DataFrame(columns=[
            "code", "code_raw", "name", "listing_date", "date", "days_since_listing", "issue_price",
            "open", "high", "low", "close", "adj_close", "volume", "ret_from_issue", "source",
        ])

    final.to_csv(out_path, index=False, encoding="utf-8-sig")
    fail_path = out_path.parent / "ipo_quote_fetch_failures.csv"
    skip_path = out_path.parent / "ipo_quote_fetch_skipped.csv"
    pd.DataFrame(failures).to_csv(fail_path, index=False, encoding="utf-8-sig")
    skipped.to_csv(skip_path, index=False, encoding="utf-8-sig")

    print("\nDone")
    print(f"Saved quotes:   {out_path} rows={len(final)} tickers={final['code'].nunique() if len(final) else 0}")
    print(f"Saved failures: {fail_path} rows={len(failures)}")
    print(f"Saved skipped:  {skip_path} rows={len(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
