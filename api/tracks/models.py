from sqlalchemy import Column, Integer, String   # ForeignKey
# from sqlalchemy.orm import relationship

from config import Base


class Track(Base):
    __tablename__ = 'tracks'

    id = Column(Integer, primary_key=True)
    name = String(length=255)
    uri = String(length=500)
    duration_ms = Integer()
    file_path = String(length=300) # TODO: add files extension (?) 
