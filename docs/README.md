<div style="text-align: center; font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;"><strong>CW · Tech Docs</strong></div>

# 1. 站点说明

本站为 **AI 工程技术笔记**，按大模型全栈能力组织为八章，与左侧导航一一对应。内容侧重**工程落地、选型与排障**，与第七、八章「项目总结」中的长篇实践文档互补。

## 1.1. 八章主线

| 章节 | 内容 |
|------|------|
| 1. 基础层 | 1.1–1.4：动机与缩放 / Transformer / 主流选型 / 趋势与参考 |
| 2. 训练与微调 | 数据处理与预训练 / SFT / LoRA / RLHF / 分布式训练 |
| 3. 部署与推理 | KV Cache 与推理加速 / vLLM / 量化 |
| 4. RAG 与知识库 | 4.1：RAG、Milvus 与 LangChain（单篇） |
| 5. Agent 开发 | 工作流 / MCP / Dify / AppAgent（OpenClaw 见第 7、8 章） |
| 6. 工程化 | FastAPI / Docker 容器化 |
| 7. 项目总结 | CineMaker 项目手册 · OpenClaw 部署与实践（见 [本章索引](07_项目总结/README.md)） |
| **8. OpenClaw 实战系列** 🆕 | Dashboard 部署 / 双龙虾架构 / Git 同步 / MCP 集成 / BTC 量化策略（见 [本章索引](08_OpenClaw 实战/README.md)） |

## 1.2. 使用方式

使用 **左侧导航栏** 浏览各篇；章节内链接多为相对路径，便于在 Docsify 或本地预览中跳转。同步或镜像上游 Markdown 后，若结构变化，可在仓库根目录执行 `python3 scripts/apply_doc_format.py` 统一篇名与标题编号（参见 `.cursor/rules/doc-heading-numbering.mdc`）。
