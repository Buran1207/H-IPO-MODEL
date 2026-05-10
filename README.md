# 港股 IPO / 半新股决策驾驶舱

Step 3 版本重点：把模型覆盖范围前移到 **A1 / 临时代码 / 未上市申请人**，并把数据拆成四张表：

| 文件 | 用途 |
|---|---|
| `deploy_data/ipo_projects.csv` | A1、PHIP、招股中、配发结果、未上市项目池 |
| `deploy_data/ipo_docs.csv` | 招股书、Application Proof、PHIP、配发结果公告的文件登记 |
| `deploy_data/hk_ipo_scored_public.csv` | 已上市 IPO / 半新股路径标签和评分 |
| `deploy_data/price_180d_sample.csv` | 上市后 180 日由密集到稀疏的行情采样 |

## 部署

把本包文件上传并覆盖 GitHub 仓库后，Streamlit Cloud 会自动部署：

```powershell
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 下一步数据生成方式

Streamlit Cloud 不直接连接本地 iFind。推荐流程：

```text
本地 Windows + iFind → 运行 local_tools 脚本 → 生成 deploy_data/*.csv → 上传 GitHub → 网页更新
```

## 采样规则

上市后行情从上市日起取 180 个交易日：

| 区间 | 频率 |
|---|---|
| D0-D10 | 每个交易日 |
| D11-D30 | 每 2 个交易日 |
| D31-D60 | 每 5 个交易日 |
| D61-D180 | 每 10 个交易日 |
