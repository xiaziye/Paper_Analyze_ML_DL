import os
from openai import OpenAI

client = OpenAI(
    api_key="sk-vDpcisxS7l9K7jNFzB3eAwTXIqsxfoklUpCStrKmXcOZWrb7",  # 替换为你的 API Key
    base_url="https://api.moonshot.cn/v1",
)

file_path = "D:/KG_LLM/Database/latex/1/main.tex"
with open(file_path, "r", encoding="utf-8") as file:
    file_content = file.read()

system_prompt = f"""
你是一个专业的论文分析助手。请执行文本分割任务，将论文{file_content}分割为简介、方法论与结论，并按照原本的内容以以下格式输出为文本：
简介：
[论文的简介内容]

方法论：
[论文的方法论内容]

结论：
[论文的结论内容]
"""

# 假设论文内容已经读取到变量 `paper_content` 中
paper_content = """
这里是论文的完整内容，包含简介、方法论和结论部分。
"""

# 调用 Kimi API
completion = client.chat.completions.create(
    model="moonshot-v1-32k",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": paper_content}
    ],
    temperature=0.3
)

model_output = completion.choices[0].message.content

output_file_path = "output.txt"
with open(output_file_path, "w", encoding="utf-8") as output_file:
    output_file.write(model_output)

print(f"模型的输出已成功保存到文件：{output_file_path}")
