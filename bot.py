import requests
import time
import telebot
import pandas as pd
import pandas_ta as ta
import threading
from flask import Flask
import os
from telebot import types

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID"))
TWELVEDATA_API_KEY = os.environ.get("TWELVEDATA_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)
last_signal = {} # Pair wise time save হবে

@app.route('/')
def home():
    return "Signal Bot Live"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("✅ Bot Status")
    btn2 = types.KeyboardButton("📊 Active Pairs")
    btn3 = types.KeyboardButton("⚙️ Strategy")
    btn4 = types.KeyboardButton("📞 Help")
    markup.add(btn1, btn2, btn3, btn4)
    bot.reply_to(message, "🤖 Bot চালু আছে ✅\n\nSignal আসবে প্রতি 3 মিনিটে - High Accuracy 🔥", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "✅ Bot Status")
def bot_status(message):
    bot.reply_to(message, "🟢 Status: Active\n⏰ Scan: প্রতি 1 মিনিট\n🔒 Cooldown: 3 মিনিট Per Pair\n📡 Mode: Filtered Signal")

@bot.message_handler(func=lambda message: message.text == "📊 Active Pairs")
def active_pairs(message):
    bot.reply_to(message, "📊 Active Pairs:\n\n1. EUR/USD\n2. GBP/USD\n3. USD/JPY\n\n⏱️ Timeframe: 1 Minute")

@bot.message_handler(func=lambda message: message.text == "⚙️ Strategy")
def strategy_info(message):
    text = "⚙️ Signal Strategy:\n\n✅ RSI < 30 + BB Lower + Price Up = CALL\n✅ RSI > 70 + BB Upper + Price Down = PUT\n\n🔒 Cooldown: 3 Min - Fake Signal Filter\n🎯 1 Min Candle"
    bot.reply_to(message, text)

@bot.message_handler(func=lambda message: message.text == "📞 Help")
def send_help(message):
    bot.reply_to(message, "📞 Help:\n\nএকই Pair এ 3 মিনিট পরপর Signal আসবে। এতে Scam কম হয়।")

def get_signal(pair):
    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=50&apikey={TWELVEDATA_API_KEY}"
    try:
        data = requests.get(url).json()
        if 'values' not in data:
    print(f"API Response: {data}")  # এই লাইন Add করো
    print(f"No data for {pair}")
    return None
            print(f"No data for {pair}")
            return None

            # Fix: 50টা Candle নিয়ে RSI + BB নিজে বানাও 
    df = pd.DataFrame(data['values'])
    df = df.astype(float)
    df = df.iloc[::-1].reset_index(drop=True) # উল্টায় দাও
    
    if len(df) < 20:
        print(f"No data for {pair}")
        return None
        
    # RSI আর Bollinger Band Calculate করো
    df['rsi'] = ta.rsi(df['close'], length=14)
    bbands = ta.bbands(df['close'], length=20)
    df['bb_upper'] = bbands['BBU_20_2.0']
    df['bb_lower'] = bbands['BBL_20_2.0']
    
    # Latest Value নাও
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    price = latest['close']
    prev_price = prev['close']
    rsi = latest['rsi']
    bb_upper = latest['bb_upper']
    bb_lower = latest['bb_lower']
    
    print(f"{pair} - Price: {price:.5f} | RSI: {rsi:.2f}")
        # Cooldown Check - Fixed
        if pair in last_signal and time.time() - last_signal[pair] < 180:
            print(f"{pair} in cooldown")
            return None

        # CALL Condition
        if price <= bb_lower and rsi < 30 and price > prev_price:
            last_signal[pair] = time.time() # Fixed
            return "CALL", f"RSI: {rsi:.2f} | Price: {price}"

        # PUT Condition
        if price >= bb_upper and rsi > 70 and price < prev_price:
            last_signal[pair] = time.time() # Fixed
            return "PUT", f"RSI: {rsi:.2f} | Price: {price}"

        print(f"{pair} - No condition match. RSI:{rsi:.2f}")
        return None
    except Exception as e:
        print(f"Error {pair}: {e}")
        return None

def check_signals():
    pairs = ["EUR/USD", "GBP/USD", "USD/JPY"]
    while True:
        for pair in pairs:
            signal = get_signal(pair)
            if signal:
                text = f"🔥 {pair}\nSignal: {signal[0]}\n{signal[1]}\n⏰ 1 Min Trade\n🔒 3 Min Filtered"
                try:
                    bot.send_message(TELEGRAM_CHAT_ID, text)
                    print(f"Signal sent: {pair}")
                except Exception as e:
                    print(f"Send Error: {e}")
        time.sleep(60)

if __name__ == '__main__':
    threading.Thread(target=check_signals, daemon=True).start()
    threading.Thread(target=lambda: bot.polling(non_stop=True)).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
