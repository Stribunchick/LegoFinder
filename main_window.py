from typing import override

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Slot

from gui.ui_mainwindow import Ui_MainWindow
import sys
from application.appcontroller import AppController

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.app_controller = AppController()
        self.connect_signals()
    
    def connect_signals(self):
        self.start_stop_acq_button.toggled.connect(self._on_start_stop_toggled)
        self.add_part_button.clicked.connect(self._on_add_part_clicked)

    @Slot(bool)
    def _on_start_stop_toggled(self, checked: bool):
        print(f"STATE START/STOP BUTTON INIT {checked}")
        if checked:
            self.app_controller.start_pipeline()
        else:
            self.app_controller.stop_pipeline()

    @Slot()
    def _on_add_part_clicked(self):
        print("Add Button Clicked")

    @override
    def closeEvent(self, event):
        self.app_controller.thread_manager.shutdown()