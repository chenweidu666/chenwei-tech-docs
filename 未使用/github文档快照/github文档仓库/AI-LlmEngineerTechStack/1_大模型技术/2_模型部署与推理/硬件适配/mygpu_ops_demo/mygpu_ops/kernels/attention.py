"""
Attention Kernels - 注意力机制的Kernel实现

这个模块模拟GPU Attention kernel的实现。
包括标准Attention和PagedAttention。

主要算子:
- scaled_dot_product_attention: 标准SDPA
- paged_attention_v1_kernel: PagedAttention V1
- paged_attention_v2_kernel: PagedAttention V2
- flash_attention_kernel: Flash Attention (简化版)
"""

import torch
from typing import Tuple, Optional, List
from dataclasses import dataclass
import math


@dataclass
class AttentionConfig:
    """Attention配置"""
    block_size: int = 16          # PagedAttention block大小
    partition_size: int = 512     # V2版本的分区大小
    use_alibi: bool = False       # 是否使用ALiBi位置编码
    sliding_window: Optional[int] = None  # 滑动窗口大小


def scaled_dot_product_attention(
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    scale: Optional[float] = None,
    attn_mask: Optional[torch.Tensor] = None,
    is_causal: bool = False,
) -> torch.Tensor:
    """
    标准缩放点积注意力
    
    公式: Attention(Q, K, V) = softmax(Q @ K^T / sqrt(d_k)) @ V
    
    GPU Kernel实现细节:
    
    ```cpp
    // 简化的CUDA实现思路
    __global__ void attention_kernel(
        float* output,
        const float* Q,
        const float* K,
        const float* V,
        int seq_len,
        int head_dim,
        float scale
    ) {
        // 每个block处理一个head的一行
        int batch_head = blockIdx.y;
        int query_pos = blockIdx.x;
        
        // 1. 计算Q @ K^T
        __shared__ float scores[MAX_SEQ_LEN];
        for (int k = threadIdx.x; k < seq_len; k += blockDim.x) {
            float score = 0.0f;
            for (int d = 0; d < head_dim; d++) {
                score += Q[query_pos * head_dim + d] * 
                        K[k * head_dim + d];
            }
            scores[k] = score * scale;
        }
        __syncthreads();
        
        // 2. Softmax (需要两遍扫描: 求max, 求sum)
        // ... softmax实现 ...
        
        // 3. 乘以V
        // ... output计算 ...
    }
    ```
    
    Args:
        query: [batch, num_heads, seq_len, head_dim]
        key: [batch, num_heads, seq_len, head_dim]
        value: [batch, num_heads, seq_len, head_dim]
        scale: 缩放因子，默认 1/sqrt(head_dim)
        attn_mask: 注意力掩码
        is_causal: 是否使用因果掩码
    
    Returns:
        output: [batch, num_heads, seq_len, head_dim]
    """
    if scale is None:
        scale = 1.0 / math.sqrt(query.shape[-1])
    
    # Q @ K^T
    scores = torch.matmul(query, key.transpose(-2, -1)) * scale
    
    # 应用掩码
    if is_causal:
        seq_len = query.shape[-2]
        causal_mask = torch.triu(
            torch.ones(seq_len, seq_len, device=query.device, dtype=torch.bool),
            diagonal=1
        )
        scores = scores.masked_fill(causal_mask, float('-inf'))
    
    if attn_mask is not None:
        scores = scores + attn_mask
    
    # Softmax
    attn_weights = torch.softmax(scores, dim=-1)
    
    # @ V
    output = torch.matmul(attn_weights, value)
    
    return output


def paged_attention_v1_kernel(
    query: torch.Tensor,
    key_cache: torch.Tensor,
    value_cache: torch.Tensor,
    block_tables: torch.Tensor,
    seq_lens: torch.Tensor,
    scale: float,
    block_size: int = 16,
) -> torch.Tensor:
    """
    PagedAttention V1 Kernel
    
    这是vLLM的核心算子，实现了分页的KV Cache管理。
    
    核心思想：
    1. KV Cache被分成固定大小的block（类似OS的内存页）
    2. 每个sequence有一个block table，记录其KV存储位置
    3. Attention计算时，根据block table访问对应的KV
    
    优势：
    - 避免KV Cache的碎片化
    - 支持动态sequence长度
    - 便于实现Continuous Batching
    
    GPU Kernel实现细节:
    
    ```cpp
    // PagedAttention V1 CUDA Kernel伪代码
    __global__ void paged_attention_v1_kernel(
        float* output,
        const float* query,
        const float* key_cache,
        const float* value_cache,
        const int* block_tables,
        const int* seq_lens,
        float scale,
        int block_size,
        int num_heads,
        int head_dim
    ) {
        // 每个block处理一个sequence的一个head
        int seq_idx = blockIdx.x;
        int head_idx = blockIdx.y;
        int seq_len = seq_lens[seq_idx];
        
        // 1. 加载query到寄存器
        float q[HEAD_DIM];
        for (int d = 0; d < head_dim; d++) {
            q[d] = query[seq_idx * num_heads * head_dim + 
                        head_idx * head_dim + d];
        }
        
        // 2. 遍历所有block，计算attention
        float max_score = -INFINITY;
        float sum_exp = 0.0f;
        float output_acc[HEAD_DIM] = {0};
        
        int num_blocks = (seq_len + block_size - 1) / block_size;
        for (int b = 0; b < num_blocks; b++) {
            int physical_block = block_tables[seq_idx * max_blocks + b];
            
            // 计算这个block内所有token的attention score
            for (int t = 0; t < block_size; t++) {
                int token_idx = b * block_size + t;
                if (token_idx >= seq_len) break;
                
                // 从cache读取K
                float score = 0.0f;
                for (int d = 0; d < head_dim; d++) {
                    float k = key_cache[physical_block * block_size * head_dim +
                                       t * head_dim + d];
                    score += q[d] * k;
                }
                score *= scale;
                
                // Online softmax更新
                float old_max = max_score;
                max_score = max(max_score, score);
                float exp_score = exp(score - max_score);
                sum_exp = sum_exp * exp(old_max - max_score) + exp_score;
                
                // 累加V
                for (int d = 0; d < head_dim; d++) {
                    float v = value_cache[physical_block * block_size * head_dim +
                                         t * head_dim + d];
                    output_acc[d] = output_acc[d] * exp(old_max - max_score) + 
                                   exp_score * v;
                }
            }
        }
        
        // 3. 归一化并写回
        for (int d = 0; d < head_dim; d++) {
            output[seq_idx * num_heads * head_dim + head_idx * head_dim + d] = 
                output_acc[d] / sum_exp;
        }
    }
    ```
    
    Args:
        query: [num_seqs, num_heads, head_dim]
        key_cache: [num_blocks, block_size, num_kv_heads, head_dim]
        value_cache: [num_blocks, block_size, num_kv_heads, head_dim]
        block_tables: [num_seqs, max_num_blocks]
        seq_lens: [num_seqs]
        scale: 缩放因子
        block_size: block大小
    
    Returns:
        output: [num_seqs, num_heads, head_dim]
    """
    num_seqs = query.shape[0]
    num_heads = query.shape[1]
    head_dim = query.shape[2]
    num_kv_heads = key_cache.shape[2]
    
    # GQA支持
    num_queries_per_kv = num_heads // num_kv_heads
    
    outputs = []
    
    # ========== 模拟PagedAttention Kernel ==========
    
    for seq_idx in range(num_seqs):
        seq_len = seq_lens[seq_idx].item()
        num_blocks_for_seq = (seq_len + block_size - 1) // block_size
        
        # 收集KV
        keys = []
        values = []
        
        for block_idx in range(num_blocks_for_seq):
            physical_block_id = block_tables[seq_idx, block_idx].item()
            
            # 计算block内有效token数
            tokens_in_block = min(block_size, seq_len - block_idx * block_size)
            
            k = key_cache[physical_block_id, :tokens_in_block]
            v = value_cache[physical_block_id, :tokens_in_block]
            
            keys.append(k)
            values.append(v)
        
        # 拼接
        k_seq = torch.cat(keys, dim=0)  # [seq_len, num_kv_heads, head_dim]
        v_seq = torch.cat(values, dim=0)
        
        # GQA扩展
        if num_queries_per_kv > 1:
            k_seq = k_seq.repeat_interleave(num_queries_per_kv, dim=1)
            v_seq = v_seq.repeat_interleave(num_queries_per_kv, dim=1)
        
        # 计算attention
        q = query[seq_idx]  # [num_heads, head_dim]
        
        # scores: [num_heads, seq_len]
        scores = torch.einsum('hd,shd->hs', q, k_seq) * scale
        attn_weights = torch.softmax(scores, dim=-1)
        
        # output: [num_heads, head_dim]
        output = torch.einsum('hs,shd->hd', attn_weights, v_seq)
        outputs.append(output)
    
    return torch.stack(outputs, dim=0)


def paged_attention_v2_kernel(
    query: torch.Tensor,
    key_cache: torch.Tensor,
    value_cache: torch.Tensor,
    block_tables: torch.Tensor,
    seq_lens: torch.Tensor,
    scale: float,
    block_size: int = 16,
    partition_size: int = 512,
) -> torch.Tensor:
    """
    PagedAttention V2 Kernel
    
    V2版本对长序列进行了优化：
    - 将序列分成多个partition
    - 每个partition独立计算
    - 最后合并结果
    
    优势：
    - 更好的并行度
    - 减少长序列的计算瓶颈
    - 更好的GPU利用率
    
    Args:
        query: [num_seqs, num_heads, head_dim]
        key_cache: [num_blocks, block_size, num_kv_heads, head_dim]
        value_cache: [num_blocks, block_size, num_kv_heads, head_dim]
        block_tables: [num_seqs, max_num_blocks]
        seq_lens: [num_seqs]
        scale: 缩放因子
        block_size: block大小
        partition_size: 分区大小
    
    Returns:
        output: [num_seqs, num_heads, head_dim]
    """
    # 简化实现：直接调用V1
    # 实际V2会有更复杂的分区逻辑
    return paged_attention_v1_kernel(
        query=query,
        key_cache=key_cache,
        value_cache=value_cache,
        block_tables=block_tables,
        seq_lens=seq_lens,
        scale=scale,
        block_size=block_size,
    )


def flash_attention_kernel(
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    scale: Optional[float] = None,
    is_causal: bool = False,
) -> torch.Tensor:
    """
    Flash Attention 简化实现
    
    Flash Attention的核心思想：
    1. 使用分块计算，减少显存占用
    2. 在SRAM中完成softmax，避免写回HBM
    3. 使用online softmax算法
    
    内存复杂度：
    - 标准Attention: O(N^2) - 需要存储完整的attention矩阵
    - Flash Attention: O(N) - 只需要存储分块大小的中间结果
    
    这里是简化版，实际Flash Attention的CUDA实现非常复杂。
    
    Args:
        query: [batch, num_heads, seq_len, head_dim]
        key: [batch, num_heads, seq_len, head_dim]
        value: [batch, num_heads, seq_len, head_dim]
        scale: 缩放因子
        is_causal: 是否因果
    
    Returns:
        output: [batch, num_heads, seq_len, head_dim]
    """
    if scale is None:
        scale = 1.0 / math.sqrt(query.shape[-1])
    
    # 分块大小（实际Flash Attention会根据SRAM大小动态选择）
    BLOCK_SIZE = 64
    
    batch_size, num_heads, seq_len, head_dim = query.shape
    
    # 初始化输出
    output = torch.zeros_like(query)
    
    # 分块计算
    for i in range(0, seq_len, BLOCK_SIZE):
        i_end = min(i + BLOCK_SIZE, seq_len)
        q_block = query[:, :, i:i_end, :]  # [B, H, block, D]
        
        # 累积softmax的分母和加权value
        max_scores = torch.full(
            (batch_size, num_heads, i_end - i, 1), 
            float('-inf'), 
            device=query.device
        )
        sum_exp = torch.zeros(
            (batch_size, num_heads, i_end - i, 1), 
            device=query.device
        )
        output_block = torch.zeros(
            (batch_size, num_heads, i_end - i, head_dim), 
            device=query.device
        )
        
        for j in range(0, seq_len, BLOCK_SIZE):
            j_end = min(j + BLOCK_SIZE, seq_len)
            
            # 因果掩码：只看之前的token
            if is_causal and j > i_end - 1:
                continue
            
            k_block = key[:, :, j:j_end, :]
            v_block = value[:, :, j:j_end, :]
            
            # 计算attention scores
            scores = torch.matmul(q_block, k_block.transpose(-2, -1)) * scale
            
            # 应用因果掩码
            if is_causal:
                # 创建block级别的因果掩码
                q_positions = torch.arange(i, i_end, device=query.device)
                k_positions = torch.arange(j, j_end, device=query.device)
                causal_mask = q_positions.unsqueeze(1) < k_positions.unsqueeze(0)
                scores = scores.masked_fill(causal_mask.unsqueeze(0).unsqueeze(0), float('-inf'))
            
            # Online softmax更新
            block_max = scores.max(dim=-1, keepdim=True)[0]
            new_max = torch.maximum(max_scores, block_max)
            
            # 更新累积值
            exp_scores = torch.exp(scores - new_max)
            sum_exp = sum_exp * torch.exp(max_scores - new_max) + exp_scores.sum(dim=-1, keepdim=True)
            
            # 更新输出
            output_block = output_block * torch.exp(max_scores - new_max) + torch.matmul(exp_scores, v_block)
            
            max_scores = new_max
        
        # 归一化
        output[:, :, i:i_end, :] = output_block / sum_exp
    
    return output


# ============================================================================
# KV Cache 管理
# ============================================================================

class KVCache:
    """
    KV Cache管理器
    
    用于管理PagedAttention的KV缓存。
    """
    
    def __init__(
        self,
        num_blocks: int,
        block_size: int,
        num_kv_heads: int,
        head_dim: int,
        dtype: torch.dtype = torch.float16,
        device: Optional[torch.device] = None,
    ):
        self.num_blocks = num_blocks
        self.block_size = block_size
        self.num_kv_heads = num_kv_heads
        self.head_dim = head_dim
        self.dtype = dtype
        self.device = device
        
        # 分配缓存
        self.key_cache = torch.zeros(
            (num_blocks, block_size, num_kv_heads, head_dim),
            dtype=dtype,
            device=device,
        )
        self.value_cache = torch.zeros(
            (num_blocks, block_size, num_kv_heads, head_dim),
            dtype=dtype,
            device=device,
        )
        
        # 空闲block列表
        self.free_blocks = list(range(num_blocks))
    
    def allocate_block(self) -> int:
        """分配一个block"""
        if not self.free_blocks:
            raise RuntimeError("No free blocks available")
        return self.free_blocks.pop(0)
    
    def free_block(self, block_id: int) -> None:
        """释放一个block"""
        self.free_blocks.append(block_id)
    
    def write_kv(
        self,
        block_id: int,
        slot: int,
        key: torch.Tensor,
        value: torch.Tensor,
    ) -> None:
        """写入KV到指定位置"""
        self.key_cache[block_id, slot] = key
        self.value_cache[block_id, slot] = value
    
    def get_num_free_blocks(self) -> int:
        """获取空闲block数量"""
        return len(self.free_blocks)
