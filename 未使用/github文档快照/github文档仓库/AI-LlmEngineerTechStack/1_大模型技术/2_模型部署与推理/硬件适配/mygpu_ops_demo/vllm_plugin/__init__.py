"""
vLLM Plugin for MyGPU - vLLM自定义算子集成层

这个模块展示如何将自研算子库集成到vLLM的CustomOp系统中。

核心概念：
1. CustomOp: vLLM的自定义算子基类
2. forward_native: PyTorch原生实现（fallback）
3. forward_oot: Out-of-Tree实现（调用自研算子库）

使用示例：
    from vllm_plugin.ops import MyGPURMSNorm, MyGPURotaryEmbedding
    
    # 创建算子
    rms_norm = MyGPURMSNorm(hidden_size=4096, eps=1e-6)
    
    # 调用（自动选择forward_native或forward_oot）
    output = rms_norm(x, weight)
"""

__version__ = "0.1.0"

from .ops import (
    MyGPURMSNorm,
    MyGPUFusedAddRMSNorm,
    MyGPURotaryEmbedding,
    MyGPUPagedAttention,
)

__all__ = [
    "MyGPURMSNorm",
    "MyGPUFusedAddRMSNorm",
    "MyGPURotaryEmbedding",
    "MyGPUPagedAttention",
]
