# 🏡 Pinica IA – Intelligent Home Automation with Agents

> **Agent-based smart home system** using voice, computer vision, and local LLMs.  
> Your house **listens, sees, understands, and talks to you** – intelligently.

---

## ✨ Overview

`pinica_ia` is a modular agent-based automation framework that integrates:

- 🎙️ Audio capture and speech recognition using Whisper
- 👁️ Vision-based scene detection using YOLOv8 (via OpenCV)
- 🧠 Natural language understanding and reasoning using Ollama + LLaMA3
- 🗣️ Natural voice responses using Facebook MMS-TTS
- 💡 MQTT-based device control (in development)
- 📊 Optional Streamlit dashboard (in development)

---

## 🧠 Agent Architecture

Each key function is encapsulated as an **agent**, allowing for modular orchestration:

```
[🎙️ AudioAgent] → Transcribe speech
        │
        ▼
[🧠 LLM PlannerAgent (optional)] → Plan actions
        │
        ├─▶ [👁️ VisionAgent] (if vision is needed)
        └─▶ [🧠 LLMAgent] → Generate response
                          │
                          ▼
                   [🗣️ SpeechAgent]
```

---

## 📦 Key Components

| Agent/Class       | Description                                                      |
|-------------------|------------------------------------------------------------------|
| `AudioAgent`      | Captures user speech and transcribes using Whisper              |
| `VisionAgent`     | Detects and describes scene objects using YOLOv8                |
| `LLMAgent`        | Sends text (and context) to Ollama LLM and returns responses    |
| `SpeechAgent`     | Converts LLM responses into voice using MMS-TTS                 |
| `main_async.py`   | Orchestrates agent interaction via asyncio loop                 |

---

## 🚀 How to Run

### 1. Clone the repository

```bash
git clone https://github.com/yourname/pinica_ia.git
cd pinica_ia
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start services with Docker

```bash
docker-compose up -d
```

### 4. Configure rooms and camera access

Edit `configs/rooms.json`:

```json
{
  "living_room": {
    "mic_device": 1,
    "cameras": ["rtsp://user:password@192.168.1.10:554/stream1"],
    "mqtt_topic": "home/living_room"
  }
}
```

Edit `configs/secrets.json` with your camera credentials.

### 5. Run the assistant with agents

```bash
python app/main_async.py
```

---

## 📂 Project Structure (after agent refactor)

```
pinica_ia/
├── app/
│   ├── main_async.py            # Async loop using agents
│   ├── agents/
│   │   ├── audio_agent.py       # Audio capture agent
│   │   ├── vision_agent.py      # Vision scene agent
│   │   ├── llm_agent.py         # LLM query agent
│   │   └── speech_agent.py      # Text-to-speech agent
│   ├── utils/                   # Whisper, YOLO, TTS helpers
│   ├── configs/
│   │   ├── rooms.json
│   │   └── secrets.json
│   └── logs/
│       └── llm_speech.log       # Log of spoken outputs
├── docker-compose.yml
└── mosquitto.conf
```

---

## 💬 Example Commands

- "Está muito calor aqui" → Turns on the air conditioning  
- "Estou indo dormir" → Turns off lights and closes curtains  
- "Tem alguém na porta?" → Uses camera to check and respond  
- "Qual a temperatura na cozinha?" → Reads sensors and answers  

---

## 🔐 Security

- Fully offline capable: LLM and TTS run locally  
- Camera credentials are isolated in `secrets.json`  
- Future support for encryption and command authentication  

---

## 💡 Credits & Inspiration

Inspired by JARVIS (Iron Man), Home Assistant, ESPHome, Ollama, and the dream of a **talking intelligent home**.