from typing import Annotated
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from requests.exceptions import HTTPError
from sqlalchemy.orm import Session

from accounts.models import User
from accounts.services import JWTService
import config
from .services import MusicSearchService

app = FastAPI()
music_service = MusicSearchService()

app.mount("/media", StaticFiles(directory=config.MEDIA_DIR), name="media")

@app.get('/search/', tags=['tracks'])
def search(query: str):
    if query:
        try:
            result = {
                'tracks': music_service.search_track(query),
                'albums': music_service.search_album(query),
                'artists': music_service.search_artist(query)
            }
        
            return JSONResponse(result, status_code=status.HTTP_200_OK)
        except HTTPError as e:
            raise ConnectionError(
                f'Service is unavailable now. Reason: {e}',
                status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            raise HTTPException(
                detail=f'Unexpected error occured: {e}',
                status_code=status.HTTP_400_BAD_REQUEST
                )
    return HTTPException(
        detail='Query is required.',
        status_code=status.HTTP_400_BAD_REQUEST)


@app.get('/detail/', tags=['tracks'])
def detail_entity(entity_type: str, uri: str):
    if entity_type:
        try:
            if entity_type == 'track':
                return music_service.detail_track(track_uri=uri)
            elif entity_type == 'album':
                return music_service.detail_album(album_uri=uri)
            elif entity_type == 'artist':
                return music_service.detail_artist(artist_uri=uri)
        except HTTPError as e:
            return HTTPException(
                f'Service is unavailable now. Reason: {e}',
                status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            raise HTTPException(
                detail=f'Unexpected error occured: {e}',
                status_code=status.HTTP_400_BAD_REQUEST
                )
    raise HTTPException(
        detail='Entity type is required.',
        status_code=status.HTTP_400_BAD_REQUEST
        )

@app.post('/download-track/', tags=['tracks'])
def load_track(track_uri: str, current_user: Annotated[User, Depends(JWTService().get_current_user)], db: Session = Depends(config.get_db)):
    return f'{config.BASE_URL}{music_service.listen_track(track_uri, db)}'
    

@app.get('/media/{track_id}', tags=['tracks'])
def get_track(track_id: str, current_user: Annotated[User, Depends(JWTService().get_current_user)]):
    return FileResponse(f'{config.MEDIA_DIR}\{track_id}.mp3')
