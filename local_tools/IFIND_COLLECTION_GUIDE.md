# iFind 取数字段清单

## 1. IPO/A1 项目池

超级命令搜索词：

```text
港股 A1 申请人 临时代码 Application Proof 招股书 保荐人 行业 递表日期
港股 IPO 申请人 临时代码 上市状态 递表日期 聆讯后资料集 招股书
```

目标导出到：`local_exports/ipo_projects.csv`

字段尽量包括：

```text
temp_code, code, name, project_status, a1_date, application_proof_date,
phip_date, prospectus_date, pricing_date, allotment_result_date,
expected_listing_date, listing_date, industry, business_summary,
sponsor_names, overall_coordinators, offer_price_low, offer_price_high,
issue_price, fundraising_amount_hkd, market_cap_at_ipo_hkd,
cornerstone_names, cornerstone_amount_hkd, cornerstone_ratio,
public_subscription_multiple, international_subscription_multiple,
one_lot_success_rate, clawback_ratio, doc_a1_url, doc_prospectus_url,
doc_allotment_url, notes
```

## 2. 发行文件 / 公告

超级命令搜索词：

```text
港股 IPO 招股书 文件链接 公告日期
港股 IPO 配发结果公告 公开认购倍数 国际配售倍数 一手中签率 回拨比例
港股 IPO Application Proof PHIP Prospectus Allotment Results
```

目标导出到：`local_exports/ipo_docs.csv`

字段尽量包括：

```text
temp_code, code, name, doc_type, doc_date, doc_name, doc_url,
local_file, extraction_status, key_fields_found, notes
```

## 3. 上市后行情

超级命令搜索词：

```text
06610.HK 日行情 开盘价 最高价 最低价 收盘价 成交量 成交额 换手率
港股 上市后 日K 开高低收 成交量 成交额 换手率
```

先导出原始日线到：`local_exports/price_daily_raw.csv`

字段尽量包括：

```text
code, name, listing_date, trade_date, open, high, low, close,
volume, amount, turnover_rate, issue_price
```

然后运行：

```powershell
python local_tools/build_deploy_data.py
```

它会自动生成：

```text
deploy_data/price_180d_sample.csv
```
