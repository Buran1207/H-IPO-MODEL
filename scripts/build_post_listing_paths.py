from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def read_csv_smart(path):
    for enc in ("utf-8-sig", "utf-8", "gb18030", "gbk", "big5", "cp950"):
        try:
            return pd.read_csv(path, encoding=enc, dtype=str)
        except Exception:
            pass
    return pd.DataFrame()


def pct(x):
    return pd.to_numeric(x, errors="coerce")


def main():
    ap = argparse.ArgumentParser(description="根据0-180D日行情生成半新股路径标签。")
    ap.add_argument("--pool", default="deploy_data/ipo_decision_pool.csv")
    ap.add_argument("--quotes", default="deploy_data/ipo_daily_quotes_180d.csv")
    ap.add_argument("--out", default="deploy_data/ipo_post_listing_paths.csv")
    ap.add_argument("--update-pool", action="store_true")
    args = ap.parse_args()

    pool = read_csv_smart(args.pool)
    q = read_csv_smart(args.quotes)
    if pool.empty or q.empty:
        out = pd.DataFrame(columns=["code", "d1_close_ret_pct", "max_20_ret_pct", "min_20_ret_pct", "max_60_ret_pct", "min_60_ret_pct", "max_180_ret_pct", "path_label", "secondary_signal"])
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(args.out, index=False, encoding="utf-8-sig")
        return

    pool["issue_price"] = pct(pool.get("issue_price"))
    q["date"] = pd.to_datetime(q["date"], errors="coerce")
    for c in ["open", "high", "low", "close", "volume", "amount_est_hkd"]:
        if c in q.columns:
            q[c] = pct(q[c])
    rows = []
    for code, g in q.dropna(subset=["date"]).sort_values(["code", "date"]).groupby("code"):
        issue = pool.loc[pool["code"].astype(str) == str(code), "issue_price"]
        issue_price = issue.dropna().iloc[0] if len(issue.dropna()) else pd.NA
        if pd.isna(issue_price) or issue_price == 0:
            continue
        g = g.reset_index(drop=True).copy()
        g["ret"] = g["close"] / issue_price - 1
        def window(n):
            return g.head(n)
        d1 = g.head(1)
        w20, w60, w180 = window(20), window(60), window(180)
        d1_ret = d1["ret"].iloc[0] if len(d1) else pd.NA
        max20, min20 = w20["ret"].max(), w20["ret"].min()
        max60, min60 = w60["ret"].max(), w60["ret"].min()
        max180, min180 = w180["ret"].max(), w180["ret"].min()
        broke20 = min20 < -0.03
        deep_v = (min20 < -0.05) and (max60 > 0.15)
        strong_open = d1_ret > 0.15
        pop_then_fade = strong_open and (min60 < 0)
        if strong_open and not pop_then_fade:
            label = "strong_open"
            signal = "首日强势；等待回踩发行价/首日VWAP附近确认，不追极端高开。"
        elif deep_v:
            label = "deep_v_rebound"
            signal = "深V路径；重点观察重新站回发行价和成交放大。"
        elif pop_then_fade:
            label = "pop_then_fade"
            signal = "升后回落；放量滞涨或跌破发行价应减仓/回避。"
        elif broke20:
            label = "persistent_break"
            signal = "破发弱势；除非出现基本面催化与资金回流，否则只跟踪。"
        else:
            label = "moderate_tradeable"
            signal = "温和交易型；按发行价、首日低点和均线状态机处理。"
        rows.append({
            "code": code,
            "d1_close_ret_pct": round(d1_ret * 100, 2) if pd.notna(d1_ret) else pd.NA,
            "max_20_ret_pct": round(max20 * 100, 2) if pd.notna(max20) else pd.NA,
            "min_20_ret_pct": round(min20 * 100, 2) if pd.notna(min20) else pd.NA,
            "max_60_ret_pct": round(max60 * 100, 2) if pd.notna(max60) else pd.NA,
            "min_60_ret_pct": round(min60 * 100, 2) if pd.notna(min60) else pd.NA,
            "max_180_ret_pct": round(max180 * 100, 2) if pd.notna(max180) else pd.NA,
            "min_180_ret_pct": round(min180 * 100, 2) if pd.notna(min180) else pd.NA,
            "path_label": label,
            "secondary_signal": signal,
        })
    out = pd.DataFrame(rows)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False, encoding="utf-8-sig")

    if args.update_pool and not out.empty:
        merged = pool.merge(out, on="code", how="left")
        merged.to_csv(args.pool, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
