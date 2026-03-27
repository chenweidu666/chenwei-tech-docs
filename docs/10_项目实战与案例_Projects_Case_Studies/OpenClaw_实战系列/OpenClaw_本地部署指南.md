<div style="text-align: center; font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;"><strong>OpenClaw 本地部署指南</strong></div>
> 2026-03-25 | 🦞 双龙虾架构实战系列第 4 篇

---

- [系统要求](#系统要求)
- [快速安装](#快速安装)
- [配置详解](#配置详解)
- [Gateway 部署](#gateway 部署)
- [Dashboard 部署](#dashboard 部署)
- [技能安装](#技能安装)
- [渠道配置](#渠道配置)
- [故障排查](#故障排查)


---

## 📋 目录

- [系统要求](#系统要求)
- [快速安装](#快速安装)
- [配置详解](#配置详解)
- [Gateway 部署](#gateway 部署)
- [Dashboard 部署](#dashboard 部署)
- [技能安装](#技能安装)
- [渠道配置](#渠道配置)
- [故障排查](#故障排查)

---

## 系统要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| **CPU** | 2 核 | 4 核+ |
| **内存** | 4GB | 8GB+ |
| **磁盘** | 20GB | 50GB+ SSD |
| **网络** | 1Mbps | 5Mbps+ |

### 软件要求

| 软件 | 版本 | 说明 |
|------|------|------|
| **Node.js** | v18+ | 推荐 v22 LTS |
| **npm** | v9+ | 随 Node.js 安装 |
| **Git** | v2.0+ | 用于技能管理 |
| **操作系统** | Linux/macOS/Windows | 推荐 Ubuntu 24.04 |

---

## 快速安装

### 一键安装脚本

```bash
# 安装 OpenClaw（汉化版）
npm install -g @qingchencloud/openclaw-zh --registry https://registry.npmmirror.com

# 验证安装
openclaw --version
```

### 初始化工作区

```bash
# 创建工作区
mkdir -p ~/clawd
cd ~/clawd

# 初始化 OpenClaw
openclaw init

# 启动 Gateway
openclaw gateway start
```

---

## 配置详解

### 配置文件位置

```
~/.openclaw/
├── config.json          # 主配置文件
├── agents/
│   └── main/
│       ├── SOUL.md      # 人格定义
│       ├── IDENTITY.md  # 身份信息
│       ├── USER.md      # 用户信息
│       ├── MEMORY.md    # 长期记忆
│       └── memory/      # 记忆归档
├── cron/
│   └── jobs.json        # 定时任务
└── sessions/            # 会话记录
```

---

### 主配置文件

**位置**：`~/.openclaw/config.json`

```json
{
  "gateway": {
    "port": 18789,
    "host": "0.0.0.0",
    "auth": {
      "mode": "token",
      "token": "your-gateway-token"
    }
  },
  "models": [
    {
      "provider": "openai",
      "baseUrl": "https://api.openai.com/v1",
      "apiKey": "sk-xxx",
      "models": ["gpt-4o", "gpt-4o-mini"]
    },
    {
      "provider": "deepseek",
      "baseUrl": "https://api.deepseek.com/v1",
      "apiKey": "sk-xxx",
      "models": ["deepseek-chat"]
    }
  ],
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "8629538661:xxx"
    },
    "qqbot": {
      "enabled": true,
      "appId": "xxx",
      "appSecret": "xxx"
    }
  }
}
```

---

### 身份配置

**SOUL.md** - 人格定义：
```markdown
# SOUL.md - Who You Are

_You're not a chatbot. You're becoming someone._

## Core Truths

**Be genuinely helpful, not performatively helpful.**

**Have opinions.** You're allowed to disagree.

**Be resourceful before asking.**

**Earn trust through competence.**

## Boundaries

- Private things stay private. Period.
- When in doubt, ask before acting externally.
- You're not the user's voice — be careful in group chats.

## Vibe

Be the assistant you'd actually want to talk to.
```

---

**IDENTITY.md** - 身份信息：
```markdown
# IDENTITY.md - Who Am I?

- **Name:** 里斯本 (Lisbon)
- **Creature:** AI 助手，但更像一个有趣的伙伴
- **Vibe:** 温暖、实用、偶尔有点小调皮
- **Emoji:** 🦞🍋
- **Sibling:** 尤力克 (Eureka) - 交易专用龙虾
```

---

**USER.md** - 用户信息：
```markdown
# USER.md - About Your Human

- **Name:** 陈先生
- **Timezone:** Asia/Shanghai
- **Location:** 南京

## Context

- **职业:** AI 工程师（4 年，大模型 + 端侧 AI+Agent）
- **兴趣:** AI Agent、量化交易、开源项目
```

---

## Gateway 部署

### 启动 Gateway

```bash
# 启动
openclaw gateway start

# 停止
openclaw gateway stop

# 重启
openclaw gateway restart

# 查看状态
openclaw gateway status
```

---

### 后台运行

**使用 systemd**：
```bash
# 创建服务文件
cat > /etc/systemd/system/openclaw-gateway.service << 'EOF'
[Unit]
Description=OpenClaw Gateway
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw
ExecStart=/root/.nvm/current/bin/openclaw gateway start
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
systemctl enable openclaw-gateway
systemctl start openclaw-gateway
systemctl status openclaw-gateway
```

---

### 端口配置

**修改 Gateway 端口**：
```bash
# 编辑配置
vim ~/.openclaw/config.json

# 修改 port
{
  "gateway": {
    "port": 18789  # 改为其他端口
  }
}

# 重启 Gateway
openclaw gateway restart
```

---

## Dashboard 部署

### 安装 Dashboard

```bash
# 克隆 Dashboard
cd /root/.openclaw/workspace
git clone --depth 1 https://github.com/tugcantopaloglu/openclaw-dashboard.git
cd openclaw-dashboard

# 启动
export DASHBOARD_PORT=7860
export DASHBOARD_ALLOW_HTTP=true
export OPENCLAW_DIR="/root/.openclaw"
export WORKSPACE_DIR="/root/.openclaw/workspace"

nohup node server.js > /tmp/dashboard.log 2>&1 &

# 验证
ss -tlnp | grep 7860
```

---

### Nginx 反向代理

```bash
# 安装 Nginx
apt-get update && apt-get install -y nginx

# 配置
cat > /etc/nginx/sites-available/openclaw << 'EOF'
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# 启用
ln -sf /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
```

---

## 技能安装

### 使用 clawhub

```bash
# 搜索技能
npx clawhub@latest search weather

# 安装技能
npx clawhub@latest add weather

# 列出已安装技能
npx clawhub@latest list
```

---

### 手动安装

```bash
# 克隆技能仓库
cd /root/.openclaw/workspace/skills
git clone https://github.com/xxx/skill-name.git

# 配置技能
cd skill-name
cp config.example.json config.json
vim config.json  # 填写配置

# 重启 Gateway
openclaw gateway restart
```

---

### 常用技能

| 技能 | 功能 | 安装命令 |
|------|------|---------|
| **weather** | 天气查询 | `npx clawhub add weather` |
| **tavily-search** | AI 搜索 | `npx clawhub add tavily-search` |
| **github** | GitHub 操作 | `npx clawhub add github` |
| **agent-browser** | 浏览器自动化 | `npx clawhub add agent-browser` |
| **summarize** | 内容摘要 | `npx clawhub add summarize` |

---

## 渠道配置

### Telegram

```bash
# 1. 创建 Bot
# 在 Telegram 搜索 @BotFather
# 发送 /newbot 创建机器人
# 保存 Bot Token

# 2. 配置
vim ~/.openclaw/config.json
```

**配置示例**：
```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "8629538661:AAGyjluTv18bD6x_OJkq4ERrZsELjEUG7so"
    }
  }
}
```

---

### QQ Bot

```bash
# 1. 在 QQ 开放平台创建应用
# https://q.qq.com/

# 2. 获取 AppID 和 AppSecret

# 3. 配置
vim ~/.openclaw/config.json
```

**配置示例**：
```json
{
  "channels": {
    "qqbot": {
      "enabled": true,
      "appId": "xxx",
      "appSecret": "xxx"
    }
  }
}
```

---

### Discord

```bash
# 1. 创建 Discord 应用
# https://discord.com/developers/applications

# 2. 创建 Bot，复制 Token

# 3. 邀请 Bot 到服务器
# OAuth2 → URL Generator → 选择 bot 权限

# 4. 配置
vim ~/.openclaw/config.json
```

---

## 故障排查

### Gateway 无法启动

**问题**：
```
Error: Port 18789 is already in use
```

**解决**：
```bash
# 查看占用端口的进程
lsof -i :18789

# 杀死进程
kill -9 <PID>

# 或修改 Gateway 端口
vim ~/.openclaw/config.json
```

---

### Dashboard 无法访问

**问题**：
```
502 Bad Gateway
```

**解决**：
```bash
# 检查 Dashboard 是否运行
ps aux | grep "node server.js"

# 检查 Nginx 配置
nginx -t

# 查看 Dashboard 日志
cat /tmp/dashboard.log

# 重启 Dashboard
pkill -f "node server.js"
cd /root/.openclaw/workspace/openclaw-dashboard
node server.js &
```

---

### 技能无法加载

**问题**：
```
Error: Cannot find module 'xxx'
```

**解决**：
```bash
# 进入技能目录
cd /root/.openclaw/workspace/skills/skill-name

# 安装依赖
npm install

# 重启 Gateway
openclaw gateway restart
```

---

### 渠道无法连接

**问题**：
```
Telegram Bot API error: 401 Unauthorized
```

**解决**：
```bash
# 检查 Bot Token 是否正确
vim ~/.openclaw/config.json

# 测试 Bot
curl "https://api.telegram.org/bot<TOKEN>/getMe"

# 重启 Gateway
openclaw gateway restart
```

---

## 性能优化

### 内存优化

```bash
# 限制 Node.js 内存
export NODE_OPTIONS="--max-old-space-size=4096"

# 永久生效
echo 'export NODE_OPTIONS="--max-old-space-size=4096"' >> ~/.bashrc
source ~/.bashrc
```

---

### 启动优化

```bash
# 使用 PM2 管理
npm install -g pm2

pm2 start /root/.nvm/current/bin/openclaw --name "openclaw-gateway" -- gateway start
pm2 save
pm2 startup
```

---

## 备份与恢复

### 备份

```bash
# 备份配置
tar -czf openclaw-backup-$(date +%Y%m%d).tar.gz \
    ~/.openclaw/config.json \
    ~/.openclaw/agents/main/ \
    ~/.openclaw/cron/
```

---

### 恢复

```bash
# 解压备份
tar -xzf openclaw-backup-20260325.tar.gz -C ~/

# 重启 Gateway
openclaw gateway restart
```

---

## 下一篇

👉 [05_Gate 交易所 MCP 集成](./05_Gate 交易所 MCP 集成.md)

---

*本文档由 里斯本 🦞 自动记录 | Powered by OpenClaw + Claude*
