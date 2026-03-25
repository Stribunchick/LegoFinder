# -*- coding: utf-8 -*-
from PySide6.QtCore import QThread


class ThreadManager:
    def __init__(self):
        """Инициализировать хранилище для рабочих потоков."""
        self._threads = []

    def register(self, thread: QThread):
        """Зарегистрировать поток для согласованного завершения."""
        self._threads.append(thread)

    def shutdown(self):
        """Остановить все зарегистрированные потоки и дождаться завершения."""
        for t in self._threads:
            t.quit()
        for t in self._threads:
            t.wait()
