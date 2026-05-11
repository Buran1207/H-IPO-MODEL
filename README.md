from __future__ import annotations

"""
Step 5 v2: ingest iFind 一级市场 GUI exports for HK IPO decision cockpit.

Supported current exports:
- 港股IPO首发信息一览.csv       => THS_DR('p05310') / IPO发行主表
- 港股IPO打新中签结果.csv       => THS_DR('p04477') / 公开发售、中签、认购热度
- 港股IPO基石投资者.csv         => THS_DR('p05309') / 基石投资者明细

Supported future exports by Chinese headers:
- 上市申请一览                 => A1/临时代码/申请状态
- IPO回拨统计                  => 回拨比例补丁
- 首发中介机构/保荐人参与度     => 保荐人、整体协调人、承销商补丁
- 孖展数据 / IPO暗盘行情        => 情绪补丁

Usage:
    python scripts/ingest_ifind_gui_exports.py --input-dir ifind_exports --outdir deploy_data

The script writes normalized CSVs that Streamlit can read directly.
"""

import argparse
import re
from pathlib import Path
from typing import Any

import pandas as pd

TODAY = pd.Timestamp.today().normalize()
MISSING_VALUES = {"", "--", "-", "—", "nan", "NaN", "None", "NULL", "null", "无", "不适用", "N/A", "n/a"}

# p05310: 港股IPO首发信息一览 / first issue information
P05310_MAP = {
    "p05310_f001": "code",
    "p05310_f002": "name",
    "p05310_f034": "listing_date",
    "p05310_f003": "result_or_latest_date_raw",
    "p05310_f028": "prospectus_date",
    "p05310_f053": "board",
    "p05310_f004": "offer_type",
    "p05310_f054": "has_public_offer",
    "p05310_f006": "is_transfer_or_intro_raw",
    "p05310_f007": "reserved_f007",
    "p05310_f009": "offer_price_low",
    "p05310_f008": "offer_price_high",
    "p05310_f010": "issue_price",
    "p05310_f011": "board_lot",
    "p05310_f012": "market_cap_at_ipo_hkd_mn",
    "p05310_f013": "global_offer_shares_initial",
    "p05310_f014": "global_offer_shares_final_base",
    "p05310_f040": "global_offer_shares_with_oa",
    "p05310_f041": "global_offer_shares_ex_oa_or_exercised_raw",
    "p05310_f015": "public_offer_shares_initial",
    "p05310_f016": "public_offer_shares_final",
    "p05310_f017": "international_offer_shares_initial",
    "p05310_f018": "international_offer_shares_final",
    "p05310_f035": "placing_or_reserved_shares_initial_raw",
    "p05310_f036": "placing_or_reserved_shares_final_raw",
    "p05310_f019": "other_offer_shares_initial_raw",
    "p05310_f020": "other_offer_shares_final_raw",
    "p05310_f021": "over_allotment_option_shares",
    "p05310_f022": "over_allotment_exercised_shares",
    "p05310_f037": "reserved_f037",
    "p05310_f038": "reserved_f038",
    "p05310_f042": "sale_shares_initial_raw",
    "p05310_f043": "sale_shares_final_raw",
    "p05310_f044": "cornerstone_shares_from_first_issue",
    "p05310_f023": "gross_proceeds_with_oa_hkd",
    "p05310_f047": "gross_proceeds_base_hkd",
    "p05310_f048": "gross_proceeds_oa_hkd",
    "p05310_f024": "listing_expenses_hkd",
    "p05310_f025": "net_proceeds_hkd",
    "p05310_f039": "offer_currency",
    "p05310_f049": "proceeds_use",
    "p05310_f045": "par_value",
    "p05310_f046": "par_value_currency",
    "p05310_f050": "issue_pe",
    "p05310_f026": "reserved_f026",
    "p05310_f027": "public_subscription_multiple_first_issue",
    "p05310_f051": "reserved_f051",
    "p05310_f052": "international_subscription_multiple_first_issue",
    "p05310_f029": "offer_start_date",
    "p05310_f030": "offer_end_date",
    "p05310_f031": "pricing_date",
    "p05310_f032": "allotment_result_date",
    "p05310_f033": "expected_listing_date",
}

# p04477: 港股IPO打新中签结果 / HK public offer and balloting result
P04477_MAP = {
    "p04477_f001": "code",
    "p04477_f002": "name",
    "p04477_f003": "allotment_result_date",
    "p04477_f004": "ballot_applications_total_raw",
    "p04477_f005": "ballot_applications_a_raw",
    "p04477_f006": "ballot_applications_b_raw",
    "p04477_f007": "ballot_applications_other_raw",
    "p04477_f008": "ballot_valid_applications_total_raw",
    "p04477_f009": "ballot_valid_applications_a_raw",
    "p04477_f010": "ballot_valid_applications_b_raw",
    "p04477_f011": "ballot_valid_applications_other_raw",
    "p04477_f012": "ballot_subscription_total_raw",
    "p04477_f013": "ballot_subscription_a_raw",
    "p04477_f014": "ballot_subscription_b_raw",
    "p04477_f015": "ballot_subscription_other_raw",
    "p04477_f016": "ballot_success_total_raw",
    "p04477_f017": "ballot_success_a_raw",
    "p04477_f018": "ballot_success_b_raw",
    "p04477_f019": "ballot_success_other_raw",
    "p04477_f020": "public_subscription_multiple",
    "p04477_f021": "one_lot_success_rate_pct_input",
    "p04477_f022": "industry",
    "p04477_f023": "sub_industry",
}

# p05309: 港股IPO基石投资者 / cornerstone investors
P05309_MAP = {
    "p05309_f001": "code",
    "p05309_f002": "name",
    "p05309_f003": "listing_date",
    "p05309_f016": "result_or_latest_date_raw",
    "p05309_f004": "prospectus_date",
    "p05309_f017": "has_cornerstone_investor",
    "p05309_f005": "cornerstone_name",
    "p05309_f018": "cornerstone_description",
    "p05309_f006": "cornerstone_controller_or_manager",
    "p05309_f019": "cornerstone_controller_description",
    "p05309_f009": "cornerstone_shares_or_reserved_raw",
    "p05309_f008": "cornerstone_amount_hkd",
    "p05309_f011": "cornerstone_currency",
    "p05309_f014": "cornerstone_ratio_pct_input",
    "p05309_f010": "cornerstone_lockup_months",
    "p05309_f015": "cornerstone_lockup_end_date",
    "p05309_f012": "cornerstone_relationship_raw",
    "p05309_f013": "industry",
}

COMMON_CHINESE_MAP = {
    "同花顺代码": "ifind_code", "证券代码": "code", "股票代码": "code", "代码": "code", "临时代码": "temp_code",
    "证券简称": "name", "股票简称": "name", "简称": "name", "公司简称": "name", "发行人": "issuer_name", "公司名称": "issuer_name",
    "申请日期": "application_date", "首次申请日期": "a1_date", "申请状态": "application_status", "申请状态更新日期": "application_status_update_date",
    "通过聆讯日期": "hearing_date", "聆讯日期": "hearing_date", "上市日期": "listing_date", "预期上市日期": "expected_listing_date", "预计上市日期": "expected_listing_date",
    "拟上市板块": "board", "上市板块": "board", "保荐人": "sponsor_names", "联席保荐人": "sponsor_names", "整体协调人": "overall_coordinator_names",
    "招股书日期": "prospectus_date", "招股开始日期": "offer_start_date", "招股截止日期": "offer_end_date", "定价日期": "pricing_date", "定价日": "pricing_date",
    "公布配发结果日期": "allotment_result_date", "配发结果公告日期": "allotment_result_date",
    "发行价": "issue_price", "最终发行价": "issue_price", "发售价": "issue_price", "招股价下限": "offer_price_low", "招股价上限": "offer_price_high",
    "每手股数": "board_lot", "一手股数": "board_lot", "上市市值": "market_cap_at_ipo_hkd", "发行市值": "market_cap_at_ipo_hkd",
    "募资金额": "fundraising_amount_hkd", "集资额": "fundraising_amount_hkd", "所得款项净额": "net_proceeds_hkd", "募资用途": "proceeds_use", "募集资金用途": "proceeds_use",
    "公开认购倍数": "public_subscription_multiple", "公开发售认购倍数": "public_subscription_multiple", "国际配售倍数": "international_subscription_multiple",
    "一手中签率": "one_lot_success_rate", "回拨比例": "clawback_ratio", "基石投资者": "cornerstone_names", "基石金额": "cornerstone_amount_hkd",
    "基石占比": "cornerstone_ratio", "行业": "industry", "所属行业": "industry", "暗盘涨跌幅": "gray_ret", "暗盘收盘价": "gray_close", "孖展倍数": "margin_multiple",
}

DATE_COLS = {"listing_date", "expected_listing_date", "prospectus_date", "offer_start_date", "offer_end_date", "pricing_date", "allotment_result_date", "application_date", "a1_date", "hearing_date", "application_status_update_date", "cornerstone_lockup_end_date"}
RATIO_COLS = {"one_lot_success_rate", "clawback_ratio", "cornerstone_ratio", "final_price_position", "gray_ret"}
NUMERIC_COLS = {
    "issue_price", "offer_price_low", "offer_price_high", "board_lot", "market_cap_at_ipo_hkd", "market_cap_at_ipo_hkd_mn",
    "fundraising_amount_hkd", "net_proceeds_hkd", "gross_proceeds_base_hkd", "gross_proceeds_with_oa_hkd", "listing_expenses_hkd",
    "public_subscription_multiple", "international_subscription_multiple", "cornerstone_amount_hkd", "cornerstone_shares", "cornerstone_lockup_months",
    "global_offer_shares_initial", "global_offer_shares_final_base", "global_offer_shares_with_oa",
    "public_subscription_multiple_first_issue", "international_subscription_multiple_first_issue",
    "public_offer_shares_initial", "public_offer_shares_final", "international_offer_shares_initial", "international_offer_shares_final",
    "issue_pe", "margin_multiple", "gray_close",
    "ballot_applications_total_raw", "ballot_applications_a_raw", "ballot_applications_b_raw", "ballot_valid_applications_total_raw",
    "ballot_subscription_total_raw", "ballot_success_total_raw",
}

PIPELINE_COLUMNS = [
    "security_key", "temp_code", "code", "name", "issuer_name", "lifecycle_stage",
    "application_date", "a1_date", "application_status", "application_status_update_date",
    "hearing_date", "prospectus_date", "offer_start_date", "offer_end_date", "pricing_date",
    "allotment_result_date", "expected_listing_date", "listing_date", "board", "industry", "sub_industry",
    "offer_price_low", "offer_price_high", "issue_price", "final_price_position", "board_lot",
    "fundraising_amount_hkd", "market_cap_at_ipo_hkd", "net_proceeds_hkd", "issue_pe",
    "public_subscription_multiple", "international_subscription_multiple", "one_lot_success_rate", "clawback_ratio",
    "cornerstone_names", "cornerstone_investor_count", "cornerstone_amount_hkd", "cornerstone_shares", "cornerstone_ratio",
    "cornerstone_lockup_months", "cornerstone_lockup_end_date", "cornerstone_quality_tags",
    "sponsor_names", "overall_coordinator_names", "bookrunner_names", "underwriter_names",
    "proceeds_use", "primary_signal", "primary_action", "data_completeness_score", "next_data_action", "source_files",
]

OFFER_COLUMNS = [
    "security_key", "code", "name", "prospectus_date", "offer_start_date", "offer_end_date", "pricing_date", "allotment_result_date", "expected_listing_date", "listing_date",
    "offer_price_low", "offer_price_high", "issue_price", "final_price_position", "board_lot", "fundraising_amount_hkd", "market_cap_at_ipo_hkd", "net_proceeds_hkd", "issue_pe",
    "public_subscription_multiple", "international_subscription_multiple", "one_lot_success_rate", "clawback_ratio",
    "cornerstone_investor_count", "cornerstone_names", "cornerstone_amount_hkd", "cornerstone_ratio", "cornerstone_lockup_months", "cornerstone_lockup_end_date",
    "industry", "sub_industry", "proceeds_use", "source_files",
]


def clean_missing(x: Any) -> Any:
    if pd.isna(x):
        return pd.NA
    s = str(x).strip()
    return pd.NA if s in MISSING_VALUES else x


def clean_text(x: Any) -> str:
    if pd.isna(x):
        return ""
    s = str(x).strip()
    return "" if s in MISSING_VALUES else s


def clean_code(x: Any, prefer_temp: bool = False) -> str:
    s = clean_text(x).upper()
    if not s:
        return ""
    if s.startswith("H"):
        m = re.search(r"H\s*(\d+)", s)
        return f"H{int(m.group(1)):04d}.HK" if m else s
    if s.endswith(".HK"):
        left = s[:-3]
        return f"{int(left):04d}.HK" if left.isdigit() else s
    if s.isdigit():
        return f"{int(s):04d}.HK"
    return s


def to_num(s: pd.Series) -> pd.Series:
    raw = s.astype(str).str.replace(",", "", regex=False).str.replace("%", "", regex=False).str.strip()
    raw = raw.mask(raw.isin(MISSING_VALUES))
    return pd.to_numeric(raw, errors="coerce")


def normalize_percent(s: pd.Series, always_pct_input: bool = False) -> pd.Series:
    raw = s.astype(str)
    has_pct = raw.str.contains("%", regex=False, na=False)
    v = to_num(s)
    # iFind tables often export percent fields as 0.8 meaning 0.8%, not 80%.
    if always_pct_input or has_pct.any() or v.dropna().gt(1.5).any():
        return v / 100.0
    return v


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    for enc in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().replace("\n", "").replace("\r", "") for c in out.columns]
    drop_cols = [c for c in out.columns if c == "" or c.startswith("Unnamed") or c.lower() in {"nan", "none"}]
    return out.drop(columns=drop_cols, errors="ignore")


def drop_source_rows(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if len(out) == 0:
        return out
    first_col = out.columns[0]
    mask = ~out[first_col].astype(str).str.contains("数据来源", na=False)
    return out.loc[mask].copy()


def detect_kind(path: Path, df: pd.DataFrame) -> str:
    stem = path.stem
    cols = set(df.columns)
    if any(c.startswith("p05310_") for c in cols) or "首发信息" in stem:
        return "first_issue"
    if any(c.startswith("p04477_") for c in cols) or "中签" in stem or "打新" in stem:
        return "ballot"
    if any(c.startswith("p05309_") for c in cols) or "基石" in stem:
        return "cornerstone"
    if "上市申请" in stem or {"同花顺代码", "申请日期", "申请状态"}.issubset(cols):
        return "listing_application"
    if "回拨" in stem:
        return "clawback"
    if "中介" in stem or "保荐" in stem:
        return "intermediary"
    if "孖展" in stem:
        return "margin"
    if "暗盘" in stem:
        return "gray_market"
    return "unknown"


def rename_and_basic_clean(df: pd.DataFrame, mapping: dict[str, str], source: str) -> pd.DataFrame:
    out = normalize_headers(drop_source_rows(df))
    if mapping:
        out = out.rename(columns={c: mapping.get(c, c) for c in out.columns})
    out = out.rename(columns={c: COMMON_CHINESE_MAP.get(c, c) for c in out.columns})
    if "ifind_code" in out.columns:
        is_temp = out["ifind_code"].astype(str).str.upper().str.startswith("H")
        out["temp_code"] = out.get("temp_code", pd.Series(index=out.index, dtype=object))
        out["code"] = out.get("code", pd.Series(index=out.index, dtype=object))
        out.loc[is_temp, "temp_code"] = out.loc[is_temp, "ifind_code"].map(lambda x: clean_code(x, True))
        out.loc[~is_temp, "code"] = out.loc[~is_temp, "ifind_code"].map(clean_code)
    for col in ["code", "temp_code"]:
        if col in out.columns:
            out[col] = out[col].map(lambda x: clean_code(x, col == "temp_code"))
    for col in out.columns:
        if col in DATE_COLS:
            out[col] = pd.to_datetime(out[col].map(clean_missing), errors="coerce")
        elif col in RATIO_COLS:
            out[col] = normalize_percent(out[col])
        elif col in NUMERIC_COLS:
            out[col] = to_num(out[col])
        else:
            if out[col].dtype == "object":
                out[col] = out[col].map(clean_text)
    if "one_lot_success_rate_pct_input" in out.columns:
        out["one_lot_success_rate"] = normalize_percent(out["one_lot_success_rate_pct_input"], always_pct_input=True)
    if "cornerstone_ratio_pct_input" in out.columns:
        out["cornerstone_ratio"] = normalize_percent(out["cornerstone_ratio_pct_input"], always_pct_input=True)
    if "name" not in out.columns and "issuer_name" in out.columns:
        out["name"] = out["issuer_name"]
    if "issuer_name" not in out.columns and "name" in out.columns:
        out["issuer_name"] = out["name"]
    out["source_files"] = source
    out["security_key"] = out.apply(lambda r: clean_text(r.get("code")) or clean_text(r.get("temp_code")) or clean_text(r.get("name")), axis=1)
    out = out[out["security_key"].astype(str).str.len() > 0]
    return out


def process_first_issue(df: pd.DataFrame, source: str) -> pd.DataFrame:
    out = rename_and_basic_clean(df, P05310_MAP, source)
    if "market_cap_at_ipo_hkd_mn" in out.columns:
        out["market_cap_at_ipo_hkd"] = out["market_cap_at_ipo_hkd_mn"] * 1_000_000
    # prefer p05310 subscription multiples, then later p04477 can overwrite public.
    if "public_subscription_multiple_first_issue" in out.columns:
        out["public_subscription_multiple"] = out["public_subscription_multiple_first_issue"]
    if "international_subscription_multiple_first_issue" in out.columns:
        out["international_subscription_multiple"] = out["international_subscription_multiple_first_issue"]
    return out


def process_ballot(df: pd.DataFrame, source: str) -> pd.DataFrame:
    out = rename_and_basic_clean(df, P04477_MAP, source)
    return out


def process_cornerstone(df: pd.DataFrame, source: str) -> pd.DataFrame:
    out = rename_and_basic_clean(df, P05309_MAP, source)
    return out


def process_generic(df: pd.DataFrame, source: str) -> pd.DataFrame:
    return rename_and_basic_clean(df, {}, source)


def unique_join(values: pd.Series, sep: str = "；") -> str:
    vals: list[str] = []
    for v in values:
        s = clean_text(v)
        if not s:
            continue
        if s not in vals:
            vals.append(s)
    return sep.join(vals)


def first_valid(values: pd.Series) -> Any:
    for v in values:
        if pd.isna(v):
            continue
        if isinstance(v, str) and clean_text(v) == "":
            continue
        return v
    return pd.NA


def collapse_by_key(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    key = "security_key"
    agg: dict[str, Any] = {}
    for col in df.columns:
        if col == key:
            continue
        if col in {"source_files", "cornerstone_names", "cornerstone_name", "sponsor_names", "overall_coordinator_names", "bookrunner_names", "underwriter_names", "industry", "sub_industry"}:
            agg[col] = unique_join
        elif col in {"cornerstone_amount_hkd", "cornerstone_shares", "cornerstone_ratio"}:
            agg[col] = "sum"
        elif pd.api.types.is_numeric_dtype(df[col]):
            agg[col] = first_valid
        else:
            agg[col] = first_valid
    return df.groupby(key, dropna=False, as_index=False).agg(agg)


def summarize_cornerstone(cornerstone: pd.DataFrame) -> pd.DataFrame:
    if cornerstone.empty:
        return pd.DataFrame(columns=["security_key", "code", "name", "cornerstone_names", "cornerstone_investor_count", "cornerstone_amount_hkd", "cornerstone_ratio", "cornerstone_lockup_months", "cornerstone_lockup_end_date", "cornerstone_quality_tags", "industry", "source_files"])
    df = cornerstone.copy()
    if "cornerstone_name" in df.columns:
        df["cornerstone_names"] = df["cornerstone_name"]
    # quality tags based on name/controller text; intentionally conservative.
    def tags_for_group(g: pd.DataFrame) -> str:
        text = " ".join([clean_text(x) for x in g.get("cornerstone_name", pd.Series(dtype=object)).tolist() + g.get("cornerstone_controller_or_manager", pd.Series(dtype=object)).tolist() + g.get("cornerstone_description", pd.Series(dtype=object)).tolist()])
        tags = []
        patterns = {
            "产业方": r"腾讯|阿里|京东|美团|小米|比亚迪|宁德|产业|集团|控股有限公司",
            "长线基金": r"基金|资产管理|Fund|Capital|Investment|Management|OFC|SPC|睿远|高瓴|Hillhouse|淡马锡|Temasek|GIC|BlackRock|贝莱德",
            "主权/国资": r"主权|国资|国有|政府|QIA|ADIA|GIC|社保",
            "上市公司关联": r"上市|股份代号|联交所|证券交易所",
        }
        for tag, pat in patterns.items():
            if re.search(pat, text, re.I):
                tags.append(tag)
        return "；".join(tags)
    grouped = []
    for key, g in df.groupby("security_key", dropna=False):
        row = {
            "security_key": key,
            "code": first_valid(g.get("code", pd.Series(dtype=object))),
            "name": first_valid(g.get("name", pd.Series(dtype=object))),
            "cornerstone_names": unique_join(g.get("cornerstone_name", pd.Series(dtype=object))),
            "cornerstone_investor_count": int(g.get("cornerstone_name", pd.Series(dtype=object)).map(clean_text).ne("").sum()),
            "cornerstone_amount_hkd": g.get("cornerstone_amount_hkd", pd.Series(dtype=float)).sum(min_count=1),
            "cornerstone_ratio": g.get("cornerstone_ratio", pd.Series(dtype=float)).sum(min_count=1),
            "cornerstone_lockup_months": first_valid(g.get("cornerstone_lockup_months", pd.Series(dtype=float))),
            "cornerstone_lockup_end_date": first_valid(g.get("cornerstone_lockup_end_date", pd.Series(dtype="datetime64[ns]"))),
            "cornerstone_quality_tags": tags_for_group(g),
            "industry": unique_join(g.get("industry", pd.Series(dtype=object))),
            "source_files": unique_join(g.get("source_files", pd.Series(dtype=object))),
        }
        grouped.append(row)
    return pd.DataFrame(grouped)


def final_price_position(df: pd.DataFrame) -> pd.Series:
    if {"issue_price", "offer_price_low", "offer_price_high"}.issubset(df.columns):
        low = df["offer_price_low"]
        high = df["offer_price_high"]
        issue = df["issue_price"]
        den = (high - low).replace(0, pd.NA)
        return (issue - low) / den
    return pd.Series(pd.NA, index=df.index, dtype="float")


def scalar_num(x: Any) -> float:
    if pd.isna(x):
        return float("nan")
    try:
        return float(str(x).replace(",", "").replace("%", ""))
    except Exception:
        return float("nan")


def infer_stage(row: pd.Series) -> str:
    listing = row.get("listing_date")
    expected = row.get("expected_listing_date")
    issue = row.get("issue_price")
    if pd.notna(listing):
        days = (TODAY - pd.to_datetime(listing)).days
        if days < 0:
            return "已定价待上市"
        if days <= 180:
            return "已上市0-180D"
        return "已上市180D后"
    if pd.notna(expected) and expected >= TODAY:
        return "已定价待上市"
    if pd.notna(issue) or pd.notna(row.get("allotment_result_date")):
        return "配发结果后"
    if pd.notna(row.get("prospectus_date")) or pd.notna(row.get("offer_start_date")) or pd.notna(row.get("offer_price_low")):
        return "招股中/待上市"
    if pd.notna(row.get("hearing_date")):
        return "已聆讯/待招股"
    return "A1/递表"


def data_completeness(row: pd.Series) -> float:
    fields = [
        "name", "code", "prospectus_date", "listing_date", "offer_price_low", "offer_price_high", "issue_price", "board_lot",
        "fundraising_amount_hkd", "market_cap_at_ipo_hkd", "public_subscription_multiple", "international_subscription_multiple",
        "one_lot_success_rate", "cornerstone_names", "cornerstone_amount_hkd", "cornerstone_ratio", "proceeds_use", "industry",
    ]
    got = 0
    for f in fields:
        v = row.get(f)
        if pd.notna(v) and clean_text(v) != "":
            got += 1
    return got / len(fields)


def action_for_row(row: pd.Series) -> str:
    stage = row.get("lifecycle_stage", "")
    pub = scalar_num(row.get("public_subscription_multiple"))
    one = scalar_num(row.get("one_lot_success_rate"))
    cs_ratio = scalar_num(row.get("cornerstone_ratio"))
    issue = scalar_num(row.get("issue_price"))
    fp = scalar_num(row.get("final_price_position"))
    if stage in {"A1/递表", "已聆讯/待招股"}:
        return "建研究档案；等招股价区间、保荐人、基石与募资用途"
    if pd.isna(issue):
        return "等配发结果；暂不定一级仓位"
    positives = 0
    risks = 0
    if pd.notna(pub):
        if pub >= 50:
            positives += 1
        if pub >= 1000:
            risks += 1
    if pd.notna(one) and one <= 0.2:
        positives += 1
    if pd.notna(cs_ratio):
        if 0.05 <= cs_ratio <= 0.55:
            positives += 1
        if cs_ratio > 0.65:
            risks += 1
    if pd.notna(fp):
        if fp <= 0.65:
            positives += 1
        if fp >= 0.95:
            risks += 1
    if positives >= 3 and risks == 0:
        return "一级可重点参与；若首日高开过多，二级等回踩确认"
    if positives >= 2:
        return "可小额/选择性参与；二级等首日浮筹释放"
    if risks >= 2:
        return "谨慎或回避一级；只做二级事件观察"
    return "中性观察；等待暗盘、首日成交和发行价支撑确认"


def signal_for_row(row: pd.Series) -> str:
    pub = scalar_num(row.get("public_subscription_multiple"))
    one = scalar_num(row.get("one_lot_success_rate"))
    cs = scalar_num(row.get("cornerstone_ratio"))
    tags = []
    if pd.notna(pub):
        if pub >= 1000:
            tags.append("散户极热/易拥挤")
        elif pub >= 50:
            tags.append("公开认购强")
        elif pub < 10:
            tags.append("公开认购弱")
    if pd.notna(one):
        if one <= 0.02:
            tags.append("一手中签极低")
        elif one <= 0.2:
            tags.append("一手中签偏低")
    if pd.notna(cs):
        if cs >= 0.5:
            tags.append("基石占比高")
        elif cs >= 0.1:
            tags.append("基石支持")
    if clean_text(row.get("cornerstone_quality_tags")):
        tags.append(clean_text(row.get("cornerstone_quality_tags")))
    return "；".join(tags) if tags else "待补关键发行结构"


def next_data_action(row: pd.Series) -> str:
    stage = row.get("lifecycle_stage", "")
    if stage in {"A1/递表", "已聆讯/待招股"}:
        return "补上市申请一览、保荐人/中介机构、行业与申请版本"
    if pd.isna(row.get("issue_price")):
        return "等配发结果；补最终发行价/认购倍数/中签率"
    if pd.isna(row.get("one_lot_success_rate")):
        return "补IPO打新中签结果"
    if clean_text(row.get("cornerstone_names")) == "":
        return "补基石投资者明细"
    listing = row.get("listing_date")
    if pd.notna(listing) and (TODAY - pd.to_datetime(listing)).days <= 180:
        return "补上市后0-180D行情、暗盘与卖点监控"
    return "补暗盘/孖展/二级行情用于交易路径回测"


def merge_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    frames = [f for f in frames if not f.empty]
    if not frames:
        return pd.DataFrame()
    all_cols = sorted(set().union(*[set(f.columns) for f in frames]))
    normalized = []
    for f in frames:
        tmp = f.copy()
        for c in all_cols:
            if c not in tmp.columns:
                tmp[c] = pd.NA
        normalized.append(tmp[all_cols])
    raw = pd.concat(normalized, ignore_index=True)
    return collapse_by_key(raw)


def finalize_master(master: pd.DataFrame) -> pd.DataFrame:
    if master.empty:
        return pd.DataFrame(columns=PIPELINE_COLUMNS)
    out = master.copy()
    if "final_price_position" not in out.columns:
        out["final_price_position"] = final_price_position(out)
    else:
        out["final_price_position"] = out["final_price_position"].fillna(final_price_position(out))
    out["lifecycle_stage"] = out.apply(infer_stage, axis=1)
    out["primary_signal"] = out.apply(signal_for_row, axis=1)
    out["primary_action"] = out.apply(action_for_row, axis=1)
    out["data_completeness_score"] = out.apply(data_completeness, axis=1)
    out["next_data_action"] = out.apply(next_data_action, axis=1)
    for c in PIPELINE_COLUMNS:
        if c not in out.columns:
            out[c] = pd.NA
    # newest / active first
    sort_col = "listing_date" if "listing_date" in out.columns else "prospectus_date"
    out = out.sort_values(sort_col, ascending=False, na_position="last")
    return out[PIPELINE_COLUMNS + [c for c in out.columns if c not in PIPELINE_COLUMNS]]


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="ifind_exports")
    parser.add_argument("--outdir", default="deploy_data")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    files = [p for p in sorted(input_dir.glob("**/*")) if p.suffix.lower() in {".csv", ".xlsx", ".xls"} and not p.name.startswith("~$")]
    first_issue_frames: list[pd.DataFrame] = []
    ballot_frames: list[pd.DataFrame] = []
    cornerstone_detail_frames: list[pd.DataFrame] = []
    patch_frames: list[pd.DataFrame] = []
    inventory = []

    for path in files:
        try:
            raw = read_table(path)
            raw = normalize_headers(raw)
            kind = detect_kind(path, raw)
            if kind == "first_issue":
                norm = process_first_issue(raw, path.name)
                first_issue_frames.append(norm)
                patch_frames.append(norm)
            elif kind == "ballot":
                norm = process_ballot(raw, path.name)
                ballot_frames.append(norm)
                patch_frames.append(norm)
            elif kind == "cornerstone":
                detail = process_cornerstone(raw, path.name)
                cornerstone_detail_frames.append(detail)
                summary = summarize_cornerstone(detail)
                patch_frames.append(summary)
                norm = detail
            else:
                norm = process_generic(raw, path.name)
                patch_frames.append(norm)
            write_csv(norm, outdir / f"{kind}_{path.stem}_raw_ifind.csv")
            inventory.append({"file": path.name, "detected_kind": kind, "raw_rows": len(raw), "raw_columns": len(raw.columns), "normalized_rows": len(norm)})
            print(f"OK {path.name}: kind={kind}, rows={len(raw)}, cols={len(raw.columns)}")
        except Exception as exc:
            inventory.append({"file": path.name, "detected_kind": "ERROR", "raw_rows": 0, "raw_columns": 0, "normalized_rows": 0, "error": str(exc)})
            print(f"ERROR {path.name}: {exc}")

    first_issue = finalize_master(collapse_by_key(pd.concat(first_issue_frames, ignore_index=True)) if first_issue_frames else pd.DataFrame())
    ballot = collapse_by_key(pd.concat(ballot_frames, ignore_index=True)) if ballot_frames else pd.DataFrame()
    cornerstone_detail = pd.concat(cornerstone_detail_frames, ignore_index=True) if cornerstone_detail_frames else pd.DataFrame()
    cornerstone_summary = summarize_cornerstone(cornerstone_detail) if not cornerstone_detail.empty else pd.DataFrame()
    master = finalize_master(merge_frames(patch_frames))

    offer = master.copy()
    for c in OFFER_COLUMNS:
        if c not in offer.columns:
            offer[c] = pd.NA
    offer = offer[OFFER_COLUMNS + [c for c in offer.columns if c not in OFFER_COLUMNS]]

    write_csv(master, outdir / "a1_ipo_pipeline.csv")
    write_csv(offer, outdir / "ipo_offer_results.csv")
    write_csv(first_issue, outdir / "ipo_master_ifind_normalized.csv")
    write_csv(ballot, outdir / "ipo_ballot_results.csv")
    write_csv(cornerstone_detail, outdir / "ipo_cornerstone_investors.csv")
    write_csv(cornerstone_summary, outdir / "ipo_cornerstone_summary.csv")
    write_csv(pd.DataFrame(inventory), outdir / "data_inventory.csv")

    print("\nWrote deploy_data:")
    for fn in ["a1_ipo_pipeline.csv", "ipo_offer_results.csv", "ipo_master_ifind_normalized.csv", "ipo_ballot_results.csv", "ipo_cornerstone_investors.csv", "ipo_cornerstone_summary.csv", "data_inventory.csv"]:
        p = outdir / fn
        print(f"- {p} rows={len(pd.read_csv(p)) if p.exists() and p.stat().st_size else 0}")


if __name__ == "__main__":
    main()
