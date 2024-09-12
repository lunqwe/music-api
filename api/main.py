import uvicorn
from fastapi import FastAPI
from accounts.routes import app as accounts_app
from tracks.routes import app as tracks_app
from config import Base, engine


main_app = FastAPI()
main_app.include_router(accounts_app.router, prefix='/accounts')
main_app.include_router(tracks_app.router, prefix='/tracks')

if __name__ == "__main__":
    # Base.metadata.create_all(bind=engine)
    uvicorn.run('main:main_app', reload=True)