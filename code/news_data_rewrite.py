import csv
import re
import nltk
from nltk.corpus import stopwords

# 清洗文本的函数
def clean_text(text):
    # 去除多余的空格
    text = text.strip()
    # 去除特殊字符和数字，仅保留字母和空格
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    # 统一处理多个连续空格为一个
    text = re.sub(r'\s+', ' ', text)

    # 获取英语停用词列表
    stop_words = set(stopwords.words('english'))

    # 分词
    words = text.split()

    # 去除停用词
    cleaned_words = [word for word in words if word.lower() not in stop_words]

    # 返回去除停用词后的文本
    return ' '.join(cleaned_words)


# 读取txt文件并按空行分割每篇新闻
with open("data_delete_sentence.txt", "r", encoding="utf-8") as file:
    content = file.read().strip().split("\n\n")  # 按空行分割
    content = content[2:]  # 如果需要跳过前两条数据（如开头的无效内容）

# 准备写入CSV的数据
csv_data = []

# 遍历每篇新闻，进行清洗
for i, news in enumerate(content):
    cleaned_news = clean_text(news)  # 对每篇新闻进行清洗
    csv_data.append([f"news{i + 1}", cleaned_news])  # 新闻编号，新闻内容

# 写入CSV文件
csv_filename = "news_data_rewrite.csv"
with open(csv_filename, mode='w', encoding='utf-8', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["news_num", "news_content"])  # 写入标题行
    writer.writerows(csv_data)  # 写入每条新闻的数据

print(f"已将数据成功写入 {csv_filename}")
