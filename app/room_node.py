import json
import time
from utils.audio_utils import gravar_audio, salvar_temp_wav
from utils.vision_utils import detectar_objetos_camera
from faster_whisper import WhisperModel
from main_llm_agent import interpretar_comando
from mqtt_controller import enviar_acao

# Carrega configuração
with open("configs/rooms.json") as f:
    rooms = json.load(f)

model = WhisperModel("base")

def processar_comodo(nome, config):
    print(f"[{nome}] Capturando áudio e imagem...")

    audio, fs = gravar_audio(config['mic_device'])
    wav_path = salvar_temp_wav(audio, fs)

    segmentos, _ = model.transcribe(wav_path)
    texto = " ".join([s.text for s in segmentos])

    objetos = []
    for cam_id in config['cameras']:
        objetos += detectar_objetos_camera(cam_id)

    resposta = interpretar_comando(nome, texto, objetos)
    enviar_acao(config['mqtt_topic'], resposta)

# LOOP contínuo (a cada 20 segundos)
while True:
    for comodo, conf in rooms.items():
        try:
            processar_comodo(comodo, conf)
        except Exception as e:
            print(f"Erro no cômodo {comodo}: {e}")
    time.sleep(20)

# from utils.voz_utils import falar_texto

# # Após enviar ação
# print("Resposta do LLM:", resposta)
# falar_texto(f"Entendido. {resposta}")
