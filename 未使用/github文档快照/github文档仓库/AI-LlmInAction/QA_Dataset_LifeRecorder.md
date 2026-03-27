# 问答数据集生成器-用大模型记录我的人生
## 项目简介

**问答数据集生成器** 是一个基于 PyQt5 和阿里云 DashScope API 的桌面应用程序，旨在通过大语言模型与用户深度互动，记录和整理个人人生经历，生成高质量的问答数据集。  
该工具利用大模型的智能对话能力，基于用户已有数据（如历史问答、个人总结）进行个性化交流，挖掘并保存人生故事、感悟和经验，适用于自传记录、个人知识库构建或大模型微调等场景。

项目通过直观的图形化界面（GUI）实现，用户可以：
- **智能生成问题**：自动生成与用户经历相关的不重复问题，引导深入回忆和表达。
- **答案记录与优化**：输入人生片段或感悟，智能润色答案，使内容更流畅、深刻。
- **数据集管理**：以 JSON 格式存储问答数据，支持实时预览、编辑和长期保存。
- **人生总结**：基于历史问答和用户输入，生成自然流畅的个人经历总结，或更新已有总结内容。

这个工具不仅是技术与生活的结合，更是记录人生、沉淀记忆的智能助手，让每段故事都以结构化的方式留存。

## 功能特性

1. **问题生成**：
   - 使用阿里云 DashScope API（支持 Qwen-Plus 等模型）生成与历史问题不重复的新问题。
   - 支持自定义提示词，基于用户提供的总结或历史数据生成问题。

2. **答案润色**：
   - 自动润色用户输入的答案，使其更流畅、专业。
   - 支持手动修改润色结果。

3. **数据集管理**：
   - 支持加载或创建 JSON 格式的问答数据集。
   - 提供实时预览和手动编辑功能，保存修改后的数据集。

4. **总结与经历管理**：
   - 基于历史问答对和用户经历生成自然流畅的总结。
   - 支持替换 JSON 文件中的总结内容。

5. **模型选择**：
   - 动态获取阿里云支持的模型列表，用户可切换模型（如 Qwen-Plus、Qwen-Max）。
   - 默认使用 Qwen-Plus，确保高效推理。

6. **用户友好界面**：
   - 基于 PyQt5 构建，界面简洁，支持多行输入、状态提示。
   - 提供“换一个问题”“提交答案”“确认保存”等便捷操作。

## 技术栈

- **编程语言**：Python 3.8+
- **GUI框架**：PyQt5
- **大模型API**：阿里云 DashScope API（需配置 API_KEY 和 BASE_URL）
- **依赖库**：
  - `requests`：用于获取模型列表。
  - `openai`：调用 DashScope API。
  - `json`：处理数据集存储。
- **多线程**：使用 QThread 实现异步 API 调用，避免界面卡顿。

## 安装与运行

### 1. 环境要求
- Python 3.8 或更高版本
- 安装依赖：
  ```bash
  pip install PyQt5 requests openai
  ```

### 2. 配置 API
1. 获取阿里云 DashScope API 密钥：
   - 注册阿里云账号，访问 [DashScope 控制台](https://bailian.console.aliyun.com/?tab=api#/api)。
   - 创建 API 密钥（API_KEY）。
2. 编辑 `config.py` 文件，配置以下内容：
   ```python
   API_KEY = "your_api_key_here"
   BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
   AUTH_HEADER = {"Authorization": f"Bearer {API_KEY}"}
   ```

### 3. 运行程序
1. 项目代码如下：

```
import sys
import os
import json
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QPushButton, QFileDialog, 
                             QVBoxLayout, QWidget, QStatusBar, QDialog, QHBoxLayout, QComboBox, QLabel)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from openai import OpenAI
from config import API_KEY, BASE_URL, AUTH_HEADER

# 工作线程类，用于处理大模型推理
class Worker(QThread):
    result_signal = pyqtSignal(str)  # 返回推理结果
    error_signal = pyqtSignal(str)   # 返回错误信息

    def __init__(self, prompt, model="qwen-plus"):
        super().__init__()
        self.prompt = prompt
        self.model = model

    def run(self):
        try:
            client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
            completion = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": self.prompt}]
            )
            result = completion.choices[0].message.content.strip()
            self.result_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(f"API调用失败: {str(e)}")

# 获取阿里云支持的模型列表
def get_aliyun_models():
    try:
        response = requests.get(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/models",
            headers=AUTH_HEADER
        )
        response.raise_for_status()
        models = response.json()
        return [model['id'] for model in models['data']]
    except Exception as e:
        print(f"获取模型列表失败: {e}")
        return []

# JSON操作函数
def load_json(file_path):
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"JSON文件 {file_path} 解析失败，返回空列表")
        return []

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_summary_answer(file_path):
    data = load_json(file_path)
    for item in data:
        if item.get('question') == 'Summary':
            return item.get('answer')
    return None

def check_duplicate(question, history):
    return any(item["question"] == question for item in history)

def replace_summary_answer(file_path, new_answer):
    data = load_json(file_path)
    for item in data:
        if item.get('question') == 'Summary':
            item['answer'] = new_answer
            save_json(file_path, data)
            return True
    return False

# 初始数据集选择对话框
class StartDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数据集选择")
        self.setGeometry(200, 200, 300, 150)
        self.json_file = None

        layout = QVBoxLayout()
        layout.addWidget(QLabel("请选择或创建数据集："))
        self.load_btn = QPushButton("加载已有数据集")
        self.create_btn = QPushButton("创建新数据集")
        layout.addWidget(self.load_btn)
        layout.addWidget(self.create_btn)
        layout.addStretch()
        self.setLayout(layout)

        self.load_btn.clicked.connect(self.load_dataset)
        self.create_btn.clicked.connect(self.create_dataset)

    def load_dataset(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择已有JSON文件", "", "JSON Files (*.json)")
        if file_path:
            self.json_file = file_path
            self.accept()

    def create_dataset(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "创建新JSON文件", "", "JSON Files (*.json)")
        if file_path:
            self.json_file = file_path
            save_json(file_path, [])
            self.accept()

# 主窗口类
class MainWindow(QMainWindow):
    def __init__(self, json_file):
        super().__init__()
        self.setWindowTitle("问答数据集生成器")
        self.setGeometry(100, 100, 1200, 800)
        self.json_file = json_file
        self.history = load_json(json_file)
        self.current_question = ""
        self.summary = get_summary_answer(json_file) or "暂无总结内容"

        # 初始化模型选择
        self.alibaba_models = get_aliyun_models()
        self.selected_model = "qwen-plus" if "qwen-plus" in self.alibaba_models else (self.alibaba_models[0] if self.alibaba_models else "qwen-plus")

        # 设置全局样式
        self.setStyleSheet("""
            QTextEdit { font-size: 16px; border: 1px solid #ccc; border-radius: 5px; padding: 5px; background-color: #f9f9f9; }
            QPushButton { font-size: 14px; background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 8px; min-width: 100px; }
            QPushButton:hover { background-color: #45a049; }
            QComboBox { font-size: 14px; padding: 5px; min-width: 150px; }
            QStatusBar { font-size: 12px; color: #555; }
            QLabel { font-size: 14px; color: #333; }
        """)

        # 初始化UI
        self.init_ui()
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 绑定事件
        self.change_btn.clicked.connect(self.generate_question)
        self.submit_btn.clicked.connect(self.polish_answer)
        self.confirm_btn.clicked.connect(self.save_data)
        self.model_selector.currentTextChanged.connect(self.update_selected_model)

        # 初次生成问题
        self.generate_question()

    def init_ui(self):
        # 主容器
        main_layout = QVBoxLayout()

        # 顶部区域：提示词和模型选择
        top_widget = QWidget()
        top_layout = QHBoxLayout()
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("请输入问题生成的提示词...")
        self.prompt_edit.setText(self.summary)
        self.prompt_edit.setFixedHeight(120)  # 增加高度，便于多行输入
        top_layout.addWidget(QLabel("提示词："))
        top_layout.addWidget(self.prompt_edit, stretch=3)

        self.model_selector = QComboBox()
        self.model_selector.addItems(self.alibaba_models)
        self.model_selector.setCurrentText(self.selected_model)
        top_layout.addWidget(QLabel("模型："))
        top_layout.addWidget(self.model_selector, stretch=1)

        self.summarize_btn = QPushButton("总结问答对和经历")
        self.replace_experience_btn = QPushButton("替换个人经历")
        top_layout.addWidget(self.summarize_btn)
        top_layout.addWidget(self.replace_experience_btn)
        top_widget.setLayout(top_layout)
        main_layout.addWidget(top_widget)

        # 中间区域：问题生成和答案编辑
        mid_widget = QWidget()
        mid_layout = QHBoxLayout()

        # 左侧：问题和答案输入
        left_layout = QVBoxLayout()
        self.question_edit = QTextEdit()
        self.question_edit.setPlaceholderText("问题将显示在这里，可手动修改...")
        self.question_edit.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.question_edit.setFixedHeight(100)  # 从60增加到100
        left_layout.addWidget(QLabel("生成的问题："))
        left_layout.addWidget(self.question_edit)

        self.answer_input = QTextEdit()
        self.answer_input.setPlaceholderText("请输入答案...")
        self.answer_input.setFixedHeight(200)  # 从120增加到200
        left_layout.addWidget(QLabel("答案输入："))
        left_layout.addWidget(self.answer_input)

        self.polished_edit = QTextEdit()
        self.polished_edit.setPlaceholderText("润色结果将显示在这里，可手动修改...")
        self.polished_edit.setStyleSheet("font-style: italic; color: #7f8c8d;")
        self.polished_edit.setFixedHeight(200)  # 从120增加到200
        left_layout.addWidget(QLabel("润色后的答案："))
        left_layout.addWidget(self.polished_edit)

        button_layout = QHBoxLayout()
        self.change_btn = QPushButton("换一个问题")
        self.submit_btn = QPushButton("提交答案")
        self.confirm_btn = QPushButton("确认保存")
        button_layout.addWidget(self.change_btn)
        button_layout.addWidget(self.submit_btn)
        button_layout.addWidget(self.confirm_btn)
        left_layout.addLayout(button_layout)
        mid_layout.addLayout(left_layout, stretch=2)

        # 右侧：数据集预览
        right_layout = QVBoxLayout()
        self.dataset_edit = QTextEdit()
        self.dataset_edit.setPlaceholderText("当前数据集内容，可手动编辑...")
        self.dataset_edit.setText(json.dumps(self.history, ensure_ascii=False, indent=4))
        right_layout.addWidget(QLabel("数据集预览："))
        right_layout.addWidget(self.dataset_edit)
        self.save_dataset_btn = QPushButton("保存数据集")
        self.save_dataset_btn.clicked.connect(self.save_dataset)
        right_layout.addWidget(self.save_dataset_btn)
        mid_layout.addLayout(right_layout, stretch=3)

        mid_widget.setLayout(mid_layout)
        main_layout.addWidget(mid_widget, stretch=1)

        # 设置主布局
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 连接信号
        self.summarize_btn.clicked.connect(self.summarize_qa_and_experience)
        self.replace_experience_btn.clicked.connect(self.replace_personal_experience)

    def update_selected_model(self, model):
        self.selected_model = model
        self.status_bar.showMessage(f"已切换模型为：{model}")

    def generate_question(self):
        self.change_btn.setEnabled(False)
        history_questions = [item["question"] for item in self.history if item["question"] != "Summary"]
        prompt = (
            f"基于以下{self.summary}和历史问题：{', '.join(history_questions) if history_questions else '无历史问题'} "
            "生成一个新的不重复问题，仅返回问题本体。"
        )
        self.worker = Worker(prompt, self.selected_model)
        self.worker.result_signal.connect(self.on_question_generated)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()
        self.status_bar.showMessage("正在生成新问题...")

    def on_question_generated(self, question):
        max_attempts = 5
        attempts = 0
        while check_duplicate(question, self.history) and attempts < max_attempts:
            self.worker = Worker(self.worker.prompt, self.selected_model)
            self.worker.result_signal.connect(self.on_question_generated)
            self.worker.error_signal.connect(self.on_error)
            self.worker.start()
            attempts += 1
            return
        if attempts >= max_attempts:
            question = f"无法生成不重复问题，请手动输入（已有 {len(self.history)} 个问题）"

        self.current_question = question
        self.question_edit.setText(question)
        self.polished_edit.clear()
        self.answer_input.clear()
        self.status_bar.showMessage("新问题已生成")
        self.change_btn.setEnabled(True)

    def polish_answer(self):
        answer = self.answer_input.toPlainText().strip()
        if not answer:
            self.status_bar.showMessage("请输入答案")
            return
        prompt = f"基于问题 '{self.current_question}'，润色以下答案，使其更流畅和专业：{answer}"
        self.submit_btn.setEnabled(False)
        self.worker = Worker(prompt, self.selected_model)
        self.worker.result_signal.connect(self.on_polish_generated)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()
        self.status_bar.showMessage("正在润色答案...")

    def on_polish_generated(self, polished):
        self.polished_edit.setText(polished)
        self.status_bar.showMessage("答案润色完成")
        self.submit_btn.setEnabled(True)

    def save_data(self):
        polished = self.polished_edit.toPlainText().strip()
        if not polished:
            self.status_bar.showMessage("请先润色答案")
            return
        final_question = self.question_edit.toPlainText().strip()
        self.history.append({"question": final_question, "answer": polished})
        save_json(self.json_file, self.history)
        self.dataset_edit.setText(json.dumps(self.history, ensure_ascii=False, indent=4))
        self.status_bar.showMessage("数据已保存")
        self.generate_question()

    def save_dataset(self):
        try:
            updated_data = json.loads(self.dataset_edit.toPlainText())
            save_json(self.json_file, updated_data)
            self.history = updated_data
            self.dataset_edit.setText(json.dumps(self.history, ensure_ascii=False, indent=4))
            self.status_bar.showMessage("数据集已保存")
        except json.JSONDecodeError:
            self.status_bar.showMessage("数据集格式错误，保存失败")

    def summarize_qa_and_experience(self):
        qa_pairs = "\n".join([f"问题: {item['question']}\n答案: {item['answer']}" for item in self.history])
        prompt = f"总结以下问答对和个人经历，生成自然流畅的文本（无需Markdown）：\n{qa_pairs}\n{self.summary}"
        self.summarize_btn.setEnabled(False)
        self.worker = Worker(prompt, self.selected_model)
        self.worker.result_signal.connect(self.on_summary_generated)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()
        self.status_bar.showMessage("正在生成总结...")

    def on_summary_generated(self, summary):
        self.summary = summary
        self.polished_edit.setText(summary)
        self.status_bar.showMessage("总结已生成")
        self.summarize_btn.setEnabled(True)

    def replace_personal_experience(self):
        new_experience = self.summary.strip()
        if replace_summary_answer(self.json_file, new_experience):
            self.prompt_edit.setText(new_experience)
            self.status_bar.showMessage("个人经历已更新至JSON文件")
            self.history = load_json(self.json_file)
            self.dataset_edit.setText(json.dumps(self.history, ensure_ascii=False, indent=4))
        else:
            self.status_bar.showMessage("未找到'Summary'项，替换失败")

    def on_error(self, error_message):
        self.status_bar.showMessage(error_message)
        self.change_btn.setEnabled(True)
        self.submit_btn.setEnabled(True)
        self.summarize_btn.setEnabled(True)

    def closeEvent(self, event):
        if self.json_file and self.history:
            save_json(self.json_file, self.history)
            self.status_bar.showMessage("程序关闭，数据已保存")
        event.accept()

# 程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    start_dialog = StartDialog()
    if start_dialog.exec_() == QDialog.Accepted and start_dialog.json_file:
        window = MainWindow(start_dialog.json_file)
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)
```

2. 运行主程序：
   ```bash
   python main.py
   ```
3. 程序启动后，选择或创建 JSON 文件作为数据集存储路径。

## 使用说明

1. **启动界面**：
   - 打开程序后，选择加载已有 JSON 文件或创建新文件。
   - ![在这里插入图片描述](https://i-blog.csdnimg.cn/direct/827dd6db62994b3398361eae391bfc5f.png)

   - JSON 文件用于存储问答对，格式为：
     ```json
     [
         {"question": "问题1", "answer": "答案1"},
         {"question": "Summary", "answer": "总结内容"}
     ]
     ```

2. **主界面操作**：
  ![在这里插入图片描述](https://i-blog.csdnimg.cn/direct/e18eb6abd9d8417ba4bf4e35de92d972.png)

   - **提示词输入**：在顶部文本框输入提示词（默认显示总结内容）。
   - **模型选择**：从下拉菜单选择模型（如 Qwen-Plus）。
   - **问题生成**：点击“换一个问题”生成新问题，显示在“生成的问题”框。
   - **答案输入与润色**：
     - 在“答案输入”框输入答案，点击“提交答案”进行润色。
     - 润色结果显示在“润色后的答案”框，可手动修改。
   - **保存数据**：点击“确认保存”将问答对存入 JSON 文件。
   - **数据集预览**：右侧显示当前数据集，可手动编辑后点击“保存数据集”。
   - **总结与经历**：
     - 点击“总结问答对和经历”生成总结，显示在润色框。
     - 点击“替换个人经历”更新 JSON 文件中的总结内容。

3. **状态提示**：
   - 底部状态栏显示操作进度（如“正在生成新问题...”）或错误信息。

## 项目结构

```
├── main.py          # 主程序入口
├── config.py        # API 配置文件
├── README.md        # 项目说明文档
```

- **main.py**：
  - `Worker`：QThread 子类，处理 API 异步调用。
  - `StartDialog`：初始对话框，选择或创建 JSON 文件。
  - `MainWindow`：主窗口，包含 GUI 和核心逻辑。
  - JSON 操作函数：`load_json`、`save_json` 等，管理数据集。
- **config.py**：存储 API 密钥和基础 URL。

## 注意事项

1. **API 依赖**：
   - 确保网络畅通，阿里云 DashScope API 需稳定连接。
   - API 调用可能受限于免费额度，建议查看阿里云文档了解配额。

2. **JSON 文件**：
   - 确保 JSON 文件格式正确，避免手动编辑导致解析错误。
   - 程序关闭时自动保存数据集，确保数据安全。

3. **性能优化**：
   - 问题生成时，程序尝试避免重复（最多重试5次）。
   - 大量问答对可能导致 JSON 文件变大，建议定期清理。

4. **版权与合规**：
   - 生成的问答内容需遵守阿里云和相关法律法规。
   - 引用书籍或资料时，注意版权问题。

## 未来改进

- **多模型支持**：集成更多大模型（如 DeepSeek、Grok）。
- **批量生成**：支持一次性生成多个问答对。
- **数据可视化**：添加问答对统计图表。
- **云同步**：支持将数据集同步到云端。
