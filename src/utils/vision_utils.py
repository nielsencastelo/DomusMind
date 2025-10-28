from ultralytics import YOLO
import cv2
from collections import defaultdict
import time

model = YOLO("yolov8x6.pt")

def capture_image_and_describe_old():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return "Não foi possível capturar a imagem da câmera."

    results = model(frame)
    names = results[0].names
    boxes = results[0].boxes

    objetos = []
    for box in boxes:
        cls_id = int(box.cls)
        label = names[cls_id]
        objetos.append(label)

    if not objetos:
        return "Nenhum objeto foi detectado na imagem."

    # Agrupar e contar os objetos detectados
    from collections import Counter
    contagem = Counter(objetos)

    # Criar descrição natural
    descricoes = []
    for objeto, qtd in contagem.items():
        if qtd == 1:
            descricoes.append(f"um(a) {objeto}")
        else:
            descricoes.append(f"{qtd} {objeto}s")

    return "Na imagem foram detectados: " + ", ".join(descricoes) + "."



def capture_image_and_describe(frames_to_capture=5, delay_between_frames=0.3, conf_threshold=0.6):
    cap = cv2.VideoCapture(0)
    instancias = defaultdict(list)  # armazena contagem por classe em cada frame

    for _ in range(frames_to_capture):
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.resize(frame, (1280, 720))
        results = model(frame)
        names = results[0].names
        boxes = results[0].boxes

        count_this_frame = defaultdict(int)

        for box in boxes:
            if box.conf < conf_threshold:
                continue
            cls_id = int(box.cls)
            label = names[cls_id]
            count_this_frame[label] += 1

        for label, qtd in count_this_frame.items():
            instancias[label].append(qtd)

        time.sleep(delay_between_frames)

    cap.release()

    if not instancias:
        return "No objects were detected after multiple captures."

    descricoes = []
    for label, ocorrencias in instancias.items():
        media = sum(ocorrencias) / len(ocorrencias)
        if media < 1.5:
            descricoes.append(f"a {label}")
        else:
            descricoes.append(f"multiple {label}s")

    return "Na imagem foram detectados: " + ", ".join(sorted(descricoes)) + "."

