# MyGPU Ops Demo - 国产GPU算子库与vLLM CustomOp集成演示

这是一个教学项目，展示如何：
1. 开发模拟的国产GPU算子库
2. 使用vLLM的CustomOp机制进行封装
3. 通过torch.library注册算子到PyTorch

## 项目结构

```
mygpu_ops_demo/
├── mygpu_ops/                    # 模拟算子库
│   ├── __init__.py              # 包入口
│   ├── core.py                  # 核心算子实现
│   └── kernels/                 # Kernel实现
│       ├── __init__.py
│       ├── layernorm.py         # LayerNorm kernels
│       ├── rotary.py            # RoPE kernels
│       └── attention.py         # Attention kernels
│
├── vllm_plugin/                  # vLLM CustomOp 集成
│   ├── __init__.py
│   ├── ops/                     # CustomOp 实现
│   │   ├── __init__.py
│   │   ├── base.py              # CustomOp 基类
│   │   ├── rms_norm.py          # RMSNorm CustomOp
│   │   ├── rotary_embedding.py  # RoPE CustomOp
│   │   └── attention.py         # Attention CustomOp
│   └── register.py              # torch.library 注册
│
├── examples/                     # 示例脚本
│   ├── test_ops.py              # 算子正确性测试
│   ├── benchmark.py             # 性能基准测试
│   └── integration_demo.py      # 完整集成演示
│
├── setup.py                      # 安装脚本
├── pyproject.toml               # 项目配置
└── README.md                    # 本文件
```

## 快速开始

### 安装

```bash
cd mygpu_ops_demo
pip install -e .
```

### 运行测试

```bash
# 算子正确性测试
python examples/test_ops.py

# 性能基准测试
python examples/benchmark.py

# 完整集成演示
python examples/integration_demo.py
```

## 核心概念

### 1. CustomOp 机制

CustomOp是vLLM用于支持自定义硬件的核心机制。每个CustomOp需要实现两个方法：

```python
class MyCustomOp(CustomOp):
    def forward_native(self, *args):
        """PyTorch原生实现 - 作为fallback"""
        pass
    
    def forward_oot(self, *args):
        """Out-of-Tree实现 - 调用自研算子库"""
        import mygpu_ops
        return mygpu_ops.my_kernel(*args)
```

### 2. 调用流程

```
用户调用 op(x, weight)
        ↓
检查 is_oot_supported()
        ↓
    ┌───┴───┐
    │       │
支持OOT  不支持
    ↓       ↓
forward_oot  forward_native
    ↓       ↓
mygpu_ops   PyTorch原生
```

### 3. torch.library 注册

通过torch.library可以将算子注册到PyTorch的Dispatcher系统：

```python
# 定义算子签名
mygpu_lib.define("rms_norm(Tensor x, Tensor weight, float eps) -> Tensor")

# 为不同设备实现
@torch.library.impl(mygpu_lib, "rms_norm", "CPU")
def rms_norm_cpu(x, weight, eps):
    # CPU实现
    pass

@torch.library.impl(mygpu_lib, "rms_norm", "CUDA")
def rms_norm_cuda(x, weight, eps):
    # CUDA实现
    pass

# 调用
output = torch.ops.mygpu.rms_norm(x, weight, 1e-6)
```

## 包含的算子

| 算子 | 说明 | 文件 |
|------|------|------|
| `rms_norm` | RMS LayerNorm | `mygpu_ops/core.py` |
| `fused_add_rms_norm` | 融合残差+RMSNorm | `mygpu_ops/core.py` |
| `rotary_embedding` | 旋转位置编码(RoPE) | `mygpu_ops/core.py` |
| `paged_attention_v1` | PagedAttention | `mygpu_ops/core.py` |

## 使用示例

### 基本用法

```python
from vllm_plugin.ops import MyGPURMSNorm

# 创建算子
rms_norm = MyGPURMSNorm(hidden_size=4096, eps=1e-6)

# 准备输入
x = torch.randn(2, 128, 4096)
weight = torch.randn(4096)

# 调用（自动选择实现）
output = rms_norm(x, weight)

# 显式调用不同实现
output_native = rms_norm.forward_native(x, weight)
output_oot = rms_norm.forward_oot(x, weight)

# 验证正确性
result = rms_norm.debug_compare(x, weight)
print(f"结果一致: {result['all_match_1e-5']}")
```

### 通过torch.ops调用

```python
from vllm_plugin.register import register_all_ops

# 注册算子
register_all_ops()

# 通过torch.ops调用
output = torch.ops.mygpu.rms_norm(x, weight, 1e-6)
```

### 集成到模型

```python
import torch.nn as nn
from vllm_plugin.ops import MyGPURMSNorm

class RMSNormLayer(nn.Module):
    def __init__(self, hidden_size, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.op = MyGPURMSNorm(hidden_size, eps)
    
    def forward(self, x):
        return self.op(x, self.weight)
```

## 面试要点

### 1. forward_native vs forward_oot

- **forward_native**: PyTorch原生实现，用于fallback和正确性验证
- **forward_oot**: Out-of-Tree实现，调用优化的GPU kernel

### 2. 为什么需要CustomOp？

- 支持自定义硬件（国产GPU）
- 可以使用高度优化的kernel
- 优雅的降级机制

### 3. torch.library的作用

- 将算子注册到PyTorch Dispatcher
- 支持通过torch.ops调用
- 支持torch.compile优化
- 支持多设备分发

### 4. PagedAttention原理

- KV Cache分页管理，类似OS虚拟内存
- 避免显存碎片化
- 支持动态序列长度
- 是vLLM高效推理的核心

## 实际适配步骤

1. **实现Platform类**: 定义设备属性和检测接口
2. **包装算子库**: 通过CustomOp的forward_oot调用
3. **注册到PyTorch**: 使用torch.library
4. **性能优化**: Profile -> 优化 -> Benchmark

## 学习资源

- [vLLM官方文档](https://docs.vllm.ai)
- [PyTorch自定义算子](https://pytorch.org/docs/stable/cpp_extension.html)
- [torch.library文档](https://pytorch.org/docs/stable/library.html)

## 许可证

Apache 2.0
