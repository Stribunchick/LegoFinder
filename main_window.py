from PySide6.QtWidgets import QApplication, QMainWindow
from gui.ui_mainwindow import Ui_MainWindow
import sys


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


