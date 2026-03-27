/**
 * RMSNorm C++ 实现
 * 
 * RMS LayerNorm 是大模型中最常用的归一化算子。
 * Llama、Qwen 等模型都使用它代替标准 LayerNorm。
 * 
 * 数学公式:
 *     RMSNorm(x) = x / sqrt(mean(x^2) + eps) * weight
 * 
 * 与标准 LayerNorm 的区别:
 *     - LayerNorm: (x - mean(x)) / sqrt(var(x) + eps) * weight + bias
 *     - RMSNorm: x / sqrt(mean(x^2) + eps) * weight
 *     - RMSNorm 省略了减均值和 bias，计算更快
 */

#include "../include/common.h"

namespace mygpu {
namespace ops {

/**
 * RMSNorm 前向传播 - CPU 实现
 * 
 * 这是 CPU 版本的实现，使用 ATen 操作。
 * 在实际的 GPU 实现中，这些操作会被替换为优化的 CUDA kernel。
 * 
 * @param input   输入张量, shape [..., hidden_size]
 * @param weight  归一化权重, shape [hidden_size]
 * @param eps     防止除零的小常数
 * @return        归一化后的张量, shape [..., hidden_size]
 */
torch::Tensor rms_norm_forward_cpu(
    torch::Tensor input,
    torch::Tensor weight,
    double eps
) {
    // ========== 1. 输入检查 ==========
    MYGPU_CHECK_INPUT(input);
    MYGPU_CHECK_INPUT(weight);
    
    TORCH_CHECK(input.dim() >= 2, 
                "input must have at least 2 dimensions, got ", input.dim());
    
    const int64_t hidden_size = input.size(-1);
    TORCH_CHECK(weight.size(0) == hidden_size,
                "weight size must match hidden_size, expected ", hidden_size,
                " got ", weight.size(0));
    
    // ========== 2. 保存原始形状并展平 ==========
    // 将 [..., hidden_size] 展平为 [num_rows, hidden_size]
    auto original_shape = input.sizes().vec();
    const int64_t num_rows = utils::get_num_rows(input);
    
    auto input_2d = input.view({num_rows, hidden_size});
    
    // ========== 3. 计算 RMSNorm ==========
    // 在实际 GPU 实现中，这三步会融合成一个 kernel
    
    // Step 1: 计算 variance = mean(x^2)
    // 对最后一个维度求平方和的均值
    auto variance = input_2d.pow(2).mean(/*dim=*/-1, /*keepdim=*/true);
    
    // Step 2: 计算 rsqrt(variance + eps)
    auto rsqrt_var = torch::rsqrt(variance + eps);
    
    // Step 3: 归一化并乘以权重
    auto output = input_2d * rsqrt_var * weight;
    
    // ========== 4. 恢复原始形状 ==========
    return output.view(original_shape);
}


/**
 * Fused Add RMSNorm 前向传播 - CPU 实现
 * 
 * 融合残差加法和 RMSNorm，减少显存访问次数。
 * 
 * 公式:
 *     hidden = input + residual
 *     output = RMSNorm(hidden) * weight
 * 
 * 融合优化原理:
 *     - 非融合: 读input + 读residual + 写sum + 读sum + 写output = 5次显存访问
 *     - 融合: 读input + 读residual + 写output + 写residual = 4次显存访问
 *     - 理论性能提升 ~20%
 * 
 * @param input    输入张量
 * @param residual 残差张量
 * @param weight   权重张量
 * @param eps      防止除零
 * @return         (output, new_residual)
 */
std::tuple<torch::Tensor, torch::Tensor> fused_add_rms_norm_forward_cpu(
    torch::Tensor input,
    torch::Tensor residual,
    torch::Tensor weight,
    double eps
) {
    // ========== 1. 输入检查 ==========
    MYGPU_CHECK_INPUT(input);
    MYGPU_CHECK_INPUT(residual);
    MYGPU_CHECK_INPUT(weight);
    
    TORCH_CHECK(input.sizes() == residual.sizes(),
                "input and residual must have the same shape");
    
    const int64_t hidden_size = input.size(-1);
    TORCH_CHECK(weight.size(0) == hidden_size,
                "weight size must match hidden_size");
    
    // ========== 2. 展平 ==========
    auto original_shape = input.sizes().vec();
    const int64_t num_rows = utils::get_num_rows(input);
    
    auto input_2d = input.view({num_rows, hidden_size});
    auto residual_2d = residual.view({num_rows, hidden_size});
    
    // ========== 3. 融合计算 ==========
    // 在实际 GPU 实现中，这些操作在一个 kernel 中完成
    
    // Step 1: 残差加法
    auto hidden = input_2d + residual_2d;
    
    // Step 2: 保存新的残差（用于下一层）
    // 注意：这里使用 clone() 确保返回独立的张量
    auto new_residual = hidden.clone();
    
    // Step 3: RMSNorm
    auto variance = hidden.pow(2).mean(/*dim=*/-1, /*keepdim=*/true);
    auto hidden_normed = hidden * torch::rsqrt(variance + eps);
    auto output = hidden_normed * weight;
    
    // ========== 4. 恢复形状 ==========
    return std::make_tuple(
        output.view(original_shape),
        new_residual.view(original_shape)
    );
}

}  // namespace ops
}  // namespace mygpu


// =============================================================================
// 导出函数（供 pybind11 绑定使用）
// =============================================================================

torch::Tensor rms_norm_forward(
    torch::Tensor input,
    torch::Tensor weight,
    double eps
) {
    // 根据设备选择实现
    // 目前只有 CPU 实现，未来可以添加 CUDA 实现
    if (input.device().is_cpu()) {
        return mygpu::ops::rms_norm_forward_cpu(input, weight, eps);
    }
    
    // 对于 CUDA 设备，暂时回退到 CPU 计算
    // 在实际实现中，这里会调用 CUDA kernel
    TORCH_WARN("CUDA implementation not available, falling back to CPU");
    auto cpu_input = input.cpu();
    auto cpu_weight = weight.cpu();
    auto cpu_output = mygpu::ops::rms_norm_forward_cpu(cpu_input, cpu_weight, eps);
    return cpu_output.to(input.device());
}

std::tuple<torch::Tensor, torch::Tensor> fused_add_rms_norm_forward(
    torch::Tensor input,
    torch::Tensor residual,
    torch::Tensor weight,
    double eps
) {
    if (input.device().is_cpu()) {
        return mygpu::ops::fused_add_rms_norm_forward_cpu(input, residual, weight, eps);
    }
    
    TORCH_WARN("CUDA implementation not available, falling back to CPU");
    auto cpu_input = input.cpu();
    auto cpu_residual = residual.cpu();
    auto cpu_weight = weight.cpu();
    auto [cpu_output, cpu_new_residual] = 
        mygpu::ops::fused_add_rms_norm_forward_cpu(cpu_input, cpu_residual, cpu_weight, eps);
    return std::make_tuple(
        cpu_output.to(input.device()),
        cpu_new_residual.to(input.device())
    );
}
