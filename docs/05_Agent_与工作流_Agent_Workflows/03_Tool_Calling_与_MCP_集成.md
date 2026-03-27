# 5.2 MCP 协议

> 📅 最后更新：2026-03-26  
> ⏱️ 阅读时间：8 分钟

---

## 一、什么是 MCP

**MCP（Model Context Protocol）**：大模型与外部工具的标准通信协议。

**类比**：USB 接口之于电脑设备。

---

## 二、核心概念

### 1. 架构

```
┌─────────────┐
│   Client    │ ← 大模型/应用
│  (LLM App)  │
└──────┬──────┘
       │ MCP 协议
┌──────┴──────┐
│   Server    │ ← 工具提供者
│  (Tools)    │
└─────────────┘
```

### 2. 通信方式

```json
// 请求
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search",
    "arguments": {"query": "AI 新闻"}
  }
}

// 响应
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": "搜索结果..."
  }
}
```

---

## 三、实战：MCP Server

### 1. 安装 SDK

```bash
pip install mcp
```

### 2. 创建 Server

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

server = Server("my-tools")

@server.tool()
def search(query: str) -> str:
    """搜索网络"""
    return f"搜索：{query}"

@server.tool()
def calculate(expr: str) -> float:
    """计算表达式"""
    return eval(expr)

async with stdio_server() as streams:
    await server.run(streams[0], streams[1])
```

### 3. 启动 Server

```bash
python mcp_server.py
```

### 4. Client 调用

```python
from mcp.client import Client

client = Client("my-tools")
await client.connect()

# 调用工具
result = await client.call_tool("search", {"query": "AI"})
print(result)
```

---

## 四、现有 MCP Servers

### 官方提供

| Server | 功能 |
|--------|------|
| filesystem | 文件系统操作 |
| postgres | PostgreSQL 数据库 |
| slack | Slack 消息 |
| github | GitHub API |
| puppeteer | 浏览器自动化 |

### 安装示例

```bash
# 文件系统
npx -y @modelcontextprotocol/server-filesystem ~/data

# PostgreSQL
npx -y @modelcontextprotocol/server-postgres postgres://localhost/mydb

# GitHub
npx -y @modelcontextprotocol/server-github
```

---

## 五、集成到 LLM

### Claude Desktop 配置

```json
// claude_desktop_config.json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "~/data"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "your_token"
      }
    }
  }
}
```

### 使用效果

```
用户：帮我找一下 data 文件夹里的 README 文件
Claude: [调用 filesystem 工具]
      找到了：/data/project/README.md
      内容是：...
```

---

## 六、常见问题

### Q1：MCP 和 Function Calling 有什么区别？

**答**：
- Function Calling：模型内置，需预定义
- MCP：外部服务，动态扩展

### Q2：安全性如何保证？

**答**：
- 权限控制（只读/读写）
- 沙箱环境
- 用户确认机制

### Q3：性能如何？

**答**：
- 本地 Server：<10ms
- 远程 Server：50-200ms
- 可缓存优化

---

## 下一步

- 👉 [5.3 Dify 工作流平台](5.3_Dify 工作流平台.md)
- 👉 [8.5 Gate 交易所 MCP 集成](../08_OpenClaw 实战/05_Gate 交易所 MCP 集成.md)

---

*MCP 规范：https://modelcontextprotocol.io/*
