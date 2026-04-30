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

## Tarefa 4 — Home Assistant não sobe (diagnóstico e fix)

### 4.1 Diagnóstico — duas causas raiz

**Causa A: `network_mode: host` não funciona no Docker Desktop (Windows)**

O `docker-compose.yml` atual configura o HA assim:

```yaml
homeassistant:
  image: homeassistant/home-assistant:stable
  network_mode: host   # ← problema
  privileged: true
  volumes:
    - ha_config:/config
```

No Linux nativo, `network_mode: host` faz o container compartilhar exatamente a rede do host — funciona perfeitamente para o HA descobrir dispositivos na LAN (mDNS, Zeroconf, etc.).

No **Docker Desktop para Windows**, o comportamento é diferente:
- Os containers rodam dentro de uma VM Linux (HyperV/WSL2)
- `network_mode: host` conecta o container à rede dessa VM, **não à rede do Windows**
- A porta 8123 fica na VM, e o Docker Desktop pode ou não fazer o forward até o Windows host
- Em versões antigas do Docker Desktop, `host` networking simplesmente não funciona e o container falha ao tentar fazer bind
- Mesmo quando funciona parcialmente, o HA não enxerga os dispositivos da LAN Windows (a descoberta de integrations fica comprometida)

**Causa B: `HASS_URL` padrão aponta para o próprio container, não para o HA**

Em `docker-compose.yml`:
```yaml
HASS_URL: ${HASS_URL:-http://localhost:8123}
```

`localhost` dentro de um container Docker = o próprio container. O backend e os workers tentam chamar `http://localhost:8123` e chegam em si mesmos, não no HA. Com `network_mode: host` no HA, não há resolução de nome `homeassistant` pelo DNS interno do Compose.

**Resultado:** O backend reporta HA como offline mesmo quando o container HA estivesse rodando, e o HA pode não subir de forma estável no Windows.

---

### 4.2 Fix — trocar para bridge networking com porta mapeada

Remover `network_mode: host` e mapear a porta explicitamente:

```yaml
homeassistant:
  image: homeassistant/home-assistant:stable
  # network_mode: host  ← remover
  privileged: true
  ports:
    - "8123:8123"
  volumes:
    - ha_config:/config
  environment:
    TZ: America/Sao_Paulo
  restart: unless-stopped
```

Com isso:
- O HA entra na rede bridge padrão do Compose (`domusmind_default`)
- É resolvível pelo nome `homeassistant` pelos outros serviços
- A porta 8123 é acessível no browser do Windows host normalmente
- Funciona igual no Windows (Docker Desktop) e no Linux (servidor de produção)

**Atualizar o `HASS_URL` padrão no Compose:**

```yaml
# backend e celery_worker
HASS_URL: ${HASS_URL:-http://homeassistant:8123}
```

Quem tiver `HASS_URL` no `.env` pode manter o valor atual — só o default muda.

### 4.3 Trade-off da mudança de rede

| Recurso | `network_mode: host` | Bridge + porta mapeada |
|---|---|---|
| Funciona no Windows/Docker Desktop | ✗ Instável | ✓ Sempre |
| Descoberta mDNS/Zeroconf na LAN | ✓ Sim (Linux) | ✗ Limitada |
| Backend acessa HA por nome | ✗ Não (DNS Compose) | ✓ `homeassistant:8123` |
| Porta 8123 no browser Windows | Inconsistente | ✓ Sempre |
| Requer configuração manual de integrações | Às vezes | Sim, para integrações UDP/mDNS |

Para o perfil do projeto (integração via REST API do HA, não discovery automático de dispositivos pelo HA), bridge networking é suficiente e muito mais estável.

### 4.4 Integrações que precisam de ajuste após a mudança

- **Integrations baseadas em mDNS** (Chromecast, Apple TV, etc.): precisarão ser configuradas manualmente no HA com IP fixo em vez de serem descobertas automaticamente
- **HASS_TOKEN**: continua sendo configurado via `.env` como antes
- **Webhook / automações que chamam o DomusMind**: devem usar `http://backend:8000` (nome do serviço) se configuradas dentro do próprio stack

---

## Tarefa 5 — Internacionalização (i18n): PT · EN · ES

**Objetivo:** Botão no frontend para alternar entre Português, English e Español. Todos os textos da UI são exibidos no idioma selecionado. A escolha persiste entre sessões.

### 5.1 Estratégia e biblioteca

**Abordagem escolhida:** arquivos JSON de tradução + hook personalizado via Zustand (biblioteca já instalada) — sem dependências extras, sem mudança de URL.

Não será usada roteamento por locale (`/pt/`, `/en/`) pois o usuário pediu apenas um botão de seleção, sem alterar as rotas.

**Estrutura de arquivos a criar:**

```
frontend/src/
├── i18n/
│   ├── pt.json       ← português (idioma base atual)
│   ├── en.json       ← english
│   └── es.json       ← español
├── hooks/
│   └── useI18n.ts    ← hook que lê idioma do store e retorna t()
└── lib/
    └── store.ts      ← adicionar `locale` ao Zustand store
```

### 5.2 Inventário de textos por página

Levantamento completo das strings a traduzir (≈ 185 strings):

| Arquivo | Qtd. de strings | Exemplos |
|---|---|---|
| `app/page.tsx` | 35 | Centro de Comando, Saúde dos Serviços, Cômodos Ativos… |
| `app/chat/page.tsx` | 13 | Chat operacional, Enviar, Sessão, Falar resposta… |
| `app/devices/page.tsx` | 12 | Dispositivos, Ligar, Desligar, Testar luz… |
| `app/vision/page.tsx` | 28 | Central de visão, Analisar cena, Nova câmera Hikvision… |
| `app/memory/page.tsx` | 10 | Memória, Adicionar documento, Indexar… |
| `app/lab/page.tsx` | 22 | Laboratório, Ambiente de testes, Enviar teste… |
| `app/settings/page.tsx` | 10 | Configurações, Editar chave, Salvar… |
| `app/settings/rooms/page.tsx` | 15 | Cômodos, Novo cômodo, Nome técnico… |
| `app/settings/llm/page.tsx` | 20 | LLM por agente, Roteamento de modelos… |
| `components/app-shell.tsx` | 10 | Painel, Visão, Dispositivos, Casa memória e agentes… |

### 5.3 Estrutura do arquivo de tradução

Organizado por namespace (página):

```json
// i18n/pt.json  (estrutura espelhada em en.json e es.json)
{
  "nav": {
    "dashboard": "Painel",
    "chat": "Chat",
    "vision": "Visão",
    "lab": "Testes",
    "devices": "Dispositivos",
    "memory": "Memória",
    "settings": "Ajustes",
    "tagline": "Casa, memória e agentes"
  },
  "dashboard": {
    "title": "Centro de Comando",
    "description": "Estado em tempo real do backend, serviços, cômodos e agentes ativos.",
    "refresh": "Atualizar",
    "refreshing": "Atualizando...",
    "services": "Serviços",
    "healthy": "saudáveis",
    "rooms": "Cômodos",
    "configured": "configurados",
    "devices": "Dispositivos",
    "registered": "registrados",
    "cameras": "Câmeras",
    "active": "ativas",
    "serviceHealth": "Saúde dos Serviços",
    "activeRooms": "Cômodos Ativos",
    "noRooms": "Nenhum cômodo cadastrado ainda.",
    "activityChart": "Atividade — últimas 24h",
    "errorLoad": "Falha ao carregar painel."
  },
  "chat": {
    "title": "Chat operacional",
    "placeholder": "Ex: liga a luz da sala",
    "send": "Enviar",
    "processing": "processando...",
    "session": "Sessão",
    "clear": "Limpar",
    "speak": "Falar resposta",
    "audioError": "Não foi possível reproduzir áudio."
  },
  "vision": {
    "title": "Central de visão",
    "description": "Cadastre câmeras Hikvision por IP, valide a captura e envie a cena para análise.",
    "analyze": "Analisar cena",
    "test": "Testar câmera",
    "save": "Salvar",
    "addCamera": "Nova câmera Hikvision",
    "name": "Nome",
    "room": "Cômodo",
    "ip": "IP",
    "port": "Porta",
    "user": "Usuário",
    "password": "Senha",
    "channel": "Canal",
    "saved": "Câmera IP salva.",
    "testFail": "Falha ao testar câmera.",
    "saveFail": "Falha ao salvar câmera."
  }
  // ... demais namespaces (devices, memory, lab, settings, rooms, llm)
}
```

```json
// i18n/en.json
{
  "nav": {
    "dashboard": "Dashboard",
    "chat": "Chat",
    "vision": "Vision",
    "lab": "Lab",
    "devices": "Devices",
    "memory": "Memory",
    "settings": "Settings",
    "tagline": "Home, memory and agents"
  },
  "dashboard": {
    "title": "Command Center",
    "description": "Real-time status of backend, services, rooms and active agents.",
    "refresh": "Refresh",
    "refreshing": "Refreshing...",
    "services": "Services",
    "healthy": "healthy",
    "rooms": "Rooms",
    "configured": "configured",
    "devices": "Devices",
    "registered": "registered",
    "cameras": "Cameras",
    "active": "active",
    "serviceHealth": "Service Health",
    "activeRooms": "Active Rooms",
    "noRooms": "No rooms registered yet.",
    "activityChart": "Activity — last 24h",
    "errorLoad": "Failed to load dashboard."
  }
  // ...
}
```

```json
// i18n/es.json
{
  "nav": {
    "dashboard": "Panel",
    "chat": "Chat",
    "vision": "Visión",
    "lab": "Laboratorio",
    "devices": "Dispositivos",
    "memory": "Memoria",
    "settings": "Ajustes",
    "tagline": "Casa, memoria y agentes"
  },
  "dashboard": {
    "title": "Centro de Mando",
    "description": "Estado en tiempo real del backend, servicios, habitaciones y agentes activos.",
    "refresh": "Actualizar",
    "refreshing": "Actualizando...",
    "services": "Servicios",
    "healthy": "saludables",
    "rooms": "Habitaciones",
    "configured": "configuradas",
    "devices": "Dispositivos",
    "registered": "registrados",
    "cameras": "Cámaras",
    "active": "activas",
    "serviceHealth": "Salud de Servicios",
    "activeRooms": "Habitaciones Activas",
    "noRooms": "Ninguna habitación registrada aún.",
    "activityChart": "Actividad — últimas 24h",
    "errorLoad": "Error al cargar el panel."
  }
  // ...
}
```

### 5.4 Store e hook

**Adição ao `src/lib/store.ts`:**

```typescript
// Adicionar ao store Zustand existente
locale: 'pt' | 'en' | 'es'
setLocale: (locale: 'pt' | 'en' | 'es') => void
// Persistência via localStorage (zustand/middleware/persist)
```

**Novo `src/hooks/useI18n.ts`:**

```typescript
// Hook retorna função t(namespace.key) e locale atual
export function useI18n(namespace: string) {
  const { locale } = useDomusStore()
  const dict = translations[locale][namespace]
  const t = (key: string) => dict[key] ?? key  // fallback = própria chave
  return { t, locale }
}
```

### 5.5 Botão seletor de idioma

**Localização:** sidebar do `AppShell`, acima dos badges de GPU e Gateway.

**Visual (coerente com o tema dark atual):**

```
┌─ idioma ─────────────────────────┐
│  [PT]  [EN]  [ES]                │
└───────────────────────────────────┘
```

- Três botões compactos com código ISO
- O idioma ativo recebe borda neon cyan (mesma classe `nav-active`)
- Idioma padrão: `pt` (Português)
- Persistido em localStorage via Zustand persist middleware

### 5.6 Uso nas páginas

Antes (hardcoded):
```tsx
<h1 className="page-title">Centro de Comando</h1>
```

Depois (traduzido):
```tsx
const { t } = useI18n('dashboard')
// ...
<h1 className="page-title">{t('title')}</h1>
```

### 5.7 Escopo completo de alterações

| O que criar/alterar | Arquivo |
|---|---|
| Criar | `frontend/src/i18n/pt.json` |
| Criar | `frontend/src/i18n/en.json` |
| Criar | `frontend/src/i18n/es.json` |
| Criar | `frontend/src/hooks/useI18n.ts` |
| Alterar | `frontend/src/lib/store.ts` — adicionar `locale` + persist |
| Alterar | `frontend/src/components/app-shell.tsx` — botão seletor |
| Alterar | `frontend/src/app/page.tsx` |
| Alterar | `frontend/src/app/chat/page.tsx` |
| Alterar | `frontend/src/app/devices/page.tsx` |
| Alterar | `frontend/src/app/vision/page.tsx` |
| Alterar | `frontend/src/app/memory/page.tsx` |
| Alterar | `frontend/src/app/lab/page.tsx` |
| Alterar | `frontend/src/app/settings/page.tsx` |
| Alterar | `frontend/src/app/settings/rooms/page.tsx` |
| Alterar | `frontend/src/app/settings/llm/page.tsx` |

**Total: 3 arquivos criados + 11 alterados. Nenhuma dependência nova.**

---

## Sequência de Implementação Recomendada

```
Fase 0 — Home Assistant (bloqueante, resolver primeiro)
  0.1  Remover network_mode: host do homeassistant no docker-compose.yml
  0.2  Adicionar ports: ["8123:8123"]
  0.3  Alterar HASS_URL default para http://homeassistant:8123
  0.4  Testar: docker compose up homeassistant → browser → http://localhost:8123
  0.5  Gerar novo HASS_TOKEN e atualizar .env

Fase 1 — Backend base (sem frontend)
  1.1  Migração Alembic para campos novos em Camera
  1.2  Endpoints de config de visão (GET/POST /vision/config)
  1.3  VisionService lê provider do banco
  1.4  Endpoint de detecção local (/vision/local-cameras)
  1.5  Endpoint de teste enriquecido (/vision/test-camera com snapshot)
  1.6  Método get_camera_by_name no repositório
  1.7  Agente de visão aceita nome de câmera
  1.8  Limpeza SQLite

Fase 2 — Frontend: câmeras e visão
  2.1  Página Settings > Visão (seleção YOLO/Gemini + key)
  2.2  Página Visão refatorada (scanner local + multi-câmera)
  2.3  Modal de preview com MJPEG ao vivo
  2.4  Integrar status de câmeras no dashboard

Fase 3 — Frontend: internacionalização
  3.1  Criar i18n/pt.json com todos os ~185 strings
  3.2  Criar i18n/en.json (tradução para inglês)
  3.3  Criar i18n/es.json (tradução para espanhol)
  3.4  Criar hook useI18n + adicionar locale ao Zustand store (com persist)
  3.5  Adicionar seletor PT/EN/ES ao AppShell
  3.6  Atualizar todas as páginas para usar t()
  3.7  Testar troca de idioma com reload de página (locale deve persistir)
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
| String nova adicionada ao código sem tradução | Hook `t()` retorna a própria chave como fallback — não quebra, apenas exibe a chave |
| Texto muito longo em ES/EN quebra layout | Testar em PT (menor) e ES (maior) — ajustar `text-xs` ou truncate onde necessário |
