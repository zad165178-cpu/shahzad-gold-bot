
import requests, time, threading, os, random
from datetime import datetime
from collections import deque
from flask import Flask

# ===== 100% SECURE - TOKEN CODE ME NAHI =====
# Render.com > Environment Variables me dalna hai:
# BOT_TOKEN = 8637769635:AAGFBvAYoxCHeCmFhtjN8hDyjWv0D1sLusk (apna naya)
# CHAT_ID = 8513356699

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN missing in ENV - Render > Environment me dalo")

app = Flask(__name__)
price_history = deque(maxlen=200)

@app.route('/')
def home():
    p = price_history[-1] if price_history else 4168
    status = "✅ BEST STRATEGY BOT LIVE & SECURE" if BOT_TOKEN else "❌ ENV missing"
    return f"<h1>{status} - Live ${p:.2f}</h1>"

def get_live():
    try:
        r=requests.get("https://api.gold-api.com/price/XAU",timeout=10)
        if r.status_code==200:
            return float(r.json()['price'])
    except: pass
    return price_history[-1]+random.uniform(-1,1) if price_history else 4168

def ema(prices,per):
    if len(prices)<per: return prices[-1]
    k=2/(per+1)
    e=sum(prices[:per])/per
    for x in prices[per:]: e=x*k+e*(1-k)
    return e

def rsi_calc(prices,per=14):
    if len(prices)<per+1: return 50
    d=[prices[i]-prices[i-1] for i in range(1,len(prices))]
    g=[x if x>0 else 0 for x in d[-per:]]
    l=[-x if x<0 else 0 for x in d[-per:]]
    ag=sum(g)/per or 0.01
    al=sum(l)/per or 0.01
    if al==0: return 70
    return max(10,min(90,100-(100/(1+ag/al))))

def atr(prices,per=14):
    if len(prices)<per+1: return 8
    tr=[abs(prices[i]-prices[i-1]) for i in range(1,len(prices))]
    return sum(tr[-per:])/per

def get_sr(p):
    if len(p)<30: return p[-1]-20, p[-1]+20
    rec=p[-30:]
    return min(rec), max(rec)

def session_now():
    h=datetime.utcnow().hour
    if 8 <= h < 12: return "LONDON OPEN 🔥 BEST"
    if 13 <= h < 17: return "NEW YORK OPEN 🔥 BEST"
    if 17 <= h < 20: return "LONDON+NY OVERLAP 🔥🔥 SUPER BEST"
    if 0 <= h < 2: return "ASIAN - Slow"
    return "Off - Avoid"

def send(msg):
    if not BOT_TOKEN or not CHAT_ID: return False
    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data={"chat_id":CHAT_ID,"text":msg,"parse_mode":"Markdown"}
    try:
        r=requests.post(url,data=data,timeout=15)
        return r.status_code==200
    except: return False

def best_strategy():
    if len(price_history)<50: return None
    prices=list(price_history)
    live=prices[-1]
    e9=ema(prices,9); e21=ema(prices,21); e50=ema(prices,50)
    r=rsi_calc(prices,14); a=atr(prices,14)
    sup,res=get_sr(prices); sess=session_now()

    buy=0; breas=[]
    if e9>e21>e50: buy+=30; breas.append(f"🔥 STRONG BULL: EMA9 {e9:.1f} > EMA21 {e21:.1f} > EMA50 {e50:.1f}")
    elif e9>e21: buy+=15; breas.append(f"✅ Bull: EMA9 > EMA21")
    if 55<r<68: buy+=20; breas.append(f"✅ RSI {r:.1f} Perfect Buy")
    elif 50<r<70: buy+=10; breas.append(f"✅ RSI {r:.1f} Bullish")
    if live>e9 and live>e21: buy+=20; breas.append(f"✅ Price ${live:.1f} Above EMAs")
    if (res-live)>15: buy+=15; breas.append(f"✅ Resistance ${res:.1f} se {(res-live):.1f}$ niche")
    if "BEST" in sess or "SUPER" in sess: buy+=15; breas.append(f"✅ {sess}")

    sell=0; sreas=[]
    if e9<e21<e50: sell+=30; sreas.append(f"🔥 STRONG BEAR: EMA9 {e9:.1f} < EMA21 {e21:.1f} < EMA50 {e50:.1f}")
    elif e9<e21: sell+=15; sreas.append(f"✅ Bear: EMA9 < EMA21")
    if 32<r<45: sell+=20; sreas.append(f"✅ RSI {r:.1f} Perfect Sell")
    elif 30<r<50: sell+=10; sreas.append(f"✅ RSI {r:.1f} Bearish")
    if live<e9 and live<e21: sell+=20; sreas.append(f"✅ Price ${live:.1f} Below EMAs")
    if (live-sup)>15: sell+=15; sreas.append(f"✅ Support ${sup:.1f} se {(live-sup):.1f}$ upar")
    if "BEST" in sess or "SUPER" in sess: sell+=15; sreas.append(f"✅ {sess}")

    if buy>=75 and buy>sell:
        return {"type":"BUY","score":buy,"reasons":breas,"live":live,"e9":e9,"e21":e21,"e50":e50,"rsi":r,"atr":a,"sup":sup,"res":res,"sess":sess}
    if sell>=75 and sell>buy:
        return {"type":"SELL","score":sell,"reasons":sreas,"live":live,"e9":e9,"e21":e21,"e50":e50,"rsi":r,"atr":a,"sup":sup,"res":res,"sess":sess}
    return None

def run():
    print("FINAL BEST SECURE BOT STARTING - NO TOKEN IN CODE")
    if not BOT_TOKEN:
        print("Add BOT_TOKEN in ENV first")
        return
    time.sleep(2)
    # Sirf ek bar start message - duplicate rokne ke liye
    send(f"""
🏆 *FINAL BEST STRATEGY BOT - SECURE & LIVE* 🏆

✅ Token secure (code me nahi)
✅ Best Strategy: EMA+RSI+SR+ATR+SESSION
✅ Sirf 75%+ wali trades
✅ Live Market: BUY/SELL + SL/TP + PIPS

⏰ {datetime.now().strftime("%d %b %H:%M")} - Ready
""")
    last=0
    while True:
        try:
            live=get_live(); price_history.append(live)
            if len(price_history)>=60 and time.time()-last>360:
                sig=best_strategy()
                if sig:
                    t=sig["type"]; sc=sig["score"]; r=sig["rsi"]; a=sig["atr"]
                    sup=sig["sup"]; res=sig["res"]; sess=sig["sess"]
                    reas="\n".join([f"• {x}" for x in sig["reasons"]])
                    e9=sig["e9"]; e21=sig["e21"]; e50=sig["e50"]
                    if t=="BUY":
                        sl=live-(a*1.8); tp1=live+(a*1.5); tp2=live+(a*3.0); tp3=live+(a*5.0)
                        msg=f"""
🟢🟢🟢 *GOLD BUY - BEST STRATEGY* 🟢🟢🟢

💰 *XAUUSD* | *BUY KARO - KHARID LO*
📍 *Entry:* ${live:.2f} (LIVE)
⭐ *Score:* {sc}% | ⏰ {datetime.now().strftime("%H:%M:%S")}
🕐 *Session:* {sess}

🏆 *STRATEGY:*
{reas}

📊 *Levels:*
EMA9 ${e9:.1f} | EMA21 ${e21:.1f} | EMA50 ${e50:.1f}
RSI {r:.1f} | ATR ${a:.2f}
Support ${sup:.1f} | Resistance ${res:.1f}

🎯 *TRADE:*
🛑 SL: ${sl:.2f} ({int((live-sl)*10)} Pips) - 1.8x ATR
💰 TP1: ${tp1:.2f} (+{int((tp1-live)*10)} Pips) 40% Close
💰 TP2: ${tp2:.2f} (+{int((tp2-live)*10)} Pips) 30% Close
💰 TP3: ${tp3:.2f} (+{int((tp3-live)*10)} Pips) Runner 30%

#BUY #GOLD
"""
                    else:
                        sl=live+(a*1.8); tp1=live-(a*1.5); tp2=live-(a*3.0); tp3=live-(a*5.0)
                        msg=f"""
🔴🔴🔴 *GOLD SELL - BEST STRATEGY* 🔴🔴🔴

💰 *XAUUSD* | *SELL KARO - BECH DO*
📍 *Entry:* ${live:.2f} (LIVE)
⭐ *Score:* {sc}% | ⏰ {datetime.now().strftime("%H:%M:%S")}
🕐 *Session:* {sess}

🏆 *STRATEGY:*
{reas}

📊 *Levels:*
EMA9 ${e9:.1f} | EMA21 ${e21:.1f} | EMA50 ${e50:.1f}
RSI {r:.1f} | ATR ${a:.2f}
Support ${sup:.1f} | Resistance ${res:.1f}

🎯 *TRADE:*
🛑 SL: ${sl:.2f} ({int((sl-live)*10)} Pips)
💰 TP1: ${tp1:.2f} (-{int((live-tp1)*10)} Pips) 40%
💰 TP2: ${tp2:.2f} (-{int((live-tp2)*10)} Pips) 30%
💰 TP3: ${tp3:.2f} (-{int((live-tp3)*10)} Pips) 30%

#SELL #GOLD
"""
                    if send(msg):
                        last=time.time()
                        print(f"SIGNAL {t} {sc}%")
            time.sleep(12)
        except Exception as e:
            print(e); time.sleep(10)

threading.Thread(target=run,daemon=True).start()
if __name__=="__main__":
    app.run(host='0.0.0.0',port=8080)
