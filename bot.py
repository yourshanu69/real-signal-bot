import requests
import time
import telebot
import threading
from flask import Flask
import os

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID"))
TWELVEDATA_API_KEY = os.environ.get("TWELVEDATA_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

last_signal = {}

@app.route('/')
def home():
    return "Signal Bot Live"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bot is running ✅")

def get_signal(pair):
    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=2&apikey={TWELVEDATA_API_KEY}&indicators=rsi,bbands"
    data = requests.get(url).json()
    if 'values' not in data: return None
    
    latest = data['values'][0]
    prev = data['values'][1]
    price = float(latest['close'])
    prev_price = float(prev['close'])
    rsi = float(latest['rsi'])
    bb_upper = float(latest['bbands_upper'])
    bb_lower = float(latest['bbands_lower'])
    
    if pair in last_signal and time.time() - last_signal[pair] < 300: return None
    
    if price <= bb_lower and rsi < 30 and price > prev_price:
        last_signal[pair] = time.time()
        return "CALL", f"RSI: {rsi:.2f}"
    
    if price >= bb_upper and rsi > 70 and price < prev_price:
        last_signal[pair] = time.time()
        return "PUT", f"RSI: {rsi:.2f}"
    
    return None

def check_signals():
    pairs = ["EUR/USD", "GBP/USD", "USD/JPY"]
    while True:
        for pair in pairs:
            signal = get_signal(pair)
            if signal:
                text = f"🔥 {pair}\nSignal: {signal[0]}\n{signal[1]}"
                bot.send_message(TELEGRAM_CHAT_ID, text)
        time.sleep(120)

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Bot Active. Auto signals every 2 min.")

if __name__ == '__main__':
    threading.Thread(target=check_signals, daemon=True).start()
    bot.polling(non_stop=True)
