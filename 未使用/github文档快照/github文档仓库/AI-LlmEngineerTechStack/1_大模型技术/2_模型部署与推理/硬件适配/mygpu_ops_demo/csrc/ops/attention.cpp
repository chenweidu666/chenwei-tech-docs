/**
 * PagedAttention C++ 实现
 * 
 * PagedAttention 是 vLLM 的核心算子，实现分页式 KV Cache 管理。
 * 它解决了 LLM 推理中的内存碎片化问题，是 vLLM 高吞吐量的关键。
 * 
 * 核心思想 (类比操作系统虚拟内存):
 *     - 物理块: 固定大小的连续内存块，存储 KV Cache
 *     - 页表: 记录每个序列使用哪些物理块
 *     - 非连续存储: 一个序列的 KV Cache 可以存在多个不连续的物理块中
 * 
 * 优点:
 *     1. 消除内存碎片
 *     2. 支持动态序列长度
 *     3. 高效的 continuous batching
 */

#include "../include/common.h"

namespace mygpu {
namespace ops {

/**
 * 标准 Scaled Dot-Product Attention (参考实现)
 * 
 * 公式: softmax(Q @ K^T / sqrt(d)) @ V
 */
torch::Tensor scaled_dot_product_attention(
    torch::Tensor query,   // [batch, num_heads, seq_len, head_dim]
    torch::Tensor key,     // [batch, num_heads, kv_len, head_dim]
    torch::Tensor value,   // [batch, num_heads, kv_len, head_dim]
    double scale
) {
    // Q @ K^T: [batch, heads, seq_len, kv_len]
    auto scores = torch::matmul(query, key.transpose(-2, -1)) * scale;
    
    // Softmax
    auto attn_weights = torch::softmax(scores, /*dim=*/-1);
    
    // Attention @ V: [batch, heads, seq_len, head_dim]
    return torch::matmul(attn_weights, value);
}

/**
 * PagedAttention V1 前向传播 - CPU 实现
 * 
 * 这是简化的 CPU 参考实现，用于理解算法原理。
 * 实际的 GPU 实现会使用优化的 CUDA kernel。
 * 
 * @param query         Query 张量 [num_seqs, num_heads, head_dim]
 * @param key_cache     Key 缓存 [num_blocks, block_size, num_kv_heads, head_dim]
 * @param value_cache   Value 缓存 [num_blocks, block_size, num_kv_heads, head_dim]
 * @param block_tables  页表 [num_seqs, max_blocks]
 * @param seq_lens      每个序列的长度 [num_seqs]
 * @param scale         缩放因子 (通常是 1/sqrt(head_dim))
 * @param block_size    每个块的大小
 * @return              输出张量 [num_seqs, num_heads, head_dim]
 */
torch::Tensor paged_attention_v1_forward_cpu(
    torch::Tensor query,
    torch::Tensor key_cache,
    torch::Tensor value_cache,
    torch::Tensor block_tables,
    torch::Tensor seq_lens,
    double scale,
    int64_t block_size
) {
    // ========== 1. 输入检查 ==========
    MYGPU_CHECK_INPUT(query);
    MYGPU_CHECK_INPUT(key_cache);
    MYGPU_CHECK_INPUT(value_cache);
    
    const int64_t num_seqs = query.size(0);
    const int64_t num_heads = query.size(1);
    const int64_t head_dim = query.size(2);
    const int64_t num_kv_heads = key_cache.size(2);
    
    // 计算每个 head group 对应的 kv_head (GQA 支持)
    const int64_t num_queries_per_kv = num_heads / num_kv_heads;
    
    // 输出张量
    auto output = torch::zeros_like(query);
    
    // ========== 2. 逐序列处理 ==========
    // 在 GPU 实现中，这会并行处理
    for (int64_t seq_idx = 0; seq_idx < num_seqs; ++seq_idx) {
        const int64_t seq_len = seq_lens[seq_idx].item<int64_t>();
        
        if (seq_len == 0) {
            continue;
        }
        
        // 计算需要的块数
        const int64_t num_blocks_needed = (seq_len + block_size - 1) / block_size;
        
        // 收集该序列的所有 Key 和 Value
        std::vector<torch::Tensor> keys_list;
        std::vector<torch::Tensor> values_list;
        
        int64_t tokens_collected = 0;
        for (int64_t block_idx = 0; block_idx < num_blocks_needed; ++block_idx) {
            // 从页表获取物理块索引
            const int64_t physical_block_idx = 
                block_tables[seq_idx][block_idx].item<int64_t>();
            
            // 计算这个块中实际的 token 数
            const int64_t tokens_in_block = 
                std::min(block_size, seq_len - tokens_collected);
            
            // 获取这个块的 key 和 value
            // key_cache: [num_blocks, block_size, num_kv_heads, head_dim]
            auto key_block = key_cache[physical_block_idx].slice(
                /*dim=*/0, /*start=*/0, /*end=*/tokens_in_block);
            auto value_block = value_cache[physical_block_idx].slice(
                /*dim=*/0, /*start=*/0, /*end=*/tokens_in_block);
            
            keys_list.push_back(key_block);
            values_list.push_back(value_block);
            
            tokens_collected += tokens_in_block;
        }
        
        // 拼接所有块
        // keys: [seq_len, num_kv_heads, head_dim]
        auto keys = torch::cat(keys_list, /*dim=*/0);
        auto values = torch::cat(values_list, /*dim=*/0);
        
        // ========== 3. 计算 Attention ==========
        // query for this seq: [num_heads, head_dim] -> [1, num_heads, 1, head_dim]
        auto q = query[seq_idx].unsqueeze(0).unsqueeze(2);
        
        // keys: [seq_len, num_kv_heads, head_dim] -> [1, num_kv_heads, seq_len, head_dim]
        auto k = keys.permute({1, 0, 2}).unsqueeze(0);
        auto v = values.permute({1, 0, 2}).unsqueeze(0);
        
        // 处理 GQA: 扩展 KV heads 以匹配 Q heads
        if (num_queries_per_kv > 1) {
            k = k.repeat_interleave(num_queries_per_kv, /*dim=*/1);
            v = v.repeat_interleave(num_queries_per_kv, /*dim=*/1);
        }
        
        // Scaled Dot-Product Attention
        // scores: [1, num_heads, 1, seq_len]
        auto scores = torch::matmul(q, k.transpose(-2, -1)) * scale;
        auto attn_weights = torch::softmax(scores, /*dim=*/-1);
        
        // output: [1, num_heads, 1, head_dim]
        auto attn_output = torch::matmul(attn_weights, v);
        
        // 存入输出
        output[seq_idx] = attn_output.squeeze(0).squeeze(1);
    }
    
    return output;
}

/**
 * 标准 Multi-Head Attention (非分页)
 * 
 * 用于 prefill 阶段，处理完整的输入序列。
 * 
 * @param query   [batch, seq_len, num_heads, head_dim]
 * @param key     [batch, seq_len, num_kv_heads, head_dim]
 * @param value   [batch, seq_len, num_kv_heads, head_dim]
 * @param scale   缩放因子
 * @return        [batch, seq_len, num_heads, head_dim]
 */
torch::Tensor standard_attention_forward_cpu(
    torch::Tensor query,
    torch::Tensor key,
    torch::Tensor value,
    double scale
) {
    MYGPU_CHECK_INPUT(query);
    MYGPU_CHECK_INPUT(key);
    MYGPU_CHECK_INPUT(value);
    
    const int64_t batch = query.size(0);
    const int64_t seq_len = query.size(1);
    const int64_t num_heads = query.size(2);
    const int64_t head_dim = query.size(3);
    const int64_t num_kv_heads = key.size(2);
    const int64_t num_queries_per_kv = num_heads / num_kv_heads;
    
    // 转置为 [batch, num_heads, seq_len, head_dim]
    auto q = query.permute({0, 2, 1, 3});
    auto k = key.permute({0, 2, 1, 3});
    auto v = value.permute({0, 2, 1, 3});
    
    // 处理 GQA
    if (num_queries_per_kv > 1) {
        k = k.repeat_interleave(num_queries_per_kv, /*dim=*/1);
        v = v.repeat_interleave(num_queries_per_kv, /*dim=*/1);
    }
    
    // Scaled Dot-Product Attention
    auto output = scaled_dot_product_attention(q, k, v, scale);
    
    // 转置回 [batch, seq_len, num_heads, head_dim]
    return output.permute({0, 2, 1, 3});
}

}  // namespace ops
}  // namespace mygpu


// =============================================================================
// 导出函数
// =============================================================================

torch::Tensor paged_attention_v1_forward(
    torch::Tensor query,
    torch::Tensor key_cache,
    torch::Tensor value_cache,
    torch::Tensor block_tables,
    torch::Tensor seq_lens,
    double scale,
    int64_t block_size
) {
    if (query.device().is_cpu()) {
        return mygpu::ops::paged_attention_v1_forward_cpu(
            query, key_cache, value_cache, block_tables, seq_lens, scale, block_size
        );
    }
    
    TORCH_WARN("CUDA implementation not available, falling back to CPU");
    auto cpu_output = mygpu::ops::paged_attention_v1_forward_cpu(
        query.cpu(),
        key_cache.cpu(),
        value_cache.cpu(),
        block_tables.cpu(),
        seq_lens.cpu(),
        scale,
        block_size
    );
    return cpu_output.to(query.device());
}

// 额外导出标准 attention 用于测试
torch::Tensor standard_attention_forward(
    torch::Tensor query,
    torch::Tensor key,
    torch::Tensor value,
    double scale
) {
    if (query.device().is_cpu()) {
        return mygpu::ops::standard_attention_forward_cpu(query, key, value, scale);
    }
    
    TORCH_WARN("CUDA implementation not available, falling back to CPU");
    auto cpu_output = mygpu::ops::standard_attention_forward_cpu(
        query.cpu(), key.cpu(), value.cpu(), scale
    );
    return cpu_output.to(query.device());
}
