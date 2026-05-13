# 港股 IPO / 半新股投资决策系统

面向港股 IPO 基金经理的全生命周期决策系统，覆盖：

- A1 / 未上市项目观察池
- 招股期参与决策
- 暗盘与首日交易
- 上市后 0-180 日半新股状态机
- 解禁与供给压力
- 评分标准与权重设置
- 回测与有效性验证
- 单票投资备忘录

## 本版核心更新

1. A1 项目观察池改为“公司维度”，同一家公司多次递表只显示最新状态，申请历史可展开查看。
2. A1 观察池只保留尚未上市公司；已经上市的公司彻底移出 A1 页面，进入半新股/历史复盘体系。
3. 失效但未上市项目继续保留；长期失效历史项目默认隐藏，可一键显示全部。
4. A1 项目质量分不再由申请状态主导，也不包含申请历史风险。
5. A1 默认评分权重：行业与港股市场偏好 35%、公司稀缺性与基本面潜力 20%、保荐/中介质量 15%、历史同类 IPO 表现 15%、未来交易可做性 10%、当前市场窗口 5%。
6. 评分标准与权重设置页面集中展示 A1 评分规则和可调权重；A1 页面只展示项目结果、拆解和下一动作，避免重复。
7. 决策总览新增“当前投资状态”，并把 C 细分为 C1-C6，例如 C1 等待发行资料、C6 失效观察。

## 部署

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

部署到 Streamlit Cloud 时，入口文件为：

```text
streamlit_app.py
```

## 数据文件

主要展示文件位于 `deploy_data/`：

- `ipo_investment_decision_scored.csv`：综合决策主表
- `a1_project_watchlist_company_level.csv`：A1 公司维度观察池
- `a1_application_history.csv`：A1 申请历史记录
- `ipo_daily_quotes_180d.csv`：上市后 0-180 日行情
- `ipo_post_listing_paths.csv`：上市后路径标签
- `data_inventory.csv`：数据接入状态

所有 CSV 均使用 `utf-8-sig` 编码，适配 GitHub、Streamlit 和 Excel。
