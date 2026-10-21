
import json
import os
import urllib.request
import urllib.parse
from datetime import datetime, timezone

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
BALANCE = float(os.environ.get("DEMO_BALANCE", "0"))
RISK_PERCENT = 0.5
BASE = "https://xaus.com/api/v1"


def get_json(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": "GoldSignalBot/1.0"}
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode())


def telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": message
    }).encode()
    req = urllib.request.Request(url, data=payload)
    with urllib.request.urlopen(req, timeout=20) as response:
        result = json.loads(response.read().decode())
        if not result.get("ok"):
            raise RuntimeError("Telegram rejected the message")


def live_price():
    data = get_json(BASE + "/spot?compact=1")
    state = data.get("data_state", {})
    price = data.get("spot_usd_oz") or data.get("xau", {}).get("price")

    if not price or state.get("status") != "fresh":
        raise ValueError("Live price is unavailable or stale")

    updated = data.get("updated_at")
    if updated:
        stamp = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - stamp).total_seconds()
        if age < -60 or age > 600:
            raise ValueError("Price timestamp is too old")

    return float(price), updated or "Unknown"


def candles(interval, period):
    query = urllib.parse.urlencode({
        "symbol": "xau",
        "range": period,
        "interval": interval
    })
    data = get_json(BASE + "/chart?" + query)
    points = data.get("points", [])

    rows = []
    for p in points:
        try:
            rows.append({
                "t": int(p["t"]),
                "h": float(p["h"]),
                "l": float(p["l"]),
                "c": float(p["c"])
            })
        except (KeyError, TypeError, ValueError):
            continue

    rows.sort(key=lambda x: x["t"])
    # Do not use a possibly unfinished current candle
    now = datetime.now(timezone.utc).timestamp()
    seconds = 900 if interval == "15m" else 3600
    rows = [r for r in rows if r["t"] + seconds <= now]
    if len(rows) < 55:
        raise ValueError(f"Not enough closed {interval} candles")
    return rows


def ema(values, period):
    alpha = 2 / (period + 1)
    result = sum(values[:period]) / period
    for v in values[period:]:
        result = alpha * v + (1 - alpha) * result
    return result


def atr(rows, period=14):
    tr = []
    for i in range(1, len(rows)):
        cur, prev = rows[i], rows[i - 1]
        tr.append(max(
            cur["h"] - cur["l"],
            abs(cur["h"] - prev["c"]),
            abs(cur["l"] - prev["c"])
        ))
    if len(tr) < period:
        raise ValueError("Not enough ATR data")
    return sum(tr[-period:]) / period


def analyse(interval, period):
    rows = candles(interval, period)
    close = [r["c"] for r in rows]
    e9, e21, e50 = ema(close, 9), ema(close, 21), ema(close, 50)
    volatility = atr(rows)

    if volatility <= 0:
        raise ValueError("Invalid ATR")

    if e9 > e21 and close[-1] > e50:
        signal = "BUY"
    elif e9 < e21 and close[-1] < e50:
        signal = "SELL"
    else:
        signal = "WAIT"

    entry = close[-1]
    sl = tp = None
    if signal == "BUY":
        sl, tp = entry - 1.5 * volatility, entry + 3 * volatility
    elif signal == "SELL":
        sl, tp = entry + 1.5 * volatility, entry - 3 * volatility

    return {
        "signal": signal, "entry": entry,
        "sl": sl, "tp": tp, "atr": volatility,
        "time": rows[-1]["t"]
    }


def main():
    price, updated = live_price()
    m15 = analyse("15m", "5d")
    h1 = analyse("1h", "1mo")

    signal = m15["signal"]
    if signal not in ("BUY", "SELL") or signal != h1["signal"]:
        signal = "WAIT"

    lines = [
        "GOLD SIGNAL BOT | XAU/USD",
        "",
        f"Live Spot Price: ${price:.2f}",
        f"Price Updated: {updated}",
        "",
        f"M15 Signal: {m15['signal']}",
        f"H1 Signal: {h1['signal']}",
        f"Confirmed Signal: {signal}",
        ""
    ]

    if signal in ("BUY", "SELL"):
        lines += [
            f"Indicative Entry: {m15['entry']:.2f}",
            f"Stop Loss: {m15['sl']:.2f}",
            f"Take Profit: {m15['tp']:.2f}",
            "Risk/Reward: 1:2",
            f"Risk Setting: {RISK_PERCENT}% per trade"
        ]
        if BALANCE > 0:
            lines.append(
                f"Risk Budget: ${BALANCE * RISK_PERCENT / 100:.2f}"
            )
        lines.append(
            "Position size not calculated; broker contract details required."
        )
    else:
        lines.append("No confirmed setup. Wait for alignment.")

    lines += [
        "",
        "Data: Independent XAU/USD spot, not Exness Bid/Ask.",
        "Signals are indicative, not guaranteed.",
        "Signals only. No trades are placed."
    ]

    telegram("\n".join(lines))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Never fabricate a price or signal when data fails
        try:
            telegram(
                "GOLD SIGNAL BOT\n"
                "No signal generated.\n"
                f"Reason: {str(error)[:250]}\n"
                "Please check data availability."
            )
        except Exception:
            raise
