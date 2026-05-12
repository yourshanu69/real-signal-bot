import os
import time
import requests
import pandas as pd
import pandas_ta as ta
from flask import Flask
import telebot

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
ALPHA_VANTAGE_KEY = os.environ.get('ALPHA_VANTAGE_KEY')

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

pairs = ["EURUSD", "GBPUSD", "USDJPY"]

def get_signal(pair):
    from_symbol = pair[:3]
    to_symbol = pair[3:]
    url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol={from_symbol}&to_symbol={to_symbol}&interval=5min&outputsize=compact&apikey={ALPHA_VANTAGE_KEY}"

    try:
        data = requests.get(url, timeout=15).json()
        key = "Time Series FX (5min)"
        if key not in data:
            print(f"Error for {pair}: {data}")
            return None

        df = pd.DataFrame(data[key]).T
        df.columns = ['open', 'high', 'low', 'close']
        df = df.astype(float)
        df = df.iloc[::-1].reset_index(drop=True)

        if len(df) < 20: return None

        df['rsi'] = ta.rsi(df['close'], length=14)
        bbands = ta.bbands(df['close'], length=20)
        df['bb_upper'] = bbands['BBU_20_2.0']
        df['bb_lower'] = bbands['BBL_20_2.0']

        latest = df.iloc[-1]
        price = latest['close']
        rsi = latest['rsi']

        print(f"{pair} - Price: {price:.5f} | RSI: {rsi:.2f}")

        if rsi < 30 and price <= latest['bb_lower']:
            return f"🟢 BUY {pair}\nPrice: {price:.5f}\nRSI: {rsi:.2f}"
        elif rsi > 70 and price >= latest['bb_upper']:
            return f"🔴 SELL {pair}\nPrice: {price:.5f}\nRSI: {rsi:.2f}"
        return None

    except Exception as e:
        print(f"Error {pair}: {e}")
        return None

def send_signals():
    for pair in pairs:
        signal = get_signal(pair)
        if signal:
            bot.send_message(TELEGRAM_CHAT_ID, signal)
        time.sleep(15)

@app.route('/')
def home(): return "Bot running!"

if __name__ == "__main__":
    print("Bot started...")
    while True:
        send_signals()
        time.sleep(300)
