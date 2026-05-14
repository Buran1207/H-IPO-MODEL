# 港股 IPO / 二级交易投资决策系统

覆盖 2024 年以来港股 IPO 全生命周期：A1 未上市项目、招股期、暗盘/首日、以及所有 2024 年后上市公司的二级交易决策。

## 本版核心口径

- **决策总览**：显示所有 2024 年之后上市公司 + 当前进入 IPO 流程但未上市公司。
- **未上市公司评级**：只代表 IPO 项目质量 / 未来参与价值。
- **已上市公司评级**：只代表当前二级市场操作决策，不在总览中展示历史 A1 评分。
- **二级市场交易状态机**：覆盖所有 2024+ 已上市公司，不再局限于上市后 180 天。
- **A1 项目观察池**：只显示未上市公司；申请状态、多次递表、失效记录作为项目管理信息，不进入项目质量分。
- **量化定义**：路径、回撤、显著高于、招股期参与标准均在页面中展示为量化阈值。
- **TradingView 跳转**：已上市公司表格中提供 TradingView 图表入口。

## 本地运行

```powershell
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 数据更新

系统继续读取 `deploy_data/` 下的标准化 CSV。免费行情脚本现在默认抓取从上市日至今天的数据，兼容 0-180D 和 180D+ 二级交易池：

```powershell
python scripts/fetch_free_hk_quotes_180d.py --pool deploy_data/ipo_decision_pool.csv --out deploy_data/ipo_daily_quotes_180d.csv
python scripts/build_post_listing_paths.py --update-pool
```

注：文件名保留 `ipo_daily_quotes_180d.csv` 是为了兼容旧版页面和脚本，但内容可以覆盖 180D 以后至最新日期的数据。

## 部署

上传以下内容到 GitHub 仓库根目录：

```text
streamlit_app.py
requirements.txt
README.md
.gitignore
.streamlit/
config/
deploy_data/
scripts/
docs/
```

不要上传压缩包本身。
