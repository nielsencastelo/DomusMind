
# 🏡 DomusMind 2.0 – Personal AI Assistant for Smart Homes

DomusMind 2.0 represents the evolution from a Streamlit prototype to a production-ready system with a modern web interface, independent agents, and advanced AI capabilities. Your personal Jarvis that sees, hears, learns, remembers, and acts.

> **Full-stack AI home assistant** with vision, voice, language intelligence, and Home Assistant integration.  
> Your house **listens, sees, understands, speaks, searches, remembers — and controls everything through a beautiful web interface.**

---

## ✨ Overview

DomusMind 2.0 is a full-stack AI home assistant system built with:

- 🖥️ **Frontend**: Next.js 15 with shadcn/ui for a modern, responsive web interface
- ⚙️ **Backend**: FastAPI with LangGraph for orchestrating independent AI agents
- 🧠 **AI Capabilities**: 
  - Speech-to-Text with faster-whisper (local, offline)
  - Vision with YOLOv8 + OpenCV and Gemini Vision API (multimodal)
  - LLM reasoning with Google Gemini 2.0 Flash (primary) + Ollama Phi-4/Llama 3.2 (local fallback)
  - Text-to-Speech with Coqui XTTS v2 (Portuguese voice cloning)
  - Web search via DuckDuckGo
- 🗄️ **Data & Memory**:
  - PostgreSQL + pgvector for persistent storage and vector search (RAG)
  - Redis for short-term session context and caching
- 🏠 **Home Assistant Integration**: Full bidirectional control via REST API
- 🐳 **Deployment**: Complete Docker Compose stack for one-command setup

> Your personal AI assistant that sees through cameras, hears through microphones, understands your requests, remembers past conversations, and controls your smart home — all accessible through a beautiful web interface.

## 🧠 Agent Architecture

DomusMind 2.0 uses a sophisticated multi-agent system built with LangGraph, where each agent is an independent node in a conditional graph. The system intelligently routes requests based on detected intent:

```
Intent Classification
          │
          ▼
┌─────────┴─────────┬─────────┬─────────┬─────────┐
▼                   ▼         ▼         ▼         ▼
[Vision]      [Search]    [HA Control]  [Exit]    [General]
   │               │            │           │         │
   ▼               ▼            ▼           ▼         ▼
[Vision Agent] [Search Agent] [HA Agent]  [Exit]  [Memory Agent]
   │               │            │           │         │
   └───────────────┴────────────┴───────────┘         │
                                                     ▼
                                              [LLM Agent] → Generates Response
                                                     │
                                                     ▼
                                               [Speech Agent] (Optional)
```

### Specialized Agents:
- **Vision Agent**: Analyzes camera feeds using YOLOv8 and Gemini Vision for rich scene understanding
- **Search Agent**: Performs web searches via DuckDuckGo and synthesizes results
- **HA Agent**: Controls Home Assistant devices (lights, switches, climate, etc.)
- **Memory Agent**: Manages long-term memory using RAG with pgvector
- **Audio Agent**: Handles speech-to-text with faster-whisper
- **Speech Agent**: Converts text to speech with Coqui XTTS v2
- **LLM Agent**: Generates responses using Google Gemini or local Ollama models
- **Orchestrator**: LangGraph that manages state and routing between agents

### Independent Workers (Celery):
- **Vision Worker**: Continuous camera monitoring for events (person detection, motion)
- **HA Sync Worker**: Keeps device states synchronized with Redis
- **Memory Consolidation Worker**: Hourly consolidation of conversations into long-term memories
- **Indexing Worker**: On-demand document indexing for RAG

---

## 📦 Core Components

DomusMind 2.0 consists of the following key components:

### Backend (FastAPI + LangGraph)
- **API Gateway**: FastAPI server with REST endpoints and WebSocket connections
- **Agent Orchestrator**: LangGraph-based system routing requests to specialized agents
- **Specialized Agents**:
  - Audio Agent: Speech-to-text with faster-whisper
  - Vision Agent: Object detection (YOLOv8) and scene understanding (Gemini Vision)
  - Search Agent: Web search via DuckDuckGo with result synthesis
  - HA Agent: Home Assistant device control and status monitoring
  - Memory Agent: Long-term memory management using RAG with pgvector
  - LLM Agent: Response generation with Gemini/Ollama fallback
  - Speech Agent: Text-to-speech with Coqui XTTS v2
- **Services Layer**: LLM router, RAG pipeline, audio/vision/HA/search services
- **Data Layer**: SQLAlchemy models, pgvector for embeddings, Redis caching
- **Configuration**: System settings stored in database, editable via UI

### Frontend (Next.js 15)
- **Dashboard**: Live status of services, devices, and recent detections
- **Chat Interface**: Conversational UI with streaming responses and voice input
- **Vision Monitor**: Live camera feeds with event timeline and manual analysis
- **Devices Control**: Real-time device status and control by room
- **Memory Browser**: Search and manage consolidated memories and documents
- **Settings Center**: Complete system configuration via web UI (no file editing)

### Infrastructure
- **Containerization**: Docker Compose orchestrating all services
- **Storage**: PostgreSQL (data + pgvector), Redis (caching/sessions)
- **AI Models**: Whisper (STT), YOLOv8 (vision), Gemini/Llama (LLM), XTTS (TTS)
- **External Integrations**: Home Assistant REST API, DuckDuckGo search

---

## 🏠 Home Assistant Integration

DomusMind 2.0 features deep integration with Home Assistant for comprehensive smart home control:

- **Bidirectional Communication**: Read device states and send control commands via Home Assistant REST API
- **Automatic Discovery**: Agents automatically discover and configure available devices from Home Assistant
- **Real-time Synchronization**: Device states are continuously synced to Redis for low-latency access
- **Rich Device Support**: Lights, switches, climate controls, locks, covers, sensors, and more
- **Context Awareness**: Vision and conversation context enhances HA control (e.g., "turn on the light where I'm standing")
- **No Manual Configuration**: Devices are managed entirely through the web interface - no JSON file editing required

The HA Agent enables natural language control like:
- "Turn on the living room lights"
- "Set the bedroom temperature to 22 degrees"
- "Is the front door locked?"
- "Close the garage door"
- "What's the current humidity in the basement?"

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourname/DomusMind.git
cd DomusMind
```

### 2. Environment Setup

Copy the example environment file and fill in your configuration:

```bash
cp .env.example .env
# Edit .env with your settings:
#   - Database passwords
#   - Home Assistant URL and token
#   - LLM API keys (Gemini, OpenAI)
#   - Ollama base URL (if using local models)
#   - Camera IP and credentials
```

### 3. Build and Start Services

```bash
docker compose up -d --build
```

This will start:
- PostgreSQL with pgvector (database)
- Redis (caching and session store)
- Backend API (FastAPI + LangGraph agents)
- Frontend UI (Next.js 15)
- Home Assistant (for device control)
- Nginx (reverse proxy for frontend/backend)
- Celery workers and beat (background agents)

### 4. Access the Application

Once all services are healthy (wait 1-2 minutes for startup):

- **Frontend Interface**: http://localhost
- **API Documentation**: http://localhost:8000/docs
- **Home Assistant**: http://localhost:8123 (if exposed)

### 5. Initial Configuration

1. Open the frontend at http://localhost
2. Go to Settings → General to set your assistant name and wake word
3. Configure LLM providers under Settings → LLM
4. Add your Home Assistant connection under Settings → Home Assistant
5. Configure cameras under Settings → Cameras
6. Define rooms and assign devices under Settings → Rooms

### 6. Using the Assistant

- **Voice Control**: Click the microphone button in the chat interface or use your wake word if configured
- **Text Chat**: Type messages directly in the chat interface
- **Vision**: Ask about what cameras see or visit the Vision page for live feeds
- **Device Control**: Control devices through the chat or Devices page
- **Memory**: Search past conversations and documents in the Memory page

> **Note**: The first startup may take several minutes as Docker images are built and models are downloaded. Subsequent startups will be much faster.

---

## 🎯 Example Commands

DomusMind 2.0 understands natural language and can handle complex requests:

| Example Request                                     | Capability Demonstrated                                     |
|-----------------------------------------------------|-------------------------------------------------------------|
| “What's happening in the living room right now?”    | Vision analysis + real-time camera feed description         |
| “Turn on the lights when I enter the kitchen”       | Future automation (planned)                                 |
| “Search for the best lasagna recipe and summarize it”| Web search + information synthesis                         |
| “What did I tell you about my weekend plans yesterday?”| Long-term memory recall via RAG                           |
| “Set the bedroom temperature to 20 degrees”         | Home Assistant climate control                             |
| “Show me what the front door camera sees”           | Live vision feed request                                    |
| “Remember that my wife's birthday is March 15th”    | Personal information storage for future recall              |
| “What's the difference between LED and OLED TVs?”   | Research assistance with web search                        |
| “Play some jazz music in the den”                   | Media control via Home Assistant (if configured)           |
| “Good night, DomusMind”                             | Triggers bedtime routine (lights off, doors locked, etc.)  |

---

## 📂 Project Structure

```
DomusMind/
├── backend/                          # FastAPI + Agents
│   ├── app/
│   │   ├── main.py                   # Entry point FastAPI
│   │   ├── core/
│   │   │   ├── settings.py           # Config via pydantic-settings
│   │   │   ├── database.py           # SQLAlchemy async + pgvector
│   │   │   └── redis.py              # Cliente Redis
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── router.py         # Agrega todas as rotas
│   │   │   │   ├── chat.py           # WebSocket + REST chat
│   │   │   │   ├── vision.py         # Stream câmera + análise
│   │   │   │   ├── devices.py        # Controle HA
│   │   │   │   ├── memory.py         # Gerenciar memórias/documentos
│   │   │   │   ├── config.py         # Configurações do sistema
│   │   │   │   └── health.py         # Status dos serviços
│   │   ├── agents/                   # Agentes independentes LangGraph
│   │   │   ├── orchestrator.py       # Grafo principal LangGraph
│   │   │   ├── audio_agent.py        # Whisper STT
│   │   │   ├── vision_agent.py       # YOLO + câmera IP + Gemini Vision
│   │   │   ├── search_agent.py       # DuckDuckGo + síntese
│   │   │   ├── ha_agent.py           # Home Assistant ações
│   │   │   ├── memory_agent.py       # RAG + memória de longo prazo
│   │   │   └── llm_agent.py          # Resposta conversacional
│   │   ├── models/
│   │   │   ├── schemas.py            # Pydantic schemas (API)
│   │   │   └── db_models.py          # SQLAlchemy ORM models
│   │   ├── repositories/
│   │   │   ├── conversation_repo.py  # CRUD conversas
│   │   │   ├── memory_repo.py        # CRUD memórias/documentos
│   │   │   ├── config_repo.py        # CRUD configurações (no DB)
│   │   │   └── room_repo.py          # CRUD cômodos
│   │   ├── services/
│   │   │   ├── llm_router.py         # Multi-provedor com fallback
│   │   │   ├── rag_service.py        # Indexação e busca RAG
│   │   │   ├── audio_service.py      # Whisper
│   │   │   ├── speech_service.py     # XTTS
│   │   │   ├── vision_service.py     # YOLO
│   │   │   ├── ha_service.py         # Home Assistant
│   │   │   └── search_service.py     # DuckDuckGo
│   │   └── prompts/
│   │       └── system_prompts.py     # Todos os prompts
│   ├── alembic/                      # Migrations do banco
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                         # Next.js 15
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx            # Layout raiz
│   │   │   ├── page.tsx              # Dashboard principal
│   │   │   ├── chat/page.tsx         # Interface de chat
│   │   │   ├── vision/page.tsx       # Monitor câmeras
│   │   │   ├── devices/page.tsx      # Controle de dispositivos
│   │   │   ├── memory/page.tsx       # Gerenciar memórias e documentos
│   │   │   └── settings/
│   │   │       ├── page.tsx          # Configurações gerais
│   │   │       ├── rooms/page.tsx    # Configurar cômodos
│   │   │       └── llm/page.tsx      # Configurar provedores LLM
│   │   ├── components/
│   │   │   ├── chat/                 # Componentes do chat
│   │   │   ├── vision/               # Feed ao vivo câmera
│   │   │   ├── devices/              # Cards de dispositivos HA
│   │   │   └── ui/                   # shadcn/ui
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts       # Hook para streaming LLM
│   │   │   └── useCamera.ts          # Hook para feed câmera
│   │   ├── lib/
│   │   │   ├── api.ts                # Cliente para FastAPI
│   │   │   └── store.ts              # Zustand state
│   │   └── types/
│   ├── public/
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.yml                # Stack completa
├── .env.example                      # Variáveis documentadas
└── docs/
    ├── ARCHITECTURE.md               # Documentação atual (este projeto)
    └── ROADMAP_REFACTOR.md           # Este documento
```

---

## 🔐 Privacy & Processing

DomusMind 2.0 is designed with privacy as a core principle:

- **Local-First Processing**: Audio transcription, vision analysis, and LLM reasoning can be performed entirely locally using Ollama models
- **Flexible Wake Word**: Customizable wake word detection (formerly "coca/koka") with adjustable sensitivity
- **Selective Cloud Processing**: Only uses cloud APIs (like Gemini) when explicitly configured by the user
- **Data Ownership**: All conversation history, memories, and configurations are stored in your own PostgreSQL database
- **Audit Trails**: Optional logging of all interactions for review and debugging
- **Network Controls**: Ability to disable all external API calls for air-gapped operation

---

## 🧠 Powered By

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - Efficient speech-to-text
- [Ollama](https://ollama.com/) - Local LLM hosting (Phi-4, Llama 3.2)
- [Google Gemini](https://gemini.google.com/) - Primary multimodal LLM
- [YOLOv8](https://github.com/ultralytics/ultralytics) - Object detection
- [Coqui XTTS v2](https://github.com/coqui-ai/TTS) - Voice cloning and TTS
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agent orchestration
- [Next.js 15](https://nextjs.org/) - React frontend framework
- [FastAPI](https://fastapi.tiangolo.com/) - High-performance Python API
- [PostgreSQL + pgvector](https://www.postgresql.org/) - Database with vector search
- [Redis](https://redis.io/) - Caching and session store
- [Docker](https://www.docker.com/) - Containerization
- [Home Assistant](https://www.home-assistant.io/) - Smart home integration

---

## 📘 License

MIT © 2025 – Developed by Nielsen Castelo Damasceno Dantas & contributors
