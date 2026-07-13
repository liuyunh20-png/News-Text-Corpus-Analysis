import nltk
import re
import os

# 先自动下载分词包，解决 punkt_tab 缺失报错
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    print("自动下载分词资源 punkt_tab...")
    nltk.download("punkt_tab")

# 读取本地 English_stopwords.txt 停用词文件
def stopwordlist():
    stop_file = r'd:\Sum-clone\News-Text-Corpus-Analysis\code\English_stopwords.txt'
    if not os.path.exists(stop_file):
        raise FileNotFoundError("当前文件夹缺少 English_stopwords.txt，请放到脚本同目录！")
    stopwords = []
    with open(stop_file, mode="r", encoding="utf-8") as myfile:
        for line in myfile.readlines():
            stopwords.append(line.strip().lower())
    return set(stopwords)

stopwords = stopwordlist()

# 读取原始清洗文本
with open("data_delete_sentence.txt", mode='r', encoding='utf-8') as inputfile:
    content = inputfile.readlines()

clean_content = []
# 写入预处理结果
with open("data_process.txt", mode='w', encoding='utf-8') as outputfile:
    for line in content:
        outstr = ""
        line = re.sub(r'[^\w\s]', "", line)  # 去除标点
        line = re.sub(r'\d+', "", line)      # 去除数字
        tokens = nltk.word_tokenize(line.strip())
        # 过滤停用词
        for word in tokens:
            if word.lower() not in stopwords:
                outstr += word + " "
        clean_content.append(outstr)
        outputfile.write(outstr + "\n")

print("预处理完成！")
print(clean_content)