# Music API
## Overview

This application serves as an add-on to the Spotify API, providing enhanced functionality for searching and accessing music tracks. It offers endpoints for searching authors, albums, and tracks, similar to the search functionality in Spotify. The key difference is that users can listen to the tracks directly through this application.

## Features

- **Search Endpoints**: 
  - Search for authors (artists)
  - Search for albums
  - Search for tracks
- **Track Playback**:
  - Once a user finds the desired track, they can listen to it using a dedicated endpoint that provides a link to the audio file. This link can be used in frontend applications to play the track.
- **JWT Authentication**
  - Application provides basic JWT authentication with 2 types of tokens: refresh & access

Also there is config provided, where you could set up database url, spotify api access, track saves directories and tokens lifetime

## Endpoints
As FastAPI was used to this project, endpoints documentation provided automatically:

- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Dependencies
- Python 3.10.0
- FastAPI 0.114.0
- SQLAlchemy 2.0.34
- pytubefix 6.16.2
- PyJWT 2.9.0
- Alembic 1.13.2

## Installation

```bash
git clone https://github.com/your-username/music-api.git
cd music-api
pip install -r requirements.txt
```
# Disclaimer
This tool is for educational purposes only.

