import os, time, requests, threading
from flask import Flask

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PRICES = []

def send(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=20)
        print("Sent")
    except Exception as e:
        print(f"Send Fail: {e}")

def get_gold():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        return float(r['price'])
    except:
        return None

def ema(data, period):
    if len(data) < period:
        return sum(data)/len(data) if data else 0
    k = 2 / (period + 1)
    ema_val = sum(data[:period]) / period
    for p in data[period:]:
        ema_val = p * k + ema_val * (1 - k)
    return ema_val

def rsi(data, period=14):
    if len(data) < period + 1:
        return 50
    gains = 0
    losses = 0
    for i in range(1, period + 1):
        diff = data[-i] - data[-i-1]
        if diff > 0:
            gains += diff
        else:
            losses += abs(diff)
    if losses == 0:
        return 70
    rs = gains / losses
    return 100 - (100 / (1 + rs))

def loop():
    time.sleep(8)
    if not BOT_TOKEN or not CHAT_ID:
        print("ENV MISSING")
        return
    send("✅ *GOLD BOT PRO 50 LIVE*\nEMA 9/21/50 + RSI\n10 Min TF Started")
    
    last_signal = ""
    while True:
        try:
            price = get_gold()
            if not price:
                time.sleep(30)
                continue
            
            PRICES.append(price)
            if len(PRICES) > 50:
                PRICES.pop(0)

            print(f"Price: {price} | Len: {len(PRICES)}")

            if len(PRICES) < 22:
                send(f"⏳ *Loading Data {len(PRICES)}/50*\nLive: {price}")
                time.sleep(600)
                continue

            e9 = ema(PRICES, 9)
            e21 = ema(PRICES, 21)
            e50 = ema(PRICES, 50)
            r = rsi(PRICES, 14)

            if e9 > e21 and e21 > e50 and r > 55 and r < 68:
                signal = "BUY"
            elif e9 < e21 and e21 < e50 and r < 45 and r > 32:
                signal = "SELL"
            else:
                signal = "WAIT"

            if signal == "BUY" and last_signal != "BUY":
                msg = f"🟢 *GOLD BUY - STRONG UP*\n\n💰 Price: `{price:.2f}`\n📊 EMA 9: {e9:.2f}\n📊 EMA 21: {e21:.2f}\n📊 EMA 50: {e50:.2f}\n📈 RSI: {r:.1f}\n\n🎯 Entry: {price:.2f}\n🛑 SL: {price-7:.2f}\n✅ TP1: {price+4:.2f}\n✅ TP2: {price+9:.2f}\n✅ TP3: {price+16:.2f}"
                send(msg)
                last_signal = "BUY"
            elif signal == "SELL" and last_signal != "SELL":
                msg = f"🔴 *GOLD SELL - STRONG DOWN*\n\n💰 Price: `{price:.2f}`\n📊 EMA 9: {e9:.2f}\n📊 EMA 21: {e21:.2f}\n📊 EMA 50: {e50:.2f}\n📉 RSI: {r:.1f}\n\n🎯 Entry: {price:.2f}\n🛑 SL: {price+7:.2f}\n✅ TP1: {price-4:.2f}\n✅ TP2: {price-9:.2f}\n✅ TP3: {price-16:.2f}"
                send(msg)
                last_signal = "SELL"
            else:
                # Har 10 min WAIT update
                send(f"🟡 *WAIT - Sideways*\nPrice: {price:.2f}\nEMA 9/21/50: {e9:.1f}/{e21:.1f}/{e50:.1f}\nRSI: {r:.1f}\nNo Entry Now")

        except Exception as e:
            print(f"Loop Error {e}")
        
        time.sleep(600) # 10 MIN

threading.Thread(target=loop, daemon=True).start()

@app.route('/')
def home():
    return "GOLD BOT PRO 50 IS LIVE"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
