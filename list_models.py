from google import genai
import os

# 检查 API key 是否设置
api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
if not api_key:
    print("错误: 请先设置 GEMINI_API_KEY 或 GOOGLE_API_KEY 环境变量")
    print("例如: export GEMINI_API_KEY='your-api-key'")
    exit(1)

# 列出所有可用的模型
client = genai.Client(api_key=api_key)

print("可用的 Gemini 模型：\n")
try:
    for model in client.models.list():
        print(f"模型名称: {model.name}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"  支持的方法: {model.supported_generation_methods}")
        if hasattr(model, 'display_name'):
            print(f"  显示名称: {model.display_name}")
        print("-" * 60)
except Exception as e:
    print(f"列出模型时出错: {e}")
