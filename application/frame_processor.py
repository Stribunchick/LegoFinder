# -*- coding: utf-8 -*-
from PySide6.QtCore import QObject, QTimer, Signal, Slot

from pipeline import RobustPartMatchingPipeline, draw_detection


class FrameProcessor(QObject):
    started = Signal()
    stopped = Signal()
    result_ready = Signal(object)

    _running: bool

    def __init__(self, folder="./data/robust_templates"):
        """Инициализировать пайплайн детекции и таймер объединения кадров."""
        super().__init__()
        self.folder = folder
        self._running = False
        self.conf_thres: float = 0.5
        self.pipeline = RobustPartMatchingPipeline(storage_dir=folder)
        self._pending_frame = None
        self._process_timer = QTimer(self)
        self._process_timer.setSingleShot(True)
        self._process_timer.timeout.connect(self._process_pending)

    @Slot(object)
    def process(self, frame):
        """Поставить последний кадр в очередь на обработку."""
        self._pending_frame = frame
        if not self._process_timer.isActive():
            self._process_timer.start(0)

    @Slot()
    def _process_pending(self):
        """Обработать последний кадр в очереди и отправить результат."""
        frame = self._pending_frame
        self._pending_frame = None
        if frame is None:
            return

        detection = self.pipeline.process_frame(
            frame,
            confidence_threshold=self.conf_thres * 100,
        )
        output_frame = draw_detection(frame, detection)
        self.result_ready.emit(output_frame)

        if self._pending_frame is not None:
            self._process_timer.start(0)

    @Slot(int)
    def update_conf_thres(self, value):
        """Обновить порог уверенности детектора по значению из интерфейса."""
        self.conf_thres = value / 100
        print(f"[FrameProcessor] Threshold updated to {self.conf_thres:.2f}")

    @Slot(str)
    def switch_reference(self, reference_name):
        """Загрузить или сбросить активный эталон для детекции."""
        if not reference_name:
            self.pipeline.clear_reference()
            return

        self.pipeline.load_reference(reference_name)
        print(f"[FrameProcessor] Switched to reference: {reference_name}")


if __name__ == "__main__":
    ...
