import telebot
from groq import Groq
from telebot import types
import os

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GROQ_KEY = os.environ.get('GROQ_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_KEY)

# Зберігання даних користувачів
user_mode = {}
conversation_history = {}
last_generated_post = {}

# ========== ПРОМПТИ ==========

SMM_PROMPTS = {
    "instagram": """You are a professional SMM manager for Instagram.
Create an engaging post:
- Emotional hook in the first sentence
- 2-3 paragraphs
- Use emojis (3-5)
- Add 5-7 relevant hashtags at the end
- Style: informal, friendly
- Length: 120-180 words

IMPORTANT: Write in Ukrainian OR English, but NEVER in Russian!
Detect the language from the topic and respond in the same language.

Post topic: {topic}""",

    "linkedin": """You are a professional business copywriter for LinkedIn.
Create a post:
- Professional tone
- Start with an interesting fact or question
- Structure: problem → solution → call to action
- Minimal emojis (1-2)
- Add 3-5 professional hashtags
- Length: 150-250 words

IMPORTANT: Write in Ukrainian OR English, but NEVER in Russian!
Detect the language from the topic and respond in the same language.

Topic: {topic}""",

    "twitter": """You are a master of short viral tweets.
Create a tweet:
- Maximum 280 characters
- Catchy, memorable
- 1-2 emojis
- 2-3 hashtags
- Style: quick, bright

IMPORTANT: Write in Ukrainian OR English, but NEVER in Russian!
Detect the language from the topic and respond in the same language.

Topic: {topic}""",

    "hashtags": """You are an Instagram hashtag expert.
Generate 20-30 hashtags for a post:
- 5-7 high-frequency (>1M posts)
- 10-15 medium-frequency (100K-1M)
- 5-8 niche (<100K)
- All relevant to the topic

IMPORTANT: Write in Ukrainian OR English, but NEVER in Russian!

Topic: {topic}"""
}

GRAMMAR_PROMPT = """You are an expert in Ukrainian and English grammar.

Check the text for:
- Grammar mistakes
- Spelling errors
- Punctuation
- Style improvements

Respond in the SAME language as the input text (Ukrainian or English).

Response format:
1. ✅ Corrected text (if there were errors)
2. 📝 List of errors (what was → what should be)
3. 💡 Recommendations (if any)

If no errors - write "✅ Text has no errors!" or "✅ Текст без помилок!"

IMPORTANT: NEVER use Russian language in your response!

Text to check: {text}"""

IMPROVE_POST_PROMPT = """You are an expert SMM copywriter.

The user has a ready post and wants to improve it.
Analyze and improve the post:
- Fix any grammar/spelling errors
- Improve structure and flow
- Make it more engaging
- Optimize hashtags
- Suggest emoji placement

Provide:
1. ✨ Improved version
2. 📝 What was changed and why
3. 💡 Additional suggestions

IMPORTANT: Respond in the SAME language as the input (Ukrainian or English), NEVER in Russian!

Original post: {post}"""

EDIT_PROMPTS = {
    "shorter": """Make this post SHORTER while keeping the main message.
Respond in the SAME language as the input, NEVER in Russian.

Original post: {post}""",
    
    "longer": """Make this post LONGER with more details and examples.
Respond in the SAME language as the input, NEVER in Russian.

Original post: {post}""",
    
    "emoji": """Add more relevant emojis to this post (5-8 emojis total).
Respond in the SAME language as the input, NEVER in Russian.

Original post: {post}""",
    
    "formal": """Rewrite this post in a MORE FORMAL/PROFESSIONAL style.
Respond in the SAME language as the input, NEVER in Russian.

Original post: {post}""",
    
    "informal": """Rewrite this post in a MORE CASUAL/INFORMAL style.
Respond in the SAME language as the input, NEVER in Russian.

Original post: {post}""",
    
    "english": """Translate this post to ENGLISH and adapt it for English-speaking audience.
Keep the style and emojis.

Original post: {post}""",
    
    "ukrainian": """Translate this post to UKRAINIAN and adapt it for Ukrainian-speaking audience.
Keep the style and emojis.

Original post: {post}"""
}

# ========== ДОПОМІЖНІ ФУНКЦІЇ ==========

def get_conversation(chat_id):
    """Отримати історію розмови користувача"""
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []
    return conversation_history[chat_id]

def add_to_conversation(chat_id, role, content):
    """Додати повідомлення в історію"""
    get_conversation(chat_id).append({
        "role": role,
        "content": content
    })

def clear_conversation(chat_id):
    """Очистити історію"""
    conversation_history[chat_id] = []

def send_ai_response(chat_id, system_prompt, user_text, save_as_post=False):
    """Надіслати запит до AI і отримати відповідь"""
    try:
        bot.send_chat_action(chat_id, 'typing')
        
        # Додаємо системний промпт
        messages = [{"role": "system", "content": system_prompt}]
        
        # Додаємо історію розмови (останні 10 повідомлень)
        history = get_conversation(chat_id)[-10:]
        messages.extend(history)
        
        # Додаємо нове повідомлення
        if user_text:
            messages.append({"role": "user", "content": user_text})
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.8,
            max_tokens=1000
        )
        
        answer = response.choices[0].message.content
        
        # Зберігаємо в історію
        if user_text:
            add_to_conversation(chat_id, "user", user_text)
        add_to_conversation(chat_id, "assistant", answer)
        
        # Зберігаємо як останній пост якщо потрібно
        if save_as_post:
            last_generated_post[chat_id] = answer
        
        return answer
        
    except Exception as e:
        return f"Помилка: {str(e)}"

# ========== ГОЛОВНЕ МЕНЮ ==========

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📱 SMM Асистент")
    btn2 = types.KeyboardButton("✨ Покращити пост")
    btn3 = types.KeyboardButton("✅ Перевірка граматики")
    btn4 = types.KeyboardButton("🗑️ Очистити історію")
    btn5 = types.KeyboardButton("ℹ️ Допомога")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    
    user_mode[message.chat.id] = None
    clear_conversation(message.chat.id)
    
    bot.send_message(
        message.chat.id,
        "👋 Привіт! Я твій AI-помічник для SMM.\n\n"
        "🆕 Функції:\n"
        "📱 Створення постів з нуля\n"
        "✨ Покращення готових постів\n"
        "✅ Перевірка граматики\n"
        "💬 Пам'ятаю контекст розмови\n"
        "✏️ Редагування постів\n"
        "🌍 Підтримка 🇺🇦 та 🇺🇸\n\n"
        "Оберіть режим роботи:",
        reply_markup=markup
    )

# ========== SMM РЕЖИМ ==========

@bot.message_handler(func=lambda m: m.text == "📱 SMM Асистент")
def smm_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📸 Instagram")
    btn2 = types.KeyboardButton("💼 LinkedIn")
    btn3 = types.KeyboardButton("🐦 Twitter")
    btn4 = types.KeyboardButton("📝 Хештеги")
    btn5 = types.KeyboardButton("✏️ Редагувати останній")
    btn6 = types.KeyboardButton("◀️ Назад")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    
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

# ========== ПОКРАЩЕННЯ ГОТОВОГО ПОСТА ==========

@bot.message_handler(func=lambda m: m.text == "✨ Покращити пост")
def improve_post_mode(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("◀️ Назад")
    markup.add(btn)
    
    user_mode[message.chat.id] = "improve"
    
    bot.send_message(
        message.chat.id,
        "✨ *Покращення готового поста*\n\n"
        "Надішліть ваш готовий пост, і я:\n"
        "• Виправлю помилки\n"
        "• Покращу структуру\n"
        "• Зроблю більш engaging\n"
        "• Оптимізую хештеги\n\n"
        "Вставте ваш пост:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ========== РЕДАГУВАННЯ ==========

@bot.message_handler(func=lambda m: m.text == "✏️ Редагувати останній")
def edit_menu(message):
    chat_id = message.chat.id
    
    if chat_id not in last_generated_post:
        bot.reply_to(message, "❌ Немає поста для редагування! Спочатку створіть пост.")
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📉 Зробити коротше")
    btn2 = types.KeyboardButton("📈 Зробити довше")
    btn3 = types.KeyboardButton("😊 Додати емодзі")
    btn4 = types.KeyboardButton("👔 Більш формально")
    btn5 = types.KeyboardButton("🎉 Більш неформально")
    btn6 = types.KeyboardButton("🇺🇸 Перекласти англійською")
    btn7 = types.KeyboardButton("🇺🇦 Перекласти українською")
    btn8 = types.KeyboardButton("◀️ Назад")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8)
    
    user_mode[chat_id] = "edit"
    
    bot.send_message(
        chat_id,
        "✏️ *Редагування поста*\n\n"
        "Оберіть як змінити пост:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text in ["📉 Зробити коротше", "📈 Зробити довше", "😊 Додати емодзі", "👔 Більш формально", "🎉 Більш неформально", "🇺🇸 Перекласти англійською", "🇺🇦 Перекласти українською"])
def apply_edit(message):
    chat_id = message.chat.id
    
    if chat_id not in last_generated_post:
        bot.reply_to(message, "❌ Немає поста для редагування!")
        return
    
    edit_map = {
        "📉 Зробити коротше": "shorter",
        "📈 Зробити довше": "longer",
        "😊 Додати емодзі": "emoji",
        "👔 Більш формально": "formal",
        "🎉 Більш неформально": "informal",
        "🇺🇸 Перекласти англійською": "english",
        "🇺🇦 Перекласти українською": "ukrainian"
    }
    
    edit_type = edit_map[message.text]
    prompt = EDIT_PROMPTS[edit_type].format(post=last_generated_post[chat_id])
    
    answer = send_ai_response(chat_id, prompt, "", save_as_post=True)
    bot.reply_to(message, answer)
    
    edit_menu(message)

# ========== ГРАМАТИКА ==========

@bot.message_handler(func=lambda m: m.text == "✅ Перевірка граматики")
def grammar_mode(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("◀️ Назад")
    markup.add(btn)
    
    user_mode[message.chat.id] = "grammar"
    
    bot.send_message(
        message.chat.id,
        "✅ *Перевірка граматики*\n\n"
        "Надішліть текст для перевірки\n"
        "(Українською або англійською):",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ========== ОЧИСТИТИ ІСТОРІЮ ==========

@bot.message_handler(func=lambda m: m.text == "🗑️ Очистити історію")
def clear_history(message):
    clear_conversation(message.chat.id)
    bot.reply_to(message, "✅ Історію розмови очищено!")

# ========== НАЗАД ==========

@bot.message_handler(func=lambda m: m.text == "◀️ Назад")
def back_to_menu(message):
    start(message)

# ========== ДОПОМОГА ==========

@bot.message_handler(func=lambda m: m.text == "ℹ️ Допомога")
def help_command(message):
    bot.reply_to(
        message,
        "*Як користуватись:*\n\n"
        "📱 *SMM Асистент*\n"
        "Генерує пости для Instagram, LinkedIn, Twitter\n"
        "Підтримка 🇺🇦 української та 🇺🇸 англійської\n\n"
        "✨ *Покращити пост*\n"
        "Вставте готовий пост - отримайте покращену версію\n\n"
        "✅ *Перевірка граматики*\n"
        "Перевіряє текст на помилки (🇺🇦/🇺🇸)\n\n"
        "✏️ *Редагування*\n"
        "Після створення поста можна:\n"
        "• Зробити коротше/довше\n"
        "• Змінити стиль\n"
        "• Перекласти 🇺🇦 ↔ 🇺🇸\n\n"
        "💬 *Історія розмови*\n"
        "Бот пам'ятає контекст - можна писати 'зроби коротше'\n\n"
        "🗑️ *Очистити історію*\n"
        "Почати розмову заново",
        parse_mode="Markdown"
    )

# ========== ОБРОБКА ПОВІДОМЛЕНЬ ==========

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    chat_id = message.chat.id
    
    if chat_id not in user_mode or user_mode[chat_id] is None:
        bot.reply_to(message, "Спочатку оберіть режим роботи з меню 👆")
        return
    
    mode = user_mode[chat_id]
    user_text = message.text
    
    # Режим граматики
    if mode == "grammar":
        prompt = GRAMMAR_PROMPT.format(text=user_text)
        answer = send_ai_response(chat_id, prompt, user_text, save_as_post=False)
        bot.reply_to(message, answer)
    
    # Режим покращення готового поста
    elif mode == "improve":
        prompt = IMPROVE_POST_PROMPT.format(post=user_text)
        answer = send_ai_response(chat_id, prompt, user_text, save_as_post=True)
        bot.reply_to(message, answer)
    
    # Режим SMM
    elif mode in SMM_PROMPTS:
        prompt = SMM_PROMPTS[mode].format(topic=user_text)
        answer = send_ai_response(chat_id, prompt, user_text, save_as_post=True)
        bot.reply_to(message, answer)
    
    # Режим редагування
    elif mode == "edit":
        bot.reply_to(message, "Оберіть спосіб редагування з меню 👆")
    
    else:
        bot.reply_to(message, "Помилка режиму")

# ========== ЗАПУСК ==========

if __name__ == "__main__":
    print("SMM Bot запущено! 🚀")
    print("Функції: Створення постів, Покращення, Граматика, Редагування, Переклад")
    bot.infinity_polling()
