# 🏡 Pinica IA

> **Smart home automation system** with voice, computer vision, and local artificial intelligence.  
> The house **listens, sees, understands, and talks to you.**

---

## ✨ Overview

`pinica_ia` is a modular home automation framework that integrates:

- Audio capture via room-specific microphones (in development)  
- Voice transcription using Whisper  
- Computer vision with YOLOv8 (OpenCV)  
- Artificial intelligence via LLMs using [Ollama](https://ollama.com)  
- Device control via MQTT (in development)  
- Offline neural voice in Portuguese (Facebook TTS)  
- Optional control panel using Streamlit (in development)

---

## 📦 Features

| Component         | Description                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| 🎤 Voice Capture  | Microphones spread across rooms listen for commands or natural phrases      |
| 👁️ Vision         | IP or local cameras detect presence, objects, people                        |
| 🧠 LLM             | A local LLaMA3 model interprets the command and decides what to do         |
| 💬 Voice           | The house responds in natural spoken language using Facebook TTS            |
| 🧭 Control         | Actions like turning on lights, AC, etc., are handled via MQTT              |
| 📈 Logs            | All generated speech is saved for auditing and future customization         |

---

## 🛠️ Architecture

```
[IP Camera / Webcam]         [Microphone]
         │                         │
         ▼                         ▼
   [YOLOv8 - OpenCV]        [Whisper - Faster]
         └──────┐              ┌──────┘
                ▼              ▼
         [ LLM (LLaMA3 via Ollama) ]
                        │
                        ▼
        [Text] → [Coqui TTS] → [Speaker]
                        │
                        ▼
                  [MQTT Publisher]
```

---

## 🚀 How to Run

### 1. Clone the project

```bash
git clone https://github.com/yourname/pinica_ia.git
cd pinica_ia
```

### 2. Install the dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the services with Docker

```bash
docker-compose up -d
```

### 4. Configure your rooms and cameras

Edit the file `configs/rooms.json`:

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

### 5. Run the main system

```bash
python app/main.py
```

---

## 📂 Project Structure

```
pinica_ia/
├── app/
│   ├── main.py                 # Main loop per room
│   ├── room_module.py          # Audio + vision capture
│   ├── llm_agent.py            # LLM communication
│   ├── mqtt_controller.py      # Broker publishing
│   ├── configs/
│   │   ├── rooms.json
│   │   └── secrets.json
│   ├── utils/
│   │   ├── audio_utils.py
│   │   ├── camera_utils.py
│   │   ├── llm_utils.py
│   │   ├── nlp_utils.py
│   │   ├── vision_utils.py
│   │   └── voice_utils.py
│   └── logs/
│       └── llm_speech.log      # All spoken responses log
├── docker-compose.yml
└── mosquitto.conf
```

---

## 💬 Sample Phrases

- “It’s too hot here in the living room” → Turns on air conditioning  
- “I’m going to sleep” → Turns off lights and closes curtains  
- “Is someone at the door?” → Checks vision and responds  
- “What’s the temperature in the kitchen?” → Reads sensors and responds  

---

## 🔐 Security

- The entire system can run **offline** (local LLM and TTS)  
- Camera credentials are stored separately in `secrets.json`  
- Future support for encryption and command authentication  

---

## 💡 Credits and Inspiration

Inspired by systems like Jarvis (Iron Man), Home Assistant, ESPHome, Ollama, and the dream of having a **house that talks to us**.