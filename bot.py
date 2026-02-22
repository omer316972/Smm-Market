import asyncio
import threading
import sqlite3
import requests
import os
import json # JSON formatında məlumat göndərmək üçün
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

# --- MƏLUMATLARI DAXİL ET ---
TOKEN = "8401084300:AAHIClVs7pTgCQJaI7A42BTQLQT32GQfAU8"
ADMIN_ID = 8566739483 
WEB_APP_URL = "https://omer316972.github.io/Smm-Market//"
KANAL_LINK = "https://t.me/TapBaxaq" # Öz kanalın
DESTEK_LINK = "https://t.me/TapBaxaq" # Öz profilin
PHOTO_URL = "https://img.freepik.com/free-vector/gradient-social-media-marketing-concept_23-2149021820.jpg"

PANEL_BAKU_API_KEY = "5c5a238037ce23ff5baa4a43142fa338"
PANEL_API_URL = "https://panelbaku.com/api/v2"

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = Flask('')

# --- DATABASE (Məlumat Bazası) ---
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

# --- PANELBAKU API FUNKSİYASI ---
def get_panel_services():
    try:
        params = {'key': PANEL_BAKU_API_KEY, 'action': 'services'}
        response = requests.get(PANEL_API_URL, params=params)
        data = response.json()
        
        # Xidmətləri sayt üçün formatlayırıq
        formatted_services = []
        for service_id, s_data in data.items():
            formatted_services.append({
                'service': s_data['service'], # API ID
                'name': s_data['name'],
                'rate': float(s_data['rate']),
                'min': s_data['min'],
                'max': s_data['max']
            })
        return formatted_services
    except Exception as e:
        print(f"API Xətası: {e}")
        return []

# --- BOT ƏMRLƏRİ ---
@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    update_balance(user_id, 0) # İstifadəçini bazaya qeyd et
    bal = get_balance(user_id)
    
    # Sayta balansı və xidmətləri göndəririk
    services_data = get_panel_services()
    web_app_url_with_params = f"{WEB_APP_URL}?balance={bal}&services={json.dumps(services_data)}"

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Marketə Gir", web_app=WebAppInfo(url=web_app_url_with_params))],
        [
            InlineKeyboardButton(text="📢 Kanal", url=KANAL_LINK),
            InlineKeyboardButton(text="👨‍💻 Dəstək", url=DESTEK_LINK)
        ]
    ])
    
    caption = (
        f"<b>Salam, User! 👋

🚀 SMM PRO — Azərbaycanın ən sürətli platformasına xoş gəlmisən.

👇 Xidmətləri görmək üçün aşağıdakı düyməyə toxun:</b>\n\n"
        f"💰 Cari Balansın: <b>{bal:.2f} AZN</b>\n\n" # Balansı 2 onluqdan sonra göstərir
        f"Sosial media xidmətlərindən yararlanmaq üçün Marketə daxil ol."
    )
    
    await message.answer_photo(
        photo=PHOTO_URL,
        caption=caption,
        parse_mode="HTML",
        reply_markup=markup
    )

# Saytdan "qebz_atildi" siqnalı gələndə
@dp.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def web_app_received(message: types.Message):
    data = message.web_app_data.data
    
    if data == "qebz_atildi":
        await message.answer("📸 <b>Qəbz sistemi aktivdir!</b>\n\nZəhmət olmasa ödəniş qəbzinin şəklini bura göndərin. Admin təsdiqlədikdən sonra balansınız artacaq.")
    
    elif data.startswith("order_"):
        # Sifariş gələndə
        parts = data.split('_')
        service_id = parts[1]
        service_name = parts[2].replace('_', ' ')
        service_rate = float(parts[3])

        await message.answer(f"📦 <b>'{service_name}' xidməti üçün sifariş qəbul edildi.</b>\n\nİndi linki və miqdarı daxil edin (məsələn: `https://instagram.com/user 1000`):",
                             parse_mode="HTML",
                             reply_markup=ReplyKeyboardRemove()) # Klaviaturanı gizlədirik

        # İstifadəçi sifariş üçün cavabı gözləmək üçün state saxlaya bilərik (daha sonra)
        # Hələlik sadəcə cavab veririk
        # Real sifariş yerləşdirmə məntiqi bura yazılacaq


# Şəkil gələndə Adminə yönləndir
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Balans Artır", callback_data=f"approve_{message.from_user.id}")],
        [InlineKeyboardButton(text="❌ İmtina", callback_data=f"decline_{message.from_user.id}")]
    ])
    
    await bot.send_photo(
        ADMIN_ID, 
        photo=message.photo[-1].file_id, 
        caption=f"🔔 <b>YENİ QƏBZ!</b>\n👤 İstifadəçi: {message.from_user.first_name}\n🆔 ID: <code>{message.from_user.id}</code>",
        parse_mode="HTML",
        reply_markup=markup
    )
    await message.answer("✅ Qəbz adminə göndərildi. Zəhmət olmasa təsdiq gözləyin.")

# Admin təsdiqi üçün Callback
@dp.callback_query(F.data.startswith("approve_"))
async def approve_payment(call: types.CallbackQuery):
    user_id_to_update = int(call.data.split("_")[1])
    
    # Adminə məbləği soruşmaq üçün yeni klaviatura
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 AZN", callback_data=f"set_amount_{user_id_to_update}_1.00"),
         InlineKeyboardButton(text="5 AZN", callback_data=f"set_amount_{user_id_to_update}_5.00"),
         InlineKeyboardButton(text="10 AZN", callback_data=f"set_amount_{user_id_to_update}_10.00")],
        [InlineKeyboardButton(text="Digər Məbləğ", callback_data=f"prompt_amount_{user_id_to_update}")]
    ])
    
    await call.message.edit_caption(
        caption=f"✅ Qəbz təsdiqləndi. Balansa hansı məbləği əlavə edək?",
        reply_markup=markup
    )
    await call.answer()

# Admin məbləğ seçəndə
@dp.callback_query(F.data.startswith("set_amount_"))
async def set_predefined_amount(call: types.CallbackQuery):
    parts = call.data.split("_")
    user_id = int(parts[2])
    amount = float(parts[3])
    
    update_balance(user_id, amount)
    await bot.send_message(user_id, f"✅ Balansınız <b>{amount:.2f} AZN</b> artırıldı! Cari balansınız: <b>{get_balance(user_id):.2f} AZN</b>", parse_mode="HTML")
    await call.message.edit_caption(caption=f"✅ Balans {user_id} üçün {amount:.2f} AZN artırıldı.")
    await call.answer()

# Admin özü məbləğ yazmaq istəyəndə
@dp.callback_query(F.data.startswith("prompt_amount_"))
async def prompt_custom_amount(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])
    # Bu hissə daha mürəkkəbdir, çünki bot adminin cavabını gözləməlidir (state istifadəsi)
    # Hələlik sadə cavab verək
    await call.message.edit_caption(caption="Custom məbləğ qəbulu hazır deyil. Zəhmət olmasa yuxarıdakı hazır düymələrdən istifadə edin.")
    await call.answer("Bu funksiya hələlik aktiv deyil.")

# --- RENDER ÜÇÜN PORT ---
@app.route('/')
def home(): return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def main():
    init_db()
    threading.Thread(target=run_flask).start()
    print("Sistem işə düşdü...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
