# -- coding: utf-8 --
from openai import OpenAI, APIError, APITimeoutError
import os
import time
from pathlib import Path
import logging

RATE_LIMIT = 3
# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('api_errors.log'), logging.StreamHandler()]
)


def list_files(folder_path):
    file_paths = []
    for root, dirs, files in os.walk(folder_path):
        for file_ in files:
            relative_path = os.path.relpath(os.path.join(str(root), str(file_)), folder_path)
            file_paths.append(relative_path)
    return file_paths


def ds_client(prompt, max_retries=3, initial_delay=1):
    client = OpenAI(
        api_key="sk-bd22417cd5ec4c7e8d6273c096a31fdc",
        base_url="https://api.deepseek.com/v1",
        timeout=120.0  # 设置全局超时时间
    )

    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )

            if not hasattr(completion, 'choices'):
                raise ValueError("API响应缺少choices字段")
            if len(completion.choices) == 0:
                raise ValueError("choices字段为空")
            if not hasattr(completion.choices[0].message, 'content'):
                raise ValueError("message字段缺少content属性")

            return completion.choices[0].message.content
        except (APIError, APITimeoutError, ValueError) as e:
            delay = initial_delay * (2 ** attempt)  # 指数退避策略
            logging.warning(f"API调用失败 (尝试 {attempt + 1}/{max_retries}): {str(e)} - {delay}秒后重试")
            time.sleep(delay)
        except Exception as e:
            logging.error(f"未知错误: {str(e)}")
            if hasattr(e, 'response') and e.response:  # 记录原始响应
                logging.error(f"原始错误响应: {e.response.text}")
            break
    return None  # 所有重试失败后返回None


if __name__ == "__main__":
    directions = r"D:\KG_LLM\Database\latex51-100"
    paths = list_files(directions)

    for file_path in paths:
        start_time = time.time()
        elapsed = time.time() - start_time
        if elapsed < 1 / RATE_LIMIT:
            time.sleep(1 / RATE_LIMIT - elapsed)
        try:
            # 读取文件
            full_path = os.path.join(directions, file_path)
            with open(full_path, "r", encoding="utf-8", errors="ignore") as file:
                file_content = file.read()

            # 构造提示词
            system_prompt = f"""
            你是一个专业的学术文本处理助手，需要按照要求从论文中提取指定章节内容。请遵循以下规则：

            **任务要求**
            1. 从输入的论文文本中精确提取以下三个部分：
               - Introduction（引言）
               - Methodology（方法论，可能包含 Methods、Approach 等类似标题）
               - Conclusion（结论）
                注：某些文本可能只包含其中的某一部分，请将最可能归属的部分提取出来，没有的部分则返回null

            2. **内容要求**：
               - 必须完全保留原文内容，不得修改、总结或删减
               - 如果某个章节不存在，对应字段设为 null
               - 确保提取内容完整性（包含章节标题和全部正文）

            **输出格式**
            返回严格合法的JSON格式，确保：
            - 使用双引号
            - 无注释内容
            - 无多余换行符
            - 编码字符正确转义

            **验证步骤**
            在最终输出前，请按此流程自检：
            1. 检查JSON语法是否正确
            2. 核对字段名称拼写
            3. 确认内容是否完整包含对应章节

            **示例**
            输入文本：
            "Introduction: This paper studies... Methodology: We propose... Conclusion: In summary..."

            期望输出：
            {{
              "Introduction": "Introduction: This paper studies...",
              "Methodology": "Methodology: We propose...",
              "Conclusion": "Conclusion: In summary..."
            }}

            **待处理论文文本**
            {file_content}
            """

            # 调用API并处理重试
            model_output = ds_client(system_prompt)

            if model_output is None:
                logging.error(f"处理文件失败: {file_path}")
                continue  # 跳过当前文件继续处理下一个

            if not model_output:
                logging.error(f"API返回空响应: {file_path}")
                continue

            # 保存结果
            output_file_path = Path(f"./result/{str(file_path).replace('tex', 'txt')}")
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            output_file_path.write_text(model_output, encoding="utf-8")
            logging.info(f"成功保存: {output_file_path}")

        except Exception as e:
            logging.error(f"处理文件时发生严重错误 ({file_path}): {str(e)}")
            continue  # 确保继续处理下一个文件
