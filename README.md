# 港股 IPO / 二级交易投资决策系统

这是一个面向港股 IPO、A1 项目、招股期、暗盘/首日，以及所有 2024 年后上市公司的二级交易决策系统。

## 本版修复

上一版包含中文 `.bat` 文件名，部分 Windows 解压环境会显示乱码。本版已经全部改成英文文件名，避免乱码：

```text
00_setup_env.bat
run_daily_update_low_quota.bat
run_daily_update_dry_run.bat
process_ifind_exports_offline.bat
build_ifind_field_mapping_offline.bat
```

## 本版新增：iFind 字段映射准备

为避免为了 `p05310_f001`、`p03764_f001`、`p03412_f001` 这类字段名反复消耗 iFind API 额度，本版新增离线字段映射脚本：

```text
scripts/build_ifind_field_mapping_from_exports.py
build_ifind_field_mapping_offline.bat
```

用法：把之前 iFind 原始导出的 Excel/CSV 放入 `ifind_exports/`，然后双击：

```text
build_ifind_field_mapping_offline.bat
```

系统会输出：

```text
config/ifind_field_mapping_auto.csv
deploy_data/ifind_field_mapping_auto.csv
```

## 第一次使用

双击：

```text
00_setup_env.bat
```

## 每天 16:30 更新

双击：

```text
run_daily_update_low_quota.bat
```

低额度策略：

```text
1. 静态表只拉近端窗口。
2. 日行情尽量增量拉取。
3. 收盘快照只拉 2024+ IPO 股票池。
4. 失败不无限重试，保留昨日数据并写日志。
```

如果只是想测试流程、不消耗 iFind API 额度，双击：

```text
run_daily_update_dry_run.bat
```

## 不调用 API 的兜底方式

把 iFind 导出的 Excel/CSV 放入：

```text
ifind_exports/
```

然后双击：

```text
process_ifind_exports_offline.bat
```

这个流程会先生成字段映射，再处理离线导出文件，不调用 iFind API，不消耗额度。

## 本地运行看页面

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Streamlit Cloud 部署

将本项目根目录上传 GitHub，并在 Streamlit Cloud 中选择：

```text
streamlit_app.py
```

## iFind 账号配置

复制：

```text
config/local_ifind_credentials.example.ini
```

改名为：

```text
config/local_ifind_credentials.ini
```

填写账号密码。该文件已加入 `.gitignore`，不会上传 GitHub。

也可以使用环境变量：

```text
IFIND_USERNAME
IFIND_PASSWORD
```

## 重要文件

```text
config/ifind_api_commands.txt                 # 已收录 iFind API 命令
config/ifind_update_config.json               # 更新频率、缓存、窗口和批量参数
config/ifind_field_mapping_auto.csv           # 离线反推字段映射输出
scripts/ifind_low_quota_daily_update.py       # 主更新引擎
scripts/build_ifind_field_mapping_from_exports.py # 字段映射反推脚本
scripts/build_technical_signals.py            # 专业技术分析模块
logs/update_YYYYMMDD.log                      # 每次更新日志
deploy_data/data_update_status.csv            # 页面展示的数据更新状态
```

## 下一版处理清单

已经写入：

```text
docs/next_version_plan.md
```

重点包括：

```text
1. iFind字段映射接入主流程。
2. 精确解禁事件标准化。
3. 解禁影响规律模型。
4. 专业技术评分真正纳入二级交易评分。
5. 评分科学性验证。
6. 低额度日度更新增强。
```

更多说明见：

```text
docs/daily_update_engine.md
docs/ifind_api_low_quota_policy.md
docs/technical_analysis_methodology.md
docs/windows_filename_fix.md
docs/next_version_plan.md
```
