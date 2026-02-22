import asyncio
import threading
import sqlite3
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# MƏLUMATLARI DAXİL ET
TOKEN = "SƏNİN_BOT_TOKENİN"
ADMIN_ID = 123456789  
WEB_APP_URL = "https://istifadəçi-adın.github.io/repo-adın/"
KANAL_LINK = "https://t.me/seninkanalin"
DESTEK_LINK = "https://t.me/senin_profilin"
PHOTO_URL = "https://img.freepik.com/free-vector/gradient-social-media-marketing-concept_23-2149021820.jpg"

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = Flask('')

# --- DATABASE QURULUŞU ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0)''')
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else 0.0

def update_balance(user_id, amount):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id, balance) VALUES (?, 0.0)", (user_id,))
    c.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, user_id))
    conn.commit()
    conn.close()

# --- RENDER ÜÇÜN FLASK ---
@app.route('/')
def home(): return "Bot is alive!"

def run_flask():
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- BOT ƏMRLƏRİ ---
@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    # İstifadəçini bazaya əlavə et (əgər yoxdursa)
    update_balance(user_id, 0) 
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Market (Veb Tətbiq)", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="📢 Kanalımız", url=KANAL_LINK),
         InlineKeyboardButton(text="👨‍💻 Dəstək", url=DESTEK_LINK)]
    ])
    
    await message.answer_photo(photo=PHOTO_URL, caption=f"<b>Salam, {message.from_user.first_name}!</b>\nBalansın: <b>{get_balance(user_id)} AZN</b>", parse_mode="HTML", reply_markup=markup)

# Qəbz bildirişi gələndə Adminə (Sənə) düymə göndərir
@dp.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def web_app_received(message: types.Message):
    if message.web_app_data.data == "qebz_atildi":
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Təsdiqlə (+5 AZN)", callback_data=f"add_5_{message.from_user.id}")],
            [InlineKeyboardButton(text="❌ İmtina Et", callback_data="decline")]
        ])
        await bot.send_message(ADMIN_ID, f"🔔 <b>YENİ QƏBZ!</b>\nİstifadəçi: {message.from_user.first_name}\nID: <code>{message.from_user.id}</code>\n\nBalans artırılsın?", parse_mode="HTML", reply_markup=markup)

# Admin düyməyə basanda balansı artırır
@dp.callback_query(F.data.startswith("add_5_"))
async def approve_payment(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    update_balance(user_id, 5.0) # Nümunə üçün 5 AZN artırırıq
    await callback.answer("Balans artırıldı!")
    await bot.send_message(user_id, "✅ Ödənişiniz təsdiqləndi! Balansınıza 5.00 AZN əlavə edildi.")
    await callback.message.edit_text(f"✅ İstifadəçi {user_id} üçün balans 5 AZN artırıldı.")

async def main():
    init_db()
    threading.Thread(target=run_flask).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
