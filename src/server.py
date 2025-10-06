from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from config import STATIC_DIR, TEMPLATES_DIR, DATA_DIR
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timedelta
import database
import argparse
import uvicorn
import json
import random
import os
import secrets

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    database.init_database()
    print("✓ Database initialized")

# Admin authentication
ADMIN_USER = os.getenv("USER", "admin")
ADMIN_PASSWORD = os.getenv("PASSWORD", "admin")
admin_sessions = {}  # session_token -> expiry_time

def create_session():
    token = secrets.token_urlsafe(32)
    admin_sessions[token] = datetime.now() + timedelta(hours=24)
    return token

def verify_session(request: Request):
    token = request.cookies.get("admin_session")
    if not token or token not in admin_sessions:
        return False
    if admin_sessions[token] < datetime.now():
        del admin_sessions[token]
        return False
    return True


def get_all_stories():
    """Retrieve all available story directories and their metadata."""
    stories = []
    data_path = Path(DATA_DIR)

    for story_dir in data_path.iterdir():
        if story_dir.is_dir():
            story_json = story_dir / "story.json"
            story_mp3 = story_dir / "story.mp3"
            cover_png = story_dir / "cover.png"

            if story_json.exists() and story_mp3.exists() and cover_png.exists():
                with open(story_json, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    stories.append({
                        "id": story_dir.name,
                        "title": metadata.get("title", "Unbekannt"),
                        "summary": metadata.get("summary", ""),
                        "audio_url": f"/data/{story_dir.name}/story.mp3",
                        "cover_url": f"/data/{story_dir.name}/cover.png"
                    })

    return stories


@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    """Serve the main application page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/impressum", response_class=HTMLResponse)
async def impressum(request: Request):
    """Serve the impressum page."""
    return templates.TemplateResponse("impressum.html", {"request": request})


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """Serve the about page."""
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/api/stories")
async def get_stories():
    """API endpoint to get all available stories."""
    stories = get_all_stories()
    return JSONResponse(content={"stories": stories})


@app.get("/api/story/random")
async def get_random_story():
    """API endpoint to get a random story."""
    stories = get_all_stories()
    if stories:
        return JSONResponse(content=random.choice(stories))
    return JSONResponse(content={"error": "No stories available"}, status_code=404)


@app.post("/api/playtime")
async def track_playtime(request: Request):
    """Track playtime for analytics."""
    try:
        data = await request.json()
        story_id = data.get("story_id")
        play_duration = data.get("play_duration", 0)

        if not story_id:
            return JSONResponse(content={"error": "story_id required"}, status_code=400)

        success = database.track_playtime(story_id, play_duration)

        if success:
            return JSONResponse(content={"success": True})
        else:
            return JSONResponse(content={"error": "Failed to track playtime"}, status_code=500)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# Admin routes
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Serve admin login page."""
    if verify_session(request):
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse("admin_login.html", {"request": request})


@app.post("/admin/login")
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle admin login."""
    if username == ADMIN_USER and password == ADMIN_PASSWORD:
        token = create_session()
        response = RedirectResponse(url="/admin", status_code=302)
        response.set_cookie(key="admin_session", value=token, httponly=True, max_age=86400)
        return response
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Ungültige Anmeldedaten"})


@app.get("/admin/logout")
async def admin_logout(request: Request):
    """Handle admin logout."""
    token = request.cookies.get("admin_session")
    if token and token in admin_sessions:
        del admin_sessions[token]
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_session")
    return response


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Serve admin dashboard."""
    if not verify_session(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})


@app.get("/api/admin/stats")
async def get_admin_stats(request: Request, period: str = "24h"):
    """Get playtime statistics for admin dashboard."""
    if not verify_session(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    stats = database.get_stats_by_period(period)
    return JSONResponse(content={"stats": stats, "period": period})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=80, help="Port to run the server on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()
    uvicorn.run("server:app", host="0.0.0.0", port=args.port, reload=args.reload)
