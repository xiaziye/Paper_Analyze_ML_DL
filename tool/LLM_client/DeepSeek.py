from openai import OpenAI, APIError, APITimeoutError
import os
import time
from pathlib import Path
import logging
import csv
from latex_chunker import LatexChunker

RATE_LIMIT = 3
MAX_INPUT_TOKENS = 20000  # 基于API总限制128k保留安全余量
MAX_OUTPUT_TOKENS = 900
TOKEN_RATIO = 2.5  # 字符数/token估算比率
CHUNK_SIZE = int(MAX_INPUT_TOKENS * TOKEN_RATIO)
LOOKAHEAD = 1024
ENV_THRESHOLD = 200
# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('api_errors.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def list_files(folder_path):
    file_paths = []
    for root, dirs, files in os.walk(folder_path):
        for file_ in files:
            relative_path = os.path.relpath(os.path.join(str(root), str(file_)), folder_path)
            file_paths.append(relative_path)
    return file_paths


def estimate_tokens(text: str) -> int:
    """快速估算文本token数量"""
    return int(len(text) / TOKEN_RATIO)


def ds_client(full_text: str, max_retries: int = 3, initial_delay: int = 1, chunk_id: int = 1):
    client = OpenAI(
        api_key="sk-bd22417cd5ec4c7e8d6273c096a31fdc",
        base_url="https://api.deepseek.com/v1",
        timeout=120.0  # 设置全局超时时间
    )

    for attempt in range(max_retries):
        try:
            steps = [
                {"role": "user", "part": "Introduction", "instruction": "仅输出研究问题部分(Introduction)，需包含\\section{"
                                                                        "Introduction}标题和核心段落"},
                {"role": "user", "part": "Methodology", "instruction": "仅输出方法框架部分，要求：1.先查找如\\section{"
                                                                       "Methodology}或\\section{System "
                                                                       "Design}等类似标题2.如果没有匹配标题，则判断段落是否是关于论文的解决方法"},
                {"role": "user", "part": "Conclusion", "instruction": "仅输出结论部分，要求：1.查找Conclusion或Discussion章节,"
                                                                      "2.如果没有匹配标题，则判断段落是否是关于论文的总结"},
                {"role": "user", "part": "Others", "instruction": "输出既不是以上三部分的第一个主要段落,可以随机挑选"}
            ]
            results = {}
            prompt = f"""
            
                            ## 核心指令
                            1. 按要求以段落分割可能存在的要求部分，摘取段落中主要句子并输出为文本，把输出限制在 600-900 tokens；
                            2. 输出仅为原文内容，不输出其他提示
                            3. 如果没有匹配的内容则输出：null
                            4. 每次输出的内容不要与已经获取的内容重复
                            
                            ## 质量控制
                            最终校验：
                                - 禁用Markdown/LaTeX格式修改
                                - 禁止包含之前步骤已提取的内容
                
            """
            messages = [
                {"role": "system", "content": "严格按当前指令提取指定章节的原始内容，保留LaTeX格式"},
                {"role": "user", "content": f"论文全文：\n{full_text}"},
                {"role": "user", "content": prompt}
            ]
            for step in steps:
                if "Introduction" not in step["instruction"]:
                    messages.append({"role": "user", "content": f"当前指令：{step['instruction']}\n"
                                                                f"注意不要包含之前已提取的内容：{list(results.values())}"})
                if chunk_id != 1 and "Introduction" in step["instruction"]:
                    continue
                messages.append({"role": "user", "content": step["instruction"]})
                completion = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=MAX_OUTPUT_TOKENS,  # 关键参数：限制输出长度
                    stream=False
                )

                if not completion.choices:
                    raise ValueError("Empty choices in API response")

                content = completion.choices[0].message.content
                content = content.replace('\n', '')
                if estimate_tokens(content) > MAX_OUTPUT_TOKENS:
                    logger.warning("输出token可能超限，建议人工检查")

                if "Introduction" in step["instruction"]:
                    results["Introduction"] = [content]
                elif "Methodology" in step["instruction"]:
                    results["Methodology"] = [content]
                elif "Conclusion" in step["instruction"]:
                    results["Conclusion"] = [content]
                else:
                    results["Others"] = [content]
            return results

        except (APIError, APITimeoutError, ValueError) as er:
            delay = initial_delay * (2 ** attempt)
            logger.warning(f"API异常 ({attempt + 1}/{max_retries}): {str(er)} - {delay}s后重试")
            time.sleep(delay)
        except Exception as er:
            logger.error(f"严重错误: {str(er)}", exc_info=True)
            break
        return None


def process_paper(timeout):
    try:
        # 获取生成器
        chunk_gen = LatexChunker(
            chunk_size=CHUNK_SIZE,
            lookahead=LOOKAHEAD,
            env_threshold=ENV_THRESHOLD,
            global_timeout=timeout
        )
        return chunk_gen

    except FileNotFoundError as er:
        print(f"错误: {str(er)}")
    except Exception as er:
        print(f"处理异常: {str(er)}")


if __name__ == "__main__":
    directions = r"D:\KG_LLM\Database\latex201_250"
    paths = list_files(directions)

    for file_path in paths:
        start_time = time.time()
        elapsed = time.time() - start_time
        if elapsed < 1 / RATE_LIMIT:
            time.sleep(1 / RATE_LIMIT - elapsed)
        try:
            # 读取文件
            full_path = os.path.join(directions, file_path)
            chunker = process_paper(timeout=3)

            for i, chunk in enumerate(chunker.chunk_generator(Path(full_path))):

                # 调用API并处理重试
                model_output = ds_client(full_text=chunk.decode('utf-8', errors='replace') + "...\n", chunk_id=i + 1)

                if model_output is None:
                    logging.error(f"处理文件失败: {file_path}")
                    continue  # 跳过当前文件继续处理下一个

                if not model_output:
                    logging.error(f"API返回空响应: {file_path}")
                    continue
                    # 保存结果
                output_file_path = Path(f"./result/{str(file_path).replace('.tex', 'Chunk') + f'{str(i + 1)}.csv'}")
                output_file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['Introduction', 'Methodology', 'Conclusion', "Others"])
                    writer.writeheader()
                    writer.writerow(model_output)
                    logging.info(f"文件已保存为{output_file_path}")
                    f.close()

        except Exception as e:
            logging.error(f"处理文件时发生严重错误 ({file_path}): {str(e)}")
            continue  # 确保继续处理下一个文件

