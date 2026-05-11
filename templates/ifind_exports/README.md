# iFind 导出文件放这里

本地更新时，把 iFind 一级市场界面导出的 CSV 放入本目录，推荐保留中文关键词文件名：

- 港股IPO首发信息一览.csv
- 港股IPO打新中签结果.csv
- 港股IPO基石投资者.csv
- 港股IPO孖展数据.csv
- 港股IPO承销团参与度-明细.xlsx.csv
- 港股IPO账簿管理人-明细.xlsx.csv

然后在项目根目录运行：

```bash
python scripts/build_deploy_data_from_ifind_exports.py --input-dir ifind_exports --outdir deploy_data
```
