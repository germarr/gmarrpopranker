from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from app.models.models import Watched, WantToWatch, BlogPost
from app.routers.auth import get_current_username
from typing import List, Optional
import shutil
from PIL import Image
from datetime import date, datetime
import sqlite3
from pathlib import Path
from uuid import uuid4
import re
import os
import json
import logging
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote_plus
from dotenv import load_dotenv, find_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

DB_PATH = "app/data/app.db"
IMAGES_DIR = "app/static/images"

dotenv_path = find_dotenv(filename="app/.env", usecwd=True)
if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path)
    logger.info(f"Loaded .env file from: {dotenv_path}")
else:
    logger.warning("WARNING: .env file not found or not loaded correctly.")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    Path("app/data").mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS watched (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                comment TEXT NOT NULL,
                score INTEGER NOT NULL,
                image_url TEXT NOT NULL,
                watch_date TEXT NOT NULL,
                content_type TEXT NOT NULL,
                season INTEGER,
                synopsis TEXT,
                release_year INTEGER,
                runtime INTEGER,
                genres TEXT,
                tmdb_id INTEGER,
                tmdb_rating REAL,
                poster_url TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS want_to_watch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                image_url TEXT NOT NULL,
                launch_date TEXT NOT NULL,
                excitement INTEGER NOT NULL,
                content_type TEXT NOT NULL,
                season INTEGER,
                synopsis TEXT,
                release_year INTEGER,
                runtime INTEGER,
                genres TEXT,
                tmdb_id INTEGER,
                tmdb_rating REAL,
                poster_url TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS blog_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                watched_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (watched_id) REFERENCES watched(id) ON DELETE CASCADE
            )
            """
        )
        ensure_column(conn, "watched", "season", "INTEGER")
        ensure_column(conn, "want_to_watch", "season", "INTEGER")
        ensure_column(conn, "watched", "synopsis", "TEXT")
        ensure_column(conn, "watched", "release_year", "INTEGER")
        ensure_column(conn, "watched", "runtime", "INTEGER")
        ensure_column(conn, "watched", "genres", "TEXT")
        ensure_column(conn, "watched", "tmdb_id", "INTEGER")
        ensure_column(conn, "watched", "tmdb_rating", "REAL")
        ensure_column(conn, "watched", "poster_url", "TEXT")
        ensure_column(conn, "watched", "top_rank", "INTEGER")
        ensure_column(conn, "watched", "release_date", "TEXT")
        ensure_column(conn, "want_to_watch", "synopsis", "TEXT")
        ensure_column(conn, "want_to_watch", "release_year", "INTEGER")
        ensure_column(conn, "want_to_watch", "runtime", "INTEGER")
        ensure_column(conn, "want_to_watch", "genres", "TEXT")
        ensure_column(conn, "want_to_watch", "tmdb_id", "INTEGER")
        ensure_column(conn, "want_to_watch", "tmdb_rating", "REAL")
        ensure_column(conn, "want_to_watch", "poster_url", "TEXT")
        conn.commit()

def save_and_resize_image(image_file: UploadFile, output_path: str):
    with open(output_path, "wb") as buffer:
        shutil.copyfileobj(image_file.file, buffer)
    
    with Image.open(output_path) as img:
        width, height = img.size
        target_ratio = 2/3
        current_ratio = width/height

        if current_ratio > target_ratio:
            new_width = int(target_ratio * height)
            left = (width - new_width) / 2
            right = (width + new_width) / 2
            top = 0
            bottom = height
            img = img.crop((left, top, right, bottom))
        else:
            new_height = int(width / target_ratio)
            top = (height - new_height) / 2
            bottom = (height + new_height) / 2
            left = 0
            right = width
            img = img.crop((left, top, right, bottom))
        
        img.save(output_path)


def ensure_column(conn: sqlite3.Connection, table: str, column: str, column_type: str):
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")

def get_tmdb_key() -> str:
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        logger.error("TMDB_API_KEY is missing. Check app/.env.")
        raise HTTPException(status_code=500, detail="TMDB API key is not configured")
    return api_key

def tmdb_request(endpoint: str, params: dict) -> dict:
    api_key = get_tmdb_key()

    # Check if this is a JWT token (Read Access Token) or v3 API key
    is_bearer_token = api_key.startswith('eyJ')

    if is_bearer_token:
        # Use Bearer token authentication (for Read Access Tokens)
        url = f"https://api.themoviedb.org/3{endpoint}"
        if params:
            query = urlencode(params, quote_via=quote_plus)
            url = f"{url}?{query}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        logger.info(f"Using Bearer token authentication for TMDB request to {endpoint}")
    else:
        # Use API key in query parameter (for v3 API keys)
        params["api_key"] = api_key
        query = urlencode(params, quote_via=quote_plus)
        url = f"https://api.themoviedb.org/3{endpoint}?{query}"
        headers = {"Accept": "application/json"}
        logger.info(f"Using API key authentication for TMDB request to {endpoint}")

    request = Request(url, headers=headers)
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))

def tmdb_poster_url(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    return f"https://image.tmdb.org/t/p/w500{path}"

def tmdb_year(date_value: Optional[str]) -> Optional[int]:
    if not date_value:
        return None
    try:
        return int(date_value.split("-")[0])
    except (ValueError, AttributeError):
        return None


def normalize_slug(slug: str) -> str:
    slug = slug.strip().lower()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug

def get_blog_slug_map(watched_ids: List[int]) -> dict:
    if not watched_ids:
        return {}
    placeholders = ",".join("?" for _ in watched_ids)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT watched_id, slug
            FROM blog_posts
            WHERE watched_id IN ({placeholders})
            """,
            watched_ids,
        ).fetchall()
    return {row["watched_id"]: row["slug"] for row in rows}

def get_blog_posts() -> List[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT b.id, b.watched_id, b.title, b.slug, b.body, b.created_at,
                   w.poster_url, w.image_url, w.score, w.release_year, w.genres, w.tmdb_rating, w.content_type
            FROM blog_posts b
            JOIN watched w ON b.watched_id = w.id
            ORDER BY b.created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]

def get_blog_post_by_slug(slug: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT b.id, b.watched_id, b.title, b.slug, b.body, b.created_at,
                   w.title as movie_title, w.image_url, w.score, w.release_year, w.poster_url,
                   w.content_type, w.season, w.synopsis, w.runtime, w.genres, w.tmdb_rating, w.watch_date
            FROM blog_posts b
            JOIN watched w ON b.watched_id = w.id
            WHERE b.slug = ?
            """,
            (slug,),
        ).fetchone()
    return dict(row) if row else None


@router.get("/top", response_model=List[Watched])
def get_top_list():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, title, comment, score, image_url, watch_date, content_type, season,
                   synopsis, release_year, release_date, runtime, genres, tmdb_id, tmdb_rating, poster_url, top_rank
            FROM watched
            WHERE top_rank IS NOT NULL
            ORDER BY top_rank ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]

@router.get("/watched", response_model=List[Watched])
def get_watched_list():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, title, comment, score, image_url, watch_date, content_type, season,
                   synopsis, release_year, release_date, runtime, genres, tmdb_id, tmdb_rating, poster_url, top_rank
            FROM watched
            WHERE top_rank IS NULL
            ORDER BY watch_date DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]

@router.post("/watched", response_model=Watched, dependencies=[Depends(get_current_username)])
def add_to_watched_list(
    title: str = Form(...),
    score: int = Form(...),
    comment: str = Form(...),
    watch_date: date = Form(...),
    content_type: str = Form(...),
    season: Optional[int] = Form(None),
    synopsis: Optional[str] = Form(None),
    release_year: Optional[int] = Form(None),
    release_date: Optional[date] = Form(None),
    runtime: Optional[int] = Form(None),
    genres: Optional[str] = Form(None),
    tmdb_id: Optional[int] = Form(None),
    tmdb_rating: Optional[float] = Form(None),
    poster_url: Optional[str] = Form(None),
    top_rank: Optional[int] = Form(None),
    image_url: Optional[str] = Form(None),
    image_file: Optional[UploadFile] = File(None)
):
    if image_url is not None:
        image_url = image_url.strip() or None
    if content_type != "TV Series":
        season = None
    has_image_url = bool(image_url)
    has_image_file = image_file is not None and bool(image_file.filename)
    if not has_image_url and not has_image_file:
        raise HTTPException(status_code=400, detail="Either image_url or image_file must be provided")

    if has_image_file:
        image_filename = f"{uuid4().hex}_{image_file.filename}"
        image_path = f"{IMAGES_DIR}/{image_filename}"
        save_and_resize_image(image_file, image_path)
        image_url = f"/static/images/{image_filename}"
        poster_url = image_url
    elif image_url:
        poster_url = poster_url or image_url

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO watched (
                title, comment, score, image_url, watch_date, content_type, season,
                synopsis, release_year, release_date, runtime, genres, tmdb_id, tmdb_rating, poster_url, top_rank
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                comment,
                score,
                image_url,
                str(watch_date),
                content_type,
                season,
                synopsis,
                release_year,
                str(release_date) if release_date else None,
                runtime,
                genres,
                tmdb_id,
                tmdb_rating,
                poster_url,
                top_rank,
            ),
        )
        conn.commit()
        item_id = cursor.lastrowid
    return Watched(
        id=item_id,
        title=title,
        score=score,
        comment=comment,
        image_url=image_url,
        watch_date=watch_date,
        content_type=content_type,
        season=season,
        synopsis=synopsis,
        release_year=release_year,
        release_date=release_date,
        runtime=runtime,
        genres=genres,
        tmdb_id=tmdb_id,
        tmdb_rating=tmdb_rating,
        poster_url=poster_url,
        top_rank=top_rank,
    )

@router.put("/watched/{item_id}", response_model=Watched, dependencies=[Depends(get_current_username)])
def update_watched_item(item_id: int, updated_item: Watched):
    with get_connection() as conn:
        result = conn.execute(
            """
            UPDATE watched
            SET title = ?, comment = ?, score = ?, image_url = ?, watch_date = ?, content_type = ?, season = ?,
                synopsis = ?, release_year = ?, release_date = ?, runtime = ?, genres = ?, tmdb_id = ?, tmdb_rating = ?, poster_url = ?, top_rank = ?
            WHERE id = ?
            """,
            (
                updated_item.title,
                updated_item.comment,
                updated_item.score,
                updated_item.image_url,
                str(updated_item.watch_date),
                updated_item.content_type,
                updated_item.season,
                updated_item.synopsis,
                updated_item.release_year,
                str(updated_item.release_date) if updated_item.release_date else None,
                updated_item.runtime,
                updated_item.genres,
                updated_item.tmdb_id,
                updated_item.tmdb_rating,
                updated_item.poster_url,
                updated_item.top_rank,
                item_id,
            ),
        )
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
    updated_item.id = item_id
    return updated_item

@router.delete("/watched/{item_id}", dependencies=[Depends(get_current_username)])
def delete_watched_item(item_id: int):
    with get_connection() as conn:
        result = conn.execute("DELETE FROM watched WHERE id = ?", (item_id,))
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}

@router.get("/want-to-watch", response_model=List[WantToWatch])
def get_want_to_watch_list():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, title, image_url, launch_date, excitement, content_type, season,
                   synopsis, release_year, runtime, genres, tmdb_id, tmdb_rating, poster_url
            FROM want_to_watch
            ORDER BY launch_date DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]

@router.post("/want-to-watch", response_model=WantToWatch, dependencies=[Depends(get_current_username)])
def add_to_want_to_watch_list(
    title: str = Form(...),
    launch_date: date = Form(...),
    excitement: int = Form(...),
    content_type: str = Form(...),
    season: Optional[int] = Form(None),
    synopsis: Optional[str] = Form(None),
    release_year: Optional[int] = Form(None),
    runtime: Optional[int] = Form(None),
    genres: Optional[str] = Form(None),
    tmdb_id: Optional[int] = Form(None),
    tmdb_rating: Optional[float] = Form(None),
    poster_url: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    image_file: Optional[UploadFile] = File(None)
):
    if image_url is not None:
        image_url = image_url.strip() or None
    if content_type != "TV Series":
        season = None
    has_image_url = bool(image_url)
    has_image_file = image_file is not None and bool(image_file.filename)
    if not has_image_url and not has_image_file:
        raise HTTPException(status_code=400, detail="Either image_url or image_file must be provided")

    if has_image_file:
        image_filename = f"{uuid4().hex}_{image_file.filename}"
        image_path = f"{IMAGES_DIR}/{image_filename}"
        save_and_resize_image(image_file, image_path)
        image_url = f"/static/images/{image_filename}"
        poster_url = image_url
    elif image_url:
        poster_url = poster_url or image_url

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO want_to_watch (
                title, image_url, launch_date, excitement, content_type, season,
                synopsis, release_year, runtime, genres, tmdb_id, tmdb_rating, poster_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                image_url,
                str(launch_date),
                excitement,
                content_type,
                season,
                synopsis,
                release_year,
                runtime,
                genres,
                tmdb_id,
                tmdb_rating,
                poster_url,
            ),
        )
        conn.commit()
        item_id = cursor.lastrowid
    return WantToWatch(
        id=item_id,
        title=title,
        image_url=image_url,
        launch_date=launch_date,
        excitement=excitement,
        content_type=content_type,
        season=season,
        synopsis=synopsis,
        release_year=release_year,
        runtime=runtime,
        genres=genres,
        tmdb_id=tmdb_id,
        tmdb_rating=tmdb_rating,
        poster_url=poster_url,
    )

@router.put("/want-to-watch/{item_id}", response_model=WantToWatch, dependencies=[Depends(get_current_username)])
def update_want_to_watch_item(item_id: int, updated_item: WantToWatch):
    with get_connection() as conn:
        result = conn.execute(
            """
            UPDATE want_to_watch
            SET title = ?, image_url = ?, launch_date = ?, excitement = ?, content_type = ?, season = ?,
                synopsis = ?, release_year = ?, runtime = ?, genres = ?, tmdb_id = ?, tmdb_rating = ?, poster_url = ?
            WHERE id = ?
            """,
            (
                updated_item.title,
                updated_item.image_url,
                str(updated_item.launch_date),
                updated_item.excitement,
                updated_item.content_type,
                updated_item.season,
                updated_item.synopsis,
                updated_item.release_year,
                updated_item.runtime,
                updated_item.genres,
                updated_item.tmdb_id,
                updated_item.tmdb_rating,
                updated_item.poster_url,
                item_id,
            ),
        )
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
    updated_item.id = item_id
    return updated_item

@router.delete("/want-to-watch/{item_id}", dependencies=[Depends(get_current_username)])
def delete_want_to_watch_item(item_id: int):
    with get_connection() as conn:
        result = conn.execute("DELETE FROM want_to_watch WHERE id = ?", (item_id,))
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}

@router.get("/tmdb/search")
def tmdb_search(query: str, media_type: Optional[str] = None):
    logger.info(f"TMDB search requested: query='{query}', media_type='{media_type}'")
    if not query.strip():
        logger.warning("TMDB search aborted: empty query")
        return []
    try:
        response = tmdb_request(
            "/search/multi",
            {"query": query, "include_adult": "false"},
        )
    except Exception as exc:
        logger.error(f"TMDB search failed: {exc}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"TMDB search failed: {str(exc)}")
    results = []
    for item in response.get("results", []):
        item_type = item.get("media_type")
        if item_type not in {"movie", "tv"}:
            continue
        if media_type and item_type != media_type:
            continue
        title = item.get("title") or item.get("name")
        release_date = item.get("release_date") or item.get("first_air_date")
        results.append(
            {
                "id": item.get("id"),
                "media_type": item_type,
                "title": title,
                "release_date": release_date,
                "year": tmdb_year(release_date),
                "overview": item.get("overview"),
                "poster_url": tmdb_poster_url(item.get("poster_path")),
                "rating": item.get("vote_average"),
            }
        )
    logger.info(f"TMDB search returned {len(results)} results")
    return results

@router.get("/tmdb/details/{media_type}/{tmdb_id}")
def tmdb_details(media_type: str, tmdb_id: int):
    logger.info(f"TMDB details requested: media_type='{media_type}', id={tmdb_id}")
    if media_type not in {"movie", "tv"}:
        raise HTTPException(status_code=400, detail="Unsupported media type")
    try:
        response = tmdb_request(
            f"/{media_type}/{tmdb_id}",
            {},
        )
    except Exception as exc:
        logger.error(f"TMDB details failed: {exc}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"TMDB details failed: {str(exc)}")
    title = response.get("title") or response.get("name")
    release_date = response.get("release_date") or response.get("first_air_date")
    genres = ", ".join([g["name"] for g in response.get("genres", [])])
    runtime = None
    if media_type == "movie":
        runtime = response.get("runtime")
    else:
        runtimes = response.get("episode_run_time") or []
        runtime = runtimes[0] if runtimes else None
    return {
        "tmdb_id": response.get("id"),
        "title": title,
        "content_type": "Movie" if media_type == "movie" else "TV Series",
        "synopsis": response.get("overview"),
        "release_year": tmdb_year(release_date),
        "release_date": release_date,
        "runtime": runtime,
        "genres": genres,
        "tmdb_rating": response.get("vote_average"),
        "poster_url": tmdb_poster_url(response.get("poster_path")),
    }

@router.get("/blog", response_model=List[BlogPost])
def list_blog_posts():
    return get_blog_posts()

@router.post("/blog", response_model=BlogPost, dependencies=[Depends(get_current_username)])
def add_blog_post(
    watched_id: int = Form(...),
    title: str = Form(...),
    slug: str = Form(...),
    body: str = Form(...)
):
    logger.info(f"Blog post creation requested: watched_id={watched_id}, title='{title}', slug='{slug}'")
    slug_value = normalize_slug(slug)
    if not slug_value:
        logger.error(f"Invalid slug provided: '{slug}'")
        raise HTTPException(status_code=400, detail="Slug must be provided")

    with get_connection() as conn:
        watched_row = conn.execute("SELECT id FROM watched WHERE id = ?", (watched_id,)).fetchone()
        if not watched_row:
            logger.error(f"Watched item not found: id={watched_id}")
            raise HTTPException(status_code=400, detail="Watched item not found")

        created_at = datetime.utcnow().isoformat()
        try:
            cursor = conn.execute(
                """
                INSERT INTO blog_posts (watched_id, title, slug, body, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (watched_id, title, slug_value, body, created_at),
            )
            conn.commit()
            post_id = cursor.lastrowid
            logger.info(f"Blog post created successfully: id={post_id}, slug='{slug_value}'")
        except sqlite3.IntegrityError as e:
            logger.error(f"Slug already exists: '{slug_value}' - {e}")
            raise HTTPException(status_code=400, detail="Slug already exists")

    return BlogPost(
        id=post_id,
        watched_id=watched_id,
        title=title,
        slug=slug_value,
        body=body,
        created_at=created_at,
    )

@router.put("/blog/{post_id}", response_model=BlogPost, dependencies=[Depends(get_current_username)])
def update_blog_post(post_id: int, updated_post: BlogPost):
    slug_value = normalize_slug(updated_post.slug)
    if not slug_value:
        raise HTTPException(status_code=400, detail="Slug must be provided")

    with get_connection() as conn:
        try:
            result = conn.execute(
                """
                UPDATE blog_posts
                SET watched_id = ?, title = ?, slug = ?, body = ?, created_at = ?
                WHERE id = ?
                """,
                (
                    updated_post.watched_id,
                    updated_post.title,
                    slug_value,
                    updated_post.body,
                    updated_post.created_at,
                    post_id,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Slug already exists")
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Post not found")

    updated_post.id = post_id
    updated_post.slug = slug_value
    return updated_post

@router.delete("/blog/{post_id}", dependencies=[Depends(get_current_username)])
def delete_blog_post(post_id: int):
    with get_connection() as conn:
        result = conn.execute("DELETE FROM blog_posts WHERE id = ?", (post_id,))
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Post not found")
    return {"message": "Post deleted successfully"}
