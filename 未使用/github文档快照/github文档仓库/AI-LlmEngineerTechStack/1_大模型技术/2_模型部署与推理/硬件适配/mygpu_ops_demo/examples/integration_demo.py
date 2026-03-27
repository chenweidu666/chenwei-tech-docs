#!/usr/bin/env python3
"""
完整集成演示

这个脚本展示如何将自定义算子集成到一个简化的Transformer模型中，
模拟vLLM的工作流程。

运行方法:
    cd mygpu_ops_demo
    python examples/integration_demo.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import torch
import torch.nn as nn
import math
from typing import Optional, Tuple, List
from dataclasses import dataclass


# ============================================================================
# 配置
# ============================================================================

@dataclass
class ModelConfig:
    """简化的模型配置"""
    hidden_size: int = 4096
    num_attention_heads: int = 32
    num_kv_heads: int = 8  # GQA
    head_dim: int = 128
    num_layers: int = 2
    vocab_size: int = 32000
    max_position_embeddings: int = 2048
    rms_norm_eps: float = 1e-6
    block_size: int = 16


# ============================================================================
# 使用CustomOp构建的模型组件
# ============================================================================

class RMSNormLayer(nn.Module):
    """使用CustomOp的RMSNorm层"""
    
    def __init__(self, hidden_size: int, eps: float = 1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.eps = eps
        
        # 使用我们的CustomOp
        from vllm_plugin.ops import MyGPURMSNorm
        self.op = MyGPURMSNorm(hidden_size=hidden_size, eps=eps)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.op(x, self.weight)


class FusedAddRMSNormLayer(nn.Module):
    """使用CustomOp的Fused Add RMSNorm层"""
    
    def __init__(self, hidden_size: int, eps: float = 1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.eps = eps
        
        from vllm_plugin.ops import MyGPUFusedAddRMSNorm
        self.op = MyGPUFusedAddRMSNorm(hidden_size=hidden_size, eps=eps)
    
    def forward(
        self, 
        x: torch.Tensor, 
        residual: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.op(x, residual, self.weight)


class RotaryEmbeddingLayer(nn.Module):
    """使用CustomOp的RoPE层"""
    
    def __init__(
        self, 
        head_dim: int, 
        max_position_embeddings: int = 2048,
        base: float = 10000.0,
    ):
        super().__init__()
        
        from vllm_plugin.ops import MyGPURotaryEmbedding
        self.op = MyGPURotaryEmbedding(
            head_dim=head_dim,
            max_position_embeddings=max_position_embeddings,
            base=base,
        )
        self.op.initialize_cache(dtype=torch.float32)
    
    def forward(
        self,
        positions: torch.Tensor,
        query: torch.Tensor,
        key: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.op(positions, query, key)


class AttentionLayer(nn.Module):
    """使用CustomOp的Attention层"""
    
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        
        # 投影层
        self.q_proj = nn.Linear(config.hidden_size, config.num_attention_heads * config.head_dim, bias=False)
        self.k_proj = nn.Linear(config.hidden_size, config.num_kv_heads * config.head_dim, bias=False)
        self.v_proj = nn.Linear(config.hidden_size, config.num_kv_heads * config.head_dim, bias=False)
        self.o_proj = nn.Linear(config.num_attention_heads * config.head_dim, config.hidden_size, bias=False)
        
        # RoPE
        self.rope = RotaryEmbeddingLayer(
            head_dim=config.head_dim,
            max_position_embeddings=config.max_position_embeddings,
        )
        
        # PagedAttention for decode, Standard Attention for prefill
        from vllm_plugin.ops import MyGPUPagedAttention, MyGPUStandardAttention
        
        self.paged_attn = MyGPUPagedAttention(
            num_heads=config.num_attention_heads,
            head_dim=config.head_dim,
            scale=1.0 / math.sqrt(config.head_dim),
            num_kv_heads=config.num_kv_heads,
            block_size=config.block_size,
        )
        
        self.standard_attn = MyGPUStandardAttention(
            num_heads=config.num_attention_heads,
            head_dim=config.head_dim,
            scale=1.0 / math.sqrt(config.head_dim),
            is_causal=True,
        )
    
    def forward_prefill(
        self,
        hidden_states: torch.Tensor,
        positions: torch.Tensor,
    ) -> torch.Tensor:
        """Prefill阶段：处理完整的prompt"""
        batch_size, seq_len, _ = hidden_states.shape
        
        # 投影
        q = self.q_proj(hidden_states)
        k = self.k_proj(hidden_states)
        v = self.v_proj(hidden_states)
        
        # Reshape
        q = q.view(batch_size, seq_len, self.config.num_attention_heads, self.config.head_dim)
        k = k.view(batch_size, seq_len, self.config.num_kv_heads, self.config.head_dim)
        v = v.view(batch_size, seq_len, self.config.num_kv_heads, self.config.head_dim)
        
        # 应用RoPE
        q, k = self.rope(positions, q, k)
        
        # 转换为attention格式: [batch, heads, seq, dim]
        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)
        
        # GQA: 扩展KV
        if self.config.num_kv_heads != self.config.num_attention_heads:
            repeat = self.config.num_attention_heads // self.config.num_kv_heads
            k = k.repeat_interleave(repeat, dim=1)
            v = v.repeat_interleave(repeat, dim=1)
        
        # 标准Attention
        attn_output = self.standard_attn(q, k, v)
        
        # 输出投影
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_len, -1)
        output = self.o_proj(attn_output)
        
        return output
    
    def forward_decode(
        self,
        hidden_states: torch.Tensor,
        positions: torch.Tensor,
        key_cache: torch.Tensor,
        value_cache: torch.Tensor,
        block_tables: torch.Tensor,
        seq_lens: torch.Tensor,
    ) -> torch.Tensor:
        """Decode阶段：使用KV Cache"""
        num_seqs = hidden_states.shape[0]
        
        # 投影
        q = self.q_proj(hidden_states)
        
        # Reshape for decode (no seq dim)
        q = q.view(num_seqs, self.config.num_attention_heads, self.config.head_dim)
        
        # PagedAttention
        attn_output = self.paged_attn(
            query=q,
            key_cache=key_cache,
            value_cache=value_cache,
            block_tables=block_tables,
            seq_lens=seq_lens,
        )
        
        # 输出投影
        attn_output = attn_output.view(num_seqs, -1)
        output = self.o_proj(attn_output)
        
        return output


class TransformerBlock(nn.Module):
    """Transformer块"""
    
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        
        # 注意力层
        self.input_layernorm = FusedAddRMSNormLayer(config.hidden_size, config.rms_norm_eps)
        self.attention = AttentionLayer(config)
        
        # FFN层（简化版）
        self.post_attention_layernorm = FusedAddRMSNormLayer(config.hidden_size, config.rms_norm_eps)
        self.mlp = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size * 4, bias=False),
            nn.SiLU(),
            nn.Linear(config.hidden_size * 4, config.hidden_size, bias=False),
        )
    
    def forward_prefill(
        self,
        hidden_states: torch.Tensor,
        positions: torch.Tensor,
        residual: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Prefill阶段"""
        # 第一个残差连接
        if residual is None:
            residual = hidden_states
            hidden_states = self.input_layernorm.op.forward_native(
                hidden_states, torch.zeros_like(hidden_states), 
                self.input_layernorm.weight
            )[0]
        else:
            hidden_states, residual = self.input_layernorm(hidden_states, residual)
        
        # Attention
        attn_output = self.attention.forward_prefill(hidden_states, positions)
        
        # 第二个残差连接
        hidden_states, residual = self.post_attention_layernorm(attn_output, residual)
        
        # FFN
        mlp_output = self.mlp(hidden_states)
        
        return mlp_output, residual


class SimpleLLM(nn.Module):
    """简化的LLM模型"""
    
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        
        # Embedding
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)
        
        # Transformer层
        self.layers = nn.ModuleList([
            TransformerBlock(config) for _ in range(config.num_layers)
        ])
        
        # 输出层
        self.norm = RMSNormLayer(config.hidden_size, config.rms_norm_eps)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
    
    def forward(
        self,
        input_ids: torch.Tensor,
        positions: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """前向传播（Prefill模式）"""
        batch_size, seq_len = input_ids.shape
        
        if positions is None:
            positions = torch.arange(seq_len, device=input_ids.device)
        
        # Embedding
        hidden_states = self.embed_tokens(input_ids)
        
        # Transformer层
        residual = None
        for layer in self.layers:
            hidden_states, residual = layer.forward_prefill(
                hidden_states, positions, residual
            )
        
        # 最后的LayerNorm需要加上residual
        hidden_states = hidden_states + residual
        hidden_states = self.norm(hidden_states)
        
        # LM Head
        logits = self.lm_head(hidden_states)
        
        return logits


# ============================================================================
# 演示函数
# ============================================================================

def demo_customop_usage():
    """演示CustomOp的基本用法"""
    print("\n" + "=" * 60)
    print("CustomOp 基本用法演示")
    print("=" * 60)
    
    from vllm_plugin.ops import MyGPURMSNorm, MyGPUFusedAddRMSNorm
    
    # 1. 创建RMSNorm算子
    print("\n1. RMSNorm CustomOp")
    rms_norm = MyGPURMSNorm(hidden_size=4096, eps=1e-6)
    print(f"   算子: {rms_norm}")
    
    x = torch.randn(2, 128, 4096)
    weight = torch.randn(4096)
    
    # 调用（自动选择实现）
    output = rms_norm(x, weight)
    print(f"   输入: {x.shape} -> 输出: {output.shape}")
    
    # 2. 显式调用不同实现
    print("\n2. 显式调用不同实现")
    
    output_native = rms_norm.forward_native(x, weight)
    print(f"   forward_native: {output_native.shape}")
    
    output_oot = rms_norm.forward_oot(x, weight)
    print(f"   forward_oot: {output_oot.shape}")
    
    # 验证一致性
    is_same = torch.allclose(output_native, output_oot, rtol=1e-5, atol=1e-5)
    print(f"   结果一致: {is_same}")
    
    # 3. Fused版本
    print("\n3. Fused Add RMSNorm")
    fused_norm = MyGPUFusedAddRMSNorm(hidden_size=4096, eps=1e-6)
    
    residual = torch.randn_like(x)
    output, new_residual = fused_norm(x, residual, weight)
    print(f"   输入: x={x.shape}, residual={residual.shape}")
    print(f"   输出: output={output.shape}, new_residual={new_residual.shape}")


def demo_torch_library():
    """演示torch.library注册"""
    print("\n" + "=" * 60)
    print("torch.library 注册演示")
    print("=" * 60)
    
    from vllm_plugin.register import register_all_ops
    
    # 注册算子
    print("\n1. 注册算子到torch.ops")
    register_all_ops()
    
    # 通过torch.ops调用
    print("\n2. 通过torch.ops调用")
    x = torch.randn(2, 64, 1024)
    weight = torch.randn(1024)
    
    output = torch.ops.mygpu.rms_norm(x, weight, 1e-6)
    print(f"   torch.ops.mygpu.rms_norm: {x.shape} -> {output.shape}")
    
    # Fused版本
    residual = torch.randn_like(x)
    out, res = torch.ops.mygpu.fused_add_rms_norm(x, residual, weight, 1e-6)
    print(f"   torch.ops.mygpu.fused_add_rms_norm: 两个输出")


def demo_model_integration():
    """演示模型集成"""
    print("\n" + "=" * 60)
    print("模型集成演示")
    print("=" * 60)
    
    # 创建配置
    config = ModelConfig(
        hidden_size=1024,  # 使用较小的配置以加快演示
        num_attention_heads=8,
        num_kv_heads=2,
        head_dim=128,
        num_layers=2,
        vocab_size=1000,
        max_position_embeddings=512,
    )
    
    print(f"\n模型配置:")
    print(f"  hidden_size: {config.hidden_size}")
    print(f"  num_heads: {config.num_attention_heads}")
    print(f"  num_kv_heads: {config.num_kv_heads}")
    print(f"  num_layers: {config.num_layers}")
    
    # 创建模型
    print("\n创建模型...")
    model = SimpleLLM(config)
    model.eval()
    
    # 计算参数量
    num_params = sum(p.numel() for p in model.parameters())
    print(f"模型参数量: {num_params / 1e6:.2f}M")
    
    # 测试前向传播
    print("\n测试前向传播 (Prefill模式)...")
    batch_size = 2
    seq_len = 64
    
    input_ids = torch.randint(0, config.vocab_size, (batch_size, seq_len))
    
    with torch.no_grad():
        logits = model(input_ids)
    
    print(f"  输入: {input_ids.shape}")
    print(f"  输出: {logits.shape}")
    print(f"  输出范围: [{logits.min().item():.4f}, {logits.max().item():.4f}]")
    
    # 简单的生成演示
    print("\n简单生成演示...")
    
    # 取最后一个位置的logits进行采样
    next_token_logits = logits[:, -1, :]
    probs = torch.softmax(next_token_logits, dim=-1)
    next_tokens = torch.argmax(probs, dim=-1)
    
    print(f"  下一个token: {next_tokens.tolist()}")


def demo_kernel_stats():
    """演示Kernel统计"""
    print("\n" + "=" * 60)
    print("Kernel 统计演示")
    print("=" * 60)
    
    import mygpu_ops
    
    # 重置统计
    mygpu_ops.reset_kernel_stats()
    
    # 执行一些操作
    print("\n执行算子操作...")
    x = torch.randn(4, 128, 4096)
    weight = torch.randn(4096)
    residual = torch.randn_like(x)
    
    for i in range(10):
        _ = mygpu_ops.rms_norm(x, weight, 1e-6)
    
    for i in range(5):
        _, _ = mygpu_ops.fused_add_rms_norm(x, residual, weight, 1e-6)
    
    # 获取统计
    stats = mygpu_ops.get_kernel_stats()
    
    print("\nKernel调用统计:")
    for name, s in stats.items():
        if s['calls'] > 0:
            print(f"  {name}:")
            print(f"    调用次数: {s['calls']}")
            print(f"    总时间: {s['total_time_ms']:.4f} ms")
            if 'avg_time_ms' in s:
                print(f"    平均时间: {s['avg_time_ms']:.4f} ms")


def run_all_demos():
    """运行所有演示"""
    print("\n" + "#" * 60)
    print("#" + " " * 12 + "MyGPU Ops 完整集成演示" + " " * 12 + "#")
    print("#" * 60)
    
    demos = [
        ("CustomOp基本用法", demo_customop_usage),
        ("torch.library注册", demo_torch_library),
        ("模型集成", demo_model_integration),
        ("Kernel统计", demo_kernel_stats),
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n✗ {name} 演示失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)
    
    print("""
总结：
1. CustomOp 提供了 forward_native 和 forward_oot 两种实现
2. torch.library 允许通过 torch.ops 调用自定义算子
3. 这些算子可以无缝集成到 PyTorch 模型中
4. 在实际国产GPU适配中，forward_oot 会调用真正的优化kernel

下一步：
- 查看 mygpu_ops/core.py 了解算子实现
- 查看 vllm_plugin/ops/ 了解CustomOp封装
- 查看 vllm_plugin/register.py 了解torch.library注册
""")


if __name__ == "__main__":
    run_all_demos()
