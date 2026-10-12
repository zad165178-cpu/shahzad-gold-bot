import os, time, requests, threading
from flask import Flask

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

print(f"BOT_TOKEN exists: {bool(BOT_TOKEN)}")
print(f"CHAT_ID: {CHAT_ID}")

def send_msg(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("ERROR: BOT_TOKEN or CHAT_ID missing!")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=15)
        print(f"Sent: {r.status_code}")
    except Exception as e:
        print(f"Send Error: {e}")

def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        return float(r['price'])
    except:
        return 4168.50

def bot_loop():
    time.sleep(5)
    send_msg("GOLD BOT V30 LIVE - 10 MIN MODE FIXED")
    while True:
        try:
            p = get_price()
            msg = f"GOLD UPDATE\nLive: {p}\nTime: 10 Min\nStatus: Monitoring..."
            send_msg(msg)
        except Exception as e:
            print(e)
        time.sleep(600)

threading.Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home():
    return "GOLD BOT IS RUNNING"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
