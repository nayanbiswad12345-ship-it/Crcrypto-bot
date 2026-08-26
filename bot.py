import os
import time
import requests

# Configuration
TELEGRAM_TOKEN = "8922634614:AAFDphqbsgmE_4-1NQQ4ZeRD7AyqPrS5YGI"
CHAT_ID = "8637317407"
RESOLUTION = "5m"

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload, timeout=5)
        print("Telegram response:", response.text)
    except Exception as e:
        print("Telegram error:", e)

def calculate_ema(prices, length):
    k = 2 / (length + 1)
    ema_list = [prices[0]]
    for price in prices[1:]:
        ema_list.append((price * k) + (ema_list[-1] * (1 - k)))
    return ema_list

def check_market():
    print("Fetching market data from Delta Exchange...")
    
    end_time = int(time.time())
    start_time = end_time - (50 * 5 * 60) # Last 50 candles of 5 minutes
    
    url = f"https://api.india.delta.exchange/v2/history/candles?resolution={RESOLUTION}&symbol=BTC&start={start_time}&end={end_time}"
    
    try:
        response = requests.get(url, timeout=10)
        print("API Status Code:", response.status_code)
        result = response.json()
        data = result.get("result", [])
    except Exception as e:
        print("Delta Exchange connection error:", e)
        return

    if not data or not isinstance(data, list) or len(data) < 20:
        print("Data not available or empty, waiting... Raw response:", result)
        return

    data = sorted(data, key=lambda x: x['time'] if isinstance(x, dict) else x[0])

    if isinstance(data[0], dict):
        opens = [float(c['open']) for c in data]
        highs = [float(c['high']) for c in data]
        lows = [float(c['low']) for c in data]
        closes = [float(c['close']) for c in data]
    else:
        opens = [float(c[1]) for c in data]
        highs = [float(c[2]) for c in data]
        lows = [float(c[3]) for c in data]
        closes = [float(c[4]) for c in data]

    ema9_list = calculate_ema(closes, 9)
    ema15_list = calculate_ema(closes, 15)

    o = opens[-1]
    h = highs[-1]
    l = lows[-1]
    c = closes[-1]
    
    prev_o = opens[-2]
    prev_c = closes[-2]

    e9 = ema9_list[-1]
    e15 = ema15_list[-1]

    print(f"Latest Close: {c}, EMA9: {e9:.2f}, EMA15: {e15:.2f}")

    body_size = abs(c - o)
    candle_range = h - l
    if candle_range == 0:
        return

    lower_wick = min(o, c) - l
    upper_wick = h - max(o, c)

    touch_ema9 = (l <= e9 <= h)
    touch_ema15 = (l <= e15 <= h)
    touching_ema = touch_ema9 or touch_ema15

    is_hammer = (lower_wick >= body_size * 1.2) and (c > o)
    bullish_rejection = is_hammer and touching_ema

    is_shooting_star = (upper_wick >= body_size * 1.2) and (c < o)
    bearish_rejection = is_shooting_star and touching_ema

    is_green = c > o
    prev_is_red = prev_c < prev_o
    is_engulfing_size = (c >= prev_o) and (o <= prev_c)
    bullish_engulfing = is_green and prev_is_red and is_engulfing_size and touching_ema

    is_red = c < o
    prev_is_green = prev_c > prev_o
    is_bear_engulf_size = (c <= prev_o) and (o >= prev_c)
    bearish_engulfing = is_red and prev_is_green and is_bear_engulf_size and touching_ema

    if bullish_rejection:
        send_telegram_message(f"🚀 *Delta BTC 5m: Bullish Rejection*\nPrice: {c}\nLower wick touched EMA 9/15 (UP)")
    elif bullish_engulfing:
        send_telegram_message(f"🟢 *Delta BTC 5m: Bullish Engulfing*\nPrice: {c}\nEngulfed near EMA 9/15 (UP)")
    elif bearish_rejection:
        send_telegram_message(f"📉 *Delta BTC 5m: Bearish Rejection*\nPrice: {c}\nUpper wick touched EMA 9/15 (DOWN)")
    elif bearish_engulfing:
        send_telegram_message(f"🔴 *Delta BTC 5m: Bearish Engulfing*\nPrice: {c}\nEngulfed near EMA 9/15 (DOWN)")
    else:
        print("Market checked. No active signal on the closed candle.")

if __name__ == "__main__":
    print("Running Delta Exchange market check...")
    # Sending startup test message
    send_telegram_message("🤖 *Crypto Bot Started Successfully!*\nDelta Exchange 5m BTC Strategy is active.")
    check_market()
    
