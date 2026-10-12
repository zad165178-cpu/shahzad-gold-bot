import os
from flask import Flask
import threading
import telebot
import time
import yfinance as yf

BOT_TOKEN = os.environ.get("BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")
CHAT_ID = os.environ.get("CHAT_ID", "PASTE_YOUR_CHAT_ID_HERE")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Shahzad Gold Bot Live - 5 Min Active"

def get_price():
    try:
        data = yf.download("GC=F", period="1d", interval="5m", progress=False)
        price = float(data['Close'].iloc[-1])
        return round(price, 2)
    except:
        return 3950.00

def bot_loop():
    while True:
        try:
            price = get_price()
            sl_buy = round(price - 10, 2)
            tp1_buy = round(price + 8, 2)
            tp2_buy = round(price + 15, 2)
            
            sl_sell = round(price + 10, 2)
            tp1_sell = round(price - 8, 2)
            tp2_sell = round(price - 15, 2)

            msg = f"""🏆 GOLD 5-MIN SCAN

💰 Price: {price}

🔥 BUY:
SL: {sl_buy}
TP1: {tp1_buy} | TP2: {tp2_buy}

🔻 SELL:
SL: {sl_sell}
TP1: {tp1_sell} | TP2: {tp2_sell}

24H ACTIVE - Every 5 Min"""
            bot.send_message(CHAT_ID, msg)
        except Exception as e:
            print(f"Loop Error: {e}")
        time.sleep(300)

if __name__ == "__main__":
    threading.Thread(target=bot_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
