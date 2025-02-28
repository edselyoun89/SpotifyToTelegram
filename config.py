import os

TELEGRAM_TOKEN = "7954LsbJ_4VXfu6hGmA"  
SPOTIFY_CLIENT_ID = "905f47739dfd08c"  
SPOTIFY_CLIENT_SECRET = "b46ffd1cbb5d1749f8"  
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"  

if TELEGRAM_TOKEN is None:
    raise ValueError("TELEGRAM_TOKEN не задан в переменных окружения!")
if SPOTIFY_CLIENT_ID is None:
    raise ValueError("SPOTIFY_CLIENT_ID не задан в переменных окружения!")
if SPOTIFY_CLIENT_SECRET is None:
    raise ValueError("SPOTIFY_CLIENT_SECRET не задан в переменных окружения!")
