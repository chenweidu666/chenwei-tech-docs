# 大模型部署技术学习清单

> 基于岗位要求整理的大模型部署技术学习清单
> 
> **岗位核心要求**：
> 1. 熟练使用 C++、Python
> 2. 有大模型的开发经验，熟悉大模型的相关基础
> 3. 熟悉大模型加速技术，如 KV Cache、模型量化、Flash-Attention、推理并行、投机采样等

---

## 🎯 学习目标

掌握大模型部署工程师的核心技能，重点聚焦：
- **编程语言**：C++、Python 熟练使用
- **大模型基础**：架构理解、开发经验
- **加速技术**：KV Cache、模型量化、Flash-Attention、推理并行、投机采样

---

## 📚 一、编程语言基础（必须掌握）

### 1.1 Python 熟练使用
- [ ] **Python 核心技能**
  - 面向对象编程
  - 多线程/多进程编程
  - 异步编程（asyncio）
  - 内存管理与性能优化

- [ ] **Python 在 AI 中的应用**
  - PyTorch/TensorFlow 使用
  - NumPy、SciPy 科学计算
  - 数据处理（Pandas）
  - API 开发（FastAPI、Flask）

### 1.2 C++ 熟练使用
- [ ] **C++ 核心技能**
  - C++11/14/17 现代特性
  - 内存管理（智能指针、RAII）
  - 模板编程
  - 多线程编程（std::thread、std::async）

- [ ] **C++ 在推理引擎中的应用**
  - CUDA 编程基础
  - 性能优化（SIMD、内存对齐）
  - 与 Python 的互操作（Pybind11）
  - 推理引擎开发实践

---

## 📚 二、大模型基础技术（必须掌握）

### 2.1 大模型架构深入理解
- [ ] **Transformer 架构核心**
  - Self-Attention 机制原理与实现
  - Multi-Head Attention 计算流程
  - Position Encoding（绝对/相对位置编码）
  - Layer Normalization 和 Residual Connection

- [ ] **主流大模型架构**
  - **LLaMA 系列**（LLaMA-1/2/3）
    - RMSNorm 归一化
    - SwiGLU 激活函数
    - RoPE 旋转位置编码
  - **Qwen 系列**
    - 架构特点与优化
    - 与 LLaMA 的差异
  - **ChatGLM 架构**
  - **Baichuan 架构**

- [ ] **模型权重与格式**
  - HuggingFace 格式（.bin, .safetensors）
  - PyTorch 格式（.pt, .pth）
  - 模型分片与加载策略
  - 权重转换与合并

### 2.2 大模型开发经验
- [ ] **模型训练与微调**
  - 预训练流程
  - LoRA 微调实践
  - SFT（Supervised Fine-Tuning）
  - 模型评估方法

- [ ] **模型推理基础**
  - 自回归生成流程
  - Token 生成与采样策略
  - 上下文窗口管理
  - 批处理推理

---

## ⚡ 三、大模型加速技术（核心重点）

### 3.1 KV Cache 优化（必须掌握）
- [ ] **KV Cache 原理**
  - 为什么需要 KV Cache
  - KV Cache 的内存占用计算
  - KV Cache 的优化策略

- [ ] **KV Cache 实现**
  - 动态 KV Cache 管理
  - PagedAttention（vLLM 中的实现）
  - KV Cache 压缩技术

### 3.2 模型量化技术（必须掌握）
- [ ] **量化基础**
  - INT8 量化原理（对称/非对称量化）
  - INT4 量化原理
  - 量化校准方法（PTQ/QAT）
  - 量化精度评估

- [ ] **量化工具与实践**
  - **llm-compressor**（vLLM 生态）
    - W8A8 量化流程
    - W4A16/W4A8 量化流程
    - 校准数据集准备
    - 量化模型验证
  - **GPTQ** 量化方法
  - **AWQ** 量化方法
  - **量化工具对比**：llm-compressor vs GPTQ vs AWQ

- [ ] **量化部署**
  - 量化模型在 vLLM 中的加载
  - 量化模型在 TensorRT-LLM 中的使用
  - 量化精度与性能权衡

### 3.3 Flash-Attention（必须掌握）
- [ ] **Flash-Attention 原理**
  - 传统 Attention 的内存瓶颈
  - Flash-Attention 的优化思路
  - 分块计算策略

- [ ] **Flash-Attention 实现**
  - Flash-Attention-1 vs Flash-Attention-2
  - 在 vLLM 中的集成
  - 性能提升效果

### 3.4 推理并行技术（必须掌握）
- [ ] **张量并行（Tensor Parallelism, TP）**
  - TP 的原理与实现
  - 通信开销分析
  - TP 配置策略

- [ ] **流水线并行（Pipeline Parallelism, PP）**
  - PP 的原理与实现
  - 流水线气泡问题
  - PP 配置策略

- [ ] **数据并行（Data Parallelism, DP）**
  - DP 在推理中的应用
  - 批处理策略

- [ ] **混合并行策略**
  - TP + PP 组合
  - 分布式推理配置

### 3.5 投机采样（Speculative Sampling）（必须掌握）
- [ ] **投机采样原理**
  - 为什么需要投机采样
  - Draft Model + Target Model 架构
  - Token 生成加速策略
  - 接受/拒绝机制

- [ ] **投机采样实现**
  - 在 vLLM 中的使用
  - Draft Model 选择策略
  - 性能提升效果
  - 适用场景与限制

---

## 🚀 四、大模型推理框架

### 4.1 vLLM（重点）
- [ ] **vLLM 基础**
  - vLLM 架构与核心特性
  - PagedAttention 机制
  - Continuous Batching
  - 安装与基础使用

- [ ] **vLLM 部署实践**
  - 模型加载与配置
  - 量化模型加载（配合 llm-compressor）
  - 并发与批处理配置
  - API 服务部署（OpenAI-Compatible）

- [ ] **vLLM 性能优化**
  - 吞吐量优化
  - 延迟优化
  - 显存优化
  - 多 GPU 部署

- [ ] **vLLM 高级特性**
  - 多模型服务
  - 动态批处理
  - 请求调度策略

### 3.2 TensorRT-LLM
- [ ] **TensorRT-LLM 基础**
  - TensorRT-LLM 架构
  - 与 vLLM 的对比
  - 安装与配置

- [ ] **TensorRT-LLM 部署**
  - 模型编译（Build）
  - 模型运行（Run）
  - 量化模型部署
  - 多 GPU 部署

- [ ] **TensorRT-LLM 优化**
  - 算子融合优化
  - 内存优化
  - 性能调优

### 3.3 LMDeploy
- [ ] **LMDeploy 基础**
  - LMDeploy 架构与特性
  - 安装与使用
  - 与 vLLM 的对比

- [ ] **LMDeploy 部署**
  - 模型转换
  - 量化部署
  - 服务部署

### 3.4 llama.cpp
- [ ] **llama.cpp 基础**
  - llama.cpp 架构
  - 适用场景（本地部署）
  - 安装与使用

- [ ] **llama.cpp 优化**
  - 量化支持
  - CPU/GPU 加速
  - 性能优化

### 3.5 推理框架对比
- [ ] **框架选择指南**
  - vLLM vs TensorRT-LLM vs LMDeploy vs llama.cpp
  - 适用场景分析
  - 性能对比
  - 部署复杂度对比

---

## 🛠️ 五、模型优化与准备

### 4.1 模型格式转换
- [ ] **HuggingFace 模型处理**
  - 模型下载与加载
  - 模型格式转换
  - 模型分片策略

- [ ] **模型转换工具**
  - transformers 库使用
  - 模型权重合并
  - 模型格式验证

### 4.2 模型微调与适配
- [ ] **LoRA 微调**
  - LoRA 原理回顾
  - PEFT 库使用
  - LoRA 权重合并
  - 微调模型部署

- [ ] **SFT（Supervised Fine-Tuning）**
  - SFT 流程
  - 指令数据准备
  - 微调模型部署

### 4.3 模型评估
- [ ] **精度评估**
  - 验证集评估
  - 量化后精度验证
  - 任务特定评估指标

- [ ] **性能评估**
  - 推理速度测试
  - 吞吐量测试
  - 显存占用测试
  - 延迟分析

---

## 🏗️ 六、部署环境与基础设施

### 5.1 容器化部署
- [ ] **Docker 基础**
  - Dockerfile 编写
  - 基础镜像选择（CUDA、驱动等）
  - 多阶段构建优化

- [ ] **Docker 实践**
  - vLLM 容器化
  - TensorRT-LLM 容器化
  - 镜像优化（减小体积）

### 5.2 Kubernetes 部署
- [ ] **K8s 基础**
  - Pod、Service、Deployment 概念
  - 资源管理（CPU、GPU、内存）
  - 存储管理（PVC）

- [ ] **K8s 部署实践**
  - vLLM 在 K8s 中的部署
  - 多副本部署
  - 滚动更新策略
  - Helm Chart 使用

- [ ] **K8s 高级特性**
  - GPU 资源调度
  - 节点亲和性配置
  - HPA（水平自动扩缩容）

### 5.3 监控与运维
- [ ] **监控指标**
  - 推理延迟监控
  - 吞吐量监控
  - GPU 利用率监控
  - 错误率监控

- [ ] **监控工具**
  - Prometheus + Grafana
  - 自定义监控指标
  - 告警配置

---

## 🌐 七、服务网关与接口

### 6.1 API 网关
- [ ] **网关选型**
  - Nginx 配置
  - APISIX 使用
  - 网关功能（路由、限流、熔断）

- [ ] **网关配置**
  - 请求路由（按模型版本/租户）
  - 负载均衡
  - 限流策略
  - 熔断机制

### 6.2 API 接口
- [ ] **OpenAI-Compatible API**
  - API 格式规范
  - Chat Completions API
  - Streaming 支持

- [ ] **HTTP REST API**
  - RESTful 设计
  - 请求/响应格式
  - 错误处理

- [ ] **鉴权与安全**
  - API Key 管理
  - Token 验证
  - 请求签名

---

## 🔧 八、AI 编译器与算子开发（加分项）

### 7.1 AI 编译器基础
- [ ] **编译器概念**
  - 计算图优化
  - 算子融合
  - 内存优化

- [ ] **主流编译器**
  - TVM（已有经验，扩展到 LLM）
  - TensorRT
  - XLA

### 7.2 算子开发
- [ ] **自定义算子**
  - CUDA 算子开发基础
  - 算子注册与集成
  - 性能优化

- [ ] **算子优化**
  - 内存访问优化
  - 计算优化
  - 并行策略

---

## 📱 九、VLM 部署（加分项）

### 8.1 VLM 基础
- [ ] **视觉语言模型架构**
  - CLIP 架构
  - LLaVA 架构
  - 多模态融合机制

### 8.2 VLM 部署
- [ ] **云端部署**
  - VLM 模型加载
  - 图像预处理
  - 推理优化

- [ ] **端侧部署**
  - 模型量化
  - 端侧推理框架
  - 性能优化

---

## 📋 十、完整部署流程实践

### 9.1 需求梳理与模型选型
- [ ] **业务需求分析**
  - 对话/检索/工具调用场景
  - QPS 要求
  - 延迟要求
  - 成本约束

- [ ] **模型选型**
  - 基座模型评估
  - 指令微调模型评估
  - 参数规模选择
  - 推理形态确定（单模型/多模型）

### 9.2 环境与基础设施搭建
- [ ] **资源规划**
  - 国产芯片资源规划
  - 集群拓扑设计
  - GPU 资源分配

- [ ] **环境搭建**
  - Docker 环境
  - Kubernetes 集群
  - 基础镜像准备
  - 监控 Agent 部署

### 9.3 模型准备与优化
- [ ] **模型获取**
  - HuggingFace 模型下载
  - 内部模型仓库使用
  - 模型格式转换

- [ ] **模型优化**
  - 量化（llm-compressor）
  - KV Cache 配置
  - Flash-Attention 启用
  - 精度与性能验证

### 9.4 推理服务部署
- [ ] **服务配置**
  - vLLM/TensorRT-LLM 配置
  - 并发度配置
  - 批处理策略
  - 分布式推理配置（TP/PP）

- [ ] **部署执行**
  - Helm Chart 部署
  - K8s 编排脚本
  - 多副本部署
  - 滚动更新

### 9.5 网关与接口
- [ ] **网关部署**
  - Nginx/APISIX 配置
  - 路由规则
  - 限流熔断

- [ ] **接口对接**
  - OpenAI-Compatible API
  - HTTP REST API
  - 鉴权配置

### 9.6 测试与验证
- [ ] **功能测试**
  - API 接口测试
  - 多模型切换测试
  - 错误处理测试

- [ ] **性能测试**
  - 压力测试
  - 延迟测试
  - 吞吐量测试

- [ ] **稳定性测试**
  - 长时间运行测试
  - 故障恢复测试

---

## 🎓 十一、学习资源

### 10.1 官方文档
- [ ] vLLM 官方文档：https://docs.vllm.ai/
- [ ] TensorRT-LLM 官方文档
- [ ] LMDeploy 官方文档
- [ ] llm-compressor 官方文档

### 10.2 实践项目
- [ ] 搭建本地 vLLM 服务
- [ ] 完成模型量化实践
- [ ] 部署 K8s 推理服务
- [ ] 实现完整部署流程

### 10.3 技术文章
- [ ] KV Cache 优化相关文章
- [ ] Flash-Attention 原理文章
- [ ] 量化技术对比文章
- [ ] 推理框架对比文章

---

## 📝 学习优先级建议（基于岗位要求）

### 🔴 最高优先级（岗位核心要求 - 必须掌握）

#### 1. 编程语言基础
- **Python**：熟练使用，面向对象、多线程、异步编程、AI 框架使用
- **C++**：熟练使用，现代 C++ 特性、内存管理、多线程、CUDA 编程基础

#### 2. 大模型基础
- **Transformer 架构**：深入理解 Self-Attention、Multi-Head Attention 等核心机制
- **主流模型架构**：LLaMA、Qwen 等架构特点
- **大模型开发经验**：模型训练、微调、推理流程

#### 3. 大模型加速技术（岗位核心）
- **KV Cache 优化**：原理、实现、PagedAttention、内存优化
- **模型量化**：INT8/INT4 量化原理、llm-compressor 使用、GPTQ/AWQ
- **Flash-Attention**：原理、实现、性能优化
- **推理并行**：TP（张量并行）、PP（流水线并行）、DP（数据并行）
- **投机采样**：原理、实现、Draft Model 策略

### 🟡 高优先级（生产部署必需）
1. **vLLM 框架**：主流推理框架，必须熟练掌握
2. **模型量化实践**：llm-compressor 完整流程
3. **Docker + K8s 部署**：生产环境必备
4. **推理服务部署**：API 接口、网关配置

### 🟢 中优先级（重要技能）
1. **TensorRT-LLM**：NVIDIA 生态，性能优秀
2. **其他推理框架**：LMDeploy、llama.cpp 了解
3. **监控与运维**：性能监控、问题排查

### ⚪ 低优先级（加分项）
1. **AI 编译器开发**：深度优化能力
2. **算子开发**：定制化能力
3. **VLM 部署**：多模态能力

---

## ✅ 学习检查清单（岗位要求对应）

### 编程语言（必须）
- [ ] 熟练使用 Python：能够进行面向对象编程、多线程/异步编程、AI 框架使用
- [ ] 熟练使用 C++：掌握现代 C++ 特性、内存管理、多线程、CUDA 基础

### 大模型基础（必须）
- [ ] 深入理解 Transformer 架构和主流大模型（LLaMA、Qwen）架构
- [ ] 有大模型开发经验：能够进行模型训练、微调、推理

### 大模型加速技术（必须）
- [ ] **KV Cache**：理解原理，掌握 PagedAttention 等优化技术
- [ ] **模型量化**：掌握 INT8/INT4 量化原理，熟练使用 llm-compressor
- [ ] **Flash-Attention**：理解原理，掌握在推理框架中的使用
- [ ] **推理并行**：掌握 TP、PP、DP 等并行技术
- [ ] **投机采样**：理解原理，掌握实现方法

### 部署实践（重要）
- [ ] 能够独立完成大模型从 HuggingFace 到生产部署的全流程
- [ ] 掌握 vLLM 的部署与优化
- [ ] 能够在 K8s 中部署大模型服务
- [ ] 能够配置 API 网关和接口
- [ ] 能够进行性能调优和问题排查

---

**最后更新**：2025-01-XX
**状态**：进行中

