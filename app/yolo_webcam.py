import cv2
from ultralytics import YOLO

# Carrega o modelo YOLOv8 (Nano é o mais leve)
model = YOLO("yolov8n.pt")  # baixa automaticamente se não tiver localmente

# Inicializa a captura da webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Erro: não foi possível acessar a webcam.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Erro ao capturar o frame da câmera.")
        break

    # Executa a detecção
    results = model(frame)[0]

    # Desenha as detecções no frame
    annotated_frame = results.plot()

    # Exibe o resultado em uma janela
    cv2.imshow("YOLOv8 - Webcam", annotated_frame)

    # Sai se pressionar a tecla ESC (27)
    if cv2.waitKey(1) == 27:
        break

# Libera recursos
cap.release()
cv2.destroyAllWindows()
