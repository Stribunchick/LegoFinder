from pathlib import Path
from typing import override
import numpy as np
import sys
import os

from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow
from PySide6.QtCore import Slot
from gui.ui_mainwindow import Ui_MainWindow

from add_part_window import AddPartWindow

from application.appcontroller import AppController

from application.frame_display import FrameDisplay

from application.sources.videofile_source import VideoFileSource
from application.sources.webcam_source import CameraSource 
from application.sources.imagefile_source import ImageFileSource
from application.des_combo_box import FileComboBox

class MainWindow(QMainWindow, Ui_MainWindow):
    add_part_window: AddPartWindow
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.folder = os.path.join(os.getcwd(),"data")
        self.select_part_combo_box = FileComboBox(self.folder)
        self.horizontalLayout.addWidget(self.select_part_combo_box)
        self.image_widget = FrameDisplay()
        self.frame.layout().addWidget(self.image_widget)
        self.app_controller = AppController(self)
        self.connect_signals()
        self.webcamsrc = 0
    
    def connect_signals(self):
        self.start_stop_acq_button.toggled.connect(self._on_start_stop_toggled)
        self.add_part_button.clicked.connect(self._on_add_part_clicked)
        self.load_img_src_button.clicked.connect(self._on_load_image_button_clicked)
        self.conf_thres_slider.valueChanged.connect(self._on_conf_thres_slider_changed)
        self.select_part_combo_box.activated.connect(self.show_list)
        self.select_part_combo_box.currentTextChanged.connect(self.select_part_from_list)

    @Slot(bool)
    def _on_start_stop_toggled(self, checked: bool):
        # print(f"STATE START/STOP BUTTON INIT {checked}")
        if not isinstance(self.app_controller.frame_grabber.source, CameraSource):
            self.app_controller.frame_grabber.set_source(CameraSource(self.webcamsrc))
        if checked:
            self.app_controller.start_pipeline()
        else:
            self.app_controller.stop_pipeline()

    @Slot()
    def _on_load_image_button_clicked(self):
        # self.start_stop_acq_button.setChecked(False)
        self.app_controller.stop_pipeline()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open media",
            "",
            "Media Files (*.mp4 *.avi *.mov *.mkv *.jpg *.png *.bmp)"
        )
        if not file_path:
            self.start_stop_acq_button.setChecked(True)
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
        self.app_controller.start_pipeline()

    #On button click -> stop camera acquisition, open window, switch frame_getter destination to app_window's videoframe
    @Slot(int)
    def _on_conf_thres_slider_changed(self, value):
        self.app_controller.update_thres(100-value)

    @Slot()
    def _on_add_part_clicked(self):
        self.add_part_window = AddPartWindow(self)
        self.app_controller.switch_to_add_part(self.add_part_window.videoframe)
        self.app_controller.frame_grabber.set_source(CameraSource(self.webcamsrc))
        self.start_stop_acq_button.setChecked(True)
        self.add_part_window.show()
        

    @Slot(object)
    def _update_frame(self, frame: np.ndarray):
        self.image_widget.update_frames(frame)


    def show_list(self):
        self.select_part_combo_box.showPopup()
    
    @Slot(str)
    def select_part_from_list(self, det_name):
        # Передать название файла в папке
        self.app_controller.change_part(det_name)


    @override
    def closeEvent(self, event):
        self.app_controller.thread_manager.shutdown()