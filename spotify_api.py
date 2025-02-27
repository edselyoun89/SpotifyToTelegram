import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI
import os

def get_spotify_client(user_id):
    cache_path = f".cache-{user_id}"
    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope="playlist-read-private playlist-read-collaborative user-read-private user-read-email",
        cache_path=cache_path
    )
    return spotipy.Spotify(auth_manager=auth_manager), auth_manager

def get_spotify_playlist_tracks(playlist_url, user_id):
    sp, auth_manager = get_spotify_client(user_id)
    playlist_id = playlist_url.split("/")[-1].split("?")[0]
    try:
        playlist_info = sp.playlist(playlist_id)
        tracks = []
        results = sp.playlist_tracks(playlist_id)
        for item in results['items']:
            track = item['track']
            tracks.append({
                'name': track['name'],
                'artist': track['artists'][0]['name']
            })
        return tracks, playlist_info['name'], len(tracks)
    except spotipy.SpotifyException as e:
        print(f"Spotify API ошибка для {user_id}: {e}")
        return [], None, 0

if __name__ == "__main__":
    # Тест для одного пользователя
    tracks, name, count = get_spotify_playlist_tracks("https://open.spotify.com/playlist/37i9dQZF1DWXJyjYfQ19m0", "test_user")
    print(f"Плейлист: {name}, Треков: {count}")
    for track in tracks:
        print(f"{track['name']} - {track['artist']}")