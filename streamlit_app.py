from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

# ============================================================
# 港股 IPO / 半新股决策驾驶舱
# Step 3: 加入 A1/未上市项目、发行文件、180日行情采样框架
# ============================================================

APP_TITLE = "港股 IPO / 半新股决策驾驶舱"
APP_SUBTITLE = (
    "Step 3：把模型覆盖范围前移到 A1/临时代码阶段，并拆出发行文件、配发结果、上市后180日行情采样。"
)

LISTED_DATA_CANDIDATES = [
    Path("deploy_data/hk_ipo_scored_public.csv"),
    Path("hk_ipo_scored_public.csv"),
    Path("data/processed/hk_ipo_scored.csv"),
]
PROJECT_DATA_CANDIDATES = [
    Path("deploy_data/ipo_projects.csv"),
    Path("ipo_projects.csv"),
    Path("data/raw/ipo_projects.csv"),
]
DOC_DATA_CANDIDATES = [
    Path("deploy_data/ipo_docs.csv"),
    Path("ipo_docs.csv"),
    Path("data/raw/ipo_docs.csv"),
]
PRICE_SAMPLE_CANDIDATES = [
    Path("deploy_data/price_180d_sample.csv"),
    Path("price_180d_sample.csv"),
    Path("data/processed/price_180d_sample.csv"),
]
PATCH_CANDIDATES = [
    Path("deploy_data/ipo_master_patch.csv"),
    Path("ipo_master_patch.csv"),
    Path("data/raw/ipo_master_patch.csv"),
]

PCT_COLS = [
    "d1_open_ret", "d1_close_ret", "d5_close_ret", "d20_close_ret", "d60_close_ret",
    "max_5_ret", "min_5_ret", "max_20_ret", "min_20_ret", "max_60_ret", "min_60_ret",
    "cornerstone_ratio", "one_lot_success_rate", "clawback_ratio", "final_price_position",
    "ret_from_ipo", "drawdown_from_high", "turnover_rate", "day_return",
]
NUM_COLS = [
    "issue_price", "offer_price_low", "offer_price_high", "fundraising_amount_hkd",
    "market_cap_at_ipo_hkd", "cornerstone_amount_hkd", "public_subscription_multiple",
    "international_subscription_multiple", "d1_amount", "d1_volume", "quote_days",
    "model_score_tradeable_20d", "liquidity_score", "structure_score", "sentiment_score",
    "fundamental_score", "composite_score", "preipo_score", "price", "open", "high", "low", "close",
    "volume", "amount", "day_offset", "sample_bucket",
]
DATE_COLS = [
    "listing_date", "expected_listing_date", "a1_date", "application_proof_date", "phip_date",
    "prospectus_date", "pricing_date", "allotment_result_date", "doc_date", "trade_date",
]
BOOL_COLS = [
    "label_strong_open", "label_deep_v", "label_broken", "label_pop_then_fade", "label_tradeable_20d",
]

COLUMN_ALIASES = {
    # common identifiers
    "证券代码": "code", "股票代码": "code", "代码": "code", "正式代码": "code", "上市代码": "code",
    "临时代码": "temp_code", "临时证券代码": "temp_code", "申请代码": "temp_code",
    "证券简称": "name", "股票简称": "name", "简称": "name", "名称": "name", "公司名称": "name", "申请人名称": "name",
    # stage and dates
    "阶段": "project_status", "项目阶段": "project_status", "上市状态": "project_status", "申请状态": "project_status",
    "上市日期": "listing_date", "首挂日期": "listing_date", "预计上市日期": "expected_listing_date",
    "递表日期": "a1_date", "A1日期": "a1_date", "申请版本日期": "application_proof_date",
    "聆讯后资料集日期": "phip_date", "PHIP日期": "phip_date", "招股书日期": "prospectus_date",
    "定价日期": "pricing_date", "配发结果日期": "allotment_result_date",
    # industry and issue
    "行业": "industry", "所属行业": "industry", "恒生行业": "industry", "业务摘要": "business_summary",
    "发行价": "issue_price", "最终发行价": "issue_price", "招股价": "issue_price",
    "招股价下限": "offer_price_low", "发售价下限": "offer_price_low",
    "招股价上限": "offer_price_high", "发售价上限": "offer_price_high",
    "定价位置": "final_price_position",
    "募资金额": "fundraising_amount_hkd", "集资额": "fundraising_amount_hkd",
    "发行市值": "market_cap_at_ipo_hkd", "上市市值": "market_cap_at_ipo_hkd",
    # parties and structure
    "保荐人": "sponsor_names", "联席保荐人": "sponsor_names", "整体协调人": "overall_coordinators",
    "基石投资者": "cornerstone_names", "基石名单": "cornerstone_names",
    "基石金额": "cornerstone_amount_hkd", "基石认购金额": "cornerstone_amount_hkd",
    "基石占比": "cornerstone_ratio", "基石比例": "cornerstone_ratio",
    "公开认购倍数": "public_subscription_multiple", "公开发售认购倍数": "public_subscription_multiple",
    "国际配售倍数": "international_subscription_multiple", "国际发售认购倍数": "international_subscription_multiple",
    "一手中签率": "one_lot_success_rate", "回拨比例": "clawback_ratio",
    # document registry
    "文件类型": "doc_type", "公告类型": "doc_type", "文件日期": "doc_date", "公告日期": "doc_date",
    "文件名": "doc_name", "文件链接": "doc_url", "公告链接": "doc_url", "本地文件": "local_file",
    "提取状态": "extraction_status", "提取字段": "key_fields_found", "备注": "notes",
    # prices
    "交易日期": "trade_date", "日期": "trade_date", "开盘价": "open", "最高价": "high", "最低价": "low", "收盘价": "close",
    "成交量": "volume", "成交额": "amount", "换手率": "turnover_rate",
}

PATH_CN = {
    "strong_open": "上市即强",
    "deep_v_rebound": "深V反弹",
    "moderate_tradeable": "可交易",
    "pop_then_fade": "升后回落",
    "persistent_break": "持续破发",
    "broken": "持续破发",
    "watch": "观察",
}

STAGE_RANK = {
    "A1递表/申请版本": 1,
    "问询/更新中": 2,
    "聆讯后/PHIP": 3,
    "招股中": 4,
    "定价/配发结果": 5,
    "已上市": 6,
    "失效/撤回": 9,
    "未知": 99,
}

REQUIRED_FIELDS = [
    ("industry", "行业", "行业胜率、估值锚、主题热度"),
    ("sponsor_names", "保荐人", "保荐人历史胜率、机构销售能力"),
    ("offer_price_low", "招股价下限", "估值区间"),
    ("offer_price_high", "招股价上限", "估值区间"),
    ("issue_price", "最终发行价", "破发、定价位置、发行价支撑"),
    ("fundraising_amount_hkd", "募资金额", "承接难度"),
    ("market_cap_at_ipo_hkd", "发行市值", "估值和流动性"),
    ("public_subscription_multiple", "公开认购倍数", "散户拥挤度"),
    ("international_subscription_multiple", "国际配售倍数", "机构真实需求"),
    ("one_lot_success_rate", "一手中签率", "打新收益/拥挤度"),
    ("clawback_ratio", "回拨比例", "上市流通盘和抛压"),
    ("cornerstone_names", "基石名单", "长线资金/产业方/明星机构质量"),
    ("cornerstone_ratio", "基石占比", "首日浮筹和6个月解禁压力"),
]

PROJECT_DISPLAY_COLS = [
    "stage_cn", "temp_code", "code", "name", "a1_date", "phip_date", "prospectus_date",
    "expected_listing_date", "listing_date", "industry", "sponsor_names", "preipo_score",
    "preipo_action", "doc_status", "data_gap_count",
]
LISTED_DISPLAY_COLS = [
    "decision_tier", "code", "name", "listing_date", "days_since_listing", "industry", "issue_price",
    "d1_close_ret", "max_20_ret", "min_20_ret", "max_60_ret", "path_label", "risk_level",
    "primary_action", "secondary_action", "position_hint", "model_score_tradeable_20d",
]
DOC_DISPLAY_COLS = [
    "stage_cn", "temp_code", "code", "name", "doc_type", "doc_date", "doc_name", "extraction_status", "key_fields_found", "doc_url", "notes",
]
PRICE_DISPLAY_COLS = [
    "code", "name", "listing_date", "trade_date", "day_offset", "sample_bucket", "open", "high", "low", "close", "volume", "amount", "turnover_rate", "ret_from_ipo", "drawdown_from_high",
]

DISPLAY_LABELS = {
    "stage_cn": "阶段", "project_status": "项目状态", "temp_code": "临时代码", "code": "正式代码", "name": "简称/申请人",
    "a1_date": "A1/递表日", "application_proof_date": "申请版本日", "phip_date": "PHIP日", "prospectus_date": "招股书日",
    "expected_listing_date": "预计上市日", "listing_date": "上市日", "industry": "行业", "sponsor_names": "保荐人",
    "preipo_score": "上市前分", "preipo_action": "上市前建议", "doc_status": "文件状态", "data_gap_count": "缺口数",
    "decision_tier": "决策层", "days_since_listing": "上市天数", "issue_price": "发行价", "d1_close_ret": "首日收盘",
    "max_20_ret": "20D最大涨幅", "min_20_ret": "20D最大回撤", "max_60_ret": "60D最大涨幅", "path_label": "路径",
    "risk_level": "风险", "primary_action": "一级建议", "secondary_action": "二级建议", "position_hint": "仓位提示",
    "model_score_tradeable_20d": "模型分", "doc_type": "文件类型", "doc_date": "文件日", "doc_name": "文件名",
    "extraction_status": "提取状态", "key_fields_found": "已提取字段", "doc_url": "链接", "notes": "备注",
    "trade_date": "交易日", "day_offset": "上市后第N个交易日", "sample_bucket": "采样层", "open": "开", "high": "高", "low": "低", "close": "收",
    "volume": "成交量", "amount": "成交额", "turnover_rate": "换手", "ret_from_ipo": "较发行价", "drawdown_from_high": "距阶段高点回撤",
}

# ============================================================
# Generic helpers
# ============================================================

def find_first_existing(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


def read_csv_if_exists(paths: list[Path]) -> tuple[pd.DataFrame, str]:
    p = find_first_existing(paths)
    if p is None:
        return pd.DataFrame(), ""
    try:
        return pd.read_csv(p, encoding="utf-8-sig"), str(p)
    except UnicodeDecodeError:
        return pd.read_csv(p), str(p)


def rename_known_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={c: COLUMN_ALIASES.get(c, c) for c in df.columns})


def clean_code(value: Any, allow_temp: bool = False) -> str:
    if pd.isna(value):
        return ""
    s = str(value).strip().upper()
    if not s or s in {"NAN", "NONE", "—", "-"}:
        return ""
    if s.endswith(".HK"):
        left = s[:-3]
        if left.isdigit():
            return f"{int(left):04d}.HK"
        return s
    if s.isdigit():
        # 港股正式代码一般四/五位；临时代码也保留 .HK，统一便于合并。
        return f"{int(s):04d}.HK" if len(s) <= 5 else s
    return s if allow_temp else s


def safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if pd.isna(value):
            return default
        if isinstance(value, str):
            value = value.replace(",", "").replace("%", "")
        return float(value)
    except Exception:
        return default


def normalize_common(df: pd.DataFrame) -> pd.DataFrame:
    df = rename_known_columns(df.copy())
    if "code" in df.columns:
        df["code"] = df["code"].map(clean_code)
    if "temp_code" in df.columns:
        df["temp_code"] = df["temp_code"].map(lambda x: clean_code(x, allow_temp=True))
    for col in DATE_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in PCT_COLS + NUM_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in BOOL_COLS:
        if col in df.columns:
            df[col] = df[col].map(lambda x: str(x).lower() in {"true", "1", "yes", "y"} if not isinstance(x, bool) else x).fillna(False)
    if "name" not in df.columns:
        df["name"] = ""
    if "industry" not in df.columns:
        df["industry"] = "Unknown"
    df["industry"] = df["industry"].fillna("Unknown").astype(str).str.strip().replace({"": "Unknown", "nan": "Unknown", "None": "Unknown"})
    return df


def fmt_date(value: Any) -> str:
    if pd.isna(value):
        return "—"
    return pd.to_datetime(value).strftime("%Y-%m-%d")


def fmt_pct(value: Any) -> str:
    x = safe_float(value)
    if x is None:
        return "—"
    return f"{x:.1%}"


def fmt_num(value: Any, digits: int = 2) -> str:
    x = safe_float(value)
    if x is None:
        return "—"
    return f"{x:,.{digits}f}"


def fmt_money(value: Any) -> str:
    x = safe_float(value)
    if x is None:
        return "—"
    if abs(x) >= 1e9:
        return f"{x / 1e9:.2f} bn"
    if abs(x) >= 1e8:
        return f"{x / 1e8:.2f} 亿"
    if abs(x) >= 1e6:
        return f"{x / 1e6:.2f} mn"
    return f"{x:,.0f}"


def make_cn_table(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    available = [c for c in cols if c in df.columns]
    out = df[available].copy()
    for col in out.columns:
        if col in PCT_COLS:
            out[col] = out[col].map(fmt_pct)
        elif col in DATE_COLS:
            out[col] = out[col].map(fmt_date)
        elif col in {"preipo_score", "model_score_tradeable_20d"}:
            out[col] = out[col].map(lambda x: "—" if pd.isna(x) else f"{float(x):.2f}")
        elif col in {"issue_price", "offer_price_low", "offer_price_high", "open", "high", "low", "close"}:
            out[col] = out[col].map(lambda x: "—" if pd.isna(x) else f"{float(x):.2f}")
        elif col in {"amount", "fundraising_amount_hkd", "market_cap_at_ipo_hkd"}:
            out[col] = out[col].map(fmt_money)
    return out.rename(columns=DISPLAY_LABELS)


def is_missing(value: Any) -> bool:
    return pd.isna(value) or str(value).strip() in {"", "Unknown", "None", "nan", "—"}

# ============================================================
# Listed stock rule engine
# ============================================================

def infer_path_label(row: pd.Series) -> str:
    d1 = safe_float(row.get("d1_close_ret"), 0.0) or 0.0
    max20 = safe_float(row.get("max_20_ret"), 0.0) or 0.0
    min20 = safe_float(row.get("min_20_ret"), 0.0) or 0.0
    max60 = safe_float(row.get("max_60_ret"), 0.0) or 0.0
    min60 = safe_float(row.get("min_60_ret"), 0.0) or 0.0
    if d1 >= 0.30 and min20 > -0.12:
        return "strong_open"
    if min20 <= -0.08 and max60 >= 0.35:
        return "deep_v_rebound"
    if d1 >= 0.20 and min60 <= -0.20:
        return "pop_then_fade"
    if min20 <= -0.25 or min60 <= -0.35:
        return "persistent_break"
    if max20 >= 0.20 and min20 > -0.15:
        return "moderate_tradeable"
    return "watch"


def rule_score(row: pd.Series) -> float:
    d1 = safe_float(row.get("d1_close_ret"), 0.0) or 0.0
    max20 = safe_float(row.get("max_20_ret"), 0.0) or 0.0
    min20 = safe_float(row.get("min_20_ret"), 0.0) or 0.0
    max60 = safe_float(row.get("max_60_ret"), 0.0) or 0.0
    path = str(row.get("path_label", ""))
    score = 0.35
    if d1 > 0:
        score += min(d1, 0.4) * 0.5
    if max20 > 0:
        score += min(max20, 0.8) * 0.35
    if max60 > 0:
        score += min(max60, 1.0) * 0.10
    if min20 < 0:
        score += max(min20, -0.5) * 0.55
    if path == "strong_open":
        score += 0.12
    elif path in {"moderate_tradeable", "deep_v_rebound"}:
        score += 0.06
    elif path in {"persistent_break", "broken", "pop_then_fade"}:
        score -= 0.12
    return float(max(0.05, min(0.87, score)))


def classify_decision_tier(row: pd.Series) -> str:
    score = safe_float(row.get("model_score_tradeable_20d"), 0.0) or 0.0
    path = str(row.get("path_label", ""))
    min20 = safe_float(row.get("min_20_ret"), 0.0) or 0.0
    if path in {"persistent_break", "broken"} or min20 <= -0.30:
        return "D 回避/仅跟踪"
    if score >= 0.78 or path == "strong_open":
        return "A 高优先"
    if score >= 0.60 or path in {"moderate_tradeable", "deep_v_rebound"}:
        return "B 交易观察"
    return "C 等触发"


def classify_risk_level(row: pd.Series) -> str:
    min20 = safe_float(row.get("min_20_ret"), 0.0) or 0.0
    min60 = safe_float(row.get("min_60_ret"), 0.0) or 0.0
    path = str(row.get("path_label", ""))
    if path in {"persistent_break", "broken"} or min20 <= -0.25 or min60 <= -0.35:
        return "高风险"
    if path == "pop_then_fade" or min20 <= -0.12 or min60 <= -0.20:
        return "中高风险"
    if is_missing(row.get("issue_price")):
        return "中风险/数据缺口"
    return "中低风险"


def primary_action(row: pd.Series) -> str:
    risk = str(row.get("risk_level", ""))
    tier = str(row.get("decision_tier", ""))
    if "高风险" in risk:
        return "一级回避"
    if tier.startswith("A"):
        return "可进一级重点池"
    if tier.startswith("B"):
        return "小额/选择性参与"
    return "暂不参与"


def secondary_action(row: pd.Series) -> str:
    path = str(row.get("path_label", "watch"))
    if path == "strong_open":
        return "不追高，等回踩确认"
    if path == "deep_v_rebound":
        return "等深V收回发行价"
    if path == "moderate_tradeable":
        return "纳入首月交易池"
    if path == "pop_then_fade":
        return "只卖不追"
    if path in {"persistent_break", "broken"}:
        return "不接飞刀"
    return "观察"


def position_hint(row: pd.Series) -> str:
    risk = str(row.get("risk_level", ""))
    tier = str(row.get("decision_tier", ""))
    if "高风险" in risk:
        return "0 / 仅跟踪"
    if tier.startswith("A"):
        return "研究仓→确认后加仓"
    if tier.startswith("B"):
        return "小仓试错"
    return "等触发再动"


def sell_signal(row: pd.Series) -> str:
    path = str(row.get("path_label", "watch"))
    max20 = safe_float(row.get("max_20_ret"), 0.0) or 0.0
    min20 = safe_float(row.get("min_20_ret"), 0.0) or 0.0
    if path in {"persistent_break", "broken"}:
        return "重新站回发行价前不买入。"
    if path == "pop_then_fade":
        return "放量不创新高先止盈；跌破发行价降优先级。"
    if path == "strong_open" and max20 >= 0.35:
        return "20日内涨幅大，放量滞涨或跌破5日线时分批止盈。"
    if path == "deep_v_rebound":
        return "深V买入后再次跌回发行价下方且两日不收回，止损。"
    if min20 <= -0.15:
        return "波动偏大，止损优先于补仓。"
    return "以发行价、首日低点、首日VWAP为三道风控线。"


def normalize_listed(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_common(df)
    if df.empty:
        return df
    if "listing_date" not in df.columns:
        df["listing_date"] = pd.NaT
    if "path_label" not in df.columns:
        df["path_label"] = df.apply(infer_path_label, axis=1)
    else:
        blank = df["path_label"].isna() | df["path_label"].astype(str).str.strip().eq("")
        df.loc[blank, "path_label"] = df[blank].apply(infer_path_label, axis=1)
    if "model_score_tradeable_20d" not in df.columns:
        df["model_score_tradeable_20d"] = df.apply(rule_score, axis=1)
    else:
        missing = df["model_score_tradeable_20d"].isna()
        df.loc[missing, "model_score_tradeable_20d"] = df[missing].apply(rule_score, axis=1)
    today = pd.Timestamp.today().normalize()
    df["days_since_listing"] = (today - df["listing_date"]).dt.days
    df.loc[df["listing_date"].isna(), "days_since_listing"] = pd.NA
    df["decision_tier"] = df.apply(classify_decision_tier, axis=1)
    df["risk_level"] = df.apply(classify_risk_level, axis=1)
    df["primary_action"] = df.apply(primary_action, axis=1)
    df["secondary_action"] = df.apply(secondary_action, axis=1)
    df["position_hint"] = df.apply(position_hint, axis=1)
    df["sell_signal"] = df.apply(sell_signal, axis=1)
    df["stage_cn"] = "已上市"
    df["data_gap_count"] = df.apply(lambda r: sum(is_missing(r.get(c)) for c, _, _ in REQUIRED_FIELDS), axis=1)
    return df

# ============================================================
# Pre-IPO / A1 project engine
# ============================================================

def infer_stage(row: pd.Series) -> str:
    raw = str(row.get("project_status", "")).strip().lower()
    if raw:
        if any(x in raw for x in ["withdraw", "失效", "撤回", "inactive", "lapsed"]):
            return "失效/撤回"
        if any(x in raw for x in ["listed", "已上市"]):
            return "已上市"
        if any(x in raw for x in ["allot", "配发", "配售结果", "定价"]):
            return "定价/配发结果"
        if any(x in raw for x in ["prospectus", "招股", "offering"]):
            return "招股中"
        if any(x in raw for x in ["phip", "聆讯"]):
            return "聆讯后/PHIP"
        if any(x in raw for x in ["query", "update", "问询", "更新"]):
            return "问询/更新中"
        if any(x in raw for x in ["a1", "application", "递表", "申请"]):
            return "A1递表/申请版本"
    if not is_missing(row.get("listing_date")):
        return "已上市"
    if not is_missing(row.get("allotment_result_date")):
        return "定价/配发结果"
    if not is_missing(row.get("prospectus_date")) or not is_missing(row.get("issue_price")):
        return "招股中"
    if not is_missing(row.get("phip_date")):
        return "聆讯后/PHIP"
    if not is_missing(row.get("a1_date")) or not is_missing(row.get("application_proof_date")):
        return "A1递表/申请版本"
    return "未知"


def project_doc_status(row: pd.Series) -> str:
    has_a1 = not is_missing(row.get("a1_date")) or not is_missing(row.get("application_proof_date")) or not is_missing(row.get("doc_a1_url"))
    has_prospectus = not is_missing(row.get("prospectus_date")) or not is_missing(row.get("doc_prospectus_url"))
    has_allot = not is_missing(row.get("allotment_result_date")) or not is_missing(row.get("doc_allotment_url"))
    parts = []
    parts.append("A1✓" if has_a1 else "A1缺")
    parts.append("招股书✓" if has_prospectus else "招股书缺")
    parts.append("配发✓" if has_allot else "配发缺")
    return " / ".join(parts)


def preipo_score_rule(row: pd.Series) -> float:
    stage = row.get("stage_cn", infer_stage(row))
    score = 45.0
    score += {"A1递表/申请版本": 0, "问询/更新中": 3, "聆讯后/PHIP": 8, "招股中": 12, "定价/配发结果": 16, "已上市": 0}.get(stage, -5)
    # information completeness matters before listing
    for col, points in [
        ("industry", 3), ("sponsor_names", 4), ("offer_price_low", 3), ("offer_price_high", 3),
        ("fundraising_amount_hkd", 4), ("market_cap_at_ipo_hkd", 4), ("cornerstone_names", 4),
        ("public_subscription_multiple", 4), ("international_subscription_multiple", 6),
        ("one_lot_success_rate", 2), ("clawback_ratio", 2),
    ]:
        if not is_missing(row.get(col)):
            score += points
    pub = safe_float(row.get("public_subscription_multiple"))
    intl = safe_float(row.get("international_subscription_multiple"))
    cornerstone = safe_float(row.get("cornerstone_ratio"))
    if intl is not None:
        if intl >= 5:
            score += 8
        elif intl >= 2:
            score += 4
        elif intl < 1:
            score -= 8
    if pub is not None:
        if 10 <= pub <= 100:
            score += 4
        elif pub > 300:
            score -= 3  # 散户过热，不直接给高分
    if cornerstone is not None:
        if 0.15 <= cornerstone <= 0.45:
            score += 3
        elif cornerstone > 0.6:
            score -= 5
    gaps = sum(is_missing(row.get(c)) for c, _, _ in REQUIRED_FIELDS)
    score -= min(gaps, 10) * 1.2
    return max(5.0, min(90.0, score))


def preipo_action(row: pd.Series) -> str:
    stage = row.get("stage_cn", infer_stage(row))
    score = safe_float(row.get("preipo_score"), 0.0) or 0.0
    gaps = int(row.get("data_gap_count", 99)) if not pd.isna(row.get("data_gap_count", pd.NA)) else 99
    if stage in {"失效/撤回"}:
        return "剔除/仅留历史"
    if stage in {"A1递表/申请版本", "问询/更新中"}:
        return "A1研究池：先读商业模式+股东+保荐人"
    if stage == "聆讯后/PHIP":
        return "预备额度：等招股价区间和基石"
    if stage == "招股中":
        if score >= 65 and gaps <= 5:
            return "进入一级/锚定讨论"
        return "只做预审，等待配发结果"
    if stage == "定价/配发结果":
        if score >= 70:
            return "上市前最终评审"
        return "不抢首日，准备二级观察"
    if stage == "已上市":
        return "转入半新股池"
    return "资料不足，先补文件"


def normalize_projects(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_common(df)
    if df.empty:
        return df
    if "temp_code" not in df.columns:
        df["temp_code"] = ""
    if "code" not in df.columns:
        df["code"] = ""
    df["stage_cn"] = df.apply(infer_stage, axis=1)
    df["stage_rank"] = df["stage_cn"].map(STAGE_RANK).fillna(99).astype(int)
    df["doc_status"] = df.apply(project_doc_status, axis=1)
    df["data_gap_count"] = df.apply(lambda r: sum(is_missing(r.get(c)) for c, _, _ in REQUIRED_FIELDS), axis=1)
    if "preipo_score" not in df.columns:
        df["preipo_score"] = df.apply(preipo_score_rule, axis=1)
    else:
        df["preipo_score"] = pd.to_numeric(df["preipo_score"], errors="coerce")
        missing = df["preipo_score"].isna()
        df.loc[missing, "preipo_score"] = df[missing].apply(preipo_score_rule, axis=1)
    df["preipo_action"] = df.apply(preipo_action, axis=1)
    return df


def make_project_template() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "temp_code": "81001.HK",
            "code": "",
            "name": "示例A1申请人",
            "project_status": "A1递表",
            "a1_date": "2026-05-01",
            "application_proof_date": "2026-05-01",
            "phip_date": "",
            "prospectus_date": "",
            "pricing_date": "",
            "allotment_result_date": "",
            "expected_listing_date": "",
            "listing_date": "",
            "industry": "示例行业",
            "business_summary": "一句话业务摘要",
            "sponsor_names": "保荐人A;保荐人B",
            "overall_coordinators": "整体协调人A",
            "offer_price_low": "",
            "offer_price_high": "",
            "issue_price": "",
            "fundraising_amount_hkd": "",
            "market_cap_at_ipo_hkd": "",
            "cornerstone_names": "",
            "cornerstone_amount_hkd": "",
            "cornerstone_ratio": "",
            "public_subscription_multiple": "",
            "international_subscription_multiple": "",
            "one_lot_success_rate": "",
            "clawback_ratio": "",
            "doc_a1_url": "",
            "doc_prospectus_url": "",
            "doc_allotment_url": "",
            "notes": "",
        }
    ])


def make_doc_template() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "temp_code": "81001.HK", "code": "", "name": "示例A1申请人", "doc_type": "Application Proof/A1",
            "doc_date": "2026-05-01", "doc_name": "示例A1申请版本.pdf", "doc_url": "", "local_file": "",
            "extraction_status": "未提取", "key_fields_found": "业务;财务;风险;保荐人", "notes": "",
        },
        {
            "temp_code": "", "code": "06610.HK", "name": "示例已上市公司", "doc_type": "Allotment Results/配发结果",
            "doc_date": "2026-06-01", "doc_name": "示例配发结果公告.pdf", "doc_url": "", "local_file": "",
            "extraction_status": "未提取", "key_fields_found": "发行价;公开认购倍数;国际配售倍数;一手中签率;回拨;基石", "notes": "",
        },
    ])


def make_price_template() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "code": "06610.HK", "name": "示例公司", "listing_date": "2026-05-01", "trade_date": "2026-05-01",
            "day_offset": 0, "sample_bucket": "D0-D10每日", "open": 10.0, "high": 11.0, "low": 9.5, "close": 10.8,
            "volume": 1000000, "amount": 10800000, "turnover_rate": 0.05, "issue_price": 10.0,
            "ret_from_ipo": 0.08, "drawdown_from_high": 0.0,
        }
    ])

# ============================================================
# Data loading
# ============================================================

@st.cache_data(show_spinner=False)
def load_all_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, str]]:
    listed_raw, listed_src = read_csv_if_exists(LISTED_DATA_CANDIDATES)
    projects_raw, project_src = read_csv_if_exists(PROJECT_DATA_CANDIDATES)
    docs_raw, doc_src = read_csv_if_exists(DOC_DATA_CANDIDATES)
    price_raw, price_src = read_csv_if_exists(PRICE_SAMPLE_CANDIDATES)
    patch_raw, patch_src = read_csv_if_exists(PATCH_CANDIDATES)

    listed = normalize_listed(listed_raw) if not listed_raw.empty else pd.DataFrame()
    projects = normalize_projects(projects_raw) if not projects_raw.empty else pd.DataFrame()

    # Patch can be used for both listed and projects by code/temp_code.
    if not patch_raw.empty:
        patch = normalize_projects(patch_raw)
        listed = overlay_patch(listed, patch, keys=["code"])
        projects = overlay_patch(projects, patch, keys=["code", "temp_code"])

    docs = normalize_docs(docs_raw, projects) if not docs_raw.empty else synthesize_docs_from_projects(projects)
    price = normalize_price(price_raw) if not price_raw.empty else pd.DataFrame()

    sources = {
        "listed": listed_src,
        "projects": project_src,
        "docs": doc_src,
        "price": price_src,
        "patch": patch_src,
    }
    return listed, projects, docs, price, sources


def overlay_patch(base: pd.DataFrame, patch: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if base.empty or patch.empty:
        return base
    out = base.copy()
    for key in keys:
        if key not in out.columns or key not in patch.columns:
            continue
        p = patch[patch[key].astype(str).str.strip() != ""].drop_duplicates(key, keep="last").set_index(key)
        if p.empty:
            continue
        out = out.set_index(key)
        common = out.index.intersection(p.index)
        for col in p.columns:
            if col not in out.columns:
                out[col] = pd.NA
            vals = p.loc[common, col]
            mask = vals.map(lambda x: not is_missing(x))
            out.loc[common[mask], col] = vals[mask]
        out = out.reset_index()
    if "stage_cn" in out.columns:
        return normalize_projects(out) if "preipo_score" in out.columns or "temp_code" in out.columns else normalize_listed(out)
    return out


def normalize_docs(df: pd.DataFrame, projects: pd.DataFrame) -> pd.DataFrame:
    df = normalize_common(df)
    if "doc_type" not in df.columns:
        df["doc_type"] = "Unknown"
    if "extraction_status" not in df.columns:
        df["extraction_status"] = "未提取"
    if "key_fields_found" not in df.columns:
        df["key_fields_found"] = ""
    if "notes" not in df.columns:
        df["notes"] = ""
    if "stage_cn" not in df.columns:
        if not projects.empty:
            stage_map = pd.concat([
                projects[[c for c in ["code", "temp_code", "stage_cn"] if c in projects.columns]]
            ])
            # simple row-wise fallback
            df["stage_cn"] = df.apply(lambda r: lookup_stage(r, projects), axis=1)
        else:
            df["stage_cn"] = "未知"
    return df


def lookup_stage(row: pd.Series, projects: pd.DataFrame) -> str:
    for key in ["code", "temp_code"]:
        v = row.get(key, "")
        if is_missing(v) or key not in projects.columns:
            continue
        hit = projects[projects[key].astype(str) == str(v)]
        if not hit.empty:
            return str(hit.iloc[0].get("stage_cn", "未知"))
    return "未知"


def synthesize_docs_from_projects(projects: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if projects.empty:
        return pd.DataFrame()
    for _, r in projects.iterrows():
        for doc_type, date_col, url_col in [
            ("Application Proof/A1", "application_proof_date", "doc_a1_url"),
            ("PHIP/聆讯后资料集", "phip_date", "doc_phip_url"),
            ("Prospectus/招股书", "prospectus_date", "doc_prospectus_url"),
            ("Allotment Results/配发结果", "allotment_result_date", "doc_allotment_url"),
        ]:
            if not is_missing(r.get(date_col)) or not is_missing(r.get(url_col)):
                rows.append({
                    "temp_code": r.get("temp_code", ""), "code": r.get("code", ""), "name": r.get("name", ""),
                    "stage_cn": r.get("stage_cn", ""), "doc_type": doc_type, "doc_date": r.get(date_col, pd.NaT),
                    "doc_name": doc_type, "doc_url": r.get(url_col, ""), "extraction_status": "待提取", "key_fields_found": "", "notes": "",
                })
    return normalize_docs(pd.DataFrame(rows), projects) if rows else pd.DataFrame()


def normalize_price(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_common(df)
    if df.empty:
        return df
    if "day_offset" not in df.columns and {"code", "trade_date"}.issubset(df.columns):
        df = df.sort_values(["code", "trade_date"])
        df["day_offset"] = df.groupby("code").cumcount()
    if "sample_bucket" not in df.columns:
        df["sample_bucket"] = df["day_offset"].map(sample_bucket)
    return df


def sample_bucket(day_offset: Any) -> str:
    d = int(safe_float(day_offset, 0) or 0)
    if d <= 10:
        return "D0-D10每日"
    if d <= 30:
        return "D11-D30隔日"
    if d <= 60:
        return "D31-D60每5日"
    return "D61-D180每10日"

# ============================================================
# Filters and memo
# ============================================================

def filter_common(projects: pd.DataFrame, listed: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    st.sidebar.header("筛选")
    stages = ["全部"] + sorted(projects.get("stage_cn", pd.Series(dtype=str)).dropna().unique().tolist(), key=lambda x: STAGE_RANK.get(x, 99))
    stage = st.sidebar.selectbox("上市前阶段", stages, index=0)
    pview = projects.copy()
    if stage != "全部" and "stage_cn" in pview.columns:
        pview = pview[pview["stage_cn"] == stage]

    industries = sorted(set(projects.get("industry", pd.Series(dtype=str)).dropna().astype(str).tolist()) | set(listed.get("industry", pd.Series(dtype=str)).dropna().astype(str).tolist()))
    ind = st.sidebar.selectbox("行业", ["全部"] + industries, index=0)
    if ind != "全部":
        if "industry" in pview.columns:
            pview = pview[pview["industry"] == ind]
        if "industry" in listed.columns:
            listed = listed[listed["industry"] == ind]

    keyword = st.sidebar.text_input("代码/名称搜索", "").strip()
    if keyword:
        for var_name, df in [("pview", pview), ("listed", listed)]:
            if df.empty:
                continue
            cols = [c for c in ["code", "temp_code", "name"] if c in df.columns]
            mask = pd.Series(False, index=df.index)
            for c in cols:
                mask |= df[c].astype(str).str.contains(keyword, case=False, na=False)
            if var_name == "pview":
                pview = df[mask]
            else:
                listed = df[mask]

    min_preipo = st.sidebar.slider("最低上市前分", 0.0, 90.0, 0.0, 5.0)
    if "preipo_score" in pview.columns:
        pview = pview[pview["preipo_score"].fillna(0) >= min_preipo]
    return pview, listed


def make_preipo_memo(row: pd.Series) -> str:
    return f"""# A1/IPO上市前研究备忘录

## 1. 项目概览

- 申请人/股票：{row.get('temp_code','')} {row.get('code','')} {row.get('name','')}
- 当前阶段：{row.get('stage_cn','—')}
- A1/递表日：{fmt_date(row.get('a1_date'))}
- PHIP日：{fmt_date(row.get('phip_date'))}
- 招股书日：{fmt_date(row.get('prospectus_date'))}
- 预计/正式上市日：{fmt_date(row.get('expected_listing_date'))} / {fmt_date(row.get('listing_date'))}
- 行业：{row.get('industry','—')}
- 保荐人：{row.get('sponsor_names','—')}
- 业务摘要：{row.get('business_summary','—')}

## 2. 上市前模型结论

- 上市前分：{fmt_num(row.get('preipo_score'))}
- 建议：{row.get('preipo_action','—')}
- 文件状态：{row.get('doc_status','—')}
- 数据缺口：{row.get('data_gap_count','—')}

## 3. 发行结构

- 招股价区间：{fmt_num(row.get('offer_price_low'))} - {fmt_num(row.get('offer_price_high'))}
- 最终发行价：{fmt_num(row.get('issue_price'))}
- 募资金额：{fmt_money(row.get('fundraising_amount_hkd'))}
- 发行市值：{fmt_money(row.get('market_cap_at_ipo_hkd'))}
- 基石名单：{row.get('cornerstone_names','—')}
- 基石占比：{fmt_pct(row.get('cornerstone_ratio'))}
- 公开认购倍数：{fmt_num(row.get('public_subscription_multiple'))}
- 国际配售倍数：{fmt_num(row.get('international_subscription_multiple'))}
- 一手中签率：{fmt_pct(row.get('one_lot_success_rate'))}
- 回拨比例：{fmt_pct(row.get('clawback_ratio'))}

## 4. 决策路径

- A1阶段：先判断商业模式、股东质量、保荐人、监管/客户集中/亏损等风险。
- 招股阶段：补招股价区间、基石、募资额、发行市值，判断是否进入一级讨论。
- 配发结果阶段：补公开认购、国际配售、一手中签、回拨，做上市前最终评分。
- 上市后：转入180日行情采样，执行深V/追高/破发路径模型。

> 本备忘录用于研究辅助，不连接实盘，不构成自动交易指令。
"""

# ============================================================
# Render tabs
# ============================================================

def render_header(projects: pd.DataFrame, listed: pd.DataFrame, docs: pd.DataFrame, price: pd.DataFrame, sources: dict[str, str]) -> None:
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)
    st.sidebar.success("数据源已加载")
    for k, v in sources.items():
        if v:
            st.sidebar.caption(f"{k}: {v}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("A1/未上市项目", f"{len(projects):,}")
    c2.metric("已上市样本", f"{len(listed):,}")
    c3.metric("发行文件记录", f"{len(docs):,}")
    c4.metric("180日行情记录", f"{len(price):,}")

    c5, c6, c7, c8 = st.columns(4)
    if not projects.empty and "stage_cn" in projects.columns:
        c5.metric("招股中/配发", int(projects["stage_cn"].isin(["招股中", "定价/配发结果"]).sum()))
        c6.metric("PHIP", int((projects["stage_cn"] == "聆讯后/PHIP").sum()))
    else:
        c5.metric("招股中/配发", 0)
        c6.metric("PHIP", 0)
    c7.metric("上市前均分", fmt_num(projects["preipo_score"].mean() if "preipo_score" in projects.columns and len(projects) else pd.NA))
    c8.metric("已上市平均缺口", fmt_num(listed["data_gap_count"].mean() if "data_gap_count" in listed.columns and len(listed) else pd.NA, 1))


def render_preipo_tab(projects: pd.DataFrame) -> None:
    st.subheader("A1 / 临时代码 / 未上市项目池")
    st.write("这个页面是模型前移的核心：A1递表、PHIP、招股中、配发结果都进同一个漏斗，正式上市后再转入半新股池。")
    if projects.empty:
        st.warning("还没有 ipo_projects.csv。请先下载模板，用 iFind/超级命令导出后上传到 deploy_data/ipo_projects.csv。")
        template = make_project_template()
        st.dataframe(template, use_container_width=True, hide_index=True)
        st.download_button("下载 ipo_projects_template.csv", template.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), "ipo_projects_template.csv", "text/csv")
        return

    sort_col = st.selectbox("排序", [c for c in ["stage_rank", "preipo_score", "a1_date", "prospectus_date", "expected_listing_date", "data_gap_count"] if c in projects.columns], index=1 if "preipo_score" in projects.columns else 0)
    ascending = st.toggle("升序", value=False)
    table = projects.sort_values(sort_col, ascending=ascending)
    st.dataframe(make_cn_table(table, PROJECT_DISPLAY_COLS), use_container_width=True, hide_index=True)

    st.markdown("### 单项目上市前 Memo")
    opts = (projects.get("temp_code", pd.Series([""]*len(projects), index=projects.index)).astype(str) + " " + projects.get("code", pd.Series([""]*len(projects), index=projects.index)).astype(str) + " " + projects["name"].astype(str)).tolist()
    selected = st.selectbox("选择项目", opts)
    if selected:
        key = selected.split()[0]
        row = projects[(projects.get("temp_code", pd.Series(dtype=str)).astype(str) == key) | (projects.get("code", pd.Series(dtype=str)).astype(str) == key)]
        if row.empty:
            row = projects.iloc[[0]]
        r = row.iloc[0]
        a, b, c, d = st.columns(4)
        a.metric("阶段", r.get("stage_cn", "—"))
        b.metric("上市前分", fmt_num(r.get("preipo_score")))
        c.metric("文件", r.get("doc_status", "—"))
        d.metric("缺口", r.get("data_gap_count", "—"))
        st.info(r.get("preipo_action", "—"))
        memo = make_preipo_memo(r)
        st.markdown(memo)
        st.download_button("下载该项目 Memo.md", memo.encode("utf-8-sig"), f"{r.get('temp_code') or r.get('code')}_preipo_memo.md", "text/markdown")


def render_docs_tab(docs: pd.DataFrame) -> None:
    st.subheader("发行文件与公告跟踪")
    st.write("发行资料不应只当附件存档，而要变成字段：A1/招股书用于上市前研究，配发结果公告用于最终一级评分。")
    if docs.empty:
        st.warning("还没有 ipo_docs.csv。先用模板登记 iFind 招股书/配发结果公告元数据。")
        template = make_doc_template()
        st.dataframe(template, use_container_width=True, hide_index=True)
        st.download_button("下载 ipo_docs_template.csv", template.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), "ipo_docs_template.csv", "text/csv")
    else:
        doc_type = st.selectbox("文件类型", ["全部"] + sorted(docs["doc_type"].dropna().astype(str).unique().tolist())) if "doc_type" in docs.columns else "全部"
        view = docs if doc_type == "全部" else docs[docs["doc_type"].astype(str) == doc_type]
        st.dataframe(make_cn_table(view, DOC_DISPLAY_COLS), use_container_width=True, hide_index=True)

    st.markdown("### 两类公告的模型职责")
    matrix = pd.DataFrame([
        {"文件": "A1/Application Proof", "阶段": "临时代码/递表后", "重点字段": "业务、股东、财务、风险、客户集中、保荐人、上市理由", "模型用途": "决定是否进入A1研究池和基本面尽调优先级"},
        {"文件": "招股书/Prospectus", "阶段": "招股中", "重点字段": "招股价区间、募资额、基石、上市时间表、估值锚", "模型用途": "决定是否准备一级额度/锚定投资"},
        {"文件": "配发结果/Allotment Results", "阶段": "上市前1日左右", "重点字段": "最终发行价、公开认购倍数、国际配售倍数、一手中签率、回拨比例、基石最终认购", "模型用途": "上市前最终评分和首日/二级策略"},
    ])
    st.dataframe(matrix, use_container_width=True, hide_index=True)


def render_listed_tab(listed: pd.DataFrame) -> None:
    st.subheader("已上市 IPO / 半新股池")
    if listed.empty:
        st.info("暂无已上市样本。")
        return
    sort_col = st.selectbox("排序字段", [c for c in ["model_score_tradeable_20d", "listing_date", "max_20_ret", "d1_close_ret", "data_gap_count"] if c in listed.columns], index=0)
    ascending = st.toggle("升序", value=False, key="listed_asc")
    view = listed.sort_values(sort_col, ascending=ascending)
    st.dataframe(make_cn_table(view, LISTED_DISPLAY_COLS), use_container_width=True, hide_index=True)
    csv = view.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button("下载当前半新股池 CSV", csv, "hk_ipo_listed_pool.csv", "text/csv")

    if "path_label" in view.columns:
        st.markdown("### 路径分布")
        path_counts = view["path_label"].value_counts().rename_axis("path").reset_index(name="count")
        path_counts["路径"] = path_counts["path"].map(lambda x: PATH_CN.get(x, x))
        st.bar_chart(path_counts.set_index("路径")["count"])


def render_price_tab(price: pd.DataFrame) -> None:
    st.subheader("上市后 180 日行情：密集到稀疏采样")
    st.write("原则：上市初期每天抓，越往后越稀疏。这样既保留首日/深V/破发路径，又不让数据量失控。")
    rule = pd.DataFrame([
        {"区间": "D0-D10", "频率": "每个交易日", "用途": "首日、T+1/T+5、破发/守发行价、暗盘/首日资金承接"},
        {"区间": "D11-D30", "频率": "每2个交易日", "用途": "深V、回踩确认、首月交易池"},
        {"区间": "D31-D60", "频率": "每5个交易日", "用途": "趋势延续/升后破发"},
        {"区间": "D61-D180", "频率": "每10个交易日", "用途": "解禁前风险、半新股中期走势"},
    ])
    st.dataframe(rule, use_container_width=True, hide_index=True)

    if price.empty:
        st.warning("还没有 price_180d_sample.csv。先下载模板，后续用本地 iFind 脚本生成。")
        template = make_price_template()
        st.dataframe(template, use_container_width=True, hide_index=True)
        st.download_button("下载 price_180d_sample_template.csv", template.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), "price_180d_sample_template.csv", "text/csv")
        return

    codes = sorted(price["code"].dropna().astype(str).unique().tolist()) if "code" in price.columns else []
    selected = st.selectbox("选择股票", codes)
    view = price[price["code"].astype(str) == selected] if selected else price
    st.dataframe(make_cn_table(view, PRICE_DISPLAY_COLS), use_container_width=True, hide_index=True)
    if {"trade_date", "close"}.issubset(view.columns) and not view.empty:
        chart = view.sort_values("trade_date").set_index("trade_date")[["close"]]
        st.line_chart(chart)


def render_quality_tab(projects: pd.DataFrame, listed: pd.DataFrame, docs: pd.DataFrame, price: pd.DataFrame) -> None:
    st.subheader("数据质量与下一步字段")
    target = pd.concat([projects, listed], ignore_index=True, sort=False) if not projects.empty or not listed.empty else pd.DataFrame()
    rows = []
    for col, cn, use in REQUIRED_FIELDS:
        if not target.empty and col in target.columns:
            miss = target[col].map(is_missing)
            missing_rate = float(miss.mean())
            status = "可用" if missing_rate < 0.2 else "部分可用" if missing_rate < 0.8 else "缺口严重"
        else:
            missing_rate = 1.0
            status = "缺失"
        rows.append({"字段": col, "中文": cn, "状态": status, "缺失率": missing_rate, "用途": use})
    q = pd.DataFrame(rows)
    q["缺失率"] = q["缺失率"].map(fmt_pct)
    st.dataframe(q, use_container_width=True, hide_index=True)

    st.markdown("### 下载模板")
    c1, c2, c3 = st.columns(3)
    c1.download_button("ipo_projects_template.csv", make_project_template().to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), "ipo_projects_template.csv", "text/csv")
    c2.download_button("ipo_docs_template.csv", make_doc_template().to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), "ipo_docs_template.csv", "text/csv")
    c3.download_button("price_180d_sample_template.csv", make_price_template().to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), "price_180d_sample_template.csv", "text/csv")

    st.markdown("### 当前文件状态")
    status = pd.DataFrame([
        {"数据表": "ipo_projects.csv", "记录数": len(projects), "用途": "A1/临时代码/未上市项目池"},
        {"数据表": "ipo_docs.csv", "记录数": len(docs), "用途": "招股书与配发结果公告"},
        {"数据表": "hk_ipo_scored_public.csv", "记录数": len(listed), "用途": "已上市样本、路径标签、回测"},
        {"数据表": "price_180d_sample.csv", "记录数": len(price), "用途": "上市后180日价格路径"},
    ])
    st.dataframe(status, use_container_width=True, hide_index=True)


def render_ifind_tab() -> None:
    st.subheader("本地 iFind 取数路线")
    st.warning("Streamlit Cloud 不能直接连你本地 iFind。正确做法是：本地 Windows 跑 iFind 脚本 → 生成 deploy_data/*.csv → 上传 GitHub → 网站展示。")
    st.markdown(
        """
### 你这次明确的三个数据包

1. **港股 IPO 列表**：必须包含 A1/临时代码/未上市申请人，因为大部分投资决策发生在这个阶段。  
2. **发行资料**：本质上来自两个文件：招股书/Prospectus 和配发结果公告/Allotment Results。  
3. **上市后行情**：从上市日起到 180 天，按 D0-D10 每日、D11-D30 隔日、D31-D60 每5日、D61-D180 每10日采样。

### 本地导出后放置位置

- `deploy_data/ipo_projects.csv`
- `deploy_data/ipo_docs.csv`
- `deploy_data/price_180d_sample.csv`
- `deploy_data/hk_ipo_scored_public.csv`

### 超级命令建议搜索词

- `港股 A1 申请人 临时代码 Application Proof 招股书 保荐人 行业 递表日期`
- `港股 IPO 招股书 发行价区间 募资金额 基石投资者 保荐人`
- `港股 IPO 配发结果 公开认购倍数 国际配售倍数 一手中签率 回拨比例 最终发行价`
- `06610.HK 上市后 日行情 开盘价 最高价 最低价 收盘价 成交量 成交额 换手率`
"""
    )


def render_roadmap_tab() -> None:
    st.subheader("逐步完善路线")
    roadmap = pd.DataFrame([
        {"阶段": "Step 3 当前", "目标": "覆盖A1/临时代码", "产出": "ipo_projects、ipo_docs、price_180d三张表和界面"},
        {"阶段": "Step 4", "目标": "本地iFind自动导出", "产出": "ifind_fetch模板替换成真实字段函数"},
        {"阶段": "Step 5", "目标": "发行结构规则模型", "产出": "一级/基石/二级三个评分"},
        {"阶段": "Step 6", "目标": "公告文本抽取", "产出": "招股书/配发结果公告自动字段化"},
        {"阶段": "Step 7", "目标": "Walk-forward回测", "产出": "2024后滚动验证和因子稳定性"},
        {"阶段": "Step 8", "目标": "每日监控", "产出": "新A1、招股中、上市首月、卖点预警"},
    ])
    st.dataframe(roadmap, use_container_width=True, hide_index=True)

# ============================================================
# Main
# ============================================================

st.set_page_config(page_title="HK IPO 决策驾驶舱", page_icon="📈", layout="wide")

listed_df, project_df, docs_df, price_df, sources = load_all_data()
project_view, listed_view = filter_common(project_df, listed_df)
render_header(project_view, listed_view, docs_df, price_df, sources)
st.divider()

tabs = st.tabs(["① A1/未上市", "② 发行文件", "③ 已上市半新股", "④ 180日行情", "⑤ 数据质量", "⑥ iFind接入", "⑦ 路线图"])
with tabs[0]:
    render_preipo_tab(project_view)
with tabs[1]:
    render_docs_tab(docs_df)
with tabs[2]:
    render_listed_tab(listed_view)
with tabs[3]:
    render_price_tab(price_df)
with tabs[4]:
    render_quality_tab(project_df, listed_df, docs_df, price_df)
with tabs[5]:
    render_ifind_tab()
with tabs[6]:
    render_roadmap_tab()

st.caption("研究辅助工具｜不连接实盘｜不构成自动交易指令")
