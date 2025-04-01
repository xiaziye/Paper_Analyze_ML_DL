import requests

# 目标 URL
with open("arxiv_paper_list.txt") as f:
    num = 0
    for url in f.readlines():
        url = url.strip("\n")
        print(url)
        # 发送 HTTP GET 请求
        response = requests.get(url)

        # 检查请求是否成功
        if response.status_code == 200:
            # 将内容保存为 tar.gz 文件
            with open(f'.\\paper\\{num}.tar.gz', 'wb') as file:
                file.write(response.content)
            print(f'文件下载成功并已保存为 {num}.tar.gz')
        else:
            print(f'下载失败，HTTP 状态码：{response.status_code}')
        num += 1

