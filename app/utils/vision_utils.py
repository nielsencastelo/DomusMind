from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.pt")

def capture_image_and_describe():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return "Nenhuma imagem capturada."

    results = model(frame)
    names = results[0].names
    boxes = results[0].boxes

    objetos = []
    for box in boxes:
        cls_id = int(box.cls)
        label = names[cls_id]
        conf = float(box.conf)
        objetos.append((label, conf))

    if not objetos:
        return "Nenhum objeto detectado."

    descricoes = []
    for label, conf in objetos:
        conf_percent = int(conf * 100)
        if conf >= 0.8:
            descricoes.append(f"{label} ({conf_percent}%)")
        elif conf >= 0.4:
            descricoes.append(f"possível {label} ({conf_percent}%)")
        else:
            descricoes.append(f"{label} incerto ({conf_percent}%)")

    return f"Objetos detectados: {', '.join(descricoes)}."