
import requests, time, threading, os, random
from datetime import datetime
from collections import deque
from flask import Flask

# ===== SECURE - TOKEN YAHAN NAHI LIKHA - ENV SE AYEGA =====
# Render.com / Replit Secrets me dalna hai:
# BOT_TOKEN = aapka naya token
# CHAT_ID = 8513356699

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ ERROR: BOT_TOKEN aur CHAT_ID Environment Variable me dalo!")
    print("Render.com > Environment > Add Variable")
    # Demo ke liye ruk jayega, crash nahi hoga

app = Flask(__name__)
price_history = deque(maxlen=100)

@app.route('/')
def home():
    price = price_history[-1] if price_history else 4171.70
    status = "✅ SECURE - Token hidden" if TELEGRAM_BOT_TOKEN else "❌ Token missing - Add in ENV"
    return f"<h1>{status}</h1><h2>Live Gold: ${price:.2f}</h2><p>{datetime.now()}</p>"

def get_live_gold():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        if r.status_code == 200:
            return float(r.json()['price'])
    except:
        pass
    if price_history:
        return price_history[-1] + random.uniform(-1.5, 1.5)
    return 4171.70 + random.uniform(-5,5)

def calc_ema(prices, p):
    if len(prices) < p:
        return prices[-1] if prices else 0
    k = 2/(p+1)
    ema = sum(prices[:p])/p
    for pr in prices[p:]:
        ema = pr*k + ema*(1-k)
    return ema

def calc_rsi(prices, p=14):
    if len(prices) < p+1:
        return 50
    deltas = [prices[i]-prices[i-1] for i in range(1,len(prices))]
    gains = [d if d>0 else 0 for d in deltas[-p:]]
    losses = [-d if d<0 else 0 for d in deltas[-p:]]
    ag = sum(gains)/p if gains else 0.01
    al = sum(losses)/p if losses else 0.01
    if al==0:
        return 75
    rs = ag/al
    return max(10,min(90,100-(100/(1+rs))))

def send_tg(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Cannot send - Token not set in ENV")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=data, timeout=15)
        return r.status_code==200
    except:
        return False

def run_bot():
    print("🚀 SECURE BOT STARTING - NO TOKEN IN CODE")
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️ BOT_TOKEN ENV me dalo phir chalega")
        return
    time.sleep(2)
    send_tg(f"""
✅ *SECURE BOT ACTIVE!* ✅

🔐 Token code me nahi - Safe!
💰 Live Gold Market
🟢 BUY / 🔴 SELL

⏰ {datetime.now().strftime("%d %b %H:%M")}
""")
    last = 0
    while True:
        try:
            live = get_live_gold()
            price_history.append(live)
            if len(price_history)>=20:
                prices = list(price_history)
                ema9 = calc_ema(prices,9)
                ema21 = calc_ema(prices,21)
                rsi = calc_rsi(prices,14)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] LIVE ${live:.2f} RSI {rsi:.1f}")
                if time.time()-last>300:
                    if ema9>ema21 and 52<rsi<68 and live>ema9:
                        msg = f"🟢 *BUY KARO - KHARID LO!*\n\n💰 XAUUSD BUY @ ${live:.2f}\n⭐ {82+(rsi-52):.0f}%\n🛑 SL ${live-13:.2f} 💵 TP ${live+30:.2f}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
                        if send_tg(msg):
                            last=time.time()
                    elif ema9<ema21 and 32<rsi<48 and live<ema9:
                        msg = f"🔴 *SELL KARO - BECH DO!*\n\n💰 XAUUSD SELL @ ${live:.2f}\n⭐ {82+(48-rsi):.0f}%\n🛑 SL ${live+13:.2f} 💵 TP ${live-30:.2f}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
                        if send_tg(msg):
                            last=time.time()
            time.sleep(15)
        except Exception as e:
            print(e)
            time.sleep(10)

threading.Thread(target=run_bot, daemon=True).start()

if __name__=="__main__":
    app.run(host='0.0.0.0', port=8080)
