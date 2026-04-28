import csv
import nltk
from nltk.corpus import wordnet
from nltk.tag import pos_tag
from nltk.stem import WordNetLemmatizer



# 配置文件路径
input_csv = "data_word_frequency.csv"
output_csv = "data_word_tag_frequency.csv"

# 初始化词形还原器
lemmatizer = WordNetLemmatizer()

# 定义需要保留的词性标签
keep_pos = {'NN', 'NNP', 'NNPS', 'NNS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'JJ', 'JJR', 'JJS'}

# 存储还原后的词频（用于合并相同还原词的频次）
lemmatized_counts = {}

# 读取原始CSV并处理
with open(input_csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # 提取并清洗单词和频次
        word = row['Word'].strip()
        frequency = row['Frequency'].strip()

        # 跳过无效数据
        if not word or not frequency.isdigit():
            continue

        # 步骤1：获取单词的NLTK词性标签
        tagged = pos_tag([word])
        nltk_tag = tagged[0][1] if tagged else ''

        # 步骤2：将NLTK标签转换为WordNet能识别的标签（用于精准还原）
        wordnet_tag = None
        if nltk_tag.startswith('J'):
            wordnet_tag = wordnet.ADJ
        elif nltk_tag.startswith('V'):
            wordnet_tag = wordnet.VERB
        elif nltk_tag.startswith('N'):
            wordnet_tag = wordnet.NOUN

        # 步骤3：词形还原（有词性标签则按词性还原，无则默认按名词）
        if wordnet_tag:
            lemmatized_word = lemmatizer.lemmatize(word, wordnet_tag)
        else:
            lemmatized_word = lemmatizer.lemmatize(word)

        # 步骤4：筛选指定词性的单词，并合并频次
        if nltk_tag in keep_pos:
            count = int(frequency)
            if lemmatized_word in lemmatized_counts:
                lemmatized_counts[lemmatized_word] += count
            else:
                lemmatized_counts[lemmatized_word] = count

# 将处理结果写入新CSV
with open(output_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['Word', 'Frequency'])
    writer.writeheader()
    # 按频次降序写入（可选，删掉sorted即可按原顺序）
    for word, count in sorted(lemmatized_counts.items(), key=lambda x: x[1], reverse=True):
        writer.writerow({'Word': word, 'Frequency': count})

print(f"处理完成！结果已写入：{output_csv}")
print(f"共保留 {len(lemmatized_counts)} 个符合条件的还原词")