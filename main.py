import http.server
import socketserver
import os
import threading

def run_http():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_http, daemon=True).start()

import telebot
from telebot import types
import random
import threading
import sqlite3

# ==================== BOT TOKEN ====================
TOKEN = "8816866283:AAERGz-96nCntew0kl3uwM8vauL7X4OskTs"
bot = telebot.TeleBot(TOKEN)

# ==================== DATABASE SETUP ====================
conn = sqlite3.connect('deathnote.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    coins INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    mvp_count INTEGER DEFAULT 0
)
''')
conn.commit()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN mvp_count INTEGER DEFAULT 0")
    conn.commit()
except sqlite3.OperationalError:
    pass

def get_user_data(user_id):
    cursor.execute("SELECT coins, wins, mvp_count FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row if row else (0, 0, 0)

def add_coins(user_id, amount):
    cursor.execute("INSERT INTO users (user_id, coins) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET coins = coins + ?", (user_id, amount, amount))
    conn.commit()

def add_win_and_mvp(user_id, is_mvp=False):
    mvp_add = 1 if is_mvp else 0
    coin_add = 250 if is_mvp else 120
    cursor.execute('''
        INSERT INTO users (user_id, wins, coins, mvp_count) 
        VALUES (?, 1, ?, ?) 
        ON CONFLICT(user_id) DO UPDATE SET 
        wins = wins + 1, 
        coins = coins + ?, 
        mvp_count = mvp_count + ?
    ''', (user_id, coin_add, mvp_add, coin_add, mvp_add))
    conn.commit()

def get_top_players():
    cursor.execute("SELECT username, wins, mvp_count, coins FROM users ORDER BY wins DESC, mvp_count DESC LIMIT 10")
    return cursor.fetchall()

# ==================== MEDIA FILE_ID LAR ====================
PHOTO_GAME_START = "AgACAgIAAxkBAAMPamJwOOS7vpcTsjE2wjtqLxTKQWQAAhQcaxv2HBFLdKBHTx5OW6cBAAMCAAN4AAM9BA"
PHOTO_KIRA_ROLE  = "BAACAgIAAxkBAAMcamJ2S3RDkOHzMgwXcFQuahhDNc8AAl6tAAL2HBFLTNcDtV99xyU9BA"
PHOTO_L_ROLE     = "AgACAgIAAxkBAAMSamJzPlzJ8Vht7_zYVmzsBwNLlSoAAhIcaxv2HBFLFZlvUkw9Nx4BAAMCAAN5AAM9BA"
PHOTO_POLICE     = "AgACAgIAAxkBAAMUamJ0JKq-sx2bhPVflNJ0fJb4DD0AAmEcaxv2HBFLZGNsgj_3J5kBAAMCAAN4AAM9BA"
PHOTO_MISA_ROLE  = "AgACAgIAAxkBAAMkamJ4ZBZIl4-VcYXZaHVvrs3isecAAnAcaxv2HBFLsEDasimDS4oBAAMCAAN4AAM9BA"

VIDEO_NIGHT_START = "BAACAgIAAxkBAAMaamJ17Ee9A_5ehiz0HAF-gAwvvToAAlitAAL2HBFLoBuHQApaPpg9BA"
VIDEO_KIRA_WIN    = "BAACAgIAAxkBAAMYamJ1lxVdkfIW81REYjNOXq_l1vEAAlStAAL2HBFLWFhMxDEzLXg9BA"
VIDEO_L_LOGO      = "BAACAgIAAxkBAAMeamJ2mz6NydCnCs183y3thz9Mu0IAAmKtAAL2HBFL94UgMhy-12I9BA"

games = {}
user_inventory = {}

# ==================== COMMANDS ====================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📜 Qoidalar", callback_data="show_rules"),
        types.InlineKeyboardButton("🎭 Rollar & Info", callback_data="show_roles")
    )
    bot.send_message(
        message.chat.id, 
        "📓 **Death Note: Yashirin Hukm**\n\nXush kelibsiz! /roles, /profile, /inventory, /top va /shop komandalaridan foydalanishingiz mumkin! 🔥", 
        parse_mode="Markdown",
        reply_markup=kb
    )

@bot.message_handler(commands=['roles'])
def roles_cmd(message):
    roles_info = (
        "🎭 **STRATEGIK PERSONAJLAR BAZASI:**\n\n"
        "📓 **Kira (Light):** Tunda 1 kishini o'ldiradi.\n"
        "🕵️‍♂️ **L (Lawliet):** Tunda 1 kishining faoliyatini tekshiradi.\n"
        "👁 **Misa Amane:** Shinigami ko'zlari bilan L kimligini qidiradi.\n"
        "🍫 **Mello:** Tunda 1 kishining tungi xususiyatini bloklaydi.\n"
        "🛡 **Soichiro Yagami:** Tunda 1 kishini Kiraning hujumidan saqlaydi.\n"
        "⚖️ **Teru Mikami:** Kira o'lsa, yangi Kira bo'ladi!\n"
        "🔫 **Matsuda:** Kunduzi 1 marta shubhali kishini otishi mumkin.\n"
        "📢 **Takada:** Ovoz berish jarayonida uning ovozi 2x hisoblanadi.\n"
        "🍏 **Ryuk:** Neytral. O'yinda o'lmaydi, tirik qolsa g'olib bo'ladi!\n"
        "👤 **Oddiy Aholi:** Tungi kuchi yo'q, lekin muhokama va ovoz berishda asosiy rol o'ynaydi!"
    )
    bot.reply_to(message, roles_info, parse_mode="Markdown")

@bot.message_handler(commands=['profile'])
def profile_cmd(message):
    coins, wins, mvp = get_user_data(message.from_user.id)
    bot.reply_to(message, f"👤 **Sizning Profilingiz:**\n\n🪙 L-Coins: {coins}\n🏆 G'alabalar: {wins}\n🌟 MVP Unvoni: {mvp} marta")

@bot.message_handler(commands=['inventory'])
def inventory_cmd(message):
    inv = user_inventory.get(message.from_user.id, {})
    apple = "✅ Bor" if inv.get('apple') else "❌ Yo'q"
    eyes = "✅ Bor" if inv.get('shinigami_eyes') else "❌ Yo'q"
    bot.reply_to(message, f"🎒 **Sizning Inventaringiz:**\n\n🍏 Ryuk Olmasi: {apple}\n👁 Shinigami Ko'zi: {eyes}")

@bot.message_handler(commands=['top'])
def top_cmd(message):
    top_list = get_top_players()
    if not top_list:
        bot.reply_to(message, "🏆 Reyting hali bo'sh!")
        return
    
    text = "🏆 **ENG ZO'R DETEKTIVLAR VA KIRALAR (TOP-10):**\n\n"
    for i, row in enumerate(top_list, 1):
        name = row[0] if row[0] else "Noma'lum"
        wins, mvp, coins = row[1], row[2], row[3]
        text += f"{i}. {name} - 🥇 {wins} G'alaba | 🌟 {mvp} MVP | 🪙 {coins} Coins\n"
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['shop'])
def shop_cmd(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🍏 Ryuk Olmasi (300 Coin)", callback_data="buy_apple"))
    kb.add(types.InlineKeyboardButton("👁 Shinigami Ko'zlari (500 Coin)", callback_data="buy_eyes"))
    bot.send_message(message.chat.id, "🛒 **Death Note Magazini:**", reply_markup=kb)

@bot.message_handler(commands=['stopgame', 'cancel'])
def stopgame_cmd(message):
    chat_id = message.chat.id
    if chat_id in games:
        del games[chat_id]
        bot.reply_to(message, "🛑 **O'yin majburiy ravishda to'xtatildi!**")
    else:
        bot.reply_to(message, "❌ Hozirda faol o'yin yo'q.")

@bot.message_handler(commands=['create'])
def create_game(message):
    chat_id = message.chat.id
    if message.chat.type == "private":
        bot.reply_to(message, "❌ Boshlash uchun botni guruhga qo'shing!")
        return

    games[chat_id] = {
        'status': 'waiting',
        'players': {},
        'roles': {},
        'alive': [],
        'votes': {},
        'night_actions': {'kill': None, 'check_l': None, 'protect': None, 'block': None, 'misa_search': None},
        'matsuda_shot': False,
        'activity': {}
    }

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✋ O'yinga Qo'shilish", callback_data="join_game"))
    kb.add(types.InlineKeyboardButton("🚀 O'yinni Boshlash", callback_data="start_game"))

    caption_text = "📓 **Yangi Death Note O'yini Yaratildi!**\n\nQatnashish uchun 'O'yinga Qo'shilish' tugmasini bosing."

    if PHOTO_GAME_START:
        try:
            bot.send_photo(chat_id, PHOTO_GAME_START, caption=caption_text, reply_markup=kb, parse_mode="Markdown")
            return
        except Exception:
            pass
 bot.send_message(chat_id, caption_text, reply_markup=kb, parse_mode="Markdown")
def start_night(chat_id):
    game = games.get(chat_id)
    if not game:
        return

    # Tungi harakatlarni nolga tushiramiz
    game['night_actions'] = {'kill': None, 'check_l': None, 'protect': None, 'block': None, 'misa_search': None}

    bot.send_message(chat_id, "🌙 **TUN TUSHDI!**\n\nHamma shahr ahli uquvda... Faol rollar shaxsiy chatda o'z harakatini bajarsin!", parse_mode="Markdown")

    # Har bir tirik o'yinchiga rolga mos tugmalarni yuboramiz
    for player_id in game['alive']:
        role = game['roles'].get(player_id)

        # 📓 KIRA UCHUN TUGMALAR:
        if role == "Kira":
            kb = types.InlineKeyboardMarkup(row_width=1)
            for target_id in game['alive']:
                if target_id != player_id: # O'zini o'ldira olmaydi
                    p_name = game['players'][target_id]
                    kb.add(types.InlineKeyboardButton(f"🗡 {p_name}ni o'ldirish", callback_data=f"kill_{chat_id}_{target_id}"))
            
            try:
                bot.send_message(player_id, "📓 **Death Note:** Bugun tunda kimning ismini daftarga yozasiz?", reply_markup=kb)
            except Exception:
                pass

        # 🕵️‍♂️ L UCHUN TUGMALAR:
        elif role == "L":
            kb = types.InlineKeyboardMarkup(row_width=1)
            for target_id in game['alive']:
                if target_id != player_id:
                    p_name = game['players'][target_id]
                    kb.add(types.InlineKeyboardButton(f"🔍 {p_name}ni tekshirish", callback_data=f"checkl_{chat_id}_{target_id}"))
            
            try:
                bot.send_message(player_id, "🕵️‍♂️ **L:** Kimni shubhali deb hisobleysiz va tekshirmoqchisiz?", reply_markup=kb)
            except Exception:
                pass
                
# ==================== CALLBACK HANDLER ====================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    user_name = call.from_user.first_name
    data = call.data

    if data == "buy_apple":
        coins, _, _ = get_user_data(user_id)
        if coins >= 300:
            add_coins(user_id, -300)
            user_inventory[user_id] = user_inventory.get(user_id, {})
            user_inventory[user_id]['apple'] = True
            bot.answer_callback_query(call.id, "✅ Ryuk Olmasi olindi!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ L-Coin yetarli emas!", show_alert=True)
        return

    elif data == "buy_eyes":
        coins, _, _ = get_user_data(user_id)
        if coins >= 500:
            add_coins(user_id, -500)
            user_inventory[user_id] = user_inventory.get(user_id, {})
            user_inventory[user_id]['shinigami_eyes'] = True
            bot.answer_callback_query(call.id, "✅ Shinigami Ko'zlari olindi!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ L-Coin yetarli emas!", show_alert=True)
        return

    if call.data == "show_rules":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "📜 **O'YIN QOIDALARI:**\n\n1. Tun tushganda faol roldagilar o'z harakatini shaxsiy chatda qiladi.\n2. Kun botganda guruhda hamma muhokama qiladi va shubhali odamga ovoz beradi.", parse_mode="Markdown")

    elif call.data == "show_roles":
        bot.answer_callback_query(call.id)
        roles_cmd(call.message)

    elif call.data == "join_game":
        game = games.get(chat_id)
        if game and game['status'] == 'waiting' and user_id not in game['players']:
            game['players'][user_id] = user_name
            game['activity'][user_id] = 0
            add_coins(user_id, 0)
            bot.answer_callback_query(call.id, "Qo'shildingiz! ✅")
            
            players_list = "\n".join([f"• {name}" for name in game['players'].values()])
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("✋ O'yinga Qo'shilish", callback_data="join_game"))
            kb.add(types.InlineKeyboardButton("🚀 O'yinni Boshlash", callback_data="start_game"))

            text = f"📓 **Ishtirokchilar ({len(game['players'])} kishi):**\n\n{players_list}"
            try: bot.edit_message_caption(text, chat_id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            except: pass

    elif call.data == "start_game":
        game = games.get(chat_id)
        if not game or len(game['players']) < 3:
            bot.answer_callback_query(call.id, "Kamida 3 kishi kerak!", show_alert=True)
            return

        game['status'] = 'playing'
        game['alive'] = list(game['players'].keys())
        p_ids = list(game['players'].keys())
        random.shuffle(p_ids)

        pool = ["Misa", "Soichiro", "Mello", "Teru Mikami", "Takada", "Matsuda", "Ryuk", "Oddiy Aholi", "Oddiy Aholi"]
        random.shuffle(pool)

        assigned_roles = ["Kira", "L"] + pool[:len(p_ids)-2]
        
        for i, pid in enumerate(p_ids):
            role = assigned_roles[i]
            game['roles'][pid] = role
            
            photo = PHOTO_POLICE
            if role == "Kira": photo = PHOTO_KIRA_ROLE
            elif role == "L": photo = PHOTO_L_ROLE
            elif role == "Misa": photo = PHOTO_MISA_ROLE

            msg = f"🎭 **Sizning rolingiz: {role}**\n\nBatafsil ma'lumot uchun /roles komandasini bosing!"
            try: bot.send_photo(pid, photo, caption=msg, parse_mode="Markdown")
            except: bot.send_message(pid, msg, parse_mode="Markdown")

        bot.send_message(chat_id, "🎲 **O'yin boshlandi!** Rollar shaxsiy chatga yuborildi.")
        start_night(chat_id)

    elif data.startswith("kill_"):
        _, g_id, target_id = data.split("_")
        games[int(g_id)]['night_actions']['kill'] = int(target_id)
        games[int(g_id)]['activity'][user_id] += 2
        bot.answer_callback_query(call.id, "Ism O'lim Daftariga yozildi! 📓", show_alert=True)

    elif data.startswith("checkl_"):
        _, g_id, target_id = data.split("_")
        role = games[int(g_id)]['roles'].get(int(target_id))
        res = "🔴 KIRA!" if role in ["Kira", "Teru Mikami"] else "🟢 Kira emas."
        games[int(g_id)]['activity'][user_id] += 2
        bot.answer_callback_query(call.id, f"Natija: {res}", show_alert=True)

    elif data.startswith("checkmisa_"):
        _, g_id, target_id = data.split("_")
        role = games[int(g_id)]['roles'].get(int(target_id))
        res = "🕵️‍♂️ L topildi!" if role == "L" else "❌ L emas."
        games[int(g_id)]['activity'][user_id] += 2
        bot.answer_callback_query(call.id, f"Natija: {res}", show_alert=True)

    elif data.startswith("protect_"):
        _, g_id, target_id = data.split("_")
        games[int(g_id)]['night_actions']['protect'] = int(target_id)
        games[int(g_id)]['activity'][user_id] += 2
        bot.answer_callback_query(call.id, "Ushbu o'yinchi himoyalandi! 🛡", show_alert=True)

    elif data.startswith("block_"):
        _, g_id, target_id = data.split("_")
        games[int(g_id)]['night_actions']['block'] = int(target_id)
        games[int(g_id)]['activity'][user_id] += 2
        bot.answer_callback_query(call.id, "O'yinchi 1 tunga bloklandi! 🍫", show_alert=True)

    elif data.startswith("vote_"):
        _, g_id, target_id = data.split("_")
        g_id = int(g_id)
        game = games.get(g_id)
        if game and user_id in game['alive']:
            if target_id == "skip":
                game['votes'][user_id] = "skip"
                bot.answer_callback_query(call.id, "Ovozsiz o'tkazildi ⏩")
            else:
                game['votes'][user_id] = int(target_id)
                bot.answer_callback_query(call.id, "Ovoz berildi! 🗳")
            game['activity'][user_id] += 1

    elif data.startswith("matsuda_shoot_"):
        _, g_id, target_id = data.split("_")
        g_id, target_id = int(g_id), int(target_id)
        game = games.get(g_id)
        if game and user_id in game['alive'] and not game['matsuda_shot']:
            game['matsuda_shot'] = True
            target_role = game['roles'].get(target_id)
            if target_role in ["Kira", "Teru Mikami"]:
                game['alive'].remove(target_id)
                bot.send_message(g_id, f"🔫 **Matsuda otib tashladi!**\n\n🎯 **{game['players'][target_id]}** (Kira) o'ldirildi!")
            else:
                game['alive'].remove(user_id)
                bot.send_message(g_id, f"💥 **Matsuda adashdi!**\n\nU bemeta'sir fuqaroni otib qo'ydi va o'zi hibsga olindi!")
            check_game_over(g_id)

# ==================== GAME ENGINE ====================
def start_night(chat_id):
    game = games.get(chat_id)
    if not game: return
    game['night_actions'] = {'kill': None, 'check_l': None, 'protect': None, 'block': None, 'misa_search': None}

    try: bot.send_animation(chat_id, VIDEO_NIGHT_START, caption="🌙 **Shahar ustiga tun tushdi... (60 Sekund)**", parse_mode="Markdown")
    except: bot.send_message(chat_id, "🌙 **Shahar ustiga tun tushdi... (60 Sekund)**", parse_mode="Markdown")

    for pid in game['alive']:
        role = game['roles'][pid]
        kb = types.InlineKeyboardMarkup()
        for t_id in game['alive']:
            if t_id != pid:
                if role in ["Kira", "Teru Mikami"]:
                    kb.add(types.InlineKeyboardButton(game['players'][t_id], callback_data=f"kill_{chat_id}_{t_id}"))
                elif role == "L":
                    kb.add(types.InlineKeyboardButton(game['players'][t_id], callback_data=f"checkl_{chat_id}_{t_id}"))
                elif role == "Misa":
                    kb.add(types.InlineKeyboardButton(game['players'][t_id], callback_data=f"checkmisa_{chat_id}_{t_id}"))
                elif role == "Soichiro":
                    kb.add(types.InlineKeyboardButton(game['players'][t_id], callback_data=f"protect_{chat_id}_{t_id}"))
                elif role == "Mello":
                    kb.add(types.InlineKeyboardButton(game['players'][t_id], callback_data=f"block_{chat_id}_{t_id}"))

        if len(kb.keyboard) > 0:
            bot.send_message(pid, "⚡️ **Tungi strategik harakatingizni tanlang:**", reply_markup=kb)

    threading.Timer(60.0, process_night_results, args=[chat_id]).start()

def process_night_results(chat_id):
    game = games.get(chat_id)
    if not game or game['status'] != 'playing': return

    blocked_id = game['night_actions']['block']
    killed_id = game['night_actions']['kill']
    protected_id = game['night_actions']['protect']

    kira_id = None
    for pid, r in game['roles'].items():
        if r in ["Kira", "Teru Mikami"] and pid in game['alive']:
            kira_id = pid
            break

    if kira_id and kira_id == blocked_id:
        killed_id = None

    if killed_id and killed_id in game['alive']:
        target_role = game['roles'].get(killed_id)
        has_apple = user_inventory.get(killed_id, {}).get('apple', False)

        if target_role == "Ryuk":
            msg = f"☀️ **Tong otdi!**\n\n😈 Kira **{game['players'][killed_id]}** (Ryuk) ga hujum qildi, lekin Shinigamilarni o'ldirib bo'lmaydi!"
        elif killed_id == protected_id:
            msg = "☀️ **Tong otdi!**\n\n🛡 Soichiro Yagami Kiraning hujumini qaytardi! Hech kim o'lmadi."
        elif has_apple:
            user_inventory[killed_id]['apple'] = False
            msg = f"☀️ **Tong otdi!**\n\n🍏 **{game['players'][killed_id]}** ga Kira hujum qildi, lekin Ryuk Olmasi uni saqlab qoldi!"
        else:
            game['alive'].remove(killed_id)
            msg = f"☀️ **Tong otdi!**\n\n☠️ Afsuski, bugun tunda **{game['players'][killed_id]}** O'lim Daftari qurboni bo'ldi..."
    else:
        msg = "☀️ **Tong otdi!**\n\n✨ Bugun tunda hech kim zarar ko'rmadi."

    bot.send_message(chat_id, msg, parse_mode="Markdown")
    if check_game_over(chat_id): return
    start_day_discussion(chat_id)

def start_day_discussion(chat_id):
    game = games.get(chat_id)
    if not game: return
    
    bot.send_message(chat_id, "🗣 **MUHOKAMA FAZASI (40 Sekund):**\n\nShubhali shaxslarni muhokama qiling! Kim Kira bo'lishi mumkin?", parse_mode="Markdown")
    
    for pid in game['alive']:
        if game['roles'].get(pid) == "Matsuda" and not game['matsuda_shot']:
            m_kb = types.InlineKeyboardMarkup()
            for t_id in game['alive']:
                if t_id != pid:
                    m_kb.add(types.InlineKeyboardButton(f"🔫 Otish: {game['players'][t_id]}", callback_data=f"matsuda_shoot_{chat_id}_{t_id}"))
            bot.send_message(pid, "🔫 **Matsuda, shubhali odamni otishingiz mumkin:**", reply_markup=m_kb)

    threading.Timer(40.0, start_day_voting, args=[chat_id]).start()

def start_day_voting(chat_id):
    game = games.get(chat_id)
    if not game or game['status'] != 'playing': return

    game['votes'] = {}
    kb = types.InlineKeyboardMarkup()
    for pid in game['alive']:
        kb.add(types.InlineKeyboardButton(f"❌ Surgun: {game['players'][pid]}", callback_data=f"vote_{chat_id}_{pid}"))
    kb.add(types.InlineKeyboardButton("⏩ Ovozsiz O'tkazish (Skip)", callback_data=f"vote_{chat_id}_skip"))

    bot.send_message(chat_id, "🗳 **OVOZ BERISH FAZASI (40 Sekund):**\n\nKimni fosh qilmoqchisiz? Quyidagi tugmalar orqali ovoz bering:", reply_markup=kb, parse_mode="Markdown")
    threading.Timer(40.0, process_voting_results, args=[chat_id]).start()

def process_voting_results(chat_id):
    game = games.get(chat_id)
    if not game or game['status'] != 'playing': return

    votes = game['votes']
    if votes:
        vote_counts = {}
        for voter, target in votes.items():
            if target == "skip":
                continue
            weight = 2 if game['roles'].get(voter) == "Takada" else 1
            vote_counts[target] = vote_counts.get(target, 0) + weight

        if vote_counts:
            ejected_id = max(vote_counts, key=vote_counts.get)
            game['alive'].remove(ejected_id)
            bot.send_message(chat_id, f"⚖️ **{game['players'][ejected_id]}** aksariyat ovoz bilan surgun qilindi!\nUning roli: **{game['roles'][ejected_id]}** edi.")
        else:
            bot.send_message(chat_id, "⚖️ Ovoz berishda yetarli ovoz to'planmadi yoki hamma o'tkazib yubordi. Hech kim surgun qilinmadi.")
    else:
        bot.send_message(chat_id, "⚖️ Hech kim ovoz bermadi. Kun tinch o'tdi.")

    if check_game_over(chat_id): return
    start_night(chat_id)

def check_game_over(chat_id):
    game = games.get(chat_id)
    if not game: return False
    kira_alive = any(game['roles'][pid] in ["Kira", "Teru Mikami"] for pid in game['alive'])

    if not kira_alive:
        mvp_id = max(game['activity'], key=game['activity'].get)
        mvp_name = game['players'][mvp_id]
        
        caption = f"🏆 **L VA POLITSIYA (AHOLI) G'ALABA QOZONDI!**\n\n🌟 **O'yin MVP'si:** {mvp_name} (+250 L-Coins!)\nQolgan g'oliblar: +120 L-Coins!"
        try: bot.send_animation(chat_id, VIDEO_L_LOGO, caption=caption, parse_mode="Markdown")
        except: bot.send_message(chat_id, caption, parse_mode="Markdown")
        
        reward_winners(game, ["L", "Soichiro", "Mello", "Takada", "Matsuda", "Oddiy Aholi"], mvp_id)
        del games[chat_id]
        return True

    if len(game['alive']) <= 2 and kira_alive:
        mvp_id = max(game['activity'], key=game['activity'].get)
        mvp_name = game['players'][mvp_id]

        caption = f"📓 **HA-HA-HA! KIRA G'ALABA QOZONDI!**\n\n*\"Men yangi dunyo Xudosiman!\"*\n\n🌟 **O'yin MVP'si:** {mvp_name} (+250 L-Coins!)\nQolgan g'oliblar: +120 L-Coins!"
        try: bot.send_animation(chat_id, VIDEO_KIRA_WIN, caption=caption, parse_mode="Markdown")
        except: bot.send_message(chat_id, caption, parse_mode="Markdown")
        
        reward_winners(game, ["Kira", "Misa", "Teru Mikami"], mvp_id)
        del games[chat_id]
        return True

    return False

def reward_winners(game, winning_roles, mvp_id):
    for pid in game['players']:
        if game['roles'].get(pid) in winning_roles or (game['roles'].get(pid) == "Ryuk" and pid in game['alive']):
            is_mvp = (pid == mvp_id)
            add_win_and_mvp(pid, is_mvp=is_mvp)

print("⚡️ Death Note Bot Muvaffaqiyatli Ishga Tushdi!")
bot.infinity_polling(timeout=10, long_polling_timeout=5, skip_pending=True)
