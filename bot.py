import os, time, threading, urllib.request, urllib.parse, json
from collections import deque
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
prices = deque(maxlen=100)

# Render Live ke liye
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Shahzad GOLD PRO Bot Running 24/7")

def run_web():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

def send(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15)
    except Exception as e:
        print("Send Error:", e)

def get_price():
    try:
        req = urllib.request.Request("https://api.gold-api.com/price/XAU", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            return float(json.loads(r.read().decode())['price'])
    except:
        return None

def calc_rsi(prices_list, period=14):
    if len(prices_list) < period + 1:
        return 50
    gains = 0
    losses = 0
    for i in range(1, period+1):
        ch = prices_list[-i] - prices_list[-i-1]
        if ch > 0:
            gains += ch
        else:
            losses += abs(ch)
    if losses == 0:
        return 75
    rs = gains / losses
    return 100 - (100 / (1 + rs))

def calc_ema(prices_list, period):
    if len(prices_list) < period:
        return None
    k = 2 / (period + 1)
    ema = prices_list[0]
    for p in prices_list[1:]:
        ema = p * k + ema * (1 - k)
    return ema

print("GOLD PRO Bot Started")
if BOT_TOKEN and CHAT_ID:
    send("✅ <b>Shahzad GOLD PRO Board Active</b>\n\n🔥 EMA 9/21 + RSI Filter\n🛑 SL/TP + % Confidence\n⏰ Har 30 min me signal check")

while True:
    try:
        price = get_price()
        if price:
            prices.append(price)
            print(f"Gold: {price}")

            if len(prices) >= 30:
                p_list = list(prices)
                ema9 = calc_ema(p_list[-20:], 9)
                ema21 = calc_ema(p_list[-20:], 21)
                rsi = calc_rsi(p_list, 14)

                signal = None
                confidence = 0

                # BUY Condition: EMA9 > EMA21 and RSI 40-68 (up trend)
                if ema9 and ema21 and ema9 > ema21 and 40 < rsi < 68:
                    signal = "BUY"
                    confidence = 70 + (rsi - 40) * 0.8

                # SELL Condition: EMA9 < EMA21 and RSI 32-60 (down trend)
                elif ema9 and ema21 and ema9 < ema21 and 32 < rsi < 60:
                    signal = "SELL"
                    confidence = 70 + (60 - rsi) * 0.8

                if signal:
                    sl_gap = 4.5
                    tp_gap = 8.5
                    if signal == "BUY":
                        sl = price - sl_gap
                        tp1 = price + tp_gap
                        tp2 = price + (tp_gap * 1.9)
                    else:
                        sl = price + sl_gap
                        tp1 = price - tp_gap
                        tp2 = price - (tp_gap * 1.9)

                    conf = int(min(92, max(65, confidence)))

                    msg = f"""<b>🔥 GOLD PRO SIGNAL 🔥</b>

<b>Action:</b> {signal} XAUUSD
<b>Entry:</b> {price:.2f}

<b>🛑 SL:</b> {sl:.2f}
<b>🎯 TP1:</b> {tp1:.2f}
<b>🎯 TP2:</b> {tp2:.2f}

<b>📊 Confidence:</b> {conf}%
<b>📈 RSI:</b> {rsi:.1f}
<b>📉 EMA 9/21:</b> {ema9:.2f} / {ema21:.2f}

<i>Risk: 0.01 lot only</i>"""

                    send(msg)
                    # Ek signal ke baad 30 min wait
                    time.sleep(1800)

        time.sleep(300) # Har 5 min price check

    except Exception as e:
        print("Loop Error:", e)
        time.sleep(30)
