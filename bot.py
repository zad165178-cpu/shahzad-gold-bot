import os, time, requests, threading
from collections import deque
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
prices = deque(maxlen=50)

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=15)
    except Exception as e:
        print(e)

def get_live_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        return float(r['price'])
    except:
        return 4172.5

def ema(data, period):
    if len(data) < period: return sum(data)/len(data)
    k = 2 / (period + 1)
    ema_val = sum(data[:period]) / period
    for price in data[period:]:
        ema_val = price * k + ema_val * (1 - k)
    return ema_val

def rsi(data, period=14):
    if len(data) < period+1: return 55
    gains, losses = 0, 0
    for i in range(1, period+1):
        diff = data[-i] - data[-i-1]
        if diff > 0: gains += diff
        else: losses += abs(diff)
    if losses == 0: return 70
    rs = gains / losses
    return 100 - (100 / (1 + rs))

def bot_loop():
    time.sleep(5)
    send_msg("🚀 *GOLD BOT V30 PRO MAX STARTED*\n10 Min | EMA 9/21 | RSI | SL/TP\nLive Now...")
    last_signal_type = ""
    
    while True:
        try:
            live = get_live_price()
            prices.append(live)

            e9 = ema(list(prices), 9)
            e21 = ema(list(prices), 21)
            r = rsi(list(prices), 14)

            # --- PRO TRADING LOGIC ---
            if len(prices) > 21:
                if e9 > e21 and r > 52 and r < 70:
                    signal_type = "BUY"
                    entry = live
                    sl = live - 7
                    tp1 = live + 4
                    tp2 = live + 8.5
                    tp3 = live + 15
                    msg = f"🟢 *GOLD BUY SIGNAL - UP TREND*\n\n💰 Live: `{entry:.2f}`\n📊 EMA: {e9:.2f} > {e21:.2f}\n📈 RSI: {r:.1f}\n\n🎯 Entry: `{entry:.2f}`\n🛑 SL: `{sl:.2f}` (-7$)\n✅ TP1: `{tp1:.2f}`\n✅ TP2: `{tp2:.2f}`\n✅ TP3: `{tp3:.2f}`\n\n⏰ 10 Min TF"
                
                elif e9 < e21 and r < 48 and r > 30:
                    signal_type = "SELL"
                    entry = live
                    sl = live + 7
                    tp1 = live - 4
                    tp2 = live - 8.5
                    tp3 = live - 15
                    msg = f"🔴 *GOLD SELL SIGNAL - DOWN TREND*\n\n💰 Live: `{entry:.2f}`\n📊 EMA: {e9:.2f} < {e21:.2f}\n📉 RSI: {r:.1f}\n\n🎯 Entry: `{entry:.2f}`\n🛑 SL: `{sl:.2f}` (+7$)\n✅ TP1: `{tp1:.2f}`\n✅ TP2: `{tp2:.2f}`\n✅ TP3: `{tp3:.2f}`\n\n⏰ 10 Min TF"
                
                else:
                    signal_type = "WAIT"
                    msg = f"🟡 *WAIT - NO TRADE*\n\n💰 Live: `{live:.2f}`\n📊 EMA 9/21: {e9:.2f} / {e21:.2f}\n📈 RSI: {r:.1f}\n\n❌ No Clear Trend - Avoid"
                
                # Same signal repeat nahi hoga
                if signal_type != last_signal_type or signal_type == "WAIT":
                    if signal_type != "WAIT" or True: # WAIT bhi bhejna hai har 10 min
                        send_msg(msg)
                    if signal_type != "WAIT":
                        last_signal_type = signal_type
            
            else:
               
