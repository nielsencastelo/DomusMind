# 🏡 Pinica IA – Intelligent Home Assistant with Modular Agents

> **Local-first smart home system** with voice, vision, and language intelligence.  
> Your house **listens, sees, understands, speaks, and searches for you.**

---

## ✨ Overview

`pinica_ia` is a modular and agent-based home automation framework that integrates:

- 🎙️ Real-time speech transcription with Whisper
- 👁️ Vision detection using YOLOv8 (via OpenCV)
- 🧠 Local LLM-based reasoning using Ollama + Phi-4
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
[🧠 IntentClassifierAgent] → Detects wake word + classifies intent
         │
 ┌───────┴────────────────────┐
 ▼                            ▼
[👁️ VisionAgent]       [🌐 SearchAgent]
         │                     │
         ▼                     ▼
     Scene summary        Web search results
         │                     │
         └──────┬──────────────┘
                ▼
           [🧠 LLMAgent] → Generates response
                │
                ▼
          [🗣️ SpeechAgent] → Speaks back
```

---

## 📦 Core Components

| Agent/Class            | Description                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| `AudioAgent`           | Captures microphone audio and transcribes using Whisper                    |
| `VisionAgent`          | Detects people/objects via camera and describes scene with YOLOv8          |
| `LLMAgent`             | Handles user interaction via prompt + context using Ollama (Phi-4, etc.)   |
| `SpeechAgent`          | Converts response text into audio using Facebook MMS-TTS                   |
| `SearchAgent`          | Searches the internet with DuckDuckGo and returns structured results       |
| `IntentClassifierAgent`| Uses a local LLM to detect if input has "coca" and which action to perform |
| `main_async.py`        | Async orchestration and command pipeline                                   |

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

## 🗣️ Example Spoken Commands

| Transcription Example                              | Resulting Action                                           |
|----------------------------------------------------|------------------------------------------------------------|
| “Coca, what's in the camera?”                      | VisionAgent runs, takes image, describes people/scene      |
| “Hey Koka, search the internet for NCDD company”   | DuckDuckGo search executed + summary spoken                |
| “Finalize assistant, Coca”                         | Assistant shuts down gracefully                           |

---

## 📂 Project Structure

```
pinica_ia/
├── app/
│   ├── main_async.py
│   ├── agents/
│   │   ├── audio_agent.py
│   │   ├── vision_agent.py
│   │   ├── search_agent.py
│   │   ├── llm_agent.py
│   │   ├── speech_agent.py
│   │   └── intent_classifier_agent.py
│   ├── utils/
│   │   ├── vision_utils.py
│   │   ├── audio_utils.py
│   │   ├── search_util.py
│   │   └── llm_utils.py
│   ├── configs/
│   │   ├── rooms.json
│   │   └── secrets.json
│   └── search_logs/
├── notebooks/
├── docker-compose.yml
└── requirements.txt
```

---

## 🔐 Privacy & Wake Word

- Assistant only responds if a variation of “coca” is heard (e.g., “koka”, “coka”, “kouka”).
- All processing is done locally unless a web search is required.
- Searches and audio logs are saved in separate folders for auditability.

---

## 🧠 Powered By

- [Whisper](https://github.com/openai/whisper)
- [Ollama](https://ollama.com/)
- [YOLOv8](https://github.com/ultralytics/ultralytics)
- [DuckDuckGo Search API](https://duckduckgo.com)
- [MMS-TTS](https://github.com/facebookresearch/fairseq/tree/main/examples/mms)

---

## 📘 License

MIT © 2025 – Developed by Niels & contributors