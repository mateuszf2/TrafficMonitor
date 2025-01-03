import cv2
import math

def draw_lines_between_cars(frame, carCenters, carsGroupedByArr, CAR_LENGTH,distancesBetweenCars,currentFrame):
    # Reset the processedPairs set for each frame
    processedPairs = set()

    # Rysuje linie tylko do samochodu znajdującego się bezpośrednio przed każdym autem
    for group in carsGroupedByArr:
        for i in range(len(group)):
            id1 = group[i][0]
            if id1 not in carCenters:
                continue

            (cx1, cy1), w1 = carCenters[id1]
            closest_car_id = None
            closest_distance = float('inf')

            # Find the closest car in front of the current car
            for j in range(len(group)):
                id2 = group[j][0]
                if id2 == id1 or id2 not in carCenters:
                    continue

                (cx2, cy2), w2 = carCenters[id2]

                # Only consider cars that are in front (larger y value for cy2)
                if cy2 > cy1:
                    distance = math.sqrt((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2)
                    if distance < closest_distance:
                        closest_distance = distance
                        closest_car_id = id2

            if closest_car_id:
                (cx2, cy2), w2 = carCenters[closest_car_id]

                # Ensure the pair is processed in a consistent order
                car_pair = tuple(sorted([id1, closest_car_id]))
                if car_pair in processedPairs:
                    continue  # Skip if the pair is already processed
                else:
                    processedPairs.add(car_pair)

                    # Najpierw uśredniamy szerokość prostokąta auta, czyli jego długość w pixelach
                    avgWidthCar = (w1 + w2) / 2
                    # Następnie przeliczamy ile jeden metr ma pixeli
                    pxToOneMeter = avgWidthCar / CAR_LENGTH

                    # Rysowanie linii między samochodami
                    cv2.line(frame, (cx1, cy1), (cx2, cy2), (255, 255, 255), 2)

                    # Obliczanie punktu, w którym umieścimy tekst (pośrodku linii)
                    midX = int((cx1 + cx2) / 2)
                    midY = int((cy1 + cy2) / 2)

                    distance=closest_distance / pxToOneMeter
                    text = f"{distance:.2f} m"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    fontScale = 0.5
                    fontThickness = 1
                    textSize = cv2.getTextSize(text, font, fontScale, fontThickness)[0]
                    textX = midX - textSize[0] // 2  # Wyśrodkowanie tekstu
                    textY = midY - 10  # Ustawienie tekstu trochę nad linią

                    cv2.putText(frame, text, (textX, textY), font, fontScale, (255, 255, 255), fontThickness)

                    if currentFrame%30==0:
                        distancesBetweenCars[(id1,closest_car_id)].append(distance)
