from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st

APP_TITLE = "港股 IPO / 半新股决策驾驶舱"
DATA_DIR = Path("deploy_data")

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")


@st.cache_data(show_spinner=False)
def read_csv_smart(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()
    last_error = None
    for enc in ("utf-8-sig", "utf-8", "gb18030", "gbk", "big5", "cp950"):
        try:
            df = pd.read_csv(path, encoding=enc)
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except Exception as exc:
            last_error = exc
    st.error(f"无法读取数据文件：{path}；最后错误：{last_error}")
    return pd.DataFrame()


def to_datetime_series(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce")


def to_numeric_series(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def fmt_pct(x, digits: int = 1) -> str:
    if pd.isna(x):
        return "--"
    try:
        return f"{float(x):.{digits}f}%"
    except Exception:
        return str(x)


def fmt_num(x, digits: int = 1) -> str:
    if pd.isna(x):
        return "--"
    try:
        return f"{float(x):,.{digits}f}"
    except Exception:
        return str(x)


def available_cols(df: pd.DataFrame, cols: Iterable[str]) -> list[str]:
    return [c for c in cols if c in df.columns]


def rename_for_display(df: pd.DataFrame) -> pd.DataFrame:
    cn = {
        "code": "代码", "stock_code": "代码", "temp_code": "临时代码", "name": "简称", "issuer_name": "发行人",
        "listing_date": "上市日", "application_date": "申请日", "first_application_date": "首次申请日", "application_status": "申请状态", "status_update_date": "状态更新日", "hearing_date": "聆讯日",
        "prospectus_date": "招股书/招股日", "offer_start_date": "招股开始", "offer_end_date": "招股结束", "pricing_date": "定价日", "allotment_date": "配发/中签日",
        "board": "板块", "offering_type": "发行方式", "issue_price": "发行价", "offer_price_low": "招股价低", "offer_price_high": "招股价高", "board_lot": "每手股数",
        "market_cap_hkdm": "上市市值/HKD mn", "gross_proceeds_hkd": "募资总额/HKD", "net_proceeds_hkd": "募资净额/HKD",
        "public_subscription_multiple": "公开认购倍数", "international_subscription_multiple": "国际配售倍数", "one_lot_success_rate_pct": "一手中签率%", "total_applicants": "认购人数",
        "margin_multiple": "孖展倍数", "margin_amount_hkd": "孖展额/HKD", "margin_over_text": "孖展状态",
        "gray_date": "暗盘日", "gray_open_ret_pct": "暗盘开盘%", "gray_close_ret_pct": "暗盘收盘%", "gray_amount_10k_hkd": "暗盘成交额/万元", "d1_open_ret_pct": "首日开盘%", "d1_close_ret_pct": "首日收盘%",
        "cornerstone_count": "基石数", "cornerstone_amount_hkd": "基石金额/HKD", "cornerstone_top_names": "主要基石", "cornerstone_quality_score": "基石质量分",
        "underwriter_count": "承销机构数", "bookrunner_count": "账簿管理人数", "top_underwriters": "主要承销机构", "top_bookrunners": "主要账簿管理人",
        "sponsor": "保荐人", "overall_coordinator": "整体协调人", "lifecycle_stage": "阶段", "pre_listing_score": "发行前评分", "decision_tier": "决策层级", "model_recommendation": "模型建议", "risk_tags": "标签",
        "use_of_proceeds": "募资用途", "business_scope": "经营范围", "company_profile": "公司简介", "industry_level_1": "一级行业", "industry_level_2": "二级行业",
        "investor_name": "投资者", "invested_amount_hkd": "投资金额/HKD", "lockup_end_date": "锁定到期日", "institution": "机构", "role": "角色", "participation_pct": "参与度%",
        "date": "日期", "open": "开盘", "high": "最高", "low": "最低", "close": "收盘", "volume": "成交量", "amount_est_hkd": "估算成交额/HKD", "source": "来源",
        "max_20_ret_pct": "20D最大涨幅%", "min_20_ret_pct": "20D最大回撤%", "max_60_ret_pct": "60D最大涨幅%", "min_60_ret_pct": "60D最大回撤%", "max_180_ret_pct": "180D最大涨幅%", "path_label": "路径", "secondary_signal": "二级信号",
        "source_name": "数据源", "file_name": "文件名", "raw_rows": "原始行数", "normalized_rows": "标准化行数", "status": "状态",
    }
    return df.rename(columns={k: v for k, v in cn.items() if k in df.columns})


@st.cache_data(show_spinner=False)
def load_all() -> dict[str, pd.DataFrame]:
    files = {
        "pool": "ipo_decision_pool.csv", "master": "ipo_master_ifind_normalized.csv", "applications": "ipo_listing_applications.csv",
        "ballot": "ipo_ballot_results.csv", "cornerstone": "ipo_cornerstone_investors.csv", "cornerstone_summary": "ipo_cornerstone_summary.csv", "margin": "ipo_margin_data.csv",
        "dark": "ipo_dark_pool.csv", "underwriters": "ipo_underwriter_participation.csv", "bookrunners": "ipo_bookrunner_details.csv", "inventory": "data_inventory.csv", "offer": "ipo_offer_results.csv",
        "quotes": "ipo_daily_quotes_180d.csv", "paths": "ipo_post_listing_paths.csv",
    }
    data = {k: read_csv_smart(DATA_DIR / v) for k, v in files.items()}
    for _, df in data.items():
        if df.empty:
            continue
        for col in ["listing_date", "application_date", "first_application_date", "status_update_date", "hearing_date", "prospectus_date", "offer_start_date", "offer_end_date", "pricing_date", "allotment_date", "record_date", "lockup_end_date", "gray_date", "date"]:
            if col in df.columns:
                df[col] = to_datetime_series(df[col])
    return data


def make_filtered_pool(pool: pd.DataFrame) -> pd.DataFrame:
    view = pool.copy()
    if "listing_date" in view.columns:
        dates = to_datetime_series(view["listing_date"])
        if dates.notna().any():
            min_date = dates.min().date(); max_date = dates.max().date()
            selected_range = st.sidebar.date_input("上市日期区间", value=(min_date, max_date), min_value=min_date, max_value=max_date)
            if isinstance(selected_range, tuple) and len(selected_range) == 2:
                start, end = selected_range
                view = view[(dates.isna()) | ((dates.dt.date >= start) & (dates.dt.date <= end))]
    for col, label in [("lifecycle_stage", "阶段"), ("decision_tier", "决策层级"), ("board", "板块"), ("industry_level_1", "行业")]:
        if col in view.columns:
            options = sorted([x for x in view[col].dropna().astype(str).unique() if x and x != "nan"])
            selected = st.sidebar.multiselect(label, options, default=options)
            if selected:
                view = view[view[col].astype(str).isin(selected)]
    if "pre_listing_score" in view.columns:
        min_score = st.sidebar.slider("最低发行前评分", 0.0, 100.0, 0.0, 1.0)
        view = view[to_numeric_series(view["pre_listing_score"]).fillna(0) >= min_score]
    if "name" in view.columns and "code" in view.columns:
        q = st.sidebar.text_input("搜索代码/名称")
        if q:
            q = q.strip().lower()
            view = view[view["code"].astype(str).str.lower().str.contains(q, na=False) | view["name"].astype(str).str.lower().str.contains(q, na=False)]
    return view


def page_dashboard(pool: pd.DataFrame) -> None:
    st.header("① 全生命周期投资池")
    st.caption("已接入A1上市申请、首发结构、中签、基石、孖展、承销团、账簿管理人、暗盘。0-180D行情可通过免费脚本生成。")
    view = make_filtered_pool(pool)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("样本数", len(view))
    c2.metric("A1预研", int(view.get("lifecycle_stage", pd.Series(dtype=str)).astype(str).str.contains("A1", na=False).sum()))
    c3.metric("A/B优先", int(view.get("decision_tier", pd.Series(dtype=str)).astype(str).str.contains("A 高|B", regex=True, na=False).sum()))
    c4.metric("平均评分", "--" if view.empty or "pre_listing_score" not in view.columns else f"{to_numeric_series(view['pre_listing_score']).mean():.1f}")
    c5.metric("有暗盘", int(to_numeric_series(view.get("gray_close_ret_pct", pd.Series(dtype=float))).notna().sum()))
    c6.metric("有基石", int(to_numeric_series(view.get("cornerstone_count", pd.Series(dtype=float))).fillna(0).gt(0).sum()))

    cols = ["decision_tier", "code", "name", "listing_date", "application_date", "application_status", "lifecycle_stage", "industry_level_1", "issue_price", "public_subscription_multiple", "one_lot_success_rate_pct", "margin_multiple", "gray_close_ret_pct", "d1_close_ret_pct", "cornerstone_count", "pre_listing_score", "risk_tags", "model_recommendation"]
    table = view.sort_values("pre_listing_score" if "pre_listing_score" in view.columns else "listing_date", ascending=False)
    table = table[available_cols(table, cols)].copy()
    st.dataframe(rename_for_display(table), use_container_width=True, hide_index=True, height=540)
    st.download_button("下载当前筛选结果 CSV", data=table.to_csv(index=False, encoding="utf-8-sig"), file_name="ipo_filtered_pool.csv", mime="text/csv")

    left, right = st.columns(2)
    with left:
        st.subheader("决策层级分布")
        if "decision_tier" in view.columns:
            st.bar_chart(view["decision_tier"].value_counts())
    with right:
        st.subheader("生命周期分布")
        if "lifecycle_stage" in view.columns:
            st.bar_chart(view["lifecycle_stage"].value_counts())


def page_a1(applications: pd.DataFrame, pool: pd.DataFrame) -> None:
    st.header("② A1 / 上市申请池")
    st.caption("这是未上市、临时代码、处理中公司的预研池。这个阶段不做买卖结论，只做行业、保荐人、上市进度和资料完整度筛选。")
    if applications.empty:
        st.warning("尚未接入 ipo_listing_applications.csv。")
        return
    view = applications.copy()
    q = st.text_input("搜索A1公司/临时代码")
    if q:
        q = q.lower().strip()
        view = view[view["code"].astype(str).str.lower().str.contains(q, na=False) | view["name"].astype(str).str.lower().str.contains(q, na=False)]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("申请样本", len(view))
    c2.metric("处理中", int(view.get("application_status", pd.Series(dtype=str)).astype(str).str.contains("处理", na=False).sum()))
    c3.metric("有保荐人", int(view.get("sponsor", pd.Series(dtype=str)).notna().sum()))
    c4.metric("有行业", int(view.get("industry_level_2", pd.Series(dtype=str)).notna().sum()))
    cols = ["code", "name", "application_date", "application_status", "hearing_date", "listing_date", "board", "sponsor", "overall_coordinator", "industry_level_1", "industry_level_2", "business_scope"]
    st.dataframe(rename_for_display(view[available_cols(view, cols)]), use_container_width=True, hide_index=True, height=560)


def page_heat(pool: pd.DataFrame, ballot: pd.DataFrame, margin: pd.DataFrame) -> None:
    st.header("③ 打新 / 孖展热度")
    st.caption("公开认购倍数、一手中签率和孖展倍数用于判断拥挤交易，而不是简单越热越买。")
    view = pool.copy()
    cols = ["code", "name", "listing_date", "public_subscription_multiple", "one_lot_success_rate_pct", "total_applicants", "margin_multiple", "margin_amount_hkd", "margin_over_text", "decision_tier", "pre_listing_score"]
    if "public_subscription_multiple" in view.columns:
        view = view.sort_values("public_subscription_multiple", ascending=False, na_position="last")
    st.dataframe(rename_for_display(view[available_cols(view, cols)]), use_container_width=True, hide_index=True, height=520)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("公开认购倍数 Top 20")
        if "public_subscription_multiple" in view.columns:
            st.bar_chart(view[["name", "public_subscription_multiple"]].dropna().head(20).set_index("name"))
    with c2:
        st.subheader("孖展倍数 Top 20")
        if "margin_multiple" in view.columns:
            st.bar_chart(view[["name", "margin_multiple"]].dropna().sort_values("margin_multiple", ascending=False).head(20).set_index("name"))


def page_dark(dark: pd.DataFrame, pool: pd.DataFrame) -> None:
    st.header("④ 暗盘 / 首日信号")
    st.caption("暗盘不是结论，而是首日交易前最后一次市场投票。暗盘强但首日低走、暗盘弱且首日破发，都要降低追高意愿。")
    if dark.empty:
        st.warning("尚未接入 ipo_dark_pool.csv。")
        return
    cols = ["code", "name", "allotment_date", "gray_date", "listing_date", "issue_price", "gray_open_ret_pct", "gray_close_ret_pct", "gray_high", "gray_low", "gray_amount_10k_hkd", "d1_open_ret_pct", "d1_close_ret_pct"]
    view = dark[available_cols(dark, cols)].copy()
    if "gray_close_ret_pct" in view.columns:
        view = view.sort_values("gray_close_ret_pct", ascending=False, na_position="last")
    st.dataframe(rename_for_display(view), use_container_width=True, hide_index=True, height=520)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("暗盘收盘涨幅 Top 20")
        if "gray_close_ret_pct" in view.columns:
            st.bar_chart(view[["name", "gray_close_ret_pct"]].dropna().head(20).set_index("name"))
    with c2:
        st.subheader("首日收盘涨幅 Top 20")
        if "d1_close_ret_pct" in view.columns:
            st.bar_chart(view[["name", "d1_close_ret_pct"]].dropna().sort_values("d1_close_ret_pct", ascending=False).head(20).set_index("name"))


def page_cornerstone(pool: pd.DataFrame, cornerstone: pd.DataFrame) -> None:
    st.header("⑤ 基石投资者")
    cols = ["code", "name", "listing_date", "cornerstone_count", "cornerstone_amount_hkd", "cornerstone_quality_score", "cornerstone_top_names", "lockup_end_date", "decision_tier", "pre_listing_score"]
    view = pool[available_cols(pool, cols)].copy()
    if "cornerstone_amount_hkd" in view.columns:
        view = view.sort_values("cornerstone_amount_hkd", ascending=False, na_position="last")
    st.dataframe(rename_for_display(view), use_container_width=True, hide_index=True, height=480)
    with st.expander("基石投资者明细"):
        detail_cols = ["code", "name", "listing_date", "investor_name", "ultimate_owner", "invested_amount_hkd", "allocation_pct", "lockup_months", "lockup_end_date", "industry"]
        st.dataframe(rename_for_display(cornerstone[available_cols(cornerstone, detail_cols)]), use_container_width=True, hide_index=True, height=460)


def page_secondary(paths: pd.DataFrame, quotes: pd.DataFrame) -> None:
    st.header("⑥ 上市后0-180D / 半新股状态机")
    if paths.empty:
        st.warning("还没有 ipo_post_listing_paths.csv。请本地运行免费行情脚本后再生成路径标签。")
        st.code("python scripts/fetch_free_hk_quotes_180d.py\npython scripts/build_post_listing_paths.py --update-pool", language="bash")
        st.info("免费源通常没有真实成交额，脚本会用典型价*成交量估算成交额；正式投研时可用券商或付费行情替换。")
    else:
        st.dataframe(rename_for_display(paths), use_container_width=True, hide_index=True, height=520)
        if "path_label" in paths.columns:
            st.subheader("路径分布")
            st.bar_chart(paths["path_label"].value_counts())
    with st.expander("已抓取的日行情样本"):
        st.dataframe(rename_for_display(quotes.head(2000)), use_container_width=True, hide_index=True, height=360)


def page_intermediaries(underwriters: pd.DataFrame, bookrunners: pd.DataFrame) -> None:
    st.header("⑦ 中介机构 / 账簿管理人")
    tab1, tab2, tab3 = st.tabs(["承销团明细", "账簿管理人", "机构参与统计"])
    with tab1:
        st.dataframe(rename_for_display(underwriters), use_container_width=True, hide_index=True, height=520)
    with tab2:
        st.dataframe(rename_for_display(bookrunners), use_container_width=True, hide_index=True, height=520)
    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            if not underwriters.empty and "institution" in underwriters.columns:
                st.dataframe(underwriters["institution"].value_counts().reset_index().rename(columns={"institution": "机构", "count": "次数"}), use_container_width=True, hide_index=True)
        with c2:
            if not bookrunners.empty and "institution" in bookrunners.columns:
                st.dataframe(bookrunners["institution"].value_counts().reset_index().rename(columns={"institution": "机构", "count": "次数"}), use_container_width=True, hide_index=True)


def page_memo(pool: pd.DataFrame, cornerstone: pd.DataFrame, margin: pd.DataFrame, underwriters: pd.DataFrame, bookrunners: pd.DataFrame, dark: pd.DataFrame, paths: pd.DataFrame) -> None:
    st.header("⑧ 单票投资 Memo")
    if pool.empty or "code" not in pool.columns:
        st.warning("没有可用主表数据。")
        return
    label = pool["code"].astype(str) + "  " + pool.get("name", pd.Series([""] * len(pool))).astype(str)
    selected = st.selectbox("选择股票", label.tolist())
    code = selected.split()[0]
    row = pool[pool["code"].astype(str) == code].iloc[0]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("决策层级", str(row.get("decision_tier", "--")))
    c2.metric("发行前评分", fmt_num(row.get("pre_listing_score")))
    c3.metric("公开倍数", fmt_num(row.get("public_subscription_multiple")))
    c4.metric("暗盘收盘", fmt_pct(row.get("gray_close_ret_pct")))
    c5.metric("基石数", fmt_num(row.get("cornerstone_count"), 0))
    st.subheader(f"{row.get('code', '')} {row.get('name', '')}")
    st.write("**模型建议：**", row.get("model_recommendation", "--"))
    st.write("**风险/交易标签：**", row.get("risk_tags", "--"))
    basic = pd.DataFrame([
        ["阶段", row.get("lifecycle_stage", "--")], ["申请状态", row.get("application_status", "--")], ["上市日", row.get("listing_date", "--")], ["申请日/聆讯日", f"{row.get('application_date','--')} / {row.get('hearing_date','--')}"],
        ["板块/行业", f"{row.get('board','--')} / {row.get('industry_level_2','--')}"], ["保荐人", row.get("sponsor", "--")],
        ["发行价/招股区间", f"{fmt_num(row.get('issue_price'))} / {fmt_num(row.get('offer_price_low'))}-{fmt_num(row.get('offer_price_high'))}"], ["一手中签率", fmt_pct(row.get("one_lot_success_rate_pct"))],
        ["暗盘/首日", f"{fmt_pct(row.get('gray_close_ret_pct'))} / {fmt_pct(row.get('d1_close_ret_pct'))}"], ["主要基石", row.get("cornerstone_top_names", "--")], ["主要承销", row.get("top_underwriters", "--")], ["主要账簿管理人", row.get("top_bookrunners", "--")],
    ], columns=["字段", "内容"])
    st.table(basic)
    st.subheader("募资用途 / 业务摘要")
    st.write(row.get("use_of_proceeds", row.get("business_scope", "--")))
    if pd.notna(row.get("company_profile")):
        with st.expander("公司简介"):
            st.write(row.get("company_profile"))
    tab1, tab2, tab3, tab4 = st.tabs(["基石明细", "孖展记录", "中介机构", "二级路径"])
    with tab1:
        d = cornerstone[cornerstone.get("code", pd.Series(dtype=str)).astype(str) == code] if not cornerstone.empty else pd.DataFrame()
        st.dataframe(rename_for_display(d), use_container_width=True, hide_index=True, height=300)
    with tab2:
        d = margin[margin.get("code", pd.Series(dtype=str)).astype(str) == code] if not margin.empty else pd.DataFrame()
        st.dataframe(rename_for_display(d), use_container_width=True, hide_index=True, height=300)
    with tab3:
        u = underwriters[underwriters.get("code", pd.Series(dtype=str)).astype(str) == code] if not underwriters.empty else pd.DataFrame()
        b = bookrunners[bookrunners.get("code", pd.Series(dtype=str)).astype(str) == code] if not bookrunners.empty else pd.DataFrame()
        st.write("承销团"); st.dataframe(rename_for_display(u), use_container_width=True, hide_index=True, height=160)
        st.write("账簿管理人"); st.dataframe(rename_for_display(b), use_container_width=True, hide_index=True, height=160)
    with tab4:
        p = paths[paths.get("code", pd.Series(dtype=str)).astype(str) == code] if not paths.empty else pd.DataFrame()
        st.dataframe(rename_for_display(p), use_container_width=True, hide_index=True, height=220)
    memo_md = f"""# {row.get('code','')} {row.get('name','')} IPO投资Memo\n\n- 决策层级：{row.get('decision_tier','--')}\n- 发行前评分：{row.get('pre_listing_score','--')}\n- 阶段：{row.get('lifecycle_stage','--')}\n- 申请状态：{row.get('application_status','--')}\n- 上市日：{row.get('listing_date','--')}\n- 发行价/招股区间：{fmt_num(row.get('issue_price'))} / {fmt_num(row.get('offer_price_low'))}-{fmt_num(row.get('offer_price_high'))}\n- 公开认购倍数：{fmt_num(row.get('public_subscription_multiple'))}\n- 一手中签率：{fmt_pct(row.get('one_lot_success_rate_pct'))}\n- 孖展倍数：{fmt_num(row.get('margin_multiple'))}\n- 暗盘收盘涨跌：{fmt_pct(row.get('gray_close_ret_pct'))}\n- 首日收盘涨跌：{fmt_pct(row.get('d1_close_ret_pct'))}\n- 基石数量：{fmt_num(row.get('cornerstone_count'),0)}\n- 主要基石：{row.get('cornerstone_top_names','--')}\n- 标签：{row.get('risk_tags','--')}\n\n## 模型建议\n{row.get('model_recommendation','--')}\n\n## 募资用途 / 业务摘要\n{row.get('use_of_proceeds', row.get('business_scope','--'))}\n"""
    st.download_button("下载本票 Memo Markdown", memo_md.encode("utf-8-sig"), file_name=f"{code}_ipo_memo.md", mime="text/markdown")


def page_data_quality(data: dict[str, pd.DataFrame]) -> None:
    st.header("⑨ 数据完整度")
    inv = data.get("inventory", pd.DataFrame())
    if inv.empty:
        st.warning("没有 data_inventory.csv。")
    else:
        st.dataframe(rename_for_display(inv), use_container_width=True, hide_index=True)
    st.info("当前还缺：IPO回拨统计、上市后0-180D行情。回拨统计可后续从HKEXnews配发结果公告中补；0-180D行情可用免费脚本从 Yahoo Finance / Stooq 获取。")
    pool = data.get("pool", pd.DataFrame())
    if not pool.empty:
        fields = ["application_status", "issue_price", "public_subscription_multiple", "international_subscription_multiple", "one_lot_success_rate_pct", "cornerstone_count", "margin_multiple", "gray_close_ret_pct", "underwriter_count", "bookrunner_count", "use_of_proceeds"]
        rows = []
        for f in fields:
            if f in pool.columns:
                non_null = pool[f].notna().sum()
                rows.append([f, non_null, len(pool), non_null / max(len(pool), 1)])
        comp = pd.DataFrame(rows, columns=["field", "non_null", "total", "coverage"])
        st.subheader("关键字段覆盖率")
        st.dataframe(comp, use_container_width=True, hide_index=True)
        if not comp.empty:
            st.bar_chart(comp.set_index("field")["coverage"])


def page_import_guide() -> None:
    st.header("⑩ 本地更新 / 免费行情说明")
    st.markdown("""
### iFind导出更新

把 iFind 导出的 CSV 放入 `ifind_exports/` 后运行：

```bash
python scripts/build_deploy_data_from_ifind_exports.py --input-dir ifind_exports --outdir deploy_data
```

### 免费抓取上市后0-180D行情

```bash
pip install -r requirements.txt
python scripts/fetch_free_hk_quotes_180d.py --pool deploy_data/ipo_decision_pool.csv --out deploy_data/ipo_daily_quotes_180d.csv
python scripts/build_post_listing_paths.py --update-pool
```

免费源说明：
- 优先用 Yahoo Finance / yfinance；失败后尝试 Stooq CSV。
- 免费源通常只有 OHLCV，没有港股真实成交额、换手率、盘口和逐笔。
- 脚本会生成估算成交额 `amount_est_hkd`，只用于交易状态机辅助，不替代正式行情源。
- 临时代码 Hxxxx.HK 没有二级行情，等正式代码后再抓。

### 编码说明

所有输出 CSV 使用 `utf-8-sig`，不要把 CSV 内容复制粘贴到 `streamlit_app.py`。
""")


data = load_all()
pool = data.get("pool", pd.DataFrame())

st.title(APP_TITLE)
st.caption("Step 6 Free Quotes：已接入上市申请和暗盘；回拨缺口走公告补充，0-180D行情走免费源脚本。")

if pool.empty:
    st.warning("没有找到 deploy_data/ipo_decision_pool.csv。请先上传 deploy_data 文件夹，或本地运行 scripts/build_deploy_data_from_ifind_exports.py。")
    page_import_guide()
    st.stop()

with st.sidebar:
    st.success("数据目录：deploy_data/")
    page = st.radio("页面", ["① 全生命周期池", "② A1上市申请", "③ 打新/孖展热度", "④ 暗盘/首日", "⑤ 基石投资者", "⑥ 0-180D状态机", "⑦ 中介机构", "⑧ 单票Memo", "⑨ 数据完整度", "⑩ 更新说明"])
    st.divider()

if page == "① 全生命周期池":
    page_dashboard(pool)
elif page == "② A1上市申请":
    page_a1(data.get("applications", pd.DataFrame()), pool)
elif page == "③ 打新/孖展热度":
    page_heat(pool, data.get("ballot", pd.DataFrame()), data.get("margin", pd.DataFrame()))
elif page == "④ 暗盘/首日":
    page_dark(data.get("dark", pd.DataFrame()), pool)
elif page == "⑤ 基石投资者":
    page_cornerstone(pool, data.get("cornerstone", pd.DataFrame()))
elif page == "⑥ 0-180D状态机":
    page_secondary(data.get("paths", pd.DataFrame()), data.get("quotes", pd.DataFrame()))
elif page == "⑦ 中介机构":
    page_intermediaries(data.get("underwriters", pd.DataFrame()), data.get("bookrunners", pd.DataFrame()))
elif page == "⑧ 单票Memo":
    page_memo(pool, data.get("cornerstone", pd.DataFrame()), data.get("margin", pd.DataFrame()), data.get("underwriters", pd.DataFrame()), data.get("bookrunners", pd.DataFrame()), data.get("dark", pd.DataFrame()), data.get("paths", pd.DataFrame()))
elif page == "⑨ 数据完整度":
    page_data_quality(data)
else:
    page_import_guide()
