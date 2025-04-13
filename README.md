# 🏡 pinica_ia

> **Sistema de automação residencial inteligente** com voz, visão computacional e inteligência artificial local.  
> A casa **ouve, vê, entende e fala com você.**

---

## ✨ Visão Geral

`pinica_ia` é um framework de automação residencial modular que integra:

✅ Captura de áudio via microfones por cômodo  
✅ Transcrição de voz com Whisper  
✅ Visão computacional com YOLOv8 (OpenCV)  
✅ Inteligência artificial com LLaMA3 via [Ollama](https://ollama.com)  
✅ Controle de dispositivos via MQTT  
✅ Fala em português com voz neural offline (Coqui TTS)  
✅ Painel opcional com Streamlit (em desenvolvimento)

---

## 📦 Funcionalidades

| Componente        | Descrição                                                                 |
|-------------------|---------------------------------------------------------------------------|
| 🎤 Captura de voz | Microfones espalhados em cada cômodo escutam comandos ou frases naturais |
| 👁️ Visão         | Câmeras IP ou locais detectam presença, objetos, pessoas                 |
| 🧠 LLM            | Um modelo LLaMA3 local interpreta o comando e decide a ação a tomar      |
| 💬 Voz            | A casa responde com frases naturais em áudio usando Coqui TTS            |
| 🧭 Controle       | Ações como ligar luz, ar-condicionado, etc., são feitas via MQTT         |
| 📈 Logs           | Toda fala gerada é salva para auditoria e personalização futura          |

---

## 🛠️ Arquitetura

```
[Câmera IP / Webcam]       [Microfone]
         │                     │
         ▼                     ▼
   [YOLOv8 - OpenCV]     [Whisper - Faster]
         └──────┐        ┌──────┘
                ▼        ▼
             [ LLM (LLaMA3 via Ollama) ]
                        │
                        ▼
        [Texto] → [Coqui TTS] → [Caixa de som]
                        │
                        ▼
                  [MQTT Publisher]
```

---

## 🚀 Como executar

### 1. Clone o projeto

```bash
git clone https://github.com/seunome/pinica_ia.git
cd pinica_ia
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Suba os serviços com Docker

```bash
docker-compose up -d
```

### 4. Configure seus cômodos e câmeras

Edite o arquivo `configs/rooms.json`:

```json
{
  "sala": {
    "mic_device": 1,
    "cameras": ["rtsp://usuario:senha@192.168.1.10:554/stream1"],
    "mqtt_topic": "casa/sala"
  }
}
```

Edite `configs/secrets.json` com suas credenciais das câmeras.

### 5. Rode o sistema principal

```bash
python app/main.py
```

---

## 📂 Estrutura do Projeto

```
pinica_ia/
├── app/
│   ├── main.py                 # Loop principal por cômodo
│   ├── room_module.py          # Captura de áudio + visão
│   ├── llm_agent.py            # Comunicação com Ollama
│   ├── mqtt_controller.py      # Publicação no broker
│   ├── validador_cameras.py    # Validação de câmeras IP
│   ├── configs/
│   │   ├── rooms.json
│   │   └── secrets.json
│   ├── utils/
│   │   ├── audio_utils.py
│   │   ├── vision_utils.py
│   │   ├── camera_utils.py
│   │   └── voz_utils.py
│   └── logs/
│       └── falas_llm.log       # Registro de todas as falas
├── docker-compose.yml
└── mosquitto.conf
```

---

## 💬 Exemplos de Frases

- “Está muito calor aqui na sala” → Aciona ar-condicionado  
- “Estou indo dormir” → Apaga luzes e fecha cortinas  
- “Tem alguém na porta?” → Verifica visão e responde  
- “Qual a temperatura na cozinha?” → Lê sensores e responde  

---

## 🔐 Segurança

- Todo o sistema pode rodar **sem internet** (com LLM e TTS locais)  
- As credenciais de câmeras são separadas no `secrets.json`  
- Suporte futuro para criptografia e autenticação de comandos  

---

## 💡 Créditos e Inspiração

Inspirado por sistemas como Jarvis (Iron Man), Home Assistant, ESPHome, Ollama e a vontade de ter uma **casa que conversa com a gente**.