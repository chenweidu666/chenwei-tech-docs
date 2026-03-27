"""
MyGPU Ops - 模拟国产GPU算子库

这是一个教学用的模拟算子库，展示国产GPU算子库的基本结构和接口设计。
在实际的国产GPU适配中，这些函数会调用真正的GPU kernel。

主要算子：
- rms_norm: RMS LayerNorm
- fused_add_rms_norm: 融合残差加法的RMSNorm
- rotary_embedding: 旋转位置编码 (RoPE)
- paged_attention_v1: 简化版PagedAttention

使用示例：
    import mygpu_ops
    
    # RMSNorm
    output = mygpu_ops.rms_norm(x, weight, eps=1e-6)
    
    # Fused Add RMSNorm
    output, residual = mygpu_ops.fused_add_rms_norm(x, residual, weight, eps=1e-6)
    
    # RoPE
    query, key = mygpu_ops.rotary_embedding(positions, query, key, cos, sin)
"""

__version__ = "0.1.0"
__author__ = "MyGPU Team"

from .core import (
    # 设备管理
    is_available,
    device_count,
    get_device_name,
    get_device_properties,
    current_device,
    set_device,
    synchronize,
    
    # 内存管理
    memory_allocated,
    memory_reserved,
    max_memory_allocated,
    empty_cache,
    
    # 核心算子
    rms_norm,
    fused_add_rms_norm,
    rotary_embedding,
    paged_attention_v1,
    
    # 统计函数
    get_kernel_stats,
    reset_kernel_stats,
)

from .kernels import (
    layernorm,
    rotary,
    attention,
)

__all__ = [
    # Version
    "__version__",
    
    # Device management
    "is_available",
    "device_count", 
    "get_device_name",
    "get_device_properties",
    "current_device",
    "set_device",
    "synchronize",
    
    # Memory management
    "memory_allocated",
    "memory_reserved",
    "max_memory_allocated",
    "empty_cache",
    
    # Core operators
    "rms_norm",
    "fused_add_rms_norm",
    "rotary_embedding",
    "paged_attention_v1",
    
    # Stats
    "get_kernel_stats",
    "reset_kernel_stats",
    
    # Kernel modules
    "layernorm",
    "rotary",
    "attention",
]
