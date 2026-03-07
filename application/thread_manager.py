from PySide6.QtCore import QThread

class ThreadManager:
    def __init__(self):
        self._threads = []

    def register(self, thread: QThread):
        self._threads.append(thread)
    def start_up(self):
        for t in self._threads:
            t.start()
            
    def shutdown(self):
        for t in self._threads:
            t.quit()
        for t in self._threads:
            t.wait()

    
        