import os
import time
import requests
import pandas as pd
import pandas_ta as ta
from flask import Flask
import telebot

# Railway Variables থেকে নিবে
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
TWELVEDATA_API_KEY = os.environ.get('TWELVEDATA_API_KEY')

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

# Pair List - TwelveData তে / ছাড়া লাগে
pairs = ["EURUSD", "GBPUSD", "USDJPY"]

def get_signal(pair):
    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=5min&outputsize=50&apikey={TWELVEDATA_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'values' not in data:
            print(f"TwelveData Error for {pair}: {data}")
            return None
        
        df = pd.DataFrame(data['values'])
        df['close'] = df['close'].astype(float)
        df = df.iloc[::-1].reset_index(drop=True)
        
        if len(df) < 20:
            print(f"Not enough candles for {pair}")
            return None
            
        # RSI + Bollinger Band Calculate
        df['rsi'] = ta.rsi(df['close'], length=14)
        bbands = ta.bbands(df['close'], length=20, std=2.0)
        df['bb_upper'] = bbands['BBU_20_2.0']
        df['bb_lower'] = bbands['BBL_20_2.0']
        
        latest = df.iloc[-1]
        price = round(latest['close'], 5)
        rsi = round(latest['rsi'], 2)
        bb_upper = round(latest['bb_upper'], 5)
        bb_lower = round(latest['bb_lower'], 5)
        
        print(f"{pair} - Price: {price} | RSI: {rsi}")
        
        # Signal Logic
        if rsi < 30 and price <= bb_lower:
            return f"🟢 BUY SIGNAL: {pair}\nPrice: {price}\nRSI: {rsi} - Oversold\nBB Lower: {bb_lower}"
        elif rsi > 70 and price >= bb_upper:
            return f"🔴 SELL SIGNAL: {pair}\nPrice: {price}\nRSI: {rsi} - Overbought\nBB Upper: {bb_upper}"
        return None
        
    except Exception as e:
        print(f"Error {pair}: {str(e)}")
        return None

def send_signals():
    for pair in pairs:
        signal = get_signal(pair)
        if signal:
            try:
                bot.send_message(TELEGRAM_CHAT_ID, signal)
                print(f"Signal sent for {pair} ✅")
            except Exception as e:
                print(f"Telegram Error: {e}")
        time.sleep(3)

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == "__main__":
    print("Bot started polling...")
    print("Monitoring: EURUSD, GBPUSD, USDJPY")
    while True:
        send_signals()
        time.sleep(300)
