import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# jwt authentication configuration
SECRET_KEY = os.environ.get('SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES_MINUTES = 30
REFRESH_TOKEN_EXPIRES_DAYS = 1

# database configuration
SQLALCHEMY_DATABASE_URL = os.environ.get('SQLALCHEMY_DATABASE_URL')

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
metadata = Base.metadata


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
