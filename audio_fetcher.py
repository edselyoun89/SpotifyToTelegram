import yt_dlp as youtube_dl
import os

def download_audio(track_name, artist, quality="192", output_dir="downloads"):
    query = f"{track_name} {artist} audio"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"{output_dir}/{track_name} - {artist}.%(ext)s",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': quality,
        }],
        'ffmpeg_location': r'C:\Users\shtepcell\Downloads\ffmpeg-7.1-essentials_build\bin\ffmpeg.exe',
        'quiet': True,
    }
    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch1:{query}"])
    
    return f"{output_dir}/{track_name} - {artist}.mp3"