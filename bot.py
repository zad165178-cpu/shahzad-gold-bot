import os, time, threading, json, urllib.request, urllib.parse
from collections import deque
from http.server import HTTPServer, BaseHTTPRequestHandler
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YAHAN_APNA_TOKEN_DALO")
CHAT_ID = os.environ.get("CHAT_ID", "8513356699")
prices = deque(maxlen=100)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Shahzad FINAL + NEWS Bot Running")

def run_web():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

def get_price():
    try:
        req = urllib.request.Request("https://api.gold-api.com/price/XAU", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            return float(json.loads(r.read().decode())['price'])
    except:
        return None

def get_gold_news():
    try:
        # Gold / USD / Fed news RSS se
        rss_url = "https://api.rss2json.com/v1/api.json?rss_url=https://www.forexlive.com/feed/"
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            news = []
            for item in data.get('items', [])[:10]:
                title = item.get('title','').lower()
                if 'gold' in title or 'dollar' in title or 'fed' in title or 'xau' in title or 'usd' in title or 'inflation' in title:
                    news.append(item.get('title',''))
            if not news:
                # agar gold ki news na mile to top 2 general news le lo
                news = [data['items'][0]['title'], data['items'][1]['title']] if len(data.get('items',[]))>=2 else []
            return news[:2]
    except Exception as e:
        print(f"News Error: {e}")
        return []

def send_chart(caption, prices_list, signal):
    try:
        plt.figure(figsize=(7, 3.5))
        plt.plot(prices_list, linewidth=2.5, color='#FFD700' if signal=='BUY' else '#FF3B30' if signal=='SELL' else '#8E8E93')
        plt.fill_between(range(len(prices_list)), prices_list, alpha=0.15, color='#FFD700' if signal=='BUY' else '#FF3B30' if signal=='SELL' else 'gray')
        plt.title(f"XAUUSD GOLD - {signal} - 5 MIN", fontsize=10, fontweight='bold')
        plt.grid(True, alpha=0.2)
        plt.tight_layout()
        path = "/tmp/gold_chart.png"
        plt.savefig(path, dpi=200)
        plt.close()

        import requests
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(path, 'rb') as photo:
            requests.post(url, data={'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'HTML'}, files={'photo': photo}, timeout=30)
    except Exception as e:
        print(f"Send Error: {e}")
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": caption, "parse_mode": "HTML"}).encode()
            urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10)
        except: pass

def ema(data, period):
    if len(data) < period: return None
    k = 2/(period+1)
    e = data[0]
    for p in data[1:]: e = p*k + e*(1-k)
    return e

def rsi(data, period=14):
    if len(data) < period+1: return 50
    g=l=0
    for i in range(1, period+1):
        ch = data[-i]-data[-i-1]
        if ch>0: g+=ch
        else: l+=abs(ch)
    if l==0: return 70
    return 100 - (100/(1+g/l))

# Start
try:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    txt = "✅ <b>Shahzad PRO MAX + NEWS Bot ON</b>\nChart + Pips + News Har 5 Min"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": txt, "parse_mode": "HTML"}).encode()
    urllib.request.urlopen(urllib.request.Request(url, data=data))
except: pass

while True:
    try:
        p = get_price()
        if not p:
            time.sleep(30)
            continue

        prices.append(p)
        plist = list(prices)
        if len(plist) < 20:
            time.sleep(60)
            continue

        e9 = ema(plist[-20:], 9)
        e21 = ema(plist[-20:], 21)
        r = rsi(plist, 14)

        news_list = get_gold_news()
        news_text = ""
        if news_list:
            news_text = "\n\n📰 <b>NEWS IMPACT:</b>\n"
            for n in news_list:
                news_text += f"• {n[:90]}\n"

        diff = abs(e9 - e21) if e9 and e21 else 999
        if diff < 0.8 or (45 < r < 55):
            signal = "WAIT"
        elif e9 > e21 and r > 52:
            signal = "BUY"
        elif e9 < e21 and r < 48:
            signal = "SELL"
        else:
            signal = "WAIT"

        if signal == "WAIT":
            caption = f"""⏳ <b>SIDEWAYS - SABAR KARO</b>

💰 Price: <b>{p:.2f}</b>
📊 RSI: {r:.1f} | EMA9/21: {e9:.2f}/{e21:.2f}
⚠️ Market Sideways Hai - Entry Mat Lo{news_text}

⏰ Next Scan 5 Min"""
        elif signal == "BUY":
            entry, sl, tp1, tp2 = p, p-5.5, p+7, p+14
            caption = f"""🚀 <b>BUY - UPAR JAYEGA ⬆️</b>

💰 ENTRY: {entry:.2f}
🛑 SL: {sl:.2f} (-{int((entry-sl)*10)} Pips)
🎯 TP1: {tp1:.2f} (+{int((tp1-entry)*10)} Pips)
🎯 TP2: {tp2:.2f} (+{int((tp2-entry)*10)} Pips)

📊 RSI: {r:.1f} | Conf: 87%{news_text}

💡 BUY Karo, SL Neeche"""
        else:
            entry, sl, tp1, tp2 = p, p+5.5, p-7, p-14
            caption = f"""🔻 <b>SELL - NEECHE JAYEGA ⬇️</b>

💰 ENTRY: {entry:.2f}
🛑 SL: {sl:.2f} (-{int((sl-entry)*10)} Pips)
🎯 TP1: {tp1:.2f} (+{int((entry-tp1)*10)} Pips)
🎯 TP2: {tp2:.2f} (+{int((entry-tp2)*10)} Pips)

📊 RSI: {r:.1f} | Conf: 87%{news_text}

💡 SELL Karo, SL Upar"""

        send_chart(caption, plist[-40:], signal)

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(300) # 5 min
