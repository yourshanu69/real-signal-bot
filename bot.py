import requests
import time
import telebot
import threading
from flask import Flask
import os
from telebot import types

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID"))
TWELVEDATA_API_KEY = os.environ.get("TWELVEDATA_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)
last_signal = {} # Pair wise cooldown track করবে

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
    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=2&apikey={TWELVEDATA_API_KEY}&indicators=rsi,bbands"
    try:
        data = requests.get(url).json()
        if 'values' not in data: return None

        latest = data['values'][0]
        prev = data['values'][1]
        price = float
