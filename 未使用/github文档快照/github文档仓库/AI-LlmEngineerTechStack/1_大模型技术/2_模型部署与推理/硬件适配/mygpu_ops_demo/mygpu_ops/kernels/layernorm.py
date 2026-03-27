"""
LayerNorm Kernels - 归一化算子的Kernel实现

这个模块模拟GPU LayerNorm kernel的实现细节。
在实际场景中，这些会是高度优化的CUDA/自研GPU kernel代码。

主要算子:
- rms_norm_kernel: RMS LayerNorm kernel
- fused_add_rms_norm_kernel: 融合残差加法的RMSNorm kernel
- layer_norm_kernel: 标准LayerNorm kernel
"""

import torch
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class KernelConfig:
    """Kernel配置参数"""
    block_size: int = 256      # 线程块大小
    num_warps: int = 8         # Warp数量
    use_fast_math: bool = True # 是否使用快速数学函数


# 默认配置
DEFAULT_CONFIG = KernelConfig()


def rms_norm_kernel(
    x: torch.Tensor,
    weight: torch.Tensor,
    eps: float = 1e-6,
    config: Optional[KernelConfig] = None,
) -> torch.Tensor:
    """
    RMS LayerNorm Kernel
    
    这个函数模拟GPU kernel的执行过程。
    
    GPU Kernel实现细节（伪代码）：
    
    ```cpp
    // CUDA Kernel伪代码
    __global__ void rms_norm_kernel(
        float* output,
        const float* input,
        const float* weight,
        int hidden_size,
        float eps
    ) {
        // 1. 每个block处理一行
        int row = blockIdx.x;
        
        // 2. 使用shared memory计算方差
        __shared__ float variance;
        
        // 3. Block内所有线程协作计算sum(x^2)
        float local_sum = 0.0f;
        for (int i = threadIdx.x; i < hidden_size; i += blockDim.x) {
            float val = input[row * hidden_size + i];
            local_sum += val * val;
        }
        
        // 4. Block内reduce求和
        variance = blockReduceSum(local_sum) / hidden_size;
        __syncthreads();
        
        // 5. 计算rsqrt并写回
        float scale = rsqrtf(variance + eps);
        for (int i = threadIdx.x; i < hidden_size; i += blockDim.x) {
            output[row * hidden_size + i] = 
                input[row * hidden_size + i] * scale * weight[i];
        }
    }
    ```
    
    Args:
        x: 输入张量, shape [..., hidden_size]
        weight: 权重, shape [hidden_size]
        eps: 防止除零
        config: Kernel配置
    
    Returns:
        归一化结果
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    # 保存原始shape
    original_shape = x.shape
    hidden_size = x.shape[-1]
    
    # 展平为2D: [num_rows, hidden_size]
    x_2d = x.view(-1, hidden_size)
    num_rows = x_2d.shape[0]
    
    # ========== 模拟Kernel执行 ==========
    # 实际GPU上每行由一个block处理
    
    # Step 1: 计算每行的方差 (模拟block reduce)
    variance = x_2d.pow(2).mean(dim=-1, keepdim=True)  # [num_rows, 1]
    
    # Step 2: rsqrt (模拟element-wise操作)
    rsqrt_var = torch.rsqrt(variance + eps)
    
    # Step 3: 归一化 + 乘权重 (模拟fused操作)
    output = x_2d * rsqrt_var * weight
    
    # 恢复原始shape
    return output.view(original_shape)


def fused_add_rms_norm_kernel(
    x: torch.Tensor,
    residual: torch.Tensor,
    weight: torch.Tensor,
    eps: float = 1e-6,
    config: Optional[KernelConfig] = None,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    融合残差加法的 RMS LayerNorm Kernel
    
    优化原理：
    - 原本需要2次kernel launch (add + norm)
    - 融合后只需1次kernel launch
    - 减少显存带宽压力（数据只需读写一次）
    
    性能对比：
    - 非融合版本: 读x + 读residual + 写sum + 读sum + 写output = 5次显存访问
    - 融合版本: 读x + 读residual + 写output + 写residual = 4次显存访问
    - 理论提升: 20%
    
    Args:
        x: 输入张量
        residual: 残差张量
        weight: 权重
        eps: 防止除零
        config: Kernel配置
    
    Returns:
        (output, new_residual)
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    # 保存原始shape
    original_shape = x.shape
    hidden_size = x.shape[-1]
    
    # 展平为2D
    x_2d = x.view(-1, hidden_size)
    residual_2d = residual.view(-1, hidden_size)
    
    # ========== 模拟融合Kernel ==========
    # 在实际GPU上，这些操作在一个kernel中完成
    
    # Step 1: 残差加法
    hidden = x_2d + residual_2d
    
    # Step 2: 保存新的残差 (用于下一层)
    new_residual = hidden.clone()
    
    # Step 3: RMSNorm
    variance = hidden.pow(2).mean(dim=-1, keepdim=True)
    hidden_normed = hidden * torch.rsqrt(variance + eps)
    output = hidden_normed * weight
    
    return output.view(original_shape), new_residual.view(original_shape)


def layer_norm_kernel(
    x: torch.Tensor,
    weight: torch.Tensor,
    bias: Optional[torch.Tensor] = None,
    eps: float = 1e-5,
    config: Optional[KernelConfig] = None,
) -> torch.Tensor:
    """
    标准 LayerNorm Kernel
    
    与RMSNorm的区别：
    - LayerNorm: (x - mean) / sqrt(var + eps) * weight + bias
    - RMSNorm: x / sqrt(mean(x^2) + eps) * weight
    
    RMSNorm省略了减均值和bias，计算更快。
    
    Args:
        x: 输入张量
        weight: 缩放权重
        bias: 偏置（可选）
        eps: 防止除零
        config: Kernel配置
    
    Returns:
        归一化结果
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    # 保存原始shape
    original_shape = x.shape
    hidden_size = x.shape[-1]
    
    # 展平
    x_2d = x.view(-1, hidden_size)
    
    # ========== 模拟Kernel ==========
    
    # Step 1: 计算均值
    mean = x_2d.mean(dim=-1, keepdim=True)
    
    # Step 2: 计算方差
    var = ((x_2d - mean) ** 2).mean(dim=-1, keepdim=True)
    
    # Step 3: 归一化
    x_normed = (x_2d - mean) * torch.rsqrt(var + eps)
    
    # Step 4: 缩放 + 偏置
    output = x_normed * weight
    if bias is not None:
        output = output + bias
    
    return output.view(original_shape)


# ============================================================================
# Kernel选择器 - 根据输入特征选择最优kernel配置
# ============================================================================

def select_kernel_config(hidden_size: int, dtype: torch.dtype) -> KernelConfig:
    """
    根据输入特征选择最优kernel配置
    
    这在实际GPU适配中很重要：
    - 不同hidden_size需要不同的block_size
    - 不同数据类型需要不同的优化策略
    
    Args:
        hidden_size: 隐藏层大小
        dtype: 数据类型
    
    Returns:
        最优的kernel配置
    """
    # 根据hidden_size选择block_size
    if hidden_size <= 256:
        block_size = 128
        num_warps = 4
    elif hidden_size <= 1024:
        block_size = 256
        num_warps = 8
    elif hidden_size <= 4096:
        block_size = 512
        num_warps = 16
    else:
        block_size = 1024
        num_warps = 32
    
    # FP16/BF16可以使用更激进的优化
    use_fast_math = dtype in [torch.float16, torch.bfloat16]
    
    return KernelConfig(
        block_size=block_size,
        num_warps=num_warps,
        use_fast_math=use_fast_math,
    )
