from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


# ============================================================
# HK IPO / Newly Listed Stock Decision Cockpit
# Step 2: UI + data-quality + decision memo layer
# ============================================================

APP_TITLE = "港股 IPO / 半新股决策驾驶舱"
APP_SUBTITLE = (
    "Step 2：先把现有样本做成能汇报、能筛选、能生成 Memo 的投研界面；"
    "下一步再接 iFind 本地取数和发行结构字段。"
)

DATA_CANDIDATES = [
    Path("deploy_data/hk_ipo_scored_public.csv"),
    Path("hk_ipo_scored_public.csv"),
    Path("data/processed/hk_ipo_scored.csv"),
    Path("data/processed/hk_ipo_features.csv"),
]
PATCH_CANDIDATES = [
    Path("deploy_data/ipo_master_patch.csv"),
    Path("ipo_master_patch.csv"),
    Path("data/raw/ipo_master_patch.csv"),
]

PCT_COLS = [
    "d1_open_ret", "d1_close_ret", "d1_intraday_ret", "d1_amplitude",
    "d5_close_ret", "d20_close_ret", "d60_close_ret",
    "max_5_ret", "min_5_ret", "max_20_ret", "min_20_ret", "max_60_ret", "min_60_ret",
    "cornerstone_ratio", "one_lot_success_rate", "clawback_ratio", "final_price_position",
]
NUM_COLS = [
    "issue_price", "offer_price_low", "offer_price_high", "fundraising_amount_hkd",
    "market_cap_at_ipo_hkd", "cornerstone_amount_hkd", "public_subscription_multiple",
    "international_subscription_multiple", "d1_amount", "d1_volume", "quote_days",
    "model_score_tradeable_20d", "liquidity_score", "structure_score", "sentiment_score",
    "fundamental_score", "composite_score",
]
BOOL_COLS = [
    "label_strong_open", "label_deep_v", "label_broken", "label_pop_then_fade", "label_tradeable_20d",
]

# External field aliases: makes future iFind export easier.
COLUMN_ALIASES = {
    "证券代码": "code", "股票代码": "code", "代码": "code",
    "证券简称": "name", "股票简称": "name", "简称": "name", "名称": "name",
    "上市日期": "listing_date", "首挂日期": "listing_date",
    "行业": "industry", "所属行业": "industry", "恒生行业": "industry",
    "发行价": "issue_price", "最终发行价": "issue_price", "招股价": "issue_price",
    "招股价下限": "offer_price_low", "发售价下限": "offer_price_low",
    "招股价上限": "offer_price_high", "发售价上限": "offer_price_high",
    "定价位置": "final_price_position",
    "募资金额": "fundraising_amount_hkd", "集资额": "fundraising_amount_hkd",
    "发行市值": "market_cap_at_ipo_hkd", "上市市值": "market_cap_at_ipo_hkd",
    "保荐人": "sponsor_names", "联席保荐人": "sponsor_names", "整体协调人": "sponsor_names",
    "基石投资者": "cornerstone_names", "基石名单": "cornerstone_names",
    "基石金额": "cornerstone_amount_hkd", "基石认购金额": "cornerstone_amount_hkd",
    "基石占比": "cornerstone_ratio", "基石比例": "cornerstone_ratio",
    "公开认购倍数": "public_subscription_multiple", "公开发售认购倍数": "public_subscription_multiple",
    "国际配售倍数": "international_subscription_multiple", "国际发售认购倍数": "international_subscription_multiple",
    "一手中签率": "one_lot_success_rate",
    "回拨比例": "clawback_ratio",
}

TARGET_SCHEMA = [
    "code", "name", "listing_date", "industry", "issue_price", "offer_price_low", "offer_price_high",
    "final_price_position", "fundraising_amount_hkd", "market_cap_at_ipo_hkd", "sponsor_names",
    "cornerstone_names", "cornerstone_amount_hkd", "cornerstone_ratio", "public_subscription_multiple",
    "international_subscription_multiple", "one_lot_success_rate", "clawback_ratio", "d1_open_ret",
    "d1_close_ret", "d5_close_ret", "d20_close_ret", "d60_close_ret", "max_20_ret", "min_20_ret",
    "max_60_ret", "min_60_ret", "path_label", "model_score_tradeable_20d",
]

DISPLAY_LABELS = {
    "decision_tier": "决策层",
    "code": "代码",
    "name": "简称",
    "listing_date": "上市日",
    "days_since_listing": "上市天数",
    "industry": "行业",
    "issue_price": "发行价",
    "d1_close_ret": "首日收盘",
    "max_20_ret": "20D最大涨幅",
    "min_20_ret": "20D最大回撤",
    "max_60_ret": "60D最大涨幅",
    "path_label": "路径",
    "risk_level": "风险",
    "primary_action": "一级建议",
    "secondary_action": "二级建议",
    "position_hint": "仓位提示",
    "model_score_tradeable_20d": "模型分",
    "rule_recommendation": "规则建议",
    "model_recommendation": "模型建议",
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

PATH_DESC = {
    "strong_open": "首日/早期强势，关键不是追高，而是观察回踩后是否仍守发行价和首日成交密集区。",
    "deep_v_rebound": "早期下杀后资金回流，是二级半新股最值得单独建模的一类。",
    "moderate_tradeable": "波动和承接尚可，可纳入首月交易池，靠触发条件做仓位。",
    "pop_then_fade": "首日/早期情绪过热，后续承接不足，是卖点预警重点。",
    "persistent_break": "发行价支撑失效，除非重新站回发行价且成交改善，否则不接。",
    "broken": "发行价支撑失效，除非重新站回发行价且成交改善，否则不接。",
    "watch": "信息不足或趋势不清，先观察，不主动给高优先级。",
}

CORE_DISPLAY_COLS = [
    "decision_tier", "code", "name", "listing_date", "days_since_listing", "industry", "issue_price",
    "d1_close_ret", "max_20_ret", "min_20_ret", "max_60_ret", "path_label", "risk_level",
    "primary_action", "secondary_action", "position_hint", "model_score_tradeable_20d",
]

REQUIRED_NEXT_FIELDS = [
    ("industry", "行业分类", "用于行业胜率、估值锚和主题热度分层"),
    ("issue_price", "发行价", "用于破发、发行价支撑、发行估值计算"),
    ("public_subscription_multiple", "公开认购倍数", "判断散户拥挤度和回拨压力"),
    ("international_subscription_multiple", "国际配售倍数", "判断机构真实需求"),
    ("one_lot_success_rate", "一手中签率", "判断打新收益和资金拥挤"),
    ("clawback_ratio", "回拨比例", "判断上市流通盘和抛压"),
    ("cornerstone_names", "基石名单", "判断长期资金/产业方/明星机构质量"),
    ("cornerstone_ratio", "基石占比", "判断首日流通与6个月解禁压力"),
    ("sponsor_names", "保荐人", "建立保荐人历史胜率"),
    ("market_cap_at_ipo_hkd", "发行市值", "判断承接难度和估值安全边际"),
]


# ============================================================
# Data helpers
# ============================================================
def find_first_existing(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


def rename_known_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {c: COLUMN_ALIASES.get(c, c) for c in df.columns}
    return df.rename(columns=rename_map)


def clean_code(value: Any) -> str:
    if pd.isna(value):
        return ""
    s = str(value).strip().upper()
    if s.endswith(".HK"):
        left = s[:-3]
        if left.isdigit():
            return f"{int(left):04d}.HK"
        return s
    if s.isdigit():
        return f"{int(s):04d}.HK"
    return s


def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    df = rename_known_columns(df.copy())

    if "code" in df.columns:
        df["code"] = df["code"].map(clean_code)
    if "name" in df.columns:
        df["name"] = df["name"].astype(str).str.strip()
    else:
        df["name"] = ""
    if "industry" not in df.columns:
        df["industry"] = "Unknown"
    df["industry"] = df["industry"].fillna("Unknown").astype(str).str.strip().replace({"": "Unknown", "nan": "Unknown", "None": "Unknown"})

    if "listing_date" in df.columns:
        df["listing_date"] = pd.to_datetime(df["listing_date"], errors="coerce")
    else:
        df["listing_date"] = pd.NaT

    for col in PCT_COLS + NUM_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in BOOL_COLS:
        if col in df.columns:
            # Handles bool, 0/1, True/False strings.
            df[col] = df[col].map(lambda x: str(x).lower() in {"true", "1", "yes", "y"} if not isinstance(x, bool) else x).fillna(False)

    for col in ["path_label", "rule_recommendation", "model_recommendation"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    # Derive missing labels from returns when possible.
    if "path_label" not in df.columns:
        df["path_label"] = df.apply(infer_path_label, axis=1)
    else:
        blank = df["path_label"].astype(str).str.strip().eq("")
        if blank.any():
            df.loc[blank, "path_label"] = df[blank].apply(infer_path_label, axis=1)

    if "model_score_tradeable_20d" not in df.columns:
        df["model_score_tradeable_20d"] = df.apply(rule_score, axis=1)
    else:
        missing = df["model_score_tradeable_20d"].isna()
        if missing.any():
            df.loc[missing, "model_score_tradeable_20d"] = df[missing].apply(rule_score, axis=1)

    if "rule_recommendation" not in df.columns:
        df["rule_recommendation"] = ""
    if "model_recommendation" not in df.columns:
        df["model_recommendation"] = ""

    today = pd.Timestamp.today().normalize()
    df["days_since_listing"] = (today - df["listing_date"]).dt.days
    df.loc[df["listing_date"].isna(), "days_since_listing"] = pd.NA

    df["decision_tier"] = df.apply(classify_decision_tier, axis=1)
    df["risk_level"] = df.apply(classify_risk_level, axis=1)
    df["primary_action"] = df.apply(primary_action, axis=1)
    df["secondary_action"] = df.apply(secondary_action, axis=1)
    df["position_hint"] = df.apply(position_hint, axis=1)
    df["sell_signal"] = df.apply(sell_signal, axis=1)
    df["data_gap_count"] = df.apply(data_gap_count, axis=1)
    return df


def overlay_patch(base: pd.DataFrame, patch: pd.DataFrame) -> pd.DataFrame:
    """Merge an optional IPO master patch by code.

    Patch CSV can be exported from iFind later. It may use Chinese or English column names.
    Non-empty patch fields overwrite base fields.
    """
    if base.empty or patch.empty or "code" not in base.columns or "code" not in patch.columns:
        return base
    patch = normalize_data(patch)
    patch = patch.drop_duplicates("code", keep="last").set_index("code")
    out = base.copy().set_index("code")

    for col in patch.columns:
        if col in {"code", "decision_tier", "risk_level", "primary_action", "secondary_action", "position_hint", "sell_signal", "data_gap_count"}:
            continue
        if col not in out.columns:
            out[col] = pd.NA
        series = patch[col]
        common_idx = out.index.intersection(series.index)
        if len(common_idx) == 0:
            continue
        patch_values = series.loc[common_idx]
        mask = patch_values.notna() & (patch_values.astype(str).str.strip() != "")
        out.loc[common_idx[mask], col] = patch_values[mask]

    out = out.reset_index()
    return normalize_data(out)


@st.cache_data(show_spinner=False)
def load_base_data() -> tuple[pd.DataFrame, str, str]:
    data_path = find_first_existing(DATA_CANDIDATES)
    if data_path is None:
        return pd.DataFrame(), "", ""

    base = pd.read_csv(data_path, encoding="utf-8-sig")
    base = normalize_data(base)

    patch_path = find_first_existing(PATCH_CANDIDATES)
    patch_source = ""
    if patch_path is not None:
        try:
            patch = pd.read_csv(patch_path, encoding="utf-8-sig")
            base = overlay_patch(base, patch)
            patch_source = str(patch_path)
        except Exception as exc:
            patch_source = f"补丁文件读取失败：{patch_path} | {exc}"

    return base, str(data_path), patch_source


def load_uploaded_patch(file, base: pd.DataFrame) -> pd.DataFrame:
    if file is None:
        return base
    patch = pd.read_csv(file, encoding="utf-8-sig")
    return overlay_patch(base, patch)


# ============================================================
# Rule engine
# ============================================================
def safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def has_true(row: pd.Series, col: str) -> bool:
    return bool(row.get(col, False))


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
    issue_price_missing = pd.isna(row.get("issue_price"))

    if path in {"persistent_break", "broken"} or min20 <= -0.25 or min60 <= -0.35:
        return "高风险"
    if path == "pop_then_fade" or min20 <= -0.12 or min60 <= -0.20:
        return "中高风险"
    if issue_price_missing:
        return "中风险/数据缺口"
    return "中低风险"


def primary_action(row: pd.Series) -> str:
    tier = str(row.get("decision_tier", ""))
    risk = str(row.get("risk_level", ""))
    path = str(row.get("path_label", ""))
    pub_mult = safe_float(row.get("public_subscription_multiple"))
    intl_mult = safe_float(row.get("international_subscription_multiple"))

    if "高风险" in risk:
        return "一级回避"
    if tier.startswith("A"):
        if pub_mult is not None and pub_mult > 100 and (intl_mult is None or intl_mult < 3):
            return "打新谨慎，二级等回踩"
        return "可进一级重点池"
    if tier.startswith("B"):
        return "小额/选择性参与"
    if path == "deep_v_rebound":
        return "一级不抢，二级等V"
    return "暂不参与"


def secondary_action(row: pd.Series) -> str:
    path = str(row.get("path_label", "watch"))
    tier = str(row.get("decision_tier", ""))
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
    if tier.startswith("A"):
        return "等量价确认"
    return "观察"


def position_hint(row: pd.Series) -> str:
    tier = str(row.get("decision_tier", ""))
    risk = str(row.get("risk_level", ""))
    if "高风险" in risk:
        return "0 / 仅跟踪"
    if tier.startswith("A"):
        return "研究仓→确认后加仓"
    if tier.startswith("B"):
        return "小仓试错"
    if tier.startswith("C"):
        return "等触发再动"
    return "不建仓"


def sell_signal(row: pd.Series) -> str:
    path = str(row.get("path_label", "watch"))
    max20 = safe_float(row.get("max_20_ret"), 0.0) or 0.0
    min20 = safe_float(row.get("min_20_ret"), 0.0) or 0.0
    if path in {"persistent_break", "broken"}:
        return "跌破发行价后不补仓；重新站回发行价前不买入。"
    if path == "pop_then_fade":
        return "若跌破首日均价/发行价，降低优先级；放量不创新高先止盈。"
    if path == "strong_open" and max20 >= 0.35:
        return "20日内涨幅大，出现放量滞涨或跌破5日线时分批止盈。"
    if path == "deep_v_rebound":
        return "深V买入后若再次跌回发行价下方且两日不收回，止损。"
    if min20 <= -0.15:
        return "波动偏大，止损优先于补仓。"
    return "以发行价、首日低点、首日VWAP为三道风控线。"


def data_gap_count(row: pd.Series) -> int:
    count = 0
    for col, _, _ in REQUIRED_NEXT_FIELDS:
        value = row.get(col, pd.NA)
        if pd.isna(value) or str(value).strip() in {"", "Unknown", "None", "nan"}:
            count += 1
    return count


# ============================================================
# Formatting helpers
# ============================================================
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


def fmt_date(value: Any) -> str:
    if pd.isna(value):
        return "—"
    return pd.to_datetime(value).strftime("%Y-%m-%d")


def fmt_money_hkd(value: Any) -> str:
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


def pct_rate(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    return float(series.fillna(False).astype(bool).mean())


def make_cn_table(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    available = [c for c in cols if c in df.columns]
    out = df[available].copy()
    for col in PCT_COLS:
        if col in out.columns:
            out[col] = out[col].map(fmt_pct)
    for col in ["listing_date"]:
        if col in out.columns:
            out[col] = out[col].map(fmt_date)
    if "model_score_tradeable_20d" in out.columns:
        out["model_score_tradeable_20d"] = out["model_score_tradeable_20d"].map(lambda x: "—" if pd.isna(x) else f"{float(x):.2f}")
    if "issue_price" in out.columns:
        out["issue_price"] = out["issue_price"].map(lambda x: "—" if pd.isna(x) else f"{float(x):.2f}")
    out = out.rename(columns=DISPLAY_LABELS)
    return out


def metric_box(label: str, value: str, help_text: str | None = None) -> None:
    st.metric(label, value, help=help_text)


# ============================================================
# Filtering + memo
# ============================================================
def filter_data(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("筛选")
    view = df.copy()

    if "listing_date" in view.columns and view["listing_date"].notna().any():
        min_date = view["listing_date"].min().date()
        max_date = view["listing_date"].max().date()
        date_range = st.sidebar.date_input("上市日期", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start, end = date_range
            view = view[(view["listing_date"].dt.date >= start) & (view["listing_date"].dt.date <= end)]

    tier_options = ["全部"] + sorted(view["decision_tier"].dropna().unique().tolist()) if "decision_tier" in view.columns else ["全部"]
    tier = st.sidebar.selectbox("决策层", tier_options, index=0)
    if tier != "全部":
        view = view[view["decision_tier"] == tier]

    path_options = ["全部"] + sorted(view["path_label"].dropna().unique().tolist()) if "path_label" in view.columns else ["全部"]
    path = st.sidebar.selectbox("路径类", path_options, index=0)
    if path != "全部":
        view = view[view["path_label"] == path]

    industry_options = ["全部"] + sorted(view["industry"].dropna().unique().tolist()) if "industry" in view.columns else ["全部"]
    industry = st.sidebar.selectbox("行业", industry_options, index=0)
    if industry != "全部":
        view = view[view["industry"] == industry]

    min_score = st.sidebar.slider("最低模型分", 0.0, 1.0, 0.0, 0.05)
    if "model_score_tradeable_20d" in view.columns:
        view = view[view["model_score_tradeable_20d"].fillna(0) >= min_score]

    keyword = st.sidebar.text_input("代码/名称搜索", "").strip()
    if keyword and {"code", "name"}.issubset(view.columns):
        mask = view["code"].astype(str).str.contains(keyword, case=False, na=False) | view["name"].astype(str).str.contains(keyword, case=False, na=False)
        view = view[mask]

    return view


def make_memo(row: pd.Series) -> str:
    code = row.get("code", "")
    name = row.get("name", "")
    score = row.get("model_score_tradeable_20d", pd.NA)
    score_text = "—" if pd.isna(score) else f"{float(score):.2f}"
    path = row.get("path_label", "—")
    path_cn = PATH_CN.get(path, path)

    return f"""# 港股 IPO / 半新股投资备忘录

## 1. 标的概览

- 股票：{code} {name}
- 上市日期：{fmt_date(row.get('listing_date'))}
- 上市天数：{fmt_num(row.get('days_since_listing'), 0)}
- 行业：{row.get('industry', '—')}
- 发行价：{fmt_num(row.get('issue_price'))}
- 发行市值：{fmt_money_hkd(row.get('market_cap_at_ipo_hkd'))}
- 募资金额：{fmt_money_hkd(row.get('fundraising_amount_hkd'))}
- 路径分类：{path_cn} / {path}
- 决策分层：{row.get('decision_tier', '—')}
- 风险等级：{row.get('risk_level', '—')}
- 模型分：{score_text}
- 数据缺口数：{row.get('data_gap_count', '—')}

## 2. 历史路径表现

- 首日开盘收益：{fmt_pct(row.get('d1_open_ret'))}
- 首日收盘收益：{fmt_pct(row.get('d1_close_ret'))}
- 5 日收盘收益：{fmt_pct(row.get('d5_close_ret'))}
- 20 日收盘收益：{fmt_pct(row.get('d20_close_ret'))}
- 60 日收盘收益：{fmt_pct(row.get('d60_close_ret'))}
- 20 日最大上涨：{fmt_pct(row.get('max_20_ret'))}
- 20 日最大回撤：{fmt_pct(row.get('min_20_ret'))}
- 60 日最大上涨：{fmt_pct(row.get('max_60_ret'))}
- 60 日最大回撤：{fmt_pct(row.get('min_60_ret'))}

## 3. 一级参与建议

{row.get('primary_action', '—')}

解释：{primary_rationale(row)}

## 4. 二级买点建议

{row.get('secondary_action', '—')}

执行计划：{secondary_plan(row)}

## 5. 卖点与风控

{row.get('sell_signal', '—')}

仓位提示：{row.get('position_hint', '—')}

## 6. 发行结构待补充

- 公开认购倍数：{fmt_num(row.get('public_subscription_multiple'))}
- 国际配售倍数：{fmt_num(row.get('international_subscription_multiple'))}
- 一手中签率：{fmt_pct(row.get('one_lot_success_rate'))}
- 回拨比例：{fmt_pct(row.get('clawback_ratio'))}
- 基石投资者：{row.get('cornerstone_names', '—')}
- 基石占比：{fmt_pct(row.get('cornerstone_ratio'))}
- 保荐人：{row.get('sponsor_names', '—')}

## 7. 系统原始建议

- 规则建议：{row.get('rule_recommendation', '—')}
- 模型建议：{row.get('model_recommendation', '—')}

> 本备忘录基于现有样本、路径规则和可得字段生成，用于研究辅助，不连接实盘，不构成自动交易指令。
"""


def primary_rationale(row: pd.Series) -> str:
    path = str(row.get("path_label", ""))
    risk = str(row.get("risk_level", ""))
    if "高风险" in risk:
        return "历史路径显示下行压力或破发特征明显，一级阶段不应靠故事硬买。"
    if path == "strong_open":
        return "历史路径偏强，但一级仍要补认购倍数、基石和估值，避免情绪过热。"
    if path == "deep_v_rebound":
        return "这类更适合二级等抛压释放后的右侧确认，一级不应过度抢额度。"
    return "当前主要依据价格路径，发行结构字段缺口较多，因此一级结论只能作为预筛。"


def secondary_plan(row: pd.Series) -> str:
    path = str(row.get("path_label", ""))
    if path == "strong_open":
        return "不追首日涨幅；等待 T+2 至 T+10 回踩后仍守住发行价/首日均价，再用研究仓试错。"
    if path == "deep_v_rebound":
        return "等待跌破发行价或首日低点后的重新收回，且成交额较前一阶段放大。"
    if path == "moderate_tradeable":
        return "优先做缩量回踩后的右侧买点，失败则按发行价/首日低点止损。"
    if path in {"persistent_break", "broken"}:
        return "重新站回发行价以前不主动买；即使反弹也只按短线事件处理。"
    if path == "pop_then_fade":
        return "只把反抽当卖点，不把首日大涨当趋势确认。"
    return "等待价格、成交和发行价关系给出触发。"


# ============================================================
# Rendering
# ============================================================
def render_header_metrics(view: pd.DataFrame) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("样本数", f"{len(view):,}")
    if len(view) and "listing_date" in view.columns and view["listing_date"].notna().any():
        c2.metric("最新上市日", fmt_date(view["listing_date"].max()))
    else:
        c2.metric("最新上市日", "—")
    c3.metric("可交易率", fmt_pct(pct_rate(view.get("label_tradeable_20d", pd.Series(dtype=bool)))))
    c4.metric("破发/弱势率", fmt_pct(pct_rate(view.get("label_broken", pd.Series(dtype=bool)))))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("首日均值", fmt_pct(view["d1_close_ret"].mean() if "d1_close_ret" in view.columns and len(view) else pd.NA))
    c6.metric("20D最大涨幅中位数", fmt_pct(view["max_20_ret"].median() if "max_20_ret" in view.columns and len(view) else pd.NA))
    c7.metric("A/B池数量", int(view["decision_tier"].astype(str).str.startswith(("A", "B")).sum()) if "decision_tier" in view.columns else 0)
    c8.metric("平均数据缺口", fmt_num(view["data_gap_count"].mean() if "data_gap_count" in view.columns and len(view) else pd.NA, 1))


def render_top_alerts(df: pd.DataFrame) -> None:
    missing_issue = float(df["issue_price"].isna().mean()) if "issue_price" in df.columns else 1.0
    unknown_ind = float((df["industry"].astype(str) == "Unknown").mean()) if "industry" in df.columns else 1.0
    if missing_issue > 0.5 or unknown_ind > 0.5:
        st.warning(
            f"当前最大问题不是界面，而是数据层：发行价缺失率 {missing_issue:.0%}，行业 Unknown 占比 {unknown_ind:.0%}。"
            "下一步必须接 iFind/补丁 CSV，把发行结构字段补起来。"
        )


def render_pool_tab(view: pd.DataFrame) -> None:
    st.subheader("优先级列表")
    st.write("A/B 只代表进入重点研究池，不代表直接买入；真实下单前必须补发行结构、估值和行业基本面。")

    sort_candidates = [c for c in ["model_score_tradeable_20d", "listing_date", "max_20_ret", "d1_close_ret", "data_gap_count"] if c in view.columns]
    a, b, c = st.columns([2, 1, 1])
    sort_col = a.selectbox("排序字段", sort_candidates, index=0 if sort_candidates else None)
    ascending = b.toggle("升序", value=False)
    max_rows = c.number_input("显示行数", min_value=20, max_value=1000, value=200, step=20)

    if sort_col:
        table_src = view.sort_values(sort_col, ascending=ascending)
    else:
        table_src = view.copy()
    table_src = table_src.head(int(max_rows))
    st.dataframe(make_cn_table(table_src, CORE_DISPLAY_COLS), use_container_width=True, hide_index=True)

    csv_bytes = view.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button("下载当前筛选结果 CSV", data=csv_bytes, file_name="hk_ipo_filtered.csv", mime="text/csv")

    with st.expander("决策层说明", expanded=True):
        st.markdown(
            """
- **A 高优先**：进入一级/锚定/二级联动研究，准备额度或交易计划。
- **B 交易观察**：更偏二级确认买点，一级小额或选择性参与。
- **C 等触发**：价格、成交、发行价关系没有共振，先不动。
- **D 回避/仅跟踪**：破发或弱势路径明显，除非基本面和发行估值显著反转。
"""
        )


def render_path_tab(view: pd.DataFrame) -> None:
    st.subheader("路径归因")
    if view.empty:
        st.info("当前筛选无数据。")
        return

    if "path_label" in view.columns:
        path_counts = view["path_label"].value_counts().rename_axis("路径").reset_index(name="数量")
        path_counts["路径中文"] = path_counts["路径"].map(lambda x: PATH_CN.get(x, x))
        st.bar_chart(path_counts.set_index("路径中文")["数量"])
        st.dataframe(path_counts, use_container_width=True, hide_index=True)

    st.markdown("### 路径说明")
    desc_df = pd.DataFrame([
        {"路径": k, "中文": PATH_CN.get(k, k), "说明": v} for k, v in PATH_DESC.items()
    ])
    st.dataframe(desc_df, use_container_width=True, hide_index=True)

    if "industry" in view.columns:
        st.markdown("### 行业维度（现在大概率是 Unknown，下一步要补）")
        agg = view.groupby("industry").agg(
            样本数=("code", "count"),
            平均模型分=("model_score_tradeable_20d", "mean"),
            首日均值=("d1_close_ret", "mean"),
            二十日最大涨幅中位数=("max_20_ret", "median"),
            平均数据缺口=("data_gap_count", "mean"),
        ).reset_index().sort_values("样本数", ascending=False)
        agg["平均模型分"] = agg["平均模型分"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
        agg["首日均值"] = agg["首日均值"].map(fmt_pct)
        agg["二十日最大涨幅中位数"] = agg["二十日最大涨幅中位数"].map(fmt_pct)
        agg["平均数据缺口"] = agg["平均数据缺口"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "—")
        st.dataframe(agg, use_container_width=True, hide_index=True)


def render_memo_tab(view: pd.DataFrame) -> None:
    st.subheader("单票 Memo")
    if view.empty or "code" not in view.columns:
        st.warning("当前筛选条件下没有股票。")
        return

    options = (view["code"].astype(str) + "  " + view["name"].astype(str)).tolist()
    selected = st.selectbox("选择股票", options)
    selected_code = selected.split()[0]
    row = view[view["code"].astype(str) == selected_code].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("决策层", row.get("decision_tier", "—"))
    c2.metric("风险", row.get("risk_level", "—"))
    c3.metric("模型分", "—" if pd.isna(row.get("model_score_tradeable_20d")) else f"{float(row.get('model_score_tradeable_20d')):.2f}")
    c4.metric("数据缺口", row.get("data_gap_count", "—"))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("首日", fmt_pct(row.get("d1_close_ret")))
    c6.metric("20D最大涨幅", fmt_pct(row.get("max_20_ret")))
    c7.metric("20D最大回撤", fmt_pct(row.get("min_20_ret")))
    c8.metric("60D最大涨幅", fmt_pct(row.get("max_60_ret")))

    st.markdown("### 一句话结论")
    st.info(f"一级：{row.get('primary_action', '—')}｜二级：{row.get('secondary_action', '—')}｜仓位：{row.get('position_hint', '—')}")
    st.warning(f"风控：{row.get('sell_signal', '—')}")

    memo = make_memo(row)
    st.markdown("### Memo 预览")
    st.markdown(memo)
    st.download_button(
        "下载该股票 Memo.md",
        data=memo.encode("utf-8-sig"),
        file_name=f"{selected_code}_ipo_memo.md",
        mime="text/markdown",
    )

    st.markdown("### 原始字段")
    raw_cols = [c for c in df_cols_order() if c in view.columns]
    st.dataframe(make_cn_table(pd.DataFrame([row]), raw_cols), use_container_width=True, hide_index=True)


def df_cols_order() -> list[str]:
    return [
        "code", "name", "listing_date", "industry", "issue_price", "offer_price_low", "offer_price_high",
        "public_subscription_multiple", "international_subscription_multiple", "one_lot_success_rate",
        "clawback_ratio", "cornerstone_ratio", "sponsor_names", "d1_open_ret", "d1_close_ret",
        "d5_close_ret", "d20_close_ret", "d60_close_ret", "max_20_ret", "min_20_ret", "max_60_ret",
        "min_60_ret", "path_label", "decision_tier", "risk_level", "model_score_tradeable_20d",
    ]


def render_risk_tab(view: pd.DataFrame) -> None:
    st.subheader("风控与卖点")
    st.write("这页先用历史路径和规则做风控框架。后续接最新行情后，可以变成每日卖点监控。")

    risk_order = {"高风险": 0, "中高风险": 1, "中风险/数据缺口": 2, "中低风险": 3}
    temp = view.copy()
    temp["risk_rank"] = temp["risk_level"].map(risk_order).fillna(9)
    temp = temp.sort_values(["risk_rank", "min_20_ret"], ascending=[True, True]) if "min_20_ret" in temp.columns else temp

    cols = ["risk_level", "code", "name", "listing_date", "path_label", "d1_close_ret", "max_20_ret", "min_20_ret", "max_60_ret", "min_60_ret", "sell_signal"]
    st.dataframe(make_cn_table(temp, [c for c in cols if c in temp.columns]), use_container_width=True, hide_index=True)

    st.markdown("### 统一卖出规则库")
    st.markdown(
        """
1. **破发行价止损**：收盘跌破发行价且连续两日不能收回，降低或清仓。
2. **首日 VWAP 失守**：强势股跌破首日成交均价，视为资金承接失败。
3. **放量滞涨止盈**：20日内涨幅较大，但成交放大、价格不创新高，分批止盈。
4. **深V失败**：深V标的重新跌回发行价下方，不能补仓摊低成本。
5. **解禁前降风险**：基石/控股股东锁定期前，若股价已大涨，应提前减仓。
"""
    )


def render_quality_tab(base_df: pd.DataFrame, view: pd.DataFrame) -> None:
    st.subheader("数据质量与字段缺口")
    st.write("截图里最明显的问题是行业大量 Unknown、发行价为空。这个页面专门告诉你下一步要补什么。")

    rows = []
    for col, cn, why in REQUIRED_NEXT_FIELDS:
        if col in base_df.columns:
            miss = base_df[col].isna() | base_df[col].astype(str).str.strip().isin(["", "Unknown", "None", "nan"])
            missing_rate = float(miss.mean())
            status = "可用" if missing_rate < 0.2 else "缺口严重" if missing_rate > 0.8 else "部分可用"
        else:
            missing_rate = 1.0
            status = "缺失"
        rows.append({"字段": col, "中文": cn, "状态": status, "缺失率": missing_rate, "用途": why})
    q = pd.DataFrame(rows)
    q["缺失率"] = q["缺失率"].map(fmt_pct)
    st.dataframe(q, use_container_width=True, hide_index=True)

    st.markdown("### 当前数据列")
    col_quality = pd.DataFrame({
        "字段": base_df.columns,
        "非空数量": [int(base_df[c].notna().sum()) for c in base_df.columns],
        "缺失率": [fmt_pct(base_df[c].isna().mean()) for c in base_df.columns],
        "示例值": [str(base_df[c].dropna().iloc[0]) if base_df[c].notna().any() else "" for c in base_df.columns],
    })
    st.dataframe(col_quality, use_container_width=True, hide_index=True)

    st.markdown("### 补丁 CSV 模板")
    template = make_patch_template()
    st.dataframe(template, use_container_width=True, hide_index=True)
    st.download_button(
        "下载 ipo_master_patch_template.csv",
        data=template.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name="ipo_master_patch_template.csv",
        mime="text/csv",
    )

    st.info("后续 iFind 本地脚本只要导出同样字段的 ipo_master_patch.csv，放进 deploy_data/，本 App 会自动覆盖补充。")


def make_patch_template() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "code": "06610.HK",
            "industry": "示例行业",
            "issue_price": 0.00,
            "offer_price_low": 0.00,
            "offer_price_high": 0.00,
            "final_price_position": 1.0,
            "fundraising_amount_hkd": 0,
            "market_cap_at_ipo_hkd": 0,
            "sponsor_names": "保荐人A;保荐人B",
            "cornerstone_names": "基石A;基石B",
            "cornerstone_amount_hkd": 0,
            "cornerstone_ratio": 0.0,
            "public_subscription_multiple": 0.0,
            "international_subscription_multiple": 0.0,
            "one_lot_success_rate": 0.0,
            "clawback_ratio": 0.0,
        }
    ])


def render_ifind_tab() -> None:
    st.subheader("iFind 接入说明")
    st.warning("Streamlit Cloud 不能直接连接你本地电脑上的 iFind。正确架构是：本地 Windows 跑 iFind 脚本 → 生成 CSV → 上传 GitHub → 云端 App 展示。")
    st.markdown(
        """
### 下一步只打通三个取数字段包

1. **IPO 样本池**：代码、简称、上市日期、发行价、行业、募资金额、发行市值、保荐人。  
2. **发行结果**：公开认购倍数、国际配售倍数、一手中签率、回拨比例、基石名单、基石占比。  
3. **上市后行情**：开高低收、成交量、成交额、换手率，用于更新路径标签和买卖点。  

### 超级命令里优先搜索这些中文字段

- 港股 IPO 列表 2024年以来 上市日期 发行价 募资金额 保荐人
- 06610.HK 上市日期 发行价 公开认购倍数 国际配售倍数 一手中签率 回拨比例
- 06610.HK 日行情 开盘价 最高价 最低价 收盘价 成交量 成交额 换手率

生成 Python 命令后，把代码和 print(data) 前几行发给我，我会把它封装成可双击/可运行的本地更新脚本。
"""
    )


def render_roadmap_tab() -> None:
    st.subheader("下一步路线")
    roadmap = pd.DataFrame([
        {"阶段": "现在", "目标": "界面能汇报", "产出": "投资池、路径归因、Memo、风控、数据质量"},
        {"阶段": "Step 3", "目标": "iFind 本地取数", "产出": "ipo_master_patch.csv + 行情更新 CSV"},
        {"阶段": "Step 4", "目标": "发行结构模型", "产出": "打新/基石/二级三套评分"},
        {"阶段": "Step 5", "目标": "Walk-forward 回测", "产出": "按上市时间滚动验证胜率和收益"},
        {"阶段": "Step 6", "目标": "每日更新", "产出": "今日观察池、买点触发、卖点预警"},
    ])
    st.dataframe(roadmap, use_container_width=True, hide_index=True)

    st.markdown(
        """
### 这套系统的关键判断

- **不要只预测首日涨跌**，要分别预测一级参与、二级深V买点、升后破发卖点。
- **2024年以后样本是合理起点**，但仍然小样本，所以先用规则+可解释模型，不上复杂深度学习。
- **发行结构字段优先级高于花哨图表**，没有认购倍数、基石、回拨、保荐人，模型只能算半成品。
"""
    )


# ============================================================
# Main
# ============================================================
st.set_page_config(page_title="HK IPO 决策驾驶舱", page_icon="📈", layout="wide")

st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

base_df, data_source, patch_source = load_base_data()
if base_df.empty:
    st.error("没有找到数据文件。请把 hk_ipo_scored_public.csv 放在 deploy_data/ 目录下。")
    st.stop()

st.sidebar.success(f"数据源：{data_source}")
if patch_source:
    st.sidebar.info(f"补丁：{patch_source}")

with st.sidebar.expander("临时上传补丁 CSV", expanded=False):
    uploaded_patch = st.file_uploader("上传 ipo_master_patch.csv", type=["csv"])
    st.caption("这个上传只对当前会话生效；要永久生效，请把文件上传到 GitHub 的 deploy_data/ 目录。")

try:
    df = load_uploaded_patch(uploaded_patch, base_df) if uploaded_patch is not None else base_df.copy()
except Exception as exc:
    st.sidebar.error(f"补丁上传失败：{exc}")
    df = base_df.copy()

render_top_alerts(df)
view = filter_data(df)
render_header_metrics(view)
st.divider()

tabs = st.tabs(["① 投资池", "② 路径归因", "③ 单票Memo", "④ 风控卖点", "⑤ 数据质量", "⑥ iFind接入", "⑦ 路线图"])

with tabs[0]:
    render_pool_tab(view)
with tabs[1]:
    render_path_tab(view)
with tabs[2]:
    render_memo_tab(view)
with tabs[3]:
    render_risk_tab(view)
with tabs[4]:
    render_quality_tab(df, view)
with tabs[5]:
    render_ifind_tab()
with tabs[6]:
    render_roadmap_tab()

st.caption("研究辅助工具｜不连接实盘｜不构成自动交易指令")
