import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# MƏLUMATLARI BURA DAXİL ET
TOKEN = "8401084300:AAEons4Amc0jb1uY9W6hervg2ut22u6Dnkg"
ADMIN_ID = 8566739483  # @userinfobot-dan aldığın ID
WEB_APP_URL = "https://omer316972.github.io/Smm-Market/"
KANAL_LINK = "https://t.me/TapBaxaq"
DESTEK_LINK = "https://t.me/TapBaxaq"
PHOTO_URL = "https://img.freepik.com/free-vector/gradient-social-media-marketing-concept_23-2149021820.jpg"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- BOTUN ƏMRLƏRİ ---
@dp.message(CommandStart())
async def start(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Market (Veb Tətbiq)", web_app=WebAppInfo(url=WEB_APP_URL))],
        [
            InlineKeyboardButton(text="📢 Kanalımız", url=KANAL_LINK),
            InlineKeyboardButton(text="👨‍💻 Dəstək", url=DESTEK_LINK)
        ]
    ])
    
    caption = (
        f"<b>Salam, {message.from_user.first_name}! 👋</b>\n\n"
        "🚀 <b>SMM PRO</b> — Azərbaycanın ən sürətli platformasına xoş gəlmisən.\n\n"
        "👇 Xidmətləri görmək üçün aşağıdakı düyməyə toxun:"
    )
    
    await message.answer_photo(photo=PHOTO_URL, caption=caption, parse_mode="HTML", reply_markup=markup)

@dp.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def get_web_app_data(message: types.Message):
    if message.web_app_data.data == "qebz_atildi":
        await bot.send_message(ADMIN_ID, f"🔔 <b>YENİ QƏBZ!</b>\n👤: {message.from_user.first_name}\n🆔: <code>{message.from_user.id}</code>", parse_mode="HTML")

# --- RENDER ÜÇÜN PORTU "ALDADAN" HİSSƏ ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render-in verdiyi portu götürür, yoxdursa 10000 istifadə edir
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server {port} portunda işə düşdü.")

async def main():
    # Həm botu, həm də veb serveri eyni vaxtda başladırıq
    await asyncio.gather(
        dp.start_polling(bot),
        start_web_server()
    )

if __name__ == "__main__":
    asyncio.run(main())
