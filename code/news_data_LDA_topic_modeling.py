import pandas as pd
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

INPUT_FILE = "news_data_rewrite.csv"
OUTPUT_FILE = "news_data_LDA_classify_result.csv"
N_TOPICS = 5  # 主题数量

# 加载数据
df = pd.read_csv(INPUT_FILE, encoding='utf-8')
df = df.dropna(subset=['news_content'])  # 删除空值行
df['news_content'] = df['news_content'].astype(str)  # 确保所有内容是字符串

# 构建词频矩阵
vectorizer = CountVectorizer(min_df=2, max_df=0.9)  # min_df: 保留出现至少2次的单词；max_df: 保留出现频率小于90%的单词
doc_term = vectorizer.fit_transform(df['news_content'])

# 训练LDA模型
lda = LatentDirichletAllocation(n_components=N_TOPICS, random_state=42)
doc_topic = lda.fit_transform(doc_term)

# 分配主题并提取核心词
df['topic_id'] = doc_topic.argmax(axis=1)  # 获取最优主题
df['topic_prob'] = doc_topic.max(axis=1)   # 获取主题的概率

# 获取词汇表
vocab = vectorizer.get_feature_names_out()

# 打印每个主题的核心词
for i in range(N_TOPICS):
    top_words = [vocab[j] for j in lda.components_[i].argsort()[-10:][::-1]]
    print(f"主题{i}: {' '.join(top_words)}")

# 保存结果（新增topic_id和topic_prob列）
df[['news_num', 'news_content', 'topic_id', 'topic_prob']].to_csv(
    OUTPUT_FILE, index=False, encoding='utf-8'
)

print(f"\n结果已保存至 {OUTPUT_FILE}")
