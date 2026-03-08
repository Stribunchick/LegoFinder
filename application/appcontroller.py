from ast import main

from PySide6.QtCore import QObject, QThread, Slot
from application.frame_display import FrameDisplay
from application.frame_grabber import FrameGrabber
from application.frame_processor import FrameProcessor
from application.thread_manager import ThreadManager
# from main_window import MainWindow

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

    def __init__(self, main_window):
        super().__init__()
        self.thread_manager = ThreadManager()
        self.main_window = main_window
        self._create_workers()
        self._create_connections()


    def _create_workers(self):
        self.frame_grabber, self.frame_grabber_thread = create_worker(FrameGrabber(), "FrameGrabberThread")
        self.thread_manager.register(self.frame_grabber_thread)
        self.frame_processor, self.frame_processor_thread = create_worker(FrameProcessor(), "FrameProcessorThread")
        self.thread_manager.register(self.frame_processor_thread)

    def _create_connections(self):
        # grabber -> processor
        self.frame_grabber.frame_ready.connect(self.frame_processor.process)

        self.frame_processor.result_ready.connect(self.main_window._update_frame)
        
    def _disconnect_frame_grabber(self):
        self.frame_grabber.frame_ready.disconnect()

    def _connect_main_pipeline(self):
        self._disconnect_frame_grabber()

        self.frame_grabber.frame_ready.connect(self.frame_processor.process)

    def switch_to_add_part(self, display: FrameDisplay):
        self._disconnect_frame_grabber()
        self.frame_grabber.frame_ready.connect(display.update_frames)

    def switch_to_main(self):
        self._connect_main_pipeline()

    def start_pipeline(self):
        self.frame_grabber.start()

    def stop_pipeline(self):
        self.frame_grabber.stop()

