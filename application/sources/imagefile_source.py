import cv2
import numpy as np

class ImageFileSource:

    def __init__(self, path: str):
        self.path = path
        self.frame = None

    def open(self) -> None:
        self.frame = cv2.imread(self.path)

    def read(self) -> np.ndarray | None:
        return self.frame

    def close(self) -> None:
        pass

    