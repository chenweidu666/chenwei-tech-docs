#!/usr/bin/env python3
"""
算子性能基准测试

这个脚本对比native实现和oot实现的性能差异。
虽然在这个模拟环境中两者性能相近，
但这展示了如何进行性能测试和对比。

运行方法:
    cd mygpu_ops_demo
    python examples/benchmark.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import torch
import time
import math
from typing import Callable, Dict, Any, List
from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    name: str
    num_runs: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    throughput: float  # elements/ms


def benchmark_function(
    func: Callable,
    args: tuple,
    kwargs: dict = None,
    num_warmup: int = 5,
    num_runs: int = 100,
    name: str = "function",
) -> BenchmarkResult:
    """
    对函数进行基准测试
    
    Args:
        func: 要测试的函数
        args: 位置参数
        kwargs: 关键字参数
        num_warmup: 预热次数
        num_runs: 正式测试次数
        name: 测试名称
    
    Returns:
        BenchmarkResult
    """
    kwargs = kwargs or {}
    
    # 预热
    for _ in range(num_warmup):
        _ = func(*args, **kwargs)
    
    # 同步（如果有CUDA）
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    
    # 正式测试
    times = []
    for _ in range(num_runs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # 转换为ms
    
    # 计算统计
    total_time = sum(times)
    avg_time = total_time / num_runs
    min_time = min(times)
    max_time = max(times)
    
    # 计算吞吐量（假设第一个参数是输入tensor）
    if isinstance(args[0], torch.Tensor):
        num_elements = args[0].numel()
        throughput = num_elements / avg_time
    else:
        throughput = 0
    
    return BenchmarkResult(
        name=name,
        num_runs=num_runs,
        total_time_ms=total_time,
        avg_time_ms=avg_time,
        min_time_ms=min_time,
        max_time_ms=max_time,
        throughput=throughput,
    )


def print_benchmark_result(result: BenchmarkResult, indent: int = 0):
    """打印基准测试结果"""
    prefix = " " * indent
    print(f"{prefix}{result.name}:")
    print(f"{prefix}  运行次数: {result.num_runs}")
    print(f"{prefix}  平均时间: {result.avg_time_ms:.4f} ms")
    print(f"{prefix}  最小时间: {result.min_time_ms:.4f} ms")
    print(f"{prefix}  最大时间: {result.max_time_ms:.4f} ms")
    if result.throughput > 0:
        print(f"{prefix}  吞吐量: {result.throughput/1e6:.2f} M elements/ms")


def compare_results(native: BenchmarkResult, oot: BenchmarkResult):
    """对比native和oot结果"""
    speedup = native.avg_time_ms / oot.avg_time_ms
    print(f"\n对比结果:")
    print(f"  Native平均时间: {native.avg_time_ms:.4f} ms")
    print(f"  OOT平均时间: {oot.avg_time_ms:.4f} ms")
    print(f"  加速比: {speedup:.2f}x")
    if speedup > 1:
        print(f"  OOT 比 Native 快 {(speedup-1)*100:.1f}%")
    else:
        print(f"  OOT 比 Native 慢 {(1-speedup)*100:.1f}%")


def benchmark_rms_norm():
    """RMSNorm性能测试"""
    print("\n" + "=" * 60)
    print("RMSNorm 性能测试")
    print("=" * 60)
    
    from vllm_plugin.ops import MyGPURMSNorm
    
    # 测试不同规模
    configs = [
        {"batch": 1, "seq": 128, "hidden": 4096, "name": "Small"},
        {"batch": 4, "seq": 512, "hidden": 4096, "name": "Medium"},
        {"batch": 8, "seq": 1024, "hidden": 4096, "name": "Large"},
        {"batch": 16, "seq": 2048, "hidden": 4096, "name": "XLarge"},
    ]
    
    for config in configs:
        print(f"\n配置: {config['name']} "
              f"(batch={config['batch']}, seq={config['seq']}, hidden={config['hidden']})")
        print("-" * 40)
        
        # 准备数据
        x = torch.randn(config['batch'], config['seq'], config['hidden'])
        weight = torch.randn(config['hidden'])
        
        # 创建算子
        rms_norm = MyGPURMSNorm(hidden_size=config['hidden'], eps=1e-6)
        
        # 测试native
        native_result = benchmark_function(
            rms_norm.forward_native,
            (x, weight),
            num_runs=50,
            name="forward_native",
        )
        print_benchmark_result(native_result, indent=2)
        
        # 测试oot
        oot_result = benchmark_function(
            rms_norm.forward_oot,
            (x, weight),
            num_runs=50,
            name="forward_oot",
        )
        print_benchmark_result(oot_result, indent=2)
        
        compare_results(native_result, oot_result)


def benchmark_fused_add_rms_norm():
    """Fused Add RMSNorm性能测试"""
    print("\n" + "=" * 60)
    print("Fused Add RMSNorm 性能测试")
    print("=" * 60)
    
    from vllm_plugin.ops import MyGPUFusedAddRMSNorm
    
    # 准备数据
    batch, seq, hidden = 8, 1024, 4096
    x = torch.randn(batch, seq, hidden)
    residual = torch.randn(batch, seq, hidden)
    weight = torch.randn(hidden)
    
    print(f"配置: batch={batch}, seq={seq}, hidden={hidden}")
    print("-" * 40)
    
    # 创建算子
    fused_norm = MyGPUFusedAddRMSNorm(hidden_size=hidden, eps=1e-6)
    
    # 测试native
    native_result = benchmark_function(
        fused_norm.forward_native,
        (x, residual, weight),
        num_runs=50,
        name="forward_native",
    )
    print_benchmark_result(native_result, indent=2)
    
    # 测试oot
    oot_result = benchmark_function(
        fused_norm.forward_oot,
        (x, residual, weight),
        num_runs=50,
        name="forward_oot",
    )
    print_benchmark_result(oot_result, indent=2)
    
    compare_results(native_result, oot_result)
    
    # 与非融合版本对比
    print("\n与非融合版本对比:")
    
    def non_fused(x, residual, weight, eps=1e-6):
        """非融合版本"""
        hidden = x + residual
        variance = hidden.pow(2).mean(dim=-1, keepdim=True)
        hidden_normed = hidden * torch.rsqrt(variance + eps)
        return hidden_normed * weight, hidden
    
    non_fused_result = benchmark_function(
        non_fused,
        (x, residual, weight),
        num_runs=50,
        name="non_fused",
    )
    print_benchmark_result(non_fused_result, indent=2)
    
    print(f"\n融合优化收益: {non_fused_result.avg_time_ms / oot_result.avg_time_ms:.2f}x")


def benchmark_rotary_embedding():
    """RoPE性能测试"""
    print("\n" + "=" * 60)
    print("Rotary Embedding 性能测试")
    print("=" * 60)
    
    from vllm_plugin.ops import MyGPURotaryEmbedding
    
    # 准备数据
    batch, seq, num_heads, head_dim = 8, 1024, 32, 128
    
    positions = torch.arange(seq)
    query = torch.randn(batch, seq, num_heads, head_dim)
    key = torch.randn(batch, seq, num_heads, head_dim)
    
    print(f"配置: batch={batch}, seq={seq}, heads={num_heads}, head_dim={head_dim}")
    print("-" * 40)
    
    # 创建算子
    rope = MyGPURotaryEmbedding(head_dim=head_dim, max_position_embeddings=2048)
    rope.initialize_cache(dtype=torch.float32)
    
    # 测试native
    native_result = benchmark_function(
        rope.forward_native,
        (positions, query, key),
        num_runs=50,
        name="forward_native",
    )
    print_benchmark_result(native_result, indent=2)
    
    # 测试oot
    oot_result = benchmark_function(
        rope.forward_oot,
        (positions, query, key),
        num_runs=50,
        name="forward_oot",
    )
    print_benchmark_result(oot_result, indent=2)
    
    compare_results(native_result, oot_result)


def benchmark_paged_attention():
    """PagedAttention性能测试"""
    print("\n" + "=" * 60)
    print("PagedAttention 性能测试")
    print("=" * 60)
    
    from vllm_plugin.ops import MyGPUPagedAttention
    
    # 配置
    num_seqs = 8
    num_heads = 32
    num_kv_heads = 8
    head_dim = 128
    block_size = 16
    num_blocks = 256
    
    print(f"配置: seqs={num_seqs}, heads={num_heads}, "
          f"kv_heads={num_kv_heads}, head_dim={head_dim}")
    print("-" * 40)
    
    # 准备数据
    query = torch.randn(num_seqs, num_heads, head_dim)
    key_cache = torch.randn(num_blocks, block_size, num_kv_heads, head_dim)
    value_cache = torch.randn(num_blocks, block_size, num_kv_heads, head_dim)
    seq_lens = torch.randint(64, 256, (num_seqs,), dtype=torch.int32)
    
    max_blocks_per_seq = (256 + block_size - 1) // block_size
    block_tables = torch.zeros(num_seqs, max_blocks_per_seq, dtype=torch.int32)
    for i in range(num_seqs):
        n_blocks = (seq_lens[i].item() + block_size - 1) // block_size
        block_tables[i, :n_blocks] = torch.randint(0, num_blocks, (n_blocks,))
    
    # 创建算子
    paged_attn = MyGPUPagedAttention(
        num_heads=num_heads,
        head_dim=head_dim,
        scale=1.0 / math.sqrt(head_dim),
        num_kv_heads=num_kv_heads,
        block_size=block_size,
    )
    
    # 测试native
    native_result = benchmark_function(
        paged_attn.forward_native,
        (query, key_cache, value_cache, block_tables, seq_lens),
        num_runs=20,  # PagedAttention较慢，减少运行次数
        name="forward_native",
    )
    print_benchmark_result(native_result, indent=2)
    
    # 测试oot
    oot_result = benchmark_function(
        paged_attn.forward_oot,
        (query, key_cache, value_cache, block_tables, seq_lens),
        num_runs=20,
        name="forward_oot",
    )
    print_benchmark_result(oot_result, indent=2)
    
    compare_results(native_result, oot_result)


def benchmark_kernel_stats():
    """测试kernel统计功能"""
    print("\n" + "=" * 60)
    print("Kernel 统计信息")
    print("=" * 60)
    
    import mygpu_ops
    
    # 重置统计
    mygpu_ops.reset_kernel_stats()
    
    # 运行一些操作
    x = torch.randn(4, 128, 4096)
    weight = torch.randn(4096)
    
    for _ in range(10):
        _ = mygpu_ops.rms_norm(x, weight, 1e-6)
    
    for _ in range(5):
        residual = torch.randn_like(x)
        _ = mygpu_ops.fused_add_rms_norm(x, residual, weight, 1e-6)
    
    # 获取统计
    stats = mygpu_ops.get_kernel_stats()
    
    print("\nKernel调用统计:")
    for kernel_name, kernel_stats in stats.items():
        if kernel_stats['calls'] > 0:
            print(f"  {kernel_name}:")
            print(f"    调用次数: {kernel_stats['calls']}")
            print(f"    总时间: {kernel_stats['total_time_ms']:.4f} ms")
            print(f"    平均时间: {kernel_stats.get('avg_time_ms', 0):.4f} ms")


def run_all_benchmarks():
    """运行所有基准测试"""
    print("\n" + "#" * 60)
    print("#" + " " * 15 + "MyGPU Ops 性能基准测试" + " " * 15 + "#")
    print("#" * 60)
    
    benchmark_rms_norm()
    benchmark_fused_add_rms_norm()
    benchmark_rotary_embedding()
    benchmark_paged_attention()
    benchmark_kernel_stats()
    
    print("\n" + "=" * 60)
    print("基准测试完成!")
    print("=" * 60)
    
    print("""
注意：
1. 在这个模拟环境中，native和oot实现底层相同，性能接近
2. 在真实的国产GPU环境中，oot实现会调用优化的GPU kernel
3. 预期的性能提升取决于具体的硬件和kernel优化程度
""")


if __name__ == "__main__":
    run_all_benchmarks()
