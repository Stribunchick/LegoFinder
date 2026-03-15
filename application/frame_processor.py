from PySide6.QtCore import QTimer, Signal, QObject, Slot
import cv2

# from lego_detector import LegoDetector

from cv_pipeline.pipeline import Pipeline

class FrameProcessor(QObject):
    started = Signal()
    stopped = Signal()
    result_ready = Signal(object)
    conf_thres: float
    _running: bool
    def __init__(self, folder):
        super().__init__()
        self.folder = folder
        self._running: bool = False
        self.desired_part = None
        self.pipeline = Pipeline(self.folder)
    
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
        self.pipeline.comparator.set_conf_thres(self.conf_thres)
    

if __name__ == "__main__":
    ...