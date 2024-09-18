from sqlalchemy import Column, Integer, String   # ForeignKey
# from sqlalchemy.orm import relationship

from config import Base


class Track(Base):
    __tablename__ = 'tracks'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    track_id = Column(String, unique=True)
    file_path = Column(String)
