# -*- coding: utf-8 -*-
import os
import json
from PySide6.QtWidgets import QComboBox


class FileComboBox(QComboBox):
    def __init__(self, directory):
        """Сохранить директорию, из которой заполняется комбобокс."""
        super().__init__()
        self.directory = directory

    def showPopup(self):
        """Обновить список элементов перед открытием выпадающего списка."""
        self.refresh_items()
        super().showPopup()

    def refresh_items(self):
        """Заново загрузить названия деталей из метаданных на диске."""
        self.clear()

        if not os.path.exists(self.directory):
            return

        items = []
        for name in os.listdir(self.directory):
            item_path = os.path.join(self.directory, name)
            meta_path = os.path.join(item_path, "meta.json")

            if os.path.isdir(item_path) and os.path.isfile(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    items.append(meta["name"])
                except Exception:
                    continue

        self.addItems(sorted(items))
