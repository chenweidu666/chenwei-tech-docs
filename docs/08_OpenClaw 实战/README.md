<div style="text-align: center; font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;"><strong>OpenClaw 实战系列</strong></div>

> 📅 创建时间：2026-03-25 | 🦞 双龙虾架构实战文档

---

# 1. 本章说明

本章为 **OpenClaw 实战系列**，共 8 篇，约 62,500 字，涵盖从 Dashboard 部署到双龙虾架构、从 Git 同步到 MCP 集成、从量化交易到技能开发的完整流程。

## 1.1. 适用读者

- ✅ 已部署或计划部署 OpenClaw 的工程师
- ✅ 需要管理多个 OpenClaw 实例的运维人员
- ✅ 对多 Agent 协作架构感兴趣的研究者
- ✅ 想通过 OpenClaw 实现量化交易的开发者

## 1.2. 前置知识

- 了解 Linux 基础命令
- 了解 Node.js 和 npm
- 了解 Git 基本操作
- 了解大模型和 Agent 概念

---

# 2. 文档索引

| 编号 | 标题 | 字数 | 核心内容 |
|------|------|------|---------|
| [8.1](01_Dashboard 部署与移动端优化.md) | Dashboard 部署与移动端优化 | 6,000 | Dashboard 安装、Nginx 代理、移动端适配 |
| [8.2](02_双龙虾架构设计与实现.md) | 双龙虾架构设计与实现 | 7,000 | 架构设计、职责分工、安全隔离 |
| [8.3](03_Git 记忆同步机制详解.md) | Git 记忆同步机制详解 | 8,000 | 同步架构、文件权限、冲突解决 |
| [8.4](04_OpenClaw 本地部署指南.md) | OpenClaw 本地部署指南 | 8,000 | 快速安装、配置详解、渠道配置 |
| [8.5](05_Gate 交易所 MCP 集成.md) | Gate 交易所 MCP 集成 | 9,000 | MCP 架构、安装配置、工具使用 |
| [8.6](06_BTC 量化交易策略实录.md) | BTC 量化交易策略实录 | 8,500 | 金字塔策略、数据采集、自动交易 |
| [8.7](07_OpenClaw 技能开发指南.md) | OpenClaw 技能开发指南 | 8,500 | 技能架构、开发流程、测试发布 |
| [8.8](08_常见问题与故障排查.md) | 常见问题与故障排查 | 7,500 | 故障排查、性能优化、诊断脚本 |

---

# 3. 快速开始

## 3.1. 新手路线

```
第一步：阅读 8.4 → 部署 OpenClaw
第二步：阅读 8.1 → 部署 Dashboard
第三步：阅读 8.2 → 理解双龙虾架构
第四步：阅读 8.3 → 配置 Git 同步
```

## 3.2. 进阶路线

```
第一步：阅读 8.5 → 集成 Gate MCP
第二步：阅读 8.6 → 实现量化交易
第三步：阅读 8.7 → 开发自定义技能
第四步：阅读 8.8 → 故障排查与优化
```

---

# 4. 架构图

## 4.1. 双龙虾架构

```
┌─────────────────────────────────────┐
│         GitHub GateClaw-Bot          │
│          (同步中枢)                   │
└──────────────┬───────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
   ┌─────────┐   ┌─────────┐
   │ 里斯本   │   │ 尤力克   │
   │ (通用)   │   │ (交易)   │
   └─────────┘   └─────────┘
```

## 4.2. 同步机制

```
里斯本 ──push──> GateClaw-Bot 仓库 <──pull── 尤力克
  │                                        │
MEMORY.md                            position_tracking.md
memory/*.md                            trade_log/*.md
```

---

# 5. 关键概念

## 5.1. 双龙虾

- **里斯本 (Lisbon)**：通用助手，负责日常对话、技能开发、记忆管理
- **尤力克 (Eureka)**：交易龙虾，负责 BTC 量化交易、仓位管理

## 5.2. Git 同步

- **同步中枢**：GitHub GateClaw-Bot 仓库
- **同步频率**：里斯本每 2 小时 push，尤力克每 30 分钟 pull
- **文件权限**：MEMORY.md 由里斯本写入，position_tracking.md 由尤力克写入

## 5.3. MCP 集成

- **MCP**：Model Context Protocol
- **Gate MCP**：提供 326+ 个 Gate 交易所工具
- **mcporter**：MCP 客户端，用于配置和管理 MCP 服务器

---

# 6. 实战项目

## 6.1. Dashboard 部署

**目标**：部署 OpenClaw 监控面板

**步骤**：
1. 克隆 openclaw-dashboard 仓库
2. 配置环境变量
3. 启动 Dashboard
4. 配置 Nginx 反向代理
5. 移动端优化

**成果**：可通过 http://your-ip:7860 访问的监控面板

## 6.2. 双龙虾部署

**目标**：部署两个独立的 OpenClaw 实例

**步骤**：
1. 准备两台服务器
2. 分别安装 OpenClaw
3. 配置 GateClaw-Bot 仓库
4. 设置 Git 同步脚本
5. 配置定时任务

**成果**：两只龙虾通过 Git 仓库同步记忆

## 6.3. BTC 量化交易

**目标**：实现 BTC 现货金字塔策略

**步骤**：
1. 配置 Gate MCP
2. 编写数据采集脚本
3. 实现金字塔挂单逻辑
4. 设置 heartbeat 决策
5. 配置告警机制

**成果**：自动执行 BTC 量化交易

---

# 7. 常见问题

## 7.1. Dashboard 无法访问

**检查**：
- Dashboard 进程是否运行
- 防火墙是否开放端口
- Nginx 配置是否正确

**解决**：
```bash
ps aux | grep "node server.js"
ufw allow 7860/tcp
nginx -t && systemctl restart nginx
```

## 7.2. Git 同步失败

**检查**：
- SSH Key 是否配置
- Git 远程仓库 URL 是否正确
- 是否有未提交的变更

**解决**：
```bash
ssh -T git@github.com
git remote -v
git status
```

## 7.3. MCP 工具找不到

**检查**：
- mcporter 是否安装
- MCP 服务器配置是否正确
- API Key 是否有效

**解决**：
```bash
mcporter list
cat ~/.mcporter/mcporter.json
```

---

# 8. 下一步

## 8.1. 相关阅读

- 👉 [1.1 动机与缩放取舍](../01_基础层/1.1_动机与缩放取舍.md) - 大模型基础
- 👉 [5.2 MCP 协议](../05_Agent 开发/5.2_MCP 协议.md) - MCP 协议详解
- 👉 [7.2 OpenClaw 部署](../07_项目总结/7.2_OpenClaw-Deployment-Issues/README.md) - 部署实践

## 8.2. 扩展阅读

- **OpenClaw 官方文档**：https://docs.openclaw.ai
- **ClawHub 技能市场**：https://clawhub.com
- **Gate MCP 文档**：https://github.com/gate/gate-skills

## 8.3. 联系与交流

- 📧 邮箱：514351508@qq.com
- 🐙 GitHub：https://github.com/chenweidu666/AI-Engineering-Docs
- 💬 Discord：https://discord.gg/clawd

---

*本文档由 里斯本 🦞 自动记录 | Powered by OpenClaw + Claude*

*最后更新：2026-03-25*
