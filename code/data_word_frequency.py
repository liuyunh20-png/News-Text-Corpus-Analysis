from collections import Counter

input_file = "data_process.txt"  # 输入文件路径
output_file = "data_word_frequency.csv"  # 输出CSV文件路径

with open(input_file, "r", encoding="utf-8") as file:
    text = file.read()
text_lower = text.lower()
words = text_lower.split()

word_counts = Counter(words)

import csv
with open(output_file, mode="w", newline='', encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Word", "Frequency"])  # 写入标题行
    for word, count in word_counts.items():
        writer.writerow([word, count])

print(f"词频统计结果已写入 {output_file}")

