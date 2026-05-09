from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


PUBLIC_DATA_PATH = Path("deploy_data/hk_ipo_scored_public.csv")
DATA_PATH = Path("data/processed/hk_ipo_scored.csv")
FEATURE_PATH = Path("data/processed/hk_ipo_features.csv")


st.set_page_config(page_title="HK IPO Decision Assistant", layout="wide")
st.title("HK IPO Decision Assistant")


@st.cache_data
def load_data() -> pd.DataFrame:
    if PUBLIC_DATA_PATH.exists():
        path = PUBLIC_DATA_PATH
    elif DATA_PATH.exists():
        path = DATA_PATH
    else:
        path = FEATURE_PATH
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, encoding="utf-8-sig")
    if "listing_date" in df.columns:
        df["listing_date"] = pd.to_datetime(df["listing_date"], errors="coerce")
    return df


def fmt_pct(value):
    if pd.isna(value):
        return ""
    return f"{float(value):.1%}"


df = load_data()
if df.empty:
    st.warning("No data yet. Run: python -m hkipo_ifind.run_pipeline")
    st.stop()

left, right = st.columns([2, 1])
with left:
    industries = sorted([x for x in df.get("industry", pd.Series(dtype=str)).dropna().unique()])
    selected_industries = st.multiselect("Industry", industries, default=industries)
with right:
    min_score = st.slider("Minimum model score", 0.0, 1.0, 0.0, 0.05)

view = df.copy()
if selected_industries and "industry" in view.columns:
    view = view[view["industry"].isin(selected_industries)]
if "model_score_tradeable_20d" in view.columns:
    view = view[view["model_score_tradeable_20d"].fillna(0) >= min_score]

metric_cols = st.columns(5)
metric_cols[0].metric("Samples", len(view))
metric_cols[1].metric("Strong open", int(view.get("label_strong_open", pd.Series(dtype=bool)).fillna(False).sum()))
metric_cols[2].metric("Deep V", int(view.get("label_deep_v", pd.Series(dtype=bool)).fillna(False).sum()))
metric_cols[3].metric("Broken IPOs", int(view.get("label_broken", pd.Series(dtype=bool)).fillna(False).sum()))
if "model_score_tradeable_20d" in view.columns and len(view):
    metric_cols[4].metric("Avg score", f"{view['model_score_tradeable_20d'].mean():.2f}")
else:
    metric_cols[4].metric("Avg score", "N/A")

st.subheader("Priority List")
display_cols = [
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
    "rule_recommendation",
    "model_score_tradeable_20d",
    "model_recommendation",
]
available = [col for col in display_cols if col in view.columns]
sort_col = "model_score_tradeable_20d" if "model_score_tradeable_20d" in view.columns else "listing_date"
table = view.sort_values(sort_col, ascending=False)[available].copy()
for col in ("d1_close_ret", "max_20_ret", "min_20_ret", "max_60_ret"):
    if col in table.columns:
        table[col] = table[col].map(fmt_pct)
if "model_score_tradeable_20d" in table.columns:
    table["model_score_tradeable_20d"] = table["model_score_tradeable_20d"].map(
        lambda x: "" if pd.isna(x) else f"{x:.2f}"
    )
st.dataframe(table, use_container_width=True, hide_index=True)

st.subheader("Path Distribution")
if "path_label" in view.columns:
    st.bar_chart(view["path_label"].value_counts())

st.subheader("Single Name Review")
name_series = view["name"] if "name" in view.columns else pd.Series([""] * len(view), index=view.index)
codes = (view["code"].astype(str) + " " + name_series.astype(str)).dropna().tolist() if "code" in view.columns else []
selected = st.selectbox("Stock", codes)
if selected:
    code = selected.split()[0]
    row = view[view["code"] == code].iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("D1 close", fmt_pct(row.get("d1_close_ret")))
    c2.metric("20D max upside", fmt_pct(row.get("max_20_ret")))
    c3.metric("20D max pressure", fmt_pct(row.get("min_20_ret")))
    score = row.get("model_score_tradeable_20d", pd.NA)
    c4.metric("Model score", "" if pd.isna(score) else f"{score:.2f}")
    st.write("Path:", row.get("path_label", ""))
    st.write("Rule recommendation:", row.get("rule_recommendation", ""))
    st.write("Model recommendation:", row.get("model_recommendation", "Model not trained yet"))
