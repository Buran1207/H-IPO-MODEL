from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

# ============================================================
# HK IPO / A1 / Newly Listed Stock Decision Cockpit
# Step 3: lifecycle model: A1 -> prospectus -> allotment result -> 0-180D trading
# ============================================================

APP_TITLE = "港股 IPO / A1 / 半新股决策驾驶舱"
APP_SUBTITLE = (
    "Step 3：把模型对象从“已上市新股”扩展为全生命周期："
    "A1递表/临时代码、招股书、配发结果公告、上市后0-180天跟踪。"
)

TODAY = pd.Timestamp.today().normalize()

LISTED_DATA_CANDIDATES = [
    Path("deploy_data/hk_ipo_scored_public.csv"),
    Path("hk_ipo_scored_public.csv"),
    Path("data/processed/hk_ipo_scored.csv"),
    Path("data/processed/hk_ipo_features.csv"),
]
PIPELINE_CANDIDATES = [
    Path("deploy_data/a1_ipo_pipeline.csv"),
    Path("a1_ipo_pipeline.csv"),
    Path("data/raw/a1_ipo_pipeline.csv"),
]
ANNOUNCEMENT_CANDIDATES = [
    Path("deploy_data/ipo_announcement_catalog.csv"),
    Path("ipo_announcement_catalog.csv"),
    Path("data/raw/ipo_announcement_catalog.csv"),
]
OFFER_RESULT_CANDIDATES = [
    Path("deploy_data/ipo_offer_results.csv"),
    Path("ipo_offer_results.csv"),
    Path("deploy_data/ipo_master_patch.csv"),
    Path("ipo_master_patch.csv"),
    Path("data/raw/ipo_offer_results.csv"),
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
    "fundamental_score", "composite_score", "readiness_score",
]
DATE_COLS = [
    "a1_date", "hearing_date", "prospectus_date", "allotment_result_date",
    "expected_listing_date", "listing_date", "announcement_date",
]
BOOL_COLS = [
    "label_strong_open", "label_deep_v", "label_broken", "label_pop_then_fade", "label_tradeable_20d",
]

COLUMN_ALIASES = {
    # identifiers
    "证券代码": "code", "股票代码": "code", "正式代码": "code", "上市代码": "code", "代码": "code",
    "临时代码": "temp_code", "暂定代码": "temp_code", "A1临时代码": "temp_code", "临时代号": "temp_code",
    "证券简称": "name", "股票简称": "name", "简称": "name", "名称": "name", "公司简称": "name",
    "发行人": "issuer_name", "发行人名称": "issuer_name", "公司名称": "issuer_name",
    "阶段": "lifecycle_stage", "状态": "lifecycle_stage", "上市状态": "lifecycle_stage",
    # dates
    "A1日期": "a1_date", "递表日期": "a1_date", "申请日期": "a1_date",
    "聆讯日期": "hearing_date", "通过聆讯日期": "hearing_date",
    "招股书日期": "prospectus_date", "招股日期": "prospectus_date", "招股开始日期": "prospectus_date",
    "配发结果公告日期": "allotment_result_date", "配售结果日期": "allotment_result_date", "分配结果公告日期": "allotment_result_date",
    "预计上市日期": "expected_listing_date", "预期上市日期": "expected_listing_date",
    "上市日期": "listing_date", "首挂日期": "listing_date",
    "公告日期": "announcement_date",
    # classification
    "行业": "industry", "所属行业": "industry", "恒生行业": "industry", "申万行业": "industry",
    # deal terms
    "发行价": "issue_price", "最终发行价": "issue_price", "发售价": "issue_price", "招股价": "issue_price",
    "招股价下限": "offer_price_low", "发售价下限": "offer_price_low", "发行价下限": "offer_price_low",
    "招股价上限": "offer_price_high", "发售价上限": "offer_price_high", "发行价上限": "offer_price_high",
    "定价位置": "final_price_position",
    "募资金额": "fundraising_amount_hkd", "集资额": "fundraising_amount_hkd", "全球发售募资额": "fundraising_amount_hkd",
    "发行市值": "market_cap_at_ipo_hkd", "上市市值": "market_cap_at_ipo_hkd", "发行后市值": "market_cap_at_ipo_hkd",
    "保荐人": "sponsor_names", "联席保荐人": "sponsor_names", "整体协调人": "overall_coordinator_names",
    "基石投资者": "cornerstone_names", "基石名单": "cornerstone_names",
    "基石金额": "cornerstone_amount_hkd", "基石认购金额": "cornerstone_amount_hkd",
    "基石占比": "cornerstone_ratio", "基石比例": "cornerstone_ratio",
    "公开认购倍数": "public_subscription_multiple", "公开发售认购倍数": "public_subscription_multiple",
    "香港公开发售认购倍数": "public_subscription_multiple",
    "国际配售倍数": "international_subscription_multiple", "国际发售认购倍数": "international_subscription_multiple",
    "一手中签率": "one_lot_success_rate", "一手中签": "one_lot_success_rate",
    "回拨比例": "clawback_ratio", "回拨后公开发售比例": "clawback_ratio",
    # announcement fields
    "文件类型": "document_type", "公告类型": "document_type", "文档类型": "document_type",
    "公告标题": "title", "文件标题": "title", "标题": "title",
    "链接": "url", "公告链接": "url", "URL": "url", "网址": "url",
    "来源": "source", "已下载": "downloaded", "本地路径": "local_path",
    "招股书标题": "prospectus_title", "招股书链接": "prospectus_url",
    "配发结果公告标题": "allotment_result_title", "配发结果公告链接": "allotment_result_url",
    # misc
    "核心风险": "key_risks", "备注": "notes",
}

PATH_CN = {
    "strong_open": "上市即强",
    "deep_v_rebound": "深V反弹",
    "moderate_tradeable": "可交易",
    "pop_then_fade": "升后回落",
    "persistent_break": "持续破发",
    "broken": "持续破发",
    "watch": "观察",
    "pre_listing": "未上市",
}

DISPLAY_LABELS = {
    "decision_tier": "决策层",
    "security_key": "主键",
    "temp_code": "临时代码",
    "code": "正式代码",
    "name": "简称",
    "issuer_name": "发行人",
    "lifecycle_stage": "阶段",
    "a1_date": "A1/递表日",
    "prospectus_date": "招股书日",
    "allotment_result_date": "配发结果日",
    "expected_listing_date": "预计上市日",
    "listing_date": "上市日",
    "days_since_listing": "上市天数",
    "industry": "行业",
    "issue_price": "发行价",
    "offer_price_low": "招股价下限",
    "offer_price_high": "招股价上限",
    "public_subscription_multiple": "公开认购倍数",
    "international_subscription_multiple": "国际配售倍数",
    "one_lot_success_rate": "一手中签率",
    "clawback_ratio": "回拨比例",
    "cornerstone_ratio": "基石占比",
    "sponsor_names": "保荐人",
    "d1_close_ret": "首日收盘",
    "max_20_ret": "20D最大涨幅",
    "min_20_ret": "20D最大回撤",
    "max_60_ret": "60D最大涨幅",
    "path_label": "路径",
    "readiness_score": "资料完整度",
    "model_score_tradeable_20d": "交易分",
    "risk_level": "风险",
    "primary_action": "一级/基石建议",
    "secondary_action": "二级建议",
    "position_hint": "仓位提示",
    "next_data_action": "下一步数据动作",
}

CRITICAL_FIELDS_BY_STAGE = {
    "A1/递表": ["name", "issuer_name", "a1_date", "prospectus_url", "industry", "sponsor_names"],
    "招股中/待上市": ["prospectus_date", "offer_price_low", "offer_price_high", "sponsor_names", "cornerstone_names"],
    "配发结果后": ["issue_price", "public_subscription_multiple", "international_subscription_multiple", "one_lot_success_rate", "clawback_ratio", "allotment_result_url"],
    "已上市0-180D": ["listing_date", "issue_price", "d1_close_ret", "max_20_ret", "min_20_ret", "max_60_ret"],
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
    path = find_first_existing(paths)
    if path is None:
        return pd.DataFrame(), "未找到"
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
        return df, str(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(), str(path)


def rename_known_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df.rename(columns={c: COLUMN_ALIASES.get(c, c) for c in df.columns})


def clean_code(value: Any, suffix: bool = True) -> str:
    if pd.isna(value):
        return ""
    s = str(value).strip().upper()
    if s in {"", "NAN", "NONE", "NULL"}:
        return ""
    if s.endswith(".HK"):
        left = s[:-3]
        if left.isdigit():
            return f"{int(left):04d}.HK"
        return s
    if s.isdigit():
        return f"{int(s):04d}.HK" if suffix else f"{int(s):04d}"
    return s


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    s = str(value).strip()
    if s.lower() in {"nan", "none", "null"}:
        return ""
    return s


def to_number(series: pd.Series) -> pd.Series:
    if series.empty:
        return series
    s = series.astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False).str.strip()
    out = pd.to_numeric(s, errors="coerce")
    # If values look like percent integers, keep as human decimals for known pct columns later.
    return out


def normalize_percent_column(df: pd.DataFrame, col: str) -> None:
    if col not in df.columns:
        return
    raw = df[col].copy()
    has_percent_symbol = raw.astype(str).str.contains("%", regex=False, na=False)
    s = raw.astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False).str.strip()
    v = pd.to_numeric(s, errors="coerce")
    # Convert only obvious percentage input, e.g. 30% or one_lot_success_rate as 20.
    if has_percent_symbol.any():
        v = v / 100.0
    elif col in {"one_lot_success_rate", "clawback_ratio", "cornerstone_ratio", "final_price_position"} and v.dropna().gt(1.5).any():
        v = v / 100.0
    df[col] = v


def normalize_common(df: pd.DataFrame) -> pd.DataFrame:
    df = rename_known_columns(df.copy())
    for col in ["code", "temp_code"]:
        if col in df.columns:
            df[col] = df[col].map(clean_code)
    for col in DATE_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in PCT_COLS:
        normalize_percent_column(df, col)
    for col in NUM_COLS:
        if col in df.columns and col not in PCT_COLS:
            df[col] = to_number(df[col])
    for col in BOOL_COLS:
        if col in df.columns:
            df[col] = df[col].map(lambda x: str(x).lower() in {"true", "1", "yes", "y", "是"} if not isinstance(x, bool) else x).fillna(False)
    for col in [
        "name", "issuer_name", "industry", "lifecycle_stage", "path_label", "rule_recommendation",
        "model_recommendation", "sponsor_names", "overall_coordinator_names", "cornerstone_names",
        "prospectus_title", "prospectus_url", "allotment_result_title", "allotment_result_url",
        "key_risks", "notes", "security_key",
    ]:
        if col in df.columns:
            df[col] = df[col].map(clean_text)
    return df


def ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col not in out.columns:
            out[col] = pd.NA
    return out


def value_present(x: Any) -> bool:
    if pd.isna(x):
        return False
    if isinstance(x, str):
        return x.strip().lower() not in {"", "nan", "none", "null", "unknown"}
    return True


def first_present(row: pd.Series, columns: list[str], default: str = "") -> str:
    for col in columns:
        if col in row.index and value_present(row.get(col)):
            return clean_text(row.get(col))
    return default


def fmt_pct(value: Any, digits: int = 1) -> str:
    if pd.isna(value):
        return ""
    try:
        return f"{float(value):.{digits}%}"
    except Exception:
        return ""


def fmt_num(value: Any, digits: int = 2) -> str:
    if pd.isna(value):
        return ""
    try:
        return f"{float(value):,.{digits}f}"
    except Exception:
        return ""


def fmt_money_hkd(value: Any) -> str:
    if pd.isna(value):
        return ""
    try:
        v = float(value)
    except Exception:
        return ""
    if abs(v) >= 1e9:
        return f"HK${v/1e9:,.2f}bn"
    if abs(v) >= 1e6:
        return f"HK${v/1e6:,.1f}mn"
    return f"HK${v:,.0f}"


def format_for_table(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if col in DATE_COLS or col == "listing_date":
            out[col] = pd.to_datetime(out[col], errors="coerce").dt.strftime("%Y-%m-%d").replace("NaT", "")
        elif col in PCT_COLS or col in ["d1_close_ret", "max_20_ret", "min_20_ret", "max_60_ret", "model_score_tradeable_20d", "readiness_score"]:
            if col in ["model_score_tradeable_20d", "readiness_score"]:
                out[col] = out[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.2f}")
            else:
                out[col] = out[col].map(fmt_pct)
        elif col in ["fundraising_amount_hkd", "market_cap_at_ipo_hkd", "cornerstone_amount_hkd"]:
            out[col] = out[col].map(fmt_money_hkd)
        elif col in ["public_subscription_multiple", "international_subscription_multiple"]:
            out[col] = out[col].map(lambda x: "" if pd.isna(x) else f"{float(x):,.1f}x")
        elif col in ["issue_price", "offer_price_low", "offer_price_high"]:
            out[col] = out[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.2f}")
    return out.rename(columns={c: DISPLAY_LABELS.get(c, c) for c in out.columns})

# ============================================================
# Listed / pipeline / announcement loaders
# ============================================================

def infer_path_label(row: pd.Series) -> str:
    d1 = row.get("d1_close_ret")
    max20 = row.get("max_20_ret")
    min20 = row.get("min_20_ret")
    max60 = row.get("max_60_ret")
    if pd.isna(d1) and pd.isna(max20) and pd.isna(min20):
        return "pre_listing"
    d1 = 0 if pd.isna(d1) else float(d1)
    max20 = 0 if pd.isna(max20) else float(max20)
    min20 = 0 if pd.isna(min20) else float(min20)
    max60 = 0 if pd.isna(max60) else float(max60)
    if d1 >= 0.25 and max20 >= 0.35:
        return "strong_open"
    if min20 <= -0.10 and max60 >= 0.25:
        return "deep_v_rebound"
    if d1 >= 0.20 and min20 <= -0.15:
        return "pop_then_fade"
    if min20 <= -0.20 and max20 < 0.10:
        return "persistent_break"
    if max20 >= 0.15:
        return "moderate_tradeable"
    return "watch"


def rule_score(row: pd.Series) -> float:
    score = 0.40
    path = clean_text(row.get("path_label")) or infer_path_label(row)
    if path == "strong_open":
        score += 0.28
    elif path == "deep_v_rebound":
        score += 0.18
    elif path == "moderate_tradeable":
        score += 0.15
    elif path in {"pop_then_fade", "persistent_break", "broken"}:
        score -= 0.18

    d1 = row.get("d1_close_ret")
    max20 = row.get("max_20_ret")
    min20 = row.get("min_20_ret")
    max60 = row.get("max_60_ret")
    if pd.notna(d1):
        score += max(min(float(d1), 0.35), -0.35) * 0.25
    if pd.notna(max20):
        score += max(min(float(max20), 0.60), -0.20) * 0.25
    if pd.notna(min20):
        score += max(float(min20), -0.50) * 0.20
    if pd.notna(max60):
        score += max(min(float(max60), 0.80), -0.20) * 0.10
    return round(float(max(0, min(1, score))), 3)


def normalize_listed_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = normalize_common(df)
    df = ensure_columns(df, [
        "code", "temp_code", "name", "issuer_name", "listing_date", "industry", "issue_price",
        "path_label", "model_score_tradeable_20d",
    ])
    df["security_key"] = df.apply(lambda r: clean_text(r.get("code")) or clean_text(r.get("temp_code")) or clean_text(r.get("name")), axis=1)
    df["issuer_name"] = df.apply(lambda r: clean_text(r.get("issuer_name")) or clean_text(r.get("name")), axis=1)
    df["source_layer"] = "listed_sample"
    if "path_label" not in df.columns:
        df["path_label"] = df.apply(infer_path_label, axis=1)
    else:
        blank = df["path_label"].map(clean_text).eq("")
        df.loc[blank, "path_label"] = df[blank].apply(infer_path_label, axis=1)
    if "model_score_tradeable_20d" not in df.columns:
        df["model_score_tradeable_20d"] = df.apply(rule_score, axis=1)
    else:
        df["model_score_tradeable_20d"] = pd.to_numeric(df["model_score_tradeable_20d"], errors="coerce")
        missing = df["model_score_tradeable_20d"].isna()
        df.loc[missing, "model_score_tradeable_20d"] = df[missing].apply(rule_score, axis=1)
    return df


def normalize_pipeline_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = normalize_common(df)
    df = ensure_columns(df, [
        "security_key", "temp_code", "code", "name", "issuer_name", "lifecycle_stage", "a1_date", "hearing_date",
        "prospectus_date", "allotment_result_date", "expected_listing_date", "listing_date", "industry",
        "offer_price_low", "offer_price_high", "issue_price", "fundraising_amount_hkd", "market_cap_at_ipo_hkd",
        "sponsor_names", "overall_coordinator_names", "cornerstone_names", "cornerstone_amount_hkd", "cornerstone_ratio",
        "public_subscription_multiple", "international_subscription_multiple", "one_lot_success_rate", "clawback_ratio",
        "prospectus_title", "prospectus_url", "allotment_result_title", "allotment_result_url", "key_risks", "notes",
    ])
    df["security_key"] = df.apply(
        lambda r: clean_text(r.get("security_key")) or clean_text(r.get("code")) or clean_text(r.get("temp_code")) or clean_text(r.get("issuer_name")) or clean_text(r.get("name")), axis=1
    )
    df["name"] = df.apply(lambda r: clean_text(r.get("name")) or clean_text(r.get("issuer_name")), axis=1)
    df["issuer_name"] = df.apply(lambda r: clean_text(r.get("issuer_name")) or clean_text(r.get("name")), axis=1)
    df["source_layer"] = "a1_pipeline"
    return df


def normalize_announcement_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = normalize_common(df)
    df = ensure_columns(df, ["security_key", "temp_code", "code", "name", "announcement_date", "document_type", "title", "url", "source", "downloaded", "local_path", "notes"])
    df["security_key"] = df.apply(lambda r: clean_text(r.get("security_key")) or clean_text(r.get("code")) or clean_text(r.get("temp_code")) or clean_text(r.get("name")), axis=1)
    return df


def normalize_offer_results(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = normalize_common(df)
    df = ensure_columns(df, ["security_key", "temp_code", "code", "name"])
    df["security_key"] = df.apply(lambda r: clean_text(r.get("security_key")) or clean_text(r.get("code")) or clean_text(r.get("temp_code")) or clean_text(r.get("name")), axis=1)
    return df


def overlay_by_keys(base: pd.DataFrame, patch: pd.DataFrame) -> pd.DataFrame:
    if base.empty:
        return base
    if patch.empty:
        return base
    out = base.copy()
    patch = patch.copy()
    keys = ["security_key", "code", "temp_code", "name", "issuer_name"]
    for key in keys:
        if key not in out.columns or key not in patch.columns:
            continue
        p = patch[patch[key].map(value_present)].drop_duplicates(key, keep="last").set_index(key)
        if p.empty:
            continue
        out_idx = out[out[key].map(value_present)].set_index(key, drop=False)
        common = out_idx.index.intersection(p.index)
        if len(common) == 0:
            continue
        # update by positional mapping back to original indexes
        for k in common:
            target_indexes = out.index[out[key] == k].tolist()
            if not target_indexes:
                continue
            prow = p.loc[k]
            if isinstance(prow, pd.DataFrame):
                prow = prow.iloc[-1]
            for col, val in prow.items():
                if col in {"source_layer"}:
                    continue
                if not value_present(val):
                    continue
                if col not in out.columns:
                    out[col] = pd.NA
                for i in target_indexes:
                    if not value_present(out.at[i, col]):
                        out.at[i, col] = val
                    elif col in [
                        "prospectus_date", "allotment_result_date", "expected_listing_date", "listing_date", "issue_price",
                        "public_subscription_multiple", "international_subscription_multiple", "one_lot_success_rate", "clawback_ratio",
                        "cornerstone_names", "cornerstone_ratio", "cornerstone_amount_hkd", "sponsor_names",
                        "offer_price_low", "offer_price_high", "fundraising_amount_hkd", "market_cap_at_ipo_hkd",
                    ]:
                        out.at[i, col] = val
    return out


def combine_universe(listed: pd.DataFrame, pipeline: pd.DataFrame, offer_results: pd.DataFrame) -> pd.DataFrame:
    frames = []
    if not pipeline.empty:
        frames.append(pipeline)
    if not listed.empty:
        frames.append(listed)
    if not frames:
        return pd.DataFrame()

    all_cols = sorted(set().union(*(set(f.columns) for f in frames)))
    universe = pd.concat([ensure_columns(f, all_cols)[all_cols] for f in frames], ignore_index=True)
    if not offer_results.empty:
        universe = overlay_by_keys(universe, offer_results)

    # If a pipeline row and a listed row describe the same code, keep the richer listed row but preserve A1 fields.
    universe["_listed_rank"] = universe["source_layer"].map({"listed_sample": 2, "a1_pipeline": 1}).fillna(0)
    universe["_completeness"] = universe.apply(lambda r: sum(value_present(r.get(c)) for c in universe.columns), axis=1)
    # first overlay all duplicate information by security codes, then dedupe.
    universe = overlay_by_keys(universe, universe.sort_values(["_listed_rank", "_completeness"]))
    dedupe_key = universe.apply(lambda r: clean_text(r.get("code")) or clean_text(r.get("temp_code")) or clean_text(r.get("security_key")) or clean_text(r.get("name")), axis=1)
    universe["_dedupe_key"] = dedupe_key
    universe = universe.sort_values(["_dedupe_key", "_listed_rank", "_completeness"], ascending=[True, False, False])
    universe = universe.drop_duplicates("_dedupe_key", keep="first").drop(columns=["_listed_rank", "_completeness", "_dedupe_key"], errors="ignore")
    universe = postprocess_universe(universe)
    return universe

# ============================================================
# Decision rules
# ============================================================

def infer_lifecycle_stage(row: pd.Series) -> str:
    manual = clean_text(row.get("lifecycle_stage"))
    if manual:
        return manual
    listing_date = row.get("listing_date")
    expected_listing_date = row.get("expected_listing_date")
    if pd.notna(listing_date):
        days = (TODAY - pd.to_datetime(listing_date)).days
        if days < 0:
            return "已定价待上市"
        if days <= 30:
            return "已上市0-30D"
        if days <= 90:
            return "已上市31-90D"
        if days <= 180:
            return "已上市91-180D"
        return "180D以后"
    if pd.notna(expected_listing_date):
        if pd.to_datetime(expected_listing_date) >= TODAY:
            return "已定价待上市"
        return "待确认上市状态"
    if value_present(row.get("allotment_result_date")) or value_present(row.get("issue_price")):
        return "配发结果后"
    if value_present(row.get("prospectus_date")) or value_present(row.get("offer_price_low")) or value_present(row.get("offer_price_high")):
        return "招股中/待上市"
    if value_present(row.get("hearing_date")):
        return "聆讯后/待招股"
    if value_present(row.get("a1_date")) or value_present(row.get("temp_code")) or value_present(row.get("prospectus_url")):
        return "A1/递表"
    return "未分层"


def stage_bucket(stage: str) -> str:
    s = clean_text(stage)
    if "A1" in s or "递表" in s:
        return "A1/递表"
    if "聆讯" in s or "招股" in s or "待上市" in s or "定价" in s:
        return "招股中/待上市"
    if "配发" in s or "结果" in s:
        return "配发结果后"
    if "上市" in s or "180" in s:
        return "已上市0-180D"
    return "A1/递表"


def readiness_score(row: pd.Series) -> float:
    stage = stage_bucket(clean_text(row.get("lifecycle_stage")))
    fields = CRITICAL_FIELDS_BY_STAGE.get(stage, CRITICAL_FIELDS_BY_STAGE["A1/递表"])
    if not fields:
        return 0.0
    got = sum(value_present(row.get(c)) for c in fields)
    score = got / len(fields)
    # add small credit for rich fields.
    bonus_fields = ["industry", "sponsor_names", "cornerstone_names", "key_risks", "notes"]
    bonus = sum(value_present(row.get(c)) for c in bonus_fields) * 0.03
    return round(float(min(1, score + bonus)), 3)


def classify_risk(row: pd.Series) -> str:
    stage = clean_text(row.get("lifecycle_stage"))
    path = clean_text(row.get("path_label"))
    min20 = row.get("min_20_ret")
    d1 = row.get("d1_close_ret")
    pub = row.get("public_subscription_multiple")
    intl = row.get("international_subscription_multiple")
    corner = row.get("cornerstone_ratio")
    score = row.get("model_score_tradeable_20d")

    risk_points = 0
    if "A1" in stage or "递表" in stage:
        risk_points += 2  # deal terms incomplete by definition
    if path in {"persistent_break", "broken", "pop_then_fade"}:
        risk_points += 2
    if pd.notna(min20) and float(min20) <= -0.20:
        risk_points += 2
    if pd.notna(d1) and float(d1) <= -0.10:
        risk_points += 1
    if pd.notna(pub) and float(pub) > 100 and (pd.isna(intl) or float(intl) < 5):
        risk_points += 1
    if pd.notna(corner) and float(corner) > 0.55:
        risk_points += 1
    if pd.notna(score) and float(score) < 0.35:
        risk_points += 1

    if risk_points >= 4:
        return "高"
    if risk_points >= 2:
        return "中"
    return "低"


def primary_action(row: pd.Series) -> str:
    stage = clean_text(row.get("lifecycle_stage"))
    risk = clean_text(row.get("risk_level"))
    readiness = row.get("readiness_score")
    score = row.get("model_score_tradeable_20d")
    pub = row.get("public_subscription_multiple")
    intl = row.get("international_subscription_multiple")
    issue = row.get("issue_price")

    if "A1" in stage or "递表" in stage:
        return "建研究档案；只做行业/股东/保荐人预筛，等待招股书与发行结构"
    if "聆讯" in stage:
        return "进入预审名单；准备估值锚与基石/锚定谈判清单"
    if "招股" in stage or "待上市" in stage or "定价" in stage:
        if pd.isna(issue):
            return "等待最终定价与配发结果；暂不下一级结论"
        if pd.notna(pub) and float(pub) > 50 and pd.notna(intl) and float(intl) >= 3:
            return "可参与打新/锚定评审；重点核查估值和回拨后流通盘"
        return "小额或观察；发行结构热度不足时不为额度付高价"
    if "配发" in stage:
        if risk == "高":
            return "配发结果风险偏高；不建议基石/重仓打新"
        return "配发结果可进入最终会签；同步制定首日卖出/二级补仓计划"
    if "上市" in stage or "180" in stage:
        if pd.notna(score) and float(score) >= 0.72:
            return "历史路径优先级高；复盘发行结构用于以后同类票"
        return "一级阶段已结束；转入二级/复盘逻辑"
    if pd.notna(readiness) and float(readiness) < 0.35:
        return "资料不足；先补公告与发行结构"
    return "观察"


def secondary_action(row: pd.Series) -> str:
    stage = clean_text(row.get("lifecycle_stage"))
    if not ("上市" in stage or "180" in stage):
        return "未上市：先不做二级买点，只准备上市后0-180D跟踪计划"
    path = clean_text(row.get("path_label")) or infer_path_label(row)
    score = row.get("model_score_tradeable_20d")
    min20 = row.get("min_20_ret")
    d1 = row.get("d1_close_ret")
    if path == "strong_open":
        return "不追首日；等回踩发行价/首日VWAP不破后再分批"
    if path == "deep_v_rebound":
        return "重点跟踪深V二买：重新站回发行价且成交改善"
    if path in {"persistent_break", "broken"}:
        return "回避；除非重新站回发行价并连续确认"
    if path == "pop_then_fade":
        return "以卖点为主；反弹缩量不过前高不加仓"
    if pd.notna(score) and float(score) >= 0.70:
        return "可列入半新股交易池；按触发条件小仓试错"
    if pd.notna(min20) and float(min20) <= -0.15 and pd.notna(d1) and float(d1) > 0:
        return "高开低走风险；等待二次承接确认"
    return "观察；未形成明确二级触发"


def position_hint(row: pd.Series) -> str:
    stage = clean_text(row.get("lifecycle_stage"))
    risk = clean_text(row.get("risk_level"))
    score = row.get("model_score_tradeable_20d")
    readiness = row.get("readiness_score")
    if not ("上市" in stage or "180" in stage):
        if pd.notna(readiness) and float(readiness) >= 0.70:
            return "研究仓/额度预案：可进入会前名单"
        return "0仓；只建档跟踪"
    if risk == "高":
        return "0-0.5仓，只允许事件型试错"
    if pd.notna(score) and float(score) >= 0.80:
        return "1.5-2.0仓，上限需看流动性"
    if pd.notna(score) and float(score) >= 0.65:
        return "0.5-1.0仓，分批确认"
    return "0-0.5仓，等待触发"


def decision_tier(row: pd.Series) -> str:
    stage = clean_text(row.get("lifecycle_stage"))
    risk = clean_text(row.get("risk_level"))
    readiness = row.get("readiness_score")
    score = row.get("model_score_tradeable_20d")
    if "A1" in stage or "递表" in stage or "聆讯" in stage:
        if pd.notna(readiness) and float(readiness) >= 0.65:
            return "B 预研重点"
        return "C 建档观察"
    if "招股" in stage or "待上市" in stage or "配发" in stage or "定价" in stage:
        if risk == "高":
            return "D 回避/仅跟踪"
        if pd.notna(readiness) and float(readiness) >= 0.70:
            return "A 一级重点"
        return "B 等配发结果"
    if pd.notna(score) and float(score) >= 0.75 and risk != "高":
        return "A 高优先"
    if pd.notna(score) and float(score) >= 0.55:
        return "B 交易观察"
    if risk == "高":
        return "D 回避/仅跟踪"
    return "C 等触发"


def sell_signal(row: pd.Series) -> str:
    stage = clean_text(row.get("lifecycle_stage"))
    if not ("上市" in stage or "180" in stage):
        return "未上市：无卖点；只做上市后监控规则预设"
    path = clean_text(row.get("path_label"))
    min20 = row.get("min_20_ret")
    max20 = row.get("max_20_ret")
    d1 = row.get("d1_close_ret")
    signals = []
    if path in {"pop_then_fade", "persistent_break", "broken"}:
        signals.append("路径本身偏卖出/回避")
    if pd.notna(min20) and float(min20) <= -0.15:
        signals.append("20D内回撤超过15%，发行价支撑需重新验证")
    if pd.notna(d1) and float(d1) >= 0.30 and pd.notna(max20) and float(max20) < float(d1) + 0.05:
        signals.append("首日过热但20D未继续打开空间")
    if not signals:
        return "暂无硬卖点；按发行价、首日VWAP、5/20日低点跟踪"
    return "；".join(signals)


def quote_sampling_plan(row: pd.Series) -> str:
    stage = clean_text(row.get("lifecycle_stage"))
    if not ("上市" in stage or "180" in stage):
        return "上市前不抓行情；上市日开始生成0-180D计划"
    return "D0-D30每日；D31-D90每3个交易日；D91-D180每周；触发破发/放量/回发行价时临时加密"


def next_data_action(row: pd.Series) -> str:
    stage = stage_bucket(clean_text(row.get("lifecycle_stage")))
    fields = CRITICAL_FIELDS_BY_STAGE.get(stage, [])
    missing = [DISPLAY_LABELS.get(c, c) for c in fields if not value_present(row.get(c))]
    if not missing:
        return "关键字段已够用，下一步做评分/复核"
    return "补：" + "、".join(missing[:4])


def postprocess_universe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = normalize_common(df)
    df = ensure_columns(df, [
        "security_key", "temp_code", "code", "name", "issuer_name", "lifecycle_stage", "a1_date",
        "hearing_date", "prospectus_date", "allotment_result_date", "expected_listing_date", "listing_date",
        "industry", "issue_price", "path_label", "model_score_tradeable_20d",
        "sponsor_names", "cornerstone_names", "prospectus_url", "allotment_result_url",
    ])
    df["security_key"] = df.apply(lambda r: clean_text(r.get("security_key")) or clean_text(r.get("code")) or clean_text(r.get("temp_code")) or clean_text(r.get("issuer_name")) or clean_text(r.get("name")), axis=1)
    df["name"] = df.apply(lambda r: clean_text(r.get("name")) or clean_text(r.get("issuer_name")) or clean_text(r.get("security_key")), axis=1)
    df["issuer_name"] = df.apply(lambda r: clean_text(r.get("issuer_name")) or clean_text(r.get("name")), axis=1)
    df["industry"] = df["industry"].map(clean_text).replace({"": "Unknown"})
    df["lifecycle_stage"] = df.apply(infer_lifecycle_stage, axis=1)
    df["days_since_listing"] = (TODAY - pd.to_datetime(df["listing_date"], errors="coerce")).dt.days
    df.loc[pd.to_datetime(df["listing_date"], errors="coerce").isna(), "days_since_listing"] = pd.NA
    blank_path = df["path_label"].map(clean_text).eq("")
    df.loc[blank_path, "path_label"] = df[blank_path].apply(infer_path_label, axis=1)
    # No trading score for not listed; keep separate readiness_score.
    if "model_score_tradeable_20d" not in df.columns:
        df["model_score_tradeable_20d"] = pd.NA
    else:
        df["model_score_tradeable_20d"] = pd.to_numeric(df["model_score_tradeable_20d"], errors="coerce")
    listed_mask = df["lifecycle_stage"].str.contains("上市|180", na=False)
    missing_score = listed_mask & df["model_score_tradeable_20d"].isna()
    df.loc[missing_score, "model_score_tradeable_20d"] = df[missing_score].apply(rule_score, axis=1)
    df.loc[~listed_mask, "model_score_tradeable_20d"] = pd.NA
    df["readiness_score"] = df.apply(readiness_score, axis=1)
    df["risk_level"] = df.apply(classify_risk, axis=1)
    df["primary_action"] = df.apply(primary_action, axis=1)
    df["secondary_action"] = df.apply(secondary_action, axis=1)
    df["position_hint"] = df.apply(position_hint, axis=1)
    df["decision_tier"] = df.apply(decision_tier, axis=1)
    df["sell_signal"] = df.apply(sell_signal, axis=1)
    df["quote_sampling_plan"] = df.apply(quote_sampling_plan, axis=1)
    df["next_data_action"] = df.apply(next_data_action, axis=1)
    return df

@st.cache_data(show_spinner=False)
def load_all_data() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    listed_raw, listed_path = read_csv_if_exists(LISTED_DATA_CANDIDATES)
    pipeline_raw, pipeline_path = read_csv_if_exists(PIPELINE_CANDIDATES)
    ann_raw, ann_path = read_csv_if_exists(ANNOUNCEMENT_CANDIDATES)
    offer_raw, offer_path = read_csv_if_exists(OFFER_RESULT_CANDIDATES)

    listed = normalize_listed_data(listed_raw)
    pipeline = normalize_pipeline_data(pipeline_raw)
    announcements = normalize_announcement_data(ann_raw)
    offer_results = normalize_offer_results(offer_raw)
    universe = combine_universe(listed, pipeline, offer_results)
    paths = {
        "已上市样本": listed_path,
        "A1/招股管线": pipeline_path,
        "公告目录": ann_path,
        "发行/配发结果补丁": offer_path,
    }
    return universe, announcements, paths

# ============================================================
# Memo and diagnostics
# ============================================================

def build_memo(row: pd.Series, anns: pd.DataFrame) -> str:
    name = first_present(row, ["name", "issuer_name", "security_key"], "未知")
    code = clean_text(row.get("code")) or "未上市"
    temp_code = clean_text(row.get("temp_code")) or ""
    stage = clean_text(row.get("lifecycle_stage"))
    doc_rows = pd.DataFrame()
    if not anns.empty:
        keys = {clean_text(row.get("security_key")), clean_text(row.get("code")), clean_text(row.get("temp_code")), clean_text(row.get("name"))}
        keys = {k for k in keys if k}
        if keys:
            doc_rows = anns[anns[["security_key", "code", "temp_code", "name"]].apply(lambda r: any(clean_text(x) in keys for x in r), axis=1)]

    memo = []
    memo.append(f"# {name} IPO/半新股决策备忘录")
    memo.append("")
    memo.append(f"- 正式代码：{code}")
    if temp_code:
        memo.append(f"- 临时代码：{temp_code}")
    memo.append(f"- 当前阶段：{stage}")
    memo.append(f"- 行业：{clean_text(row.get('industry')) or 'Unknown'}")
    memo.append(f"- 决策层：{clean_text(row.get('decision_tier'))}")
    memo.append(f"- 风险等级：{clean_text(row.get('risk_level'))}")
    memo.append("")
    memo.append("## 1. 当前建议")
    memo.append(f"- 一级/基石：{clean_text(row.get('primary_action'))}")
    memo.append(f"- 二级：{clean_text(row.get('secondary_action'))}")
    memo.append(f"- 仓位：{clean_text(row.get('position_hint'))}")
    memo.append(f"- 下一步数据动作：{clean_text(row.get('next_data_action'))}")
    memo.append("")
    memo.append("## 2. 发行结构")
    memo.append(f"- 招股区间：{fmt_num(row.get('offer_price_low'))} - {fmt_num(row.get('offer_price_high'))}")
    memo.append(f"- 最终发行价：{fmt_num(row.get('issue_price'))}")
    memo.append(f"- 募资金额：{fmt_money_hkd(row.get('fundraising_amount_hkd'))}")
    memo.append(f"- 发行市值：{fmt_money_hkd(row.get('market_cap_at_ipo_hkd'))}")
    memo.append(f"- 公开认购倍数：{fmt_num(row.get('public_subscription_multiple'), 1)}x")
    memo.append(f"- 国际配售倍数：{fmt_num(row.get('international_subscription_multiple'), 1)}x")
    memo.append(f"- 一手中签率：{fmt_pct(row.get('one_lot_success_rate'))}")
    memo.append(f"- 回拨比例：{fmt_pct(row.get('clawback_ratio'))}")
    memo.append(f"- 基石占比：{fmt_pct(row.get('cornerstone_ratio'))}")
    memo.append(f"- 保荐人：{clean_text(row.get('sponsor_names'))}")
    memo.append(f"- 基石：{clean_text(row.get('cornerstone_names'))}")
    memo.append("")
    memo.append("## 3. 上市后路径")
    memo.append(f"- 路径：{PATH_CN.get(clean_text(row.get('path_label')), clean_text(row.get('path_label')))}")
    memo.append(f"- 首日收盘收益：{fmt_pct(row.get('d1_close_ret'))}")
    memo.append(f"- 20D最大涨幅：{fmt_pct(row.get('max_20_ret'))}")
    memo.append(f"- 20D最大回撤：{fmt_pct(row.get('min_20_ret'))}")
    memo.append(f"- 60D最大涨幅：{fmt_pct(row.get('max_60_ret'))}")
    memo.append(f"- 卖点/回避信号：{clean_text(row.get('sell_signal'))}")
    memo.append("")
    memo.append("## 4. 公告文件")
    prospectus = clean_text(row.get("prospectus_url"))
    allotment = clean_text(row.get("allotment_result_url"))
    if prospectus:
        memo.append(f"- 招股书：{prospectus}")
    if allotment:
        memo.append(f"- 配发结果公告：{allotment}")
    if not doc_rows.empty:
        for _, d in doc_rows.head(10).iterrows():
            memo.append(f"- {pd.to_datetime(d.get('announcement_date'), errors='coerce').strftime('%Y-%m-%d') if pd.notna(pd.to_datetime(d.get('announcement_date'), errors='coerce')) else ''} {clean_text(d.get('document_type'))}：{clean_text(d.get('title'))} {clean_text(d.get('url'))}")
    if not prospectus and not allotment and doc_rows.empty:
        memo.append("- 暂无公告链接；下一步从 iFind 公告/招股书字段补齐。")
    memo.append("")
    memo.append("## 5. 0-180D行情抓取计划")
    memo.append(f"- {clean_text(row.get('quote_sampling_plan'))}")
    memo.append("")
    memo.append("## 6. 待人工复核")
    memo.append(f"- 核心风险：{clean_text(row.get('key_risks'))}")
    memo.append(f"- 备注：{clean_text(row.get('notes'))}")
    return "\n".join(memo)


def data_quality_table(universe: pd.DataFrame) -> pd.DataFrame:
    fields = [
        ("temp_code", "临时代码", "A1/未上市公司识别"),
        ("a1_date", "A1/递表日", "确认递表节奏"),
        ("prospectus_url", "招股书链接", "招股书文本/风险抽取"),
        ("allotment_result_url", "配发结果公告链接", "发行结果最后决策"),
        ("industry", "行业", "行业胜率与估值锚"),
        ("issue_price", "发行价", "破发/发行价支撑"),
        ("public_subscription_multiple", "公开认购倍数", "散户拥挤度"),
        ("international_subscription_multiple", "国际配售倍数", "机构真实需求"),
        ("one_lot_success_rate", "一手中签率", "打新资金效率"),
        ("clawback_ratio", "回拨比例", "首日流通/抛压"),
        ("cornerstone_names", "基石名单", "资金质量"),
        ("cornerstone_ratio", "基石占比", "首日浮筹/6个月压力"),
        ("sponsor_names", "保荐人", "保荐人胜率"),
        ("market_cap_at_ipo_hkd", "发行市值", "承接难度"),
    ]
    rows = []
    n = len(universe)
    for col, cn, use in fields:
        if n == 0:
            present = 0
        elif col not in universe.columns:
            present = 0
        else:
            present = int(universe[col].map(value_present).sum())
        rows.append({"字段": cn, "英文列名": col, "已覆盖": present, "总数": n, "覆盖率": present / n if n else 0, "用途": use})
    return pd.DataFrame(rows)

# ============================================================
# UI
# ============================================================

st.set_page_config(page_title=APP_TITLE, layout="wide")

universe, announcements, data_paths = load_all_data()

st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

with st.sidebar:
    st.success("数据源：\n" + "\n".join([f"{k}: {v}" for k, v in data_paths.items()]))
    st.header("筛选")
    if universe.empty:
        st.warning("没有读到任何样本。请上传 deploy_data/hk_ipo_scored_public.csv 或 a1_ipo_pipeline.csv。")
        st.stop()

    stages = sorted([x for x in universe.get("lifecycle_stage", pd.Series(dtype=str)).dropna().astype(str).unique() if x])
    default_stages = stages
    selected_stages = st.multiselect("生命周期阶段", stages, default=default_stages)

    tiers = sorted([x for x in universe.get("decision_tier", pd.Series(dtype=str)).dropna().astype(str).unique() if x])
    selected_tiers = st.multiselect("决策层", tiers, default=tiers)

    industries = sorted([x for x in universe.get("industry", pd.Series(dtype=str)).dropna().astype(str).unique() if x])
    selected_industries = st.multiselect("行业", industries, default=industries)

    risk_levels = sorted([x for x in universe.get("risk_level", pd.Series(dtype=str)).dropna().astype(str).unique() if x])
    selected_risks = st.multiselect("风险", risk_levels, default=risk_levels)

    only_180d = st.checkbox("只看上市后0-180D", value=False)
    keyword = st.text_input("搜索代码/公司/保荐人/基石")

view = universe.copy()
if selected_stages:
    view = view[view["lifecycle_stage"].isin(selected_stages)]
if selected_tiers:
    view = view[view["decision_tier"].isin(selected_tiers)]
if selected_industries:
    view = view[view["industry"].isin(selected_industries)]
if selected_risks:
    view = view[view["risk_level"].isin(selected_risks)]
if only_180d:
    view = view[view["lifecycle_stage"].str.contains("上市0-30D|上市31-90D|上市91-180D", na=False)]
if keyword.strip():
    kw = keyword.strip().lower()
    hay_cols = ["security_key", "code", "temp_code", "name", "issuer_name", "sponsor_names", "cornerstone_names"]
    mask = pd.Series(False, index=view.index)
    for col in hay_cols:
        if col in view.columns:
            mask |= view[col].astype(str).str.lower().str.contains(kw, na=False)
    view = view[mask]

# KPI row
kpis = st.columns(6)
kpis[0].metric("全样本", len(universe))
kpis[1].metric("当前筛选", len(view))
kpis[2].metric("A1/未上市", int(universe["lifecycle_stage"].str.contains("A1|递表|聆讯|招股|待上市|配发|定价", na=False).sum()))
kpis[3].metric("0-180D", int(universe["lifecycle_stage"].str.contains("上市0-30D|上市31-90D|上市91-180D", na=False).sum()))
kpis[4].metric("A层", int(universe["decision_tier"].astype(str).str.startswith("A").sum()))
kpis[5].metric("高风险", int((universe["risk_level"] == "高").sum()))

st.divider()

tabs = st.tabs([
    "① 全生命周期投资池",
    "② A1/招股前",
    "③ 招股书/配发结果",
    "④ 上市后0-180D",
    "⑤ 单票 Memo",
    "⑥ iFind取数清单",
    "⑦ 数据质量",
])

with tabs[0]:
    st.subheader("全生命周期优先级列表")
    st.write("这个页面把已递表、招股中、配发结果后、刚上市和半新股放在同一个决策池里。")
    sort_options = ["decision_tier", "readiness_score", "model_score_tradeable_20d", "listing_date", "a1_date"]
    sort_col = st.selectbox("排序字段", [c for c in sort_options if c in view.columns], index=0)
    asc = st.toggle("升序", value=False)
    core_cols = [
        "decision_tier", "lifecycle_stage", "temp_code", "code", "name", "listing_date", "days_since_listing",
        "industry", "issue_price", "readiness_score", "model_score_tradeable_20d", "risk_level",
        "primary_action", "secondary_action", "next_data_action",
    ]
    show_cols = [c for c in core_cols if c in view.columns]
    table = view.sort_values(sort_col, ascending=asc, na_position="last")[show_cols]
    st.dataframe(format_for_table(table), use_container_width=True, hide_index=True)
    st.download_button(
        "下载当前投资池 CSV",
        data=view.to_csv(index=False, encoding="utf-8-sig"),
        file_name="hk_ipo_lifecycle_pool.csv",
        mime="text/csv",
    )
    st.subheader("阶段分布")
    st.bar_chart(view["lifecycle_stage"].value_counts())

with tabs[1]:
    st.subheader("A1 / 临时代码 / 招股前决策")
    pre = view[view["lifecycle_stage"].str.contains("A1|递表|聆讯|招股|待上市|配发|定价", na=False)].copy()
    if pre.empty:
        st.info("当前没有 A1/招股前样本。上传 deploy_data/a1_ipo_pipeline.csv 后这里会显示。")
    else:
        cols = [
            "decision_tier", "lifecycle_stage", "temp_code", "code", "name", "issuer_name", "a1_date",
            "prospectus_date", "allotment_result_date", "expected_listing_date", "industry",
            "offer_price_low", "offer_price_high", "issue_price", "public_subscription_multiple",
            "international_subscription_multiple", "cornerstone_ratio", "readiness_score", "risk_level", "primary_action",
        ]
        cols = [c for c in cols if c in pre.columns]
        st.dataframe(format_for_table(pre.sort_values(["decision_tier", "readiness_score"], ascending=[True, False])[cols]), use_container_width=True, hide_index=True)
    st.markdown(
        """
        **A1阶段不要直接给买入结论。** 正确动作是：建研究档案、做行业/股东/保荐人预筛、等待招股书和配发结果公告。  
        一旦出现招股书，模型补充发行区间、保荐人、基石、募资用途；一旦出现配发结果公告，再补公开认购倍数、国际配售倍数、一手中签率、回拨比例、最终发行价。
        """
    )

with tabs[2]:
    st.subheader("招股书与配发结果公告")
    st.write("这里把每只股票的两个关键文件单独管理：招股书 + 配发结果公告。")
    doc_cols = [
        "lifecycle_stage", "temp_code", "code", "name", "prospectus_date", "allotment_result_date",
        "prospectus_title", "prospectus_url", "allotment_result_title", "allotment_result_url",
        "public_subscription_multiple", "international_subscription_multiple", "one_lot_success_rate", "clawback_ratio",
        "next_data_action",
    ]
    doc_cols = [c for c in doc_cols if c in view.columns]
    st.dataframe(format_for_table(view.sort_values("prospectus_date", ascending=False, na_position="last")[doc_cols]), use_container_width=True, hide_index=True)
    if not announcements.empty:
        st.subheader("公告目录明细")
        ann_cols = ["announcement_date", "document_type", "temp_code", "code", "name", "title", "url", "source", "downloaded", "notes"]
        ann_cols = [c for c in ann_cols if c in announcements.columns]
        st.dataframe(format_for_table(announcements.sort_values("announcement_date", ascending=False, na_position="last")[ann_cols]), use_container_width=True, hide_index=True)
    else:
        st.info("还没有公告目录文件。后续 iFind 本地脚本会生成 deploy_data/ipo_announcement_catalog.csv。")

with tabs[3]:
    st.subheader("上市后 0-180 天：由密集到稀疏跟踪")
    listed_180 = view[view["lifecycle_stage"].str.contains("上市0-30D|上市31-90D|上市91-180D", na=False)].copy()
    if listed_180.empty:
        st.info("当前筛选下没有0-180D半新股。")
    else:
        cols = [
            "decision_tier", "code", "name", "listing_date", "days_since_listing", "issue_price", "d1_close_ret",
            "max_20_ret", "min_20_ret", "max_60_ret", "path_label", "model_score_tradeable_20d",
            "secondary_action", "sell_signal", "quote_sampling_plan",
        ]
        cols = [c for c in cols if c in listed_180.columns]
        st.dataframe(format_for_table(listed_180.sort_values("days_since_listing", ascending=True)[cols]), use_container_width=True, hide_index=True)
        st.subheader("路径分布")
        st.bar_chart(listed_180["path_label"].map(lambda x: PATH_CN.get(x, x)).value_counts())
    st.markdown(
        """
        **行情抓取策略**  
        - D0-D30：每日抓取，最容易出现破发、深V、首日过热回落。  
        - D31-D90：每3个交易日抓取一次，若重新站回发行价/放量/创新高则临时加密。  
        - D91-D180：每周抓取一次，重点看趋势延续和解禁前风险预警。  
        """
    )

with tabs[4]:
    st.subheader("单票 Memo")
    name_series = view["name"] if "name" in view.columns else pd.Series([""] * len(view), index=view.index)
    code_series = view["code"].fillna("").astype(str) if "code" in view.columns else pd.Series([""] * len(view), index=view.index)
    temp_series = view["temp_code"].fillna("").astype(str) if "temp_code" in view.columns else pd.Series([""] * len(view), index=view.index)
    labels = (temp_series.where(temp_series.ne(""), code_series) + " " + name_series.astype(str) + " | " + view["lifecycle_stage"].astype(str)).tolist()
    selected = st.selectbox("选择股票/发行人", labels)
    if selected:
        selected_key = selected.split()[0]
        candidates = view[(view["temp_code"].astype(str) == selected_key) | (view["code"].astype(str) == selected_key) | (view["security_key"].astype(str) == selected_key)]
        if candidates.empty:
            candidates = view.iloc[[labels.index(selected)]]
        row = candidates.iloc[0]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("阶段", clean_text(row.get("lifecycle_stage")))
        c2.metric("决策层", clean_text(row.get("decision_tier")))
        c3.metric("资料完整度", "" if pd.isna(row.get("readiness_score")) else f"{float(row.get('readiness_score')):.2f}")
        c4.metric("交易分", "" if pd.isna(row.get("model_score_tradeable_20d")) else f"{float(row.get('model_score_tradeable_20d')):.2f}")
        c5.metric("风险", clean_text(row.get("risk_level")))
        memo = build_memo(row, announcements)
        st.markdown(memo)
        st.download_button(
            "下载该票 Memo.md",
            data=memo.encode("utf-8"),
            file_name=f"{clean_text(row.get('name')) or clean_text(row.get('security_key'))}_ipo_memo.md",
            mime="text/markdown",
        )

with tabs[5]:
    st.subheader("iFind 取数清单：先按这三个层级打通")
    st.markdown(
        """
        **你的三个要求已变成数据层设计：**

        1. **港股 IPO 列表必须包括 A1/未上市公司**：用 `a1_ipo_pipeline.csv` 存临时代码、A1日期、招股书链接、预计上市日。  
        2. **单票发行资料来自两个公告**：招股书 + 配发结果公告，落到 `ipo_offer_results.csv` 和 `ipo_announcement_catalog.csv`。  
        3. **上市后行情抓取 0-180D**：D0-D30每日，D31-D90每3个交易日，D91-D180每周，触发信号时加密。
        """
    )
    st.code(
        """
# 超级命令优先生成这些查询，不要先追求字段完美：

1）A1/未上市管线
港股 A1 递表 临时代码 发行人 招股书 公告日期 保荐人 预期上市日期

2）单票招股书
某临时代码/某公司 招股书 招股价区间 募资金额 保荐人 基石投资者 募资用途 风险因素

3）单票配发结果公告
某代码 配发结果公告 最终发行价 公开认购倍数 国际配售倍数 一手中签率 回拨比例 基石认购金额 上市日期

4）上市后行情
某正式代码 日行情 上市日期至上市后180天 开盘价 最高价 最低价 收盘价 成交量 成交额 换手率
        """.strip(),
        language="text",
    )
    st.subheader("CSV 模板列名")
    st.write("不用手工整理完整历史；先让 iFind 导出后按这些列名落地。")
    st.code(
        """
deploy_data/a1_ipo_pipeline.csv
security_key,temp_code,code,name,issuer_name,lifecycle_stage,a1_date,hearing_date,prospectus_date,allotment_result_date,expected_listing_date,listing_date,industry,offer_price_low,offer_price_high,issue_price,fundraising_amount_hkd,market_cap_at_ipo_hkd,sponsor_names,overall_coordinator_names,cornerstone_names,cornerstone_amount_hkd,cornerstone_ratio,public_subscription_multiple,international_subscription_multiple,one_lot_success_rate,clawback_ratio,prospectus_title,prospectus_url,allotment_result_title,allotment_result_url,key_risks,notes

deploy_data/ipo_offer_results.csv
security_key,temp_code,code,name,prospectus_date,allotment_result_date,expected_listing_date,listing_date,offer_price_low,offer_price_high,issue_price,final_price_position,public_subscription_multiple,international_subscription_multiple,one_lot_success_rate,clawback_ratio,fundraising_amount_hkd,market_cap_at_ipo_hkd,cornerstone_names,cornerstone_amount_hkd,cornerstone_ratio,sponsor_names,overall_coordinator_names,notes

deploy_data/ipo_announcement_catalog.csv
security_key,temp_code,code,name,announcement_date,document_type,title,url,source,downloaded,local_path,notes
        """.strip(),
        language="text",
    )

with tabs[6]:
    st.subheader("数据质量")
    q = data_quality_table(universe)
    q_display = q.copy()
    q_display["覆盖率"] = q_display["覆盖率"].map(fmt_pct)
    st.dataframe(q_display, use_container_width=True, hide_index=True)
    st.subheader("按阶段的缺字段动作")
    cols = ["lifecycle_stage", "temp_code", "code", "name", "decision_tier", "readiness_score", "next_data_action"]
    cols = [c for c in cols if c in universe.columns]
    st.dataframe(format_for_table(universe.sort_values("readiness_score", ascending=True)[cols].head(100)), use_container_width=True, hide_index=True)
