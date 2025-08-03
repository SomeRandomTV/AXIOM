# detection/person_.py

from ultralytics import YOLO
import cv2

class PersonDetector:
    def __init__(self, model_name="yolov8n.pt", confidence_threshold=0.3):
        """
        Initialize the person detector.
        :param model_name: YOLO model name
        :param confidence_threshold: human confidence threshold
        """
        self.model = YOLO(model_name)
        self.conf_thresh = confidence_threshold

    def detect(self, frame) -> object:
        """
        Detect people in the frame
        :param frame: current frame
        :return: written frame with person in bounding box
        """
        if frame is None:
            return None

        # ensure frame is contiguous for OpenCV if it's not already
        if not frame.flags['CONTIGUOUS']:
            frame = frame.copy()

        results = self.model.predict(frame, conf=self.conf_thresh, classes=[0], verbose=False)[0]
        frame = self._draw_boxes(frame, results)
        return frame

    @staticmethod
    def _draw_boxes(frame, results) -> object:
        """
        Draws bounding boxes around the results(people)
        :param frame: current frame
        :param results: human detection results
        :return: current frame with bounding boxes
        """
        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            label = f"Person {conf:.2f}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return frame



