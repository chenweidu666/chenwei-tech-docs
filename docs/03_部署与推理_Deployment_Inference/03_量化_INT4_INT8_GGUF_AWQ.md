# 3.3 INT4/INT8 量化

> 📅 最后更新：2026-03-26  
> ⏱️ 阅读时间：8 分钟

---

## 一、量化基础

**量化**：用低精度表示权重，减少显存和计算。

```
FP16（原始）：16 bit，范围 ±65504
INT8（量化）：8 bit，范围 -128~127
INT4（量化）：4 bit，范围 -8~7
```

### 显存对比

| 精度 | LLaMA-3-8B | LLaMA-3-70B |
|------|-----------|-----------|
| FP16 | 16GB | 140GB |
| INT8 | 8GB | 70GB |
| INT4 | 4GB | 35GB |

---

## 二、量化方法

### 1. PTQ（训练后量化）

**无需训练，直接量化**。

```python
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",  # 正态分布量化
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,  # 双重量化
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Meta-Llama-3-8B",
    quantization_config=bnb_config,
)
```

**优点**：
- ✅ 简单，一行代码
- ✅ 无需训练数据
- ✅ 精度损失小（1-2%）

**缺点**：
- ❌ 精度略低于 QAT

### 2. QAT（量化感知训练）

**训练时模拟量化**。

```python
from torch.ao import quantization

# 准备量化配置
qconfig = torch.ao.quantization.get_default_qat_config('fbgemm')

# 应用到模型
model.qconfig = qconfig
model = torch.ao.quantization.prepare_qat(model)

# 训练...

# 转换为量化模型
model = torch.ao.quantization.convert(model)
```

**优点**：
- ✅ 精度最高
- ✅ 可针对特定任务优化

**缺点**：
- ❌ 需要训练
- ❌ 时间长

---

## 三、实战：INT4 量化

### 1. 用 BitsAndBytes

```python
import torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

# 配置
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

# 加载
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Meta-Llama-3-8B",
    quantization_config=bnb_config,
    device_map="auto",
)

# 推理
inputs = tokenizer("你好", return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=100)
print(tokenizer.decode(outputs[0]))
```

### 2. 用 AWQ

```bash
# 安装
pip install autoawq

# 量化
python -m awq.quantize \
    --model_path meta-llama/Meta-Llama-3-8B \
    --quant_path TheBloke/Llama-3-8B-AWQ \
    --w_bit 4 \
    --q_group_size 128
```

### 3. 用 GGUF（llama.cpp）

```bash
# 安装
pip install llama-cpp-python

# 量化
python -m llama_cpp.quantize \
    --input meta-llama-3-8B-f16.gguf \
    --output meta-llama-3-8B-Q4_K_M.gguf \
    --quantization Q4_K_M
```

---

## 四、精度对比

### 基准测试（MT-Bench）

| 模型 | 精度 | 显存 | 速度 |
|------|------|------|------|
| LLaMA-3-8B FP16 | 8.2 | 16GB | 1x |
| LLaMA-3-8B INT8 | 8.1 | 8GB | 1.5x |
| LLaMA-3-8B INT4 | 7.9 | 4GB | 2x |

### 主观评测

```
任务：写一封邮件

FP16：
"尊敬的客户，感谢您选择我们的服务..."

INT8：
"尊敬的客户，感谢您选择我们的服务..."（几乎一样）

INT4：
"尊敬的客户，感谢选择我们服务..."（略有简化）
```

---

## 五、部署量化模型

### 1. vLLM 部署

```bash
python -m vllm.entrypoints.api_server \
    --model TheBloke/Llama-3-8B-AWQ \
    --quantization awq \
    --gpu-memory-utilization 0.9
```

### 2. Ollama 部署

```bash
# 拉取量化模型
ollama pull llama3:4b

# 运行
ollama run llama3:4b
```

### 3. llama.cpp 部署

```bash
# CPU 推理（无需 GPU）
./main -m models/llama-3-8B-Q4_K_M.gguf \
    -p "你好" \
    -n 100
```

---

## 六、常见问题

### Q1：量化后效果差多少？

**答**：
- INT8：损失 0.5-1%
- INT4：损失 1-2%
- 对大多数应用可接受

### Q2：所有模型都能量化吗？

**答**：
- 大部分可以（LLaMA/Qwen/ChatGLM）
- 有些模型量化后效果差（需测试）
- MoE 模型量化更复杂

### Q3：量化后还能微调吗？

**答**：
- 可以，用 QLoRA
- 冻结量化权重，只训练 LoRA
- 显存只需 1/4

---

## 下一步

- 👉 [第四章：RAG 与知识库](../04_RAG 与知识库/4.1_RAG 检索增强生成.md)
- 👉 [5.2 MCP 协议](../05_Agent 开发/5.2_MCP 协议.md)

---

*量化模型下载：https://huggingface.co/TheBloke*
