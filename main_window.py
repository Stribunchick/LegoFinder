from typing import override
import numpy as np

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Slot

from add_part_window import AddPartWindow
from gui.ui_mainwindow import Ui_MainWindow
import sys
from application.appcontroller import AppController
from application.frame_display import FrameDisplay

class MainWindow(QMainWindow, Ui_MainWindow):
    add_part_window: AddPartWindow
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.image_widget = FrameDisplay()
        self.frame.layout().addWidget(self.image_widget)
        self.app_controller = AppController(self)
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

    #On button click -> stop camera acquisition, open window, switch frame_getter destination to app_window's videoframe

    @Slot()
    def _on_add_part_clicked(self):
        self.add_part_window = AddPartWindow()
        self.add_part_window.show()
        

    @Slot(object)
    def _update_frame(self, frame: np.ndarray):
        self.image_widget.update_frames(frame)

    @override
    def closeEvent(self, event):
        self.app_controller.thread_manager.shutdown()