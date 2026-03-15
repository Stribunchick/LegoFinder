from PySide6.QtWidgets import QApplication, QMainWindow
from gui.ui_mainwindow import Ui_MainWindow
import sys
from main_window import MainWindow

app = QApplication()
w = MainWindow()
w.show()
sys.exit(app.exec())

