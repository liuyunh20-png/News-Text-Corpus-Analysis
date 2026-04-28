import pandas as pd
from textblob import TextBlob  # 使用 TextBlob 进行情感分析

# 读取原始CSV文件
input_csv = "news_data_rewrite.csv"
output_csv = "news_data_sentiment.csv"

# 读取CSV文件
df = pd.read_csv(input_csv)

# 函数：使用TextBlob进行情感分析
def analyze_sentiment(text):
    # 计算情感极性（polarity），值范围从 -1 到 1，负值表示负面情感，正值表示正面情感
    blob = TextBlob(text)
    return blob.sentiment.polarity

# 对每篇新闻的content进行情感分析
df['sentiment_score'] = df['news_content'].apply(analyze_sentiment)

# 将分析结果写入新的CSV文件
df.to_csv(output_csv, index=False, encoding='utf-8')

print(f"情感分析结果已成功写入 {output_csv}")

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

# 输出结果到新的CSV文件
df.to_csv(output_csv, index=False, encoding='utf-8')
