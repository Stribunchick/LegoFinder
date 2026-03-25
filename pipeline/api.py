# -*- coding: utf-8 -*-
from __future__ import annotations

from pipeline.detector import DetectionResult, PartDetector
from pipeline.reference_manager import ReferenceManager


class PartMatchingPipeline:
    def __init__(self, storage_dir: str = "data/templates"):
        """Инициализировать хранилище эталонов и экземпляр детектора."""
        self.reference_manager = ReferenceManager(storage_dir=storage_dir)
        self.detector = PartDetector()
        self.current_reference = None

    def add_reference(self, name, image_bgr):
        """Сохранить новое эталонное изображение с указанным именем."""
        return self.reference_manager.add_reference(name, image_bgr)

    def list_references(self):
        """Вернуть список всех доступных эталонов."""
        return self.reference_manager.list_references()

    def load_reference(self, name: str):
        """Загрузить и сохранить в памяти эталон для последующей детекции."""
        self.current_reference = self.reference_manager.load_reference(name)
        self.detector.reset_tracking()
        self.detector.warmup(self.current_reference)
        return self.current_reference

    def clear_reference(self):
        """Сбросить текущий выбранный эталон."""
        self.current_reference = None
        self.detector.reset_tracking()

    def process_frame(self, frame_bgr, confidence_threshold: float = 50.0) -> list[DetectionResult]:
        """Запустить детекцию всех объектов активного эталона на кадре."""
        return self.detector.detect_all(
            frame_bgr=frame_bgr,
            reference=self.current_reference,
            confidence_threshold=confidence_threshold,
        )
