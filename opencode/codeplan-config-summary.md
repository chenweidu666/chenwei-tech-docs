# OpenCode + 阿里云 CodePlan 配置指南

## ✅ 配置已验证成功

### API 信息
- **API 密钥**: `sk-sp-4a72cbac7f5d407eb9e0041e234fb563`
- **Anthropic 兼容接口**: `https://coding.dashscope.aliyuncs.com/apps/anthropic/v1`
- **模型**: `qwen3.5-plus`

## 1. OpenCode 配置（已验证可用）

### 配置文件
文件路径: `~/.config/opencode/opencode.json`

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "bailian-coding-plan": {
      "npm": "@ai-sdk/anthropic",
      "name": "Model Studio Coding Plan",
      "options": {
        "baseURL": "https://coding.dashscope.aliyuncs.com/apps/anthropic/v1",
        "apiKey": "sk-sp-4a72cbac7f5d407eb9e0041e234fb563"
      },
      "models": {
        "qwen3.5-plus": {
          "name": "Qwen3.5 Plus",
          "modalities": {
            "input": ["text", "image"],
            "output": ["text"]
          },
          "options": {
            "thinking": {
              "type": "enabled",
              "budgetTokens": 8192
            }
          },
          "limit": {
            "context": 1000000,
            "output": 65536
          }
        }
      }
    }
  }
}
```

## 2. 关键配置点

### ⚠️ 重要注意事项

1. **Base URL 必须包含 `/v1` 末尾**
   - ❌ 错误: `https://coding.dashscope.aliyuncs.com/apps/anthropic`
   - ✅ 正确: `https://coding.dashscope.aliyuncs.com/apps/anthropic/v1`

2. **提供商名称**: `bailian-coding-plan` (不是 `anthropic`)

3. **必须定义 models**: 在配置中明确列出可用的模型

## 3. 使用方法

### 启动 OpenCode
```bash
opencode
```

### 运行单次命令
```bash
opencode run -m bailian-coding-plan/qwen3.5-plus "你好"
```

### 在 TUI 中选择模型
1. 运行 `opencode`
2. 输入 `/models`
3. 搜索 `Model Studio Coding Plan`
4. 选择 `qwen3.5-plus`

### 列出可用模型
```bash
opencode models 2>&1 | grep bailian-coding-plan
```

输出:
```
bailian-coding-plan/qwen3.5-plus
```

## 4. 环境变量（可选）

如果需要设置环境变量，添加到 `~/.zshrc` 或 `~/.bashrc`:

```bash
# OpenCode / Claude CodePlan Configuration
export CLAUDE_API_KEY=sk-sp-4a72cbac7f5d407eb9e0041e234fb563
export CLAUDE_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic/v1
export CLAUDE_MODEL=qwen3.5-plus
export ANTHROPIC_API_KEY=sk-sp-4a72cbac7f5d407eb9e0041e234fb563
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic/v1
```

## 5. 测试结果

### ✅ API 连接测试成功

```bash
curl -s "https://coding.dashscope.aliyuncs.com/apps/anthropic/v1/messages" \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-sp-4a72cbac7f5d407eb9e0041e234fb563" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "qwen3.5-plus",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

响应:
```json
{
  "role": "assistant",
  "model": "qwen3.5-plus",
  "content": [
    {"type": "thinking", "thinking": "Thinking Process: ..."},
    {"type": "text", "text": "你好！有什么我可以帮你的吗？"}
  ]
}
```

### ✅ OpenCode 运行测试成功

```bash
opencode run -m bailian-coding-plan/qwen3.5-plus "你好，请介绍一下你自己"
```

输出:
```
> build · qwen3.5-plus

你好！我是 opencode，一个运行在命令行界面的交互式编程助手工具。我可以帮助你完成各种软件工程任务，比如：

- 编写和调试代码
- 搜索和理解代码库
- 修改和重构代码
- 运行命令和测试
- 处理文件和目录

我主要通过工具调用来帮你完成任务，而不是仅仅给出建议。有什么我可以帮助你的吗？
```

## 6. 相关资源

- [阿里云 CodePlan 文档](https://help.aliyun.com/zh/model-studio/coding-plan-faq)
- [OpenCode 官方文档](https://opencode.ai/docs)
- [Anthropic API 文档](https://docs.anthropic.com/)

## 7. 版本信息

- **配置日期**: 2026-04-08
- **测试状态**: ✅ 全部通过
- **OpenCode 版本**: 1.3.17