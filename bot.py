import os
import time
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "8637317407"
SYMBOL = "BTCUSDT"
INTERVAL = "5m"

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=5)
        print("Telegram message sent successfully.")
    except Exception as e:
        print("Telegram error:", e)

def calculate_ema(prices, length):
    k = 2 / (length + 1)
    ema_list = [prices[0]]
    for price in prices[1:]:
        ema_list.append((price * k) + (ema_list[-1] * (1 - k)))
    return ema_list

def check_market():
    print("Fetching market data from Binance...")
    url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit=30"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
    except Exception as e:
        print("Binance connection error:", e)
        return

       if not data or not isinstance(data, list) or len(data) < 20:
        print("Data not available, retrying once...")
        time.sleep(3)
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
        except Exception:
            pass
            
        if not data or not isinstance(data, list) or len(data) < 20:
            print("Data still empty, waiting for next schedule.")
            return

    closes = [float(candle[4]) for candle in data]
    highs = [float(candle[2]) for candle in data]
    lows = [float(candle[3]) for candle in data]
    opens = [float(candle[1]) for candle in data]

    ema9_list = calculate_ema(closes, 9)
    ema15_list = calculate_ema(closes, 15)

    o, h, l, c = opens[-2], highs[-2], lows[-2], closes[-2]
    e9 = ema9_list[-2]
    e15 = ema15_list[-2]

    body_size = abs(c - o)
    candle_range = h - l
    if candle_range == 0:
        return

    print("Market check completed successfully.")

if __name__ == "__main__":
    check_market()
  
