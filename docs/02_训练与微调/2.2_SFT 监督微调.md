# 2.2 SFT 监督微调

> 📅 最后更新：2026-03-26  
> ⏱️ 阅读时间：12 分钟

---

## 一、什么是 SFT

**SFT（Supervised Fine-Tuning）**：用标注好的数据微调预训练模型。

```
预训练模型（通用知识）
       ↓
SFT 数据（任务特定）
       ↓
微调后模型（任务专家）
```

---

## 二、何时需要 SFT

### ✅ 需要 SFT 的场景

| 场景 | 原因 | 数据量 |
|------|------|--------|
| 客服问答 | 学习公司特定知识 | 500+ |
| 医疗诊断 | 专业术语和规范 | 2000+ |
| 法律文档 | 法律条文和格式 | 1000+ |
| 代码风格 | 团队编码规范 | 300+ |

### ❌ 不需要 SFT 的场景

- 通用问答 → 直接用基础模型
- 简单分类 → 用 Few-shot
- 数据<50 条 → 用 RAG

---

## 三、实战：微调 LLaMA-3

### 1. 准备环境

```bash
# 安装依赖
pip install transformers datasets accelerate peft

# 下载数据
git clone https://huggingface.co/datasets/llamastack/chinese-fineweb-edu
```

### 2. 加载模型

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_name = "meta-llama/Meta-Llama-3-8B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto"
)
```

### 3. 准备数据

```python
from datasets import load_dataset

dataset = load_dataset("json", data_files="sft_data.json", split="train")

def tokenize(example):
    return tokenizer(
        example["text"],
        truncation=True,
        max_length=512,
        padding="max_length"
    )

tokenized_dataset = dataset.map(tokenize, batched=True)
```

### 4. 配置训练

```python
from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir="./llama3-sft",
    num_train_epochs=3,
    per_device_train_batch_size=8,
    gradient_accumulation_steps=4,
    learning_rate=2e-5,
    warmup_steps=100,
    logging_steps=50,
    save_steps=500,
    fp16=True,
)
```

### 5. 开始训练

```python
from transformers import Trainer

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

trainer.train()

# 保存模型
trainer.save_model("./llama3-sft")
tokenizer.save_pretrained("./llama3-sft")
```

---

## 四、评估微调效果

### 1. 人工评估

```python
test_questions = [
    "公司的退货政策是什么？",
    "如何联系客服？",
    "产品保修期多久？"
]

for q in test_questions:
    inputs = tokenizer(q, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=100)
    print(f"Q: {q}")
    print(f"A: {tokenizer.decode(outputs[0])}")
    print("---")
```

### 2. 自动指标

```python
from sklearn.metrics import accuracy_score, f1_score

# 分类任务
predictions = model.predict(test_dataset)
acc = accuracy_score(test_labels, predictions)
f1 = f1_score(test_labels, predictions, average="weighted")

print(f"Accuracy: {acc:.4f}")
print(f"F1 Score: {f1:.4f}")
```

---

## 五、常见问题

### Q1：微调后效果变差了？

**可能原因**：
- 学习率太高 → 降到 1e-5
- 训练轮数太多 → 减到 2-3 轮
- 数据质量差 → 重新清洗

### Q2：过拟合怎么办？

**解决方案**：
- 增加 Dropout（0.1 → 0.2）
- 减少训练轮数
- 增加数据量
- 用 LoRA 而非全量微调

### Q3：需要多少 GPU？

**参考**：
- 7B 全量微调：4×A100 80G
- 7B LoRA 微调：1×RTX 4090
- 70B LoRA 微调：8×A100 80G

---

## 下一步

- 👉 [2.3 LoRA/QLoRA 高效微调](2.3_LoRA_QLoRA 高效微调.md)
- 👉 [3.1 KV Cache 与推理加速](../03_部署与推理/3.1_KVCache 与推理加速.md)

---

*完整代码：https://github.com/chenweidu666/AI-Engineering-Docs/tree/main/examples/sft*
