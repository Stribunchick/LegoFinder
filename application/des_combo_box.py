import os
from PySide6.QtWidgets import QApplication, QComboBox, QWidget, QVBoxLayout


class FileComboBox(QComboBox):
    def __init__(self, directory):
        super().__init__()
        self.directory = directory

    def showPopup(self):
        
        self.clear()
        files = [
            f for f in os.listdir(self.directory)
            if os.path.isfile(os.path.join(self.directory, f))
        ]
        self.addItems(files)

        super().showPopup()


