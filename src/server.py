from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from config import STATIC_DIR, TEMPLATES_DIR, DATA_DIR
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pathlib import Path
import argparse
import uvicorn
import json
import random

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=80, help="Port to run the server on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()
    uvicorn.run("server:app", host="0.0.0.0", port=args.port, reload=args.reload)
