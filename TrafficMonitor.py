import threading

import cv2
import cvzone
import math
import numpy as np
import torch
import os

import queue
#from torch.multiprocessing import queue #nie wiem ktore queue importowac

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
from detectingLights import draw_light_circle
from calculatingSpeed import check_for_break_in_detection
from creatingInterface import drawInterface

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
#videoPath = './Videos/VID_20241122_143045.mp4'
videoPath = './lightsLong.mkv'

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
out = cv2.VideoWriter('yolo.mp4', fourcc, 30, (1548,860), isColor=True)

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


selectedOption = 1 #selectedOption = 1 BUTTON1 , selectedOption = 2 BUTTON2
def mouse_callback(event, x, y, flags, param):
    global roadLineSegments,carsGroupedByArr,lightLineSegments, selectedOption, thirdClickedPoints
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
                    lightLineSegments = calculate_light_lines(lightLineSegments, rightClickedPoints, isFirstFrame, firstFrame, idToColorLight)
            elif(selectedOption == 3):
                thirdClickedPoints.append((x, y))
                draw_light_circle(firstFrame,thirdClickedPoints)

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

# Queues for frame sharing
frameQueue = queue.Queue(maxsize=10)  # Limit size to prevent excessive memory use
processedQueue = queue.Queue(maxsize=10)

# Thread control variables
stopThreads = False
startProcessing = False

frameCount=None
def capture_thread(videoPath, frameQueue):
    global stopThreads,startProcessing,frameCount
    cap = cv2.VideoCapture(videoPath)
    frameCount = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Total frames in input video: {frameCount}")
    while not stopThreads:
        if startProcessing:
            success, frame = cap.read()
            if not success:
                break
            try:
                frameQueue.put(frame,timeout=1)  # Use timeout to avoid hanging
            except queue.Full:
                continue  # Skip if the queue is full
    cap.release()

idToColorLight= defaultdict(str) #Domyślna wartość dla brakującego klucza to pusty string
carsHasCrossedLight = {}

def processing_thread(frameQueue, processedQueue, model, tracker):
    global stopThreads,currentFrame,isFirstFrame,isRed,clickedPoints,carsGroupedByArr,roadLineSegments
    global trackIdBoolArray,rightClickedPoints,lightLineSegments,thirdClickedPoints,firstFrame, carsHasCrossedLight
    global lightsModel,fileLights,classNames,classNamesLights,CAR_LENGTH,carPositions,carSpeeds,lastSeenFrame,selectedOption

    while not stopThreads:
        try:
            frame= frameQueue.get(timeout=1)  # Unpack frame and timestamp
        except queue.Empty:
            continue

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
        lightResults = lightsModel(frame, stream=True,
                                   verbose=False)  # stream do filmików, a verbose=False aby nie wyświetlać detekcje yolo w konsoli

        for lr in lightResults:
            boxes = lr.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                w, h = x2 - x1, y2 - y1
                conf = math.ceil((box.conf[0] * 100)) / 100
                cls = int(box.cls[0])

                for i, (x, y) in enumerate(thirdClickedPoints):
                    if( (x1 < x < x1+w) and (y1 < y < y1+h) ):
                        if classNamesLights[cls] == "Traffic Light -Red-":
                            idToColorLight[i]= "red"
                        elif classNamesLights[cls] == "Traffic Light -Green-":
                            idToColorLight[i]= "green"

                if classNamesLights[cls] == "Traffic Light -Red-":
                    isRed = True
                elif classNamesLights[cls] == "Traffic Light -Green-":
                    isRed = False
                cvzone.cornerRect(frame, (x1, y1, w, h))
            cvzone.putTextRect(frame, f'Are the lights red? {idToColorLight[0]}', (50, 50), scale=2, thickness=2, offset=1,
                               colorR="")

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
                trackIdBoolArray, carsGroupedByArr = group_cars_by_roadLine(id, cx, cy, roadLineSegments,
                                                                            trackIdBoolArray, carsGroupedByArr)

            check_for_break_in_detection(lastSeenFrame, id, currentFrame, carPositions,
                                         cx, cy, carSpeeds, w, CAR_LENGTH, frame, x1, y1)

            # Zaktualizuj ostatnio widzianą klatke i historie pozycji dla następnej klatki
            lastSeenFrame[id] = currentFrame
            carPositions[id].append((cx, cy))
            if len(carPositions[id]) > 2:
                carPositions[id].pop(0)

            #what happens after someone runsa a red light (photo + log info)
            if check_if_enter_light_line(cx, cy, id, lightLineSegments, idToColorLight, carsHasCrossedLight):
                fileLights.write(f'{id} run through a red light? {carsHasCrossedLight.get(id)}\n')
                print(f"{id} przejechało na RED?? {carsHasCrossedLight.get(id)}")

                cv2.rectangle(frame, (x1, y1), (x1 + w, y1 + h), (0, 0, 255), 4)

                outputFolder= './ImagesRed'
                os.makedirs(outputFolder, exist_ok=True)
                cv2.imwrite(f'{outputFolder}/{id}RED.jpg', frame)


        draw_segment_lines(frame, roadLineSegments)
        draw_light_lines(frame, lightLineSegments, idToColorLight)
        draw_light_circle(frame, thirdClickedPoints)
        draw_lines_between_cars(frame, carCenters, carsGroupedByArr, CAR_LENGTH)

        # Add processed frame to the processed queue
        if not processedQueue.full():
            processedQueue.put(frame)  # Pass timestamp along
            #print(currentFrame)


def main():
    global stopThreads, startProcessing, firstFrame
    # Start threads
    captureThreadObj = threading.Thread(target=capture_thread, args=(videoPath, frameQueue))
    processingThreadObj = threading.Thread(target=processing_thread, args=(frameQueue, processedQueue, model, tracker))

    captureThreadObj.start()
    processingThreadObj.start()

    # Initialize video capture for the first frame
    cap = cv2.VideoCapture(videoPath)
    success, firstFrame= cap.read()
    cap.release()

    if not success:
        print("Error: Could not read the first frame.")


    # cv2.imshow musza pracowac na tym samym wątku (w tym przypadku MainThread)
    while not stopThreads:
        if not startProcessing:  # In drawing mode
            cv2.imshow("Traffic Tracking", firstFrame)
            drawInterface(firstFrame,selectedOption)
            key = cv2.waitKey(1)
            if key == ord('d'):  # Start processing when 'd' is pressed
                startProcessing = True
            elif key == ord('q'):  # Quit
                stopThreads = True
                break
        else:  # In processing mode
            try:
                frame = processedQueue.get(timeout=1)
                cv2.imshow("Traffic Tracking", frame)
                out.write(frame)
            except queue.Empty:
                continue

            key = cv2.waitKey(1)
            # Quit (Some of frames can be lost,once lost 3 frames and I was suprised why video has not ended)
            if key == ord('q') or currentFrame==frameCount-5:
                stopThreads = True
                break

    # Wait for threads to finish
    captureThreadObj.join()
    processingThreadObj.join()


    fileLights.close()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

