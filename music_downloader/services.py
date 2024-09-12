import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pytubefix import YouTube, Search
import config


class MusicSearchService:
    """
    A service that is responsible
    for searching (from Spotify API)
    and downloading tracks (YouTube)

    """

    def __init__(self):
        self.client_id = config.CLIENT_ID
        self.secret = config.CLIENT_SECRET
        self.auth_manager = SpotifyClientCredentials(
            client_id=self.client_id, client_secret=self.secret)
        self.spotify = spotipy.Spotify(auth_manager=self.auth_manager)

    # request for track data that the user wants to receive
    def search_by_query(self, query):
        data = self.spotify.search(query).get('tracks')
        title = data.get('items')[0].get('name')
        author = data.get('items')[0].get('artists')[0].get('name')
        return f'{author}-{title}'

    # request to search detailed data about track by its url
    def search_by_url(self, url):
        data = self.spotify.track(url)
        title = data.get('name')
        author = data.get('artists')[0].get('name')
        return f'{author}-{title}'

    # searching youtube video that matches query
    def get_youtube_url(self, query):
        vids = Search(query)
        # using [0] because in our case, we use the exact name of the track, so the error is minimal
        video_url = vids.videos[0].watch_url
        return video_url

    # downloading video audio from youtube
    def download_track(self, url):
        yt = YouTube(url)
        audio_title = yt.title

        # filename = f"{audio_title}.mp3"
        full_path = os.path.join(config.BASE_DIR, f'{audio_title}.mp3')

        print(f'Downloading to: {full_path}')

        file = yt.streams.get_audio_only().download()
        print(file)
