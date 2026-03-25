# -*- coding: utf-8 -*-
from PySide6.QtCore import QTimer, Signal, QObject, Slot, Qt
from application.source import Source


class FrameGrabber(QObject):
    frame_ready = Signal(object)

    def __init__(self):
        """Подготовить периодический захват кадров от текущего источника."""
        super().__init__()
        self.source = None
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self.acquire)

    @Slot(object)
    def set_source(self, source: Source):
        """Заменить активный источник и при необходимости открыть его заново."""
        if self.source is not None:
            self.source.close()
        self.source = source
        if self.source is not None:
            self.source.open()

    @Slot()
    def start(self):
        """Запустить периодический захват кадров."""
        if self.source is None or self._timer.isActive():
            return
        self._timer.start(33)

    @Slot()
    def stop(self):
        """Остановить периодический захват кадров."""
        if self._timer.isActive():
            self._timer.stop()

    @Slot()
    def close_source(self):
        """Остановить захват и закрыть текущий источник."""
        self.stop()
        if self.source is not None:
            self.source.close()
            self.source = None

    @Slot()
    def acquire(self):
        """Считать следующий кадр из источника и отправить сигнал."""
        if self.source is None:
            return

        frame = self.source.read()
        if frame is None:
            return
        self.frame_ready.emit(frame)
