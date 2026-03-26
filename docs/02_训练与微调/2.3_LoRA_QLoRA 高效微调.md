# 2.3 LoRA/QLoRA 高效微调

> 📅 最后更新：2026-03-26  
> ⏱️ 阅读时间：10 分钟

---

## 一、为什么用 LoRA

**全量微调的问题**：
- ❌ 显存占用大（7B 需要 80GB）
- ❌ 训练慢
- ❌ 每个任务存一个完整模型

**LoRA 的优势**：
- ✅ 显存小（7B 只需 16GB）
- ✅ 训练快（3-5 倍）
- ✅ 只存适配器（几 MB）

---

## 二、LoRA 原理

### 核心思想

冻结原模型，只训练低秩矩阵：

```
原权重：W₀ (d×d)

LoRA 更新：
W = W₀ + ΔW
ΔW = B × A

其中：
- A: (r×d) 低秩矩阵
- B: (d×r) 低秩矩阵
- r << d（通常 r=8 或 16）
```

### 显存对比

| 方法 | 7B 显存 | 70B 显存 |
|------|--------|---------|
| 全量微调 | 80GB | 800GB |
| LoRA | 16GB | 80GB |
| QLoRA | 12GB | 48GB |

---

## 三、实战：LoRA 微调

### 1. 安装 PEFT

```bash
pip install peft accelerate bitsandbytes
```

### 2. 配置 LoRA

```python
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=16,  # 秩
    lora_alpha=32,  # 缩放因子
    target_modules=["q_proj", "v_proj"],  # 目标层
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# 输出：trainable params: 4,194,304 || all params: 8,030,261,248
# 可训练参数仅占 0.05%
```

### 3. 训练

```python
from transformers import TrainingArguments, Trainer

training_args = TrainingArguments(
    output_dir="./lora-model",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    learning_rate=2e-4,  # LoRA 可以用更大学习率
    fp16=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
)

trainer.train()
```

### 4. 保存和加载

```python
# 保存（只存 LoRA 权重，几 MB）
model.save_pretrained("./lora-adapter")

# 加载
from peft import PeftModel

base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3-8B")
model = PeftModel.from_pretrained(base_model, "./lora-adapter")
```

---

## 四、QLoRA：量化 + LoRA

### 配置 QLoRA

```python
import torch
from transformers import BitsAndBytesConfig

# 4 比特量化配置
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

# 加载量化模型
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3-70B",
    quantization_config=bnb_config,
    device_map="auto"
)

# 再加 LoRA
model = get_peft_model(model, lora_config)
```

### 效果对比

| 配置 | 70B 显存 | 训练速度 | 精度损失 |
|------|---------|---------|---------|
| 全量 FP16 | 800GB | 1x | 0% |
| LoRA FP16 | 80GB | 3x | 0.5% |
| QLoRA INT4 | 48GB | 5x | 1% |

---

## 五、最佳实践

### 1. 秩（r）的选择

```python
# 小数据集（<1000 条）
r = 8

# 中等数据集（1000-10000 条）
r = 16

# 大数据集（>10000 条）
r = 32
```

### 2. 目标模块

```python
# 只 attention（最快）
target_modules = ["q_proj", "v_proj"]

# attention + MLP（效果更好）
target_modules = ["q_proj", "v_proj", "gate_proj", "up_proj", "down_proj"]

# 所有线性层（效果最好，但慢）
target_modules = "all-linear"
```

### 3. 学习率

```python
# LoRA 学习率通常比全量微调大 10 倍
learning_rate = 2e-4  # LoRA
learning_rate = 2e-5  # 全量
```

---

## 六、常见问题

### Q1：LoRA 效果比全量差多少？

**答**：通常差 1-3%，但显存只需 1/5，速度更快。

### Q2：可以叠加多个 LoRA 吗？

**答**：可以！用 PEFT 的多适配器功能：

```python
model.add_adapter("adapter1", lora_config)
model.add_adapter("adapter2", lora_config)

# 切换适配器
model.set_adapter("adapter1")  # 用于任务 1
model.set_adapter("adapter2")  # 用于任务 2
```

### Q3：QLoRA 量化会影响效果吗？

**答**：INT4 量化通常损失 1% 左右精度，但显存减半。

---

## 下一步

- 👉 [2.4 RLHF/DPO 对齐训练](2.4_RLHF_DPO 对齐训练.md)
- 👉 [3.3 INT4/INT8 量化](../03_部署与推理/3.3_INT 量化.md)

---

*代码示例：https://github.com/chenweidu666/AI-Engineering-Docs/tree/main/examples/lora*
