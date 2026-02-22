import asyncio
import threading
import sqlite3
import requests
import os
import json
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

# --- MƏLUMATLARI DAXİL ET ---
TOKEN = "8401084300:AAHIClVs7pTgCQJaI7A42BTQLQT32GQfAU8"
ADMIN_ID = 8566739483  # @userinfobot-dan aldigin ID
WEB_APP_URL = "https://omer316972.github.io/Smm-Market/"
PANEL_BAKU_API_KEY = "5c5a238037ce23ff5baa4a43142fa338"
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
def get_panel_services():
    try:
        params = {'key': PANEL_BAKU_API_KEY, 'action': 'services'}
        response = requests.get(PANEL_API_URL, params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# --- BOT ---
@dp.message(CommandStart())
async def start(message: types.Message):
    uid = message.from_user.id
    update_balance(uid, 0)
    bal = get_balance(uid)
    
    # API-den xidmetleri cekirik
    services = get_panel_services()
    
    # WebApp URL-e balansi ve qisaca xidmetleri gonderirik
    # Qeyd: URL cox uzun olmasin deye sadece balansi gonderirik, xidmetleri sayt oz daxilinde API ile de ceke biler.
    final_url = f"{WEB_APP_URL}?balance={bal}"

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Market (Profil & Balans)", web_app=WebAppInfo(url=final_url))],
        [InlineKeyboardButton(text="📢 Kanal", url="https://t.me/example"),
         InlineKeyboardButton(text="👨‍💻 Destek", url="https://t.me/example")]
    ])
    
    await message.answer_photo(
        photo="https://img.freepik.com/free-vector/gradient-social-media-marketing-concept_23-2149021820.jpg",
        caption=f"<b>Salam, {message.from_user.first_name}! 👋</b>\n\n💰 Balansın: <b>{bal:.2f} AZN</b>\n\nMarketə daxil olaraq xidmətləri görə və balansını artıra bilərsən.",
        parse_mode="HTML",
        reply_markup=markup
    )

@dp.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def web_app_received(message: types.Message):
    if message.web_app_data.data == "qebz_atildi":
        await message.answer("📸 <b>Qəbz sistemi aktivdir!</b>\n\nZəhmət olmasa ödəniş qəbzinin şəklini bura göndərin.")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ 1 AZN", callback_data=f"pay_{message.from_user.id}_1"),
         InlineKeyboardButton(text="✅ 5 AZN", callback_data=f"pay_{message.from_user.id}_5"),
         InlineKeyboardButton(text="✅ 10 AZN", callback_data=f"pay_{message.from_user.id}_10")],
        [InlineKeyboardButton(text="❌ Imtina", callback_data=f"refuse_{message.from_user.id}")]
    ])
    await bot.send_photo(ADMIN_ID, photo=message.photo[-1].file_id, 
                         caption=f"🔔 Yeni qəbz!\nİstifadəçi: {message.from_user.first_name}\nID: {message.from_user.id}", 
                         reply_markup=markup)
    await message.answer("✅ Qəbz adminə göndərildi.")

@dp.callback_query(F.data.startswith("pay_"))
async def approve(call: types.CallbackQuery):
    _, uid, amt = call.data.split("_")
    update_balance(int(uid), float(amt))
    await bot.send_message(int(uid), f"✅ Balansınız {amt} AZN artırıldı!")
    await call.message.edit_caption(caption=f"✅ {uid} üçün {amt} AZN təsdiqləndi.")

# --- RENDER/FLASK ---
@app.route('/')
def home(): return "Bot is live!"

def run_flask():
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def main():
    init_db()
    threading.Thread(target=run_flask).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
