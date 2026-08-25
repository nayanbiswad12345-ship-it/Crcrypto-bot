import requests

# আপনার বর্তমান টোকেন এবং চ্যাট আইডি
TELEGRAM_TOKEN = "8922634614:AAFDphqbsgmE_4-1NQQ4ZeRD7Ay qPrS5YGI"
CHAT_ID = "8637317407"

print("Sending test message to Telegram...")

url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
payload = {
    "chat_id": CHAT_ID,
    "text": "🚀 Hello Nayon! This is a test message from GitHub Actions."
}

response = requests.post(url, json=payload)

print("Status Code:", response.status_code)
print("Response Text:", response.text)
