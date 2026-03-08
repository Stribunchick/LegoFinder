from PySide6.QtCore import QTimer, Signal, QObject, Slot
import cv2
import numpy as np

class FrameGrabber(QObject):
    started: Signal
    stopped: Signal
    frame_ready = Signal(object)
    _running: bool
    
    def __init__(self):
        super().__init__()
        self.started = Signal()
        self.stopped = Signal()
        self.source = None
        self._running: bool = False
        
        self._timer = QTimer()
        self._timer.timeout.connect(self.acquire)
    
    def set_source(self, source):
        if self.source is not None:
            self.source.close()
        self.source = source
        self.source.open()
    
    def start(self):
        self._timer.start(30)
        

    def stop(self):
        self._timer.stop()
    
    @Slot()
    def acquire(self):
        # print("FRAME_GRABBER SEND FRAME")
        # self.frame_ready.emit(np.random.randint(0, 255, (480, 640), dtype=np.uint8))
        frame = self.source.read()
        if frame is None:
            return
        self.frame_ready.emit(frame)