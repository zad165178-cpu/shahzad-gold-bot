import os, time, threading, json, urllib.request, urllib.parse
from collections import deque
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "8513356699")

if not BOT_TOKEN:
    print("BOT_TOKEN missing! Set in Render Environment")

prices = deque(maxlen=100)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Shahzad Bot LIVE - Status OK")

def run_web():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15)
        print("Sent OK")
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_price():
    try:
        req = urllib.request.Request("https://api.gold-api.com/price/XAU", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            return float(json.loads(r.read().decode())['price'])
    except Exception as e:
        print(f"Price Error: {e}")
        return None

def get_news():
    try:
        rss_url = "https://api.rss2json.com/v1/api.json?rss_url=https://www.forexlive.com/feed/"
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            for item in data.get('items', [])[:5]:
                t = item.get('title','').lower()
                if 'gold' in t or 'dollar' in t or 'fed' in t or 'xau' in t:
                    return item.get('title','')[:100]
            return data['items'][0]['title'][:100] if data.get('items') else "No News"
    except:
        return "Gold Market Active"

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

send_msg("✅ <b>Shahzad Bot LIVE Ho Gaya</b>\nAb Status 1 Error Khatam\nHar 5 Min Signal Ayega")

while True:
    try:
        p = get_price()
        if not p:
            time.sleep(60)
            continue
        prices.append(p)
        plist = list(prices)

        if len(plist) < 20:
            print(f"Collecting prices {len(plist)}/20")
            time.sleep(60)
            continue

        e9 = ema(plist[-20:], 9)
        e21 = ema(plist[-20:], 21)
        r = rsi(plist, 14)
        news = get_news()

        diff = abs(e9 - e21) if e9 and e21 else 999
        if diff < 1.0 or (45 < r < 55):
            signal = "WAIT"
        elif e9 > e21 and r > 52:
            signal = "BUY"
        elif e9 < e21 and r < 48:
            signal = "SELL"
        else:
            signal = "WAIT"

        if signal == "WAIT":
            msg = f"""⏳ <b>SABAR KARO - SIDEWAYS</b>

💰 Price: {p:.2f}
📊 RSI: {r:.1f} | EMA9: {e9:.2f} / EMA21: {e21:.2f}
⚠️ Market Sideways Hai, Abhi Entry Mat Lo

📰 News: {news}

⏰ Agla Scan 5 Min Me"""
        elif signal == "BUY":
            sl, tp1, tp2 = p-5.5, p+7, p+14
            msg = f"""🚀 <b>BUY - UPAR JAYEGA ⬆️</b>

💰 ENTRY: {p:.2f}
🛑 SL: {sl:.2f} (-{int((p-sl)*10)} Pips)
🎯 TP1: {tp1:.2f} (+{int((tp1-p)*10)} Pips)
🎯 TP2: {tp2:.2f} (+{int((tp2-p)*10)} Pips)

📊 RSI: {r:.1f}
📰 News: {news}

💡 Abhi BUY Karo"""
        else:
            sl, tp1, tp2 = p+5.5, p-7, p-14
            msg = f"""🔻 <b>SELL - NEECHE JAYEGA ⬇️</b>

💰 ENTRY: {p:.2f}
🛑 SL: {sl:.2f} (-{int((sl-p)*10)} Pips)
🎯 TP1: {tp1:.2f} (+{int((p-tp1)*10)} Pips)
🎯 TP2: {tp2:.2f} (+{int((p-tp2)*10)} Pips)

📊 RSI: {r:.1f}
📰 News: {news}

💡 Abhi SELL Karo"""

        send_msg(msg)

    except Exception as e:
        print(f"Loop Error: {e}")

    time.sleep(300)
