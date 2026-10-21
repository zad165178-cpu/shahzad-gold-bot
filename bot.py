
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
BALANCE = float(os.environ.get("DEMO_BALANCE", "0"))

RISK_PERCENT = 0.5
BASE = "https://xaus.com/api/v1"
MAX_PRICE_AGE = 180


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ShahzadGoldSignals/2.0"}
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode())


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    body = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": message
    }).encode()

    req = urllib.request.Request(url, data=body)
    with urllib.request.urlopen(req, timeout=20) as response:
        result = json.loads(response.read().decode())
        if not result.get("ok"):
            raise RuntimeError("Telegram message failed")


def get_live_price():
    # Cache-busting parameter for a freshness-sensitive request
    url = BASE + "/spot?compact=1&fresh=" + str(
        int(datetime.now(timezone.utc).timestamp())
    )
    data = get_json(url)

    state = data.get("data_state", {})
    if state.get("status") != "fresh":
        raise ValueError("Spot price is stale or unavailable")

    price = data.get("spot_usd_oz")
    updated = data.get("updated_at")

    if not isinstance(price, (int, float)) or price <= 0:
        raise ValueError("Invalid spot price")

    if not updated:
        raise ValueError("Price timestamp missing")

    stamp = datetime.fromisoformat(updated.replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - stamp).total_seconds()

    if age < -60 or age > MAX_PRICE_AGE:
        raise ValueError("Price timestamp is too old")

    return float(price), updated


def get_candles(interval, period):
    query = urllib.parse.urlencode({
        "symbol": "xau",
        "range": period,
        "interval": interval
    })
    data = get_json(BASE + "/chart?" + query)

    rows = []
    for point in data.get("points", []):
        try:
            rows.append({
                "t": int(point["t"]),
                "o": float(point["o"]),
                "h": float(point["h"]),
                "l": float(point["l"]),
                "c": float(point["c"])
            })
        except (KeyError, ValueError, TypeError):
            continue

    rows.sort(key=lambda r: r["t"])

    candle_seconds = 900 if interval == "15m" else 3600
    now = datetime.now(timezone.utc).timestamp()

    # Only use fully closed candles
    rows = [
        r for r in rows
        if r["t"] + candle_seconds <= now
    ]

    if len(rows) < 55:
        raise ValueError("Insufficient closed candle data: " + interval)

    return rows


def ema(values, period):
    if len(values) < period:
        raise ValueError("Insufficient EMA data")

    alpha = 2 / (period + 1)
    result = sum(values[:period]) / period

    for value in values[period:]:
        result = alpha * value + (1 - alpha) * result

    return result


def calculate_atr(rows, period=14):
    ranges = []

    for i in range(1, len(rows)):
        current = rows[i]
        previous = rows[i - 1]

        ranges.append(max(
            current["h"] - current["l"],
            abs(current["h"] - previous["c"]),
            abs(current["l"] - previous["c"])
        ))

    if len(ranges) < period:
        raise ValueError("Insufficient ATR data")

    return sum(ranges[-period:]) / period


def analyse(interval, period):
    rows = get_candles(interval, period)
    closes = [r["c"] for r in rows]

    e9 = ema(closes, 9)
    e21 = ema(closes, 21)
    e50 = ema(closes, 50)
    volatility = calculate_atr(rows)

    if volatility <= 0:
        raise ValueError("Invalid ATR")

    if e9 > e21 and closes[-1] > e50:
        direction = "BUY"
    elif e9 < e21 and closes[-1] < e50:
        direction = "SELL"
    else:
        direction = "WAIT"

    return {
        "signal": direction,
        "ema9": e9,
        "ema21": e21,
        "ema50": e50,
        "atr": volatility,
        "candle_time": rows[-1]["t"]
    }


def make_signal():
    # Both chart timeframes and spot must be available
    spot, updated = get_live_price()
    m15 = analyse("15m", "5d")
    h1 = analyse("1h", "1mo")

    signal = m15["signal"]
    if signal not in ("BUY", "SELL") or signal != h1["signal"]:
        signal = "WAIT"

    lines = [
        "SHAHZAD GOLD SIGNALS",
        "Instrument: XAU/USD",
        f"Live Spot: ${spot:.2f}",
        f"Price Timestamp: {updated}",
        "",
        f"M15 Trend: {m15['signal']}",
        f"H1 Trend: {h1['signal']}",
        f"Confirmed Signal: {signal}",
        ""
    ]

    if signal in ("BUY", "SELL"):
        # Entry is from the same spot feed displayed above.
        # ATR is derived from the independent chart feed.
        entry = spot
        distance = 1.5 * m15["atr"]
        target_distance = 3.0 * m15["atr"]

        if signal == "BUY":
            sl = entry - distance
            tp = entry + target_distance
        else:
            sl = entry + distance
            tp = entry - target_distance

        lines.extend([
            f"Indicative Entry: ${entry:.2f}",
            f"Stop Loss: ${sl:.2f}",
            f"Take Profit: ${tp:.2f}",
            "Risk/Reward: 1:2",
            f"Risk Setting: {RISK_PERCENT}%",
            "Entry is an indicative spot price."
        ])

        if BALANCE > 0:
            risk_cash = BALANCE * RISK_PERCENT / 100
            lines.append(f"Risk Budget: ${risk_cash:.2f}")

        lines.append(
            "Lot size not calculated; broker contract details required."
        )
    else:
        lines.append("No confirmed setup. Wait for alignment.")

    lines.extend([
        "",
        "WARNING: Independent spot data, NOT Exness Bid/Ask.",
        "Chart and spot feeds may differ.",
        "Signals only. No trades are placed.",
        "No profit or win-rate guarantee."
    ])

    return "\n".join(lines)


def main():
    try:
        message = make_signal()
    except Exception as error:
        message = (
            "SHAHZAD GOLD SIGNALS\n"
            "NO SIGNAL GENERATED\n"
            f"Reason: {str(error)[:200]}\n"
            "Check data connection and timestamps."
        )

    send_telegram(message)


if __name__ == "__main__":
    main()
