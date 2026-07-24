import os
import random
import threading
import time
from flask import Flask
from telebot import TeleBot, types

# Flask server (Render port xatosini yo'qotish uchun)
app = Flask(__name__)

@app.route('/')
def home():
    return "Death Note Bot ishlamoqda!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Bot tokeni
TOKEN = "8816866283:AAERGz-96nCntew0kl3uwM8vauL7X4OskTs"
bot = TeleBot(TOKEN)

games = {}

# ================= ROLLARNI TAQSIMLASH =================
def assign_roles(players_dict):
    player_ids = list(players_dict.keys())
    random.shuffle(player_ids)
    
    roles = {}
    total = len(player_ids)
    
    roles[player_ids[0]] = "Kira"
    roles[player_ids[1]] = "L"
    
    if total >= 4:
        roles[player_ids[2]] = "Misa"
    if total >= 5:
        roles[player_ids[3]] = "Ryuk"
    if total >= 6:
        roles[player_ids[4]] = "Soichiro Yagami"
    if total >= 7:
        roles[player_ids[5]] = "Near"
    if total >= 8:
        roles[player_ids[6]] = "Mello"
        
    for p_id in player_ids:
        if p_id not in roles:
            roles[p_id] = "Matsuda (Politsiya)"
            
    return roles

# ================= TAYMER =================
def auto_start_timer(chat_id):
    time.sleep(45)
    game = games.get(chat_id)
    if game and game.get('status') == 'waiting':
        if len(game.get('players', {})) >= 3:
            bot.send_message(chat_id, "⏰ **Vaqt tugadi! O'yin avtomatik ravishda boshlanmoqda...**", parse_mode="Markdown")
            start_game_logic(chat_id)
        else:
            bot.send_message(chat_id, "❌ **O'yinni boshlash uchun kamida 3 kishi kerak edi. O'yin bekor qilindi.**")
            games.pop(chat_id, None)

# ================= O'YINNI BOSHLASH =================
def start_game_logic(chat_id):
    game = games.get(chat_id)
    if not game:
        return

    game['status'] = 'in_game'
    game['roles'] = assign_roles(game['players'])
    game['alive'] = list(game['players'].keys())

    bot.send_message(chat_id, "🎭 **Barcha personajlar va rollar taqsimlandi!**\n\nHar bir o'yinchiga shaxsiy chatda o'z roli va vazifasi yuborildi.", parse_mode="Markdown")

    role_descriptions = {
        "Kira": "📓 **Siz Kirasiz (Light Yagami)!** Vazifangiz: Tunda O'lim Daftari orqali hammangizni yo'q qilish va L'ni topish.",
        "L": "🕵️‍♂️ **Siz Lsiz!** Vazifangiz: Tunda shubhalilarni tekshirib, Kiraning shaxsiyatini fosh qilish.",
        "Misa": "👁 **Siz Misa Amanesiz!** Vazifangiz: Kiraga yordam berish va Shinigami ko'zlari bilan L'ni qidirish.",
        "Ryuk": "🍎 **Siz Ryuksiz (Shinigami)!** Siz neytralsiz, tunda istalgan o'yinchining roliga mo'ralashingiz mumkin.",
        "Soichiro Yagami": "👮‍♂️ **Siz Soichiro Yagamisiz (Politsiya Boshlig'i)!** Vazifangiz: Tunda biror o'yinchini Kiraning hujumidan **himoya qilish**.",
        "Near": "🧩 **Siz Nearsiz!** Vazifangiz: L bilan birga tahlil o'tkazish.",
        "Mello": "🍫 **Siz Mellosiz!** Vazifangiz: Kirani burchakka taqash.",
        "Matsuda (Politsiya)": "👮‍♂️ **Siz Matsudasiz (Politsiya)!** Tunda uxlaysiz, kunduzi ovoz berasiz."
    }

    for p_id, role in game['roles'].items():
        try:
            desc = role_descriptions.get(role, f"Sizning rolingiz: {role}")
            bot.send_message(p_id, desc, parse_mode="Markdown")
        except Exception:
            pass

    time.sleep(2)
    start_night(chat_id)

# ================= TUN SIKLI =================
def start_night(chat_id):
    game = games.get(chat_id)
    if not game:
        return

    game['status'] = 'night'
    game['night_actions'] = {}

    bot.send_message(chat_id, "🌙 **Shahar ustiga tun tushdi...**\n\nKira, L, Soichiro, Ryuk va boshqalar shaxsiy chatda o'z harakatlarini amalga oshirmoqda.", parse_mode="Markdown")

    alive_players = game['alive']
    for player_id in alive_players:
        role = game['roles'].get(player_id)

        if role == "Kira":
            kb = types.InlineKeyboardMarkup(row_width=1)
            for target_id in alive_players:
                if target_id != player_id:
                    p_name = game['players'][target_id]
                    kb.add(types.InlineKeyboardButton(f"🗡 {p_name}ni daftarga yozish", callback_data=f"kill_{chat_id}_{target_id}"))
            try:
                bot.send_message(player_id, "📓 **Death Note:** Bugun tunda kimning ismini daftarga yozasiz?", reply_markup=kb)
            except Exception:
                pass

        elif role == "L":
            kb = types.InlineKeyboardMarkup(row_width=1)
            for target_id in alive_players:
                if target_id != player_id:
                    p_name = game['players'][target_id]
                    kb.add(types.InlineKeyboardButton(f"🔍 {p_name}ni tekshirish", callback_data=f"checkl_{chat_id}_{target_id}"))
            try:
                bot.send_message(player_id, "🕵️‍♂️ **L:** Kimni shubhali deb hisoblaysiz?", reply_markup=kb)
            except Exception:
                pass

        elif role == "Soichiro Yagami":
            kb = types.InlineKeyboardMarkup(row_width=1)
            for target_id in alive_players:
                p_name = game['players'][target_id]
                kb.add(types.InlineKeyboardButton(f"🛡 {p_name}ni himoya qilish", callback_data=f"protect_{chat_id}_{target_id}"))
            try:
                bot.send_message(player_id, "👮‍♂️ **Soichiro Yagami:** Bugun tunda kimni Kiradan himoya qilasiz?", reply_markup=kb)
            except Exception:
                pass

        elif role == "Ryuk":
            kb = types.InlineKeyboardMarkup(row_width=1)
            for target_id in alive_players:
                if target_id != player_id:
                    p_name = game['players'][target_id]
                    kb.add(types.InlineKeyboardButton(f"🍎 {p_name}ning rolini ko'rish", callback_data=f"ryuk_{chat_id}_{target_id}"))
            try:
                bot.send_message(player_id, "🍎 **Ryuk:** Kimning kartasiga qaramoqchisiz?", reply_markup=kb)
            except Exception:
                pass

# ================= HANDLERLAR =================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(message, "👋 Death Note botiga xush kelibsiz! Guruhda /create orqali o'yin yarating.")

@bot.message_handler(commands=['create'])
def create_game_command(message):
    chat_id = message.chat.id
    if chat_id in games:
        bot.reply_to(message, "⚠️ Bu guruhda allaqachon o'yin ketmoqda!")
        return

    games[chat_id] = {
        'status': 'waiting',
        'players': {message.from_user.id: message.from_user.first_name},
        'roles': {},
        'alive': [],
        'night_actions': {}
    }

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✋ O'yinga Qo'shilish", callback_data=f"join_{chat_id}"))
    kb.add(types.InlineKeyboardButton("🚀 O'yinni Boshlash", callback_data=f"start_{chat_id}"))

    bot.send_message(chat_id, f"🎮 **Death Note O'yini Yaratildi!**\n\nYaratuvchi: {message.from_user.first_name}\n\n45 soniya ichida qo'shiling!", reply_markup=kb, parse_mode="Markdown")
    
    threading.Thread(target=auto_start_timer, args=(chat_id,), daemon=True).start()

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    data = call.data.split("_")
    action = data[0]

    if action == "join":
        c_id = int(data[1])
        game = games.get(c_id)
        if game and game['status'] == 'waiting':
            if call.from_user.id not in game['players']:
                game['players'][call.from_user.id] = call.from_user.first_name
                bot.answer_callback_query(call.id, "Muvaffaqiyatli qo'shildingiz!")
            else:
                bot.answer_callback_query(call.id, "Siz allaqachon o'yindasiz!")

    elif action == "start":
        c_id = int(data[1])
        game = games.get(c_id)
        if game and game['status'] == 'waiting':
            if len(game['players']) >= 3:
                start_game_logic(c_id)
            else:
                bot.answer_callback_query(call.id, "Kamida 3 kishi kerak!", show_alert=True)

    elif action == "kill":
        bot.answer_callback_query(call.id, "Ism daftarga yozildi...")
        bot.edit_message_text("✅ Niyatingiz qabul qilindi.", call.message.chat.id, call.message.message_id)

    elif action == "checkl":
        c_id = int(data[1])
        target_id = int(data[2])
        game = games.get(c_id)
        if game:
            target_role = game['roles'].get(target_id)
            res = "HA (Kira!)" if target_role == "Kira" else "YO'Q (Kira emas)"
            bot.answer_callback_query(call.id, f"Natija: {res}", show_alert=True)
            bot.edit_message_text(f"🔍 Tekshiruv natijasi: {res}", call.message.chat.id, call.message.message_id)

    elif action == "protect":
        bot.answer_callback_query(call.id, "Himoya o'rnatildi!")
        bot.edit_message_text("🛡 Tanlangan o'yinchi bu kecha himoyaga olindi.", call.message.chat.id, call.message.message_id)

    elif action == "ryuk":
        c_id = int(data[1])
        target_id = int(data[2])
        game = games.get(c_id)
        if game:
            target_role = game['roles'].get(target_id)
            bot.answer_callback_query(call.id, f"Uning roli: {target_role}", show_alert=True)
            bot.edit_message_text(f"🍎 Uning roli: **{target_role}** ekan.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

if __name__ == "__main__":
    # Flask serverni alohida oqimda yurgazish
    threading.Thread(target=run_flask, daemon=True).start()
    bot.polling(none_stop=True)
