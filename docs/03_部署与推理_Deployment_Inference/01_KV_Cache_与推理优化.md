# 3.1 KV Cache 与推理加速

> 📅 最后更新：2026-03-26  
> ⏱️ 阅读时间：10 分钟

---

## 一、为什么需要 KV Cache

**问题**：生成每个 token 都要重新计算所有 K/V，太慢。

```
无 Cache：
生成 token 1: 计算 1 个位置
生成 token 2: 计算 2 个位置
生成 token 3: 计算 3 个位置
...
生成 token 100: 计算 100 个位置

总计算量：1+2+3+...+100 = 5050
```

**KV Cache**：缓存已计算的 K/V，避免重复计算。

```
有 Cache：
生成 token 1: 计算 1 个位置，缓存
生成 token 2: 复用缓存 + 计算 1 个新位置
生成 token 3: 复用缓存 + 计算 1 个新位置
...

总计算量：100（线性增长）
```

**加速比**：50 倍+

---

## 二、KV Cache 原理

### 注意力计算

```python
# 无 Cache
def attention(Q, K, V):
    scores = Q @ K.transpose(-2, -1) / sqrt(d)
    weights = softmax(scores)
    return weights @ V

# 有 Cache
def attention_with_cache(Q, K, V, cache_k, cache_v):
    # 拼接缓存
    K = torch.cat([cache_k, K], dim=-2)
    V = torch.cat([cache_v, V], dim=-2)
    
    # 更新缓存
    new_cache_k = K
    new_cache_v = V
    
    # 计算注意力
    scores = Q @ K.transpose(-2, -1) / sqrt(d)
    weights = softmax(scores)
    output = weights @ V
    
    return output, new_cache_k, new_cache_v
```

### 显存占用

```
KV Cache 大小 = 2 × batch_size × seq_len × num_layers × hidden_size × dtype

示例（LLaMA-3-8B，batch=1，seq=4096）：
= 2 × 1 × 4096 × 32 × 4096 × 2 bytes
= 4GB
```

---

## 三、优化技术

### 1. GQA（Grouped-Query Attention）

**核心**：减少 K/V 头数。

```python
# MHA（多头注意力）
Q: 32 heads
K: 32 heads
V: 32 heads
KV Cache: 100%

# GQA（分组查询）
Q: 32 heads
K: 8 heads  # 减少 4 倍
V: 8 heads
KV Cache: 25%

# MQA（多查询）
Q: 32 heads
K: 1 head   # 极致压缩
V: 1 head
KV Cache: 3%
```

### 2. PagedAttention（vLLM）

**核心**：像操作系统管理内存一样管理 KV Cache。

```python
# 传统：连续内存，容易碎片化
[Block1][Block2][   空闲   ][Block3]

# PagedAttention：分页管理，利用率高
Page0 → Block1
Page1 → Block3
Page2 → Block2
```

**优势**：
- ✅ 显存利用率 90%+（传统 60%）
- ✅ 支持更大 batch
- ✅ 减少 OOM

### 3. FlashAttention

**核心**：IO 感知的注意力算法。

```
传统 Attention：
GPU HBM ↔ SRAM 多次读写

FlashAttention：
分块计算，减少 HBM 访问

加速：2-3 倍
```

---

## 四、实战：vLLM 部署

### 1. 安装

```bash
pip install vllm
```

### 2. 启动服务

```bash
python -m vllm.entrypoints.api_server \
    --model meta-llama/Meta-Llama-3-8B-Instruct \
    --port 8000 \
    --gpu-memory-utilization 0.9 \
    --max-model-len 8192
```

### 3. API 调用

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="EMPTY"  # vLLM 不需要 key
)

response = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    messages=[
        {"role": "user", "content": "你好"}
    ],
    max_tokens=100,
)

print(response.choices[0].message.content)
```

### 4. 性能对比

| 框架 | 吞吐量 (token/s) | 显存占用 | 并发支持 |
|------|-----------------|---------|---------|
| Transformers | 30 | 高 | 低 |
| vLLM | 150 | 低 | 高 |
| TGI | 120 | 中 | 中 |

---

## 五、量化加速

### INT8 量化

```python
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_8bit=True,
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3-8B",
    quantization_config=bnb_config,
)
```

**效果**：
- 显存：16GB → 8GB
- 速度：1.5 倍
- 精度损失：<1%

### INT4 量化

```python
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)
```

**效果**：
- 显存：16GB → 4GB
- 速度：2 倍
- 精度损失：1-2%

---

## 六、常见问题

### Q1：如何选择 batch size？

**答**：
- 显存充足：batch=32-64
- 显存紧张：batch=8-16
- 用 vLLM：自动优化

### Q2：长上下文怎么处理？

**答**：
- 用支持长上下文的模型（128K+）
- 开启 sliding window（只缓存最近 N 个 token）
- 用稀疏注意力

### Q3：多卡推理怎么部署？

**答**：
```bash
# 张量并行（推荐）
python -m vllm.entrypoints.api_server \
    --model llama-3-70b \
    --tensor-parallel-size 4  # 4 卡并行
```

---

## 下一步

- 👉 [3.2 vLLM 推理部署](3.2_vLLM 推理部署.md)
- 👉 [3.3 INT4/INT8 量化](3.3_INT 量化.md)

---

*性能基准：https://github.com/chenweidu666/AI-Engineering-Docs/tree/main/benchmarks*
