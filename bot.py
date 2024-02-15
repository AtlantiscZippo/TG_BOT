import telebot
from telebot import types
import sqlite3

bot = telebot.TeleBot('')

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        language TEXT,
        name TEXT,
        phone_number TEXT,
        latitude REAL,
        longitude REAL
    )
''')
conn.commit()

user_data = {}


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Русский 🇷🇺', callback_data='lang_ru'),
               types.InlineKeyboardButton(text='O‘zbekcha 🇺🇿', callback_data='lang_uz'))
    bot.send_message(message.chat.id, 'Выберите язык / Choose your language:', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_') and len(call.data) > 5)
def callback_query(call):
    lang = call.data[5:]
    user_data[call.message.chat.id] = {'language': lang}

    if lang == 'uz':
        bot.send_message(call.message.chat.id, f'Siz tanlagan til: {lang}\nIsmingizni kiriting:')
    else:
        bot.send_message(call.message.chat.id, f'Выбран язык: {lang}\nВведите своё имя:')
    bot.register_next_step_handler(call.message, process_name_step)


def process_name_step(message):
    chat_id = message.chat.id
    name = message.text
    user_data[chat_id]['name'] = name
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item = types.KeyboardButton('Отправить контакт', request_contact=True)
    markup.add(item)

    if user_data[chat_id]['language'] == 'uz':
        bot.send_message(chat_id, f'Assalomu alaykum, {name}! Telefon raqamingizni yuboring📲', reply_markup=markup)
    else:
        bot.send_message(chat_id, f'Привет, {name}! Отправь свой номер телефона📲', reply_markup=markup)
    bot.register_next_step_handler(message, contact_handler)


@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    chat_id = message.chat.id
    contact = message.contact
    user_data[chat_id]['contact'] = contact.phone_number
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item = types.KeyboardButton('Отправить локацию', request_location=True)
    markup.add(item)

    if user_data[chat_id]['language'] == 'uz':
        bot.send_message(chat_id, 'Ro‘yxatdan o‘tish uchun o‘zingizni joylashuvni yuboring🗺️', reply_markup=markup)
    else:
        bot.send_message(chat_id, 'Для завершения регистрации отправь свою локацию🗺️', reply_markup=markup)
    bot.register_next_step_handler(message, location_handler)


@bot.message_handler(content_types=['location'])
def location_handler(message):
    chat_id = message.chat.id
    location = message.location
    user_data[chat_id]['location'] = {'latitude': location.latitude, 'longitude': location.longitude}

    cursor.execute('INSERT INTO users (user_id, language, name, phone_number, latitude, longitude)VALUES ('
                   '?, ?, ?, ?, ?, ?)', (chat_id, user_data[chat_id]['language'], user_data[chat_id]['name'],
                                         user_data[chat_id].get('contact', ''), location.latitude, location.longitude))
    conn.commit()

    if user_data[chat_id]['language'] == 'uz':
        bot.send_message(chat_id, 'Ro‘yxatdan o‘tdingiz!🎉')
    else:
        bot.send_message(chat_id, 'Спасибо за регистрацию!🎉')


bot.polling(none_stop=True)
