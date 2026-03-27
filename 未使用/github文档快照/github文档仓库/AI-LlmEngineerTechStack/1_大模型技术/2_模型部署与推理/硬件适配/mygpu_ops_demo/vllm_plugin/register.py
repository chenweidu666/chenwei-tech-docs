"""
torch.library 算子注册模块

这个模块展示如何使用 PyTorch 的 torch.library API 注册自定义算子。
这是将国产GPU算子集成到PyTorch生态的另一种方式。

核心概念：
1. Library: 定义算子的命名空间
2. impl: 为特定设备实现算子
3. Dispatcher: PyTorch的算子分发机制

使用场景：
- 当你想让算子通过 torch.ops.xxx 调用时
- 当你需要支持 torch.compile 时
- 当你需要多设备支持时

使用示例：
    # 注册后可以这样调用
    import torch
    from vllm_plugin.register import register_all_ops
    
    register_all_ops()
    
    # 通过torch.ops调用
    output = torch.ops.mygpu.rms_norm(x, weight, eps)
"""

import torch
from typing import Tuple, Optional, List
import functools

# 导入路径处理
import sys
from pathlib import Path
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))


# ============================================================================
# 创建自定义Library
# ============================================================================

# 定义我们的算子库
# "DEF" 表示定义新的命名空间
try:
    mygpu_lib = torch.library.Library("mygpu", "DEF")
except Exception:
    # 如果已经定义过，使用IMPL模式
    mygpu_lib = torch.library.Library("mygpu", "IMPL")


# ============================================================================
# 算子签名定义
# ============================================================================

def define_ops():
    """
    定义算子签名
    
    签名格式: "op_name(参数列表) -> 返回类型"
    
    这告诉PyTorch：
    1. 算子名称
    2. 输入参数的类型
    3. 返回值的类型
    """
    try:
        # RMSNorm
        mygpu_lib.define(
            "rms_norm(Tensor x, Tensor weight, float eps) -> Tensor"
        )
        
        # Fused Add RMSNorm
        mygpu_lib.define(
            "fused_add_rms_norm(Tensor x, Tensor residual, Tensor weight, float eps) -> (Tensor, Tensor)"
        )
        
        # Rotary Embedding
        mygpu_lib.define(
            "rotary_embedding("
            "Tensor positions, Tensor query, Tensor key, "
            "Tensor cos_cache, Tensor sin_cache, "
            "int rotary_dim, bool is_neox"
            ") -> (Tensor, Tensor)"
        )
        
        # Paged Attention V1
        mygpu_lib.define(
            "paged_attention_v1("
            "Tensor query, Tensor key_cache, Tensor value_cache, "
            "Tensor block_tables, Tensor seq_lens, "
            "float scale, int block_size"
            ") -> Tensor"
        )
        
        print("[mygpu] Operator signatures defined successfully")
        
    except Exception as e:
        # 可能已经定义过
        print(f"[mygpu] Skipping op definition (may already exist): {e}")


# ============================================================================
# CPU实现（Fallback）
# ============================================================================

def impl_cpu():
    """
    注册CPU实现
    
    这是默认的fallback实现，当没有特定设备实现时使用。
    """
    
    @torch.library.impl(mygpu_lib, "rms_norm", "CPU")
    def rms_norm_cpu(x: torch.Tensor, weight: torch.Tensor, eps: float) -> torch.Tensor:
        """CPU版本的RMSNorm"""
        variance = x.pow(2).mean(dim=-1, keepdim=True)
        x_normed = x * torch.rsqrt(variance + eps)
        return x_normed * weight
    
    @torch.library.impl(mygpu_lib, "fused_add_rms_norm", "CPU")
    def fused_add_rms_norm_cpu(
        x: torch.Tensor, 
        residual: torch.Tensor, 
        weight: torch.Tensor, 
        eps: float
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """CPU版本的Fused Add RMSNorm"""
        hidden = x + residual
        new_residual = hidden.clone()
        variance = hidden.pow(2).mean(dim=-1, keepdim=True)
        hidden_normed = hidden * torch.rsqrt(variance + eps)
        output = hidden_normed * weight
        return output, new_residual
    
    @torch.library.impl(mygpu_lib, "rotary_embedding", "CPU")
    def rotary_embedding_cpu(
        positions: torch.Tensor,
        query: torch.Tensor,
        key: torch.Tensor,
        cos_cache: torch.Tensor,
        sin_cache: torch.Tensor,
        rotary_dim: int,
        is_neox: bool,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """CPU版本的RoPE"""
        cos = cos_cache[positions]
        sin = sin_cache[positions]
        
        while cos.dim() < query.dim():
            cos = cos.unsqueeze(-2)
            sin = sin.unsqueeze(-2)
        
        def apply_rotary(x):
            x_rot = x[..., :rotary_dim]
            x_pass = x[..., rotary_dim:]
            
            if is_neox:
                half_dim = rotary_dim // 2
                x1, x2 = x_rot[..., :half_dim], x_rot[..., half_dim:]
                rotated = torch.cat([-x2, x1], dim=-1)
                x_rotated = x_rot * cos + rotated * sin
            else:
                x1, x2 = x_rot[..., ::2], x_rot[..., 1::2]
                cos_half, sin_half = cos[..., ::2], sin[..., ::2]
                out1 = x1 * cos_half - x2 * sin_half
                out2 = x1 * sin_half + x2 * cos_half
                x_rotated = torch.stack([out1, out2], dim=-1).flatten(-2)
            
            return torch.cat([x_rotated, x_pass], dim=-1)
        
        return apply_rotary(query), apply_rotary(key)
    
    @torch.library.impl(mygpu_lib, "paged_attention_v1", "CPU")
    def paged_attention_v1_cpu(
        query: torch.Tensor,
        key_cache: torch.Tensor,
        value_cache: torch.Tensor,
        block_tables: torch.Tensor,
        seq_lens: torch.Tensor,
        scale: float,
        block_size: int,
    ) -> torch.Tensor:
        """CPU版本的PagedAttention"""
        num_seqs = query.shape[0]
        num_heads = query.shape[1]
        head_dim = query.shape[2]
        num_kv_heads = key_cache.shape[2]
        num_queries_per_kv = num_heads // num_kv_heads
        
        outputs = []
        
        for seq_idx in range(num_seqs):
            seq_len = seq_lens[seq_idx].item()
            num_blocks = (seq_len + block_size - 1) // block_size
            
            keys, values = [], []
            for b in range(num_blocks):
                block_id = block_tables[seq_idx, b].item()
                tokens = min(block_size, seq_len - b * block_size)
                keys.append(key_cache[block_id, :tokens])
                values.append(value_cache[block_id, :tokens])
            
            k_seq = torch.cat(keys, dim=0)
            v_seq = torch.cat(values, dim=0)
            
            if num_queries_per_kv > 1:
                k_seq = k_seq.repeat_interleave(num_queries_per_kv, dim=1)
                v_seq = v_seq.repeat_interleave(num_queries_per_kv, dim=1)
            
            q = query[seq_idx]
            scores = torch.einsum('hd,shd->hs', q, k_seq) * scale
            attn_weights = torch.softmax(scores, dim=-1)
            output = torch.einsum('hs,shd->hd', attn_weights, v_seq)
            outputs.append(output)
        
        return torch.stack(outputs, dim=0)
    
    print("[mygpu] CPU implementations registered")


# ============================================================================
# CUDA实现（如果有CUDA设备）
# ============================================================================

def impl_cuda():
    """
    注册CUDA实现
    
    在实际场景中，这里会调用真正的CUDA kernel。
    这里我们用mygpu_ops模拟。
    """
    try:
        import mygpu_ops
    except ImportError:
        print("[mygpu] mygpu_ops not available, skipping CUDA impl")
        return
    
    @torch.library.impl(mygpu_lib, "rms_norm", "CUDA")
    def rms_norm_cuda(x: torch.Tensor, weight: torch.Tensor, eps: float) -> torch.Tensor:
        """CUDA版本 - 调用mygpu_ops"""
        return mygpu_ops.rms_norm(x, weight, eps)
    
    @torch.library.impl(mygpu_lib, "fused_add_rms_norm", "CUDA")
    def fused_add_rms_norm_cuda(
        x: torch.Tensor,
        residual: torch.Tensor,
        weight: torch.Tensor,
        eps: float
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """CUDA版本 - 调用mygpu_ops"""
        return mygpu_ops.fused_add_rms_norm(x, residual, weight, eps)
    
    @torch.library.impl(mygpu_lib, "rotary_embedding", "CUDA")
    def rotary_embedding_cuda(
        positions: torch.Tensor,
        query: torch.Tensor,
        key: torch.Tensor,
        cos_cache: torch.Tensor,
        sin_cache: torch.Tensor,
        rotary_dim: int,
        is_neox: bool,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """CUDA版本 - 调用mygpu_ops"""
        return mygpu_ops.rotary_embedding(
            positions, query, key, cos_cache, sin_cache, rotary_dim, is_neox
        )
    
    @torch.library.impl(mygpu_lib, "paged_attention_v1", "CUDA")
    def paged_attention_v1_cuda(
        query: torch.Tensor,
        key_cache: torch.Tensor,
        value_cache: torch.Tensor,
        block_tables: torch.Tensor,
        seq_lens: torch.Tensor,
        scale: float,
        block_size: int,
    ) -> torch.Tensor:
        """CUDA版本 - 调用mygpu_ops"""
        return mygpu_ops.paged_attention_v1(
            query, key_cache, value_cache, block_tables, seq_lens, scale, block_size
        )
    
    print("[mygpu] CUDA implementations registered")


# ============================================================================
# PrivateUse1实现（自定义设备）
# ============================================================================

def impl_privateuse1():
    """
    注册PrivateUse1实现
    
    PrivateUse1是PyTorch预留给第三方设备的dispatch key。
    国产GPU通常使用这个key来注册自己的实现。
    
    使用方法：
    1. torch.utils.rename_privateuse1_backend("mygpu_device")
    2. 然后可以使用 torch.device("mygpu_device")
    """
    try:
        import mygpu_ops
    except ImportError:
        print("[mygpu] mygpu_ops not available, skipping PrivateUse1 impl")
        return
    
    @torch.library.impl(mygpu_lib, "rms_norm", "PrivateUse1")
    def rms_norm_mygpu(x: torch.Tensor, weight: torch.Tensor, eps: float) -> torch.Tensor:
        """MyGPU设备实现"""
        return mygpu_ops.rms_norm(x, weight, eps)
    
    @torch.library.impl(mygpu_lib, "fused_add_rms_norm", "PrivateUse1")
    def fused_add_rms_norm_mygpu(
        x: torch.Tensor,
        residual: torch.Tensor,
        weight: torch.Tensor,
        eps: float
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """MyGPU设备实现"""
        return mygpu_ops.fused_add_rms_norm(x, residual, weight, eps)
    
    @torch.library.impl(mygpu_lib, "rotary_embedding", "PrivateUse1")
    def rotary_embedding_mygpu(
        positions: torch.Tensor,
        query: torch.Tensor,
        key: torch.Tensor,
        cos_cache: torch.Tensor,
        sin_cache: torch.Tensor,
        rotary_dim: int,
        is_neox: bool,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """MyGPU设备实现"""
        return mygpu_ops.rotary_embedding(
            positions, query, key, cos_cache, sin_cache, rotary_dim, is_neox
        )
    
    @torch.library.impl(mygpu_lib, "paged_attention_v1", "PrivateUse1")
    def paged_attention_v1_mygpu(
        query: torch.Tensor,
        key_cache: torch.Tensor,
        value_cache: torch.Tensor,
        block_tables: torch.Tensor,
        seq_lens: torch.Tensor,
        scale: float,
        block_size: int,
    ) -> torch.Tensor:
        """MyGPU设备实现"""
        return mygpu_ops.paged_attention_v1(
            query, key_cache, value_cache, block_tables, seq_lens, scale, block_size
        )
    
    print("[mygpu] PrivateUse1 implementations registered")


# ============================================================================
# 统一注册入口
# ============================================================================

_registered = False

def register_all_ops():
    """
    注册所有算子
    
    这是主要的注册入口，应该在程序启动时调用一次。
    
    Usage:
        from vllm_plugin.register import register_all_ops
        register_all_ops()
        
        # 然后可以通过torch.ops调用
        output = torch.ops.mygpu.rms_norm(x, weight, 1e-6)
    """
    global _registered
    if _registered:
        print("[mygpu] Ops already registered, skipping")
        return
    
    print("[mygpu] Registering operators...")
    
    # 1. 定义算子签名
    define_ops()
    
    # 2. 注册CPU实现（fallback）
    impl_cpu()
    
    # 3. 注册CUDA实现（如果可用）
    if torch.cuda.is_available():
        impl_cuda()
    
    # 4. 注册PrivateUse1实现
    impl_privateuse1()
    
    _registered = True
    print("[mygpu] All operators registered successfully!")


def is_registered() -> bool:
    """检查是否已注册"""
    return _registered


# ============================================================================
# 便捷调用函数
# ============================================================================

def call_rms_norm(x: torch.Tensor, weight: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    """
    调用注册的RMSNorm算子
    
    这个函数会自动根据输入tensor的设备选择对应的实现。
    """
    if not _registered:
        register_all_ops()
    return torch.ops.mygpu.rms_norm(x, weight, eps)


def call_fused_add_rms_norm(
    x: torch.Tensor, 
    residual: torch.Tensor, 
    weight: torch.Tensor, 
    eps: float = 1e-6
) -> Tuple[torch.Tensor, torch.Tensor]:
    """调用注册的Fused Add RMSNorm算子"""
    if not _registered:
        register_all_ops()
    return torch.ops.mygpu.fused_add_rms_norm(x, residual, weight, eps)


def call_rotary_embedding(
    positions: torch.Tensor,
    query: torch.Tensor,
    key: torch.Tensor,
    cos_cache: torch.Tensor,
    sin_cache: torch.Tensor,
    rotary_dim: Optional[int] = None,
    is_neox: bool = True,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """调用注册的RoPE算子"""
    if not _registered:
        register_all_ops()
    if rotary_dim is None:
        rotary_dim = query.shape[-1]
    return torch.ops.mygpu.rotary_embedding(
        positions, query, key, cos_cache, sin_cache, rotary_dim, is_neox
    )


def call_paged_attention_v1(
    query: torch.Tensor,
    key_cache: torch.Tensor,
    value_cache: torch.Tensor,
    block_tables: torch.Tensor,
    seq_lens: torch.Tensor,
    scale: float,
    block_size: int = 16,
) -> torch.Tensor:
    """调用注册的PagedAttention算子"""
    if not _registered:
        register_all_ops()
    return torch.ops.mygpu.paged_attention_v1(
        query, key_cache, value_cache, block_tables, seq_lens, scale, block_size
    )


# ============================================================================
# 自动注册（导入时执行）
# ============================================================================

if __name__ != "__main__":
    # 模块被导入时自动注册
    # register_all_ops()  # 可以取消注释以实现自动注册
    pass
