import requests
import time
import pandas as pd
import numpy as np
from datetime import datetime

# ========== اپنی Details یہاں ڈالو ==========
TELEGRAM_TOKEN = "7123456789:AAH_YOUR_TOKEN_HERE"  # BotFather والا ٹوکن
CHAT_ID = "123456789"  # آپ کی Chat ID
SYMBOL = "XAUUSD"
# ===========================================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
        print("Telegram پر بھیج دیا!")
    except Exception as e:
        print(f"Error: {e}")

def get_gold_data():
    # Gold کا Live Data yfinance سے (موبائل پر آسانی سے چلتا ہے)
    try:
        # yfinance نہ ہو تو simple API use کریں
        url = "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=15m&limit=100"
        # PAXG = Gold
        r = requests.get(url).json()
        df = pd.DataFrame(r, columns=['time','open','high','low','close','vol','a','b','c','d','e','f'])
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        return df
    except:
        return None

def full_analysis(df):
    df['support'] = df['low'].rolling(20).min()
    df['resistance'] = df['high'].rolling(20).max()
    df['ema50'] = df['close'].ewm(span=50).mean()
    df['ema200'] = df['close'].ewm(span=200).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + gain/loss))
    
    last = df.iloc[-1]
    
    signal = "HOLD"
    sl = 0
    tp = 0
    
    # آپ کے اصول
    uptrend = last['ema50'] > last['ema200']
    downtrend = last['ema50'] < last['ema200']
    
    if uptrend and last['close'] <= last['support']*1.01 and 35 < last['rsi'] < 60:
        signal = "BUY 🟢"
        sl = last['support'] * 0.997
        tp = last['close'] + (last['close'] - sl) * 2.0
        
    elif downtrend and last['close'] >= last['resistance']*0.99 and 40 < last['rsi'] < 70:
        signal = "SELL 🔴"
        sl = last['resistance'] * 1.003
        tp = last['close'] - (sl - last['close']) * 2.0

    return last, signal, sl, tp

def mobile_bot_loop():
    send_telegram(f"🤖 *Shahzad Gold Bot Started*\nSymbol: {SYMBOL}\nMobile پر Live ہے ✅")
    
    last_signal = ""
    while True:
        try:
            df = get_gold_data()
            if df is None:
                time.sleep(30)
                continue
                
            last, signal, sl, tp = full_analysis(df)
            
            print(f"{datetime.now()} | Price: {last['close']} | Signal: {signal}")
            
            # صرف نیا سگنل آنے پر ٹیلی گرام پر بھیجے گا
            if signal != "HOLD" and signal != last_signal:
                msg = f"""
🚨 *GOLD SIGNAL - {signal}* 🚨

*Symbol:* {SYMBOL} (Exness Gold)
*Price:* {last['close']}
*Time:* {datetime.now().strftime('%H:%M:%S')}

📊 *Analysis:*
- Support: {last['support']:.2f}
- Resistance: {last['resistance']:.2f}
- Trend: {'UPTREND ⬆️' if last['ema50'] > last['ema200'] else 'DOWNTREND ⬇️'}
- RSI: {last['rsi']:.1f}

🎯 *Trading Plan:*
- Entry: {last['close']:.2f}
- Stop Loss: {sl:.2f}
- Target: {tp:.2f}
- Risk: 2% | RR: 1:2

⚠️ Mobile Bot سے بھیجا گیا
"""
                send_telegram(msg)
                last_signal = signal
            
            time.sleep(60) # ہر 1 منٹ چیک کرے گا
            
        except Exception as e:
            print(f"Error in loop: {e}")
            time.sleep(10)

# بوٹ اسٹارٹ
if __name__ == "__main__":
    mobile_bot_loop()
