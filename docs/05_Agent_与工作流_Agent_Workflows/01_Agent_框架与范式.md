# 5.1 Agent 设计与工作流

> 📅 最后更新：2026-03-26  
> ⏱️ 阅读时间：10 分钟

---

## 一、什么是 Agent

**Agent = 大模型 + 规划 + 工具使用**

```
传统 AI：输入 → 输出

Agent：输入 → 思考 → 规划 → 使用工具 → 输出
```

---

## 二、核心能力

### 1. 规划（Planning）

```python
任务："分析某公司股票"

Agent 思考：
1. 获取股票价格 → 调用 Yahoo Finance API
2. 查看新闻 → 搜索最近新闻
3. 分析情绪 → 用情感分析模型
4. 生成报告 → 综合所有信息
```

### 2. 工具使用（Tool Use）

```python
tools = [
    SearchEngine(),    # 搜索
    Calculator(),      # 计算
    CodeInterpreter(), # 代码执行
    Database(),        # 数据库查询
]
```

### 3. 记忆（Memory）

```python
memory = {
    "short_term": "最近对话历史",
    "long_term": "用户偏好、事实知识",
}
```

---

## 三、实战：LangChain Agent

### 1. 安装

```bash
pip install langchain langchain-openai
```

### 2. 定义工具

```python
from langchain.tools import tool

@tool
def search(query: str) -> str:
    """搜索网络信息"""
    return f"搜索结果：{query}"

@tool
def calculate(expression: str) -> str:
    """计算数学表达式"""
    return str(eval(expression))

tools = [search, calculate]
```

### 3. 创建 Agent

```python
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(model="gpt-4", temperature=0)

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)
```

### 4. 运行

```python
response = agent.run("北京到上海的距离乘以 2 是多少？")
print(response)
```

**输出**：
```
> Entering new AgentExecutor chain...
Thought: 我需要先搜索北京到上海的距离
Action: search
Action Input: "北京到上海的距离"
Observation: 约 1200 公里
Thought: 现在计算乘以 2
Action: calculate
Action Input: 1200 * 2
Observation: 2400
Thought: 我得到答案了
Final Answer: 北京到上海的距离乘以 2 是 2400 公里
```

---

## 四、工作流模式

### 1. 顺序工作流

```python
workflow = [
    "收集信息",
    "分析数据",
    "生成报告",
    "审核输出",
]
```

### 2. 条件工作流

```python
if 情感 == "负面":
    转人工客服
else:
    自动回复
```

### 3. 循环工作流

```python
while 任务未完成:
    执行一步
    检查结果
    if 成功:
        break
```

---

## 五、多 Agent 协作

```python
# 研究者 Agent
researcher = Agent(role="研究员", tools=[SearchEngine()])

# 分析师 Agent
analyst = Agent(role="分析师", tools=[Calculator()])

# 作家 Agent
writer = Agent(role="作家", tools=[])

# 协作流程
research_result = researcher.run("查询 AI 发展趋势")
analysis = analyst.run(f"分析：{research_result}")
report = writer.run(f"写报告：{analysis}")
```

---

## 六、常见问题

### Q1：Agent 执行太慢？

**优化**：
- 减少工具数量
- 设置最大迭代次数
- 用更小的模型做规划

### Q2：Agent 陷入循环？

**解决**：
- 设置最大迭代次数（max_iterations=5）
- 添加超时机制
- 检查工具定义

### Q3：如何调试 Agent？

**方法**：
- 开启 verbose=True
- 记录每一步思考
- 可视化执行轨迹

---

## 下一步

- 👉 [5.2 MCP 协议](5.2_MCP 协议.md)
- 👉 [5.3 Dify 工作流平台](5.3_Dify 工作流平台.md)

---

*代码示例：https://github.com/chenweidu666/AI-Engineering-Docs/tree/main/examples/agent*
