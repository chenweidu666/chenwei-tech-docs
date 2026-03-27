
# vLLM 使用指南

## 1. 概述

vLLM 是一个高效的大语言模型（LLM）推理和服务库，针对 GPU 和 CPU 环境优化。本指南详细介绍了 vLLM（0.8.3 版本）的安装步骤、使用 ModelScope 下载 `qwen/Qwen2-0.5B-Instruct` 模型、基本使用示例、常见问题排查（包括 `psutil` 版本冲突和 `ValueError: Invalid repository ID` 错误）以及进阶配置。

## 2. 前置条件

### 硬件
- **推荐**：NVIDIA GPU，支持 CUDA 11.8 或 12.1；CPU 也可使用（性能较低）。
- **GPU 内存需求**：`Qwen2-0.5B-Instruct` 约需 1–2GB 显存。
- **磁盘空间**：约 1GB 用于模型文件。

### 软件
- **Python**：3.8–3.12。
- **NVIDIA 驱动和 CUDA Toolkit**（GPU 环境）。
- **pip**：建议 25.1.1 或更高版本。

### 可选
- **Conda 或 Python virtualenv**：用于环境隔离。
- **ModelScope SDK**：用于下载模型。

## 3. 安装步骤

### 步骤 1：创建虚拟环境
为避免依赖冲突，创建一个干净的虚拟环境：

```bash
# 使用 Conda
conda create -n modelscope_env python=3.12
conda activate modelscope_env
```

### 步骤 2：升级 pip
确保 pip 为最新版本：

```bash
pip install --upgrade pip
```

### 步骤 3：安装 PyTorch
根据 CUDA 版本安装兼容的 PyTorch（以下为 CUDA 12.1 示例）：

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

验证 PyTorch：

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

预期输出：PyTorch 版本（如 `2.4.1`）和 `True`（若有 GPU）。

### 步骤 4：安装 ModelScope SDK
为从 ModelScope 下载模型，安装 ModelScope 库：

```bash
pip install modelscope
```

### 步骤 5：安装 vLLM
安装 vLLM 0.8.3：

```bash
pip install vllm==0.8.3
```

验证安装：

```bash
python -c "import vllm; print(vllm.__version__)"
```

预期输出：`0.8.3`

## 4. 下载模型

### 使用 ModelScope 下载 `Qwen2-0.5B-Instruct`
下载 `qwen/Qwen2-0.5B-Instruct` 模型到本地：

```python
from modelscope.hub.snapshot_download import snapshot_download
from modelscope import AutoModelForCausalLM, AutoTokenizer
import torch
import gradio as gr

# 目标文件夹路径
model_dir = "./models/"

# 下载模型到指定目录
model_id = "Qwen/Qwen2-0.5B-Instruct"
model_path = snapshot_download(model_id, cache_dir=model_dir)

# 加载本地模型和分词器
model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto", torch_dtype=torch.float16)
tokenizer = AutoTokenizer.from_pretrained(model_path)

# 打印设备信息
print(f"模型加载的设备: {model.device}")

# 定义推理函数
def generate_response(prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        inputs.input_ids,
        max_length=512,
        do_sample=True,
        top_p=0.9,
        temperature=0.7,
        pad_token_id=tokenizer.eos_token_id
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

# 创建 Gradio 界面
with gr.Blocks() as demo:
    gr.Markdown("## 与 Qwen/Qwen2-0.5B-Instruct 问答")
    msg = gr.Textbox(label="输入你的问题")
    response = gr.Textbox(label="模型回答", lines=10)
    submit_btn = gr.Button("提交")

    # 定义消息处理逻辑
    def respond(message):
        bot_message = generate_response(message)
        return bot_message

    # 绑定事件
    submit_btn.click(respond, inputs=msg, outputs=response)

# 启动 Gradio 应用
demo.launch()
```

运行脚本：

```bash
python 1_Down&Test_MS_model
```

![在这里插入图片描述](https://i-blog.csdnimg.cn/direct/95ab1ee4ed1f411a9d280f452edb328c.png)

## 5. 基本使用

### 1. 命令行推理
使用本地模型路径启动 vLLM 服务器：

```bash
vllm serve ./models/Qwen2-0.5B-Instruct --tensor-parallel-size 1 --port 8080
```

服务器将在 `http://localhost:8000` 提供 OpenAI 兼容的 API。

### 2. Python 脚本推理
通过 Python 脚本进行推理：

```python
from modelscope.hub.snapshot_download import snapshot_download
from vllm import LLM, SamplingParams
import gradio as gr

# 目标文件夹路径
model_dir = "./models/"

# 下载模型到指定目录
model_id = "Qwen/Qwen2-0.5B-Instruct"
model_path = snapshot_download(model_id, cache_dir=model_dir)

# 加载模型到 vLLM
llm = LLM(model=model_path, tensor_parallel_size=1)  # tensor_parallel_size 根据 GPU 数量调整

# 定义推理函数
def generate_response(prompt):
    # 设置生成参数
    sampling_params = SamplingParams(
        max_tokens=512,
        top_p=0.9,
        temperature=0.7,
    )

    # 使用 vLLM 进行推理
    outputs = llm.generate([prompt], sampling_params)

    # 提取生成的文本
    response = outputs[0].outputs[0].text
    return response

# 创建 Gradio 界面
with gr.Blocks() as demo:
    gr.Markdown("## 与 Qwen/Qwen2-0.5B-Instruct 问答")
    msg = gr.Textbox(label="输入你的问题")
    response = gr.Textbox(label="模型回答", lines=10)
    submit_btn = gr.Button("提交")

    # 定义消息处理逻辑
    def respond(message):
        bot_message = generate_response(message)
        return bot_message

    # 绑定事件
    submit_btn.click(respond, inputs=msg, outputs=response)

# 启动 Gradio 应用
demo.launch()
```

![在这里插入图片描述](https://i-blog.csdnimg.cn/direct/3f0201d5d22b4671af942f42b28f1f25.png)

### 3. OpenAI 兼容 API
使用 curl 测试 API：

```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "./models/Qwen2-0.5B-Instruct",
    "prompt": "你好，世界！",
    "max_tokens": 50,
    "temperature": 0.7
  }'
```

或使用 Python `openai` 客户端：

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")
response = client.completions.create(
    model="./models/Qwen2-0.5B-Instruct",
    prompt="你好，世界！",
    max_tokens=50
)
print(response.choices[0].text)
```

### 4. CPU 推理
在 CPU 环境下运行：

```bash
vllm serve ./models/Qwen2-0.5B-Instruct --device cpu
```

或在 Python 中：

```python
model = LLM(model="./models/Qwen2-0.5B-Instruct", device="cpu")
```

## 6. 性能对比

| 特性                  | 使用 `vllm` 的代码               | 使用 `transformers` 的代码       |
|-----------------------|----------------------------------|----------------------------------|
| **加载速度**          | 快                              | 慢                              |
| **推理速度**          | 快                              | 慢                              |
| **内存占用**          | 低                              | 高                              |
| **多 GPU 支持**       | 支持（通过 `tensor_parallel_size`） | 支持（通过 `device_map="auto"`） |
| **适用场景**          | 大模型、高并发推理              | 小模型、通用推理                |

## 7. 常见问题

### `ValueError: Invalid repository ID`
- **原因**：模型路径或 ID 错误。
- **解决**：检查模型路径或 ID 是否正确。

### `psutil` 版本冲突
- **原因**：安装的 `psutil` 版本不兼容。
- **解决**：卸载并重新安装指定版本。

## 8. 进阶配置

### 多 GPU 支持
```bash
vllm serve ./models/Qwen2-0.5B-Instruct --tensor-parallel-size 2
```

### 自定义端口
```bash
vllm serve ./models/Qwen2-0.5B-Instruct --port 8080
```
