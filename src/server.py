"""FastAPI web server for the True Crime story application."""

from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from config import (
    STATIC_DIR,
    TEMPLATES_DIR,
    DATA_DIR,
    ADMIN_USER,
    ADMIN_PASSWORD,
    SESSION_DURATION_HOURS
)
from utils import load_json
import database
import image_optimizer
import argparse
import uvicorn
import random
import secrets
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="untoldcrime", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Admin session management
_admin_sessions: dict[str, datetime] = {}


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize application on startup."""
    try:
        database.init_database()
        logger.info("✓ Database initialized")
        logger.info("✓ Server ready")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


def _create_session() -> str:
    """Create a new admin session.

    Returns:
        Session token
    """
    token = secrets.token_urlsafe(32)
    _admin_sessions[token] = datetime.now() + timedelta(hours=SESSION_DURATION_HOURS)
    return token


def _verify_session(request: Request) -> bool:
    """Verify if request has valid admin session.

    Args:
        request: FastAPI request object

    Returns:
        True if session is valid
    """
    token = request.cookies.get("admin_session")
    if not token or token not in _admin_sessions:
        return False

    if _admin_sessions[token] < datetime.now():
        del _admin_sessions[token]
        return False

    return True


def _get_all_stories() -> list[dict[str, str]]:
    """Retrieve all available stories with metadata.

    Returns:
        List of story dictionaries
    """
    stories = []
    data_path = Path(DATA_DIR)

    if not data_path.exists():
        logger.warning(f"Data directory does not exist: {data_path}")
        return stories

    for story_dir in data_path.iterdir():
        if not story_dir.is_dir():
            continue

        story_json = story_dir / "story.json"
        story_mp3 = story_dir / "story.mp3"
        cover_png = story_dir / "cover.png"

        # Check if all required files exist
        if not (story_json.exists() and story_mp3.exists() and cover_png.exists()):
            logger.debug(f"Skipping incomplete story: {story_dir.name}")
            continue

        # Load metadata
        metadata = load_json(story_json)
        if not metadata:
            logger.warning(f"Failed to load metadata for: {story_dir.name}")
            continue

        stories.append({
            "id": story_dir.name,
            "title": metadata.get("title", "Unbekannt"),
            "summary": metadata.get("summary", ""),
            "audio_url": f"/data/{story_dir.name}/story.mp3",
            "cover_url": f"/data/{story_dir.name}/cover.png"
        })

    return stories


# ===== PUBLIC ROUTES =====


@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    """Serve the main application page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/impressum", response_class=HTMLResponse)
async def impressum_page(request: Request):
    """Serve the impressum (legal notice) page."""
    return templates.TemplateResponse("impressum.html", {"request": request})


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """Serve the about page."""
    return templates.TemplateResponse("about.html", {"request": request})


# ===== API ROUTES =====


@app.get("/api/stories")
async def api_get_stories():
    """Get all available stories.

    Returns:
        JSON response with list of stories
    """
    stories = _get_all_stories()
    return JSONResponse(content={"stories": stories})


@app.get("/api/story/random")
async def api_get_random_story():
    """Get a random story.

    Returns:
        JSON response with random story or error
    """
    stories = _get_all_stories()
    if stories:
        return JSONResponse(content=random.choice(stories))
    return JSONResponse(content={"error": "No stories available"}, status_code=404)


@app.get("/api/image/{story_id}/cover")
async def api_get_optimized_cover(
    story_id: str,
    width: int = Query(default=800, ge=100, le=2048, description="Target width in pixels"),
    quality: int = Query(default=85, ge=1, le=100, description="Image quality (1-100)"),
    format: str = Query(default="webp", regex="^(webp|jpeg|png)$", description="Output format")
):
    """Get optimized cover image for a story.

    Args:
        story_id: Story identifier
        width: Target width in pixels (100-2048)
        quality: Image quality 1-100
        format: Output format (webp, jpeg, png)

    Returns:
        Optimized image file or 404 error
    """
    try:
        # Find original cover
        original_path = Path(DATA_DIR) / story_id / "cover.png"

        if not original_path.exists():
            return JSONResponse(
                content={"error": "Cover image not found"},
                status_code=404
            )

        # Get or create optimized version
        format_upper = format.upper()
        optimized_path = image_optimizer.get_optimized_image(
            original_path=original_path,
            width=width,
            quality=quality,
            format=format_upper
        )

        # Determine media type
        media_types = {
            "WEBP": "image/webp",
            "JPEG": "image/jpeg",
            "PNG": "image/png"
        }
        media_type = media_types.get(format_upper, "image/png")

        return FileResponse(
            path=optimized_path,
            media_type=media_type,
            headers={
                "Cache-Control": "public, max-age=31536000",  # 1 year
                "Vary": "Accept"
            }
        )

    except Exception as e:
        logger.error(f"Error serving optimized image: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


@app.post("/api/playtime")
async def api_track_playtime(request: Request):
    """Track playtime for analytics.

    Args:
        request: Request containing story_id and play_duration

    Returns:
        JSON response with success status
    """
    try:
        data = await request.json()
        story_id = data.get("story_id")
        play_duration = data.get("play_duration", 0)

        if not story_id:
            return JSONResponse(
                content={"error": "story_id required"},
                status_code=400
            )

        success = database.track_playtime(story_id, play_duration)

        if success:
            return JSONResponse(content={"success": True})

        return JSONResponse(
            content={"error": "Failed to track playtime"},
            status_code=500
        )

    except Exception as e:
        logger.error(f"Error tracking playtime: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ===== ADMIN ROUTES =====


@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Serve admin login page or redirect if already logged in."""
    if _verify_session(request):
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse("admin_login.html", {"request": request})


@app.post("/admin/login")
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Handle admin login.

    Args:
        request: FastAPI request
        username: Admin username
        password: Admin password

    Returns:
        Redirect to dashboard or login page with error
    """
    if username == ADMIN_USER and password == ADMIN_PASSWORD:
        token = _create_session()
        response = RedirectResponse(url="/admin", status_code=302)
        response.set_cookie(
            key="admin_session",
            value=token,
            httponly=True,
            max_age=SESSION_DURATION_HOURS * 3600
        )
        logger.info(f"Admin login successful: {username}")
        return response

    logger.warning(f"Failed login attempt: {username}")
    return templates.TemplateResponse(
        "admin_login.html",
        {"request": request, "error": "Ungültige Anmeldedaten"}
    )


@app.get("/admin/logout")
async def admin_logout(request: Request):
    """Handle admin logout.

    Args:
        request: FastAPI request

    Returns:
        Redirect to login page
    """
    token = request.cookies.get("admin_session")
    if token and token in _admin_sessions:
        del _admin_sessions[token]
        logger.info("Admin logged out")

    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_session")
    return response


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Serve admin dashboard or redirect to login."""
    if not _verify_session(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})


@app.get("/api/admin/stats")
async def api_admin_stats(request: Request, period: str = "24h"):
    """Get playtime statistics for admin dashboard.

    Args:
        request: FastAPI request
        period: Time period for stats (24h, 7d, 30d, alltime)

    Returns:
        JSON response with statistics
    """
    if not _verify_session(request):
        return JSONResponse(
            content={"error": "Unauthorized"},
            status_code=401
        )

    stats = database.get_stats_by_period(period)
    return JSONResponse(content={"stats": stats, "period": period})


# ===== MAIN =====


def main() -> None:
    """Run the web server."""
    parser = argparse.ArgumentParser(description="untoldcrime web server")
    parser.add_argument(
        "--port",
        type=int,
        default=80,
        help="Port to run the server on"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    args = parser.parse_args()

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
