"""
Attention CustomOp Implementation

这个模块展示如何将PagedAttention算子包装成vLLM CustomOp。
"""

import torch
from typing import Optional
import math

from .base import CustomOp, use_native_if_debug

# 导入路径处理
import sys
from pathlib import Path
_project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_project_root))


class MyGPUPagedAttention(CustomOp):
    """
    MyGPU PagedAttention CustomOp
    
    PagedAttention是vLLM的核心创新，实现了：
    1. 分页的KV Cache管理
    2. 动态序列长度支持
    3. 高效的Continuous Batching
    
    使用示例：
        paged_attn = MyGPUPagedAttention(
            num_heads=32,
            head_dim=128,
            scale=1.0 / math.sqrt(128),
            num_kv_heads=8,  # GQA
            block_size=16,
        )
        
        output = paged_attn(
            query=query,
            key_cache=key_cache,
            value_cache=value_cache,
            block_tables=block_tables,
            seq_lens=seq_lens,
        )
    """
    
    def __init__(
        self,
        num_heads: int,
        head_dim: int,
        scale: Optional[float] = None,
        num_kv_heads: Optional[int] = None,
        block_size: int = 16,
        sliding_window: Optional[int] = None,
    ):
        """
        初始化PagedAttention
        
        Args:
            num_heads: Query头数量
            head_dim: 头维度
            scale: 缩放因子（默认 1/sqrt(head_dim)）
            num_kv_heads: KV头数量（GQA支持，默认等于num_heads）
            block_size: PagedAttention块大小
            sliding_window: 滑动窗口大小（可选）
        """
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.scale = scale if scale is not None else 1.0 / math.sqrt(head_dim)
        self.num_kv_heads = num_kv_heads if num_kv_heads is not None else num_heads
        self.block_size = block_size
        self.sliding_window = sliding_window
        
        # GQA: 计算每个KV头服务多少个Query头
        self.num_queries_per_kv = self.num_heads // self.num_kv_heads
    
    def forward_native(
        self,
        query: torch.Tensor,
        key_cache: torch.Tensor,
        value_cache: torch.Tensor,
        block_tables: torch.Tensor,
        seq_lens: torch.Tensor,
    ) -> torch.Tensor:
        """
        PyTorch原生实现
        
        这个实现用循环模拟PagedAttention的行为，
        便于理解算法逻辑，但性能不佳。
        
        Args:
            query: [num_seqs, num_heads, head_dim]
            key_cache: [num_blocks, block_size, num_kv_heads, head_dim]
            value_cache: [num_blocks, block_size, num_kv_heads, head_dim]
            block_tables: [num_seqs, max_num_blocks]
            seq_lens: [num_seqs]
        
        Returns:
            output: [num_seqs, num_heads, head_dim]
        """
        num_seqs = query.shape[0]
        outputs = []
        
        for seq_idx in range(num_seqs):
            seq_len = seq_lens[seq_idx].item()
            num_blocks_for_seq = (seq_len + self.block_size - 1) // self.block_size
            
            # 收集KV
            keys = []
            values = []
            
            for block_idx in range(num_blocks_for_seq):
                physical_block_id = block_tables[seq_idx, block_idx].item()
                tokens_in_block = min(
                    self.block_size, 
                    seq_len - block_idx * self.block_size
                )
                
                k = key_cache[physical_block_id, :tokens_in_block]
                v = value_cache[physical_block_id, :tokens_in_block]
                
                keys.append(k)
                values.append(v)
            
            # 拼接
            k_seq = torch.cat(keys, dim=0)
            v_seq = torch.cat(values, dim=0)
            
            # GQA扩展
            if self.num_queries_per_kv > 1:
                k_seq = k_seq.repeat_interleave(self.num_queries_per_kv, dim=1)
                v_seq = v_seq.repeat_interleave(self.num_queries_per_kv, dim=1)
            
            # 滑动窗口（可选）
            if self.sliding_window is not None and seq_len > self.sliding_window:
                start_idx = seq_len - self.sliding_window
                k_seq = k_seq[start_idx:]
                v_seq = v_seq[start_idx:]
            
            # Attention计算
            q = query[seq_idx]
            scores = torch.einsum('hd,shd->hs', q, k_seq) * self.scale
            attn_weights = torch.softmax(scores, dim=-1)
            output = torch.einsum('hs,shd->hd', attn_weights, v_seq)
            
            outputs.append(output)
        
        return torch.stack(outputs, dim=0)
    
    @use_native_if_debug
    def forward_oot(
        self,
        query: torch.Tensor,
        key_cache: torch.Tensor,
        value_cache: torch.Tensor,
        block_tables: torch.Tensor,
        seq_lens: torch.Tensor,
    ) -> torch.Tensor:
        """
        Out-of-Tree实现 - 调用mygpu_ops
        
        PagedAttention kernel的优化点：
        1. Block级别的并行
        2. 共享内存缓存KV数据
        3. Online Softmax避免两次扫描
        4. 向量化内存访问
        """
        import mygpu_ops
        
        return mygpu_ops.paged_attention_v1(
            query=query,
            key_cache=key_cache,
            value_cache=value_cache,
            block_tables=block_tables,
            seq_lens=seq_lens,
            scale=self.scale,
            block_size=self.block_size,
        )
    
    def __repr__(self) -> str:
        return (
            f"MyGPUPagedAttention("
            f"num_heads={self.num_heads}, "
            f"head_dim={self.head_dim}, "
            f"num_kv_heads={self.num_kv_heads}, "
            f"block_size={self.block_size})"
        )


class MyGPUStandardAttention(CustomOp):
    """
    标准Scaled Dot-Product Attention
    
    用于prefill阶段，不使用KV Cache。
    """
    
    def __init__(
        self,
        num_heads: int,
        head_dim: int,
        scale: Optional[float] = None,
        is_causal: bool = True,
    ):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.scale = scale if scale is not None else 1.0 / math.sqrt(head_dim)
        self.is_causal = is_causal
    
    def forward_native(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attn_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        PyTorch原生实现
        
        Args:
            query: [batch, num_heads, seq_len, head_dim]
            key: [batch, num_heads, seq_len, head_dim]
            value: [batch, num_heads, seq_len, head_dim]
            attn_mask: 可选的attention mask
        
        Returns:
            output: [batch, num_heads, seq_len, head_dim]
        """
        # Q @ K^T
        scores = torch.matmul(query, key.transpose(-2, -1)) * self.scale
        
        # 因果掩码
        if self.is_causal:
            seq_len = query.shape[-2]
            causal_mask = torch.triu(
                torch.ones(seq_len, seq_len, device=query.device, dtype=torch.bool),
                diagonal=1
            )
            scores = scores.masked_fill(causal_mask, float('-inf'))
        
        # 额外掩码
        if attn_mask is not None:
            scores = scores + attn_mask
        
        # Softmax
        attn_weights = torch.softmax(scores, dim=-1)
        
        # @ V
        output = torch.matmul(attn_weights, value)
        
        return output
    
    @use_native_if_debug
    def forward_oot(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attn_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Out-of-Tree实现
        
        在实际场景中，这里会调用Flash Attention kernel。
        """
        # 导入mygpu_ops的attention模块
        from mygpu_ops.kernels.attention import scaled_dot_product_attention
        
        return scaled_dot_product_attention(
            query=query,
            key=key,
            value=value,
            scale=self.scale,
            attn_mask=attn_mask,
            is_causal=self.is_causal,
        )
    
    def __repr__(self) -> str:
        return (
            f"MyGPUStandardAttention("
            f"num_heads={self.num_heads}, "
            f"head_dim={self.head_dim}, "
            f"is_causal={self.is_causal})"
        )
