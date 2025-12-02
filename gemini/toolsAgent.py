"""
==============================================================================
Gemini Function Calling (工具调用) 完整示例
==============================================================================

本脚本展示如何让 Gemini 大模型智能地调用本地工具（函数）来完成任务。

核心概念：
- Function Calling 不是为了完成简单任务（如列文件），而是让 AI 能够：
  1. 理解自然语言指令
  2. 智能决策需要调用哪些工具
  3. 自动执行复杂的多步骤任务
  4. 将结果转换成人类可读的回答

执行流程（以 list_dir 为例）：
  用户提问 (轮次1)
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

总结：4个轮次，2次大模型调用，1次本地函数执行
==============================================================================
"""

import os
import json
from google import genai
from google.genai import types

# ==============================================================================
# 第一部分：定义工具（Tool Definitions）
# ==============================================================================
# 这里定义了模型可以调用的工具，告诉模型：
# - 工具的名称
# - 工具的功能描述
# - 需要哪些参数
#
# 重要：必须使用 types.FunctionDeclaration 格式，不能用普通字典！

# 工具1：读取文件
read_file_definition = types.FunctionDeclaration(
    name="read_file",  # 工具名称
    description="读取文件并返回其内容。",  # 描述告诉模型这个工具做什么
    parameters={  # 参数定义
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "要读取的文件路径。",
            }
        },
        "required": ["file_path"],  # 必需参数
    },
)

# 工具2：列出目录内容
list_dir_definition = types.FunctionDeclaration(
    name="list_dir",
    description="列出指定目录中的所有文件和文件夹。使用 '.' 表示当前目录。",
    parameters={
        "type": "object",
        "properties": {
            "directory_path": {
                "type": "string",
                "description": "要列出的目录路径，例如 '.' 表示当前目录，'..' 表示上级目录",
            }
        },
        "required": ["directory_path"],
    },
)

# 工具3：写入文件
write_file_definition = types.FunctionDeclaration(
    name="write_file",
    description="使用给定内容写入文件。",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "要写入的文件路径。",
            },
            "contents": {
                "type": "string",
                "description": "要写入文件的内容。",
            },
        },
        "required": ["file_path", "contents"],
    },
)

# ==============================================================================
# 第二部分：实现工具的实际功能（Tool Implementations）
# ==============================================================================
# 这些是真正执行操作的 Python 函数，在本地运行，不访问大模型

def read_file(file_path: str) -> str:
    """读取文件内容"""
    with open(file_path, "r") as f:
        return f.read()

def write_file(file_path: str, contents: str) -> bool:
    """写入文件内容"""
    with open(file_path, "w") as f:
        f.write(contents)
    return True

def list_dir(directory_path: str) -> list[str]:
    """列出目录中的所有文件和文件夹"""
    full_path = os.path.expanduser(directory_path)  # 展开 ~ 等路径符号
    return os.listdir(full_path)  # 返回文件列表

# ==============================================================================
# 第三部分：组装工具字典
# ==============================================================================
# 将工具定义和实现函数关联起来
# 格式：{"工具名": {"definition": 定义, "function": 实现函数}}

file_tools = {
    "read_file": {
        "definition": read_file_definition,  # 告诉模型这个工具是什么
        "function": read_file  # 实际执行的 Python 函数
    },
    "write_file": {
        "definition": write_file_definition,
        "function": write_file
    },
    "list_dir": {
        "definition": list_dir_definition,
        "function": list_dir
    },
}

# ==============================================================================
# 第四部分：Agent 类 - 封装工具调用逻辑
# ==============================================================================

class Agent:
    """
    智能代理类，负责：
    1. 管理与 Gemini 模型的对话
    2. 处理工具调用流程
    3. 维护对话历史
    """

    def __init__(self, model: str, tools: dict, system_instruction: str = None):
        """
        初始化代理

        参数：
            model: 模型名称，如 "gemini-2.5-flash"
            tools: 工具字典，包含工具定义和实现函数
            system_instruction: 系统指令（可选），设置模型的行为方式
        """
        self.model = model  # 保存模型名称
        self.client = genai.Client()  # 创建 Gemini 客户端（需要设置 API key）
        self.contents = []  # 对话历史列表，记录所有轮次
        self.tools = tools  # 保存工具字典
        self.system_instruction = system_instruction  # 保存系统指令

    def run(self, contents: str):
        """
        执行一次完整的对话流程（可能包含工具调用）

        参数：
            contents: 用户的输入文本

        返回：
            response: 模型的最终响应

        流程说明：
            1. 添加用户消息到历史 (轮次1)
            2. 第1次调用大模型 → 模型决定是否调用工具 (轮次2)
            3. 如果需要调用工具：
               a. 在本地执行工具函数
               b. 将结果添加到历史 (轮次3)
               c. 第2次调用大模型 → 模型生成最终回答 (轮次4)
            4. 返回最终响应
        """

        # ------------------------------------------------------------------
        # 步骤1：添加用户消息到对话历史（轮次1）
        # ------------------------------------------------------------------
        self.contents.append({
            "role": "user",  # 角色：用户
            "parts": [{"text": contents}]  # 消息内容
        })

        # ------------------------------------------------------------------
        # 步骤2：配置工具列表和系统指令
        # ------------------------------------------------------------------
        # 告诉模型有哪些工具可用，以及如何表现（system_instruction）
        config_params = {
            "tools": [
                types.Tool(
                    function_declarations=[
                        tool["definition"] for tool in self.tools.values()
                    ]
                )
            ]
        }

        # 如果设置了系统指令，添加到配置中
        if self.system_instruction:
            config_params["system_instruction"] = self.system_instruction

        config = types.GenerateContentConfig(**config_params)

        # ------------------------------------------------------------------
        # 步骤3：【第1次调用大模型】
        # ------------------------------------------------------------------
        # 目的：让模型分析用户问题，决定是否需要调用工具
        # 输入：用户问题 + 可用工具列表
        # 输出：文本回答 或 函数调用指令
        print(">>> 第1次调用大模型：让模型决定是否调用工具...")
        response = self.client.models.generate_content(
            model=self.model,
            contents=self.contents,
            config=config
        )

        # 将模型响应添加到对话历史（轮次2）
        self.contents.append(response.candidates[0].content)

        # ------------------------------------------------------------------
        # 步骤4：检查模型是否决定调用工具
        # ------------------------------------------------------------------
        # 检查第一个 part 是否有 function_call
        has_function_call = (
            response.candidates[0].content.parts
            and hasattr(response.candidates[0].content.parts[0], 'function_call')
            and response.candidates[0].content.parts[0].function_call
        )

        if has_function_call:
            print(">>> 模型决定调用工具！开始执行...")

            # 提取所有函数调用（可能有多个）
            function_calls = [
                part.function_call
                for part in response.candidates[0].content.parts
                if part.function_call
            ]

            # ------------------------------------------------------------------
            # 步骤5：执行所有函数调用（在本地执行，不访问大模型！）
            # ------------------------------------------------------------------
            for function_call in function_calls:
                function_name = function_call.name  # 工具名称，如 "list_dir"
                function_args = function_call.args  # 参数，如 {"directory_path": "."}

                print(f">>> 在本地执行工具: {function_name}({function_args})")

                # 检查工具是否存在
                if function_name in self.tools:
                    # 调用实际的 Python 函数（本地执行）
                    # **function_args 将字典展开为关键字参数
                    # 例如：list_dir(**{"directory_path": "."})
                    #    等价于：list_dir(directory_path=".")
                    result = self.tools[function_name]["function"](**function_args)

                    print(f">>> 工具执行结果: {result}")

                    # 将函数执行结果添加到对话历史（轮次3）
                    self.contents.append({
                        "role": "user",  # 角色：用户（函数结果以用户身份发送）
                        "parts": [{
                            "function_response": {
                                "name": function_name,
                                "response": {"result": result}
                            }
                        }]
                    })

            # ------------------------------------------------------------------
            # 步骤6：【第2次调用大模型】
            # ------------------------------------------------------------------
            # 目的：让模型看到工具执行结果，生成最终的自然语言回答
            # 输入：之前的对话 + 工具执行结果
            # 输出：最终的自然语言回答
            print(">>> 第2次调用大模型：让模型根据工具结果生成最终回答...")
            response = self.client.models.generate_content(
                model=self.model,
                contents=self.contents,
                config=config
            )

            # 将最终回答添加到对话历史（轮次4）
            self.contents.append(response.candidates[0].content)
            print(">>> 完成！")
        else:
            # 模型没有调用工具，直接返回了文本回答
            print(">>> 模型没有调用工具，直接返回了文本回答")
            print(f">>> 回答: {response.text if hasattr(response, 'text') else '(无文本)'}")

        return response

# ==============================================================================
# 第五部分：主程序 - 创建 Agent 并执行任务
# ==============================================================================

# 创建智能代理
# - 使用 gemini-2.5-flash 模型
# - 配备 file_tools（文件操作工具）
# agent = Agent(model="gemini-2.5-flash", tools=file_tools)
agent = Agent(
    model="gemini-2.5-flash",
    tools=file_tools,
    system_instruction="你是一个有帮助的编码助手。回应时像 Linus Torvalds 一样。"
)
print("Agent 已就绪。让它检查此目录中的文件。")
while True:
    user_input = input("你: ")
    if user_input.lower() in ['exit', 'quit']:
        break
    response = agent.run(user_input)
    print(f"Linus: {response.text}\n")

# 执行任务
# 注意：这里明确要求使用工具是为了演示，实际使用时可以用自然语言提问
# 例如："这个目录里有哪些文件？" 模型会自动决定调用 list_dir
response = agent.run(
    contents="当前目录中有几个包含tools名字的文件"
    # contents="请使用 list_dir 工具列出 '.' 目录中的文件"
)

# ==============================================================================
# 第六部分：显示结果
# ==============================================================================

# 显示最终回答
print("=" * 60)
print("【最终回答】")
print(response.text if hasattr(response, 'text') else "无文本内容")
print("=" * 60)

# 显示完整对话历史（4个轮次）
print("【完整对话历史】")
print("说明：")
print("  - 轮次 = 对话中的每一条消息")
print("  - 本示例有4个轮次，2次大模型调用，1次本地函数执行")
print()

for i, content in enumerate(agent.contents):
    print(f"\n轮次 {i+1}:")

    # 处理不同类型的内容（字典或对象）
    if isinstance(content, dict):
        # 字典类型（用户消息）
        print(f"  角色: {content.get('role', 'model')}")
        parts = content.get('parts', [])
    else:
        # 对象类型（模型响应）
        print(f"  角色: {getattr(content, 'role', 'model')}")
        parts = getattr(content, 'parts', [])

    # 显示每个 part 的内容
    for part in parts:
        if isinstance(part, dict):
            # 字典类型的 part
            if 'text' in part:
                print(f"  文本: {part['text']}")
            elif 'function_response' in part:
                print(f"  函数响应: {part['function_response']}")
        else:
            # 对象类型的 part
            if hasattr(part, 'text') and part.text:
                print(f"  文本: {part.text}")
            elif hasattr(part, 'function_call') and part.function_call:
                print(f"  函数调用: {part.function_call.name}({part.function_call.args})")

print("=" * 60)

# ==============================================================================
# 运行说明
# ==============================================================================
#
# 1. 设置 API key：
#    export GEMINI_API_KEY='your-api-key'
#
# 2. 运行脚本：
#    python3 toolsAgent.py
#
# 3. 预期输出：
#    - 最终回答：模型用自然语言列出文件
#    - 对话历史：显示4个轮次的完整交互过程
#
# ==============================================================================
