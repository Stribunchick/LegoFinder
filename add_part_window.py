from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QWidget
from PySide6.QtCore import Slot
import cv2

from gui.ui_add_part_window import Ui_AddPartWindow
from application.frame_display import FrameDisplay

class AddPartWindow(QWidget, Ui_AddPartWindow):
    videoframe: FrameDisplay
    staticframe: FrameDisplay
    def __init__(self, parent):
        super().__init__()
        self.setupUi(self)
        self.main_window = parent
        self.videoframe = FrameDisplay()
        self.videostream_frame.layout().addWidget(self.videoframe)
        
        self.staticframe = FrameDisplay()
        self.static_frame.layout().addWidget(self.staticframe)
        
        
        self._connect_signals()
    
    def _connect_signals(self):
        self.snapshot_button.clicked.connect(self._on_snapshot_button_clicked)
        self.load_image_button.clicked.connect(self._on_load_image_button_clicked)
        
    def _on_snapshot_button_clicked(self):
        frame = self.videoframe.copy_frame()
        self.staticframe.update_frames(frame)

    def _on_load_image_button_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open media",
            "",
            "Media Files (*.jpg *.png *.bmp *.jpeg)"
        )
        if not file_path:
            return
        
        ext = Path(file_path).suffix.lower()

        if ext in [".jpg", ".jpeg", ".png", ".bmp"]:
            image = cv2.imread(file_path)
            self.staticframe.update_frames(image)
        

    def closeEvent(self, event):
        self.main_window.app_controller.switch_to_main()
        super().closeEvent(event)