import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pytubefix import YouTube, Search
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import config
from .models import Track


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
    def download_track(self, track_id: str, url: str):
        yt = YouTube(url)
        downloaded_file = yt.streams.get_audio_only().download(
            output_path=config.MEDIA_DIR, filename=track_id, mp3=True)
        if downloaded_file:
            return downloaded_file

    def search_track(self, query: str) -> list[dict]:
        response = self.spotify.search(query, type='track')
        tracks = response.get('tracks', {}).get('items', [])

        result = []
        for track in tracks:
            track_data = {
                'entity_type': 'track',
                'name': track.get('name'),
                'artists': [
                    {'name': artist.get('name'), 'uri': artist.get('uri')}
                    for artist in track.get('artists', [])
                ],
                'cover_url': track.get('album', {}).get('images', [{}])[0].get('url'),
                'duration_ms': track.get('duration_ms'),
                'spotify_uri': track.get('uri')
            }
            result.append(track_data)

        return result

    def search_album(self, query: str) -> list[dict]:
        response = self.spotify.search(query, type='album')
        albums = response.get('albums').get('items')[:1]
        result = []
        for album in albums:
            album_data = {
                'entity_type': 'album',
                'uri': album.get('uri'),
                'name': album.get('name'),
                'artists': [
                    {'name': artist.get('name'), 'uri': artist.get('uri')}
                    for artist in album.get('artists', [])
                ],
                'total_tracks': album.get('total_tracks'),
                'cover_url': album.get('images')[0].get('url'),
                'release_date': album.get('release_date')

            }
            result.append(album_data)
        return result

    def search_artist(self, query: str) -> list[dict]:
        response = self.spotify.search(query, type='artist')
        artists = response.get('artists').get('items')
        result = []
        for artist in artists:
            artist_data = {
                'entity_type': 'artist',
                'name': artist.get('name'),
                'uri': artist.get('uri'),
                'image': artist.get('images')[0].get('url'),
                'genres': artist.get('genres')
            }
            result.append(artist_data)
        return result

    def detail_album_tracks(self, tracks: list) -> list:
        result = []
        for track in tracks:
            track_data = {
                'name': track.get('name'),
                'duration_ms': track.get('duration_ms'),
                'spotify_uri': track.get('uri')
            }
            result.append(track_data)
        return result

    def detail_album(self, album_uri: str) -> dict:
        response = self.spotify.album(album_uri)
        album_data = {
            'uri': response.get('uri'),
            'name': response.get('name'),
            'artists': [
                {'name': artist.get('name'), 'uri': artist.get('uri')}
                for artist in response.get('artists', [])
            ],
            'total_tracks': response.get('total_tracks'),
            'cover_url': response.get('images')[0].get('url'),
            'release_date': response.get('release_data')

        }
        tracks = self.detail_album_tracks(response.get('tracks').get('items'))
        album_data['tracks'] = tracks
        return album_data

    def detail_artist_albums(self, artist_uri: str) -> list[dict]:
        response = self.spotify.artist_albums(artist_uri, limit=50)
        albums = response.get('items')
        result = []
        for album in albums:
            uri = album.get('uri')
            result.append(self.detail_album(uri))
        return result

    def detail_artist(self, artist_uri: str) -> dict:
        response = self.spotify.artist(artist_id=artist_uri)
        artist_data = {
            'name': response.get('name'),
            'uri': response.get('uri'),
            'image': response.get('images')[0].get('url'),
            'genres': response.get('genres')
        }
        top_tracks = self.spotify.artist_top_tracks(artist_uri, country='UA').get('tracks')
        result = self.detail_album_tracks(top_tracks)
        artist_data['top_tracks'] = result
        albums = self.detail_artist_albums(artist_uri)
        artist_data['albums'] = albums
        return artist_data

    def detail_track(self, track_uri: str) -> dict:
        track = self.spotify.track(track_id=track_uri)
        track_data = {
            'name': track.get('name'),
            'artists': [
                {'name': artist.get('name'), 'uri': artist.get('uri')}
                for artist in track.get('artists', [])
            ],
            'cover_url': track.get('album', {}).get('images', [{}])[0].get('url'),
            'duration_ms': track.get('duration_ms'),
            'spotify_uri': track.get('uri')
        }
        return track_data

    # returns url to listen track
    def listen_track(self, track_uri: str, db: Session) -> str:
        track_data = self.spotify.track(track_uri)
        track_id = track_uri.split(':')[2]
        track_in_db = db.query(Track).filter(Track.track_id == track_id).first()
        if not track_in_db:
            name = track_data.get('name')
            artist = track_data.get('artists')[0].get('name')
            dowload_query = f'{artist} - {name}'
            file_path = self.download_track(
                track_id=track_id,
                url=self.get_youtube_url(dowload_query)
            )
            try:
                track = Track(
                    name=dowload_query,
                    track_id=track_id,
                    file_path=file_path
                )
                db.add(track)
                db.commit()
            except (IntegrityError, ValueError):
                db.rollback()
                raise
        track_url = f'/tracks/media/{track_id}'
        return track_url
