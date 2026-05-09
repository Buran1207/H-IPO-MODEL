from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


# -----------------------------
# Config
# -----------------------------
DATA_CANDIDATES = [
    Path("deploy_data/hk_ipo_scored_public.csv"),
    Path("hk_ipo_scored_public.csv"),
    Path("data/processed/hk_ipo_scored.csv"),
    Path("data/processed/hk_ipo_features.csv"),
]

PCT_COLS = [
    "d1_open_ret",
    "d1_close_ret",
    "d1_intraday_ret",
    "d1_amplitude",
    "d5_close_ret",
    "d20_close_ret",
    "d60_close_ret",
    "max_5_ret",
    "min_5_ret",
    "max_20_ret",
    "min_20_ret",
    "max_60_ret",
    "min_60_ret",
]

CORE_DISPLAY_COLS = [
    "decision_tier",
    "code",
    "name",
    "listing_date",
    "industry",
    "issue_price",
    "d1_close_ret",
    "max_20_ret",
    "min_20_ret",
    "max_60_ret",
    "path_label",
    "risk_level",
    "rule_recommendation",
    "model_score_tradeable_20d",
    "model_recommendation",
]

TARGET_SCHEMA = [
    "code",
    "name",
    "listing_date",
    "industry",
    "issue_price",
    "offer_price_low",
    "offer_price_high",
    "final_price_position",
    "fundraising_amount_hkd",
    "market_cap_at_ipo_hkd",
    "sponsor_names",
    "cornerstone_names",
    "cornerstone_amount_hkd",
    "cornerstone_ratio",
    "public_subscription_multiple",
    "international_subscription_multiple",
    "one_lot_success_rate",
    "clawback_ratio",
    "d1_open_ret",
    "d1_close_ret",
    "d5_close_ret",
    "d20_close_ret",
    "d60_close_ret",
    "max_20_ret",
    "min_20_ret",
    "max_60_ret",
    "min_60_ret",
    "path_label",
    "model_score_tradeable_20d",
]

PATH_DESC = {
    "strong_open": "上市即强势：首日表现好，通常不适合无脑追高，要看回踩承接。",
    "deep_v_rebound": "深 V 反弹：首日/早期有压力，但后续资金回流，适合做二级确认买点。",
    "moderate_tradeable": "可交易型：没有极端破发，首月存在交易机会。",
    "pop_then_fade": "升后回落：首日或前几日情绪过热，后续容易转弱，适合卖点预警。",
    "broken": "破发型：发行价支撑失效，一级和二级都要谨慎。",
    "watch": "观察型：缺少明显趋势，只能小仓试错或等待新触发。",
}


# -----------------------------
# Helpers
# -----------------------------
def find_data_path() -> Path | None:
    for path in DATA_CANDIDATES:
        if path.exists():
            return path
    return None


@st.cache_data(show_spinner=False)
def load_data() -> tuple[pd.DataFrame, str]:
    path = find_data_path()
    if path is None:
        return pd.DataFrame(), ""
    df = pd.read_csv(path, encoding="utf-8-sig")
    df = normalize_data(df)
    return df, str(path)


def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "code" in df.columns:
        df["code"] = df["code"].astype(str).str.strip()
    if "name" in df.columns:
        df["name"] = df["name"].astype(str).str.strip()
    if "industry" in df.columns:
        df["industry"] = df["industry"].fillna("Unknown").astype(str).replace({"": "Unknown"})
    else:
        df["industry"] = "Unknown"

    if "listing_date" in df.columns:
        df["listing_date"] = pd.to_datetime(df["listing_date"], errors="coerce")

    for col in PCT_COLS + ["model_score_tradeable_20d", "issue_price", "d1_amount", "d1_volume", "quote_days"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["label_strong_open", "label_deep_v", "label_broken", "label_pop_then_fade", "label_tradeable_20d"]:
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)

    if "model_score_tradeable_20d" not in df.columns:
        df["model_score_tradeable_20d"] = pd.NA

    df["decision_tier"] = df.apply(classify_decision_tier, axis=1)
    df["risk_level"] = df.apply(classify_risk_level, axis=1)
    df["primary_view"] = df.apply(primary_view, axis=1)
    df["secondary_view"] = df.apply(secondary_view, axis=1)
    df["sell_view"] = df.apply(sell_view, axis=1)
    return df


def safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


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


def has_true(row: pd.Series, col: str) -> bool:
    return bool(row.get(col, False))


def classify_decision_tier(row: pd.Series) -> str:
    score = safe_float(row.get("model_score_tradeable_20d"), 0.0) or 0.0
    path = str(row.get("path_label", ""))

    if score >= 0.78 or path == "strong_open":
        return "A 高优先"
    if score >= 0.60 or path in {"moderate_tradeable", "deep_v_rebound"}:
        return "B 交易观察"
    if has_true(row, "label_broken") or path == "broken" or score < 0.35:
        return "D 回避/仅跟踪"
    return "C 等触发"


def classify_risk_level(row: pd.Series) -> str:
    min20 = safe_float(row.get("min_20_ret"), 0.0) or 0.0
    min60 = safe_float(row.get("min_60_ret"), 0.0) or 0.0
    path = str(row.get("path_label", ""))

    if path == "broken" or has_true(row, "label_broken") or min20 <= -0.25 or min60 <= -0.35:
        return "高风险"
    if path == "pop_then_fade" or min20 <= -0.12 or min60 <= -0.20:
        return "中高风险"
    if min20 < -0.05:
        return "中风险"
    return "低/中风险"


def primary_view(row: pd.Series) -> str:
    tier = str(row.get("decision_tier", ""))
    risk = str(row.get("risk_level", ""))
    if tier.startswith("A"):
        return "一级可进入重点池，但必须补发行估值、认购倍数、基石和保荐人质量后再决定仓位。"
    if tier.startswith("B"):
        return "一级只适合小额或选择性参与；如果认购过热且估值没有折让，优先转为二级观察。"
    if "高风险" in risk:
        return "一级原则上回避，除非发行价极低、基石质量强且有明确流动性保护。"
    return "一级暂不下结论，等待发行结构和认购结果更新。"


def secondary_view(row: pd.Series) -> str:
    path = str(row.get("path_label", "watch"))
    if path == "strong_open":
        return "二级不追首日高开，等 T+2 至 T+10 回踩后仍守住发行价/首日均价，再小仓确认。"
    if path == "deep_v_rebound":
        return "二级重点等深 V 确认：跌破发行价或首日低点后重新收回，并伴随成交放大。"
    if path == "moderate_tradeable":
        return "可纳入首月交易池，优先寻找缩量回踩后的右侧买点。"
    if path == "pop_then_fade":
        return "首日冲高后容易转弱，不追高；若跌破发行价或首日 VWAP，应降低优先级。"
    if path == "broken":
        return "不接飞刀；至少等待重新站回发行价、成交改善、行业 beta 配合。"
    return "只观察，不主动买入；等待价格、成交、发行价三者同时给出触发。"


def sell_view(row: pd.Series) -> str:
    path = str(row.get("path_label", "watch"))
    min20 = safe_float(row.get("min_20_ret"), 0.0) or 0.0
    max20 = safe_float(row.get("max_20_ret"), 0.0) or 0.0

    base = "卖点以发行价、首日 VWAP、首日低点和 20 日成交密集区为核心。"
    if path == "strong_open" and max20 >= 0.35:
        return base + " 20 日内已有较大涨幅时，若放量滞涨或跌破 5 日线，应分批止盈。"
    if path == "deep_v_rebound":
        return base + " 深 V 失败的信号是重新跌回发行价下方并连续两日不能收回。"
    if path in {"broken", "pop_then_fade"} or min20 <= -0.15:
        return base + " 破发行情中止损优先级高于补仓，不能用基本面故事对抗流动性。"
    return base + " 如果没有持续放量和新高，首月交易以快进快出为主。"


def pct_rate(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    return float(series.fillna(False).astype(bool).mean())


def prepare_display_table(df: pd.DataFrame) -> pd.DataFrame:
    available = [col for col in CORE_DISPLAY_COLS if col in df.columns]
    out = df[available].copy()
    for col in PCT_COLS:
        if col in out.columns:
            out[col] = out[col].map(fmt_pct)
    if "model_score_tradeable_20d" in out.columns:
        out["model_score_tradeable_20d"] = out["model_score_tradeable_20d"].map(lambda x: "—" if pd.isna(x) else f"{float(x):.2f}")
    if "listing_date" in out.columns:
        out["listing_date"] = out["listing_date"].map(fmt_date)
    return out


def make_memo(row: pd.Series) -> str:
    code = row.get("code", "")
    name = row.get("name", "")
    path = row.get("path_label", "—")
    score = row.get("model_score_tradeable_20d", pd.NA)
    score_text = "—" if pd.isna(score) else f"{float(score):.2f}"

    return f"""# 港股 IPO / 半新股投资备忘录

## 1. 标的

- 股票：{code} {name}
- 上市日期：{fmt_date(row.get('listing_date'))}
- 行业：{row.get('industry', '—')}
- 发行价：{fmt_num(row.get('issue_price'))}
- 路径分类：{path}
- 决策分层：{row.get('decision_tier', '—')}
- 风险等级：{row.get('risk_level', '—')}
- 模型分：{score_text}

## 2. 历史路径表现

- 首日收盘收益：{fmt_pct(row.get('d1_close_ret'))}
- 5 日收盘收益：{fmt_pct(row.get('d5_close_ret'))}
- 20 日收盘收益：{fmt_pct(row.get('d20_close_ret'))}
- 60 日收盘收益：{fmt_pct(row.get('d60_close_ret'))}
- 20 日最大上涨：{fmt_pct(row.get('max_20_ret'))}
- 20 日最大回撤：{fmt_pct(row.get('min_20_ret'))}
- 60 日最大上涨：{fmt_pct(row.get('max_60_ret'))}
- 60 日最大回撤：{fmt_pct(row.get('min_60_ret'))}

## 3. 一级参与观点

{row.get('primary_view', '—')}

## 4. 二级买点观点

{row.get('secondary_view', '—')}

## 5. 卖点与风控

{row.get('sell_view', '—')}

## 6. 系统原始建议

- 规则建议：{row.get('rule_recommendation', '—')}
- 模型建议：{row.get('model_recommendation', '—')}

## 7. 需要人工补充的信息

- 发行价区间和最终定价位置
- 公开发售倍数、国际配售倍数、一手中签率、回拨比例
- 基石投资者名单、基石金额和占比
- 保荐人/整体协调人质量
- 发行市值、募资金额、同业估值折溢价
- 公司基本面核心判断和行业景气度

> 本备忘录基于现有 CSV 样本和路径规则生成，用于研究和决策辅助，不构成自动交易指令。
"""


def render_metric_row(df: pd.DataFrame) -> None:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("样本数", f"{len(df):,}")
    if "listing_date" in df.columns and df["listing_date"].notna().any():
        c2.metric("最新上市日", fmt_date(df["listing_date"].max()))
    else:
        c2.metric("最新上市日", "—")
    c3.metric("可交易率", fmt_pct(pct_rate(df.get("label_tradeable_20d", pd.Series(dtype=bool)))))
    c4.metric("破发/弱势率", fmt_pct(pct_rate(df.get("label_broken", pd.Series(dtype=bool)))))
    c5.metric("首日均值", fmt_pct(df["d1_close_ret"].mean() if "d1_close_ret" in df.columns else pd.NA))
    c6.metric("20D最大涨幅中位数", fmt_pct(df["max_20_ret"].median() if "max_20_ret" in df.columns else pd.NA))


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

    industries = sorted(view["industry"].dropna().unique().tolist()) if "industry" in view.columns else []
    selected_industries = st.sidebar.multiselect("行业", industries, default=industries)
    if selected_industries and "industry" in view.columns:
        view = view[view["industry"].isin(selected_industries)]

    paths = sorted(view["path_label"].dropna().unique().tolist()) if "path_label" in view.columns else []
    selected_paths = st.sidebar.multiselect("路径分类", paths, default=paths)
    if selected_paths and "path_label" in view.columns:
        view = view[view["path_label"].isin(selected_paths)]

    tiers = sorted(view["decision_tier"].dropna().unique().tolist()) if "decision_tier" in view.columns else []
    selected_tiers = st.sidebar.multiselect("决策分层", tiers, default=tiers)
    if selected_tiers:
        view = view[view["decision_tier"].isin(selected_tiers)]

    min_score = st.sidebar.slider("最低模型分", 0.0, 1.0, 0.0, 0.05)
    if "model_score_tradeable_20d" in view.columns:
        view = view[view["model_score_tradeable_20d"].fillna(0) >= min_score]

    keyword = st.sidebar.text_input("代码/名称搜索", "").strip()
    if keyword and {"code", "name"}.issubset(view.columns):
        mask = view["code"].astype(str).str.contains(keyword, case=False, na=False) | view["name"].astype(str).str.contains(keyword, case=False, na=False)
        view = view[mask]

    return view


# -----------------------------
# App
# -----------------------------
st.set_page_config(page_title="HK IPO 决策驾驶舱", page_icon="📈", layout="wide")

st.title("港股 IPO / 半新股决策驾驶舱")
st.caption("Step 1：先把现有样本转成可筛选、可解释、可下载 memo 的投研界面。后续再接 iFind 自动取数和发行结构模型。")

df, data_path = load_data()
if df.empty:
    st.error("没有找到数据文件。请把 hk_ipo_scored_public.csv 放在 deploy_data/ 目录下。")
    st.stop()

st.sidebar.success(f"数据源：{data_path}")
view = filter_data(df)

render_metric_row(view)
st.divider()

tab_pool, tab_paths, tab_memo, tab_risk, tab_quality, tab_roadmap = st.tabs([
    "① 投资池",
    "② 路径归因",
    "③ 单票 Memo",
    "④ 风控与卖点",
    "⑤ 数据质量",
    "⑥ 下一步",
])

with tab_pool:
    st.subheader("优先级列表")
    st.write("先用现有路径标签和模型分，把股票分成 A/B/C/D 四类。A 不是直接买入，而是进入重点研究和额度准备。")

    sort_candidates = [c for c in ["model_score_tradeable_20d", "listing_date", "max_20_ret", "d1_close_ret"] if c in view.columns]
    if sort_candidates:
        sort_col = st.selectbox("排序字段", sort_candidates, index=0)
        ascending = st.toggle("升序", value=False)
        table_src = view.sort_values(sort_col, ascending=ascending)
    else:
        table_src = view
    st.dataframe(prepare_display_table(table_src), use_container_width=True, hide_index=True)

    csv_bytes = view.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button("下载当前筛选结果 CSV", data=csv_bytes, file_name="hk_ipo_filtered.csv", mime="text/csv")

    st.markdown("### 决策层含义")
    st.markdown(
        """
- **A 高优先**：可进入一级/基石/二级联动研究，但还要补发行结构和估值。
- **B 交易观察**：更适合二级做确认买点，一级谨慎参与。
- **C 等触发**：先不做动作，等价格、成交和发行价关系给信号。
- **D 回避/仅跟踪**：流动性或路径风险较高，除非基本面显著超预期。
"""
    )

with tab_paths:
    st.subheader("路径分布和行业统计")

    if "path_label" in view.columns and not view.empty:
        path_counts = view["path_label"].value_counts().rename_axis("path_label").reset_index(name="count")
        st.bar_chart(path_counts.set_index("path_label"))

        with st.expander("路径标签说明", expanded=True):
            for key, desc in PATH_DESC.items():
                st.write(f"**{key}**：{desc}")

    if "industry" in view.columns and not view.empty:
        st.markdown("### 行业维度")
        agg_map = {"code": "count"}
        if "model_score_tradeable_20d" in view.columns:
            agg_map["model_score_tradeable_20d"] = "mean"
        if "d1_close_ret" in view.columns:
            agg_map["d1_close_ret"] = "mean"
        if "max_20_ret" in view.columns:
            agg_map["max_20_ret"] = "median"
        industry = view.groupby("industry").agg(agg_map).rename(columns={"code": "样本数"}).reset_index()
        if "model_score_tradeable_20d" in industry.columns:
            industry["model_score_tradeable_20d"] = industry["model_score_tradeable_20d"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
        for col in ["d1_close_ret", "max_20_ret"]:
            if col in industry.columns:
                industry[col] = industry[col].map(fmt_pct)
        st.dataframe(industry.sort_values("样本数", ascending=False), use_container_width=True, hide_index=True)

    if "model_score_tradeable_20d" in view.columns and view["model_score_tradeable_20d"].notna().any():
        st.markdown("### 模型分分布")
        score_bins = pd.cut(view["model_score_tradeable_20d"].dropna(), bins=[0, 0.35, 0.60, 0.78, 1.0], include_lowest=True)
        score_counts = score_bins.value_counts().sort_index().rename_axis("score_bin").reset_index(name="count")
        score_counts["score_bin"] = score_counts["score_bin"].astype(str)
        st.bar_chart(score_counts.set_index("score_bin"))

with tab_memo:
    st.subheader("单票投资备忘录")

    if view.empty or "code" not in view.columns:
        st.warning("当前筛选条件下没有股票。")
    else:
        name_series = view["name"] if "name" in view.columns else pd.Series([""] * len(view), index=view.index)
        options = (view["code"].astype(str) + "  " + name_series.astype(str)).tolist()
        selected = st.selectbox("选择股票", options)
        selected_code = selected.split()[0]
        row = view[view["code"].astype(str) == selected_code].iloc[0]

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("决策层", row.get("decision_tier", "—"))
        c2.metric("风险", row.get("risk_level", "—"))
        c3.metric("模型分", "—" if pd.isna(row.get("model_score_tradeable_20d")) else f"{float(row.get('model_score_tradeable_20d')):.2f}")
        c4.metric("首日", fmt_pct(row.get("d1_close_ret")))
        c5.metric("20D最大涨幅", fmt_pct(row.get("max_20_ret")))

        st.markdown("### 系统观点")
        st.info(row.get("primary_view", "—"))
        st.success(row.get("secondary_view", "—"))
        st.warning(row.get("sell_view", "—"))

        detail_cols = [c for c in CORE_DISPLAY_COLS if c in view.columns]
        st.markdown("### 原始字段")
        st.dataframe(prepare_display_table(pd.DataFrame([row]))[detail_cols], use_container_width=True, hide_index=True)

        memo = make_memo(row)
        st.markdown("### Memo 预览")
        st.markdown(memo)
        st.download_button(
            "下载该股票 Memo.md",
            data=memo.encode("utf-8-sig"),
            file_name=f"{selected_code}_ipo_memo.md",
            mime="text/markdown",
        )

with tab_risk:
    st.subheader("风控与卖点监控")
    st.write("这一页先用历史路径做风控框架。下一阶段接入实时/最新 K 线后，可把它变成每日卖点提醒。")

    risk_view = view.copy()
    risk_rank_cols = ["risk_level", "code", "name", "listing_date", "path_label", "d1_close_ret", "max_20_ret", "min_20_ret", "max_60_ret", "min_60_ret", "sell_view"]
    risk_rank_cols = [c for c in risk_rank_cols if c in risk_view.columns]

    high_risk = risk_view[risk_view["risk_level"].isin(["高风险", "中高风险"])] if "risk_level" in risk_view.columns else risk_view.head(0)
    st.markdown("### 高风险/中高风险名单")
    risk_table = high_risk[risk_rank_cols].copy()
    for col in PCT_COLS:
        if col in risk_table.columns:
            risk_table[col] = risk_table[col].map(fmt_pct)
    if "listing_date" in risk_table.columns:
        risk_table["listing_date"] = risk_table["listing_date"].map(fmt_date)
    st.dataframe(risk_table, use_container_width=True, hide_index=True)

    st.markdown("### 统一卖出规则库")
    st.markdown(
        """
1. **破发行价止损**：收盘价跌破发行价且连续两日不能收回，降低或清仓。
2. **首日 VWAP 失守**：首日强势股若跌破首日成交均价，视为资金承接失败。
3. **放量滞涨止盈**：20 日内涨幅较大但成交放大、价格不创新高，分批止盈。
4. **深 V 失败**：深 V 标的重新跌回发行价下方，不能补仓摊低成本。
5. **解禁前降风险**：基石/控股股东锁定期前，若股价已大涨，应提前做减仓预案。
"""
    )

with tab_quality:
    st.subheader("数据质量和缺口")

    present = set(df.columns)
    schema_rows = []
    for col in TARGET_SCHEMA:
        status = "已有" if col in present else "缺失"
        missing_rate = df[col].isna().mean() if col in present else 1.0
        schema_rows.append({"字段": col, "状态": status, "缺失率": missing_rate})
    schema_df = pd.DataFrame(schema_rows)
    schema_df["缺失率"] = schema_df["缺失率"].map(fmt_pct)
    st.dataframe(schema_df, use_container_width=True, hide_index=True)

    st.markdown("### 当前数据表字段")
    col_quality = pd.DataFrame({
        "字段": df.columns,
        "非空数量": [int(df[c].notna().sum()) for c in df.columns],
        "缺失率": [fmt_pct(df[c].isna().mean()) for c in df.columns],
        "示例值": [str(df[c].dropna().iloc[0]) if df[c].notna().any() else "" for c in df.columns],
    })
    st.dataframe(col_quality, use_container_width=True, hide_index=True)

    st.markdown("### 下一阶段最该补的 10 个字段")
    st.markdown(
        """
1. 公开发售认购倍数
2. 国际配售认购倍数
3. 一手中签率
4. 回拨比例
5. 基石投资者名单
6. 基石金额和基石占比
7. 保荐人/整体协调人
8. 募资金额和上市市值
9. 招股价区间与最终定价位置
10. 同业估值折溢价
"""
    )

with tab_roadmap:
    st.subheader("一步步完善路线")
    st.markdown(
        """
### 第一步：把界面变成能汇报的驾驶舱
当前包已经完成：投资池、路径归因、单票 memo、风控规则、数据质量。

### 第二步：接 iFind 自动数据
目标不是一次做全，而是先打通三类数据：IPO 样本列表、单票发行资料、上市后行情。

### 第三步：补发行结构模型
加入公开认购倍数、国际配售、回拨、一手中签率、基石、保荐人、发行估值。

### 第四步：做 Walk-forward 回测
按上市时间滚动训练和验证，避免随机切分造成未来函数。

### 第五步：上线每日更新版
每日更新新股池和半新股池，自动生成“今日需要看”的股票和卖点提醒。
"""
    )

st.caption("研究辅助工具｜不连接实盘｜不构成自动交易指令")
