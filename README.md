# DomusMind

![DomusMind platform overview](docs/assets/domusmind-platform-overview.svg)

DomusMind is a full-stack smart-home AI platform for conversational control, camera intelligence, memory, automation, and multi-provider LLM orchestration. It combines a FastAPI backend, a Next.js operations console, PostgreSQL with pgvector, Redis, Celery workers, Home Assistant, LangGraph agents, IP camera vision, and GPU-aware local inference.

The active application lives in `backend/`, `frontend/`, and `docker-compose.yml`. The old root-level `app/` Streamlit prototype is legacy and is not used by the Docker stack.

## Highlights

- **Agentic assistant** with LangGraph intent routing for general chat, vision, search, device automation, and memory.
- **LLM matrix by agent** for choosing Local/Ollama, Gemini, OpenAI/GPT, or Claude per agent.
- **Laboratory page** for testing each agent independently before using the main chat flow.
- **Hikvision/IP camera setup** with RTSP generation from IP, port, channel, username, and password.
- **Vision pipeline** with Gemini Vision when configured and YOLOv8x/OpenCV fallback.
- **GPU-aware inference** with `TORCH_DEVICE=auto`: CUDA when available, CPU fallback when not.
- **Visible compute badge** in the frontend showing active GPU model or CPU model.
- **Persistent platform configuration** stored in PostgreSQL through `system_config`.
- **RAG foundation** using memories, documents, embeddings, PostgreSQL, and pgvector.
- **Background workers** for Home Assistant sync, camera monitoring, and memory consolidation.

## Runtime Architecture

```mermaid
flowchart LR
  user["Browser"] --> web["Next.js Console<br/>Dashboard, Chat, Vision, Lab, Settings"]
  web --> api["FastAPI Backend<br/>REST + WebSocket + Health"]
  api --> orchestrator["LangGraph Orchestrator"]
  orchestrator --> router["LLM Router<br/>provider per agent"]
  router --> gemini["Gemini"]
  router --> openai["OpenAI / GPT"]
  router --> claude["Claude"]
  router --> ollama["Ollama Local"]
  api --> vision["Vision Service<br/>OpenCV + YOLOv8x + Gemini Vision"]
  vision --> camera["IP Cameras<br/>Hikvision RTSP"]
  api --> ha["Home Assistant"]
  api --> pg[("PostgreSQL + pgvector")]
  api --> redis[("Redis")]
  beat["Celery Beat"] --> worker["Celery Worker"]
  worker --> vision
  worker --> ha
  worker --> pg
  worker --> redis
```

## Agent Flow

```mermaid
flowchart TD
  start["User message"] --> intent["Classify intent"]
  intent --> route{"Intent"}
  route -->|vision| camera["Capture or describe camera context"]
  route -->|search| search["Search and summarize"]
  route -->|lights| ha["Parse room/action and call Home Assistant"]
  route -->|general / exit| memory["Load memory context"]
  camera --> memory
  search --> memory
  ha --> memory
  memory --> answer["Generate response with configured LLM"]
  answer --> persist["Persist in Redis and PostgreSQL"]
  persist --> done["Return to frontend"]
```

## Model Stack

![DomusMind model stack](docs/assets/domusmind-model-stack.svg)

| Area | Default / Supported Models | Notes |
| --- | --- | --- |
| General LLM | `gemini-2.0-flash`, `gpt-4o`, `claude-sonnet-4-6`, `phi4` | Configurable per agent in the LLM settings screen. |
| Local LLM | Ollama `phi4` | Runs through `OLLAMA_BASE_URL`, usually `http://host.docker.internal:11434`. |
| Vision | Gemini Vision + `yolov8x.pt` | Gemini gives rich descriptions; YOLO/OpenCV is the local fallback. |
| Speech-to-text | faster-whisper `medium` | Uses CUDA if available, CPU otherwise. |
| Text-to-speech | Coqui XTTS v2 | Uses `models/Voz_Nielsen.wav` as reference voice when configured. |
| Embeddings | Google `text-embedding-004` or Ollama fallback | Stored/searchable through pgvector. |
| Compute | `TORCH_DEVICE=auto` | Auto-selects CUDA, falls back to CPU safely. |

## Compute: GPU First, CPU Safe

DomusMind is designed to use local acceleration when it exists, without requiring it.

```mermaid
flowchart LR
  start["Model task"] --> check{"TORCH_DEVICE"}
  check -->|auto| cuda{"CUDA available?"}
  check -->|cpu| cpu["Run on CPU"]
  check -->|cuda| gpu["Run on GPU"]
  cuda -->|yes| gpu
  cuda -->|no| cpu
  gpu --> badge["Frontend badge: GPU + device name"]
  cpu --> badge2["Frontend badge: CPU + processor name"]
```

The frontend shows a visible compute badge:

- `GPU: NVIDIA RTX A2000...` when CUDA is available inside the container.
- `CPU: <processor name>` when no GPU is exposed or CUDA is unavailable.

If the GPU is missing, model execution continues normally on CPU.

## Vision And IP Cameras

The Vision page supports Hikvision-style IP cameras. For your current camera:

```text
IP: 192.168.2.218
RTSP port: 554
Primary channel: 101
Substream channel: 102
```

Generated RTSP format:

```text
rtsp://USER:PASSWORD@192.168.2.218:554/Streaming/Channels/101
```

Vision flow:

```mermaid
sequenceDiagram
  participant UI as Vision UI
  participant API as FastAPI
  participant DB as PostgreSQL
  participant CAM as Hikvision Camera
  participant CV as OpenCV / YOLO
  participant G as Gemini Vision

  UI->>API: Save IP camera config
  API->>DB: Store camera source_url
  UI->>API: Test source
  API->>CAM: Open RTSP stream
  CAM-->>API: Frame
  UI->>API: Analyze scene
  API->>DB: Load default camera
  API->>CAM: Capture frame
  alt GEMINI_API_KEY configured
    API->>G: Send image
    G-->>API: Scene description
  else Local fallback
    API->>CV: YOLOv8x detection
    CV-->>API: Object summary
  end
  API-->>UI: Description
```

The backend Docker image downloads `models/yolov8x.pt` during build. The Compose stack also mounts `./backend/models` into `/app/models`, so local model assets remain visible to the containers.

## Repository Layout

```text
DomusMind/
  backend/
    app/
      api/v1/          REST and WebSocket routes
      agents/          LangGraph orchestration
      core/            settings, database, Redis, compute detection
      models/          Pydantic schemas and SQLAlchemy models
      repositories/    database access layer
      services/        LLM, RAG, HA, audio, speech, search, vision
      workers/         Celery tasks
    alembic/           database migrations
    models/            YOLO weights and voice references
    Dockerfile
    requirements.txt

  frontend/
    src/app/           Next.js routes
    src/components/    shared UI shell and controls
    src/hooks/         camera and WebSocket hooks
    src/lib/           API client and Zustand store
    src/types/         shared frontend types
    Dockerfile
    package.json

  docs/
    assets/            documentation images
    ARCHITECTURE.md    architecture notes
    ROADMAP_REFACTOR.md

  docker-compose.yml
  nginx.conf
  .env.example
```

## Requirements

- Docker Desktop or Docker Engine with Docker Compose.
- A valid `.env` file in the project root.
- Optional: NVIDIA GPU support in Docker for CUDA acceleration.
- Optional: Home Assistant URL and long-lived access token.
- Optional: Gemini, OpenAI, Anthropic, or local Ollama configuration.
- Optional: XTTS reference voice file in `backend/models`.

## Quick Start

Create an environment file:

```powershell
Copy-Item .env.example .env
```

Edit `.env`, then start the full stack:

```powershell
docker compose up -d --build
```

Open:

| Service | URL |
| --- | --- |
| Web app through Nginx | `http://localhost` |
| Frontend direct port | `http://localhost:3000` |
| API docs | `http://localhost:8000/docs` |
| Backend health | `http://localhost:8000/api/v1/health` |
| Home Assistant | `http://localhost:8123` |

Follow logs:

```powershell
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f celery_worker
docker compose logs -f celery_beat
```

Stop:

```powershell
docker compose down
```

Remove persistent volumes only when you intentionally want to delete PostgreSQL, Redis, and Home Assistant data:

```powershell
docker compose down -v
```

## Environment Configuration

### Core

```env
ENV=dev
DOMUSMIND_DEBUG=false
```

### Database

```env
DB_PASSWORD=change_me_domusmind
```

Containers build the internal database URL automatically:

```text
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

Create a long-lived token in Home Assistant from your user profile.

### LLM Providers

At least one provider should be usable.

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash

OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o

ANTHROPIC_API_KEY=
CLAUDE_MODEL=claude-sonnet-4-6

LOCAL_MODEL=phi4
OLLAMA_BASE_URL=http://host.docker.internal:11434
LLM_FALLBACK_CHAIN=gemini,local,openai,claude
```

The LLM settings page persists per-agent routing in PostgreSQL under `llm.agents`.

### Camera And Vision

```env
CAMERA_IP=192.168.2.218
CAMERA_USER=admin
CAMERA_PASSWORD=
DEFAULT_CAMERA_SOURCE=0
YOLO_WEIGHTS=models/yolov8x.pt
TORCH_DEVICE=auto
```

Prefer configuring IP cameras in the Vision page. `DEFAULT_CAMERA_SOURCE=0` is only the final fallback for a local device camera.

### Audio And TTS

```env
AUDIO_SAMPLE_RATE=16000
WHISPER_MODEL=medium
WHISPER_COMPUTE_TYPE=float32
TTS_MODEL_NAME=tts_models/multilingual/multi-dataset/xtts_v2
TTS_SPEAKER_WAV=models/Voz_Nielsen.wav
TTS_LANGUAGE=pt
```

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

For remote deployment, set these to the externally reachable backend and WebSocket URLs.

## Web UI Setup

1. Start the stack with `docker compose up -d --build`.
2. Open `http://localhost`.
3. Check the compute badge in the sidebar: GPU or CPU.
4. Go to **Vision** and add the Hikvision camera by IP.
5. Test the camera capture.
6. Go to **Settings -> LLM** and choose the model/provider per agent.
7. Go to **Lab** and validate each agent.
8. Go to **Chat** and use the full assistant flow.

## Main Screens

| Screen | Purpose |
| --- | --- |
| Dashboard | Service health, rooms, devices, cameras, backend status. |
| Chat | WebSocket assistant for automation, vision, search, and memory. |
| Vision | IP camera registration, stream preview, source testing, scene analysis. |
| Lab | Agent laboratory for isolated model/provider validation. |
| Devices | Room devices, light control, Home Assistant cached state. |
| Memory | Memories and document ingestion for RAG. |
| Settings | Generic config, rooms, and LLM matrix. |

## API Reference

Open interactive docs:

```text
http://localhost:8000/docs
```

Important endpoints:

### Health

- `GET /api/v1/health`

### Chat And Agents

- `POST /api/v1/chat`
- `WS /api/v1/chat/ws/{session_id}`
- `POST /api/v1/chat/test-agent`
- `POST /api/v1/chat/transcribe`
- `POST /api/v1/chat/speech`
- `GET /api/v1/chat/history/{session_id}`

### Vision

- `POST /api/v1/vision/describe`
- `POST /api/v1/vision/test-source`
- `GET /api/v1/vision/stream/{room}`
- `GET /api/v1/vision/stream/default`

### Devices And Home Assistant

- `POST /api/v1/devices/light`
- `GET /api/v1/devices/cameras`
- `POST /api/v1/devices/cameras/ip`
- `GET /api/v1/devices/ha/states`
- `GET /api/v1/devices/ha/state/{entity_id}`
- `GET /api/v1/devices/ha/cache`
- `GET /api/v1/devices/ha/cache/{entity_id}`
- `GET /api/v1/devices/rooms`
- `POST /api/v1/devices/rooms`
- `DELETE /api/v1/devices/rooms/{room_id}`
- `POST /api/v1/devices/rooms/{room_id}/devices`
- `POST /api/v1/devices/rooms/{room_id}/cameras`

### Memory And Documents

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

Queues:

```text
default, vision, memory, ha
```

Useful logs:

```powershell
docker compose logs -f celery_worker
docker compose logs -f celery_beat
```

## Database Migrations

The backend runs migrations before starting FastAPI:

```text
alembic upgrade head
```

Manual command:

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

## Development

Backend with only infrastructure:

```powershell
docker compose up -d postgres redis
cd backend
uvicorn app.main:app --reload
```

Frontend only:

```powershell
cd frontend
npm install
npm run dev
```

Full rebuild:

```powershell
docker compose up -d --build
```

Check services:

```powershell
docker compose ps
docker compose logs -f backend
```

## Troubleshooting

### GPU does not appear in the frontend

Check the host first:

```powershell
nvidia-smi
```

Then check the backend health:

```text
http://localhost:8000/api/v1/health
```

If health says CPU, the system still works. To enable GPU inside containers, ensure Docker Desktop has NVIDIA/WSL GPU support enabled and rebuild the stack.

### YOLO weights missing

The backend Dockerfile downloads `models/yolov8x.pt` during build. If you mount `./backend/models`, make sure the file exists locally or rebuild:

```powershell
docker compose build backend celery_worker
```

### Camera stream does not load

Check:

- The camera is reachable from the backend container.
- RTSP port is `554`.
- Hikvision channel is usually `101` for main stream or `102` for substream.
- Username and password are correct.
- The Vision page source test succeeds.

### Home Assistant is degraded

Confirm:

- `HASS_URL` is reachable from the backend container.
- `HASS_TOKEN` is valid.
- Home Assistant is running.

The assistant can still use chat, memory, LLMs, and vision if Home Assistant is degraded.

### LLM responses fail

Check at least one configured provider:

- Gemini needs `GEMINI_API_KEY`.
- OpenAI needs `OPENAI_API_KEY`.
- Claude needs `ANTHROPIC_API_KEY`.
- Ollama needs a reachable `OLLAMA_BASE_URL` and the configured model pulled.

### TTS fails

Check:

- `backend/models/Voz_Nielsen.wav` exists, or update `TTS_SPEAKER_WAV`.
- Server-side audio output may not be available inside Docker depending on the host setup.

## Legacy Streamlit App

The root-level `app/` directory is the old Streamlit prototype. It is not used by the current Docker stack.

Do not start the production system with:

```powershell
streamlit run app/main.py
```

Use:

```powershell
docker compose up -d --build
```

## Known Gaps

- WebSocket output streams the final response word by word after the agent finishes, not true provider token streaming yet.
- Authentication is not implemented yet.
- Advanced Home Assistant domains such as climate, locks, covers, and media players are not fully implemented.
- Robust PDF parsing and chunking are not complete.
- Vision events are not persisted in a dedicated event table yet.
- Automated tests are still missing.

## License

MIT. Developed by Nielsen Castelo Damasceno Dantas and contributors.
