# Step 8 模型说明

## 目标

Step 8 不追求一次性建立黑箱机器学习模型，而是把可解释、可复盘、可调参的规则模型先跑通。

## 因子组

- `issue_heat_score`：公开认购、孖展、一手中签率。
- `allocation_quality_score`：配售和中签结构，避免只看热度。
- `cornerstone_bank_score`：基石、账簿管理人、承销团、保荐人。
- `pricing_safety_score`：发行价在招股区间的位置及热度匹配。
- `gray_signal_score`：暗盘和首日信号。
- `post_listing_score`：上市后0-180D路径表现。
- `a1_maturity_score`：A1/上市申请阶段成熟度。
- `data_quality_score`：数据完整度。
- `risk_penalty_score`：拥挤交易、破发、升后破发、行情缺失等惩罚。

## 权重方案

配置文件：`config/step8_weight_profiles.json`

- `balanced`：均衡默认。
- `primary_ipo`：一级打新优先。
- `secondary_trade`：二级交易优先。
- `anti_break`：防破发保守。
- `hot_market`：强势新股市。

## 回测标签

- `target_tradeable_20d`：20D最大涨幅 >= 15%，且20D最小跌幅不低于 -25%。
- `target_strong_or_deepv`：路径包含上市即强势、深V、修复、反弹。
- `target_bad_path`：路径包含破发、弱势、升后破发，或20D最大回撤低于 -20%。

## 使用方式

1. 先看 `decision_tier_step8`。
2. 再区分一级、基石、二级三套建议。
3. 最后看 `buy_trigger_step8` 和 `sell_trigger_step8`。
4. 对 A/B 票做人工基本面和估值复核。
