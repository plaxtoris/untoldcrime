# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**untoldcrime** is a web application that generates and serves AI-generated German true crime audio stories. The application uses:
- Google Cloud TTS (Chirp3-HD) for speech synthesis
- Google Imagen for cover image generation
- LLM API (via LiteLLM proxy) for story generation
- FastAPI web server with admin dashboard and analytics

## Development Commands

### Running the Server

```bash
# Development mode with auto-reload
python3 src/server.py --reload --port 8000

# Production mode (requires admin credentials in .env)
uvicorn src.server:app --host 0.0.0.0 --port 80

# Docker mode (production)
docker build -t untoldcrime .
docker run -p 80:80 untoldcrime
```

### Story Generation

```bash
# Generate batch of stories (runs run.py with predefined settings)
python3 src/run.py

# Generate single story programmatically
python3 -c "from generator import generate_complete_story; generate_complete_story()"
```

### Data Management

```bash
# Count total playtime of stories
python3 -c "from run import count_stories; count_stories()"

# Clean invalid stories (wrong duration or missing covers)
python3 -c "from run import clean_invalid_stories; clean_invalid_stories()"
```

## Architecture

### Story Generation Pipeline

The complete story generation flow (`generator.py`):
1. **Text Generation** (`llm.py`): Calls LiteLLM proxy to generate structured JSON with `story`, `title`, and `summary` fields using prompt from `prompts.py`
2. **Cover Generation** (`cover.py`): Uses Google Imagen API to create cover image from story summary
3. **Audio Synthesis** (`tts.py`): Uses Google Cloud TTS Long Audio Synthesis API with rate limiting and retry logic
4. **Storage**: Saves to `data/{random_id}/` with `story.json`, `cover.png`, and `story.mp3`

### Web Server Architecture

`server.py` is the main FastAPI application with three route groups:

1. **Public Routes**: Index page, about, impressum (German legal requirement)
2. **API Routes**:
   - `/api/stories` - List all stories
   - `/api/story/random` - Get random story
   - `/api/image/{story_id}/cover` - Optimized cover images (uses `image_optimizer.py` for caching)
   - `/api/playtime` - Track listening analytics
3. **Admin Routes**: Session-based authentication (`_admin_sessions` dict), dashboard with analytics

### Configuration

`config.py` centralizes all configuration:
- Environment variables: `LITELLM_MASTER_KEY`, `DOMAIN_WRAPPER`, `USER`, `PASSWORD`
- Google Cloud: Project, location, bucket, credentials path
- TTS: Voice settings, rate limits (90 requests/60s), retry logic
- Story validation: Duration limits (10-45 minutes)

### Key Technical Details

**TTS Rate Limiting**: `tts.py` implements a sliding window rate limiter (`RateLimiter` class) to prevent quota exhaustion. It tracks request timestamps and automatically waits when limit is reached.

**Database**: SQLite database (`database.py`) tracks playtime analytics with timezone-aware timestamps (Europe/Berlin). Stats aggregated by period: 24h (hourly), 7d (daily), 30d (daily), alltime (monthly).

**Image Optimization**: `image_optimizer.py` creates cached, resized versions of cover images to reduce bandwidth. Cache directory structure: `data/{story_id}/cache/{format}/{width}_{quality}.{ext}`

**Parallel Generation**: `run.py` uses `ProcessPoolExecutor` for batch story generation with progress tracking via `tqdm`.

## Environment Variables

Required in `.env`:
- `LITELLM_MASTER_KEY` - API key for LLM proxy
- `DOMAIN_WRAPPER` - LiteLLM proxy domain (default: localhost:8080)
- `USER` - Admin username (default: admin)
- `PASSWORD` - Admin password (default: admin)

Google Cloud authentication via `google.json` service account file in project root.

## Story Content Guidelines

Stories target German-speaking female audience (25-45) with focus on psychological depth, character identification, and preventive insights. See `prompts.py` for detailed prompt structure emphasizing emotional narrative over graphic violence.
