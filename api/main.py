import uvicorn
from fastapi import FastAPI
from accounts.routes import app as accounts_app
from tracks.routes import app as tracks_app


app = FastAPI()
app.include_router(accounts_app.router, prefix='/accounts')
app.include_router(tracks_app.router, prefix='/tracks')

if __name__ == "__main__":
    uvicorn.run('main:app', reload=True)
