import os, time, requests, threading
from flask import Flask
app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
PRICES = []

def send(t):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": t, "parse_mode": "Markdown"}, timeout=15)
    except: pass

def get_live():
    try:
        return float(requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()['price'])
    except: return None

def get_history():
    try:
        url = "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=15m&limit=50"
        data = requests.get(url, timeout=10).json()
        return [float(c[4]) for c in data]
    except: return []

def ema(d, p):
    if len(d) < p: return sum(d)/len(d)
    k = 2/(p+1)
    e = sum(d[:p])/p
    for x in d[p:]: e = x*k + e*(1-k)
    return e

def rsi(d, p=14):
    if len(d) < p+1: return 50
    g=l=0
    for i in range(1, p+1):
        diff = d[-i]-d[-i-1]
        if diff>0: g+=diff
        else: l+=abs(diff)
    if l==0: return 70
    return 100-(100/(1+g/l))

def loop():
    global PRICES
    time.sleep(5)
    PRICES = get_history()
    send("✅ *GOLD 24H LIVE BOT STARTED*\nEMA 9/21/50 + RSI\nSL/TP Auto")

    last = ""
    while True:
        try:
            live = get_live()
            if not live:
                time.sleep(20)
                continue

            PRICES.append(live)
            if len(PRICES) > 50: PRICES.pop(0)

            e9 = ema(PRICES, 9)
            e21 = ema(PRICES, 21)
            e50 = ema(PRICES, 50)
            r = rsi(PRICES, 14)

            # 24H TREND LOGIC - Clean Signal
            # UPTREND = Price > EMA50 and EMA9 > EMA21
            # DOWNTREND = Price < EMA50 and EMA9 < EMA21

            if live > e50 and e9 > e21 and r > 55 and r < 70:
                sig = "BUY"
            elif live < e50 and e9 < e21 and r < 45:
                sig = "SELL"
            else:
