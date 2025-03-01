import requests

# 定义 SPARQL 查询模板
SPARQL_QUERY_TEMPLATE = """
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?entity ?label ?abstract
WHERE {{
  ?entity dbo:abstract ?abstract .
  OPTIONAL {{
    ?entity rdfs:label ?label .
    FILTER(LANG(?label) = 'en')
  }}
  FILTER(LANG(?abstract) = 'en')
}}
LIMIT {limit}
OFFSET {offset}
"""

# DBpedia SPARQL 端点 URL
SPARQL_ENDPOINT = "https://dbpedia.org/sparql"

# 每批次下载的数据量
BATCH_SIZE = 10000

# 最大下载批次（根据需要调整）
MAX_BATCHES = 10

# 输出文件名
OUTPUT_FILE = "entities_with_abstracts.csv"

# 初始化文件，写入 CSV 表头
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("entity,label,abstract\n")

# 分批下载数据
for batch in range(MAX_BATCHES):
    # 计算当前批次的 OFFSET
    offset = batch * BATCH_SIZE

    # 构造 SPARQL 查询
    query = SPARQL_QUERY_TEMPLATE.format(limit=BATCH_SIZE, offset=offset)

    # 发送请求
    params = {
        "query": query,
        "format": "csv"
    }
    response = requests.get(SPARQL_ENDPOINT, params=params)

    # 检查请求是否成功
    if response.status_code != 200:
        print(f"请求失败，状态码：{response.status_code}")
        break

    # 获取结果并保存到文件
    results = response.text

    # 跳过表头（如果是第一次写入）
    if batch > 0:
        results = results.split("\n", 1)[-1]  # 去掉第一行表头

    # 追加结果到文件
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(results)

    print(f"已下载第 {batch + 1} 批次数据，OFFSET: {offset}")

print(f"数据已保存到 {OUTPUT_FILE}")