import os

from dotenv import dotenv_values

config = dotenv_values(".env")

TELEGRAM_TOKEN = config.TELEGRAM_TOKEN # Вставь свой токен от BotFather
SPOTIFY_CLIENT_ID = config.SPOTIFY_CLIENT_ID  # Из Spotify Developer Dashboard
SPOTIFY_CLIENT_SECRET = config.SPOTIFY_CLIENT_SECRET # Из Spotify Developer Dashboard
SPOTIFY_REDIRECT_URI = config.SPOTIFY_CLIENT_SECRET # Для локальной машины

# Проверка на None
if TELEGRAM_TOKEN is None:
    raise ValueError("TELEGRAM_TOKEN не задан в переменных окружения!")
if SPOTIFY_CLIENT_ID is None:
    raise ValueError("SPOTIFY_CLIENT_ID не задан в переменных окружения!")
if SPOTIFY_CLIENT_SECRET is None:
    raise ValueError("SPOTIFY_CLIENT_SECRET не задан в переменных окружения!")