import cv2
import numpy as np

class VideoFileSource:

    def __init__(self, path: str):
        self.path = path
        self.cap = None

    def open(self):
        self.cap = cv2.VideoCapture(self.path)

    def read(self) -> np.ndarray | None:
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame
    
    def close(self):
        if self.cap:
            self.cap.release()