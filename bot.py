import requests
import time
import telebot
import threading
from flask import Flask

TELEGRAM_BOT_TOKEN = "8343572374:AAF7LsPYu7XjS7KYMxtAmsy0RBuGiWrUXmE"
TELEGRAM_CHAT_ID = "-1003095197963"
TWELVEDATA_API_KEY = "20709bd186db4413924c7c2b164da09b"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

last_signal = {}

@app.route('/')
def home():
    return "Signal Bot Live"

def get_signal(pair):
    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&apikey={TWELVEDATA_API_KEY}&outputsize=20&indicators=rsi,bbands"
    data = requests.get(url).json()
    if 'values' not in data: return None

    latest = data['values'][0]
    prev = data['values'][1]
    price = float(latest['close'])
    prev_price = float(prev['close'])
    rsi = float(latest['rsi'])
    bb_upper = float(latest['bbands_upper'])
    bb_lower = float(latest['bbands_lower'])

    if pair in last_signal and time.time() - last_signal < 300: return None

    if price <= bb_lower and rsi < 30 and price > prev_price:
        last_signal = time.time()
        return "CALL", f"RSI: {rsi:.2f}"

    if price >= bb_upper and rsi > 70 and price < prev_price:
        last_signal = time.time()
        return "PUT", f"RSI: {rsi:.2f}"

    return None

def check_signals():
    pairs = ["EUR/USD", "GBP/USD", "USD/JPY", "BTC/USD"]
    while True:
        for pair in pairs:
            try:
                signal = get_signal(pair)
                if signal:
                    signal_type, details = signal
                    msg = f"🔥 **{signal_type} SIGNAL** 🔥\n\nPair: `{pair}`\n{details}\n\n⚡ 1 Minute Expiry"
                    bot.send_message(TELEGRAM_CHAT_ID, msg, parse_mode="Markdown")
            except Exception as e:
                print(f"Error: {e}")
        time.sleep(60)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot is running ✅")

threading.Thread(target=bot.polling, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
