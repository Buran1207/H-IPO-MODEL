# 港股 IPO / 半新股决策驾驶舱 · Step 8

本版本在 Step 7 的基础上增加：因子拆解、权重方案、分层回测、买卖触发器和单票 Step 8 Memo。

## 本地运行

```powershell
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 更新数据流程

### 1. iFind 导出结构化表

将 iFind 导出的 CSV/XLSX 放入：

```text
ifind_exports/
```

然后运行：

```powershell
python scripts/build_deploy_data_from_ifind_exports.py
```

### 2. 抓免费上市后 0-180D 行情

```powershell
python scripts/fetch_free_hk_quotes_180d.py --pool deploy_data/ipo_decision_pool.csv --out deploy_data/ipo_daily_quotes_180d.csv
python scripts/build_post_listing_paths.py --update-pool
```

### 3. 跑 Step 8 评分和回测

```powershell
python scripts/score_step8_model_lab.py
```

生成：

```text
deploy_data/ipo_decision_scored_step8.csv
deploy_data/step8_backtest_score_buckets.csv
deploy_data/step8_weight_profile_performance.csv
deploy_data/step8_factor_diagnostics.csv
deploy_data/step8_watchlist_actions.csv
```

## Step 8 页面

1. 决策池：综合排序、一级/基石/二级建议、买卖触发器。
2. 权重与回测：不同权重方案的历史分层表现。
3. 因子诊断：每个因子的区分度和相关性。
4. 交易状态机：上市后 0-180D 路径、买点和卖点。
5. 风险预警：孖展拥挤、破发、行情缺失、锁定期等风险。
6. 单票 Memo：下载可汇报的 Markdown 投资备忘录。
7. 数据完整度：检查数据源是否接入。
8. 更新说明：日常更新步骤。

## 注意

- A 高优先不等于直接买入，而是进入重点研究和额度准备。
- `partial` 表示上市不足 180 天或免费行情源数据不完整，不等于未接入。
- 模型不接实盘，只做研究和决策辅助。
