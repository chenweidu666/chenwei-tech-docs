/**
 * Rotary Position Embedding (RoPE) C++ 实现
 * 
 * RoPE 是现代大模型的标准位置编码方式。
 * Llama、Qwen、Mistral 等模型都使用它。
 * 
 * 数学原理:
 *     对于位置 m 的向量 x，RoPE 应用旋转矩阵 R(m):
 *     RoPE(x, m) = R(m) @ x
 *     
 *     其中 R(m) 是一个块对角矩阵，每个 2x2 块是:
 *     [cos(m*θ), -sin(m*θ)]
 *     [sin(m*θ),  cos(m*θ)]
 * 
 * 两种风格:
 *     1. GPT-NeoX style: 前半和后半交换
 *        rotate_half([x1, x2, x3, x4]) = [-x3, -x4, x1, x2]
 *     2. GPT-J style: 奇偶位置交换
 *        rotate_half([x1, x2, x3, x4]) = [-x2, x1, -x4, x3]
 */

#include "../include/common.h"

namespace mygpu {
namespace ops {

/**
 * GPT-NeoX 风格的旋转
 * 
 * 将向量分成前后两半，交换并取负
 * [x1, x2, ..., x_n/2, x_{n/2+1}, ..., x_n] 
 * -> [-x_{n/2+1}, ..., -x_n, x1, x2, ..., x_n/2]
 */
torch::Tensor rotate_half_neox(const torch::Tensor& x) {
    const int64_t last_dim = x.size(-1);
    const int64_t half_dim = last_dim / 2;
    
    // 分割成两半
    auto x1 = x.slice(/*dim=*/-1, /*start=*/0, /*end=*/half_dim);
    auto x2 = x.slice(/*dim=*/-1, /*start=*/half_dim, /*end=*/last_dim);
    
    // 交换并取负: [-x2, x1]
    return torch::cat({-x2, x1}, /*dim=*/-1);
}

/**
 * GPT-J 风格的旋转
 * 
 * 奇偶位置交换
 * [x1, x2, x3, x4, ...] -> [-x2, x1, -x4, x3, ...]
 */
torch::Tensor rotate_half_gptj(const torch::Tensor& x) {
    // 取奇偶位置
    auto x1 = x.slice(/*dim=*/-1, /*start=*/0, /*end=*/x.size(-1), /*step=*/2);  // 偶数位置
    auto x2 = x.slice(/*dim=*/-1, /*start=*/1, /*end=*/x.size(-1), /*step=*/2);  // 奇数位置
    
    // 交错合并: [-x2, x1]
    auto rotated = torch::stack({-x2, x1}, /*dim=*/-1);
    return rotated.flatten(/*start_dim=*/-2);
}

/**
 * 应用 RoPE 到单个张量
 * 
 * @param x            输入张量 [batch, seq, heads, dim]
 * @param cos          cos 值 [1, seq, 1, dim] 或 [seq, 1, dim]
 * @param sin          sin 值 [1, seq, 1, dim] 或 [seq, 1, dim]
 * @param rotary_dim   旋转的维度数
 * @param is_neox      是否使用 NeoX 风格
 */
torch::Tensor apply_rotary_emb(
    const torch::Tensor& x,
    const torch::Tensor& cos,
    const torch::Tensor& sin,
    int64_t rotary_dim,
    bool is_neox
) {
    // 分离旋转部分和非旋转部分
    auto x_rot = x.slice(/*dim=*/-1, /*start=*/0, /*end=*/rotary_dim);
    auto x_pass = x.slice(/*dim=*/-1, /*start=*/rotary_dim, /*end=*/x.size(-1));
    
    // 应用旋转
    torch::Tensor rotated;
    if (is_neox) {
        rotated = rotate_half_neox(x_rot);
    } else {
        rotated = rotate_half_gptj(x_rot);
    }
    
    // 旋转公式: x * cos + rotate_half(x) * sin
    auto x_rotated = x_rot * cos + rotated * sin;
    
    // 拼接旋转和非旋转部分
    if (x_pass.size(-1) > 0) {
        return torch::cat({x_rotated, x_pass}, /*dim=*/-1);
    }
    return x_rotated;
}

/**
 * Rotary Embedding 前向传播 - CPU 实现
 * 
 * @param positions    位置索引 [seq_len]
 * @param query        Query 张量 [batch, seq_len, num_heads, head_dim]
 * @param key          Key 张量 [batch, seq_len, num_kv_heads, head_dim]
 * @param cos_cache    预计算的 cos 缓存 [max_len, rotary_dim]
 * @param sin_cache    预计算的 sin 缓存 [max_len, rotary_dim]
 * @param rotary_dim   旋转维度
 * @param is_neox_style 是否使用 GPT-NeoX 风格
 * @return             (rotated_query, rotated_key)
 */
std::tuple<torch::Tensor, torch::Tensor> rotary_embedding_forward_cpu(
    torch::Tensor positions,
    torch::Tensor query,
    torch::Tensor key,
    torch::Tensor cos_cache,
    torch::Tensor sin_cache,
    int64_t rotary_dim,
    bool is_neox_style
) {
    // ========== 1. 输入检查 ==========
    MYGPU_CHECK_INPUT(positions);
    MYGPU_CHECK_INPUT(query);
    MYGPU_CHECK_INPUT(key);
    MYGPU_CHECK_INPUT(cos_cache);
    MYGPU_CHECK_INPUT(sin_cache);
    
    // 如果没有指定 rotary_dim，使用 head_dim
    if (rotary_dim <= 0) {
        rotary_dim = query.size(-1);
    }
    
    // ========== 2. 获取 cos/sin 值 ==========
    // 使用 index_select 根据 positions 选择对应的 cos/sin
    auto cos = torch::index_select(cos_cache, /*dim=*/0, positions);
    auto sin = torch::index_select(sin_cache, /*dim=*/0, positions);
    
    // ========== 3. 调整 cos/sin 形状以支持广播 ==========
    // positions: [seq_len] -> cos/sin: [seq_len, rotary_dim]
    // query: [batch, seq_len, num_heads, head_dim]
    // 需要将 cos/sin 扩展为 [1, seq_len, 1, rotary_dim]
    
    if (query.dim() == 4) {
        // [seq_len, rotary_dim] -> [1, seq_len, 1, rotary_dim]
        cos = cos.unsqueeze(0).unsqueeze(2);
        sin = sin.unsqueeze(0).unsqueeze(2);
    } else if (query.dim() == 3) {
        // [seq_len, rotary_dim] -> [seq_len, 1, rotary_dim]
        cos = cos.unsqueeze(1);
        sin = sin.unsqueeze(1);
    }
    
    // 确保 cos/sin 的最后一维与 rotary_dim 匹配
    if (cos.size(-1) > rotary_dim) {
        cos = cos.slice(/*dim=*/-1, /*start=*/0, /*end=*/rotary_dim);
        sin = sin.slice(/*dim=*/-1, /*start=*/0, /*end=*/rotary_dim);
    }
    
    // ========== 4. 应用 RoPE ==========
    auto query_rotated = apply_rotary_emb(query, cos, sin, rotary_dim, is_neox_style);
    auto key_rotated = apply_rotary_emb(key, cos, sin, rotary_dim, is_neox_style);
    
    return std::make_tuple(query_rotated, key_rotated);
}

}  // namespace ops
}  // namespace mygpu


// =============================================================================
// 导出函数
// =============================================================================

std::tuple<torch::Tensor, torch::Tensor> rotary_embedding_forward(
    torch::Tensor positions,
    torch::Tensor query,
    torch::Tensor key,
    torch::Tensor cos_cache,
    torch::Tensor sin_cache,
    int64_t rotary_dim,
    bool is_neox_style
) {
    // 目前只有 CPU 实现
    if (query.device().is_cpu()) {
        return mygpu::ops::rotary_embedding_forward_cpu(
            positions, query, key, cos_cache, sin_cache, rotary_dim, is_neox_style
        );
    }
    
    // CUDA 设备回退到 CPU
    TORCH_WARN("CUDA implementation not available, falling back to CPU");
    auto [q_out, k_out] = mygpu::ops::rotary_embedding_forward_cpu(
        positions.cpu(),
        query.cpu(),
        key.cpu(),
        cos_cache.cpu(),
        sin_cache.cpu(),
        rotary_dim,
        is_neox_style
    );
    return std::make_tuple(
        q_out.to(query.device()),
        k_out.to(query.device())
    );
}
