"""
Requirements:
- spotipy==2.25.0
"""
import spotipy
from spotipy.oauth2 import SpotifyOAuth

CLIENT_ID="<SPOTIFY DEVELOPER APP CLIENT ID>"
CLIENT_SECRET="<SPOTIFY DEVELOPER APP CLIENT ID>"
REDIRECT_URI='http://localhost:8080/callback'
# REDIRECT_URI='https://my.home-assistant.io/redirect/oauth'

# Cookies (retrieved by from web client cookies for an active session)
SP_DC="<ACTIVE SPOTIFY AUTH SESSION COOKIE>"
SP_KEY="<ACTIVE SPOTIFY AUTH SESSION COOKIE>"

USERNAME="1299957985"
OFFICE_SPEAKER_ID="cf01f73d3370695211d0e4d380958dde"
SCOTTS_BIG_BOY_SPEAKER_ID="89bd483827f2955b508d8d9930d978fdf7bb8c18"
SUMMER_JAZZ_PLAYLIST_ID="spotify:playlist:37i9dQZF1DWTKxc7ZObqeH"

scope = "user-read-playback-state,user-modify-playback-state,app-remote-control,user-read-currently-playing"
oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=scope)
sp = spotipy.Spotify(auth_manager=oauth)

print(sp.devices())

# print(sp.transfer_playback(device_id=OFFICE_SPEAKER_ID, force_play=True))

sp.start_playback(
    device_id=OFFICE_SPEAKER_ID,
    context_uri=SUMMER_JAZZ_PLAYLIST_ID,
    offset={"position": 5}  # Start at the 6th song (0-indexed)
)