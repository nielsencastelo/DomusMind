# Plano de Ação — Visão, Câmeras e Infraestrutura

**Status:** Planejado · **Criado em:** 2026-04-30  
**Escopo:** Backend + Frontend · Sem alteração de banco de dados estrutural (somente remoção de dependências obsoletas)

---

## Contexto e Estado Atual

| Componente | Estado Atual | Problema |
|---|---|---|
| Modelo de visão | Fixo em `.env` (`GEMINI_API_KEY`, `YOLO_WEIGHTS`) | Não configurável pelo frontend |
| Câmeras | 1 câmera IP global + índice local `0` no `.env` | Não suporta múltiplas câmeras nomeadas |
| Teste de câmera | `/api/v1/vision/test-source` testa apenas conectividade | Não retorna metadados (resolução, latência) |
| Detecção local | Tenta `/dev/video0` fixo | Não escaneia dispositivos automaticamente |
| AI agent + câmera | Usa a câmera padrão do cômodo | Agente não busca câmera por nome diretamente |
| Banco de dados | PostgreSQL (`postgresql+asyncpg://`) | Referências a SQLite em `requirements.txt` e possivelmente em alembic |

---

## Tarefa 1 — Seleção do modelo de visão pelo frontend

**Objetivo:** O operador escolhe YOLO ou Gemini, e configura a API key do Gemini, tudo pela UI sem tocar no `.env`.

### 1.1 Backend — novo grupo de config na tabela `config`

A tabela `config` já existe (chave/valor genérico). Não é necessária migração de schema.

Chaves a serem gerenciadas:

| Chave | Tipo | Descrição |
|---|---|---|
| `vision.provider` | `string` | `"yolo"` ou `"gemini"` |
| `vision.gemini_api_key` | `string` | API key do Gemini Vision (salva encriptada ou como texto simples) |
| `vision.yolo_weights` | `string` | Caminho do arquivo `.pt` dentro do container |
| `vision.yolo_confidence` | `float` | Limiar de confiança do YOLO (padrão `0.6`) |
| `vision.yolo_frames` | `int` | Frames analisados por chamada (padrão `10`) |

**Mudanças em `app/services/vision_service.py`:**
- `VisionService.__init__()` passa a ler `vision.provider` e `vision.gemini_api_key` do banco via `ConfigRepository`, não de `settings`
- `describe()` decide YOLO vs Gemini com base na config do banco
- Fallback: se config não existir, usa `settings.gemini_api_key` e `settings.yolo_weights` como default (compatibilidade)

**Mudanças em `app/api/v1/vision.py`:**
- Endpoint `GET /api/v1/vision/config` — retorna provider atual e se Gemini key está configurada (sem expor a key)
- Endpoint `POST /api/v1/vision/config` — salva provider, key, e parâmetros YOLO

**Mudanças em `app/workers/vision_worker.py`:**
- Worker `monitor_default_camera` passa a consultar a config do banco para escolher o provider

### 1.2 Frontend — nova seção em Configurações > Visão

**Novo arquivo:** `frontend/src/app/settings/vision/page.tsx`

Interface:
```
┌─ Modelo de Visão ─────────────────────────────────────────────┐
│  ○ YOLO (local, offline)         ● Gemini Vision (cloud)      │
│                                                                │
│  [Gemini API Key]  ●●●●●●●●●●●●●●●●●●●  [Testar]  [Salvar]   │
│                                                                │
│  Confiança YOLO:  [====●=====] 60%                            │
│  Frames por análise: [10]                                      │
└───────────────────────────────────────────────────────────────┘
```

- O campo de API key usa `type="password"` e exibe apenas `••••••` se já salvo
- Botão "Testar" faz um `POST /api/v1/vision/describe` e exibe a resposta
- Só exibe campos YOLO se provider = YOLO selecionado

---

## Tarefa 2 — Múltiplas câmeras com nome, teste e detecção local

### 2.1 Modelo de câmera — extensão do schema existente

O model `Camera` (tabela `cameras`) já tem `name`, `source_url`, `username`, `password`, `room_id`, `is_default`.

**Adicionar via migração Alembic:**

| Campo | Tipo | Descrição |
|---|---|---|
| `camera_type` | `enum` | `ip` / `local` / `rtsp` / `usb` |
| `channel` | `int` | Canal Hikvision (padrão `101`) |
| `is_local` | `bool` | Câmera detectada automaticamente na máquina |
| `device_path` | `str` | Ex: `/dev/video0`, preenchido na detecção automática |
| `last_seen_at` | `datetime` | Último frame capturado com sucesso |
| `resolution` | `str` | Ex: `1280x720`, preenchido no teste |

### 2.2 Backend — detecção automática de câmeras locais

**Novo endpoint:** `GET /api/v1/vision/local-cameras`

Lógica:
```python
import cv2

def scan_local_cameras(max_index: int = 5) -> list[dict]:
    found = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            found.append({
                "index": i,
                "device_path": f"/dev/video{i}",
                "resolution": f"{int(w)}x{int(h)}",
                "source_url": str(i),
            })
            cap.release()
    return found
```

- Roda sob timeout de 5s para não bloquear no container sem câmera
- Retorna lista vazia se não houver dispositivos (container Docker sem device mapping)
- O frontend exibe um botão "Escanear câmeras locais" que chama este endpoint

**Novo endpoint:** `POST /api/v1/vision/test-camera`

Corpo:
```json
{
  "source_url": "rtsp://...",
  "username": "admin",
  "password": "••••"
}
```

Resposta enriquecida (sem LLM — apenas OpenCV):
```json
{
  "ok": true,
  "message": "Câmera respondeu com sucesso",
  "latency_ms": 342,
  "resolution": "1920x1080",
  "fps": 25.0,
  "snapshot_base64": "data:image/jpeg;base64,..."
}
```

- `snapshot_base64`: frame JPEG codificado em base64 para exibir preview imediato no frontend
- Sem chamada a YOLO, Gemini ou qualquer LLM
- Timeout de 8s para evitar travar o request

### 2.3 Câmeras nomeadas para o agente de IA

**Mudanças em `app/repositories/room_repo.py`:**
- Novo método `get_camera_by_name(name: str) -> Camera | None`
- Busca case-insensitive no campo `name` da tabela `cameras`

**Mudanças em `app/services/vision_service.py`:**
- `describe(camera_name: str | None)` — aceita nome da câmera em vez de source_url diretamente
- Se `camera_name` for passado, resolve o `source_url` pelo banco
- O agente pode chamar: `"descreva a câmera Garagem"` e o sistema faz `get_camera_by_name("Garagem")`

**Mudanças no agente `visao` (`app/agents/`):**
- O agente extrai o nome da câmera da mensagem do usuário
- Exemplo de fluxo:
  - Usuário: _"O que está acontecendo na câmera da sala?"_
  - Agente extrai: `camera_name = "sala"`
  - Chama `VisionService().describe(camera_name="sala")`
  - Sistema busca câmera com `name ILIKE '%sala%'` no banco

### 2.4 Frontend — página de câmeras refatorada

**Arquivo:** `frontend/src/app/vision/page.tsx`

Nova estrutura da página:

```
┌─ Câmeras Locais Detectadas ──────────────────────────────────┐
│  [Escanear agora]                                             │
│  ○ /dev/video0  —  1280x720  [Adicionar como câmera]         │
└───────────────────────────────────────────────────────────────┘

┌─ Adicionar câmera IP ────────────────────────────────────────┐
│  Nome: [Garagem          ]   Tipo: [IP Hikvision ▼]          │
│  IP:   [192.168.1.100    ]   Porta: [554]  Canal: [101]      │
│  Usuário: [admin]  Senha: [••••••••]                          │
│                [Testar conexão]  [Adicionar]                  │
└───────────────────────────────────────────────────────────────┘

┌─ Câmeras cadastradas ─────────────────────────────────────────┐
│  [Sala]  ● online   1920×1080  [Preview] [Remover]            │
│  [Garagem]  ● online  1280×720  [Preview] [Remover]           │
│  [Quintal]  ✕ offline           [Preview] [Remover]           │
└───────────────────────────────────────────────────────────────┘
```

- **Preview** abre modal com MJPEG stream ao vivo (`/api/v1/vision/stream/{camera_id}`)
- **Testar conexão** chama o novo `POST /api/v1/vision/test-camera` e exibe snapshot + latência
- Câmeras locais detectadas aparecem separadas das IP
- Status online/offline é calculado pelo `last_seen_at` (verde se < 60s)

---

## Tarefa 3 — Remover SQLite da infraestrutura

### 3.1 O que remover

| Arquivo | O que fazer |
|---|---|
| `backend/requirements.txt` | Remover `aiosqlite` se presente |
| `backend/app/core/settings.py` | Remover fallback `sqlite:///` da `database_url` default (já é PostgreSQL) |
| `backend/alembic/env.py` | Verificar se há lógica condicional para SQLite e remover |
| `.env.example` (se existir) | Garantir que `DATABASE_URL` só documenta PostgreSQL |

### 3.2 O que garantir

- O padrão de `database_url` em `settings.py` deve ser apenas `postgresql+asyncpg://...`
- Nenhum teste ou script usa SQLite como banco de dados
- A documentação de setup não menciona SQLite

---

## Sequência de Implementação Recomendada

```
Fase 1 — Backend base (sem frontend)
  1.1  Migração Alembic para campos novos em Camera
  1.2  Endpoints de config de visão (GET/POST /vision/config)
  1.3  VisionService lê provider do banco
  1.4  Endpoint de detecção local (/vision/local-cameras)
  1.5  Endpoint de teste enriquecido (/vision/test-camera com snapshot)
  1.6  Método get_camera_by_name no repositório
  1.7  Agente de visão aceita nome de câmera
  1.8  Limpeza SQLite

Fase 2 — Frontend
  2.1  Página Settings > Visão (seleção YOLO/Gemini + key)
  2.2  Página Visão refatorada (scanner local + multi-câmera)
  2.3  Modal de preview com MJPEG ao vivo
  2.4  Integrar status de câmeras no dashboard
```

---

## Dependências e Riscos

| Risco | Mitigação |
|---|---|
| Container Docker sem acesso a `/dev/video*` | Endpoint retorna lista vazia com mensagem explicativa; não é erro |
| API key Gemini salva no banco sem criptografia | Anotar como TODO para versão futura usar Vault ou variável de ambiente criptografada |
| MJPEG stream bloqueia worker assíncrono | Mover `mjpeg_frames` para thread pool com `run_in_threadpool` (já é gerador síncrono) |
| Agente extrai nome de câmera errado | Busca fuzzy / ILIKE — retorna a câmera mais próxima; se nenhuma, usa câmera padrão |
| Câmera sem `last_seen_at` aparece como offline | Considerar `last_seen_at = None` como "nunca testada" (badge cinza, não vermelho) |
