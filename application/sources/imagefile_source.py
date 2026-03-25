import cv2
import numpy as np


class ImageFileSource:
    fps: int

    def __init__(self, path: str):
        """Сохранить путь к изображению, используемому как статический источник."""
        self.path = path
        self.frame = None

    def open(self) -> None:
        """Загрузить изображение с диска в память."""
        self.frame = cv2.imread(self.path)

    def read(self) -> np.ndarray | None:
        """Вернуть сохранённый в памяти кадр изображения."""
        return self.frame

    def close(self) -> None:
        """Закрыть источник без дополнительной очистки."""
        pass
