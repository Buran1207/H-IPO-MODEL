# HK IPO / 半新股决策驾驶舱

这是港股 IPO / 半新股研究辅助系统的 Step 2 版本。

## 已有功能

- 投资池分层：A 高优先 / B 交易观察 / C 等触发 / D 回避
- 路径归因：上市即强、深 V 反弹、升后回落、持续破发等
- 单票 Memo：自动生成可下载的投资备忘录
- 风控卖点：发行价、首日 VWAP、深 V 失败、放量滞涨等规则
- 数据质量：显示发行价、行业、认购倍数、基石、保荐人等字段缺口
- iFind 接入说明：本地取数 -> CSV -> 上传 GitHub -> 云端展示

## Streamlit Cloud 部署

主入口文件：

```text
streamlit_app.py
```

依赖文件：

```text
requirements.txt
```

公开数据文件路径：

```text
deploy_data/hk_ipo_scored_public.csv
```

可选补丁文件路径：

```text
deploy_data/ipo_master_patch.csv
```

## 本地运行

```powershell
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 重要说明

Streamlit Cloud 不能直接连接你本地电脑上的 iFind。正确架构是：

```text
本地 Windows 跑 iFind 脚本 -> 生成 CSV -> 上传 GitHub -> Streamlit Cloud 展示
```

下一阶段要补的字段：公开认购倍数、国际配售倍数、一手中签率、回拨比例、基石名单、基石占比、保荐人、发行市值、募资金额、行业。
