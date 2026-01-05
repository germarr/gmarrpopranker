from pydantic import BaseModel, conint
from typing import Optional
from datetime import date

class Watched(BaseModel):
    id: int
    title: str
    comment: str
    score: conint(ge=0, le=10)
    image_url: str
    watch_date: date
    content_type: str
    season: Optional[conint(ge=1)] = None
    synopsis: Optional[str] = None
    release_year: Optional[int] = None
    release_date: Optional[date] = None
    runtime: Optional[int] = None
    genres: Optional[str] = None
    tmdb_id: Optional[int] = None
    tmdb_rating: Optional[float] = None
    poster_url: Optional[str] = None
    top_rank: Optional[int] = None

class WantToWatch(BaseModel):
    id: int
    title: str
    image_url: str
    launch_date: date
    excitement: conint(ge=1, le=10)
    content_type: str
    season: Optional[conint(ge=1)] = None
    synopsis: Optional[str] = None
    release_year: Optional[int] = None
    runtime: Optional[int] = None
    genres: Optional[str] = None
    tmdb_id: Optional[int] = None
    tmdb_rating: Optional[float] = None
    poster_url: Optional[str] = None

class BlogPost(BaseModel):
    id: int
    watched_id: int
    title: str
    slug: str
    body: str
    created_at: str
