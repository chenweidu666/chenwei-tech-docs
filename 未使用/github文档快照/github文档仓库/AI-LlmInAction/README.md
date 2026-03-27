# LLM-In-Action | 大模型应用实战笔记

> 记录我在大模型（LLM）领域的学习与实践，涵盖微调、推理部署、RAG、OCR、数据集生成等方向。所有项目均基于阿里云 Qwen 系列模型实现。

## 文章目录

| # | 文章 | 关键技术 |
|---|------|----------|
| 1 | [QA 数据集生成工具](#1-qa-数据集生成工具) | Qwen3, RAG, Chroma, Gradio |
| 2 | [大模型微调原理与实践](#2-大模型微调原理与实践) | LoRA, Adapter, PEFT, Instruction Tuning |
| 3 | [分布式训练框架调研](#3-分布式训练框架调研) | DeepSpeed, Megatron-LM, LLaMA-Factory |
| 4 | [PaddleOCR + LLM 的 PDF 转换工具](#4-paddleocr--llm-的-pdf-转换工具) | PaddleOCR, Qwen-plus, DashScope API |
| 5 | [vLLM 使用指南](#5-vllm-使用指南) | vLLM, Qwen2-0.5B-Instruct, ModelScope |
| 6 | [RAG 问答系统](#6-rag-问答系统) | RAG, Qwen-Plus, Chroma, bge-large-zh |
| 7 | [问答数据集生成器 — 用大模型记录人生](#7-问答数据集生成器--用大模型记录人生) | PyQt5, DashScope API, Qwen-Plus |
| 8 | [写作 Agent — 基于网文语料的风格化创作助手](#8-写作-agent--基于网文语料的风格化创作助手) | RAG, LORA, Agent, 网文语料, 双语字幕 |

---

## 1. QA 数据集生成工具

📄 [QA_Dataset_Generator.md](./QA_Dataset_Generator.md)

基于 Qwen3 和 RAG 的问答数据集生成工具。支持从 `.txt`、`.pdf`、`.docx` 提取文本，自动分割为语义完整的句子，生成自然问题并润色（确保主语明确），通过 RAG 检索上下文生成高质量答案。提供 Gradio Web 界面，支持文件上传、结果展示和数据下载。

**技术栈**：Qwen3 · Chroma · HuggingFace Embeddings · Gradio · Matplotlib

---

## 2. 大模型微调原理与实践

📄 [LLM_FineTuning_Guide.md](./LLM_FineTuning_Guide.md)

系统介绍大语言模型微调的原理与实践。涵盖微调的定义与目标（任务适应、领域适应、性能提升），详细对比三大类微调方法：全参数微调、参数高效微调（LoRA / Adapter / PEFT）、提示微调与指令微调，分析各方法的优缺点和适用场景。

**技术栈**：LoRA · Adapter · PEFT · Prompt Tuning · Instruction Tuning

---

## 3. 分布式训练框架调研

📄 [Distributed_Training_Frameworks.md](./Distributed_Training_Frameworks.md)

调研主流分布式训练与微调框架，包括 Megatron-LM、DeepSpeed、Hugging Face PEFT、FSDP、Colossal-AI、Axolotl、LLaMA-Factory 等。分析各框架的技术特点和适用场景，针对 Qwen2.5-0.5B-Instruct 微调任务提供具体实现建议。

**技术栈**：Megatron-LM · DeepSpeed · FSDP · Colossal-AI · Axolotl · LLaMA-Factory · LoRA · QLoRA · ZeRO

---

## 4. PaddleOCR + LLM 的 PDF 转换工具

📄 [PaddleOCR_LLM_PDF_Tool.md](./PaddleOCR_LLM_PDF_Tool.md)

结合 PaddleOCR（PP-OCRv4）和阿里云 Qwen-plus 的 PDF 转 Markdown 工具。先用 OCR 提取 PDF 中的文字，再通过大模型将非结构化文本整理为结构化 Markdown 格式输出。提供 Gradio Web 界面，支持多页 PDF 处理。

**技术栈**：PaddleOCR · PaddlePaddle · Qwen-plus · DashScope API · Gradio

---

## 5. vLLM 使用指南

📄 [vLLM_Usage_Guide.md](./vLLM_Usage_Guide.md)

vLLM（v0.8.3）的安装与使用指南。涵盖从 ModelScope 下载 Qwen2-0.5B-Instruct 模型、基本推理示例、常见问题排查（`psutil` 版本冲突、Repository ID 错误等），以及 GPU / CPU 环境下的进阶配置。

**技术栈**：vLLM · ModelScope · Qwen2-0.5B-Instruct · CUDA

---

## 6. RAG 问答系统

📄 [RAG_QA_System.md](./RAG_QA_System.md)

基于 RAG（检索增强生成）和阿里云 DashScope API 的 PDF 智能问答工具。从 PDF 提取文本，使用 BAAI/bge-large-zh-v1.5 嵌入模型和 Chroma 构建向量数据库，结合 Qwen-Plus 实现上下文感知的智能问答和多轮对话。提供 Gradio 界面，适用于文档理解与知识挖掘。

**技术栈**：RAG · Qwen-Plus · pdfplumber · bge-large-zh-v1.5 · Chroma · Gradio

---

## 7. 问答数据集生成器 — 用大模型记录人生

📄 [QA_Dataset_LifeRecorder.md](./QA_Dataset_LifeRecorder.md)

一个有趣的项目：用大模型帮你记录人生经历。基于 PyQt5 的桌面应用，通过阿里云 DashScope API 自动生成不重复的问题，AI 润色答案，以 JSON 格式管理问答数据集，还能基于历史问答生成个人总结。适用于自传记录、个人知识库构建，或作为模型微调的训练数据。

**技术栈**：PyQt5 · DashScope API · Qwen-Plus · JSON

---

## 8. 写作 Agent — 基于网文语料的风格化创作助手

📄 [Writing_Agent_Idea.md](./Writing_Agent_Idea.md)

基于手上的两类数据资产（45 部中文网文语料 + NAS 上持续生成的中日双语字幕），构思的写作 Agent 方案。规划了三个递进方案：RAG 写作助手（快速原型）→ LORA 微调（风格内化）→ Agent 编排（完整创作流程），以及利用双语字幕的日语学习应用扩展方向。

**技术栈**：RAG · LORA · Qwen3 · Chroma · bge-large-zh · Gradio · Agent

---

## 技术全景

```
┌─────────────────────────────────────────────────┐
│                  大模型应用实战                     │
├──────────┬──────────┬──────────┬────────────────┤
│  数据集   │   微调    │  推理部署  │    应用层       │
│          │          │          │               │
│ QA生成(1) │ LoRA(2)  │ vLLM(5)  │ RAG问答(6)     │
│ 人生记录(7)│DeepSpeed │          │ OCR+LLM(4)    │
│          │  (3)     │          │ 写作Agent(8)   │
└──────────┴──────────┴──────────┴────────────────┘
```

## 环境

- **模型**：阿里云 Qwen 系列（Qwen-Plus / Qwen3 / Qwen2.5）
- **API**：阿里云 DashScope（OpenAI 兼容模式）
- **系统**：Ubuntu 22.04 LTS

---

> 持续更新中。欢迎 Star ⭐
