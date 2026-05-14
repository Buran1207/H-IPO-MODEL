# 港股 IPO / 二级交易投资决策系统

这是一个面向港股 IPO、A1 项目、招股期、暗盘/首日以及 2024 年后上市公司二级交易的 Streamlit 决策系统。

## 本版新增

- 今日决策清单：按“今天要做什么”归类。
- 人工研究评分：`deploy_data/manual_research_scores.csv` 可纳入基金经理基本面观点。
- 人工复核池：集中列出行情滞后、日期异常、高解禁压力、高分但数据不足等需要人工复核的股票。
- 回测页增加评级分布校准。
- 单票 Memo 继续作为投委会式输出。

## 本地运行

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 部署

将本项目根目录上传 GitHub，并在 Streamlit Cloud 中选择：

```text
streamlit_app.py
```

## 数据更新

主要数据放在：

```text
deploy_data/
```

人工研究评分模板：

```text
deploy_data/manual_research_scores.csv
```

编辑后上传覆盖该文件即可。
