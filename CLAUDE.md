# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Zauberohren is a web application for AI-generated children's stories with text-to-speech capabilities. It's a FastAPI-based service that generates stories using LLMs and converts them to audio using Google Cloud Text-to-Speech.

## Commands

### Development Server
```bash
# Run development server with auto-reload on port 90
python src/server.py --port 90 --reload

# Or using uvicorn directly
uvicorn src.server:app --host 0.0.0.0 --port 90 --reload
```

### Story Generation
```bash
# Batch generate stories for all themes
python src/run.py
```

### Docker Operations
```bash
# Build Docker image
docker build -t zauberohren:latest .

# Run with Docker Compose (production)
docker compose -f vm/docker-compose.yaml up -d
```

### Deployment
```bash
# Deploy to production server (Hetzner)
cd vm && ./deploy.sh
```

## Architecture

### Core Components

**FastAPI Application (`src/server.py`)**
- Main web server with routes for web interface and API endpoints
- Serves static files and Jinja2 templates
- Admin dashboard with basic auth at `/admin`
- Audio streaming with HTTP Range support

**Services Architecture**
- `audio_service.py`: Handles audio file streaming with range requests
- `auth_service.py`: Admin authentication using environment variable PASSWORD
- `db_service.py`: SQLite database for tracking playtime statistics
- `tts.py`: Google Cloud Text-to-Speech integration
- `llm.py`: LLM integration for story generation via LiteLLM
- `generator.py`: Story generation orchestration

**Story Generation Pipeline**
1. LLM generates story text based on theme/parameters
2. Text converted to speech using Google Cloud TTS
3. Audio files stored locally in `data/` directory
4. Database tracks metadata and playback statistics

### Configuration

**Environment Variables** (`.env`)
- `PASSWORD`: Admin panel password
- `LITELLM_MASTER_KEY`: API key for LiteLLM service
- `DOMAIN_WRAPPER`: LiteLLM endpoint URL

**Google Cloud** (`google.json`)
- Service account credentials for Text-to-Speech and Storage APIs
- Project: zalazium-gmbh
- Bucket: gs://zalazium/

### Production Infrastructure

**Docker Compose Stack** (`vm/docker-compose.yaml`)
- Traefik: Reverse proxy with automatic SSL via Let's Encrypt
- Zauberohren: Main application container
- Watchtower: Automatic container updates from Docker Hub

**GitHub Actions** (`.github/workflows/deploy-main.yaml`)
- Builds and pushes Docker image to Docker Hub on main branch push
- Image: plaxtito/zauberohren:latest

## Key Implementation Details

### Audio Streaming
The application implements HTTP Range requests for audio streaming, allowing clients to seek within audio files and resume interrupted downloads.

### Rate Limiting
TTS requests are rate-limited to 90 requests per 60-second window to stay within Google Cloud quotas.

### Database Schema
SQLite database stores:
- Story metadata (theme, title, audio path)
- Playtime tracking with timestamps
- Aggregated statistics for admin dashboard

### Frontend
- Static HTML/CSS/JS in `src/templates/` and `src/static/`
- Progressive Web App with offline support (manifest.json)
- Admin dashboard for viewing playtime statistics