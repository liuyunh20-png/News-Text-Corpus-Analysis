import csv
from wordcloud import WordCloud

csv_file = "data_word_tag_frequency.csv"

word_freq = {}
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # 直接提取词语和频次（假设数据格式正确）
        word = row['Word'].strip()
        freq = int(row['Frequency'])
        if word and freq > 0:
            word_freq[word] = freq

# 2. 生成词云
wordcloud = WordCloud(
    width=800,
    height=600,
    background_color='white',
    max_words=200
).generate_from_frequencies(word_freq)


wordcloud.to_file('data_word_tag_frequency_wordcloud.png')