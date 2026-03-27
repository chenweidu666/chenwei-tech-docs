"""
Rotary Embedding CustomOp Implementation

这个模块展示如何将RoPE算子包装成vLLM CustomOp。
"""

import torch
from typing import Tuple, Optional

from .base import CustomOp, use_native_if_debug

# 导入路径处理
import sys
from pathlib import Path
_project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_project_root))


class MyGPURotaryEmbedding(CustomOp):
    """
    MyGPU Rotary Position Embedding CustomOp
    
    RoPE是现代大模型的标准位置编码方式。
    这个CustomOp封装了RoPE的计算，包括：
    1. cos/sin缓存的管理
    2. Query和Key的旋转
    
    使用示例：
        rope = MyGPURotaryEmbedding(
            head_dim=128,
            max_position_embeddings=8192,
            base=10000.0,
        )
        
        # 预计算缓存
        rope.initialize_cache(dtype=torch.float16, device='cuda')
        
        # 应用RoPE
        positions = torch.arange(128, device='cuda')
        query_rot, key_rot = rope(positions, query, key)
    """
    
    def __init__(
        self,
        head_dim: int,
        max_position_embeddings: int = 8192,
        base: float = 10000.0,
        is_neox_style: bool = True,
        rotary_dim: Optional[int] = None,
    ):
        """
        初始化RoPE
        
        Args:
            head_dim: 注意力头维度
            max_position_embeddings: 最大位置数
            base: RoPE基数
            is_neox_style: 是否使用GPT-NeoX风格
            rotary_dim: 旋转维度（默认等于head_dim）
        """
        super().__init__()
        self.head_dim = head_dim
        self.max_position_embeddings = max_position_embeddings
        self.base = base
        self.is_neox_style = is_neox_style
        self.rotary_dim = rotary_dim or head_dim
        
        # 缓存
        self.cos_cache: Optional[torch.Tensor] = None
        self.sin_cache: Optional[torch.Tensor] = None
    
    def initialize_cache(
        self,
        dtype: torch.dtype = torch.float16,
        device: Optional[torch.device] = None,
    ) -> None:
        """
        初始化cos/sin缓存
        
        这个方法应该在模型初始化时调用一次。
        缓存会被重复使用，避免每次推理都重新计算。
        
        Args:
            dtype: 数据类型
            device: 设备
        """
        # 计算频率
        inv_freq = 1.0 / (
            self.base ** (
                torch.arange(0, self.rotary_dim, 2, dtype=torch.float32) 
                / self.rotary_dim
            )
        )
        
        # 位置索引
        t = torch.arange(self.max_position_embeddings, dtype=torch.float32)
        
        # 计算 freqs
        freqs = torch.outer(t, inv_freq)
        freqs = torch.cat([freqs, freqs], dim=-1)
        
        # 计算 cos/sin
        self.cos_cache = freqs.cos().to(dtype=dtype)
        self.sin_cache = freqs.sin().to(dtype=dtype)
        
        if device is not None:
            self.cos_cache = self.cos_cache.to(device)
            self.sin_cache = self.sin_cache.to(device)
    
    def _ensure_cache(self, device: torch.device) -> None:
        """确保缓存已初始化"""
        if self.cos_cache is None:
            self.initialize_cache(device=device)
        elif self.cos_cache.device != device:
            self.cos_cache = self.cos_cache.to(device)
            self.sin_cache = self.sin_cache.to(device)
    
    def forward_native(
        self,
        positions: torch.Tensor,
        query: torch.Tensor,
        key: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        PyTorch原生实现
        
        Args:
            positions: 位置索引, shape [seq_len] 或 [batch, seq_len]
            query: Query张量, shape [batch, seq_len, num_heads, head_dim]
            key: Key张量, shape [batch, seq_len, num_kv_heads, head_dim]
        
        Returns:
            (rotated_query, rotated_key)
        """
        self._ensure_cache(query.device)
        
        # 获取cos/sin
        # positions: [seq_len] -> cos/sin: [seq_len, rotary_dim]
        cos = self.cos_cache[positions]
        sin = self.sin_cache[positions]
        
        # 处理不同的输入形状
        # query/key: [batch, seq_len, num_heads, head_dim]
        # cos/sin需要: [1, seq_len, 1, rotary_dim] 或 [seq_len, 1, rotary_dim]
        if positions.dim() == 1 and query.dim() == 4:
            # positions: [seq_len], query: [batch, seq_len, heads, dim]
            cos = cos.unsqueeze(0).unsqueeze(2)  # [1, seq_len, 1, rotary_dim]
            sin = sin.unsqueeze(0).unsqueeze(2)
        elif positions.dim() == 1 and query.dim() == 3:
            # positions: [seq_len], query: [seq_len, heads, dim]
            cos = cos.unsqueeze(1)  # [seq_len, 1, rotary_dim]
            sin = sin.unsqueeze(1)
        
        # 应用旋转
        def apply_rotary(x: torch.Tensor) -> torch.Tensor:
            x_rot = x[..., :self.rotary_dim]
            x_pass = x[..., self.rotary_dim:]
            
            if self.is_neox_style:
                half_dim = self.rotary_dim // 2
                x1 = x_rot[..., :half_dim]
                x2 = x_rot[..., half_dim:]
                rotated = torch.cat([-x2, x1], dim=-1)
                x_rotated = x_rot * cos + rotated * sin
            else:
                x1 = x_rot[..., ::2]
                x2 = x_rot[..., 1::2]
                cos_half = cos[..., ::2]
                sin_half = sin[..., ::2]
                out1 = x1 * cos_half - x2 * sin_half
                out2 = x1 * sin_half + x2 * cos_half
                x_rotated = torch.stack([out1, out2], dim=-1).flatten(-2)
            
            return torch.cat([x_rotated, x_pass], dim=-1)
        
        return apply_rotary(query), apply_rotary(key)
    
    @use_native_if_debug
    def forward_oot(
        self,
        positions: torch.Tensor,
        query: torch.Tensor,
        key: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Out-of-Tree实现 - 调用mygpu_ops
        
        融合RoPE kernel的优势：
        - Query和Key在同一个kernel中处理
        - 减少cos/sin的重复读取
        - 性能提升显著
        """
        self._ensure_cache(query.device)
        
        import mygpu_ops
        
        return mygpu_ops.rotary_embedding(
            positions=positions,
            query=query,
            key=key,
            cos_cache=self.cos_cache,
            sin_cache=self.sin_cache,
            rotary_dim=self.rotary_dim,
            is_neox_style=self.is_neox_style,
        )
    
    def __repr__(self) -> str:
        return (
            f"MyGPURotaryEmbedding("
            f"head_dim={self.head_dim}, "
            f"max_pos={self.max_position_embeddings}, "
            f"base={self.base}, "
            f"neox_style={self.is_neox_style})"
        )


class MyGPURotaryEmbeddingV2(MyGPURotaryEmbedding):
    """
    RoPE V2 - 支持动态序列长度和扩展
    
    相比基础版本，增加了：
    - 动态缓存扩展
    - 线性/动态缩放支持
    - yarn扩展支持
    """
    
    def __init__(
        self,
        head_dim: int,
        max_position_embeddings: int = 8192,
        base: float = 10000.0,
        is_neox_style: bool = True,
        rotary_dim: Optional[int] = None,
        scaling_type: str = "default",
        scaling_factor: float = 1.0,
    ):
        super().__init__(
            head_dim=head_dim,
            max_position_embeddings=max_position_embeddings,
            base=base,
            is_neox_style=is_neox_style,
            rotary_dim=rotary_dim,
        )
        self.scaling_type = scaling_type
        self.scaling_factor = scaling_factor
    
    def _compute_inv_freq(self) -> torch.Tensor:
        """计算逆频率（支持各种缩放方式）"""
        if self.scaling_type == "linear":
            # 线性缩放：直接缩放位置
            inv_freq = 1.0 / (
                self.base ** (
                    torch.arange(0, self.rotary_dim, 2, dtype=torch.float32)
                    / self.rotary_dim
                )
            )
        elif self.scaling_type == "dynamic":
            # 动态缩放：根据序列长度调整base
            base = self.base * (
                (self.scaling_factor * self.max_position_embeddings / self.max_position_embeddings)
                ** (self.rotary_dim / (self.rotary_dim - 2))
            )
            inv_freq = 1.0 / (
                base ** (
                    torch.arange(0, self.rotary_dim, 2, dtype=torch.float32)
                    / self.rotary_dim
                )
            )
        else:
            # 默认
            inv_freq = 1.0 / (
                self.base ** (
                    torch.arange(0, self.rotary_dim, 2, dtype=torch.float32)
                    / self.rotary_dim
                )
            )
        
        return inv_freq
    
    def extend_cache(self, new_max_len: int) -> None:
        """
        动态扩展缓存
        
        当遇到更长的序列时调用。
        """
        if new_max_len <= self.max_position_embeddings:
            return
        
        self.max_position_embeddings = new_max_len
        
        # 重新计算缓存
        inv_freq = self._compute_inv_freq()
        t = torch.arange(new_max_len, dtype=torch.float32)
        
        if self.scaling_type == "linear":
            t = t / self.scaling_factor
        
        freqs = torch.outer(t, inv_freq)
        freqs = torch.cat([freqs, freqs], dim=-1)
        
        # 更新缓存
        dtype = self.cos_cache.dtype if self.cos_cache is not None else torch.float16
        device = self.cos_cache.device if self.cos_cache is not None else None
        
        self.cos_cache = freqs.cos().to(dtype=dtype, device=device)
        self.sin_cache = freqs.sin().to(dtype=dtype, device=device)
