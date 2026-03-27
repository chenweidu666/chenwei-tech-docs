"""
Rotary Embedding Kernels - RoPE位置编码的Kernel实现

这个模块模拟GPU RoPE kernel的实现。
RoPE是现代大模型的标准位置编码方式。

主要功能:
- rotary_embedding_kernel: RoPE kernel
- precompute_freqs_cis: 预计算频率
- get_rope_cache: 获取RoPE缓存
"""

import torch
from typing import Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class RoPEConfig:
    """RoPE配置"""
    max_position_embeddings: int = 8192
    base: float = 10000.0
    scaling_factor: float = 1.0
    rope_type: str = "default"  # default, linear, dynamic


def precompute_freqs_cis(
    head_dim: int,
    max_seq_len: int,
    base: float = 10000.0,
    dtype: torch.dtype = torch.float32,
    device: torch.device = None,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    预计算RoPE的cos和sin缓存
    
    这是一个初始化时调用的函数，计算好的缓存在推理时重复使用。
    
    数学原理：
        对于维度i，频率为: theta_i = base^(-2i/d)
        对于位置m: cos(m * theta_i), sin(m * theta_i)
    
    Args:
        head_dim: 注意力头维度
        max_seq_len: 最大序列长度
        base: RoPE基数（默认10000）
        dtype: 输出数据类型
        device: 输出设备
    
    Returns:
        (cos_cache, sin_cache): shape都是 [max_seq_len, head_dim]
    """
    # 计算频率（inv_freq）
    # inv_freq[i] = 1 / (base^(2i/dim))
    inv_freq = 1.0 / (
        base ** (torch.arange(0, head_dim, 2, dtype=torch.float32) / head_dim)
    )
    
    # 位置索引
    t = torch.arange(max_seq_len, dtype=torch.float32)
    
    # 计算 position * frequency
    # freqs[m, i] = m * inv_freq[i]
    freqs = torch.outer(t, inv_freq)  # [max_seq_len, head_dim/2]
    
    # 扩展到完整维度（每个频率用于两个维度）
    freqs = torch.cat([freqs, freqs], dim=-1)  # [max_seq_len, head_dim]
    
    # 计算cos和sin
    cos_cache = freqs.cos().to(dtype=dtype)
    sin_cache = freqs.sin().to(dtype=dtype)
    
    if device is not None:
        cos_cache = cos_cache.to(device)
        sin_cache = sin_cache.to(device)
    
    return cos_cache, sin_cache


def rotary_embedding_kernel(
    positions: torch.Tensor,
    query: torch.Tensor,
    key: torch.Tensor,
    cos_cache: torch.Tensor,
    sin_cache: torch.Tensor,
    rotary_dim: Optional[int] = None,
    is_neox_style: bool = True,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    RoPE Kernel实现
    
    GPU Kernel实现细节（伪代码）：
    
    ```cpp
    // CUDA Kernel伪代码
    __global__ void rotary_embedding_kernel(
        float* query_out,
        float* key_out,
        const float* query,
        const float* key,
        const float* cos,
        const float* sin,
        int rotary_dim
    ) {
        int idx = blockIdx.x * blockDim.x + threadIdx.x;
        int pos = positions[idx / head_dim];
        int dim_idx = idx % head_dim;
        
        if (dim_idx < rotary_dim) {
            // 对于前rotary_dim个维度，应用旋转
            float cos_val = cos[pos * rotary_dim + dim_idx];
            float sin_val = sin[pos * rotary_dim + dim_idx];
            
            // NeoX style: 前半和后半交换
            int paired_idx = (dim_idx < rotary_dim/2) ? 
                            dim_idx + rotary_dim/2 : 
                            dim_idx - rotary_dim/2;
            float sign = (dim_idx < rotary_dim/2) ? -1.0f : 1.0f;
            
            query_out[idx] = query[idx] * cos_val + 
                            sign * query[paired_idx] * sin_val;
            key_out[idx] = key[idx] * cos_val + 
                          sign * key[paired_idx] * sin_val;
        } else {
            // 超过rotary_dim的维度直接复制
            query_out[idx] = query[idx];
            key_out[idx] = key[idx];
        }
    }
    ```
    
    Args:
        positions: 位置索引
        query: Query张量
        key: Key张量
        cos_cache: cos缓存
        sin_cache: sin缓存
        rotary_dim: 旋转维度
        is_neox_style: NeoX风格 vs GPT-J风格
    
    Returns:
        (rotated_query, rotated_key)
    """
    if rotary_dim is None:
        rotary_dim = query.shape[-1]
    
    # 获取对应位置的cos/sin
    cos = cos_cache[positions]
    sin = sin_cache[positions]
    
    # 调整shape以支持广播
    # query/key: [..., num_heads, head_dim]
    # cos/sin需要变成: [..., 1, rotary_dim]
    while cos.dim() < query.dim():
        cos = cos.unsqueeze(-2)
        sin = sin.unsqueeze(-2)
    
    # 只取rotary_dim部分的cos/sin
    if cos.shape[-1] > rotary_dim:
        cos = cos[..., :rotary_dim]
        sin = sin[..., :rotary_dim]
    
    # ========== 模拟融合RoPE Kernel ==========
    
    def apply_rotary_emb(x: torch.Tensor) -> torch.Tensor:
        """对单个张量应用RoPE"""
        x_rot = x[..., :rotary_dim]
        x_pass = x[..., rotary_dim:]
        
        if is_neox_style:
            # GPT-NeoX style
            # 将rotary_dim分成两半，交叉旋转
            half_dim = rotary_dim // 2
            x1 = x_rot[..., :half_dim]
            x2 = x_rot[..., half_dim:]
            
            # 旋转公式: 
            # out1 = x1 * cos - x2 * sin
            # out2 = x2 * cos + x1 * sin
            # NeoX变体: out = x * cos + rotate_half(x) * sin
            # 其中 rotate_half([x1, x2]) = [-x2, x1]
            rotated = torch.cat([-x2, x1], dim=-1)
            x_rotated = x_rot * cos + rotated * sin
        else:
            # GPT-J style
            # 奇偶位置配对旋转
            x1 = x_rot[..., ::2]   # 偶数位置
            x2 = x_rot[..., 1::2]  # 奇数位置
            
            cos_half = cos[..., ::2]
            sin_half = sin[..., ::2]
            
            # 2D旋转
            out1 = x1 * cos_half - x2 * sin_half
            out2 = x1 * sin_half + x2 * cos_half
            
            # 交错合并
            x_rotated = torch.stack([out1, out2], dim=-1).flatten(-2)
        
        # 拼接旋转部分和非旋转部分
        return torch.cat([x_rotated, x_pass], dim=-1)
    
    query_rotated = apply_rotary_emb(query)
    key_rotated = apply_rotary_emb(key)
    
    return query_rotated, key_rotated


class RoPECache:
    """
    RoPE缓存管理器
    
    管理cos/sin缓存，支持动态扩展。
    """
    
    def __init__(
        self,
        head_dim: int,
        max_seq_len: int = 8192,
        base: float = 10000.0,
        dtype: torch.dtype = torch.float16,
        device: Optional[torch.device] = None,
    ):
        self.head_dim = head_dim
        self.max_seq_len = max_seq_len
        self.base = base
        self.dtype = dtype
        self.device = device
        
        # 预计算缓存
        self.cos_cache, self.sin_cache = precompute_freqs_cis(
            head_dim=head_dim,
            max_seq_len=max_seq_len,
            base=base,
            dtype=dtype,
            device=device,
        )
    
    def get_cos_sin(
        self,
        seq_len: int,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """获取指定长度的cos/sin"""
        if seq_len > self.max_seq_len:
            # 动态扩展缓存
            self._extend_cache(seq_len)
        
        return self.cos_cache[:seq_len], self.sin_cache[:seq_len]
    
    def _extend_cache(self, new_max_len: int) -> None:
        """扩展缓存"""
        self.max_seq_len = new_max_len
        self.cos_cache, self.sin_cache = precompute_freqs_cis(
            head_dim=self.head_dim,
            max_seq_len=new_max_len,
            base=self.base,
            dtype=self.dtype,
            device=self.device,
        )
    
    def apply(
        self,
        positions: torch.Tensor,
        query: torch.Tensor,
        key: torch.Tensor,
        is_neox_style: bool = True,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        应用RoPE
        
        这是最常用的接口，直接传入query/key即可。
        """
        return rotary_embedding_kernel(
            positions=positions,
            query=query,
            key=key,
            cos_cache=self.cos_cache,
            sin_cache=self.sin_cache,
            rotary_dim=self.head_dim,
            is_neox_style=is_neox_style,
        )


# 全局RoPE缓存实例
_ROPE_CACHES = {}


def get_rope_cache(
    head_dim: int,
    max_seq_len: int = 8192,
    base: float = 10000.0,
    dtype: torch.dtype = torch.float16,
    device: Optional[torch.device] = None,
) -> RoPECache:
    """
    获取或创建RoPE缓存
    
    使用全局缓存避免重复计算。
    
    Args:
        head_dim: 头维度
        max_seq_len: 最大序列长度
        base: RoPE基数
        dtype: 数据类型
        device: 设备
    
    Returns:
        RoPECache实例
    """
    key = (head_dim, max_seq_len, base, dtype, device)
    
    if key not in _ROPE_CACHES:
        _ROPE_CACHES[key] = RoPECache(
            head_dim=head_dim,
            max_seq_len=max_seq_len,
            base=base,
            dtype=dtype,
            device=device,
        )
    
    return _ROPE_CACHES[key]
