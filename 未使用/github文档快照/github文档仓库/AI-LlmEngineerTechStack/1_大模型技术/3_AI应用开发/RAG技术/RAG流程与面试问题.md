# RAG（Retrieval-Augmented Generation）流程概述

RAG 是一种结合检索（Retrieval）和生成（Generation）的 AI 技术框架，用于提升大型语言模型（LLM）的准确性和相关性。它通过从外部知识库中检索相关信息来"增强"生成过程，避免 LLM 仅依赖预训练知识，从而减少幻觉（hallucination）和提高事实准确性。

下面详细描述一个典型的 RAG 流程，包括两个主要阶段：**知识库构建阶段**（离线准备）和**在线查询阶段**（实时响应）。每一步说明推荐的技术栈（工具/框架）和模型（嵌入模型或 LLM）。

---

## 一、知识库构建阶段（Offline Preparation）

这个阶段是预处理数据，构建可检索的知识库。通常在系统初始化时执行一次，或定期更新。

### 步骤 1.1: 数据采集和清洗

- **描述**：收集原始数据（如文本文档、PDF、网页等），进行清洗（去除噪声、格式化）。
- **技术栈**：
  - Python 库：Pandas（数据处理）、BeautifulSoup（网页解析）、PyPDF2 / PyMuPDF（PDF 处理）
  - 大规模数据：Apache Spark 或 Dask 进行分布式处理
  - OCR（扫描件）：PaddleOCR、Tesseract
- **模型**：无需特定模型，此步主要是规则-based 或简单 NLP（如 NLTK 或 spaCy 用于分词/去停用词）。

### 步骤 1.2: 文档切分和嵌入生成

- **描述**：将长文档切分成小块（chunks），然后生成向量嵌入（embeddings），以便后续检索。
- **技术栈**：
  - 文档加载和切分：LangChain、LlamaIndex
  - 嵌入生成：Sentence Transformers、Hugging Face Transformers
- **模型**：
  - 开源：`all-MiniLM-L6-v2`（Sentence Transformers，轻量高效）、`bge-large-zh`（中文效果好）、`m3e-base`
  - 商用：`text-embedding-ada-002`（OpenAI，高精度）、`text-embedding-3-small/large`
- **切分策略**：固定长度（如 512 tokens）或语义-based（如 SemanticChunker）

### 步骤 1.3: 索引构建

- **描述**：将嵌入向量存储到向量数据库中，构建索引以支持快速相似度搜索。
- **技术栈**：
  - 向量数据库：FAISS（开源本地）、Milvus（分布式）、Pinecone（托管）、Weaviate、ChromaDB
  - 混合搜索：Elasticsearch（向量 + 关键词 BM25）
- **模型**：无特定生成模型，依赖嵌入模型的输出
- **索引算法**：HNSW（Hierarchical Navigable Small World）、IVF（Inverted File）

---

## 二、在线查询阶段（Online Querying）

这个阶段是用户实时交互的部分，每次查询都会触发。

### 步骤 2.1: 查询嵌入生成

- **描述**：接收用户查询，生成其向量嵌入。
- **技术栈**：LangChain、Haystack（查询处理管道）
- **模型**：与知识库一致的嵌入模型（如 `bge-large-zh` 或 `text-embedding-ada-002`），确保查询和文档嵌入在同一向量空间。

### 步骤 2.2: 检索相关文档

- **描述**：使用查询嵌入从知识库中检索 top-K 最相似的文档块（基于余弦相似度等）。
- **技术栈**：
  - 检索引擎：FAISS、Milvus、Pinecone
  - Reranking：Cohere Rerank、BGE-Reranker、BM25 混合
- **模型**：
  - 检索：基于嵌入模型
  - Reranking：cross-encoder 模型如 `ms-marco-MiniLM-L-6-v2`、`bge-reranker-large`

### 步骤 2.3: 提示工程和上下文增强

- **描述**：将检索到的文档与查询组合成完整的提示（prompt）。

```
基于以下上下文回答问题：
[文档1]
[文档2]
...
问题：[query]
```

- **技术栈**：LangChain 的 PromptTemplate、Jinja2（模板渲染）
- **模型**：无生成模型，此步是纯文本处理
- **优化**：few-shot prompting、chain-of-thought

### 步骤 2.4: 生成响应

- **描述**：将增强后的提示输入 LLM，生成最终答案。
- **技术栈**：
  - 集成框架：LangChain、Hugging Face Inference API
  - 流式输出：Streamlit、FastAPI
- **模型**：
  - 商用：GPT-4/GPT-4o（OpenAI）、Claude 3（Anthropic）
  - 开源：Llama-2/3（Meta）、Qwen（阿里）、Mistral-7B、ChatGLM、DeepSeek
- **参数设置**：`temperature=0.7`（平衡创造性和准确性），`max_tokens=512`

### 步骤 2.5: 后处理和评估（可选）

- **描述**：对生成响应进行过滤（如去除冗余）、事实检查，或评估质量。
- **技术栈**：
  - 评估指标：NLTK、Rouge
  - 监控：LangSmith、HumanEval
- **模型**：可选用小型模型如 BERT（事实检查）

---

## 三、RAG 流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                    知识库构建阶段（离线）                          │
├─────────────────────────────────────────────────────────────────┤
│  原始文档  →  数据清洗  →  文档切分  →  嵌入生成  →  向量数据库    │
│  (PDF/Doc)   (清洗/OCR)   (Chunking)  (BGE/Ada)    (Milvus/FAISS)│
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    在线查询阶段（实时）                           │
├─────────────────────────────────────────────────────────────────┤
│  用户查询  →  查询嵌入  →  向量检索  →  Rerank  →  Prompt 构建   │
│     ↓                        ↓                        ↓         │
│                         Top-K 文档              上下文 + 查询     │
│                              ↓                        ↓         │
│                           LLM 生成  ←────────────────┘          │
│                              ↓                                   │
│                           最终答案                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、整体技术栈建议

| 类别 | 推荐方案 |
|------|----------|
| **端到端框架** | LangChain（易集成）、LlamaIndex（注重索引）、Haystack（注重搜索）、Dify（低代码） |
| **向量数据库** | FAISS（本地）、Milvus（分布式）、Pinecone（托管）、ChromaDB（轻量） |
| **嵌入模型** | BGE（中文推荐）、M3E、text-embedding-ada-002（OpenAI） |
| **LLM** | GPT-4（商用）、Qwen/Llama/DeepSeek（开源） |
| **部署** | Docker + Kubernetes（容器化）；AWS SageMaker / Azure ML（托管） |

### 优化方向

- **长上下文**：HyDE（Hypothetical Document Embeddings）
- **多模态 RAG**：集成 CLIP（图像嵌入）
- **混合检索**：Dense（向量）+ Sparse（BM25）
- **知识图谱增强**：Neo4j 集成

### 潜在挑战

| 挑战 | 解决方案 |
|------|----------|
| 检索召回率低 | Dense + Sparse 混合搜索、Reranking |
| 成本高 | 用开源模型（Llama/Qwen）替代商用 |
| 上下文过长 | 文档压缩、摘要、滑动窗口 |
| 知识库过时 | 增量更新、流式摄入（Kafka） |

---

## 五、如何提升 RAG 召回率

召回率（Recall）是衡量检索系统能否找到所有相关文档的关键指标。低召回率意味着相关信息被遗漏，导致 LLM 无法生成准确答案。以下是系统性提升召回率的策略：

### 5.1 索引阶段优化（Indexing）

#### 1. 优化文档切分策略

| 策略 | 描述 | 适用场景 |
|------|------|----------|
| **重叠切分** | chunk 之间保留 10-20% 重叠 | 避免关键信息被切断 |
| **语义切分** | 按段落/章节/语义边界切分 | 结构化文档（论文、手册） |
| **递归切分** | 先大块再小块，保留层级关系 | 长文档、层次结构明显 |
| **小切分 + 父文档** | 用小块检索，返回父文档 | 需要上下文完整性 |

```python
# LangChain 递归切分示例
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,  # 20% 重叠
    separators=["\n\n", "\n", "。", "；", " "]  # 中文优化
)
```

#### 2. 文档增强（Document Enrichment）

- **添加元数据**：标题、章节、来源、时间等，支持过滤检索
- **生成摘要**：为每个 chunk 生成摘要，同时索引原文和摘要
- **提取关键词**：用 TF-IDF / KeyBERT 提取关键词，作为补充索引
- **问题生成**：用 LLM 为每个 chunk 生成可能的问题，索引问题-文档对

```python
# 为文档生成假设性问题
def generate_questions(chunk, llm):
    prompt = f"基于以下内容，生成3个用户可能会问的问题：\n{chunk}"
    return llm.generate(prompt)
```

#### 3. 多粒度索引

```
┌─────────────────────────────────────────┐
│              文档级索引                  │  → 粗粒度，快速过滤
├─────────────────────────────────────────┤
│              段落级索引                  │  → 中粒度，平衡
├─────────────────────────────────────────┤
│              句子级索引                  │  → 细粒度，精确匹配
└─────────────────────────────────────────┘
```

检索时先粗筛再细筛，或多粒度结果融合。

### 5.2 检索阶段优化（Retrieval）

#### 三种检索方式对比（核心概念）

| 方式 | 核心机制 | 强项 | 弱项 | 典型场景 |
|------|----------|------|------|----------|
| **Keyword Search**（关键词/稀疏检索） | BM25 / TF-IDF 词频匹配 | 精确匹配（专有名词、ID、数字、缩写） | 无法理解语义、同义词 | 代码搜索、产品型号、法律条款 |
| **Semantic Search**（语义/向量检索） | Embedding 余弦相似度 | 理解语义、同义改写、模糊查询 | 精确匹配弱、对专有名词易错 | 自然语言问答、概念相关、长尾查询 |
| **Hybrid Search**（混合检索） | Keyword + Semantic → RRF 融合 | 召回率 + 精确率兼顾 | 计算稍重、需调权重 | **生产级 RAG 默认推荐** |

> **一句话总结**：关键词管"准"（exact），语义管"全"（recall），Hybrid 管综合，Rerank 管最终排序质量。

#### 1. 混合检索（Hybrid Search）

结合稠密向量（Dense）和稀疏向量（Sparse）的优势：

| 方法 | 优势 | 劣势 |
|------|------|------|
| **Dense（向量）** | 捕获语义相似 | 对专业术语/实体名效果差 |
| **Sparse（BM25）** | 精确匹配关键词 | 无法理解同义词 |
| **Hybrid** | 兼顾语义和关键词 | 需要调权重 |

```python
# LangChain 混合检索
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers import BM25Retriever

# 向量检索器
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# BM25 检索器
bm25_retriever = BM25Retriever.from_documents(documents)
bm25_retriever.k = 10

# 混合检索（权重各 50%）
ensemble_retriever = EnsembleRetriever(
    retrievers=[vector_retriever, bm25_retriever],
    weights=[0.5, 0.5]
)
```

#### 2. 查询改写与扩展

| 技术 | 描述 | 实现 |
|------|------|------|
| **Query Rewriting** | 用 LLM 重写查询，使其更清晰 | `"把这个问题改写得更具体：{query}"` |
| **Query Expansion** | 添加同义词、相关词 | WordNet / LLM 生成 |
| **Multi-Query** | 生成多个变体查询，合并结果 | LangChain MultiQueryRetriever |
| **HyDE** | 先生成假设性答案，用答案做检索 | 适合问答场景 |

```python
# Multi-Query 示例
from langchain.retrievers.multi_query import MultiQueryRetriever

retriever = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(),
    llm=llm
)
# 自动生成 3-5 个查询变体，合并去重结果
```

#### 3. HyDE（Hypothetical Document Embeddings）

```
用户查询 → LLM 生成假设性答案 → 用答案的嵌入检索 → 返回真实文档
```

原理：假设性答案与真实文档在语义空间更接近。

```python
from langchain.chains import HypotheticalDocumentEmbedder

hyde_embeddings = HypotheticalDocumentEmbedder.from_llm(
    llm=llm,
    base_embeddings=embeddings,
    prompt_key="web_search"  # 或自定义 prompt
)
```

#### 4. 增大检索数量 + Reranking

**为什么需要 Rerank**：Hybrid 初筛（Top-50~200）后排序不准（分数尺度不一致），Rerank 用更精准的 Cross-Encoder 模型重新打分。

**两阶段检索**：先召回大量候选（高召回），再精排（高精度）

```
Query → Hybrid 召回 Top-100 → Reranker 重排序 → Top-5~15 → LLM
```

**2026 年主流 Rerank 模型**：

| 类型 | 模型 | 特点 |
|------|------|------|
| **开源** | `bge-reranker-v2-m3` / `bge-reranker-large` | 中英多语言强，性价比高 |
| **商用** | Cohere Rerank 3.5/4、Voyage Reranker-2、Jina Reranker | 精度高，API 调用 |
| **轻量本地** | FlashRank | 速度快，适合边缘部署 |

**效果提升**：NDCG/MRR/Hit Rate 提升 10–30%，端到端准确率常升 20%+。

**Dify 中的配置实践**：
- 知识库 → 检索设置 → 选择 **Hybrid Search**（默认推荐）
- 开启 **Rerank** → 配置模型 API Key（Cohere / BGE 等）
- 参数建议：TopK 初筛 50–100 → Rerank 后 Top 8–12；Score Threshold 0.7–0.85
- Weighted Score 模式：可调 Keyword/Semantic 权重（如 Keyword 0.6 用于精确场景）

> **黄金组合**：Hybrid + Rerank 是 Dify 生产级 RAG 的标配。

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

# Cross-Encoder Reranker
model = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-large")
compressor = CrossEncoderReranker(model=model, top_n=5)

# 先检索 20 个，再 rerank 到 5 个
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vectorstore.as_retriever(search_kwargs={"k": 20})
)
```

#### 5. 关键词 Rerank vs 语义 Rerank

| 类型 | 原理 | 优点 | 缺点 | 典型方案 |
|------|------|------|------|----------|
| **关键词 Rerank** | 基于词频/TF-IDF/BM25 计算文本匹配度 | 精确匹配强、速度快、可解释 | 无法理解同义词/语义 | BM25、TF-IDF |
| **语义 Rerank** | 用 Cross-Encoder 计算 Query-Doc 语义相似度 | 理解语义、效果好 | 速度慢、计算成本高 | BGE-Reranker、Cohere Rerank |
| **混合 Rerank** | 关键词分数 + 语义分数加权融合 | 兼顾精确匹配和语义理解 | 需要调权重 | RRF、线性加权 |

**关键词 Rerank（BM25）**：

```python
from rank_bm25 import BM25Okapi

# 构建 BM25 索引
tokenized_docs = [doc.split() for doc in documents]
bm25 = BM25Okapi(tokenized_docs)

# 对初检结果重排序
def keyword_rerank(query, candidates, top_k=10):
    tokenized_query = query.split()
    scores = bm25.get_scores(tokenized_query)
    # 只对 candidates 重排序
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, score in ranked[:top_k]]
```

**语义 Rerank（Cross-Encoder）**：

```python
from sentence_transformers import CrossEncoder

# 加载 Cross-Encoder 模型
reranker = CrossEncoder("BAAI/bge-reranker-large")

def semantic_rerank(query, candidates, top_k=10):
    # 构建 (query, doc) 对
    pairs = [(query, doc) for doc in candidates]
    # 计算相似度分数
    scores = reranker.predict(pairs)
    # 按分数排序
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, score in ranked[:top_k]]
```

**混合 Rerank（RRF 倒数排名融合）**：

```python
def reciprocal_rank_fusion(rankings_list, k=60):
    """
    RRF: 融合多个排序结果
    rankings_list: [[doc1, doc2, ...], [doc3, doc1, ...], ...]
    """
    scores = {}
    for rankings in rankings_list:
        for rank, doc in enumerate(rankings):
            if doc not in scores:
                scores[doc] = 0
            scores[doc] += 1 / (k + rank + 1)
    
    # 按融合分数排序
    return sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

# 使用示例
keyword_ranking = keyword_rerank(query, candidates, top_k=20)
semantic_ranking = semantic_rerank(query, candidates, top_k=20)
final_ranking = reciprocal_rank_fusion([keyword_ranking, semantic_ranking])[:10]
```

**线性加权融合**：

```python
def linear_fusion(query, candidates, alpha=0.5, top_k=10):
    """
    alpha: 语义分数权重（0-1）
    1-alpha: 关键词分数权重
    """
    # 获取两种分数（归一化到 0-1）
    keyword_scores = get_bm25_scores(query, candidates)  # 归一化
    semantic_scores = get_cross_encoder_scores(query, candidates)  # 归一化
    
    # 加权融合
    final_scores = {}
    for doc in candidates:
        final_scores[doc] = alpha * semantic_scores[doc] + (1 - alpha) * keyword_scores[doc]
    
    ranked = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
    return [doc for doc, score in ranked[:top_k]]
```

**Rerank 方案选择建议**：

| 场景 | 推荐方案 | 说明 |
|------|----------|------|
| 专业术语/实体名多 | 关键词优先（BM25） | 精确匹配重要 |
| 口语化查询/同义词多 | 语义优先（Cross-Encoder） | 需要理解语义 |
| 通用场景 | 混合 Rerank（RRF） | 兼顾两者 |
| 延迟敏感 | 关键词 Rerank | Cross-Encoder 较慢 |
| 精度优先 | 语义 Rerank | 效果最好 |

### 5.3 嵌入模型优化

#### 1. 选择合适的嵌入模型

| 模型 | 特点 | 推荐场景 |
|------|------|----------|
| `bge-large-zh-v1.5` | 中文 SOTA，支持指令 | 中文通用 |
| `bge-m3` | 多语言、多粒度 | 跨语言场景 |
| `text-embedding-3-large` | OpenAI 最新，维度可调 | 商用高精度 |
| `jina-embeddings-v2` | 支持 8K 长文本 | 长文档场景 |

#### 2. 指令微调嵌入

BGE 等模型支持添加指令前缀，提升检索效果：

```python
# 查询时添加指令
query = "为这个句子生成表示以用于检索相关文章：" + user_query

# 文档不加指令
doc_embedding = model.encode(document)
```

#### 3. 领域微调

对嵌入模型做领域数据微调，提升特定领域召回：

```python
# 使用 sentence-transformers 微调
from sentence_transformers import SentenceTransformer, losses

model = SentenceTransformer('BAAI/bge-base-zh-v1.5')
train_loss = losses.MultipleNegativesRankingLoss(model)
# ... 训练代码
```

### 5.4 知识图谱增强

结合知识图谱补充向量检索的不足：

```
用户查询 → 实体识别 → 图谱查询 → 相关实体/关系
                ↓
          向量检索 → 合并结果 → LLM
```

- 适合：实体关系明确的领域（医疗、法律、金融）
- 技术栈：Neo4j、LlamaIndex KnowledgeGraphIndex

### 5.5 召回率优化 Checklist

| 阶段 | 优化项 | 优先级 |
|------|--------|--------|
| **切分** | 重叠切分（10-20%） | ⭐⭐⭐ |
| **切分** | 语义/递归切分 | ⭐⭐ |
| **索引** | 文档增强（摘要/问题） | ⭐⭐ |
| **检索** | 混合检索（Dense + BM25） | ⭐⭐⭐ |
| **检索** | Multi-Query / HyDE | ⭐⭐ |
| **检索** | 增大 Top-K + Reranking | ⭐⭐⭐ |
| **模型** | 选择合适的嵌入模型 | ⭐⭐⭐ |
| **模型** | 领域微调嵌入 | ⭐ |
| **高级** | 知识图谱增强 | ⭐ |

### 5.6 召回率评估

```python
def recall_at_k(retrieved_ids, relevant_ids, k):
    """计算 Recall@K"""
    retrieved_k = set(retrieved_ids[:k])
    relevant = set(relevant_ids)
    return len(retrieved_k & relevant) / len(relevant) if relevant else 0

# 评估示例
queries = [...]  # 测试查询
ground_truth = [...]  # 每个查询的相关文档 ID

recalls = []
for query, relevant_ids in zip(queries, ground_truth):
    retrieved = retriever.get_relevant_documents(query)
    retrieved_ids = [doc.metadata['id'] for doc in retrieved]
    recalls.append(recall_at_k(retrieved_ids, relevant_ids, k=10))

print(f"平均 Recall@10: {sum(recalls) / len(recalls):.2%}")
```

---

## 六、RAG 面试问题（补充召回率相关）

以下是常见面试问题，按难度分级，附简要答案提示。

### 初级问题

#### 1. 什么是 RAG？为什么需要它？

**答案提示**：
- RAG = Retrieval-Augmented Generation，检索增强生成
- 结合检索外部知识来辅助 LLM 生成
- **优点**：减少幻觉，提高事实准确性，无需重训模型，知识可更新
- **缺点**：依赖知识库质量，增加延迟，检索可能不准确

#### 2. RAG 和 Fine-Tuning 的区别是什么？

| 维度 | RAG | Fine-Tuning |
|------|-----|-------------|
| 原理 | 动态检索外部知识 | 调整模型权重 |
| 数据需求 | 知识库文档 | 大量标注数据 |
| 计算成本 | 低（推理时检索） | 高（需要训练） |
| 知识更新 | 更新知识库即可 | 需要重新训练 |
| 适用场景 | 知识密集型、需要实时更新 | 特定任务、风格适配 |

#### 3. RAG 中的「检索」和「生成」分别指什么？

**答案提示**：
- **检索**：从知识库中找到与查询相关的文档片段（基于向量相似度）
- **生成**：将检索到的文档作为上下文，由 LLM 生成最终答案

### 中级问题

#### 4. 在 RAG 中，如何处理查询与文档的不匹配（如同义词问题）？

**答案提示**：
- 用语义嵌入模型（如 Sentence Transformers / BGE）捕获语义相似，而非字面匹配
- 添加 Reranking 步骤，用 cross-encoder 细化排序
- Query Expansion：对查询进行扩展（同义词、相关词）
- HyDE：先让 LLM 生成假设性文档，再用其做检索

#### 5. 描述一个 RAG 系统的端到端流程，并说明每个步骤的潜在瓶颈。

**答案提示**：

| 步骤 | 瓶颈 | 优化 |
|------|------|------|
| 文档切分 | 切分粒度不当导致语义断裂 | 语义切分、重叠窗口 |
| 嵌入生成 | 速度慢、成本高 | GPU 加速、批处理、用轻量模型 |
| 向量检索 | 延迟、召回率 | 高效索引（HNSW）、混合检索 |
| Prompt 构建 | 上下文过长 | 文档压缩、摘要 |
| LLM 生成 | 延迟、成本 | 流式输出、用小模型、缓存 |

#### 6. 如何评估 RAG 系统的性能？

**答案提示**：

| 维度 | 指标 |
|------|------|
| 检索质量 | Recall@K、Precision@K、MRR（Mean Reciprocal Rank） |
| 生成质量 | BLEU、ROUGE、BERTScore |
| 端到端 | 准确率、F1、用户满意度 |
| 效率 | 延迟（P50/P95）、吞吐量 |

评估方法：A/B 测试、用户反馈、LLM-as-Judge

### 高级问题

#### 7. 在 RAG 中，如何实现多跳检索（multi-hop retrieval）？

**答案提示**：
- **场景**：复杂问题需要多步推理，单次检索无法覆盖
- **方案**：
  1. 迭代检索：先检索初步文档，再基于其内容生成子查询检索更多
  2. 技术栈：LangChain 的 `MultiQueryRetriever`、Self-Ask
  3. 知识图谱：用图结构连接实体，支持多跳推理

#### 8. 如果知识库很大，如何优化 RAG 的检索效率和成本？

**答案提示**：
- **分层索引**：coarse-to-fine search（先粗筛再细筛）
- **向量量化**：减少存储和计算（如 PQ、SQ）
- **分区/分片**：按主题或时间分区，缩小检索范围
- **缓存**：热门查询结果缓存
- **知识图谱增强**：用 Neo4j 减少无关检索

#### 9. RAG 在处理实时数据（如新闻）时，有什么挑战？如何解决？

**答案提示**：

| 挑战 | 解决方案 |
|------|----------|
| 知识库过时 | 定期增量更新、流式摄入（Kafka） |
| 实时性要求高 | 结合在线搜索 API（如 Google Search、Bing） |
| 数据量大 | 滑动窗口、只保留近期数据 |
| 数据质量参差 | 来源可信度评分、去重 |

#### 10. 如何处理 RAG 中的「答案幻觉」问题？

**答案提示**：
- **检索侧**：提高召回率和精度，确保检索到相关文档
- **生成侧**：
  - Prompt 中明确要求「仅基于上下文回答」
  - 降低 temperature
  - 后处理：用 NLI 模型检查答案与上下文的一致性
- **系统侧**：添加「不确定」选项，置信度低时拒绝回答

---

## 七、代码示例（LangChain + FAISS）

```python
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI

# 1. 加载文档
loader = PyPDFLoader("document.pdf")
documents = loader.load()

# 2. 文档切分
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
chunks = text_splitter.split_documents(documents)

# 3. 嵌入生成 + 索引构建
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-large-zh")
vectorstore = FAISS.from_documents(chunks, embeddings)

# 4. 构建 RAG 链
llm = OpenAI(temperature=0.7)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5})
)

# 5. 查询
query = "这份文档的主要内容是什么？"
answer = qa_chain.run(query)
print(answer)
```

---

## 参考资源

- LangChain 文档：https://python.langchain.com/docs/
- LlamaIndex 文档：https://docs.llamaindex.ai/
- FAISS：https://github.com/facebookresearch/faiss
- BGE 模型：https://huggingface.co/BAAI/bge-large-zh
- RAG 论文：[Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)
