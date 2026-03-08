from pathlib import Path
from typing import override
import numpy as np
import sys

from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow
from PySide6.QtCore import Slot
from gui.ui_mainwindow import Ui_MainWindow

from add_part_window import AddPartWindow

from application.appcontroller import AppController

from application.frame_display import FrameDisplay

from application.sources.videofile_source import VideoFileSource
from application.sources.webcam_source import CameraSource 
from application.sources.imagefile_source import ImageFileSource

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
        self.load_img_src_button.clicked.connect(self._on_load_image_button_clicked)

    @Slot(bool)
    def _on_start_stop_toggled(self, checked: bool):
        # print(f"STATE START/STOP BUTTON INIT {checked}")
        self.app_controller.frame_grabber.set_source(CameraSource(0))
        if checked:
            self.app_controller.start_pipeline()
        else:
            self.app_controller.stop_pipeline()

    def _on_load_image_button_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open media",
            "",
            "Media Files (*.mp4 *.avi *.mov *.mkv *.jpg *.png *.bmp)"
        )
        if not file_path:
            return
        
        ext = Path(file_path).suffix.lower()

        if ext in [".mp4", ".avi", ".mov", ".mkv"]:
            source = VideoFileSource(file_path)

        elif ext in [".jpg", ".jpeg", ".png", ".bmp"]:
            source = ImageFileSource(file_path)
        
        else:
            return
        self.app_controller.frame_grabber.set_source(source)

        if not self.start_stop_acq_button.isChecked():
            self.start_stop_acq_button.setChecked(True)

    #On button click -> stop camera acquisition, open window, switch frame_getter destination to app_window's videoframe

    @Slot()
    def _on_add_part_clicked(self):
        self.add_part_window = AddPartWindow(self)
        self.app_controller.switch_to_add_part(self.add_part_window.videoframe)
        self.start_stop_acq_button.setChecked(True)
        self.add_part_window.show()
        

    @Slot(object)
    def _update_frame(self, frame: np.ndarray):
        self.image_widget.update_frames(frame)

    @override
    def closeEvent(self, event):
        self.app_controller.thread_manager.shutdown()