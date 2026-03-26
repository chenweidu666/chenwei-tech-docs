<div style="text-align: center; font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;"><strong>OpenClaw 技能开发指南</strong></div>
> 2026-03-25 | 🦞 双龙虾架构实战系列第 7 篇

---

- [技能架构](#技能架构)
- [技能模板](#技能模板)
- [开发流程](#开发流程)
- [测试调试](#测试调试)
- [发布流程](#发布流程)
- [最佳实践](#最佳实践)
- [案例解析](#案例解析)


---

## 📋 目录

- [技能架构](#技能架构)
- [技能模板](#技能模板)
- [开发流程](#开发流程)
- [测试调试](#测试调试)
- [发布流程](#发布流程)
- [最佳实践](#最佳实践)
- [案例解析](#案例解析)

---

## 技能架构

### 技能目录结构

```
skill-name/
├── SKILL.md              # 技能说明（必需）
├── _meta.json            # 元数据（必需）
├── scripts/
│   ├── main.mjs          # 主脚本
│   └── utils.mjs         # 工具函数
├── references/
│   ├── api_reference.md  # API 文档
│   └── config_template.json  # 配置模板
├── setup.sh              # 安装脚本
└── .clawhub/
    └── origin.json       # clawhub 源信息
```

---

### SKILL.md 结构

```markdown
# Skill Name

技能描述。

## Activation

当用户提及关键词时激活：
- 关键词 1
- 关键词 2

## Capabilities

- 功能 1
- 功能 2
- 功能 3

## Configuration

需要配置以下环境变量：
- `API_KEY`: API 密钥
- `BASE_URL`: API 地址

## Usage

示例用法：
- "示例问题 1"
- "示例问题 2"
```

---

### _meta.json 结构

```json
{
  "name": "skill-name",
  "version": "1.0.0",
  "description": "技能描述",
  "author": "Your Name",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"],
  "scripts": ["scripts/main.mjs"],
  "dependencies": ["node-fetch"],
  "env": {
    "API_KEY": {
      "required": true,
      "description": "API 密钥"
    }
  }
}
```

---

## 技能模板

### 基础模板

**创建技能目录**：
```bash
cd /root/.openclaw/workspace/skills
mkdir my-skill
cd my-skill
```

---

**SKILL.md**：
```markdown
# My Skill

我的技能描述。

## Activation

当用户提及：
- 关键词 1
- 关键词 2

## Capabilities

- 功能 1
- 功能 2

## Configuration

需要配置：
- `API_KEY`: API 密钥

## Usage

- "帮我做 XXX"
- "查询 XXX"
```

---

**_meta.json**：
```json
{
  "name": "my-skill",
  "version": "1.0.0",
  "description": "我的技能",
  "author": "Your Name",
  "license": "MIT",
  "keywords": ["keyword"],
  "scripts": ["scripts/main.mjs"],
  "dependencies": [],
  "env": {
    "API_KEY": {
      "required": true,
      "description": "API 密钥"
    }
  }
}
```

---

**scripts/main.mjs**：
```javascript
// My Skill - 主脚本

export async function main(context) {
  const { message, env } = context;
  
  // 获取配置
  const apiKey = env.API_KEY;
  
  // 处理用户消息
  if (message.includes('关键词 1')) {
    return await handleKeyword1(message, apiKey);
  }
  
  if (message.includes('关键词 2')) {
    return await handleKeyword2(message, apiKey);
  }
  
  return "我不太明白，请换个说法试试~";
}

async function handleKeyword1(message, apiKey) {
  // 实现功能 1
  const result = await doSomething(apiKey);
  return `这是结果：${result}`;
}

async function handleKeyword2(message, apiKey) {
  // 实现功能 2
  return "这是功能 2 的结果";
}

async function doSomething(apiKey) {
  // 调用 API
  const response = await fetch('https://api.example.com/data', {
    headers: {
      'Authorization': `Bearer ${apiKey}`
    }
  });
  const data = await response.json();
  return data.result;
}
```

---

## 开发流程

### Step 1: 需求分析

**明确技能功能**：
- 解决什么问题？
- 输入是什么？
- 输出是什么？
- 需要哪些外部 API？

---

### Step 2: 创建骨架

```bash
# 创建目录结构
cd /root/.openclaw/workspace/skills
mkdir my-skill
cd my-skill

mkdir scripts references .clawhub

# 创建文件
touch SKILL.md _meta.json scripts/main.mjs setup.sh
```

---

### Step 3: 编写代码

**编辑 main.mjs**：
```javascript
export async function main(context) {
  const { message, env } = context;
  
  // 你的逻辑
  // ...
  
  return "结果";
}
```

---

### Step 4: 配置环境

**创建 .env 文件**：
```bash
cat > .env << 'EOF'
API_KEY=your-api-key
BASE_URL=https://api.example.com
EOF
```

---

**配置模板**：
```json
{
  "name": "my-skill",
  "env": {
    "API_KEY": "your-api-key"
  }
}
```

---

## 测试调试

### 本地测试

**创建测试脚本**：
```javascript
// scripts/test.mjs
import { main } from './main.mjs';

const context = {
  message: "测试消息",
  env: {
    API_KEY: "test-key"
  }
};

const result = await main(context);
console.log("测试结果:", result);
```

---

**运行测试**：
```bash
cd /root/.openclaw/workspace/skills/my-skill
node scripts/test.mjs
```

---

### OpenClaw 中测试

**重启 Gateway**：
```bash
openclaw gateway restart
```

---

**在对话中测试**：
```
你：使用 my-skill 功能
AI: [技能响应]
```

---

### 日志调试

**查看日志**：
```bash
# 实时日志
openclaw logs

# 或查看日志文件
tail -f ~/.openclaw/agents/main/logs/*.log
```

---

**添加日志输出**：
```javascript
export async function main(context) {
  console.log("🔍 收到消息:", context.message);
  
  // ...
  
  console.log("✅ 处理完成");
  return result;
}
```

---

## 发布流程

### 发布到 clawhub

**初始化 clawhub**：
```bash
cd /root/.openclaw/workspace/skills/my-skill
npx clawhub@latest init
```

---

**发布**：
```bash
npx clawhub@latest publish
```

---

**更新**：
```bash
# 修改版本号
vim _meta.json  # 修改 version

# 发布新版本
npx clawhub@latest publish
```

---

### 发布到 GitHub

**初始化 Git**：
```bash
cd /root/.openclaw/workspace/skills/my-skill
git init
git add .
git commit -m "Initial commit"
```

---

**推送到 GitHub**：
```bash
git remote add origin git@github.com:yourname/my-skill.git
git push -u origin master
```

---

**添加 Release**：
```bash
# 打标签
git tag v1.0.0
git push origin v1.0.0
```

---

## 最佳实践

### 代码规范

**使用 ESM 模块**：
```javascript
// ✅ 推荐
export async function main(context) {
  // ...
}

// ❌ 不推荐
module.exports = async function(context) {
  // ...
}
```

---

**错误处理**：
```javascript
export async function main(context) {
  try {
    // 你的逻辑
    return result;
  } catch (error) {
    console.error("❌ 错误:", error);
    return `出错了：${error.message}`;
  }
}
```

---

**环境变量**：
```javascript
// ✅ 推荐
const apiKey = env.API_KEY || process.env.API_KEY;

// ❌ 不推荐
const apiKey = "hardcoded-key";  // 不要硬编码密钥
```

---

### 性能优化

**缓存结果**：
```javascript
const cache = new Map();

export async function main(context) {
  const cacheKey = context.message;
  
  if (cache.has(cacheKey)) {
    return cache.get(cacheKey);
  }
  
  const result = await doSomething();
  cache.set(cacheKey, result);
  
  return result;
}
```

---

**批量处理**：
```javascript
// ✅ 推荐：批量 API 调用
const results = await Promise.all(items.map(item => fetchItem(item)));

// ❌ 不推荐：逐个调用
for (const item of items) {
  await fetchItem(item);  // 慢
}
```

---

### 安全实践

**不泄露密钥**：
```bash
# .gitignore
echo ".env" >> .gitignore
echo "secrets/" >> .gitignore
```

---

**输入验证**：
```javascript
export async function main(context) {
  const message = context.message?.trim();
  
  if (!message || message.length > 1000) {
    return "消息格式不正确";
  }
  
  // ...
}
```

---

## 案例解析

### 案例 1：天气查询技能

**SKILL.md**：
```markdown
# Weather

天气查询技能。

## Activation

- 天气
- 气温
- 下雨

## Capabilities

- 查询当前天气
- 查询天气预报

## Usage

- "北京天气怎么样？"
- "上海明天会下雨吗？"
```

---

**main.mjs**：
```javascript
export async function main(context) {
  const { message } = context;
  
  // 提取城市名
  const city = extractCity(message);
  
  if (!city) {
    return "请告诉我你想查询哪个城市的天气~";
  }
  
  // 调用天气 API
  const weather = await fetchWeather(city);
  
  return `${city}当前天气：${weather.condition}，气温${weather.temp}°C`;
}

function extractCity(message) {
  const cities = ['北京', '上海', '广州', '深圳'];
  for (const city of cities) {
    if (message.includes(city)) return city;
  }
  return null;
}

async function fetchWeather(city) {
  const response = await fetch(
    `https://api.weather.com/v1/current?city=${city}`
  );
  return response.json();
}
```

---

### 案例 2：GitHub 技能

**_meta.json**：
```json
{
  "name": "github",
  "version": "1.0.0",
  "description": "GitHub 操作技能",
  "keywords": ["github", "git", "repo"],
  "scripts": ["scripts/main.mjs"],
  "env": {
    "GITHUB_TOKEN": {
      "required": true,
      "description": "GitHub Token"
    }
  }
}
```

---

**main.mjs**：
```javascript
export async function main(context) {
  const { message, env } = context;
  const token = env.GITHUB_TOKEN;
  
  if (message.includes('仓库')) {
    return await listRepos(token);
  }
  
  if (message.includes('Issue')) {
    return await listIssues(token);
  }
  
  return "我可以帮你查询 GitHub 仓库、Issue 等信息~";
}

async function listRepos(token) {
  const response = await fetch('https://api.github.com/user/repos', {
    headers: {
      'Authorization': `token ${token}`
    }
  });
  const repos = await response.json();
  
  return `你有 ${repos.length} 个仓库:\n` + 
    repos.slice(0, 5).map(r => `- ${r.name}`).join('\n');
}

async function listIssues(token) {
  const response = await fetch(
    'https://api.github.com/user/issues',
    {
      headers: {
        'Authorization': `token ${token}`
      }
    }
  );
  const issues = await response.json();
  
  return `你有 ${issues.length} 个 Issue:\n` +
    issues.slice(0, 5).map(i => `- ${i.title}`).join('\n');
}
```

---

## 下一篇

👉 [08_常见问题与故障排查](./08_常见问题与故障排查.md)

---

*本文档由 里斯本 🦞 自动记录 | Powered by OpenClaw + Claude*
