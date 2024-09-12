from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta

import config


class User(config.Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    username = Column(String)
    hashed_password = Column(String)
    tokens = relationship("RefreshToken", back_populates="user")


class RefreshToken(config.Base):
    __tablename__ = 'refresh_tokens'

    token = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='tokens')
    expires_at = Column(
        DateTime,
        default=datetime.now(timezone.utc) + timedelta(
            days=config.REFRESH_TOKEN_EXPIRES_DAYS
        ))
