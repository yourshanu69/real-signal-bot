import os
import time
import requests
import pandas as pd
import pandas_ta as ta
from flask import Flask
import telebot
from telebot import types

# Railway Variables থেকে নিবে
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
TWELVEDATA_API_KEY = os.environ.get('TWELVEDATA_API_KEY')

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

# Pair List - / ছাড়া দিতে হবে
pairs = ["EURUSD", "GBPUSD", "USDJPY"]

def get_signal(pair):
    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=5min&outputsize=50&apikey={TWELVEDATA_API_KEY}"
    try:
        data = requests.get(url).json()
        
        if 'values' not in data:
            print(f"TwelveData Error: {data}")
            return None
        
        df = pd.DataFrame(data['values'])
        df = df.astype(float)
        df = df.iloc[::-1].reset_index(drop=True)
        
        if len(df) < 20:
            print(f"Not enough candles for {pair}")
            return None
            
        # RSI + Bollinger Band Calculate
        df['rsi'] = ta.rsi(df['close'], length=14)
        bbands = ta.bbands(df['close'], length=20)
        df['bb_upper'] = bbands['BBU_20_2.0']
        df['bb_lower'] = bbands['BBL_20_2.0']
        df['bb_middle'] = bbands['BBM_20_2.0']
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        price = latest['close']
        prev_price = prev['close']
        rsi = latest['rsi']
        bb_upper = latest['bb_upper']
        bb_lower = latest['bb_lower']
        bb_middle = latest['bb_middle']
        
        print(f"{pair} - Price: {price:.5f} | RSI: {rsi:.2f}")
        
        # Signal Logic - তোমার মত করে Change করো
        signal = None
        if rsi < 30 and price <= bb_lower:
            signal = f"🟢 BUY {pair}\nPrice: {price:.5f}\nRSI: {rsi:.2f} Oversold"
        elif rsi > 70 and price >= bb_upper:
            signal = f"🔴 SELL {pair}\nPrice: {price:.5f}\nRSI: {rsi:.2f} Overbought"
            
        return signal
        
    except Exception as e:
        print(f"Error {pair}: {e}")
        return None

def send_signals():
    for pair in pairs:
        signal = get_signal(pair)
        if signal:
            try:
                bot.send_message(TELEGRAM_CHAT_ID, signal)
                print(f"Signal sent to Telegram ✅")
            except Exception as e:
                print(f"Telegram Error: {e}")
        time.sleep(2) # API Limit এর জন্য

@app.route('/')
