Movie Ranker 2026

Overview

This project is a FastAPI web app for tracking watched films/series, building a watchlist,
and publishing blog entries tied to watched titles. The landing page shows two timelines
with rich metadata, and the CRM lets you add/edit/delete entries with TMDB-powered search.

Features

- Watched timeline with ratings, comments, and optional blog entry links.
- Want-to-watch timeline with excitement scores.
- TV Series support with optional season number.
- Blog section with slug-based URLs (e.g., /home-alone).
- Markdown editor with live preview and inline editing for blog posts.
- TMDB integration to search and autofill metadata (synopsis, poster, genres, runtime).
- SQLite persistence.

Tech Stack

- Backend: FastAPI (Python), SQLite, Jinja2 templates
- Frontend: HTML, CSS, vanilla JS
- Data: TMDB API for metadata enrichment
- Auth: HTTP Basic for CRM routes

Directory Structure

- main.py
  - FastAPI app, routing, and template rendering.
- app/models/models.py
  - Pydantic models for watched, planned, and blog posts.
- app/routers/items.py
  - API routes for CRUD, TMDB search/details, and SQLite helpers.
- app/routers/auth.py
  - Basic auth and .env loading.
- app/templates/index.html
  - Landing page with watched + planned timelines.
- app/templates/crm.html
  - Admin console for adding/editing entries and blog posts.
- app/templates/blog.html
  - Blog index page.
- app/templates/blog_post.html
  - Blog detail page (slug-based).
- app/static/style.css
  - Global styling for the app.
- app/static/images
  - Uploaded images.
- app/data/app.db
  - SQLite database (auto-created).

Environment Setup

Create `app/.env` with:

```
BASIC_AUTH_USERNAME=your_username
BASIC_AUTH_PASSWORD=your_password
TMDB_API_KEY=your_tmdb_key
```

`BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD` are used for the CRM Basic Auth.
`TMDB_API_KEY` is used to search and fetch metadata.

Database

SQLite database lives at `app/data/app.db`. The app creates tables on startup and
adds missing columns when new fields are introduced.

Tables

- watched
  - id, title, comment, score, image_url, watch_date, content_type, season
  - synopsis, release_year, runtime, genres, tmdb_id, tmdb_rating, poster_url
- want_to_watch
  - id, title, image_url, launch_date, excitement, content_type, season
  - synopsis, release_year, runtime, genres, tmdb_id, tmdb_rating, poster_url
- blog_posts
  - id, watched_id, title, slug, body, created_at

Blog System

- Each blog post is tied to a watched item via `watched_id`.
- Blog URLs use the slug only. Example: `http://localhost:8000/home-alone`.
- The landing page links to the blog post only if a slug exists for that watched item.
- Markdown is rendered on the blog list and blog detail pages.

TMDB Integration

Search:

- Endpoint: `GET /api/tmdb/search?query=...`
- Uses TMDB `search/multi`.
- Returns movie and TV results with poster URLs.

Details:

- Endpoint: `GET /api/tmdb/details/{media_type}/{tmdb_id}`
- Returns title, synopsis, release year, runtime, genres, rating, poster URL.

CRM Use:

- Use the TMDB search panel in either form.
- Select a result to autofill fields and hidden metadata inputs.
- The poster URL is stored and used for card display.

Routing

- `/` Landing page
- `/crm` Admin console (Basic Auth required)
- `/blog` Blog index
- `/{slug}` Blog detail (slug-based)

API

- `/api/watched`
  - GET list
  - POST create (form data)
  - PUT update (JSON body)
  - DELETE remove
- `/api/want-to-watch`
  - GET list
  - POST create (form data)
  - PUT update (JSON body)
  - DELETE remove
- `/api/blog`
  - GET list
  - POST create (form data)
  - PUT update (JSON body)
  - DELETE remove
- `/api/tmdb/search`
  - GET search
- `/api/tmdb/details/{media_type}/{tmdb_id}`
  - GET details

UI Notes

- Landing cards include season badges for TV series.
- Metadata row shows release year, runtime, genres, and TMDB rating when available.
- Synopsis is shown if present.
- Poster ratio is 2:3.

Running the App

From the project root:

```
uvicorn main:app --reload
```

Open:

- `http://localhost:8000` for the landing page.
- `http://localhost:8000/crm` for the admin console.

Data Entry Flow

1. Use TMDB search to auto-fill or manually enter the data.
2. Submit watched or planned entries.
3. Create a blog entry for a watched item and set a slug.
4. The landing page will show a blog link when a post exists.
