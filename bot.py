import telebot
import logging
from config import TELEGRAM_TOKEN
from spotify_api import get_spotify_playlist_tracks, get_spotify_client
from audio_fetcher import download_audio
import os
import time
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import re
from threading import Thread  # Добавляем для многопоточности

# Логирование
logging.basicConfig(filename='bot.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_quality = {}  # Качество аудио для каждого пользователя
user_auth_managers = {}  # Хранение auth_manager для авторизации

# Главная клавиатура
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("/start"))
    keyboard.add(KeyboardButton("/help"))
    keyboard.add(KeyboardButton("/auth"))
    keyboard.add(KeyboardButton("/quality"))
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🎵 Привет! Я бот для переноса треков из Spotify в Telegram.\n"
        "Нажми /auth, чтобы подключить Spotify (просто вставь URL после авторизации).\n"
        "Используй кнопки ниже для удобства!"
    )
    bot.reply_to(message, welcome_text, reply_markup=get_main_keyboard())
    logging.info(f"Пользователь {message.from_user.id} запустил бота")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "📚 **Команды бота**:\n"
        "/start - Начать работу\n"
        "/help - Показать справку\n"
        "/auth - Подключить Spotify (вставь полный URL после авторизации)\n"
        "/quality [128/192/320] - Установить качество аудио (по умолчанию 192 kbps)\n"
        "Отправь ссылку на плейлист Spotify для скачивания!"
    )
    bot.reply_to(message, help_text, reply_markup=get_main_keyboard())

@bot.message_handler(commands=['auth'])
def spotify_auth(message):
    user_id = message.from_user.id
    sp, auth_manager = get_spotify_client(user_id)
    auth_url = auth_manager.get_authorize_url()
    user_auth_managers[user_id] = auth_manager

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Подключить Spotify", url=auth_url))
    bot.reply_to(message, "🔗 Нажми кнопку ниже, чтобы подключить Spotify. После авторизации вставь сюда полный URL из браузера!",
                 reply_markup=keyboard)
    logging.info(f"Пользователь {user_id} запросил авторизацию Spotify")

@bot.message_handler(func=lambda message: "code=" in message.text and message.from_user.id in user_auth_managers)
def handle_auth_code(message):
    user_id = message.from_user.id
    
    # Извлекаем код из полного URL с помощью регулярного выражения
    text = message.text.strip()
    match = re.search(r'code=([^&]+)', text)
    if match:
        code = match.group(1)
    else:
        bot.reply_to(message, "❌ Не удалось найти код в URL. Попробуй ещё раз!")
        return
    
    auth_manager = user_auth_managers[user_id]
    try:
        auth_manager.get_access_token(code)
        bot.reply_to(message, "✅ Авторизация Spotify прошла успешно! Теперь отправь ссылку на плейлист.",
                     reply_markup=get_main_keyboard())
        del user_auth_managers[user_id]
        logging.info(f"Пользователь {user_id} успешно авторизовался в Spotify")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка авторизации: {str(e)}")
        logging.error(f"Ошибка авторизации для {user_id}: {str(e)}")

@bot.message_handler(commands=['quality'])
def set_quality(message):
    try:
        quality = message.text.split()[1]
        if quality in ['128', '192', '320']:
            user_quality[message.from_user.id] = quality
            bot.reply_to(message, f"🎶 Качество установлено: {quality} kbps", reply_markup=get_main_keyboard())
            logging.info(f"Пользователь {message.from_user.id} установил качество {quality} kbps")
        else:
            bot.reply_to(message, "❌ Укажи качество: 128, 192 или 320")
    except IndexError:
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("128 kbps", callback_data="quality_128"),
            InlineKeyboardButton("192 kbps", callback_data="quality_192"),
            InlineKeyboardButton("320 kbps", callback_data="quality_320")
        )
        bot.reply_to(message, "❌ Укажи качество через команду или выбери ниже:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("quality_"))
def handle_quality_callback(call):
    user_id = call.from_user.id
    quality = call.data.split("_")[1]
    user_quality[user_id] = quality
    bot.edit_message_text(f"🎶 Качество установлено: {quality} kbps", call.message.chat.id, call.message.message_id,
                          reply_markup=None)
    bot.answer_callback_query(call.id)
    logging.info(f"Пользователь {user_id} выбрал качество {quality} kbps через кнопку")

# Функция для скачивания и отправки трека в отдельном потоке
def download_and_send_track(track, user_id, quality, chat_id, processed, track_count):
    progress = f"[{processed}/{track_count}] ({int(processed/track_count*100)}%)"
    bot.send_message(chat_id, f"⬇️ {progress} Скачиваю: {track['name']} - {track['artist']}")
    try:
        audio_file = download_audio(track['name'], track['artist'], quality)
        with open(audio_file, 'rb') as audio:
            bot.send_audio(chat_id, audio, title=track['name'], performer=track['artist'])
        os.remove(audio_file)
        logging.info(f"Успешно отправлен: {track['name']} для {user_id}")
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ Ошибка при скачивании {track['name']}: {str(e)}")
        logging.error(f"Ошибка скачивания {track['name']} для {user_id}: {str(e)}")

@bot.message_handler(func=lambda message: "spotify.com/playlist" in message.text)
def handle_playlist(message):
    user_id = message.from_user.id
    bot.reply_to(message, "🎧 Начинаю обработку плейлиста...", reply_markup=get_main_keyboard())
    logging.info(f"Пользователь {user_id} отправил плейлист: {message.text}")
    
    try:
        tracks, playlist_name, track_count = get_spotify_playlist_tracks(message.text, user_id)
        if not tracks:
            bot.reply_to(message, "❌ Не удалось получить треки. Убедись, что ты авторизован (/auth) и плейлист доступен!")
            return
        
        quality = user_quality.get(user_id, "192")
        bot.send_message(message.chat.id, f"📀 Плейлист: {playlist_name}\nТреков: {track_count}\nКачество: {quality} kbps")
        
        threads = []
        processed = 0
        for track in tracks:
            processed += 1
            # Создаём поток для каждого трека
            thread = Thread(target=download_and_send_track, 
                            args=(track, user_id, quality, message.chat.id, processed, track_count))
            threads.append(thread)
            thread.start()
        
        # Ждём завершения всех потоков
        for thread in threads:
            thread.join()
        
        bot.send_message(message.chat.id, f"✅ Готово! Все треки из {playlist_name} отправлены!")
        logging.info(f"Завершена обработка {playlist_name} для {user_id}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")
        logging.error(f"Ошибка обработки плейлиста для {user_id}: {str(e)}")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "🤔 Отправь ссылку на плейлист Spotify или используй кнопки ниже!",
                 reply_markup=get_main_keyboard())

try:
    print("Бот запущен на сервере...")
    bot.polling()
except Exception as e:
    print(f"Ошибка запуска бота: {str(e)}")
    logging.error(f"Ошибка запуска бота: {str(e)}")