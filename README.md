# 港股 IPO / 半新股决策驾驶舱

Step 6 Free Quotes 版。

## 已接入数据

- 港股IPO上市申请
- 港股IPO首发信息一览
- 港股IPO打新中签结果
- 港股IPO基石投资者
- 港股IPO孖展数据
- 港股IPO承销团参与度
- 港股IPO账簿管理人
- 港股IPO暗盘行情

## 本地重新生成 deploy_data

把 iFind 导出的 CSV 放入 `ifind_exports/`，然后运行：

```bash
pip install -r requirements.txt
python scripts/build_deploy_data_from_ifind_exports.py --input-dir ifind_exports --outdir deploy_data
```

## 免费抓取上市后0-180D行情

```bash
python scripts/fetch_free_hk_quotes_180d.py --pool deploy_data/ipo_decision_pool.csv --out deploy_data/ipo_daily_quotes_180d.csv
python scripts/build_post_listing_paths.py --update-pool
```

## 部署

上传到 GitHub 根目录，Streamlit Cloud 的入口文件填：

```text
streamlit_app.py
```

## 编码

所有 CSV 输出均为 `utf-8-sig`，不要把 CSV 内容复制进 `streamlit_app.py`。
