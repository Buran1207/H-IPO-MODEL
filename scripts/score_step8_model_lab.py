from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path("deploy_data")
CONFIG_PATH = Path("config/step8_weight_profiles.json")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    for enc in ("utf-8-sig", "utf-8", "gb18030", "big5"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def to_num(s) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def safe_col(df: pd.DataFrame, col: str, default=np.nan) -> pd.Series:
    if col in df.columns:
        return df[col]
    return pd.Series([default] * len(df), index=df.index)


def clip(s, lo=0, hi=100) -> pd.Series:
    return pd.Series(np.clip(pd.to_numeric(s, errors="coerce"), lo, hi), index=s.index)


def norm_pos(s: pd.Series, good: float, excellent: float, base=35, maxv=100) -> pd.Series:
    x = to_num(s).fillna(0)
    out = base + (x / max(good, 1e-9)) * 25
    out = np.where(x >= good, 60 + (np.minimum(x, excellent) - good) / max(excellent - good, 1e-9) * 30, out)
    out = np.where(x >= excellent, maxv, out)
    return pd.Series(np.clip(out, 0, maxv), index=s.index)


def norm_ret(s: pd.Series, mid: float, high: float, low: float) -> pd.Series:
    x = to_num(s).fillna(0)
    # low -> 20, 0 -> 45, mid -> 70, high -> 95
    out = np.interp(x, [low, 0, mid, high], [20, 45, 70, 95])
    return pd.Series(np.clip(out, 0, 100), index=s.index)


def load_weight_profiles(path: Path = CONFIG_PATH) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def prepare_pool(data_dir: Path) -> pd.DataFrame:
    pool = read_csv(data_dir / "ipo_decision_pool.csv")
    paths = read_csv(data_dir / "ipo_post_listing_paths.csv")
    if pool.empty:
        raise FileNotFoundError("deploy_data/ipo_decision_pool.csv not found")
    if not paths.empty and "code" in paths.columns:
        keep = [c for c in paths.columns if c not in ("name", "listing_date", "issue_price")]
        pool = pool.drop(columns=[c for c in keep if c in pool.columns and c != "code"], errors="ignore")
        pool = pool.merge(paths[keep], on="code", how="left")
    for c in ["listing_date", "application_date", "first_application_date", "hearing_date", "lockup_end_date", "prospectus_date", "gray_date"]:
        if c in pool.columns:
            pool[c] = pd.to_datetime(pool[c], errors="coerce")
    return pool


def compute_factor_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    pub = to_num(safe_col(out, "public_subscription_multiple")).combine_first(to_num(safe_col(out, "public_subscription_multiple_ballot"))).fillna(0)
    margin = to_num(safe_col(out, "margin_multiple")).fillna(0)
    one_lot = to_num(safe_col(out, "one_lot_success_rate_pct")).fillna(np.nan)
    c_count = to_num(safe_col(out, "cornerstone_count")).fillna(0)
    c_quality = to_num(safe_col(out, "cornerstone_quality_score")).fillna(0)
    bookrunner_count = to_num(safe_col(out, "bookrunner_count")).fillna(0)
    underwriter_count = to_num(safe_col(out, "underwriter_count")).fillna(0)
    issue_price = to_num(safe_col(out, "issue_price")).fillna(np.nan)
    offer_low = to_num(safe_col(out, "offer_price_low")).fillna(np.nan)
    offer_high = to_num(safe_col(out, "offer_price_high")).fillna(np.nan)
    gray_close = to_num(safe_col(out, "gray_close_ret_pct")).combine_first(to_num(safe_col(out, "d1_close_ret_pct"))).fillna(np.nan)
    gray_open = to_num(safe_col(out, "gray_open_ret_pct")).fillna(np.nan)
    d1 = to_num(safe_col(out, "d1_close_ret")).combine_first(to_num(safe_col(out, "d1_close_ret_pct")) / 100).fillna(np.nan)
    max20 = to_num(safe_col(out, "max_20_ret")).fillna(np.nan)
    min20 = to_num(safe_col(out, "min_20_ret")).fillna(np.nan)
    max60 = to_num(safe_col(out, "max_60_ret")).fillna(np.nan)
    min60 = to_num(safe_col(out, "min_60_ret")).fillna(np.nan)
    max180 = to_num(safe_col(out, "max_180_ret")).fillna(np.nan)
    min180 = to_num(safe_col(out, "min_180_ret")).fillna(np.nan)
    quote_rows = to_num(safe_col(out, "quote_rows")).fillna(0)
    path = safe_col(out, "path_label", "").fillna("").astype(str)
    status = safe_col(out, "application_status", "").fillna("").astype(str)
    stage = safe_col(out, "lifecycle_stage", "").fillna("").astype(str)
    sponsor = safe_col(out, "sponsor", "").fillna("").astype(str)
    coord = safe_col(out, "overall_coordinator", "").fillna("").astype(str)
    industry = safe_col(out, "industry_level_1", "").fillna("").astype(str)
    first_app = pd.to_datetime(safe_col(out, "first_application_date"), errors="coerce")
    hearing = pd.to_datetime(safe_col(out, "hearing_date"), errors="coerce")
    today = pd.Timestamp.today().normalize()

    # 1. 资金热度。极热给高热度，但后续用风险惩罚处理。
    heat = pd.Series(35.0, index=out.index)
    heat += np.select([pub >= 100, pub >= 30, pub >= 10, pub > 0], [22, 16, 9, 3], default=0)
    heat += np.select([margin >= 500, margin >= 100, margin >= 20, margin > 0], [22, 16, 8, 3], default=0)
    heat += np.select([(one_lot > 0) & (one_lot <= 5), (one_lot > 5) & (one_lot <= 20), one_lot > 20], [8, 5, 1], default=0)
    out["issue_heat_score"] = clip(heat)

    # 2. 配售/中签质量。极低中签是热度，但交易层面有拥挤风险。
    alloc = pd.Series(45.0, index=out.index)
    alloc += np.select([(one_lot > 0) & (one_lot <= 8), (one_lot > 8) & (one_lot <= 25), (one_lot > 25) & (one_lot <= 60)], [10, 7, 3], default=0)
    alloc += np.select([pub >= 50, pub >= 10, pub > 0], [8, 5, 2], default=0)
    alloc -= np.select([margin >= 1000, margin >= 500], [8, 4], default=0)
    out["allocation_quality_score"] = clip(alloc)

    # 3. 基石/投行背书。
    cb = pd.Series(38.0, index=out.index)
    cb += np.minimum(c_quality / 10, 12)
    cb += np.select([c_count >= 10, c_count >= 5, c_count >= 1], [9, 6, 2], default=0)
    cb += np.select([bookrunner_count >= 5, bookrunner_count >= 2, bookrunner_count >= 1], [8, 5, 2], default=0)
    cb += np.select([underwriter_count >= 15, underwriter_count >= 5, underwriter_count >= 1], [6, 4, 1], default=0)
    cb += np.where(sponsor.str.contains("中金|高盛|摩根|摩通|美林|花旗|瑞银|中信|华泰|国泰君安|海通|招银|农银|平安|里昂", na=False), 5, 0)
    out["cornerstone_bank_score"] = clip(cb)

    # 4. 定价安全。靠近下限/折价安全，上限定价无热度扣分。
    denom = (offer_high - offer_low).replace(0, np.nan)
    price_pos = ((issue_price - offer_low) / denom).clip(0, 1)
    pricing = pd.Series(50.0, index=out.index)
    pricing += np.where(price_pos <= 0.2, 14, 0)
    pricing += np.where((price_pos > 0.2) & (price_pos <= 0.55), 8, 0)
    pricing -= np.where((price_pos >= 0.85) & (pub < 10), 12, 0)
    pricing += np.where((price_pos >= 0.85) & (pub >= 30), 5, 0)
    pricing -= np.where(issue_price.isna(), 5, 0)
    out["pricing_safety_score"] = clip(pricing)

    # 5. 暗盘/首日信号。暗盘为百分数输入时按100转换，d1_close_ret是小数。
    gray_ret = gray_close / 100
    gray_sig = pd.Series(45.0, index=out.index)
    gray_sig += np.select([gray_ret >= 0.50, gray_ret >= 0.20, gray_ret >= 0.05, gray_ret > 0], [23, 16, 8, 3], default=0)
    gray_sig -= np.select([gray_ret <= -0.15, gray_ret < 0], [15, 7], default=0)
    gray_sig += np.select([d1 >= 0.30, d1 >= 0.10, d1 > 0], [16, 10, 4], default=0)
    gray_sig -= np.select([d1 <= -0.15, d1 < 0], [14, 6], default=0)
    gray_sig += np.where((gray_open / 100 >= 0.20) & (gray_ret < 0.05), -8, 0)  # 高开低走
    out["gray_signal_score"] = clip(gray_sig)

    # 6. 上市后交易状态。
    post = pd.Series(42.0, index=out.index)
    post += np.select([d1 >= 0.30, d1 >= 0.10, d1 > 0], [9, 6, 2], default=0)
    post += np.select([max20 >= 0.50, max20 >= 0.20, max20 >= 0.08], [15, 10, 5], default=0)
    post += np.select([max60 >= 0.80, max60 >= 0.30, max60 >= 0.12], [12, 8, 4], default=0)
    post += np.select([max180 >= 1.00, max180 >= 0.50, max180 >= 0.20], [10, 7, 3], default=0)
    post -= np.select([min20 <= -0.30, min20 <= -0.15, min20 < 0], [16, 9, 3], default=0)
    post -= np.select([min60 <= -0.40, min60 <= -0.20, min60 < 0], [12, 6, 2], default=0)
    post += np.select([quote_rows >= 60, quote_rows >= 20, quote_rows >= 5], [5, 3, 1], default=0)
    post += np.where(path.str.contains("上市即强势", na=False), 8, 0)
    post += np.where(path.str.contains("深V|修复|反弹", na=False), 8, 0)
    post -= np.where(path.str.contains("破发|弱势", na=False), 9, 0)
    post -= np.where(path.str.contains("升后破发", na=False), 14, 0)
    out["post_listing_score"] = clip(post)

    # 7. A1成熟度。
    a1 = pd.Series(40.0, index=out.index)
    a1 += np.where(status.str.contains("通过聆讯|已通过|聆讯后", na=False), 22, 0)
    a1 += np.where(stage.str.contains("招股|待上市", na=False), 16, 0)
    a1 += np.where(status.str.contains("处理中", na=False), 8, 0)
    a1 += np.where(hearing.notna(), 8, 0)
    a1 += np.where(sponsor.str.len() > 3, 5, 0)
    a1 += np.where(coord.str.len() > 3, 3, 0)
    a1 += np.where(industry.str.contains("生物|科技|医疗|制药|电子|机器人|新能源|半导体|AI|人工智能", na=False), 5, 0)
    a1 -= np.where(first_app.notna() & (today - first_app).dt.days.gt(540), 8, 0)
    out["a1_maturity_score"] = clip(a1)

    # 8. 数据质量。
    important_cols = ["issue_price", "listing_date", "public_subscription_multiple", "one_lot_success_rate_pct", "margin_multiple", "cornerstone_count", "bookrunner_count", "quote_rows"]
    dq = pd.Series(0.0, index=out.index)
    for c in important_cols:
        if c in out.columns:
            dq += out[c].notna().astype(float)
    dq = 35 + dq / len(important_cols) * 65
    out["data_quality_score"] = clip(dq)

    # 风险惩罚。
    penalty = pd.Series(0.0, index=out.index)
    penalty += np.where(margin >= 1000, 10, np.where(margin >= 500, 7, np.where(margin >= 100, 4, 0)))
    penalty += np.where(pub >= 300, 7, np.where(pub >= 100, 4, 0))
    penalty += np.where((one_lot > 0) & (one_lot <= 3), 3, 0)
    penalty += np.where(c_count >= 10, 3, 0)
    penalty += np.where(min20 <= -0.15, 8, 0)
    penalty += np.where(min60 <= -0.25, 7, 0)
    penalty += np.where(path.str.contains("升后破发|持续破发|弱势", na=False), 10, 0)
    penalty += np.where(safe_col(out, "quote_status", "").astype(str).eq("missing"), 6, 0)
    out["risk_penalty_score"] = pd.Series(np.clip(penalty, 0, 35), index=out.index)

    # 交易状态信号，便于人工读。
    out["buy_trigger_step8"] = np.select(
        [
            path.str.contains("上市即强势", na=False) & (to_num(out["post_listing_score"]) >= 72),
            path.str.contains("深V|修复|反弹", na=False) & (min20 < 0) & (max60 > 0.2),
            (d1 < 0) & (max20 > 0.08),
            (to_num(out["secondary_trade_score"]) if "secondary_trade_score" in out.columns else to_num(out["post_listing_score"])) >= 75,
        ],
        ["趋势确认：回踩不破首日VWAP/发行价可试仓", "深V确认：重新站回发行价后分批买入", "破发修复：站回发行价且成交放大后观察", "二级高分：趋势延续持有/试仓"],
        default="等待触发：不追高，观察发行价、首日VWAP和20D低点",
    )
    out["sell_trigger_step8"] = np.select(
        [
            path.str.contains("升后破发", na=False),
            min20 <= -0.15,
            (d1 >= 0.30) & (max20 <= d1 + 0.05),
            max20 >= 0.80,
        ],
        ["升后破发：反弹至发行价/首日VWAP附近减仓", "跌破发行价或20D低点：止损/降仓", "首日情绪强但后续不足：放量不创新高止盈", "短期涨幅过大：分批止盈并跟踪成交背离"],
        default="持仓风控：发行价、首日VWAP、20D低点为核心防线",
    )
    return out


def apply_weight_profile(df: pd.DataFrame, profile: dict, suffix: str) -> pd.Series:
    weights = profile.get("weights", profile)
    score = pd.Series(0.0, index=df.index)
    weight_sum = 0.0
    for col, w in weights.items():
        if col in df.columns:
            score += to_num(df[col]).fillna(0) * float(w)
            weight_sum += float(w)
    if weight_sum > 0:
        score = score / weight_sum
    return clip(score - to_num(safe_col(df, "risk_penalty_score")).fillna(0) * 0.55)


def add_scores_and_recommendations(df: pd.DataFrame, profiles: dict) -> pd.DataFrame:
    out = df.copy()
    for key, profile in profiles.items():
        out[f"score_{key}"] = apply_weight_profile(out, profile, key).round(1)
    # 默认用 balanced
    if "score_balanced" not in out.columns:
        out["score_balanced"] = apply_weight_profile(out, {}, "balanced").round(1)
    out["step8_score"] = out["score_balanced"]

    # 场景分数
    out["primary_score_step8"] = (
        to_num(out["issue_heat_score"]) * 0.28 + to_num(out["allocation_quality_score"]) * 0.15 + to_num(out["cornerstone_bank_score"]) * 0.22 + to_num(out["pricing_safety_score"]) * 0.22 + to_num(out["a1_maturity_score"]) * 0.08 + to_num(out["data_quality_score"]) * 0.05 - to_num(out["risk_penalty_score"]) * 0.45
    ).clip(0,100).round(1)
    out["secondary_score_step8"] = (
        to_num(out["gray_signal_score"]) * 0.24 + to_num(out["post_listing_score"]) * 0.48 + to_num(out["pricing_safety_score"]) * 0.08 + to_num(out["cornerstone_bank_score"]) * 0.08 + to_num(out["data_quality_score"]) * 0.12 - to_num(out["risk_penalty_score"]) * 0.55
    ).clip(0,100).round(1)
    out["cornerstone_score_step8"] = (
        to_num(out["cornerstone_bank_score"]) * 0.35 + to_num(out["pricing_safety_score"]) * 0.25 + to_num(out["a1_maturity_score"]) * 0.15 + to_num(out["issue_heat_score"]) * 0.10 + to_num(out["data_quality_score"]) * 0.15 - to_num(out["risk_penalty_score"]) * 0.50
    ).clip(0,100).round(1)

    final = to_num(out["step8_score"])
    path = safe_col(out, "path_label", "").fillna("").astype(str)
    quote_rows = to_num(safe_col(out, "quote_rows")).fillna(0)
    lifecycle = safe_col(out, "lifecycle_stage", "").fillna("").astype(str)

    out["decision_tier_step8"] = np.select(
        [final >= 78, final >= 65, final >= 52],
        ["A 高优先", "B 交易观察", "C 等触发"],
        default="D 回避/仅跟踪",
    )
    out["primary_recommendation_step8"] = np.select(
        [to_num(out["primary_score_step8"]) >= 78, to_num(out["primary_score_step8"]) >= 65, to_num(out["primary_score_step8"]) >= 52],
        ["强参与/积极争取额度", "小额参与/控制仓位", "只看二级/等待价格确认"],
        default="回避或仅跟踪",
    )
    out["cornerstone_recommendation_step8"] = np.select(
        [to_num(out["cornerstone_score_step8"]) >= 78, to_num(out["cornerstone_score_step8"]) >= 65, to_num(out["cornerstone_score_step8"]) >= 52],
        ["可谈基石/锚定，重点压估值和份额", "仅低价或小额锚定；严控锁定期风险", "不建议基石，除非估值显著让利"],
        default="不建议锁定",
    )
    out["secondary_recommendation_step8"] = np.select(
        [to_num(out["secondary_score_step8"]) >= 78, path.str.contains("深V|修复|反弹", na=False) & (to_num(out["secondary_score_step8"]) >= 62), path.str.contains("破发|弱势|升后破发", na=False), quote_rows <= 0],
        ["趋势确认买入/持有", "深V确认后分批买入", "破发弱势，回避或止损", "无行情：仅做发行阶段判断"],
        default="等待回踩发行价/VWAP后试仓",
    )
    out["stage_action_step8"] = np.select(
        [lifecycle.str.contains("申请|处理中", na=False) & quote_rows.eq(0), lifecycle.str.contains("招股|待上市", na=False), quote_rows.gt(0)],
        ["A1预筛：建档、跟踪聆讯和招股书", "招股期：根据一级分决定打新/锚定", "上市后：按二级状态机执行买卖点"],
        default="资料补全后再判断",
    )
    out["final_recommendation_step8"] = (
        "阶段：" + out["stage_action_step8"].astype(str)
        + "；一级：" + out["primary_recommendation_step8"].astype(str)
        + "；基石：" + out["cornerstone_recommendation_step8"].astype(str)
        + "；二级：" + out["secondary_recommendation_step8"].astype(str)
    )

    return out


def make_risk_tags(df: pd.DataFrame) -> pd.Series:
    result = []
    for _, r in df.iterrows():
        tags = []
        for col in ["risk_tags_step7", "risk_tags"]:
            v = r.get(col, "")
            if isinstance(v, str) and v and v != "nan":
                tags.extend([x.strip() for x in v.replace("；", ";").split(";") if x.strip()])
        def num(c): return pd.to_numeric(r.get(c, np.nan), errors="coerce")
        if num("risk_penalty_score") >= 18: tags.append("综合风险惩罚高")
        if num("margin_multiple") >= 500: tags.append("孖展极度拥挤")
        elif num("margin_multiple") >= 100: tags.append("孖展拥挤")
        if num("public_subscription_multiple") >= 100 or num("public_subscription_multiple_ballot") >= 100: tags.append("公开认购过热")
        if num("one_lot_success_rate_pct") <= 5 and pd.notna(num("one_lot_success_rate_pct")): tags.append("中签率极低")
        if num("min_20_ret") <= -0.15 or num("min_60_ret") <= -0.25: tags.append("上市后回撤大")
        if "升后破发" in str(r.get("path_label", "")): tags.append("升后破发")
        if str(r.get("quote_status", "")) == "missing": tags.append("免费行情缺失")
        if str(r.get("quote_status", "")) == "partial": tags.append("行情样本不足")
        if pd.notna(r.get("lockup_end_date", np.nan)) and str(r.get("lockup_end_date")) not in ("", "nan", "NaT"):
            tags.append("关注基石锁定期")
        seen=[]
        for t in tags:
            if t and t not in seen:
                seen.append(t)
        result.append("；".join(seen))
    return pd.Series(result, index=df.index)


def build_backtest(df: pd.DataFrame, score_col: str = "step8_score") -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    bt = df.copy()
    listed = bt[to_num(safe_col(bt, "quote_rows")).fillna(0) > 0].copy()
    if listed.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    listed[score_col] = to_num(listed[score_col])
    listed["target_tradeable_20d"] = (to_num(safe_col(listed, "max_20_ret")).fillna(-999) >= 0.15) & (to_num(safe_col(listed, "min_20_ret")).fillna(-999) > -0.25)
    listed["target_strong_or_deepv"] = safe_col(listed, "path_label", "").astype(str).str.contains("上市即强势|深V|反弹|修复", na=False)
    listed["target_bad_path"] = safe_col(listed, "path_label", "").astype(str).str.contains("破发|弱势|升后破发", na=False) | (to_num(safe_col(listed, "min_20_ret")).fillna(0) <= -0.20)
    listed["score_bucket"] = pd.cut(listed[score_col], bins=[-1, 52, 65, 78, 101], labels=["D", "C", "B", "A"], include_lowest=True)
    bucket = listed.groupby("score_bucket", observed=False).agg(
        样本数=("code", "count"),
        首日均值=("d1_close_ret", "mean"),
        二十日最大均值=("max_20_ret", "mean"),
        六十日最大均值=("max_60_ret", "mean"),
        一八零日最大均值=("max_180_ret", "mean"),
        二十日最小均值=("min_20_ret", "mean"),
        交易成功率=("target_tradeable_20d", "mean"),
        强势或深V率=("target_strong_or_deepv", "mean"),
        坏路径率=("target_bad_path", "mean"),
        平均分=(score_col, "mean"),
    ).reset_index()

    # 权重方案对比：每个方案A/B组表现。
    profile_rows = []
    for col in [c for c in df.columns if c.startswith("score_")]:
        temp = listed.copy()
        temp["bucket"] = pd.cut(to_num(temp[col]), bins=[-1, 52, 65, 78, 101], labels=["D", "C", "B", "A"], include_lowest=True)
        top = temp[temp["bucket"].isin(["A", "B"])]
        if top.empty:
            continue
        profile_rows.append({
            "profile": col.replace("score_", ""),
            "top_samples": len(top),
            "top_tradeable_20d_rate": top["target_tradeable_20d"].mean(),
            "top_strong_or_deepv_rate": top["target_strong_or_deepv"].mean(),
            "top_bad_path_rate": top["target_bad_path"].mean(),
            "top_d1_mean": to_num(top["d1_close_ret"]).mean(),
            "top_max20_mean": to_num(top["max_20_ret"]).mean(),
            "top_min20_mean": to_num(top["min_20_ret"]).mean(),
        })
    profiles = pd.DataFrame(profile_rows).sort_values("top_tradeable_20d_rate", ascending=False) if profile_rows else pd.DataFrame()

    # 因子诊断：分位数组效果 + 简单相关。
    factor_cols = ["issue_heat_score", "allocation_quality_score", "cornerstone_bank_score", "pricing_safety_score", "gray_signal_score", "post_listing_score", "a1_maturity_score", "data_quality_score", "risk_penalty_score"]
    diag_rows = []
    for f in factor_cols:
        if f not in listed.columns:
            continue
        ser = to_num(listed[f])
        top = listed[ser >= ser.quantile(0.75)] if ser.notna().sum() >= 10 else pd.DataFrame()
        bottom = listed[ser <= ser.quantile(0.25)] if ser.notna().sum() >= 10 else pd.DataFrame()
        diag_rows.append({
            "factor": f,
            "valid_samples": int(ser.notna().sum()),
            "corr_max20": ser.corr(to_num(listed["max_20_ret"])),
            "corr_min20": ser.corr(to_num(listed["min_20_ret"])),
            "top_quartile_samples": len(top),
            "top_quartile_tradeable_rate": top["target_tradeable_20d"].mean() if not top.empty else np.nan,
            "bottom_quartile_tradeable_rate": bottom["target_tradeable_20d"].mean() if not bottom.empty else np.nan,
            "top_minus_bottom": (top["target_tradeable_20d"].mean() - bottom["target_tradeable_20d"].mean()) if not top.empty and not bottom.empty else np.nan,
        })
    diag = pd.DataFrame(diag_rows)
    return bucket, profiles, diag


def update_inventory(data_dir: Path, outputs: list[tuple[str, str, int]]) -> pd.DataFrame:
    inv = read_csv(data_dir / "data_inventory.csv")
    rows = [{"source_name": n, "file_name": f, "raw_rows": r, "normalized_rows": r, "status": "已接入"} for n, f, r in outputs]
    new = pd.DataFrame(rows)
    if inv.empty:
        inv = new
    else:
        inv = inv[~inv["source_name"].isin(new["source_name"])]
        inv = pd.concat([inv, new], ignore_index=True)
    write_csv(inv, data_dir / "data_inventory.csv")
    return inv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="deploy_data")
    parser.add_argument("--config", default="config/step8_weight_profiles.json")
    args = parser.parse_args()
    data_dir = Path(args.data_dir)
    profiles = load_weight_profiles(Path(args.config))
    pool = prepare_pool(data_dir)
    scored = compute_factor_scores(pool)
    scored["risk_tags_step8"] = make_risk_tags(scored)
    scored = add_scores_and_recommendations(scored, profiles)
    write_csv(scored, data_dir / "ipo_decision_scored_step8.csv")

    bucket, profile_perf, diag = build_backtest(scored)
    write_csv(bucket, data_dir / "step8_backtest_score_buckets.csv")
    write_csv(profile_perf, data_dir / "step8_weight_profile_performance.csv")
    write_csv(diag, data_dir / "step8_factor_diagnostics.csv")
    watch_cols = [c for c in ["decision_tier_step8", "code", "name", "listing_date", "lifecycle_stage", "step8_score", "primary_score_step8", "cornerstone_score_step8", "secondary_score_step8", "primary_recommendation_step8", "cornerstone_recommendation_step8", "secondary_recommendation_step8", "buy_trigger_step8", "sell_trigger_step8", "risk_tags_step8"] if c in scored.columns]
    watch = scored.sort_values("step8_score", ascending=False)[watch_cols]
    write_csv(watch, data_dir / "step8_watchlist_actions.csv")
    update_inventory(data_dir, [
        ("Step8决策评分", "ipo_decision_scored_step8.csv", len(scored)),
        ("Step8分层回测", "step8_backtest_score_buckets.csv", len(bucket)),
        ("Step8因子诊断", "step8_factor_diagnostics.csv", len(diag)),
        ("Step8权重方案表现", "step8_weight_profile_performance.csv", len(profile_perf)),
    ])
    print("Saved Step8 outputs to", data_dir)
    print("Rows:", len(scored), "Backtest buckets:", len(bucket), "Diagnostics:", len(diag))


if __name__ == "__main__":
    main()
