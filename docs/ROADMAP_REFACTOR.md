# DomusMind 2.0 — Plano de Refatoração e Evolução

> Plano técnico para evoluir o DomusMind de protótipo Streamlit para um sistema  
> de produção com backend FastAPI, frontend Next.js, múltiplos agentes independentes,  
> visão computacional avançada, memória persistente, RAG e integração completa com HA.

---

## Visão Estratégica

O objetivo é transformar o DomusMind em um **Jarvis pessoal**: um sistema que vê, ouve, aprende, se lembra e age — com uma interface web moderna, configurável diretamente pelo navegador, sem necessidade de editar arquivos manualmente.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DomusMind 2.0                                │
│                                                                       │
│  ┌──────────────┐    ┌──────────────────────────────────────────┐   │
│  │  Next.js UI  │◄──►│             FastAPI Gateway               │   │
│  │  (browser)   │    │         (WebSocket + REST)               │   │
│  └──────────────┘    └──────────┬───────────────────────────────┘   │
│                                  │                                    │
│          ┌───────────────────────┼──────────────────────┐           │
│          │                       │                       │           │
│   ┌──────▼──────┐  ┌─────────────▼──────┐  ┌───────────▼────────┐  │
│   │ Agent: Audio│  │  Agent: Orchestrate │  │  Agent: Vision     │  │
│   │  (Whisper)  │  │   (LangGraph)       │  │  (YOLO + IP Cam)   │  │
│   └─────────────┘  └────────────────────┘  └────────────────────┘  │
│                                                                       │
│   ┌─────────────┐  ┌─────────────────────┐  ┌────────────────────┐  │
│   │ Agent: HA   │  │   Agent: Memory/RAG  │  │  Agent: Search     │  │
│   │ (HA REST)   │  │   (pgvector + RAG)  │  │  (DuckDuckGo)      │  │
│   └─────────────┘  └─────────────────────┘  └────────────────────┘  │
│                                                                       │
│   ┌──────────────────┐   ┌──────────────┐   ┌────────────────────┐  │
│   │  PostgreSQL       │   │    Redis     │   │  IP Camera         │  │
│   │  (dados + pgvect) │   │  (ctx curto) │   │  192.168.2.218     │  │
│   └──────────────────┘   └──────────────┘   └────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Stack Proposta

### Backend
| Componente | Tecnologia | Justificativa |
|-----------|-----------|--------------|
| Framework API | **FastAPI** | Async nativo, WebSocket, OpenAPI automático |
| Agentes | **LangGraph** | Grafo de agentes com estado, fluxo condicional |
| LLM primário online | **Google Gemini 2.0 Flash** | Custo-benefício, multimodal, visão nativa |
| LLM local | **Ollama** (Phi-4 / Llama 3.2) | Privacidade, offline |
| Abstração LLM | **LangChain + LangGraph** | Multi-provedor, ferramentas, memória |
| Banco de dados | **PostgreSQL** + **pgvector** | Relacional + busca vetorial num só lugar |
| Cache / memória curta | **Redis** | Contexto de sessão, rate-limiting |
| RAG | **LlamaIndex** ou **LangChain RAG** | Indexação e busca semântica |
| Embeddings | **Google text-embedding-004** ou **nomic-embed-text** (local) | Gerar vetores para RAG |
| Speech-to-Text | **faster-whisper** | Rápido, local, offline |
| Text-to-Speech | **Coqui XTTS v2** | Clonagem de voz em Português |
| Visão | **YOLOv8 + OpenCV** | Detecção de objetos em tempo real |
| Visão Multimodal | **Gemini Vision API** | Descrever cenas via LLM multimodal |
| Tarefas Assíncronas | **Celery + Redis** | Agentes independentes em background |
| Servidor | **Uvicorn** | ASGI, suporte WebSocket |

### Frontend
| Componente | Tecnologia | Justificativa |
|-----------|-----------|--------------|
| Framework | **Next.js 15** (App Router) | SSR, React 19, performance |
| UI Components | **shadcn/ui** + **Tailwind CSS** | Design moderno, acessível |
| Estado global | **Zustand** | Simples, sem boilerplate |
| Dados em tempo real | **WebSocket** nativo | Streaming de respostas do LLM |
| Formulários | **react-hook-form** + **zod** | Validação type-safe |
| Visualização câmera | **HTML5 Video** + MJPEG stream | Preview ao vivo da câmera IP |
| Autenticação | **NextAuth.js** | Login local ou OAuth |

### Infraestrutura
| Componente | Tecnologia |
|-----------|-----------|
| Containerização | **Docker Compose** |
| HA | Home Assistant (container oficial) |
| Banco | PostgreSQL 16 |
| Cache | Redis 7 |
| Proxy | Nginx (para frontend + backend) |

---

## Estrutura de Pastas Proposta

```
DomusMind/
├── backend/                          # FastAPI + Agentes
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

## Banco de Dados PostgreSQL

Substituir o `rooms.json` e memória volátil por tabelas persistentes.

### Schema Principal

```sql
-- Cômodos e dispositivos
CREATE TABLE rooms (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) UNIQUE NOT NULL,
    friendly_name VARCHAR(200),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE devices (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id         UUID REFERENCES rooms(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    entity_id       VARCHAR(200) NOT NULL,  -- HA entity
    domain          VARCHAR(50) NOT NULL,    -- light, switch, climate
    device_type     VARCHAR(50) NOT NULL,    -- light, camera, sensor
    config          JSONB,                   -- configurações extras
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Câmeras
CREATE TABLE cameras (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id     UUID REFERENCES rooms(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    source_url  VARCHAR(500) NOT NULL,  -- RTSP, HTTP, índice local
    username    VARCHAR(100),
    password    VARCHAR(200),           -- criptografado
    is_default  BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Histórico de conversas (memória de longo prazo)
CREATE TABLE conversations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  VARCHAR(100) NOT NULL,
    role        VARCHAR(20) NOT NULL,   -- user | assistant
    content     TEXT NOT NULL,
    intent      VARCHAR(50),
    provider    VARCHAR(50),
    metadata    JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Memórias semânticas (RAG)
CREATE TABLE memories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       VARCHAR(500),
    content     TEXT NOT NULL,
    source      VARCHAR(200),           -- conversation, document, manual
    embedding   VECTOR(768),            -- pgvector
    metadata    JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON memories USING ivfflat (embedding vector_cosine_ops);

-- Documentos indexados para RAG
CREATE TABLE documents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename    VARCHAR(500) NOT NULL,
    content     TEXT NOT NULL,
    embedding   VECTOR(768),
    metadata    JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);

-- Configurações do sistema (chave-valor)
CREATE TABLE system_config (
    key         VARCHAR(200) PRIMARY KEY,
    value       JSONB NOT NULL,
    description TEXT,
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Redis — Memória de Curto Prazo

Redis é usado para contexto de sessão e cache de alta velocidade.

```
redis:session:{session_id}     → últimas N mensagens da conversa ativa (TTL: 1h)
redis:intent_cache:{hash}      → cache de classificação de intenção (TTL: 5min)
redis:vision_cache:{frame_hash} → cache do resultado YOLO (TTL: 30s)
redis:ha_state:{entity_id}     → estado atual dos dispositivos HA (TTL: 10s)
redis:rate:{user_id}           → rate limit por usuário
```

**Fluxo de memória:**

```
Usuário faz pergunta
       │
       ▼
[Redis] ── busca contexto curto (últimas 10 msgs desta sessão)
       │
       ▼
[PostgreSQL] ── busca memórias relevantes via pgvector (RAG)
       │
       ▼
[LangGraph] ── monta contexto completo: curto + longo prazo + documentos
       │
       ▼
[LLM] ── gera resposta com contexto rico
       │
       ▼
[Redis] ── salva nova mensagem na sessão ativa
[PostgreSQL] ── persiste conversa + gera embedding para memória
```

---

## Arquitetura de Agentes com LangGraph

Cada agente é um **nó independente** no grafo LangGraph. O estado flui entre nós de forma condicional.

```python
# Estrutura do grafo de agentes

Estado = {
    "session_id": str,
    "user_input": str,
    "audio_transcription": str | None,
    "intent": str,                    # visao | pesquisa | luz | sair | outro
    "vision_context": str | None,     # resultado YOLO/Gemini Vision
    "search_results": str | None,     # resultados DuckDuckGo
    "ha_result": str | None,          # resultado da ação HA
    "memory_context": str | None,     # memórias relevantes do RAG
    "short_term_context": list,       # histórico Redis
    "final_response": str | None,
    "provider_used": str,
    "error": str | None
}

Grafo:
  ENTRADA
     │
     ▼
 [intent_node]  ──── classifica intenção
     │
     ├── "visao" ──────► [vision_node] ──► [memory_node] ──► [llm_node]
     │
     ├── "pesquisa" ───► [search_node] ──► [memory_node] ──► [llm_node]
     │
     ├── "luz" ────────► [ha_node] ──────► [memory_node] ──► [llm_node]
     │
     ├── "sair" ───────► [exit_node]
     │
     └── "outro" ──────► [memory_node] ──────────────────► [llm_node]
                                                                │
                                                                ▼
                                                          [speech_node]
                                                                │
                                                                ▼
                                                            SAÍDA
```

### Agentes Independentes (Celery Workers)

Além do grafo principal, alguns agentes rodam como **workers Celery independentes**:

| Worker | Tarefa | Frequência |
|--------|--------|-----------|
| `vision_worker` | Monitora câmera IP continuamente, alerta sobre eventos | Contínuo |
| `ha_sync_worker` | Sincroniza estado dos dispositivos HA com Redis | A cada 30s |
| `memory_consolidation_worker` | Consolida conversas em memórias de longo prazo | A cada hora |
| `indexing_worker` | Indexa novos documentos adicionados | On-demand |

---

## Visão Computacional — Integração com Câmera IP

A câmera IP em `192.168.2.218` (RTSP/HTTP) será integrada de duas formas:

### 1. Stream ao vivo no Frontend (MJPEG)
```
Frontend Next.js
    │
    ├── <img src="http://backend/api/v1/vision/stream/{room}">
    │         │
    │         ▼
    │   FastAPI endpoint que faz proxy do stream RTSP
    │   (OpenCV → MJPEG → HTTP multipart)
    └── Preview ao vivo na interface web
```

### 2. Análise sob demanda + monitoramento contínuo

**Modo 1 — YOLO local:**
```python
# vision_agent.py
async def analyze_frame(room: str) -> str:
    cap = cv2.VideoCapture(f"rtsp://user:pass@192.168.2.218:554/stream")
    frames = [cap.read() for _ in range(10)]
    detections = yolo_model(frames, conf=0.6)
    return format_detections(detections)
```

**Modo 2 — Gemini Vision (multimodal):**
```python
# vision_agent.py — usando Gemini para descrição rica
async def describe_scene_with_llm(frame: np.ndarray) -> str:
    image_b64 = frame_to_base64(frame)
    response = gemini_client.generate_content([
        "Descreva detalhadamente o que você vê nesta imagem da câmera de segurança.",
        {"mime_type": "image/jpeg", "data": image_b64}
    ])
    return response.text
```

**Modo 3 — Monitoramento autônomo (Celery worker):**
```python
# vision_worker.py — agente independente
@celery.task
def monitor_camera_continuous(room: str):
    """Monitora câmera e notifica via WebSocket sobre eventos."""
    while True:
        frame = capture_frame(room)
        detections = yolo_model(frame)
        if has_person(detections):
            notify_frontend(f"Pessoa detectada em {room}")
            save_event_to_db(room, detections, frame)
        time.sleep(5)  # checa a cada 5 segundos
```

### Configuração da câmera no sistema
A câmera será configurada diretamente na interface web, sem editar arquivos:
```
Settings → Cômodos → Sala → Câmera:
  URL: rtsp://admin:globalsys123@192.168.2.218:554/stream
  ou: http://192.168.2.218/video
  Tipo: IP Camera (RTSP)
  Nome: Câmera Sala Principal
```

---

## RAG — Base de Conhecimento

O DomusMind terá memória semântica de longo prazo usando RAG (Retrieval-Augmented Generation).

### Fontes de conhecimento indexadas:
1. **Histórico de conversas** — cada conversa é embeddada e indexada
2. **Documentos manuais** — PDFs, TXTs adicionados pelo usuário via interface
3. **Logs de eventos** — detecções da câmera, ações HA, alertas
4. **Manuais de dispositivos** — documentação dos dispositivos HA
5. **Anotações do usuário** — "lembre-se que minha reunião é às 10h nas sextas"

### Pipeline RAG:
```
Usuário: "Como eu ligo o ar da sala mesmo?"
    │
    ▼
[EmbeddingService] ── gera embedding da pergunta
    │
    ▼
[pgvector] ── busca k=5 chunks mais similares nas tabelas memories + documents
    │
    ▼
[Context Builder] ── monta:
    Sistema: "Você é o DomusMind..."
    Memórias relevantes: [chunks similares]
    Histórico recente: [Redis session]
    Pergunta: "Como eu ligo o ar da sala?"
    │
    ▼
[Gemini/LLM] ── gera resposta contextualizada
```

### Consolidação automática de memória:
```python
# memory_consolidation_worker.py (Celery, roda a cada hora)
async def consolidate_memories():
    recent_conversations = get_conversations_last_hour()
    for convo in recent_conversations:
        summary = llm.summarize(convo)  # Gemini resume a conversa
        embedding = embed(summary)
        save_memory(content=summary, embedding=embedding, source="conversation")
```

---

## Interface Web Next.js — Páginas

### Dashboard (`/`)
- Status ao vivo dos serviços (backend, HA, câmeras)
- Cards com dispositivos HA e estados atuais
- Últimas detecções da câmera
- Atalhos rápidos: ligar/desligar luz por cômodo

### Chat (`/chat`)
- Interface de chat estilo ChatGPT
- Suporte a texto e voz (Web Speech API ou botão de gravar)
- Streaming de respostas via WebSocket
- Indicador de intenção detectada e provedor LLM usado
- Visualização do contexto de memória utilizado

### Monitor de Câmeras (`/vision`)
- Grid com feeds ao vivo de todas as câmeras configuradas
- Painel de últimas detecções e alertas
- Botão para análise manual da cena atual
- Timeline de eventos detectados

### Dispositivos (`/devices`)
- Lista de todos os dispositivos HA por cômodo
- Toggle rápido para luzes
- Estado em tempo real (sincronizado via WebSocket com HA)

### Memória (`/memory`)
- Visualizar memórias armazenadas (conversas consolidadas)
- Adicionar documentos para indexação (drag & drop PDF/TXT)
- Pesquisar na base de conhecimento
- Gerenciar/deletar memórias

### Configurações (`/settings`)
- **Geral**: nome do assistente, palavra de ativação, idioma
- **LLM**: selecionar provedores, inserir chaves de API, testar
- **Câmeras**: adicionar/editar câmeras IP, testar conexão
- **Cômodos**: criar/editar cômodos e associar dispositivos HA
- **Home Assistant**: URL do HA, token, sincronizar entidades
- **Áudio**: selecionar dispositivo de entrada/saída, testar voz

---

## Docker Compose — Stack Completa

O objetivo é que o usuário rode **um único comando** para ter tudo funcionando:

```bash
docker compose up -d
```

```yaml
# docker-compose.yml (raiz do projeto)
version: "3.9"

services:

  # ─── Banco de dados ──────────────────────────────────────
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: domusmind
      POSTGRES_USER: domusmind
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "domusmind"]
      interval: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  # ─── Backend ─────────────────────────────────────────────
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://domusmind:${DB_PASSWORD}@postgres:5432/domusmind
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      HASS_URL: ${HASS_URL}
      HASS_TOKEN: ${HASS_TOKEN}
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-http://host.docker.internal:11434}
    volumes:
      - ./backend/models:/app/models  # pesos YOLO, voz clonada
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # ─── Celery Workers (agentes independentes) ─────────────
  celery_worker:
    build: ./backend
    command: celery -A app.celery worker --loglevel=info -Q default,vision,memory
    environment:
      DATABASE_URL: postgresql+asyncpg://domusmind:${DB_PASSWORD}@postgres:5432/domusmind
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - postgres
      - redis
      - backend
    restart: unless-stopped

  celery_beat:
    build: ./backend
    command: celery -A app.celery beat --loglevel=info
    depends_on:
      - redis
    restart: unless-stopped

  # ─── Frontend ────────────────────────────────────────────
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NEXT_PUBLIC_WS_URL: ws://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped

  # ─── Home Assistant ──────────────────────────────────────
  homeassistant:
    image: homeassistant/home-assistant:stable
    network_mode: host
    privileged: true
    volumes:
      - ha_config:/config
    environment:
      - TZ=America/Sao_Paulo
    restart: unless-stopped

  # ─── Nginx (proxy reverso) ───────────────────────────────
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  ha_config:
```

### Variáveis necessárias (`.env`)
```env
# Obrigatórias
DB_PASSWORD=senha_forte_aqui
REDIS_PASSWORD=senha_redis_aqui
HASS_URL=http://192.168.2.x:8123
HASS_TOKEN=token_do_ha

# LLM (pelo menos uma)
GEMINI_API_KEY=AIza...
OPENAI_API_KEY=sk-...         # opcional

# Ollama (se usar local)
OLLAMA_BASE_URL=http://host.docker.internal:11434

# Câmera IP
CAMERA_IP=192.168.2.218
CAMERA_USER=admin
CAMERA_PASSWORD=globalsys123
```

---

## Roteiro de Implementação (Fases)

### Fase 1 — Fundação (2–3 semanas)
- [ ] Criar estrutura `backend/` e `frontend/`
- [ ] Configurar PostgreSQL com pgvector + Alembic migrations
- [ ] Migrar `rooms.json` para banco de dados (tabelas rooms, devices, cameras)
- [ ] Configurar Redis como session store
- [ ] Criar `docker-compose.yml` base funcional
- [ ] Setup Next.js 15 com shadcn/ui e Tailwind

### Fase 2 — Agentes LangGraph (2–3 semanas)
- [ ] Implementar grafo LangGraph com todos os nós
- [ ] Migrar todos os services para agentes no grafo
- [ ] Adicionar WebSocket para streaming de respostas
- [ ] Integrar Gemini como LLM primário
- [ ] Implementar fallback chain atualizado

### Fase 3 — Câmera IP + Visão (1–2 semanas)
- [ ] Integrar câmera IP via RTSP (192.168.2.218)
- [ ] Proxy MJPEG no FastAPI para o frontend
- [ ] Implementar Gemini Vision para descrição de cenas
- [ ] Celery worker para monitoramento contínuo da câmera
- [ ] Page `/vision` no Next.js com feed ao vivo

### Fase 4 — Memória e RAG (2 semanas)
- [ ] Implementar sistema de embeddings (Google text-embedding-004)
- [ ] Pipeline RAG com pgvector
- [ ] Consolidação automática de conversas (Celery beat)
- [ ] Indexação de documentos via upload
- [ ] Page `/memory` na interface web

### Fase 5 — Frontend Completo (2–3 semanas)
- [ ] Dashboard com status ao vivo
- [ ] Chat com streaming e histórico
- [ ] Página de configurações completa (sem editar arquivos)
- [ ] Gerenciamento de dispositivos HA
- [ ] Monitor de câmeras

### Fase 6 — Polimento e Produção (1–2 semanas)
- [ ] Nginx como proxy reverso
- [ ] Autenticação (NextAuth)
- [ ] Documentação atualizada
- [ ] Testes de integração
- [ ] Guia de setup em 5 minutos

---

## Comparativo: Atual vs. Proposto

| Aspecto | Atual | Proposto |
|---------|-------|----------|
| Frontend | Streamlit | Next.js 15 + shadcn/ui |
| API | FastAPI (parcial) | FastAPI completo + WebSocket |
| Agentes | Sequential, single process | LangGraph + Celery workers |
| LLM | Multi-provedor com fallback | Gemini primário + fallback local |
| Persistência | JSON em arquivo | PostgreSQL |
| Memória | Sessão em memória RAM | Redis (curto) + pgvector (longo) |
| RAG | Sem RAG | LlamaIndex + pgvector |
| Câmera | RTSP básico | RTSP + MJPEG stream + Gemini Vision |
| Visão | YOLO apenas | YOLO + Gemini Vision (multimodal) |
| HA | REST básico | REST + sync contínuo (Celery) |
| Configuração | Editar arquivos | Interface web completa |
| Deploy | Manual | Docker Compose (1 comando) |
| Multi-usuário | Não | Sim (com autenticação) |

---

## Inovações Destacadas

### Memória contextual em duas camadas
- **Redis** (curto prazo): contexto da conversa atual, estado dos dispositivos
- **pgvector** (longo prazo): memórias consolidadas, base de conhecimento RAG

### Agente de visão autônomo
O `vision_worker` roda independentemente, monitora a câmera e notifica sobre eventos (pessoa detectada, movimento, etc.) sem o usuário precisar perguntar.

### Gemini como "olhos" do sistema
Ao usar o Gemini Vision API, o assistente consegue descrever cenas de câmera de forma muito mais rica do que apenas detectar objetos com YOLO — entendendo contexto, emoções, atividades.

### Configuração 100% via interface web
Tudo que hoje exige editar `.env` ou `rooms.json` será configurável na página `/settings` do Next.js, tornando o sistema acessível para usuários não-técnicos.

### RAG com memória de conversas
O sistema aprende com o tempo. Toda conversa é consolidada automaticamente em memórias semânticas, permitindo que o assistente se lembre de preferências, rotinas e informações mencionadas semanas atrás.
