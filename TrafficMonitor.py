import cv2
import cvzone
import math

from sort import *
import numpy as np
import torch
from ultralytics import YOLO

# Wykrywanie urządzenia CUDA
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Urządzenie używane: {device}")

# Ładowanie modelu YOLO
model = YOLO("yolov8l.pt")

# Wczytanie wideo
video_path = './ruch_uliczny.mp4'
cap = cv2.VideoCapture(video_path)

classNames = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
              "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
              "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
              "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
              "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
              "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
              "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "pottedplant", "bed",
              "diningtable", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
              "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
              "teddy bear", "hair drier", "toothbrush"]

CAR_LENGTH = 4.7 #przyjęta długość auta w metrach

# Inicjalizacja historii śledzenia i sortowania obiektów
tracker = Sort(max_age=150, min_hits=3, iou_threshold=0.2)

# Tworzenie pliku wideo wyjściowego
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('yolo.mp4', fourcc, 30, (1548, 860), isColor=True)

# Definicje zmiennych globalnych
clicked_points = []  # Punkty kliknięte przez użytkownika do definiowania pasów ruchu
carsGroupedByArr = []
roadLineSegments = []  # Segmenty dla każdego pasa jako lista punktów
trackIdBoolArray = []

def calculateSegmentLineEquations():
    # Oblicza równania prostych segmentów między klikniętymi punktami
    global roadLineSegments, carsGroupedByArr
    roadLineSegments = []
    carsGroupedByArr = []  # Zresetuj listę grupowania aut
    for i in range(0, len(clicked_points), 2):
        if i+1 < len(clicked_points):
            p1, p2 = clicked_points[i], clicked_points[i+1]
            if p1[0] != p2[0]:  # Unikaj dzielenia przez zero
                a = (p2[1] - p1[1]) / (p2[0] - p1[0])
                b = p1[1] - a * p1[0]
                roadLineSegments.append((a, b, p1, p2))
                carsGroupedByArr.append([])  # Dodaj pustą listę dla każdego segmentu

def drawSegmentLines(frame):
    # Rysowanie odcinków między klikniętymi punktami na klatce
    for a, b, p1, p2 in roadLineSegments:
        cv2.line(frame, p1, p2, (0, 255, 0), 2)  # Zielona linia

def groupCarsByRoadLine(track_id, cx, cy):
    # Grupuje auta według najbliższego pasa ruchu
    for i, (a, b, p1, p2) in enumerate(roadLineSegments):
        # Sprawdza, czy punkt (cx, cy) jest blisko odcinka
        if abs(cy - (a * cx + b)) < 10 and p1[0] <= cx <= p2[0]:
            trackIdBoolArray[track_id] = True
            carsGroupedByArr[i].append(track_id)
            break

def drawLinesBetweenCars(frame, car_centers):
    # Rysuje linie między samochodami, jeśli oba auta należą do tej samej grupy
    for group in carsGroupedByArr:
        for i in range(len(group) - 1):
            id1, id2 = group[i], group[i + 1]
            if id1 in car_centers and id2 in car_centers:
                (cx1, cy1), w1 = car_centers[id1]
                (cx2, cy2), w2 = car_centers[id2]
                # Obliczanie odległości między samochodami
                distance = math.sqrt((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2)
                #print(f"Odległość między samochodami {id1} a {id2}: {distance:.2f} pikseli")

                #najpierw uśredniamy szerokość prostokąta auta, czyli jego długość w pixelach
                avg_width_car = (w1 + w2) / 2
                #następnie przeliczamy ile jeden metr ma pixeli
                px_to_one_meter = avg_width_car / CAR_LENGTH

                # Rysowanie linii między samochodami
                cv2.line(frame, (cx1, cy1), (cx2, cy2), (255, 255, 255), 2)

                # Obliczanie punktu, w którym umieścimy tekst (pośrodku linii)
                mid_x = int((cx1 + cx2) / 2)
                mid_y = int((cy1 + cy2) / 2)

                text = f"{distance/px_to_one_meter:.2f} m"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                font_thickness = 1
                text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]
                text_x = mid_x - text_size[0] // 2  # Wyśrodkowanie tekstu
                text_y = mid_y - 10  # Ustawienie tekstu trochę nad linią


                cv2.putText(frame, text, (text_x, text_y), font, font_scale, (255, 255, 255), font_thickness)

def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        clicked_points.append((x, y))
        if len(clicked_points) % 2 == 0:
            calculateSegmentLineEquations()

# Przypisanie obsługi zdarzeń myszy
cv2.namedWindow('Traffic Tracking')
cv2.setMouseCallback('Traffic Tracking', mouse_callback)

isFirstFrame= True

while cap.isOpened():
    success, frame = cap.read()
    if success:
        results = model(frame, stream=True)
        detections = np.empty((0, 5))

        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                w, h = x2 - x1, y2 - y1
                conf = math.ceil((box.conf[0] * 100)) / 100
                cls = int(box.cls[0])
                if classNames[cls] == "car":
                    detections = np.vstack((detections, [x1, y1, x2, y2, conf]))

        resultsTracker = tracker.update(detections)
        car_centers = {}


        for rt in resultsTracker:
            x1, y1, x2, y2, id = map(int, rt)
            w, h = x2 - x1, y2 - y1
            cx, cy = x1 + w // 2, y1 + h // 2
            color = (0, 255, 0) if any(id in group for group in carsGroupedByArr) else (255, 0, 255)
            cvzone.cornerRect(frame, (x1, y1, w, h), l=9, rt=2, colorR=color)
            cvzone.putTextRect(frame, f' {id}', (max(0, x1), max(35, y1)), scale=2, thickness=3, offset=10)\

            car_centers[id] = ((cx, cy), w) #w- width, potrzebne też do przybliżania metrów

            if id >= len(trackIdBoolArray):
                trackIdBoolArray.extend([False] * (id + 1 - len(trackIdBoolArray)))

            if not trackIdBoolArray[id]:
                groupCarsByRoadLine(id, cx, cy)

        drawSegmentLines(frame)
        drawLinesBetweenCars(frame, car_centers)

        cv2.imshow("Traffic Tracking", frame)
        out.write(frame)

        if isFirstFrame:
            cv2.waitKey(0)
            isFirstFrame = False

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        break

cap.release()
out.release()
cv2.destroyAllWindows()
