from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Optional

import pandas as pd

NA_VALUES = {"--", "---", "", "nan", "NaN", "None", "null", "NULL", "不适用", "-"}


def read_csv_smart(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    last_error: Optional[Exception] = None
    for enc in ("utf-8-sig", "utf-8", "gb18030", "gbk", "big5", "cp950"):
        try:
            return pd.read_csv(path, encoding=enc, dtype=str)
        except Exception as exc:  # pragma: no cover
            last_error = exc
    raise RuntimeError(f"无法读取文件：{path}，最后错误：{last_error}")


def clean_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
    for c in df.columns:
        df[c] = df[c].astype("string").str.strip()
        df[c] = df[c].replace(list(NA_VALUES), pd.NA)
    return df


def pick(df: pd.DataFrame, col: str, default=pd.NA) -> pd.Series:
    if col in df.columns:
        return df[col]
    return pd.Series([default] * len(df), index=df.index, dtype="object")


def to_num(s: pd.Series) -> pd.Series:
    x = s.astype("string").fillna("")
    x = x.str.replace(",", "", regex=False)
    x = x.str.replace("倍", "", regex=False)
    x = x.str.replace("%", "", regex=False)
    x = x.str.replace("超购于", "", regex=False)
    x = x.str.extract(r"([-+]?\d+(?:\.\d+)?)", expand=False)
    return pd.to_numeric(x, errors="coerce")


def to_date(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce").dt.strftime("%Y-%m-%d")


def normalize_code(s: pd.Series) -> pd.Series:
    def one(v):
        if pd.isna(v):
            return pd.NA
        t = str(v).strip().upper()
        if not t:
            return pd.NA
        if t.endswith(".HK"):
            base = t[:-3]
            if base.startswith("H"):
                return f"{base}.HK"
            if base.isdigit():
                return f"{base.zfill(4)}.HK"
            return t
        return t
    return s.map(one)


def first_numeric(*series: pd.Series) -> pd.Series:
    out = pd.Series([pd.NA] * len(series[0]), index=series[0].index, dtype="Float64")
    for s in series:
        n = to_num(s)
        out = out.fillna(n)
    return out


def normalize_master(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_frame(df)
    out = pd.DataFrame(index=df.index)
    out["code"] = normalize_code(pick(df, "p05310_f001"))
    out["name"] = pick(df, "p05310_f002")
    out["listing_date"] = to_date(pick(df, "p05310_f034")).fillna(to_date(pick(df, "p05310_f033")))
    out["prospectus_date"] = to_date(pick(df, "p05310_f003")).fillna(to_date(pick(df, "p05310_f029")))
    out["offer_start_date"] = to_date(pick(df, "p05310_f029"))
    out["offer_end_date"] = to_date(pick(df, "p05310_f030"))
    out["pricing_date"] = to_date(pick(df, "p05310_f031"))
    out["allotment_date"] = to_date(pick(df, "p05310_f032"))
    out["board"] = pick(df, "p05310_f053")
    out["offering_type"] = pick(df, "p05310_f004")
    out["is_latest"] = pick(df, "p05310_f054")
    # 根据样本字段位置：f009/f008通常为招股价区间，f010常为最终价/定价；若尚未定价则为空。
    out["offer_price_low"] = to_num(pick(df, "p05310_f009"))
    out["offer_price_high"] = to_num(pick(df, "p05310_f008"))
    out["issue_price"] = to_num(pick(df, "p05310_f010"))
    out["board_lot"] = to_num(pick(df, "p05310_f011"))
    out["market_cap_hkdm"] = to_num(pick(df, "p05310_f012"))
    out["offer_shares"] = to_num(pick(df, "p05310_f013"))
    out["public_offer_shares"] = to_num(pick(df, "p05310_f015"))
    out["placing_shares"] = to_num(pick(df, "p05310_f017"))
    out["gross_proceeds_hkd"] = to_num(pick(df, "p05310_f023"))
    out["net_proceeds_hkd"] = to_num(pick(df, "p05310_f025"))
    out["proceeds_currency"] = pick(df, "p05310_f039")
    out["use_of_proceeds"] = pick(df, "p05310_f049")
    out["public_subscription_multiple"] = to_num(pick(df, "p05310_f027"))
    out["international_subscription_multiple"] = to_num(pick(df, "p05310_f052"))
    out["valuation_metric"] = to_num(pick(df, "p05310_f050"))
    out["source_table"] = "首发信息一览"
    out = out.dropna(how="all")
    out = out[out["code"].notna() | out["name"].notna()]
    return out


def normalize_ballot(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_frame(df)
    out = pd.DataFrame(index=df.index)
    out["code"] = normalize_code(pick(df, "p04477_f001"))
    out["name"] = pick(df, "p04477_f002")
    out["listing_date"] = to_date(pick(df, "p04477_f003"))
    out["total_applicants"] = to_num(pick(df, "p04477_f004"))
    out["valid_applicants"] = to_num(pick(df, "p04477_f005"))
    out["subscribed_shares"] = to_num(pick(df, "p04477_f012"))
    out["public_subscription_multiple_ballot"] = to_num(pick(df, "p04477_f020"))
    out["one_lot_success_rate_pct"] = to_num(pick(df, "p04477_f021"))
    out["industry_level_1"] = pick(df, "p04477_f022")
    out["industry_level_2"] = pick(df, "p04477_f023")
    out["source_table"] = "IPO打新中签结果"
    out = out[out["code"].notna() | out["name"].notna()]
    return out


def normalize_cornerstone(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = clean_frame(df)
    out = pd.DataFrame(index=df.index)
    out["code"] = normalize_code(pick(df, "p05309_f001"))
    out["name"] = pick(df, "p05309_f002")
    out["listing_date"] = to_date(pick(df, "p05309_f003"))
    out["prospectus_date"] = to_date(pick(df, "p05309_f004"))
    out["cornerstone_flag"] = pick(df, "p05309_f017")
    out["investor_name"] = pick(df, "p05309_f005")
    out["investor_description"] = pick(df, "p05309_f018")
    out["ultimate_owner"] = pick(df, "p05309_f006")
    out["ultimate_owner_description"] = pick(df, "p05309_f019")
    out["invested_amount_hkd"] = to_num(pick(df, "p05309_f008"))
    out["currency"] = pick(df, "p05309_f011")
    out["allocation_pct"] = to_num(pick(df, "p05309_f014"))
    out["lockup_months"] = to_num(pick(df, "p05309_f010"))
    out["lockup_end_date"] = to_date(pick(df, "p05309_f015"))
    out["industry"] = pick(df, "p05309_f012")
    out["sub_industry"] = pick(df, "p05309_f013")
    out["source_table"] = "基石投资者"
    out = out[out["code"].notna() | out["name"].notna()]
    if out.empty:
        summary = pd.DataFrame(columns=["code", "cornerstone_count", "cornerstone_amount_hkd", "cornerstone_top_names", "cornerstone_quality_score"])
    else:
        def top_names(s: pd.Series) -> str:
            vals = [str(x) for x in s.dropna().unique().tolist()[:5]]
            return "；".join(vals)
        def quality(names: pd.Series) -> float:
            text = " ".join(names.dropna().astype(str).tolist()).lower()
            score = 50.0
            strong_words = ["腾讯", "阿里", "京东", "美团", "高瓴", "淡马锡", "temasek", "qatar", "gic", "blackrock", "国资", "政府", "产业", "保险", "银行", "基金"]
            for w in strong_words:
                if w.lower() in text:
                    score += 5
            return min(score, 95.0)
        summary = out.groupby("code", dropna=False).agg(
            name=("name", "first"),
            cornerstone_count=("investor_name", "nunique"),
            cornerstone_amount_hkd=("invested_amount_hkd", "sum"),
            cornerstone_top_names=("investor_name", top_names),
            cornerstone_quality_score=("investor_name", quality),
            lockup_end_date=("lockup_end_date", "max"),
        ).reset_index()
    return out, summary


def normalize_margin(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_frame(df)
    out = pd.DataFrame(index=df.index)
    out["code"] = normalize_code(pick(df, "p05551_f001"))
    out["name"] = pick(df, "jydm_mc")
    out["listing_date"] = to_date(pick(df, "p05551_f002"))
    out["record_date"] = to_date(pick(df, "p05551_f003"))
    out["margin_amount_hkd"] = to_num(pick(df, "p05551_f004"))
    out["public_offer_amount_hkd"] = to_num(pick(df, "p05551_f005"))
    out["margin_multiple"] = to_num(pick(df, "p05551_f006"))
    out["margin_over_text"] = pick(df, "p05551_f007")
    out["currency"] = pick(df, "p05551_f008")
    out["source_table"] = "孖展数据"
    out = out[out["code"].notna() | out["name"].notna()]
    return out


def normalize_underwriters(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_frame(df)
    out = pd.DataFrame(index=df.index)
    out["institution"] = pick(df, "p03412_f001")
    out["code"] = normalize_code(pick(df, "p03412_f002"))
    out["name"] = pick(df, "p03412_f003")
    out["role"] = pick(df, "p03412_f004")
    out["listing_date"] = to_date(pick(df, "p03412_f005"))
    out["participation_pct"] = to_num(pick(df, "p03412_f006"))
    out["industry_level_1"] = pick(df, "p03412_f007")
    out["industry_level_2"] = pick(df, "p03412_f008")
    out["source_table"] = "承销团参与度"
    out = out[out["code"].notna() | out["institution"].notna()]
    return out


def normalize_bookrunners(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_frame(df)
    out = pd.DataFrame(index=df.index)
    out["institution"] = pick(df, "p03414_f001")
    out["code"] = normalize_code(pick(df, "p03414_f002"))
    out["name"] = pick(df, "p03414_f003")
    out["listing_date"] = to_date(pick(df, "p03414_f004"))
    out["issue_price_or_score"] = to_num(pick(df, "p03414_f005"))
    out["industry_level_1"] = pick(df, "p03414_f006")
    out["industry_level_2"] = pick(df, "p03414_f007")
    out["source_table"] = "账簿管理人"
    out = out[out["code"].notna() | out["institution"].notna()]
    return out


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def find_file(input_dir: Path, keywords: list[str]) -> Optional[Path]:
    files = list(input_dir.glob("*.csv"))
    for p in files:
        name = p.name
        if all(k in name for k in keywords):
            return p
    return None


def build(input_dir: str | Path, outdir: str | Path) -> None:
    input_dir = Path(input_dir)
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    inventory = []

    paths = {
        "master": find_file(input_dir, ["首发信息"]),
        "ballot": find_file(input_dir, ["打新", "中签"]),
        "cornerstone": find_file(input_dir, ["基石"]),
        "margin": find_file(input_dir, ["孖展"]),
        "underwriters": find_file(input_dir, ["承销团"]),
        "bookrunners": find_file(input_dir, ["账簿管理"]),
    }

    master = pd.DataFrame()
    ballot = pd.DataFrame()
    cornerstone = pd.DataFrame()
    cs_summary = pd.DataFrame()
    margin = pd.DataFrame()
    underwriters = pd.DataFrame()
    bookrunners = pd.DataFrame()

    if paths["master"]:
        raw = read_csv_smart(paths["master"])
        master = normalize_master(raw)
        write_csv(master, outdir / "ipo_master_ifind_normalized.csv")
        inventory.append(["首发信息一览", str(paths["master"].name), len(raw), len(master), "已接入"])

    if paths["ballot"]:
        raw = read_csv_smart(paths["ballot"])
        ballot = normalize_ballot(raw)
        write_csv(ballot, outdir / "ipo_ballot_results.csv")
        inventory.append(["IPO打新中签结果", str(paths["ballot"].name), len(raw), len(ballot), "已接入"])

    if paths["cornerstone"]:
        raw = read_csv_smart(paths["cornerstone"])
        cornerstone, cs_summary = normalize_cornerstone(raw)
        write_csv(cornerstone, outdir / "ipo_cornerstone_investors.csv")
        write_csv(cs_summary, outdir / "ipo_cornerstone_summary.csv")
        inventory.append(["基石投资者", str(paths["cornerstone"].name), len(raw), len(cornerstone), "已接入"])

    if paths["margin"]:
        raw = read_csv_smart(paths["margin"])
        margin = normalize_margin(raw)
        write_csv(margin, outdir / "ipo_margin_data.csv")
        inventory.append(["孖展数据", str(paths["margin"].name), len(raw), len(margin), "已接入"])

    if paths["underwriters"]:
        raw = read_csv_smart(paths["underwriters"])
        underwriters = normalize_underwriters(raw)
        write_csv(underwriters, outdir / "ipo_underwriter_participation.csv")
        inventory.append(["承销团参与度", str(paths["underwriters"].name), len(raw), len(underwriters), "已接入"])

    if paths["bookrunners"]:
        raw = read_csv_smart(paths["bookrunners"])
        bookrunners = normalize_bookrunners(raw)
        write_csv(bookrunners, outdir / "ipo_bookrunner_details.csv")
        inventory.append(["账簿管理人", str(paths["bookrunners"].name), len(raw), len(bookrunners), "已接入"])

    # App主表：以首发信息为骨架，合并中签、基石、孖展和中介机构。
    if not master.empty:
        pool = master.copy()
        if not ballot.empty:
            keep = ["code", "public_subscription_multiple_ballot", "one_lot_success_rate_pct", "industry_level_1", "industry_level_2", "total_applicants"]
            pool = pool.merge(ballot[[c for c in keep if c in ballot.columns]].drop_duplicates("code"), on="code", how="left")
            pool["public_subscription_multiple"] = pool["public_subscription_multiple"].fillna(pool.get("public_subscription_multiple_ballot"))
        if not cs_summary.empty:
            pool = pool.merge(cs_summary, on="code", how="left", suffixes=("", "_cs"))
        if not margin.empty:
            mg = margin.sort_values("record_date").groupby("code", as_index=False).tail(1)
            pool = pool.merge(mg[["code", "record_date", "margin_amount_hkd", "margin_multiple", "margin_over_text"]], on="code", how="left")
        if not underwriters.empty:
            uw = underwriters.groupby("code").agg(
                underwriter_count=("institution", "nunique"),
                top_underwriters=("institution", lambda s: "；".join(s.dropna().astype(str).unique().tolist()[:5])),
            ).reset_index()
            pool = pool.merge(uw, on="code", how="left")
        if not bookrunners.empty:
            br = bookrunners.groupby("code").agg(
                bookrunner_count=("institution", "nunique"),
                top_bookrunners=("institution", lambda s: "；".join(s.dropna().astype(str).unique().tolist()[:5])),
            ).reset_index()
            pool = pool.merge(br, on="code", how="left")

        today = pd.Timestamp.today().normalize()
        ld = pd.to_datetime(pool["listing_date"], errors="coerce")
        pool["lifecycle_stage"] = "已上市/半新股"
        pool.loc[ld.isna(), "lifecycle_stage"] = "待补上市日"
        pool.loc[ld > today, "lifecycle_stage"] = "招股/待上市"

        # 简化评分：只作为预筛辅助，不替代投委会判断。
        sub = pd.to_numeric(pool.get("public_subscription_multiple"), errors="coerce")
        one = pd.to_numeric(pool.get("one_lot_success_rate_pct"), errors="coerce")
        margin_mult = pd.to_numeric(pool.get("margin_multiple"), errors="coerce")
        cs_quality = pd.to_numeric(pool.get("cornerstone_quality_score"), errors="coerce")
        cs_count = pd.to_numeric(pool.get("cornerstone_count"), errors="coerce")
        book_count = pd.to_numeric(pool.get("bookrunner_count"), errors="coerce")
        under_count = pd.to_numeric(pool.get("underwriter_count"), errors="coerce")
        inter_mult = pd.to_numeric(pool.get("international_subscription_multiple"), errors="coerce")

        score = pd.Series(45.0, index=pool.index)
        score += sub.clip(0, 2000).fillna(0) / 2000 * 18
        score += margin_mult.clip(0, 1000).fillna(0) / 1000 * 10
        score += inter_mult.clip(0, 30).fillna(0) / 30 * 12
        score += cs_quality.fillna(50).sub(50).clip(0, 45) / 45 * 12
        score += cs_count.clip(0, 8).fillna(0) / 8 * 6
        score += book_count.clip(0, 8).fillna(0) / 8 * 4
        score += under_count.clip(0, 12).fillna(0) / 12 * 4
        score -= one.fillna(20).rsub(20).clip(0, 20) / 20 * 3  # 极低中签率提示拥挤，但不大幅扣分
        pool["pre_listing_score"] = score.clip(0, 100).round(1)

        def tier(x: float) -> str:
            if pd.isna(x):
                return "C 等待补数据"
            if x >= 75:
                return "A 高优先"
            if x >= 62:
                return "B 重点观察"
            if x >= 50:
                return "C 等待触发"
            return "D 回避/仅跟踪"
        pool["decision_tier"] = pool["pre_listing_score"].map(tier)

        def rec(row) -> str:
            stg = row.get("lifecycle_stage", "")
            tier_ = row.get("decision_tier", "")
            if "A" in tier_:
                return "一级重点研究；若估值与配售结构合理，可争取额度/锚定，并准备二级回踩买点。"
            if "B" in tier_:
                return "保持交易观察；关注定价、配发结果、暗盘与首日承接，不建议无条件追高。"
            if "C" in tier_:
                return "等待补充字段或价格触发；更适合二级深V/回踩确认后再行动。"
            return "暂不主动参与；仅在明显低估或上市后资金重新进场时复盘。"
        pool["model_recommendation"] = pool.apply(rec, axis=1)

        def tags(row) -> str:
            res = []
            if pd.notna(row.get("public_subscription_multiple")) and row.get("public_subscription_multiple") >= 1000:
                res.append("公开超购极热")
            if pd.notna(row.get("margin_multiple")) and row.get("margin_multiple") >= 500:
                res.append("孖展拥挤")
            if pd.notna(row.get("one_lot_success_rate_pct")) and row.get("one_lot_success_rate_pct") <= 5:
                res.append("一手中签率低")
            if pd.notna(row.get("cornerstone_count")) and row.get("cornerstone_count") >= 5:
                res.append("基石阵容较多")
            if not res:
                res.append("等待更多结构数据")
            return "；".join(res)
        pool["risk_tags"] = pool.apply(tags, axis=1)
        write_csv(pool, outdir / "ipo_decision_pool.csv")

        # 兼容旧版App的A1表/offer表。
        a1 = pool[["code", "name", "listing_date", "prospectus_date", "board", "lifecycle_stage", "decision_tier", "pre_listing_score", "model_recommendation", "risk_tags"]].copy()
        a1 = a1.rename(columns={"code": "stock_code", "name": "issuer_name"})
        write_csv(a1, outdir / "a1_ipo_pipeline.csv")
        offer_cols = ["code", "name", "listing_date", "issue_price", "offer_price_low", "offer_price_high", "public_subscription_multiple", "international_subscription_multiple", "one_lot_success_rate_pct", "cornerstone_count", "cornerstone_amount_hkd", "margin_multiple", "decision_tier", "pre_listing_score"]
        write_csv(pool[[c for c in offer_cols if c in pool.columns]], outdir / "ipo_offer_results.csv")

    # 数据完整度
    expected = [
        "上市申请一览", "首发信息一览", "IPO打新中签结果", "IPO回拨统计", "基石投资者", "首发中介机构/承销团", "账簿管理人", "孖展数据", "IPO暗盘行情", "上市后0-180D行情"
    ]
    inv = pd.DataFrame(inventory, columns=["source_name", "file_name", "raw_rows", "normalized_rows", "status"])
    for e in expected:
        if not inv["source_name"].str.contains(e.split("/")[0], na=False).any():
            inv.loc[len(inv)] = [e, "", 0, 0, "未接入"]
    write_csv(inv, outdir / "data_inventory.csv")
    print(f"Done. Output dir: {outdir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize iFind GUI CSV exports into deploy_data/*.csv")
    parser.add_argument("--input-dir", default="ifind_exports", help="Directory containing iFind CSV exports")
    parser.add_argument("--outdir", default="deploy_data", help="Output directory")
    args = parser.parse_args()
    build(args.input_dir, args.outdir)
