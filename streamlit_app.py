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
}


def tr(lang: str, key: str):
    return TEXT[lang].get(key, key)


def label_cols(df: pd.DataFrame, lang: str) -> pd.DataFrame:
    mapping = COL_ZH if lang == "中文" else COL_EN
    return df.rename(columns={c: mapping.get(c, c) for c in df.columns})


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
    for c in ["overall_score", "primary_score", "secondary_score", "cornerstone_score", "a1_score", "custom_score", "margin_multiple", "public_subscription_multiple", "public_subscription_multiple_ballot", "cornerstone_value_to_avg20_turnover"]:
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

## 二、项目阶段与发行结构
- 生命周期阶段：{g('lifecycle_stage')}
- 申请状态：{g('application_status')}
- 上市日：{g('listing_date')}
- 发行价：{g('issue_price')}
- 招股价区间：{g('offer_price_low')} - {g('offer_price_high')}
- 公开认购倍数：{g('public_subscription_multiple', g('public_subscription_multiple_ballot'))}
- 一手中签率：{g('one_lot_success_rate_pct')}
- 孖展倍数：{g('margin_multiple')}

## 三、基石、投行与解禁
- 基石数量：{g('cornerstone_count')}
- 基石金额：{g('cornerstone_amount_hkd')}
- 主要基石：{g('cornerstone_top_names')}
- 保荐人：{g('sponsor')}
- 整体协调人：{g('overall_coordinator')}
- 下一解禁日：{g('next_unlock_date')}
- 解禁类型：{g('next_unlock_type_cn')}
- 解禁压力：{g('lockup_pressure_cn')}
- 解禁提示：{g('lockup_action_cn')}

## 四、暗盘与上市后路径
- 暗盘开盘：{g('gray_open_ret_pct')}
- 暗盘收盘：{g('gray_close_ret_pct')}
- 首日收盘收益：{g('d1_close_ret')}
- 20D最大涨幅：{g('max_20_ret')}
- 20D最大压力：{g('min_20_ret')}
- 180D最大涨幅：{g('max_180_ret')}
- 180D最大压力：{g('min_180_ret')}
- 路径标签：{g('path_label')}
- 行情状态：{g('quote_status')}

## 五、业务简介与募资用途
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

## 2. Stage and Deal Structure
- Lifecycle Stage: {g('lifecycle_stage')}
- Application Status: {g('application_status')}
- Listing Date: {g('listing_date')}
- Issue Price: {g('issue_price')}
- Offer Price Range: {g('offer_price_low')} - {g('offer_price_high')}
- Public Subscription Multiple: {g('public_subscription_multiple', g('public_subscription_multiple_ballot'))}
- One-lot Success Rate: {g('one_lot_success_rate_pct')}
- Margin Multiple: {g('margin_multiple')}

## 3. Cornerstone, Syndicate and Lock-up
- Cornerstone Count: {g('cornerstone_count')}
- Cornerstone Amount: {g('cornerstone_amount_hkd')}
- Major Cornerstones: {g('cornerstone_top_names')}
- Sponsor: {g('sponsor')}
- Overall Coordinator: {g('overall_coordinator')}
- Next Unlock Date: {g('next_unlock_date')}
- Unlock Type: {g('next_unlock_type_en')}
- Lock-up Pressure: {g('lockup_pressure_en')}
- Lock-up Action: {g('lockup_action_en')}

## 4. Gray Market and Post-listing Path
- Gray Open: {g('gray_open_ret_pct')}
- Gray Close: {g('gray_close_ret_pct')}
- D1 Close Return: {g('d1_close_ret')}
- 20D Max Upside: {g('max_20_ret')}
- 20D Max Pressure: {g('min_20_ret')}
- 180D Max Upside: {g('max_180_ret')}
- 180D Max Pressure: {g('min_180_ret')}
- Path Label: {g('path_label')}
- Quote Status: {g('quote_status')}

## 5. Business Scope and Use of Proceeds
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

listed_mask = pool.get("listing_date", pd.Series(pd.NaT, index=pool.index)).notna()
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
    cols = [tier_col, "code", "name", "lifecycle_stage", "listing_date", "industry_level_1", "overall_score", "primary_recommendation", "secondary_recommendation", "lockup_pressure_cn" if lang == "中文" else "lockup_pressure_en", "final_recommendation"]
    display_table(view.sort_values("overall_score", ascending=False, na_position="last"), lang, cols, 560)
    download_button(view, "investment_decision_pool.csv", lang)

elif page == "a1":
    st.subheader(T["pages"]["a1"])
    if lang == "中文":
        st.info("A1阶段不直接给买入建议，重点是研究优先级、额度准备和下一事件跟踪。")
    else:
        st.info("The A1 stage does not produce a buy recommendation; it ranks research priority, allocation preparation and next-event monitoring.")
    a1 = view[view.get("application_date", pd.Series(pd.NaT, index=view.index)).notna()].copy()
    cols = ["a1_priority_cn" if lang == "中文" else "a1_priority_en", "temp_code", "code", "name", "application_date", "first_application_date", "hearing_date", "application_status", "a1_score", "sponsor", "overall_coordinator", "industry_level_1", "business_scope", "a1_action_cn" if lang == "中文" else "a1_action_en"]
    display_table(a1.sort_values("a1_score", ascending=False, na_position="last"), lang, cols, 620)
    with st.expander(tr(lang, "standards"), expanded=True):
        if lang == "中文":
            st.markdown("""
| 档位 | 定义 | 动作 |
|---|---|---|
| A 重点跟踪 | 已通过聆讯或项目推进度高，保荐/中介完整，业务简介清晰 | 立即建档，安排行业与公司研究，提前关注额度 |
| B 研究池 | 处理中且资料较完整，行业或中介有一定看点 | 等招股书、估值区间和发行结构 |
| C 观察 | 申请进展一般或信息不完整 | 保留观察，等待聆讯或结构改善 |
| D 暂不覆盖 | 失效、撤回、信息缺失或可交易性差 | 除非后续重新递表并改善，否则不投入资源 |
""")
        else:
            st.markdown("""
| Tier | Definition | Action |
|---|---|---|
| A High-priority watch | Hearing passed or advanced process; complete syndicate; clear business profile | Open research file and prepare allocation discussion |
| B Research pool | Active filing with adequate information and some sector/syndicate merit | Wait for prospectus, valuation range and deal structure |
| C Monitor | Limited progress or incomplete information | Monitor until hearing or structure improves |
| D No active coverage | Lapsed/withdrawn, missing information or weak tradability | No resource allocation unless refiling improves |
""")

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
