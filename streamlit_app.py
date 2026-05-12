from __future__ import annotations

from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st

BASE = Path("deploy_data")

st.set_page_config(page_title="港股 IPO 决策驾驶舱 Step 7", layout="wide")


def read_csv_any(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    for enc in ("utf-8-sig", "utf-8", "gb18030", "big5"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_all():
    scored = read_csv_any(BASE / "ipo_decision_scored_step7.csv")
    if scored.empty:
        scored = read_csv_any(BASE / "ipo_decision_pool.csv")
    paths = read_csv_any(BASE / "ipo_post_listing_paths.csv")
    quotes = read_csv_any(BASE / "ipo_daily_quotes_180d.csv")
    inventory = read_csv_any(BASE / "data_inventory.csv")
    for df in (scored, paths, quotes):
        for c in ["listing_date", "date", "application_date", "first_application_date", "hearing_date", "lockup_end_date"]:
            if c in df.columns:
                df[c] = pd.to_datetime(df[c], errors="coerce")
    return scored, paths, quotes, inventory


def fmt_pct(x):
    if pd.isna(x):
        return ""
    try:
        return f"{float(x):.1%}"
    except Exception:
        return str(x)


def fmt_num(x, digits=1):
    if pd.isna(x):
        return ""
    try:
        return f"{float(x):,.{digits}f}"
    except Exception:
        return str(x)


def fmt_money(x):
    if pd.isna(x):
        return ""
    try:
        x = float(x)
        if abs(x) >= 1e9:
            return f"{x/1e9:.1f}十亿"
        if abs(x) >= 1e8:
            return f"{x/1e8:.1f}亿"
        if abs(x) >= 1e4:
            return f"{x/1e4:.1f}万"
        return f"{x:.0f}"
    except Exception:
        return str(x)


def pct_cols(df, cols):
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = out[c].map(fmt_pct)
    return out


def show_df(df: pd.DataFrame, cols=None, height=520):
    if df.empty:
        st.info("暂无数据")
        return
    if cols:
        cols = [c for c in cols if c in df.columns]
        df = df[cols]
    st.dataframe(df, use_container_width=True, hide_index=True, height=height)


def download_csv_button(df: pd.DataFrame, name: str, label="下载当前表"):
    if df.empty:
        return
    st.download_button(
        label,
        data=df.to_csv(index=False, encoding="utf-8-sig"),
        file_name=name,
        mime="text/csv",
    )


def make_memo(row: pd.Series) -> str:
    def g(c, default=""):
        v = row.get(c, default)
        if pd.isna(v):
            return default
        if isinstance(v, pd.Timestamp):
            return v.strftime("%Y-%m-%d")
        return v
    memo = f"""# 港股 IPO / 半新股投资备忘录：{g('code')} {g('name')}

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

## 一、模型结论

- 综合分：{g('ipo_decision_score')}
- 决策层：{g('decision_tier_step7', g('decision_tier'))}
- 一级建议：{g('primary_recommendation')}
- 基石/锚定建议：{g('cornerstone_recommendation')}
- 二级建议：{g('secondary_recommendation')}
- 卖点/风控：{g('sell_risk_recommendation')}

## 二、发行结构

- 生命周期阶段：{g('lifecycle_stage')}
- 上市日：{g('listing_date')}
- 发行价：{g('issue_price')}
- 招股价区间：{g('offer_price_low')} - {g('offer_price_high')}
- 市值：{g('market_cap_hkdm')}
- 公开认购倍数：{g('public_subscription_multiple', g('public_subscription_multiple_ballot'))}
- 一手中签率：{g('one_lot_success_rate_pct')}
- 孖展倍数：{g('margin_multiple')}

## 三、基石与投行

- 基石数量：{g('cornerstone_count')}
- 基石金额：{g('cornerstone_amount_hkd')}
- 主要基石：{g('cornerstone_top_names')}
- 保荐人：{g('sponsor')}
- 整体协调人：{g('overall_coordinator')}
- 账簿管理人：{g('top_bookrunners')}
- 承销团：{g('top_underwriters')}

## 四、暗盘和上市后路径

- 暗盘开盘：{g('gray_open_ret_pct')}
- 暗盘收盘：{g('gray_close_ret_pct')}
- 首日收盘收益：{g('d1_close_ret')}
- 20D最大收益：{g('max_20_ret')}
- 20D最小收益：{g('min_20_ret')}
- 180D最大收益：{g('max_180_ret')}
- 180D最小收益：{g('min_180_ret')}
- 路径标签：{g('path_label')}
- 行情状态：{g('quote_status')}

## 五、风险标签

{g('risk_tags_step7', g('risk_tags'))}

## 六、业务简介 / 募资用途

### 业务简介
{g('business_scope')}

### 募资用途
{g('use_of_proceeds')}
"""
    return memo


pool, paths, quotes, inventory = load_all()

st.title("港股 IPO / 半新股决策驾驶舱 · Step 7")
st.caption("发行结构 + 打新热度 + 基石/投行 + 暗盘 + 上市后0-180D路径，输出一级/基石/二级/卖点建议。")

if pool.empty:
    st.error("未找到 deploy_data/ipo_decision_scored_step7.csv 或 ipo_decision_pool.csv")
    st.stop()

# 补动态库存显示，避免旧 data_inventory 显示行情未接入
inv_extra = []
if not quotes.empty:
    inv_extra.append({"source_name": "上市后0-180D行情", "file_name": "ipo_daily_quotes_180d.csv", "raw_rows": len(quotes), "normalized_rows": len(quotes), "status": "已接入"})
if not paths.empty:
    inv_extra.append({"source_name": "上市后路径标签", "file_name": "ipo_post_listing_paths.csv", "raw_rows": len(paths), "normalized_rows": len(paths), "status": "已接入"})
if "ipo_decision_score" in pool.columns:
    inv_extra.append({"source_name": "Step7决策评分", "file_name": "ipo_decision_scored_step7.csv", "raw_rows": len(pool), "normalized_rows": len(pool), "status": "已接入"})
if not inventory.empty and inv_extra:
    inventory = inventory[~inventory["source_name"].isin([x["source_name"] for x in inv_extra])]
    inventory = pd.concat([inventory, pd.DataFrame(inv_extra)], ignore_index=True)
elif inv_extra:
    inventory = pd.DataFrame(inv_extra)

with st.sidebar:
    st.success(f"样本：{len(pool):,} 只/条")
    if "listing_date" in pool.columns:
        mind, maxd = pool["listing_date"].min(), pool["listing_date"].max()
        st.caption(f"上市日范围：{mind.date() if pd.notna(mind) else '-'} 至 {maxd.date() if pd.notna(maxd) else '-'}")
    tier_opts = sorted([x for x in pool.get("decision_tier_step7", pd.Series(dtype=str)).dropna().unique()])
    selected_tiers = st.multiselect("决策层", tier_opts, default=tier_opts)
    industry_opts = sorted([x for x in pool.get("industry_level_1", pd.Series(dtype=str)).dropna().astype(str).unique() if x and x != "nan"])
    selected_industries = st.multiselect("行业", industry_opts, default=[])
    quote_opts = sorted([x for x in pool.get("quote_status", pd.Series(dtype=str)).dropna().astype(str).unique() if x and x != "nan"])
    selected_quote = st.multiselect("行情状态", quote_opts, default=[])
    min_score = st.slider("最低综合分", 0, 100, 0, 5)
    keyword = st.text_input("搜索代码/简称/基石/保荐人")

view = pool.copy()
if selected_tiers and "decision_tier_step7" in view.columns:
    view = view[view["decision_tier_step7"].isin(selected_tiers)]
if selected_industries and "industry_level_1" in view.columns:
    view = view[view["industry_level_1"].isin(selected_industries)]
if selected_quote and "quote_status" in view.columns:
    view = view[view["quote_status"].isin(selected_quote)]
if "ipo_decision_score" in view.columns:
    view = view[pd.to_numeric(view["ipo_decision_score"], errors="coerce").fillna(0) >= min_score]
if keyword:
    k = keyword.lower().strip()
    text_cols = [c for c in ["code", "name", "sponsor", "overall_coordinator", "cornerstone_top_names", "top_bookrunners", "top_underwriters"] if c in view.columns]
    mask = pd.Series(False, index=view.index)
    for c in text_cols:
        mask |= view[c].astype(str).str.lower().str.contains(k, na=False)
    view = view[mask]

metric_cols = st.columns(6)
metric_cols[0].metric("筛选样本", f"{len(view):,}")
metric_cols[1].metric("A高优先", int(view.get("decision_tier_step7", pd.Series(dtype=str)).astype(str).str.contains("A", na=False).sum()))
metric_cols[2].metric("B交易观察", int(view.get("decision_tier_step7", pd.Series(dtype=str)).astype(str).str.contains("B", na=False).sum()))
metric_cols[3].metric("有0-180D行情", int(pd.to_numeric(view.get("quote_rows", pd.Series(dtype=float)), errors="coerce").fillna(0).gt(0).sum()))
metric_cols[4].metric("平均综合分", fmt_num(pd.to_numeric(view.get("ipo_decision_score", pd.Series(dtype=float)), errors="coerce").mean(), 1))
metric_cols[5].metric("深V/强势路径", int(view.get("path_label", pd.Series(dtype=str)).astype(str).str.contains("深V|强势|反弹", na=False).sum()))

tabs = st.tabs([
    "① 决策池",
    "② 一级/基石评分",
    "③ 暗盘/首日",
    "④ 0-180D状态机",
    "⑤ 基石/孖展/投行",
    "⑥ 单票Memo",
    "⑦ 回测复盘",
    "⑧ 数据完整度",
    "⑨ 更新说明",
])

with tabs[0]:
    st.subheader("综合优先级列表")
    st.caption("A不是直接买入，而是进入重点研究和额度准备；B适合交易观察；C等待价格/信息触发；D只跟踪或回避。")
    sort_col = st.selectbox("排序字段", [c for c in ["ipo_decision_score", "issue_participation_score", "secondary_trade_score", "a1_prescreen_score", "listing_date"] if c in view.columns])
    asc = st.toggle("升序", value=False)
    table = view.sort_values(sort_col, ascending=asc).copy()
    display_cols = [
        "decision_tier_step7", "code", "name", "listing_date", "lifecycle_stage", "industry_level_1",
        "ipo_decision_score", "issue_participation_score", "secondary_trade_score", "a1_prescreen_score",
        "primary_recommendation", "secondary_recommendation", "sell_risk_recommendation", "risk_tags_step7",
    ]
    cn = {
        "decision_tier_step7": "决策层", "code": "代码", "name": "简称", "listing_date": "上市日", "lifecycle_stage": "阶段", "industry_level_1": "行业",
        "ipo_decision_score": "综合分", "issue_participation_score": "一级分", "secondary_trade_score": "二级分", "a1_prescreen_score": "A1分",
        "primary_recommendation": "一级建议", "secondary_recommendation": "二级建议", "sell_risk_recommendation": "卖点/风控", "risk_tags_step7": "风险标签",
    }
    show = table[[c for c in display_cols if c in table.columns]].rename(columns=cn)
    show_df(show, height=620)
    download_csv_button(table, "ipo_decision_pool_filtered.csv")

with tabs[1]:
    st.subheader("一级参与 / 基石锚定评分")
    table = view.sort_values("issue_participation_score" if "issue_participation_score" in view.columns else view.columns[0], ascending=False).copy()
    cols = ["code", "name", "listing_date", "issue_price", "offer_price_low", "offer_price_high", "public_subscription_multiple", "public_subscription_multiple_ballot", "one_lot_success_rate_pct", "margin_multiple", "cornerstone_count", "cornerstone_quality_score", "issue_participation_score", "primary_recommendation", "cornerstone_recommendation", "risk_tags_step7"]
    show_df(table, cols, height=620)
    st.markdown("""
**读法：** 公开认购、孖展、中签率反映资金拥挤度；基石质量和账簿管理人反映机构背书；过度拥挤会进入风险标签，不机械等同于买入。
""")

with tabs[2]:
    st.subheader("暗盘 / 首日信号")
    cols = ["code", "name", "listing_date", "issue_price", "gray_date", "gray_open_ret_pct", "gray_close_ret_pct", "gray_amount_10k_hkd", "d1_open_ret_pct", "d1_close_ret_pct", "secondary_trade_score", "primary_recommendation", "secondary_recommendation"]
    table = view.copy()
    show_df(table, cols, height=620)
    st.caption("暗盘强但首日不跟随，容易出现升后回落；暗盘弱且首日不能收回发行价，原则上不追。")

with tabs[3]:
    st.subheader("上市后 0-180D / 半新股状态机")
    if paths.empty:
        st.warning("未找到 ipo_post_listing_paths.csv")
    else:
        state = paths.copy()
        if keyword and "code" in state.columns:
            state = state[state.astype(str).agg(" ".join, axis=1).str.lower().str.contains(keyword.lower(), na=False)]
        c1, c2 = st.columns([2, 1])
        with c1:
            show_df(pct_cols(state, ["d1_close_ret", "max_20_ret", "min_20_ret", "max_60_ret", "min_60_ret", "max_180_ret", "min_180_ret"]), height=560)
        with c2:
            if "path_label" in state.columns:
                st.write("路径分布")
                st.bar_chart(state["path_label"].value_counts())
            if "quote_status" in state.columns:
                st.write("行情状态")
                st.bar_chart(state["quote_status"].value_counts())
        if not quotes.empty:
            st.markdown("### 单票行情明细")
            options = (state["code"].astype(str) + " " + state.get("name", pd.Series("", index=state.index)).astype(str)).dropna().tolist()
            sel = st.selectbox("选择股票", options, key="quote_sel")
            code = sel.split()[0] if sel else ""
            q = quotes[quotes["code"].astype(str).str.replace("^0+", "", regex=True).eq(code.replace(".HK", "").lstrip("0")) | quotes["code"].astype(str).eq(code)] if code else pd.DataFrame()
            if not q.empty:
                st.line_chart(q.set_index("date")[[c for c in ["close", "ret_from_issue"] if c in q.columns]])
                show_df(q.tail(80), height=300)

with tabs[4]:
    st.subheader("基石 / 孖展 / 投行结构")
    table = view.sort_values("cornerstone_amount_hkd" if "cornerstone_amount_hkd" in view.columns else "ipo_decision_score", ascending=False).copy()
    cols = ["code", "name", "listing_date", "cornerstone_count", "cornerstone_amount_hkd", "cornerstone_quality_score", "cornerstone_top_names", "margin_amount_hkd", "margin_multiple", "margin_over_text", "sponsor", "overall_coordinator", "top_bookrunners", "top_underwriters"]
    show_df(table, cols, height=620)
    st.caption("基石数量多不一定好：短期减少流通，6个月后要关注锁定期和潜在供给。")

with tabs[5]:
    st.subheader("单票投资 Memo")
    options = (view["code"].astype(str) + " " + view.get("name", pd.Series("", index=view.index)).astype(str)).dropna().tolist()
    if not options:
        st.info("当前筛选无股票")
    else:
        sel = st.selectbox("选择股票", options, key="memo_sel")
        code = sel.split()[0]
        row = view[view["code"].astype(str).eq(code)].iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("综合分", fmt_num(row.get("ipo_decision_score"), 1))
        c2.metric("一级分", fmt_num(row.get("issue_participation_score"), 1))
        c3.metric("二级分", fmt_num(row.get("secondary_trade_score"), 1))
        c4.metric("决策层", str(row.get("decision_tier_step7", "")))
        st.markdown("### 投资结论")
        st.write(row.get("model_recommendation_step7", ""))
        st.write("**基石/锚定：**", row.get("cornerstone_recommendation", ""))
        st.write("**卖点/风控：**", row.get("sell_risk_recommendation", ""))
        st.write("**风险标签：**", row.get("risk_tags_step7", row.get("risk_tags", "")))
        memo = make_memo(row)
        st.download_button("下载这只股票的 Markdown Memo", data=memo.encode("utf-8-sig"), file_name=f"{code}_ipo_memo.md", mime="text/markdown")
        with st.expander("查看完整 Memo", expanded=True):
            st.markdown(memo)

with tabs[6]:
    st.subheader("回测复盘 / 模型解释")
    st.caption("当前为规则评分复盘，不是实盘收益承诺。重点看模型高分组是否更容易出现强势/深V路径、低分组是否更容易破发。")
    back = view.copy()
    if "ipo_decision_score" in back.columns and "d1_close_ret" in back.columns:
        back["score_bucket"] = pd.cut(pd.to_numeric(back["ipo_decision_score"], errors="coerce"), bins=[0, 52, 65, 78, 100], labels=["D", "C", "B", "A"], include_lowest=True)
        agg = back.groupby("score_bucket", observed=False).agg(
            样本数=("code", "count"),
            首日均值=("d1_close_ret", "mean"),
            二十日最大均值=("max_20_ret", "mean"),
            六十日最大均值=("max_60_ret", "mean"),
            一八零日最大均值=("max_180_ret", "mean"),
            二十日最小均值=("min_20_ret", "mean"),
        ).reset_index()
        show_df(pct_cols(agg, ["首日均值", "二十日最大均值", "六十日最大均值", "一八零日最大均值", "二十日最小均值"]), height=260)
        st.bar_chart(back["decision_tier_step7"].value_counts() if "decision_tier_step7" in back.columns else pd.Series(dtype=int))
    else:
        st.info("缺少评分或行情收益字段，无法做分层复盘。")

with tabs[7]:
    st.subheader("数据完整度")
    show_df(inventory, height=420)
    st.markdown("""
**说明：** `partial` 通常表示股票上市不足180天，或者免费行情源只能拿到部分日期；这不等于未接入。真正需要人工复核的是 `missing`。
""")
    if not quotes.empty:
        st.write("行情源统计")
        show_df(pd.DataFrame({"source": quotes.get("source", pd.Series(dtype=str)).value_counts().index, "rows": quotes.get("source", pd.Series(dtype=str)).value_counts().values}), height=180)

with tabs[8]:
    st.subheader("更新说明")
    st.markdown("""
### 每次更新数据的顺序

1. 从 iFind 导出新的结构化表，放入 `ifind_exports/`，再运行导入脚本。
2. 抓免费 0-180D 行情：

```bash
python scripts/fetch_free_hk_quotes_180d.py --pool deploy_data/ipo_decision_pool.csv --out deploy_data/ipo_daily_quotes_180d.csv
python scripts/build_post_listing_paths.py --update-pool
```

3. 重新跑 Step 7 决策评分：

```bash
python scripts/score_decisions.py
```

4. 上传 `deploy_data/` 下更新后的 CSV 到 GitHub。

### 现在这版的核心输出

- `ipo_decision_scored_step7.csv`：四阶段评分和投资建议。
- `ipo_post_listing_paths.csv`：0-180D路径标签。
- `ipo_daily_quotes_180d.csv`：免费行情明细。
""")
