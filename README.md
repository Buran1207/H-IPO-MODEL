# 港股 IPO / 二级交易投资决策系统 v8

本版重点是：评分透明化、二级交易评分重构、解禁合并为二级风险扣分、行情更新状态解释。

## 本版核心变化

1. **三阶段评分规则内嵌到各自页面**
   - A1项目观察池：展示 A1 项目质量分的维度、权重、量化方法。
   - 招股期参与决策：展示发行定价、需求热度、资金效率、基石、发行结构等量化规则。
   - 二级市场交易状态机：展示技术状态如何转成评分、买入触发和卖出触发。

2. **解禁不再单独评分**
   - 解禁只作为二级交易评分中的风险扣分项和动作限制。
   - 正式评分只使用 iFind 精确解禁明细。
   - 上市日 + 6/12个月估算只作为复核提示，不进入正式二级评分。

3. **二级交易评分重构**
   - 二级评分 = 技术结构 + 量价确认 + IPO锚点 + 相对强弱 + 流动性 - 风险扣分。
   - 技术指标先转为交易状态，再转为分数和动作。
   - 状态包括：趋势确认、放量突破、缩量回踩、深V确认、强势但过热、放量滞涨、破发弱势、高位回撤预警。

4. **行情新鲜度改为更新状态**
   - 页面显示行情来源、最新交易日、更新状态、异常原因。
   - iFind 是正式行情主源，Yahoo/Stooq 只作为兜底。

5. **iFind 路径支持**
   - `run_daily_update_low_quota.bat` 和 `run_daily_update_dry_run.bat` 默认加入：
     `C:\iFinD\THSDataInterface_Windows\bin\x64`
   - 若你的 iFind 安装路径不同，请修改 bat 文件顶部的 `IFIND_API_DIR`。

## 本地运行顺序

```bat
00_setup_env.bat
run_daily_update_dry_run.bat
run_daily_update_low_quota.bat
streamlit run streamlit_app.py
```

## 账号文件

复制：

```text
config/local_ifind_credentials.example.ini
```

改名为：

```text
config/local_ifind_credentials.ini
```

内容格式：

```ini
[ifind]
username=你的iFind账号
password=你的iFind密码
```

不要把 `local_ifind_credentials.ini` 上传 GitHub。

## 重点查看页面

- ③ A1项目观察池
- ④ 招股期参与决策
- ⑥ 二级市场交易状态机
- ⑦ 二级风险：解禁供给解释
- ⑧ 评分体系与模型校准
- ⑬ 数据更新
