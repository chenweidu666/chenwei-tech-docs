# 2.5 分布式训练

> 📅 最后更新：2026-03-26  
> ⏱️ 阅读时间：10 分钟

---

## 一、为什么需要分布式

**单卡限制**：
- ❌ 显存不够（70B 需要 140GB+）
- ❌ 训练太慢（单卡训练 7B 需要数月）

**分布式优势**：
- ✅ 多卡并行，显存叠加
- ✅ 训练加速，线性扩展

---

## 二、并行策略

### 1. 数据并行（Data Parallel）

```
GPU0: 数据 batch 1 → 模型 → 梯度
GPU1: 数据 batch 2 → 模型 → 梯度
GPU2: 数据 batch 3 → 模型 → 梯度
       ↓
    梯度平均 → 更新模型
```

**适用**：小模型（<7B）

### 2. 张量并行（Tensor Parallel）

```
单卡显存不够时，把一层拆到多卡：

Layer Norm
   ↓
[Q 投影] → GPU0
[K 投影] → GPU1
[V 投影] → GPU2
[O 投影] → GPU3
   ↓
合并结果
```

**适用**：大模型推理

### 3. 流水线并行（Pipeline Parallel）

```
GPU0: Layer 1-8
GPU1: Layer 9-16
GPU2: Layer 17-24
GPU3: Layer 25-32
```

**适用**：超大模型训练

### 4. ZeRO 优化（DeepSpeed）

```
ZeRO-1: 优化器状态分片
ZeRO-2: 优化器 + 梯度分片
ZeRO-3: 优化器 + 梯度 + 参数分片
```

**显存节省**：
- 70B 模型，ZeRO-3：8×A100 80G 可训练

---

## 三、实战：DeepSpeed 训练

### 1. 安装

```bash
pip install deepspeed
```

### 2. 配置文件

```json
// ds_config.json
{
  "train_batch_size": 64,
  "gradient_accumulation_steps": 4,
  
  "zero_optimization": {
    "stage": 3,
    "offload_optimizer": {
      "device": "cpu",
      "pin_memory": true
    },
    "offload_param": {
      "device": "cpu",
      "pin_memory": true
    }
  },
  
  "fp16": {
    "enabled": true,
    "loss_scale": 0
  },
  
  "optimizer": {
    "type": "AdamW",
    "params": {
      "lr": 2e-5,
      "betas": [0.9, 0.999],
      "eps": 1e-8
    }
  }
}
```

### 3. 启动训练

```bash
# 单机 8 卡
deepspeed --num_gpus=8 \
    train.py \
    --deepspeed ds_config.json

# 多机（4 台×8 卡）
deepspeed --hostfile=hosts.txt \
    --num_nodes=4 \
    --num_gpus=8 \
    train.py \
    --deepspeed ds_config.json
```

### 4. 代码集成

```python
from transformers import Trainer, TrainingArguments

training_args = TrainingArguments(
    output_dir="./model",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    deepspeed="ds_config.json",  # 关键！
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
)

trainer.train()
```

---

## 四、FSDP：PyTorch 原生方案

### 配置 FSDP

```python
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP

model = FSDP(
    model,
    sharding_strategy=ShardingStrategy.FULL_SHARD,  # ZeRO-3
    cpu_offload=CPUOffload(offload_params=True),
    mixed_precision=MixedPrecision(
        param_dtype=torch.float16,
        reduce_dtype=torch.float16,
    ),
)
```

### 启动

```bash
# torchrun 启动
torchrun --nproc_per_node=8 \
    train.py
```

---

## 五、训练监控

### 1. WandB 集成

```python
import wandb

wandb.init(project="llama3-finetune")

# Trainer 自动集成
training_args = TrainingArguments(
    ...
    report_to="wandb",
    logging_steps=50,
)
```

### 2. 关键指标

```python
# 监控内容
- Loss 曲线（是否下降）
- 学习率（是否按计划）
- 显存使用（是否溢出）
- 梯度范数（是否爆炸）
- 吞吐量（tokens/s）
```

---

## 六、常见问题

### Q1：训练 Loss 不下降？

**可能原因**：
- 学习率太高/太低
- 数据有问题
- 模型加载错误

**解决**：
- 调学习率（2e-5 → 1e-5）
- 检查数据质量
- 重新加载模型

### Q2：OOM（显存溢出）？

**解决**：
- 减小 batch size
- 增加 gradient accumulation
- 用 ZeRO-3 + CPU Offload
- 混合精度训练（FP16）

### Q3：多机训练慢？

**优化**：
- 检查网络带宽（需要 100Gbps+）
- 用 InfiniBand 而非以太网
- 增加 gradient accumulation
- 减少通信频率

---

## 下一步

- 👉 [第三章：部署与推理](../03_部署与推理/3.1_KVCache 与推理加速.md)
- 👉 [6.2 Docker 容器化](../06_工程化/6.2_Docker.md)

---

*配置模板：https://github.com/chenweidu666/AI-Engineering-Docs/tree/main/examples/deepspeed*
