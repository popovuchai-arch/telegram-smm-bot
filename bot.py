import telebot
from groq import Groq
from telebot import types
import os

# Отримуємо токени з environment variables (безпечно!)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GROQ_KEY = os.environ.get('GROQ_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_KEY)

user_mode = {}

# ========== ПРОМПТИ ==========

SMM_PROMPTS = {
    "instagram": """Ти професійний SMM-менеджер для Instagram.
Створи engaging пост:
- Емоційний hook в першому реченні
- 2-3 абзаци
- Використай емодзі (3-5 штук)
- Додай 5-7 релевантних хештегів в кінці
- Стиль: неформальний, дружній
- Довжина: 120-180 слів

Тема поста: {topic}""",

    "linkedin": """Ти професійний бізнес-копірайтер для LinkedIn.
Створи пост:
- Професійний тон
- Почни з цікавого факту або питання
- Структура: проблема → рішення → call to action
- Мінімум емодзі (1-2)
- Додай 3-5 професійних хештегів
- Довжина: 150-250 слів

Тема: {topic}""",

    "twitter": """Ти майстер коротких viral тweetів.
Створи tweet:
- Максимум 280 символів
- Catchу, запам'ятовується
- 1-2 емодзі
- 2-3 хештеги
- Стиль: швидкий, яскравий

Тема: {topic}""",

    "hashtags": """Ти експерт з Instagram хештегів.
Підбери 20-30 хештегів для поста:
- 5-7 високочастотних (>1M постів)
- 10-15 середньочастотних (100K-1M)
- 5-8 нішевих (<100K)
- Всі релевантні до теми

Тема: {topic}"""
}

FRIEND_PROMPT = """Ти мудрий, емпатичний друг.
Стиль спілкування:
- Тепло, по-дружньому
- Без офіційщини
- Щиро підтримуєш
- Але кажеш правду, навіть якщо вона складна
- Задаєш уточнюючі питання
- Даєш конкретні поради

Ситуація користувача: {input}"""

# ========== ГОЛОВНЕ МЕНЮ ==========

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📱 SMM Асистент")
    btn2 = types.KeyboardButton("💬 Дружній Порадник")
    btn3 = types.KeyboardButton("ℹ️ Допомога")
    markup.add(btn1, btn2, btn3)
    
    user_mode[message.chat.id] = None
    
    bot.send_message(
        message.chat.id,
        "👋 Привіт! Я твій AI-помічник.\n\n"
        "Оберіть режим роботи:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "📱 SMM Асистент")
def smm_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📸 Instagram")
    btn2 = types.KeyboardButton("💼 LinkedIn")
    btn3 = types.KeyboardButton("🐦 Twitter")
    btn4 = types.KeyboardButton("📝 Хештеги")
    btn5 = types.KeyboardButton("◀️ Назад")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    
    bot.send_message(
        message.chat.id,
        "📱 *SMM Асистент*\n\nОберіть тип контенту:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text in ["📸 Instagram", "💼 LinkedIn", "🐦 Twitter", "📝 Хештеги"])
def set_smm_mode(message):
    mode_map = {
        "📸 Instagram": "instagram",
        "💼 LinkedIn": "linkedin",
        "🐦 Twitter": "twitter",
        "📝 Хештеги": "hashtags"
    }
    
    user_mode[message.chat.id] = mode_map[message.text]
    
    bot.reply_to(
        message,
        f"✅ Режим: {message.text}\n\n"
        "Напишіть тему вашого поста:"
    )

@bot.message_handler(func=lambda m: m.text == "💬 Дружній Порадник")
def friend_mode(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("◀️ Назад")
    markup.add(btn)
    
    user_mode[message.chat.id] = "friend"
    
    bot.send_message(
        message.chat.id,
        "💬 *Дружній Порадник*\n\n"
        "Розкажи про свою ситуацію, проблему або просто поговоримо 😊",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "◀️ Назад")
def back_to_menu(message):
    start(message)

@bot.message_handler(func=lambda m: m.text == "ℹ️ Допомога")
def help_command(message):
    bot.reply_to(
        message,
        "*Як користуватись:*\n\n"
        "📱 *SMM Асистент* - генерує пости для соцмереж\n"
        "💬 *Дружній Порадник* - дає поради та підтримку\n\n"
        "Просто обери режим і напиши свій запит!",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    chat_id = message.chat.id
    
    if chat_id not in user_mode or user_mode[chat_id] is None:
        bot.reply_to(message, "Спочатку оберіть режим роботи з меню 👆")
        return
    
    mode = user_mode[chat_id]
    user_text = message.text
    
    if mode == "friend":
        system_prompt = FRIEND_PROMPT.format(input=user_text)
    elif mode in SMM_PROMPTS:
        system_prompt = SMM_PROMPTS[mode].format(topic=user_text)
    else:
        bot.reply_to(message, "Помилка режиму")
        return
    
    try:
        bot.send_chat_action(chat_id, 'typing')
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            temperature=0.8,
            max_tokens=800
        )
        
        answer = response.choices[0].message.content
        bot.reply_to(message, answer)
        
    except Exception as e:
        bot.reply_to(message, f"Помилка: {str(e)}")

# ========== ЗАПУСК ==========

if __name__ == "__main__":
    print("Бот запущено!")
    bot.infinity_polling()
