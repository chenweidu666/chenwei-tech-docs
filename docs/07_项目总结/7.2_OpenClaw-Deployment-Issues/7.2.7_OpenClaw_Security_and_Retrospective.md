<!-- 文档同步自 https://github.com/chenweidu666/OpenClaw-Deployment-Issues 分支 main — 请勿手工与上游长期双轨编辑 -->


# 1. OpenClaw 安全加固与项目复盘


> 本文档从 [README 主文档](../README.md) 拆出，含 **安全加固（4 层）**、**部署时间线**、**功能完成度**、**系统提示词裁剪决策**与**优缺点 / Token 评估**。  
> 返回 [项目总览](../README.md)

---


# 2. 目录


- [安全加固：4 层纵深防御详解](#安全加固4-层纵深防御详解)
- [部署时间线](#部署时间线)
- [功能完成度总览](#功能完成度总览)
- [系统提示词裁剪决策记录（2026-02-11）](#系统提示词裁剪决策记录2026-02-11)
- [OpenClaw 优缺点评估（实测总结）](#openclaw-优缺点评估实测总结)

---

<a id="安全加固4-层纵深防御详解"></a>


# 3. 安全加固：4 层纵深防御详解


## 3.1. 风险分析

OpenClaw 作为 AI Agent 拥有 shell 执行能力，默认配置下权限几乎不受限：

| 风险点 | 说明 | 危险等级 |
|--------|------|:--------:|
| 内置 `exec` 工具 | AI 可执行任意 shell 命令，不限于注册的工具 | **极高** |
| 自定义插件 | `runScript()` / `runScriptAsync()` 直接调用 `execSync`/`exec` | **高** |
| SSH 远程访问 | 可 SSH 到 3060 工作站执行命令 | **高** |
| NAS 全量存储 | AI 可读取所有 NAS 文件（视频、照片、文档） | 中 |
| SOUL.md / AGENTS.md | 软性规则（"不要删文件"），模型可能无视 | 低（仅约束力） |

## 3.2. 已实施的安全措施（4 层防御）

### 第 1 层：Exec Approvals（框架级白名单）

创建 `~/.openclaw/exec-approvals.json`，限制 AI 只能执行白名单中的命令：

```json
{
  "version": 1,
  "defaults": {
    "security": "allowlist",
    "ask": "on-miss",
    "askFallback": "allow",
    "autoAllowSkills": true
  },
  "agents": {
    "main": {
      "security": "allowlist",
      "askFallback": "allow",
      "allowlist": [
        { "pattern": "*/bash" },
        { "pattern": "*/grep" },
        { "pattern": "*/cat" },
        { "pattern": "*/ls" },
        { "pattern": "*/find" },
        { "pattern": "*/df" },
        { "pattern": "*/free" },
        { "pattern": "*/sensors" },
        { "pattern": "*/curl" },
        { "pattern": "*/python3" },
        { "pattern": "*/ssh" },
        { "pattern": "*/systemctl" }
      ]
    }
  }
}
```

**关键设置**：
- `security: "allowlist"` — 只允许白名单中的命令
- `askFallback: "allow"` — Docker 非交互环境下无法弹窗审批时默认放行（仅对白名单命令有效）
- 白名单只包含**查询类**命令，不含 `rm`、`sudo`、`chmod` 等

### 第 2 层：Tool Policy（openclaw.json）

在主配置中设置 exec 工具的安全策略：

```json
{
  "tools": {
    "exec": {
      "security": "allowlist",
      "host": "gateway",
      "safeBins": ["jq", "grep", "cut", "sort", "uniq", "head", "tail", "tr", "wc"]
    }
  }
}
```

### 第 3 层：插件命令黑名单（index.ts）

在自定义插件的 `runScript()` / `runScriptAsync()` 中加入危险命令正则过滤：

```typescript
const DANGEROUS_PATTERNS = [
  /\brm\s+(-[rfRF]+\s+|.*\/)/,  // rm -rf
  /\bsudo\b/,                     // sudo
  /\bmkfs\b/,                     // 格式化
  /\bdd\s+.*of=/,                 // dd 写入
  /\bshutdown\b/,                 // 关机
  /\breboot\b/,                   // 重启
  /\bcurl\b.*\|\s*\bbash\b/,     // curl | bash
  /\/etc\/shadow/,                // 密码文件
  /\.ssh\/.*_key/,                // SSH 私钥
  // ... 共 18 条规则
];

function validateCommand(cmd: string): void {
  for (const pattern of DANGEROUS_PATTERNS) {
    if (pattern.test(cmd)) {
      throw new Error(`🚫 命令被安全策略拦截`);
    }
  }
}
```

每条命令执行前都会过 `validateCommand()` 校验，匹配到危险模式立即拒绝。

### 第 4 层：Workspace 安全规则（AGENTS.md）

将模糊的"Don't run destructive commands"改为明确的分级权限清单：

| 等级 | 操作 | 示例 |
|:----:|------|------|
| **🚫 绝对禁止** | 特权命令 | `sudo`、`rm -rf`、`dd`、`shutdown`、`passwd` |
| **⚠️ 需确认** | 有副作用的操作 | `pip install`、修改 `/etc/`、创建 cron、远程写入 |
| **✅ 可自由执行** | 只读查询 | 读文件、搜索、查温度、查天气、查账单 |

## 安全效果

| 指标 | 加固前 | 加固后 |
|------|--------|--------|
| exec 工具 | 任意命令 | 白名单 + 黑名单双重过滤 |
| sudo 权限 | 可用（密码可获取） | 插件层拦截 + AGENTS.md 禁止 |
| 文件删除 | 无限制 | `rm -rf` 被正则拦截 |
| 远程执行 | SSH 无限制 | SSH 仍保留（读取 3060 信息），但危险命令被拦截 |
| 审批机制 | 无 | `askFallback: "allow"` — 白名单命令自动放行，Docker 非交互环境兼容 |

> **注意**：这些措施是**纵深防御**而非绝对安全。已通过 Docker 容器实现进一步隔离：非 root 运行、只读挂载、cap_drop ALL、no-new-privileges。详见 `docker/` 目录。

---


# 4. 部署时间线


| 状态 | 时间 | 里程碑 |
|:----:|------|--------|
| ✅ | 2026-02-08 17:00 | 在 NAS 上安装 OpenClaw，配置阿里云 DashScope API |
| ✅ | 2026-02-08 17:30 | 配置飞书双向机器人（企业自建应用 + WebSocket 长连接） |
| ✅ | 2026-02-08 18:00 | 配置 Nginx HTTPS 反向代理，局域网 Web UI 可访问 |
| ✅ | 2026-02-08 18:30 | 自定义 Workspace（SOUL.md / IDENTITY.md / TOOLS.md） |
| ✅ | 2026-02-08 19:00 | 测试 Qwen3 模型（4B / 14B / 32B），确定 14B 为默认 |
| ✅ | 2026-02-08 21:00 | 开发 system_info Skill，AI 可读取 NAS 硬件/软件信息 |
| ✅ | 2026-02-08 21:30 | 模型对比实测：验证 14B 的工具调用能力 |
| ✅ | 2026-02-08 22:00 | 整理项目结构，初始化 Git 仓库，撰写本文 |
| ✅ | 2026-02-08 22:30 | 配置记忆系统（MEMORY.md + 每日日志） |
| ✅ | 2026-02-08 23:00 | 修复 IM 消息不回复问题（session channel 错配） |
| ✅ | 2026-02-08 23:30 | 配置 sudo 支持，AI 可直接安装软件、查询系统状态 |
| ⏳ | 2026-02-09 00:00 | 部署 Mi-GPT，小爱音箱 Play 接入（等待小米账号验证） |
| ✅ | 2026-02-09 00:30 | 重置会话历史（清除旧模型引用，修复 AI 自称 4B 问题） |
| ✅ | 2026-02-09 01:50 | 开发 weather Skill：天气查询 + 飞书每 2 小时定时推送 |
| ✅ | 2026-02-09 02:20 | 开发 personal_info Skill：导入个人 Q&A 数据集，AI 可回答主人相关问题 |
| ✅ | 2026-02-09 12:30 | 重构 Skill 文档：精简总览、统一章节编号 |
| ✅ | 2026-02-09 14:00 | 开发 bilibili_summary Skill v1~v3：架构演进（本地全流程 → 3060 工作站 FastAPI 服务） |
| ✅ | 2026-02-09 17:00 | bilibili_summary v4~v5：3060 工作站服务新增 Qwen3-32B LLM 总结，NAS 传输修复 |
| ✅ | 2026-02-09 19:00 | 3060 工作站 FastAPI systemd 开机自启、UFW 防火墙 |
| ✅ | 2026-02-09 20:00 | 更新 Workspace（TOOLS.md / USER.md / MEMORY.md）+ Git 推送 |
| ✅ | 2026-02-09 21:00 | 更新 Skills 文档：新增"为什么用本地 Whisper"章节、修复 Mermaid 架构图 |
| ✅ | 2026-02-09 22:00 | 排查 AI 死循环问题（坑 8 + 坑 9）：清除被污染的会话 + 移除 MEMORY.md |
| ✅ | 2026-02-09 22:55 | **bilibili_summary 端到端验证成功**：飞书发链接 → AI 匹配 Skill → 3060 工作站处理 114.6s → 飞书回复总结 |
| ✅ | 2026-02-10 03:20 | 开发 qwen_usage Skill → 独立为脚本（解耦 OpenClaw） |
| ✅ | 2026-02-10 03:23 | 发现并修复 **nativeSkills 导致 14B Skill 失效**（坑 10）：`nativeSkills: false` |
| ✅ | 2026-02-10 12:50 | **系统提示瘦身**：AGENTS.md 230→40 行、5 个 SKILL.md 总计 243→129 行，上下文减少 53% |
| ✅ | 2026-02-10 13:07 | 清理 584KB 过大会话文件（坑 11），修复 DashScope `input length > 98304` 溢出错误 |
| ✅ | 2026-02-10 14:30 | **自定义插件原生 function calling**（坑 12）：开发 `custom-skills` 插件，5 个 Skill 全部注册为原生工具 |
| ✅ | 2026-02-10 14:40 | 端到端验证：5 个技能全部通过 function calling 调用成功 |
| ✅ | 2026-02-10 14:45 | **天气功能解耦**：weather 采集/推送迁移为独立脚本，cw_weather 改读 CSV |
| ✅ | 2026-02-10 15:42 | **修复 bilibili_summary 工具调用被截断**（坑 13）：`execSync` → 异步 `exec`，解决事件循环阻塞 |
| ✅ | 2026-02-10 16:00 | **NAS 路径优化**：`cw_nas_search` 改为本地 find（无需 SSH），重新定位为"深度搜索"工具 |
| ✅ | 2026-02-10 16:20 | **bilibili_summary v6 架构重构**：3060 只做下载+转写（存 NAS），AI 总结改用 OpenClaw Qwen API（云端） |
| ❌ | 2026-02-10 16:45 | **bilibili 纯 API 备用链路调研后放弃**：DashScope Paraformer 不支持本地文件，需 OSS 中转，3060 方案已满足需求 |
| ✅ | 2026-02-10 21:00 | **架构迁移：Surface Pro → NAS**：放弃不稳定的 Surface Pro，在绿联 NAS 上通过 nvm 安装 Node.js 22 + OpenClaw（坑 15） |
| ✅ | 2026-02-10 22:00 | **NAS 端全量配置恢复**：DashScope Qwen3 API + 飞书 WebSocket 机器人 + 5 个原生工具插件 |
| ✅ | 2026-02-10 22:30 | **NAS 端到端验证成功**：飞书收发消息正常，AI 通过 Qwen3-14B 回复，飞书文档/Wiki/多维表格工具已加载 |
| ✅ | 2026-02-10 23:00 | 更新全部文档：README.md 架构图重绘、踩坑记录更新、部署指南适配 NAS |
| ✅ | 2026-02-11 | **安全加固 4 层防御**：exec-approvals 白名单 + tool policy + 插件命令黑名单（18 条规则）+ AGENTS.md 分级权限 |
| ✅ | 2026-02-11 | **Docker 隔离环境**：Dockerfile + docker-compose.yml + entrypoint.sh，OpenClaw 运行在独立容器（node:22-slim + UID 1000），只读挂载代码/配置，sessions 持久化卷，2GB 内存限制，no-new-privileges |
| ✅ | 2026-02-11 | **本地模型部署**：3060 工作站通过 vLLM Docker 运行 Qwen3-8B-AWQ，`--max-model-len 24000 --enable-auto-tool-choice --tool-call-parser hermes`，替代云端 DashScope 作为主力模型 |
| ✅ | 2026-02-11 | **自动模型回退**：entrypoint.sh 启动时探测 3060 健康状态，在线则用本地模型，离线自动切回云端 Qwen3-14B |
| ✅ | 2026-02-11 | **飞书启动通知**：容器启动后自动通过飞书 API 发消息给用户，告知重启时间、当前模型、Gateway 状态 |
| ✅ | 2026-02-11 | **系统提示词大裁剪**：34 工具 → 23 工具（详见下方裁剪决策记录） |
| ✅ | 2026-02-11 | 关闭全部 5 个自定义 Skill/工具：system_info、weather、nas_search、personal_info、bilibili_summary |
| ✅ | 2026-02-11 | 关闭 11 个飞书内置工具：doc / wiki / drive / scopes / bitable（get_meta/list_fields/list_records/get_record/create_record/update_record），patch bitable.ts 源码使其尊重 tools.doc=false |
| ✅ | 2026-02-11 | **上下文窗口调优**：vLLM max-model-len 24000 ↔ OpenClaw contextWindow 24000，系统提示 ~8K tokens，剩余 ~16K tokens 供对话 |
| ✅ | 2026-02-11 | **回归纯云端 API**：经过本地 8B 模型的完整测试后，决定放弃本地推理，改用 DashScope Qwen3-14B API。原因：14B 工具调用能力显著优于 8B，131K 上下文窗口不再受限，极低成本（百万 token ¥1.5），且无需维护 3060 工作站 |
| ⏸️ | 2026-02-11 | **OpenClaw 暂停运行**：评估 Token 成本后决定暂停。核心问题：每轮对话 ~9K tokens 的系统开销（23 个工具 Schema + Workspace 自学习），其中 60%+ 不是用户实际对话。对云端 API 预算不友好，后续考虑轻量 Bot 替代方案 |

> 从零到功能完备的 OpenClaw 私人 AI 助手（还在持续进化中）。
>
> **2/9 回顾**：完成了 bilibili_summary — 第一个 API 服务型 Skill，实现双机协同（NAS + 3060 工作站）的分布式架构。过程中踩了多个坑（NAS 传输、端口冲突、Qwen3 API、对话历史污染），均已解决并记录。最终端到端验证成功：飞书发送B站链接 → AI 自动匹配 Skill → 3060 工作站完成下载+转写 → OpenClaw Qwen API 总结 → AI 回复飞书用户。
>
> **2/10 回顾**：发现并修复了坑 10（nativeSkills）和坑 11（上下文溢出）。最重要的突破是**坑 12**：深入分析 OpenClaw 源码后发现，Skill 的上下文注入机制对 14B/32B 模型都不够可靠，最终通过**插件系统 `api.registerTool()`** 将 5 个自定义 Skill 注册为原生 function calling 工具，实现了**不依赖上下文的确定性调用**。架构优化：NAS 作为主机后 `cw_nas_search` 改为本地 `find` 执行（无需 SSH），bilibili_summary v6 实现转写与总结解耦。晚间完成**架构迁移**：彻底放弃不稳定的 Surface Pro，在绿联 NAS 上通过 nvm 安装 Node.js 22 + OpenClaw，恢复全部配置并验证成功。
>
> **2/11 回顾**：完成四项关键架构变更。**第一**，安全加固 + Docker 容器化，4 层纵深防御确保 AI 无法执行危险操作。**第二**，部署本地 Qwen3-8B-AWQ 到 3060 工作站进行测试，发现 8B 模型的工具调用能力不足（不稳定、倾向用 shell 重定向代替文件工具、上下文窗口受限）。**第三**，系统提示词大裁剪：从 34 工具裁剪到 23 工具，删除全部 5 个自定义工具 + 11 个飞书文档类工具，其中 bitable 工具需 patch 源码。**第四，最终决策**——**回归纯云端 API**：综合测试 8B/14B 后，14B 工具调用能力显著优于 8B，131K 上下文不再受限，DashScope 成本极低（百万 token ¥1.5），不再需要维护 3060 工作站和 vLLM 服务。最终架构精简为：NAS Docker 网关 + DashScope Qwen3-14B API。

---


# 5. 功能完成度总览


| 状态 | 功能 | 说明 |
|:----:|------|------|
| ✅ | OpenClaw 基础部署 | NAS Docker 容器 + 飞书 WebSocket + Gateway |
| ✅ | **云端 LLM 推理** | 阿里云 DashScope Qwen3-14B / 32B API，131K 上下文，极低成本 |
| ✅ | 飞书双向机器人 | 企业自建应用 + WebSocket 长连接，主要 IM 渠道 |
| ✅ | **飞书启动通知** | 容器启动/重启后自动发飞书消息，通知当前模型和状态 |
| ✅ | Docker 隔离环境 | node 用户（UID 1000）+ 只读挂载 + cap_drop ALL + no-new-privileges + 2GB 内存限制 |
| ✅ | 安全加固 | 4 层纵深防御：exec 白名单 + tool policy + 插件命令黑名单 + 分级权限 |
| ✅ | **系统提示词裁剪** | 从 34 工具精简到 23 工具，关闭飞书文档类 11 个工具 + 5 个自定义工具 |
| ✅ | 记忆系统 | MEMORY.md 长期记忆 + 每日日志 |
| ⛔ | ~~全部自定义 Skill~~ | ~~system_info / weather / nas_search / personal_info / bilibili_summary~~ — **已清理** |
| ⛔ | ~~飞书文档工具~~ | ~~doc / wiki / drive / bitable / scopes~~ — **已关闭**（tools 配置 + 源码 patch） |
| ⛔ | ~~原生 Function Calling 插件~~ | ~~5 个自定义工具~~ — **已清空**，保留插件框架 |
| ⛔ | ~~本地 8B 推理~~ | ~~3060 vLLM Qwen3-8B-AWQ~~ — **已弃用**，改为纯云端 DashScope API |
| ⏸️ | **OpenClaw 整体暂停** | Token 成本结构不合理（系统开销占 60%+），对云端 API 预算不友好，详见[优缺点评估](#openclaw-优缺点评估实测总结) |
| ⏳ | 小爱音箱语音交互 | Mi-GPT 已部署，等待小米账号安全验证生效 |
| 📋 | 轻量 Bot 替代方案 | 直接调 DashScope API + 按需注入工具，Token 效率更高 |
| 📋 | MCP Server 集成 | 通过 Model Context Protocol 接入外部工具 |
| 📋 | Home Assistant 联动 | AI 控制智能家居 |
| 📋 | 知识库 RAG | 私有文档库问答 |

> ✅ = 已完成 &nbsp; ⏳ = 进行中 &nbsp; ⏸️ = 暂停 &nbsp; 📋 = 待完成 &nbsp; ⛔ = 已关闭/已清理

---

<a id="系统提示词裁剪决策记录2026-02-11"></a>


# 6. 系统提示词裁剪决策记录（2026-02-11）


## 6.1. 背景

在部署本地 Qwen3-8B-AWQ 阶段，上下文窗口仅 24K tokens，而 OpenClaw 默认加载的系统提示词 + 工具 Schema 高达 ~14K tokens（34 个工具），留给实际对话的空间仅 ~10K tokens，8B 模型频繁出现空回复或上下文溢出。

**核心矛盾**：工具越多 → 系统提示越大 → 对话空间越小 → 8B 模型回复质量越差。必须裁剪。

> **后续演进**：裁剪完成后经过 8B vs 14B 对比测试，最终决定回归纯云端 DashScope Qwen3-14B API。14B 拥有 131K 上下文窗口，裁剪后的 23 工具不再是上下文瓶颈，但精简后的工具集更加聚焦实用，因此保留裁剪成果。

## 6.2. 裁剪前状态

| 类别 | 数量 | 占用 |
|------|:----:|------|
| OpenClaw 内置工具 | 18 个 | ~6K tokens |
| 飞书文档/云盘/Wiki/多维表格 | 11 个 | ~5K tokens |
| 自定义 Function Calling 工具 | 5 个 | ~3K tokens |
| **总计** | **34 个** | **~14K tokens** |

## 6.3. 裁剪决策

### 第一刀：删除全部自定义工具（5 个 → 0 个）

| 工具 | 原功能 | 删除原因 |
|------|--------|----------|
| `cw_system_info` | 读取 NAS 硬件信息 | Docker 容器内信息有限，价值低 |
| `cw_weather` | 天气查询 | 依赖外部 API + cron，维护成本 > 收益 |
| `cw_nas_search` | NAS 文件搜索 | Docker 容器只读挂载，find 权限受限 |
| `cw_bilibili_summary` | B站视频转写总结 | 依赖 3060 Whisper 服务（现已改为 vLLM），流程复杂 |
| `cw_qwen_billing` | DashScope 费用查询 | 已切本地模型，云端费用不再是主要关注点 |

**操作**：清空 `extensions/custom-skills/index.ts` 中所有 `api.registerTool()` 调用，删除 `skills/` 目录下全部子目录。

### 第二刀：关闭飞书文档类工具（11 个 → 0 个）

| 工具组 | 包含工具 | 删除原因 |
|--------|----------|----------|
| 飞书文档 | `feishu_doc` | 当前仅用飞书做 IM 通讯，不需要操作文档 |
| 飞书 Wiki | `feishu_wiki` | 无知识库使用场景 |
| 飞书云盘 | `feishu_drive` | 文件存储用 NAS 本地 |
| 飞书权限 | `feishu_app_scopes` | 仅开发时需要，日常无用 |
| 飞书多维表格 | `feishu_bitable_*`（6 个） | 无多维表格使用场景 |

**操作**：在 `openclaw.json` 的 `channels.feishu.tools` 中设置：

```json
"tools": {
  "doc": false,
  "wiki": false,
  "drive": false,
  "perm": false,
  "scopes": false
}
```

**踩坑**：`feishu_bitable_*` 的 6 个工具不受上述配置控制——OpenClaw 源码中 `bitable.ts` 的注册函数没有检查 `tools` 配置。

**修复**：直接 patch 宿主机上的 OpenClaw 源码 `~/.nvm/.../openclaw/extensions/feishu/src/bitable.ts`，在 `registerFeishuBitableTools()` 开头添加：

```typescript
const toolsCfg = feishuCfg.tools as Record<string, boolean> | undefined;
if (toolsCfg?.doc === false) {
  api.logger.info?.("feishu_bitable: Skipped (tools.doc=false)");
  return;
}
```

然后通过 `prepare.sh` 将 patch 后的包复制到 Docker build context，重新构建镜像。

## 裁剪后状态

| 类别 | 数量 | 占用 |
|------|:----:|------|
| OpenClaw 内置工具 | 18 个 | ~6K tokens |
| 飞书消息工具 | 5 个 | ~2K tokens |
| 自定义工具 | 0 个 | 0 |
| **总计** | **23 个** | **~8K tokens** |

## 效果对比

| 指标 | 裁剪前 | 裁剪后 |
|------|:------:|:------:|
| 工具数量 | 34 | **23** (-32%) |
| 系统提示占用 | ~14K tokens | **~8K tokens** (-43%) |
| 对话可用空间 | ~10K tokens | **~16K tokens** (+60%) |
| 8B 模型回复质量 | 频繁空回复 | **稳定回复** |

## 保留的 23 个工具

| # | 工具名 | 类别 | 用途 |
|:--:|--------|------|------|
| 1 | `read_file` | 文件 | 读取文件 |
| 2 | `write_file` | 文件 | 写入文件 |
| 3 | `edit_file` | 文件 | 编辑文件（搜索替换） |
| 4 | `multi_edit_file` | 文件 | 批量编辑 |
| 5 | `list_dir` | 文件 | 列出目录 |
| 6 | `file_search` | 文件 | 文件名搜索 |
| 7 | `grep_search` | 文件 | 内容搜索 |
| 8 | `exec` | 系统 | Shell 命令执行（白名单限制） |
| 9 | `web_search` | 网络 | 网页搜索 |
| 10 | `web_read` | 网络 | 读取网页 |
| 11 | `web_browse` | 网络 | 浏览器操作 |
| 12 | `heartbeat_create` | 定时 | 创建定时任务 |
| 13 | `heartbeat_list` | 定时 | 列出定时任务 |
| 14 | `heartbeat_delete` | 定时 | 删除定时任务 |
| 15 | `memory_read` | 记忆 | 读取长期记忆 |
| 16 | `memory_edit` | 记忆 | 编辑长期记忆 |
| 17 | `message` | 消息 | 发送消息 |
| 18 | `report` | 系统 | 生成报告 |
| 19 | `feishu_reply` | 飞书 | 回复消息 |
| 20 | `feishu_react` | 飞书 | 表情回应 |
| 21 | `feishu_reply_action` | 飞书 | 回复操作 |
| 22 | `feishu_message_card` | 飞书 | 发送卡片消息 |
| 23 | `feishu_thread_reply` | 飞书 | 话题回复 |

---

<a id="openclaw-优缺点评估实测总结"></a>


# 7. OpenClaw 优缺点评估（实测总结）


> 经过 4 天的完整部署、开发、测试和迭代（2/8 ~ 2/11），对 OpenClaw 的能力和局限有了深刻认识。以下是基于实战经验的客观评估。

## 7.1. 优点

| 维度 | 评价 |
|------|------|
| **完整的 AI Agent 操作系统** | 不只是聊天框架，内置 23+ 工具（文件操作、Shell 执行、网页浏览、定时任务、记忆系统），开箱即可执行实际任务 |
| **多渠道接入** | 飞书 WebSocket 一键接入，还支持 Telegram / Discord / Web UI 等，不需要自己写对接代码 |
| **模型自由** | 任意 OpenAI 兼容 API，可接 DashScope / Ollama / vLLM / GPT 等，切换只改一行配置 |
| **Workspace 设计精巧** | Markdown 定义人格/身份/工具/记忆，"一切皆文件"的哲学非常 Unix，易懂易改 |
| **插件系统灵活** | `api.registerTool()` 注册原生 Function Calling 工具，不依赖上下文注入，100% 确定性调用 |
| **安全机制完善** | exec-approvals 白名单 + safeBins + askFallback，多层防御可配置，比纯 prompt 约束靠谱得多 |
| **部署轻量** | Node.js 单进程，内存占用 ~50MB（不含模型），ARM64 NAS 也能流畅运行 |
| **社区活跃** | 2026 年热门开源项目，文档完善，安装工具成熟（OpenClawInstaller） |

## 7.2. 缺点与 Token 浪费问题

这是决定暂停 OpenClaw 的核心原因——**Token 成本结构不合理**，对云端 API 用户极不友好。

### 系统提示词的 Token 开销巨大

每次对话（包括用户说一句"你好"），OpenClaw 都会注入完整的系统上下文：

| 组件 | Token 占用 | 说明 |
|------|:----------:|------|
| SOUL.md | ~500 | AI 人格定义 |
| IDENTITY.md | ~300 | 身份信息 |
| AGENTS.md | ~800 | 行为规则 |
| TOOLS.md | ~500 | 工具速查 |
| BOOTSTRAP.md | ~300 | 启动引导 |
| 23 个工具 Schema | **~6,000** | 工具定义（不可控，框架自动注入） |
| 飞书上下文 | ~500 | 消息格式、反应规则 |
| **合计** | **~9,000** | **每轮对话的固定开销** |

> **关键问题**：23 个工具的 Schema 是框架自动注入的，**用户无法控制**。即使只想聊天不用工具，这 ~6K tokens 也会照常消耗。

### 环境自学习浪费 Token

OpenClaw 的 AGENTS.md 默认指导 AI 在每次新会话时：
1. 读取 `SOUL.md` → 消耗 tool call tokens
2. 读取 `IDENTITY.md` → 消耗 tool call tokens
3. 读取 `memory/YYYY-MM-DD.md`（今天 + 昨天）→ 消耗 tool call tokens
4. 读取 `MEMORY.md` → 消耗 tool call tokens

每次会话开始，AI **先花几千 tokens 读文件了解自己是谁**，然后才开始回答用户问题。这对闲聊场景是巨大浪费。

### 模型"过度谨慎"浪费 Token

实测中 Qwen3-14B 在 OpenClaw 框架下经常：
- 执行只读命令前**先问用户确认**（"请确认是否批准执行此操作"），等用户回复后才执行 → 多一轮对话 = 多 ~2K tokens
- 回复结尾附加"引申问题"（AGENTS.md 要求）→ 每轮额外 ~200 tokens
- 调用不必要的工具（如先 `read_file` 读 TOOLS.md 再决定怎么做）

### Token 成本估算

以下为 **2026-02 前后**按 DashScope Qwen3-14B **当时价目**粗算（输入约 ¥1.5/百万 token、输出约 ¥6/百万 token），**复算请以阿里云现网计费为准**：

| 场景 | 单次 Token 消耗 | 日均 | 月估算 |
|------|:--------------:|:----:|:------:|
| 系统提示（每轮固定） | ~9,000 输入 | — | — |
| 简单闲聊（1 轮） | ~10,000 输入 + ~500 输出 | 20 次 → 200K 输入 | ~¥0.3 输入 |
| 文件搜索（2 轮，含确认） | ~25,000 输入 + ~1,000 输出 | 5 次 → 125K 输入 | ~¥0.2 输入 |
| 复杂任务（5 轮工具调用） | ~60,000 输入 + ~3,000 输出 | 3 次 → 180K 输入 | ~¥0.3 输入 |
| **月合计** | | | **~¥1-3**（轻度使用） |

> **单看绝对金额并不高**，但问题是：**其中 60%+ 的 Token 消耗是系统开销（系统提示 + 自学习 + 工具 Schema），不是用户实际对话**。如果去掉 OpenClaw 框架的开销，直接调 API，同样的功能 Token 消耗可以降低一半以上。

### 与直接调 API 的对比

| 维度 | OpenClaw 框架 | 直接调 DashScope API |
|------|:------------:|:-------------------:|
| 每轮固定 Token 开销 | ~9,000（不可避免） | ~500（自定义 system prompt） |
| 工具调用 | 23 个 Schema 全量注入 | 按需注入需要的工具 |
| 自学习开销 | 每会话读 4-5 个文件 | 0（prompt 直接写） |
| 功能完整度 | 开箱即用，飞书/Web/记忆 | 需自己开发对接层 |
| 开发成本 | 低（配置即用） | 高（需写代码） |
| Token 效率 | **低**（60% 系统开销） | **高**（95% 有效对话） |

## 7.3. 结论

**OpenClaw 是一个优秀的 AI Agent 框架**——如果你使用的是无限上下文的本地模型（如 Ollama + 大显存 GPU）或不在意 API 成本的场景，它的工具系统、渠道接入、安全机制都非常成熟。

**但对于预算敏感的云端 API 用户**，OpenClaw 的 Token 效率是一个显著问题。每轮对话 ~9K tokens 的固定开销，在轻量使用场景下占比过高。如果主要需求是飞书聊天 + 偶尔搜文件，自己写一个轻量 Bot（直接调 API + 按需注入工具）的 Token 效率会好得多。

> **适用场景推荐**：
> - ✅ **本地大模型用户**（Ollama / vLLM + 大显存 GPU）— Token 免费，OpenClaw 的丰富功能尽管享用
> - ✅ **企业用户**（不在意 API 成本）— 开箱即用的多渠道 AI 助手
> - ⚠️ **个人用户 + 云端 API**（预算敏感）— Token 开销偏高，建议评估是否值得
> - ❌ **轻量聊天场景**— 系统开销占比过大，杀鸡用牛刀

---

> **文档最近修订**：2026-03-23（由 README 拆出独立成篇；补充裁剪章节目录锚点）
