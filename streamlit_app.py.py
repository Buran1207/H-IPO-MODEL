from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

APP_TITLE = "港股 IPO / A1 / 半新股决策驾驶舱"
APP_SUBTITLE = "Step 5 v2：接入 iFind 首发信息、中签结果、基石投资者三张核心结构化表。"
TODAY = pd.Timestamp.today().normalize()

DATA_DIR = Path("deploy_data")
PIPELINE_PATHS = [DATA_DIR / "a1_ipo_pipeline.csv", Path("a1_ipo_pipeline.csv")]
OFFER_PATHS = [DATA_DIR / "ipo_offer_results.csv", Path("ipo_offer_results.csv")]
BALLOT_PATHS = [DATA_DIR / "ipo_ballot_results.csv", Path("ipo_ballot_results.csv")]
CORNERSTONE_DETAIL_PATHS = [DATA_DIR / "ipo_cornerstone_investors.csv", Path("ipo_cornerstone_investors.csv")]
CORNERSTONE_SUMMARY_PATHS = [DATA_DIR / "ipo_cornerstone_summary.csv", Path("ipo_cornerstone_summary.csv")]
INVENTORY_PATHS = [DATA_DIR / "data_inventory.csv", Path("data_inventory.csv")]
LISTED_PATHS = [DATA_DIR / "hk_ipo_scored_public.csv", Path("hk_ipo_scored_public.csv")]

DATE_COLS = [
    "application_date", "a1_date", "application_status_update_date", "hearing_date", "prospectus_date",
    "offer_start_date", "offer_end_date", "pricing_date", "allotment_result_date", "expected_listing_date",
    "listing_date", "cornerstone_lockup_end_date",
]
PCT_COLS = ["one_lot_success_rate", "clawback_ratio", "cornerstone_ratio", "final_price_position", "gray_ret"]
MONEY_COLS = ["fundraising_amount_hkd", "market_cap_at_ipo_hkd", "net_proceeds_hkd", "cornerstone_amount_hkd"]

DISPLAY = {
    "decision_tier": "决策层", "security_key": "主键", "temp_code": "临时代码", "code": "正式代码", "name": "简称", "issuer_name": "发行人",
    "lifecycle_stage": "阶段", "application_date": "申请日", "a1_date": "首次申请日", "application_status": "申请状态",
    "hearing_date": "聆讯日", "prospectus_date": "招股书日", "offer_start_date": "招股开始", "offer_end_date": "招股截止",
    "pricing_date": "定价日", "allotment_result_date": "配发结果日", "expected_listing_date": "预计上市日", "listing_date": "上市日",
    "days_since_listing": "上市天数", "board": "板块", "industry": "行业", "sub_industry": "子行业",
    "offer_price_low": "招股价下限", "offer_price_high": "招股价上限", "issue_price": "发行价", "final_price_position": "定价位置",
    "board_lot": "每手股数", "fundraising_amount_hkd": "募资额", "market_cap_at_ipo_hkd": "发行市值", "net_proceeds_hkd": "所得款净额", "issue_pe": "发行PE",
    "public_subscription_multiple": "公开认购倍数", "international_subscription_multiple": "国际配售倍数", "one_lot_success_rate": "一手中签率", "clawback_ratio": "回拨比例",
    "cornerstone_names": "基石投资者", "cornerstone_investor_count": "基石数", "cornerstone_amount_hkd": "基石金额", "cornerstone_ratio": "基石占比",
    "cornerstone_lockup_months": "基石锁定月", "cornerstone_lockup_end_date": "基石解禁日", "cornerstone_quality_tags": "基石标签",
    "sponsor_names": "保荐人", "overall_coordinator_names": "整体协调人", "proceeds_use": "募资用途",
    "primary_signal": "发行信号", "primary_action": "模型建议", "data_completeness_score": "资料完整度", "next_data_action": "下一步数据动作", "source_files": "来源文件",
}

REQUIRED_DATASETS = {
    "首发信息一览": "已接入：发行价区间、发行价、上市日、募资额、认购倍数、募资用途等",
    "IPO打新中签结果": "已接入：公开认购倍数、一手中签率、行业、打新热度字段",
    "基石投资者": "已接入：基石名单、金额、占比、锁定期、投资者描述",
    "上市申请一览": "未上传：A1/临时代码/申请状态/聆讯日期，决定能否覆盖未招股公司",
    "首发中介机构": "未上传：保荐人、整体协调人、账簿管理人，用于保荐人胜率与承销质量",
    "IPO回拨统计": "未上传：可补充/校验回拨比例",
    "孖展数据": "未上传：招股期资金拥挤度与散户情绪",
    "IPO暗盘行情": "未上传：上市前交易情绪，首日卖点/买点重要输入",
    "上市后0-180D行情": "未接入：半新股二级买卖点、路径标签、回测必须补",
}


def find_path(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


@st.cache_data(show_spinner=False)
def load_csv(paths: list[Path]) -> tuple[pd.DataFrame, str]:
    path = find_path(paths)
    if path is None:
        return pd.DataFrame(), "未找到"
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except pd.errors.EmptyDataError:
        return pd.DataFrame(), str(path)
    for c in DATE_COLS:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df, str(path)


def clean_text(x: Any) -> str:
    if pd.isna(x):
        return ""
    s = str(x).strip()
    return "" if s.lower() in {"nan", "none", "null"} or s in {"--", "-", "—"} else s


def fmt_date(x: Any) -> str:
    if pd.isna(x):
        return ""
    try:
        return pd.to_datetime(x).strftime("%Y-%m-%d")
    except Exception:
        return clean_text(x)


def fmt_num(x: Any, digits: int = 2) -> str:
    if pd.isna(x):
        return ""
    try:
        return f"{float(x):,.{digits}f}"
    except Exception:
        return clean_text(x)


def fmt_pct(x: Any) -> str:
    if pd.isna(x):
        return ""
    try:
        return f"{float(x):.1%}"
    except Exception:
        return clean_text(x)


def fmt_money(x: Any) -> str:
    if pd.isna(x):
        return ""
    try:
        v = float(x)
        if abs(v) >= 1e9:
            return f"{v / 1e9:,.2f} 十亿HKD"
        if abs(v) >= 1e8:
            return f"{v / 1e8:,.2f} 亿HKD"
        if abs(v) >= 1e4:
            return f"{v / 1e4:,.2f} 万HKD"
        return f"{v:,.0f} HKD"
    except Exception:
        return clean_text(x)


def prepare_master(master: pd.DataFrame) -> pd.DataFrame:
    if master.empty:
        return master
    df = master.copy()
    if "listing_date" in df.columns:
        df["days_since_listing"] = (TODAY - df["listing_date"]).dt.days
    else:
        df["days_since_listing"] = pd.NA
    if "data_completeness_score" not in df.columns:
        df["data_completeness_score"] = pd.NA
    df["decision_tier"] = df.apply(decision_tier, axis=1)
    return df


def decision_tier(row: pd.Series) -> str:
    stage = clean_text(row.get("lifecycle_stage"))
    score = row.get("data_completeness_score")
    pub = row.get("public_subscription_multiple")
    one = row.get("one_lot_success_rate")
    cs = row.get("cornerstone_ratio")
    fp = row.get("final_price_position")
    if stage in {"A1/递表", "已聆讯/待招股"}:
        return "C 建档跟踪"
    if pd.notna(score) and score < 0.35:
        return "C 数据不足"
    positives = 0
    risks = 0
    if pd.notna(pub):
        if pub >= 50:
            positives += 1
        if pub >= 1000:
            risks += 1
    if pd.notna(one) and one <= 0.2:
        positives += 1
    if pd.notna(cs):
        if 0.05 <= cs <= 0.55:
            positives += 1
        if cs > 0.65:
            risks += 1
    if pd.notna(fp):
        if fp <= 0.65:
            positives += 1
        if fp >= 0.95:
            risks += 1
    if risks >= 2:
        return "D 谨慎/回避"
    if positives >= 3:
        return "A 重点研究"
    if positives >= 2:
        return "B 交易观察"
    return "C 等触发"


def filter_df(df: pd.DataFrame, stages: list[str], tiers: list[str], industries: list[str], search: str) -> pd.DataFrame:
    out = df.copy()
    if stages and "lifecycle_stage" in out.columns:
        out = out[out["lifecycle_stage"].isin(stages)]
    if tiers and "decision_tier" in out.columns:
        out = out[out["decision_tier"].isin(tiers)]
    if industries and "industry" in out.columns:
        out = out[out["industry"].fillna("").isin(industries)]
    if search:
        s = search.strip().upper()
        mask = pd.Series(False, index=out.index)
        for c in ["code", "temp_code", "name", "issuer_name", "cornerstone_names", "sponsor_names"]:
            if c in out.columns:
                mask |= out[c].astype(str).str.upper().str.contains(s, na=False, regex=False)
        out = out[mask]
    return out


def format_table(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    available = [c for c in cols if c in df.columns]
    table = df[available].copy()
    for c in table.columns:
        if c in DATE_COLS or c == "listing_date":
            table[c] = table[c].map(fmt_date)
        elif c in PCT_COLS:
            table[c] = table[c].map(fmt_pct)
        elif c in MONEY_COLS:
            table[c] = table[c].map(fmt_money)
        elif c.endswith("multiple") or c in {"public_subscription_multiple", "international_subscription_multiple", "issue_pe"}:
            table[c] = table[c].map(lambda x: fmt_num(x, 2))
        elif c == "data_completeness_score":
            table[c] = table[c].map(fmt_pct)
    return table.rename(columns={c: DISPLAY.get(c, c) for c in table.columns})


def memo_markdown(row: pd.Series) -> str:
    name = clean_text(row.get("name")) or clean_text(row.get("issuer_name"))
    code = clean_text(row.get("code")) or clean_text(row.get("temp_code"))
    lines = [
        f"# {name} {code} IPO/半新股投资备忘录",
        "",
        f"- 阶段：{clean_text(row.get('lifecycle_stage'))}",
        f"- 决策层：{clean_text(row.get('decision_tier'))}",
        f"- 模型建议：{clean_text(row.get('primary_action'))}",
        f"- 发行信号：{clean_text(row.get('primary_signal'))}",
        "",
        "## 发行结构",
        f"- 招股价区间：{fmt_num(row.get('offer_price_low'))} - {fmt_num(row.get('offer_price_high'))}",
        f"- 发行价：{fmt_num(row.get('issue_price'))}",
        f"- 定价位置：{fmt_pct(row.get('final_price_position'))}",
        f"- 募资额：{fmt_money(row.get('fundraising_amount_hkd'))}",
        f"- 发行市值：{fmt_money(row.get('market_cap_at_ipo_hkd'))}",
        f"- 公开认购倍数：{fmt_num(row.get('public_subscription_multiple'))}",
        f"- 国际配售倍数：{fmt_num(row.get('international_subscription_multiple'))}",
        f"- 一手中签率：{fmt_pct(row.get('one_lot_success_rate'))}",
        "",
        "## 基石与锁定",
        f"- 基石数量：{fmt_num(row.get('cornerstone_investor_count'), 0)}",
        f"- 基石金额：{fmt_money(row.get('cornerstone_amount_hkd'))}",
        f"- 基石占比：{fmt_pct(row.get('cornerstone_ratio'))}",
        f"- 基石标签：{clean_text(row.get('cornerstone_quality_tags'))}",
        f"- 基石解禁日：{fmt_date(row.get('cornerstone_lockup_end_date'))}",
        f"- 基石名单：{clean_text(row.get('cornerstone_names'))[:1500]}",
        "",
        "## 后续动作",
        f"- {clean_text(row.get('next_data_action'))}",
        "",
        "## 募资用途",
        clean_text(row.get("proceeds_use"))[:2000],
    ]
    return "\n".join(lines)


st.set_page_config(page_title="港股IPO决策驾驶舱", layout="wide")
st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

master_raw, master_source = load_csv(PIPELINE_PATHS)
offers, offer_source = load_csv(OFFER_PATHS)
ballot, ballot_source = load_csv(BALLOT_PATHS)
cs_detail, cs_detail_source = load_csv(CORNERSTONE_DETAIL_PATHS)
cs_summary, cs_summary_source = load_csv(CORNERSTONE_SUMMARY_PATHS)
inventory, inventory_source = load_csv(INVENTORY_PATHS)
listed, listed_source = load_csv(LISTED_PATHS)

if master_raw.empty:
    st.error("没有找到 deploy_data/a1_ipo_pipeline.csv。请先运行 scripts/ingest_ifind_gui_exports.py。")
    st.stop()

master = prepare_master(master_raw)

with st.sidebar:
    st.success(f"主表：{master_source}")
    st.caption(f"样本：{len(master)} | 基石明细：{len(cs_detail)} | 中签：{len(ballot)}")
    st.divider()
    stages = sorted([x for x in master.get("lifecycle_stage", pd.Series(dtype=str)).dropna().unique() if clean_text(x)])
    tiers = sorted([x for x in master.get("decision_tier", pd.Series(dtype=str)).dropna().unique() if clean_text(x)])
    industries = sorted([x for x in master.get("industry", pd.Series(dtype=str)).dropna().unique() if clean_text(x)])
    selected_stages = st.multiselect("阶段", stages, default=stages)
    selected_tiers = st.multiselect("决策层", tiers, default=tiers)
    selected_industries = st.multiselect("行业", industries, default=[])
    search = st.text_input("代码/简称/基石/保荐人搜索", "")

view = filter_df(master, selected_stages, selected_tiers, selected_industries, search)

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("总样本", len(master))
m2.metric("当前筛选", len(view))
m3.metric("已定价/待上市", int(master["lifecycle_stage"].astype(str).str.contains("待上市|配发", na=False).sum()))
m4.metric("0-180D", int(master["lifecycle_stage"].astype(str).str.contains("0-180", na=False).sum()))
m5.metric("有中签", int(master.get("one_lot_success_rate", pd.Series(index=master.index)).notna().sum()))
m6.metric("有基石", int(master.get("cornerstone_names", pd.Series(index=master.index)).map(clean_text).ne("").sum()))

page = st.tabs(["① 全生命周期池", "② 中签/热度", "③ 基石投资者", "④ 单票 Memo", "⑤ 数据完整度", "⑥ 下一步"])

with page[0]:
    st.subheader("优先级列表")
    cols = [
        "decision_tier", "code", "temp_code", "name", "lifecycle_stage", "listing_date", "industry",
        "issue_price", "public_subscription_multiple", "one_lot_success_rate", "cornerstone_ratio",
        "cornerstone_quality_tags", "primary_signal", "primary_action", "data_completeness_score", "next_data_action",
    ]
    sort_options = [c for c in ["listing_date", "data_completeness_score", "public_subscription_multiple", "cornerstone_ratio"] if c in view.columns]
    sort_col = st.selectbox("排序字段", sort_options, index=0 if sort_options else None)
    ascending = st.toggle("升序", value=False)
    table_view = view.sort_values(sort_col, ascending=ascending, na_position="last") if sort_col else view
    st.dataframe(format_table(table_view, cols), use_container_width=True, hide_index=True, height=520)
    st.download_button("下载当前筛选 CSV", view.to_csv(index=False, encoding="utf-8-sig"), file_name="hk_ipo_filtered.csv", mime="text/csv")

with page[1]:
    st.subheader("IPO 打新中签 / 公开发售热度")
    if ballot.empty:
        st.warning("未找到 ipo_ballot_results.csv。")
    else:
        top_cols = ["code", "name", "allotment_result_date", "public_subscription_multiple", "one_lot_success_rate", "industry", "sub_industry"]
        b = ballot.copy()
        if "public_subscription_multiple" in b.columns:
            b = b.sort_values("public_subscription_multiple", ascending=False, na_position="last")
        st.dataframe(format_table(b.head(100), top_cols), use_container_width=True, hide_index=True, height=420)
        c1, c2 = st.columns(2)
        with c1:
            if "public_subscription_multiple" in ballot.columns:
                st.write("公开认购倍数 Top 20")
                chart = ballot.dropna(subset=["public_subscription_multiple"]).sort_values("public_subscription_multiple", ascending=False).head(20)
                st.bar_chart(chart.set_index("name")["public_subscription_multiple"])
        with c2:
            if "one_lot_success_rate" in ballot.columns:
                st.write("一手中签率最低 Top 20")
                chart = ballot.dropna(subset=["one_lot_success_rate"]).sort_values("one_lot_success_rate", ascending=True).head(20)
                st.bar_chart(chart.set_index("name")["one_lot_success_rate"])

with page[2]:
    st.subheader("基石投资者：汇总与明细")
    if cs_summary.empty:
        st.warning("未找到 ipo_cornerstone_summary.csv。")
    else:
        cs_cols = ["code", "name", "listing_date", "industry", "cornerstone_investor_count", "cornerstone_amount_hkd", "cornerstone_ratio", "cornerstone_lockup_end_date", "cornerstone_quality_tags", "cornerstone_names"]
        cs_view = cs_summary.copy()
        if "cornerstone_amount_hkd" in cs_view.columns:
            cs_view = cs_view.sort_values("cornerstone_amount_hkd", ascending=False, na_position="last")
        st.dataframe(format_table(cs_view, cs_cols), use_container_width=True, hide_index=True, height=420)
        if not cs_detail.empty:
            st.caption("明细表用于核查单个基石投资者、背景、控制人和锁定期。")
            detail_cols = ["code", "name", "cornerstone_name", "cornerstone_controller_or_manager", "cornerstone_amount_hkd", "cornerstone_ratio", "cornerstone_lockup_months", "cornerstone_lockup_end_date", "industry"]
            st.dataframe(format_table(cs_detail.head(300), detail_cols), use_container_width=True, hide_index=True, height=360)

with page[3]:
    st.subheader("单票 Memo")
    labels = []
    for _, r in view.iterrows():
        labels.append(f"{clean_text(r.get('code')) or clean_text(r.get('temp_code'))} {clean_text(r.get('name')) or clean_text(r.get('issuer_name'))}")
    selected = st.selectbox("选择股票", labels)
    if selected:
        key = selected.split()[0]
        row = view[(view.get("code", pd.Series(dtype=str)).astype(str) == key) | (view.get("temp_code", pd.Series(dtype=str)).astype(str) == key)].iloc[0]
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("决策层", clean_text(row.get("decision_tier")))
        k2.metric("发行价", fmt_num(row.get("issue_price")))
        k3.metric("公开认购", fmt_num(row.get("public_subscription_multiple")))
        k4.metric("一手中签", fmt_pct(row.get("one_lot_success_rate")))
        k5.metric("基石占比", fmt_pct(row.get("cornerstone_ratio")))
        st.info(clean_text(row.get("primary_action")) or "暂无建议")
        memo = memo_markdown(row)
        st.markdown(memo)
        st.download_button("下载该票 Memo.md", memo, file_name=f"{key}_ipo_memo.md", mime="text/markdown")

with page[4]:
    st.subheader("数据完整度与缺口")
    if not inventory.empty:
        st.write("已接入文件")
        st.dataframe(inventory, use_container_width=True, hide_index=True)
    status_rows = []
    joined_files = " ".join(inventory.get("file", pd.Series(dtype=str)).astype(str).tolist()) if not inventory.empty else ""
    for ds, note in REQUIRED_DATASETS.items():
        ok = any(k in joined_files for k in [ds, ds.replace("IPO", ""), "首发信息" if ds == "首发信息一览" else ds])
        if ds == "上市后0-180D行情" and not listed.empty:
            ok = True
        status_rows.append({"数据源": ds, "状态": "已接入" if ok else "缺失/待接入", "说明": note})
    st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)
    st.write("字段覆盖率 Top/Bottom")
    coverage_cols = ["code", "name", "lifecycle_stage", "data_completeness_score", "next_data_action", "source_files"]
    st.dataframe(format_table(master.sort_values("data_completeness_score", ascending=True).head(50), coverage_cols), use_container_width=True, hide_index=True)

with page[5]:
    st.subheader("下一步路线")
    st.markdown(
        """
### 当前判断
数据源**还没有完整**，但 Step 5 v2 已经具备发行结构层的主干：首发信息 + 中签结果 + 基石投资者。

### 最高优先级补数
1. **上市申请一览**：解决 A1/临时代码/未招股公司的覆盖，这是你前面强调的阶段。
2. **上市后 0-180D 行情**：解决半新股二级买卖点、深 V、升后破发、止盈止损。
3. **首发中介机构**：解决保荐人、整体协调人、承销质量评分。
4. **孖展与暗盘行情**：解决招股期资金拥挤度与上市前情绪。
5. **IPO回拨统计**：作为回拨比例独立校验表。

### 本地更新命令
```bash
python scripts/ingest_ifind_gui_exports.py --input-dir ifind_exports --outdir deploy_data
```

把新的 iFind 导出文件放入 `ifind_exports/`，运行后上传 `deploy_data/*.csv` 到 GitHub 即可。
        """
    )
