import os, time, requests

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

last_sent = ""

def get_live_price():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get("https://data-asg.goldprice.org/dbXRates/USD", headers=headers, timeout=10).json()
        return float(r['items'][0]['xauPrice'])
    except:
        try:
            r = requests.get("https://api.gold-api.com/price/XAU", headers=headers, timeout=10).json()
            return float(r['price'])
        except:
            try:
                r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", headers=headers, timeout=10).json()
                return float(r['price'])
            except:
                return None

def get_candles():
    try:
        url="https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=1m&limit=50"
        d=requests.get(url,timeout=10).json()
        return [float(c[4]) for c in d]
    except:
        return None

def send(t):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHAT_ID,"text":t})

def ema(p,n): return sum(p[-n:])/n

def rsi(p,per=14):
    if len(p)<per+1: return 50
    g=l=0
    for i in range(-per,0):
        d=p[i]-p[i-1]
        if d>0: g+=d
        else: l+=abs(d)
    if l==0: return 70
    return 100-(100/(1+g/l))

send("GOLD BOT V10 - ENGLISH ONLY - LIVE PRICE - STARTED")

while True:
    live = get_live_price()
    closes = get_candles()
    if live is None or closes is None:
        time.sleep(30)
        continue

    e9=ema(closes,9); e21=ema(closes,21); rsi_v=rsi(closes,14)

    if abs(e9-e21)<1.5 and 45<rsi_v<55:
        msg=f"SIDEWAYS MARKET\nLive Price: {live:.2f}\nRSI: {rsi_v:.1f}\nAction: DO NOT TRADE"
    elif e9>e21 and rsi_v>53:
        msg=f"BUY SIGNAL\nLive Price: {live:.2f}\nDirection: UP\nEntry: {live:.2f}\nSL: {live-6:.2f} (60 pips)\nTP1: {live+4:.2f} TP2: {live+8:.2f} TP3: {live+12:.2f}"
    elif e9<e21 and rsi_v<47:
        msg=f"SELL SIGNAL\nLive Price: {live:.2f}\nDirection: DOWN\nEntry: {live:.2f}\nSL: {live+6:.2f} (60 pips)\nTP1: {live-4:.2f} TP2: {live-8:.2f} TP3: {live-12:.2f}"
    else:
        msg=f"WAIT - NO TRADE\nLive Price: {live:.2f}\nEMA9: {e9:.2f} EMA21: {e21:.2f} RSI: {rsi_v:.1f}\nAction: WAIT"

    if msg!= last_sent:
        send(msg)
        last_sent = msg

    time.sleep(300)
