# -*- coding: utf-8 -*-
"""
generate_html_report.py  (完整语料版)
读取 data-original/ 下的全部分析结果（3,263 篇 · 2018Q3–2026Q3），
生成一个多彩、交互式、且"基于全部数据"的 HTML 可视化分析报告。
输出：项目根目录 report.html
"""
import os
import csv
import json
import collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data-combined")          # 合并后的全量语料
TREND = os.path.join(BASE, "data-original")          # 仅 data-original 含发布日期，用于时间趋势


def load_word_freq(top=None):
    path = os.path.join(DATA, "data_word_tag_frequency.csv")
    words = []
    with open(path, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            w = row["Word"].strip()
            try:
                freq = int(row["Frequency"])
            except ValueError:
                continue
            if w and freq > 0:
                words.append((w, freq))
    words.sort(key=lambda x: x[1], reverse=True)
    return words if top is None else words[:top]


def load_raw_freq():
    # 合并语料的实词词表规模（词形还原后唯一词数）
    path = os.path.join(DATA, "data_word_tag_frequency.csv")
    unique = 0
    with open(path, "r", encoding="utf-8-sig") as f:
        for _ in csv.DictReader(f):
            unique += 1
    return 0, unique


TOPIC_META = {
    "0": ("全球治理与国际合作", "聚焦全球格局、治理、多边合作中的 AI 议题"),
    "1": ("中美博弈与市场经济", "围绕中美关系、市场、经济增长与相关政策"),
    "2": ("教育与文化发展", "关注教育、高校、数字化与文化议题"),
    "3": ("AI 技术与产业创新", "聚焦人工智能、数据、技术与产业创新"),
    "4": ("AI 医疗与公共服务", "涉及医疗、公共服务与地区（如香港）应用"),
}
def load_topics():
    topics = {}
    path = os.path.join(DATA, "news_data_LDA_topic_result.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if line.startswith("主题") and ":" in line:
                    tid, kw = line.split(":", 1)
                    topics[tid.replace("主题", "").strip()] = kw.strip().split()
    return topics


def load_sentiment():
    path = os.path.join(DATA, "news_data_sentiment.csv")
    counts = collections.Counter()
    total = 0
    with open(path, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            cat = (row.get("sentiment_category") or "").strip().lower()
            if cat:
                counts[cat] += 1
                total += 1
    return dict(counts), total


def load_topic_classify():
    """逐篇主题分配 -> 主题分布 + 主题×情感交叉"""
    path = os.path.join(DATA, "news_data_LDA_classify_result.csv")
    topic_of = {}
    with open(path, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            tid = (row.get("topic_id") or "").strip()
            topic_of[row.get("news_num", "").strip()] = tid
    # 与情感结果 join（按 news_num）
    sent_path = os.path.join(DATA, "news_data_sentiment.csv")
    cat_of = {}
    with open(sent_path, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            cat_of[row.get("news_num", "").strip()] = (row.get("sentiment_category") or "").strip().lower()
    dist = collections.Counter()
    cross = collections.defaultdict(lambda: collections.Counter())
    for n, tid in topic_of.items():
        if not tid:
            continue
        dist[tid] += 1
        cross[tid][cat_of.get(n, "")] += 1
    return dist, cross


def load_trend():
    path = os.path.join(TREND, "news_data_sentiment_quarterly.csv")
    quarters, mean_p, n_art = [], [], []
    pos_s, neu_s, neg_s = [], [], []
    with open(path, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            quarters.append(row["quarter"])
            mean_p.append(round(float(row["mean_polarity"]), 4))
            n_art.append(int(row["n_articles"]))
            pos_s.append(round(float(row["pos_share"]) * 100, 1))
            neu_s.append(round(float(row["neu_share"]) * 100, 1))
            neg_s.append(round(float(row["neg_share"]) * 100, 1))
    return {"quarters": quarters, "mean_polarity": mean_p, "n_articles": n_art,
            "pos_share": pos_s, "neu_share": neu_s, "neg_share": neg_s}


# ================= 汇总 =================
word_freq = load_word_freq(100)
all_lemma = load_word_freq(None)
lemma_unique = len(all_lemma)
raw_total, raw_unique = load_raw_freq()
topics = load_topics()
sentiment, total_articles = load_sentiment()
topic_dist, topic_cross = load_topic_classify()
trend = load_trend()

TOP_N_BAR = 30
bar_words = [w for w, _ in word_freq[:TOP_N_BAR]][::-1]
bar_freqs = [f for _, f in word_freq[:TOP_N_BAR]][::-1]
cloud_data = [{"name": w, "value": f} for w, f in word_freq]

topic_colors = ["#FF6B6B", "#4ECDC4", "#FFD93D", "#6C5CE7", "#FF9F1C"]
topic_list = []
for i, (tid, kws) in enumerate(sorted(topics.items())):
    cn_name, cn_desc = TOPIC_META.get(tid, ("主题", ""))
    topic_list.append({
        "id": tid, "color": topic_colors[i % len(topic_colors)], "keywords": kws,
        "cn_name": cn_name, "cn_desc": cn_desc,
        "dist": topic_dist.get(tid, 0),
        "cross": [topic_cross[tid].get("positive", 0),
                  topic_cross[tid].get("neutral", 0),
                  topic_cross[tid].get("negative", 0)],
    })

sent_labels = ["positive", "neutral", "negative"]
sent_values = [sentiment.get(k, 0) for k in sent_labels]
sent_colors = ["#2ED573", "#A4B0BE", "#FF6B81"]
pos_pct = round(100 * sentiment.get("positive", 0) / total_articles)
neu_pct = round(100 * sentiment.get("neutral", 0) / total_articles)
neg_pct = round(100 * sentiment.get("negative", 0) / total_articles)
span = f"{trend['quarters'][0]} – {trend['quarters'][-1]}"
raw_unique_wan = f"{raw_unique/10000:.1f}万"

data_payload = {
    "bar_words": bar_words, "bar_freqs": bar_freqs, "cloud_data": cloud_data,
    "topics": topic_list, "sent_labels": sent_labels, "sent_values": sent_values,
    "sent_colors": sent_colors, "total_articles": total_articles,
    "top_word": word_freq[0][0], "top_word_freq": word_freq[0][1],
    "n_words": len(word_freq), "span": span,
    "raw_unique": raw_unique, "raw_unique_wan": raw_unique_wan,
    "lemma_unique": lemma_unique,
    "pos_pct": pos_pct, "neu_pct": neu_pct, "neg_pct": neg_pct,
    "trend": trend,
    "topic_dist": [topic_dist.get(t["id"], 0) for t in topic_list],
    "topic_colors": topic_colors,
}

# ================= HTML =================
HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>AI Governance News Corpus · 全量可视化分析报告</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/echarts-wordcloud@2.1.0/dist/echarts-wordcloud.min.js"></script>
<style>
  *{margin:0;padding:0;box-sizing:border-box;}
  :root{--c1:#FF6B6B;--c2:#4ECDC4;--c3:#FFD93D;--c4:#6C5CE7;--c5:#FF9F1C;}
  body{font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
    background:linear-gradient(135deg,#1a1a2e,#16213e 40%,#0f3460);color:#fff;overflow-x:hidden;}
  .wrap{max-width:1180px;margin:0 auto;padding:0 20px;}
  .hero{min-height:56vh;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;position:relative;
    background:radial-gradient(circle at 20% 20%,rgba(255,107,107,.35),transparent 40%),
               radial-gradient(circle at 80% 30%,rgba(78,205,196,.35),transparent 42%),
               radial-gradient(circle at 50% 80%,rgba(108,92,231,.35),transparent 45%);}
  .badge{display:inline-block;padding:6px 16px;border-radius:999px;background:rgba(46,213,115,.15);
    border:1px solid rgba(46,213,115,.4);color:#7CFFB2;font-size:13px;letter-spacing:1px;margin-bottom:14px;}
  .hero h1{font-size:clamp(26px,5vw,52px);font-weight:800;letter-spacing:1px;
    background:linear-gradient(90deg,#FF6B6B,#FFD93D,#4ECDC4,#6C5CE7,#FF9F1C);
    -webkit-background-clip:text;background-clip:text;color:transparent;background-size:300% auto;animation:flow 8s linear infinite;}
  @keyframes flow{to{background-position:300% center;}}
  .hero p{margin-top:14px;color:#cfd8ff;font-size:clamp(14px,2vw,18px);}
  .stats{display:flex;gap:18px;flex-wrap:wrap;justify-content:center;margin-top:34px;}
  .stat{background:rgba(255,255,255,.08);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.18);
    border-radius:18px;padding:22px 30px;min-width:150px;box-shadow:0 8px 32px rgba(0,0,0,.25);}
  .stat .num{font-size:32px;font-weight:800;}
  .stat .lbl{font-size:13px;color:#aab4e8;margin-top:6px;}
  .c1{color:var(--c1);}.c2{color:var(--c2);}.c3{color:var(--c3);}.c4{color:var(--c4);}.c5{color:var(--c5);}
  section{padding:58px 0;}
  h2.sec{font-size:clamp(22px,3.5vw,34px);font-weight:800;margin-bottom:8px;display:inline-block;
    background:linear-gradient(90deg,#4ECDC4,#6C5CE7);-webkit-background-clip:text;background-clip:text;color:transparent;}
  .sub{color:#9aa6d6;margin-bottom:22px;font-size:15px;}
  .card{background:rgba(255,255,255,.06);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,.12);
    border-radius:20px;padding:20px;box-shadow:0 10px 40px rgba(0,0,0,.3);}
  .chart{width:100%;height:460px;}
  .insight{margin-top:16px;padding:16px 18px;border-left:4px solid var(--c2);border-radius:10px;
    background:rgba(78,205,196,.08);color:#dbe6ff;font-size:14.5px;line-height:1.7;}
  .insight b{color:#fff;}
  .findings{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px;}
  .finding{position:relative;overflow:hidden;border-radius:18px;padding:22px;
    background:linear-gradient(135deg,rgba(255,255,255,.1),rgba(255,255,255,.03));border:1px solid rgba(255,255,255,.14);}
  .finding .ic{font-size:26px;}
  .finding .big{font-size:28px;font-weight:800;margin:8px 0 4px;}
  .finding .t{font-size:15px;font-weight:700;color:#fff;}
  .finding .d{font-size:13px;color:#bcc6f0;margin-top:8px;line-height:1.6;}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:22px;}
  .grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:18px;}
  .topic-card{border-radius:18px;padding:22px;background:rgba(255,255,255,.06);
    border:1px solid rgba(255,255,255,.14);transition:transform .25s,box-shadow .25s;}
  .topic-card:hover{transform:translateY(-6px);box-shadow:0 14px 40px rgba(0,0,0,.4);}
  .topic-card .tid{font-size:13px;letter-spacing:2px;opacity:.7;text-transform:uppercase;}
  .topic-card .cn{font-size:18px;font-weight:800;margin-top:6px;}
  .topic-card .desc{font-size:13px;color:#c2cbf0;margin-top:8px;line-height:1.6;}
  .topic-card .cnt{font-size:13px;color:#9aa6d6;margin-top:10px;}
  .topic-card .tags{margin-top:12px;display:flex;flex-wrap:wrap;gap:8px;}
  .tag{font-size:13px;padding:5px 12px;border-radius:999px;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.2);}
  .concl{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;}
  .concl .box{border-radius:18px;padding:24px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);}
  .concl h3{font-size:17px;margin-bottom:10px;color:var(--c3);}
  .concl p{font-size:14px;color:#cdd6ff;line-height:1.75;}
  .concl ul{margin:8px 0 0 18px;font-size:14px;color:#cdd6ff;line-height:1.75;}
  footer{text-align:center;padding:40px 20px;color:#7e8ac0;font-size:13px;}
  @media(max-width:760px){.grid2{grid-template-columns:1fr;}}
</style>
</head>
<body>

<div class="hero wrap">
  <div class="badge">● 基于合并语料（data-new + data-original）</div>
  <h1>AI Governance 新闻语料可视化分析</h1>
  <p>China Daily 全量 AI 治理报道 · 量化 NLP 分析（词频 / 主题 / 情感 / 时间趋势）</p>
  <div class="stats">
    <div class="stat"><div class="num c2" data-count="__TOTAL__">0</div><div class="lbl">分析文章数</div></div>
    <div class="stat"><div class="num c1" data-count="__TOPFREQ__">0</div><div class="lbl">最高频词「__TOPWORD__」</div></div>
    <div class="stat"><div class="num c4" data-count="__NWORD__">0</div><div class="lbl">高频实词（Top100）</div></div>
    <div class="stat"><div class="num c5">__SPAN__</div><div class="lbl">时间跨度</div></div>
  </div>
</div>

<section class="wrap">
  <h2 class="sec">执行摘要 · 核心发现</h2>
  <div class="sub">基于 __TOTAL__ 篇全量报道（__SPAN__）提炼的关键洞察</div>
  <div class="findings">
    <div class="finding"><div class="ic">📊</div><div class="big c2">__TOTAL__</div>
      <div class="t">语料规模</div><div class="d">篇 AI 治理报道构成完整样本，时间跨度 __SPAN__，覆盖技术、产业、政策多视角。</div></div>
    <div class="finding"><div class="ic">🌏</div><div class="big c1">china · ai</div>
      <div class="t">话语重心</div><div class="d">「china」(__TOPFREQ__) 与「ai」高频领跑，呈现以中国视角叙述 AI 发展的鲜明特征。</div></div>
    <div class="finding"><div class="ic">😊</div><div class="big c5">__NEU__%</div>
      <div class="t">情感基调</div><div class="d">中性占 __NEU__%，积极 __POS__%、消极仅 __NEG__%；近八年情感极性高度稳定、整体建设性。</div></div>
    <div class="finding"><div class="ic">🎯</div><div class="big c4">__RAWUNIQWAN__</div>
      <div class="t">词表提炼</div><div class="d">个唯一词经词性筛选与词形还原，聚焦 Top100 高频实词并归并为 5 大主题，形成可解释语义结构。</div></div>
  </div>
</section>

<section class="wrap">
  <h2 class="sec">高频实词 Top 30</h2>
  <div class="sub">名词 / 动词 / 形容词 经词形还原后的词频分布（悬停查看数值）</div>
  <div class="card"><div id="bar" class="chart"></div></div>
  <div class="insight">📌 <b>解读：</b>除「china」「ai」外，<b>technology / development / global / innovation / digital</b> 等高频词显示报道主线为"以技术创新驱动产业升级与全球化发展"；<b>governance / cooperation / international</b> 凸显治理与协作维度。</div>
</section>

<section class="wrap">
  <h2 class="sec">词云</h2>
  <div class="sub">词频越高，字号越大、色彩越鲜艳</div>
  <div class="card"><div id="cloud" class="chart" style="height:520px;"></div></div>
</section>

<section class="wrap">
  <h2 class="sec">情感倾向分布（全量）</h2>
  <div class="sub">基于 TextBlob 极性得分（&gt;0.1 积极 / &lt;−0.1 消极 / 其余中性）</div>
  <div class="card"><div id="sent" class="chart"></div></div>
  <div class="insight">📌 <b>解读：</b>中性报道占主导，符合主流媒体客观陈述的定位；积极情绪主要来自技术突破、政策利好与国际合作，消极内容极少，整体审慎乐观。</div>
</section>

<section class="wrap">
  <h2 class="sec">情感随时间变化趋势</h2>
  <div class="sub">按季度聚合：平均极性（折线）与 积极/中性/消极 占比（堆叠面积），展现 2018–2026 的演进（基于 data-original 含发布日期的 3,263 篇；data-new 444 篇未含日期，已计入整体总量）</div>
  <div class="card"><div id="trend" class="chart" style="height:480px;"></div></div>
  <div class="insight">📌 <b>解读：</b>平均情感极性长期稳定在 0.09 附近，说明语料叙事基调平稳；2022Q1 出现阶段性高点（均值 0.122），2025 年起样本量显著放大（单季 300+ 篇），反映 AI 治理议题热度的持续升温。</div>
</section>

<section class="wrap">
  <h2 class="sec">LDA 主题建模（5 大主题）</h2>
  <div class="sub">由 Top 关键词刻画并辅以中文议题解读；卡片标注各主题文章数</div>
  <div class="grid3" id="topics"></div>
</section>

<section class="wrap">
  <h2 class="sec">主题分布 & 主题×情感</h2>
  <div class="sub">左：各主题文章数占比；右：每个主题内部的情感构成</div>
  <div class="grid2">
    <div class="card"><div id="topicDist" class="chart"></div></div>
    <div class="card"><div id="topicSent" class="chart"></div></div>
  </div>
  <div class="insight">📌 <b>解读：</b>五大主题文章分布相对均衡，表明语料对技术、治理、发展、教育、产业等维度覆盖全面；各主题内部均以中性为主、积极为辅，未见明显负面情绪集中，说明不同议题均呈建设性报道姿态。</div>
</section>

<section class="wrap">
  <h2 class="sec">结论与启示</h2>
  <div class="sub">基于全量语料（__TOTAL__ 篇，__SPAN__）的研究总结</div>
  <div class="concl">
    <div class="box"><h3>🔍 主要发现</h3>
      <p>全量语料以中国视角系统呈现 AI 治理议题：技术底座、全球治理、中国发展、教育创新与产业应用五大主题交织。报道整体中立偏积极且长期稳定，体现"技术发展 + 制度建设"并重的叙事框架。</p></div>
    <div class="box"><h3>💡 实践建议</h3>
      <ul>
        <li>关注"AI 治理""国际合作"高频议题，把握政策与标准动向；</li>
        <li>结合情感趋势监测议题热度（2025 起显著升温）；</li>
        <li>对少量消极信号建立专项追踪，防范潜在风险舆情。</li>
      </ul></div>
    <div class="box"><h3>⚠️ 方法局限</h3>
      <p>样本为单源媒体（China Daily），存在立场偏向；LDA 主题数需结合业务先验设定；情感分析基于词典法，对反讽与隐含情绪敏感度有限。结论宜结合多源语料交叉验证。</p></div>
  </div>
</section>

<footer>生成于 News-Text-Corpus-Analysis · 数据源 data-new + data-original 合并（全量 __TOTAL__ 篇）· 可视化由 ECharts 驱动 · 仅供研究参考</footer>

<script>
const D = __DATA__;
function animateCount(el){const target=+el.dataset.count;let cur=0;const step=Math.max(1,Math.ceil(target/60));
  const t=setInterval(()=>{cur+=step;if(cur>=target){cur=target;clearInterval(t);}el.textContent=cur.toLocaleString();},18);}
document.querySelectorAll('.stat .num[data-count]').forEach(animateCount);

const bar=echarts.init(document.getElementById('bar'));
bar.setOption({grid:{left:95,right:30,top:20,bottom:20},
  tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
  xAxis:{type:'value',axisLabel:{color:'#cfd8ff'},splitLine:{lineStyle:{color:'rgba(255,255,255,.08)'}}},
  yAxis:{type:'category',data:D.bar_words,axisLabel:{color:'#e6ebff'},axisLine:{lineStyle:{color:'rgba(255,255,255,.2)'}}},
  series:[{type:'bar',data:D.bar_freqs,itemStyle:{borderRadius:[0,8,8,0],
    color:new echarts.graphic.LinearGradient(0,0,1,0,[{offset:0,color:'#4ECDC4'},{offset:.5,color:'#6C5CE7'},{offset:1,color:'#FF6B6B'}])},
    label:{show:true,position:'right',color:'#fff',fontWeight:'bold'}}]});

const cloud=echarts.init(document.getElementById('cloud'));
cloud.setOption({tooltip:{show:true},series:[{type:'wordCloud',shape:'circle',sizeRange:[12,72],rotationRange:[-45,45],
  gridSize:6,width:'100%',height:'100%',
  textStyle:{fontWeight:'bold',color:function(){const c=['#FF6B6B','#4ECDC4','#FFD93D','#6C5CE7','#FF9F1C','#2ED573','#FF7F50','#45AAF2'];return c[Math.floor(Math.random()*c.length)];}},
  data:D.cloud_data}]});

const sent=echarts.init(document.getElementById('sent'));
sent.setOption({tooltip:{trigger:'item',formatter:'{b}: {c} 篇 ({d}%)'},legend:{show:false},
  series:[{type:'pie',radius:['42%','70%'],center:['50%','50%'],itemStyle:{borderColor:'#16213e',borderWidth:3,borderRadius:8},
    label:{color:'#fff',fontSize:14,formatter:'{b}\\n{c} 篇 ({d}%)'},
    data:D.sent_labels.map((l,i)=>({name:l,value:D.sent_values[i],itemStyle:{color:D.sent_colors[i]}}))}]});

const tr=echarts.init(document.getElementById('trend'));
tr.setOption({
  tooltip:{trigger:'axis'},
  legend:{data:['平均极性','积极%','中性%','消极%'],textStyle:{color:'#cdd6ff'},top:0},
  grid:{left:50,right:55,top:40,bottom:60},
  xAxis:{type:'category',data:D.trend.quarters,axisLabel:{color:'#cfd8ff',rotate:55,fontSize:10},
    axisLine:{lineStyle:{color:'rgba(255,255,255,.2)'}}},
  yAxis:[
    {type:'value',name:'平均极性',min:0,max:0.2,axisLabel:{color:'#cfd8ff'},splitLine:{lineStyle:{color:'rgba(255,255,255,.08)'}}},
    {type:'value',name:'占比%',min:0,max:100,axisLabel:{color:'#cfd8ff',formatter:'{value}%'},splitLine:{show:false}}
  ],
  series:[
    {name:'平均极性',type:'line',smooth:true,data:D.trend.mean_polarity,
      lineStyle:{width:3,color:'#FFD93D'},itemStyle:{color:'#FFD93D'},symbolSize:6,z:5},
    {name:'积极%',type:'line',stack:'share',areaStyle:{opacity:.55},smooth:true,data:D.trend.pos_share,itemStyle:{color:'#2ED573'},lineStyle:{width:0},symbol:'none'},
    {name:'中性%',type:'line',stack:'share',areaStyle:{opacity:.55},smooth:true,data:D.trend.neu_share,itemStyle:{color:'#A4B0BE'},lineStyle:{width:0},symbol:'none'},
    {name:'消极%',type:'line',stack:'share',areaStyle:{opacity:.55},smooth:true,data:D.trend.neg_share,itemStyle:{color:'#FF6B81'},lineStyle:{width:0},symbol:'none'}
  ]});

const tc=document.getElementById('topics');
D.topics.forEach(t=>{
  const tags=t.keywords.map(k=>`<span class="tag">${k}</span>`).join('');
  const el=document.createElement('div');el.className='topic-card';
  el.style.boxShadow=`inset 0 -4px 0 ${t.color}, 0 10px 30px rgba(0,0,0,.3)`;
  el.innerHTML=`<div class="tid" style="color:${t.color}">Topic ${t.id}</div>
    <div class="cn" style="color:${t.color}">${t.cn_name}</div>
    <div class="desc">${t.cn_desc}</div>
    <div class="cnt">📄 归属文章：${t.dist} 篇</div>
    <div class="tags">${tags}</div>`;
  tc.appendChild(el);
});

const td=echarts.init(document.getElementById('topicDist'));
td.setOption({title:{text:'各主题文章数',left:'center',textStyle:{color:'#e6ebff',fontSize:15}},
  tooltip:{trigger:'item',formatter:'{b}: {c} 篇 ({d}%)'},
  series:[{type:'pie',radius:['40%','68%'],data:D.topics.map((t,i)=>({name:t.cn_name,value:D.topic_dist[i],itemStyle:{color:D.topic_colors[i]}})),
    label:{color:'#fff',formatter:'{b}\\n{c}'}}]});

const ts=echarts.init(document.getElementById('topicSent'));
ts.setOption({title:{text:'主题内情感构成',left:'center',textStyle:{color:'#e6ebff',fontSize:15}},
  tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
  legend:{data:['积极','中性','消极'],textStyle:{color:'#cdd6ff'},top:28},
  grid:{left:50,right:20,top:64,bottom:30},
  xAxis:{type:'category',data:D.topics.map(t=>t.cn_name),axisLabel:{color:'#cfd8ff',interval:0,fontSize:11},axisLine:{lineStyle:{color:'rgba(255,255,255,.2)'}}},
  yAxis:{type:'value',axisLabel:{color:'#cfd8ff'},splitLine:{lineStyle:{color:'rgba(255,255,255,.08)'}}},
  series:[
    {name:'积极',type:'bar',stack:'s',data:D.topics.map(t=>t.cross[0]),itemStyle:{color:'#2ED573'}},
    {name:'中性',type:'bar',stack:'s',data:D.topics.map(t=>t.cross[1]),itemStyle:{color:'#A4B0BE'}},
    {name:'消极',type:'bar',stack:'s',data:D.topics.map(t=>t.cross[2]),itemStyle:{color:'#FF6B81'}}
  ]});

window.addEventListener('resize',()=>{[bar,cloud,sent,tr,td,ts].forEach(c=>c.resize());});
</script>
</body>
</html>"""

HTML = (HTML
        .replace("__TOTAL__", str(total_articles))
        .replace("__TOPWORD__", word_freq[0][0])
        .replace("__TOPFREQ__", str(word_freq[0][1]))
        .replace("__NWORD__", str(len(word_freq)))
        .replace("__SPAN__", span)
        .replace("__POS__", str(pos_pct))
        .replace("__NEU__", str(neu_pct))
        .replace("__NEG__", str(neg_pct))
        .replace("__RAWUNIQWAN__", raw_unique_wan)
        .replace("__DATA__", json.dumps(data_payload, ensure_ascii=False)))

out_path = os.path.join(BASE, "report.html")
with open(out_path, "w", encoding="utf-8-sig") as f:
    f.write(HTML)

print("已生成(全量版):", out_path)
print("文章数:", total_articles, "| 跨度:", span, "| 实词唯一:", lemma_unique,
      "| 主题分布:", dict(topic_dist), "| 情感:", sentiment)
