from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from config import STATIC_DIR, TEMPLATES_DIR, DATA_DIR
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import argparse
import uvicorn

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    """Serve the main application page."""
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=80, help="Port to run the server on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()
    uvicorn.run("server:app", host="0.0.0.0", port=args.port, reload=args.reload)
