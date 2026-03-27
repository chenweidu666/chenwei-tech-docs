/**
 * MyGPU Ops - pybind11 模块入口
 * 
 * 这个文件定义了 Python 模块的入口点，使用 pybind11 将 C++ 函数暴露给 Python。
 * 
 * pybind11 核心概念:
 *     - PYBIND11_MODULE: 定义模块入口
 *     - m.def(): 绑定 C++ 函数到 Python
 *     - py::arg(): 定义参数名和默认值
 * 
 * 编译后，Python 可以这样调用:
 *     from mygpu_ops._C import rms_norm
 *     output = rms_norm(input, weight, eps)
 */

#include <torch/extension.h>

// =============================================================================
// 函数声明（定义在各个 ops/*.cpp 文件中）
// =============================================================================

// RMSNorm
torch::Tensor rms_norm_forward(
    torch::Tensor input,
    torch::Tensor weight,
    double eps
);

std::tuple<torch::Tensor, torch::Tensor> fused_add_rms_norm_forward(
    torch::Tensor input,
    torch::Tensor residual,
    torch::Tensor weight,
    double eps
);

// Rotary Embedding
std::tuple<torch::Tensor, torch::Tensor> rotary_embedding_forward(
    torch::Tensor positions,
    torch::Tensor query,
    torch::Tensor key,
    torch::Tensor cos_cache,
    torch::Tensor sin_cache,
    int64_t rotary_dim,
    bool is_neox_style
);

// Attention
torch::Tensor paged_attention_v1_forward(
    torch::Tensor query,
    torch::Tensor key_cache,
    torch::Tensor value_cache,
    torch::Tensor block_tables,
    torch::Tensor seq_lens,
    double scale,
    int64_t block_size
);

torch::Tensor standard_attention_forward(
    torch::Tensor query,
    torch::Tensor key,
    torch::Tensor value,
    double scale
);


// =============================================================================
// pybind11 模块定义
// =============================================================================

/**
 * PYBIND11_MODULE 宏说明:
 *     - TORCH_EXTENSION_NAME: 由 setup.py 中的 name 参数自动定义
 *     - m: 模块对象，用于添加函数和类
 */
PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.doc() = R"doc(
MyGPU Ops - 自定义 GPU 算子库 (C++ 实现)

这是一个演示如何为国产 GPU 实现自定义算子库的项目。
包含以下算子:
    - rms_norm: RMSNorm 归一化
    - fused_add_rms_norm: 融合残差加法的 RMSNorm
    - rotary_embedding: 旋转位置编码 (RoPE)
    - paged_attention_v1: PagedAttention (vLLM 核心算子)
    - standard_attention: 标准 Multi-Head Attention

使用示例:
    >>> import torch
    >>> from mygpu_ops._C import rms_norm
    >>> x = torch.randn(2, 4, 128)
    >>> weight = torch.ones(128)
    >>> output = rms_norm(x, weight, 1e-6)
)doc";

    // =========================================================================
    // RMSNorm 算子
    // =========================================================================
    
    m.def(
        "rms_norm",
        &rms_norm_forward,
        R"doc(
RMSNorm 前向传播

Args:
    input: 输入张量，shape [..., hidden_size]
    weight: 归一化权重，shape [hidden_size]
    eps: 防止除零的小常数 (默认 1e-6)

Returns:
    归一化后的张量，shape 同 input

公式:
    output = input / sqrt(mean(input^2) + eps) * weight
)doc",
        py::arg("input"),
        py::arg("weight"),
        py::arg("eps") = 1e-6
    );

    m.def(
        "fused_add_rms_norm",
        &fused_add_rms_norm_forward,
        R"doc(
融合残差加法的 RMSNorm

Args:
    input: 输入张量
    residual: 残差张量
    weight: 归一化权重
    eps: 防止除零的小常数

Returns:
    tuple(output, new_residual)
    - output: 归一化后的输出
    - new_residual: 新的残差 (= input + residual)

融合优化原理:
    非融合版本需要 5 次显存访问，融合版本只需 4 次。
    理论性能提升约 20%。
)doc",
        py::arg("input"),
        py::arg("residual"),
        py::arg("weight"),
        py::arg("eps") = 1e-6
    );

    // =========================================================================
    // Rotary Embedding 算子
    // =========================================================================
    
    m.def(
        "rotary_embedding",
        &rotary_embedding_forward,
        R"doc(
旋转位置编码 (RoPE) 前向传播

Args:
    positions: 位置索引，shape [seq_len]
    query: Query 张量，shape [batch, seq_len, num_heads, head_dim]
    key: Key 张量，shape [batch, seq_len, num_kv_heads, head_dim]
    cos_cache: 预计算的 cos 缓存，shape [max_len, rotary_dim]
    sin_cache: 预计算的 sin 缓存，shape [max_len, rotary_dim]
    rotary_dim: 应用旋转的维度数 (默认为 head_dim)
    is_neox_style: 是否使用 GPT-NeoX 风格 (默认 True)

Returns:
    tuple(rotated_query, rotated_key)

两种风格:
    - NeoX style: 前后半分割旋转
    - GPT-J style: 奇偶位置交替旋转
)doc",
        py::arg("positions"),
        py::arg("query"),
        py::arg("key"),
        py::arg("cos_cache"),
        py::arg("sin_cache"),
        py::arg("rotary_dim") = -1,
        py::arg("is_neox_style") = true
    );

    // =========================================================================
    // Attention 算子
    // =========================================================================
    
    m.def(
        "paged_attention_v1",
        &paged_attention_v1_forward,
        R"doc(
PagedAttention V1 前向传播 (vLLM 核心算子)

Args:
    query: Query 张量，shape [num_seqs, num_heads, head_dim]
    key_cache: Key 缓存，shape [num_blocks, block_size, num_kv_heads, head_dim]
    value_cache: Value 缓存，shape [num_blocks, block_size, num_kv_heads, head_dim]
    block_tables: 页表，shape [num_seqs, max_blocks]
    seq_lens: 每个序列的长度，shape [num_seqs]
    scale: 缩放因子 (通常是 1/sqrt(head_dim))
    block_size: 每个块的大小

Returns:
    输出张量，shape [num_seqs, num_heads, head_dim]

PagedAttention 核心思想:
    类似操作系统的虚拟内存，使用页表管理 KV Cache。
    消除内存碎片，支持动态序列长度。
)doc",
        py::arg("query"),
        py::arg("key_cache"),
        py::arg("value_cache"),
        py::arg("block_tables"),
        py::arg("seq_lens"),
        py::arg("scale"),
        py::arg("block_size")
    );

    m.def(
        "standard_attention",
        &standard_attention_forward,
        R"doc(
标准 Multi-Head Attention 前向传播

Args:
    query: Query 张量，shape [batch, seq_len, num_heads, head_dim]
    key: Key 张量，shape [batch, seq_len, num_kv_heads, head_dim]
    value: Value 张量，shape [batch, seq_len, num_kv_heads, head_dim]
    scale: 缩放因子

Returns:
    输出张量，shape [batch, seq_len, num_heads, head_dim]

这是标准的 attention 实现，用于 prefill 阶段。
支持 GQA (Grouped Query Attention)。
)doc",
        py::arg("query"),
        py::arg("key"),
        py::arg("value"),
        py::arg("scale")
    );

    // =========================================================================
    // 版本信息
    // =========================================================================
    
    m.attr("__version__") = "0.1.0";
    m.attr("__author__") = "MyGPU Team";
}
