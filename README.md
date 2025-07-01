
# 🏡 Pinica IA – Intelligent Home Assistant with Modular Agents

> **Local-first smart home system** with voice, vision, and language intelligence.  
> Your house **listens, sees, understands, speaks, searches — and now controls lights.**

---

## ✨ Overview

`pinica_ia` is a modular and agent-based home automation framework that integrates:

- 🎙️ Real-time speech transcription with Whisper
- 👁️ Vision detection using YOLOv8 (via OpenCV)
- 🧠 Local LLM-based reasoning using Ollama + Phi-4
- 🗣️ Natural speech responses using Facebook MMS-TTS
- 🌐 Web search agent via DuckDuckGo
- 💡 Device control via **Home Assistant (Sonoff supported)**
- 📊 Optional UI with Django (in development)

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
| `HomeAssistantUtils`   | Controls smart devices via Home Assistant REST API                         |
| `main.py`              | Async orchestration and command pipeline                                   |

---

## 🧩 Home Assistant Integration

Pinica IA now integrates with [Home Assistant](https://www.home-assistant.io/) to control devices like **Sonoff switches**.

- Uses the **local REST API** with long-lived token authentication.
- Devices must be configured in Home Assistant and mapped to rooms.
- New field `light_entity_id` added in `configs/rooms.json`:

```json
{
  "escritorio": {
    "mic_device": 4,
    "cameras": ["rtsp://..."],
    "mqtt_topic": "casa/escritorio",
    "light_entity_id": "switch.sonoff_10013abe9c_1"
  }
}
```

> Support for more Home Assistant services (climate, locks, etc.) coming soon.

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
  "sala": {
    "mic_device": 2,
    "cameras": ["rtsp://user:pass@192.168.1.20:554/stream"],
    "mqtt_topic": "home/sala",
    "light_entity_id": "switch.sonoff_sala"
  }
}
```

Update `.env` with your Home Assistant token:

```env
TOKEN=your_home_assistant_token
HASS_URL=http://localhost:8123
```

### 5. Run the assistant

```bash
python app/main_async.py
```

---

## 🗣️ Example Spoken Commands

| Transcription Example                               | Resulting Action                                            |
|-----------------------------------------------------|-------------------------------------------------------------|
| “Coca, what's in the camera?”                       | VisionAgent runs, takes image, describes people/scene       |
| “Koka, turn on the light in the office”             | Sends request to HA to turn on `switch.sonoff_...`          |
| “Hey Coka, search the internet for pinica project”  | DuckDuckGo search executed + summary spoken                 |
| “Desligar todas as luzes, Coca”                     | (Upcoming) Multi-device HA control pipeline                 |
| “Finalize assistant, Coca”                          | Assistant shuts down gracefully                             |

---

## 📂 Project Structure

```
pinica_ia/
├── app/
│   ├── main_async.py
│   ├── agents/
│   ├── utils/
│   │   ├── home_assistant.py  ← control via HA
│   ├── configs/
│   │   ├── rooms.json
│   │   ├── secrets.json
├── notebooks/
├── .env
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
- [Home Assistant](https://www.home-assistant.io/)

---

## 📘 License

MIT © 2025 – Developed by Nielsen Castelo Damasceno Dantas & contributors
