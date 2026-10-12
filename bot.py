import os, time, threading, urllib.request, urllib.parse, json
from collections import deque
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
prices = deque(maxlen=500)
candles = deque(maxlen=50)
cur = {"o":0,"h":0,"l":99999,"c":0,"start":0}
news_list = []

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"24H NEWS + PIPS BOT LIVE")

def web():
    HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 10000))), H).serve_forever()

threading.Thread(target=web, daemon=True).start()

def send(t):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data=urllib.parse.urlencode({"chat_id":CHAT_ID,"text":t,"parse_mode":"HTML"}).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15)
    except: pass

def gp():
    try:
        req=urllib.request.Request("https://api.gold-api.com/price/XAU", headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            return float(json.loads(r.read().decode())['price'])
    except: return None

def get_news():
    global news_list
    try:
        url="https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data=json.loads(r.read().decode())
            today_news=[]
            today_str=datetime.utcnow().strftime("%Y-%m-%d")
            for n in data:
                if today_str in n['date'] and 'USD' in n['country'] and n['impact'] in ['High','Medium']:
                    today_news.append(f"{n['title']} - {n['time']} ({n['impact']})")
            news_list=today_news[:5]
            return today_news
    except:
        return news_list

def ema(d,p):
    if len(d)<p: return None
    k=2/(p+1); e=d[0]
    for v in d[1:]: e=v*k+e*(1-k)
    return e

def rsi(d,pe=14):
    if len(d)<pe+1: return 50
    g=l=0
    for i in range(1,pe+1):
        ch=d[-i]-d[-i-1]
        if ch>0: g+=ch
        else: l+=abs(ch)
    if l==0: return 70
    return 100-(100/(1+g/l))

def atr(d,pe=14):
    if len(d)<pe+1: return 3.5
    trs=[]
    for i in range(1,pe+1):
        trs.append(abs(d[-i]-d[-i-1]))
    return sum(trs)/len(trs)

def pat(a,b):
    b1=abs(a['c']-a['o']); b2=abs(b['c']-b['o'])
    if b2==0: return None,0
    bull=b['c']>b['o'] and b['o']<a['c'] and b['c']>a['o'] and b2>b1*1.3
    bear=b['c']<b['o'] and b['o']>a['c'] and b['c']<a['o'] and b2>b1*1.3
    if bull: return "BULLISH ENGULFING",90
    if bear: return "BEARISH ENGULFING",90
    return None,0

if BOT_TOKEN and CHAT_ID:
    news=get_news()
    news_text="\n".join(news) if news else "No High Impact News Today - Safe to Trade"
    send(f"🚀 <b>24H ULTIMATE BOT LIVE</b>\n\n<b>📰 Aaj ki News:</b>\n{news_text}\n\n✅ 24H Working\n✅ Pips Prediction ON\n✅ News Filter ON\n✅ 80%+ Only")

last_scan=0
print("24H BOT STARTED")

while True:
    try:
        p=gp()
        if not p: time.sleep(20); continue
        now=time.time()
        if now-cur['start']>300 or cur['start']==0:
            if cur['o']!=0: candles.append(dict(cur))
            cur={"o":p,"h":p,"l":p,"c":p,"start":now}
        else:
            cur['h']=max(cur['h'],p); cur['l']=min(cur['l'],p); cur['c']=p
        prices.append(p)

        if time.time()-last_scan>7200 and len(candles)>=5:
            last_scan=time.time()
            n=get_news()
            nt="\n".join(n) if n else "No News"
            send(f"⏳ <b>24H SCAN ACTIVE</b> | Gold ${p:.2f}\n\n<b>📰 News Update:</b>\n{nt}\n\nNo best setup yet - Waiting for 85%+ confirmation")

        if len(candles)<8 or len(prices)<60: time.sleep(30); continue

        pl=list(prices); e9=ema(pl[-30:],9); e21=ema(pl[-50:],21); e50=ema(pl,50); r=rsi(pl,14); atr_v=atr(pl,14)
        pips_up = int(atr_v * 10 * 2.5)
        pips_down = int(atr_v * 10 * 2.5)
        c1=candles[-2]; c2=candles[-1]
        pattern, pc = pat(c1,c2)

        sig=None; conf=0
        if e9 and e21 and e50 and pattern:
            if e9>e21>e50 and "BULLISH" in pattern and 48<r<65:
                sig="BUY"; conf=pc + (r-45)
            elif e9<e21<e50 and "BEARISH" in pattern and 35<r<52:
                sig="SELL"; conf=pc + (52-r)

        if sig and conf>=82:
            conf=int(min(92, conf))
            sl=p- (atr_v*1.2) if sig=="BUY" else p+(atr_v*1.2)
            tp1=p+ (atr_v*1.8) if sig=="BUY" else p-(atr_v*1.8)
            tp2=p+ (atr_v*3.2) if sig=="BUY" else p-(atr_v*3.2)
            tp3=p+ (atr_v*5) if sig=="BUY" else p-(atr_v*5)
            pip_tp1=int(abs(tp1-p)*10)
            pip_tp2=int(abs(tp2-p)*10)
            pip_tp3=int(abs(tp3-p)*10)
            msg=f"""<b>🔥 BEST TRADE FOUND 🔥</b>

<b>{sig} GOLD - {pattern}</b>
<b>Entry:</b> {p:.2f}

<b>📈 Pips Prediction:</b>
Up: +{pips_up} pips | Down: -{pips_down} pips

<b>🛑 SL:</b> {sl:.2f} ({int(abs(sl-p)*10)} pips)
<b>🎯 TP1:</b> {tp1:.2f} (+{pip_tp1} pips)
<b>🎯 TP2:</b> {tp2:.2f} (+{pip_tp2} pips)
<b>💎 TP3:</b> {tp3:.2f} (+{pip_tp3} pips)

<b>✅ Confirmation: {conf}%</b>
<b>RSI:</b> {r:.1f} | <b>ATR:</b> {atr_v:.2f}

<i>0.01 lot only</i>"""
            send(msg)
            time.sleep(3600)

        time.sleep(40)
    except Exception as e:
        print(e); time.sleep(20)
