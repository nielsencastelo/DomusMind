# 🏡 Pinica IA – Intelligent Home Assistant with Modular Agents

> **Local-first smart home system** with voice, vision, and language intelligence.  
> Your house **listens, sees, understands, speaks, and searches for you.**

---

## ✨ Overview

`pinica_ia` is a modular and agent-based home automation framework that integrates:

- 🎙️ Real-time speech transcription with Whisper
- 👁️ Vision detection using YOLOv8 (via OpenCV)
- 🧠 Local LLM-based reasoning using Ollama + LLaMA3
- 🗣️ Natural speech responses using Facebook MMS-TTS
- 🌐 Web search agent via DuckDuckGo
- 💡 Device control via MQTT (in development)
- 📊 Optional UI with Streamlit (in development)

---

## 🧠 Agent Architecture

Each function is encapsulated as an **independent agent**, orchestrated asynchronously:

```
[🎙️ AudioAgent] → Captures & transcribes speech
         │
         ▼
[🧠 LLM Planner] (optional)
         │
 ┌───────┴───────────────────┐
 ▼                           ▼
[👁️ VisionAgent]       [🌐 SearchAgent]
         │                    │
         ▼                    ▼
     Scene summary        Web search results
         │                    │
         └──────┬─────────────┘
                ▼
           [🧠 LLMAgent] → Generates response
                │
                ▼
          [🗣️ SpeechAgent] → Speaks back
```

---

## 📦 Core Components

| Agent/Class        | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| `AudioAgent`       | Captures microphone audio and transcribes using Whisper                    |
| `VisionAgent`      | Detects people/objects via camera and describes scene with YOLOv8          |
| `LLMAgent`         | Handles user interaction via prompt + context using Ollama (LLaMA3, etc.) |
| `SpeechAgent`      | Converts response text into audio using Facebook MMS-TTS                   |
| `SearchAgent`      | Searches the internet with DuckDuckGo and returns structured results       |
| `main_async.py`    | Async orchestration and command pipeline                                   |

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourname/pinica_ia.git
cd pinica_ia
```

### 2. Install requirements

```bash
pip install -r requirements.txt
```

### 3. Start support services (if using Docker)

```bash
docker-compose up -d
```

### 4. Configure your environment

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

And update `configs/secrets.json` with your credentials.

### 5. Run the assistant

```bash
python app/main_async.py
```

---

## 📂 Project Structure

```
pinica_ia/
├── app/
│   ├── main_async.py            # Async orchestrator
│   ├── agents/
│   │   ├── audio_agent.py       # Audio input + Whisper
│   │   ├── vision_agent.py      # Scene understanding
│   │   ├── search_agent.py      # DuckDuckGo web search
│   │   ├── llm_agent.py         # Language model interaction
│   │   └── speech_agent.py      # Text-to-speech output
│   ├── utils/
│   │   ├── vision_utils.py
│   │   ├── audio_utils.py
│   │   ├── search_util.py
│   │   └── nlp_utils.py         # Wake word, intent classification
│   ├── configs/
│   │   ├── rooms.json
│   │   └── secrets.json
│   └── search_logs/             # Saved search sessions
├── notebooks/                   # Test notebooks per agent
│   ├── Internet.ipynb
│   ├── Audio.ipynb
│   ├── LLM.ipynb
│   └── ...
├── docker-compose.yml
└── requirements.txt
```

---

## 💬 Example Commands

| Spoken Command                           | What Happens                                              |
|------------------------------------------|-----------------------------------------------------------|
| “Estou indo dormir”                      | Turns off lights, closes curtains                         |
| “Tem alguém na porta?”                   | Captures image, detects people, describes via LLM         |
| “Qual a temperatura na cozinha?”         | Reads sensors and responds                                |
| “Pesquise na internet sobre IA médica”  | Uses DuckDuckGo, saves results, and summarizes response   |

---

## 🔐 Security and Privacy

- Fully offline capability (LLM, TTS, Vision, Audio)
- Internet search is optional and saved separately
- Credentials are stored securely in `secrets.json`

---

## 💡 Credits & Inspiration

Inspired by:
- JARVIS (Iron Man)
- Home Assistant & ESPHome
- Ollama + DuckDuckGo
- The dream of a truly intelligent, offline-capable, human-friendly home.

---

## 📘 License

MIT © 2025 – Developed by Niels & collaborators