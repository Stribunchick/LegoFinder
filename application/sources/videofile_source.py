import cv2
import numpy as np


class VideoFileSource:
    fps: int

    def __init__(self, path: str):
        """Сохранить путь к видеофайлу-источнику."""
        self.path = path
        self.cap = None

    def open(self) -> None:
        """Открыть видеофайл для покадрового чтения."""
        self.cap = cv2.VideoCapture(self.path)

    def read(self) -> np.ndarray | None:
        """Считать и вернуть следующий кадр из файла."""
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def close(self) -> None:
        """Освободить объект захвата видео."""
        if self.cap:
            self.cap.release()
