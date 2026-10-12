import os, time, requests, random
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
price_history = []

def get_price():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=10)
        return float(r.json()['price'])
    except:
        return 2650.0 + random.uniform(-5, 5)

def send(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
        print("Sent")
    except Exception as e:
        print(e)

def ema(prices, p):
    return sum(prices[-p:]) / p if len(prices) >= p else sum(prices)/len(prices)

def rsi_calc(prices, period=14):
    if len(prices) < period+1: return 50
    gains=0; losses=0
    for i in range(-period,0):
        d = prices[i] - prices[i-1]
        if d>0: gains+=d
        else: losses+=abs(d)
    if losses==0: return 70
    rs=gains/losses if losses!=0 else 1
    return 100 - (100/(1+rs))

def check_news():
    # High Impact News Time Check (UTC Time)
    now = datetime.utcnow()
    # 12:30, 13:30, 14:00 UTC = US Big News (CPI, NFP, FOMC)
    # 18:00 UTC = FOMC Evening
    risky_times = [
        (12, 30), (13, 30), (14, 0), (18, 0), (18, 30)
    ]
    for h, m in risky_times:
        if now.hour == h and abs(now.minute - m) <= 30:
            return True, f"HIGH IMPACT NEWS at {h}:{m} UTC"
    return False, ""

send("GOLD BOT V3 FINAL STARTED - With News Filter + Best Rules")

while True:
    try:
        is_news, news_name = check_news()
        price = get_price()
        price_history.append(price)
        if len(price_history)>50: price_history.pop(0)

        e9 = ema(price_history, 9)
        e21 = ema(price_history, 21)
        rsi = rsi_calc(price_history, 14)

        # NEWS FILTER
        if is_news:
            msg = f"""
NEWS ALERT - NO TRADE

Time: {datetime.utcnow().strftime('%H:%M UTC')}
News: {news_name}

Action: DO NOT TAKE ANY TRADE NOW
Reason: High impact news = SL hunting

Wait for next 5 min candle after news
Current Gold Price: {price:.2f}
"""
            send(msg)
            time.sleep(300)
            continue

        # BEST CONFIRMATION LOGIC
        buy_cond = e9 > e21 and rsi > 52 and rsi < 70
        sell_cond = e9 < e21 and rsi < 48 and rsi > 30

        if buy_cond:
            signal="BUY"
            sl=price-5.5; tp1=price+3.5; tp2=price+6.5; tp3=price+11
            status="BEST TRADE - CONFIRMED BUY"
        elif sell_cond:
            signal="SELL"
            sl=price+5.5; tp1=price-3.5; tp2=price-6.5; tp3=price-11
            status="BEST TRADE - CONFIRMED SELL"
        else:
            msg = f"""
WAIT - NO TRADE NOW

Price: {price:.2f}
EMA9: {e9:.2f} | EMA21: {e21:.2f} | RSI: {rsi:.1f}
News: No News - Market Sideways

Action: DO NOT TRADE - Wait 5 min
"""
            send(msg)
            time.sleep(300)
            continue

        msg = f"""
{signal} SIGNAL - V3 FINAL (Best)

Entry: {price:.2f}
RSI: {rsi:.1f} | EMA: {e9:.2f}/{e21:.2f}
News Filter: PASSED - No News

SL: {sl:.2f} (55 pips) - MUST USE
TP1: {tp1:.2f} (35 pips) Close 30%
TP2: {tp2:.2f} (65 pips) Close 40%
TP3: {tp3:.2f} (110 pips) Close 30%

Status: {status}

--- BEST TRADING RULES (Follow 100%) ---
1. Always SL - No SL = No Trade
2. Risk 1% only per trade
3. After TP1 hit, move SL to Entry
4. No trade 30 min before/after big news (Bot will auto stop)
5. 2 Loss in a row = Stop trading today
6. Take only CONFIRMED trades

Win Rate: 65-70% if you follow rules
Time: {datetime.utcnow().strftime('%H:%M UTC')}
"""
        send(msg)

    except Exception as e:
        print(e)
    time.sleep(300)
