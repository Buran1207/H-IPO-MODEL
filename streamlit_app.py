from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import numpy as np
import pandas as pd
import streamlit as st

BASE = Path("deploy_data")
CONFIG = Path("config/weight_profiles.json")

st.set_page_config(page_title="港股 IPO / 半新股投资决策系统", layout="wide")


def read_csv_any(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    for enc in ("utf-8-sig", "utf-8", "gb18030", "big5"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path)


def to_num(x):
    return pd.to_numeric(x, errors="coerce")


def fmt_pct(x):
    if pd.isna(x) or x == "":
        return ""
    try:
        return f"{float(x):.1%}"
    except Exception:
        return str(x)


def fmt_pct_raw(x):
    """For columns already stored as 12.3 meaning 12.3%."""
    if pd.isna(x) or x == "":
        return ""
    try:
        return f"{float(x):.1f}%"
    except Exception:
        return str(x)


def fmt_num(x, digits=1):
    if pd.isna(x) or x == "":
        return ""
    try:
        return f"{float(x):,.{digits}f}"
    except Exception:
        return str(x)


def fmt_money(x):
    if pd.isna(x) or x == "":
        return ""
    try:
        x = float(x)
        if abs(x) >= 1e9:
            return f"HK${x/1e9:.1f}bn"
        if abs(x) >= 1e8:
            return f"HK${x/1e8:.1f}亿"
        if abs(x) >= 1e4:
            return f"HK${x/1e4:.1f}万"
        return f"HK${x:.0f}"
    except Exception:
        return str(x)


TEXT = {
    "中文": {
        "app_title": "港股 IPO / 半新股投资决策系统",
        "caption": "覆盖 A1 项目、招股期、暗盘/首日、上市后0-180日、解禁与供给压力的全生命周期决策框架。",
        "language": "语言 / Language",
        "profile": "权重方案",
        "min_score": "最低综合分",
        "stage": "生命周期阶段",
        "rating": "综合评级",
        "industry": "行业",
        "search": "搜索代码/名称",
        "download": "下载当前表",
        "empty": "暂无数据",
        "pages": {
            "dashboard": "① 决策总览",
            "a1": "② A1项目观察池",
            "ipo": "③ 招股期参与决策",
            "gray": "④ 暗盘与首日交易",
            "post": "⑤ 半新股交易状态机",
            "lockup": "⑥ 解禁与供给压力",
            "weights": "⑦ 评分标准与权重设置",
            "backtest": "⑧ 回测与有效性验证",
            "memo": "⑨ 单票投资备忘录",
            "quality": "⑩ 数据质量",
        },
        "metric_total": "样本数",
        "metric_a1": "A1/申请项目",
        "metric_listed": "已上市/半新股",
        "metric_high_lockup": "90日内中高解禁压力",
        "metric_avg": "平均综合分",
        "decision_pool": "决策池",
        "standards": "评判标准",
        "custom_weights": "自定义权重",
        "effectiveness": "有效性验证",
        "memo_title": "单票投资备忘录",
        "data_quality": "数据接入与质量",
        "export_memo": "下载 Memo",
        "live_score": "按当前权重重算的排序",
    },
    "English": {
        "app_title": "HK IPO & Newly Listed Equity Decision System",
        "caption": "A full lifecycle decision framework covering A1 filings, IPO subscription, gray market/first day, post-listing 0-180D trading and lock-up pressure.",
        "language": "Language / 语言",
        "profile": "Weight Profile",
        "min_score": "Minimum Score",
        "stage": "Lifecycle Stage",
        "rating": "Rating",
        "industry": "Industry",
        "search": "Search code/name",
        "download": "Download table",
        "empty": "No data",
        "pages": {
            "dashboard": "① Decision Dashboard",
            "a1": "② A1 Project Watchlist",
            "ipo": "③ IPO Participation Decision",
            "gray": "④ Gray Market & First Day",
            "post": "⑤ Post-listing Trading State Machine",
            "lockup": "⑥ Lock-up & Supply Pressure",
            "weights": "⑦ Scoring Standards & Weights",
            "backtest": "⑧ Backtest & Effectiveness",
            "memo": "⑨ Single-name Investment Memo",
            "quality": "⑩ Data Quality",
        },
        "metric_total": "Samples",
        "metric_a1": "A1 / Filing projects",
        "metric_listed": "Listed / Newly listed",
        "metric_high_lockup": "Medium/High lock-up pressure within 90D",
        "metric_avg": "Avg. score",
        "decision_pool": "Decision Pool",
        "standards": "Scoring Standards",
        "custom_weights": "Custom Weights",
        "effectiveness": "Effectiveness Review",
        "memo_title": "Single-name Investment Memo",
        "data_quality": "Data Coverage & Quality",
        "export_memo": "Download Memo",
        "live_score": "Ranking recalculated with current weights",
    },
}

COL_ZH = {
    "code": "代码", "temp_code": "临时代码", "name": "简称", "listing_date": "上市日", "application_date": "申请日",
    "first_application_date": "首次申请日", "hearing_date": "通过聆讯日", "application_status": "申请状态",
    "lifecycle_stage": "阶段", "industry_level_1": "行业一级", "industry_level_2": "行业二级", "sponsor": "保荐人",
    "overall_coordinator": "整体协调人", "issue_price": "发行价", "offer_price_low": "招股价下限", "offer_price_high": "招股价上限",
    "market_cap_hkdm": "上市市值", "gross_proceeds_hkd": "募资额", "public_subscription_multiple": "公开认购倍数",
    "public_subscription_multiple_ballot": "公开认购倍数", "one_lot_success_rate_pct": "一手中签率", "margin_multiple": "孖展倍数",
    "margin_amount_hkd": "孖展金额", "cornerstone_count": "基石数量", "cornerstone_amount_hkd": "基石金额",
    "cornerstone_top_names": "主要基石", "top_underwriters": "承销团", "top_bookrunners": "账簿管理人",
    "gray_open_ret_pct": "暗盘开盘", "gray_close_ret_pct": "暗盘收盘", "gray_amount_10k_hkd": "暗盘成交额(万港元)",
    "d1_open_ret_pct": "首日开盘", "d1_close_ret_pct": "首日收盘", "d1_close_ret": "首日收盘收益",
    "max_20_ret": "20D最大涨幅", "min_20_ret": "20D最大压力", "max_60_ret": "60D最大涨幅", "min_60_ret": "60D最大压力",
    "max_180_ret": "180D最大涨幅", "min_180_ret": "180D最大压力", "path_label": "路径", "quote_status": "行情状态",
    "quote_rows": "行情行数", "quote_source": "行情来源", "overall_score": "综合分", "primary_score": "一级分", "secondary_score": "二级分",
    "cornerstone_score": "基石分", "a1_score": "A1预筛分", "investment_tier_cn": "综合评级", "a1_priority_cn": "A1优先级",
    "primary_recommendation": "一级建议", "cornerstone_recommendation": "基石/锚定建议", "secondary_recommendation": "二级建议",
    "buy_trigger": "买入触发", "sell_trigger": "卖点/风控", "risk_tags_model": "风险标签", "next_unlock_date": "下一解禁日",
    "days_to_unlock": "距离天数", "next_unlock_type_cn": "解禁类型", "lockup_pressure_cn": "解禁压力", "lockup_action_cn": "解禁提示",
    "cornerstone_value_to_avg20_turnover": "基石金额/20日成交额", "avg20_trading_value_hkd_est": "20日均成交额估算", "business_scope": "业务简介",
    "use_of_proceeds": "募资用途", "a1_action_cn": "A1动作", "first_day_action_cn": "暗盘/首日动作", "custom_score": "自定义分",
    "custom_tier_cn": "自定义评级",
    "a1_quality_score": "A1项目质量分", "a1_industry_preference_score": "行业与港股偏好", "a1_company_quality_score": "公司稀缺性/基本面",
    "a1_sponsor_quality_score": "保荐/中介质量", "a1_peer_ipo_score": "历史同类IPO", "a1_tradability_score": "未来交易可做性", "a1_market_window_score": "市场窗口",
    "a1_research_priority_cn": "研究优先级", "future_ipo_participation_cn": "未来IPO参与倾向", "current_investment_status_cn": "当前投资状态",
    "next_action_cn": "下一动作", "filing_count": "递表次数", "latest_application_date_calc": "最近申请日", "first_application_date_calc": "首次申请日",
    "has_lapsed_history": "曾失效", "status_note_cn": "状态提示", "a1_positive_reasons_cn": "加分原因", "a1_negative_reasons_cn": "扣分原因",
}
COL_EN = {
    "code": "Code", "temp_code": "Temp Code", "name": "Name", "listing_date": "Listing Date", "application_date": "Application Date",
    "first_application_date": "First Filing Date", "hearing_date": "Hearing Date", "application_status": "Application Status",
    "lifecycle_stage": "Stage", "industry_level_1": "Sector L1", "industry_level_2": "Sector L2", "sponsor": "Sponsor",
    "overall_coordinator": "Overall Coordinator", "issue_price": "Issue Price", "offer_price_low": "Offer Low", "offer_price_high": "Offer High",
    "market_cap_hkdm": "Market Cap", "gross_proceeds_hkd": "Gross Proceeds", "public_subscription_multiple": "Public Subscription Multiple",
    "public_subscription_multiple_ballot": "Public Subscription Multiple", "one_lot_success_rate_pct": "One-lot Success Rate", "margin_multiple": "Margin Multiple",
    "margin_amount_hkd": "Margin Amount", "cornerstone_count": "Cornerstone Count", "cornerstone_amount_hkd": "Cornerstone Amount",
    "cornerstone_top_names": "Major Cornerstones", "top_underwriters": "Underwriters", "top_bookrunners": "Bookrunners",
    "gray_open_ret_pct": "Gray Open", "gray_close_ret_pct": "Gray Close", "gray_amount_10k_hkd": "Gray Turnover (HKD 10k)",
    "d1_open_ret_pct": "D1 Open", "d1_close_ret_pct": "D1 Close", "d1_close_ret": "D1 Close Return",
    "max_20_ret": "20D Max Upside", "min_20_ret": "20D Max Pressure", "max_60_ret": "60D Max Upside", "min_60_ret": "60D Max Pressure",
    "max_180_ret": "180D Max Upside", "min_180_ret": "180D Max Pressure", "path_label": "Path", "quote_status": "Quote Status",
    "quote_rows": "Quote Rows", "quote_source": "Quote Source", "overall_score": "Overall Score", "primary_score": "Primary Score", "secondary_score": "Secondary Score",
    "cornerstone_score": "Cornerstone Score", "a1_score": "A1 Score", "investment_tier_en": "Rating", "a1_priority_en": "A1 Priority",
    "primary_recommendation": "Primary Recommendation", "cornerstone_recommendation": "Cornerstone / Anchor Recommendation", "secondary_recommendation": "Secondary Recommendation",
    "buy_trigger": "Buy Trigger", "sell_trigger": "Sell / Risk Control", "risk_tags_model": "Risk Tags", "next_unlock_date": "Next Unlock Date",
    "days_to_unlock": "Days to Unlock", "next_unlock_type_en": "Unlock Type", "lockup_pressure_en": "Lock-up Pressure", "lockup_action_en": "Lock-up Action",
    "cornerstone_value_to_avg20_turnover": "Cornerstone / Avg 20D Trading Value", "avg20_trading_value_hkd_est": "Avg 20D Trading Value Est.", "business_scope": "Business Scope",
    "use_of_proceeds": "Use of Proceeds", "a1_action_en": "A1 Action", "first_day_action_en": "Gray / First-day Action", "custom_score": "Custom Score",
    "custom_tier_en": "Custom Rating",
    "a1_quality_score": "A1 Project Quality Score", "a1_industry_preference_score": "Sector & HK Market Preference", "a1_company_quality_score": "Scarcity / Fundamental Potential",
    "a1_sponsor_quality_score": "Sponsor / Intermediary Quality", "a1_peer_ipo_score": "Comparable IPO Performance", "a1_tradability_score": "Future Tradability", "a1_market_window_score": "Market Window",
    "a1_research_priority_en": "Research Priority", "future_ipo_participation_en": "Future IPO Participation Bias", "current_investment_status_en": "Current Investment Status",
    "next_action_en": "Next Action", "filing_count": "Filing Count", "latest_application_date_calc": "Latest Filing Date", "first_application_date_calc": "First Filing Date",
    "has_lapsed_history": "Had Lapsed Filing", "status_note_en": "Status Note", "a1_positive_reasons_en": "Positive Reasons", "a1_negative_reasons_en": "Negative Reasons",
}


def tr(lang: str, key: str):
    return TEXT[lang].get(key, key)


def make_unique_columns(columns: list[str]) -> list[str]:
    """Streamlit/pyarrow cannot render dataframes with duplicate column names.
    Some bilingual labels intentionally map related raw fields to the same display name
    (for example two versions of public subscription multiple). Add a short suffix
    only when duplicates appear.
    """
    seen: dict[str, int] = {}
    out: list[str] = []
    for col in columns:
        base = str(col)
        if base not in seen:
            seen[base] = 0
            out.append(base)
        else:
            seen[base] += 1
            out.append(f"{base} ({seen[base] + 1})")
    return out


def label_cols(df: pd.DataFrame, lang: str) -> pd.DataFrame:
    mapping = COL_ZH if lang == "中文" else COL_EN
    out = df.copy()
    out = out.rename(columns={c: mapping.get(c, c) for c in out.columns})
    out.columns = make_unique_columns(list(out.columns))
    return out


@st.cache_data(show_spinner=False)
def load_all():
    pool = read_csv_any(BASE / "ipo_investment_decision_scored.csv")
    if pool.empty:
        pool = read_csv_any(BASE / "ipo_decision_pool.csv")
    paths = read_csv_any(BASE / "ipo_post_listing_paths.csv")
    quotes = read_csv_any(BASE / "ipo_daily_quotes_180d.csv")
    inventory = read_csv_any(BASE / "data_inventory.csv")
    buckets = read_csv_any(BASE / "investment_backtest_score_buckets.csv")
    profile_perf = read_csv_any(BASE / "investment_weight_profile_performance.csv")
    diag = read_csv_any(BASE / "investment_factor_diagnostics.csv")
    weight_profiles = {}
    if CONFIG.exists():
        try:
            weight_profiles = json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception:
            weight_profiles = {}
    return pool, paths, quotes, inventory, buckets, profile_perf, diag, weight_profiles




def normalize_name_value(x) -> str:
    if pd.isna(x):
        return ""
    s = str(x).strip()
    for suf in ["-W", "-B", "－W", "－B", "股份有限公司", "有限公司", "控股", "集团", "科技", "股份"]:
        s = s.replace(suf, "")
    return s.replace(" ", "").replace("（", "(").replace("）", ")")


def safe_date_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col in df.columns:
        return pd.to_datetime(df[col], errors="coerce")
    return pd.Series(pd.NaT, index=df.index)


def is_unlisted_row(df: pd.DataFrame) -> pd.Series:
    """A1 watchlist includes companies not yet listed; already listed companies are removed."""
    listing = safe_date_series(df, "listing_date")
    today = pd.Timestamp.today().normalize()
    return listing.isna() | (listing > today)


def status_is_lapsed(status: object) -> bool:
    s = "" if pd.isna(status) else str(status)
    return any(k in s for k in ["失效", "撤回", "被拒", "终止", "不予"])


def status_rank(status: object) -> int:
    s = "" if pd.isna(status) else str(status)
    if any(k in s for k in ["招股", "待上市", "定价", "配售"]): return 60
    if any(k in s for k in ["通过聆讯", "聆讯后"]): return 55
    if any(k in s for k in ["处理中", "递表"]): return 45
    if status_is_lapsed(s): return 20
    return 35


def split_names(text: object) -> list[str]:
    if pd.isna(text):
        return []
    s = str(text)
    for sep in ["；", ";", "、", ",", "，", "/", "及"]:
        s = s.replace(sep, "|")
    return [x.strip() for x in s.split("|") if x.strip() and x.strip() != "--"]


def score_from_rank_pct(x, default=50):
    if pd.isna(x):
        return default
    return float(np.clip(30 + 70 * x, 0, 100))


def build_a1_quality_scores(df: pd.DataFrame, weights: dict[str, float] | None = None) -> pd.DataFrame:
    """Build A1 project-quality scores. Application status is not part of the quality score."""
    out = df.copy()
    if weights is None:
        weights = {
            "industry": 35,
            "company": 20,
            "sponsor": 15,
            "peer": 15,
            "tradability": 10,
            "market": 5,
        }
    total_w = sum(float(v) for v in weights.values()) or 1

    listed = out[~is_unlisted_row(out)].copy()
    # Base listed-performance score for peer/sponsor history.
    perf = pd.Series(50.0, index=listed.index)
    if "d1_close_ret" in listed.columns:
        perf += to_num(listed["d1_close_ret"]).fillna(0).clip(-0.5, 1.0) * 25
    if "max_20_ret" in listed.columns:
        perf += to_num(listed["max_20_ret"]).fillna(0).clip(-0.5, 2.0) * 20
    if "min_20_ret" in listed.columns:
        perf += to_num(listed["min_20_ret"]).fillna(0).clip(-1.0, 0.2) * 15
    if "post_listing_score" in listed.columns:
        perf = perf * 0.45 + to_num(listed["post_listing_score"]).fillna(50) * 0.55
    perf = perf.clip(0, 100)
    listed = listed.assign(_perf=perf)

    # Industry score: mainly from same-sector listed results, with small keyword priors.
    industry_score_map = {}
    if "industry_level_1" in listed.columns and not listed.empty:
        industry_score_map = listed.groupby("industry_level_1")["_perf"].mean().to_dict()
    ind = out.get("industry_level_1", pd.Series("", index=out.index)).astype(str)
    ind_score = ind.map(industry_score_map).fillna(55.0)
    hot_keywords = ["机器人", "人工智能", "AI", "半导体", "医疗器械", "创新药", "生物科技", "特专科技", "新能源", "算力", "云", "软件"]
    weak_keywords = ["物业", "建筑", "传统", "纺织", "餐饮", "煤", "钢", "建材"]

    def safe_text(value) -> str:
        """Convert pandas/pyarrow missing values to a normal string before keyword matching."""
        try:
            if pd.isna(value):
                return ""
        except Exception:
            pass
        return str(value)

    def contains_any(value, keywords: list[str]) -> bool:
        text = safe_text(value)
        return any(k in text for k in keywords)

    all_text = (
        out.get("industry_level_1", pd.Series("", index=out.index)).map(safe_text)
        + " "
        + out.get("industry_level_2", pd.Series("", index=out.index)).map(safe_text)
        + " "
        + out.get("business_scope", pd.Series("", index=out.index)).map(safe_text)
        + " "
        + out.get("company_profile", pd.Series("", index=out.index)).map(safe_text)
    )
    ind_score = (
        ind_score
        + all_text.map(lambda s: 8 if contains_any(s, hot_keywords) else 0)
        - all_text.map(lambda s: 6 if contains_any(s, weak_keywords) else 0)
    )
    out["a1_industry_preference_score"] = ind_score.clip(0, 100).round(1)

    # Company quality proxy: use business/profile language and information completeness. This is a proxy before analyst overrides are introduced.
    profile = (
        out.get("business_scope", pd.Series("", index=out.index)).map(safe_text)
        + " "
        + out.get("company_profile", pd.Series("", index=out.index)).map(safe_text)
    )
    pos_words = ["领先", "龙头", "第一", "最大", "唯一", "稀缺", "全球", "行业排名", "自主研发", "核心技术", "商业化", "高增长"]
    neg_words = ["依赖", "亏损", "诉讼", "处罚", "客户集中", "供应商集中", "现金流", "资不抵债"]
    comp_score = pd.Series(50.0, index=out.index)
    comp_score += profile.map(lambda s: min(25, sum(1 for k in pos_words if k in s) * 5))
    comp_score -= profile.map(lambda s: min(20, sum(1 for k in neg_words if k in s) * 5))
    comp_score += profile.str.len().fillna(0).clip(0, 5000) / 5000 * 10
    out["a1_company_quality_score"] = comp_score.clip(0, 100).round(1)

    # Sponsor / intermediary quality: based on historical listed outcomes for matching sponsors/coordinators.
    sponsor_perf = {}
    if not listed.empty:
        for _, r in listed.iterrows():
            names = split_names(r.get("sponsor")) + split_names(r.get("overall_coordinator")) + split_names(r.get("top_bookrunners"))
            for n in names:
                sponsor_perf.setdefault(n, []).append(float(r.get("_perf", 50)))
    sponsor_avg = {k: float(np.mean(v)) for k, v in sponsor_perf.items() if v}
    strong_house = ["中金", "高盛", "摩根", "J.P. Morgan", "JP Morgan", "摩根士丹利", "美银", "花旗", "瑞银", "中信", "华泰", "海通", "中银", "招银", "建银"]
    def sponsor_score_row(r):
        names = split_names(r.get("sponsor")) + split_names(r.get("overall_coordinator"))
        vals = [sponsor_avg[n] for n in names if n in sponsor_avg]
        base = float(np.mean(vals)) if vals else 52.0
        joined = " ".join(names)
        if any(k in joined for k in strong_house):
            base += 6
        if not names:
            base -= 8
        return float(np.clip(base, 0, 100))
    out["a1_sponsor_quality_score"] = out.apply(sponsor_score_row, axis=1).round(1)

    # Peer IPO score: same industry and same broad board/type history.
    peer_score = ind.map(industry_score_map).fillna(55.0)
    if "board" in out.columns and "board" in listed.columns and not listed.empty:
        board_map = listed.groupby("board")["_perf"].mean().to_dict()
        peer_score = peer_score * 0.75 + out["board"].map(board_map).fillna(55.0) * 0.25
    out["a1_peer_ipo_score"] = peer_score.clip(0, 100).round(1)

    # Future tradability: expected attention/liquidity. Use available deal size if any, otherwise sector/sponsor proxy.
    trad = pd.Series(50.0, index=out.index)
    mcap = to_num(out.get("market_cap_hkdm", pd.Series(np.nan, index=out.index)))
    proceeds = to_num(out.get("gross_proceeds_hkd", pd.Series(np.nan, index=out.index)))
    trad += out["a1_industry_preference_score"].fillna(50).sub(50) * 0.25
    trad += out["a1_sponsor_quality_score"].fillna(50).sub(50) * 0.15
    # If market cap exists in HKD million, reward medium-sized deals; penalize extremely large/small.
    trad += mcap.apply(lambda x: 12 if pd.notna(x) and 2000 <= x <= 50000 else (5 if pd.notna(x) and 500 <= x < 2000 else (-8 if pd.notna(x) and x > 100000 else 0)))
    trad += proceeds.apply(lambda x: 8 if pd.notna(x) and 5e8 <= x <= 1.0e10 else (-6 if pd.notna(x) and x > 3.0e10 else 0))
    out["a1_tradability_score"] = trad.clip(0, 100).round(1)

    # Market window: recent IPO market state, same for all rows.
    recent = listed.copy()
    if "listing_date" in recent.columns:
        recent["listing_date"] = pd.to_datetime(recent["listing_date"], errors="coerce")
        recent = recent.sort_values("listing_date").tail(20)
    if not recent.empty:
        wins = (to_num(recent.get("d1_close_ret", pd.Series(np.nan, index=recent.index))) > 0).mean()
        avg20 = to_num(recent.get("max_20_ret", pd.Series(np.nan, index=recent.index))).mean()
        market_window = float(np.clip(40 + wins * 35 + (0 if pd.isna(avg20) else avg20 * 40), 0, 100))
    else:
        market_window = 55.0
    out["a1_market_window_score"] = round(market_window, 1)

    score = (
        out["a1_industry_preference_score"] * float(weights.get("industry", 0)) +
        out["a1_company_quality_score"] * float(weights.get("company", 0)) +
        out["a1_sponsor_quality_score"] * float(weights.get("sponsor", 0)) +
        out["a1_peer_ipo_score"] * float(weights.get("peer", 0)) +
        out["a1_tradability_score"] * float(weights.get("tradability", 0)) +
        out["a1_market_window_score"] * float(weights.get("market", 0))
    ) / total_w
    out["a1_quality_score"] = score.round(1)

    def pr_cn(x):
        if pd.isna(x): return "信息不足"
        if x >= 80: return "A 重点跟踪"
        if x >= 70: return "B+ 重点研究"
        if x >= 60: return "B 研究池"
        if x >= 50: return "C 观察"
        return "D 低优先级"
    def pr_en(x):
        if pd.isna(x): return "Insufficient data"
        if x >= 80: return "A High-priority watch"
        if x >= 70: return "B+ Priority research"
        if x >= 60: return "B Research pool"
        if x >= 50: return "C Monitor"
        return "D Low priority"
    def tendency_cn(x):
        if pd.isna(x): return "等待资料"
        if x >= 80: return "拟重点参与，等待发行验证"
        if x >= 70: return "倾向参与，需看定价"
        if x >= 60: return "可参与，需强发行信号"
        if x >= 50: return "暂不主动参与"
        return "暂不参与"
    def tendency_en(x):
        if pd.isna(x): return "Wait for data"
        if x >= 80: return "Likely priority participation, pending deal validation"
        if x >= 70: return "Positive bias, subject to pricing"
        if x >= 60: return "Participate only with strong deal signals"
        if x >= 50: return "No proactive participation"
        return "No participation"
    out["a1_research_priority_cn"] = out["a1_quality_score"].map(pr_cn)
    out["a1_research_priority_en"] = out["a1_quality_score"].map(pr_en)
    out["future_ipo_participation_cn"] = out["a1_quality_score"].map(tendency_cn)
    out["future_ipo_participation_en"] = out["a1_quality_score"].map(tendency_en)

    reasons_add, reasons_sub = [], []
    for _, r in out.iterrows():
        adds, subs = [], []
        if r.get("a1_industry_preference_score", 50) >= 70: adds.append("行业/港股偏好较强")
        if r.get("a1_company_quality_score", 50) >= 70: adds.append("公司稀缺性或业务表述较强")
        if r.get("a1_sponsor_quality_score", 50) >= 65: adds.append("保荐/中介质量较好")
        if r.get("a1_peer_ipo_score", 50) >= 65: adds.append("历史同类IPO表现较好")
        if r.get("a1_industry_preference_score", 50) < 45: subs.append("行业在港股新股市场偏弱")
        if r.get("a1_company_quality_score", 50) < 45: subs.append("公司稀缺性/基本面信息不足")
        if r.get("a1_sponsor_quality_score", 50) < 45: subs.append("中介历史表现或信息不足")
        if not adds: adds.append("暂无明显结构性加分项")
        if not subs: subs.append("主要扣分来自资料未完整披露前的不确定性")
        reasons_add.append("；".join(adds[:3])); reasons_sub.append("；".join(subs[:3]))
    out["a1_positive_reasons_cn"] = reasons_add
    out["a1_negative_reasons_cn"] = reasons_sub
    out["a1_positive_reasons_en"] = out["a1_positive_reasons_cn"]
    out["a1_negative_reasons_en"] = out["a1_negative_reasons_cn"]
    return out


def add_current_status(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    today = pd.Timestamp.today().normalize()
    listing = safe_date_series(out, "listing_date")
    unlisted = listing.isna() | (listing > today)
    status = out.get("application_status", pd.Series("", index=out.index)).astype(str)
    issue = to_num(out.get("issue_price", pd.Series(np.nan, index=out.index))).notna()
    offer = to_num(out.get("offer_price_high", pd.Series(np.nan, index=out.index))).notna() | out.get("offer_start_date", pd.Series(np.nan, index=out.index)).notna()
    gray = out.get("gray_close_ret_pct", pd.Series(np.nan, index=out.index)).notna() | out.get("d1_close_ret", pd.Series(np.nan, index=out.index)).notna()
    path = out.get("path_label", pd.Series("", index=out.index)).notna()
    lock_high = out.get("lockup_pressure_cn", pd.Series("", index=out.index)).isin(["高", "中"])
    cn, en, action_cn, action_en = [], [], [], []
    for i, r in out.iterrows():
        stt = str(r.get("application_status", ""))
        li = pd.to_datetime(r.get("listing_date"), errors="coerce")
        is_unlisted = pd.isna(li) or li > today
        if is_unlisted and status_is_lapsed(stt):
            cn.append("C6 失效观察"); en.append("C6 Lapsed filing watch")
            action_cn.append("等待是否重新递表/更新财务资料，保留在未上市项目池")
            action_en.append("Wait for refiling / updated financials; keep in unlisted project pool")
        elif is_unlisted and not (pd.notna(r.get("issue_price")) or pd.notna(r.get("offer_price_high"))):
            cn.append("C1 等待发行资料"); en.append("C1 Wait for deal terms")
            action_cn.append("等待招股价区间、发行规模、基石和账簿热度")
            action_en.append("Wait for offer range, deal size, cornerstone and bookbuilding signals")
        elif is_unlisted and (pd.notna(r.get("issue_price")) or pd.notna(r.get("offer_price_high"))) and pd.isna(r.get("gray_close_ret_pct")):
            cn.append("C2 等待配发/暗盘"); en.append("C2 Wait for allotment / gray market")
            action_cn.append("等待配发结果、孖展/中签和暗盘确认")
            action_en.append("Wait for allotment, margin/ballot and gray-market confirmation")
        elif is_unlisted:
            cn.append("C3 等待上市确认"); en.append("C3 Wait for listing confirmation")
            action_cn.append("不追高，等待首日价格和成交确认")
            action_en.append("Do not chase; wait for first-day price and turnover confirmation")
        elif bool(lock_high.loc[i]) if i in lock_high.index else False:
            cn.append("C5 等待风险释放"); en.append("C5 Wait for risk release")
            action_cn.append("解禁或供给压力进入观察窗口，降低追高权重")
            action_en.append("Lock-up/supply pressure in watch window; reduce chasing weight")
        elif pd.notna(r.get("path_label")):
            sc = r.get("secondary_score")
            if pd.notna(sc) and float(sc) >= 65:
                cn.append("B 二级交易观察"); en.append("B Secondary trading watch")
                action_cn.append("等待回踩/趋势确认触发买点")
                action_en.append("Wait for pullback / trend confirmation trigger")
            else:
                cn.append("C4 等待二级买点"); en.append("C4 Wait for secondary entry")
                action_cn.append("不追高，等待深V、站回发行价或成交确认")
                action_en.append("Do not chase; wait for deep-V, reclaim of issue price or turnover confirmation")
        else:
            base = r.get("investment_tier_cn", "")
            if isinstance(base, str) and base.startswith("A"):
                cn.append("A 重点参与"); en.append("A Priority participate")
                action_cn.append("进入重点额度/交易讨论")
                action_en.append("Move to priority allocation / trading discussion")
            elif isinstance(base, str) and base.startswith("D"):
                cn.append("D 回避/仅跟踪"); en.append("D Avoid / track only")
                action_cn.append("不主动参与，保留复盘")
                action_en.append("No active participation; keep for review")
            else:
                cn.append("C4 等待二级买点"); en.append("C4 Wait for secondary entry")
                action_cn.append("等待价格、成交或风险释放")
                action_en.append("Wait for price, turnover or risk release")
    out["current_investment_status_cn"] = cn
    out["current_investment_status_en"] = en
    out["next_action_cn"] = action_cn
    out["next_action_en"] = action_en
    return out


def build_a1_company_view(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return one-row-per-company A1 watchlist and application history. Already-listed companies are removed."""
    d = df.copy()
    today = pd.Timestamp.today().normalize()
    listing = safe_date_series(d, "listing_date")
    # Only unlisted: no listing date or future scheduled listing date.
    d = d[listing.isna() | (listing > today)].copy()
    # Must have at least application info / temp code / status to be considered A1 pipeline.
    has_app = safe_date_series(d, "application_date").notna() | d.get("application_status", pd.Series("", index=d.index)).notna() | d.get("temp_code", pd.Series("", index=d.index)).notna()
    d = d[has_app].copy()
    if d.empty:
        return d, d
    name_key = d.get("name", pd.Series("", index=d.index)).fillna("").map(normalize_name_value)
    alt_key = d.get("company_chinese_name", pd.Series("", index=d.index)).fillna("").map(normalize_name_value)
    d["company_key"] = name_key.where(name_key != "", alt_key)
    d["company_key"] = d["company_key"].where(d["company_key"] != "", d.get("temp_code", pd.Series("", index=d.index)).astype(str))
    d["application_date_dt"] = safe_date_series(d, "application_date")
    d["status_rank"] = d.get("application_status", pd.Series("", index=d.index)).map(status_rank)
    d["_latest_sort"] = d["application_date_dt"].fillna(pd.Timestamp("1900-01-01"))
    history = d.sort_values(["company_key", "application_date_dt", "status_rank"], ascending=[True, False, False]).copy()
    counts = history.groupby("company_key").agg(
        filing_count=("company_key", "size"),
        first_application_date_calc=("application_date_dt", "min"),
        latest_application_date_calc=("application_date_dt", "max"),
        has_lapsed_history=("application_status", lambda s: any(status_is_lapsed(x) for x in s)),
    )
    latest_idx = history.sort_values(["company_key", "application_date_dt", "status_rank"], ascending=[True, False, False]).groupby("company_key").head(1).index
    latest = history.loc[latest_idx].copy().set_index("company_key")
    latest = latest.join(counts, how="left").reset_index()
    latest["filing_count"] = latest["filing_count"].fillna(1).astype(int)
    latest["first_application_date_calc"] = pd.to_datetime(latest["first_application_date_calc"], errors="coerce")
    latest["latest_application_date_calc"] = pd.to_datetime(latest["latest_application_date_calc"], errors="coerce")
    latest["has_lapsed_history"] = latest["has_lapsed_history"].fillna(False)
    latest["status_note_cn"] = latest.apply(lambda r: ("曾失效后重新递表" if bool(r.get("has_lapsed_history")) and int(r.get("filing_count",1)) >= 2 and not status_is_lapsed(r.get("application_status")) else ("最新申请失效，等待是否重新递表" if status_is_lapsed(r.get("application_status")) else ("多次递表，需关注前次问询/财务更新" if int(r.get("filing_count",1)) >= 2 else "申请进展正常跟踪"))), axis=1)
    latest["status_note_en"] = latest.apply(lambda r: ("Refiled after lapse" if bool(r.get("has_lapsed_history")) and int(r.get("filing_count",1)) >= 2 and not status_is_lapsed(r.get("application_status")) else ("Latest filing lapsed; wait for refiling" if status_is_lapsed(r.get("application_status")) else ("Multiple filings; check previous questions / financial updates" if int(r.get("filing_count",1)) >= 2 else "Normal filing progress tracking"))), axis=1)
    return latest, history


def enrich_dynamic(df: pd.DataFrame, quotes: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in ["listing_date", "application_date", "first_application_date", "hearing_date", "lockup_end_date", "next_unlock_date", "cornerstone_unlock_date", "controller_first_window_date", "controller_second_window_date"]:
        if c in out.columns:
            out[c] = pd.to_datetime(out[c], errors="coerce")
    for c in ["overall_score", "primary_score", "secondary_score", "cornerstone_score", "a1_score", "cornerstone_amount_hkd", "cornerstone_count", "avg20_trading_value_hkd_est", "max_180_ret", "max_60_ret", "d1_close_ret"]:
        if c in out.columns:
            out[c] = to_num(out[c])

    # Re-estimate avg 20D trading value from quotes if available.
    if not quotes.empty and {"code", "close", "volume"}.issubset(quotes.columns):
        q = quotes.copy()
        q["date"] = pd.to_datetime(q.get("date"), errors="coerce")
        q["close"] = to_num(q["close"])
        q["volume"] = to_num(q["volume"])
        q["trading_value_hkd_est"] = q["close"] * q["volume"]
        avg = q.sort_values(["code", "date"]).groupby("code").tail(20).groupby("code")["trading_value_hkd_est"].mean()
        out["avg20_trading_value_hkd_est"] = out["code"].map(avg).combine_first(out.get("avg20_trading_value_hkd_est"))

    today = pd.Timestamp.today().normalize()
    listing = pd.to_datetime(out.get("listing_date"), errors="coerce")
    corner_amt = to_num(out.get("cornerstone_amount_hkd", pd.Series(np.nan, index=out.index))).fillna(0)
    corner_count = to_num(out.get("cornerstone_count", pd.Series(np.nan, index=out.index))).fillna(0)

    if "cornerstone_unlock_date" not in out.columns:
        out["cornerstone_unlock_date"] = pd.NaT
    if "controller_first_window_date" not in out.columns:
        out["controller_first_window_date"] = pd.NaT
    if "controller_second_window_date" not in out.columns:
        out["controller_second_window_date"] = pd.NaT

    cu, c6, c12 = [], [], []
    for i, d in listing.items():
        if pd.isna(d):
            cu.append(pd.NaT); c6.append(pd.NaT); c12.append(pd.NaT)
            continue
        actual = pd.to_datetime(out.get("lockup_end_date", pd.Series(pd.NaT, index=out.index)).iloc[i], errors="coerce") if i < len(out) else pd.NaT
        cu.append(actual if pd.notna(actual) else (d + pd.DateOffset(months=6) if (corner_amt.iloc[i] > 0 or corner_count.iloc[i] > 0) else pd.NaT))
        c6.append(d + pd.DateOffset(months=6))
        c12.append(d + pd.DateOffset(months=12))
    out["cornerstone_unlock_date"] = pd.to_datetime(cu)
    out["controller_first_window_date"] = pd.to_datetime(c6)
    out["controller_second_window_date"] = pd.to_datetime(c12)

    next_dates, type_cn, type_en = [], [], []
    for _, r in out.iterrows():
        candidates = []
        if pd.notna(r.get("cornerstone_unlock_date")):
            candidates.append((r["cornerstone_unlock_date"], "基石投资者解禁", "Cornerstone investor lock-up"))
        if pd.notna(r.get("controller_first_window_date")):
            candidates.append((r["controller_first_window_date"], "控股股东首个窗口", "Controlling shareholder first window"))
        if pd.notna(r.get("controller_second_window_date")):
            candidates.append((r["controller_second_window_date"], "控股股东第二窗口", "Controlling shareholder second window"))
        candidates = [c for c in candidates if c[0] >= today]
        if candidates:
            d, z, e = min(candidates, key=lambda x: x[0])
            next_dates.append(d); type_cn.append(z); type_en.append(e)
        else:
            next_dates.append(pd.NaT); type_cn.append("暂无未来解禁窗口"); type_en.append("No future lock-up window")
    out["next_unlock_date"] = pd.to_datetime(next_dates)
    out["days_to_unlock"] = (out["next_unlock_date"] - today).dt.days
    out["next_unlock_type_cn"] = type_cn
    out["next_unlock_type_en"] = type_en

    avgv = to_num(out.get("avg20_trading_value_hkd_est", pd.Series(np.nan, index=out.index))).replace({0: np.nan})
    out["cornerstone_value_to_avg20_turnover"] = (corner_amt / avgv).replace([np.inf, -np.inf], np.nan)
    max_gain = to_num(out.get("max_180_ret", pd.Series(np.nan, index=out.index))).fillna(to_num(out.get("max_60_ret", pd.Series(np.nan, index=out.index))).fillna(0))

    pressure_cn, pressure_en, action_cn, action_en, safety_score = [], [], [], [], []
    for i, r in out.iterrows():
        days = r.get("days_to_unlock")
        ratio = r.get("cornerstone_value_to_avg20_turnover")
        gain = max_gain.iloc[i] if i < len(max_gain) else np.nan
        if pd.isna(days):
            pcn, pen, score = "未知", "Unknown", 50
            acn = "缺少解禁字段，需人工复核招股书/持股结构"
            aen = "Missing lock-up data; manually check prospectus/shareholding structure"
        elif days <= 30 and ((pd.notna(ratio) and ratio >= 5) or (pd.notna(gain) and gain >= 0.5) or corner_amt.iloc[i] >= 1e9):
            pcn, pen, score = "高", "High", 25
            acn = "临近高压解禁：不追高，优先止盈/降仓，等待解禁后承接确认"
            aen = "High lock-up pressure nearby: avoid chasing; prioritize taking profit/reducing risk until post-unlock absorption confirms"
        elif days <= 90 or (pd.notna(ratio) and ratio >= 3):
            pcn, pen, score = "中", "Medium", 60
            acn = "解禁进入观察窗口：降低追高权重，买入需成交和价格确认"
            aen = "In lock-up watch window: reduce chasing; require price/turnover confirmation before adding"
        else:
            pcn, pen, score = "低", "Low", 85
            acn = "短期解禁压力较低：按趋势和发行价支撑执行"
            aen = "Low near-term lock-up pressure: follow trend and issue-price support rules"
        pressure_cn.append(pcn); pressure_en.append(pen); action_cn.append(acn); action_en.append(aen); safety_score.append(score)
    out["lockup_pressure_cn"] = pressure_cn
    out["lockup_pressure_en"] = pressure_en
    out["lockup_action_cn"] = action_cn
    out["lockup_action_en"] = action_en
    out["lockup_safety_score"] = safety_score

    # Keep a clean rating alias.
    if "investment_tier_cn" not in out.columns:
        out["investment_tier_cn"] = out.get("overall_score", pd.Series(np.nan, index=out.index)).map(lambda x: "A 重点参与" if pd.notna(x) and x >= 75 else "B 交易观察" if pd.notna(x) and x >= 60 else "C 等待触发" if pd.notna(x) and x >= 45 else "D 回避/仅跟踪")
    if "investment_tier_en" not in out.columns:
        out["investment_tier_en"] = out.get("overall_score", pd.Series(np.nan, index=out.index)).map(lambda x: "A Priority Participate" if pd.notna(x) and x >= 75 else "B Trading Watch" if pd.notna(x) and x >= 60 else "C Wait for Trigger" if pd.notna(x) and x >= 45 else "D Avoid / Track only")

    # A1 project-quality score is about future IPO participation potential, not application progress.
    out = build_a1_quality_scores(out)
    out = add_current_status(out)
    return out


def display_table(df: pd.DataFrame, lang: str, cols: list[str] | None = None, height: int = 520):
    if df.empty:
        st.info(tr(lang, "empty"))
        return
    out = df.copy()
    if cols is not None:
        out = out[[c for c in cols if c in out.columns]]
    # format selected columns
    for c in ["d1_close_ret", "max_20_ret", "min_20_ret", "max_60_ret", "min_60_ret", "max_180_ret", "min_180_ret"]:
        if c in out.columns: out[c] = out[c].map(fmt_pct)
    for c in ["gray_open_ret_pct", "gray_close_ret_pct", "d1_open_ret_pct", "d1_close_ret_pct", "one_lot_success_rate_pct"]:
        if c in out.columns: out[c] = out[c].map(fmt_pct_raw)
    for c in ["overall_score", "primary_score", "secondary_score", "cornerstone_score", "a1_score", "a1_quality_score", "a1_industry_preference_score", "a1_company_quality_score", "a1_sponsor_quality_score", "a1_peer_ipo_score", "a1_tradability_score", "a1_market_window_score", "custom_score", "margin_multiple", "public_subscription_multiple", "public_subscription_multiple_ballot", "cornerstone_value_to_avg20_turnover"]:
        if c in out.columns: out[c] = out[c].map(lambda x: fmt_num(x, 1))
    for c in ["cornerstone_amount_hkd", "margin_amount_hkd", "avg20_trading_value_hkd_est"]:
        if c in out.columns: out[c] = out[c].map(fmt_money)
    st.dataframe(label_cols(out, lang), use_container_width=True, hide_index=True, height=height)


def download_button(df: pd.DataFrame, name: str, lang: str):
    if not df.empty:
        st.download_button(tr(lang, "download"), df.to_csv(index=False, encoding="utf-8-sig"), name, "text/csv")


def make_custom_scores(df: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    out = df.copy()
    factor_map = {
        "定价安全": "pricing_safety_score",
        "需求热度": "issue_heat_score",
        "基石质量": "cornerstone_score",
        "投行质量": "cornerstone_bank_score",
        "暗盘/首日": "gray_signal_score",
        "上市后路径": "post_listing_score",
        "解禁安全": "lockup_safety_score",
        "解禁风险": "lockup_safety_score",
    }
    score = pd.Series(0.0, index=out.index)
    denom = 0.0
    for dim, w in weights.items():
        col = factor_map.get(dim)
        if col not in out.columns:
            if dim in ("解禁安全", "解禁风险") and "lockup_safety_score" in out.columns:
                col = "lockup_safety_score"
            else:
                continue
        vals = to_num(out[col]).fillna(50).clip(0, 100)
        score += vals * float(w)
        denom += float(w)
    out["custom_score"] = (score / denom if denom else out.get("overall_score", 0)).round(1)
    out["custom_tier_cn"] = out["custom_score"].map(lambda x: "A 重点参与" if x >= 75 else "B 交易观察" if x >= 60 else "C 等待触发" if x >= 45 else "D 回避/仅跟踪")
    out["custom_tier_en"] = out["custom_score"].map(lambda x: "A Priority Participate" if x >= 75 else "B Trading Watch" if x >= 60 else "C Wait for Trigger" if x >= 45 else "D Avoid / Track only")
    return out


def make_memo(row: pd.Series, lang: str) -> str:
    def g(c, default=""):
        v = row.get(c, default)
        if pd.isna(v):
            return default
        if isinstance(v, pd.Timestamp):
            return v.strftime("%Y-%m-%d")
        return v
    if lang == "中文":
        return f"""# 港股 IPO / 半新股投资备忘录：{g('code')} {g('name')}

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

## 一、投资结论
- 综合评级：{g('investment_tier_cn')}
- 综合分：{g('overall_score')}
- 一级建议：{g('primary_recommendation')}
- 基石/锚定建议：{g('cornerstone_recommendation')}
- 二级建议：{g('secondary_recommendation')}
- 买入触发：{g('buy_trigger')}
- 卖点/风控：{g('sell_trigger')}

## 二、A1项目质量与当前阶段
- A1项目质量分：{g('a1_quality_score')}
- 研究优先级：{g('a1_research_priority_cn')}
- 未来IPO参与倾向：{g('future_ipo_participation_cn')}
- 当前投资状态：{g('current_investment_status_cn')}
- 下一动作：{g('next_action_cn')}
- 加分原因：{g('a1_positive_reasons_cn')}
- 扣分/不确定性：{g('a1_negative_reasons_cn')}

## 三、项目阶段与发行结构
- 生命周期阶段：{g('lifecycle_stage')}
- 申请状态：{g('application_status')}
- 上市日：{g('listing_date')}
- 发行价：{g('issue_price')}
- 招股价区间：{g('offer_price_low')} - {g('offer_price_high')}
- 公开认购倍数：{g('public_subscription_multiple', g('public_subscription_multiple_ballot'))}
- 一手中签率：{g('one_lot_success_rate_pct')}
- 孖展倍数：{g('margin_multiple')}

## 四、基石、投行与解禁
- 基石数量：{g('cornerstone_count')}
- 基石金额：{g('cornerstone_amount_hkd')}
- 主要基石：{g('cornerstone_top_names')}
- 保荐人：{g('sponsor')}
- 整体协调人：{g('overall_coordinator')}
- 下一解禁日：{g('next_unlock_date')}
- 解禁类型：{g('next_unlock_type_cn')}
- 解禁压力：{g('lockup_pressure_cn')}
- 解禁提示：{g('lockup_action_cn')}

## 五、暗盘与上市后路径
- 暗盘开盘：{g('gray_open_ret_pct')}
- 暗盘收盘：{g('gray_close_ret_pct')}
- 首日收盘收益：{g('d1_close_ret')}
- 20D最大涨幅：{g('max_20_ret')}
- 20D最大压力：{g('min_20_ret')}
- 180D最大涨幅：{g('max_180_ret')}
- 180D最大压力：{g('min_180_ret')}
- 路径标签：{g('path_label')}
- 行情状态：{g('quote_status')}

## 六、业务简介与募资用途
### 业务简介
{g('business_scope')}

### 募资用途
{g('use_of_proceeds')}
"""
    return f"""# HK IPO / Newly Listed Equity Investment Memo: {g('code')} {g('name')}

Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 1. Investment View
- Rating: {g('investment_tier_en')}
- Overall Score: {g('overall_score')}
- Primary Recommendation: {g('primary_recommendation')}
- Cornerstone / Anchor Recommendation: {g('cornerstone_recommendation')}
- Secondary Recommendation: {g('secondary_recommendation')}
- Buy Trigger: {g('buy_trigger')}
- Sell / Risk Control: {g('sell_trigger')}

## 2. A1 Project Quality and Current Stage
- A1 Project Quality Score: {g('a1_quality_score')}
- Research Priority: {g('a1_research_priority_en')}
- Future IPO Participation Bias: {g('future_ipo_participation_en')}
- Current Investment Status: {g('current_investment_status_en')}
- Next Action: {g('next_action_en')}
- Positive Reasons: {g('a1_positive_reasons_en')}
- Negative / Uncertain Factors: {g('a1_negative_reasons_en')}

## 3. Stage and Deal Structure
- Lifecycle Stage: {g('lifecycle_stage')}
- Application Status: {g('application_status')}
- Listing Date: {g('listing_date')}
- Issue Price: {g('issue_price')}
- Offer Price Range: {g('offer_price_low')} - {g('offer_price_high')}
- Public Subscription Multiple: {g('public_subscription_multiple', g('public_subscription_multiple_ballot'))}
- One-lot Success Rate: {g('one_lot_success_rate_pct')}
- Margin Multiple: {g('margin_multiple')}

## 4. Cornerstone, Syndicate and Lock-up
- Cornerstone Count: {g('cornerstone_count')}
- Cornerstone Amount: {g('cornerstone_amount_hkd')}
- Major Cornerstones: {g('cornerstone_top_names')}
- Sponsor: {g('sponsor')}
- Overall Coordinator: {g('overall_coordinator')}
- Next Unlock Date: {g('next_unlock_date')}
- Unlock Type: {g('next_unlock_type_en')}
- Lock-up Pressure: {g('lockup_pressure_en')}
- Lock-up Action: {g('lockup_action_en')}

## 5. Gray Market and Post-listing Path
- Gray Open: {g('gray_open_ret_pct')}
- Gray Close: {g('gray_close_ret_pct')}
- D1 Close Return: {g('d1_close_ret')}
- 20D Max Upside: {g('max_20_ret')}
- 20D Max Pressure: {g('min_20_ret')}
- 180D Max Upside: {g('max_180_ret')}
- 180D Max Pressure: {g('min_180_ret')}
- Path Label: {g('path_label')}
- Quote Status: {g('quote_status')}

## 6. Business Scope and Use of Proceeds
### Business Scope
{g('business_scope')}

### Use of Proceeds
{g('use_of_proceeds')}
"""


pool_raw, paths, quotes, inventory, buckets, profile_perf, diag, weight_profiles = load_all()
if pool_raw.empty:
    st.error("Missing deploy_data/ipo_investment_decision_scored.csv or source data.")
    st.stop()

pool = enrich_dynamic(pool_raw, quotes)

# Sidebar
lang = st.sidebar.radio("语言 / Language", ["中文", "English"], horizontal=True)
T = TEXT[lang]
page_labels = list(T["pages"].values())
page_key_by_label = {v: k for k, v in T["pages"].items()}
page_label = st.sidebar.selectbox("页面 / Page", page_labels)
page = page_key_by_label[page_label]

st.title(tr(lang, "app_title"))
st.caption(tr(lang, "caption"))

# Filters
with st.sidebar.expander("筛选 / Filters", expanded=True):
    min_score = st.slider(tr(lang, "min_score"), 0, 100, 0, 5)
    stage_vals = sorted([x for x in pool.get("lifecycle_stage", pd.Series(dtype=str)).dropna().astype(str).unique()])
    stages = st.multiselect(tr(lang, "stage"), stage_vals, default=stage_vals)
    tier_col = "investment_tier_cn" if lang == "中文" else "investment_tier_en"
    tier_vals = sorted([x for x in pool.get(tier_col, pd.Series(dtype=str)).dropna().astype(str).unique()])
    tiers = st.multiselect(tr(lang, "rating"), tier_vals, default=tier_vals)
    ind_vals = sorted([x for x in pool.get("industry_level_1", pd.Series(dtype=str)).dropna().astype(str).unique()])
    inds = st.multiselect(tr(lang, "industry"), ind_vals, default=[])
    query = st.text_input(tr(lang, "search"), "")

view = pool.copy()
if "overall_score" in view.columns:
    view = view[to_num(view["overall_score"]).fillna(0) >= min_score]
if stages and "lifecycle_stage" in view.columns:
    view = view[view["lifecycle_stage"].astype(str).isin(stages)]
if tiers and tier_col in view.columns:
    view = view[view[tier_col].astype(str).isin(tiers)]
if inds and "industry_level_1" in view.columns:
    view = view[view["industry_level_1"].astype(str).isin(inds)]
if query:
    q = query.strip().lower()
    mask = view.get("code", pd.Series("", index=view.index)).astype(str).str.lower().str.contains(q, na=False) | view.get("name", pd.Series("", index=view.index)).astype(str).str.lower().str.contains(q, na=False)
    view = view[mask]

listing_dates_for_mask = pd.to_datetime(pool.get("listing_date", pd.Series(pd.NaT, index=pool.index)), errors="coerce")
today_for_mask = pd.Timestamp.today().normalize()
listed_mask = listing_dates_for_mask.notna() & (listing_dates_for_mask <= today_for_mask)
a1_mask = pool.get("application_date", pd.Series(pd.NaT, index=pool.index)).notna() & ~listed_mask
high_lock = pool.get("lockup_pressure_cn", pd.Series("", index=pool.index)).isin(["高", "中"]) & (to_num(pool.get("days_to_unlock", pd.Series(np.nan, index=pool.index))) <= 90)

if page == "dashboard":
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(tr(lang, "metric_total"), len(view))
    c2.metric(tr(lang, "metric_a1"), int(a1_mask.sum()))
    c3.metric(tr(lang, "metric_listed"), int(listed_mask.sum()))
    c4.metric(tr(lang, "metric_high_lockup"), int(high_lock.sum()))
    c5.metric(tr(lang, "metric_avg"), fmt_num(to_num(view.get("overall_score", pd.Series(dtype=float))).mean(), 1))
    st.subheader(tr(lang, "decision_pool"))
    cols = [tier_col, "current_investment_status_cn" if lang == "中文" else "current_investment_status_en", "code", "name", "lifecycle_stage", "listing_date", "industry_level_1", "overall_score", "a1_quality_score", "future_ipo_participation_cn" if lang == "中文" else "future_ipo_participation_en", "primary_recommendation", "secondary_recommendation", "lockup_pressure_cn" if lang == "中文" else "lockup_pressure_en", "next_action_cn" if lang == "中文" else "next_action_en"]
    display_table(view.sort_values("overall_score", ascending=False, na_position="last"), lang, cols, 560)
    download_button(view, "investment_decision_pool.csv", lang)

elif page == "a1":
    st.subheader(T["pages"]["a1"])
    if lang == "中文":
        st.info("A1项目观察池只保留尚未上市公司；评分衡量未来IPO是否值得重点参与，申请状态只作为项目管理信息，不进入项目质量分。")
    else:
        st.info("The A1 watchlist only includes unlisted companies. The score measures future IPO participation potential; filing status is project-management information and is not part of project quality.")

    a1_company, a1_history = build_a1_company_view(view)
    if a1_company.empty:
        st.info(tr(lang, "empty"))
    else:
        show_all_lapsed = st.checkbox("显示长期失效历史项目" if lang == "中文" else "Show long-lapsed historical projects", value=False)
        latest_dt = pd.to_datetime(a1_company.get("latest_application_date_calc"), errors="coerce")
        status_ser0 = a1_company.get("application_status", pd.Series("", index=a1_company.index)).astype(str)
        long_lapsed_mask = status_ser0.map(status_is_lapsed) & latest_dt.notna() & (latest_dt < pd.Timestamp.today().normalize() - pd.DateOffset(months=24))
        hidden_count = int(long_lapsed_mask.sum())
        if not show_all_lapsed:
            a1_company = a1_company[~long_lapsed_mask].copy()
            if hidden_count:
                st.caption((f"已默认隐藏 {hidden_count} 个长期失效历史项目；勾选上方选项可查看全部。" if lang == "中文" else f"{hidden_count} long-lapsed historical projects are hidden by default; tick above to show all."))
        tab_all, tab_active, tab_lapsed, tab_multi = st.tabs(["全部未上市项目" if lang == "中文" else "All Unlisted", "活跃申请" if lang == "中文" else "Active Filings", "失效观察" if lang == "中文" else "Lapsed Watch", "多次递表" if lang == "中文" else "Multiple Filings"])
        status_ser = a1_company.get("application_status", pd.Series("", index=a1_company.index)).astype(str)
        lapsed_mask = status_ser.map(status_is_lapsed)
        active_mask = ~lapsed_mask
        multi_mask = to_num(a1_company.get("filing_count", pd.Series(1, index=a1_company.index))).fillna(1) >= 2
        base_cols = [
            "a1_research_priority_cn" if lang == "中文" else "a1_research_priority_en",
            "future_ipo_participation_cn" if lang == "中文" else "future_ipo_participation_en",
            "current_investment_status_cn" if lang == "中文" else "current_investment_status_en",
            "temp_code", "code", "name", "application_status", "filing_count", "latest_application_date_calc", "first_application_date_calc",
            "status_note_cn" if lang == "中文" else "status_note_en",
            "a1_quality_score", "a1_industry_preference_score", "a1_company_quality_score", "a1_sponsor_quality_score", "a1_peer_ipo_score", "a1_tradability_score", "a1_market_window_score",
            "industry_level_1", "sponsor", "overall_coordinator", "next_action_cn" if lang == "中文" else "next_action_en"
        ]
        with tab_all:
            display_table(a1_company.sort_values("a1_quality_score", ascending=False, na_position="last"), lang, base_cols, 580)
        with tab_active:
            display_table(a1_company[active_mask].sort_values("a1_quality_score", ascending=False, na_position="last"), lang, base_cols, 580)
        with tab_lapsed:
            display_table(a1_company[lapsed_mask].sort_values("a1_quality_score", ascending=False, na_position="last"), lang, base_cols, 580)
        with tab_multi:
            display_table(a1_company[multi_mask].sort_values("a1_quality_score", ascending=False, na_position="last"), lang, base_cols, 580)

        st.markdown("### " + ("单个项目评分拆解与申请记录" if lang == "中文" else "Single-project Score Breakdown & Filing History"))
        options = (a1_company.get("name", pd.Series("", index=a1_company.index)).astype(str) + " | " + a1_company.get("temp_code", pd.Series("", index=a1_company.index)).astype(str)).tolist()
        selected_a1 = st.selectbox("选择项目" if lang == "中文" else "Select project", options)
        if selected_a1:
            sel_name = selected_a1.split(" | ")[0]
            row = a1_company[a1_company["name"].astype(str) == sel_name].iloc[0]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("A1项目质量分" if lang == "中文" else "A1 Quality Score", fmt_num(row.get("a1_quality_score"), 1))
            m2.metric("研究优先级" if lang == "中文" else "Research Priority", row.get("a1_research_priority_cn" if lang == "中文" else "a1_research_priority_en", ""))
            m3.metric("未来参与倾向" if lang == "中文" else "Future Participation Bias", row.get("future_ipo_participation_cn" if lang == "中文" else "future_ipo_participation_en", ""))
            m4.metric("递表次数" if lang == "中文" else "Filing Count", int(row.get("filing_count", 1)) if pd.notna(row.get("filing_count")) else 1)
            breakdown = pd.DataFrame({
                ("维度" if lang == "中文" else "Dimension"): [
                    "行业与港股市场偏好" if lang == "中文" else "Sector & HK Market Preference",
                    "公司稀缺性与基本面潜力" if lang == "中文" else "Scarcity & Fundamental Potential",
                    "保荐人/中介质量" if lang == "中文" else "Sponsor / Intermediary Quality",
                    "历史同类IPO表现" if lang == "中文" else "Comparable IPO Performance",
                    "未来交易可做性" if lang == "中文" else "Future Tradability",
                    "当前市场窗口" if lang == "中文" else "Current Market Window",
                ],
                ("默认权重" if lang == "中文" else "Default Weight"): ["35%", "20%", "15%", "15%", "10%", "5%"],
                ("得分" if lang == "中文" else "Score"): [
                    fmt_num(row.get("a1_industry_preference_score"), 1), fmt_num(row.get("a1_company_quality_score"), 1), fmt_num(row.get("a1_sponsor_quality_score"), 1),
                    fmt_num(row.get("a1_peer_ipo_score"), 1), fmt_num(row.get("a1_tradability_score"), 1), fmt_num(row.get("a1_market_window_score"), 1),
                ]
            })
            st.dataframe(breakdown, use_container_width=True, hide_index=True)
            cadd, csub = st.columns(2)
            with cadd:
                st.write("加分原因" if lang == "中文" else "Positive Reasons")
                st.success(row.get("a1_positive_reasons_cn" if lang == "中文" else "a1_positive_reasons_en", ""))
            with csub:
                st.write("扣分/不确定性" if lang == "中文" else "Negative / Uncertain Factors")
                st.warning(row.get("a1_negative_reasons_cn" if lang == "中文" else "a1_negative_reasons_en", ""))
            st.write(("状态提示：" if lang == "中文" else "Status note: ") + str(row.get("status_note_cn" if lang == "中文" else "status_note_en", "")))
            st.write(("下一动作：" if lang == "中文" else "Next action: ") + str(row.get("next_action_cn" if lang == "中文" else "next_action_en", "")))
            key = row.get("company_key")
            hist = a1_history[a1_history["company_key"] == key].copy() if "company_key" in a1_history.columns else pd.DataFrame()
            with st.expander("查看完整申请记录" if lang == "中文" else "View full filing history", expanded=False):
                hcols = ["temp_code", "code", "name", "application_date", "application_status", "status_update_date", "hearing_date", "sponsor", "overall_coordinator"]
                display_table(hist.sort_values("application_date_dt", ascending=False, na_position="last"), lang, hcols, 260)

    with st.expander("本页和评分标准页的关系" if lang == "中文" else "How this page relates to Scoring Standards", expanded=False):
        if lang == "中文":
            st.markdown("A1项目观察池是**应用页面**：展示每个未上市项目的结果、拆解和下一动作。完整的维度定义、档位和可调权重集中在 **⑦ 评分标准与权重设置**，避免重复。")
        else:
            st.markdown("The A1 Watchlist is an **application page**: it shows project-level results, breakdown and next actions. Full dimension definitions, tiers and adjustable weights are centralized in **⑦ Scoring Standards & Weights** to avoid duplication.")

elif page == "ipo":
    st.subheader(T["pages"]["ipo"])
    ipo = view[view.get("issue_price", pd.Series(np.nan, index=view.index)).notna() | view.get("offer_price_high", pd.Series(np.nan, index=view.index)).notna()].copy()
    cols = [tier_col, "code", "name", "listing_date", "issue_price", "offer_price_low", "offer_price_high", "public_subscription_multiple", "public_subscription_multiple_ballot", "one_lot_success_rate_pct", "margin_multiple", "cornerstone_count", "cornerstone_amount_hkd", "primary_score", "primary_recommendation", "cornerstone_recommendation"]
    display_table(ipo.sort_values("primary_score", ascending=False, na_position="last"), lang, cols, 620)
    with st.expander(tr(lang, "standards"), expanded=True):
        if lang == "中文":
            st.markdown("""
| 维度 | 关注点 | 高档定义 | 风险档定义 |
|---|---|---|---|
| 发行定价 | 发行价区间、发行价位置、估值安全边际 | 定价合理或让利，仍有估值空间 | 定价贴近上限但基本面/行业承接不足 |
| 需求热度 | 公开认购、孖展、国际配售 | 多渠道需求强且不过度拥挤 | 单靠孖展或散户过热，机构承接弱 |
| 发行结构 | 流通盘、回拨、募资规模 | 流通和募资规模适中 | 流通太小容易炒作后失衡，太大承接压力大 |
| 基石质量 | 基石数量、金额、类型 | 长线主权/产业/头部机构参与 | 关联、短线或质量不明，且解禁压力大 |
| 投行质量 | 保荐人、账簿管理人、承销团 | 历史项目表现和销售能力较好 | 历史破发率高或销售能力弱 |
""")
        else:
            st.markdown("""
| Dimension | Focus | Strong Tier | Risk Tier |
|---|---|---|---|
| Pricing | Offer range, final pricing, valuation safety | Reasonable/discounted pricing with upside room | Top-end pricing without sufficient support |
| Demand Heat | Public subscription, margin, international placing | Broad-based demand without excessive crowding | Retail/margin-driven heat with weak institutional support |
| Deal Structure | Float, clawback, fundraising size | Balanced float and fundraising size | Too small to sustain or too large to absorb |
| Cornerstone Quality | Investor type, count and amount | Long-only sovereign/strategic/top-tier investors | Related/unclear quality and high lock-up pressure |
| Syndicate Quality | Sponsor, bookrunners, underwriters | Strong track record and distribution | Weak historical performance or distribution |
""")

elif page == "gray":
    st.subheader(T["pages"]["gray"])
    gray = view[view.get("gray_close_ret_pct", pd.Series(np.nan, index=view.index)).notna() | view.get("d1_close_ret_pct", pd.Series(np.nan, index=view.index)).notna() | view.get("d1_close_ret", pd.Series(np.nan, index=view.index)).notna()].copy()
    action_col = "first_day_action_cn" if lang == "中文" else "first_day_action_en"
    cols = ["code", "name", "listing_date", "issue_price", "gray_open_ret_pct", "gray_close_ret_pct", "gray_amount_10k_hkd", "d1_open_ret_pct", "d1_close_ret_pct", "d1_close_ret", "gray_signal_score", action_col, "primary_recommendation", "secondary_recommendation"]
    display_table(gray.sort_values("gray_signal_score", ascending=False, na_position="last"), lang, cols, 620)
    with st.expander(tr(lang, "standards"), expanded=True):
        if lang == "中文":
            st.markdown("""
| 信号 | 判断 |
|---|---|
| 暗盘强且收近高位 | 首日可观察参与，但高开过大不追 |
| 暗盘高开低走 | 情绪兑现，首日优先卖出或等回踩 |
| 暗盘破发 | 除非基本面极强且首日快速收回发行价，否则回避 |
| 首日放量上涨 | 可进入二级观察池，等待回踩不破发行价/首日VWAP |
| 首日放量下跌 | 资金承接弱，进入风险池 |
""")
        else:
            st.markdown("""
| Signal | Interpretation |
|---|---|
| Strong gray market and close near high | Can participate selectively, but do not chase an excessive gap-up |
| Gray market gap-up then fade | Sentiment monetized; sell first day or wait for pullback |
| Gray market breaks issue price | Avoid unless first day quickly reclaims issue price with strong fundamentals |
| First-day volume-up rally | Add to secondary watchlist; wait for pullback holding issue price / D1 VWAP area |
| First-day volume-down decline | Weak absorption; add to risk list |
""")

elif page == "post":
    st.subheader(T["pages"]["post"])
    post = view[view.get("quote_status", pd.Series("", index=view.index)).astype(str).isin(["ok", "partial"]) | view.get("path_label", pd.Series("", index=view.index)).notna()].copy()
    cols = [tier_col, "code", "name", "listing_date", "issue_price", "quote_rows", "quote_source", "quote_status", "path_label", "d1_close_ret", "max_20_ret", "min_20_ret", "max_60_ret", "min_60_ret", "max_180_ret", "min_180_ret", "secondary_score", "secondary_recommendation", "buy_trigger", "sell_trigger"]
    display_table(post.sort_values("secondary_score", ascending=False, na_position="last"), lang, cols, 640)
    with st.expander(tr(lang, "standards"), expanded=True):
        if lang == "中文":
            st.markdown("""
| 路径 | 定义 | 操作含义 |
|---|---|---|
| 上市即强势 | 首日/早期显著高于发行价，回撤可控 | 不追高，等回踩或趋势确认 |
| 深V反弹 | 先破发或明显回撤，随后重新站回关键位 | 重点关注二级买点 |
| 温和趋势 | 涨跌不极端，逐步形成支撑 | 小仓试错，重视成交确认 |
| 升后破发 | 前期大涨后跌回发行价下方 | 卖点/降仓优先 |
| 持续破发/弱势 | 长期低于发行价且承接弱 | 回避，除非基本面或估值重新定价 |
""")
        else:
            st.markdown("""
| Path | Definition | Trading Implication |
|---|---|---|
| Strong open | Early price remains significantly above issue price with controlled drawdown | Do not chase; wait for pullback or trend confirmation |
| Deep-V rebound | Breaks issue price / sharp drawdown then reclaims key levels | Key secondary buy setup |
| Moderate trend | Non-extreme path with developing support | Small trial position only with turnover confirmation |
| Pump then break | Early rally followed by break below issue price | Sell / reduce risk first |
| Persistent break / weak | Stays below issue price with weak absorption | Avoid unless fundamentals/valuation reset |
""")

elif page == "lockup":
    st.subheader(T["pages"]["lockup"])
    lock = view[view.get("listing_date", pd.Series(pd.NaT, index=view.index)).notna()].copy()
    c1, c2, c3 = st.columns(3)
    c1.metric("High / 高", int((lock.get("lockup_pressure_cn", pd.Series("", index=lock.index)) == "高").sum()))
    c2.metric("Medium / 中", int((lock.get("lockup_pressure_cn", pd.Series("", index=lock.index)) == "中").sum()))
    c3.metric("Within 90D / 90日内", int((to_num(lock.get("days_to_unlock", pd.Series(np.nan, index=lock.index))) <= 90).sum()))
    type_col = "next_unlock_type_cn" if lang == "中文" else "next_unlock_type_en"
    pressure_col = "lockup_pressure_cn" if lang == "中文" else "lockup_pressure_en"
    action_col = "lockup_action_cn" if lang == "中文" else "lockup_action_en"
    cols = ["code", "name", "listing_date", "next_unlock_date", "days_to_unlock", type_col, pressure_col, "cornerstone_count", "cornerstone_amount_hkd", "avg20_trading_value_hkd_est", "cornerstone_value_to_avg20_turnover", "max_180_ret", action_col]
    display_table(lock.sort_values(["days_to_unlock", "cornerstone_value_to_avg20_turnover"], ascending=[True, False], na_position="last"), lang, cols, 640)
    with st.expander(tr(lang, "standards"), expanded=True):
        if lang == "中文":
            st.markdown("""
| 解禁压力 | 定义 | 操作影响 |
|---|---|---|
| 高 | 30日内解禁，且基石金额/20日成交额较高、或上市后涨幅较大 | 不追高，优先止盈/降仓，等解禁后承接确认 |
| 中 | 90日内解禁，或估算供给压力中等 | 买入需价格与成交确认，降低追高权重 |
| 低 | 解禁距离较远，或成交承接较好 | 按趋势和发行价支撑执行 |
| 未知 | 缺少持股或锁定期字段 | 需要人工复核招股书和股东结构 |
""")
        else:
            st.markdown("""
| Pressure | Definition | Trading Impact |
|---|---|---|
| High | Unlock within 30D with high cornerstone/20D turnover ratio or large post-listing gain | Avoid chasing; prioritize profit-taking/risk reduction until absorption confirms |
| Medium | Unlock within 90D or moderate supply pressure | Require price and turnover confirmation; lower chasing weight |
| Low | Unlock is far away or liquidity absorption is strong | Follow trend and issue-price support rules |
| Unknown | Missing shareholding / lock-up fields | Manually review prospectus and shareholder structure |
""")

elif page == "weights":
    st.subheader(T["pages"]["weights"])
    profile_items = list(weight_profiles.items())
    if not profile_items:
        weight_profiles = {"balanced": {"zh_name":"平衡型","en_name":"Balanced","zh_desc":"默认方案","en_desc":"Default profile","weights":{"定价安全":20,"需求热度":20,"基石质量":15,"投行质量":10,"暗盘/首日":15,"上市后路径":15,"解禁安全":5}}}
        profile_items = list(weight_profiles.items())
    display_name = lambda kv: (kv[1].get("zh_name") if lang == "中文" else kv[1].get("en_name")) or kv[0]
    selected_tuple = st.selectbox(tr(lang, "profile"), profile_items, format_func=display_name)
    selected_key, selected_profile = selected_tuple
    st.info(selected_profile.get("zh_desc" if lang == "中文" else "en_desc", ""))
    preset = selected_profile.get("weights", {})
    # Normalize naming
    if "解禁风险" in preset and "解禁安全" not in preset:
        preset["解禁安全"] = preset.pop("解禁风险")
    dims = ["定价安全", "需求热度", "基石质量", "投行质量", "暗盘/首日", "上市后路径", "解禁安全"]
    dim_en = {"定价安全":"Pricing Safety", "需求热度":"Demand Heat", "基石质量":"Cornerstone Quality", "投行质量":"Syndicate Quality", "暗盘/首日":"Gray / First Day", "上市后路径":"Post-listing Path", "解禁安全":"Lock-up Safety"}
    st.markdown(f"### {tr(lang, 'custom_weights')}")
    cols = st.columns(2)
    weights = {}
    for i, d in enumerate(dims):
        with cols[i % 2]:
            label = d if lang == "中文" else dim_en[d]
            weights[d] = st.slider(label, 0, 50, int(preset.get(d, 10)), 1)
    total = sum(weights.values()) or 1
    norm = {d: weights[d] / total * 100 for d in dims}
    weight_tbl = pd.DataFrame({"维度" if lang == "中文" else "Dimension": [d if lang == "中文" else dim_en[d] for d in dims], "权重" if lang == "中文" else "Weight": [f"{norm[d]:.1f}%" for d in dims]})
    st.dataframe(weight_tbl, use_container_width=True, hide_index=True)
    custom = make_custom_scores(view, weights)
    st.markdown(f"### {tr(lang, 'live_score')}")
    cols_show = ["custom_tier_cn" if lang == "中文" else "custom_tier_en", "code", "name", "lifecycle_stage", "custom_score", "overall_score", "primary_recommendation", "secondary_recommendation", "lockup_pressure_cn" if lang == "中文" else "lockup_pressure_en"]
    display_table(custom.sort_values("custom_score", ascending=False, na_position="last"), lang, cols_show, 420)
    download_button(custom, "custom_weight_ranking.csv", lang)
    st.markdown(f"### {tr(lang, 'standards')}")
    if lang == "中文":
        st.markdown("""
| 分数区间 | 评级 | 含义 |
|---:|---|---|
| 75-100 | A 重点参与 | 多维度同时支持，可进入重点额度/交易讨论 |
| 60-75 | B 交易观察 | 有交易价值，但需要价格、成交或发行结构确认 |
| 45-60 | C 等待触发 | 信息不完整或信号分化，等待关键事件 |
| 0-45 | D 回避/仅跟踪 | 风险或缺口明显，不主动参与 |
""")
    else:
        st.markdown("""
| Score Range | Rating | Meaning |
|---:|---|---|
| 75-100 | A Priority Participate | Multiple dimensions support active allocation/trading discussion |
| 60-75 | B Trading Watch | Tradable but requires price, turnover or deal-structure confirmation |
| 45-60 | C Wait for Trigger | Incomplete information or mixed signals; wait for key events |
| 0-45 | D Avoid / Track only | Clear risks or missing data; no active participation |
""")


    st.markdown("---")
    st.markdown("### " + ("A1早期项目评分：标准与自定义权重" if lang == "中文" else "A1 Early-project Scoring: Standards & Custom Weights"))
    if lang == "中文":
        st.caption("A1项目质量分用于判断公司未来IPO是否值得重点参与；申请状态、失效和多次递表仅作为项目管理信息，不进入项目质量分。")
    else:
        st.caption("The A1 quality score estimates future IPO participation potential. Filing status, lapse and refiling history are project-management information and are not included in project-quality scoring.")
    a1_dims = [
        ("industry", "行业与港股市场偏好", "Sector & HK Market Preference", 35),
        ("company", "公司稀缺性与基本面潜力", "Scarcity & Fundamental Potential", 20),
        ("sponsor", "保荐人/中介质量", "Sponsor / Intermediary Quality", 15),
        ("peer", "历史同类IPO表现", "Comparable IPO Performance", 15),
        ("tradability", "未来交易可做性", "Future Tradability", 10),
        ("market", "当前市场窗口", "Current Market Window", 5),
    ]
    a1_cols = st.columns(2)
    a1_weights = {}
    for i, (key, zh, en, default) in enumerate(a1_dims):
        with a1_cols[i % 2]:
            a1_weights[key] = st.slider(zh if lang == "中文" else en, 0, 60, default, 1, key=f"a1w_{key}")
    a1_total = sum(a1_weights.values()) or 1
    a1_weight_table = pd.DataFrame({
        "维度" if lang == "中文" else "Dimension": [zh if lang == "中文" else en for _, zh, en, _ in a1_dims],
        "当前权重" if lang == "中文" else "Current Weight": [f"{a1_weights[k]/a1_total*100:.1f}%" for k, _, _, _ in a1_dims],
        "档位定义" if lang == "中文" else "Tier Definition": [
            "强：近期同类IPO表现强、成交活跃、港股估值弹性高；弱：历史破发率高或关注度低" if lang == "中文" else "Strong: comparable IPOs show returns, liquidity and valuation elasticity; Weak: high break rate / low attention",
            "强：稀缺龙头、成长性和商业模式清晰；弱：同质化、信息不足或基本面存疑" if lang == "中文" else "Strong: scarce leader, clear growth and business model; Weak: commoditized, insufficient data or questionable fundamentals",
            "强：历史项目表现和销售能力优于市场；弱：历史破发率高或中介信息不足" if lang == "中文" else "Strong: historical projects and distribution above market; Weak: high break rate / insufficient sponsor data",
            "强：同行业/同类型项目有赚钱效应；弱：同类项目长期弱势或流动性差" if lang == "中文" else "Strong: similar IPOs have money-making effect; Weak: similar projects are weak / illiquid",
            "强：预计关注度、流通和成交可支持二级交易；弱：上市后可能无人交易" if lang == "中文" else "Strong: expected attention, float and turnover support secondary trading; Weak: likely illiquid after listing",
            "强：近期新股赚钱效应强；弱：新股市场退潮" if lang == "中文" else "Strong: recent IPO market has positive return effect; Weak: IPO market cooling",
        ]
    })
    st.dataframe(a1_weight_table, use_container_width=True, hide_index=True)
    a1_custom_df = build_a1_quality_scores(view, a1_weights)
    a1_custom_company, _ = build_a1_company_view(a1_custom_df)
    st.markdown("#### " + ("按当前A1权重重算的未上市项目排名" if lang == "中文" else "Unlisted Project Ranking Recalculated with Current A1 Weights"))
    if not a1_custom_company.empty:
        cols_a1_live = ["a1_research_priority_cn" if lang == "中文" else "a1_research_priority_en", "future_ipo_participation_cn" if lang == "中文" else "future_ipo_participation_en", "temp_code", "code", "name", "application_status", "filing_count", "a1_quality_score", "a1_industry_preference_score", "a1_company_quality_score", "a1_sponsor_quality_score", "a1_peer_ipo_score", "a1_tradability_score", "a1_market_window_score"]
        display_table(a1_custom_company.sort_values("a1_quality_score", ascending=False, na_position="last"), lang, cols_a1_live, 420)

elif page == "backtest":
    st.subheader(T["pages"]["backtest"])
    if lang == "中文":
        st.info("这个页面回答：高分组合是否更好、模型是否能避开破发、二级交易信号是否有用，以及失败样本在哪里。")
    else:
        st.info("This page answers whether high-score buckets perform better, whether the model avoids break-issue-price cases, whether secondary signals work, and where failures occur.")
    st.markdown("### " + ("评分分层表现" if lang == "中文" else "Score Bucket Performance"))
    display_table(buckets, lang, None, 240)
    st.markdown("### " + ("权重方案表现" if lang == "中文" else "Weight Profile Performance"))
    display_table(profile_perf, lang, None, 260)
    st.markdown("### " + ("因子有效性诊断" if lang == "中文" else "Factor Diagnostics"))
    display_table(diag, lang, None, 300)
    # Failure review
    st.markdown("### " + ("失败/漏判案例复盘" if lang == "中文" else "Failure / Missed-case Review"))
    data = view.copy()
    data["overall_score_num"] = to_num(data.get("overall_score"))
    data["max20_num"] = to_num(data.get("max_20_ret"))
    data["min20_num"] = to_num(data.get("min_20_ret"))
    high_fail = data[(data["overall_score_num"] >= 60) & (data["max20_num"] < 0.05)].sort_values("overall_score_num", ascending=False)
    low_miss = data[(data["overall_score_num"] < 45) & (to_num(data.get("max_180_ret")) > 0.5)].sort_values("max_180_ret", ascending=False)
    col1, col2 = st.columns(2)
    with col1:
        st.write("高分但表现弱" if lang == "中文" else "High score but weak outcome")
        display_table(high_fail, lang, ["code", "name", "overall_score", "path_label", "d1_close_ret", "max_20_ret", "min_20_ret", "risk_tags_model"], 280)
    with col2:
        st.write("低分但后续大涨" if lang == "中文" else "Low score but later strong rally")
        display_table(low_miss, lang, ["code", "name", "overall_score", "path_label", "d1_close_ret", "max_180_ret", "min_180_ret", "risk_tags_model"], 280)

elif page == "memo":
    st.subheader(tr(lang, "memo_title"))
    options = (view.get("code", pd.Series("", index=view.index)).astype(str) + " " + view.get("name", pd.Series("", index=view.index)).astype(str)).tolist()
    selected = st.selectbox("Stock", options)
    if selected:
        code = selected.split()[0]
        row = view[view["code"].astype(str) == code].iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rating" if lang == "English" else "评级", row.get("investment_tier_en" if lang == "English" else "investment_tier_cn", ""))
        c2.metric("Score" if lang == "English" else "综合分", fmt_num(row.get("overall_score"), 1))
        c3.metric("Lock-up" if lang == "English" else "解禁压力", row.get("lockup_pressure_en" if lang == "English" else "lockup_pressure_cn", ""))
        c4.metric("Path" if lang == "English" else "路径", row.get("path_label", ""))
        st.markdown(make_memo(row, lang))
        st.download_button(tr(lang, "export_memo"), make_memo(row, lang), file_name=f"memo_{code}.md", mime="text/markdown")

elif page == "quality":
    st.subheader(tr(lang, "data_quality"))
    # dynamic inventory rows
    extra = []
    if not quotes.empty:
        extra.append({"source_name":"上市后0-180D行情", "file_name":"ipo_daily_quotes_180d.csv", "raw_rows":len(quotes), "normalized_rows":len(quotes), "status":"已接入"})
    if not paths.empty:
        extra.append({"source_name":"上市后路径标签", "file_name":"ipo_post_listing_paths.csv", "raw_rows":len(paths), "normalized_rows":len(paths), "status":"已接入"})
    extra.append({"source_name":"投资决策评分", "file_name":"ipo_investment_decision_scored.csv", "raw_rows":len(pool), "normalized_rows":len(pool), "status":"已接入"})
    inv = inventory.copy()
    if extra:
        ex = pd.DataFrame(extra)
        if not inv.empty and "source_name" in inv.columns:
            inv = inv[~inv["source_name"].isin(ex["source_name"])]
        inv = pd.concat([inv, ex], ignore_index=True)
    display_table(inv, lang, None, 360)
    st.markdown("### " + ("关键字段缺失率" if lang == "中文" else "Key Field Missingness"))
    key_cols = ["code", "name", "listing_date", "issue_price", "public_subscription_multiple", "one_lot_success_rate_pct", "margin_multiple", "cornerstone_amount_hkd", "sponsor", "gray_close_ret_pct", "path_label", "next_unlock_date"]
    miss = []
    for c in key_cols:
        if c in pool.columns:
            miss.append({"field": c, "missing_rate": pool[c].isna().mean(), "available_rows": int(pool[c].notna().sum())})
        else:
            miss.append({"field": c, "missing_rate": 1.0, "available_rows": 0})
    miss_df = pd.DataFrame(miss)
    miss_df["missing_rate"] = miss_df["missing_rate"].map(fmt_pct)
    st.dataframe(miss_df, use_container_width=True, hide_index=True)
