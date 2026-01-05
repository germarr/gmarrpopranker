from fastapi import FastAPI, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.routers.auth import get_current_username
from app.routers import items

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(items.router, prefix="/api", tags=["items"])

@app.on_event("startup")
def startup():
    items.init_db()

@app.get("/")
def read_root(request: Request):
    watched_list = items.get_watched_list()
    want_to_watch_list = items.get_want_to_watch_list()
    watched_ids = [item["id"] for item in watched_list]
    blog_map = items.get_blog_slug_map(watched_ids)
    for item in watched_list:
        item["blog_slug"] = blog_map.get(item["id"])
    watched_count = len(watched_list)
    planned_count = len(want_to_watch_list)
    watched_avg_score = (
        sum(item.get("score", 0) for item in watched_list) / watched_count
        if watched_count
        else 0
    )
    planned_avg_excitement = (
        sum(item.get("excitement", 0) for item in want_to_watch_list) / planned_count
        if planned_count
        else 0
    )
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "watched_list": watched_list,
            "want_to_watch_list": want_to_watch_list,
            "watched_count": watched_count,
            "planned_count": planned_count,
            "watched_avg_score": round(watched_avg_score, 1),
            "planned_avg_excitement": round(planned_avg_excitement, 1)
        }
    )

@app.get("/blog")
def blog(request: Request):
    posts = items.get_blog_posts()
    return templates.TemplateResponse(request, "blog.html", {"posts": posts})

@app.get("/top")
def top_list(request: Request):
    all_top = items.get_top_list()
    top_ids = [item["id"] for item in all_top]
    blog_map = items.get_blog_slug_map(top_ids)
    for item in all_top:
        item["blog_slug"] = blog_map.get(item["id"])
    top_movies = [item for item in all_top if item["content_type"] == "Movie"]
    top_series = [item for item in all_top if item["content_type"] == "TV Series"]
    return templates.TemplateResponse(request, "top.html", {"top_movies": top_movies, "top_series": top_series})

@app.get("/secure")
def read_secure(username: str = Depends(get_current_username)):
    return {"message": f"Hello {username}, you are authenticated!"}

@app.get("/crm", dependencies=[Depends(get_current_username)])
def crm(request: Request):
    return templates.TemplateResponse(request, "crm_landing.html")

@app.get("/crm-library", dependencies=[Depends(get_current_username)])
def crm_library(request: Request):
    return templates.TemplateResponse(request, "crm_library.html")

@app.get("/crm-simple", dependencies=[Depends(get_current_username)])
def crm_simple(request: Request):
    return templates.TemplateResponse(request, "crm_simple.html")

@app.get("/crm-blog", dependencies=[Depends(get_current_username)])
def crm_blog(request: Request):
    return templates.TemplateResponse(request, "crm_blog.html")

@app.get("/crm-tmdb", dependencies=[Depends(get_current_username)])
def crm_tmdb(request: Request):
    return templates.TemplateResponse(request, "crm_tmdb.html")

@app.get("/crm-top", dependencies=[Depends(get_current_username)])
def crm_top(request: Request):
    return templates.TemplateResponse(request, "crm_top.html")

@app.get("/blog/{slug}")
def blog_post(request: Request, slug: str):
    post = items.get_blog_post_by_slug(slug)
    if not post:
        return templates.TemplateResponse(request, "blog_post.html", {"post": None}, status_code=404)
    return templates.TemplateResponse(request, "blog_post.html", {"post": post})
