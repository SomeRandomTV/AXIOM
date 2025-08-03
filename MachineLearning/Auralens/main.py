# main.py

import cv2
from detection.person import PersonDetector

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise IOError("Cannot open webcam")

detector = PersonDetector()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = detector.detect(frame)

    cv2.imshow('Person Detection', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
