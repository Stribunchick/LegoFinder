import cv2
import numpy as np


class CameraSource:
    fps: int

    def __init__(self, camera_id=0):
        """Сохранить идентификатор камеры для захвата."""
        self.camera_id = camera_id
        self.cap = None

    def open(self) -> None:
        """Открыть поток с веб-камеры."""
        self.cap = cv2.VideoCapture(self.camera_id)

    def read(self) -> np.ndarray | None:
        """Считать и вернуть следующий кадр с веб-камеры."""
        if self.cap is None:
            return None

        ret, frame = self.cap.read()

        if not ret:
            return None

        return frame

    def close(self) -> None:
        """Освободить объект захвата веб-камеры."""
        if self.cap:
            self.cap.release()
