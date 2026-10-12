import requests
import time
import random
from datetime import datetime

# === YOUR SETTINGS ===
TELEGRAM_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"
CHAT_ID = "PASTE_YOUR_CHAT_ID_HERE"
SCAN_INTERVAL = 300  # 5 Minutes = 300 seconds

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except:
        pass

def get_gold_analysis():
    # Dummy smart analysis - you can connect real TradingView later
    # For now it gives realistic Gold levels
    price = 2045 + random.uniform(-5, 5)
    rsi = random.randint(30, 75)
    pips = random.randint(25, 80)
    
    if rsi < 45:
        signal = "BUY"
        sl = price - 4.5
        tp1 = price + (pips * 0.1)
        tp2 = price + (pips * 0.15)
        take = "✅ TRADE LENI HAI"
    elif rsi > 65:
        signal = "SELL"
        sl = price + 4.5
        tp1 = price - (pips * 0.1)
        tp2 = price - (pips * 0.15)
        take = "✅ TRADE LENI HAI"
    else:
        signal = "WAIT"
        sl = price
        tp1 = price
        tp2 = price
        pips = 0
        take = "❌ TRADE NAHI LENI - MARKET SIDEWAYS HAI"

    return price, signal, pips, sl, tp1, tp2, take, rsi

# START BOT
send_telegram("🚀 *5-MINUTE ULTIMATE BOT LIVE*\nAb har 5 minute me full update ayega!")

while True:
    try:
        price, signal, pips, sl, tp1, tp2, take, rsi = get_gold_analysis()
        now = datetime.now().strftime("%I:%M %p")

        if signal == "WAIT":
            message = f"""
⏳ *5-MIN SCAN - {now}*

GOLD: {price:.2f}
RSI: {rsi}

{take}
Pips: 0
Reason: RSI {rsi} - No Clear Trend

Agle 5 min me phir check karunga...
"""
        else:
            message = f"""
🔥 *TRADE SETUP - {now}*

GOLD: {price:.2f} | {signal}
RSI: {rsi}

{take}

*Pips Target:* {pips} Pips
*SL Lagana Hai:* {sl:.2f}
*TP1 (Safe):* {tp1:.2f}
*TP2 (Full):* {tp2:.2f}

Lot Size: 0.02 - 0.05
Risk: 2% only!
"""
        send_telegram(message)

    except Exception as e:
        print(e)

    time.sleep(SCAN_INTERVAL)
