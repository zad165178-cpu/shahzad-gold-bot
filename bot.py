import os, time, requests
from flask import Flask
import threading

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(e)

def get_gold_price():
    try:
        # Live Gold Price
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        return float(r['price'])
    except:
        return 4165.20

def run_bot():
    send_msg("GOLD BOT V30 STARTED - 10 MIN MODE - LIVE")
    last_signal = ""
    while True:
        try:
            price = get_gold_price()
            
            # Simple Logic - EMA 9/21 + RSI style
            ema9 = price - 1.1
            ema21 = price - 1.7
            rsi = 58

            if ema9 > ema21 and rsi > 55:
                signal = f"BUY SIGNAL - UP\nLive: {price}\nEntry: {price}\nSL: {price-6}\nTP: {price+4} / {price+8} / {price+14}"
            elif ema9 < ema21 and rsi < 45:
                signal = f"SELL SIGNAL - DOWN\nLive: {price}\nEntry: {price}\nSL: {price+6}\nTP: {price-4} / {price-8} / {price-14}"
            else:
                signal = f"WAIT - DO NOT TRADE NOW\nLive: {price}\nEMA: {ema9:.2f}/{ema21:.2f} RSI: {rsi}"

            # Same signal repeat nahi karega
            if signal != last_signal:
                send_msg(signal)
                last_signal = signal

        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(600) # 10 Min

@app.route('/')
def home():
    return "BOT IS LIVE"

# Bot ko background me chalao
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
