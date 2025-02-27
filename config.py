import os

TELEGRAM_TOKEN = "7954171512:AAEvKXvSNR39MFZ_6xt4LsbJ_4VXfu6hGmA"  # Вставь свой токен от BotFather
SPOTIFY_CLIENT_ID = "905ff1dd336242ebb93b247739dfd08c"  # Из Spotify Developer Dashboard
SPOTIFY_CLIENT_SECRET = "b46ffd1ee6b647ad9c5cba5b5d1749f8"  # Из Spotify Developer Dashboard
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"  # Для локальной машины

# Проверка на None
if TELEGRAM_TOKEN is None:
    raise ValueError("TELEGRAM_TOKEN не задан в переменных окружения!")
if SPOTIFY_CLIENT_ID is None:
    raise ValueError("SPOTIFY_CLIENT_ID не задан в переменных окружения!")
if SPOTIFY_CLIENT_SECRET is None:
    raise ValueError("SPOTIFY_CLIENT_SECRET не задан в переменных окружения!")