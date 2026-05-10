# 港股 IPO / A1 / 半新股决策驾驶舱 - Step 3

这个版本把研究对象从“已上市 IPO 样本”扩展为完整生命周期：

```text
A1递表 / 临时代码 → 招股书 → 配发结果公告 → 上市后0-180天半新股跟踪
```

## 你要上传到 GitHub 的文件

- `streamlit_app.py`
- `requirements.txt`
- `.gitignore`
- `.streamlit/config.toml`
- `deploy_data/hk_ipo_scored_public.csv`
- `deploy_data/a1_ipo_pipeline.csv`
- `deploy_data/ipo_announcement_catalog.csv`
- `deploy_data/ipo_offer_results.csv`
- `templates/*.csv`
- `scripts/make_quote_sampling_plan.py`
- `docs/ifind_super_command_targets.md`

## 新增能力

1. A1/未上市公司支持  
   支持临时代码、A1日期、招股书链接、预计上市日期等字段。

2. 两个公告文件作为发行资料核心来源  
   招股书用于发行区间、行业、募资用途、风险因素、保荐人、基石初始信息。  
   配发结果公告用于最终发行价、公开认购倍数、国际配售倍数、一手中签率、回拨比例。

3. 上市后0-180天行情策略  
   D0-D30每日抓取；D31-D90每3个交易日；D91-D180每周；触发破发/放量/回发行价时加密。

4. 单票 Memo  
   每只股票/发行人可以生成一页 Markdown 投资备忘录。

## 数据文件说明

### deploy_data/a1_ipo_pipeline.csv

存 A1、临时代码、招股书前后的管线数据。可以先只有表头，后续由 iFind 本地导出脚本生成。

### deploy_data/ipo_offer_results.csv

存招股书和配发结果公告抽取出来的发行结构字段。

### deploy_data/ipo_announcement_catalog.csv

存公告目录：招股书、聆讯后资料集、配发结果公告等。

### deploy_data/hk_ipo_scored_public.csv

存已上市股票的路径、收益、模型分、标签。

## Streamlit Cloud 重要说明

Streamlit Cloud 不能直接连接你本地电脑上的 iFind。正确流程是：

```text
本地 Windows + iFind API 取数 → 生成 CSV → 上传 GitHub → Streamlit Cloud 自动展示
```

## 本地运行

```powershell
pip install -r requirements.txt
streamlit run streamlit_app.py
```

