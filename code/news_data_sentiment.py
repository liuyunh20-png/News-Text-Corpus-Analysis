import pandas as pd
from textblob import TextBlob  # 使用 TextBlob 进行情感分析

# 读取原始CSV文件
input_csv = "news_data_rewrite.csv"
output_csv = "news_data_sentiment.csv"

# 读取CSV文件，指定utf-8编码
df = pd.read_csv(input_csv, encoding="utf-8")

# 函数：使用TextBlob进行情感分析，增加空值容错
def analyze_sentiment(text):
    # 处理NaN、空值、非字符串
    if pd.isna(text) or not isinstance(text, str) or text.strip() == "":
        return 0.0  # 空文本默认中性分数0
    # 计算情感极性（polarity），值范围从 -1 到 1，负值负面，正值正面
    blob = TextBlob(text)
    return blob.sentiment.polarity

# 1. 预处理：删除news_content为空的行，全部转为字符串
df = df.dropna(subset=["news_content"])
df["news_content"] = df["news_content"].astype(str)

# 对每篇新闻的content进行情感分析
df['sentiment_score'] = df['news_content'].apply(analyze_sentiment)

# 分类情感为 positive, neutral, negative
def classify_sentiment(score):
    if score > 0.1:
        return 'positive'
    elif score < -0.1:
        return 'negative'
    else:
        return 'neutral'

# 添加情感分类列
df['sentiment_category'] = df['sentiment_score'].apply(classify_sentiment)

# 将完整结果写入CSV文件
df.to_csv(output_csv, index=False, encoding='utf-8')

print(f"情感分析结果（分数+分类）已成功写入 {output_csv}")
