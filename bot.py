import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# MƏLUMATLARI BURA DAXİL ET
TOKEN = "8401084300:AAEons4Amc0jb1uY9W6hervg2ut22u6Dnkg"
ADMIN_ID = 8566739483  # @userinfobot-dan aldığın ID
WEB_APP_URL = "https://omer316972/Smm-Market.github.io/repo-adın/"
KANAL_LINK = "https://t.me/TapBaxaq" # Öz kanalın
DESTEK_LINK = "https://t.me/TapBaxaq" # Öz profilin
# Qəşəng bir SMM şəkli (və ya öz loqonun linki)
PHOTO_URL = "https://img.freepik.com/free-vector/gradient-social-media-marketing-concept_23-2149021820.jpg"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    # Düymələrin qurulması
    markup = InlineKeyboardMarkup(inline_keyboard=[
        # Market düyməsi (Veb-tətbiqi açır)
        [InlineKeyboardButton(text="🚀 Market (Veb Tətbiq)", web_app=WebAppInfo(url=WEB_APP_URL))],
        
        # Kanalımız və Dəstək düymələri yanaşı
        [
            InlineKeyboardButton(text="📢 Kanalımız", url=KANAL_LINK),
            InlineKeyboardButton(text="👨‍💻 Dəstək", url=DESTEK_LINK)
        ]
    ])
    
    # Şəkilli və Səliqəli Xoş Gəldin Mesajı
    caption = (
        f"<b>Salam, {message.from_user.first_name}! 👋</b>\n\n"
        "🚀 <b>SMM PRO</b> — Azərbaycanın ən sürətli və keyfiyyətli SMM xidmətləri platformasına xoş gəlmisən.\n\n"
        "✨ <b>Niyə biz?</b>\n"
        "├ ⚡ Avtomatik sifarişlər\n"
        "├ 💰 Sərfəli qiymətlər\n"
        "└ 🛠 7/24 Dəstək\n\n"
        "👇 Xidmətləri görmək üçün aşağıdakı düyməyə toxun:"
    )
    
    await message.answer_photo(
        photo=PHOTO_URL,
        caption=caption,
        parse_mode="HTML",
        reply_markup=markup
    )

# Qəbz gələndə sənə bildiriş atması üçün
@dp.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def get_web_app_data(message: types.Message):
    if message.web_app_data.data == "qebz_atildi":
        await bot.send_message(
            ADMIN_ID, 
            f"🔔 <b>YENİ QƏBZ!</b>\n\n"
            f"👤 İstifadəçi: {message.from_user.first_name}\n"
            f"🆔 ID: <code>{message.from_user.id}</code>\n\n"
            f"⚠️ Müştəri qəbzi yüklədi, zəhmət olmasa təsdiqləyin.",
            parse_mode="HTML"
        )

async def main():
    print("Bot aktivdir...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
