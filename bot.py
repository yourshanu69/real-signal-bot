import os
import telebot
from telebot import types
import requests
import time
from datetime import datetime
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Signal Bot Live"
Thread(target=lambda: app.run(host='0.0.0.0',port=8080)).start()

BOT_TOKEN = os.environ.get('BOT_TOKEN')
API_KEY = os.environ.get('TWELVEDATA_API_KEY')
CHANNEL_ID = "@YourChannelUsername"
ADMIN_ID = 1692907487
bot = telebot.TeleBot(BOT_TOKEN)

approved_users = set()
PAIRS = ["EUR/USD", "GBP/USD"]
last_signal = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = message.from_user.username

    if user_id == ADMIN_ID:
        bot.reply_to(message, f"Admin Panel\nApproved Users: {len(approved_users)}")
        return

    if user_id in approved_users:
        bot.reply_to(message, f"Access Granted\nSignals: {CHANNEL_ID}")
    else:
        bot.reply_to(message, "Request Sent\nWait for admin approval")

        markup = types.InlineKeyboardMarkup()
        approve_btn = types.InlineKeyboardButton("Approve", callback_data=f"approve_{user_id}")
        reject_btn = types.InlineKeyboardButton("Reject", callback_data=f"reject_{user_id}")
        markup.add(approve_btn, reject_btn)

        text = f"New User Request\nName: {user_name}\nUser ID: {user_id}\nUsername: @{username}"
        bot.send_message(ADMIN_ID, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.from_user.id!= ADMIN_ID:
        bot.answer_callback_query(call.id, "Admin Only")
        return

    data = call.data.split('_')
    action = data[0]
    user_id = int(data[1])

    if action == "approve":
        approved_users.add(user_id)
        bot.edit_message_text(f"Approved\nUser ID: {user_id}", call.message.chat.id, call.message.message_id)
        bot.send_message(user_id, f"Approved by admin\nYou will get signals now")
    elif action == "reject":
        bot.edit_message_text(f"Rejected\nUser ID: {user_id}", call.message.chat.id, call.message.message_id)
        bot.send_message(user_id, "Request rejected by admin")

def get_signal(pair):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=30&indicators=rsi,bbands&apikey={API_KEY}"
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
        return "CALL", f"RSI: {rsi}"
