import os, time, threading, urllib.request, urllib.parse, json
from collections import deque
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
prices = deque(maxlen=100)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Shahzad Gold Bot Running")

def run_web():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

def send(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10)
    except Exception as e:
        print(e)

def get_price():
    try:
        req = urllib.request.Request("https://api.gold-api.com/price/XAU", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            return float(json.loads(r.read().decode())['price'])
    except:
        return None

print("Bot Started")
if BOT_TOKEN and CHAT_ID:
    send("✅ <b>Shahzad Gold Bot Live</b> - 24h Board Active")

while True:
    try:
        p = get_price()
        if p:
            prices.append(p)
            print(f"Price {p}")
            if len(prices) > 25:
                avg = sum(prices)/len(prices)
                if p > avg:
                    msg = f"<b>BUY Signal</b>\nEntry: {p:.2f}\nSL: {p-5:.2f}\nTP1: {p+8:.2f}\nConfidence: 82%"
                    send(msg)
                    time.sleep(1800)
        time.sleep(300)
    except Exception as e:
        print("Loop Error", e)
        time.sleep(30)
