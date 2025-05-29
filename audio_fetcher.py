import yt_dlp as youtube_dl
import os
import re
from config import FFMPEG_PATH

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def download_audio(track_name, artist, quality="192", output_dir="downloads"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    query = f"{track_name} {artist} audio"
    safe_name = sanitize_filename(f"{track_name} - {artist}")
    output_path = os.path.join(output_dir, f"{safe_name}.%(ext)s")
    mp3_path = os.path.join(output_dir, f"{safe_name}.mp3")

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'cookiefile': 'youtube.com_cookies.txt',
        'ffmpeg_location': FFMPEG_PATH,
        'outtmpl': output_path,
        'allow_unplayable_formats': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': quality,
        }]
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{query}"])
    except Exception as e:
        raise Exception(f"yt-dlp ошибка: {e}")

    if not os.path.isfile(mp3_path):
        raise FileNotFoundError(f"Файл не найден: {mp3_path}")

    return mp3_path
