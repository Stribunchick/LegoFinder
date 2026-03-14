from PySide6.QtCore import QTimer, Signal, QObject, Slot
import cv2

# from lego_detector import LegoDetector

from pipeline import Pipeline

class FrameProcessor(QObject):
    started = Signal()
    stopped = Signal()
    result_ready = Signal(object)
    conf_thres: float
    _running: bool
    def __init__(self):
        super().__init__()
        self._running: bool = False
        self.desired_part = None
        self.pipeline = Pipeline()
    
    @Slot(object)
    def process(self, frame):
        """
        Do stuff and drawing here
        """
        # img = self.detector.detect_and_draw(frame, self.desired_part)
        img = self.pipeline.process(frame)
        self.result_ready.emit(img)


    @Slot(float)
    def update_conf_thres(self, value):
        self.conf_thres = value / 100
    
    def update_detected_detail(self, detail):
        self.desired_part = detail

if __name__ == "__main__":
    ...