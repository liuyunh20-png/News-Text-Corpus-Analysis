import pandas as pd
import matplotlib.pyplot as plt

# 读取CSV文件
csv_file = "data_word_tag_frequency.csv"  # 词频统计CSV文件路径
df = pd.read_csv(csv_file)

# 排序：根据词频降序排列，取前100个单词
df_sorted = df.sort_values(by="Frequency", ascending=False).head(50)

# 绘制柱状图
plt.figure(figsize=(10, 8))
plt.barh(df_sorted['Word'], df_sorted['Frequency'], color='skyblue')
plt.xlabel('Frequency')
plt.ylabel('Words')
plt.title('Top 50 Most Frequent Words')
plt.gca().invert_yaxis()  # 反转y轴，使频次最高的单词在顶部

# 显示图表
plt.show()
