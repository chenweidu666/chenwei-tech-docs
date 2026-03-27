"""
MyGPU Ops Core - 核心算子实现

这个模块模拟国产GPU算子库的核心接口。
在实际场景中，这些函数会通过 C++ binding 调用 GPU kernel。
"""

import torch
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
import time
import functools

# ============================================================================
# 设备管理 API（模拟国产GPU Runtime）
# ============================================================================

@dataclass
class DeviceProperties:
    """设备属性"""
    name: str
    total_memory: int  # bytes
    compute_capability: Tuple[int, int]
    multi_processor_count: int


# 模拟设备状态
_DEVICE_STATE = {
    "current_device": 0,
    "device_count": 1,  # 模拟单卡
    "memory_allocated": 0,
    "memory_reserved": 0,
    "max_memory_allocated": 0,
}


def is_available() -> bool:
    """检查MyGPU是否可用"""
    # 在模拟环境中，始终返回True
    # 实际场景：检查驱动、runtime是否正常
    return True


def device_count() -> int:
    """获取设备数量"""
    return _DEVICE_STATE["device_count"]


def get_device_name(device_id: int = 0) -> str:
    """获取设备名称"""
    return f"MyGPU-V100-Simulator-{device_id}"


def get_device_properties(device_id: int = 0) -> DeviceProperties:
    """获取设备属性"""
    return DeviceProperties(
        name=get_device_name(device_id),
        total_memory=24 * 1024 * 1024 * 1024,  # 24GB
        compute_capability=(8, 0),
        multi_processor_count=80,
    )


def current_device() -> int:
    """获取当前设备ID"""
    return _DEVICE_STATE["current_device"]


def set_device(device_id: int) -> None:
    """设置当前设备"""
    if device_id >= _DEVICE_STATE["device_count"]:
        raise RuntimeError(f"Invalid device id: {device_id}")
    _DEVICE_STATE["current_device"] = device_id


def synchronize(device_id: Optional[int] = None) -> None:
    """同步设备（模拟）"""
    # 在实际GPU中，这会等待所有kernel执行完成
    pass


# ============================================================================
# 内存管理 API
# ============================================================================

def memory_allocated(device_id: int = 0) -> int:
    """获取已分配内存（字节）"""
    return _DEVICE_STATE["memory_allocated"]


def memory_reserved(device_id: int = 0) -> int:
    """获取已预留内存（字节）"""
    return _DEVICE_STATE["memory_reserved"]


def max_memory_allocated(device_id: int = 0) -> int:
    """获取峰值内存使用（字节）"""
    return _DEVICE_STATE["max_memory_allocated"]


def empty_cache() -> None:
    """清空缓存"""
    _DEVICE_STATE["memory_reserved"] = _DEVICE_STATE["memory_allocated"]


def _update_memory_stats(tensor: torch.Tensor) -> None:
    """更新内存统计（内部使用）"""
    size = tensor.numel() * tensor.element_size()
    _DEVICE_STATE["memory_allocated"] += size
    _DEVICE_STATE["max_memory_allocated"] = max(
        _DEVICE_STATE["max_memory_allocated"],
        _DEVICE_STATE["memory_allocated"]
    )
    _DEVICE_STATE["memory_reserved"] = max(
        _DEVICE_STATE["memory_reserved"],
        _DEVICE_STATE["memory_allocated"]
    )


# ============================================================================
# 性能监控装饰器
# ============================================================================

def kernel_timer(kernel_name: str):
    """Kernel计时装饰器 - 用于性能分析"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 记录开始时间
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            start = time.perf_counter()
            
            # 执行kernel
            result = func(*args, **kwargs)
            
            # 记录结束时间
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            end = time.perf_counter()
            
            # 记录到全局统计（可选）
            elapsed_ms = (end - start) * 1000
            if hasattr(wrapper, '_stats'):
                wrapper._stats['calls'] += 1
                wrapper._stats['total_time_ms'] += elapsed_ms
            else:
                wrapper._stats = {'calls': 1, 'total_time_ms': elapsed_ms}
            
            return result
        
        wrapper._stats = {'calls': 0, 'total_time_ms': 0.0}
        wrapper.kernel_name = kernel_name
        return wrapper
    return decorator


# ============================================================================
# 核心算子实现
# ============================================================================

@kernel_timer("rms_norm")
def rms_norm(
    x: torch.Tensor,
    weight: torch.Tensor,
    eps: float = 1e-6,
) -> torch.Tensor:
    """
    RMS LayerNorm 算子
    
    这是大模型中最常用的归一化算子，Llama/Qwen 等模型都使用它。
    
    数学公式：
        RMSNorm(x) = x / sqrt(mean(x^2) + eps) * weight
    
    Args:
        x: 输入张量, shape [..., hidden_size]
        weight: 归一化权重, shape [hidden_size]
        eps: 防止除零的小常数
    
    Returns:
        归一化后的张量, shape [..., hidden_size]
    
    Note:
        在真实的国产GPU实现中，这个函数会：
        1. 将数据从Python层传递到C++ binding
        2. C++ binding调用GPU kernel
        3. GPU kernel在显存中完成计算
        4. 返回结果张量
        
        这里我们用PyTorch实现来模拟kernel的行为。
    """
    # ========== 模拟 Kernel 执行 ==========
    # 实际场景：mygpu_runtime.launch_kernel("rms_norm", x, weight, eps)
    
    # Step 1: 计算方差 (在GPU上是一个reduction操作)
    variance = x.pow(2).mean(dim=-1, keepdim=True)
    
    # Step 2: 计算 rsqrt (在GPU上是一个element-wise操作)
    x_normed = x * torch.rsqrt(variance + eps)
    
    # Step 3: 乘以权重 (在GPU上是一个element-wise操作)
    output = x_normed * weight
    
    return output


@kernel_timer("fused_add_rms_norm")
def fused_add_rms_norm(
    x: torch.Tensor,
    residual: torch.Tensor,
    weight: torch.Tensor,
    eps: float = 1e-6,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    融合残差加法的 RMS LayerNorm
    
    这是一个优化版本，将残差加法和RMSNorm融合成一个kernel，
    减少显存访问次数，提升性能。
    
    数学公式：
        hidden = x + residual
        output = RMSNorm(hidden) * weight
    
    Args:
        x: 输入张量, shape [..., hidden_size]
        residual: 残差张量, shape [..., hidden_size]
        weight: 归一化权重, shape [hidden_size]
        eps: 防止除零的小常数
    
    Returns:
        (output, new_residual): 归一化输出和更新后的残差
    
    Note:
        融合kernel的优势：
        - 原本需要2次显存读写（add + norm），现在只需1次
        - 减少kernel launch开销
        - 在大batch下性能提升可达 20-30%
    """
    # ========== 模拟融合 Kernel ==========
    # 实际场景：单个kernel完成 add + norm
    
    # Step 1: 残差加法 (in-place更高效，但这里为了清晰分开写)
    hidden = x + residual
    new_residual = hidden  # 保存用于下一层
    
    # Step 2: RMSNorm
    variance = hidden.pow(2).mean(dim=-1, keepdim=True)
    hidden_normed = hidden * torch.rsqrt(variance + eps)
    output = hidden_normed * weight
    
    return output, new_residual


@kernel_timer("rotary_embedding")
def rotary_embedding(
    positions: torch.Tensor,
    query: torch.Tensor,
    key: torch.Tensor,
    cos_cache: torch.Tensor,
    sin_cache: torch.Tensor,
    rotary_dim: Optional[int] = None,
    is_neox_style: bool = True,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    旋转位置编码 (Rotary Position Embedding, RoPE)
    
    RoPE是现代大模型的标准位置编码方式，Llama/Qwen等都使用它。
    它通过旋转操作将位置信息编码到query和key中。
    
    数学原理：
        对于位置m的向量x，RoPE应用旋转矩阵R(m)：
        RoPE(x, m) = R(m) @ x
        
        其中R(m)是一个块对角矩阵，每个2x2块是：
        [cos(m*theta), -sin(m*theta)]
        [sin(m*theta),  cos(m*theta)]
    
    Args:
        positions: 位置索引, shape [seq_len] 或 [batch, seq_len]
        query: Query张量, shape [batch, seq_len, num_heads, head_dim]
        key: Key张量, shape [batch, seq_len, num_kv_heads, head_dim]
        cos_cache: 预计算的cos值, shape [max_seq_len, rotary_dim]
        sin_cache: 预计算的sin值, shape [max_seq_len, rotary_dim]
        rotary_dim: 应用旋转的维度数，默认为head_dim
        is_neox_style: 是否使用GPT-NeoX风格（交错 vs 分半）
    
    Returns:
        (rotated_query, rotated_key): 应用RoPE后的query和key
    """
    if rotary_dim is None:
        rotary_dim = query.shape[-1]
    
    # 获取cos/sin值
    cos = cos_cache[positions]  # [seq_len, rotary_dim]
    sin = sin_cache[positions]
    
    # 扩展维度以匹配query/key
    # query/key: [batch, seq_len, num_heads, head_dim]
    # cos/sin需要: [1, seq_len, 1, rotary_dim]
    if positions.dim() == 1 and query.dim() == 4:
        cos = cos.unsqueeze(0).unsqueeze(2)  # [1, seq_len, 1, rotary_dim]
        sin = sin.unsqueeze(0).unsqueeze(2)
    elif positions.dim() == 1 and query.dim() == 3:
        cos = cos.unsqueeze(1)  # [seq_len, 1, rotary_dim]
        sin = sin.unsqueeze(1)
    
    # ========== 模拟融合 RoPE Kernel ==========
    def apply_rotary(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
        """应用旋转变换"""
        x_rot = x[..., :rotary_dim]
        x_pass = x[..., rotary_dim:]
        
        if is_neox_style:
            # GPT-NeoX style: 前半和后半交换
            x1 = x_rot[..., :rotary_dim // 2]
            x2 = x_rot[..., rotary_dim // 2:]
            
            # 旋转
            rotated = torch.cat([-x2, x1], dim=-1)
            x_rotated = x_rot * cos + rotated * sin
        else:
            # GPT-J style: 奇偶位置交换
            x1 = x_rot[..., ::2]
            x2 = x_rot[..., 1::2]
            
            cos_squeezed = cos[..., ::2]
            sin_squeezed = sin[..., ::2]
            
            x_rotated = torch.stack([
                x1 * cos_squeezed - x2 * sin_squeezed,
                x1 * sin_squeezed + x2 * cos_squeezed,
            ], dim=-1).flatten(-2)
        
        return torch.cat([x_rotated, x_pass], dim=-1)
    
    query_rotated = apply_rotary(query, cos, sin)
    key_rotated = apply_rotary(key, cos, sin)
    
    return query_rotated, key_rotated


@kernel_timer("paged_attention_v1")
def paged_attention_v1(
    query: torch.Tensor,
    key_cache: torch.Tensor,
    value_cache: torch.Tensor,
    block_tables: torch.Tensor,
    seq_lens: torch.Tensor,
    scale: float,
    block_size: int = 16,
) -> torch.Tensor:
    """
    Paged Attention V1 - vLLM的核心算子
    
    PagedAttention是vLLM的核心创新，它将KV Cache分页管理，
    类似操作系统的虚拟内存机制，大大提高了显存利用率。
    
    核心思想：
        1. 将KV Cache分成固定大小的block（通常16或32 tokens）
        2. 每个sequence有一个block table，记录其KV存储在哪些物理block中
        3. Attention计算时，根据block table找到对应的KV数据
    
    Args:
        query: Query张量, shape [num_seqs, num_heads, head_dim]
        key_cache: Key缓存, shape [num_blocks, block_size, num_kv_heads, head_dim]
        value_cache: Value缓存, shape [num_blocks, block_size, num_kv_heads, head_dim]
        block_tables: Block映射表, shape [num_seqs, max_num_blocks]
        seq_lens: 每个sequence的长度, shape [num_seqs]
        scale: Attention缩放因子, 通常为 1/sqrt(head_dim)
        block_size: Block大小
    
    Returns:
        output: Attention输出, shape [num_seqs, num_heads, head_dim]
    
    Note:
        这是简化版实现，实际的GPU kernel会：
        1. 使用共享内存缓存block数据
        2. 使用Flash Attention风格的分块计算
        3. 支持GQA（Grouped Query Attention）
    """
    num_seqs = query.shape[0]
    num_heads = query.shape[1]
    head_dim = query.shape[2]
    num_kv_heads = key_cache.shape[2]
    
    # GQA: 计算每个KV head服务多少个Q head
    num_queries_per_kv = num_heads // num_kv_heads
    
    outputs = []
    
    # ========== 模拟 PagedAttention Kernel ==========
    # 实际GPU实现会高度并行化，这里用循环模拟逻辑
    
    for seq_idx in range(num_seqs):
        seq_len = seq_lens[seq_idx].item()
        num_blocks_for_seq = (seq_len + block_size - 1) // block_size
        
        # 收集该sequence的所有KV
        keys = []
        values = []
        
        for block_idx in range(num_blocks_for_seq):
            physical_block_id = block_tables[seq_idx, block_idx].item()
            
            # 计算这个block中有效的token数
            if block_idx == num_blocks_for_seq - 1:
                # 最后一个block可能不满
                tokens_in_block = seq_len - block_idx * block_size
            else:
                tokens_in_block = block_size
            
            # 从cache中取出KV
            k = key_cache[physical_block_id, :tokens_in_block]    # [tokens, num_kv_heads, head_dim]
            v = value_cache[physical_block_id, :tokens_in_block]  # [tokens, num_kv_heads, head_dim]
            
            keys.append(k)
            values.append(v)
        
        # 拼接所有block的KV
        k_seq = torch.cat(keys, dim=0)  # [seq_len, num_kv_heads, head_dim]
        v_seq = torch.cat(values, dim=0)  # [seq_len, num_kv_heads, head_dim]
        
        # 扩展KV以支持GQA
        if num_queries_per_kv > 1:
            k_seq = k_seq.repeat_interleave(num_queries_per_kv, dim=1)
            v_seq = v_seq.repeat_interleave(num_queries_per_kv, dim=1)
        
        # 计算attention
        q = query[seq_idx]  # [num_heads, head_dim]
        
        # Attention scores: Q @ K^T
        # q: [num_heads, head_dim], k_seq: [seq_len, num_heads, head_dim]
        # scores: [num_heads, seq_len]
        scores = torch.einsum('hd,shd->hs', q, k_seq) * scale
        
        # Softmax
        attn_weights = torch.softmax(scores, dim=-1)  # [num_heads, seq_len]
        
        # Output: attn_weights @ V
        # attn_weights: [num_heads, seq_len], v_seq: [seq_len, num_heads, head_dim]
        # output: [num_heads, head_dim]
        output = torch.einsum('hs,shd->hd', attn_weights, v_seq)
        
        outputs.append(output)
    
    return torch.stack(outputs, dim=0)  # [num_seqs, num_heads, head_dim]


# ============================================================================
# 辅助函数
# ============================================================================

def get_kernel_stats() -> Dict[str, Any]:
    """获取所有kernel的统计信息"""
    stats = {}
    for name, func in [
        ("rms_norm", rms_norm),
        ("fused_add_rms_norm", fused_add_rms_norm),
        ("rotary_embedding", rotary_embedding),
        ("paged_attention_v1", paged_attention_v1),
    ]:
        if hasattr(func, '_stats'):
            stats[name] = func._stats.copy()
            if stats[name]['calls'] > 0:
                stats[name]['avg_time_ms'] = stats[name]['total_time_ms'] / stats[name]['calls']
    return stats


def reset_kernel_stats() -> None:
    """重置所有kernel的统计信息"""
    for func in [rms_norm, fused_add_rms_norm, rotary_embedding, paged_attention_v1]:
        if hasattr(func, '_stats'):
            func._stats = {'calls': 0, 'total_time_ms': 0.0}
