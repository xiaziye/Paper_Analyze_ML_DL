import os
import shutil


def copy_large_tex_files(source_dir: str, target_dir: str, min_size_kb: int = 10):
    """
    复制目录中所有大于等于指定大小的 .tex 文件到目标目录
    :param source_dir: 源目录路径
    :param target_dir: 目标目录路径
    :param min_size_kb: 最小文件大小（单位KB，默认为10KB）
    """
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)

    # 遍历源目录
    for root, _, files in os.walk(source_dir):
        for filename in files:
            # 过滤 .tex 文件
            if filename.endswith(".tex"):
                file_path = os.path.join(root, filename)

                # 获取文件大小（单位：字节）
                file_size = os.path.getsize(file_path)
                # 转换为KB并比较
                if file_size >= min_size_kb * 1000:
                    # 构建目标路径（保持目录结构）
                    relative_path = os.path.relpath(root, source_dir)
                    dest_folder = os.path.join(target_dir, relative_path)
                    os.makedirs(dest_folder, exist_ok=True)

                    # 复制文件
                    try:
                        shutil.copy2(file_path, dest_folder)
                        print(f"已复制：{os.path.join(relative_path, filename)}")
                    except Exception as e:
                        print(f"复制失败：{filename} - {str(e)}")


if __name__ == "__main__":
    # 使用示例
    source_directory = "./paper/"  # 替换为你的源目录
    target_directory = "./latex/"  # 替换为你的目标目录

    copy_large_tex_files(
        source_dir=source_directory,
        target_dir=target_directory,
        min_size_kb=10
    )