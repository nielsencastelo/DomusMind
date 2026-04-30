# DomusMind 2.0

DomusMind is a full-stack smart-home assistant. The current system is built around a FastAPI backend, a Next.js frontend, PostgreSQL with pgvector, Redis, LangGraph agents, Celery background workers, and Home Assistant integration.

The old root-level `app/` Streamlit prototype is legacy code. The active application is:

- `backend/` for the FastAPI API, agents, services, database models, migrations, and workers.
- `frontend/` for the Next.js web interface.
- `docker-compose.yml` for the complete runtime stack.

## Current Features

- Chat assistant with REST and WebSocket endpoints.
- Intent routing through a LangGraph agent graph.
- LLM fallback chain across Gemini, Ollama, OpenAI, and Claude.
- Home Assistant light/switch control.
- Home Assistant state sync into Redis through Celery.
- Room, device, and camera configuration stored in PostgreSQL.
- Compatibility import/export for the old `rooms.json` shape through `/api/v1/config/rooms`.
- Camera MJPEG streaming through FastAPI.
- Vision analysis with Gemini Vision when configured, with YOLO/OpenCV fallback.
- Short-term chat context in Redis.
- Persistent conversation history in PostgreSQL.
- Basic RAG storage with memories and documents using pgvector.
- Celery workers for HA sync, memory consolidation, and periodic camera monitoring.
- Next.js pages for dashboard, chat, camera monitor, devices, memory, and settings.

## Architecture

```text
Browser
  |
  v
Next.js frontend (:3000)
  |
  v
FastAPI backend (:8000)
  |
  +-- LangGraph orchestrator
  +-- LLM providers: Gemini, Ollama, OpenAI, Claude
  +-- Home Assistant REST API
  +-- OpenCV / YOLO / Gemini Vision
  +-- faster-whisper / XTTS
  |
  +-- PostgreSQL + pgvector
  +-- Redis
  +-- Celery worker + Celery beat

Nginx (:80) proxies the frontend and backend for browser access.
```

## Repository Layout

```text
DomusMind/
  backend/
    app/
      main.py                 FastAPI entrypoint
      api/v1/                 REST and WebSocket routes
      agents/                 LangGraph orchestration
      core/                   settings, database, Redis
      models/                 Pydantic and SQLAlchemy models
      repositories/           database access layer
      services/               LLM, RAG, HA, audio, speech, search, vision
      workers/                Celery tasks
    alembic/                  database migrations
    Dockerfile
    requirements.txt

  frontend/
    src/app/                  Next.js routes
    src/components/           shared UI components
    src/hooks/                camera and WebSocket hooks
    src/lib/                  API client and Zustand store
    src/types/                shared frontend types
    Dockerfile
    package.json

  docker-compose.yml          full stack
  nginx.conf                  reverse proxy
  .env.example                environment template
  docs/                       roadmap and architecture notes
  app/                        legacy Streamlit prototype, not used by Docker stack
```

## Requirements

- Docker Desktop or Docker Engine with Docker Compose.
- A valid `.env` file in the project root.
- Optional: Home Assistant URL and long-lived access token.
- Optional: Gemini, OpenAI, Anthropic, or local Ollama configuration.
- Optional: YOLO weights and XTTS reference voice files in `backend/models`.

## Quick Start

From the repository root:

```powershell
Copy-Item .env.example .env
```

Edit `.env`, then start the stack:

```powershell
docker compose up -d --build
```

Open:

- Web app: `http://localhost`
- Frontend direct port: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- Home Assistant: `http://localhost:8123`

Check logs:

```powershell
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f celery_worker
docker compose logs -f celery_beat
```

Stop the stack:

```powershell
docker compose down
```

Stop and remove persistent volumes:

```powershell
docker compose down -v
```

Use `down -v` only when you intentionally want to delete PostgreSQL, Redis, and Home Assistant persisted data.

## Environment Configuration

Create `.env` from `.env.example`.

### Core

```env
ENV=dev
DOMUSMIND_DEBUG=false
```

### Database

```env
DB_PASSWORD=change_me_domusmind
```

`docker-compose.yml` builds `DATABASE_URL` automatically for containers:

```env
postgresql+asyncpg://domusmind:<DB_PASSWORD>@postgres:5432/domusmind
```

### Redis

```env
REDIS_PASSWORD=change_me_redis
REDIS_SESSION_TTL=3600
```

### Home Assistant

```env
HASS_URL=http://192.168.2.x:8123
HASS_TOKEN=your_long_lived_access_token
```

Create a Home Assistant long-lived access token from your Home Assistant user profile and paste it into `HASS_TOKEN`.

### LLM Providers

At least one provider should be usable.

Gemini:

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
```

Ollama:

```env
LOCAL_MODEL=phi4
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

OpenAI:

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o
```

Claude:

```env
ANTHROPIC_API_KEY=
CLAUDE_MODEL=claude-sonnet-4-6
```

Fallback order:

```env
LLM_FALLBACK_CHAIN=gemini,local,openai,claude
```

### Camera

```env
CAMERA_IP=192.168.2.218
CAMERA_USER=admin
CAMERA_PASSWORD=
DEFAULT_CAMERA_SOURCE=0
YOLO_WEIGHTS=models/yolov8x.pt
```

`DEFAULT_CAMERA_SOURCE=0` uses a local camera device. For an IP camera, configure the camera URL in the web UI under Settings -> Rooms, or import it through the JSON editor.

### Audio and TTS

```env
AUDIO_SAMPLE_RATE=16000
WHISPER_MODEL=medium
WHISPER_COMPUTE_TYPE=float32
TTS_MODEL_NAME=tts_models/multilingual/multi-dataset/xtts_v2
TTS_SPEAKER_WAV=models/Voz_Nielsen.wav
TTS_LANGUAGE=pt
```

The Docker Compose file mounts `./backend/models` into `/app/models`. Put YOLO weights and the XTTS reference voice file there if you use these features.

### Embeddings

```env
EMBEDDING_PROVIDER=google
EMBEDDING_DIM=768
```

`google` uses Gemini embeddings when `GEMINI_API_KEY` is available. The backend falls back to Ollama embeddings where possible.

### Frontend

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

These values are used by the browser. If you deploy remotely, set them to the externally reachable backend and WebSocket URLs.

## First-Time Setup In The Web UI

1. Start the stack with `docker compose up -d --build`.
2. Open `http://localhost`.
3. Go to `Settings`.
4. Open `Rooms`.
5. Add rooms manually, or use the JSON editor to import the old `rooms.json` shape.
6. Go to `Devices` and test light control.
7. Go to `Vision` and test the default camera or a room camera.
8. Go to `Chat` and send a command.

## Room Configuration

Rooms, devices, and cameras are stored in PostgreSQL. The UI still supports a compatibility JSON format similar to the old `rooms.json` file.

Example:

```json
{
  "sala": {
    "friendly_name": "Living Room",
    "light_entity_id": "light.sala_principal",
    "light_domain": "light",
    "camera_source": "rtsp://user:password@192.168.2.218:554/stream"
  },
  "quarto": {
    "friendly_name": "Bedroom",
    "light_entity_id": "switch.quarto_luz",
    "light_domain": "switch",
    "camera_source": "0"
  }
}
```

Import/export endpoints:

- `GET /api/v1/config/rooms`
- `POST /api/v1/config/rooms`

Native room/device endpoints:

- `GET /api/v1/devices/rooms`
- `POST /api/v1/devices/rooms`
- `DELETE /api/v1/devices/rooms/{room_id}`
- `POST /api/v1/devices/rooms/{room_id}/devices`
- `POST /api/v1/devices/rooms/{room_id}/cameras`

## Using The Application

### Dashboard

The dashboard shows service health, room count, device count, camera count, and status messages for backend dependencies.

### Chat

The chat page sends messages over WebSocket:

- Text commands are processed by the LangGraph orchestrator.
- The response includes the detected intent and provider used.
- The `Speak response` button sends the latest assistant response to the backend TTS endpoint.
- Conversation turns are stored in Redis for short-term context and PostgreSQL for history.

Example messages:

```text
Turn on the living room light.
What is happening on the camera?
Search the web for Home Assistant best practices.
Remember that the office light is connected to switch.office_light.
```

### Vision

The vision page supports:

- MJPEG stream preview from `/api/v1/vision/stream/{room}`.
- Scene analysis through `/api/v1/vision/describe`.
- Manual room override for quick testing.

Gemini Vision is used when `GEMINI_API_KEY` is configured. Otherwise the service falls back to YOLO/OpenCV.

### Devices

The devices page supports:

- Listing configured rooms and devices.
- Light on/off controls.
- Manual light test by room name.
- Cached Home Assistant state display from Redis when the HA sync worker has data.

### Memory

The memory page supports:

- Listing stored memories.
- Adding text documents for indexing.
- Document storage in PostgreSQL with embeddings when an embedding provider is available.

### Settings

Settings includes:

- Generic key/value configuration in PostgreSQL.
- LLM preference settings.
- Room and device configuration.
- JSON import/export for room compatibility.

## API Reference

Open the generated API docs at:

```text
http://localhost:8000/docs
```

Important endpoints:

### Health

- `GET /api/v1/health`

### Chat

- `POST /api/v1/chat`
- `WS /api/v1/chat/ws/{session_id}`
- `POST /api/v1/chat/transcribe`
- `POST /api/v1/chat/speech`
- `GET /api/v1/chat/history/{session_id}`

### Vision

- `POST /api/v1/vision/describe`
- `GET /api/v1/vision/stream/{room}`
- `GET /api/v1/vision/stream/default`

### Devices and Home Assistant

- `POST /api/v1/devices/light`
- `GET /api/v1/devices/ha/states`
- `GET /api/v1/devices/ha/state/{entity_id}`
- `GET /api/v1/devices/ha/cache`
- `GET /api/v1/devices/ha/cache/{entity_id}`
- `GET /api/v1/devices/rooms`
- `POST /api/v1/devices/rooms`

### Memory and Documents

- `GET /api/v1/memory/memories`
- `DELETE /api/v1/memory/memories/{memory_id}`
- `POST /api/v1/memory/search`
- `GET /api/v1/memory/documents`
- `POST /api/v1/memory/documents`
- `POST /api/v1/memory/documents/upload`

### Configuration

- `GET /api/v1/config`
- `GET /api/v1/config/{key}`
- `PUT /api/v1/config/{key}`
- `DELETE /api/v1/config/{key}`
- `GET /api/v1/config/rooms`
- `POST /api/v1/config/rooms`

## Background Workers

The Compose stack starts:

- `celery_worker`
- `celery_beat`

Scheduled jobs:

- Home Assistant state sync every 30 seconds.
- Memory consolidation every hour.
- Default camera monitoring every 10 seconds.

Worker queues:

```text
default, vision, memory, ha
```

Useful logs:

```powershell
docker compose logs -f celery_worker
docker compose logs -f celery_beat
```

## Database Migrations

The backend container runs migrations automatically before starting FastAPI:

```text
alembic upgrade head
```

Manual migration command:

```powershell
docker compose run --rm backend alembic upgrade head
```

The initial migration creates:

- `rooms`
- `devices`
- `cameras`
- `conversations`
- `memories`
- `documents`
- `system_config`
- pgvector indexes

## Development Notes

### Backend only

If you want to run only infrastructure and then start the backend manually:

```powershell
docker compose up -d postgres redis
cd backend
uvicorn app.main:app --reload
```

You need Python dependencies installed locally for this mode.

### Frontend only

```powershell
cd frontend
npm install
npm run dev
```

The frontend expects `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` to point to a running backend.

### Full stack rebuild

```powershell
docker compose up -d --build
```

### Check service status

```powershell
docker compose ps
docker compose logs -f backend
```

## Legacy Streamlit App

The root-level `app/` directory is the old Streamlit prototype. It is not used by the current Docker stack.

Do not start the production system with:

```powershell
streamlit run app/main.py
```

Use this instead:

```powershell
docker compose up -d --build
```

The old Streamlit app called legacy endpoints such as `/api/v1/speech` and `/api/v1/devices/vision`. The current backend uses `/api/v1/chat/speech` and `/api/v1/vision/describe`.

## Troubleshooting

### Backend cannot connect to PostgreSQL

Check:

```powershell
docker compose ps
docker compose logs -f postgres
docker compose logs -f backend
```

Make sure `DB_PASSWORD` in `.env` is set before the first database volume is created. If you change it after the volume exists, PostgreSQL may still use the old password.

### Redis authentication fails

Check `REDIS_PASSWORD` and restart Redis:

```powershell
docker compose logs -f redis
```

If this is a local development environment and you can lose Redis data:

```powershell
docker compose down -v
docker compose up -d --build
```

### Home Assistant is degraded

Confirm:

- `HASS_URL` is reachable from the backend container.
- `HASS_TOKEN` is a valid long-lived access token.
- Home Assistant is running.

You can still use chat, memory, and vision features if HA is degraded.

### Camera stream does not load

Check:

- The room has a camera URL configured.
- The backend container can reach the camera network address.
- `DEFAULT_CAMERA_SOURCE` is valid.
- YOLO weights exist at `backend/models/yolov8x.pt` if Gemini Vision is not configured.

### LLM responses fail

Check at least one provider in `LLM_FALLBACK_CHAIN` is configured:

- Gemini needs `GEMINI_API_KEY`.
- OpenAI needs `OPENAI_API_KEY`.
- Claude needs `ANTHROPIC_API_KEY`.
- Ollama needs a reachable `OLLAMA_BASE_URL` and the configured local model pulled.

### TTS fails

Check:

- `backend/models/Voz_Nielsen.wav` exists, or update `TTS_SPEAKER_WAV`.
- The backend container has access to audio output if you expect server-side playback.

## Current Gaps

These are known implementation gaps in the current codebase:

- WebSocket output currently streams the final response word by word after the agent finishes, not true provider token streaming.
- Authentication is not implemented yet.
- Advanced Home Assistant domains such as climate, locks, covers, and media players are not fully implemented.
- Document upload supports text extraction for text-like files; robust PDF parsing and chunking are not yet implemented.
- Vision events are not persisted in a dedicated event table yet.
- The frontend uses custom UI components, not shadcn/ui installation.
- Automated tests are still missing.

## License

MIT. Developed by Nielsen Castelo Damasceno Dantas and contributors.
