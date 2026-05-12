from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import numpy as np
import pandas as pd
import streamlit as st

BASE = Path("deploy_data")
CONFIG = Path("config/step8_weight_profiles.json")

st.set_page_config(page_title="港股 IPO 决策驾驶舱 Step 8", layout="wide")


def read_csv_any(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    for enc in ("utf-8-sig", "utf-8", "gb18030", "big5"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path)


def to_num(s):
    return pd.to_numeric(s, errors="coerce")


@st.cache_data(show_spinner=False)
def load_all():
    scored = read_csv_any(BASE / "ipo_decision_scored_step8.csv")
    if scored.empty:
        scored = read_csv_any(BASE / "ipo_decision_scored_step7.csv")
    if scored.empty:
        scored = read_csv_any(BASE / "ipo_decision_pool.csv")
    paths = read_csv_any(BASE / "ipo_post_listing_paths.csv")
    quotes = read_csv_any(BASE / "ipo_daily_quotes_180d.csv")
    inv = read_csv_any(BASE / "data_inventory.csv")
    buckets = read_csv_any(BASE / "step8_backtest_score_buckets.csv")
    profiles = read_csv_any(BASE / "step8_weight_profile_performance.csv")
    diag = read_csv_any(BASE / "step8_factor_diagnostics.csv")
    watch = read_csv_any(BASE / "step8_watchlist_actions.csv")
    for df in (scored, paths, quotes, watch):
        for c in ["listing_date", "date", "application_date", "first_application_date", "hearing_date", "lockup_end_date", "prospectus_date", "gray_date"]:
            if c in df.columns:
                df[c] = pd.to_datetime(df[c], errors="coerce")
    weight_profiles = {}
    if CONFIG.exists():
        try:
            weight_profiles = json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception:
            weight_profiles = {}
    return scored, paths, quotes, inv, buckets, profiles, diag, watch, weight_profiles


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


def show_df(df: pd.DataFrame, cols=None, height=520):
    if df.empty:
        st.info("暂无数据")
        return
    out = df.copy()
    if cols:
        cols = [c for c in cols if c in out.columns]
        out = out[cols]
    st.dataframe(out, use_container_width=True, hide_index=True, height=height)


def pct_view(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = out[c].map(fmt_pct)
    return out


def download_csv_button(df: pd.DataFrame, name: str, label="下载当前表"):
    if not df.empty:
        st.download_button(label, df.to_csv(index=False, encoding="utf-8-sig"), file_name=name, mime="text/csv")


def make_memo(row: pd.Series) -> str:
    def g(c, default=""):
        v = row.get(c, default)
        if pd.isna(v):
            return default
        if isinstance(v, pd.Timestamp):
            return v.strftime("%Y-%m-%d")
        return v
    return f"""# 港股 IPO / 半新股投资备忘录：{g('code')} {g('name')}

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

## 1. Step 8 模型结论

- 综合分：{g('step8_score')}
- 决策层：{g('decision_tier_step8')}
- 阶段动作：{g('stage_action_step8')}
- 一级建议：{g('primary_recommendation_step8')}
- 基石/锚定建议：{g('cornerstone_recommendation_step8')}
- 二级建议：{g('secondary_recommendation_step8')}
- 买入触发：{g('buy_trigger_step8')}
- 卖点/风控：{g('sell_trigger_step8')}

## 2. 分项评分

- 一级分：{g('primary_score_step8')}
- 基石分：{g('cornerstone_score_step8')}
- 二级分：{g('secondary_score_step8')}
- 发行热度分：{g('issue_heat_score')}
- 定价安全分：{g('pricing_safety_score')}
- 暗盘/首日分：{g('gray_signal_score')}
- 0-180D路径分：{g('post_listing_score')}
- 风险惩罚：{g('risk_penalty_score')}

## 3. 发行结构

- 生命周期阶段：{g('lifecycle_stage')}
- 申请状态：{g('application_status')}
- 上市日：{g('listing_date')}
- 发行价：{g('issue_price')}
- 招股价区间：{g('offer_price_low')} - {g('offer_price_high')}
- 市值：{g('market_cap_hkdm')}
- 公开认购倍数：{g('public_subscription_multiple', g('public_subscription_multiple_ballot'))}
- 一手中签率：{g('one_lot_success_rate_pct')}
- 孖展倍数：{g('margin_multiple')}

## 4. 基石与投行

- 基石数量：{g('cornerstone_count')}
- 基石金额：{g('cornerstone_amount_hkd')}
- 主要基石：{g('cornerstone_top_names')}
- 保荐人：{g('sponsor')}
- 整体协调人：{g('overall_coordinator')}
- 账簿管理人：{g('top_bookrunners')}
- 承销团：{g('top_underwriters')}

## 5. 暗盘与上市后路径

- 暗盘开盘：{g('gray_open_ret_pct')}
- 暗盘收盘：{g('gray_close_ret_pct')}
- 首日收盘收益：{g('d1_close_ret')}
- 20D最大收益：{g('max_20_ret')}
- 20D最小收益：{g('min_20_ret')}
- 180D最大收益：{g('max_180_ret')}
- 180D最小收益：{g('min_180_ret')}
- 路径标签：{g('path_label')}
- 行情状态：{g('quote_status')}

## 6. 风险标签

{g('risk_tags_step8')}

## 7. 业务简介 / 募资用途

### 业务简介
{g('business_scope')}

### 募资用途
{g('use_of_proceeds')}
"""


pool, paths, quotes, inventory, buckets, profile_perf, diag, watch, weight_profiles = load_all()

st.title("港股 IPO / 半新股决策驾驶舱 · Step 8")
st.caption("Step 8：在 Step 7 基础上增加因子拆解、权重方案、分层回测、买卖触发器和单票模型解释。")

if pool.empty:
    st.error("未找到 deploy_data/ipo_decision_scored_step8.csv / ipo_decision_pool.csv")
    st.stop()

# 动态补库存显示
extra = []
if not quotes.empty:
    extra.append({"source_name": "上市后0-180D行情", "file_name": "ipo_daily_quotes_180d.csv", "raw_rows": len(quotes), "normalized_rows": len(quotes), "status": "已接入"})
if not paths.empty:
    extra.append({"source_name": "上市后路径标签", "file_name": "ipo_post_listing_paths.csv", "raw_rows": len(paths), "normalized_rows": len(paths), "status": "已接入"})
if "step8_score" in pool.columns:
    extra.append({"source_name": "Step8决策评分", "file_name": "ipo_decision_scored_step8.csv", "raw_rows": len(pool), "normalized_rows": len(pool), "status": "已接入"})
if extra:
    new_inv = pd.DataFrame(extra)
    if inventory.empty:
        inventory = new_inv
    else:
        inventory = inventory[~inventory["source_name"].isin(new_inv["source_name"])]
        inventory = pd.concat([inventory, new_inv], ignore_index=True)

with st.sidebar:
    st.success(f"样本：{len(pool):,} 条")
    if "listing_date" in pool.columns:
        dates = pool["listing_date"].dropna()
        if not dates.empty:
            st.caption(f"上市日范围：{dates.min().date()} 至 {dates.max().date()}")
    tier_col = "decision_tier_step8" if "decision_tier_step8" in pool.columns else "decision_tier_step7"
    tier_opts = sorted([x for x in pool.get(tier_col, pd.Series(dtype=str)).dropna().astype(str).unique()])
    selected_tiers = st.multiselect("决策层", tier_opts, default=tier_opts)
    industry_opts = sorted([x for x in pool.get("industry_level_1", pd.Series(dtype=str)).dropna().astype(str).unique() if x and x != "nan"])
    selected_industries = st.multiselect("行业", industry_opts, default=[])
    quote_opts = sorted([x for x in pool.get("quote_status", pd.Series(dtype=str)).dropna().astype(str).unique() if x and x != "nan"])
    selected_quote = st.multiselect("行情状态", quote_opts, default=[])
    min_score = st.slider("最低 Step8 综合分", 0, 100, 0, 5)
    keyword = st.text_input("搜索代码/简称/基石/保荐人")

view = pool.copy()
if selected_tiers and tier_col in view.columns:
    view = view[view[tier_col].isin(selected_tiers)]
if selected_industries and "industry_level_1" in view.columns:
    view = view[view["industry_level_1"].isin(selected_industries)]
if selected_quote and "quote_status" in view.columns:
    view = view[view["quote_status"].isin(selected_quote)]
if "step8_score" in view.columns:
    view = view[to_num(view["step8_score"]).fillna(0) >= min_score]
if keyword:
    k = keyword.lower().strip()
    text_cols = [c for c in ["code", "name", "sponsor", "overall_coordinator", "cornerstone_top_names", "top_bookrunners", "top_underwriters", "business_scope"] if c in view.columns]
    mask = pd.Series(False, index=view.index)
    for c in text_cols:
        mask |= view[c].astype(str).str.lower().str.contains(k, na=False)
    view = view[mask]

metric_cols = st.columns(7)
metric_cols[0].metric("筛选样本", f"{len(view):,}")
metric_cols[1].metric("A高优先", int(view.get("decision_tier_step8", pd.Series(dtype=str)).astype(str).str.contains("A", na=False).sum()))
metric_cols[2].metric("B交易观察", int(view.get("decision_tier_step8", pd.Series(dtype=str)).astype(str).str.contains("B", na=False).sum()))
metric_cols[3].metric("有行情", int(to_num(view.get("quote_rows", pd.Series(dtype=float))).fillna(0).gt(0).sum()))
metric_cols[4].metric("平均分", fmt_num(to_num(view.get("step8_score", pd.Series(dtype=float))).mean(), 1))
metric_cols[5].metric("高风险", int(to_num(view.get("risk_penalty_score", pd.Series(dtype=float))).fillna(0).ge(18).sum()))
metric_cols[6].metric("强势/深V", int(view.get("path_label", pd.Series(dtype=str)).astype(str).str.contains("强势|深V|修复|反弹", na=False).sum()))

tabs = st.tabs([
    "① 决策池",
    "② 权重与回测",
    "③ 因子诊断",
    "④ 交易状态机",
    "⑤ 风险预警",
    "⑥ 单票Memo",
    "⑦ 数据完整度",
    "⑧ 更新说明",
])

with tabs[0]:
    st.subheader("Step 8 综合决策池")
    sort_options = [c for c in ["step8_score", "primary_score_step8", "cornerstone_score_step8", "secondary_score_step8", "risk_penalty_score", "listing_date"] if c in view.columns]
    sort_col = st.selectbox("排序字段", sort_options, index=0 if sort_options else None)
    asc = st.toggle("升序", value=False)
    table = view.sort_values(sort_col, ascending=asc) if sort_col else view
    cols = [
        "decision_tier_step8", "code", "name", "listing_date", "lifecycle_stage", "industry_level_1",
        "step8_score", "primary_score_step8", "cornerstone_score_step8", "secondary_score_step8", "risk_penalty_score",
        "primary_recommendation_step8", "cornerstone_recommendation_step8", "secondary_recommendation_step8",
        "buy_trigger_step8", "sell_trigger_step8", "risk_tags_step8",
    ]
    cn = {
        "decision_tier_step8":"决策层", "code":"代码", "name":"简称", "listing_date":"上市日", "lifecycle_stage":"阶段", "industry_level_1":"行业",
        "step8_score":"综合分", "primary_score_step8":"一级分", "cornerstone_score_step8":"基石分", "secondary_score_step8":"二级分", "risk_penalty_score":"风险惩罚",
        "primary_recommendation_step8":"一级建议", "cornerstone_recommendation_step8":"基石建议", "secondary_recommendation_step8":"二级建议",
        "buy_trigger_step8":"买入触发", "sell_trigger_step8":"卖点/风控", "risk_tags_step8":"风险标签",
    }
    show_df(table[[c for c in cols if c in table.columns]].rename(columns=cn), height=660)
    download_csv_button(table, "step8_decision_pool_filtered.csv")

with tabs[1]:
    st.subheader("权重方案与分层回测")
    st.caption("这是规则模型复盘，目标是检验高分组是否更容易出现强势/深V/可交易路径，不代表未来收益承诺。")
    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.markdown("### 分数分层表现")
        show_df(pct_view(buckets, ["首日均值", "二十日最大均值", "六十日最大均值", "一八零日最大均值", "二十日最小均值", "交易成功率", "强势或深V率", "坏路径率"]), height=260)
        if not buckets.empty and "score_bucket" in buckets.columns:
            chart = buckets.set_index("score_bucket")[[c for c in ["交易成功率", "坏路径率", "强势或深V率"] if c in buckets.columns]]
            st.bar_chart(chart)
    with c2:
        st.markdown("### 权重方案表现")
        show_df(pct_view(profile_perf, ["top_tradeable_20d_rate", "top_strong_or_deepv_rate", "top_bad_path_rate", "top_d1_mean", "top_max20_mean", "top_min20_mean"]), height=260)
        if weight_profiles:
            with st.expander("查看权重配置", expanded=False):
                for k, v in weight_profiles.items():
                    st.markdown(f"**{k} / {v.get('name_cn','')}**：{v.get('description','')}")
                    st.json(v.get("weights", {}))
    st.markdown("### 方案分数对比")
    score_cols = [c for c in ["code", "name", "listing_date", "score_balanced", "score_primary_ipo", "score_secondary_trade", "score_anti_break", "score_hot_market", "step8_score", "decision_tier_step8"] if c in view.columns]
    show_df(view.sort_values("step8_score", ascending=False)[score_cols], height=360)

with tabs[2]:
    st.subheader("因子诊断")
    st.caption("看每个因子在当前样本中对20D可交易路径的区分度。top_minus_bottom越高，说明高分分位比低分分位更有效。")
    show_df(pct_view(diag, ["corr_max20", "corr_min20", "top_quartile_tradeable_rate", "bottom_quartile_tradeable_rate", "top_minus_bottom"]), height=340)
    if not diag.empty and "factor" in diag.columns:
        c1, c2 = st.columns(2)
        with c1:
            st.write("Top - Bottom 交易成功率差")
            st.bar_chart(diag.set_index("factor")[["top_minus_bottom"]])
        with c2:
            st.write("因子与20D最大收益相关")
            st.bar_chart(diag.set_index("factor")[["corr_max20"]])
    st.markdown("### 单票因子雷达表")
    factor_cols = ["issue_heat_score", "allocation_quality_score", "cornerstone_bank_score", "pricing_safety_score", "gray_signal_score", "post_listing_score", "a1_maturity_score", "data_quality_score", "risk_penalty_score"]
    cols = ["code", "name", "step8_score", "decision_tier_step8"] + [c for c in factor_cols if c in view.columns]
    show_df(view.sort_values("step8_score", ascending=False)[cols], height=420)

with tabs[3]:
    st.subheader("0-180D 交易状态机 / 买卖点")
    cols = ["code", "name", "listing_date", "issue_price", "quote_rows", "quote_source", "quote_status", "path_label", "d1_close_ret", "max_20_ret", "min_20_ret", "max_60_ret", "min_60_ret", "max_180_ret", "min_180_ret", "secondary_score_step8", "buy_trigger_step8", "sell_trigger_step8"]
    table = view.copy()
    pct_cols = ["d1_close_ret", "max_20_ret", "min_20_ret", "max_60_ret", "min_60_ret", "max_180_ret", "min_180_ret"]
    show_df(pct_view(table[[c for c in cols if c in table.columns]], pct_cols), height=560)
    if not paths.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.write("路径分布")
            st.bar_chart(paths.get("path_label", pd.Series(dtype=str)).value_counts())
        with c2:
            st.write("行情状态")
            st.bar_chart(paths.get("quote_status", pd.Series(dtype=str)).value_counts())
    if not quotes.empty:
        st.markdown("### 单票行情曲线")
        options = (view["code"].astype(str) + " " + view.get("name", pd.Series("", index=view.index)).astype(str)).dropna().tolist()
        sel = st.selectbox("选择股票", options, key="quote_line") if options else ""
        code = sel.split()[0] if sel else ""
        q = quotes[quotes["code"].astype(str).eq(code)].copy() if code and "code" in quotes.columns else pd.DataFrame()
        if not q.empty:
            q["date"] = pd.to_datetime(q["date"], errors="coerce")
            chart_cols = [c for c in ["close", "ret_from_issue"] if c in q.columns]
            st.line_chart(q.sort_values("date").set_index("date")[chart_cols])
            show_df(q.sort_values("date").tail(80), height=260)
        elif code:
            st.info("这只股票暂无免费行情明细，可能是未上市、临时代码或免费源未覆盖。")

with tabs[4]:
    st.subheader("风险预警看板")
    risk = view.copy()
    if "risk_penalty_score" in risk.columns:
        risk = risk.sort_values("risk_penalty_score", ascending=False)
    cols = ["code", "name", "listing_date", "step8_score", "risk_penalty_score", "margin_multiple", "public_subscription_multiple", "one_lot_success_rate_pct", "path_label", "quote_status", "risk_tags_step8", "sell_trigger_step8"]
    show_df(risk[[c for c in cols if c in risk.columns]], height=560)
    c1, c2, c3 = st.columns(3)
    c1.metric("孖展>=500倍", int(to_num(view.get("margin_multiple", pd.Series(dtype=float))).fillna(0).ge(500).sum()))
    c2.metric("坏路径", int(view.get("path_label", pd.Series(dtype=str)).astype(str).str.contains("破发|弱势|升后破发", na=False).sum()))
    c3.metric("行情缺失", int(view.get("quote_status", pd.Series(dtype=str)).astype(str).eq("missing").sum()))

with tabs[5]:
    st.subheader("单票投资 Memo")
    options = (view["code"].astype(str) + " " + view.get("name", pd.Series("", index=view.index)).astype(str)).dropna().tolist()
    if not options:
        st.info("当前筛选无股票")
    else:
        sel = st.selectbox("选择股票", options, key="memo")
        code = sel.split()[0]
        row = view[view["code"].astype(str).eq(code)].iloc[0]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("综合分", fmt_num(row.get("step8_score"), 1))
        c2.metric("一级分", fmt_num(row.get("primary_score_step8"), 1))
        c3.metric("基石分", fmt_num(row.get("cornerstone_score_step8"), 1))
        c4.metric("二级分", fmt_num(row.get("secondary_score_step8"), 1))
        c5.metric("风险惩罚", fmt_num(row.get("risk_penalty_score"), 1))
        st.markdown("### 投资结论")
        st.write(row.get("final_recommendation_step8", ""))
        st.write("**买入触发：**", row.get("buy_trigger_step8", ""))
        st.write("**卖点/风控：**", row.get("sell_trigger_step8", ""))
        st.write("**风险标签：**", row.get("risk_tags_step8", ""))
        memo = make_memo(row)
        st.download_button("下载这只股票 Markdown Memo", memo.encode("utf-8-sig"), file_name=f"{code}_step8_memo.md", mime="text/markdown")
        with st.expander("查看完整 Memo", expanded=True):
            st.markdown(memo)

with tabs[6]:
    st.subheader("数据完整度")
    show_df(inventory, height=420)
    if not quotes.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.write("行情源统计")
            src = quotes.get("source", pd.Series(dtype=str)).value_counts().reset_index()
            src.columns = ["source", "rows"]
            show_df(src, height=180)
        with c2:
            st.write("行情记录数统计")
            if not paths.empty and "quote_status" in paths.columns:
                st.bar_chart(paths["quote_status"].value_counts())
    st.caption("partial通常表示上市不足180天，或免费源只拿到部分日期；不等于未接入。missing才需要人工复核。")

with tabs[7]:
    st.subheader("更新说明")
    st.markdown("""
### 日常更新顺序

1. 从 iFind 导出结构化表，放入 `ifind_exports/` 后运行：

```bash
python scripts/build_deploy_data_from_ifind_exports.py
```

2. 抓免费0-180D行情并生成路径：

```bash
python scripts/fetch_free_hk_quotes_180d.py --pool deploy_data/ipo_decision_pool.csv --out deploy_data/ipo_daily_quotes_180d.csv
python scripts/build_post_listing_paths.py --update-pool
```

3. 重新跑 Step 8 评分和回测：

```bash
python scripts/score_step8_model_lab.py
```

4. 上传 `deploy_data/` 中更新后的 CSV 到 GitHub。

### Step 8 新增输出

- `ipo_decision_scored_step8.csv`：多场景评分、因子拆解、买卖触发器。
- `step8_backtest_score_buckets.csv`：A/B/C/D 分层回测。
- `step8_weight_profile_performance.csv`：权重方案表现。
- `step8_factor_diagnostics.csv`：因子诊断。
- `step8_watchlist_actions.csv`：行动清单。

### 使用提醒

模型是辅助决策，不是自动交易。A高优先表示进入重点研究和额度准备，最终仍需叠加行业/公司基本面、估值和发行条款判断。
""")
