from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st

APP_TITLE = "港股 IPO / 半新股决策驾驶舱"
DATA_DIR = Path("deploy_data")

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")


# -----------------------------
# Data helpers
# -----------------------------
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
        except Exception as exc:  # pragma: no cover
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


def fmt_hkd(x) -> str:
    if pd.isna(x):
        return "--"
    try:
        val = float(x)
        if abs(val) >= 1e9:
            return f"HK${val/1e9:,.2f}bn"
        if abs(val) >= 1e6:
            return f"HK${val/1e6:,.1f}mn"
        return f"HK${val:,.0f}"
    except Exception:
        return str(x)


def available_cols(df: pd.DataFrame, cols: Iterable[str]) -> list[str]:
    return [c for c in cols if c in df.columns]


def rename_for_display(df: pd.DataFrame) -> pd.DataFrame:
    cn = {
        "code": "代码",
        "stock_code": "代码",
        "name": "简称",
        "issuer_name": "发行人",
        "listing_date": "上市日",
        "prospectus_date": "招股书/招股日",
        "offer_start_date": "招股开始",
        "offer_end_date": "招股结束",
        "pricing_date": "定价日",
        "allotment_date": "配发结果日",
        "board": "板块",
        "offering_type": "发行方式",
        "issue_price": "发行价",
        "offer_price_low": "招股价低",
        "offer_price_high": "招股价高",
        "board_lot": "每手股数",
        "market_cap_hkdm": "上市市值/HKD mn",
        "gross_proceeds_hkd": "募资总额/HKD",
        "net_proceeds_hkd": "募资净额/HKD",
        "public_subscription_multiple": "公开认购倍数",
        "international_subscription_multiple": "国际配售倍数",
        "one_lot_success_rate_pct": "一手中签率%",
        "margin_multiple": "孖展倍数",
        "margin_over_text": "孖展状态",
        "cornerstone_count": "基石数",
        "cornerstone_amount_hkd": "基石金额/HKD",
        "cornerstone_top_names": "主要基石",
        "cornerstone_quality_score": "基石质量分",
        "underwriter_count": "承销机构数",
        "bookrunner_count": "账簿管理人数",
        "top_underwriters": "主要承销机构",
        "top_bookrunners": "主要账簿管理人",
        "lifecycle_stage": "阶段",
        "pre_listing_score": "发行前评分",
        "decision_tier": "决策层级",
        "model_recommendation": "模型建议",
        "risk_tags": "标签",
        "use_of_proceeds": "募资用途",
        "industry_level_1": "一级行业",
        "industry_level_2": "二级行业",
        "record_date": "记录日",
        "investor_name": "投资者",
        "invested_amount_hkd": "投资金额/HKD",
        "lockup_end_date": "锁定到期日",
        "institution": "机构",
        "role": "角色",
        "participation_pct": "参与度%",
        "source_name": "数据源",
        "file_name": "文件名",
        "raw_rows": "原始行数",
        "normalized_rows": "标准化行数",
        "status": "状态",
    }
    return df.rename(columns={k: v for k, v in cn.items() if k in df.columns})


@st.cache_data(show_spinner=False)
def load_all() -> dict[str, pd.DataFrame]:
    files = {
        "pool": "ipo_decision_pool.csv",
        "master": "ipo_master_ifind_normalized.csv",
        "ballot": "ipo_ballot_results.csv",
        "cornerstone": "ipo_cornerstone_investors.csv",
        "cornerstone_summary": "ipo_cornerstone_summary.csv",
        "margin": "ipo_margin_data.csv",
        "underwriters": "ipo_underwriter_participation.csv",
        "bookrunners": "ipo_bookrunner_details.csv",
        "inventory": "data_inventory.csv",
        "offer": "ipo_offer_results.csv",
    }
    data = {k: read_csv_smart(DATA_DIR / v) for k, v in files.items()}
    for k, df in data.items():
        if df.empty:
            continue
        for col in ["listing_date", "prospectus_date", "offer_start_date", "offer_end_date", "pricing_date", "allotment_date", "record_date", "lockup_end_date"]:
            if col in df.columns:
                df[col] = to_datetime_series(df[col])
    return data


def make_filtered_pool(pool: pd.DataFrame) -> pd.DataFrame:
    view = pool.copy()
    if "listing_date" in view.columns:
        dates = to_datetime_series(view["listing_date"])
        if dates.notna().any():
            min_date = dates.min().date()
            max_date = dates.max().date()
            selected_range = st.sidebar.date_input("上市日期区间", value=(min_date, max_date), min_value=min_date, max_value=max_date)
            if isinstance(selected_range, tuple) and len(selected_range) == 2:
                start, end = selected_range
                view = view[(dates.dt.date >= start) & (dates.dt.date <= end)]
    for col, label in [("lifecycle_stage", "阶段"), ("decision_tier", "决策层级"), ("board", "板块"), ("industry_level_1", "行业")]:
        if col in view.columns:
            options = sorted([x for x in view[col].dropna().astype(str).unique() if x and x != "nan"])
            default = options
            selected = st.sidebar.multiselect(label, options, default=default)
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


# -----------------------------
# Page components
# -----------------------------
def page_dashboard(pool: pd.DataFrame) -> None:
    st.header("① 全生命周期投资池")
    st.caption("覆盖已导入的首发信息、中签结果、基石、孖展、承销团和账簿管理人数据。当前仍未包含上市申请一览、暗盘和上市后0-180D行情。")
    view = make_filtered_pool(pool)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("样本数", len(view))
    c2.metric("A/B优先数", int(view.get("decision_tier", pd.Series(dtype=str)).astype(str).str.contains("A|B", regex=True).sum()))
    c3.metric("平均评分", "--" if view.empty or "pre_listing_score" not in view.columns else f"{to_numeric_series(view['pre_listing_score']).mean():.1f}")
    c4.metric("有基石样本", int(to_numeric_series(view.get("cornerstone_count", pd.Series(dtype=float))).fillna(0).gt(0).sum()))
    c5.metric("有孖展样本", int(to_numeric_series(view.get("margin_multiple", pd.Series(dtype=float))).notna().sum()))

    st.subheader("优先级列表")
    cols = [
        "decision_tier", "code", "name", "listing_date", "lifecycle_stage", "industry_level_1", "issue_price",
        "public_subscription_multiple", "one_lot_success_rate_pct", "margin_multiple", "cornerstone_count",
        "pre_listing_score", "risk_tags", "model_recommendation"
    ]
    table = view.sort_values("pre_listing_score" if "pre_listing_score" in view.columns else "listing_date", ascending=False)
    table = table[available_cols(table, cols)].copy()
    st.dataframe(rename_for_display(table), use_container_width=True, hide_index=True, height=520)
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


def page_heat(pool: pd.DataFrame, ballot: pd.DataFrame, margin: pd.DataFrame) -> None:
    st.header("② 打新 / 孖展热度")
    st.caption("公开认购倍数、一手中签率和孖展倍数用于判断拥挤交易，而不是简单越热越买。")
    view = pool.copy()
    sort_col = "public_subscription_multiple"
    cols = ["code", "name", "listing_date", "public_subscription_multiple", "one_lot_success_rate_pct", "total_applicants", "margin_multiple", "margin_amount_hkd", "margin_over_text", "decision_tier", "pre_listing_score"]
    if sort_col in view.columns:
        view = view.sort_values(sort_col, ascending=False, na_position="last")
    st.dataframe(rename_for_display(view[available_cols(view, cols)]), use_container_width=True, hide_index=True, height=520)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("公开认购倍数 Top 20")
        if "public_subscription_multiple" in view.columns:
            chart = view[["name", "public_subscription_multiple"]].dropna().head(20).set_index("name")
            st.bar_chart(chart)
    with c2:
        st.subheader("孖展倍数 Top 20")
        if "margin_multiple" in view.columns:
            chart = view[["name", "margin_multiple"]].dropna().sort_values("margin_multiple", ascending=False).head(20).set_index("name")
            st.bar_chart(chart)

    with st.expander("原始标准化表：打新中签结果"):
        st.dataframe(rename_for_display(ballot), use_container_width=True, hide_index=True, height=360)
    with st.expander("原始标准化表：孖展数据"):
        st.dataframe(rename_for_display(margin), use_container_width=True, hide_index=True, height=360)


def page_cornerstone(pool: pd.DataFrame, cornerstone: pd.DataFrame, cs_summary: pd.DataFrame) -> None:
    st.header("③ 基石投资者")
    st.caption("基石数量、金额、名称和锁定期是一级参与和上市后解禁压力判断的关键输入。")
    cols = ["code", "name", "listing_date", "cornerstone_count", "cornerstone_amount_hkd", "cornerstone_quality_score", "cornerstone_top_names", "lockup_end_date", "decision_tier", "pre_listing_score"]
    view = pool[available_cols(pool, cols)].copy()
    if "cornerstone_amount_hkd" in view.columns:
        view = view.sort_values("cornerstone_amount_hkd", ascending=False, na_position="last")
    st.dataframe(rename_for_display(view), use_container_width=True, hide_index=True, height=480)

    left, right = st.columns(2)
    with left:
        st.subheader("基石金额 Top 20")
        if "cornerstone_amount_hkd" in view.columns:
            chart = view[["name", "cornerstone_amount_hkd"]].dropna().head(20).set_index("name")
            st.bar_chart(chart)
    with right:
        st.subheader("基石数量分布")
        if "cornerstone_count" in view.columns:
            st.bar_chart(view["cornerstone_count"].fillna(0).astype(int).value_counts().sort_index())

    with st.expander("基石投资者明细"):
        detail_cols = ["code", "name", "listing_date", "investor_name", "ultimate_owner", "invested_amount_hkd", "allocation_pct", "lockup_months", "lockup_end_date", "industry"]
        st.dataframe(rename_for_display(cornerstone[available_cols(cornerstone, detail_cols)]), use_container_width=True, hide_index=True, height=460)


def page_intermediaries(underwriters: pd.DataFrame, bookrunners: pd.DataFrame) -> None:
    st.header("④ 中介机构 / 账簿管理人")
    st.caption("后续可以在这里沉淀保荐人、整体协调人、账簿管理人和承销团历史胜率。")
    tab1, tab2, tab3 = st.tabs(["承销团明细", "账簿管理人", "机构参与统计"])
    with tab1:
        st.dataframe(rename_for_display(underwriters), use_container_width=True, hide_index=True, height=520)
    with tab2:
        st.dataframe(rename_for_display(bookrunners), use_container_width=True, hide_index=True, height=520)
    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("承销团机构参与次数")
            if not underwriters.empty and "institution" in underwriters.columns:
                st.dataframe(underwriters["institution"].value_counts().reset_index().rename(columns={"institution": "机构", "count": "次数"}), use_container_width=True, hide_index=True)
        with c2:
            st.subheader("账簿管理人参与次数")
            if not bookrunners.empty and "institution" in bookrunners.columns:
                st.dataframe(bookrunners["institution"].value_counts().reset_index().rename(columns={"institution": "机构", "count": "次数"}), use_container_width=True, hide_index=True)


def page_memo(pool: pd.DataFrame, cornerstone: pd.DataFrame, margin: pd.DataFrame, underwriters: pd.DataFrame, bookrunners: pd.DataFrame) -> None:
    st.header("⑤ 单票投资 Memo")
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
    c4.metric("孖展倍数", fmt_num(row.get("margin_multiple")))
    c5.metric("基石数", fmt_num(row.get("cornerstone_count"), 0))

    st.subheader(f"{row.get('code', '')} {row.get('name', '')}")
    st.write("**模型建议：**", row.get("model_recommendation", "--"))
    st.write("**风险/交易标签：**", row.get("risk_tags", "--"))

    basic = pd.DataFrame([
        ["上市日", row.get("listing_date", "--")],
        ["招股日", row.get("prospectus_date", "--")],
        ["板块", row.get("board", "--")],
        ["发行价/招股区间", f"{fmt_num(row.get('issue_price'))} / {fmt_num(row.get('offer_price_low'))}-{fmt_num(row.get('offer_price_high'))}"],
        ["上市市值", fmt_num(row.get("market_cap_hkdm")) + " HKD mn"],
        ["一手中签率", fmt_pct(row.get("one_lot_success_rate_pct"))],
        ["国际配售倍数", fmt_num(row.get("international_subscription_multiple"))],
        ["主要基石", row.get("cornerstone_top_names", "--")],
        ["主要承销", row.get("top_underwriters", "--")],
        ["主要账簿管理人", row.get("top_bookrunners", "--")],
    ], columns=["字段", "内容"])
    st.table(basic)

    st.subheader("募资用途")
    st.write(row.get("use_of_proceeds", "--"))

    tab1, tab2, tab3 = st.tabs(["基石明细", "孖展记录", "中介机构"])
    with tab1:
        d = cornerstone[cornerstone.get("code", pd.Series(dtype=str)).astype(str) == code] if not cornerstone.empty else pd.DataFrame()
        st.dataframe(rename_for_display(d), use_container_width=True, hide_index=True, height=300)
    with tab2:
        d = margin[margin.get("code", pd.Series(dtype=str)).astype(str) == code] if not margin.empty else pd.DataFrame()
        st.dataframe(rename_for_display(d), use_container_width=True, hide_index=True, height=300)
    with tab3:
        u = underwriters[underwriters.get("code", pd.Series(dtype=str)).astype(str) == code] if not underwriters.empty else pd.DataFrame()
        b = bookrunners[bookrunners.get("code", pd.Series(dtype=str)).astype(str) == code] if not bookrunners.empty else pd.DataFrame()
        st.write("承销团")
        st.dataframe(rename_for_display(u), use_container_width=True, hide_index=True, height=180)
        st.write("账簿管理人")
        st.dataframe(rename_for_display(b), use_container_width=True, hide_index=True, height=180)

    memo_md = f"""# {row.get('code','')} {row.get('name','')} IPO投资Memo

- 决策层级：{row.get('decision_tier','--')}
- 发行前评分：{row.get('pre_listing_score','--')}
- 阶段：{row.get('lifecycle_stage','--')}
- 上市日：{row.get('listing_date','--')}
- 发行价/招股区间：{fmt_num(row.get('issue_price'))} / {fmt_num(row.get('offer_price_low'))}-{fmt_num(row.get('offer_price_high'))}
- 公开认购倍数：{fmt_num(row.get('public_subscription_multiple'))}
- 一手中签率：{fmt_pct(row.get('one_lot_success_rate_pct'))}
- 孖展倍数：{fmt_num(row.get('margin_multiple'))}
- 基石数量：{fmt_num(row.get('cornerstone_count'),0)}
- 主要基石：{row.get('cornerstone_top_names','--')}
- 标签：{row.get('risk_tags','--')}

## 模型建议
{row.get('model_recommendation','--')}

## 募资用途
{row.get('use_of_proceeds','--')}
"""
    st.download_button("下载本票 Memo Markdown", memo_md.encode("utf-8-sig"), file_name=f"{code}_ipo_memo.md", mime="text/markdown")


def page_data_quality(data: dict[str, pd.DataFrame]) -> None:
    st.header("⑥ 数据完整度")
    inv = data.get("inventory", pd.DataFrame())
    if inv.empty:
        st.warning("没有 data_inventory.csv。")
    else:
        st.dataframe(rename_for_display(inv), use_container_width=True, hide_index=True)

    st.subheader("当前版本判断")
    st.info("本包已经接入你上传的 6 个 iFind 导出：首发信息一览、打新中签结果、基石投资者、孖展数据、承销团参与度、账簿管理人。还缺上市申请一览、IPO回拨统计、IPO暗盘行情、上市后0-180D行情。")

    pool = data.get("pool", pd.DataFrame())
    if not pool.empty:
        fields = [
            "issue_price", "public_subscription_multiple", "international_subscription_multiple", "one_lot_success_rate_pct",
            "cornerstone_count", "margin_multiple", "underwriter_count", "bookrunner_count", "use_of_proceeds"
        ]
        rows = []
        for f in fields:
            if f in pool.columns:
                non_null = pool[f].notna().sum()
                rows.append([f, non_null, len(pool), non_null / max(len(pool), 1)])
        comp = pd.DataFrame(rows, columns=["field", "non_null", "total", "coverage"])
        st.subheader("关键字段覆盖率")
        st.dataframe(rename_for_display(comp), use_container_width=True, hide_index=True)
        if not comp.empty:
            st.bar_chart(comp.set_index("field")["coverage"])


def page_import_guide() -> None:
    st.header("⑦ 本地更新数据说明")
    st.markdown(
        """
### 推荐流程

1. 在 iFind 一级市场界面导出 CSV，文件名保留中文关键词，例如：
   - 港股IPO首发信息一览.csv
   - 港股IPO打新中签结果.csv
   - 港股IPO基石投资者.csv
   - 港股IPO孖展数据.csv
   - 港股IPO承销团参与度-明细.xlsx.csv
   - 港股IPO账簿管理人-明细.xlsx.csv

2. 把这些 CSV 放入项目目录的 `ifind_exports/`。

3. 在本地运行：

```bash
python scripts/build_deploy_data_from_ifind_exports.py --input-dir ifind_exports --outdir deploy_data
```

4. 把生成后的 `deploy_data/` 上传 GitHub，Streamlit Cloud 会自动更新。

### 编码说明

本版本所有输出 CSV 都使用 `utf-8-sig`，Excel、GitHub 和 Streamlit 都更不容易乱码。
不要把 CSV 内容复制粘贴到 `streamlit_app.py`，`streamlit_app.py` 只能是 Python 代码。
"""
    )


# -----------------------------
# Main
# -----------------------------
data = load_all()
pool = data.get("pool", pd.DataFrame())

st.title(APP_TITLE)
st.caption("Step 5 Clean v3：干净仓库可直接上传版。先把一级发行结构和关键参与方数据打通，再进入A1、回拨、暗盘与上市后交易状态机。")

if pool.empty:
    st.warning("没有找到 deploy_data/ipo_decision_pool.csv。请先上传 deploy_data 文件夹，或本地运行 scripts/build_deploy_data_from_ifind_exports.py。")
    page_import_guide()
    st.stop()

with st.sidebar:
    st.success("数据目录：deploy_data/")
    page = st.radio(
        "页面",
        ["① 全生命周期池", "② 打新/孖展热度", "③ 基石投资者", "④ 中介机构", "⑤ 单票Memo", "⑥ 数据完整度", "⑦ 更新说明"],
    )
    st.divider()

if page == "① 全生命周期池":
    page_dashboard(pool)
elif page == "② 打新/孖展热度":
    page_heat(pool, data.get("ballot", pd.DataFrame()), data.get("margin", pd.DataFrame()))
elif page == "③ 基石投资者":
    page_cornerstone(pool, data.get("cornerstone", pd.DataFrame()), data.get("cornerstone_summary", pd.DataFrame()))
elif page == "④ 中介机构":
    page_intermediaries(data.get("underwriters", pd.DataFrame()), data.get("bookrunners", pd.DataFrame()))
elif page == "⑤ 单票Memo":
    page_memo(pool, data.get("cornerstone", pd.DataFrame()), data.get("margin", pd.DataFrame()), data.get("underwriters", pd.DataFrame()), data.get("bookrunners", pd.DataFrame()))
elif page == "⑥ 数据完整度":
    page_data_quality(data)
else:
    page_import_guide()
