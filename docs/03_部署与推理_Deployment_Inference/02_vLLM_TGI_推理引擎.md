# 3.2 vLLM 推理部署

> 📅 最后更新：2026-03-26  
> ⏱️ 阅读时间：8 分钟

---

## 一、vLLM 简介

**vLLM**：UC Berkeley 开源的高性能推理框架。

**核心优势**：
- ✅ PagedAttention（显存利用率 90%+）
- ✅ 连续批处理（Continuous Batching）
- ✅ 高性能（2-4 倍于 Transformers）

---

## 二、快速开始

### 1. 安装

```bash
pip install vllm
```

### 2. Python API

```python
from vllm import LLM, SamplingParams

# 加载模型
llm = LLM(model="meta-llama/Meta-Llama-3-8B-Instruct")

# 配置生成参数
sampling_params = SamplingParams(
    temperature=0.7,
    max_tokens=100,
    top_p=0.9,
)

# 推理
prompts = ["你好，介绍一下你自己", "Python 怎么读文件？"]
outputs = llm.generate(prompts, sampling_params)

for output in outputs:
    print(output.outputs[0].text)
```

### 3. API 服务

```bash
python -m vllm.entrypoints.api_server \
    --model meta-llama/Meta-Llama-3-8B-Instruct \
    --port 8000 \
    --host 0.0.0.0
```

### 4. OpenAI 兼容调用

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="EMPTY"
)

response = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    messages=[
        {"role": "user", "content": "你好"}
    ]
)

print(response.choices[0].message.content)
```

---

## 三、高级配置

### 1. 多卡部署

```bash
# 张量并行
python -m vllm.entrypoints.api_server \
    --model llama-3-70b \
    --tensor-parallel-size 4
```

### 2. 量化部署

```bash
# AWQ 量化
python -m vllm.entrypoints.api_server \
    --model TheBloke/Llama-3-8B-AWQ \
    --quantization awq
```

### 3. 长上下文

```bash
python -m vllm.entrypoints.api_server \
    --model meta-llama/Meta-Llama-3-8B-Instruct \
    --max-model-len 128000 \
    --gpu-memory-utilization 0.95
```

---

## 四、性能优化

### 1. 显存配置

```bash
# 设置显存使用比例
--gpu-memory-utilization 0.9  # 默认 0.9

# CPU Offload（显存不足时）
--swap-space 4  # 4GB 交换空间
```

### 2. 批处理优化

```bash
# 最大批处理大小
--max-num-batched-tokens 4096

# 最大并发请求
--max-num-seqs 256
```

### 3. 调度策略

```python
# 调度器配置
llm = LLM(
    model="llama-3-8b",
    scheduler="virtual_token",  # 或 fcfs
)
```

---

## 五、监控与日志

### 1.  Prometheus 指标

```bash
# 启用指标
python -m vllm.entrypoints.api_server \
    --model llama-3-8b \
    --enable-metrics
```

**关键指标**：
- `vllm:num_requests_running`：正在处理的请求
- `vllm:gpu_cache_usage_perc`：显存使用率
- `vllm:time_to_first_token`：首 token 延迟

### 2. 日志级别

```bash
# 详细日志
export VLLM_LOGGING_LEVEL=DEBUG

# 生产环境
export VLLM_LOGGING_LEVEL=WARNING
```

---

## 六、常见问题

### Q1：OOM 怎么办？

**解决**：
- 减小 `--max-model-len`
- 降低 `--gpu-memory-utilization`
- 增加 `--swap-space`
- 用量化模型

### Q2：并发上不去？

**优化**：
- 增加 `--max-num-seqs`
- 用多卡（张量并行）
- 检查 GPU 利用率

### Q3：首 token 延迟高？

**优化**：
- 用更小的模型
- 减少上下文长度
- 用量化

---

## 下一步

- 👉 [3.3 INT4/INT8 量化](3.3_INT 量化.md)
- 👉 [6.1 FastAPI 服务化](../06_工程化/6.1_FastAPI 服务化.md)

---

*部署脚本：https://github.com/chenweidu666/AI-Engineering-Docs/tree/main/examples/vllm*
