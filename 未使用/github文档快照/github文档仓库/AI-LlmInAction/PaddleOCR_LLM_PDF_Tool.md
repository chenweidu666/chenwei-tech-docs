# P5-OCR-结合PaddleOCR和LLM的PDF转换工具

## 项目概述

**PDF到Markdown转换器** 是一个基于Python的应用程序，用于将PDF文件中的文本转换为格式良好的Markdown文档。它利用PaddleOCR进行光学字符识别（OCR）从PDF页面中提取文本，并使用Qwen-plus大语言模型将提取的文本结构化为Markdown格式。该应用程序通过Gradio提供了一个用户友好的Web界面，允许用户上传PDF、处理文件并查看生成的Markdown输出。

### 主要功能
- **多页PDF处理**：从PDF的所有页面提取文本并转换为Markdown。
- **PaddleOCR进行OCR**：使用PaddleOCR（PP-OCRv4）进行高精度的文本识别，优化为中文文本（`lang="ch"`）。
- **Qwen-plus生成Markdown**：通过DashScope API使用Qwen-plus模型将OCR输出结构化为包含标题、列表、表格和段落的Markdown。
- **Gradio Web界面**：提供直观的界面，用于上传PDF、配置选项、查看渲染的Markdown和结构化JSON输出。
- **处理时间记录**：记录每页的OCR和Markdown处理时间以及总OCR处理时间，用于性能监控。
- **输出管理**：在每次运行前清空并重新生成`mdges`目录，存储每页和最终的Markdown文件。

## 依赖项

项目需要以下Python库：

- **paddleocr**：用于从PDF中提取OCR文本。
- **paddlepaddle**：PaddleOCR的后端。
- **gradio**：用于Web界面。
- **openai**：通过DashScope API与Qwen-plus模型交互。
- **shutil**、**tempfile**、**os**、**logging**、**time**：用于文件处理、临时文件和日志记录的标准Python库。

安装依赖项：
```bash
pip install paddleocr paddlepaddle gradio openai
```

## 使用方法

### 前提条件
- **Python环境**：Python 3.8+，安装了所需库。
- **DashScope API密钥**：Qwen-plus模型的有效API密钥。
- **网络访问**：对于外部访问，确保服务器上的7860端口已开放。

### 运行应用程序
1. **保存脚本**：

```python
import gradio as gr
from paddleocr import PaddleOCR
import os
import tempfile
from openai import OpenAI
import shutil
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang="ch", det=True, rec=True, type="ocr", ocr_version="PP-OCRv4")

# Initialize large language model client
client = OpenAI(
    api_key="你的KEY",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# Split Markdown content into chunks to avoid token limits
def split_markdown_content(content, max_chars=300000):
    """Split Markdown content into chunks, each under max_chars characters"""
    chunks = []
    current_chunk = []
    current_length = 0

    for line in content.split("\n"):
        line_length = len(line)
        if current_length + line_length > max_chars:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_length = line_length
        else:
            current_chunk.append(line)
            current_length += line_length

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks

def process_pdf(pdf_file, use_final_model):
    # Create mdges folder (clear existing contents if any)
    output_dir = os.path.join(os.getcwd(), "mdges")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)  # Delete directory and all contents
    os.makedirs(output_dir, exist_ok=True)  # Create fresh directory

    # Process uploaded PDF file (binary format)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(pdf_file)
        pdf_path = temp_file.name

    # Use PaddleOCR to parse all pages of the PDF
    start_time = time.time()
    result = ocr.ocr(pdf_path, cls=True)
    total_ocr_time = time.time() - start_time
    logger.info(f"Total OCR processing time for all pages: {total_ocr_time:.2f} seconds")

    # Delete temporary file
    os.unlink(pdf_path)

    # Store OCR results and preliminary Markdown for each page
    page_markdowns = []
    all_texts = []
    all_boxes = []
    all_scores = []

    # Process each page
    for page_idx, page_result in enumerate(result):
        # Log time for processing this page
        page_start_time = time.time()

        # Extract recognition results for the page
        boxes = [line[0] for line in page_result]
        texts = [line[1][0] for line in page_result]
        scores = [line[1][1] for line in page_result]

        # Store OCR results
        all_texts.extend(texts)
        all_boxes.extend(boxes)
        all_scores.extend(scores)

        # Feed OCR results to the large model to generate Markdown
        ocr_text = "\n".join(texts)
        prompt = f"""
        以下是从PDF第{page_idx + 1}页中提取的OCR文本，请将其整理成Markdown格式：
        {ocr_text}

        请确保：
        - 使用适当的标题（如#、##）。
        - 列表项使用-或*。
        - 段落之间空一行。
        - 如果包含表格，请使用Markdown表格格式。
        """

        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant skilled in formatting text into Markdown.'},
                {'role': 'user', 'content': prompt}
            ],
        )

        # Extract Markdown content for the page
        page_markdown = completion.choices[0].message.content
        page_markdowns.append(f"## Page {page_idx + 1}\n{page_markdown}")

        # Save per-page Markdown
        page_md_file = os.path.join(output_dir, f"page_{page_idx + 1}.md")
        with open(page_md_file, "w", encoding="utf-8") as f:
            f.write(page_markdown)

        # Log time taken for this page
        page_time = time.time() - page_start_time
        logger.info(f"OCR and Markdown processing time for page {page_idx + 1}: {page_time:.2f} seconds")

    # Decide whether to use the final model for synthesis
    if use_final_model and page_markdowns:
        # Combine all page Markdowns
        combined_markdown = "\n\n".join(page_markdowns)

        # Split Markdown content into chunks
        markdown_chunks = split_markdown_content(combined_markdown, max_chars=300000)
        final_chunks = []

        # Process each chunk with the large model
        for chunk_idx, chunk in enumerate(markdown_chunks):
            final_prompt = f"""
            以下是从PDF部分页面提取并初步整理的Markdown内容（块{chunk_idx + 1}/{len(markdown_chunks)}），请将其整理为Markdown格式：
            {chunk}

            请确保：
            - 统一标题层级（如#、##）。
            - 优化结构，保持内容逻辑清晰。
            - 列表项使用-或*，段落之间空一行。
            - 表格使用Markdown表格格式。
            - 删除冗余的分页标记（如## Page X），但保留页面内容的逻辑顺序。
            """

            final_completion = client.chat.completions.create(
                model="qwen-plus",
                messages=[
                    {'role': 'system', 'content': 'You are a helpful assistant skilled in formatting and optimizing Markdown.'},
                    {'role': 'user', 'content': final_prompt}
                ],
            )

            # Extract refined Markdown chunk
            final_chunks.append(final_completion.choices[0].message.content)

        # Combine all chunks
        final_markdown = "\n\n".join(final_chunks)
    else:
        # Directly combine per-page Markdowns
        final_markdown = "\n\n".join(page_markdowns) if page_markdowns else "# No content extracted"

    # Save final Markdown file
    final_md_file = os.path.join(output_dir, "final_ocr_result.md")
    with open(final_md_file, "w", encoding="utf-8") as f:
        f.write(final_markdown)

    # Structured storage (LangChain Document object)
    document = {
        "page_content": final_markdown,
        "metadata": {
            "source": "uploaded_pdf",
            "output_markdown": final_md_file,
            "per_page_markdowns": [os.path.join(output_dir, f"page_{i + 1}.md") for i in range(len(page_markdowns))],
            "ocr_texts": all_texts,
            "boxes": all_boxes,
            "scores": all_scores,
            "timestamp": "2025-05-09",
            "type": "ocr_to_markdown",
            "model": "qwen-plus",
            "page_count": len(result),
            "use_final_model": use_final_model
        }
    }

    return final_markdown, document

# Create Gradio interface
interface = gr.Interface(
    fn=process_pdf,
    inputs=[
        gr.File(label="Upload PDF File", type="binary"),
        gr.Checkbox(label="Use Final Model for Markdown Synthesis", value=True)
    ],
    outputs=[
        gr.Markdown(label="Final Markdown Output"),
        gr.JSON(label="Structured Document")
    ],
    title="PDF to Markdown Converter (Multi-Page)",
    description="Upload a PDF file to convert the text of all its pages to Markdown format using OCR and Qwen-plus. The final Markdown will be rendered with proper formatting."
)

# Run Gradio application
interface.launch(server_name="0.0.0.0", server_port=7860)
```

2. **执行脚本**：
   - Gradio界面将在`http://<服务器IP>:7860`启动（本地为`http://localhost:7860`）。
![在这里插入图片描述](https://i-blog.csdnimg.cn/direct/e2b237ecc37f4fbd9a69c0e0ae8f0df7.png)

3. **使用Gradio界面**：
   - **上传PDF**：通过文件上传组件选择PDF文件。
   - **配置选项**：勾选或取消勾选“使用最终模型进行Markdown合成”以启用/禁用Qwen-plus优化。
   - **提交**：点击提交按钮处理PDF。
   - **查看输出**：
     - **Markdown输出**：在Gradio界面中显示渲染的Markdown，包含标题、列表和表格。
     - **结构化文档**：JSON输出，包含Markdown内容和元数据（例如，OCR文本、边界框）。
   - **检查文件**：Markdown文件保存在`mdges`目录（`page_1.md`、`page_2.md`、`final_ocr_result.md`）。

### 示例输出
- **控制台日志**：
  ```
  2025-05-09 12:34:56,123 - INFO - 所有页面的总OCR处理时间：10.25秒
  2025-05-09 12:34:57,456 - INFO - 第1页的OCR和Markdown处理时间：2.34秒
  2025-05-09 12:34:59,789 - INFO - 第2页的OCR和Markdown处理时间：2.45秒
  ```
- **Markdown输出**（示例）：
  ```markdown
  # 报告标题
  ## 第1页
  - 项目一
  - 项目二

  | 列1 | 列2 |
  |-----|-----|
  | 值1 | 值2 |

  ## 第2页
  ### 第二部分
  - 项目三
  - 项目四
  ```
- **文件**：
  - `mdges/page_1.md`、`mdges/page_2.md`等：每页的Markdown文件。
  - `mdges/final_ocr_result.md`：所有页面的合并Markdown。

## 技术细节

### 工作流程
1. **PDF上传**：
   - 用户通过Gradio界面上传PDF文件。
   - 使用`tempfile`保存临时文件。

2. **OCR处理**：
   - PaddleOCR（PP-OCRv4）处理PDF的所有页面，提取文本、边界框和置信度得分。
   - 记录总OCR处理时间和每页处理时间。

3. **Markdown生成**：
   - 对每页，OCR提取的文本通过DashScope API发送到Qwen-plus，生成结构化的Markdown。
   - 每页的Markdown文件保存为`page_<n>.md`。

4. **最终合成**（可选）：
   - 如果启用“使用最终模型进行Markdown合成”，Qwen-plus会优化合并的Markdown，删除冗余的页面标记。
   - 最终Markdown保存为`final_ocr_result.md`。

5. **输出**：
   - Gradio界面显示渲染的Markdown和包含元数据的JSON对象。
   - 每次运行前清空`mdges`目录，避免文件冲突。

### 主要组件
- **PaddleOCR**：
  - 配置为`lang="ch"`，优化中文文本识别。
  - 使用PP-OCRv4模型，精度高。
  - 逐页处理PDF，提取文本和边界框数据。

- **Qwen-plus**：
  - 通过OpenAI兼容的DashScope API访问。
  - 将原始OCR文本格式化为包含标题、列表和表格的Markdown。
  - 通过分块处理（`max_chars=300000`）支持大输入。

- **Gradio**：
  - 提供文件上传、复选框输入、Markdown渲染和JSON输出的Web界面。
  - 在`server_name="0.0.0.0"`和`server_port=7860`上运行，支持网络访问。

- **日志记录**：
  - 使用Python的`logging`模块记录处理时间。
  - 记录总OCR时间和每页的处理时间（包括OCR提取和Markdown生成）。

### 文件结构
- **输入**：通过Gradio上传的PDF文件。
- **输出**：
  - `mdges/page_<n>.md`：每页的Markdown。
  - `mdges/final_ocr_result.md`：所有页面的合并Markdown。
  - Gradio界面中的结构化JSON输出。

## 故障排除

### 常见问题
- **端口冲突**：
  - 如果7860端口被占用：
    ```bash
    lsof -i :7860
    kill -9 <pid>
    ```
    - 或更改脚本中的`server_port`（例如，`server_port=7861`）。

- **无文本检测**：
  - 确保PDF页面包含清晰的文本或文本图像。
  - 添加调试日志：
    ```python
    logger.info(f"第{page_idx + 1}页的OCR结果：{page_result}")
    ```
    - 放置在`boxes = [line[0] for line in page_result]`之后。

- **Qwen-plus API错误**：
  - 验证API密钥和DashScope配额。
  - 使用`use_final_model=False`测试，跳过最终合成。

- **Gradio问题**：
  - 确保安装了Gradio 4.x：
    ```bash
    pip show gradio
    pip install --upgrade gradio
    ```
  - 检查防火墙设置：
    ```bash
    sudo ufw allow 7860
    ```

### 性能优化
- **启用GPU**：加速OCR：
  ```python
  ocr = PaddleOCR(use_angle_cls=True, lang="ch", det=True, rec=True, type="ocr", ocr_version="PP-OCRv4", use_gpu=True)
  ```
  - 需要`paddlepaddle-gpu`。
- **减少API调用**：对于大型PDF，设置`use_final_model=False`以跳过最终合成。
- **监控日志**：使用每页时间日志识别瓶颈。

## 未来改进
- **表格和图像检测**：在PaddleOCR中集成`use_pp_structure=True`进行布局分析。
- **图像可视化**：添加`draw_ocr`生成带边界框的注释图像。
- **日志文件输出**：将日志保存到`mdges`目录中的文件。
- **多语言支持**：添加其他语言支持（例如，`lang="en"`）。
