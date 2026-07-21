"""
News sentiment over time — quarterly trend analysis.

Why this script exists
----------------------
The original pipeline (news_data_rewrite.py / news_data_sentiment.py) dropped the
publication date, so we cannot study how sentiment evolves over time from the
existing outputs. Dates ARE recoverable from the raw scraped CSVs:

  * article URL  : https://www.chinadaily.com.cn/a/202512/01/WS....html  -> 2025-12-01
  * author byline: "Updated: 2025-12-01 07:48" or "(China Daily) 2025-11-29 09:51"

We therefore read the RAW CSVs directly (not the cleaned corpus) to keep a
reliable 1:1 mapping between (date, content, sentiment). TextBlob is fast, so
recomputing polarity from the raw content is cheap and avoids any fragile
row-order alignment with the old news_num ids.

Outputs
-------
  data-original/news_data_sentiment_timeseries.csv   (per-article: date, quarter, score, category, source)
  data-original/news_data_sentiment_quarterly.csv    (quarterly aggregates)
  picture-original/sentiment_trend_quarterly.png      (line: mean polarity per quarter)
  picture-original/sentiment_mix_quarterly.png        (stacked bar: pos/neu/neg share per quarter)
"""

import csv
import glob
import os
import re
from collections import defaultdict

import pandas as pd
from textblob import TextBlob
import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt

# ---- locate repo root (script lives in code/) ---------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ORIG = os.path.join(ROOT, "data-original")
PIC_ORIG = os.path.join(ROOT, "picture-original")
os.makedirs(PIC_ORIG, exist_ok=True)

# ---- date extraction -----------------------------------------------------------
URL_RE = re.compile(r"/a/(\d{6})/(\d{2})/")          # /a/202512/01/
URL_RE2 = re.compile(r"/(\d{6})/(\d{2})/")           # looser fallback
UPD_RE = re.compile(r"Updated:\s*(\d{4})-(\d{2})-(\d{2})")
AUTH_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})\s+\d{2}:\d{2}")


def extract_date(url, author):
    """Return 'YYYY-MM-DD' or None, trying URL first then author byline."""
    for rx in (URL_RE, URL_RE2):
        m = rx.search(url or "")
        if m:
            return f"{m.group(1)[:4]}-{m.group(1)[4:]}-{m.group(2)}"
    for rx in (UPD_RE, AUTH_RE):
        m = rx.search(author or "")
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


def quarter_of(date_str):
    y, m, _ = date_str.split("-")
    q = (int(m) - 1) // 3 + 1
    return f"{y}Q{q}"


def classify(score):
    if score > 0.1:
        return "positive"
    if score < -0.1:
        return "negative"
    return "neutral"


def analyze(text):
    if not isinstance(text, str) or text.strip() == "":
        return 0.0
    try:
        return TextBlob(text).sentiment.polarity
    except Exception:
        return 0.0


# ---- gather raw CSVs -----------------------------------------------------------
raw_files = sorted(glob.glob(os.path.join(DATA_ORIG, "*后羿采集器.csv")))
if not raw_files:
    # fallback: also accept any csv that looks like a scrape export
    raw_files = sorted(glob.glob(os.path.join(DATA_ORIG, "*Search Results*.csv")))
print("Found raw scraped files:")
for f in raw_files:
    print("  ", os.path.basename(f))

rows = []
for path in raw_files:
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = {c.lower(): c for c in reader.fieldnames or []}
        url_col = cols.get("标题链接") or cols.get("url") or None
        auth_col = cols.get("author") or cols.get("作者") or None
        content_col = cols.get("content") or cols.get("正文") or None
        if not content_col:
            # try the last column as content
            content_col = reader.fieldnames[-1]
        src = os.path.basename(path)
        for r in reader:
            url = r.get(url_col) if url_col else ""
            author = r.get(auth_col) if auth_col else ""
            content = r.get(content_col) or ""
            date = extract_date(url, author)
            if not date:
                continue
            score = analyze(content)
            rows.append({
                "date": date,
                "quarter": quarter_of(date),
                "sentiment_score": round(score, 6),
                "sentiment_category": classify(score),
                "source_file": src,
            })

df = pd.DataFrame(rows)
print(f"\nTotal dated articles with sentiment: {len(df)}")
print(f"Date coverage: {df['date'].min()} -> {df['date'].max()}")
undated_note = (f"Note: {len(raw_files)} raw files scanned; "
                f"articles without a parseable date were skipped.")

# ---- per-article output --------------------------------------------------------
per_article_path = os.path.join(DATA_ORIG, "news_data_sentiment_timeseries.csv")
df_sorted = df.sort_values("date").reset_index(drop=True)
df_sorted.insert(0, "news_num", [f"news{i+1}" for i in range(len(df_sorted))])
df_sorted.to_csv(per_article_path, index=False, encoding="utf-8-sig")
print(f"Wrote per-article dated sentiment -> {per_article_path}")

# ---- quarterly aggregation -----------------------------------------------------
g = df.groupby("quarter")
quarterly = pd.DataFrame({
    "n_articles": g.size(),
    "mean_polarity": g["sentiment_score"].mean().round(4),
    "median_polarity": g["sentiment_score"].median().round(4),
    "positive": g.apply(lambda x: (x["sentiment_category"] == "positive").sum(), include_groups=False),
    "neutral": g.apply(lambda x: (x["sentiment_category"] == "neutral").sum(), include_groups=False),
    "negative": g.apply(lambda x: (x["sentiment_category"] == "negative").sum(), include_groups=False),
}).reset_index()
quarterly["pos_share"] = (quarterly["positive"] / quarterly["n_articles"]).round(3)
quarterly["neu_share"] = (quarterly["neutral"] / quarterly["n_articles"]).round(3)
quarterly["neg_share"] = (quarterly["negative"] / quarterly["n_articles"]).round(3)
# chronological order by year-quarter
quarterly = quarterly.sort_values("quarter").reset_index(drop=True)

quarterly_path = os.path.join(DATA_ORIG, "news_data_sentiment_quarterly.csv")
quarterly.to_csv(quarterly_path, index=False, encoding="utf-8-sig")
print(f"Wrote quarterly aggregates -> {quarterly_path}")
print(quarterly.to_string(index=False))

# ---- figure 1: mean polarity line --------------------------------------------
plt.figure(figsize=(12, 5))
x = range(len(quarterly))
plt.plot(x, quarterly["mean_polarity"], marker="o", color="#1f77b4", linewidth=2)
plt.axhline(0, color="grey", linestyle="--", linewidth=0.8)
plt.xticks(list(x), quarterly["quarter"], rotation=90)
plt.ylabel("Mean TextBlob polarity")
plt.title("China Daily AI-governance news — mean sentiment by quarter")
plt.tight_layout()
fig1 = os.path.join(PIC_ORIG, "sentiment_trend_quarterly.png")
plt.savefig(fig1, dpi=120)
plt.close()
print(f"Wrote chart -> {fig1}")

# ---- figure 2: stacked share of pos/neu/neg ----------------------------------
plt.figure(figsize=(12, 5))
q = quarterly["quarter"]
plt.bar(q, quarterly["pos_share"], color="#2ca02c", label="positive")
plt.bar(q, quarterly["neu_share"], bottom=quarterly["pos_share"], color="#bcbcbc", label="neutral")
plt.bar(q, quarterly["neg_share"], bottom=quarterly["pos_share"] + quarterly["neu_share"],
        color="#d62728", label="negative")
plt.xticks(rotation=90)
plt.ylabel("Share of articles")
plt.ylim(0, 1)
plt.title("China Daily AI-governance news — sentiment mix by quarter")
plt.legend(loc="upper right")
plt.tight_layout()
fig2 = os.path.join(PIC_ORIG, "sentiment_mix_quarterly.png")
plt.savefig(fig2, dpi=120)
plt.close()
print(f"Wrote chart -> {fig2}")

print("\n" + undated_note)
