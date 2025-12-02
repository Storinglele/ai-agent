from google import genai
from google.genai import types
class Agent:
    def __init__(self, model: str):
        self.model = model
        self.client = genai.Client()
        self.contents = []
    def run(self, contents: str):
        self.contents.append({"role": "user", "parts": [{"text": contents}]})
        response = self.client.models.generate_content(model=self.model, contents=self.contents)
        self.contents.append(response.candidates[0].content)
        return response
agent = Agent(model="gemini-2.5-flash")
response1 = agent.run(
    contents="你好,德国最值得游览的前 3 个城市是什么?只返回城市名称。"
)
print(f"模型: {response1.text}")

# 输出: Berlin, Munich, Cologne
response2 = agent.run(
    contents="告诉我关于第二个城市的一些事情。"
)
print(f"模型: {response2.text}")
# 输出: Munich is the capital of Bavaria and is known f