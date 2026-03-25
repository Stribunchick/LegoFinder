# -*- coding: utf-8 -*-
import os

from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt
from application.frame_display import FrameDisplay
from application.frame_grabber import FrameGrabber
from application.frame_processor import FrameProcessor
from application.thread_manager import ThreadManager


def create_worker(worker, thread_name: str) -> tuple:
    """Переместить рабочий объект в отдельный поток и запустить его."""
    thread = QThread()
    thread.setObjectName(thread_name)
    thread.started.connect(lambda: print(f"thread {thread_name} started"))
    worker.moveToThread(thread)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(lambda: print(f"thread {thread_name} finished"))
    thread.start()
    return worker, thread


class AppController(QObject):
    frame_grabber: FrameGrabber
    frame_processor: FrameProcessor

    set_conf_thres = Signal(int)
    start_grabber_requested = Signal()
    stop_grabber_requested = Signal()
    close_grabber_requested = Signal()
    set_source_requested = Signal(object)
    switch_reference_requested = Signal(str)

    def __init__(self, main_window, folder="./data/robust_templates"):
        """Создать рабочие объекты и связать сигналы приложения."""
        super().__init__()
        self.folder = folder
        self.thread_manager = ThreadManager()
        self.main_window = main_window
        self._create_workers()
        self._create_connections()

    @Slot()
    def _create_workers(self):
        """Создать рабочий объект для захвата кадров и рабочий объект для обработки."""
        ref_folder = os.path.join(self.folder)
        self.frame_grabber, self.frame_grabber_thread = create_worker(FrameGrabber(), "FrameGrabberThread")
        self.thread_manager.register(self.frame_grabber_thread)
        self.frame_processor, self.frame_processor_thread = create_worker(FrameProcessor(ref_folder), "FrameProcessorThread")
        self.thread_manager.register(self.frame_processor_thread)

    @Slot()
    def _create_connections(self):
        """Связать сигналы рабочих объектов между собой и с интерфейсом."""
        self.frame_grabber.frame_ready.connect(self.frame_processor.process)
        self.frame_processor.result_ready.connect(self.main_window._update_frame)

        self.set_conf_thres.connect(self.frame_processor.update_conf_thres, Qt.ConnectionType.QueuedConnection)
        self.start_grabber_requested.connect(self.frame_grabber.start, Qt.ConnectionType.QueuedConnection)
        self.stop_grabber_requested.connect(self.frame_grabber.stop, Qt.ConnectionType.QueuedConnection)
        self.close_grabber_requested.connect(self.frame_grabber.close_source, Qt.ConnectionType.QueuedConnection)
        self.set_source_requested.connect(self.frame_grabber.set_source, Qt.ConnectionType.QueuedConnection)
        self.switch_reference_requested.connect(self.frame_processor.switch_reference, Qt.ConnectionType.QueuedConnection)

    @Slot()
    def _disconnect_frame_grabber(self):
        """Отключить всех текущих подписчиков от захватчика кадров."""
        try:
            self.frame_grabber.frame_ready.disconnect()
        except (RuntimeError, TypeError):
            pass

    @Slot()
    def _connect_main_pipeline(self):
        """Восстановить стандартную цепочку захвата и обработки кадров."""
        self._disconnect_frame_grabber()
        self.frame_grabber.frame_ready.connect(self.frame_processor.process)

    def update_thres(self, value):
        """Обновить порог уверенности детектора."""
        self.set_conf_thres.emit(value)

    def switch_to_add_part(self, display: FrameDisplay):
        """Перенаправить сырые кадры в виджет предпросмотра добавления детали."""
        self._disconnect_frame_grabber()
        self.frame_grabber.frame_ready.connect(display.update_frames)

    def switch_to_main(self):
        """Восстановить основной пайплайн детекции."""
        self._connect_main_pipeline()

    def start_pipeline(self):
        """Запустить получение кадров."""
        self.start_grabber_requested.emit()

    def stop_pipeline(self):
        """Остановить получение кадров."""
        self.stop_grabber_requested.emit()

    def set_source(self, source):
        """Заменить текущий источник кадров."""
        self.set_source_requested.emit(source)

    def close(self):
        """Закрыть текущий источник перед завершением работы."""
        self.close_grabber_requested.emit()

    def change_part(self, det_name):
        """Переключить активное имя эталона в обработчике."""
        self.switch_reference_requested.emit(det_name)
