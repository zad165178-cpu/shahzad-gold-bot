from flask import Flask
import threading
import telebot
import time
import yfinance as yf

# ====== اپنا ڈیٹا یہاں ڈالو ======
BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"
CHAT_ID = "PASTE_YOUR_CHAT_ID_HERE"
# =================================

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Shahzad Gold Bot is Live - 5 Min Scan Active"

def get_gold_analysis():
    try:
        data = yf.download("GC=F", period="1d", interval="5m")
        current_price = round(float(data['Close'].iloc[-1]), 2)
        
        # سادہ SL/TP لاجک
        sl_buy = round(current_price - 10, 2)
        tp1_buy = round(current_price + 8, 2)
        tp2_buy = round(current_price + 15, 2)
        
        sl_sell = round(current_price + 10, 2)
        tp1_sell = round(current_price - 8, 2)
        tp2_sell = round(current_price - 15, 2)

        msg = f"""🏆 GOLD 5-MIN SCAN - SHAHZAD BOT

💰 Current Price: {current_price}

🔥 BUY SETUP:
SL Lagana Hai: {sl_buy}
TP1: {tp1_buy}
TP2: {tp2_buy}
Pips: 80 / 150

🔻 SELL SETUP:
SL Lagana Hai: {sl_sell}
TP1: {tp1_sell}
TP2: {tp2_sell}
Pips: 80 / 150

✅ Status: 24H SCAN ACTIVE (Every 5 Min)
"""
        return msg
    except Exception as e:
        return f"Error: {e}"

def start_bot_loop():
    while True:
        try:
            analysis = get_gold_analysis()
            bot.send_message(CHAT_ID, analysis)
        except Exception as e:
            print(f"Error in loop: {e}")
        time.sleep(300)  # 300 = 5 منٹ

# Flask کو الگ Thread میں چلانا تاکہ Render Timed Out نہ دے
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
# بوٹ کا لوپ الگ Thread میں
threading.Thread(target=start_bot_loop).start()

if __name__ == "__main__":
    bot.infinity_polling()
