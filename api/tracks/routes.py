from typing import Annotated
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from requests.exceptions import HTTPError
from sqlalchemy.orm import Session
from functools import wraps

from accounts.models import User
from accounts.services import JWTService
import config
from .services import MusicSearchService

app = FastAPI()
music_service = MusicSearchService()

app.mount("/media", StaticFiles(directory=config.MEDIA_DIR), name="media")


def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f'Service is unavailable now. Reason: {e}'
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Unexpected error occurred: {e}'
            )
    return wrapper

@app.get('/search/', tags=['tracks'])
def search(query: str):
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Query is required.'
        )

    result = {
        'tracks': music_service.search_track(query),
        'albums': music_service.search_album(query),
        'artists': music_service.search_artist(query)
    }

    return JSONResponse(result, status_code=status.HTTP_200_OK)


@app.get('/detail/', tags=['tracks'])
@handle_errors
def detail_entity(entity_type: str, uri: str):
    if not entity_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Entity type is required.'
        )

    if entity_type == 'track':
        return music_service.detail_track(track_uri=uri)
    elif entity_type == 'album':
        return music_service.detail_album(album_uri=uri)
    elif entity_type == 'artist':
        return music_service.detail_artist(artist_uri=uri)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid entity type.'
        )

@app.post('/download-track/', tags=['tracks'])
def load_track(track_uri: str,
               current_user: Annotated[User,
                                       Depends(JWTService().get_current_user)],
               db: Session = Depends(config.get_db)):
    return f'{config.BASE_URL}{music_service.listen_track(track_uri, db)}'


@app.get('/media/{track_id}', tags=['tracks'])
def get_track(track_id: str, current_user: Annotated[User, Depends(JWTService().get_current_user)]):
    return FileResponse(f'{config.MEDIA_DIR}\\{track_id}.mp3')
