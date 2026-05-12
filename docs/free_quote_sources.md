# 免费行情与回拨数据方案

## 0-180D日行情

本项目的免费脚本 `scripts/fetch_free_hk_quotes_180d.py` 采用两级来源：

1. Yahoo Finance / yfinance：优先使用，覆盖港股常见代码如 `0700.HK`、`6610.HK`。
2. Stooq CSV：作为备用来源，使用 `https://stooq.com/q/d/l/?s=0700.hk&d1=YYYYMMDD&d2=YYYYMMDD&i=d` 格式。

限制：

- 免费源通常只有 OHLCV，没有港股真实成交额、换手率、盘口和逐笔成交。
- 脚本会生成 `amount_est_hkd = 典型价 * 成交量`，仅用于状态机辅助。
- 临时代码 `Hxxxx.HK` 未正式上市前没有二级行情。

## IPO回拨统计

iFind没有独立回拨统计时，优先使用以下替代：

1. 首发信息一览中的公开发售/国际配售股份数、公开认购倍数、国际配售倍数。
2. HKEXnews 配发结果公告中的「Reallocation / 回拨」段落。
3. 先不把回拨作为硬性字段，模型用“公开认购倍数 + 一手中签率 + 孖展倍数 + 暗盘表现”替代衡量散户拥挤和流通冲击。
