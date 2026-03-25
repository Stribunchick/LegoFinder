import os
import sys

import cv2
from PySide6.QtWidgets import QApplication

from main_window import MainWindow

cv2.setUseOptimized(True)
try:
    cv2.setNumThreads(max(1, (os.cpu_count() or 1) - 1))
except Exception:
    pass

app = QApplication(sys.argv)
w = MainWindow()
w.show()
sys.exit(app.exec())

