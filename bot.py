import os, time, threading, json, urllib.request, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# ===== تمہارا ٹوکن اور ID اندر لگا ہوا ہے =====
BOT_TOKEN = os.environ.get("BOT_TOKEN", "APNA_TOKEN_YAHAN_DAAL_DO_AGAR_ENV_ME_NAHI_HAI")
CHAT_ID = os.environ.get("CHAT_ID", "8513356699")
# =============================================

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Shahzad GOLD Bot LIVE - 5 Min Scan")

def run_web():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": msg}).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10)
        print("Sent:", msg[:30])
    except Exception as e:
        print("Send Fail:", e)

def get_price():
    try:
        req = urllib.request.Request("https://api.gold-api.com/price/XAU", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            return float(json.loads(r.read().decode())['price'])
    except:
        return 4325.50

# Bot start message
time.sleep(5)
send("✅ Shahzad Bhai Bot LIVE ho gaya - Har 5 Min me GOLD Signal ayega")

while True:
    try:
        price = get_price()
        msg = f"""🏆 GOLD 5-MIN SCAN

💰 Price: {price}

BUY SETUP:
SL: {price-8:.2f}
TP1: {price+7:.2f}
TP2: {price+14:.2f}

SELL SETUP:
SL: {price+8:.2f}
TP1: {price-7:.2f}
TP2: {price-14:.2f}

Status: Active - {time.strftime('%H:%M:%S') }"""
        send(msg)
    except Exception as e:
        print(e)
    time.sleep(300) # 5 minute
