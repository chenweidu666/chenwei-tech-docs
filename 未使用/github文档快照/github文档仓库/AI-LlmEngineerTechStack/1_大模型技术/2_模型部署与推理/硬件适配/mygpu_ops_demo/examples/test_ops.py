#!/usr/bin/env python3
"""
算子正确性测试脚本

这个脚本测试所有自定义算子的正确性，
通过对比forward_native和forward_oot的结果。

运行方法:
    cd mygpu_ops_demo
    python examples/test_ops.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import torch
import math
from typing import Tuple


def test_rms_norm():
    """测试RMSNorm算子"""
    print("\n" + "=" * 60)
    print("测试 RMSNorm")
    print("=" * 60)
    
    from vllm_plugin.ops import MyGPURMSNorm
    
    # 配置
    batch_size = 4
    seq_len = 128
    hidden_size = 4096
    eps = 1e-6
    
    # 创建算子
    rms_norm = MyGPURMSNorm(hidden_size=hidden_size, eps=eps)
    
    # 准备输入
    x = torch.randn(batch_size, seq_len, hidden_size, dtype=torch.float32)
    weight = torch.randn(hidden_size, dtype=torch.float32)
    
    # 测试正确性
    print(f"输入形状: x={x.shape}, weight={weight.shape}")
    
    result = rms_norm.debug_compare(x, weight)
    
    print(f"结果对比:")
    for comp in result["comparisons"]:
        print(f"  Tensor {comp['tensor_index']}: "
              f"max_diff={comp['max_diff']:.2e}, "
              f"mean_diff={comp['mean_diff']:.2e}, "
              f"allclose(1e-5)={comp['allclose_1e-5']}")
    
    assert result["all_match_1e-5"], "RMSNorm 结果不匹配!"
    print("✓ RMSNorm 测试通过!")
    
    return True


def test_fused_add_rms_norm():
    """测试Fused Add RMSNorm算子"""
    print("\n" + "=" * 60)
    print("测试 Fused Add RMSNorm")
    print("=" * 60)
    
    from vllm_plugin.ops import MyGPUFusedAddRMSNorm
    
    # 配置
    batch_size = 4
    seq_len = 128
    hidden_size = 4096
    eps = 1e-6
    
    # 创建算子
    fused_norm = MyGPUFusedAddRMSNorm(hidden_size=hidden_size, eps=eps)
    
    # 准备输入
    x = torch.randn(batch_size, seq_len, hidden_size, dtype=torch.float32)
    residual = torch.randn(batch_size, seq_len, hidden_size, dtype=torch.float32)
    weight = torch.randn(hidden_size, dtype=torch.float32)
    
    print(f"输入形状: x={x.shape}, residual={residual.shape}, weight={weight.shape}")
    
    result = fused_norm.debug_compare(x, residual, weight)
    
    print(f"结果对比 ({result['num_tensors']} 个输出张量):")
    for comp in result["comparisons"]:
        print(f"  Tensor {comp['tensor_index']}: "
              f"max_diff={comp['max_diff']:.2e}, "
              f"mean_diff={comp['mean_diff']:.2e}, "
              f"allclose(1e-5)={comp['allclose_1e-5']}")
    
    assert result["all_match_1e-5"], "Fused Add RMSNorm 结果不匹配!"
    print("✓ Fused Add RMSNorm 测试通过!")
    
    return True


def test_rotary_embedding():
    """测试RoPE算子"""
    print("\n" + "=" * 60)
    print("测试 Rotary Embedding (RoPE)")
    print("=" * 60)
    
    from vllm_plugin.ops import MyGPURotaryEmbedding
    
    # 配置
    batch_size = 4
    seq_len = 128
    num_heads = 32
    head_dim = 128
    
    # 创建算子
    rope = MyGPURotaryEmbedding(
        head_dim=head_dim,
        max_position_embeddings=2048,
        base=10000.0,
        is_neox_style=True,
    )
    
    # 初始化缓存
    rope.initialize_cache(dtype=torch.float32)
    
    # 准备输入
    positions = torch.arange(seq_len)
    query = torch.randn(batch_size, seq_len, num_heads, head_dim, dtype=torch.float32)
    key = torch.randn(batch_size, seq_len, num_heads, head_dim, dtype=torch.float32)
    
    print(f"输入形状: positions={positions.shape}, query={query.shape}, key={key.shape}")
    
    result = rope.debug_compare(positions, query, key)
    
    print(f"结果对比 ({result['num_tensors']} 个输出张量):")
    for comp in result["comparisons"]:
        print(f"  Tensor {comp['tensor_index']} (shape={comp['shape']}): "
              f"max_diff={comp['max_diff']:.2e}, "
              f"mean_diff={comp['mean_diff']:.2e}, "
              f"allclose(1e-5)={comp['allclose_1e-5']}")
    
    assert result["all_match_1e-5"], "Rotary Embedding 结果不匹配!"
    print("✓ Rotary Embedding 测试通过!")
    
    return True


def test_paged_attention():
    """测试PagedAttention算子"""
    print("\n" + "=" * 60)
    print("测试 Paged Attention V1")
    print("=" * 60)
    
    from vllm_plugin.ops import MyGPUPagedAttention
    
    # 配置
    num_seqs = 4
    num_heads = 32
    num_kv_heads = 8  # GQA
    head_dim = 128
    block_size = 16
    max_seq_len = 256
    
    # 创建算子
    paged_attn = MyGPUPagedAttention(
        num_heads=num_heads,
        head_dim=head_dim,
        scale=1.0 / math.sqrt(head_dim),
        num_kv_heads=num_kv_heads,
        block_size=block_size,
    )
    
    # 准备KV Cache
    num_blocks = 64
    key_cache = torch.randn(
        num_blocks, block_size, num_kv_heads, head_dim, dtype=torch.float32
    )
    value_cache = torch.randn(
        num_blocks, block_size, num_kv_heads, head_dim, dtype=torch.float32
    )
    
    # 准备query和元数据
    query = torch.randn(num_seqs, num_heads, head_dim, dtype=torch.float32)
    
    # 每个sequence使用不同长度
    seq_lens = torch.tensor([64, 128, 96, 48], dtype=torch.int32)
    
    # Block tables (每个sequence指向的物理block)
    max_blocks = (max_seq_len + block_size - 1) // block_size
    block_tables = torch.zeros(num_seqs, max_blocks, dtype=torch.int32)
    for i in range(num_seqs):
        num_blocks_for_seq = (seq_lens[i].item() + block_size - 1) // block_size
        block_tables[i, :num_blocks_for_seq] = torch.arange(
            i * 10, i * 10 + num_blocks_for_seq
        )
    
    print(f"输入形状:")
    print(f"  query: {query.shape}")
    print(f"  key_cache: {key_cache.shape}")
    print(f"  value_cache: {value_cache.shape}")
    print(f"  block_tables: {block_tables.shape}")
    print(f"  seq_lens: {seq_lens}")
    
    result = paged_attn.debug_compare(
        query, key_cache, value_cache, block_tables, seq_lens
    )
    
    print(f"结果对比:")
    for comp in result["comparisons"]:
        print(f"  Output: "
              f"max_diff={comp['max_diff']:.2e}, "
              f"mean_diff={comp['mean_diff']:.2e}, "
              f"allclose(1e-3)={comp['allclose_1e-3']}")
    
    # PagedAttention由于复杂性，使用更宽松的容差
    assert result["all_match_1e-3"], "PagedAttention 结果不匹配!"
    print("✓ PagedAttention 测试通过!")
    
    return True


def test_torch_library():
    """测试torch.library注册"""
    print("\n" + "=" * 60)
    print("测试 torch.library 注册")
    print("=" * 60)
    
    from vllm_plugin.register import register_all_ops, call_rms_norm
    
    # 注册算子
    register_all_ops()
    
    # 测试调用
    x = torch.randn(2, 64, 1024)
    weight = torch.randn(1024)
    
    # 通过便捷函数调用
    output = call_rms_norm(x, weight, 1e-6)
    
    # 直接通过torch.ops调用
    output2 = torch.ops.mygpu.rms_norm(x, weight, 1e-6)
    
    print(f"输入形状: x={x.shape}")
    print(f"输出形状: {output.shape}")
    
    # 验证两种调用方式结果一致
    assert torch.allclose(output, output2), "两种调用方式结果不一致!"
    print("✓ torch.library 注册测试通过!")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "#" * 60)
    print("#" + " " * 18 + "MyGPU Ops 测试套件" + " " * 18 + "#")
    print("#" * 60)
    
    tests = [
        ("RMSNorm", test_rms_norm),
        ("Fused Add RMSNorm", test_fused_add_rms_norm),
        ("Rotary Embedding", test_rotary_embedding),
        ("PagedAttention", test_paged_attention),
        ("torch.library", test_torch_library),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success, None))
        except Exception as e:
            print(f"✗ {name} 测试失败: {e}")
            results.append((name, False, str(e)))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, error in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")
        if error:
            print(f"         Error: {error}")
    
    print("-" * 60)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
