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
from queue import Queue  # Для очереди загрузки

# Логирование
logging.basicConfig(filename='bot.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_quality = {}  # Качество аудио для каждого пользователя
user_auth_managers = {}  # Хранение auth_manager для авторизации
user_queues = {}  # Очереди загрузки для каждого пользователя

# Главная клавиатура
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("/start"))
    keyboard.add(KeyboardButton("/help"))
    keyboard.add(KeyboardButton("/auth"))
    keyboard.add(KeyboardButton("/quality"))
    keyboard.add(KeyboardButton("/queue"))  # Добавляем кнопку для очереди
    keyboard.add(KeyboardButton("/clear"))  # Добавляем кнопку для очистки очереди
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
        "/queue - Показать очередь загрузки\n"
        "/clear - Очистить очередь\n"
        "Отправь ссылку на плейлист, альбом или трек Spotify для скачивания!"
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

@bot.message_handler(commands=['queue'])
def show_queue(message):
    user_id = message.from_user.id
    if user_id not in user_queues or not user_queues[user_id].queue:
        bot.reply_to(message, "❌ Очередь пуста!", reply_markup=get_main_keyboard())
        return
    queue_list = list(user_queues[user_id].queue)
    queue_text = "📋 **Очередь загрузки**:\n"
    for i, url in enumerate(queue_list, 1):
        queue_text += f"{i}. {url}\n"
    bot.reply_to(message, queue_text, reply_markup=get_main_keyboard())
    logging.info(f"Пользователь {user_id} запросил очередь")

@bot.message_handler(commands=['clear'])
def clear_queue(message):
    user_id = message.from_user.id
    if user_id in user_queues:
        user_queues[user_id] = Queue()
        bot.reply_to(message, "✅ Очередь очищена!", reply_markup=get_main_keyboard())
        logging.info(f"Пользователь {user_id} очистил очередь")
    else:
        bot.reply_to(message, "❌ Очередь уже пуста!", reply_markup=get_main_keyboard())

# Функция для скачивания и отправки трека в отдельном потоке
def download_and_send_track(track, user_id, quality, chat_id, processed, track_count, total_size, start_time):
    progress = f"[{processed}/{track_count}] ({int(processed/track_count*100)}%)"
    bot.send_message(chat_id, f"⬇️ {progress} Скачиваю: {track['name']} - {track['artist']}")
    try:
        audio_file = download_audio(track['name'], track['artist'], quality)
        file_size = os.path.getsize(audio_file) / (1024 * 1024)  # Размер в MB
        total_size[0] += file_size
        with open(audio_file, 'rb') as audio:
            bot.send_audio(chat_id, audio, title=track['name'], performer=track['artist'])
        os.remove(audio_file)
        logging.info(f"Успешно отправлен: {track['name']} для {user_id}")
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ Ошибка при скачивании {track['name']}: {str(e)}")
        logging.error(f"Ошибка скачивания {track['name']} для {user_id}: {str(e)}")

# Обработка плейлистов, альбомов и треков
def handle_playlist_processing(message, url):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Инициализация очереди, если её нет
    if user_id not in user_queues:
        user_queues[user_id] = Queue()
    
    # Добавляем URL в очередь
    user_queues[user_id].put(url)
    bot.send_message(chat_id, f"📥 Добавлено в очередь: {url}", reply_markup=get_main_keyboard())
    
    # Обрабатываем очередь
    while not user_queues[user_id].empty():
        current_url = user_queues[user_id].get()
        bot.send_message(chat_id, f"🎧 Обрабатываю: {current_url}")
        
        # Определяем тип ссылки и получаем треки
        tracks = []
        playlist_name = "Unknown"
        track_count = 0
        total_size = [0]  # Для статистики (список для изменения в потоках)
        start_time = time.time()
        
        if "spotify.com" in current_url:
            if "playlist" in current_url:
                tracks, playlist_name, track_count = get_spotify_playlist_tracks(current_url, user_id)
            elif "album" in current_url:
                sp, _ = get_spotify_client(user_id)
                album_id = current_url.split("/")[-1].split("?")[0]
                album = sp.album(album_id)
                playlist_name = album['name']
                tracks = [{'name': track['name'], 'artist': track['artists'][0]['name']} for track in album['tracks']['items']]
                track_count = len(tracks)
            elif "track" in current_url:
                sp, _ = get_spotify_client(user_id)
                track_id = current_url.split("/")[-1].split("?")[0]
                track = sp.track(track_id)
                playlist_name = track['name']
                tracks = [{'name': track['name'], 'artist': track['artists'][0]['name']}]
                track_count = 1
        
        if not tracks:
            bot.send_message(chat_id, "❌ Не удалось получить треки. Проверь ссылку или авторизацию (/auth)!")
            continue
        
        quality = user_quality.get(user_id, "192")
        bot.send_message(chat_id, f"📀 Источник: {playlist_name}\nТреков: {track_count}\nКачество: {quality} kbps")
        
        threads = []
        processed = 0
        for track in tracks:
            processed += 1
            thread = Thread(target=download_and_send_track, 
                            args=(track, user_id, quality, chat_id, processed, track_count, total_size, start_time))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        elapsed_time = time.time() - start_time
        stats = f"✅ Готово! Все треки из {playlist_name} отправлены!\n" \
                f"Время: {elapsed_time:.2f} сек\nРазмер: {total_size[0]:.2f} MB"
        bot.send_message(chat_id, stats, reply_markup=get_main_keyboard())
        logging.info(f"Завершена обработка {playlist_name} для {user_id}")

@bot.message_handler(func=lambda message: any(x in message.text for x in ["spotify.com/playlist", "spotify.com/album", "spotify.com/track"]))
def handle_playlist(message):
    handle_playlist_processing(message, message.text)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "🤔 Отправь ссылку на плейлист, альбом или трек Spotify или используй кнопки ниже!",
                 reply_markup=get_main_keyboard())

try:
    print("Бот запущен на сервере...")
    bot.polling()
except Exception as e:
    print(f"Ошибка запуска бота: {str(e)}")
    logging.error(f"Ошибка запуска бота: {str(e)}")