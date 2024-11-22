import cv2
import math

def draw_lines_between_cars(frame, carCenters,carsGroupedByArr,CAR_LENGTH):
    # Rysuje linie między samochodami, jeśli oba auta należą do tej samej grupy
    for group in carsGroupedByArr:
        for i in range(len(group) - 1):
            id1, id2 = group[i], group[i + 1]
            if id1 in carCenters and id2 in carCenters:
                (cx1, cy1), w1 = carCenters[id1]
                (cx2, cy2), w2 = carCenters[id2]
                # Obliczanie odległości między samochodami
                distance = math.sqrt((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2)
                #print(f"Odległość między samochodami {id1} a {id2}: {distance:.2f} pikseli")

                # Najpierw uśredniamy szerokość prostokąta auta, czyli jego długość w pixelach
                avgWidthCar = (w1 + w2) / 2
                # Następnie przeliczamy ile jeden metr ma pixeli
                pxToOneMeter = avgWidthCar / CAR_LENGTH

                # Rysowanie linii między samochodami
                cv2.line(frame, (cx1, cy1), (cx2, cy2), (255, 255, 255), 2)

                # Obliczanie punktu, w którym umieścimy tekst (pośrodku linii)
                midX = int((cx1 + cx2) / 2)
                midY = int((cy1 + cy2) / 2)

                text = f"{distance/pxToOneMeter:.2f} m"
                font = cv2.FONT_HERSHEY_SIMPLEX
                fontScale = 0.5
                fontThickness = 1
                textSize = cv2.getTextSize(text, font, fontScale, fontThickness)[0]
                textX = midX - textSize[0] // 2  # Wyśrodkowanie tekstu
                textY = midY - 10  # Ustawienie tekstu trochę nad linią


                cv2.putText(frame, text, (textX, textY), font, fontScale, (255, 255, 255), fontThickness)
