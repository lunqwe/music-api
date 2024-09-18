from pydantic import BaseModel


class SearchTrack(BaseModel):
    tracks: dict
    albums: dict
    artists: dict
