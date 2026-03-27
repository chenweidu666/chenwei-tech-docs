# 6.1 FastAPI 服务化

> 📅 最后更新：2026-03-26  
> ⏱️ 阅读时间：8 分钟

---

## 一、为什么用 FastAPI

**优势**：
- ✅ 自动文档（Swagger UI）
- ✅ 类型检查
- ✅ 高性能（接近 Node.js）
- ✅ 异步支持

---

## 二、快速开始

### 1. 安装

```bash
pip install fastapi uvicorn
```

### 2. Hello World

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
```

### 3. 启动

```bash
uvicorn main:app --reload
```

访问：http://localhost:8000/docs

---

## 三、LLM API 封装

### 1. 定义请求/响应

```python
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    temperature: float = 0.7

class ChatResponse(BaseModel):
    reply: str
    tokens: int
```

### 2. 实现 API

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("llama-3-8b")
tokenizer = AutoTokenizer.from_pretrained("llama-3-8b")

@app.post("/chat")
async def chat(req: ChatRequest) -> ChatResponse:
    inputs = tokenizer(req.message, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=100)
    reply = tokenizer.decode(outputs[0])
    
    return ChatResponse(
        reply=reply,
        tokens=len(outputs[0])
    )
```

---

## 四、高级功能

### 1. 中间件

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. 认证

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.get("/protected")
async def protected(
    creds: HTTPAuthorizationCredentials = Depends(security)
):
    if creds.credentials != "secret_token":
        raise HTTPException(401, "Unauthorized")
    return {"message": "OK"}
```

### 3. 后台任务

```python
from fastapi import BackgroundTasks

def send_email(email: str):
    # 发送邮件
    pass

@app.post("/signup")
async def signup(
    email: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(send_email, email)
    return {"message": "Signup successful"}
```

---

## 五、部署

### 1. Docker

```dockerfile
FROM python:3.11

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Gunicorn

```bash
gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

---

## 六、常见问题

### Q1：如何处理长请求？

**答**：
- 用异步（async/await）
- 设置超时
- 用后台任务

### Q2：如何限流？

**答**：
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api")
@limiter.limit("5/minute")
async def api_call(request: Request):
    ...
```

### Q3：如何监控？

**答**：
- Prometheus + Grafana
- 添加/metrics 端点
- 记录请求日志

---

## 下一步

- 👉 [6.2 Docker 容器化](6.2_Docker.md)
- 👉 [8.7 OpenClaw 技能开发指南](../08_OpenClaw 实战/07_OpenClaw 技能开发指南.md)

---

*完整示例：https://github.com/chenweidu666/AI-Engineering-Docs/tree/main/examples/fastapi*
