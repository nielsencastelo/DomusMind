# DomusMind — Arquitetura Atual

> Documentação técnica do estado atual do projeto.  
> Versão: 1.x | Data: Abril 2026

---

## Visão Geral

**DomusMind** é um assistente doméstico inteligente, local-first, que combina:

- Reconhecimento de voz em tempo real (Whisper)
- Visão computacional para detecção de objetos (YOLOv8)
- Raciocínio via LLM local ou em nuvem (Ollama, OpenAI, Gemini, Claude)
- Voz sintetizada com clonagem de voz (XTTS v2)
- Controle de dispositivos via Home Assistant
- Busca na web via DuckDuckGo
- Interface web via Streamlit
- API REST via FastAPI

A palavra de ativação é **"Coca"** (variações: koka, coka, kouka).

---

## Stack Tecnológica

| Camada | Tecnologia |
|--------|-----------|
| Interface Web | Streamlit |
| API | FastAPI + Uvicorn |
| LLM Local | Ollama (Phi-4 padrão) |
| LLM Nuvem | OpenAI / Google Gemini / Anthropic Claude |
| LLM Abstração | LangChain (langchain-core, langchain-ollama, etc.) |
| Voz → Texto | faster-whisper (OpenAI Whisper otimizado) |
| Texto → Voz | Coqui TTS (XTTS v2, clonagem de voz) |
| Visão | YOLOv8 (Ultralytics) + OpenCV |
| Busca | DuckDuckGo Search API |
| Automação Residencial | Home Assistant (REST API) |
| Configuração | python-dotenv + Pydantic |
| Persistência | PostgreSQL + pgvector |

---

## Estrutura de Diretórios

```
DomusMind/
├── app/
│   ├── main.py                   # Entry point da UI Streamlit
│   ├── adapters/
│   │   ├── camera_adapter.py     # Wrapper OpenCV para câmeras
│   │   └── home_assistant_client.py  # Integração REST com Home Assistant
│   ├── api/
│   │   ├── app.py                # Fábrica da aplicação FastAPI
│   │   └── routes/
│   │       ├── chat.py           # POST /chat, /chat/speech, /chat/transcribe
│   │       ├── config.py         # system_config no PostgreSQL
│   │       ├── devices.py        # POST /devices/light, /devices/vision
│   │       └── health.py         # GET /health
│   ├── configs/
│   │   └── database.py            # Engine PostgreSQL async
│   ├── core/
│   │   └── settings.py           # Variáveis de ambiente via Pydantic
│   ├── ha/
│   │   └── docker-compose.yml    # Home Assistant em Docker
│   ├── models/
│   │   └── schemas.py            # Modelos Pydantic (request/response)
│   ├── prompts/
│   │   └── system_prompts.py     # System prompts por intenção
│   ├── repositories/
│   │   └── room_repo.py          # Cômodos, dispositivos e câmeras no PostgreSQL
│   └── services/
│       ├── orchestrator.py       # Orquestrador principal de requisições
│       ├── router_llm.py         # Roteador multi-provedor LLM com fallback
│       ├── intent_service.py     # Classificação de intenção via LLM
│       ├── audio_service.py      # Captura e transcrição de áudio
│       ├── speech_service.py     # Síntese de voz (TTS)
│       ├── vision_service.py     # Detecção de objetos com YOLO
│       ├── search_service.py     # Busca web com DuckDuckGo
│       ├── light_service.py      # Parsing e execução de comandos de luz
│       └── response_service.py   # Geração de resposta conversacional
├── notebooks/                    # Experimentos Jupyter por funcionalidade
│   ├── Audio.ipynb
│   ├── Whisper.ipynb
│   ├── TTS.ipynb, LLM_TTS.ipynb
│   ├── Yolo.ipynb
│   ├── Device.ipynb
│   └── Internet.ipynb
├── requirements.txt
├── README.md
└── .env                          # Variáveis de ambiente (não versionado)
```

---

## Fluxo de Dados Principal

```
Usuário fala
    │
    ▼
[AudioService] ── sounddevice captura mic
    │              faster-whisper transcreve
    │              detecção de silêncio automática
    ▼
[IntentService] ── LLM local classifica intenção
    │              visao | pesquisa | luz | sair | outro
    │
    ├─── "visao" ──► [VisionService] ── YOLOv8 em frames da câmera
    │                                   retorna objetos detectados
    │
    ├─── "pesquisa" ─► [SearchService] ── DuckDuckGo API
    │                                     retorna resultados formatados
    │
    ├─── "luz" ──► [LightService] ── LLM extrai JSON {room, action}
    │                                HomeAssistantClient executa
    │
    └─── "outro" ──► [ResponseService] ── contexto diretamente ao LLM
    │
    ▼
[ResponseService] ── monta mensagens (histórico + system prompt + input)
    │                ProviderRouter seleciona provedor LLM
    │                fallback automático: local → openai → gemini → claude
    ▼
[SpeechService] ── Coqui XTTS v2 sintetiza voz clonada
    │               sounddevice reproduz áudio
    ▼
Usuário ouve resposta
```

---

## Serviços

### DomusOrchestrator
Roteador central de requisições. Recebe mensagem + histórico, classifica intenção e coordena os serviços especializados.

**Intenções suportadas:**

| Intenção | Trigger | Ação |
|----------|---------|------|
| `visao` | "o que tem na câmera", "me mostra" | Captura frames + YOLO |
| `pesquisa` | "pesquisa", "busca na internet" | DuckDuckGo |
| `luz` | "liga/desliga a luz", "acende" | HA REST API |
| `sair` | "encerra", "finalizar" | Encerra sessão |
| `outro` | qualquer outro | LLM conversacional |

---

### ProviderRouter
Roteador multi-provedor LLM com fallback automático.

```
LLM_FALLBACK_CHAIN = "local,openai,gemini,claude"
```

- `local` → Ollama (offline, phi4 por padrão)
- `openai` → OpenAI API
- `gemini` → Google Generative AI
- `claude` → Anthropic Claude

Se um provedor falhar, o próximo da cadeia é tentado automaticamente.

---

### AudioService
- Captura áudio com `sounddevice` em chunks de 0.2s
- Detecção de silêncio por RMS (threshold: 0.005)
- Máximo de 30s por captura
- Transcrição com `faster-whisper` (modelo configurável: tiny/base/medium/large)
- Preferência CUDA se disponível, fallback para CPU

---

### SpeechService
- Motor: Coqui TTS (XTTS v2)
- Clonagem de voz usando arquivo WAV de referência (`models/Voz_Nielsen.wav`)
- Língua padrão: `pt` (Português)
- Reprodução imediata via `sounddevice`

---

### VisionService
- Modelo: YOLOv8x (configurável via `YOLO_WEIGHTS`)
- Captura 10 frames com intervalo de 0.2s
- Agrega detecções entre frames
- Threshold de confiança: 0.6
- Suporta câmeras locais (índice inteiro) e câmeras de rede (RTSP URL)

---

### HomeAssistantClient
- Autenticação via Bearer Token (`TOKEN` no .env)
- Suporta domínios `light` e `switch`
- Método `toggle_light(entity_id, action, domain)` → `(bool, str)`
- Método `ping()` para verificação de conectividade

---

## API REST

Base URL: `http://localhost:8000/api/v1`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/chat` | Processa mensagem de texto do usuário |
| `POST` | `/chat/speech` | Converte texto em fala (TTS) |
| `POST` | `/chat/transcribe` | Captura microfone e transcreve |
| `GET` | `/devices/rooms` | Lista cômodos, dispositivos e câmeras do PostgreSQL |
| `POST` | `/devices/rooms` | Cria/atualiza cômodo, dispositivos e câmeras no PostgreSQL |
| `POST` | `/devices/light` | Liga/desliga luz em cômodo |
| `POST` | `/devices/vision` | Captura câmera e descreve cena |
| `GET` | `/health` | Status do sistema e conectividade HA |

---

## Interface Web (Streamlit)

Acessível em `http://localhost:8501` com 4 abas:

| Aba | Função |
|-----|--------|
| **Assistente** | Chat por texto, botão de fala, histórico de conversa |
| **Configuração** | Formulários gravando em PostgreSQL |
| **Dispositivos** | Teste manual de luzes e câmeras |
| **Saúde** | Status dos serviços e conectividade HA |

---

## Configuração de Cômodos

Cômodos, dispositivos e câmeras são persistidos nas tabelas PostgreSQL `rooms`,
`devices` e `cameras`. A interface de Ajustes grava diretamente no banco, sem
editor de arquivo JSON.

---

## Variáveis de Ambiente (`.env`)

```env
# LLM
LOCAL_MODEL=phi4
OPENAI_MODEL=gpt-4o
GEMINI_MODEL=gemini-2.0-flash
CLAUDE_MODEL=claude-sonnet-4-6
LLM_FALLBACK_CHAIN=local,openai,gemini,claude

# Home Assistant
HASS_URL=http://localhost:8123
TOKEN=seu_token_ha

# Câmera
DEFAULT_CAMERA_SOURCE=0
YOLO_WEIGHTS=models/yolov8x.pt

# Áudio
AUDIO_SAMPLE_RATE=16000
WHISPER_MODEL=medium
WHISPER_COMPUTE_TYPE=float32

# TTS
TTS_MODEL_NAME=tts_models/multilingual/multi-dataset/xtts_v2
TTS_SPEAKER_WAV=models/Voz_Nielsen.wav
TTS_LANGUAGE=pt
```

---

## Home Assistant (Docker)

```yaml
# app/ha/docker-compose.yml
services:
  homeassistant:
    image: homeassistant/home-assistant:stable
    network_mode: host
    privileged: true
    volumes:
      - ./config:/config
    environment:
      - TZ=America/Sao_Paulo
```

---

## Limitações da Arquitetura Atual

| Item | Limitação |
|------|-----------|
| Persistência | PostgreSQL obrigatório para rooms, câmeras, memória e configurações |
| Memória | Histórico de conversa apenas na sessão ativa (em memória) |
| Agentes | Executam de forma sequencial no mesmo processo |
| Frontend | Streamlit: limitado para UX rica e mobile |
| Escalabilidade | Tudo roda em um único processo Python |
| Câmera IP | Sem suporte a autenticação HTTP em câmeras de rede |
| RAG | Nenhuma base de conhecimento persistente |
| Multi-usuário | Nenhum suporte a múltiplos usuários simultâneos |

---

## Notebooks de Experimentação

| Notebook | Conteúdo |
|----------|---------|
| `Audio.ipynb` | Captura e processamento de áudio |
| `Whisper.ipynb` | Testes do modelo Whisper |
| `TTS.ipynb`, `LLM_TTS.ipynb` | Síntese de voz |
| `Yolo.ipynb` | Detecção de objetos |
| `Device.ipynb` | Controle de dispositivos HA |
| `Internet.ipynb` | Busca e resumo web |
| `LLM.ipynb` | Testes de LLM |
| `fala.ipynb` | Pipeline completo de fala |
