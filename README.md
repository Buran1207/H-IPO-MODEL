# 港股 IPO / 半新股决策驾驶舱 · Step 7

这是 Step 7 决策评分版，已接入：

- 上市申请 / A1 临时代码池
- 首发信息一览
- 打新中签结果
- 基石投资者
- 孖展数据
- 承销团参与度
- 账簿管理人
- IPO 暗盘行情
- 免费上市后 0-180D 日行情
- 上市后路径标签

## 在线部署

在 Streamlit Community Cloud 中选择本仓库，入口文件填：

```text
streamlit_app.py
```

## 本地运行

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 每次更新数据后的本地流程

### 1. 从免费源抓上市后0-180D行情

```bash
python scripts/fetch_free_hk_quotes_180d.py --pool deploy_data/ipo_decision_pool.csv --out deploy_data/ipo_daily_quotes_180d.csv
python scripts/build_post_listing_paths.py --update-pool
```

### 2. 重新生成 Step 7 决策评分

```bash
python scripts/score_decisions.py
```

生成文件：

```text
deploy_data/ipo_decision_scored_step7.csv
```

### 3. 上传 GitHub

上传或覆盖 `deploy_data/` 里的 CSV 文件，Streamlit Cloud 会自动刷新。

## 评分说明

当前模型是规则评分模型，不是实盘交易系统。它用于辅助判断：

- 一级是否参与
- 基石/锚定是否可谈
- 暗盘/首日是否追或卖
- 上市后是否等深 V、站回发行价、趋势确认或止损

后续可以在积累更多历史样本后，把规则评分升级为 LightGBM / CatBoost 模型。
