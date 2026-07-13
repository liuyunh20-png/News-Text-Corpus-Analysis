import pandas as pd
import matplotlib.pyplot as plt

# 读取CSV文件（替换为你的文件路径）
df = pd.read_csv("data_word_tag_frequency.csv")

# 只保留频率>0的有效数据
df = df[df['Frequency'] > 400].dropna()

# 绘制饼状图
plt.figure(figsize=(8, 8))
plt.pie(df['Frequency'], labels=df['Word'], autopct='%1.1f%%')
plt.title('Word Frequency')  # 标题
plt.axis('equal')  # 保证饼图为正圆

# 显示图表
plt.show()