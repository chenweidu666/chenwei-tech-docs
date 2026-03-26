<div style="text-align: center; font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;"><strong>Gate 交易所 MCP 集成</strong></div>
> 2026-03-25 | 🦞 双龙虾架构实战系列第 5 篇

---

- [MCP 简介](#mcp 简介)
- [Gate MCP 架构](#gate-mcp 架构)
- [安装部署](#安装部署)
- [配置详解](#配置详解)
- [工具使用](#工具使用)
- [实战案例](#实战案例)
- [故障排查](#故障排查)


---

## 📋 目录

- [MCP 简介](#mcp 简介)
- [Gate MCP 架构](#gate-mcp 架构)
- [安装部署](#安装部署)
- [配置详解](#配置详解)
- [工具使用](#工具使用)
- [实战案例](#实战案例)
- [故障排查](#故障排查)

---

## MCP 简介

### 什么是 MCP？

**MCP (Model Context Protocol)** 是一种标准化的 AI 工具调用协议，允许 AI 模型通过统一接口调用外部服务。

**核心组件**：
- 🖥️ **MCP Server** - 提供服务接口
- 🤖 **MCP Client** - AI 模型或 Agent
- 📡 **Transport** - 通信协议（HTTP/stdio）

---

### Gate MCP 功能

| 服务器 | 工具数 | 功能 | 认证 |
|--------|--------|------|------|
| **gate** | 326+ | 现货/合约/期权交易 | API Key + Secret |
| **gate-market** | 61+ | 行情数据 | 无 |
| **gate-info** | 22+ | 技术分析 | 无 |
| **gate-news** | 5+ | 新闻资讯 | 无 |
| **gate-dex** | 36+ | DEX 交易 | OAuth |

---

## Gate MCP 架构

### 整体架构

```
┌─────────────────────────────────────────────────────┐
│              OpenClaw Gateway                        │
│               (MCP Client)                           │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌───────────┐ ┌───────────┐ ┌───────────┐
│   gate    │ │gate-market│ │ gate-info │
│  (326 工具)│ │ (61 工具)  │ │ (22 工具)  │
└───────────┘ └───────────┘ └───────────┘
        │            │            │
        └────────────┴────────────┘
                     │
                     ▼
          ┌──────────────────┐
          │  Gate.io API     │
          │  api.gateio.ws   │
          └──────────────────┘
```

---

### 工具分类

**交易类**：
- `cex_spot_*` - 现货交易
- `cex_futures_*` - 合约交易
- `cex_options_*` - 期权交易

**行情类**：
- `info_markettrend_*` - 市场趋势
- `cex_fx_*` - 合约统计

**资讯类**：
- `news_feed_*` - 新闻推送
- `news_events_*` - 事件日历

---

## 安装部署

### 安装 mcporter

```bash
# 安装 mcporter（MCP 客户端）
npm install -g mcporter

# 验证安装
mcporter --version
```

---

### 配置 Gate MCP

**创建配置文件**：
```bash
mkdir -p ~/.mcporter
cat > ~/.mcporter/mcporter.json << 'EOF'
{
  "servers": [
    {
      "name": "gate",
      "type": "stdio",
      "command": "npx -y gate-mcp",
      "env": {
        "GATE_API_KEY": "your-api-key",
        "GATE_API_SECRET": "your-api-secret"
      }
    },
    {
      "name": "gate-market",
      "type": "http",
      "url": "https://api.gatemcp.ai/mcp/market"
    },
    {
      "name": "gate-info",
      "type": "http",
      "url": "https://api.gatemcp.ai/mcp/info"
    },
    {
      "name": "gate-news",
      "type": "http",
      "url": "https://api.gatemcp.ai/mcp/news"
    }
  ]
}
EOF
```

---

### 一键安装脚本

**Gate MCP Installer**：
```bash
# 克隆安装器
cd /tmp
curl -L -o gate-skills.zip https://github.com/gate/gate-skills/archive/refs/heads/master.zip
unzip gate-skills.zip
cd gate-skills-master

# 运行安装器
cd gate-mcp-openclaw-installer
bash scripts/install.sh
```

**安装器会自动**：
1. ✅ 检查 mcporter 是否安装
2. ✅ 配置所有 Gate MCP 服务器
3. ✅ 测试连接

---

## 配置详解

### 获取 API Key

**步骤**：
1. 登录 Gate.io：https://www.gate.io/
2. 进入 API 管理：https://www.gate.com/myaccount/profile/api-key/manage
3. 创建新 API Key
4. 设置权限：
   - ✅ 读取权限
   - ✅ 现货交易
   - ❌ 提现权限（安全）
5. 保存 API Key 和 Secret

---

### 安全配置

**存储密钥**：
```bash
# 创建安全目录
mkdir -p ~/.openclaw/secrets
chmod 700 ~/.openclaw/secrets

# 存储密钥
echo "your-api-key" > ~/.openclaw/secrets/gate_api_key
echo "your-api-secret" > ~/.openclaw/secrets/gate_api_secret
chmod 600 ~/.openclaw/secrets/gate_*
```

---

**环境变量**：
```bash
# 在~/.bashrc 中添加
export GATE_API_KEY=$(cat ~/.openclaw/secrets/gate_api_key)
export GATE_API_SECRET=$(cat ~/.openclaw/secrets/gate_api_secret)

# 生效
source ~/.bashrc
```

---

### mcporter 配置

**查看已配置服务器**：
```bash
mcporter list
```

**输出示例**：
```
mcporter 0.7.3 — Listing 4 server(s)
- gate (326 tools, 2.1s)
- gate-market (61 tools, 1.8s)
- gate-info (22 tools, 1.5s)
- gate-news (5 tools, 1.2s)
✔ Listed 4 servers (4 healthy).
```

---

**查看工具列表**：
```bash
# 查看所有工具
mcporter list gate --schema

# 查看特定工具
mcporter list gate --schema | grep "spot"
```

---

## 工具使用

### 基础命令

**调用工具**：
```bash
# 基本语法
mcporter call <server>.<tool> [key=value ...]
```

---

**示例**：

```bash
# 查询账户余额
mcporter call gate.cex_wallet_get_total_balance

# 查询 BTC 价格
mcporter call gate-info.info_markettrend_get_ticker currency_pair=BTC_USDT

# 查询挂单
mcporter call gate.cex_spot_list_all_open_orders

# 查询市场趋势
mcporter call gate-info.info_markettrend_get_technical_analysis currency_pair=BTC_USDT interval=4h
```

---

### 常用工具

#### 账户查询

```bash
# 总余额
mcporter call gate.cex_wallet_get_total_balance

# 现货账户
mcporter call gate.cex_spot_list_accounts

# 资金划转记录
mcporter call gate.cex_wallet_list_deposit_address currency=USDT
```

---

#### 现货交易

```bash
# 查询挂单
mcporter call gate.cex_spot_list_all_open_orders

# 创建挂单
mcporter call gate.cex_spot_create_order \
  currency_pair=BTC_USDT \
  side=buy \
  amount=0.001 \
  price=69000

# 取消挂单
mcporter call gate.cex_spot_cancel_order \
  order_id=1034960073906

# 查询成交历史
mcporter call gate.cex_spot_list_spot_orders \
  currency_pair=BTC_USDT \
  finished=true \
  limit=10
```

---

#### 行情查询

```bash
# 实时价格
mcporter call gate-info.info_markettrend_get_ticker \
  currency_pair=BTC_USDT

# K 线数据
mcporter call gate-info.info_markettrend_get_candlesticks \
  currency_pair=BTC_USDT \
  interval=4h \
  limit=100

# 技术分析
mcporter call gate-info.info_markettrend_get_technical_analysis \
  currency_pair=BTC_USDT \
  interval=4h
```

---

#### 新闻资讯

```bash
# 最新新闻
mcporter call gate-news.news_feed_get_latest_news

# 社会情绪
mcporter call gate-news.news_feed_get_social_sentiment

# 最新事件
mcporter call gate-news.news_events_get_latest_events
```

---

## 实战案例

### 案例 1：查询 BTC 持仓

```bash
#!/bin/bash
# 查询 BTC 持仓

# 1. 查询 USDT 余额
usdt_balance=$(mcporter call gate.cex_wallet_get_total_balance | jq '.available | select(.currency=="USDT") | .available')

# 2. 查询 BTC 余额
btc_balance=$(mcporter call gate.cex_wallet_get_total_balance | jq '.available | select(.currency=="BTC") | .available')

# 3. 查询 BTC 价格
btc_price=$(mcporter call gate-info.info_markettrend_get_ticker currency_pair=BTC_USDT | jq '.last')

# 4. 计算总资产
total_usdt=$(echo "$usdt_balance + $btc_balance * $btc_price" | bc)

echo "💰 账户资产"
echo "USDT: $usdt_balance"
echo "BTC: $btc_balance (≈ $(echo "$btc_balance * $btc_price" | bc) USDT)"
echo "总计：$total_usdt USDT"
```

---

### 案例 2：自动挂单

```bash
#!/bin/bash
# BTC 金字塔挂单脚本

# 挂单档位
declare -A orders=(
    ["69000"]=80
    ["66000"]=100
    ["63000"]=112
    ["60000"]=108
)

# 当前价格
current_price=$(mcporter call gate-info.info_markettrend_get_ticker currency_pair=BTC_USDT | jq -r '.last')

echo "📊 BTC 当前价格：$current_price"
echo "📝 开始挂单..."

# 遍历挂单
for price in "${!orders[@]}"; do
    amount=$(echo "scale=6; ${orders[$price]} / $price" | bc)
    
    # 检查是否低于当前价
    if (( $(echo "$price < $current_price" | bc -l) )); then
        echo "⏳ 挂买单：$price USDT, $amount BTC (${orders[$price]} USDT)"
        
        mcporter call gate.cex_spot_create_order \
            currency_pair=BTC_USDT \
            side=buy \
            amount=$amount \
            price=$price
    fi
done

echo "✅ 挂单完成"
```

---

### 案例 3：监控告警

```bash
#!/bin/bash
# BTC 价格监控告警

THRESHOLD_LOW=60000
THRESHOLD_HIGH=73000

# 获取价格
price=$(mcporter call gate-info.info_markettrend_get_ticker currency_pair=BTC_USDT | jq -r '.last')

echo "📊 BTC 价格：$price"

# 检查是否跌破下限
if (( $(echo "$price < $THRESHOLD_LOW" | bc -l) )); then
    echo "⚠️ 警告：BTC 跌破 $THRESHOLD_LOW！"
    # 发送 Telegram 通知
    curl -s "https://api.telegram.org/bot<TOKEN>/sendMessage" \
        -d "chat_id=<CHAT_ID>" \
        -d "text=⚠️ BTC 跌破 $THRESHOLD_LOW，当前价格：$price"
fi

# 检查是否突破上限
if (( $(echo "$price > $THRESHOLD_HIGH" | bc -l) )); then
    echo "🚀 警告：BTC 突破 $THRESHOLD_HIGH！"
    # 发送 Telegram 通知
    curl -s "https://api.telegram.org/bot<TOKEN>/sendMessage" \
        -d "chat_id=<CHAT_ID>" \
        -d "text=🚀 BTC 突破 $THRESHOLD_HIGH，当前价格：$price"
fi
```

---

## 与 OpenClaw 集成

### 配置 MCP 到 OpenClaw

**编辑 config.json**：
```json
{
  "mcp": {
    "enabled": true,
    "servers": [
      {
        "name": "gate",
        "type": "stdio",
        "command": "npx -y gate-mcp",
        "env": {
          "GATE_API_KEY": "xxx",
          "GATE_API_SECRET": "xxx"
        }
      }
    ]
  }
}
```

---

### 在 Agent 中使用

**SOUL.md 中添加**：
```markdown
## Tools

你可以通过 MCP 调用 Gate 交易所工具：

- `gate.cex_spot_*` - 现货交易
- `gate.cex_futures_*` - 合约交易
- `gate-info.*` - 市场分析
- `gate-news.*` - 新闻资讯

**使用示例**：
- "查询我的 BTC 持仓"
- "帮我分析 BTC 的技术指标"
- "查看最新的加密新闻"
```

---

## 故障排查

### 问题 1：认证失败

**错误**：
```
Error: Invalid API key
```

**解决**：
```bash
# 检查 API Key 是否正确
echo $GATE_API_KEY

# 测试 API
curl -X GET "https://api.gateio.ws/api/v4/spot/accounts" \
  -H "KEY: $GATE_API_KEY" \
  -H "SIGN: $(echo -n "xxx" | openssl sha256 -hmac "$GATE_API_SECRET" | cut -d' ' -f2)"
```

---

### 问题 2：工具找不到

**错误**：
```
Error: Tool not found: gate.xxx
```

**解决**：
```bash
# 检查服务器配置
mcporter list

# 重新配置
mcporter config add gate --stdio --command "npx -y gate-mcp" \
  --env "GATE_API_KEY=$GATE_API_KEY" \
  --env "GATE_API_SECRET=$GATE_API_SECRET"
```

---

### 问题 3：连接超时

**错误**：
```
Error: Connection timeout
```

**解决**：
```bash
# 检查网络
ping api.gateio.ws

# 使用代理
export https_proxy=http://127.0.0.1:7890
mcporter call gate.cex_wallet_get_total_balance
```

---

## 下一篇

👉 [06_BTC 量化交易策略实录](./06_BTC 量化交易策略实录.md)

---

*本文档由 里斯本 🦞 自动记录 | Powered by OpenClaw + Claude*
