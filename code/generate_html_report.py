# -*- coding: utf-8 -*-
"""
generate_html_report.py
读取真实分析结果（data-new/），生成一个"多彩 + 有分析深度"的交互式 HTML 报告。
输出：项目根目录 report.html
"""
import os
import csv
import json
import collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_NEW = os.path.join(BASE, "data-new")

# ---------------- 1. 实词（名词/动词/形容词，已词形还原） ----------------
def load_word_freq(top=None):
    path = os.path.join(DATA_NEW, "data_word_tag_frequency.csv")
    words = []
    with open(path, "r", encoding="utf-8") as f:
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

# ---------------- 2. 原始词频（含全部 token） ----------------
def load_raw_freq():
    path = os.path.join(DATA_NEW, "data_word_frequency.csv")
    total = 0
    unique = 0
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                total += int(row["Frequency"])
            except ValueError:
                continue
            unique += 1
    return total, unique

# ---------------- 3. LDA 主题关键词 + 中文解读 ----------------
TOPIC_META = {
    "0": ("AI 技术与算力基础设施", "聚焦人工智能、数据、算力与模型等核心技术要素"),
    "1": ("全球治理与多边合作", "强调中国在全球 AI 治理、国际合作与多边机制中的角色"),
    "2": ("产业创新与市场规模", "围绕产业升级、技术创新与市场规模扩张的议题"),
    "3": ("经济发展与增长动力", "关注宏观经济发展、服务业增长与新质生产力"),
    "4": ("法律合规与内容治理", "涉及文化权益、法律框架与公共内容治理"),
}
def load_topics():
    topics = {}
    for fname in ["news_data_LDA_topic_result.txt", "news_data_LDA_classify_result.txt"]:
        path = os.path.join(DATA_NEW, fname)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("主题") and ":" in line:
                    tid, kw = line.split(":", 1)
                    topics[tid.replace("主题", "").strip()] = kw.strip().split()
    return topics

# ---------------- 4. 情感分析 ----------------
def load_sentiment():
    path = os.path.join(DATA_NEW, "news_data_sentiment.csv")
    counts = collections.Counter()
    total = 0
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cat = (row.get("sentiment_category") or "").strip().lower()
            if cat:
                counts[cat] += 1
                total += 1
    return dict(counts), total

# ---------------- 5. 情感随时间变化（按季度，基于全量语料） ----------------
def load_quarterly():
    path = os.path.join(BASE, "data-original", "news_data_sentiment_quarterly.csv")
    labels, mean, pos, neu, neg, n = [], [], [], [], [], []
    if not os.path.exists(path):
        return labels, mean, pos, neu, neg, n
    with open(path, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            labels.append(row["quarter"])
            mean.append(round(float(row["mean_polarity"]), 4))
            pos.append(round(float(row["pos_share"]), 3))
            neu.append(round(float(row["neu_share"]), 3))
            neg.append(round(float(row["neg_share"]), 3))
            try:
                n.append(int(row["n_articles"]))
            except ValueError:
                n.append(0)
    return labels, mean, pos, neu, neg, n

# ================= 汇总计算 =================
word_freq = load_word_freq(100)
all_lemma = load_word_freq(None)
lemma_total = sum(f for _, f in all_lemma)
lemma_unique = len(all_lemma)
raw_total, raw_unique = load_raw_freq()
topics = load_topics()
sentiment, total_articles = load_sentiment()
(q_labels, q_mean, q_pos, q_neu, q_neg, q_n) = load_quarterly()
ts_total = sum(q_n)

TOP_N_BAR = 30
bar_words = [w for w, _ in word_freq[:TOP_N_BAR]][::-1]
bar_freqs = [f for _, f in word_freq[:TOP_N_BAR]][::-1]
cloud_data = [{"name": w, "value": f} for w, f in word_freq]

topic_colors = ["#FF6B6B", "#4ECDC4", "#FFD93D", "#6C5CE7", "#FF9F1C"]
topic_list = []
for i, (tid, kws) in enumerate(sorted(topics.items())):
    cn_name, cn_desc = TOPIC_META.get(tid, ("主题", ""))
    topic_list.append({
        "id": tid,
        "color": topic_colors[i % len(topic_colors)],
        "keywords": kws,
        "cn_name": cn_name,
        "cn_desc": cn_desc,
    })

sent_labels = ["positive", "neutral", "negative"]
sent_values = [sentiment.get(k, 0) for k in sent_labels]
sent_colors = ["#2ED573", "#A4B0BE", "#FF6B81"]
pos_pct = round(100 * sentiment.get("positive", 0) / total_articles)
neu_pct = round(100 * sentiment.get("neutral", 0) / total_articles)
neg_pct = round(100 * sentiment.get("negative", 0) / total_articles)
compression = round(raw_total / lemma_total, 1) if lemma_total else 0

data_payload = {
    "bar_words": bar_words, "bar_freqs": bar_freqs, "cloud_data": cloud_data,
    "topics": topic_list, "sent_labels": sent_labels, "sent_values": sent_values,
    "sent_colors": sent_colors, "total_articles": total_articles,
    "top_word": word_freq[0][0], "top_word_freq": word_freq[0][1],
    "n_words": len(word_freq),
    "raw_total": raw_total, "raw_unique": raw_unique,
    "lemma_total": lemma_total, "lemma_unique": lemma_unique,
    "compression": compression, "pos_pct": pos_pct, "neu_pct": neu_pct, "neg_pct": neg_pct,
    "ts_total": ts_total,
    "q_labels": q_labels, "q_mean": q_mean, "q_pos": q_pos, "q_neu": q_neu, "q_neg": q_neg, "q_n": q_n,
}

# ================= 生成 HTML =================
HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>AI Governance News Corpus · 可视化分析报告</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/echarts-wordcloud@2.1.0/dist/echarts-wordcloud.min.js"></script>
<style>
  *{margin:0;padding:0;box-sizing:border-box;}
  :root{--c1:#FF6B6B;--c2:#4ECDC4;--c3:#FFD93D;--c4:#6C5CE7;--c5:#FF9F1C;--ink:#1a1a2e;}
  body{font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
    background:linear-gradient(135deg,#1a1a2e,#16213e 40%,#0f3460);color:#fff;overflow-x:hidden;}
  .wrap{max-width:1180px;margin:0 auto;padding:0 20px;}
  .hero{min-height:58vh;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;position:relative;
    background:radial-gradient(circle at 20% 20%,rgba(255,107,107,.35),transparent 40%),
               radial-gradient(circle at 80% 30%,rgba(78,205,196,.35),transparent 42%),
               radial-gradient(circle at 50% 80%,rgba(108,92,231,.35),transparent 45%);}
  .hero h1{font-size:clamp(28px,5vw,56px);font-weight:800;letter-spacing:1px;
    background:linear-gradient(90deg,#FF6B6B,#FFD93D,#4ECDC4,#6C5CE7,#FF9F1C);
    -webkit-background-clip:text;background-clip:text;color:transparent;background-size:300% auto;animation:flow 8s linear infinite;}
  @keyframes flow{to{background-position:300% center;}}
  .hero p{margin-top:14px;color:#cfd8ff;font-size:clamp(14px,2vw,18px);}
  .stats{display:flex;gap:18px;flex-wrap:wrap;justify-content:center;margin-top:34px;}
  .stat{background:rgba(255,255,255,.08);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.18);
    border-radius:18px;padding:22px 30px;min-width:150px;box-shadow:0 8px 32px rgba(0,0,0,.25);}
  .stat .num{font-size:34px;font-weight:800;}
  .stat .lbl{font-size:13px;color:#aab4e8;margin-top:6px;}
  .c1{color:var(--c1);}.c2{color:var(--c2);}.c3{color:var(--c3);}.c4{color:var(--c4);}.c5{color:var(--c5);}
  section{padding:60px 0;}
  h2.sec{font-size:clamp(22px,3.5vw,34px);font-weight:800;margin-bottom:8px;display:inline-block;
    background:linear-gradient(90deg,#4ECDC4,#6C5CE7);-webkit-background-clip:text;background-clip:text;color:transparent;}
  .sub{color:#9aa6d6;margin-bottom:22px;font-size:15px;}
  .card{background:rgba(255,255,255,.06);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,.12);
    border-radius:20px;padding:20px;box-shadow:0 10px 40px rgba(0,0,0,.3);}
  .chart{width:100%;height:460px;}
  .insight{margin-top:16px;padding:16px 18px;border-left:4px solid var(--c2);border-radius:10px;
    background:rgba(78,205,196,.08);color:#dbe6ff;font-size:14.5px;line-height:1.7;}
  .insight b{color:#fff;}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:22px;}
  .grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:18px;}
  .topic-card{border-radius:18px;padding:22px;background:rgba(255,255,255,.06);
    border:1px solid rgba(255,255,255,.14);transition:transform .25s,box-shadow .25s;}
  .topic-card:hover{transform:translateY(-6px);box-shadow:0 14px 40px rgba(0,0,0,.4);}
  .topic-card .tid{font-size:13px;letter-spacing:2px;opacity:.7;text-transform:uppercase;}
  .topic-card .cn{font-size:18px;font-weight:800;margin-top:6px;}
  .topic-card .desc{font-size:13px;color:#c2cbf0;margin-top:8px;line-height:1.6;}
  .topic-card .tags{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px;}
  .tag{font-size:13px;padding:5px 12px;border-radius:999px;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.2);}
  /* Key Findings */
  .findings{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px;margin-top:10px;}
  .finding{position:relative;overflow:hidden;border-radius:18px;padding:22px;
    background:linear-gradient(135deg,rgba(255,255,255,.1),rgba(255,255,255,.03));
    border:1px solid rgba(255,255,255,.14);}
  .finding .ic{font-size:26px;}
  .finding .big{font-size:30px;font-weight:800;margin:8px 0 4px;}
  .finding .t{font-size:15px;font-weight:700;color:#fff;}
  .finding .d{font-size:13px;color:#bcc6f0;margin-top:8px;line-height:1.6;}
  /* Conclusion */
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
  <h1>AI Governance 新闻语料可视化分析</h1>
  <p>基于 China Daily 的 AI 治理新闻语料 · 量化 NLP 分析（词频 / 主题 / 情感）</p>
  <div class="stats">
    <div class="stat"><div class="num c2" data-count="__TOTAL__">0</div><div class="lbl">分析文章数</div></div>
    <div class="stat"><div class="num c1" data-count="__TOPFREQ__">0</div><div class="lbl">最高频词「__TOPWORD__」</div></div>
    <div class="stat"><div class="num c4" data-count="__NWORD__">0</div><div class="lbl">高频实词（Top100）</div></div>
    <div class="stat"><div class="num c5" data-count="__NTOPIC__">0</div><div class="lbl">LDA 主题数</div></div>
  </div>
</div>

<!-- 执行摘要 / 核心发现 -->
<section class="wrap">
  <h2 class="sec">执行摘要 · 核心发现</h2>
  <div class="sub">用数据说话：本报告从语料规模、话语重心、情感基调与主题结构四个维度提炼关键洞察</div>
  <div class="findings">
    <div class="finding"><div class="ic">📊</div><div class="big c2">__TOTAL__</div>
      <div class="t">语料规模</div><div class="d">篇 AI 治理相关英文报道构成分析样本，覆盖技术、产业、政策多视角。</div></div>
    <div class="finding"><div class="ic">🌏</div><div class="big c1">china · ai</div>
      <div class="t">话语重心</div><div class="d">「china」(2968) 与「ai」(2175) 为绝对高频词，呈现以中国视角叙述 AI 发展的鲜明特征。</div></div>
    <div class="finding"><div class="ic">😊</div><div class="big c5">__NEU__%</div>
      <div class="t">情感基调</div><div class="d">中性报道占 __NEU__%，积极 __POS__%、消极仅 __NEG__%，整体为客观且建设性的叙事基调。</div></div>
    <div class="finding"><div class="ic">🎯</div><div class="big c4">__RAWUNIQ_WAN__</div>
      <div class="t">词表提炼</div><div class="d">个唯一词经词性筛选与词形还原，聚焦 Top100 高频实词并归并为 5 大主题，实现从海量词表到可解释语义结构的提炼。</div></div>
  </div>
</section>

<section class="wrap">
  <h2 class="sec">高频实词 Top 30</h2>
  <div class="sub">名词 / 动词 / 形容词 经词形还原后的词频分布（悬停查看数值）</div>
  <div class="card"><div id="bar" class="chart"></div></div>
  <div class="insight">📌 <b>解读：</b>除「china」「ai」外，<b>global / development / technology / innovation / market / industry</b> 等词高频出现，说明报道聚焦"以技术创新驱动产业升级与全球化发展"的主线；<b>governance / policy / cooperation / international</b> 则凸显治理与协作维度。</div>
</section>

<section class="wrap">
  <h2 class="sec">词云</h2>
  <div class="sub">词频越高，字号越大、色彩越鲜艳</div>
  <div class="card"><div id="cloud" class="chart" style="height:520px;"></div></div>
</section>

<section class="wrap">
  <h2 class="sec">情感倾向分布</h2>
  <div class="sub">基于 TextBlob 极性得分（&gt;0.1 积极 / &lt;−0.1 消极 / 其余中性）</div>
  <div class="card"><div id="sent" class="chart"></div></div>
  <div class="insight">📌 <b>解读：</b>中性报道占主导，符合主流媒体客观陈述事实的定位；积极情绪主要来自技术突破、政策利好与国际合作进展，消极内容极少，反映语料整体持审慎乐观的建设性态度。</div>
</section>

<section class="wrap">
  <h2 class="sec">LDA 主题建模（5 个主题）</h2>
  <div class="sub">每个主题由 Top 关键词刻画并辅以中文议题解读，反映语料核心议题版图</div>
  <div class="grid3" id="topics"></div>
</section>

<!-- 情感随时间变化（按季度） -->
<section class="wrap">
  <h2 class="sec">情感随时间变化 · 按季度</h2>
  <div class="sub">基于<b>全量语料</b>（2018–2026，共 __TS_TOTAL__ 篇）的 TextBlob 极性得分，按季度聚合，观察新闻态度随时间的变化</div>

  <div class="card"><div id="trend" class="chart"></div></div>
  <div class="insight">📌 <b>解读：</b>各季度平均 polarity 长期位于 <b>0.07–0.12</b> 的温和正向区间，整体基调稳定、建设性为主；
    其中 <b>2022Q1 达到峰值（0.122）</b>，此后回落并稳定在约 0.095–0.10。说明 China Daily 对 AI 治理的报道始终保持审慎乐观，未出现明显情绪拐点。
    <span style="color:#9aa6d6">（注：2018Q3 仅 1 篇、2026Q3 为进行中季度，解读时宜谨慎。）</span></div>

  <div class="card" style="margin-top:22px;"><div id="mix" class="chart"></div></div>
  <div class="insight">📌 <b>解读：</b>中性报道在各季度占 <b>50%–65%</b>，主导地位稳固；积极占比由 2019 年的约 27–40% 升至 2022–2026 年的 <b>46%–49%</b>，
    呈现温和上行后趋稳；消极占比极低（各季度 ≤ 3.4%，多数仅 0–2%），进一步印证语料以正面、建设性叙事为主的特征。</div>
</section>

<!-- 结论与启示 -->
<section class="wrap">
  <h2 class="sec">结论与启示</h2>
  <div class="sub">基于上述量化结果的研究总结与建议</div>
  <div class="concl">
    <div class="box"><h3>🔍 主要发现</h3>
      <p>语料以中国视角系统呈现 AI 治理议题：技术底座（算力/模型）、全球治理合作、产业创新、经济发展与法律合规五大主题相互交织。报道整体中立偏积极，体现"技术发展 + 制度建设"并重的叙事框架。</p></div>
    <div class="box"><h3>💡 实践建议</h3>
      <ul>
        <li>关注"AI 治理""国际合作"高频议题，把握政策与标准动向；</li>
        <li>追踪主题 0/2（技术·产业）以识别技术商业化信号；</li>
        <li>对消极信号（仅占 __NEG__%）建立专项监测，防范风险舆情。</li>
      </ul></div>
    <div class="box"><h3>⚠️ 方法局限</h3>
      <p>样本为单源媒体（China Daily），存在立场偏向；LDA 主题数需结合业务先验设定；情感分析基于词典法，对反讽与隐含情绪敏感度有限。结论宜结合多源语料交叉验证。</p></div>
  </div>
</section>

<footer>生成于 News-Text-Corpus-Analysis · 数据来源 data-new/ · 可视化由 ECharts 驱动 · 仅供研究参考</footer>

<script>
const D = __DATA__;
function animateCount(el){const target=+el.dataset.count;let cur=0;const step=Math.max(1,Math.ceil(target/60));
  const t=setInterval(()=>{cur+=step;if(cur>=target){cur=target;clearInterval(t);}el.textContent=cur.toLocaleString();},18);}
document.querySelectorAll('.stat .num').forEach(animateCount);

const bar=echarts.init(document.getElementById('bar'));
bar.setOption({grid:{left:90,right:30,top:20,bottom:20},
  tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
  xAxis:{type:'value',axisLabel:{color:'#cfd8ff'},splitLine:{lineStyle:{color:'rgba(255,255,255,.08)'}}},
  yAxis:{type:'category',data:D.bar_words,axisLabel:{color:'#e6ebff'},axisLine:{lineStyle:{color:'rgba(255,255,255,.2)'}}},
  series:[{type:'bar',data:D.bar_freqs,itemStyle:{borderRadius:[0,8,8,0],
    color:new echarts.graphic.LinearGradient(0,0,1,0,[{offset:0,color:'#4ECDC4'},{offset:.5,color:'#6C5CE7'},{offset:1,color:'#FF6B6B'}])},
    label:{show:true,position:'right',color:'#fff',fontWeight:'bold'}}]});

const cloud=echarts.init(document.getElementById('cloud'));
cloud.setOption({tooltip:{show:true},series:[{type:'wordCloud',shape:'circle',sizeRange:[12,68],rotationRange:[-45,45],
  gridSize:6,width:'100%',height:'100%',
  textStyle:{fontWeight:'bold',color:function(){const c=['#FF6B6B','#4ECDC4','#FFD93D','#6C5CE7','#FF9F1C','#2ED573','#FF7F50','#45AAF2'];return c[Math.floor(Math.random()*c.length)];}},
  data:D.cloud_data}]});

const sent=echarts.init(document.getElementById('sent'));
sent.setOption({tooltip:{trigger:'item',formatter:'{b}: {c} 篇 ({d}%)'},legend:{show:false},
  series:[{type:'pie',radius:['42%','70%'],center:['50%','50%'],itemStyle:{borderColor:'#16213e',borderWidth:3,borderRadius:8},
    label:{color:'#fff',fontSize:14,formatter:'{b}\\n{c} 篇 ({d}%)'},
    data:D.sent_labels.map((l,i)=>({name:l,value:D.sent_values[i],itemStyle:{color:D.sent_colors[i]}}))}]});

const tc=document.getElementById('topics');
D.topics.forEach(t=>{
  const tags=t.keywords.map(k=>`<span class="tag">${k}</span>`).join('');
  const el=document.createElement('div');el.className='topic-card';
  el.style.boxShadow=`inset 0 -4px 0 ${t.color}, 0 10px 30px rgba(0,0,0,.3)`;
  el.innerHTML=`<div class="tid" style="color:${t.color}">Topic ${t.id}</div>
    <div class="cn" style="color:${t.color}">${t.cn_name}</div>
    <div class="desc">${t.cn_desc}</div>
    <div class="tags">${tags}</div>`;
  tc.appendChild(el);
});
const trend=echarts.init(document.getElementById('trend'));
trend.setOption({
  grid:{left:60,right:30,top:30,bottom:90},
  tooltip:{trigger:'axis',formatter:function(ps){const i=ps[0].dataIndex;
    return D.q_labels[i]+'<br/>平均 polarity: <b>'+D.q_mean[i]+'</b><br/>样本量: '+D.q_n[i]+' 篇';}},
  xAxis:{type:'category',data:D.q_labels,axisLabel:{color:'#cfd8ff',rotate:90,fontSize:10},
    axisLine:{lineStyle:{color:'rgba(255,255,255,.2)'}}},
  yAxis:{type:'value',name:'平均 polarity',nameTextStyle:{color:'#cfd8ff'},
    axisLabel:{color:'#cfd8ff'},splitLine:{lineStyle:{color:'rgba(255,255,255,.08)'}}},
  series:[{type:'line',data:D.q_mean,smooth:true,symbol:'circle',symbolSize:7,
    lineStyle:{width:3,color:'#4ECDC4'},itemStyle:{color:'#FFD93D'},
    areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(78,205,196,.45)'},{offset:1,color:'rgba(78,205,196,0)'}])},
    markLine:{silent:true,symbol:'none',data:[{yAxis:0}],lineStyle:{color:'grey',type:'dashed'}}}]
});

const mix=echarts.init(document.getElementById('mix'));
mix.setOption({
  grid:{left:60,right:30,top:36,bottom:90},
  tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:v=>(v*100).toFixed(1)+'%'},
  legend:{data:['positive','neutral','negative'],textStyle:{color:'#cfd8ff'},top:0},
  xAxis:{type:'category',data:D.q_labels,axisLabel:{color:'#cfd8ff',rotate:90,fontSize:10},
    axisLine:{lineStyle:{color:'rgba(255,255,255,.2)'}}},
  yAxis:{type:'value',max:1,axisLabel:{color:'#cfd8ff',formatter:v=>(v*100)+'%'},
    splitLine:{lineStyle:{color:'rgba(255,255,255,.08)'}}},
  series:[
    {name:'positive',type:'bar',stack:'s',data:D.q_pos,itemStyle:{color:'#2ED573'}},
    {name:'neutral',type:'bar',stack:'s',data:D.q_neu,itemStyle:{color:'#A4B0BE'}},
    {name:'negative',type:'bar',stack:'s',data:D.q_neg,itemStyle:{color:'#FF6B81'}}
  ]
});

window.addEventListener('resize',()=>{bar.resize();cloud.resize();sent.resize();trend.resize();mix.resize();});
</script>
</body>
</html>"""

HTML = (HTML
        .replace("__TOTAL__", str(total_articles))
        .replace("__TOPWORD__", word_freq[0][0])
        .replace("__TOPFREQ__", str(word_freq[0][1]))
        .replace("__NWORD__", str(len(word_freq)))
        .replace("__NTOPIC__", str(len(topic_list)))
        .replace("__POS__", str(pos_pct))
        .replace("__NEU__", str(neu_pct))
        .replace("__NEG__", str(neg_pct))
        .replace("__RAWUNIQ_WAN__", f"{raw_unique/10000:.1f}万")
        .replace("__TS_TOTAL__", str(ts_total))
        .replace("__DATA__", json.dumps(data_payload, ensure_ascii=False)))

out_path = os.path.join(BASE, "report.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(HTML)

print("已生成:", out_path)
print("文章数:", total_articles, "| 原始唯一词:", raw_unique, "| 实词唯一:", lemma_unique,
      "| 压缩比:", compression, "| 情感:", sentiment)
