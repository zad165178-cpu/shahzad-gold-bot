import os, time, requests
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def get_live():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        return float(r['price'])
    except:
        try:
            r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=10).json()
            return float(r['price'])
        except:
            return None # Apna rate nahi likhunga

def get_candles():
    try:
        url="https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=1m&limit=50"
        d=requests.get(url,timeout=10).json()
        return [float(c[4]) for c in d]
    except:
        return None

def send(t):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHAT_ID,"text":t})
    except: pass

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

send("GOLD V7 FINAL STARTED - Live Only + Full Analysis")

while True:
    live = get_live()
    closes = get_candles()

    if live is None or closes is None:
        send("Live API Fail - 1 min baad phir try karunga, apna rate nahi likhunga")
        time.sleep(60)
        continue

    e9=ema(closes,9); e21=ema(closes,21)
    rsi_v=rsi(closes,14)

    # NEWS CHECK - US Time
    now=datetime.utcnow()
    news=False
    if now.hour in [12,13,18] and now.minute<40:
        msg=f"""
NEWS ALERT

Live Rate: {live:.2f}
News Time: {now.strftime('%H:%M UTC')} - US News Chal Raha Hai

Action: ABHI TRADE MAT LO
Reason: News me market tez hilta hai
"""
        send(msg)
        time.sleep(1800)
        continue

    # SIDEWAYS CHECK
    if abs(e9-e21)<1.5 and 45<rsi_v<55:
        msg=f"""
SIDEWAYS - TRADE MAT LO

Live Rate: {live:.2f} (Market me abhi yehi chal raha hai)
EMA9: {e9:.2f} | EMA21: {e21:.2f} | RSI: {rsi_v:.1f}

Market: Sideways hai, upar neeche ho raha hai
Action: ABHI TRADE NAHI LENI
"""
        send(msg)
        time.sleep(300)
        continue

    # BUY / SELL
    if e9>e21 and rsi_v>53 and live>e9:
        msg=f"""
BUY SIGNAL - UPAR JAYEGA

Live Rate: {live:.2f} (Yehi rate market me hai)
Direction: Yahan se UPAR JAYEGA

Entry: {live:.2f}
SL: {live-6:.2f} (60 pips)
TP1: {live+3.5:.2f} | TP2: {live+7:.2f} | TP3: {live+12:.2f}
Condition: UPTREND | News: Nahi | Sideways: Nahi
Action: BUY LE SAKTE HO
"""
    elif e9<e21 and rsi_v<47 and live<e9:
        msg=f"""
SELL SIGNAL - NEECHE JAYEGA

Live Rate: {live:.2f} (Yehi rate market me hai)
Direction: Yahan se NEECHE JAYEGA

Entry: {live:.2f}
SL: {live+6:.2f} (60 pips)
TP1: {live-3.5:.2f} | TP2: {live-7:.2f} | TP3: {live-12:.2f}
Condition: DOWNTREND | News: Nahi | Sideways: Nahi
Action: SELL LE SAKTE HO
"""
    else:
        msg=f"""
WAIT - ABHI TRADE MAT LO

Live Rate: {live:.2f}
EMA: {e9:.2f}/{e21:.2f} | RSI: {rsi_v:.1f}
Reason: Confirmation nahi hai

Action: WAIT - Agla check 5 min me
"""
    send(msg)
    time.sleep(300)
