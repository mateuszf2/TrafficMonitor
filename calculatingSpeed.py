import math
import cv2
from collections import defaultdict


# Ustaw liczbę klatek na sekundę (zakładając 30 FPS))
FPS = 30
TIME_BETWEEN_FRAMES = 1 / FPS  # Czas między klatkami w sekundach

FRAME_GAP_THRESHOLD = 10 # Liczba klatek, po których powinna zostać zresetowana historia prędkości

# Zdefiniuj słownik do przechowywania ostatnich prędkości dla każdego samochodu, aby wygładzić wyniki
speedHistory = defaultdict(list)
WINDOW_SIZE = 30  # Liczba klatek do uśrednienia
def calculate_speed(distancePixels, pxToOneMeter):
    # Konwertuj piksele na metry
    distanceMeters = distancePixels / pxToOneMeter
    # Oblicz prędkość w metrach na sekundę
    speedMps = distanceMeters / TIME_BETWEEN_FRAMES
    # Konwertuj prędkość na km/h
    speedKph = speedMps * 3.6
    return speedKph

def moving_average(speeds):
    return sum(speeds) / len(speeds) if speeds else 0

def check_for_break_in_detection(lastSeenFrame,id,currentFrame,carPositions,
                             cx,cy,carSpeeds,w,CAR_LENGTH,frame,x1,y1):
    # Sprawdź przerwę w wykrywaniu (okluzja lub ponowne pojawienie się)
    if lastSeenFrame[id] == -1 or (currentFrame - lastSeenFrame[id] > FRAME_GAP_THRESHOLD):
        # Zresetuj historię prędkości, jeśli samochód był niewidoczny przez zbyt wiele klatek
        speedHistory[id] = []  # Wyczyść historię prędkości, aby uniknąć skoku
        carPositions[id] = [(cx, cy)]  # Zresetuj historię pozycji
    else:
        # Obliczenie normalnej prędkości, jeśli wykrywanie jest spójne
        if len(carPositions[id]) > 0:
            prevX, prevY = carPositions[id][-1]
            distancePixels = math.sqrt((cx - prevX) ** 2 + (cy - prevY) ** 2)
            pxToOneMeter = w / CAR_LENGTH
            speedKph = calculate_speed(distancePixels, pxToOneMeter)

            # Zaktualizuj historię prędkości i oblicz wygładzoną prędkość
            speedHistory[id].append(speedKph)
            if len(speedHistory[id]) > WINDOW_SIZE:
                speedHistory[id].pop(0)

            smoothedSpeedKph = moving_average(speedHistory[id])

            # Wyświetl wygładzoną prędkość na klatce
            speedText = f"{smoothedSpeedKph:.2f} km/h"
            cv2.putText(frame, speedText, (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

            # To database adding
            if currentFrame%30==0:
                carSpeeds[id].append(smoothedSpeedKph)

