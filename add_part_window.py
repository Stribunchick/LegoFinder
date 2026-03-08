from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Slot
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
        # self.snapshot_button.clicked.connect()
        # self.load_image_button.clicked.connect()
        ...
        
    def closeEvent(self, event):
        self.main_window.app_controller.switch_to_main()
        super().closeEvent(event)