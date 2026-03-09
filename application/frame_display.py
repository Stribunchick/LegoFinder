from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPainter, QPixmap, QColor
import cv2
import numpy as np

class FrameDisplay(QLabel):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(640, 480)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._last_frame = None

        self._last_pixmap = None

        self._bg_color = QColor(0, 0, 0)
    
    @Slot(object)
    def update_frames(self, frame: np.ndarray):
        self._last_frame = frame.copy()

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape

        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)

        self._last_pixmap = QPixmap.fromImage(qimg)

        self._update_pixmap()

    def _update_pixmap(self):
        if self._last_pixmap is None:
            return
        
        scaled = self._last_pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        final_pixmap = QPixmap(self.size())
        final_pixmap.fill(self._bg_color)

        painter = QPainter(final_pixmap)
        x = (self.width() - scaled.width())
        y = (self.height() - scaled.height())
        painter.drawPixmap(x, y, scaled)
        painter.end()
        self.setPixmap(final_pixmap)

    def set_bg_color(self, color):
        self._bg_color = color
        self._update_pixmap()

    def copy_frame(self):
        frame = self._last_frame.copy()
        
        return frame

       