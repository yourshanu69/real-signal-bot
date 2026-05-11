import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Permission Bot Live ✅"
Thread(target=lambda: app.run(host='0.0.0.0',port=8080)).start()

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = "@YourChannel"
ADMIN_ID = 1692907487# তোমার Telegram ID @userinfobot থেকে নাও
bot = telebot.TeleBot(BOT_TOKEN)

# Approved User List - এখানে Save হবে
approved_users = set()

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = message.from_user.username

    if user_id == ADMIN_ID:
        bot.reply_to(message, "✅ **Admin Panel**\n\nApproved Users: " + str(len(approved_users)))
        return

    if user_id in approved_users:
        bot.reply_to(message, "✅ **Access Granted**\n\nতুমি Already Approved। Signal Channel এ পাবা: " + CHANNEL_ID)
    else:
        # User কে বলবো Wait করতে
        bot.reply_to(message, "⏳ **Request Sent**\n\nAdmin Approval এর জন্য Wait করুন। Approve হলে জানিয়ে দেওয়া হবে।")

        # Admin এর কাছে Notification + Button পাঠাবো
        markup = types.InlineKeyboardMarkup()
        approve_btn = types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}")
        reject_btn = types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
        markup.add(approve_btn, reject_btn)

        text = f"""
🔔 **New User Request** 🔔

👤 **Name:** {user_name}
🆔 **User ID:** `{user_id}`
📱 **Username:** @{username if username else 'None'}

Signal Access দিবেন?
        """
        bot.send_message(ADMIN_ID, text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.from_user.id!= ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Admin Only")
        return

    data = call.data.split('_')
    action = data[0]
    user_id = int(data[1])

    if action == "approve":
        approved_users.add(user_id)
        bot.edit_message_text(f"✅ **Approved**\n\nUser ID `{user_id}` কে Access দেওয়া হয়েছে।",
                              call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        # User কে জানায় দিলাম
        bot.send_message(user_id, f"🎉 **Congratulations!**\n\nAdmin আপনাকে Approve করেছে।\nএখন থেকে সব Signal পাবেন: {CHANNEL_ID}")

    elif action == "reject":
        bot.edit_message_text(f"❌ **Rejected**\n\nUser ID `{user_id}` কে Reject করা হয়েছে।",
                              call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        bot.send_message(user_id, "😔 **Sorry**\n\nআপনার Request Reject করা হয়েছে। Admin এর সাথে Contact করুন।")

# Signal পাঠানোর আগে Check করবো Approved কিনা
def send_signal_to_all(signal_text):
    for user_id in approved_users:
        try:
            bot.send_message(user_id, signal_text)
        except: # Block করলে Error আসবে
            approved_users.remove(user_id)

# Example: Admin Command দিয়ে Signal পাঠানো
@bot.message_handler(commands=['signal'])
def admin_signal(message):
    if message.chat.id!= ADMIN_ID: return
    signal_text = "🔥 **Test Signal**\n📊 EUR/USD\n📈 CALL ⬆️\n\nOnly Approved Users Got This"
    send_signal_to_all(signal_text)
    bot.reply_to(message, f"✅ Signal Sent to {len(approved_users)} Users")

if __name__ == "__main__":
    print("Permission Bot Started...")
    bot.infinity_polling()
