# AI Test Project - Gemini Function Calling 示例

这是一个展示如何使用 Google Gemini API 进行 **Function Calling（工具调用）** 的完整示例项目。

## 📚 项目简介

本项目演示了如何让 Gemini 大模型智能地调用本地 Python 函数来完成任务，包括：
- 读取文件
- 列出目录内容
- 写入文件

**核心价值**：通过 Function Calling，AI 不再只是聊天机器人，而是能够真正执行操作、获取信息、完成复杂任务的智能代理。

## ✨ 功能特性

- ✅ **完整的 Function Calling 流程**：从工具定义到执行到结果返回
- ✅ **详细的代码注释**：每个步骤都有中文注释说明
- ✅ **交互式对话**：支持循环对话，持续使用工具
- ✅ **系统指令支持**：可自定义模型的行为方式
- ✅ **完整的对话历史**：可追踪每一轮的交互

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/你的用户名/ai-test.git
cd ai-test
```

### 2. 创建虚拟环境（推荐）

```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

这会安装以下依赖：
- **google-genai**: Google Generative AI SDK，用于调用 Gemini API

### 4. 获取 Gemini API Key

1. 访问 [Google AI Studio](https://aistudio.google.com/app/apikey)
2. 点击 "Create API Key" 创建 API key
3. 复制你的 API key

### 5. 配置 API Key

**方法 1：设置环境变量（推荐）**

```bash
# macOS/Linux
export GEMINI_API_KEY='your-api-key-here'

# 或添加到 ~/.zshrc 或 ~/.bashrc 永久保存
echo "export GEMINI_API_KEY='your-api-key-here'" >> ~/.zshrc
source ~/.zshrc
```

```powershell
# Windows PowerShell
$env:GEMINI_API_KEY='your-api-key-here'
```

**方法 2：使用 .env 文件**

创建 `.env` 文件（已在 .gitignore 中，不会被提交）：
```
GEMINI_API_KEY=your-api-key-here
```

### 6. 运行示例

```bash
cd gemini
python3 toolsAgent.py
```

## 📂 项目结构

```
ai-test/
├── gemini/
│   ├── __init__.py              # 包初始化文件
│   ├── toolsAgent.py            # 主程序：完整的 Function Calling 示例
│   ├── tools.py                 # 工具定义和实现（可选，用于模块化）
│   ├── useTools.py              # 简化版示例
│   └── geminiTest.py            # 基础对话示例
├── .gitignore                   # Git 忽略文件
├── requirements.txt             # Python 依赖列表
└── README.md                    # 项目说明文档
```

## 💡 使用示例

### 示例 1：列出目录文件

```python
# 运行 toolsAgent.py 后
你: 当前目录中有几个包含tools名字的文件

# 模型会：
# 1. 调用 list_dir 工具
# 2. 分析结果
# 3. 返回：当前目录中有 3 个包含 'tools' 名字的文件：useTools.py、tools.py、toolsAgent.py
```

### 示例 2：读取文件

```python
你: 读取 geminiTest.py 文件的内容

# 模型会调用 read_file 工具并返回文件内容
```

### 示例 3：复杂任务

```python
你: 列出所有 Python 文件，并告诉我总共有多少行代码

# 模型会：
# 1. 调用 list_dir 列出文件
# 2. 多次调用 read_file 读取每个 .py 文件
# 3. 统计总行数
# 4. 返回结果
```

## 🔧 工作原理

### Function Calling 执行流程

```
用户输入 (轮次1)
    ↓
【第1次调用大模型】← 模型分析问题，决定调用哪个工具
    ↓
模型返回函数调用指令 (轮次2)
    ↓
【本地执行 Python 函数】← 不访问大模型！在本地运行
    ↓
函数结果添加到历史 (轮次3)
    ↓
【第2次调用大模型】← 模型看到结果，生成自然语言回答
    ↓
模型生成最终回答 (轮次4)
```

**总结**：4个轮次，2次大模型调用，1次本地函数执行

### 代码核心部分

```python
# 1. 定义工具
tool_definition = types.FunctionDeclaration(
    name="list_dir",
    description="列出目录内容",
    parameters={...}
)

# 2. 实现工具
def list_dir(directory_path: str):
    return os.listdir(directory_path)

# 3. 创建 Agent
agent = Agent(model="gemini-2.5-flash", tools=file_tools)

# 4. 执行任务
response = agent.run("列出当前目录的文件")
```

## 🎓 学习要点

通过本项目，你可以学习到：

1. **工具定义**：如何使用 `types.FunctionDeclaration` 定义工具
2. **工具实现**：如何编写实际执行操作的 Python 函数
3. **工具调用流程**：理解完整的 Function Calling 工作机制
4. **对话管理**：如何维护对话历史和上下文
5. **系统指令**：如何自定义模型的行为方式

## 📝 核心文件说明

### toolsAgent.py

完整的 Function Calling 示例，包含：
- 详细的中文注释（400+ 行注释）
- 三个工具：read_file、write_file、list_dir
- 完整的 Agent 类实现
- 交互式对话循环

**关键类**：
```python
class Agent:
    def __init__(self, model, tools, system_instruction=None)
    def run(self, contents) -> response
```

### tools.py

可选的工具定义文件，用于模块化管理工具。

## ⚠️ 重要提示

### API Key 安全

- ❌ **不要**将 API key 硬编码在代码中
- ❌ **不要**将 API key 提交到 Git
- ✅ **使用**环境变量存储 API key
- ✅ **.gitignore** 已配置忽略 `.env` 文件

### 免费配额

Gemini API 有免费配额限制：
- 每日请求次数限制
- 每分钟请求次数限制

如果遇到 `429 RESOURCE_EXHAUSTED` 错误，说明配额用尽，需要：
- 等待配额重置
- 或升级到付费计划

### 模型选择

推荐使用的免费模型：
- `gemini-2.5-flash` - 最新最快
- `gemini-1.5-flash` - 稳定可靠
- `gemini-1.5-flash-8b` - 更轻量

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关资源

- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API 文档](https://ai.google.dev/gemini-api/docs)
- [Function Calling 指南](https://ai.google.dev/gemini-api/docs/function-calling)
- [费率限制说明](https://ai.google.dev/gemini-api/docs/rate-limits)

## 📧 联系方式

如有问题，请通过 GitHub Issues 联系。

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**
