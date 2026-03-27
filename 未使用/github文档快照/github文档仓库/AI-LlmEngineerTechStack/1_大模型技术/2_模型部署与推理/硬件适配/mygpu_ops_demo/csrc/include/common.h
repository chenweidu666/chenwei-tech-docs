/**
 * MyGPU Ops - 公共头文件
 * 
 * 这个文件包含所有 C++ 算子实现需要的公共定义、宏和工具函数。
 * 
 * 主要内容:
 * 1. PyTorch C++ API 头文件
 * 2. 输入检查宏
 * 3. 类型分发宏
 * 4. 工具函数
 */

#pragma once

// =============================================================================
// PyTorch C++ API 头文件
// =============================================================================

#include <torch/extension.h>  // 主要的 PyTorch C++ 扩展头文件
#include <ATen/ATen.h>        // ATen 张量库
#include <c10/util/Optional.h>

#include <vector>
#include <tuple>
#include <cmath>

// =============================================================================
// 版本信息
// =============================================================================

#define MYGPU_OPS_VERSION_MAJOR 0
#define MYGPU_OPS_VERSION_MINOR 1
#define MYGPU_OPS_VERSION_PATCH 0

// =============================================================================
// 输入检查宏
// =============================================================================

/**
 * MYGPU_CHECK_INPUT - 检查输入张量的基本属性
 * 
 * 使用示例:
 *     MYGPU_CHECK_INPUT(input);
 */
#define MYGPU_CHECK_INPUT(x) \
    TORCH_CHECK(x.is_contiguous(), #x " must be contiguous")

/**
 * MYGPU_CHECK_CUDA - 检查张量是否在 CUDA 设备上
 * 
 * 注意: 在 CPU 模拟模式下可以跳过这个检查
 */
#define MYGPU_CHECK_CUDA(x) \
    TORCH_CHECK(x.device().is_cuda(), #x " must be a CUDA tensor")

/**
 * MYGPU_CHECK_CPU - 检查张量是否在 CPU 上
 */
#define MYGPU_CHECK_CPU(x) \
    TORCH_CHECK(x.device().is_cpu(), #x " must be a CPU tensor")

/**
 * MYGPU_CHECK_DTYPE - 检查数据类型
 */
#define MYGPU_CHECK_DTYPE(x, dtype) \
    TORCH_CHECK(x.dtype() == dtype, #x " must have dtype " #dtype)

/**
 * MYGPU_CHECK_DIM - 检查维度数量
 */
#define MYGPU_CHECK_DIM(x, dim) \
    TORCH_CHECK(x.dim() == dim, #x " must be " #dim "-dimensional")

/**
 * MYGPU_CHECK_SHAPE - 检查形状
 */
#define MYGPU_CHECK_SHAPE(x, expected_shape) \
    TORCH_CHECK(x.sizes() == expected_shape, \
                #x " has wrong shape, expected ", expected_shape)

// =============================================================================
// 类型分发宏
// =============================================================================

/**
 * AT_DISPATCH_FLOATING_TYPES_AND_HALF - 分发浮点类型和半精度
 * 
 * 这个宏用于为不同的数据类型生成特化代码。
 * 在实际 GPU 实现中，不同精度需要不同的 kernel。
 * 
 * 使用示例:
 *     AT_DISPATCH_FLOATING_TYPES_AND_HALF(
 *         input.scalar_type(), "rms_norm_forward", [&] {
 *             // 这里 scalar_t 是具体的类型 (float, double, at::Half)
 *             auto* data = input.data_ptr<scalar_t>();
 *         });
 */

// PyTorch 已经定义了这个宏，我们直接使用即可

// =============================================================================
// 工具函数
// =============================================================================

namespace mygpu {
namespace utils {

/**
 * 计算元素数量
 */
inline int64_t numel(const std::vector<int64_t>& shape) {
    int64_t n = 1;
    for (auto s : shape) {
        n *= s;
    }
    return n;
}

/**
 * 获取张量的最后一个维度大小
 */
inline int64_t get_last_dim(const torch::Tensor& x) {
    return x.size(-1);
}

/**
 * 计算除最后一个维度外的所有元素数量
 * 用于将张量展平为 2D: [batch, hidden_size]
 */
inline int64_t get_num_rows(const torch::Tensor& x) {
    int64_t num_rows = 1;
    for (int i = 0; i < x.dim() - 1; ++i) {
        num_rows *= x.size(i);
    }
    return num_rows;
}

/**
 * 确保张量是连续的
 * 如果不是，返回连续的副本
 */
inline torch::Tensor ensure_contiguous(const torch::Tensor& x) {
    if (x.is_contiguous()) {
        return x;
    }
    return x.contiguous();
}

/**
 * 打印张量信息（用于调试）
 */
inline void print_tensor_info(const torch::Tensor& x, const std::string& name) {
    std::cout << name << ": shape=" << x.sizes() 
              << ", dtype=" << x.dtype()
              << ", device=" << x.device()
              << ", contiguous=" << x.is_contiguous()
              << std::endl;
}

}  // namespace utils
}  // namespace mygpu

// =============================================================================
// 函数声明（供 pybind11 使用）
// =============================================================================

// RMSNorm 算子
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

// Rotary Embedding 算子
std::tuple<torch::Tensor, torch::Tensor> rotary_embedding_forward(
    torch::Tensor positions,
    torch::Tensor query,
    torch::Tensor key,
    torch::Tensor cos_cache,
    torch::Tensor sin_cache,
    int64_t rotary_dim,
    bool is_neox_style
);

// PagedAttention 算子
torch::Tensor paged_attention_v1_forward(
    torch::Tensor query,
    torch::Tensor key_cache,
    torch::Tensor value_cache,
    torch::Tensor block_tables,
    torch::Tensor seq_lens,
    double scale,
    int64_t block_size
);
