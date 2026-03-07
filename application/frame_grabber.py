from PySide6.QtCore import QTimer, Signal, QObject, Slot
import cv2


class FrameGrabber(QObject):
    started: Signal
    stopped: Signal
    frame_ready: Signal
    _running: bool
    
    def __init__(self):
        super().__init__()
        self.started = Signal()
        self.stopped = Signal()
        self.frame_ready = Signal(object)
        
        self._running: bool = False
        
        self._timer = QTimer()
        self._timer.timeout.connect(self.acquire)
        
    
    def start(self):
        self._timer.start(30)

    def stop(self):
        self._timer.stop()
    
    @Slot()
    def acquire(self):
        print("FRAME GET")
        self.frame_ready.emit("FRAME")