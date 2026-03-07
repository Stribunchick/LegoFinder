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
        
    
    def start(self):
        ...

    def stop(self):
        ...
    
    @Slot(object)
    def process(self, frame):
        print("FRAME PROCESSOR SEND FRAME")
        self.result_ready.emit(frame)