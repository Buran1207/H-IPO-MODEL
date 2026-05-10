# iFind 超级命令取数目标 - Step 3

这一阶段不要追求一次性字段完美，先让四类取数能跑通。

## 1. A1 / 未上市 IPO 管线

在超级命令里尝试：

```text
港股 A1 递表 临时代码 发行人 招股书 公告日期 保荐人 预期上市日期
```

需要落地到：

```text
deploy_data/a1_ipo_pipeline.csv
```

优先字段：

```text
security_key,temp_code,code,name,issuer_name,lifecycle_stage,a1_date,hearing_date,prospectus_date,expected_listing_date,listing_date,industry,sponsor_names,prospectus_title,prospectus_url,key_risks,notes
```

## 2. 单票招股书资料

超级命令示例：

```text
某临时代码 招股书 招股价区间 募资金额 发行市值 保荐人 基石投资者 募资用途 风险因素
```

落地字段：

```text
offer_price_low,offer_price_high,fundraising_amount_hkd,market_cap_at_ipo_hkd,sponsor_names,cornerstone_names,prospectus_title,prospectus_url,key_risks
```

## 3. 单票配发结果公告

超级命令示例：

```text
某代码 配发结果公告 最终发行价 公开认购倍数 国际配售倍数 一手中签率 回拨比例 基石认购金额 上市日期
```

需要落地到：

```text
deploy_data/ipo_offer_results.csv
```

优先字段：

```text
issue_price,final_price_position,public_subscription_multiple,international_subscription_multiple,one_lot_success_rate,clawback_ratio,cornerstone_amount_hkd,cornerstone_ratio,allotment_result_title,allotment_result_url
```

## 4. 上市后 0-180D 行情

超级命令示例：

```text
某正式代码 日行情 上市日期至上市后180天 开盘价 最高价 最低价 收盘价 成交量 成交额 换手率
```

抓取频率：

```text
D0-D30：每日
D31-D90：每3个交易日
D91-D180：每周
触发破发、放量、重新站回发行价、创新高时临时加密
```

可以先运行：

```powershell
python scripts/make_quote_sampling_plan.py
```

生成：

```text
local_outputs/quote_sampling_plan.csv
```
