# 港股 IPO / 半新股决策驾驶舱 - Step 5 Clean v3

这是一个干净仓库可直接上传的 Streamlit 版本，已解决上一版 CSV 乱码和文件混乱问题。

## 已接入数据

本版本已经接入以下 iFind 一级市场导出数据，并生成标准化 `deploy_data/*.csv`：

1. 港股IPO首发信息一览
2. 港股IPO打新中签结果
3. 港股IPO基石投资者
4. 港股IPO孖展数据
5. 港股IPO承销团参与度-明细
6. 港股IPO账簿管理人-明细

## 仍未接入的数据

当前数据源还不能称为完整，后续仍需补：

1. 上市申请一览：覆盖 A1、临时代码、处理中、聆讯、未上市申请公司。
2. IPO回拨统计：独立校验回拨比例。
3. IPO暗盘行情：上市前交易情绪。
4. 上市后0-180D行情：二级买点、深V、破发和卖点状态机。

## GitHub 上传方式

请只上传解压后的文件内容，不要上传 zip 包本身。

根目录应包含：

```text
streamlit_app.py
requirements.txt
README.md
.gitignore
.streamlit/config.toml
deploy_data/
scripts/
docs/
templates/
```

不要把 CSV 内容复制进 `streamlit_app.py`。`streamlit_app.py` 只能是 Python 代码。

## 本地运行

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 本地更新数据

1. 在 iFind 导出 CSV。
2. 放入本地 `ifind_exports/` 文件夹。
3. 运行：

```bash
python scripts/build_deploy_data_from_ifind_exports.py --input-dir ifind_exports --outdir deploy_data
```

4. 上传新的 `deploy_data/` 到 GitHub。

## 编码说明

所有标准化 CSV 均使用 `utf-8-sig` 输出，兼容 Excel、GitHub 和 Streamlit，尽量避免中文乱码。
