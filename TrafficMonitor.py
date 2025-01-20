import threading
from datetime import datetime

import cv2
import ctypes
import cvzone
import math
import torch
import queue

from contourpy.util.data import simple

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
from calculatingDriversReactionTime import calculate_reaction_time

import tkinter as tk
from tkinter import simpledialog
from tkinter import messagebox

from database import insert_nameOfPlace, get_nameOfPlace
from database import insert_video
from database import insert_trafficLanes
from database import insert_signalLights
from database import insert_carGrouped
from database import insert_carNotGrouped
from database import insert_speedsOfCars
from database import insert_distancesBetweenCars
from database import get_signallights
from database import get_trafficlanes
from database import delete_trafficLanes_cascade

# Wykrywanie urządzenia CUDA
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Urządzenie używane: {device}")

# Ładowanie modelu YOLO
model = YOLO("yolov8l.pt")
lightsModel = YOLO('lightsYolo.pt')

# Plik do zapisywania które auto przejechało na jakim świetle
fileLights = open('lightsData.txt', 'w')

# Wczytanie wideo
#videoPath = '../trafficMonitorVideos/ruch_uliczny.mp4'
videoPath = '../trafficMonitorVideos/VID_20241122_143045.mp4'
#videoPath = './Videos/VID_20241122_143045.mp4'
#videoPath = './lightsLong.mkv'

# Explicitly set OpenCV to avoid scaling issues
ctypes.windll.user32.SetProcessDPIAware()  # For Windows systems

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
out = cv2.VideoWriter('yolo.mp4', fourcc, 30, (1920,1080), isColor=True)

# Definicje zmiennych globalnych
clickedPoints = []  # Punkty kliknięte przez użytkownika do definiowania pasów ruchu (button 1)
carsGroupedByArr = []
roadLineSegments = []  # Segmenty dla każdego pasa jako lista punktów
trackIdBoolArray = []
allCarsId = set()

rightClickedPoints = [] # Punkty kliknięte do definiowania pasów świateł (button 2)
lightLineSegments = []

thirdClickedPoints = [] # Punkty kliknięte do definiowania położenia sygnalizatora (sygnalizator przypisany do konkretnego pasa świateł)

firstFrame = None  # Aby wyświetlić linie na pierwszej, zatrzymanej klatce
isFirstFrame= True


selectedOption = 1 #selectedOption = 1 BUTTON1 , selectedOption = 2 BUTTON2

# Global variables for ROI
drawing = False
roiStart = (1,1)
roiEnd = (1,1)
ifRoi=False
def mouse_callback(event, x, y, flags, param):
    global roadLineSegments,carsGroupedByArr,lightLineSegments, selectedOption, thirdClickedPoints
    global drawing, roiStart, roiEnd,ifRoi

    if event == cv2.EVENT_LBUTTONDOWN:
        if(x > 50 and x < 200 and y > 50 and y < 100): #button 1
            selectedOption = 1
        elif(x > 250 and x < 400 and y > 50 and y < 100): #button 2
            selectedOption = 2
        elif (x > 450 and x < 600 and y > 50 and y < 100):  # button 3
            selectedOption = 3
        elif(x > 650 and x < 800 and y > 50 and y < 100):
            selectedOption=4
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
            elif (selectedOption == 4):
                ifRoi=True
                if drawing == False:
                    if event == cv2.EVENT_LBUTTONDOWN:
                        drawing = True
                        roiStart = (x, y)
                        roiEnd = (x, y)
                if drawing == True:
                    if event == cv2.EVENT_LBUTTONDOWN:
                        roiEnd = (x, y)


def load_saved_data():
    global roadLineSegments,carsGroupedByArr, clickedPoints, isFirstFrame, firstFrame, lightLineSegments, rightClickedPoints, thirdClickedPoints

    roadLineSegments, carsGroupedByArr = calculate_segment_line_equations(roadLineSegments,
                                                                          carsGroupedByArr,
                                                                          clickedPoints, isFirstFrame,
                                                                          firstFrame)
    lightLineSegments = calculate_light_lines(lightLineSegments, rightClickedPoints, isFirstFrame, firstFrame,
                                              idToColorLight)
    draw_light_circle(firstFrame, thirdClickedPoints)

# Przypisanie obsługi zdarzeń myszy
cv2.namedWindow('Traffic Tracking')
cv2.setMouseCallback('Traffic Tracking', mouse_callback)

#  Zdefiniuj słownik do przechowywania poprzednich pozycji ramek dla każdego pojazdu
carPositions = defaultdict(list)
carSpeeds = defaultdict(list)
distancesBetweenCars = defaultdict(list)

# Słownik do przechowywania ostatniej klatki, w której wykryto każdy samochód
lastSeenFrame = defaultdict(lambda: -1)  # -1 indicates the car has not been seen yet
currentFrame = 0

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

previousLightStates = defaultdict(lambda: "Off")  # Default to "Off" for all lights
lightGreenFrame = defaultdict(lambda: 0)  # Tracks the frame when the light turned green for each traffic light
carsInFirstFrame = set()
carStartTimes = defaultdict(lambda: -1)



def processing_thread(frameQueue, processedQueue, model, tracker):
    global stopThreads,currentFrame,isFirstFrame,carsInFirstFrame,clickedPoints,carsGroupedByArr,roadLineSegments
    global trackIdBoolArray,rightClickedPoints,lightLineSegments,thirdClickedPoints,firstFrame, carsHasCrossedLight
    global lightsModel,fileLights,classNames,classNamesLights,CAR_LENGTH,carPositions,carSpeeds,lastSeenFrame,selectedOption
    global previousLightStates, lightGreenFrame
    global idVideo
    global listOfIdTrafficLanes
    global allCarsId
    global carStartTimes,distancesBetweenCars
    global roiStart,roiEnd

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
                if ifRoi == True:
                    if roiStart[0]>roiEnd[0]:   # Change order if necessary
                        help=roiStart
                        roiStart=roiEnd
                        roiEnd=help
                    if (roiStart[0] <= x1 <= roiEnd[0] and roiStart[0] <= x2 <= roiEnd[0]
                    and roiStart[1] >= y1 >= roiEnd[1] and roiStart[1] >= y2 >= roiEnd[1]):
                        w, h = x2 - x1, y2 - y1
                        conf = math.ceil((box.conf[0] * 100)) / 100
                        cls = int(box.cls[0])
                        if classNames[cls] == "car":
                            detections = np.vstack((detections, [x1, y1, x2, y2, conf]))
                else:
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
                    if (x1 < x < x1 + w) and (y1 < y < y1 + h):
                        # Update the idToColorLight dictionary with the current state
                        if classNamesLights[cls] == "Traffic Light -Red-":
                            idToColorLight[i] = "red"
                        elif classNamesLights[cls] == "Traffic Light -Green-":
                            idToColorLight[i] = "green"
                        else:
                            idToColorLight[i] = "off"

                        # Detect transitions by comparing the current state with the previous state
                        if idToColorLight[i] != previousLightStates[i]:
                            if previousLightStates[i] == "red" and idToColorLight[i] == "green":
                                # Log the transition from red to green
                                lightGreenFrame[i] = currentFrame
                                print(f"Traffic light {i} turned green at frame {currentFrame}")

                            # Update the previous state
                            previousLightStates[i] = idToColorLight[i]

                cvzone.cornerRect(frame, (x1, y1, w, h))
            cvzone.putTextRect(frame, f'Are the lights red? {idToColorLight[0]}', (50, 50), scale=2, thickness=2, offset=1,
                               colorR="")

        for rt in resultsTracker:
            x1, y1, x2, y2, id = map(int, rt)
            w, h = x2 - x1, y2 - y1
            cx, cy = x1 + w // 2, y1 + h // 2
            color = (0, 255, 0) if any(id == car[0] for group in carsGroupedByArr for car in group) else (255, 0, 255)
            cvzone.cornerRect(frame, (x1, y1, w, h), l=9, rt=2, colorR=color)
            cvzone.putTextRect(frame, f'{id}', (max(0, x1), max(35, y1)), scale=2, thickness=2, offset=1, colorR="")


            carCenters[id] = ((cx, cy), w)

            if id >= len(trackIdBoolArray):
                trackIdBoolArray.extend([False] * (id + 1 - len(trackIdBoolArray)))


            if not trackIdBoolArray[id]:
                trackIdBoolArray, carsGroupedByArr, allCarsId = group_cars_by_roadLine(id, cx, cy, roadLineSegments,
                                                                            trackIdBoolArray, carsGroupedByArr, allCarsId)

            if not trackIdBoolArray[id] and id not in allCarsId:
                allCarsId.add(id)

            check_for_break_in_detection(lastSeenFrame, id, currentFrame, carPositions,
                                         cx, cy, carSpeeds, w, CAR_LENGTH, frame, x1, y1)

            # Zaktualizuj ostatnio widzianą klatke i historie pozycji dla następnej klatki
            lastSeenFrame[id] = currentFrame
            carPositions[id].append((cx, cy))
            if len(carPositions[id]) > 2:
                carPositions[id].pop(0)

            if currentFrame == 1:  # First frame processing
                carsInFirstFrame.add(id)  # Add the car ID to the set

            calculate_reaction_time(id, cx, cy, carPositions, carsGroupedByArr, currentFrame,lightGreenFrame,carsInFirstFrame,carStartTimes)

            #what happens after someone runsa a red light (photo + log info)
            if check_if_enter_light_line(cx, cy, id, lightLineSegments, idToColorLight, carsHasCrossedLight):
                fileLights.write(f'{id} run through a red light? {carsHasCrossedLight.get(id)}\n')
                print(f"{id} przejechało na RED?? {carsHasCrossedLight.get(id)}")

                cv2.rectangle(frame, (x1, y1), (x1 + w, y1 + h), (0, 0, 255), 4)

                outputFolder= './ImagesRed'
                os.makedirs(outputFolder, exist_ok=True)
                cv2.imwrite(f'{outputFolder}/{id}RED.jpg', frame)

            # Save car to DB
            if id in lastSeenFrame and currentFrame - lastSeenFrame[id] > 5:  # Example timeout for being "lost"
                pass


        draw_segment_lines(frame, roadLineSegments)
        draw_light_lines(frame, lightLineSegments, idToColorLight)
        draw_light_circle(frame, thirdClickedPoints)
        draw_lines_between_cars(frame, carCenters, carsGroupedByArr, CAR_LENGTH,distancesBetweenCars,currentFrame)
        cv2.rectangle(frame, roiStart, roiEnd, color=(255, 0, 0), thickness=2)

        # Add processed frame to the processed queue
        if not processedQueue.full():
            processedQueue.put(frame)  # Pass timestamp along
            #print(currentFrame)

#DIALOG WINDOW FOR INPUT DATA
def get_basic_info():
    root = tk.Tk()
    root.withdraw()

    crossroad_name = simpledialog.askstring("Informacje o skrzyżowaniu", "Podaj nazwę skrzyżowania:")
    city_name = simpledialog.askstring("Informacje o skrzyżowaniu", "Podaj miasto:")

    return crossroad_name, city_name

resultLoadData = False

def ask_if_load_data():
    global resultLoadData
    root = tk.Tk()
    root.withdraw()

    resultLoadData = messagebox.askyesno("Wczytanie danych", "Czy załadować linie z bazy?")

    return resultLoadData

#IMPORTANT FOR DATABASE INSERTIONS (FOREIGN KEYS!)
idNameOfPlace = None
idVideo = None
listOfIdTrafficLanes = [] #Lista id TrafficLanes dla kolejnych pasów w roadLineSegments, jeżeli w roadLineSegment pas jest pod indexem 0 to jego id będzie w listOfIdTrafficLanes pod indeksem 0 itp.
listOfSginalLights = [] #for saved points of signal lights in db
listOfTrafficLanes = [] #for saved points of traffic lanes in db

def main():
    global stopThreads, startProcessing, firstFrame
    global clickedPoints
    global rightClickedPoints, thirdClickedPoints
    global idNameOfPlace
    global idVideo
    global listOfIdTrafficLanes
    global allCarsId,carStartTimes,carSpeeds
    global listOfSginalLights
    global listOfTrafficLanes
    global resultLoadData
    global roadLineSegments, carsGroupedByArr, isFirstFrame

    crossroad_name, city_name = get_basic_info()
    print(f"Skrzyżowanie: {crossroad_name}")
    print(f"Miasto: {city_name}")

    resultLoadData = ask_if_load_data()

    if resultLoadData:
        listOfSginalLights = get_signallights(crossroad_name, city_name)
        if listOfSginalLights:
            for signalLight in listOfSginalLights:
                rightClickedPoints.append((signalLight[1], signalLight[2])) #start point of light line
                rightClickedPoints.append((signalLight[3], signalLight[4])) #end point of light line
                thirdClickedPoints.append((signalLight[5], signalLight[6])) #point of signal light
                print(rightClickedPoints)
                print(thirdClickedPoints)
                print(f"ID: {signalLight[0]}, StopLineStartX: {signalLight[1]}, StopLineStartY: {signalLight[2]}, StopLineEndX: {signalLight[3]}, StopLineEndY: {signalLight[4]}, SignalX: {signalLight[5]}, SignalY: {signalLight[6]}")

        listOfTrafficLanes = get_trafficlanes(crossroad_name, city_name)
        if listOfTrafficLanes:
            for trafficlane in listOfTrafficLanes:
                clickedPoints.append((trafficlane[1], trafficlane[2])) #start point of traffic lane
                clickedPoints.append((trafficlane[3], trafficlane[4])) #end point of traffic lane
                listOfIdTrafficLanes.append(trafficlane[0]) #we need to create listOfIdTrafficLanes, because it is important during inserting cars; if we create new dataset for intersection, this list is created later during `listOfIdTrafficLanes = insert_trafficLanes(clickedPoints, idNameOfPlace)` => lastRowid from db
                print(clickedPoints)
                print(f"ID: {trafficlane[0]}, TrafficLanesStartX: {trafficlane[1]}, TrafficLanesStartY: {trafficlane[2]}, TrafficLanesEndX: {trafficlane[3]}, TrafficLanesEndY: {trafficlane[4]}")


    #Getting all data from table nameofplace
    intersections = get_nameOfPlace()

    isPlaceNew = True

    if intersections:
        for intersection in intersections:
            print(f"ID: {intersection[0]}, Name: {intersection[1]}, City: {intersection[2]}")
            if intersection[1]==crossroad_name and intersection[2]==city_name:
                isPlaceNew = False
                idNameOfPlace = intersection[0]
    else:
        print("No data found.")

    if isPlaceNew:
        # Inserting data to nameofplace
        insert_nameOfPlace(crossroad_name, city_name)
        intersections = get_nameOfPlace()
        idNameOfPlace = intersections[-1][0]

    print(f"Id (nameOfPlace): {idNameOfPlace}, Name: {crossroad_name}, City: {city_name}")

    idVideo = insert_video(idNameOfPlace, videoPath, datetime.now())

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

    load_saved_data()

    # cv2.imshow musza pracowac na tym samym wątku (w tym przypadku MainThread)
    while not stopThreads:
        if not startProcessing:  # In drawing mode
            cv2.imshow("Traffic Tracking", firstFrame)
            drawInterface(firstFrame,selectedOption)
            key = cv2.waitKey(1)
            if key == ord('d'):  # Start processing when 'd' is pressed
                startProcessing = True
                if not resultLoadData:
                    #Deleting all stored data about intersection
                    delete_trafficLanes_cascade(idNameOfPlace)

                    #Inserting new data about intersection
                    listOfIdTrafficLanes = insert_trafficLanes(clickedPoints, idNameOfPlace)
                    insert_signalLights(rightClickedPoints, thirdClickedPoints, idNameOfPlace)

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

    print(listOfIdTrafficLanes)

    insert_carGrouped(idVideo, carsGroupedByArr, listOfIdTrafficLanes,carStartTimes)
    insert_carNotGrouped(idVideo, allCarsId)
    insert_speedsOfCars(idVideo,carSpeeds)
    insert_distancesBetweenCars(idVideo,distancesBetweenCars)

    for carId in allCarsId:
        print(f"{carId}")

    fileLights.close()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

