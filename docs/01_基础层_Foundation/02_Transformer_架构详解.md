# 1.2 Transformer 架构详解

> 📅 最后更新：2026-03-26  
> ⏱️ 阅读时间：15 分钟

---

## 一、Transformer 核心思想

**一句话总结**：用**自注意力机制**替代 RNN，实现并行计算。

### RNN vs Transformer

```
RNN（串行）：
输入 1 → [RNN] → 输出 1
            ↓
输入 2 → [RNN] → 输出 2
            ↓
输入 3 → [RNN] → 输出 3

Transformer（并行）：
输入 [1,2,3] → [Self-Attention] → 输出 [1,2,3]
```

**优势**：
- ✅ 并行计算，训练快 10 倍
- ✅ 长距离依赖，不会遗忘
- ✅ 架构简洁，易于扩展

---

## 二、自注意力机制（Self-Attention）

### 核心公式

```python
Attention(Q, K, V) = softmax(QK^T / √d) × V
```

**通俗解释**：
- **Q（Query）**：我想找什么
- **K（Key）**：你有什么
- **V（Value）**：实际内容

### 示例：翻译 "I love AI"

```
单词：I    love   AI
       │    │     │
       ↓    ↓     ↓
Q:    [查询] [查询]  [查询]
K:    [钥匙] [钥匙]  [钥匙]
V:    [内容] [内容]  [内容]

计算注意力：
"I" 关注 → "I"(0.1) + "love"(0.6) + "AI"(0.3)
"love" 关注 → "I"(0.2) + "love"(0.5) + "AI"(0.3)
"AI" 关注 → "I"(0.1) + "love"(0.4) + "AI"(0.5)
```

---

## 三、多头注意力（Multi-Head Attention）

### 为什么需要多头？

**类比**：一个人看问题 vs 多个人从不同角度分析

```python
# 单头注意力
attention1 = Attention(Q, K, V)

# 多头注意力（8 个头）
head1 = Attention(Q1, K1, V1)  # 关注语法
head2 = Attention(Q2, K2, V2)  # 关注语义
head3 = Attention(Q3, K3, V3)  # 关注位置
...
output = Concat(head1, head2, ...) × W
```

### 实际效果

```
句子："The animal didn't cross the street because it was too tired"

头 1（语法）：it → animal（主谓一致）
头 2（语义）：it → animal（指代关系）
头 3（位置）：it → didn't（否定范围）
```

---

## 四、位置编码（Positional Encoding）

### 问题

Transformer 没有 RNN 的顺序概念，需要显式添加位置信息。

### 解决方案

```python
import numpy as np

def positional_encoding(seq_len, d_model):
    """生成位置编码"""
    pe = np.zeros((seq_len, d_model))
    
    for pos in range(seq_len):
        for i in range(0, d_model, 2):
            # 偶数维度用 sin
            pe[pos, i] = np.sin(pos / (10000 ** (2*i/d_model)))
            # 奇数维度用 cos
            pe[pos, i+1] = np.cos(pos / (10000 ** (2*i/d_model)))
    
    return pe

# 使用
pe = positional_encoding(seq_len=100, d_model=512)
embedding = word_embedding + pe
```

---

## 五、完整 Transformer 架构

### 编码器（Encoder）

```
输入 → 嵌入层 → 位置编码 → [Multi-Head Attention]
                              ↓
                         [Add & Norm]
                              ↓
                      [Feed Forward]
                              ↓
                         [Add & Norm]
                              ↓
                          输出
```

### 解码器（Decoder）

```
输出 → 嵌入层 → 位置编码 → [Masked Attention]
                              ↓
                         [Add & Norm]
                              ↓
                    [Encoder-Decoder Attention]
                              ↓
                         [Add & Norm]
                              ↓
                      [Feed Forward]
                              ↓
                         [Add & Norm]
                              ↓
                      [Softmax] → 概率分布
```

---

## 六、动手实现：最小 Transformer

### PyTorch 实现（50 行核心代码）

```python
import torch
import torch.nn as nn

class SelfAttention(nn.Module):
    def __init__(self, embed_size, heads):
        super().__init__()
        self.embed_size = embed_size
        self.heads = heads
        self.head_dim = embed_size // heads
        
        self.query = nn.Linear(embed_size, embed_size)
        self.key = nn.Linear(embed_size, embed_size)
        self.value = nn.Linear(embed_size, embed_size)
        self.fc_out = nn.Linear(embed_size, embed_size)
        
    def forward(self, Q, K, V, mask=None):
        N = Q.shape[0]
        Q_len, K_len, V_len = Q.shape[1], K.shape[1], V.shape[1]
        
        # 拆分多头
        Q = self.query(Q).reshape(N, Q_len, self.heads, self.head_dim)
        K = self.key(K).reshape(N, K_len, self.heads, self.head_dim)
        V = self.value(V).reshape(N, V_len, self.heads, self.head_dim)
        
        # 计算注意力
        energy = torch.einsum("nqhd,nkhd->nhqk", [Q, K])
        if mask is not None:
            energy = energy.masked_fill(mask == 0, float("-1e20"))
        
        attention = torch.softmax(energy / (self.head_dim ** 0.5), dim=3)
        out = torch.einsum("nhql,nlhd->nqhd", [attention, V])
        
        # 合并多头
        out = out.reshape(N, Q_len, self.heads * self.head_dim)
        return self.fc_out(out)

# 测试
model = SelfAttention(embed_size=512, heads=8)
Q = K = V = torch.randn(32, 100, 512)  # batch=32, seq=100
output = model(Q, K, V)
print(output.shape)  # torch.Size([32, 100, 512])
```

---

## 七、关键优化技巧

### 1. Layer Normalization

```python
# Transformer 使用 LayerNorm 而非 BatchNorm
self.norm1 = nn.LayerNorm(embed_size)
self.norm2 = nn.LayerNorm(embed_size)

# 位置：Attention 前后各一个
x = self.norm1(x + Attention(x))
x = self.norm2(x + FFN(x))
```

### 2. Residual Connection（残差连接）

```python
# 防止梯度消失
output = x + SubLayer(x)  # 关键！
```

### 3. Label Smoothing

```python
# 防止过拟合
criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
```

---

## 八、常见面试问题

### Q1：为什么除以 √d？

**答**：防止点积过大导致 softmax 梯度消失。

### Q2：Masked Attention 的作用？

**答**：解码时防止看到未来位置（训练时）或已生成位置（推理时）。

```python
# 生成 mask
mask = torch.tril(torch.ones(seq_len, seq_len))
# [[1, 0, 0],
#  [1, 1, 0],
#  [1, 1, 1]]
```

### Q3：为什么用 LayerNorm 不用 BatchNorm？

**答**：
- LayerNorm 对序列长度不敏感
- NLP 任务 batch 大小不稳定
- LayerNorm 在每个样本上独立计算

---

## 九、实战：用 HuggingFace 训练 Transformer

```python
from transformers import Trainer, TrainingArguments

# 定义训练参数
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    learning_rate=2e-5,
    warmup_steps=500,
    logging_steps=100,
)

# 创建 Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
)

# 开始训练
trainer.train()
```

---

## 下一步

- 👉 [1.3 主流模型选型 2026](1.3_主流模型选型 2026.md)
- 👉 [2.2 SFT 监督微调](../02_训练与微调/2.2_SFT 监督微调.md)
- 👉 [5.1 Agent 设计与工作流](../05_Agent 开发/5.1_Agent 设计与工作流.md)

---

*代码示例 GitHub：https://github.com/chenweidu666/AI-Engineering-Docs/tree/main/examples/transformer*
