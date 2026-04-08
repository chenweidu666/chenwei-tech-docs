# Hermes Agent 配置阿里云 Claude 兼容接口指南

## 1. 环境准备

### 1.1 系统要求
- macOS / Linux / Windows (WSL2)
- Python 3.9+
- Git
- Node.js (可选，用于浏览器工具)

### 1.2 依赖工具
- `curl` - 用于下载安装脚本
- `git` - 用于克隆仓库
- `uv` - Python 包管理器（会自动安装）

## 2. 安装 Hermes Agent

### 2.1 一键安装（推荐）
```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

### 2.2 手动安装（备选）
```bash
# 安装 uv 包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆仓库
git clone --recurse-submodules https://github.com/NousResearch/hermes-agent.git
cd hermes-agent

# 创建虚拟环境
uv venv
source .venv/bin/activate

# 安装依赖
uv pip install -e ".[all]"
uv pip install -e "./mini-swe-agent"

# 安装 Node.js 依赖
npm install
```

## 3. 配置阿里云 Claude 兼容接口

### 3.1 配置文件设置

创建或编辑 `~/.hermes/config.yaml` 文件：

```yaml
# Hermes Agent Configuration

# Model settings
model:
  default: "anthropic/qwen3.5-plus"
  provider: "anthropic"
  api_key: "sk-sp-4a72cbac7f5d407eb9e0041e234fb563"
  base_url: "https://coding.dashscope.aliyuncs.com/apps/anthropic"
  max_tokens: 4096  # 阿里云要求范围 [1, 65536]

# OpenAI compatible settings for Qwen models
openai:
  api_key: "sk-sp-4a72cbac7f5d407eb9e0041e234fb563"
  base_url: "https://coding.dashscope.aliyuncs.com/v1"
  model: "qwen3.5-plus"
  max_tokens: 4096  # 阿里云要求范围 [1, 65536]
```

### 3.2 环境变量设置

创建或编辑 `~/.hermes/.env` 文件：

```bash
# Hermes Agent Environment Variables

# Anthropic API settings
ANTHROPIC_API_KEY=sk-sp-4a72cbac7f5d407eb9e0041e234fb563
ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic

# OpenAI API settings (for Qwen models)
OPENAI_API_KEY=sk-sp-4a72cbac7f5d407eb9e0041e234fb563
OPENAI_BASE_URL=https://coding.dashscope.aliyuncs.com/v1

# Default model
HERMES_DEFAULT_MODEL=anthropic/qwen3.5-plus
HERMES_INFERENCE_PROVIDER=anthropic
```

## 4. 验证配置

### 4.1 检查配置
```bash
hermes config
```

预期输出：
- Anthropic API 密钥显示为 `sk-s...b563`（部分隐藏）
- 模型配置为 `anthropic/qwen3.5-plus`
- 基础 URL 为 `https://coding.dashscope.aliyuncs.com/apps/anthropic`

### 4.2 测试连接
```bash
hermes
```

然后输入：
```
你好
```

如果配置正确，Hermes Agent 应该能够正常响应，不会显示认证错误。

## 5. 开机自启动配置

### 5.1 创建启动脚本
```bash
mkdir -p ~/.scripts && cat > ~/.scripts/start-hermes.sh << 'EOF'
#!/bin/bash

# Start Hermes agent gateway
/Users/chenwei/.local/bin/hermes gateway &

echo "Hermes agent started at $(date)" >> ~/.hermes/logs/startup.log
EOF

chmod +x ~/.scripts/start-hermes.sh
```

### 5.2 添加到 shell 配置
```bash
if [ -f ~/.zshrc ]; then
    echo '\n# Start Hermes agent gateway\nif ! pgrep -f "hermes gateway" > /dev/null; then\n    ~/.scripts/start-hermes.sh\nfi' >> ~/.zshrc
elif [ -f ~/.bashrc ]; then
    echo '\n# Start Hermes agent gateway\nif ! pgrep -f "hermes gateway" > /dev/null; then\n    ~/.scripts/start-hermes.sh\nfi' >> ~/.bashrc
fi

# 重新加载配置
source ~/.zshrc  # 或 source ~/.bashrc
```

## 6. 常见问题排查

### 6.1 认证错误
- 错误信息：`No Anthropic credentials found`
- 解决方案：确保 `.env` 文件中的 API 密钥正确设置

### 6.2 连接超时
- 错误信息：`Connection timeout`
- 解决方案：检查网络连接，确保能够访问阿里云 API 端点

### 6.3 模型未找到
- 错误信息：`Model not found`
- 解决方案：确保模型名称正确，阿里云的 Qwen 模型使用 `qwen3.5-plus`

### 6.4 命令未找到
- 错误信息：`zsh: command not found: hermes`
- 解决方案：确保 `~/.local/bin` 在 PATH 环境变量中，或重新安装 Hermes Agent

### 6.5 max_tokens 参数错误
- 错误信息：`Range of max_tokens should be [1, 65536]`
- 解决方案：在 `config.yaml` 中明确设置 `max_tokens` 参数，推荐值为 4096
- 配置示例：
  ```yaml
  model:
    max_tokens: 4096
  openai:
    max_tokens: 4096
  ```

## 7. 相关资源

- [Hermes Agent 官方文档](https://hermes-agent.nousresearch.com/docs)
- [阿里云 DashScope 文档](https://help.aliyun.com/document_detail/611753.html)
- [GitHub 仓库](https://github.com/NousResearch/hermes-agent)

## 8. 版本信息

- Hermes Agent 版本：v0.8.0 (2026.4.8)
- 配置日期：2026-04-08
- 测试环境：macOS

---

**注意**：本配置指南使用的 API 密钥和端点地址仅供参考，请根据实际情况进行修改。