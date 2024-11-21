import cv2
import cvzone
import math

from PIL.ImageChops import offset

from sort import *
import numpy as np
import torch
from ultralytics import YOLO
from collections import defaultdict


# Wykrywanie urządzenia CUDA
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Urządzenie używane: {device}")

# Ładowanie modelu YOLO
model = YOLO("yolov8l.pt")
lightsModel = YOLO('lightsYolo.pt')

# Plik do zapisywania które auto przejechało na jakim świetle
fileLights = open('lightsData.txt', 'a')

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

classNamesLights = ['Traffic Light -Green-', 'Traffic Light -Off-', 'Traffic Light -Red-', 'Traffic Light -Yellow-']

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

rightClicked_points = []
lightLineSegments = []

firstFrame = None  # to display lines on the frist, stopped frame
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
                if isFirstFrame:
                    drawSegmentLines(firstFrame) #to display lines on the frist, stopped frame
                    cv2.imshow("Traffic Tracking", firstFrame)

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
    if event == cv2.EVENT_RBUTTONDOWN:
        rightClicked_points.append((x, y))
        if len(rightClicked_points) % 2 == 0:
            calculateLightLines()

def calculateLightLines():
    global lightLineSegments
    lightLineSegments = []
    for i in range(0, len(rightClicked_points), 2):
        if i+1 < len(rightClicked_points):
            p1, p2 = rightClicked_points[i], rightClicked_points[i+1]
            if p1[0] != p2[0]:  # Unikaj dzielenia przez zero
                a = (p2[1] - p1[1]) / (p2[0] - p1[0])
                b = p1[1] - a * p1[0]
                lightLineSegments.append((a, b, p1, p2))
                if isFirstFrame:
                    drawLightLines(firstFrame) #to display lines on the frist, stopped frame
                    cv2.imshow("Traffic Tracking", firstFrame)
#lines for traffic lights, to detect if car breaks the law
def drawLightLines(frame):
    global isLightEntered
    for (a, b, p1, p2) in lightLineSegments:
        color = (255, 0, 0) if not isLightEntered else (0, 0, 255)
        cv2.line(frame, p1, p2, color, 2)

isRed = False
isLightEntered= False
cars_has_crossed_light = {}
def checkIfEnterLightLine(cx, cy, id):
    global cars_has_crossed_light
    #cars_has_crossed_light.get(id, False) sprawdza czy w danym id jest True, jeśli nie byłoby w słowniku klucza o danym id to nie będzie błędu bo wtedy przyjmujemy domyślnie False dla takiego id
    if cars_has_crossed_light.get(id, False):
        return False
    for a, b, p1, p2 in lightLineSegments:
        # Sprawdza, czy punkt (cx, cy) jest blisko odcinka
        if abs(cy - (a * cx + b)) < 10 and p1[0] <= cx <= p2[0]:
            global isLightEntered
            isLightEntered = True
            cars_has_crossed_light[id] = True
            return True
    return False


# Przypisanie obsługi zdarzeń myszy
cv2.namedWindow('Traffic Tracking')
cv2.setMouseCallback('Traffic Tracking', mouse_callback)

isFirstFrame= True

# Define a dictionary to store previous frame positions for each vehicle
car_positions = defaultdict(list)
car_speeds = {}

# Set video frame rate (assuming 30 FPS)
FPS = 30
TIME_BETWEEN_FRAMES = 1 / FPS  # Time between frames in seconds

def calculate_speed(distance_pixels, px_to_one_meter):
    # Convert pixels to meters
    distance_meters = distance_pixels / px_to_one_meter
    # Calculate speed in meters per second
    speed_mps = distance_meters / TIME_BETWEEN_FRAMES
    # Convert speed to km/h
    speed_kph = speed_mps * 3.6
    return speed_kph

# Define a dictionary to store recent speeds for each car to smooth the results
speed_history = defaultdict(list)
WINDOW_SIZE = 30  # The number of frames to average over

def moving_average(speeds):
    return sum(speeds) / len(speeds) if speeds else 0

# Dictionary to store the last frame where each car was detected
last_seen_frame = defaultdict(lambda: -1)  # -1 indicates the car has not been seen yet
FRAME_GAP_THRESHOLD = 10  # Number of frames after which speed history should reset

current_frame = 0

while cap.isOpened():
    success, frame = cap.read()
    if success:
        if isFirstFrame:
            firstFrame = frame.copy()
            cv2.imshow("Traffic Tracking", firstFrame)
            while True:
                #To start video you should click 'd'
                if cv2.waitKey(1) & 0xFF == ord('d'):
                    break
            isFirstFrame = False



        current_frame += 1
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

        #Traffic lights model detection
        lightResults = lightsModel(frame, stream=True)

        for lr in lightResults:
            boxes = lr.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                w, h = x2 -x1, y2 - y1
                conf = math.ceil((box.conf[0]*100)) / 100
                cls = int(box.cls[0])

                if classNamesLights[cls] == "Traffic Light -Red-":
                    isRed = True
                elif classNamesLights[cls] == "Traffic Light -Green-":
                    isRed = False
            cvzone.putTextRect(frame, f'Are the lights red? {isRed}', (50, 50), scale=2, thickness=2, offset=1, colorR="")

        for rt in resultsTracker:
            x1, y1, x2, y2, id = map(int, rt)
            w, h = x2 - x1, y2 - y1
            cx, cy = x1 + w // 2, y1 + h // 2
            color = (0, 255, 0) if any(id in group for group in carsGroupedByArr) else (255, 0, 255)
            cvzone.cornerRect(frame, (x1, y1, w, h), l=9, rt=2, colorR=color)
            cvzone.putTextRect(frame, f'{id}', (max(0, x1), max(35, y1)), scale=2, thickness=2, offset=1, colorR="")

            car_centers[id] = ((cx, cy), w)

            if id >= len(trackIdBoolArray):
                trackIdBoolArray.extend([False] * (id + 1 - len(trackIdBoolArray)))

            if not trackIdBoolArray[id]:
                groupCarsByRoadLine(id, cx, cy)

            # Check for a break in detection (occlusion or reappearance)
            if last_seen_frame[id] == -1 or (current_frame - last_seen_frame[id] > FRAME_GAP_THRESHOLD):
                # Reset speed history if the car was unseen for too many frames
                speed_history[id] = []  # Clear the speed history to avoid a spike
                car_positions[id] = [(cx, cy)]  # Reset position history
                car_speeds[id] = 0  # Reset displayed speed
            else:
                # Normal speed calculation if detection is consistent
                if len(car_positions[id]) > 0:
                    prev_x, prev_y = car_positions[id][-1]
                    distance_pixels = math.sqrt((cx - prev_x) ** 2 + (cy - prev_y) ** 2)
                    px_to_one_meter = w / CAR_LENGTH
                    speed_kph = calculate_speed(distance_pixels, px_to_one_meter)

                    # Update speed history and calculate smoothed speed
                    speed_history[id].append(speed_kph)
                    if len(speed_history[id]) > WINDOW_SIZE:
                        speed_history[id].pop(0)

                    smoothed_speed_kph = moving_average(speed_history[id])
                    car_speeds[id] = smoothed_speed_kph

                    # Display the smoothed speed on the frame
                    speed_text = f"{smoothed_speed_kph:.2f} km/h"
                    cv2.putText(frame, speed_text, (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

            # Update last seen frame and position history for the next frame
            last_seen_frame[id] = current_frame
            car_positions[id].append((cx, cy))
            if len(car_positions[id]) > 2:
                car_positions[id].pop(0)

            if checkIfEnterLightLine(cx, cy, id):
                fileLights.write(f'{id} run through a red light? {isRed}\n')

        drawSegmentLines(frame)
        drawLightLines(frame)
        isLightEntered = False
        drawLinesBetweenCars(frame, car_centers)

        cv2.imshow("Traffic Tracking", frame)
        out.write(frame)


        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        break

fileLights.close()
cap.release()
out.release()
cv2.destroyAllWindows()