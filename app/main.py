import json
import time
from room_module import processar_comodo

with open("configs/rooms.json") as f:
    rooms = json.load(f)

while True:
    for nome, config in rooms.items():
        try:
            processar_comodo(nome, config)
        except Exception as e:
            print(f"[{nome}] Erro: {e}")
    time.sleep(20)
