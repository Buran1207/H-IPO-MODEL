#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build post-listing path labels from deploy_data/ipo_daily_quotes_180d.csv."""
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

CODE_CANDIDATES = ["code", "证券代码", "股票代码", "正式代码", "同花顺代码"]


def read_csv_smart(path: Path) -> pd.DataFrame:
    for enc in ["utf-8-sig", "utf-8", "gb18030", "gbk", "big5"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            pass
    return pd.read_csv(path)


def safe_ret(close, base):
    try:
        if pd.isna(close) or pd.isna(base) or float(base) <= 0:
            return pd.NA
        return float(close) / float(base) - 1
    except Exception:
        return pd.NA


def window_metric(g: pd.DataFrame, days: int, base: float):
    w = g[g["days_since_listing"] <= days]
    if w.empty or pd.isna(base) or base <= 0:
        return pd.NA, pd.NA
    return w["close"].max() / base - 1, w["close"].min() / base - 1


def label_path(row):
    d1 = row.get("d1_close_ret")
    max20 = row.get("max_20_ret")
    min20 = row.get("min_20_ret")
    max60 = row.get("max_60_ret")
    min60 = row.get("min_60_ret")
    max180 = row.get("max_180_ret")
    min180 = row.get("min_180_ret")

    def val(x, default=0.0):
        return default if pd.isna(x) else float(x)

    if val(d1) >= 0.25 and val(max60) >= 0.35 and val(min20) > -0.08:
        return "上市即强势"
    if val(min20) <= -0.10 and val(max60) >= 0.20:
        return "深V反弹"
    if val(max20) >= 0.25 and val(min180, 0) <= -0.05:
        return "升后回落/破发风险"
    if val(max60) < 0.08 and val(min60) <= -0.10:
        return "持续破发/弱势"
    if val(max180) >= 0.20 and val(min20) > -0.15:
        return "温和趋势"
    return "观察/无明显路径"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quotes", default="deploy_data/ipo_daily_quotes_180d.csv")
    parser.add_argument("--pool", default="deploy_data/ipo_decision_pool.csv")
    parser.add_argument("--out", default="deploy_data/ipo_post_listing_paths.csv")
    parser.add_argument("--update-pool", action="store_true")
    args = parser.parse_args()

    quotes_path = Path(args.quotes)
    out_path = Path(args.out)
    if not quotes_path.exists():
        raise FileNotFoundError(quotes_path)

    q = read_csv_smart(quotes_path)
    if q.empty:
        paths = pd.DataFrame(columns=[
            "code", "name", "listing_date", "issue_price", "quote_rows", "quote_source",
            "d1_close_ret", "max_20_ret", "min_20_ret", "max_60_ret", "min_60_ret",
            "max_180_ret", "min_180_ret", "path_label", "quote_status",
        ])
        paths.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"No quotes. Saved empty {out_path}")
        return

    q["date"] = pd.to_datetime(q["date"], errors="coerce")
    q["listing_date"] = pd.to_datetime(q["listing_date"], errors="coerce")
    q["days_since_listing"] = pd.to_numeric(q.get("days_since_listing"), errors="coerce")
    q["close"] = pd.to_numeric(q["close"], errors="coerce")
    q["issue_price"] = pd.to_numeric(q.get("issue_price"), errors="coerce")
    q = q.dropna(subset=["code", "date", "close"]).sort_values(["code", "date"])

    records = []
    for code, g in q.groupby("code"):
        g = g.sort_values("date")
        first = g.iloc[0]
        base = first.get("issue_price")
        if pd.isna(base) or base <= 0:
            base = first["close"]
        d1_close_ret = safe_ret(first["close"], base)
        max20, min20 = window_metric(g, 20, base)
        max60, min60 = window_metric(g, 60, base)
        max180, min180 = window_metric(g, 180, base)
        rec = {
            "code": code,
            "name": first.get("name", ""),
            "listing_date": first.get("listing_date"),
            "issue_price": first.get("issue_price"),
            "quote_rows": len(g),
            "quote_source": ";".join(sorted(set(g.get("source", pd.Series(dtype=str)).dropna().astype(str)))),
            "d1_close_ret": d1_close_ret,
            "max_20_ret": max20,
            "min_20_ret": min20,
            "max_60_ret": max60,
            "min_60_ret": min60,
            "max_180_ret": max180,
            "min_180_ret": min180,
            "quote_status": "ok" if len(g) >= 10 else "partial",
        }
        rec["path_label"] = label_path(rec)
        records.append(rec)

    paths = pd.DataFrame(records).sort_values(["listing_date", "code"], ascending=[False, True])
    paths.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"Saved {out_path} rows={len(paths)}")

    if args.update_pool:
        pool_path = Path(args.pool)
        if pool_path.exists():
            pool = read_csv_smart(pool_path)
            code_col = None
            for c in CODE_CANDIDATES:
                if c in pool.columns:
                    code_col = c
                    break
            if code_col is None and "code" in pool.columns:
                code_col = "code"
            if code_col is not None:
                # Use code column as-is; the quote script normalizes to 4-digit .HK. Try a simple normalized helper.
                def norm(x):
                    s = str(x).strip().upper().replace(".HK", "")
                    import re
                    if s.startswith("H"):
                        return s + ".HK" if not s.endswith(".HK") else s
                    d = re.sub(r"\D", "", s)
                    if len(d) >= 5 and d.startswith("0"):
                        d = d[-4:]
                    elif len(d) < 4:
                        d = d.zfill(4)
                    return f"{d}.HK" if d else str(x)
                pool["_merge_code"] = pool[code_col].map(norm)
                merge_cols = ["code", "path_label", "quote_status", "d1_close_ret", "max_20_ret", "min_20_ret", "max_60_ret", "min_60_ret", "max_180_ret", "min_180_ret"]
                updated = pool.merge(paths[merge_cols], how="left", left_on="_merge_code", right_on="code", suffixes=("", "_new"))
                for c in ["path_label", "quote_status", "d1_close_ret", "max_20_ret", "min_20_ret", "max_60_ret", "min_60_ret", "max_180_ret", "min_180_ret"]:
                    new_col = c + "_new"
                    if new_col in updated.columns:
                        updated[c] = updated[new_col].combine_first(updated[c]) if c in updated.columns else updated[new_col]
                drop_cols = [c for c in updated.columns if c.endswith("_new") or c in {"_merge_code", "code_new"}]
                updated = updated.drop(columns=drop_cols, errors="ignore")
                updated.to_csv(pool_path, index=False, encoding="utf-8-sig")
                print(f"Updated {pool_path}")
            else:
                print(f"Pool not updated: cannot find code column in {pool_path}")


if __name__ == "__main__":
    main()
