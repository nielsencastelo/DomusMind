from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.pt")

def detectar_objetos_camera(camera_source):
    cap = cv2.VideoCapture(camera_source)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print(f"[ERRO] Não foi possível capturar imagem da câmera: {camera_source}")
        return []

    results = model(frame)
    nomes = results[0].names
    labels = [nomes[int(cls)] for cls in results[0].boxes.cls.tolist()]
    return list(set(labels))  # Remove duplicadas
