"""Build a source-linked Chinese news digest. AI summaries are optional, never fabricated."""
import os, re, json, html, datetime, pathlib, urllib.parse
import feedparser, requests

ROOT=pathlib.Path(__file__).parent
OUT=ROOT/'site'/'news.json'
TODAY=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
TOPICS=[
 ('政策与经济','国家政策 经济 就业 site:gov.cn OR site:news.cn',1.0),
 ('教育与就业','高校毕业生 招聘 考研 教育部 site:moe.gov.cn OR site:news.cn',1.2),
 ('AI与科技','人工智能 产业 政策 site:gov.cn OR site:news.cn',1.1),
 ('汽车与制造','新能源汽车 智能制造 工信部 site:miit.gov.cn OR site:news.cn',1.3),
 ('财富与社会','居民收入 消费 房地产 统计 site:stats.gov.cn OR site:news.cn',0.9),
]
ALLOWED=['gov.cn','news.cn','xinhuanet.com','stats.gov.cn','moe.gov.cn','miit.gov.cn','people.com.cn']

def source_domain(text):
    m=re.search(r'(?:https?://)?([\w.-]+\.(?:gov\.cn|news\.cn|xinhuanet\.com|people\.com\.cn))',text,re.I)
    return m.group(1).lower() if m else ''

def is_allowed(domain):
    return any(domain==d or domain.endswith('.'+d) for d in ALLOWED)

def clean(s):
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',s or ''))).strip()

def get_feed(query):
    url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':query+' when:7d','hl':'zh-CN','gl':'CN','ceid':'CN:zh-Hans'})
    r=requests.get(url,timeout=25,headers={'User-Agent':'Mozilla/5.0 NewsResearchDigest/1.0'})
    r.raise_for_status()
    return feedparser.parse(r.content).entries

def ai_analyze(items):
    key=os.environ.get('OPENAI_API_KEY')
    if not key or not items: return items
    try:
        from openai import OpenAI
        client=OpenAI(api_key=key)
        payload=[{'id':x['id'],'title':x['title'],'source':x['source'],'category':x['category']} for x in items]
        res=client.chat.completions.create(model=os.getenv('OPENAI_MODEL','gpt-4.1-mini'),temperature=0.2,response_format={'type':'json_object'},messages=[
            {'role':'system','content':'你是谨慎的中文新闻解读编辑。仅根据提供的新闻标题和来源进行解读，不得编造报道细节、数字、政策原文或采访内容。输出JSON对象，键为items，值为数组，每项含id,plain,why,impact,caveat。plain是通俗解释标题含义(不超过80字)，why解释为何值得关注(不超过75字)，impact面向正在准备专升本、学习新能源汽车技术、关心就业的大学生(不超过80字)，caveat注明仅凭标题不能确认的事项。不得把推断说成事实。'},
            {'role':'user','content':json.dumps(payload,ensure_ascii=False)}
        ])
        parsed=json.loads(res.choices[0].message.content)
        mapping={x['id']:x for x in parsed.get('items',[]) if isinstance(x,dict) and 'id' in x}
        for item in items:
            a=mapping.get(item['id'],{})
            for field in ['plain','why','impact','caveat']:
                if isinstance(a.get(field),str): item[field]=a[field][:220]
            item['ai']=bool(a.get('plain'))
    except Exception as exc:
        print('AI unavailable:',type(exc).__name__,str(exc)[:160])
    return items

def main():
    items=[]; seen=set(); errors=[]
    for category,query,weight in TOPICS:
        try: entries=get_feed(query)
        except Exception as exc:
            errors.append(f'{category}: {type(exc).__name__}')
            continue
        for e in entries[:18]:
            title=clean(e.get('title',''))
            publisher=clean(e.get('source',{}).get('title','')) if hasattr(e.get('source',{}),'get') else ''
            source_url=e.get('source',{}).get('href','') if hasattr(e.get('source',{}),'get') else ''
            domain=urllib.parse.urlparse(source_url).hostname or source_domain(title+' '+publisher)
            if not is_allowed(domain or ''): continue
            title=re.sub(r'\s+-\s+[^-]+$','',title).strip()
            key=re.sub(r'\W','',title)[:38]
            if not key or key in seen:continue
            seen.add(key)
            pub=e.get('published_parsed')
            if pub:
                stamp=datetime.datetime(*pub[:6],tzinfo=datetime.timezone.utc)
                age=max(0,(TODAY.astimezone(datetime.timezone.utc)-stamp).total_seconds()/86400)
            else: age=7;stamp=TODAY
            score=round(min(9.8,5.5+weight*1.5+max(0,7-age)*0.27),1)
            items.append({'id':str(len(items)+1),'title':title,'category':category,'source':publisher or domain,'source_domain':domain,'url':e.get('link',''),'published':stamp.isoformat(),'score':score,'plain':'目前仅显示经过来源筛选的新闻标题，尚未生成AI解读。','why':'此条与政策、就业、技术或经济趋势有关，值得进一步核对原文。','impact':'结合个人升学和新能源汽车职业规划判断是否需要关注。','caveat':'请点击原文核实；聚合新闻链接可能跳转。','ai':False})
    items.sort(key=lambda x:(-x['score'],x['published']))
    items=items[:24]
    ai_analyze(items)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({'updated_at':TODAY.isoformat(),'items':items,'errors':errors,'method':'Google News RSS索引 + 指定权威媒体域名过滤；仅依据标题进行AI解读，需点击原文核实。','ai_enabled':any(x['ai'] for x in items)},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Wrote {len(items)} news entries; AI: {sum(x["ai"] for x in items)}; errors: {errors}')

if __name__=='__main__':main()
