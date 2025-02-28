from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
FFMPEG_PATH = os.getenv("FFMPEG_PATH")

# Проверка на None
if TELEGRAM_TOKEN is None:
    raise ValueError("TELEGRAM_TOKEN не задан в переменных окружения!")
if SPOTIFY_CLIENT_ID is None:
    raise ValueError("SPOTIFY_CLIENT_ID не задан в переменных окружения!")
if SPOTIFY_CLIENT_SECRET is None:
    raise ValueError("SPOTIFY_CLIENT_SECRET не задан в переменных окружения!")