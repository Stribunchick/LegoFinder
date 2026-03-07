from PySide6.QtCore import QObject, QThread
from application.frame_grabber import FrameGrabber
from application.frame_processor import FrameProcessor
from application.thread_manager import ThreadManager


def create_worker(worker, thread_name: str) -> tuple:
    thread = QThread()
    thread.setObjectName(thread_name)
    thread.started.connect(lambda : print(f"thread {thread_name} started"))
    worker.moveToThread(thread)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(lambda : print(f"thread {thread_name} finished"))
    thread.start()
    return worker, thread



class AppController(QObject):

    frame_grabber: FrameGrabber
    frame_processor: FrameProcessor

    def __init__(self):
        super().__init__()
        self.thread_manager = ThreadManager()
        self._create_workers()
       


    def _create_workers(self):
        self.frame_grabber, self.frame_grabber_thread = create_worker(FrameGrabber(), "FrameGrabberThread")
        self.thread_manager.register(self.frame_grabber_thread)
        self.frame_processor, self.frame_processor_thread = create_worker(FrameProcessor(), "FrameProcessorThread")
        self.thread_manager.register(self.frame_processor_thread)

    def start_pipeline(self):
        ...

    def stop_pipeline(self):
        ...