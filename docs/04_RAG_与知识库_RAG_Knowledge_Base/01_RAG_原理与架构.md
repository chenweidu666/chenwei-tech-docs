# 4.1 RAG 检索增强生成

> 📅 最后更新：2026-03-26  
> ⏱️ 阅读时间：12 分钟

---

## 一、什么是 RAG

**RAG（Retrieval-Augmented Generation）**：检索 + 生成。

```
用户问题
   ↓
[检索] → 相关文档
   ↓
[增强] → 问题 + 文档
   ↓
[生成] → 回答
```

**优势**：
- ✅ 减少幻觉
- ✅ 注入私有知识
- ✅ 无需微调

---

## 二、核心组件

### 1. 向量数据库

| 数据库 | 特点 | 适用场景 |
|--------|------|---------|
| Milvus | 开源，功能全 | 企业级 |
| Chroma | 轻量，易用 | 小规模 |
| Pinecone | 托管，省心 | 快速上线 |
| FAISS | Facebook，速度快 | 本地部署 |

### 2. 嵌入模型

| 模型 | 维度 | 中文效果 |
|------|------|---------|
| text-embedding-3 | 1536 | 好 |
| m3e-base | 768 | 很好 |
| bge-large-zh | 1024 | 最好 |

### 3. 框架

- LangChain：功能最全
- LlamaIndex：专注 RAG
- Haystack：企业级

---

## 三、实战：LangChain RAG

### 1. 安装

```bash
pip install langchain langchain-community chromadb
```

### 2. 准备文档

```python
from langchain.document_loaders import TextLoader

# 加载文档
loader = TextLoader("company_policy.txt")
documents = loader.load()
```

### 3. 切分文档

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)

chunks = text_splitter.split_documents(documents)
```

### 4. 生成嵌入

```python
from langchain.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-zh-v1.5"
)
```

### 5. 存入向量库

```python
from langchain.vectorstores import Chroma

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
```

### 6. 检索 + 生成

```python
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

# 加载向量库
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)

# 创建检索器
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)

# 创建 QA 链
llm = ChatOpenAI(model="gpt-3.5-turbo")
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

# 查询
query = "公司的年假政策是什么？"
result = qa_chain({"query": query})

print(result["result"])
print("来源:", result["source_documents"])
```

---

## 四、高级技巧

### 1. 混合检索

```python
# 语义检索 + 关键词检索
retriever = vectorstore.as_retriever(
    search_type="mmr",  # Maximal Marginal Relevance
    search_kwargs={
        "k": 5,
        "fetch_k": 10,
        "lambda_mult": 0.5  # 0=纯语义，1=纯关键词
    }
)
```

### 2. 多向量检索

```python
# 同时检索文档和段落
from langchain.retrievers import EnsembleRetriever

retriever1 = vectorstore1.as_retriever(k=3)
retriever2 = vectorstore2.as_retriever(k=3)

ensemble = EnsembleRetriever(
    retrievers=[retriever1, retriever2],
    weights=[0.5, 0.5]
)
```

### 3. 重排序

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CohereRerank

compressor = CohereRerank()

compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=retriever
)
```

---

## 五、常见问题

### Q1：检索不准确怎么办？

**解决**：
- 调整 chunk_size（300-800）
- 换更好的嵌入模型
- 增加 k 值（检索更多）
- 用混合检索

### Q2：回答有幻觉？

**解决**：
- 增加检索文档数量
- 在 prompt 中强调"基于文档"
- 设置温度=0

### Q3：响应太慢？

**优化**：
- 减少 k 值
- 用更小的嵌入模型
- 缓存常见查询

---

## 下一步

- 👉 [5.1 Agent 设计与工作流](../05_Agent 开发/5.1_Agent 设计与工作流.md)
- 👉 [6.1 FastAPI 服务化](../06_工程化/6.1_FastAPI 服务化.md)

---

*完整示例：https://github.com/chenweidu666/AI-Engineering-Docs/tree/main/examples/rag*
