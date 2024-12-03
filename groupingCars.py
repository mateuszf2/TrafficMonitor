import cv2

def calculate_segment_line_equations(roadLineSegments,carsGroupedByArr,clickedPoints,isFirstFrame,firstFrame):
    for i in range(0, len(clickedPoints), 2):
        if i+1 < len(clickedPoints):
            # Obojetnie z ktorej strony zaznaczamy pas
            if clickedPoints[i][0]>clickedPoints[i+1][0]:
                help=clickedPoints[i]
                clickedPoints[i]=clickedPoints[i+1]
                clickedPoints[i + 1]=help

            p1, p2 = clickedPoints[i], clickedPoints[i+1]
            if p1[0] != p2[0]:  # Unikaj dzielenia przez zero
                a = (p2[1] - p1[1]) / (p2[0] - p1[0])
                b = p1[1] - a * p1[0]
                roadLineSegments.append((a, b, p1, p2))
                carsGroupedByArr.append([])  # Dodaj pustą listę dla każdego segmentu
                if isFirstFrame:
                    # Aby wyświetlić linie na pierwszej, zatrzymanej klatce
                    draw_segment_lines(firstFrame,roadLineSegments)
                    cv2.imshow("Traffic Tracking", firstFrame)
    return roadLineSegments,carsGroupedByArr

def draw_segment_lines(frame,roadLineSegments):
    # Rysowanie odcinków między klikniętymi punktami na klatce
    for a, b, p1, p2 in roadLineSegments:
        cv2.line(frame, p1, p2, (0, 255, 0), 2)  # Zielona linia

def group_cars_by_roadLine(trackId, cx, cy,roadLineSegments,trackIdBoolArray,carsGroupedByArr):
    # Grupuje auta według najbliższego pasa ruchu
    for i, (a, b, p1, p2) in enumerate(roadLineSegments):
        # Sprawdza, czy punkt (cx, cy) jest blisko odcinka
        if abs(cy - (a * cx + b)) < 10 and p1[0] - 10 <= cx <= p2[0] + 10:
            trackIdBoolArray[trackId] = True
            carsGroupedByArr[i].append(trackId)
            break
    return trackIdBoolArray,carsGroupedByArr