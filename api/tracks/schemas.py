from pydantic import BaseModel


class TrackBase(BaseModel):
    name: str
