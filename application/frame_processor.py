from PySide6.QtCore import QTimer, Signal, QObject, Slot
import cv2

class FrameProcessor(QObject):
    started = Signal()
    stopped = Signal()
    result_ready = Signal(object)
    _running: bool
    def __init__(self):
        super().__init__()
        self._running: bool = False
    
    @Slot(object)
    def process(self, frame):
        """
        Do stuff and drawing here
        """

        self.result_ready.emit(frame)