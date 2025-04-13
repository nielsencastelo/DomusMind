import json
from utils.camera_utils import expand_url_placeholders
import cv2

with open("configs/rooms.json") as f:
    rooms = json.load(f)

print("\n[Validação de Câmeras IP]")

for comodo, conf in rooms.items():
    for camera in conf["cameras"]:
        url = expand_url_placeholders(camera)
        cap = cv2.VideoCapture(url)
        status = "OK" if cap.isOpened() else "FALHA"
        cap.release()
        print(f"[{comodo}] Câmera {url}: {status}")
