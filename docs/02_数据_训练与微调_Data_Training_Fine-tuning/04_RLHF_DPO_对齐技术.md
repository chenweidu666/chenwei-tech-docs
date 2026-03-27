# 2.4 RLHF/DPO 对齐训练

> 📅 最后更新：2026-03-26  
> ⏱️ 阅读时间：12 分钟

---

## 一、为什么需要对齐

**问题**：预训练模型会胡说八道、有偏见、不安全。

**对齐目标**：
- ✅ 有帮助（Helpful）
- ✅ 诚实（Honest）
- ✅ 无害（Harmless）

---

## 二、RLHF：人类反馈强化学习

### 流程

```
1. 收集人类偏好数据
   问题 A → 回答 1（人类选✓）
   问题 A → 回答 2（人类选✗）

2. 训练奖励模型（Reward Model）
   输入：(问题，回答)
   输出：分数（越高越好）

3. PPO 强化学习
   用奖励模型指导策略更新
```

### 代码示例

```python
from trl import PPOTrainer, PPOConfig

config = PPOConfig(
    model_name="llama-3-8b",
    learning_rate=1e-6,
    batch_size=32,
)

trainer = PPOTrainer(
    config=config,
    model=model,
    ref_model=ref_model,  # 参考模型
    tokenizer=tokenizer,
    dataset=preference_dataset,
)

# PPO 训练
for batch in dataloader:
    query_tensors = batch["query"]
    response_tensors = trainer.generate(query_tensors)
    
    # 奖励模型打分
    rewards = reward_model(query_tensors, response_tensors)
    
    # PPO 更新
    stats = trainer.step(query_tensors, response_tensors, rewards)
```

---

## 三、DPO：直接偏好优化

### 为什么用 DPO

**RLHF 的问题**：
- ❌ 训练复杂（需要奖励模型 + PPO）
- ❌ 不稳定
- ❌ 计算量大

**DPO 的优势**：
- ✅ 直接优化，不需要奖励模型
- ✅ 稳定，易训练
- ✅ 效果相当或更好

### DPO 原理

```python
# DPO 损失函数
# 直接优化偏好数据，无需显式奖励模型

from trl import DPOTrainer

trainer = DPOTrainer(
    model=model,
    ref_model=ref_model,
    beta=0.1,  # 温度参数
    train_dataset=preference_dataset,
    ...
)

trainer.train()
```

### 数据格式

```json
[
  {
    "prompt": "如何学习 Python？",
    "chosen": "学习 Python 可以从基础语法开始...",
    "rejected": "Python 是一种蛇..."
  },
  {
    "prompt": "解释量子力学",
    "chosen": "量子力学是物理学的一个分支...",
    "rejected": "量子力学就是量子 + 力学..."
  }
]
```

---

## 四、实战：DPO 微调

### 1. 准备偏好数据

```python
from datasets import load_dataset

dataset = load_dataset("json", data_files="preference_data.json")

# 格式转换
def format_example(example):
    return {
        "prompt": example["prompt"],
        "chosen": example["chosen"],
        "rejected": example["rejected"]
    }

dataset = dataset.map(format_example)
```

### 2. 配置 DPO

```python
from trl import DPOConfig, DPOTrainer

training_args = DPOConfig(
    output_dir="./dpo-model",
    learning_rate=5e-7,
    per_device_train_batch_size=4,
    num_train_epochs=3,
    beta=0.1,  # DPO 温度参数
)

trainer = DPOTrainer(
    model=model,
    ref_model=ref_model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
)
```

### 3. 训练

```python
trainer.train()
trainer.save_model("./dpo-model")
```

---

## 五、RLHF vs DPO

| 对比项 | RLHF | DPO |
|--------|------|-----|
| 复杂度 | 高（3 阶段） | 低（1 阶段） |
| 稳定性 | 不稳定 | 稳定 |
| 计算量 | 大 | 小 |
| 效果 | 好 | 相当或更好 |
| 推荐 | ❌ | ✅ |

---

## 六、常见问题

### Q1：需要多少偏好数据？

**答**：
- 基础对齐：1000-5000 条
- 高质量对齐：10000+ 条
- 持续优化：持续收集

### Q2：可以自己标注吗？

**答**：可以！建议：
- 定义清晰的标注规范
- 多人标注 + 交叉验证
- 定期抽检质量

### Q3：DPO 的 beta 参数怎么调？

**答**：
- beta=0.1：默认值，适合大多数场景
- beta=0.2：更保守，少偏离参考模型
- beta=0.05：更激进，更多优化

---

## 下一步

- 👉 [2.5 分布式训练](2.5_分布式训练.md)
- 👉 [5.1 Agent 设计与工作流](../05_Agent 开发/5.1_Agent 设计与工作流.md)

---

*完整教程：https://github.com/chenweidu666/AI-Engineering-Docs/tree/main/examples/dpo*
