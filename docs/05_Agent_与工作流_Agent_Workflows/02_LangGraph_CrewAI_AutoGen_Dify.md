# 5.3 Dify 工作流平台

> 📅 最后更新：2026-03-26  
> ⏱️ 阅读时间：8 分钟

---

## 一、什么是 Dify

**Dify**：开源的 LLM 应用开发平台。

**核心功能**：
- ✅ 可视化工作流编排
- ✅ 内置 RAG 引擎
- ✅ 多模型管理
- ✅ 一键部署

---

## 二、快速开始

### 1. Docker 部署

```bash
git clone https://github.com/langgenius/dify
cd dify/docker
docker compose up -d
```

访问：http://localhost:3000

### 2. 创建应用

1. 点击"创建应用"
2. 选择"聊天助手"
3. 选择模型（GPT-4/Claude/本地）
4. 配置 Prompt

---

## 三、工作流编排

### 1. 节点类型

| 节点 | 功能 |
|------|------|
| 开始 | 输入变量 |
| LLM | 调用大模型 |
| 知识检索 | RAG 检索 |
| 条件判断 | if/else |
| HTTP 请求 | 调用 API |
| 代码执行 | Python/JS |
| 结束 | 输出结果 |

### 2. 示例：客服工作流

```
开始（用户问题）
  ↓
知识检索（从知识库找答案）
  ↓
条件判断
  ├─ 找到 → LLM 润色 → 结束
  └─ 未找到 → 转人工 → 结束
```

---

## 四、知识库管理

### 1. 上传文档

```
支持格式：PDF, Word, Markdown, TXT
自动切分：按段落/标题
向量化：自动嵌入
```

### 2. 检索配置

```yaml
检索方式：语义检索 / 关键词检索
返回数量：3-5 条
阈值：0.7（相似度）
```

---

## 五、API 调用

### 1. 获取 API Key

```
设置 → API 密钥 → 创建新密钥
```

### 2. 调用示例

```python
import requests

response = requests.post(
    "https://api.dify.ai/v1/chat-messages",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "inputs": {},
        "query": "你好",
        "response_mode": "blocking"
    }
)

print(response.json()["answer"])
```

---

## 六、常见问题

### Q1：Dify 和 LangChain 有什么区别？

**答**：
- Dify：可视化平台，开箱即用
- LangChain：代码框架，灵活但复杂

### Q2：支持哪些模型？

**答**：
- 商业 API：GPT-4/Claude/DeepSeek
- 开源模型：LLaMA/Qwen（通过 Ollama）
- 本地部署：vLLM/TGI

### Q3：如何私有化部署？

**答**：
```bash
# 修改 docker-compose.yml
# 配置本地模型 endpoint
# 配置本地向量数据库
```

---

## 下一步

- 👉 [5.4 AppAgent Android 自动化](5.4_AppAgent.md)
- 👉 [8.4 OpenClaw 本地部署指南](../08_OpenClaw 实战/04_OpenClaw 本地部署指南.md)

---

*Dify 官网：https://dify.ai*
