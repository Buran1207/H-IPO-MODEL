# 港股 IPO / 半新股投资决策系统

面向投资委员会和基金经理的港股 IPO、A1 项目及半新股决策驾驶舱。

## 本地运行

```powershell
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 数据更新

- iFind 导出数据放入本地后，使用 `scripts/build_investment_dataset.py` 重新生成 `deploy_data/ipo_investment_decision_scored.csv`。
- 免费行情使用 `scripts/fetch_free_hk_quotes_180d.py` 与 `scripts/build_post_listing_paths.py`。
- 页面不展示开发版本号，所有技术说明保留在 README 和 docs 中。
