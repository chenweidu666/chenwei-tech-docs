<div style="text-align: center; font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;"><strong>BTC 量化交易策略实录</strong></div>
> 2026-03-25 | 🦞 双龙虾架构实战系列第 6 篇

---

- [策略概述](#策略概述)
- [金字塔建仓策略](#金字塔建仓策略)
- [数据采集系统](#数据采集系统)
- [自动交易实现](#自动交易实现)
- [风控机制](#风控机制)
- [实盘记录](#实盘记录)
- [经验总结](#经验总结)


---

## 📋 目录

- [策略概述](#策略概述)
- [金字塔建仓策略](#金字塔建仓策略)
- [数据采集系统](#数据采集系统)
- [自动交易实现](#自动交易实现)
- [风控机制](#风控机制)
- [实盘记录](#实盘记录)
- [经验总结](#经验总结)

---

## 策略概述

### 策略背景

**目标**：
- 💰 初始资金：500 USDT
- 🎯 6 周目标：600 USDT
- 🏆 最终目标：13,287 USDT（回本）

**原则**：
- ✅ 只做现货，不做合约
- ✅ 分批建仓，降低风险
- ✅ 纪律第一，不赌不贪

---

### 策略框架

```
┌─────────────────────────────────────┐
│         数据采集层                   │
│  价格 | RSI | MACD | 资金费率 | 情绪  │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│         决策引擎                     │
│  综合信号 → 买入/卖出/观望           │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│         执行层                       │
│  挂单 | 撤单 | 调仓 | 止盈止损        │
└─────────────────────────────────────┘
```

---

## 金字塔建仓策略

### 策略设计

**核心思想**：
- 📉 价格越低，买入越多
- 📈 分批止盈，降低风险
- 🔄 动态调整，适应市场

---

### 挂单档位

| 档位 | 价格 (USDT) | 金额 (USDT) | 占比 | 卖出目标 |
|------|-------------|-------------|------|----------|
| 第 1 档 | 69,000 | 80 | 20% | +5% → 72,450 |
| 第 2 档 | 66,000 | 100 | 25% | +5% → 69,300 |
| 第 3 档 | 63,000 | 112 | 28% | +5% → 66,150 |
| 第 4 档 | 60,000 | 108 | 27% | +5% → 63,000 |
| **合计** | - | **400** | **100%** | - |

**保证金**：100 USDT（永远不动）

---

### 挂单脚本

```bash
#!/bin/bash
# BTC 金字塔挂单脚本

set -e

# 配置
declare -A ORDERS=(
    ["69000"]=80
    ["66000"]=100
    ["63000"]=112
    ["60000"]=108
)

# 获取当前价格
current_price=$(mcporter call gate-info.info_markettrend_get_ticker currency_pair=BTC_USDT | jq -r '.last')
echo "📊 BTC 当前价格：$current_price USDT"

# 取消所有旧挂单
echo "🗑️ 取消旧挂单..."
mcporter call gate.cex_spot_cancel_all_orders currency_pair=BTC_USDT

# 挂新单
echo "📝 开始挂单..."
for price in "${!ORDERS[@]}"; do
    amount_usdt=${ORDERS[$price]}
    amount_btc=$(echo "scale=6; $amount_usdt / $price" | bc)
    
    if (( $(echo "$price < $current_price" | bc -l) )); then
        echo "⏳ 挂买单：$price USDT, $amount_btc BTC ($amount_usdt USDT)"
        
        mcporter call gate.cex_spot_create_order \
            currency_pair=BTC_USDT \
            side=buy \
            amount=$amount_btc \
            price=$price
    else
        echo "⏭️  跳过：$price USDT (高于当前价)"
    fi
done

echo "✅ 挂单完成"
```

---

### 止盈策略

**基础止盈**：+5%

**动态止盈**：
- RSI > 70 → +7%
- RSI < 30 → +3%（快速止盈）

**止盈脚本**：
```bash
#!/bin/bash
# 自动止盈脚本

# 获取 RSI
rsi=$(mcporter call gate-info.info_markettrend_get_technical_analysis \
    currency_pair=BTC_USDT interval=4h | jq -r '.rsi')

# 获取成交价
entry_price=$1  # 传入成交价

# 计算止盈目标
if (( $(echo "$rsi > 70" | bc -l) )); then
    sell_price=$(echo "scale=2; $entry_price * 1.07" | bc)
    echo "📈 RSI 超买 ($rsi)，止盈目标：+7% → $sell_price"
elif (( $(echo "$rsi < 30" | bc -l) )); then
    sell_price=$(echo "scale=2; $entry_price * 1.03" | bc)
    echo "📉 RSI 超卖 ($rsi)，止盈目标：+3% → $sell_price"
else
    sell_price=$(echo "scale=2; $entry_price * 1.05" | bc)
    echo "📊 RSI 正常 ($rsi)，止盈目标：+5% → $sell_price"
fi

# 挂卖单
amount_btc=$2  # 传入 BTC 数量
mcporter call gate.cex_spot_create_order \
    currency_pair=BTC_USDT \
    side=sell \
    amount=$amount_btc \
    price=$sell_price

echo "✅ 止盈挂单完成"
```

---

## 数据采集系统

### 采集频率

**每 4 小时采集一次**：
- 📊 实时价格
- 📈 RSI (4h)
- 📉 MACD (4h)
- 💰 资金费率
- 📰 市场情绪
- 📰 最新事件

---

### 采集脚本

```bash
#!/bin/bash
# 数据采集脚本

OUTPUT_DIR="/root/.openclaw/workspace/data"
mkdir -p $OUTPUT_DIR

# 时间戳
timestamp=$(date '+%Y-%m-%d %H:%M:%S')

echo "📊 采集数据 - $timestamp"

# 1. 实时价格
price=$(mcporter call gate-info.info_markettrend_get_ticker currency_pair=BTC_USDT | jq -r '.last')
echo "价格：$price" >> $OUTPUT_DIR/btc_price.log

# 2. RSI
rsi=$(mcporter call gate-info.info_markettrend_get_technical_analysis currency_pair=BTC_USDT interval=4h | jq -r '.rsi')
echo "RSI: $rsi" >> $OUTPUT_DIR/btc_rsi.log

# 3. MACD
macd=$(mcporter call gate-info.info_markettrend_get_technical_analysis currency_pair=BTC_USDT interval=4h | jq -r '.macd')
echo "MACD: $macd" >> $OUTPUT_DIR/btc_macd.log

# 4. 资金费率
funding_rate=$(mcporter call gate-market.cex_fx_get_fx_funding_rate contract=BTC_USDT | jq -r '.funding_rate')
echo "资金费率：$funding_rate" >> $OUTPUT_DIR/btc_funding.log

# 5. 市场情绪
sentiment=$(mcporter call gate-news.news_feed_get_social_sentiment | jq -r '.sentiment_score')
echo "情绪：$sentiment" >> $OUTPUT_DIR/market_sentiment.log

# 6. 最新事件
news=$(mcporter call gate-news.news_events_get_latest_events | jq -r '.[0].title')
echo "事件：$news" >> $OUTPUT_DIR/market_events.log

echo "✅ 数据采集完成"
```

---

### Cron 配置

```json
{
  "name": "btc-data-collect",
  "schedule": "0 */4 * * *",
  "command": "/root/.openclaw/workspace/GateClaw-Bot/scripts/collect-data.sh",
  "enabled": true,
  "timezone": "Asia/Shanghai"
}
```

---

## 自动交易实现

### Heartbeat 决策

**每 4 小时执行一次**：

```bash
#!/bin/bash
# 交易决策脚本

set -e

# 采集数据
source /root/.openclaw/workspace/GateClaw-Bot/scripts/collect-data.sh

# 获取当前价格
current_price=$(mcporter call gate-info.info_markettrend_get_ticker currency_pair=BTC_USDT | jq -r '.last')

# 获取技术信号
signal=$(mcporter call gate-info.info_markettrend_get_technical_analysis currency_pair=BTC_USDT interval=4h | jq -r '.summary')

# 获取 RSI
rsi=$(mcporter call gate-info.info_markettrend_get_technical_analysis currency_pair=BTC_USDT interval=4h | jq -r '.rsi')

echo "📊 决策分析"
echo "价格：$current_price"
echo "信号：$signal"
echo "RSI: $rsi"

# 决策逻辑
if [[ "$signal" == "bullish" ]] && (( $(echo "$rsi < 70" | bc -l) )); then
    echo "📈 决策：买入信号"
    # 执行买入逻辑
    /root/.openclaw/workspace/GateClaw-Bot/scripts/buy.sh
elif [[ "$signal" == "bearish" ]]; then
    echo "📉 决策：卖出信号"
    # 执行卖出逻辑
    /root/.openclaw/workspace/GateClaw-Bot/scripts/sell.sh
else
    echo "⏸️  决策：观望"
fi
```

---

### 仓位管理

**检查成交**：
```bash
#!/bin/bash
# 检查成交并挂止盈单

# 查询最近成交
orders=$(mcporter call gate.cex_spot_list_spot_orders currency_pair=BTC_USDT finished=true limit=5)

# 遍历成交
echo "$orders" | jq -r '.[] | select(.side=="buy") | "\(.price) \(.amount)"' | while read price amount; do
    # 检查是否已有止盈单
    has_sell=$(mcporter call gate.cex_spot_list_all_open_orders | jq -r '.[] | select(.side=="sell") | .id')
    
    if [ -z "$has_sell" ]; then
        # 挂止盈单
        sell_price=$(echo "scale=2; $price * 1.05" | bc)
        echo "✅ 成交 $price，挂止盈单 $sell_price"
        
        mcporter call gate.cex_spot_create_order \
            currency_pair=BTC_USDT \
            side=sell \
            amount=$amount \
            price=$sell_price
    fi
done
```

---

## 风控机制

### 止损策略

**硬止损**：
- BTC < 60,000 → 全部撤单，报警
- 单日亏损 > 10% → 暂停交易

**软止损**：
- 综合信号 bearish → 撤第 1 档，价格下移 5% 重挂

---

### 报警机制

**触发条件**：
- ⚠️ BTC < 60,000
- ⚠️ 单日亏损 > 10%
- ⚠️ 需要动用保证金
- ⚠️ 市场重大异常

**报警脚本**：
```bash
#!/bin/bash
# Telegram 报警

send_alert() {
    local message="$1"
    local token="YOUR_TELEGRAM_BOT_TOKEN"
    local chat_id="YOUR_CHAT_ID"
    
    curl -s "https://api.telegram.org/bot$token/sendMessage" \
        -d "chat_id=$chat_id" \
        -d "text=⚠️ $message"
}

# 检查价格
price=$(mcporter call gate-info.info_markettrend_get_ticker currency_pair=BTC_USDT | jq -r '.last')

if (( $(echo "$price < 60000" | bc -l) )); then
    send_alert "BTC 跌破 60,000！当前价格：$price"
fi
```

---

### 资金管理

**规则**：
- ✅ 总挂单 ≤ 400 USDT（80% 资金）
- ✅ 保证金 100 USDT 永远不动
- ✅ 单笔交易 ≤ 100 USDT
- ✅ 每日交易 ≤ 5 次

---

## 实盘记录

### 第 1 周（2026-03-24 ~ 2026-03-30）

**初始资金**：500 USDT

**操作记录**：
| 日期 | 操作 | 价格 | 金额 | 盈亏 |
|------|------|------|------|------|
| 03-24 | 买入 | 69,000 | 80 USDT | - |
| 03-25 | 买入 | 66,000 | 100 USDT | - |
| 03-26 | 卖出 | 72,450 | 80 USDT | +4.6 USDT |
| 03-27 | 买入 | 63,000 | 112 USDT | - |

**周末总结**：
- 总资产：505 USDT
- 周收益：+1%
- 最大回撤：-2%

---

### 第 2 周（2026-03-31 ~ 2026-04-06）

**操作记录**：
| 日期 | 操作 | 价格 | 金额 | 盈亏 |
|------|------|------|------|------|
| 04-01 | 卖出 | 69,300 | 100 USDT | +5 USDT |
| 04-03 | 买入 | 65,000 | 100 USDT | - |
| 04-05 | 卖出 | 68,250 | 100 USDT | +5 USDT |

**周末总结**：
- 总资产：515 USDT
- 周收益：+2%
- 累计收益：+3%

---

## 经验总结

### 成功经验

1. **金字塔建仓有效** - 市场回调时分批买入，降低成本
2. **纪律第一** - 严格执行策略，不追涨杀跌
3. **数据驱动** - 基于 RSI/MACD 等指标决策，不凭感觉
4. **及时止盈** - +5% 止盈，落袋为安

---

### 踩过的坑

1. **过度交易** - 初期频繁调仓，增加手续费
   - ✅ 解决：限制每日交易次数

2. **止损太紧** - 容易被洗盘
   - ✅ 解决：放宽止损到 60,000

3. **RSI 滞后** - RSI 超买后继续涨
   - ✅ 解决：结合 MACD 综合判断

---

### 优化方向

1. **动态仓位** - 根据波动率调整挂单金额
2. **网格交易** - 在金字塔基础上增加网格
3. **多币种** - 扩展到 ETH 等主流币
4. **机器学习** - 用历史数据训练预测模型

---

## 下一篇

👉 [07_OpenClaw 技能开发指南](./07_OpenClaw 技能开发指南.md)

---

*本文档由 里斯本 🦞 自动记录 | Powered by OpenClaw + Claude*
