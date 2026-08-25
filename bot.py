import os
import requests
import time

# Configuration
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
         
  # Extracting candles
  closes = [float(candle[4]) for candle in data]
  highs = [float(candle[2]) for candle in data]
  lows = [float(candle[3]) for candle in data]
  opens = [float(candle[1]) for candle in data]

  # Calculate EMA 9 and EMA 15
  ema9_list = calculate_ema(closes, 9)
  ema15_list = calculate_ema(closes, 15)

  # Analyzing the latest confirmed closed candle (index -2)
  o, h, l, c = opens[-2], highs[-2], lows[-2], closes[-2]
  prev_o, prev_c = opens[-3], closes[-3]

  e9 = ema9_list[-2]
  e15 = ema15_list[-2]

  body_size = abs(c - o)
  candle_range = h - l
  if candle_range == 0:
    return

  lower_wick = min(o, c) - l
  upper_wick = h - max(o, c)

  # Touch Conditions
  touch_ema9_b = (l <= e9 and h >= e9) or (abs(l - e9) <= candle_range * 0.5)
  touch_ema15_b = (l <= e15 and h >= e15) or (abs(l - e15) <= candle_range * 0.5)
  touching_bull = touch_ema9_b or touch_ema15_b

  touch_ema9_s = (h >= e9 and l <= e9) or (abs(h - e9) <= candle_range * 0.5)
  touch_ema15_s = (h >= e15 and l <= e15) or (abs(h - e15) <= candle_range * 0.5)
  touching_bear = touch_ema9_s or touch_ema15_s

  # 1. Bullish Rejection
  is_bull_pin = (
      (lower_wick >= 2 * body_size)
      and (upper_wick <= body_size)
      and (candle_range > 0)
  )
  bullish_rejection = is_bull_pin and touching_bull and (c > o)

  # 2. Bullish Engulfing
  is_green = c > o
  prev_is_red = prev_c < prev_o
  bullish_engulfs = (c >= prev_o) and (o <= prev_c)
  bullish_engulfing = is_green and prev_is_red and bullish_engulfs and touching_bull

  # 3. Bearish Rejection
  is_bear_pin = (
      (upper_wick >= 2 * body_size)
      and (lower_wick <= body_size)
      and (candle_range > 0)
  )
  bearish_rejection = is_bear_pin and touching_bear and (c < o)

  # 4. Bearish Engulfing
  is_red = c < o
  prev_is_green = prev_c > prev_o
  bearish_engulfs = (c <= prev_o) and (o >= prev_c)
  bearish_engulfing = is_red and prev_is_green and bearish_engulfs and touching_bear

  # Send Telegram Alerts
  if bullish_rejection:
    send_telegram_message(
        f"🚀 *BTC 5m: Bullish Rejection*\nPrice: {c}\nTouched EMA 9/15 (UP)"
    )
  elif bullish_engulfing:
    send_telegram_message(
        f"🟢 *BTC 5m: Bullish Engulfing*\nPrice: {c}\nTouched EMA 9/15 (UP)"
    )
  elif bearish_rejection:
    send_telegram_message(
        f"📉 *BTC 5m: Bearish Rejection*\nPrice: {c}\nTouched EMA 9/15 (DOWN)"
    )
  elif bearish_engulfing:
    send_telegram_message(
        f"🔴 *BTC 5m: Bearish Engulfing*\nPrice: {c}\nTouched EMA 9/15 (DOWN)"
    )
  else:
    print("Market checked. No signal matched current conditions.")


if __name__ == "__main__":
  print("Running market check...")
  check_market()
  
    
