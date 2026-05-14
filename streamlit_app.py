from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

BASE = Path("deploy_data")
CONFIG = Path("config/weight_profiles.json")

st.set_page_config(page_title="港股 IPO / 二级交易投资决策系统", layout="wide")


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
        "app_title": "港股 IPO / 二级交易投资决策系统",
        "caption": "覆盖 A1 项目、招股期、暗盘/首日，以及所有2024年后上市公司的二级交易决策框架。",
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
            "actions": "① 今日决策清单",
            "dashboard": "② 决策总览",
            "a1": "③ A1项目观察池",
            "ipo": "④ 招股期参与决策",
            "gray": "⑤ 暗盘与首日交易",
            "post": "⑥ 二级市场交易状态机",
            "lockup": "⑦ 解禁与供给压力",
            "weights": "⑧ 评分标准与权重设置",
            "backtest": "⑨ 回测与有效性验证",
            "memo": "⑩ 单票投资备忘录",
            "research": "⑪ 人工研究评分",
            "review": "⑫ 人工复核池",
            "update": "⑬ 数据更新",
            "quality": "⑭ 数据质量",
        },
        "metric_total": "样本数",
        "metric_a1": "A1/申请项目",
        "metric_listed": "2024+已上市",
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
        "app_title": "HK IPO & Secondary Trading Decision System",
        "caption": "A full lifecycle decision framework covering A1 filings, IPO subscription, gray market/first day and secondary trading for all companies listed since 2024.",
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
            "actions": "① Today's Action List",
            "dashboard": "② Decision Dashboard",
            "a1": "③ A1 Project Watchlist",
            "ipo": "④ IPO Participation Decision",
            "gray": "⑤ Gray Market & First Day",
            "post": "⑥ Secondary-market Trading State Machine",
            "lockup": "⑦ Lock-up & Supply Pressure",
            "weights": "⑧ Scoring Standards & Weights",
            "backtest": "⑨ Backtest & Effectiveness",
            "memo": "⑩ Single-name Investment Memo",
            "research": "⑪ Manual Research Scores",
            "review": "⑫ Manual Review Queue",
            "update": "⑬ Data Update",
            "quality": "⑭ Data Quality",
        },
        "metric_total": "Samples",
        "metric_a1": "A1 / Filing projects",
        "metric_listed": "2024+ Listed",
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


COL_ZH.update({
    "action_category_cn": "动作分类", "action_priority_cn": "优先级", "action_reason_cn": "触发原因", "review_reason_cn": "复核原因",
    "manual_quality_rating": "人工基本面评级", "manual_quality_score": "人工基本面分", "industry_view": "行业观点", "valuation_view": "估值观点", "research_comment": "研究备注", "updated_by": "更新人", "updated_date": "更新日期",
    "rating_bucket": "评级档位", "sample_count": "样本数", "sample_pct": "样本占比", "target_range": "建议占比", "calibration_note_cn": "校准提示",
    "tradingview_url": "TradingView图表", "current_stage_score": "当前阶段分", "dashboard_rating_cn": "当前评级",
    "decision_type_cn": "决策类型", "listed_age_bucket_cn": "上市分层", "listed_days": "上市天数",
    "quant_path_label_cn": "量化路径/状态", "relative_to_issue_pct": "较发行价", "last_close": "最近收盘",
    "last_quote_date": "最近行情日", "ret20_current": "近20日收益", "ret60_current": "近60日收益",
    "drawdown_from_quote_high": "距行情高点回撤", "quote_freshness_note_cn": "路径说明",
    "quote_freshness_cn": "行情新鲜度", "score_confidence_cn": "评分置信度", "date_check_cn": "日期校验",
    "secondary_rating_cn": "二级评级", "secondary_action_cn": "二级操作建议",
})
COL_EN.update({
    "action_category_en": "Action Category", "action_priority_en": "Priority", "action_reason_en": "Trigger Reason", "review_reason_en": "Review Reason",
    "manual_quality_rating": "Manual Fundamental Rating", "manual_quality_score": "Manual Fundamental Score", "industry_view": "Industry View", "valuation_view": "Valuation View", "research_comment": "Research Comment", "updated_by": "Updated By", "updated_date": "Updated Date",
    "rating_bucket": "Rating Bucket", "sample_count": "Samples", "sample_pct": "Sample %", "target_range": "Target Range", "calibration_note_en": "Calibration Note",
    "tradingview_url": "TradingView Chart", "current_stage_score": "Current-stage Score", "dashboard_rating_en": "Current Rating",
    "decision_type_en": "Decision Type", "listed_age_bucket_en": "Listing-age Bucket", "listed_days": "Days Listed",
    "quant_path_label_en": "Quant Path / State", "relative_to_issue_pct": "Vs Issue Price", "last_close": "Last Close",
    "last_quote_date": "Last Quote Date", "ret20_current": "20D Return", "ret60_current": "60D Return",
    "drawdown_from_quote_high": "Drawdown from Quote High", "quote_freshness_note_en": "Path Note",
    "quote_freshness_en": "Quote Freshness", "score_confidence_en": "Score Confidence", "date_check_en": "Date Check",
    "secondary_rating_en": "Secondary Rating", "secondary_action_en": "Secondary Action",
})

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


def is_listed_mask(df: pd.DataFrame) -> pd.Series:
    listing = safe_date_series(df, "listing_date")
    today = pd.Timestamp.today().normalize()
    return listing.notna() & (listing <= today)


def hk_tradingview_url(code: object) -> str:
    if pd.isna(code):
        return ""
    c = str(code).strip().upper()
    if not c or c.startswith("H") or ".HK" not in c:
        return ""
    sym = c.replace(".HK", "")
    sym = sym.lstrip("0") or sym
    return f"https://www.tradingview.com/symbols/HKEX-{sym}/"


def add_tradingview_links(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "code" in out.columns:
        out["tradingview_url"] = out["code"].map(hk_tradingview_url)
    return out


def add_quote_current_metrics(df: pd.DataFrame, quotes: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if quotes.empty or "code" not in quotes.columns:
        for c in ["last_close", "last_quote_date", "ret20_current", "ret60_current", "drawdown_from_quote_high", "quote_freshness_cn", "quote_freshness_en"]:
            if c not in out.columns:
                out[c] = np.nan if c not in ["quote_freshness_cn", "quote_freshness_en"] else ("缺失" if c.endswith("cn") else "Missing")
        return out
    q = quotes.copy()
    q["date"] = pd.to_datetime(q.get("date"), errors="coerce")
    q["close"] = to_num(q.get("close", pd.Series(np.nan, index=q.index)))
    q = q.dropna(subset=["code", "date", "close"]).sort_values(["code", "date"])
    if q.empty:
        for c in ["quote_freshness_cn", "quote_freshness_en"]:
            out[c] = "缺失" if c.endswith("cn") else "Missing"
        return out
    today = pd.Timestamp.today().normalize()
    rows = []
    for code, g in q.groupby("code"):
        g = g.sort_values("date")
        last_close = float(g["close"].iloc[-1]) if len(g) else np.nan
        last_date = g["date"].iloc[-1] if len(g) else pd.NaT
        c20 = float(g["close"].iloc[-21]) if len(g) >= 21 else np.nan
        c60 = float(g["close"].iloc[-61]) if len(g) >= 61 else np.nan
        high = float(g["close"].max()) if len(g) else np.nan
        lag = (today - pd.to_datetime(last_date).normalize()).days if pd.notna(last_date) else np.nan
        if pd.isna(lag):
            qcn, qen = "缺失", "Missing"
        elif lag <= 3:
            qcn, qen = "正常", "Fresh"
        elif lag <= 10:
            qcn, qen = "轻微滞后", "Slightly stale"
        else:
            qcn, qen = "明显滞后", "Stale"
        rows.append({
            "code": code,
            "last_close": last_close,
            "last_quote_date": last_date,
            "ret20_current": last_close / c20 - 1 if pd.notna(c20) and c20 else np.nan,
            "ret60_current": last_close / c60 - 1 if pd.notna(c60) and c60 else np.nan,
            "drawdown_from_quote_high": last_close / high - 1 if pd.notna(high) and high else np.nan,
            "quote_freshness_cn": qcn,
            "quote_freshness_en": qen,
        })
    m = pd.DataFrame(rows).set_index("code")
    if "code" in out.columns:
        for c in m.columns:
            out[c] = out["code"].map(m[c])
    return out


def add_listing_age_and_path(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    today = pd.Timestamp.today().normalize()
    listing = safe_date_series(out, "listing_date")
    out["listed_days"] = (today - listing).dt.days
    def age_cn(x):
        if pd.isna(x): return "未上市"
        if x <= 30: return "新上市观察期(0-30D)"
        if x <= 180: return "半新股交易期(31-180D)"
        return "次新延伸期(180D+)"
    def age_en(x):
        if pd.isna(x): return "Unlisted"
        if x <= 30: return "New listing watch (0-30D)"
        if x <= 180: return "Newly listed trading (31-180D)"
        return "Extended post-IPO (180D+)"
    out["listed_age_bucket_cn"] = out["listed_days"].map(age_cn)
    out["listed_age_bucket_en"] = out["listed_days"].map(age_en)
    issue = to_num(out.get("issue_price", pd.Series(np.nan, index=out.index)))
    last = to_num(out.get("last_close", pd.Series(np.nan, index=out.index)))
    out["relative_to_issue_pct"] = (last / issue - 1).replace([np.inf, -np.inf], np.nan)
    d1 = to_num(out.get("d1_close_ret", pd.Series(np.nan, index=out.index)))
    max20 = to_num(out.get("max_20_ret", pd.Series(np.nan, index=out.index)))
    min20 = to_num(out.get("min_20_ret", pd.Series(np.nan, index=out.index)))
    max60 = to_num(out.get("max_60_ret", pd.Series(np.nan, index=out.index)))
    min60 = to_num(out.get("min_60_ret", pd.Series(np.nan, index=out.index)))
    max180 = to_num(out.get("max_180_ret", pd.Series(np.nan, index=out.index)))
    min180 = to_num(out.get("min_180_ret", pd.Series(np.nan, index=out.index)))
    rel_issue = out["relative_to_issue_pct"]
    ret20 = to_num(out.get("ret20_current", pd.Series(np.nan, index=out.index)))
    ret60 = to_num(out.get("ret60_current", pd.Series(np.nan, index=out.index)))
    dd_high = to_num(out.get("drawdown_from_quote_high", pd.Series(np.nan, index=out.index)))
    labels_cn, labels_en, notes_cn, notes_en = [], [], [], []
    qrows = to_num(out.get("quote_rows", pd.Series(np.nan, index=out.index))).fillna(0)
    for idx, r in out.iterrows():
        days = r.get("listed_days")
        qr = qrows.loc[idx] if idx in qrows.index else 0
        if pd.isna(days):
            labels_cn.append("未上市"); labels_en.append("Unlisted"); notes_cn.append("未上市项目不适用二级路径"); notes_en.append("Secondary path not applicable to unlisted projects"); continue
        if qr < 5:
            labels_cn.append("数据不足/新上市观察"); labels_en.append("Insufficient data / new listing watch"); notes_cn.append("有效行情少于5行，暂不做路径结论"); notes_en.append("Fewer than 5 valid quote rows; no path conclusion yet"); continue
        if days > 180:
            li = r.get("relative_to_issue_pct")
            r20 = r.get("ret20_current")
            r60 = r.get("ret60_current")
            dd = r.get("drawdown_from_quote_high")
            if pd.notna(r60) and pd.notna(dd) and r60 >= 0.15 and dd > -0.20:
                labels_cn.append("趋势延续"); labels_en.append("Trend continuation"); notes_cn.append("60日收益≥15%且距行情高点回撤<20%"); notes_en.append("60D return ≥15% and drawdown from quote high <20%")
            elif pd.notna(dd) and dd > -0.15 and pd.notna(r20) and -0.10 <= r20 <= 0.10:
                labels_cn.append("高位震荡"); labels_en.append("High-level consolidation"); notes_cn.append("距行情高点回撤<15%，20日收益在±10%内"); notes_en.append("Drawdown from quote high <15%, 20D return within ±10%")
            elif pd.notna(li) and li >= 0 and (idx in min180.index) and pd.notna(min180.loc[idx]) and min180.loc[idx] <= -0.05:
                labels_cn.append("长期破发修复"); labels_en.append("Long break-price recovery"); notes_cn.append("曾跌破发行价，当前重新高于发行价"); notes_en.append("Previously broke issue price, now above issue price")
            elif pd.notna(li) and li <= -0.10 and (pd.isna(r60) or r60 < 0.15):
                labels_cn.append("长期破发弱势"); labels_en.append("Long-term weak below issue price"); notes_cn.append("上市180日后仍低于发行价10%以上且反弹不足"); notes_en.append("After 180D still >10% below issue price with weak rebound")
            elif pd.notna(dd) and dd <= -0.30:
                labels_cn.append("高位回撤预警"); labels_en.append("High-level drawdown alert"); notes_cn.append("从行情高点回撤≥30%"); notes_en.append("Drawdown from quote high ≥30%")
            else:
                labels_cn.append("次新延伸观察"); labels_en.append("Extended post-IPO watch"); notes_cn.append("上市180日后继续按趋势、成交和解禁后再定价观察"); notes_en.append("After 180D, monitor trend, turnover and post-lock-up repricing")
            continue
        # 0-180D quantitative path rules
        v_d1 = d1.loc[idx] if idx in d1.index else np.nan
        v_max20 = max20.loc[idx] if idx in max20.index else np.nan
        v_min20 = min20.loc[idx] if idx in min20.index else np.nan
        v_max60 = max60.loc[idx] if idx in max60.index else np.nan
        v_min60 = min60.loc[idx] if idx in min60.index else np.nan
        v_rel = rel_issue.loc[idx] if idx in rel_issue.index else np.nan
        if pd.notna(v_d1) and pd.notna(v_min20) and pd.notna(v_max20) and v_d1 >= 0.10 and v_min20 >= -0.05 and v_max20 >= 0.20:
            labels_cn.append("上市即强势"); labels_en.append("Strong from listing"); notes_cn.append("首日收盘≥10%，20日低点不低于发行价-5%，20日最大涨幅≥20%"); notes_en.append("D1 close ≥10%, 20D low not below issue price -5%, 20D max gain ≥20%")
        elif ((pd.notna(v_min20) and v_min20 <= -0.10) or (pd.notna(v_min60) and v_min60 <= -0.15)) and pd.notna(v_max60) and v_max60 >= 0.25 and pd.notna(v_rel) and v_rel >= 0:
            labels_cn.append("深V反弹"); labels_en.append("Deep-V rebound"); notes_cn.append("20日最大跌幅≤-10%或60日压力≤-15%，之后60日最大反弹≥25%且站回发行价"); notes_en.append("20D drawdown ≤-10% or 60D pressure ≤-15%, later 60D rebound ≥25% and back above issue price")
        elif pd.notna(v_max20) and v_max20 >= 0.15 and ((pd.notna(v_rel) and v_rel < 0) or (pd.notna(v_min60) and v_min60 <= -0.30)):
            labels_cn.append("升后破发"); labels_en.append("Pump then break"); notes_cn.append("前20日最大涨幅≥15%，但之后跌破发行价或60日压力≤-30%"); notes_en.append("20D max gain ≥15%, then below issue price or 60D pressure ≤-30%")
        elif ((pd.notna(v_d1) and v_d1 < 0) or (pd.notna(v_min20) and v_min20 <= -0.05)) and (pd.isna(v_rel) or v_rel < 0) and (pd.isna(v_max60) or v_max60 < 0.15):
            labels_cn.append("一路破发"); labels_en.append("Persistent break issue price"); notes_cn.append("首日或20日内跌破发行价-5%，且60日最大反弹<15%/未站回发行价"); notes_en.append("Breaks issue price by D1/within 20D and 60D max rebound <15% / not back above issue price")
        elif pd.notna(v_max20) and pd.notna(v_min20) and -0.10 <= (v_d1 if pd.notna(v_d1) else 0) <= 0.15 and v_min20 >= -0.15 and v_max20 <= 0.20:
            labels_cn.append("温和交易型"); labels_en.append("Moderate trading path"); notes_cn.append("20日收益/波动未形成强趋势，最大回撤不超过15%、最大涨幅不超过20%"); notes_en.append("No strong trend in first 20D; max drawdown <=15% and max gain <=20%")
        else:
            labels_cn.append("观察中"); labels_en.append("Under observation"); notes_cn.append("未触发强势、深V、破发或升后破发的量化阈值"); notes_en.append("No quantitative threshold triggered for strong/deep-V/break/pump-then-break path")
    out["quant_path_label_cn"] = labels_cn
    out["quant_path_label_en"] = labels_en
    out["quote_freshness_note_cn"] = notes_cn
    out["quote_freshness_note_en"] = notes_en
    return out


def secondary_rating(score, lockup_cn=None):
    if pd.isna(score):
        return ("信息不足", "Insufficient data", "补充行情/成交数据", "Add quote / turnover data")
    score = float(score)
    if lockup_cn in ["高"] and score < 80:
        return ("C5 等待风险释放", "C5 Wait for risk release", "解禁压力高，不追高，等待供给压力释放", "High lock-up pressure; avoid chasing until supply pressure clears")
    if score >= 75:
        return ("A 二级趋势确认", "A Secondary trend confirmed", "可参与；优先等回踩或成交确认", "Actionable; prefer pullback or turnover confirmation")
    if score >= 60:
        return ("B 二级交易观察", "B Secondary trading watch", "小仓或等待确认", "Small allocation or wait for confirmation")
    if score >= 45:
        return ("C4 等待二级买点", "C4 Wait for secondary entry", "不追高，等待深V、站回发行价或趋势确认", "Do not chase; wait for deep-V, reclaim of issue price or trend confirmation")
    return ("D 破发/弱势回避", "D Avoid weak / broken structure", "二级结构弱，原则上回避", "Weak secondary structure; avoid by default")


def build_secondary_view(df: pd.DataFrame, quotes: pd.DataFrame) -> pd.DataFrame:
    d = add_quote_current_metrics(df.copy(), quotes)
    d = add_listing_age_and_path(d)
    d = add_tradingview_links(d)
    d = d[is_listed_mask(d)].copy()
    # The secondary trading universe is all companies listed from 2024 onward.
    ld = safe_date_series(d, "listing_date")
    d = d[ld >= pd.Timestamp("2024-01-01")].copy()
    if d.empty:
        return d
    # prefer real listed codes and one row per listed stock
    d["_code_key"] = d.get("code", pd.Series("", index=d.index)).astype(str).str.upper().str.strip()
    d = d[d["_code_key"].ne("")].copy()
    d["_score_sort"] = to_num(d.get("secondary_score", pd.Series(np.nan, index=d.index))).fillna(to_num(d.get("post_listing_score", pd.Series(np.nan, index=d.index))).fillna(0))
    d["_date_sort"] = safe_date_series(d, "listing_date")
    d = d.sort_values(["_code_key", "_date_sort", "_score_sort"], ascending=[True, False, False])
    d = d.drop_duplicates("_code_key", keep="first").copy()
    sec_score = to_num(d.get("secondary_score", pd.Series(np.nan, index=d.index))).fillna(to_num(d.get("post_listing_score", pd.Series(np.nan, index=d.index))))
    d["current_stage_score"] = sec_score
    ratings = [secondary_rating(sc, r.get("lockup_pressure_cn")) for sc, (_, r) in zip(sec_score, d.iterrows())]
    d["secondary_rating_cn"] = [x[0] for x in ratings]
    d["secondary_rating_en"] = [x[1] for x in ratings]
    d["secondary_action_cn"] = [x[2] for x in ratings]
    d["secondary_action_en"] = [x[3] for x in ratings]
    return d.drop(columns=[c for c in ["_code_key", "_score_sort", "_date_sort"] if c in d.columns])


def primary_rating(score):
    if pd.isna(score): return ("C1 等待发行资料", "C1 Wait for deal terms")
    score = float(score)
    if score >= 80: return ("A 强参与", "A Strong participate")
    if score >= 70: return ("B 小额/中等参与", "B Small / moderate participate")
    if score >= 60: return ("C2 谨慎参与，等配发/暗盘", "C2 Cautious; wait for allotment/gray")
    if score >= 50: return ("C3 只看二级", "C3 Secondary only")
    return ("D 回避", "D Avoid")


def a1_project_rating(score, status=None):
    if status_is_lapsed(status):
        return ("C6 失效观察", "C6 Lapsed filing watch")
    if pd.isna(score): return ("C1 等待发行资料", "C1 Wait for deal terms")
    score = float(score)
    if score >= 80: return ("A 高质量IPO候选", "A High-quality IPO candidate")
    if score >= 70: return ("B 值得研究", "B Worth research")
    if score >= 60: return ("B- 可参与但需验证", "B- Participate only after validation")
    if score >= 50: return ("C1 等待发行资料", "C1 Wait for deal terms")
    return ("D 项目质量较弱", "D Low project quality")


def build_dashboard_view(df: pd.DataFrame, quotes: pd.DataFrame) -> pd.DataFrame:
    """One row per company/stock for the dashboard. Listed companies use secondary ratings only; unlisted companies use project/IPO-stage ratings."""
    listed = build_secondary_view(df, quotes)
    if not listed.empty:
        listed["decision_type_cn"] = "二级交易"
        listed["decision_type_en"] = "Secondary trading"
        listed["dashboard_rating_cn"] = listed["secondary_rating_cn"]
        listed["dashboard_rating_en"] = listed["secondary_rating_en"]
        listed["current_stage_score"] = to_num(listed.get("current_stage_score", pd.Series(np.nan, index=listed.index)))
        listed["next_action_cn"] = listed.get("secondary_action_cn", listed.get("next_action_cn", ""))
        listed["next_action_en"] = listed.get("secondary_action_en", listed.get("next_action_en", ""))
    a1_company, _ = build_a1_company_view(df)
    unlisted = a1_company.copy()
    if not unlisted.empty:
        # If deal terms already exist, use IPO participation score; otherwise A1 quality score.
        has_terms = to_num(unlisted.get("issue_price", pd.Series(np.nan, index=unlisted.index))).notna() | to_num(unlisted.get("offer_price_high", pd.Series(np.nan, index=unlisted.index))).notna()
        unlisted["decision_type_cn"] = np.where(has_terms, "招股期参与", "A1项目质量")
        unlisted["decision_type_en"] = np.where(has_terms, "IPO participation", "A1 project quality")
        current_scores = to_num(unlisted.get("primary_score", pd.Series(np.nan, index=unlisted.index))).where(has_terms, to_num(unlisted.get("a1_quality_score", pd.Series(np.nan, index=unlisted.index))))
        unlisted["current_stage_score"] = current_scores
        dr_cn, dr_en = [], []
        for i, r in unlisted.iterrows():
            if has_terms.loc[i]:
                cn, en = primary_rating(r.get("primary_score"))
            else:
                cn, en = a1_project_rating(r.get("a1_quality_score"), r.get("application_status"))
            dr_cn.append(cn); dr_en.append(en)
        unlisted["dashboard_rating_cn"] = dr_cn
        unlisted["dashboard_rating_en"] = dr_en
    out = pd.concat([listed, unlisted], ignore_index=True, sort=False)
    out = add_tradingview_links(out)
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

    # Management-use confidence and date checks. These do not change project-quality scores.
    completeness_cols = ["industry_level_1", "business_scope", "sponsor", "overall_coordinator", "application_status"]
    def confidence_row(r):
        present = 0
        for c in completeness_cols:
            v = r.get(c, "")
            if pd.notna(v) and str(v).strip() not in ["", "--", "None", "nan"]:
                present += 1
        if pd.notna(r.get("a1_quality_score")):
            present += 1
        if present >= 5:
            return ("高", "High")
        if present >= 3:
            return ("中", "Medium")
        return ("低", "Low")
    conf = latest.apply(confidence_row, axis=1)
    latest["score_confidence_cn"] = [x[0] for x in conf]
    latest["score_confidence_en"] = [x[1] for x in conf]
    today = pd.Timestamp.today().normalize()
    def date_check_row(r):
        first = pd.to_datetime(r.get("first_application_date_calc"), errors="coerce")
        latest_dt = pd.to_datetime(r.get("latest_application_date_calc"), errors="coerce")
        if pd.notna(first) and pd.notna(latest_dt) and first > latest_dt:
            return ("日期需复核：首次申请日晚于最近申请日", "Check dates: first filing is later than latest filing")
        if pd.notna(latest_dt) and latest_dt > today + pd.DateOffset(days=60):
            return ("日期需复核：最近申请日明显晚于当前日期", "Check dates: latest filing date is far in the future")
        return ("正常", "OK")
    dchk = latest.apply(date_check_row, axis=1)
    latest["date_check_cn"] = [x[0] for x in dchk]
    latest["date_check_en"] = [x[1] for x in dchk]
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
        # TradingView is embedded into code/name cells, not displayed as a standalone column.
        cols = [c for c in cols if c != "tradingview_url"]
        out = out[[c for c in cols if c in out.columns]]

    # Make code/name clickable to TradingView for listed stocks. The URL carries a tv_display query
    # parameter so Streamlit LinkColumn can display the code/name text instead of the raw URL.
    tv_urls = df.get("tradingview_url", pd.Series("", index=df.index)).fillna("").astype(str)
    if "code" in out.columns:
        code_text = out["code"].fillna("").astype(str)
        out["code"] = [f"{u}?tv_display={c}" if u and c else c for u, c in zip(tv_urls, code_text)]
    if "name" in out.columns:
        name_text = out["name"].fillna("").astype(str)
        out["name"] = [f"{u}?tv_display={n}" if u and n else n for u, n in zip(tv_urls, name_text)]

    # format selected columns
    for c in ["d1_close_ret", "max_20_ret", "min_20_ret", "max_60_ret", "min_60_ret", "max_180_ret", "min_180_ret", "relative_to_issue_pct", "ret20_current", "ret60_current", "drawdown_from_quote_high"]:
        if c in out.columns: out[c] = out[c].map(fmt_pct)
    for c in ["gray_open_ret_pct", "gray_close_ret_pct", "d1_open_ret_pct", "d1_close_ret_pct", "one_lot_success_rate_pct"]:
        if c in out.columns: out[c] = out[c].map(fmt_pct_raw)
    for c in ["首日均值", "二十日最大均值", "六十日最大均值", "一八零日最大均值", "二十日最小均值", "交易成功率", "强势或深V率", "坏路径率", "top_tradeable_20d_rate", "top_strong_or_deepv_rate", "top_bad_path_rate", "top_d1_mean", "top_max20_mean", "top_min20_mean", "sample_pct"]:
        if c in out.columns: out[c] = out[c].map(fmt_pct)
    for c in ["overall_score", "current_stage_score", "primary_score", "secondary_score", "cornerstone_score", "a1_score", "a1_quality_score", "a1_industry_preference_score", "a1_company_quality_score", "a1_sponsor_quality_score", "a1_peer_ipo_score", "a1_tradability_score", "a1_market_window_score", "custom_score", "margin_multiple", "public_subscription_multiple", "public_subscription_multiple_ballot", "cornerstone_value_to_avg20_turnover", "last_close"]:
        if c in out.columns: out[c] = out[c].map(lambda x: fmt_num(x, 1))
    for c in ["cornerstone_amount_hkd", "margin_amount_hkd", "avg20_trading_value_hkd_est"]:
        if c in out.columns: out[c] = out[c].map(fmt_money)
    labelled = label_cols(out, lang)
    column_config = {}
    code_label = "代码" if lang == "中文" else "Code"
    name_label = "简称" if lang == "中文" else "Name"
    for link_col in [code_label, name_label]:
        if link_col in labelled.columns:
            column_config[link_col] = st.column_config.LinkColumn(link_col, display_text=r"tv_display=([^&#]+)")
    st.dataframe(labelled, use_container_width=True, hide_index=True, height=height, column_config=column_config)


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
        "上市后二级路径": "post_listing_score",
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


def manual_score_from_rating(value):
    if pd.isna(value):
        return np.nan
    s = str(value).strip()
    mapping = {
        "强": 90, "较强": 78, "中性": 60, "较弱": 45, "回避": 20,
        "Strong": 90, "Positive": 78, "Neutral": 60, "Weak": 45, "Avoid": 20,
        "A": 90, "B": 78, "C": 60, "D": 35,
    }
    return mapping.get(s, np.nan)


def apply_manual_research_scores(df: pd.DataFrame, manual: pd.DataFrame) -> pd.DataFrame:
    """Merge analyst research views into the model without requiring a database.
    The CSV can be edited locally and uploaded as deploy_data/manual_research_scores.csv.
    Manual company-quality score only affects the A1 company-quality dimension and recalculates A1 quality score.
    """
    out = df.copy()
    if manual is None or manual.empty:
        for c in ["manual_quality_rating", "manual_quality_score", "industry_view", "valuation_view", "research_comment", "updated_by", "updated_date"]:
            if c not in out.columns:
                out[c] = np.nan
        return out
    m = manual.copy()
    # Normalize expected columns; tolerate Chinese column names.
    rename = {
        "代码": "code", "简称": "name", "公司": "name", "公司名称": "name", "人工基本面评级": "manual_quality_rating",
        "人工基本面分": "manual_quality_score", "行业观点": "industry_view", "估值观点": "valuation_view",
        "研究备注": "research_comment", "更新人": "updated_by", "更新日期": "updated_date",
    }
    m = m.rename(columns={k:v for k,v in rename.items() if k in m.columns})
    if "code" not in m.columns:
        m["code"] = ""
    if "name" not in m.columns:
        m["name"] = ""
    m["_code_key"] = m["code"].fillna("").astype(str).str.upper().str.strip()
    m["_name_key"] = m["name"].fillna("").map(normalize_name_value)
    if "manual_quality_score" in m.columns:
        m["manual_quality_score"] = to_num(m["manual_quality_score"])
    else:
        m["manual_quality_score"] = np.nan
    if "manual_quality_rating" in m.columns:
        rating_score = m["manual_quality_rating"].map(manual_score_from_rating)
        m["manual_quality_score"] = m["manual_quality_score"].combine_first(rating_score)
    m = m.sort_values(["_code_key", "_name_key"]).drop_duplicates(["_code_key", "_name_key"], keep="last")
    out["_code_key"] = out.get("code", pd.Series("", index=out.index)).fillna("").astype(str).str.upper().str.strip()
    out["_name_key"] = out.get("name", pd.Series("", index=out.index)).fillna("").map(normalize_name_value)
    by_code = m[m["_code_key"].ne("")].set_index("_code_key")
    by_name = m[m["_name_key"].ne("")].set_index("_name_key")
    cols = ["manual_quality_rating", "manual_quality_score", "industry_view", "valuation_view", "research_comment", "updated_by", "updated_date"]
    for c in cols:
        if c not in out.columns:
            out[c] = np.nan
        if c in by_code.columns:
            out[c] = out["_code_key"].map(by_code[c]).combine_first(out[c])
        if c in by_name.columns:
            out[c] = out["_name_key"].map(by_name[c]).combine_first(out[c])
    # If manual quality exists, overwrite company quality dimension and recalculate A1 quality score under default weights.
    mq = to_num(out.get("manual_quality_score", pd.Series(np.nan, index=out.index))).clip(0, 100)
    has_mq = mq.notna()
    if "a1_company_quality_score" in out.columns:
        out.loc[has_mq, "a1_company_quality_score"] = mq[has_mq]
    if {"a1_industry_preference_score", "a1_company_quality_score", "a1_sponsor_quality_score", "a1_peer_ipo_score", "a1_tradability_score", "a1_market_window_score"}.issubset(out.columns):
        out["a1_quality_score"] = (
            to_num(out["a1_industry_preference_score"]).fillna(50) * 0.35 +
            to_num(out["a1_company_quality_score"]).fillna(50) * 0.20 +
            to_num(out["a1_sponsor_quality_score"]).fillna(50) * 0.15 +
            to_num(out["a1_peer_ipo_score"]).fillna(50) * 0.15 +
            to_num(out["a1_tradability_score"]).fillna(50) * 0.10 +
            to_num(out["a1_market_window_score"]).fillna(50) * 0.05
        ).round(1)
        # refresh user-facing buckets
        out["a1_research_priority_cn"] = out["a1_quality_score"].map(lambda x: "A 重点跟踪" if pd.notna(x) and x >= 80 else "B+ 重点研究" if pd.notna(x) and x >= 70 else "B 研究池" if pd.notna(x) and x >= 60 else "C 观察" if pd.notna(x) and x >= 50 else "D 低优先级")
        out["a1_research_priority_en"] = out["a1_quality_score"].map(lambda x: "A High-priority watch" if pd.notna(x) and x >= 80 else "B+ Priority research" if pd.notna(x) and x >= 70 else "B Research pool" if pd.notna(x) and x >= 60 else "C Monitor" if pd.notna(x) and x >= 50 else "D Low priority")
        out["future_ipo_participation_cn"] = out["a1_quality_score"].map(lambda x: "拟重点参与，等待发行验证" if pd.notna(x) and x >= 80 else "倾向参与，需看定价" if pd.notna(x) and x >= 70 else "可参与，需强发行信号" if pd.notna(x) and x >= 60 else "暂不主动参与" if pd.notna(x) and x >= 50 else "暂不参与")
        out["future_ipo_participation_en"] = out["a1_quality_score"].map(lambda x: "Likely priority participation, pending deal validation" if pd.notna(x) and x >= 80 else "Positive bias, subject to pricing" if pd.notna(x) and x >= 70 else "Participate only with strong deal signals" if pd.notna(x) and x >= 60 else "No proactive participation" if pd.notna(x) and x >= 50 else "No participation")
    return out.drop(columns=[c for c in ["_code_key", "_name_key"] if c in out.columns])


def build_today_actions(dashboard: pd.DataFrame) -> pd.DataFrame:
    if dashboard.empty:
        return dashboard
    rows = []
    for _, r in dashboard.iterrows():
        listed = pd.notna(pd.to_datetime(r.get("listing_date"), errors="coerce")) and pd.to_datetime(r.get("listing_date"), errors="coerce") <= pd.Timestamp.today().normalize()
        name, code = r.get("name", ""), r.get("code", "")
        base = r.to_dict()
        def add(cat_cn, cat_en, pri_cn, pri_en, reason_cn, reason_en):
            x = base.copy()
            x["action_category_cn"] = cat_cn; x["action_category_en"] = cat_en
            x["action_priority_cn"] = pri_cn; x["action_priority_en"] = pri_en
            x["action_reason_cn"] = reason_cn; x["action_reason_en"] = reason_en
            rows.append(x)
        score = pd.to_numeric(pd.Series([r.get("current_stage_score")]), errors="coerce").iloc[0]
        if not listed:
            stt = str(r.get("application_status", ""))
            if status_is_lapsed(stt):
                add("失效观察", "Lapsed filing watch", "中", "Medium", "未上市且最新申请失效，等待是否重新递表", "Unlisted and latest filing lapsed; wait for refiling")
            elif pd.notna(score) and score >= 75:
                add("A1重点建档", "A1 priority research", "高", "High", "项目质量分较高，建议提前建档和准备估值框架", "High project-quality score; build research file and valuation framework")
            elif pd.isna(r.get("issue_price")) and pd.isna(r.get("offer_price_high")):
                add("等待招股", "Wait for prospectus / deal terms", "中", "Medium", "尚缺发行价、募资规模、基石和账簿热度", "Waiting for offer price, deal size, cornerstone and bookbuilding signals")
            else:
                add("等待配发/暗盘确认", "Wait for allotment / gray confirmation", "中", "Medium", "已有发行资料但缺最终配发、孖展/中签或暗盘信号", "Deal terms available but allotment/margin/gray-market signal pending")
        else:
            rating = str(r.get("dashboard_rating_cn", ""))
            if rating.startswith("A"):
                add("二级趋势确认", "Secondary trend confirmed", "高", "High", "二级交易评分较高，趋势/价格结构触发关注", "High secondary score; trend/price structure warrants attention")
            elif "C4" in rating:
                add("等待二级买点", "Wait for secondary entry", "中", "Medium", "尚未出现合适买点，不追高，等待回踩/站回发行价/成交确认", "No entry yet; wait for pullback/reclaim of issue price/turnover confirmation")
            elif "C5" in rating or str(r.get("lockup_pressure_cn", "")) in ["高", "中"]:
                add("解禁前复核", "Review before lock-up", "高", "High", "解禁/供给压力进入观察窗口，交易前需复核承接", "Lock-up/supply pressure is in watch window; verify absorption before trading")
            elif rating.startswith("D"):
                add("破发/弱势回避", "Avoid broken / weak structure", "低", "Low", "二级结构弱或破发风险较高，原则上回避", "Weak secondary structure / break-price risk; avoid by default")
        # Data review overlay
        qfresh = str(r.get("quote_freshness_cn", ""))
        if qfresh in ["明显滞后", "缺失"] or str(r.get("score_confidence_cn", "")) == "低" or str(r.get("date_check_cn", "")) not in ["", "正常", "nan"]:
            add("数据需复核", "Data review required", "高", "High", "行情、评分置信度或日期字段存在复核项", "Quote freshness, score confidence or date fields require review")
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    priority_order = {"高": 0, "中": 1, "低": 2, "High": 0, "Medium": 1, "Low": 2}
    out["_p"] = out["action_priority_cn"].map(priority_order).fillna(out["action_priority_en"].map(priority_order)).fillna(9)
    out = out.sort_values(["_p", "current_stage_score"], ascending=[True, False], na_position="last").drop(columns=["_p"])
    return out


def build_rating_distribution(df: pd.DataFrame, rating_col: str) -> pd.DataFrame:
    if df.empty or rating_col not in df.columns:
        return pd.DataFrame()
    ser = df[rating_col].fillna("信息不足").astype(str).str[0].replace({"信":"NA", "I":"NA"})
    vc = ser.value_counts().reindex(["A", "B", "C", "D", "N", "NA"]).dropna()
    total = int(vc.sum()) or 1
    rows = []
    targets = {"A":"5%-15%", "B":"20%-35%", "C":"35%-50%", "D":"10%-25%"}
    for k, n in vc.items():
        if k == "N":
            continue
        pct = float(n)/total
        note_cn = "正常"
        note_en = "OK"
        if k == "A" and pct < 0.03: note_cn, note_en = "A档过少，阈值可能偏严", "Too few A names; threshold may be strict"
        if k == "A" and pct > 0.20: note_cn, note_en = "A档过多，区分度可能不足", "Too many A names; separation may be weak"
        if k == "D" and pct > 0.40: note_cn, note_en = "D档偏多，需检查数据缺失是否导致低分", "Too many D names; check whether missing data drives low scores"
        rows.append({"rating_bucket": k, "sample_count": int(n), "sample_pct": pct, "target_range": targets.get(k, "-"), "calibration_note_cn": note_cn, "calibration_note_en": note_en})
    return pd.DataFrame(rows)


def build_manual_review_pool(dashboard: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if dashboard.empty:
        return pd.DataFrame()
    for _, r in dashboard.iterrows():
        reasons_cn, reasons_en = [], []
        if str(r.get("quote_freshness_cn", "")) in ["明显滞后", "缺失"]:
            reasons_cn.append("行情明显滞后或缺失"); reasons_en.append("Quote is stale or missing")
        if str(r.get("score_confidence_cn", "")) == "低":
            reasons_cn.append("A1评分置信度低"); reasons_en.append("Low A1 score confidence")
        if str(r.get("date_check_cn", "")) not in ["", "正常", "nan"]:
            reasons_cn.append("申请日期字段异常"); reasons_en.append("Application date anomaly")
        if pd.isna(r.get("issue_price")) and pd.notna(r.get("listing_date")):
            reasons_cn.append("已上市但发行价缺失"); reasons_en.append("Listed but issue price missing")
        if str(r.get("lockup_pressure_cn", "")) in ["高"]:
            reasons_cn.append("高解禁压力"); reasons_en.append("High lock-up pressure")
        score = pd.to_numeric(pd.Series([r.get("current_stage_score")]), errors="coerce").iloc[0]
        if pd.notna(score) and score >= 75 and ("行情明显滞后或缺失" in reasons_cn or "A1评分置信度低" in reasons_cn):
            reasons_cn.append("高分但数据不完整"); reasons_en.append("High score but incomplete data")
        if reasons_cn:
            x = r.to_dict()
            x["review_reason_cn"] = "；".join(reasons_cn)
            x["review_reason_en"] = "; ".join(reasons_en)
            rows.append(x)
    return pd.DataFrame(rows)



def make_memo(row: pd.Series, lang: str) -> str:
    def g(c, default=""):
        v = row.get(c, default)
        if pd.isna(v):
            return default
        if isinstance(v, pd.Timestamp):
            return v.strftime("%Y-%m-%d")
        return v
    if lang == "中文":
        return f"""# 港股 IPO / 二级交易投资备忘录：{g('code')} {g('name')}

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

## 五、暗盘与上市后二级路径
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
manual_research = read_csv_any(BASE / "manual_research_scores.csv")
pool = apply_manual_research_scores(pool, manual_research)

# Sidebar
lang = st.sidebar.radio("语言 / Language", ["中文", "English"], horizontal=True)
T = TEXT[lang]
page_labels = list(T["pages"].values())
page_key_by_label = {v: k for k, v in T["pages"].items()}
page_label = st.sidebar.selectbox("页面 / Page", page_labels)
page = page_key_by_label[page_label]

st.title(tr(lang, "app_title"))
st.caption(tr(lang, "caption"))

# Optional auto-refresh for listed-company pages. This refreshes the browser view; data updates when the underlying CSV/data source is refreshed.
refresh_seconds = st.sidebar.selectbox(
    "已上市行情刷新 / Listed quote refresh",
    [0, 30, 60, 120, 300],
    index=0,
    format_func=lambda x: ("关闭" if x == 0 else f"{x}秒"),
)
if refresh_seconds and page in ["actions", "dashboard", "post", "memo"]:
    components.html(f"<script>setTimeout(function(){{window.parent.location.reload();}}, {int(refresh_seconds)*1000});</script>", height=0)

# Filters
# Use page-aware source columns so the sidebar rating filter matches the displayed rating.
filter_source = build_dashboard_view(pool, quotes) if page in ["actions", "dashboard", "review"] else pool
with st.sidebar.expander("筛选 / Filters", expanded=True):
    min_score = st.slider(tr(lang, "min_score"), 0, 100, 0, 5)
    stage_vals = sorted([x for x in filter_source.get("lifecycle_stage", pd.Series(dtype=str)).dropna().astype(str).unique()])
    stages = st.multiselect(tr(lang, "stage"), stage_vals, default=stage_vals)
    if page in ["actions", "dashboard", "review"]:
        tier_col = "dashboard_rating_cn" if lang == "中文" else "dashboard_rating_en"
    elif page == "post":
        tier_col = "secondary_rating_cn" if lang == "中文" else "secondary_rating_en"
        if tier_col not in filter_source.columns:
            tmp_post = build_secondary_view(pool, quotes)
            tier_vals_source = tmp_post
        else:
            tier_vals_source = filter_source
    else:
        tier_col = "investment_tier_cn" if lang == "中文" else "investment_tier_en"
        tier_vals_source = filter_source
    if page != "post":
        tier_vals_source = filter_source
    tier_vals = sorted([x for x in tier_vals_source.get(tier_col, pd.Series(dtype=str)).dropna().astype(str).unique()])
    tiers = st.multiselect(tr(lang, "rating"), tier_vals, default=tier_vals)
    ind_vals = sorted([x for x in filter_source.get("industry_level_1", pd.Series(dtype=str)).dropna().astype(str).unique()])
    inds = st.multiselect(tr(lang, "industry"), ind_vals, default=[])
    query = st.text_input(tr(lang, "search"), "")

view = pool.copy()
if "overall_score" in view.columns and page not in ["actions", "dashboard", "post", "review"]:
    view = view[to_num(view["overall_score"]).fillna(0) >= min_score]
if stages and "lifecycle_stage" in view.columns:
    view = view[view["lifecycle_stage"].astype(str).isin(stages)]
if tiers and tier_col in view.columns and page not in ["actions", "dashboard", "post", "review"]:
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

if page == "actions":
    dash = build_dashboard_view(pool, quotes)
    actions = build_today_actions(dash)
    # Apply global filters to the action list.
    if query:
        q = query.strip().lower()
        mask = actions.get("code", pd.Series("", index=actions.index)).astype(str).str.lower().str.contains(q, na=False) | actions.get("name", pd.Series("", index=actions.index)).astype(str).str.lower().str.contains(q, na=False)
        actions = actions[mask]
    if stages and "lifecycle_stage" in actions.columns:
        actions = actions[actions["lifecycle_stage"].astype(str).isin(stages)]
    if inds and "industry_level_1" in actions.columns:
        actions = actions[actions["industry_level_1"].astype(str).isin(inds)]
    dash_rating_col = "dashboard_rating_cn" if lang == "中文" else "dashboard_rating_en"
    if tiers and dash_rating_col in actions.columns:
        actions = actions[actions[dash_rating_col].astype(str).isin(tiers)]
    if "current_stage_score" in actions.columns:
        actions = actions[to_num(actions["current_stage_score"]).fillna(0) >= min_score]
    st.subheader(T["pages"]["actions"])
    if lang == "中文":
        st.info("本页按“今天需要做什么”归类，而不是简单列股票。重点用于晨会/盘前检查：建档、等待、参与、复核、回避。")
    else:
        st.info("This page groups names by what needs to be done today, rather than listing stocks only. It is designed for morning meeting / pre-trade checks.")
    if actions.empty:
        st.info(tr(lang, "empty"))
    else:
        pri_col = "action_priority_cn" if lang == "中文" else "action_priority_en"
        cat_col = "action_category_cn" if lang == "中文" else "action_category_en"
        cats = actions[cat_col].dropna().astype(str).unique().tolist()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("动作数" if lang == "中文" else "Actions", len(actions))
        c2.metric("高优先级" if lang == "中文" else "High priority", int(actions[pri_col].astype(str).isin(["高", "High"]).sum()))
        c3.metric("需复核" if lang == "中文" else "Review required", int(actions[cat_col].astype(str).isin(["数据需复核", "Data review required"]).sum()))
        c4.metric("类别" if lang == "中文" else "Categories", len(cats))
        tabs = st.tabs(cats[:10]) if cats else []
        cols = [pri_col, cat_col, "tradingview_url", "code", "name", "lifecycle_stage", "listed_age_bucket_cn" if lang == "中文" else "listed_age_bucket_en", "dashboard_rating_cn" if lang == "中文" else "dashboard_rating_en", "current_stage_score", "action_reason_cn" if lang == "中文" else "action_reason_en", "secondary_action_cn" if lang == "中文" else "secondary_action_en", "lockup_pressure_cn" if lang == "中文" else "lockup_pressure_en", "quote_freshness_cn" if lang == "中文" else "quote_freshness_en"]
        if tabs:
            for tab, cat in zip(tabs, cats[:10]):
                with tab:
                    display_table(actions[actions[cat_col].astype(str) == cat], lang, cols, 420)
        st.markdown("### " + ("完整动作清单" if lang == "中文" else "Full Action List"))
        display_table(actions, lang, cols, 520)
        download_button(actions, "today_action_list.csv", lang)

elif page == "dashboard":
    dash = build_dashboard_view(pool, quotes)
    # Apply dashboard-specific filters without mixing historical A1 quality into listed-company ratings.
    dash_view = dash.copy()
    if query:
        q = query.strip().lower()
        mask = dash_view.get("code", pd.Series("", index=dash_view.index)).astype(str).str.lower().str.contains(q, na=False) | dash_view.get("name", pd.Series("", index=dash_view.index)).astype(str).str.lower().str.contains(q, na=False)
        dash_view = dash_view[mask]
    if stages and "lifecycle_stage" in dash_view.columns:
        dash_view = dash_view[dash_view["lifecycle_stage"].astype(str).isin(stages)]
    if inds and "industry_level_1" in dash_view.columns:
        dash_view = dash_view[dash_view["industry_level_1"].astype(str).isin(inds)]
    dash_rating_col = "dashboard_rating_cn" if lang == "中文" else "dashboard_rating_en"
    if tiers and dash_rating_col in dash_view.columns:
        dash_view = dash_view[dash_view[dash_rating_col].astype(str).isin(tiers)]
    if "current_stage_score" in dash_view.columns:
        dash_view = dash_view[to_num(dash_view["current_stage_score"]).fillna(0) >= min_score]
    c1, c2, c3, c4, c5 = st.columns(5)
    listed_dash = is_listed_mask(dash_view) if not dash_view.empty else pd.Series(dtype=bool)
    c1.metric(tr(lang, "metric_total"), len(dash_view))
    c2.metric(tr(lang, "metric_a1"), int((~listed_dash).sum()) if len(dash_view) else 0)
    c3.metric(tr(lang, "metric_listed"), int(listed_dash.sum()) if len(dash_view) else 0)
    c4.metric(tr(lang, "metric_high_lockup"), int((dash_view.get("lockup_pressure_cn", pd.Series("", index=dash_view.index)).isin(["高", "中"]) & (to_num(dash_view.get("days_to_unlock", pd.Series(np.nan, index=dash_view.index))) <= 90)).sum()) if len(dash_view) else 0)
    c5.metric("平均当前阶段分" if lang == "中文" else "Avg current-stage score", fmt_num(to_num(dash_view.get("current_stage_score", pd.Series(dtype=float))).mean(), 1))
    st.subheader(tr(lang, "decision_pool"))
    if lang == "中文":
        st.info("决策总览覆盖所有2024年后上市公司和未上市IPO流程公司；未上市公司评级代表项目质量/一级参与价值，已上市公司评级只代表当前二级交易决策。历史A1评分不在本页展示。")
    else:
        st.info("The dashboard covers all post-2024 listed companies and unlisted IPO-process companies. Unlisted ratings refer to project quality / primary participation value; listed ratings refer only to current secondary-market decisions. Historical A1 scores are not shown here.")
    cols = ["dashboard_rating_cn" if lang == "中文" else "dashboard_rating_en", "decision_type_cn" if lang == "中文" else "decision_type_en", "tradingview_url", "code", "name", "lifecycle_stage", "listed_age_bucket_cn" if lang == "中文" else "listed_age_bucket_en", "listing_date", "industry_level_1", "current_stage_score", "quant_path_label_cn" if lang == "中文" else "quant_path_label_en", "secondary_action_cn" if lang == "中文" else "secondary_action_en", "lockup_pressure_cn" if lang == "中文" else "lockup_pressure_en", "next_action_cn" if lang == "中文" else "next_action_en"]
    display_table(dash_view.sort_values("current_stage_score", ascending=False, na_position="last"), lang, cols, 620)
    download_button(dash_view, "current_decision_dashboard.csv", lang)

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
            "score_confidence_cn" if lang == "中文" else "score_confidence_en", "date_check_cn" if lang == "中文" else "date_check_en",
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
    ipo_all = view[view.get("issue_price", pd.Series(np.nan, index=view.index)).notna() | view.get("offer_price_high", pd.Series(np.nan, index=view.index)).notna()].copy()
    if not ipo_all.empty:
        ratings = [primary_rating(x) for x in to_num(ipo_all.get("primary_score", pd.Series(np.nan, index=ipo_all.index)))]
        ipo_all["ipo_participation_rating_cn"] = [x[0] for x in ratings]
        ipo_all["ipo_participation_rating_en"] = [x[1] for x in ratings]
    listing_now = is_listed_mask(ipo_all) if not ipo_all.empty else pd.Series(dtype=bool)
    current_ipo = ipo_all[~listing_now].copy() if len(ipo_all) else ipo_all
    history_ipo = ipo_all[listing_now].copy() if len(ipo_all) else ipo_all
    cols = ["ipo_participation_rating_cn" if lang == "中文" else "ipo_participation_rating_en", "code", "name", "listing_date", "issue_price", "offer_price_low", "offer_price_high", "public_subscription_multiple", "public_subscription_multiple_ballot", "one_lot_success_rate_pct", "margin_multiple", "cornerstone_count", "cornerstone_amount_hkd", "primary_score", "primary_recommendation", "cornerstone_recommendation"]
    tab_cur, tab_hist = st.tabs(["当前招股/待上市项目" if lang == "中文" else "Current IPO / Pre-listing", "历史招股样本复盘" if lang == "中文" else "Historical IPO Review"])
    with tab_cur:
        if lang == "中文":
            st.info("本页默认先看当前仍未上市、但已出现发行价/招股区间的项目；评级只代表招股期是否参与，不代表上市后二级买卖。")
        else:
            st.info("This tab focuses on current not-yet-listed projects with issue price / offer range. The rating is for IPO participation only, not secondary trading.")
        display_table(current_ipo.sort_values("primary_score", ascending=False, na_position="last"), lang, cols, 560)
    with tab_hist:
        if lang == "中文":
            st.info("历史样本用于复盘招股期评分的有效性，不代表当前仍可参与一级。")
        else:
            st.info("Historical samples are for reviewing IPO participation score effectiveness and do not imply current primary-market availability.")
        display_table(history_ipo.sort_values("primary_score", ascending=False, na_position="last"), lang, cols, 560)
    with st.expander(tr(lang, "standards"), expanded=True):
        if lang == "中文":
            st.markdown("""
#### 招股期参与分：默认100分量化框架
| 维度 | 默认权重 | 量化定义 |
|---|---:|---|
| 发行定价 | 20% | 定价位置=(最终发行价-招股价下限)/(招股价上限-招股价下限)。≤30%高分；30%-70%中性；≥70%且认购弱扣分。 |
| 需求热度 | 20% | 公开认购≥100倍=极热；50-100倍=热；15-50倍=中高；3-15倍=中性；<3倍=偏弱。孖展≥100倍=极拥挤，需结合暗盘确认。 |
| 中签与资金效率 | 15% | 一手中签率<5%=极拥挤、资金效率低；5%-20%=热；20%-50%=中性；>50%=热度偏弱但中签效率高。 |
| 基石质量 | 15% | 基石占发行比例20%-50%为中性偏好；主权/长线/产业方加分；关联或不透明资金扣分；过高基石占比增加解禁风险。 |
| 发行结构 | 10% | 募资规模和流通盘适中加分；过大=承接压力，过小=易炒作后失衡。 |
| 投行/账簿质量 | 10% | 用历史项目首日胜率、20/60日表现、破发率和成交活跃度量化。 |
| 市场窗口 | 10% | 最近10-20只IPO首日收益、破发率、港股成交环境；新股赚钱效应强加分。 |

#### 输出档位
| 分数 | 建议 |
|---:|---|
| ≥80 | 强参与 |
| 70-79 | 小额/中等参与 |
| 60-69 | 谨慎参与，等配发/暗盘 |
| 50-59 | 只看二级 |
| <50 | 回避 |
""")
        else:
            st.markdown("""
#### IPO Participation Score: 100-point quantitative framework
| Dimension | Default Weight | Quantitative Definition |
|---|---:|---|
| Pricing | 20% | Pricing position=(final price-low end)/(high end-low end). ≤30% high score; 30%-70% neutral; ≥70% plus weak demand penalized. |
| Demand Heat | 20% | Public subscription ≥100x=extreme; 50-100x=hot; 15-50x=medium-high; 3-15x=neutral; <3x=weak. Margin ≥100x=very crowded and must be confirmed by gray market. |
| Ballot / Capital Efficiency | 15% | One-lot success <5%=very crowded / low capital efficiency; 5%-20%=hot; 20%-50%=neutral; >50%=weak heat but high hit rate. |
| Cornerstone Quality | 15% | 20%-50% cornerstone share is neutral-positive; sovereign/long-only/strategic investors add points; related/opaque capital penalized; too high share raises lock-up risk. |
| Deal Structure | 10% | Balanced deal size / float add points; too large creates absorption pressure, too small can lead to unstable speculation. |
| Syndicate Quality | 10% | Quantified by historical first-day win rate, 20/60D performance, break rate and liquidity. |
| Market Window | 10% | Recent 10-20 IPO returns, break rate and HK market turnover; strong IPO money-making effect adds points. |

#### Output Tiers
| Score | Recommendation |
|---:|---|
| ≥80 | Strong participate |
| 70-79 | Small / moderate participate |
| 60-69 | Cautious; wait for allotment / gray market |
| 50-59 | Secondary only |
| <50 | Avoid |
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
    if lang == "中文":
        st.info("本页覆盖所有2024年后上市公司，不仅限于180日内。0-180日重点看发行价关系、深V和升后破发；180日后重点看趋势延续、长期破发修复、解禁后再定价和高位回撤。")
    else:
        st.info("This page covers all companies listed since 2024, not only the first 180 days. For 0-180D it focuses on issue-price relationship, deep-V and pump-then-break; after 180D it focuses on trend continuation, long break-price recovery, post-lock-up repricing and high-level drawdown.")
    post = build_secondary_view(view, quotes)
    bucket_options = sorted(post.get("listed_age_bucket_cn" if lang == "中文" else "listed_age_bucket_en", pd.Series(dtype=str)).dropna().unique()) if not post.empty else []
    selected_buckets = st.multiselect("上市分层" if lang == "中文" else "Listing-age bucket", bucket_options, default=bucket_options)
    if selected_buckets:
        bcol = "listed_age_bucket_cn" if lang == "中文" else "listed_age_bucket_en"
        post = post[post[bcol].isin(selected_buckets)]
    post_rating_col = "secondary_rating_cn" if lang == "中文" else "secondary_rating_en"
    if tiers and post_rating_col in post.columns:
        post = post[post[post_rating_col].astype(str).isin(tiers)]
    if "current_stage_score" in post.columns:
        post = post[to_num(post["current_stage_score"]).fillna(0) >= min_score]
    cols = ["secondary_rating_cn" if lang == "中文" else "secondary_rating_en", "code", "name", "listing_date", "listed_days", "listed_age_bucket_cn" if lang == "中文" else "listed_age_bucket_en", "issue_price", "last_close", "relative_to_issue_pct", "quote_rows", "quote_source", "last_quote_date", "quote_freshness_cn" if lang == "中文" else "quote_freshness_en", "quant_path_label_cn" if lang == "中文" else "quant_path_label_en", "d1_close_ret", "max_20_ret", "min_20_ret", "max_60_ret", "min_60_ret", "max_180_ret", "min_180_ret", "ret20_current", "ret60_current", "drawdown_from_quote_high", "current_stage_score", "secondary_action_cn" if lang == "中文" else "secondary_action_en", "buy_trigger", "sell_trigger"]
    display_table(post.sort_values("current_stage_score", ascending=False, na_position="last"), lang, cols, 680)
    with st.expander("量化路径定义" if lang == "中文" else "Quantitative Path Definitions", expanded=True):
        if lang == "中文":
            st.markdown("""
| 路径/状态 | 量化定义 | 操作含义 |
|---|---|---|
| 上市即强势 | 首日收盘涨幅≥10%，且20日内最低价未低于发行价-5%，且20日最大涨幅≥20% | 不追高，等回踩或趋势确认 |
| 深V反弹 | 20日内较发行价最大跌幅≤-10%或60日压力≤-15%，之后60日最大反弹≥25%，且重新站回发行价 | 重点关注二级买点 |
| 一路破发 | 首日收盘破发或20日内跌破发行价-5%，且60日最大反弹<15%/未站回发行价 | 原则上回避 |
| 升后破发 | 前20日最大涨幅≥15%，但之后跌破发行价或60日压力≤-30% | 卖点/降仓优先 |
| 温和交易型 | 20日内最大回撤不超过15%，最大涨幅不超过20%，未形成强趋势 | 等催化或成交确认 |
| 趋势延续(180D+) | 近60日收益≥15%，且距行情高点回撤<20% | 可继续二级跟踪 |
| 高位震荡(180D+) | 距行情高点回撤<15%，且近20日收益在±10%以内 | 等突破或回踩确认 |
| 长期破发修复(180D+) | 曾跌破发行价，当前重新高于发行价 | 关注修复交易 |
| 长期破发弱势(180D+) | 上市180日后仍低于发行价10%以上，且60日反弹不足15% | 回避或仅观察 |
| 高位回撤预警(180D+) | 从行情高点回撤≥30% | 风控/止盈优先 |

**术语阈值**：明显回撤≥15%；显著回撤≥25%；显著高于发行价=收盘价高于发行价≥10%；重新站回发行价=连续2日收盘价≥发行价；放量=成交额≥过去5日均值1.5倍；放量滞涨=成交额≥5日均值1.5倍但收盘涨幅<2%。
""")
        else:
            st.markdown("""
| Path / State | Quantitative Definition | Trading Implication |
|---|---|---|
| Strong from listing | D1 close ≥10%, 20D low not below issue price -5%, 20D max gain ≥20% | Do not chase; wait for pullback/trend confirmation |
| Deep-V rebound | 20D max drawdown ≤-10% vs issue price or 60D pressure ≤-15%, later 60D rebound ≥25%, back above issue price | Key secondary buy setup |
| Persistent break issue price | D1 break or 20D break below issue price -5%, and 60D max rebound <15% / not back above issue price | Avoid by default |
| Pump then break | 20D max gain ≥15%, then below issue price or 60D pressure ≤-30% | Sell / reduce risk first |
| Moderate trading path | 20D max drawdown <=15%, max gain <=20%, no strong trend | Wait for catalyst or turnover confirmation |
| Trend continuation (180D+) | 60D return ≥15% and drawdown from quote high <20% | Continue secondary tracking |
| High-level consolidation (180D+) | Drawdown from quote high <15% and 20D return within ±10% | Wait for breakout or pullback confirmation |
| Long break-price recovery (180D+) | Previously broke issue price, now above issue price | Watch recovery trade |
| Long-term weak below issue price (180D+) | After 180D still >10% below issue price and 60D rebound <15% | Avoid / observe only |
| High-level drawdown alert (180D+) | Drawdown from quote high ≥30% | Prioritize risk control / profit taking |
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
        weight_profiles = {"balanced": {"zh_name":"平衡型","en_name":"Balanced","zh_desc":"默认方案","en_desc":"Default profile","weights":{"定价安全":20,"需求热度":20,"基石质量":15,"投行质量":10,"暗盘/首日":15,"上市后二级路径":15,"解禁安全":5}}}
        profile_items = list(weight_profiles.items())
    display_name = lambda kv: (kv[1].get("zh_name") if lang == "中文" else kv[1].get("en_name")) or kv[0]
    selected_tuple = st.selectbox(tr(lang, "profile"), profile_items, format_func=display_name)
    selected_key, selected_profile = selected_tuple
    st.info(selected_profile.get("zh_desc" if lang == "中文" else "en_desc", ""))
    preset = selected_profile.get("weights", {})
    # Normalize naming
    if "解禁风险" in preset and "解禁安全" not in preset:
        preset["解禁安全"] = preset.pop("解禁风险")
    dims = ["定价安全", "需求热度", "基石质量", "投行质量", "暗盘/首日", "上市后二级路径", "解禁安全"]
    dim_en = {"定价安全":"Pricing Safety", "需求热度":"Demand Heat", "基石质量":"Cornerstone Quality", "投行质量":"Syndicate Quality", "暗盘/首日":"Gray / First Day", "上市后二级路径":"Post-listing Path", "解禁安全":"Lock-up Safety"}
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
    # Rating distribution calibration
    dash_for_cal = build_dashboard_view(pool, quotes)
    rating_col_cal = "dashboard_rating_cn" if lang == "中文" else "dashboard_rating_en"
    dist = build_rating_distribution(dash_for_cal, rating_col_cal)
    st.markdown("### " + ("评级分布校准" if lang == "中文" else "Rating Distribution Calibration"))
    if not dist.empty:
        display_table(dist, lang, ["rating_bucket", "sample_count", "sample_pct", "target_range", "calibration_note_cn" if lang == "中文" else "calibration_note_en"], 220)
        st.caption("说明：A/B/C/D需要有区分度。A档过少说明阈值偏严；A档过多说明区分度不足；D档过多则要检查是否由数据缺失导致低分。" if lang == "中文" else "Interpretation: A/B/C/D should be well separated. Too few A names suggests a strict threshold; too many A names suggests weak separation; too many D names may reflect missing data.")
    
    # Plain-language conclusion first.
    if not buckets.empty and "score_bucket" in buckets.columns:
        def bucket_val(bucket, col):
            r = buckets[buckets["score_bucket"].astype(str) == bucket]
            if r.empty or col not in r.columns:
                return np.nan
            return pd.to_numeric(r[col].iloc[0], errors="coerce")
        b20, c20, d20 = bucket_val("B", "二十日最大均值"), bucket_val("C", "二十日最大均值"), bucket_val("D", "二十日最大均值")
        bbad, dbad = bucket_val("B", "坏路径率"), bucket_val("D", "坏路径率")
        conclusions = []
        if pd.notna(b20) and pd.notna(d20) and b20 > d20:
            conclusions.append("高分组的20日最大收益高于D组，说明当前评分有一定筛选能力。" if lang == "中文" else "Higher-score buckets show better 20D upside than D bucket, suggesting useful selection value.")
        if pd.notna(bbad) and pd.notna(dbad) and bbad < dbad:
            conclusions.append("B组坏路径率低于D组，说明回避信号具备一定风控价值。" if lang == "中文" else "B bucket has a lower bad-path rate than D bucket, suggesting risk-control value.")
        if bucket_val("A", "样本数") == 0:
            conclusions.append("A组样本数为0，说明当前A档阈值偏严，可在后续权重校准中调整。" if lang == "中文" else "A bucket has zero samples, suggesting the A threshold may be too strict and should be calibrated later.")
        if conclusions:
            st.success(("模型有效性初步结论：" if lang == "中文" else "Initial effectiveness readout: ") + "；".join(conclusions))
    st.markdown("### " + ("评分分层表现" if lang == "中文" else "Score Bucket Performance"))
    display_table(buckets, lang, None, 240)
    if lang == "中文":
        st.caption("说明：本表用于验证高分组是否优于低分组。若高分组首日、20日、60日收益更高且破发率更低，说明评分模型具有实际筛选价值；若分组差异不明显，说明权重或阈值需要调整。")
    else:
        st.caption("Interpretation: This table checks whether high-score buckets outperform low-score buckets. Higher D1/20D/60D returns and lower break-rate in high-score buckets indicate useful selection value; weak separation suggests weights/thresholds need adjustment.")
    st.markdown("### " + ("权重方案表现" if lang == "中文" else "Weight Profile Performance"))
    display_table(profile_perf, lang, None, 260)
    if lang == "中文":
        st.caption("说明：本表比较不同权重方案的历史表现，用来判断当前基金风格应偏重打新收益、二级交易、风险控制还是平衡配置。")
    else:
        st.caption("Interpretation: This table compares historical performance of weight profiles and helps choose whether the fund should emphasize IPO return, secondary trading, risk control or a balanced profile.")
    st.markdown("### " + ("因子有效性诊断" if lang == "中文" else "Factor Diagnostics"))
    display_table(diag, lang, None, 300)
    if lang == "中文":
        st.caption("说明：本表检查单个因子与后续表现的关系。正向因子应当表现为高分对应更高收益或更低破发率；若方向相反，需要降低该因子权重或重新定义档位。")
    else:
        st.caption("Interpretation: This table checks each factor against subsequent performance. A useful positive factor should show higher returns or lower break-rate at higher values; if the relationship is reversed, reduce its weight or redefine tiers.")
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
        st.caption("说明：高分但表现弱的样本用于复盘模型是否低估了估值、解禁、流动性或市场窗口风险。" if lang == "中文" else "Interpretation: High-score weak outcomes help review whether valuation, lock-up, liquidity or market-window risks were underestimated.")
    with col2:
        st.write("低分但后续大涨" if lang == "中文" else "Low score but later strong rally")
        display_table(low_miss, lang, ["code", "name", "overall_score", "path_label", "d1_close_ret", "max_180_ret", "min_180_ret", "risk_tags_model"], 280)
        st.caption("说明：低分但大涨的样本用于复盘模型是否遗漏了行业催化、资金偏好、估值重估或二级交易信号。" if lang == "中文" else "Interpretation: Low-score strong rallies help review whether sector catalysts, fund preference, valuation rerating or secondary signals were missed.")

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

elif page == "research":
    st.subheader(T["pages"]["research"])
    if lang == "中文":
        st.info("这里提供人工基本面评分入口。页面上编辑后请下载 CSV，并上传/覆盖 deploy_data/manual_research_scores.csv；系统会把人工基本面分纳入 A1 公司稀缺性与基本面潜力维度。")
    else:
        st.info("This page provides a manual fundamental-score input. After editing, download the CSV and upload/replace deploy_data/manual_research_scores.csv; the score feeds into the A1 scarcity/fundamental-potential dimension.")
    template_cols = ["code", "name", "manual_quality_rating", "manual_quality_score", "industry_view", "valuation_view", "research_comment", "updated_by", "updated_date"]
    if manual_research.empty:
        base = pd.DataFrame(columns=template_cols)
        # seed with top A1 names to make editing easier
        a1_company, _ = build_a1_company_view(pool)
        seed = a1_company.sort_values("a1_quality_score", ascending=False, na_position="last").head(50)[[c for c in ["code", "name"] if c in a1_company.columns]].copy() if not a1_company.empty else pd.DataFrame(columns=["code", "name"])
        for c in template_cols:
            if c not in seed.columns:
                seed[c] = ""
        base = seed[template_cols]
    else:
        base = manual_research.copy()
        for c in template_cols:
            if c not in base.columns:
                base[c] = ""
        base = base[template_cols]
    st.caption("评级可填：强 / 较强 / 中性 / 较弱 / 回避；也可直接填 0-100 的人工基本面分。" if lang == "中文" else "Rating can be: Strong / Positive / Neutral / Weak / Avoid; alternatively enter a 0-100 manual score.")
    edited = st.data_editor(base, use_container_width=True, num_rows="dynamic", height=520)
    st.download_button("下载人工评分CSV" if lang == "中文" else "Download manual score CSV", edited.to_csv(index=False, encoding="utf-8-sig"), "manual_research_scores.csv", "text/csv")
    if not manual_research.empty:
        st.markdown("### " + ("已接入人工评分的项目" if lang == "中文" else "Names with Manual Scores Applied"))
        with_manual = pool[to_num(pool.get("manual_quality_score", pd.Series(np.nan, index=pool.index))).notna()].copy()
        display_table(with_manual.sort_values("manual_quality_score", ascending=False, na_position="last"), lang, ["code", "name", "manual_quality_rating", "manual_quality_score", "industry_view", "valuation_view", "research_comment", "a1_quality_score", "a1_company_quality_score"], 360)

elif page == "review":
    st.subheader(T["pages"]["review"])
    dash = build_dashboard_view(pool, quotes)
    review = build_manual_review_pool(dash)
    if lang == "中文":
        st.info("本页把系统认为需要人工复核的项目集中列出：行情滞后、日期异常、发行价缺失、高解禁压力、高分但数据不足等。")
    else:
        st.info("This page centralizes names that need manual review: stale quotes, date anomalies, missing issue price, high lock-up pressure, high score with incomplete data, etc.")
    if review.empty:
        st.success("暂无重大人工复核项。" if lang == "中文" else "No major manual-review items.")
    else:
        cols = ["review_reason_cn" if lang == "中文" else "review_reason_en", "tradingview_url", "code", "name", "lifecycle_stage", "listed_age_bucket_cn" if lang == "中文" else "listed_age_bucket_en", "dashboard_rating_cn" if lang == "中文" else "dashboard_rating_en", "current_stage_score", "quote_freshness_cn" if lang == "中文" else "quote_freshness_en", "score_confidence_cn" if lang == "中文" else "score_confidence_en", "date_check_cn" if lang == "中文" else "date_check_en", "issue_price", "lockup_pressure_cn" if lang == "中文" else "lockup_pressure_en"]
        display_table(review.sort_values("current_stage_score", ascending=False, na_position="last"), lang, cols, 620)
        download_button(review, "manual_review_queue.csv", lang)

elif page == "update":
    st.subheader(T["pages"]["update"])
    status = read_csv_any(BASE / "data_update_status.csv")
    if lang == "中文":
        st.info("本页显示16:30日度更新引擎的结果。日常可在本地双击 `run_daily_update_low_quota.bat`；若只处理iFind导出文件，可双击 `process_ifind_exports_offline.bat`。")
    else:
        st.info("This page shows the result of the 16:30 daily update engine. Run `run_daily_update_low_quota.bat` locally for API updates, or `process_ifind_exports_offline.bat` for offline iFind exports.")
    c1, c2, c3, c4 = st.columns(4)
    if status.empty:
        c1.metric("数据源" if lang == "中文" else "Sources", "0")
        c2.metric("成功" if lang == "中文" else "OK", "0")
        c3.metric("失败/保留旧数据" if lang == "中文" else "Failed / old kept", "0")
        c4.metric("最近更新时间" if lang == "中文" else "Last updated", "")
        st.warning("暂无 data_update_status.csv。运行一次更新脚本后这里会显示状态。" if lang == "中文" else "No data_update_status.csv yet. Run the update script once to populate this page.")
    else:
        status_col = "status" if "status" in status.columns else None
        ok = int(status[status_col].astype(str).str.contains("ok|dry_run|no_new_data", case=False, na=False).sum()) if status_col else 0
        fail = int(status[status_col].astype(str).str.contains("failed", case=False, na=False).sum()) if status_col else 0
        updated = status["updated_at"].dropna().astype(str).max() if "updated_at" in status.columns and status["updated_at"].notna().any() else ""
        c1.metric("数据源" if lang == "中文" else "Sources", len(status))
        c2.metric("成功/保留可用" if lang == "中文" else "OK / usable", ok)
        c3.metric("失败" if lang == "中文" else "Failed", fail)
        c4.metric("最近更新时间" if lang == "中文" else "Last updated", updated)
        display_table(status, lang, None, 420)
        download_button(status, "data_update_status.csv", lang)
    st.markdown("### " + ("本地更新入口" if lang == "中文" else "Local update entry points"))
    if lang == "中文":
        st.markdown("""
- `00_setup_env.bat`：首次使用安装依赖。
- `run_daily_update_low_quota.bat`：收盘后日常更新，会调用 iFind API，但采用低额度策略。
- `run_daily_update_dry_run.bat`：模拟运行，不调用 API，不消耗额度。
- `process_ifind_exports_offline.bat`：只处理 `ifind_exports/` 下的 Excel/CSV，不调用 API。
- `build_ifind_field_mapping_offline.bat`：根据 iFind 导出文件中文表头反推 `p05310_f001`、`p03764_f001` 等字段含义，不调用 API。

更多说明见 `docs/daily_update_engine.md` 和 `docs/next_version_plan.md`。
""")
    else:
        st.markdown("""
- `00_setup_env.bat`: install dependencies for first-time use.
- `run_daily_update_low_quota.bat`: daily post-close update using low-quota iFind API calls.
- `run_daily_update_dry_run.bat`: dry-run mode, no API quota used.
- `process_ifind_exports_offline.bat`: process Excel/CSV files under `ifind_exports/` without API calls.
- `build_ifind_field_mapping_offline.bat`: infer field meanings such as `p05310_f001` and `p03764_f001` from exported iFind column headers, without API calls.

See `docs/daily_update_engine.md` and `docs/next_version_plan.md` for details.
""")

elif page == "quality":
    st.subheader(tr(lang, "data_quality"))
    # dynamic inventory rows
    extra = []
    if not quotes.empty:
        extra.append({"source_name":"上市后0-180D行情", "file_name":"ipo_daily_quotes_180d.csv", "raw_rows":len(quotes), "normalized_rows":len(quotes), "status":"已接入"})
    if not paths.empty:
        extra.append({"source_name":"上市后二级路径标签", "file_name":"ipo_post_listing_paths.csv", "raw_rows":len(paths), "normalized_rows":len(paths), "status":"已接入"})
    extra.append({"source_name":"投资决策评分", "file_name":"ipo_investment_decision_scored.csv", "raw_rows":len(pool), "normalized_rows":len(pool), "status":"已接入"})
    inv = inventory.copy()
    if extra:
        ex = pd.DataFrame(extra)
        if not inv.empty and "source_name" in inv.columns:
            inv = inv[~inv["source_name"].isin(ex["source_name"])]
        inv = pd.concat([inv, ex], ignore_index=True)
    display_table(inv, lang, None, 360)
    st.markdown("### " + ("管理层数据质量状态" if lang == "中文" else "Management Data Quality Status"))
    status_rows = []
    stale_col = "quote_freshness_cn" if lang == "中文" else "quote_freshness_en"
    sec_quality = build_secondary_view(pool, quotes)
    if not sec_quality.empty and stale_col in sec_quality.columns:
        stale_count = int(sec_quality[stale_col].astype(str).isin(["明显滞后", "Stale", "缺失", "Missing"]).sum())
        status_rows.append({"项目" if lang == "中文" else "Item": "行情新鲜度" if lang == "中文" else "Quote freshness", "状态" if lang == "中文" else "Status": "需复核" if stale_count else "可用", "说明" if lang == "中文" else "Description": (f"{stale_count} 只股票行情明显滞后或缺失，交易前需用TradingView/券商终端复核。" if stale_count else "主要二级交易池行情处于可用状态。")})
    status_rows.append({"项目" if lang == "中文" else "Item": "回拨数据" if lang == "中文" else "Clawback data", "状态" if lang == "中文" else "Status": "缺失", "说明" if lang == "中文" else "Description": "iFind暂未提供结构化回拨统计，当前通过认购倍数/中签率/孖展和暗盘信号替代。" if lang == "中文" else "Structured clawback data is not currently available; subscription, ballot, margin and gray-market signals are used as substitutes."})
    st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)
    st.markdown("### " + ("重复公司/股票检查" if lang == "中文" else "Duplicate Company / Stock Check"))
    dup_rows = []
    if "code" in pool.columns:
        listed_pool = pool[is_listed_mask(pool)].copy()
        vc = listed_pool["code"].astype(str).str.upper().str.strip().value_counts()
        for code, n in vc[vc > 1].head(30).items():
            name = listed_pool.loc[listed_pool["code"].astype(str).str.upper().str.strip() == code, "name"].astype(str).head(1).iloc[0] if "name" in listed_pool.columns else ""
            dup_rows.append({"code": code, "name": name, "duplicate_rows": int(n), "handling": "已在领导页面按code聚合为一行" if lang == "中文" else "Aggregated to one row by code in leadership pages"})
    dup_df = pd.DataFrame(dup_rows)
    if dup_df.empty:
        st.success("未发现会影响展示的重复股票。" if lang == "中文" else "No display-impacting duplicated stocks found.")
    else:
        display_table(dup_df, lang, None, 260)
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
