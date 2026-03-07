from PySide6.QtCore import QTimer, Signal, QObject, Slot
import cv2


class FrameProcessor(QObject):
    started: Signal
    stopped: Signal
    result_ready: Signal
    _running: bool
    def __init__(self):
        super().__init__()
        self.started = Signal()
        self.stopped = Signal()
        self.result_ready = Signal(object)

        self._running: bool = False
        
    
    def start(self):
        ...

    def stop(self):
        ...
    
    @Slot(object)
    def process(self, frame):
        print(f"result : {frame} ")
        self.result_ready.emit("42")