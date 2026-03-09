import cv2
import numpy as np
from application.source import Source

class CameraSource:

    fps: int

    def __init__(self, camera_id = 0):
        self.camera_id = camera_id
        self.cap = None

    def open(self) -> None:
        self.cap = cv2.VideoCapture(self.camera_id)

    def read(self) -> np.ndarray | None:
        if self.cap is None:
            return None
        
        ret, frame = self.cap.read()

        if not ret:
            return None
        
        return frame
    
    def close(self) -> None:
        if self.cap:
            self.cap.release()

# camera = CameraSource()
# if isinstance(camera, Source):
#     print("Is Source")