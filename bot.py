import os, time, requests
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

last_signal = ""

def get_live():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get("https://data-asg.goldprice.org/dbXRates/USD", headers=headers, timeout=12).json()
        p = float(r['items'][0]['xauPrice'])
        if p > 3000: return p
    except: pass
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", headers=headers, timeout=12).json()
        return float(r['price'])
    except: pass
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", headers=headers, timeout=12).json()
        return float(r['price'])
    except: pass
    return None

def get_candles():
    try:
        url = "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=100"
        d = requests.get(url, timeout=12).json()
        return [float(c[4]) for c in d]
    except:
        return None

def send(t):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": t}, timeout=12)
    except: pass

def ema(arr, n): return sum(arr[-n:]) / n

def rsi(arr, per=14):
    if len(arr) < per+1: return 50
    g = l = 0
    for i in range(-per, 0):
        diff = arr[i] - arr[i-1]
        if diff > 0: g += diff
        else: l += abs(diff)
    if l == 0: return 70
    rs = g / l
    return 100 - (100 / (1 + rs))

send("GOLD BOT V30 - 10 MIN MODE STARTED")

while True:
    live = get_live()
    candles = get_candles()

    if live is None or candles is None:
        print("API fail, silent retry 60 sec")
        time.sleep(60)
        continue

    e9 = ema(candles, 9)
    e21 = ema(candles, 21)
    e50 = ema(candles, 50)
    r = rsi(candles, 14)

    if abs(e9 - e21) < 2.0 and 46 < r < 54:
        msg = f"SIDEWAYS - DO NOT TRADE\nLive: {live:.2f}\nRSI: {r:.1f}"
        sig = "SIDEWAYS"
    elif e9 > e21 and e21 > e50 and 55 < r < 70:
        msg = f"BUY SIGNAL - PRICE WILL GO UP\nLive: {live:.2f}\nEntry: {live:.2f}\nSL: {live-6:.2f}\nTP: {live+4:.2f} / {live+8:.2f} / {live+14:.2f}"
        sig = "BUY"
    elif e9 < e21 and e21 < e50 and 30 < r < 45:
        msg = f"SELL SIGNAL - PRICE WILL GO DOWN\nLive: {live:.2f}\nEntry: {live:.2f}\nSL: {live+6:.2f}\nTP: {live-4:.2f} / {live-8:.2f} / {live-14:.2f}"
        sig = "SELL"
    else:
        msg = f"WAIT - DO NOT TRADE NOW\nLive: {live:.2f}\nEMA: {e9:.2f}/{e21:.2f} RSI: {r:.1f}"
        sig = "WAIT"

    if sig!= last_signal or sig in ["BUY", "SELL"]:
        if sig!= last_signal:
            send(msg)
            last_signal = sig

    time.sleep(600) # <-- 10 MINUTE FIX
