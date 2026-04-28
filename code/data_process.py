import nltk
import re

def stopwordlist():
    stopwords= []
    with open("English_stopwords.txt",mode="r",encoding="utf-8") as myfile:
        content = myfile.readlines()
        for line in content:
            stopwords.append(line.strip())
    return stopwords

stopwords = stopwordlist()


# read text from file
inputfile = open("data_delete_sentence.txt", mode='r',encoding='utf-8')
outputfile = open("data_process.txt", mode='w',encoding='utf-8')
content = inputfile.readlines()

# data pre-prpocessing
clean_content= []
for line in content:
    outstr = ""
    line = re.sub(r'[^\w\s]',"",line)  #\w\s表示大小写英文字母、数字、下划线、空格
    line = re.sub(r'\d+',"", line)
    result = nltk.word_tokenize(line.strip()) #分词
    for word in result:
        if word not in stopwords:
            outstr += word + " "
    clean_content.append(outstr) #保留数据预处理后的结果
    outputfile.write(outstr)

print(clean_content)


inputfile.close()
outputfile.close()
