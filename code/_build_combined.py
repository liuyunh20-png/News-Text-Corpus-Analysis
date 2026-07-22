# 合并 data-new 与 data-original，生成 data-combined/
import csv, os, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "data-combined")
os.makedirs(OUT, exist_ok=True)

def load(p):
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def ren(rows, prefix):
    for r in rows:
        r["news_num"] = prefix + r["news_num"]
    return rows

# 1) rewrite（语料正文）
new = ren(load(os.path.join(BASE, "data-new/news_data_rewrite.csv")), "N_")
orig = ren(load(os.path.join(BASE, "data-original/news_data_rewrite.csv")), "O_")
combined = new + orig
with open(os.path.join(OUT, "news_data_rewrite.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["news_num", "news_content"]); w.writeheader()
    for r in combined:
        w.writerow({"news_num": r["news_num"], "news_content": r["news_content"]})

# 2) sentiment（情感，重编号以匹配）
ns = ren(load(os.path.join(BASE, "data-new/news_data_sentiment.csv")), "N_")
os_ = ren(load(os.path.join(BASE, "data-original/news_data_sentiment.csv")), "O_")
with open(os.path.join(OUT, "news_data_sentiment.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["news_num", "news_content", "sentiment_score", "sentiment_category"]); w.writeheader()
    for r in ns + os_:
        w.writerow(r)

# 3) 词频 union-sum（词形还原后的实词）
cnt = collections.Counter()
for p in ["data-new/data_word_tag_frequency.csv", "data-original/data_word_tag_frequency.csv"]:
    for row in load(os.path.join(BASE, p)):
        cnt[row["Word"]] += int(row["Frequency"])
with open(os.path.join(OUT, "data_word_tag_frequency.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["Word", "Frequency"])
    for wd, fr in cnt.most_common():
        w.writerow([wd, fr])

print("合并 rewrite:", len(combined), "| 合并 sentiment:", len(ns) + len(os_), "| 合并实词词表:", len(cnt))
