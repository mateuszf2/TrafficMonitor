import cv2


isLightEntered= False
def calculate_light_lines(lightLineSegments,rightClickedPoints,isFirstFrame,firstFrame,idToColorLight):
    lightLineSegments = []  # ZAPOMNIELIŚMY O CZYSZCZENIU TABLICY I DO STARTEJ TABLICY DODAWALIŚMY STARE WARTOŚCI PLUS NOWE I TAK CAŁY CZAS(CIĄG FIBONACIEGO SIĘ ZROBIŁ CZY COŚ XD)
    for i in range(0, len(rightClickedPoints), 2):
        if i+1 < len(rightClickedPoints):
            if rightClickedPoints[i][0] > rightClickedPoints[i+1][0]:
                help= rightClickedPoints[i]
                rightClickedPoints[i] = rightClickedPoints[i+1]
                rightClickedPoints[i+1] = help

            p1, p2 = rightClickedPoints[i], rightClickedPoints[i+1]
            if p1[0] != p2[0]:  # Unikaj dzielenia przez zero
                a = (p2[1] - p1[1]) / (p2[0] - p1[0])
                b = p1[1] - a * p1[0]
                lightLineSegments.append((a, b, p1, p2))
                if isFirstFrame:
                    # Aby wyświetlić linie na pierwszej, zatrzymanej klatce
                    draw_light_lines(firstFrame,lightLineSegments,idToColorLight)
                    cv2.imshow("Traffic Tracking", firstFrame)
    return lightLineSegments
# Linie do sygnalizacji świetlnej, umożliwiające wykrycie, czy samochód łamie prawo
def draw_light_lines(frame,lightLineSegments,idToColorLight):
    global isLightEntered
    for i, (a, b, p1, p2) in enumerate(lightLineSegments):
        color = (0, 255, 0) if idToColorLight[i]=="green" else (0, 0, 255) if idToColorLight[i]=="red" else (0, 0, 0)
        cv2.line(frame, p1, p2, color, 2)
        middle = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
        cv2.putText(frame, f"numer: {i}", middle, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

def check_if_enter_light_line(cx, cy, id,lightLineSegments, idToColorLight, carsHasCrossedLight):
    #carsHasCrossedLight.get(id, False) sprawdza czy w danym id jest True,
    # Jeśli nie byłoby w słowniku klucza o danym id to nie będzie błędu bo wtedy przyjmujemy domyślnie False dla takiego id
    if carsHasCrossedLight.get(id, False):
        return False
    for i, (a, b, p1, p2) in enumerate(lightLineSegments):
        # Sprawdza, czy punkt (cx, cy) jest blisko odcinka
        if abs(cy - (a * cx + b)) < 20 and p1[0] - 10 <= cx <= p2[0] + 10:
            #global isLightEntered
            #isLightEntered = True
            if idToColorLight[i] == "red":
                carsHasCrossedLight[id] = True
                return True
    return False
def draw_light_circle(frame, thirdClickedPoints):
    for i, (x, y) in enumerate(thirdClickedPoints):
        cv2.circle(frame, (x, y), 6, (255, 0, 255), -1)
        cv2.putText(frame, f"numer: {i}", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)