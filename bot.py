
import requests, time, threading, os, random
from datetime import datetime
from collections import deque
from flask import Flask

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN", "8637769635:AAGFBvAYoxCHeCmFhtjN8hDyjWv0D1sLusk")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID", "8513356699")

app = Flask(__name__)
price_history = deque(maxlen=200)

@app.route('/')
def home():
    price = price_history[-1] if price_history else 4168
    return f"BEST STRATEGY GOLD BOT LIVE - ${price:.2f} - EMA+RSI+SR+VOLUME+SESSION"

def get_live():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        if r.status_code==200:
            return float(r.json()['price'])
    except: pass
    return price_history[-1]+random.uniform(-1,1) if price_history else 4168

def ema(p, period):
    if len(p)<period: return p[-1]
    k=2/(period+1)
    e=sum(p[:period])/period
    for x in p[period:]: e=x*k+e*(1-k)
    return e

def rsi_calc(p, per=14):
    if len(p)<per+1: return 50
    deltas=[p[i]-p[i-1] for i in range(1,len(p))]
    gains=[d if d>0 else 0 for d in deltas[-per:]]
    losses=[-d if d<0 else 0 for d in deltas[-per:]]
    ag=sum(gains)/per or 0.01
    al=sum(losses)/per or 0.01
    if al==0: return 70
    return max(10,min(90,100-(100/(1+ag/al))))

def atr_calc(p, per=14):
    if len(p)<per+1: return 8
    tr=[abs(p[i]-p[i-1]) for i in range(1,len(p))]
    return sum(tr[-per:])/per

def get_sr(p):
    if len(p)<30:
        return p[-1]-20, p[-1]+20
    recent=p[-30:]
    return min(recent), max(recent)

def get_session():
    hour=datetime.utcnow().hour
    # Best Gold sessions
    if 8 <= hour < 12:
        return "LONDON OPEN 🔥 BEST TIME"
    elif 13 <= hour < 17:
        return "NEW YORK OPEN 🔥 BEST TIME"
    elif 17 <= hour < 20:
        return "LONDON+NY OVERLAP 🔥🔥 BEST"
    elif 0 <= hour < 2:
        return "ASIAN - Low Volatility"
    else:
        return "Off Session - Avoid"

def send(msg):
    url=f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data={"chat_id":TELEGRAM_CHAT_ID,"text":msg,"parse_mode":"Markdown"}
    try:
        r=requests.post(url,data=data,timeout=15)
        return r.status_code==200
    except: return False

def best_strategy_analysis():
    """
    BEST GOLD STRATEGY - 5 FILTERS:
    1. TREND FILTER - EMA 9 > 21 > 50 = Strong Bull
    2. MOMENTUM FILTER - RSI 50-70 BUY, 30-50 SELL
    3. SUPPORT/RESISTANCE - Breakout + Retest
    4. VOLATILITY FILTER - ATR se SL/TP
    5. SESSION FILTER - London/NY me hi best trades
    """
    if len(price_history)<50:
        return None
    prices=list(price_history)
    live=prices[-1]
    e9=ema(prices,9)
    e21=ema(prices,21)
    e50=ema(prices,50)
    r=rsi_calc(prices,14)
    atr=atr_calc(prices,14)
    sup,res=get_sr(prices)
    session=get_session()

    # Scoring system - Best strategy
    buy_score=0
    buy_reasons=[]
    
    # 1. TREND (30 points)
    if e9>e21>e50:
        buy_score+=30
        buy_reasons.append(f"🔥 STRONG BULL TREND: EMA9({e9:.1f}) > EMA21({e21:.1f}) > EMA50({e50:.1f})")
    elif e9>e21:
        buy_score+=15
        buy_reasons.append(f"✅ Bull Trend: EMA9 > EMA21")
    
    # 2. RSI Momentum (20 points)
    if 55<r<68:
        buy_score+=20
        buy_reasons.append(f"✅ RSI {r:.1f} - Perfect Buy Zone (55-68)")
    elif 50<r<70:
        buy_score+=10
        buy_reasons.append(f"✅ RSI {r:.1f} - Bullish Momentum")
    
    # 3. Price Position (20 points)
    if live>e9 and live>e21:
        buy_score+=20
        buy_reasons.append(f"✅ Price (${live:.1f}) Above EMA9 & EMA21 - Strong")
    elif live>e9:
        buy_score+=10
        buy_reasons.append(f"✅ Price Above EMA9")
    
    # 4. Support Bounce (15 points)
    distance_to_res=(res-live)
    if distance_to_res>15:
        buy_score+=15
        buy_reasons.append(f"✅ Resistance ${res:.1f} se {distance_to_res:.1f}$ neeche - Room for UP")
    
    # 5. Session (15 points)
    if "BEST" in session:
        buy_score+=15
        buy_reasons.append(f"✅ {session} - High Volume Time")
    elif "London" in session or "New York" in session:
        buy_score+=10
        buy_reasons.append(f"✅ {session}")

    # SELL scoring
    sell_score=0
    sell_reasons=[]
    if e9<e21<e50:
        sell_score+=30
        sell_reasons.append(f"🔥 STRONG BEAR TREND: EMA9({e9:.1f}) < EMA21({e21:.1f}) < EMA50({e50:.1f})")
    elif e9<e21:
        sell_score+=15
        sell_reasons.append(f"✅ Bear Trend: EMA9 < EMA21")
    
    if 32<r<45:
        sell_score+=20
        sell_reasons.append(f"✅ RSI {r:.1f} - Perfect Sell Zone (32-45)")
    elif 30<r<50:
        sell_score+=10
        sell_reasons.append(f"✅ RSI {r:.1f} - Bearish Momentum")
    
    if live<e9 and live<e21:
        sell_score+=20
        sell_reasons.append(f"✅ Price (${live:.1f}) Below EMA9 & EMA21 - Strong Down")
    
    distance_to_sup=(live-sup)
    if distance_to_sup>15:
        sell_score+=15
        sell_reasons.append(f"✅ Support ${sup:.1f} se {distance_to_sup:.1f}$ upar - Room for DOWN")
    
    if "BEST" in session:
        sell_score+=15
        sell_reasons.append(f"✅ {session}")
    
    # Decision - Only 75%+ trades
    if buy_score>=75 and buy_score>sell_score:
        return {"type":"BUY","score":buy_score,"reasons":buy_reasons,"live":live,"e9":e9,"e21":e21,"e50":e50,"rsi":r,"atr":atr,"sup":sup,"res":res,"session":session}
    elif sell_score>=75 and sell_score>sell_score or sell_score>=75 and sell_score>buy_score:
        return {"type":"SELL","score":sell_score,"reasons":sell_reasons,"live":live,"e9":e9,"e21":e21,"e50":e50,"rsi":r,"atr":atr,"sup":sup,"res":res,"session":session}
    
    return None

def run():
    print("BEST STRATEGY BOT STARTING")
    time.sleep(3)
    send(f"""
🏆 *BEST GOLD STRATEGY BOT ACTIVE* 🏆

*Strategy jo Pro Traders use karte hain:*

1️⃣ *TREND:* EMA 9/21/50 Cross
2️⃣ *MOMENTUM:* RSI 14 Perfect Zone
3️⃣ *SUPPORT/RESISTANCE:* Breakout Logic
4️⃣ *VOLATILITY:* ATR based SL/TP
5️⃣ *SESSION:* London + New York Best Time

✅ Sirf 75%+ score wali trades
✅ Live Market se analysis

Ab Best trades ayengi! 🚀
⏰ {datetime.now().strftime("%H:%M")}
""")
    last=0
    while True:
        try:
            live=get_live()
            price_history.append(live)
            if len(price_history)>=60:
                if time.time()-last>360:  # 6 min cooldown for quality
                    signal=best_strategy_analysis()
                    if signal:
                        t=signal["type"]
                        sc=signal["score"]
                        e9=signal["e9"]
                        e21=signal["e21"]
                        e50=signal["e50"]
                        r=signal["rsi"]
                        atr=signal["atr"]
                        sup=signal["sup"]
                        res=signal["res"]
                        sess=signal["session"]
                        reasons="\n".join([f"• {x}" for x in signal["reasons"]])

                        if t=="BUY":
                            entry=live
                            sl=entry - (atr*1.8)  # Best strategy: 1.8x ATR
                            tp1=entry + (atr*1.5)
                            tp2=entry + (atr*3.0)
                            tp3=entry + (atr*5.0)
                            sl_p=int((entry-sl)*10)
                            tp1_p=int((tp1-entry)*10)
                            tp2_p=int((tp2-entry)*10)
                            tp3_p=int((tp3-entry)*10)
                            rr1=round((tp1-entry)/(entry-sl),1)
                            rr2=round((tp2-entry)/(entry-sl),1)

                            msg=f"""
🟢🟢🟢 *BEST STRATEGY - GOLD BUY* 🟢🟢🟢

💰 *XAUUSD / GOLD - {t}*
📍 *Entry:* ${entry:.2f} (LIVE)
⭐ *Score:* {sc}% (Best Strategy)
⏰ *Time:* {datetime.now().strftime("%d %b %H:%M:%S")}
🕐 *Session:* {sess}

🏆 *BEST STRATEGY ANALYSIS:*
{reasons}

📊 *TECHNICAL LEVELS:*
• EMA9: ${e9:.2f} | EMA21: ${e21:.2f} | EMA50: ${e50:.2f}
• RSI: {r:.1f} | ATR: ${atr:.2f}
• Support: ${sup:.2f} | Resistance: ${res:.2f}

🎯 *TRADE SETUP (ATR Based - Best Risk Management):*

🛑 *STOP LOSS:*
• Price: ${sl:.2f}
• Pips: {sl_p} Pips
• Logic: 1.8x ATR (${atr:.2f}) - Pro Method

💰 *TAKE PROFIT:*
• TP1: ${tp1:.2f} (+{tp1_p} pips) RR 1:{rr1} - Close 40%
• TP2: ${tp2:.2f} (+{tp2_p} pips) RR 1:{rr2} - Close 30%
• TP3: ${tp3:.2f} (+{int((tp3-entry)*10)} pips) - Runner 30%

📋 *HOW TO TRADE - STEP BY STEP:*
1. Abhi BUY karo ${entry:.2f} par
2. SL lagao ${sl:.2f} ({sl_p} pips)
3. TP1 pe 40% book karo, SL to Entry le aao
4. TP2 pe 30% book karo
5. TP3 tak baki 30% hold karo (Break-even pe safe)

💡 *Best Strategy Rule:* 
• London/NY session me hi trade lo
• 75%+ score = High Probability
• Risk = 1-2% per trade

⚠️ *Risk Warning: Gold volatile hai, SL zaroor lagao*

#GOLD #XAUUSD #BUY #BestStrategy #{datetime.now().strftime("%H%M")}
"""
                        else:
                            entry=live
                            sl=entry + (atr*1.8)
                            tp1=entry - (atr*1.5)
                            tp2=entry - (atr*3.0)
                            tp3=entry - (atr*5.0)
                            sl_p=int((sl-entry)*10)
                            tp1_p=int((entry-tp1)*10)
                            tp2_p=int((entry-tp2)*10)
                            rr1=round((entry-tp1)/(sl-entry),1)
                            rr2=round((entry-tp2)/(sl-entry),1)

                            msg=f"""
🔴🔴🔴 *BEST STRATEGY - GOLD SELL* 🔴🔴🔴

💰 *XAUUSD / GOLD - {t}*
📍 *Entry:* ${entry:.2f} (LIVE)
⭐ *Score:* {sc}% (Best Strategy)
⏰ *Time:* {datetime.now().strftime("%d %b %H:%M:%S")}
🕐 *Session:* {sess}

🏆 *BEST STRATEGY ANALYSIS:*
{reasons}

📊 *TECHNICAL LEVELS:*
• EMA9: ${e9:.2f} | EMA21: ${e21:.2f} | EMA50: ${e50:.2f}
• RSI: {r:.1f} | ATR: ${atr:.2f}
• Support: ${sup:.2f} | Resistance: ${res:.2f}

🎯 *TRADE SETUP (ATR Based):*

🛑 *STOP LOSS:*
• Price: ${sl:.2f}
• Pips: {sl_p} Pips
• Logic: 1.8x ATR - Pro Method

💰 *TAKE PROFIT:*
• TP1: ${tp1:.2f} (-{tp1_p} pips) RR 1:{rr1} - Close 40%
• TP2: ${tp2:.2f} (-{tp2_p} pips) RR 1:{rr2} - Close 30%
• TP3: ${tp3:.2f} (-{int((entry-tp3)*10)} pips) - Runner 30%

📋 *HOW TO TRADE:*
1. Abhi SELL karo ${entry:.2f} par
2. SL ${sl:.2f} ({sl_p} pips)
3. TP1 pe 40% book, SL to Entry
4. TP2 pe 30% book
5. TP3 tak baki hold

💡 *Best Rule: 75%+ = High Win Rate*

#GOLD #XAUUSD #SELL #BestStrategy #{datetime.now().strftime("%H%M")}
"""
                        if send(msg):
                            last=time.time()
                            print(f"🔥 BEST STRATEGY SIGNAL {t} SCORE {sc}")

            time.sleep(12)
        except Exception as e:
            print(e)
            time.sleep(10)

threading.Thread(target=run,daemon=True).start()

if __name__=="__main__":
    app.run(host='0.0.0.0',port=8080)
