# Dify 技术介绍

> 2025–2026 年最热门的开源 Agentic AI 应用开发平台  
> 2023 年开源，由中国团队开发，2026 年已成为全球生成式 AI 应用构建的事实标准之一（GitHub 超 12 万星）

---

## 1. 什么是 Dify？

| 属性 | 内容 |
|------|------|
| **全称** | Dify（源自 "Do It For You" 或 "Define + Modify"） |
| **提出者** | 深度求索（DeepSeek）团队 / Dify.AI |
| **开源时间** | 2023 年 5 月（早期版本），2024–2025 年快速迭代 |
| **当前版本** | 2025–2026 主线（Beehive 模块化架构 + 多模态 RAG + Agent 框架） |
| **官网** | https://dify.ai |
| **定位** | 开源的可视化 LLM 应用开发平台 + Agentic Workflow 构建器 |

**一句话总结**：  
Dify 是一个**开源、低代码/无代码**的 AI 应用开发平台，通过拖拽式工作流、可视化 Prompt 编排、RAG 引擎、Agent 框架和模型管理，让开发者/业务人员快速从原型到生产级生成式 AI 应用（聊天机器人、智能体、知识库、自动化工具等）。

---

## 2. 为什么需要 Dify？（痛点解决）

| 痛点 | 传统方案（2023–2024） | Dify 解决方式 |
|------|---------------------|--------------|
| 开发门槛高 | LangChain / LlamaIndex 纯代码 | 拖拽可视化 + 内置模板，业务人员也能上手 |
| 基础设施碎片化 | 手动集成模型、向量库、API、监控 | 一站式 LLMOps + BaaS（Backend as a Service） |
| RAG/Agent 实现复杂 | 自己写检索、重排序、工具调用逻辑 | 内置高质量 RAG 引擎 + Agent 策略（ReAct/CoT 等） |
| 从原型到生产难 | 调试、日志、版本、部署全靠手工 | 可视化调试 + 观测性 + 一键部署（云/自托管） |
| 模型/工具锁定 | 绑定单一厂商 | 支持 100+ 模型 + 多模态 + Plugin Marketplace |

**一句话**：Dify 把复杂的 LLM 应用开发从"工程师专属"变成"团队协作可投产"。

### 2.1 Dify vs 主流竞品对比（2026 年视角）

| 维度 | Dify | LangChain / LlamaIndex | Flowise / Langflow | Coze / n8n |
|------|------|------------------------|-------------------|------------|
| **开源程度** | 完全开源（社区活跃） | 开源，但更像框架 | 开源，低代码可视化 | Coze 闭源，n8n 开源 |
| **技术门槛** | ⭐⭐（中低，可视化为主） | ⭐⭐⭐⭐（代码为主） | ⭐⭐（纯拖拽） | ⭐（极低） |
| **Agent 支持** | 强大（Agent Node + 多策略） | 需手动组合 | 基础 | 简单插件式 |
| **RAG 能力** | 高质量内置（多模态、Agentic RAG） | 灵活但需自建 | 中等 | 基础 |
| **生产级能力** | 强（观测、日志、多租户、插件生态） | 需额外工具 | 较弱 | 中等（n8n 自动化强） |
| **生态规模** | 超 12 万星 + Marketplace | 框架级生态 | 社区中等 | 插件多但非 AI 专属 |
| **典型用户** | 企业/中大型团队/独立开发者 | AI 工程师/研究 | 快速原型开发者 | 自媒体/小团队 |

**结论**：Dify 在"可视化 + 生产级 + Agent/RAG 深度"上做到最佳平衡。

---

## 3. Dify 核心架构

### 3.1 架构简图

```
用户/业务人员
  ↓
可视化画布 (Studio)
  ↓
Backend（核心引擎）
├── LLM Orchestration
└── Workflow Runtime
  ↓
核心模块（独立部署/扩展）
├── Prompt 编排 & Agent 框架
├── RAG 引擎（多模态/Chunking/重排序）
├── 模型管理（100+ LLM / Embedding）
├── 数据集 & 知识库
├── Plugin / Tools Marketplace
└── Observability（日志/Tracing/指标）
  ↓
部署目标：Dify Cloud / Docker / Kubernetes
```

### 3.2 四大核心能力

| 能力 | 说明 | 典型示例 |
|------|------|---------|
| **Workflow** | 拖拽式 Agentic 工作流（Chatflow / Workflow） | 客服机器人、多步研究助手、内容生成管道 |
| **RAG 引擎** | 内置高质量检索 + Agentic RAG（迭代重写/评估） | 企业知识库问答、多模态（文本+图像）检索 |
| **Agent 框架** | 支持 ReAct/CoT/ToT/Function Call 等策略 | 自主工具调用、多步推理、外部系统交互 |
| **Plugin 系统** | 解耦扩展（模型、工具、Agent 策略） | TTS、图像生成、数据库查询、企业微信集成 |

**通信与部署**：前后端分离，支持自托管（Docker Compose 一键）、云 SaaS、多租户。

---

## 4. Dify 常见使用场景

| 排名 | 场景 | 说明 |
|------|------|------|
| ⭐1 | **智能客服 & 企业知识库** | FAQ 机器人 + RAG，自动回答客户问题 |
| 2 | **内容生成 & 多平台分发** | 文章 → 微博/小红书/LinkedIn 自动生成 |
| 3 | **内部工具 Agent** | 项目管理、代码审查、数据分析助手 |
| 4 | **多模态应用** | 图像 + 文本 RAG、文档理解 |
| 5 | **自动化工作流** | 邮件处理、CRM 更新、研究报告生成 |

---

## 5. 实战案例：旅游推荐 Agent 工作流设计

> 以"个性化旅行规划助手"为例，展示如何用 Dify 构建一个**会问、会查、会算、会画**的智能 Agent。

### 5.1 架构类型选择

| 类型 | 适用场景 | 复杂度 | 推荐指数 | 说明 |
|------|---------|--------|---------|------|
| 纯 Chatflow + Prompt | 简单问答、静态知识库 | 低 | ★☆☆☆☆ | 无法处理复杂多步规划 |
| Workflow（固定步骤） | 标准流程（预算/天数固定） | 中 | ★★☆☆☆ | 灵活性不足，多轮交互弱 |
| **Agentic Workflow** | 个性化、多轮、动态决策 | 中高 | ★★★★★ | 最接近真人顾问体验 |
| **Hybrid**（推荐） | 结构化收集 + Agent 自主规划 | 高 | ★★★★☆ | 平衡控制与智能，最实用 |

**推荐方案**：**Hybrid 模式**（Form 收集需求 + Agent Node 核心规划 + 多工具调用）

### 5.2 工作流架构图

```
Start
  ↓
Form Node ──► 收集用户偏好（目的地、预算、天数、兴趣等） → 输出 JSON
  ↓
RAG Node ──► 检索预上传知识库（攻略、POI、签证等）
  ↓
Agent Node (核心) ──┬──► ReAct / Function Calling 策略
                    │
                    ↕ (多轮工具调用)
                 Tools
                 ├── Web Search (Tavily/Serper)
                 ├── 地图 POI & 路线 (高德/Google Maps)
                 ├── 天气查询
                 ├── 汇率转换
                 ├── 图片生成 (DALL·E / Flux)
                 └── 知识库再检索 (Dify 内置)
  ↓
Answer Node ──► 解析 JSON → 美观输出（Markdown + 图片 + 地图）
  ↓
WebApp / API / 微信 等发布
```

### 5.3 各阶段节点详解

#### 阶段1：需求收集（Form Node）

**收集的核心信息**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `destination` | 文本/选择 | 目的地（或多个意向城市） |
| `travel_dates` | 日期 | 出行日期 & 天数 |
| `travelers` | 数字+选择 | 人数 & 同行者类型（情侣/家庭/朋友） |
| `budget` | 选择 | 预算范围（经济/舒适/豪华） |
| `interests` | 多选 | 兴趣偏好（美食/文化/自然/购物/冒险） |
| `special_needs` | 文本 | 特殊需求（无障碍、素食、带小孩等） |

**输出**：`user_preferences` JSON 变量

#### 阶段2：知识检索（RAG Node）

**知识库由谁提供？**
- **开发者/运营者预先上传**（不是用户提供）
- 用户只需说需求，Agent 自动从你的知识库检索

**知识库配置**：
- 在 Dify Knowledge Base 提前上传：
  - 热门目的地攻略（日本/东南亚/欧洲.pdf）
  - 景点 POI 列表、季节推荐、签证信息
  - 酒店/民宿数据、交通指南
- 检索设置：Hybrid Search + Rerank
- Query 模板：`"{{destination}} 适合 {{travel_type}} 的 {{days}} 天行程推荐"`

#### 阶段3：Agent Node（核心大脑）

**Agent 策略**：Function Calling 或 ReAct

**系统提示（关键）**：

```
你是一位专业、细致、贴心的旅行规划师。

## 目标
根据用户偏好，生成一份完整、可执行的个性化行程，包含：
- 每天详细安排（上午/下午/晚上）
- 交通方式与时间
- 住宿建议（含价格区间）
- 餐饮推荐
- 预算估算（明细）
- 注意事项

## 规则
1. 必须先理解用户所有需求（预算、兴趣、天数、人数、特殊要求）
2. 行程要现实可行（考虑交通时间、景点开放、季节天气）
3. 优先推荐性价比高、非过度商业化的体验
4. 每一步都要有依据（引用知识库或工具结果）
5. 如果信息不足，主动问用户澄清
6. 最终输出严格 JSON 结构（方便前端展示）
```

**工具配置（推荐 6-8 个）**：

| 工具 | 用途 | 接入方式 |
|------|------|---------|
| **Web Search** | 实时天气、机票价格、酒店均价、最新活动 | Tavily / Serper / Exa |
| **地图 POI** | 附近景点、餐厅、路线规划 | 高德/百度/Google Maps API |
| **天气查询** | 当天/未来天气预报 | 和风天气 / OpenWeather |
| **汇率转换** | 货币换算 | Code Node / API |
| **图片生成** | 为景点/行程生成示意图 | DALL·E / Flux |
| **知识库检索** | Agent 内部再检索 | Dify 内置 |

#### 阶段4：输出呈现（Answer Node）

- 解析 Agent 的 JSON 输出
- 渲染成美观格式（Markdown + 地图 + 图片）
- 可选：生成 PDF / 发送邮件 / 保存到 Notion

### 5.4 典型工作流示例（含 API 调用 + 多轮对话）

```
【第 1 轮对话】
用户："我想去日本，预算中等，喜欢美食和温泉，5 天，两个人。"
  ↓
【Form Node】收集完成 → user_preferences JSON
  ↓
【RAG Node】检索日本攻略 → 返回箱根/东京/大阪温泉+美食信息
  ↓
【Agent Node】开始思考（CoT）：
  ├── ❶ 确认需求 → 已收集完整
  ├── ❷ tool_call: web_search("2026 日本 5 天中等预算 美食温泉")
  │       └─ API: Tavily Search → POST /search
  ├── ❸ tool_call: map_poi("箱根温泉区 餐厅")
  │       └─ API: 高德 POI → GET /v5/place/text?keywords=餐厅&region=箱根
  ├── ❹ tool_call: weather("东京 2026-03-01")
  │       └─ API: 和风天气 → GET /v7/weather/7d?location=101021200
  ├── ❺ 规划 Day1–5 → 住宿、交通估算
  │       └─ API: 高德路径规划 → GET /v5/direction/transit
  ├── ❻ 生成预算 breakdown
  │       └─ API: ExchangeRate-API → GET /v6/latest/CNY（日元汇率）
  └── ❼ 输出 JSON + 建议图片
          └─ API: DALL·E 3 → POST /v1/images/generations
  ↓
【Answer Node】渲染成美观行程单
  ↓
【保存状态】→ Conversation Variable: {user_preferences, plan_v1}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【第 2 轮对话 - 多轮处理】
用户："太贵了，有没有更经济的方案？"
  ↓
【读取上下文】← Conversation Variable: {user_preferences, plan_v1}
【Session Memory】← 自动携带最近 N 轮对话（window_size: 10）
  ↓
【Agent Node】理解上下文 + 重新规划：
  ├── 分析：用户说"太贵" → 预算降低 30-50%
  ├── tool_call: web_search("日本经济型温泉旅馆 2026")
  ├── 保留核心需求（美食+温泉），调整住宿/交通
  └── 生成经济版 plan_v2
  ↓
【Answer Node】返回经济版行程（预算 8000）
  ↓
【更新状态】→ Conversation Variable: {previous_plans: [v1,v2], rejection: "太贵"}
```

**工具调用数据流（API 返回 → 大模型）**：

```
┌─────────────────────────────────────────────────────────────────┐
│ Agent(LLM) 决定调用工具                                          │
│ → "我需要搜索日本旅游信息"                                        │
│ → tool_call: web_search("2026 日本 5 天中等预算")                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Dify 执行 API 请求 → Tavily Search                               │
│ POST https://api.tavily.com/search                              │
│ {"query": "2026 日本 5 天中等预算 美食温泉", "max_results": 5}    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ API 返回 JSON 结果                                               │
│ {                                                               │
│   "results": [                                                  │
│     {"title": "日本温泉5日游攻略", "content": "Day1 东京→箱根..."}│
│     {"title": "中等预算指南", "content": "5天约8000-12000元/人"}  │
│   ]                                                             │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Dify 把 API 结果注入回 LLM 上下文                                 │
│ → Agent 阅读搜索结果                                             │
│ → 基于真实数据继续推理："根据搜索结果，箱根温泉性价比高..."        │
│ → 决定是否调用下一个工具（map_poi/weather）                       │
└─────────────────────────────────────────────────────────────────┘
```

> **关键点**：API 返回的数据**会传回给大模型**，Agent 基于真实数据推理，而不是凭空编造。这就是 Agent 比普通对话更"靠谱"的原因。

**多轮对话关键配置**：

| 配置项 | 作用 | 设置 |
|--------|------|------|
| **Conversation Variable** | 跨轮次存储偏好/历史方案 | Workflow → Variables |
| **Session Memory** | Agent 自动带最近 N 轮 | Agent Node → Memory → window_size: 10 |
| **System Prompt 注入** | 引用历史 `{{previous_plans}}` | 让 Agent 知道"太贵"指的是哪个方案 |

### 5.5 Dify 操作步骤

```bash
# 1. 创建 Workflow 类型应用
Dify Studio → New App → Workflow

# 2. 拖入节点
Start → Form（收集需求）→ Knowledge Retrieval → Agent Node → Answer

# 3. 配置 Agent Node
- 选择策略：Function Calling
- 添加系统提示（见上文）
- 添加 5-8 个工具

# 4. 调试
- Debug 模式多轮对话
- 观察 Agent 是否合理调用工具
- 检查 JSON 输出格式

# 5. 发布
Publish → WebApp / API / 嵌入微信/飞书
```

### 5.6 进阶优化

| 优化点 | 说明 |
|--------|------|
| **多 Agent 分工** | 一个负责行程规划，一个负责酒店/机票查询，一个负责图片生成 |
| **用户画像 RAG** | 长期用户历史偏好存向量库，实现个性化推荐 |
| **实时价格** | 接入携程/Booking/Expedia API（Custom Tool） |
| **多语言支持** | 支持中英日韩输出 |
| **人工审核** | 敏感目的地加人工审核节点 |
| **Memory 优化** | 使用 Conversation Variables 保存对话历史 |

> **一句话总结**：用 **Form + Agent Node + 多工具** 打造"会问、会查、会算、会画"的个性化旅行规划师，而不是简单的问答机器人。

---

## 6. Dify 优缺点

### 优点 ✅

- **可视化 + 生产级一站式** → 从原型到监控全覆盖
- **Agentic Workflow 强大** → 迭代推理、多工具组合
- **开源 + 活跃社区** → 超 12 万星，Plugin Marketplace 爆发
- **多模态 RAG & 模型中立** → 支持 DeepSeek、Claude、GPT、Grok 等

### 挑战 ⚠️

- **自托管运维门槛稍高** → 数据库/向量库/Redis 需配置
- **极致定制仍需理解底层** → 复杂 Agent 逻辑可能要调 YAML
- **与纯代码框架相比** → 性能调优空间稍小

---

## 7. 快速上手

```bash
# 方式1：Docker 一键自托管（推荐开发/测试）
git clone https://github.com/langgenius/dify.git
cd dify/docker
docker-compose up -d

# 方式2：云端快速试用（官方 SaaS）
# 访问 https://cloud.dify.ai → 注册 → New App

# 方式3：创建第一个 Agentic Workflow
# 1. 创建 Application → 选择 Workflow
# 2. 拖拽 Start → LLM → Knowledge Retrieval → Answer
# 3. 配置模型（Claude / DeepSeek）+ 上传知识库
# 4. Debug → Publish → API / WebApp 部署
```

---

## 8. 面试加分点

- Dify 本质上是 **"可视化的 LLMOps + Agent 操作系统"**
- 它把 **LangChain 的灵活性 + Flowise 的易用性 + Coze 的插件生态** 做了融合
- 2025–2026 最大趋势：**Agentic RAG + 多模态 + Plugin 生态**（类似 VS Code Marketplace）
- 企业私有化首选：**开源 + 多租户 + 观测性 + 与飞书/企业微信深度集成**
- 如果公司要做 AI 中台或 Agent 工厂，Dify 是目前性价比最高的开源底座
- **实战案例加分**：可以举旅游推荐 Agent 为例，展示 Hybrid 架构（Form + Agent Node + 多工具）如何实现"会问、会查、会算、会画"的智能体

---

## 9. 一句话总结

> **Dify 不是又一个低代码工具，它是 AI 时代的"可视化操作系统"，让团队用拖拽方式构建可投产的 Agentic AI 应用。**

面试开场可以说：
> "Dify 就是 AI 应用开发的 Figma —— 可视化、协作、从设计到上线一站式。"

---

## 参考资料

- [Dify 官方官网](https://dify.ai)
- [Dify 文档](https://docs.dify.ai)
- [Dify GitHub](https://github.com/langgenius/dify)

---

**更新日期**：2026 年 2 月
