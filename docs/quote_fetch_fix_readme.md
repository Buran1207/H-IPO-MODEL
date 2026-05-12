# 0-180D 免费行情抓取修复说明

## 修复点

这版脚本只抓：

- 上市日期 >= 2024-01-01
- 上市日期 <= 今天
- 已有正式港股交易代码的股票
- 从上市日到 `min(上市日+180天, 今天)` 的日行情

自动跳过：

- 2024 年以前上市的老股票
- H2556.HK 这类临时代码/未上市申请公司
- 上市日在未来的公司
- 非标准港股交易代码

## 覆盖文件

把本包里的两个文件上传覆盖到 GitHub 的 `scripts/` 文件夹：

```text
scripts/fetch_free_hk_quotes_180d.py
scripts/build_post_listing_paths.py
```

## 本地运行命令

在项目根目录运行：

```bat
python scripts\fetch_free_hk_quotes_180d.py --pool deploy_data\ipo_decision_pool.csv --out deploy_data\ipo_daily_quotes_180d.csv
python scripts\build_post_listing_paths.py --update-pool
```

## 先测试 10 只

如果担心又全失败，先跑：

```bat
python scripts\fetch_free_hk_quotes_180d.py --pool deploy_data\ipo_decision_pool.csv --out deploy_data\ipo_daily_quotes_180d.csv --limit 10
```

成功后再去掉 `--limit 10` 全量跑。

## 结果文件

```text
deploy_data/ipo_daily_quotes_180d.csv
deploy_data/ipo_post_listing_paths.csv
deploy_data/ipo_quote_fetch_failures.csv
deploy_data/ipo_quote_fetch_skipped.csv
```

失败文件不代表系统失败，常见原因：极新股免费源尚无数据、临时代码、停牌/未上市、免费源暂时访问失败。
