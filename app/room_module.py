# captura de áudio e visão
from utils.audio_utils import gravar_audio, salvar_temp_wav
from utils.vision_utils import detectar_objetos_camera
from faster_whisper import WhisperModel
from llm_agent import interpretar_comando
from mqtt_controller import enviar_acao

model = WhisperModel("base")

def processar_comodo(nome, config):
    print(f"[{nome}] Capturando entrada...")

    audio, fs = gravar_audio(config['mic_device'])
    path = salvar_temp_wav(audio, fs)
    segmentos, _ = model.transcribe(path)
    texto = " ".join([s.text for s in segmentos])

    objetos = []
    for cam_id in config['cameras']:
        objetos += detectar_objetos_camera(cam_id)

    resposta = interpretar_comando(nome, texto, objetos)
    enviar_acao(config['mqtt_topic'], resposta)
