import telebot
import logging
from config import TELEGRAM_TOKEN
from spotify_api import get_spotify_playlist_tracks, get_spotify_client
from audio_fetcher import download_audio
import os
import time

# Логирование
logging.basicConfig(filename='bot.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_quality = {}  # Качество аудио для каждого пользователя
user_auth_managers = {}  # Хранение auth_manager для авторизации

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🎵 Привет! Я бот для переноса треков из Spotify в Telegram.\n"
        "1. Используй /auth для подключения своего аккаунта Spotify.\n"
        "2. Отправь ссылку на плейлист.\n"
        "Дополнительно: /help, /quality"
    )
    bot.reply_to(message, welcome_text)
    logging.info(f"Пользователь {message.from_user.id} запустил бота")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "📚 **Команды бота**:\n"
        "/start - Начать работу\n"
        "/help - Показать справку\n"
        "/auth - Авторизоваться в Spotify\n"
        "/quality [128/192/320] - Установить качество аудио (по умолчанию 192 kbps)\n"
        "Отправь ссылку на плейлист Spotify для скачивания!"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['auth'])
def spotify_auth(message):
    user_id = message.from_user.id
    sp, auth_manager = get_spotify_client(user_id)
    auth_url = auth_manager.get_authorize_url()
    user_auth_managers[user_id] = auth_manager
    bot.reply_to(message, f"🔗 Перейди по ссылке для авторизации Spotify:\n{auth_url}\nПосле этого отправь код из URL (часть после `code=`).")
    logging.info(f"Пользователь {user_id} запросил авторизацию Spotify")

@bot.message_handler(func=lambda message: message.text.startswith("code="))
def handle_auth_code(message):
    user_id = message.from_user.id
    if user_id not in user_auth_managers:
        bot.reply_to(message, "❌ Сначала используй /auth!")
        return
    code = message.text.replace("code=", "").strip()
    auth_manager = user_auth_managers[user_id]
    try:
        auth_manager.get_access_token(code)
        bot.reply_to(message, "✅ Авторизация Spotify прошла успешно! Теперь отправь ссылку на плейлист.")
        del user_auth_managers[user_id]  # Удаляем временный менеджер
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
            bot.reply_to(message, f"🎶 Качество установлено: {quality} kbps")
            logging.info(f"Пользователь {message.from_user.id} установил качество {quality} kbps")
        else:
            bot.reply_to(message, "❌ Укажи качество: 128, 192 или 320")
    except IndexError:
        bot.reply_to(message, "❌ Укажи качество, например: /quality 320")

@bot.message_handler(func=lambda message: "spotify.com/playlist" in message.text)
def handle_playlist(message):
    user_id = message.from_user.id
    bot.reply_to(message, "🎧 Начинаю обработку плейлиста...")
    logging.info(f"Пользователь {user_id} отправил плейлист: {message.text}")
    
    try:
        tracks, playlist_name, track_count = get_spotify_playlist_tracks(message.text, user_id)
        if not tracks:
            bot.reply_to(message, "❌ Не удалось получить треки. Убедись, что ты авторизован (/auth) и ссылка верна!")
            return
        
        quality = user_quality.get(user_id, "192")
        bot.send_message(message.chat.id, f"📀 Плейлист: *{playlist_name}*\nТреков: {track_count}\nКачество: {quality} kbps")
        
        processed = 0
        for track in tracks:
            processed += 1
            progress = f"[{processed}/{track_count}] ({int(processed/track_count*100)}%)"
            bot.send_message(message.chat.id, f"⬇️ {progress} Скачиваю: *{track['name']}* - {track['artist']}")
            try:
                audio_file = download_audio(track['name'], track['artist'], quality)
                with open(audio_file, 'rb') as audio:
                    bot.send_audio(message.chat.id, audio, title=track['name'], performer=track['artist'])
                os.remove(audio_file)
                logging.info(f"Успешно отправлен: {track['name']} для {user_id}")
            except Exception as e:
                bot.send_message(message.chat.id, f"⚠️ Ошибка при скачивании *{track['name']}*: {str(e)}")
                logging.error(f"Ошибка скачивания {track['name']} для {user_id}: {str(e)}")
        
        bot.send_message(message.chat.id, f"✅ Готово! Все треки из *{playlist_name}* отправлены!")
        logging.info(f"Завершена обработка {playlist_name} для {user_id}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")
        logging.error(f"Ошибка обработки плейлиста для {user_id}: {str(e)}")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "🤔 Отправь ссылку на плейлист Spotify или используй /help для справки.")

try:
    print("Бот запущен на сервере...")
    bot.polling()
except Exception as e:
    print(f"Ошибка запуска бота: {str(e)}")
    logging.error(f"Ошибка запуска бота: {str(e)}")