from pathlib import Path
import os

import cv2
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from application.frame_display import FrameDisplay
from gui.add_part_window_ui import Ui_AddPartWindow
from robust_pipeline import RobustReferenceManager


class AddPartWindow(QWidget, Ui_AddPartWindow):
    videoframe: FrameDisplay
    staticframe: FrameDisplay

    def __init__(self, parent, reference_folder="./data/robust_templates"):
        """Инициализировать окно для захвата и сохранения эталонов."""
        super().__init__()
        self.setupUi(self)
        self.main_window = parent
        self.reference_folder = reference_folder
        self.reference_manager = RobustReferenceManager(reference_folder)

        os.makedirs(self.reference_folder, exist_ok=True)

        self.videoframe = FrameDisplay()
        self.videostream_frame.layout().addWidget(self.videoframe)

        self.staticframe = FrameDisplay()
        self.static_frame.layout().addWidget(self.staticframe)

        self._connect_signals()

    def _connect_signals(self):
        """Подключить кнопки окна добавления детали к обработчикам."""
        self.snapshot_button.clicked.connect(self._on_snapshot_button_clicked)
        self.load_image_button.clicked.connect(self._on_load_image_button_clicked)
        self.process_template_button.clicked.connect(self._on_process_template_button_clicked)

    def _on_snapshot_button_clicked(self):
        """Скопировать последний кадр с камеры в статический предпросмотр."""
        frame = self.videoframe.copy_frame()
        if frame is None:
            QMessageBox.warning(self, "РћС€РёР±РєР°", "РќРµС‚ РєР°РґСЂР° СЃ РєР°РјРµСЂС‹ РґР»СЏ СЃРЅРёРјРєР°")
            return
        self.staticframe.update_frames(frame)

    def _on_load_image_button_clicked(self):
        """Загрузить изображение с диска в статический предпросмотр."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open media",
            "",
            "Media Files (*.jpg *.png *.bmp *.jpeg)",
        )
        if not file_path:
            return

        ext = Path(file_path).suffix.lower()
        if ext not in [".jpg", ".jpeg", ".png", ".bmp"]:
            return

        image = cv2.imread(file_path)
        if image is None:
            QMessageBox.warning(self, "РћС€РёР±РєР°", "РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РіСЂСѓР·РёС‚СЊ РёР·РѕР±СЂР°Р¶РµРЅРёРµ")
            return
        self.staticframe.update_frames(image)

    @Slot()
    def _on_process_template_button_clicked(self):
        """Создать и сохранить новый эталон из текущего статического кадра."""
        name = self.part_name_lineedit.text().strip()
        if not name:
            QMessageBox.warning(self, "РћС€РёР±РєР°", "Р’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ РґРµС‚Р°Р»Рё")
            return

        frame = self.staticframe.copy_frame()
        if frame is None:
            QMessageBox.warning(self, "РћС€РёР±РєР°", "РЎРЅР°С‡Р°Р»Р° СЃРґРµР»Р°Р№С‚Рµ СЃРЅРёРјРѕРє РёР»Рё Р·Р°РіСЂСѓР·РёС‚Рµ РёР·РѕР±СЂР°Р¶РµРЅРёРµ")
            return

        try:
            self.reference_manager.add_reference(name, frame)
            QMessageBox.information(self, "РЈСЃРїРµС…", f"Р”РµС‚Р°Р»СЊ '{name}' СѓСЃРїРµС€РЅРѕ РґРѕР±Р°РІР»РµРЅР°")
            self.main_window.select_part_combo_box.refresh_items()
            self.part_name_lineedit.clear()
        except Exception as exc:
            QMessageBox.critical(self, "РћС€РёР±РєР°", str(exc))

    def closeEvent(self, event):
        """Восстановить основной пайплайн после закрытия окна добавления."""
        self.main_window.app_controller.switch_to_main()
        super().closeEvent(event)
