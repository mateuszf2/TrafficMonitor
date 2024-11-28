import cv2
import cvzone
import math
import numpy as np
import torch

from sort import *
from ultralytics import YOLO
from collections import defaultdict

from groupingCars import calculate_segment_line_equations
from groupingCars import draw_segment_lines
from groupingCars import group_cars_by_roadLine
from calculatingDistanceBetweenCars import draw_lines_between_cars
from detectingLights import calculate_light_lines
from detectingLights import draw_light_lines
from detectingLights import check_if_enter_light_line
from calculatingSpeed import check_for_break_in_detection

# Wykrywanie urządzenia CUDA
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Urządzenie używane: {device}")

# Ładowanie modelu YOLO
model = YOLO("yolov8l.pt")
lightsModel = YOLO('lightsYolo.pt')

# Plik do zapisywania które auto przejechało na jakim świetle
fileLights = open('lightsData.txt', 'w')

# Wczytanie wideo
#videoPath = './ruch_uliczny.mp4'
#videoPath = '../trafficMonitorVideos/VID_20241122_142222.mp4'
videoPath = './Videos/VID_20241122_142222.mp4'
cap = cv2.VideoCapture(videoPath)

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

CAR_LENGTH = 4.7 # Przyjęta długość auta w metrach

# Inicjalizacja historii śledzenia i sortowania obiektów
tracker = Sort(max_age=150, min_hits=3, iou_threshold=0.2)

# Tworzenie pliku wideo wyjściowego
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('yolo.mp4', fourcc, 30, (1546, 866), isColor=True)

# Definicje zmiennych globalnych
clickedPoints = []  # Punkty kliknięte przez użytkownika do definiowania pasów ruchu (button 1)
carsGroupedByArr = []
roadLineSegments = []  # Segmenty dla każdego pasa jako lista punktów
trackIdBoolArray = []

rightClickedPoints = [] # Punkty kliknięte do definiowania pasów świateł (button 2)
lightLineSegments = []

thirdClickedPoints = [] # Punkty kliknięte do definiowania położenia sygnalizatora (sygnalizator przypisany do konkretnego pasa świateł)

firstFrame = None  # Aby wyświetlić linie na pierwszej, zatrzymanej klatce
isFirstFrame= True

def draw_light_cricle(frame):
    for i, (x, y) in enumerate(thirdClickedPoints):
        cv2.circle(frame, (x, y), 6, (255, 0, 255), -1)
        cv2.putText(frame, f"numer: {i}", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

selectedOption = 1 #selectedOption = 1 BUTTON1 , selectedOption = 2 BUTTON2
def mouse_callback(event, x, y, flags, param):
    global roadLineSegments,carsGroupedByArr,lightLineSegments, selectedOption
    if event == cv2.EVENT_LBUTTONDOWN:
        if(x > 50 and x < 200 and y > 50 and y < 100): #button 1
            selectedOption = 1
        elif(x > 250 and x < 400 and y > 50 and y < 100): #button 2
            selectedOption = 2
        elif (x > 450 and x < 600 and y > 50 and y < 100):  # button 3
            selectedOption = 3
        else: #Here we decide what function we should use(after checking which button is selected <-- )
            if(selectedOption == 1):
                clickedPoints.append((x, y))
                if len(clickedPoints) % 2 == 0:
                    roadLineSegments, carsGroupedByArr = calculate_segment_line_equations(roadLineSegments,
                                                                                          carsGroupedByArr,
                                                                                          clickedPoints, isFirstFrame,
                                                                                          firstFrame)
            elif(selectedOption == 2):
                rightClickedPoints.append((x, y))
                if len(rightClickedPoints) % 2 == 0:
                    lightLineSegments = calculate_light_lines(lightLineSegments, rightClickedPoints, isFirstFrame, firstFrame)
            elif(selectedOption == 3):
                thirdClickedPoints.append((x, y))
                draw_light_cricle(firstFrame)

# Przypisanie obsługi zdarzeń myszy
cv2.namedWindow('Traffic Tracking')
cv2.setMouseCallback('Traffic Tracking', mouse_callback)

#  Zdefiniuj słownik do przechowywania poprzednich pozycji ramek dla każdego pojazdu
carPositions = defaultdict(list)
carSpeeds = {}

# Słownik do przechowywania ostatniej klatki, w której wykryto każdy samochód
lastSeenFrame = defaultdict(lambda: -1)  # -1 indicates the car has not been seen yet
currentFrame = 0

isRed = False

def drawInterface(frame):
    global selectedOption
    cv2.rectangle(frame, (50, 50), (200, 100), (0, 0, 0), -1) #button 1
    cv2.putText(frame, "Pasy ruchu", (60, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.rectangle(frame, (250, 50), (400, 100), (0, 0, 0), -1) #button 2
    cv2.putText(frame, "Linie swiatel", (260, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.rectangle(frame, (450, 50), (600, 100), (0, 0, 0), -1) #button 3
    cv2.putText(frame, "Sygnalizacja", (460, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    match selectedOption:
        case 1:
            cv2.rectangle(frame, (50, 50), (200, 100), (0, 0, 255), 4) #red rectangle on button 1
            cv2.rectangle(frame, (250, 50), (400, 100), (0, 0, 0), 4) #red rectangle on button 2 overwritten by black rectangle
            cv2.rectangle(frame, (450, 50), (600, 100), (0, 0, 0), 4) #red rectangle on button 3 overwritten by black rectangle
        case 2:
            cv2.rectangle(frame, (250, 50), (400, 100), (0, 0, 255), 4) #red rectangle on button 2
            cv2.rectangle(frame, (50, 50), (200, 100), (0, 0, 0), 4) #red rectangle on button 1 overwritten by black rectangle
            cv2.rectangle(frame, (450, 50), (600, 100), (0, 0, 0), 4) #red rectangle on button 3 overwritten by black rectangle
        case 3:
            cv2.rectangle(frame, (450, 50), (600, 100), (0, 0, 255), 4) #red rectangle on button 3
            cv2.rectangle(frame, (50, 50), (200, 100), (0, 0, 0), 4) #red rectangle on button 1 overwritten by black rectangle
            cv2.rectangle(frame, (250, 50), (400, 100), (0, 0, 0), 4) #red rectangle on button 2 overwritten by black rectangle

while cap.isOpened():
    success, frame = cap.read()
    if success:
        if isFirstFrame:
            firstFrame = frame.copy()
            cv2.imshow("Traffic Tracking", firstFrame)
            while True:
                drawInterface(firstFrame)
                cv2.imshow("Traffic Tracking", firstFrame)
                # Aby rozpocząć wideo, kliknij „d”
                if cv2.waitKey(1) & 0xFF == ord('d'):
                    break
            isFirstFrame = False

        currentFrame += 1
        results = model(frame, stream=True, verbose=False)
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
        carCenters = {}

        # Wykrywanie modelu sygnalizacji świetlnej
        lightResults = lightsModel(frame, stream=True, verbose=False) #stream do filmików, a verbose=False aby nie wyświetlać detekcje yolo w konsoli

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
                cvzone.cornerRect(frame, (x1, y1, w, h))
            cvzone.putTextRect(frame, f'Are the lights red? {isRed}', (50, 50), scale=2, thickness=2, offset=1, colorR="")

        for rt in resultsTracker:
            x1, y1, x2, y2, id = map(int, rt)
            w, h = x2 - x1, y2 - y1
            cx, cy = x1 + w // 2, y1 + h // 2
            color = (0, 255, 0) if any(id in group for group in carsGroupedByArr) else (255, 0, 255)
            cvzone.cornerRect(frame, (x1, y1, w, h), l=9, rt=2, colorR=color)
            cvzone.putTextRect(frame, f'{id}', (max(0, x1), max(35, y1)), scale=2, thickness=2, offset=1, colorR="")

            carCenters[id] = ((cx, cy), w)

            if id >= len(trackIdBoolArray):
                trackIdBoolArray.extend([False] * (id + 1 - len(trackIdBoolArray)))

            if not trackIdBoolArray[id]:
                trackIdBoolArray,carsGroupedByArr=group_cars_by_roadLine(id, cx, cy,roadLineSegments,trackIdBoolArray,carsGroupedByArr)

            check_for_break_in_detection(lastSeenFrame,id,currentFrame,carPositions,
                                     cx,cy,carSpeeds,w,CAR_LENGTH,frame,x1,y1)

            # Zaktualizuj ostatnio widzianą klatke i historie pozycji dla następnej klatki
            lastSeenFrame[id] = currentFrame
            carPositions[id].append((cx, cy))
            if len(carPositions[id]) > 2:
                carPositions[id].pop(0)

            if check_if_enter_light_line(cx, cy, id,lightLineSegments):
                fileLights.write(f'{id} run through a red light? {isRed}\n')

        draw_segment_lines(frame,roadLineSegments)
        draw_light_lines(frame,lightLineSegments)
        draw_light_cricle(frame)
        isLightEntered = False
        draw_lines_between_cars(frame, carCenters,carsGroupedByArr,CAR_LENGTH)

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