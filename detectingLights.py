import cv2

def calculate_light_lines(lightLineSegments,rightClickedPoints,isFirstFrame,firstFrame,roadLineSegments):
    for i in range(0, len(rightClickedPoints), 2):
        if i+1 < len(rightClickedPoints):
            p1, p2 = rightClickedPoints[i], rightClickedPoints[i+1]
            if p1[0] != p2[0]:  # Unikaj dzielenia przez zero
                a = (p2[1] - p1[1]) / (p2[0] - p1[0])
                b = p1[1] - a * p1[0]
                lightLineSegments.append((a, b, p1, p2))
                if isFirstFrame:
                    # Aby wyświetlić linie na pierwszej, zatrzymanej klatce
                    draw_light_lines(firstFrame,roadLineSegments)
                    cv2.imshow("Traffic Tracking", firstFrame)
    return lightLineSegments
# Linie do sygnalizacji świetlnej, umożliwiające wykrycie, czy samochód łamie prawo
def draw_light_lines(frame,lightLineSegments):
    global isLightEntered
    for (a, b, p1, p2) in lightLineSegments:
        color = (255, 0, 0) if not isLightEntered else (0, 0, 255)
        cv2.line(frame, p1, p2, color, 2)

isLightEntered= False
carsHasCrossedLight = {}
def check_if_enter_light_line(cx, cy, id,lightLineSegments):
    global carsHasCrossedLight
    #carsHasCrossedLight.get(id, False) sprawdza czy w danym id jest True,
    # Jeśli nie byłoby w słowniku klucza o danym id to nie będzie błędu bo wtedy przyjmujemy domyślnie False dla takiego id
    if carsHasCrossedLight.get(id, False):
        return False
    for a, b, p1, p2 in lightLineSegments:
        # Sprawdza, czy punkt (cx, cy) jest blisko odcinka
        if abs(cy - (a * cx + b)) < 10 and p1[0] <= cx <= p2[0]:
            global isLightEntered
            isLightEntered = True
            carsHasCrossedLight[id] = True
            return True
    return False