# HK IPO Decision Assistant — Step 1

这是第一阶段重构版：先把已有 CSV 数据做成可以给领导演示的港股 IPO / 半新股决策驾驶舱。

## 部署方式

1. 把本压缩包里的文件上传到你的 GitHub 仓库根目录。
2. 覆盖原来的 `streamlit_app.py`、`requirements.txt`、`README.md`。
3. 确认 `deploy_data/hk_ipo_scored_public.csv` 也在仓库里。
4. Streamlit Community Cloud 会自动重新部署。

## 本版本新增

- 决策分层：A/B/C/D 观察池
- 一级、二级、风控三个视角
- 路径分布、行业统计、样本质量检查
- 单票投资备忘录自动生成和下载
- 数据缺口清单，为下一阶段接入 iFind 做准备

## 本地运行

```powershell
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 下一阶段

第二阶段应补齐发行结构和 IPO 认购数据，包括：公开发售倍数、国际配售倍数、一手中签率、回拨比例、基石比例、保荐人、上市市值、募资金额、发行价区间和最终定价位置。
