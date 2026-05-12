from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path("deploy_data")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    for enc in ("utf-8-sig", "utf-8", "gb18030", "big5"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path)


def to_num(s):
    return pd.to_numeric(s, errors="coerce")


def clip(x, lo=0, hi=100):
    return np.clip(x, lo, hi)


def safe_col(df: pd.DataFrame, col: str, default=np.nan):
    if col in df.columns:
        return df[col]
    return pd.Series([default] * len(df), index=df.index)


def sigmoid_score(x, center, scale, max_points):
    x = to_num(x).fillna(0)
    return max_points / (1 + np.exp(-(x - center) / scale))


def compute_issue_score(df: pd.DataFrame) -> pd.Series:
    n = len(df)
    score = pd.Series(45.0, index=df.index)

    public_sub = to_num(safe_col(df, "public_subscription_multiple")).combine_first(
        to_num(safe_col(df, "public_subscription_multiple_ballot"))
    ).fillna(0)
    margin = to_num(safe_col(df, "margin_multiple")).fillna(0)
    one_lot = to_num(safe_col(df, "one_lot_success_rate_pct")).fillna(np.nan)
    cornerstone_quality = to_num(safe_col(df, "cornerstone_quality_score")).fillna(0)
    cornerstone_count = to_num(safe_col(df, "cornerstone_count")).fillna(0)
    issue_price = to_num(safe_col(df, "issue_price")).fillna(np.nan)
    offer_low = to_num(safe_col(df, "offer_price_low")).fillna(np.nan)
    offer_high = to_num(safe_col(df, "offer_price_high")).fillna(np.nan)
    bookrunners = to_num(safe_col(df, "bookrunner_count")).fillna(0)
    underwriters = to_num(safe_col(df, "underwriter_count")).fillna(0)

    # 认购热度：不是越高越好，极端拥挤会作为风险另行提示
    score += np.select(
        [public_sub >= 100, public_sub >= 30, public_sub >= 10, public_sub > 0],
        [10, 8, 5, 2],
        default=0,
    )
    score += np.select(
        [margin >= 500, margin >= 100, margin >= 20, margin > 0],
        [8, 7, 4, 1],
        default=0,
    )
    # 中签率越低说明拥挤，给热度分，但小于5%同时会进风险标签
    score += np.select(
        [(one_lot > 0) & (one_lot <= 5), (one_lot > 5) & (one_lot <= 20), one_lot > 20],
        [6, 4, 1],
        default=0,
    )
    score += np.minimum(cornerstone_quality / 10, 8)
    score += np.select([cornerstone_count >= 10, cornerstone_count >= 5, cornerstone_count >= 1], [5, 3, 1], default=0)
    score += np.select([bookrunners >= 3, bookrunners >= 1], [3, 1], default=0)
    score += np.select([underwriters >= 10, underwriters >= 3], [2, 1], default=0)

    # 定价位置：接近上限定价在强热度下可加分；无热度上限定价扣分
    price_pos = (issue_price - offer_low) / (offer_high - offer_low)
    high_price = price_pos >= 0.85
    low_price = price_pos <= 0.20
    score += np.where(low_price.fillna(False), 3, 0)
    score += np.where(high_price.fillna(False) & (public_sub >= 30), 2, 0)
    score -= np.where(high_price.fillna(False) & (public_sub < 10), 4, 0)

    # 信息完整度加分：能拿到发行价/上市日/孖展/中签/基石，模型可信度更高
    completeness = pd.Series(0, index=df.index, dtype=float)
    for c in ["issue_price", "listing_date", "margin_multiple", "one_lot_success_rate_pct", "cornerstone_count", "bookrunner_count"]:
        if c in df.columns:
            completeness += df[c].notna().astype(float)
    score += completeness * 1.2
    return pd.Series(clip(score), index=df.index)


def compute_secondary_score(df: pd.DataFrame) -> pd.Series:
    score = pd.Series(45.0, index=df.index)
    d1 = to_num(safe_col(df, "d1_close_ret")).combine_first(to_num(safe_col(df, "d1_close_ret_pct")) / 100).fillna(0)
    max20 = to_num(safe_col(df, "max_20_ret")).fillna(0)
    min20 = to_num(safe_col(df, "min_20_ret")).fillna(0)
    max60 = to_num(safe_col(df, "max_60_ret")).fillna(0)
    min60 = to_num(safe_col(df, "min_60_ret")).fillna(0)
    max180 = to_num(safe_col(df, "max_180_ret")).fillna(0)
    min180 = to_num(safe_col(df, "min_180_ret")).fillna(0)
    quote_rows = to_num(safe_col(df, "quote_rows")).fillna(0)
    path = safe_col(df, "path_label", "").fillna("").astype(str)

    score += np.select([d1 >= 0.30, d1 >= 0.10, d1 > 0], [12, 7, 3], default=0)
    score += np.select([max20 >= 0.50, max20 >= 0.20, max20 >= 0.08], [12, 8, 4], default=0)
    score += np.select([max60 >= 0.80, max60 >= 0.30, max60 >= 0.12], [10, 7, 3], default=0)
    score -= np.select([min20 <= -0.30, min20 <= -0.15, min20 < 0], [14, 8, 3], default=0)
    score -= np.select([min60 <= -0.40, min60 <= -0.20, min60 < 0], [10, 5, 2], default=0)
    score += np.select([quote_rows >= 60, quote_rows >= 20, quote_rows >= 5], [4, 2, 1], default=0)

    score += np.where(path.str.contains("上市即强势", na=False), 8, 0)
    score += np.where(path.str.contains("深V|修复|反弹", na=False), 7, 0)
    score -= np.where(path.str.contains("破发|弱势", na=False), 8, 0)
    score -= np.where(path.str.contains("升后破发", na=False), 12, 0)
    return pd.Series(clip(score), index=df.index)


def compute_a1_score(df: pd.DataFrame) -> pd.Series:
    score = pd.Series(40.0, index=df.index)
    status = safe_col(df, "application_status", "").fillna("").astype(str)
    stage = safe_col(df, "lifecycle_stage", "").fillna("").astype(str)
    sponsor = safe_col(df, "sponsor", "").fillna("").astype(str)
    coord = safe_col(df, "overall_coordinator", "").fillna("").astype(str)
    industry1 = safe_col(df, "industry_level_1", "").fillna("").astype(str)
    first_date = pd.to_datetime(safe_col(df, "first_application_date"), errors="coerce")
    hearing_date = pd.to_datetime(safe_col(df, "hearing_date"), errors="coerce")

    score += np.where(status.str.contains("通过聆讯|已通过|聆讯后", na=False), 20, 0)
    score += np.where(stage.str.contains("招股|待上市", na=False), 15, 0)
    score += np.where(status.str.contains("处理中", na=False), 8, 0)
    score += np.where(hearing_date.notna(), 8, 0)
    score += np.where(sponsor.str.len() > 3, 5, 0)
    score += np.where(coord.str.len() > 3, 3, 0)
    score += np.where(industry1.str.contains("生物|科技|医疗|制药|电子|机器人|新能源", na=False), 5, 0)
    score -= np.where(first_date.notna() & (pd.Timestamp.today().normalize() - first_date).dt.days.gt(540), 6, 0)
    return pd.Series(clip(score), index=df.index)


def build_risk_tags(df: pd.DataFrame) -> pd.Series:
    tags = []
    for _, r in df.iterrows():
        t = []
        existing = r.get("risk_tags", "")
        if isinstance(existing, str) and existing and existing != "nan":
            t.extend([x.strip() for x in existing.replace("；", ";").split(";") if x.strip()])
        pub = pd.to_numeric(r.get("public_subscription_multiple", np.nan), errors="coerce")
        pub2 = pd.to_numeric(r.get("public_subscription_multiple_ballot", np.nan), errors="coerce")
        margin = pd.to_numeric(r.get("margin_multiple", np.nan), errors="coerce")
        one_lot = pd.to_numeric(r.get("one_lot_success_rate_pct", np.nan), errors="coerce")
        min20 = pd.to_numeric(r.get("min_20_ret", np.nan), errors="coerce")
        min60 = pd.to_numeric(r.get("min_60_ret", np.nan), errors="coerce")
        max20 = pd.to_numeric(r.get("max_20_ret", np.nan), errors="coerce")
        d1 = pd.to_numeric(r.get("d1_close_ret", np.nan), errors="coerce")
        quote_status = str(r.get("quote_status", ""))
        c_count = pd.to_numeric(r.get("cornerstone_count", np.nan), errors="coerce")
        lockup = r.get("lockup_end_date", np.nan)

        if pd.notna(margin) and margin >= 500:
            t.append("孖展极度拥挤")
        elif pd.notna(margin) and margin >= 100:
            t.append("孖展拥挤")
        if pd.notna(pub) and pub >= 100 or pd.notna(pub2) and pub2 >= 100:
            t.append("公开认购过热")
        if pd.notna(one_lot) and one_lot <= 5:
            t.append("一手中签率低")
        if pd.notna(c_count) and c_count >= 8:
            t.append("基石阵容较多")
        if pd.notna(lockup) and str(lockup) not in ("", "nan", "NaT"):
            t.append("关注基石锁定期")
        if pd.notna(min20) and min20 <= -0.15 or pd.notna(min60) and min60 <= -0.20:
            t.append("上市后回撤大")
        if pd.notna(d1) and d1 >= 0.30 and pd.notna(max20) and max20 <= d1 + 0.05:
            t.append("首日情绪后续不足")
        if quote_status == "missing":
            t.append("免费行情缺失")
        elif quote_status == "partial":
            t.append("行情样本不足")
        # 去重保序
        seen = []
        for x in t:
            if x and x not in seen:
                seen.append(x)
        tags.append("；".join(seen))
    return pd.Series(tags, index=df.index)


def make_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    issue = df["issue_participation_score"]
    sec = df["secondary_trade_score"]
    a1 = df["a1_prescreen_score"]
    final = df["ipo_decision_score"]
    stage = safe_col(df, "lifecycle_stage", "").fillna("").astype(str)
    path = safe_col(df, "path_label", "").fillna("").astype(str)
    quote_status = safe_col(df, "quote_status", "").fillna("").astype(str)

    primary = np.where(issue >= 78, "强参与/积极争取额度",
                np.where(issue >= 65, "小额参与/控制仓位",
                np.where(issue >= 52, "只看二级/等待价格确认", "回避或仅跟踪")))
    cornerstone = np.where((issue >= 72) & (a1 >= 60), "可谈基石/锚定，重点压估值和锁定期条件",
                    np.where(issue >= 60, "仅低价或小额锚定；不建议高估值锁定", "不建议基石锁定"))
    secondary = np.where(sec >= 78, "趋势确认买入/持有",
                 np.where((sec >= 65) & path.str.contains("深V|修复|反弹", na=False), "深V确认后分批买入",
                 np.where(sec >= 60, "等待回踩发行价/VWAP后试仓",
                 np.where(path.str.contains("破发|弱势", na=False), "破发弱势，回避或止损", "观察，等待触发"))))
    sell = np.where(path.str.contains("升后破发", na=False), "升后破发：反弹至发行价/首日VWAP附近减仓",
            np.where((sec >= 75) & (to_num(safe_col(df, "max_20_ret")).fillna(0) >= 0.5), "涨幅较大：放量不创新高时止盈",
            np.where(to_num(safe_col(df, "min_20_ret")).fillna(0) <= -0.15, "跌破发行价或20D低点时止损", "持仓以发行价、首日VWAP、20D低点为风控线")))
    tier = np.where(final >= 78, "A 高优先",
            np.where(final >= 65, "B 交易观察",
            np.where(final >= 52, "C 等触发", "D 回避/仅跟踪")))

    out = df.copy()
    out["decision_tier_step7"] = tier
    out["primary_recommendation"] = primary
    out["cornerstone_recommendation"] = cornerstone
    out["secondary_recommendation"] = secondary
    out["sell_risk_recommendation"] = sell
    out["model_recommendation_step7"] = (
        "一级：" + pd.Series(primary, index=df.index).astype(str) + "；二级：" + pd.Series(secondary, index=df.index).astype(str)
    )
    return out


def score_pool(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    pool = read_csv(data_dir / "ipo_decision_pool.csv")
    paths = read_csv(data_dir / "ipo_post_listing_paths.csv")
    if pool.empty:
        raise FileNotFoundError("deploy_data/ipo_decision_pool.csv not found or empty")

    # 以路径表刷新行情相关列，避免旧 pool 未合并最新路径
    if not paths.empty and "code" in paths.columns:
        keep = [c for c in paths.columns if c not in ("name", "listing_date", "issue_price")]
        pool = pool.drop(columns=[c for c in keep if c in pool.columns and c != "code"], errors="ignore")
        pool = pool.merge(paths[keep], on="code", how="left")

    for c in ["listing_date", "application_date", "first_application_date", "hearing_date", "lockup_end_date"]:
        if c in pool.columns:
            pool[c] = pd.to_datetime(pool[c], errors="coerce").dt.strftime("%Y-%m-%d")

    pool["issue_participation_score"] = compute_issue_score(pool).round(1)
    pool["secondary_trade_score"] = compute_secondary_score(pool).round(1)
    pool["a1_prescreen_score"] = compute_a1_score(pool).round(1)
    # 已上市且有行情时，二级权重提高；未上市则一级/A1权重提高
    has_quotes = to_num(safe_col(pool, "quote_rows")).fillna(0) > 0
    final = np.where(
        has_quotes,
        pool["issue_participation_score"] * 0.35 + pool["secondary_trade_score"] * 0.45 + pool["a1_prescreen_score"] * 0.20,
        pool["issue_participation_score"] * 0.55 + pool["a1_prescreen_score"] * 0.35 + pool["secondary_trade_score"] * 0.10,
    )
    pool["ipo_decision_score"] = pd.Series(final, index=pool.index).round(1)
    pool["risk_tags_step7"] = build_risk_tags(pool)
    pool = make_recommendations(pool)
    return pool


def update_inventory(data_dir: Path):
    inv = read_csv(data_dir / "data_inventory.csv")
    rows = [] if inv.empty else inv.to_dict("records")
    def upsert(name, file_name):
        path = data_dir / file_name
        raw = 0
        if path.exists():
            try:
                raw = len(read_csv(path))
            except Exception:
                raw = 0
        status = "已接入" if raw > 0 else "未接入"
        for r in rows:
            if r.get("source_name") == name:
                r["file_name"] = file_name if raw > 0 else r.get("file_name")
                r["raw_rows"] = raw
                r["normalized_rows"] = raw
                r["status"] = status
                return
        rows.append({"source_name": name, "file_name": file_name if raw > 0 else "", "raw_rows": raw, "normalized_rows": raw, "status": status})
    upsert("上市后0-180D行情", "ipo_daily_quotes_180d.csv")
    upsert("上市后路径标签", "ipo_post_listing_paths.csv")
    upsert("Step7决策评分", "ipo_decision_scored_step7.csv")
    out = pd.DataFrame(rows)
    out.to_csv(data_dir / "data_inventory.csv", index=False, encoding="utf-8-sig")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="deploy_data")
    parser.add_argument("--out", default="ipo_decision_scored_step7.csv")
    args = parser.parse_args()
    data_dir = Path(args.data_dir)
    scored = score_pool(data_dir)
    out_path = data_dir / args.out
    scored.to_csv(out_path, index=False, encoding="utf-8-sig")
    # 同步更新主 pool，方便旧页面读取
    scored.to_csv(data_dir / "ipo_decision_pool.csv", index=False, encoding="utf-8-sig")
    update_inventory(data_dir)
    print(f"Saved {out_path} rows={len(scored)} cols={len(scored.columns)}")


if __name__ == "__main__":
    main()
