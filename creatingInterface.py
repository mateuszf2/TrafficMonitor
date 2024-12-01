import cv2
def drawInterface(frame,selectedOption):
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
