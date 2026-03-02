import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# BU İKİ SATIRI KENDİNE GÖRE DÜZENLE ⬇️
BOT_TOKEN = "8401084300:AAEjWNpxFHkO_0vlgCQv-hx5j8ISpnO2bQM"  # Token doğru
ADMIN_ID = 8566739483  # BURAYI KENDİ TELEGRAM ID'İNLE DEĞİŞTİR!

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Basit veritabanı
users = {}  # {user_id: {'points': 0, 'referrals': 0, 'name': ''}}
products = []  # {'id': 1, 'name': 'Ürün', 'price': 100, 'stock': 10}
next_product_id = 1

# Yeni eklenen veritabanları
forced_channels = []  # Zorunlu kanallar listesi [{'chat_id': -100123, 'name': 'Kanal Adı', 'link': 'https://t.me/...'}]
authorized_users = [ADMIN_ID]  # Yetkili kullanıcılar listesi (admin her zaman yetkili)

# Admin paneli için geçici veri
admin_data = {}

# Kanal kontrolü
async def check_channels(user_id, context):
    """Kullanıcının zorunlu kanallara katılıp katılmadığını kontrol eder"""
    if not forced_channels:  # Zorunlu kanal yoksa True dön
        return True, []
    
    if user_id in authorized_users:  # Yetkili kullanıcılar için kontrol etme
        return True, []
    
    not_joined = []
    
    for channel in forced_channels:
        try:
            member = await context.bot.get_chat_member(chat_id=channel['chat_id'], user_id=user_id)
            if member.status in ['left', 'kicked']:
                not_joined.append(channel)
        except:
            # Kanal bulunamadı veya bot kanalda admin değil
            not_joined.append(channel)
    
    return len(not_joined) == 0, not_joined

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    
    # Zorunlu kanal kontrolü
    is_joined, not_joined = await check_channels(user.id, context)
    
    if not is_joined:
        keyboard = []
        for channel in not_joined:
            keyboard.append([InlineKeyboardButton(f"📢 {channel['name']}", url=channel['link'])])
        
        keyboard.append([InlineKeyboardButton("✅ Kontrol Et", callback_data="check_join")])
        
        await update.message.reply_text(
            "⚠️ *Botu kullanmak için aşağıdaki kanallara katılmalısın!*\n\n"
            "Kanallara katıldıktan sonra 'Kontrol Et' butonuna tıkla.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    # Yeni kullanıcı kaydı
    if user.id not in users:
        # Referans var mı?
        if args and args[0].isdigit():
            referrer_id = int(args[0])
            if referrer_id in users:
                users[referrer_id]['points'] += 10
                users[referrer_id]['referrals'] += 1
                # Bildirim gönder
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 {user.first_name} senin linkinle katıldı! +10 puan kazandın!"
                    )
                except:
                    pass
        
        # Yeni kullanıcıyı ekle
        users[user.id] = {
            'points': 0, 
            'referrals': 0, 
            'name': user.first_name
        }
    
    # Ana menü
    await ana_menu(update, context)

# Katılım kontrol butonu
async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    is_joined, not_joined = await check_channels(user_id, context)
    
    if is_joined:
        await query.edit_message_text("✅ Tüm kanallara katılmışsın! Ana menüye yönlendiriliyorsun...")
        # Kullanıcıyı kaydet (daha önce kayıtlı değilse)
        if user_id not in users:
            users[user_id] = {
                'points': 0, 
                'referrals': 0, 
                'name': query.from_user.first_name
            }
        await ana_menu(update, context)
    else:
        keyboard = []
        for channel in not_joined:
            keyboard.append([InlineKeyboardButton(f"📢 {channel['name']}", url=channel['link'])])
        
        keyboard.append([InlineKeyboardButton("🔄 Tekrar Kontrol Et", callback_data="check_join")])
        
        await query.edit_message_text(
            "⚠️ *Hala katılmadığın kanallar var!*\n\n"
            "Lütfen aşağıdaki kanallara katıl ve tekrar dene:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

# Ana menü
async def ana_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Zorunlu kanal kontrolü
    user_id = update.effective_user.id
    is_joined, not_joined = await check_channels(user_id, context)
    
    if not is_joined and user_id not in authorized_users:
        if update.message:
            await start(update, context)
        else:
            await check_join_callback(update, context)
        return
    
    # Mesaj mı buton mu?
    if update.message:
        msg = update.message
        is_message = True
    else:
        msg = update.callback_query
        is_message = False
        await msg.answer()
    
    # Kullanıcı bilgisi
    user_data = users.get(user_id, {'points': 0, 'referrals': 0})
    
    # Butonlar
    keyboard = [
        [InlineKeyboardButton("🔗 Referans Linkim", callback_data="link")],
        [InlineKeyboardButton("🛒 Market", callback_data="market")],
        [InlineKeyboardButton("📊 Profilim", callback_data="profil")],
    ]
    
    # Admin/Yetkili butonu
    if user_id in authorized_users:
        keyboard.append([InlineKeyboardButton("👑 Admin Paneli", callback_data="admin_panel")])
    
    keyboard.append([InlineKeyboardButton("❓ Yardım", callback_data="yardim")])
    
    text = (f"👋 Merhaba {update.effective_user.first_name}!\n\n"
            f"💰 Puanın: {user_data['points']}\n"
            f"👥 Referansların: {user_data['referrals']}\n\n"
            f"Ne yapmak istersin?")
    
    if is_message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Buton işlemleri
async def butonlar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Zorunlu kanal kontrolü
    user_id = query.from_user.id
    is_joined, not_joined = await check_channels(user_id, context)
    
    if not is_joined and user_id not in authorized_users and query.data != "check_join":
        await check_join_callback(update, context)
        return
    
    if query.data == "check_join":
        await check_join_callback(update, context)
    
    elif query.data == "link":
        bot = (await context.bot.get_me()).username
        link = f"https://t.me/{bot}?start={query.from_user.id}"
        
        keyboard = [[InlineKeyboardButton("◀️ Ana Menü", callback_data="menu")]]
        await query.edit_message_text(
            f"🔗 *REFERANS LİNKİN*\n\n`{link}`\n\n"
            f"Bu linki paylaş, her katılan için **10 puan** kazan!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif query.data == "profil":
        user = users.get(query.from_user.id, {'points': 0, 'referrals': 0, 'name': ''})
        yetki = "✅ Yetkili" if query.from_user.id in authorized_users else "❌ Normal Kullanıcı"
        text = (f"👤 *PROFİLİN*\n\n"
                f"İsim: {query.from_user.first_name}\n"
                f"ID: {query.from_user.id}\n"
                f"💰 Puan: {user['points']}\n"
                f"👥 Referans: {user['referrals']}\n"
                f"🔰 Yetki: {yetki}")
        
        keyboard = [[InlineKeyboardButton("◀️ Ana Menü", callback_data="menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif query.data == "market":
        await market_goster(query)
    
    elif query.data.startswith("urun_"):
        urun_id = int(query.data.split('_')[1])
        urun = next((u for u in products if u['id'] == urun_id), None)
        
        if urun:
            text = (f"📦 *{urun['name']}*\n\n"
                    f"💰 Fiyat: {urun['price']} puan\n"
                    f"📦 Stok: {urun['stock']}\n\n"
                    f"Satın almak istiyor musun?")
            
            keyboard = [
                [InlineKeyboardButton("✅ Satın Al", callback_data=f"satin_al_{urun_id}")],
                [InlineKeyboardButton("◀️ Markete Dön", callback_data="market")]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif query.data.startswith("satin_al_"):
        urun_id = int(query.data.split('_')[2])
        urun = next((u for u in products if u['id'] == urun_id), None)
        user = users.get(query.from_user.id, {'points': 0})
        
        if urun and user['points'] >= urun['price'] and urun['stock'] > 0:
            # Puan düş, stok azalt
            user['points'] -= urun['price']
            urun['stock'] -= 1
            
            await query.edit_message_text(
                f"✅ *Satın Alma Başarılı!*\n\n"
                f"Ürün: {urun['name']}\n"
                f"Harcanan: {urun['price']} puan\n"
                f"Kalan puanın: {user['points']}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🛒 Markete Dön", callback_data="market"),
                    InlineKeyboardButton("🏠 Ana Menü", callback_data="menu")
                ]]),
                parse_mode='Markdown'
            )
            
            # Admin'lere bildirim
            for admin_id in authorized_users:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"🛒 YENİ SİPARİŞ!\n\n"
                             f"👤 {query.from_user.first_name} (@{query.from_user.username})\n"
                             f"📦 {urun['name']}\n"
                             f"💰 {urun['price']} puan"
                    )
                except:
                    pass
        else:
            if user['points'] < urun['price']:
                hata = "Yetersiz puan! Daha fazla arkadaş davet et."
            elif urun['stock'] <= 0:
                hata = "Ürün stokta yok!"
            else:
                hata = "Satın alma başarısız!"
            
            await query.edit_message_text(
                f"❌ *{hata}*",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🛒 Markete Dön", callback_data="market")
                ]]),
                parse_mode='Markdown'
            )
    
    elif query.data == "yardim":
        text = ("❓ *YARDIM*\n\n"
                "📌 *Nasıl puan kazanırım?*\n"
                "• Referans linkini arkadaşlarına gönder\n"
                "• Her katılan için **10 puan** kazan\n\n"
                "📌 *Nasıl harcarım?*\n"
                "• Marketten ürün satın al\n"
                "• Puanların düşer, ürünü alırsın\n\n"
                "📌 *Komutlar*\n"
                "/start - Ana menü")
        
        keyboard = [[InlineKeyboardButton("◀️ Ana Menü", callback_data="menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif query.data == "admin_panel":
        if query.from_user.id not in authorized_users:
            await query.edit_message_text("🚫 Bu bölüme erişim yetkin yok!")
            return
        
        keyboard = [
            [InlineKeyboardButton("📦 Ürün Ekle", callback_data="admin_urun_ekle")],
            [InlineKeyboardButton("🗑 Ürün Sil", callback_data="admin_urun_sil")],
            [InlineKeyboardButton("📋 Ürünleri Listele", callback_data="admin_urun_liste")],
            [InlineKeyboardButton("📢 Zorunlu Kanal", callback_data="admin_kanal_menu")],
            [InlineKeyboardButton("👥 Yetki Yönetimi", callback_data="admin_yetki_menu")],
            [InlineKeyboardButton("📊 İstatistik", callback_data="admin_istatistik")],
            [InlineKeyboardButton("◀️ Ana Menü", callback_data="menu")]
        ]
        await query.edit_message_text(
            "👑 *ADMIN PANELİ*\n\nYapmak istediğin işlemi seç:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # YETKİ YÖNETİMİ MENÜSÜ
    elif query.data == "admin_yetki_menu":
        if query.from_user.id not in authorized_users:
            return
        
        yetkililer_text = "👥 *YETKİLİ KULLANICILAR*\n\n"
        for yetkili_id in authorized_users:
            user_info = users.get(yetkili_id, {})
            isim = user_info.get('name', 'Bilinmiyor')
            yetkililer_text += f"• {isim} - `{yetkili_id}`\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Yetki Ver", callback_data="admin_yetki_ver")],
            [InlineKeyboardButton("➖ Yetki Al", callback_data="admin_yetki_al")],
            [InlineKeyboardButton("◀️ Admin Paneli", callback_data="admin_panel")]
        ]
        await query.edit_message_text(
            yetkililer_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif query.data == "admin_yetki_ver":
        if query.from_user.id not in authorized_users:
            return
        
        admin_data[query.from_user.id] = {'action': 'yetki_ver'}
        await query.edit_message_text(
            "👥 *YETKİ VER*\n\n"
            "Yetki vermek istediğin kullanıcının ID'sini yaz:",
            parse_mode='Markdown'
        )
    
    elif query.data == "admin_yetki_al":
        if query.from_user.id not in authorized_users:
            return
        
        if len(authorized_users) <= 1:
            await query.edit_message_text(
                "❌ Son yetkiliyi silemezsin! En az bir yetkili olmalı.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Yetki Menüsü", callback_data="admin_yetki_menu")
                ]])
            )
            return
        
        admin_data[query.from_user.id] = {'action': 'yetki_al'}
        await query.edit_message_text(
            "👥 *YETKİ AL*\n\n"
            "Yetkisini almak istediğin kullanıcının ID'sini yaz:",
            parse_mode='Markdown'
        )
    
    # ZORUNLU KANAL MENÜSÜ
    elif query.data == "admin_kanal_menu":
        if query.from_user.id not in authorized_users:
            return
        
        kanal_text = "📢 *ZORUNLU KANALLAR*\n\n"
        if not forced_channels:
            kanal_text += "Hiç zorunlu kanal eklenmemiş."
        else:
            for i, kanal in enumerate(forced_channels, 1):
                kanal_text += f"{i}. {kanal['name']} - `{kanal['chat_id']}`\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Kanal Ekle", callback_data="admin_kanal_ekle")],
            [InlineKeyboardButton("➖ Kanal Sil", callback_data="admin_kanal_sil")],
            [InlineKeyboardButton("◀️ Admin Paneli", callback_data="admin_panel")]
        ]
        await query.edit_message_text(
            kanal_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif query.data == "admin_kanal_ekle":
        if query.from_user.id not in authorized_users:
            return
        
        admin_data[query.from_user.id] = {'action': 'kanal_id'}
        await query.edit_message_text(
            "📢 *KANAL EKLE - 1/3*\n\n"
            "Kanalın ID'sini yaz (örn: -100123456789):\n\n"
            "⚠️ *ÖNEMLİ:* Botu kanalda admin yapmayı unutma!",
            parse_mode='Markdown'
        )
    
    elif query.data == "admin_kanal_sil":
        if query.from_user.id not in authorized_users:
            return
        
        if not forced_channels:
            await query.edit_message_text(
                "📢 Silinecek kanal yok!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Kanal Menüsü", callback_data="admin_kanal_menu")
                ]])
            )
            return
        
        text = "🗑 *SİLİNECEK KANALI SEÇ*\n\n"
        keyboard = []
        
        for i, kanal in enumerate(forced_channels):
            text += f"{i+1}. {kanal['name']}\n"
            keyboard.append([InlineKeyboardButton(
                f"❌ {kanal['name'][:20]}", 
                callback_data=f"kanal_sil_{i}"
            )])
        
        keyboard.append([InlineKeyboardButton("◀️ Kanal Menüsü", callback_data="admin_kanal_menu")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif query.data.startswith("kanal_sil_"):
        if query.from_user.id not in authorized_users:
            return
        
        index = int(query.data.split('_')[2])
        if 0 <= index < len(forced_channels):
            silinen = forced_channels.pop(index)
            await query.edit_message_text(
                f"✅ *Kanal Silindi!*\n\n"
                f"Kanal: {silinen['name']}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Kanal Menüsü", callback_data="admin_kanal_menu")
                ]]),
                parse_mode='Markdown'
            )
    
    elif query.data == "admin_urun_liste":
        if query.from_user.id not in authorized_users:
            return
        
        if not products:
            text = "📦 *ÜRÜNLER*\n\nHiç ürün eklenmemiş."
        else:
            text = "📦 *ÜRÜN LİSTESİ*\n\n"
            for urun in products:
                text += f"🆔 {urun['id']} | {urun['name']} | {urun['price']} puan | Stok: {urun['stock']}\n"
        
        keyboard = [[InlineKeyboardButton("◀️ Admin Paneli", callback_data="admin_panel")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif query.data == "admin_urun_ekle":
        if query.from_user.id not in authorized_users:
            return
        
        admin_data[query.from_user.id] = {'action': 'urun_adi'}
        await query.edit_message_text(
            "📦 *ÜRÜN EKLE*\n\n1/4 - Ürün adını yaz:",
            parse_mode='Markdown'
        )
    
    elif query.data == "admin_urun_sil":
        if query.from_user.id not in authorized_users:
            return
        
        if not products:
            await query.edit_message_text(
                "📦 Silinecek ürün yok!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Admin Paneli", callback_data="admin_panel")
                ]])
            )
            return
        
        text = "🗑 *SİLİNECEK ÜRÜNÜ SEÇ*\n\n"
        keyboard = []
        
        for urun in products:
            text += f"🆔 {urun['id']} | {urun['name']} | {urun['price']} puan\n"
            keyboard.append([InlineKeyboardButton(
                f"❌ {urun['name']}", 
                callback_data=f"sil_onay_{urun['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("◀️ Admin Paneli", callback_data="admin_panel")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif query.data.startswith("sil_onay_"):
        if query.from_user.id not in authorized_users:
            return
        
        urun_id = int(query.data.split('_')[2])
        
        for i, urun in enumerate(products):
            if urun['id'] == urun_id:
                products.pop(i)
                break
        
        await query.edit_message_text(
            "✅ Ürün başarıyla silindi!",
   reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Admin Paneli", callback_data="admin_panel")
            ]])
        )
    
    elif query.data == "admin_istatistik":
        if query.from_user.id not in authorized_users:
            return
        
        toplam_kullanici = len(users)
        toplam_puan = sum(u['points'] for u in users.values())
        toplam_referans = sum(u['referrals'] for u in users.values())
        toplam_urun = len(products)
        toplam_kanal = len(forced_channels)
        toplam_yetkili = len(authorized_users)
        
        text = (f"📊 *İSTATİSTİKLER*\n\n"
                f"👥 Toplam Kullanıcı: {toplam_kullanici}\n"
                f"💰 Toplam Puan: {toplam_puan}\n"
                f"🔄 Toplam Referans: {toplam_referans}\n"
                f"📦 Toplam Ürün: {toplam_urun}\n"
                f"📢 Zorunlu Kanal: {toplam_kanal}\n"
                f"👑 Yetkili Sayısı: {toplam_yetkili}")
        
        keyboard = [[InlineKeyboardButton("◀️ Admin Paneli", callback_data="admin_panel")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif query.data == "menu":
        await ana_menu(update, context)

# Marketi göster
async def market_goster(query):
    if not products:
        text = "🛒 *MARKET*\n\nŞu anda satın alınabilecek ürün bulunmuyor."
        keyboard = [[InlineKeyboardButton("◀️ Ana Menü", callback_data="menu")]]
    else:
        text = "🛒 *MARKET*\n\nSatın almak istediğin ürünü seç:\n\n"
        keyboard = []
        
        for urun in products:
            text += f"• {urun['name']} - {urun['price']} puan (Stok: {urun['stock']})\n"
            keyboard.append([InlineKeyboardButton(
                f"📦 {urun['name']} - {urun['price']} puan", 
                callback_data=f"urun_{urun['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("◀️ Ana Menü", callback_data="menu")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# Mesajları işle (admin ürün ekleme, yetki verme, kanal ekleme için)
async def mesaj_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    # Yetkili mi kontrol et
    if user_id not in authorized_users:
        return
    
    # Admin işlemi var mı?
    if user_id not in admin_data:
        return
    
    action = admin_data[user_id].get('action')
    
    # YETKİ VERME İŞLEMLERİ
    if action == 'yetki_ver':
        try:
            yetkili_id = int(text.strip())
            if yetkili_id in authorized_users:
                await update.message.reply_text("❌ Bu kullanıcı zaten yetkili!")
            else:
                authorized_users.append(yetkili_id)
                # Kullanıcıyı users'a ekle (yoksa)
                if yetkili_id not in users:
                    try:
                        user = await context.bot.get_chat(yetkili_id)
                        users[yetkili_id] = {
                            'points': 0,
                            'referrals': 0,
                            'name': user.first_name
                        }
                    except:
                        users[yetkili_id] = {
                            'points': 0,
                            'referrals': 0,
                            'name': 'Bilinmiyor'
                        }
                
                await update.message.reply_text(
                    f"✅ *Yetki Verildi!*\n\n"
                    f"ID: `{yetkili_id}` artık yetkili.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("👥 Yetki Menüsü", callback_data="admin_yetki_menu")
                    ]]),
                    parse_mode='Markdown'
                )
            del admin_data[user_id]
        except:
            await update.message.reply_text("❌ Hatalı ID! Lütfen geçerli bir sayı girin:")
    
    elif action == 'yetki_al':
        try:
            yetkili_id = int(text.strip())
            if yetkili_id == ADMIN_ID:
                await update.message.reply_text("❌ Ana adminin yetkisini alamazsın!")
            elif yetkili_id not in authorized_users:
                await update.message.reply_text("❌ Bu ID yetkili değil!")
            else:
                authorized_users.remove(yetkili_id)
                await update.message.reply_text(
                    f"✅ *Yetki Alındı!*\n\n"
                    f"ID: `{yetkili_id}` artık yetkili değil.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("👥 Yetki Menüsü", callback_data="admin_yetki_menu")
                    ]]),
                    parse_mode='Markdown'
                )
            del admin_data[user_id]
        except:
            await update.message.reply_text("❌ Hatalı ID! Lütfen geçerli bir sayı girin:")
    
    # ZORUNLU KANAL EKLEME İŞLEMLERİ
    elif action == 'kanal_id':
        try:
            kanal_id = int(text.strip())
            admin_data[user_id]['kanal_id'] = kanal_id
            admin_data[user_id]['action'] = 'kanal_adi'
            await update.message.reply_text("✅ 2/3 - Kanalın adını yaz:")
        except:
            await update.message.reply_text("❌ Hatalı ID! Lütfen geçerli bir kanal ID'si girin:")
    
    elif action == 'kanal_adi':
        kanal_adi = text
        admin_data[user_id]['kanal_adi'] = kanal_adi
        admin_data[user_id]['action'] = 'kanal_link'
        await update.message.reply_text("✅ 3/3 - Kanalın davet linkini yaz (örn: https://t.me/...):")
    
    elif action == 'kanal_link':
        kanal_link = text
        kanal_id = admin_data[user_id]['kanal_id']
        kanal_adi = admin_data[user_id]['kanal_adi']
        
        # Kanalı ekle
        forced_channels.append({
            'chat_id': kanal_id,
            'name': kanal_adi,
            'link': kanal_link
        })
        
        # Admin data'yı temizle
        del admin_data[user_id]
        
        await update.message.reply_text(
            f"✅ *Kanal Başarıyla Eklendi!*\n\n"
            f"📢 {kanal_adi}\n"
            f"🆔 `{kanal_id}`",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Kanal Menüsü", callback_data="admin_kanal_menu"),
                InlineKeyboardButton("👑 Admin Paneli", callback_data="admin_panel")
            ]]),
            parse_mode='Markdown'
        )
    
    # ÜRÜN EKLEME İŞLEMLERİ
    elif action == 'urun_adi':
        admin_data[user_id]['urun_adi'] = text
        admin_data[user_id]['action'] = 'urun_fiyat'
        await update.message.reply_text("✅ 2/4 - Ürün fiyatını (puan olarak) yaz (Sadece sayı):")
    
    elif action == 'urun_fiyat':
        try:
            fiyat = int(text)
            admin_data[user_id]['urun_fiyat'] = fiyat
            admin_data[user_id]['action'] = 'urun_stok'
            await update.message.reply_text("✅ 3/4 - Ürün stok miktarını yaz (Sadece sayı):")
        except:
            await update.message.reply_text("❌ Hatalı giriş! Lütfen sayı girin:")
    
    elif action == 'urun_stok':
        try:
            stok = int(text)
            admin_data[user_id]['urun_stok'] = stok
            
            # Ürünü ekle
            global next_product_id, products
            yeni_urun = {
                'id': next_product_id,
                'name': admin_data[user_id]['urun_adi'],
                'price': admin_data[user_id]['urun_fiyat'],
                'stock': stok
            }
            products.append(yeni_urun)
            next_product_id += 1
            
            # Admin data'yı temizle
            del admin_data[user_id]
            
            # Başarılı mesajı
            keyboard = [[
                InlineKeyboardButton("📦 Ürün Ekle", callback_data="admin_urun_ekle"),
                InlineKeyboardButton("👑 Admin Paneli", callback_data="admin_panel")
            ]]
            
            await update.message.reply_text(
                f"✅ *Ürün Başarıyla Eklendi!*\n\n"
                f"📦 {yeni_urun['name']}\n"
                f"💰 {yeni_urun['price']} puan\n"
                f"📊 Stok: {yeni_urun['stock']}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except:
            await update.message.reply_text("❌ Hatalı giriş! Lütfen sayı girin:")

# Ana fonksiyon
def main():
    print("🚀 Bot başlatılıyor...")
    print(f"🤖 Token: {BOT_TOKEN[:10]}...")
    print(f"👑 Admin ID: {ADMIN_ID} (BUNU DEĞİŞTİRMEYİ UNUTMA!)")
    
    # Örnek ürünler
    global products, next_product_id
    products = [
        {'id': 1, 'name': '🎁 Hediye Kartı', 'price': 50, 'stock': 10},
        {'id': 2, 'name': '📱 Premium Üyelik', 'price': 100, 'stock': 5},
        {'id': 3, 'name': '☕ Kahve Kuponu', 'price': 25, 'stock': 20},
    ]
    next_product_id = 4
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(butonlar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj_handler))
    
    print("✅ Bot çalışıyor! Telegram'da @botunu dene")
    print("📦 Hazır ürünler eklendi!")
    print("📢 Zorunlu kanal özelliği aktif!")
    print("👥 Yetki yönetimi eklendi!")
    app.run_polling()

if __name__ == '__main__':
    main()
