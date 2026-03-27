# RAG 问答系统 - 基于 PDF 的智能问答工具

## 项目简介

**RAG 问答系统** 是一个基于 Python 的桌面应用程序，结合了 Retrieval-Augmented Generation（RAG）技术和阿里云 DashScope API（Qwen-Plus 模型），通过上传 PDF 文件实现智能问答和多轮对话。  
这个工具可以从 PDF 中提取文本，构建向量数据库，并利用大语言模型回答用户查询，特别适合需要快速理解文档内容、挖掘知识点的场景，比如学术研究、技术文档分析或教育资料整理。

通过 Gradio 提供的简洁界面，用户可以：
- **上传 PDF 文件**：支持任意文本 PDF，自动提取内容并构建问答环境。
- **智能问答**：基于文档内容回答问题，提供检索到的上下文。
- **多轮对话**：保留聊天历史，支持连续提问。
- **日志监控**：实时记录操作状态，便于调试和反馈。

这不仅是一个技术demo，更是一个能帮助你快速消化文档、提取价值的实用工具！

---

## 功能特性

1. **PDF 文本提取**：
   - 使用 `pdfplumber` 从 PDF 文件中提取纯文本。
   - 支持分页处理，保留元数据（路径、页码）。

2. **向量数据库构建**：
   - 利用 `HuggingFaceEmbeddings`（BAAI/bge-large-zh-v1.5）生成文本嵌入。
   - 使用 `Chroma` 存储向量，支持高效检索。

3. **智能问答（RAG）**：
   - 结合文档检索和 Qwen-Plus 模型生成准确、自然的答案。
   - 返回 top-4 相关文档片段，增强答案可信度。

4. **多轮对话**：
   - 支持对话历史记录，上下文连贯。
   - 可随时清空历史，重新开始。

5. **用户界面**：
   - 基于 Gradio 构建，支持文件上传和实时交互。
   - 显示答案、检索内容和聊天历史。

---

## 技术栈

- **编程语言**：Python 3.8+
- **核心库**：
  - `openai`：调用 DashScope API。
  - `pdfplumber`：PDF 文本提取。
  - `langchain` & `langchain-community`：RAG 管道和嵌入生成。
  - `chromadb`：向量数据库。
  - `sentence-transformers`：嵌入模型支持。
  - `gradio`：交互式界面。
- **大模型**：阿里云 DashScope Qwen-Plus。
- **硬件支持**：支持 GPU（CUDA）加速嵌入计算，兼容 CPU。

---

## 安装与运行

### 1. 环境要求
- Python 3.8 或更高版本。
- 可选：NVIDIA GPU + CUDA（加速嵌入生成）。

### 2. 安装依赖
在终端运行以下命令：
```bash
conda install -c conda-forge openai pdfplumber langchain langchain-community chromadb gradio
pip install sentence-transformers
```

### 3. 配置 API
1. 获取阿里云 DashScope API 密钥：
   - 注册阿里云账号，访问 [DashScope 控制台](https://bailian.console.aliyun.com/?tab=api#/api)。
   - 创建 API 密钥（API_KEY）。
2. 在代码中配置：
   ```python
   API_KEY = "your_api_key_here"
   BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
   ```

### 4. 运行程序
1. 下载项目代码：

```
import os
import logging
import json
from typing import List
from openai import OpenAI
import pdfplumber
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import torch
import gradio as gr
import shutil
import time

# conda install -c conda-forge openai pdfplumber langchain langchain-community chromadb gradio
# pip install sentence-transformers

# 设置日志配置，用于记录程序运行信息
# - level: INFO，记录关键操作和错误
# - format: 包含时间、日志级别和消息
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 全局变量，用于存储 RAG 链、Qwen-Plus 客户端、聊天历史和当前向量数据库路径
# - rag_chain: LangChain RAG 管道，处理查询和答案生成
# - qwen_client: Qwen-Plus API 客户端
# - chat_history: 存储多轮对话记录（用户查询和助手回答）
# - current_vector_db: 当前 Chroma 向量数据库的路径
rag_chain = None
qwen_client = None
chat_history = []
current_vector_db = None


API_KEY = 你的阿里云API
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1" 


def extract_text_from_pdf(pdf_path: str) -> List[Document]:
    """从 PDF 文件提取文本并转换为 LangChain Document 对象

    Args:
        pdf_path (str): PDF 文件的路径（如 './wenxian/yolov11.pdf'）

    Returns:
        List[Document]: 包含每页文本的 LangChain Document 列表，每个 Document 包含文本内容和元数据（路径、页码）

    Raises:
        Exception: 如果 PDF 文件无法打开或提取失败（例如文件损坏、权限问题）

    Notes:
        - 使用 pdfplumber 逐页提取文本，仅处理文本 PDF（不支持扫描 PDF）
        - 跳过无文本页面（如空白页），记录警告日志
        - 适合轻量文本提取，显存占用低（<100MB）
    """
    try:
        documents = []  # 存储所有页面的 Document 对象
        with pdfplumber.open(pdf_path) as pdf:  # 打开 PDF 文件
            for page_num, page in enumerate(pdf.pages, 1):  # 从第 1 页开始遍历
                text = page.extract_text()  # 提取页面文本
                if text:  # 如果提取到文本
                    doc = Document(
                        page_content=text,  # 页面文本内容
                        metadata={"source": pdf_path,
                                  "page": page_num}  # 元数据：文件路径和页码
                    )
                    documents.append(doc)  # 添加到列表
                else:
                    logger.warning(
                        f"No text extracted from page {page_num}")  # 记录无文本警告
        # 记录成功提取的页面数
        logger.info(f"Extracted {len(documents)} pages from {pdf_path}")
        return documents
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {str(e)}")  # 记录错误
        raise



def initialize_qwen_client():
    """初始化 DashScope Qwen-Plus 客户端，用于调用大语言模型 API

    Returns:
        OpenAI: 初始化后的 Qwen-Plus 客户端对象

    Raises:
        Exception: 如果 API 密钥无效或网络连接失败

    Notes:
        - 使用 OpenAI 兼容接口，连接 DashScope 的 Qwen-Plus 模型
        - API 密钥需有效，当前使用示例密钥
        - 云端运行，不占用本地显存
    """
    try:
        client = OpenAI(
            api_key=API_KEY,  # Qwen-Plus API 密钥
            base_url=BASE_URL,  # DashScope API 地址
        )
        logger.info("Qwen-Plus client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Qwen-Plus client: {str(e)}")
        raise


def build_rag_chain(documents: List[Document], qwen_client, vector_db_path: str):
    """构建 LangChain RAG 管道，用于处理 PDF 内容并生成答案

    Args:
        documents (List[Document]): 从 PDF 提取的 LangChain Document 列表
        qwen_client: Qwen-Plus 客户端对象
        vector_db_path (str): Chroma 向量数据库的存储路径（如 './chroma_db_yolov11_20250424'）

    Returns:
        Runnable: LangChain RAG 链，包含检索、提示构建和答案生成

    Raises:
        Exception: 如果文本分割、嵌入生成或向量存储初始化失败

    Notes:
        - 包括文本分割、嵌入生成、向量存储、检索和答案生成
        - 支持多轮对话，提示包含对话历史
    """
    try:
        # 文本分割：将长文档分割为小块，便于嵌入和检索
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # 每个块的最大长度
            chunk_overlap=200,  # 块之间的重叠长度，保留上下文
            length_function=len  # 使用字符长度计算
        )
        splits = text_splitter.split_documents(documents)  # 分割文档
        logger.info(f"Split documents into {len(splits)} chunks")


        #模型下载
        from modelscope import snapshot_download
        model_dir = snapshot_download('BAAI/bge-large-zh-v1.5')
        # model_dir = snapshot_download('sentence-transformers/all-MiniLM-L6-v2')
        # 初始化嵌入模型：生成文本的向量表示
        embedding_model = HuggingFaceEmbeddings(
            model_name=model_dir,  # 轻量嵌入模型
            model_kwargs={
                "device": "cuda" if torch.cuda.is_available() else "cpu"}  # 优先使用 GPU
        )

        # 创建向量存储：将文档嵌入存储到 Chroma 数据库
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embedding_model,
            persist_directory=vector_db_path  # 动态路径，确保隔离
        )
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": 4})  # 配置检索器，返回 top-4 相关文档
        logger.info(f"Vector store initialized at {vector_db_path}")

        # 定义提示模板：支持文档上下文、对话历史和当前问题
        prompt_template = ChatPromptTemplate.from_template(
            """You are a helpful assistant. Answer the question based on the following context from a document and the conversation history.

            **Document Context**:
            {context}

            **Conversation History**:
            {history}

            **Current Question**:
            {question}

            Answer in a concise and accurate manner, considering the conversation history."""
        )

        # 定义 Qwen-Plus 生成函数：调用 API 生成答案
        def qwen_generate(inputs: dict) -> str:
            context = inputs["context"]  # 检索到的文档内容
            question = inputs["question"]  # 当前用户查询
            history = inputs["history"]  # 对话历史
            logger.debug(
                f"Qwen-Plus input - Context: {context[:100]}..., History: {history[:100]}..., Question: {question}")
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},  # 系统提示
                {"role": "user", "content": prompt_template.format(
                    context=context, history=history, question=question)}  # 用户提示
            ]
            try:
                completion = qwen_client.chat.completions.create(
                    model="qwen-plus",  # Qwen-Plus 模型
                    messages=messages,
                    temperature=0.7,  # 控制生成随机性
                    max_tokens=200  # 最大输出长度
                )
                answer = completion.choices[0].message.content  # 提取答案
                logger.debug(f"Qwen-Plus output: {answer}")
                return answer
            except Exception as e:
                logger.error(f"Qwen-Plus API call failed: {str(e)}")
                raise

        # 格式化检索文档：为每段添加编号和页码
        def format_docs(docs):
            formatted = ""
            for i, doc in enumerate(docs, 1):
                formatted += f"**文档片段 {i} (页 {doc.metadata.get('page', '未知')})**:\n{doc.page_content}\n\n"
            return formatted

        # 格式化对话历史：将历史记录转为字符串
        def format_history(history):
            formatted = ""
            for role, text in history:
                formatted += f"{role}: {text}\n"
            return formatted if formatted else "无历史记录"

        # 构建 RAG 链：整合检索、提示和生成
        rag_chain = (
            {
                "context": retriever | format_docs,  # 检索并格式化文档
                "question": RunnablePassthrough(),  # 传递用户查询
                "retrieved_docs": retriever,  # 原始检索文档
                "history": lambda x: format_history(chat_history)  # 对话历史
            }
            | RunnablePassthrough.assign(answer=qwen_generate)  # 调用生成函数
            | (lambda x: {  # 返回答案和检索内容
                "answer": x["answer"],
                "retrieved_docs": x["context"]
            })
        )

        logger.info("RAG chain built successfully")
        return rag_chain
    except Exception as e:
        logger.error(f"Failed to build RAG chain: {str(e)}")
        raise


def process_pdf(pdf_file):
    """处理上传的 PDF 文件，构建新的向量数据库和 RAG 链

    Args:
        pdf_file: Gradio 上传的文件对象，包含临时路径

    Returns:
        str: 处理状态消息（成功或错误提示）

    Raises:
        Exception: 如果 PDF 处理或 RAG 链构建失败

    Notes:
        - 支持 Gradio 文件上传，处理临时文件
        - 每次上传创建新向量数据库，删除旧数据库
        - 清空聊天历史，确保新 PDF 的问答隔离
    """
    global rag_chain, qwen_client, chat_history, current_vector_db
    try:
        # 检查 pdf_file 类型，确保非空
        logger.debug(f"PDF file type: {type(pdf_file)}")
        if pdf_file is None:
            return "请上传 PDF 文件！"

        # 获取 Gradio 上传文件的临时路径
        tmp_path = pdf_file.name if hasattr(pdf_file, 'name') else pdf_file
        logger.debug(f"Processing PDF file: {tmp_path}")

        # 验证文件存在
        if not os.path.exists(tmp_path):
            return f"PDF 文件 {tmp_path} 不存在！"

        # 生成唯一的向量数据库路径：基于文件名和时间戳
        pdf_basename = os.path.splitext(os.path.basename(tmp_path))[0]
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        vector_db_path = f"./chroma_db_{pdf_basename}_{timestamp}"
        logger.info(f"Creating new vector database at {vector_db_path}")

        # 删除旧向量数据库，释放磁盘空间
        if current_vector_db and os.path.exists(current_vector_db):
            shutil.rmtree(current_vector_db)
            logger.info(f"Deleted old vector database at {current_vector_db}")

        # 提取 PDF 文本
        documents = extract_text_from_pdf(tmp_path)

        # 初始化 Qwen-Plus 客户端（仅首次）
        if qwen_client is None:
            qwen_client = initialize_qwen_client()

        # 构建 RAG 链
        rag_chain = build_rag_chain(documents, qwen_client, vector_db_path)
        current_vector_db = vector_db_path  # 更新当前向量库路径

        # 清空聊天历史
        chat_history = []

        return f"PDF 上传并处理成功！新向量数据库创建于 {vector_db_path}。请在聊天框中输入查询。"
    except Exception as e:
        logger.error(f"Failed to process PDF: {str(e)}")
        return f"处理 PDF 失败：{str(e)}"

def chat_with_rag(query: str):
    """处理用户查询，返回答案、检索内容和聊天历史

    Args:
        query (str): 用户输入的查询（如 "What is the main topic?"）

    Returns:
        tuple: (答案, 检索到的文档内容, 格式化的聊天历史)

    Raises:
        Exception: 如果 RAG 链未初始化或查询执行失败

    Notes:
        - 支持多轮对话，更新聊天历史
        - 返回检索内容，增强答案透明度
        - 日志记录查询和检索信息
    """
    global rag_chain, chat_history
    try:
        if rag_chain is None:
            return "请先上传 PDF 文件！", "", chat_history

        # 执行查询
        result = rag_chain.invoke(query)  # 调用 RAG 链
        answer = result["answer"]  # 提取答案
        retrieved_docs = result["retrieved_docs"]  # 提取检索内容
        logger.info(f"Query executed successfully: {query}")
        logger.debug(f"Retrieved documents:\n{retrieved_docs}")

        # 更新聊天历史
        chat_history.append(("用户", query))
        chat_history.append(("助手", answer))

        # 格式化聊天历史为显示
        history_text = ""
        for role, text in chat_history:
            history_text += f"**{role}**: {text}\n\n"

        return answer, retrieved_docs, history_text
    except Exception as e:
        logger.error(f"Failed to execute query: {str(e)}")
        return f"查询失败：{str(e)}", "", chat_history


def clear_history():
    """清空聊天历史，重置对话

    Returns:
        tuple: (清空提示, 空答案)

    Notes:
        - 清空全局 chat_history
        - 用于重新开始对话
    """
    global chat_history
    chat_history = []
    return "聊天历史已清空！", ""


def main():
    """启动 Gradio 界面，提供 PDF 上传和问答功能

    Notes:
        - 使用 Gradio Blocks 构建界面
        - 包含 PDF 上传、聊天交互、历史清空和日志显示
        - 界面支持多轮对话和检索内容展示
    """
    with gr.Blocks(title="RAG 问答系统") as demo:
        gr.Markdown("# RAG 问答系统")  # 标题
        gr.Markdown("上传 PDF 文件，通过聊天框查询文档内容，支持多轮对话。")  # 说明

        # PDF 上传组件
        pdf_input = gr.File(label="上传 PDF 文件", file_types=[".pdf"])  # 文件上传框
        pdf_output = gr.Textbox(label="PDF 处理状态")  # 处理状态显示
        pdf_input.change(
            fn=process_pdf,  # 调用 PDF 处理函数
            inputs=pdf_input,
            outputs=pdf_output
        )

        # 聊天组件
        with gr.Row():  # 横向布局
            query_input = gr.Textbox(
                label="输入查询", placeholder="例如：What is the main topic of the document?")  # 查询输入框
            submit_button = gr.Button("提交")  # 提交按钮
            clear_button = gr.Button("清空历史")  # 清空历史按钮
        chat_output = gr.Textbox(label="答案")  # 答案显示框
        retrieved_output = gr.Textbox(label="检索到的文档内容", lines=10)  # 检索内容显示框
        history_output = gr.Textbox(label="聊天历史", lines=10)  # 聊天历史显示框

        submit_button.click(
            fn=chat_with_rag,  # 调用查询处理函数
            inputs=query_input,
            outputs=[chat_output, retrieved_output,
                     history_output]  # 输出答案、检索内容和历史
        )
        clear_button.click(
            fn=clear_history,  # 调用历史清空函数
            inputs=None,
            outputs=[history_output, chat_output]  # 重置历史和答案
        )

        # 日志输出
        gr.Markdown("### 日志")  # 日志标题
        log_output = gr.Textbox(label="日志输出", lines=5)  # 日志显示框（当前未绑定，查看控制台）

    demo.launch()  # 启动 Gradio 界面，默认端口 7860


if __name__ == "__main__":
    main()  # 程序入口，运行 Gradio 界面

```

2. 运行主程序：
   ```bash
   python main.py
   ```
3. 浏览器会自动打开 Gradio 界面（默认端口 7860）。
![在这里插入图片描述](https://i-blog.csdnimg.cn/direct/6815caa0cc8f40cb9db77b2f5f9069f2.png)

---

## 使用说明

1. **上传 PDF**：
   - 在界面点击“上传 PDF 文件”，选择本地 PDF。
   - 处理完成后，状态框显示向量数据库路径。

2. **提问与交互**：
   - 在“输入查询”框输入问题（如“What is the main topic?”）。
   - 点击“提交”，查看答案和检索内容。
   - “聊天历史”实时更新对话记录。

3. **清空历史**：
   - 点击“清空历史”按钮，重置对话。

4. **日志查看**：
   - 界面底部显示操作日志，详细日志可见终端。

---

## 项目结构

```
├── main.py          # 主程序入口
├── README.md        # 项目说明文档
├── chroma_db_*      # 动态生成的向量数据库文件夹
```

- **main.py**：
  - `extract_text_from_pdf`：PDF 文本提取。
  - `build_rag_chain`：RAG 管道构建。
  - `chat_with_rag`：查询处理。
  - `main`：Gradio 界面逻辑。

---

## 注意事项

1. **PDF 限制**：
   - 仅支持文本 PDF，不支持扫描版或图片 PDF。
   - 文件过大可能导致处理时间增加。

2. **API 依赖**：
   - 需稳定网络连接，确保 DashScope API 可用。
   - API 调用受配额限制，详见阿里云文档。

3. **存储管理**：
   - 每次上传 PDF 会创建新向量数据库，旧数据库自动删除。
   - 定期清理磁盘空间，避免占用过多。

---

## 未来改进

- **多文档支持**：同时处理多个 PDF。
- **离线模式**：集成本地模型，摆脱 API 依赖。
- **答案优化**：增强生成内容的多样性和深度。
- **界面升级**：添加更多交互功能，如导出聊天记录。
