import asyncio
import threading
import sqlite3
import requests
import os
import json
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# --- MƏLUMATLARI DAXİL ET ---
TOKEN = "8401084300:AAF5y2cjnIpSl4LHKUxfLGof-7Gxy8Sy08E"
ADMIN_ID = 8566739483 
WEB_APP_URL = "https://omer316972.github.io/Smm-Market/"
PANEL_BAKU_API_KEY = "b5b8b170835942c21c44ae65fdec454c"
PANEL_API_URL = "https://panelbaku.com/api/v2"

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = Flask('')

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('users.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0)')
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect('users.db')
    res = conn.execute("SELECT balance FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return res[0] if res else 0.0

def update_balance(user_id, amount):
    conn = sqlite3.connect('users.db')
    conn.execute("INSERT OR IGNORE INTO users (id, balance) VALUES (?, 0.0)", (user_id,))
    conn.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, user_id))
    conn.commit()
    conn.close()

# --- PANELBAKU API ---
def get_live_services():
    try:
        params = {'key': PANEL_BAKU_API_KEY, 'action': 'services'}
        r = requests.get(PANEL_API_URL, params=params)
        if r.status_code == 200:
            data = r.json()
            return data[:10] # İlk 10 xidməti göndəririk (URL çox uzun olmasın deyə)
        return []
    except:
        return []

# --- BOT ---
@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    update_balance(user_id, 0)
    bal = get_balance(user_id)
    services = get_live_services()
    
    # Məlumatları URL-ə sıxırıq
    services_json = json.dumps(services)
    final_url = f"{WEB_APP_URL}?balance={bal}&services={services_json}"

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Marketə Giriş", web_app=WebAppInfo(url=final_url))],
        [InlineKeyboardButton(text="📢 Kanal", url="https://t.me/kanal"),
         InlineKeyboardButton(text="👨‍💻 Dəstək", url="https://t.me/profil")]
    ])
    
    await message.answer_photo(
        photo="https://img.freepik.com/free-vector/gradient-social-media-marketing-concept_23-2149021820.jpg",
        caption=f"<b>Salam, {message.from_user.first_name}! 👋</b>\n💰 Balansın: <b>{bal:.2f} AZN</b>",
        parse_mode="HTML",
        reply_markup=markup
    )

@dp.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def handle_data(message: types.Message):
    data = message.web_app_data.data
    if data == "qebz_atildi":
        await message.answer("📸 Zəhmət olmasa qəbz şəklini bura göndər.")
    elif data.startswith("order_"):
        await message.answer(f"📦 Sifariş qəbul edildi! ID: {data.split('_')[1]}\nLinki göndərin.")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ 1 AZN", callback_data=f"pay_{message.from_user.id}_1"),
         InlineKeyboardButton(text="✅ 5 AZN", callback_data=f"pay_{message.from_user.id}_5")],
        [InlineKeyboardButton(text="❌ Rədd et", callback_data=f"ref_{message.from_user.id}")]
    ])
    await bot.send_photo(ADMIN_ID, photo=message.photo[-1].file_id, caption="Yeni qəbz!", reply_markup=markup)
    await message.answer("✅ Qəbz adminə göndərildi.")

@dp.callback_query(F.data.startswith("pay_"))
async def approve(call: types.CallbackQuery):
    _, uid, amt = call.data.split("_")
    update_balance(int(uid), float(amt))
    await bot.send_message(int(uid), f"✅ Balansınız {amt} AZN artırıldı!")
    await call.message.edit_caption(caption="✅ Təsdiqləndi.")

# --- SERVER ---
@app.route('/')
def home(): return "Bot Live"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

async def main():
    init_db()
    threading.Thread(target=run_flask).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
