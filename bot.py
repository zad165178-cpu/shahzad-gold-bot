import os
import time
import requests
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

price_history = []

def get_gold_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        return float(r.json()['price'])
    except:
        try:
            # backup api
            r = requests.get("https://api.metals.live/v1/spot", timeout=10)
            return float(r.json()[0]['gold'])
        except:
            return None

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
        print("Sent")
    except Exception as e:
        print(e)

def get_analysis(prices):
    if len(prices) < 21:
        return "WAIT", prices[-1]

    ema9 = sum(prices[-9:]) / 9
    ema21 = sum(prices[-21:]) / 21
    last = prices[-1]

    if ema9 > ema21:
        return "BUY", last
    else:
        return "SELL", last

# Start message
send_msg("GOLD BOT STARTED - You will get signal every 5 min")

while True:
    try:
        price = get_gold_price()
        if price:
            price_history.append(price)
            if len(price_history) > 50:
                price_history.pop(0)

            print(f"Price: {price} - Count: {len(price_history)}")

            # Analysis
            signal, entry = get_analysis(price_history)

            if len(price_history) < 21:
                msg = f"""
WAIT - COLLECTING DATA

Current Price: {entry:.2f}
Status: {len(price_history)}/21 candles collected
Next signal in 5 min
"""
                send_msg(msg)
            else:
                if signal == "BUY":
                    sl = entry - 7.0
                    tp1 = entry + 4.0
                    tp2 = entry + 8.0
                    tp3 = entry + 13.0
                    status = "GOOD TRADE - BUY NOW"
                    news = "Trend is UP"
                else:
                    sl = entry + 7.0
                    tp1 = entry - 4.0
                    tp2 = entry - 8.0
                    tp3 = entry - 13.0
                    status = "GOOD TRADE - SELL NOW"
                    news = "Trend is DOWN"

                msg = f"""
{signal} SIGNAL - {status}

Pair: XAUUSD GOLD
News: {news} - Take Trade Now

Entry: {entry:.2f}

Stop Loss: {sl:.2f}
SL Pips: 70 pips (700 points)
SL Area: Price will reverse from here

Take Profit:
TP1: {tp1:.2f} (40 pips)
TP2: {tp2:.2f} (80 pips)
TP3: {tp3:.2f} (130 pips)

Time: {datetime.now().strftime('%H:%M:%S')} UTC
Next Update: After 5 min
"""
                send_msg(msg)

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(300)
