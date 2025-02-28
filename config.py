import os

TELEGRAM_TOKEN = "7715124LsbJ_4VXfu6hGmA"  
SPOTIFY_CLIENT_ID = "5ff1dd33624239dfd08c" 
SPOTIFY_CLIENT_SECRET = "b46ffdc5cba5b5d1749f8" 
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"  

if TELEGRAM_TOKEN is None:
    raise ValueError("TELEGRAM_TOKEN не задан в переменных окружения!")
if SPOTIFY_CLIENT_ID is None:
    raise ValueError("SPOTIFY_CLIENT_ID не задан в переменных окружения!")
if SPOTIFY_CLIENT_SECRET is None:
    raise ValueError("SPOTIFY_CLIENT_SECRET не задан в переменных окружения!")
