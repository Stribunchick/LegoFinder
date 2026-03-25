# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from pipeline.preprocessing import (
    apply_rootsift,
    build_edge_map,
    compute_lab_stats,
    compute_masked_hs_hist,
    crop_to_mask,
    estimate_border_color,
    extract_reference_mask,
    generate_affine_views,
    gradient_magnitude,
    normalize_gray,
    order_points,
    resize_reference,
)


class ReferenceManager:
    schema_version = 2

    def __init__(self, storage_dir: str = "data/templates", max_reference_side: int = 960):
        """Подготовить хранилище эталонов и локальный экстрактор признаков."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.max_reference_side = max_reference_side
        self.max_features_per_view = 560
        self.feature_name = "sift" if hasattr(cv2, "SIFT_create") else "akaze"
        self.extractor = self._create_extractor()

    def _create_extractor(self):
        """Создать экстрактор признаков для представлений эталона."""
        if self.feature_name == "sift":
            return cv2.SIFT_create(
                nfeatures=1400,
                contrastThreshold=0.018,
                edgeThreshold=10,
                sigma=1.4,
            )
        return cv2.AKAZE_create(threshold=0.0008, nOctaves=5, nOctaveLayers=5)

    def add_reference(self, name: str, image_bgr: np.ndarray) -> str:
        """Выделить, закодировать и сохранить новый эталонный объект."""
        if image_bgr is None:
            raise ValueError("Empty reference image")

        mask = extract_reference_mask(image_bgr)
        if mask is None:
            raise ValueError("Failed to segment the part from the plain background")

        crop, crop_mask, _ = crop_to_mask(image_bgr, mask, padding=12)
        if crop is None or crop_mask is None:
            raise ValueError("Failed to crop the segmented part")

        crop, crop_mask = resize_reference(crop, crop_mask, max_side=self.max_reference_side)
        payload = self._build_reference_payload(name, crop, crop_mask)

        item_dir = self.storage_dir / self._safe_name(name)
        if item_dir.exists():
            raise FileExistsError(f"Reference '{name}' already exists")
        item_dir.mkdir(parents=True, exist_ok=False)

        self._save_reference_payload(item_dir, payload)
        return str(item_dir)

    def load_reference(self, name: str) -> dict:
        """Загрузить сохранённый эталон и обновить его при смене схемы."""
        item_dir = self.storage_dir / self._safe_name(name)
        meta_path = item_dir / "meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"Reference '{name}' not found")

        meta = self._read_meta(item_dir)
        if meta.get("schema_version", 1) < self.schema_version or not (item_dir / "views.npz").exists():
            self._upgrade_reference_item(item_dir, meta["name"])
            meta = self._read_meta(item_dir)

        image = cv2.imread(str(item_dir / "template.png"))
        mask = cv2.imread(str(item_dir / "mask.png"), cv2.IMREAD_GRAYSCALE)
        edges = cv2.imread(str(item_dir / "edges.png"), cv2.IMREAD_GRAYSCALE)
        hist = np.load(str(item_dir / "hist.npy"))
        lab_stats = np.load(str(item_dir / "lab_stats.npy"))

        if image is None or mask is None or edges is None:
            raise ValueError(f"Reference '{name}' is incomplete")

        views = self._load_views(item_dir, image, mask, edges)
        if not views:
            raise ValueError(f"Reference '{name}' has no valid view descriptors")

        contour = self._largest_contour(mask)
        aspect_ratio, rectangularity = self._shape_stats(contour)
        hsv_mean, hsv_std = self._hsv_stats(image, mask)

        return {
            "name": meta["name"],
            "feature_name": meta["feature_name"],
            "image": image,
            "mask": mask,
            "edges": edges,
            "hist": hist.astype(np.float32),
            "lab_stats": lab_stats.astype(np.float32),
            "width": int(meta["width"]),
            "height": int(meta["height"]),
            "mask_area": int(cv2.countNonZero(mask)),
            "contour": contour,
            "aspect_ratio": aspect_ratio,
            "rectangularity": rectangularity,
            "hsv_mean": hsv_mean,
            "hsv_std": hsv_std,
            "views": views,
        }

    def list_references(self) -> list[str]:
        """Вернуть список всех эталонов, доступных в хранилище."""
        result: list[str] = []
        for item_dir in self.storage_dir.iterdir():
            meta_path = item_dir / "meta.json"
            if not meta_path.exists():
                continue
            try:
                with open(meta_path, "r", encoding="utf-8") as file_obj:
                    result.append(json.load(file_obj)["name"])
            except Exception:
                continue
        return sorted(result)

    def _build_reference_payload(self, name: str, image_bgr: np.ndarray, mask: np.ndarray) -> dict:
        """Собрать полный сериализуемый набор данных для нового эталона."""
        _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
        hist = compute_masked_hs_hist(image_bgr, mask)
        lab_stats = compute_lab_stats(image_bgr, mask)
        edges = build_edge_map(image_bgr, mask)
        views = self._build_views(image_bgr, mask)

        if not views:
            raise ValueError("Reference image has too few stable local features")

        meta = {
            "schema_version": self.schema_version,
            "name": name,
            "feature_name": self.feature_name,
            "width": int(image_bgr.shape[1]),
            "height": int(image_bgr.shape[0]),
            "num_views": int(len(views)),
            "feature_count": int(sum(len(view["points"]) for view in views)),
        }
        return {
            "meta": meta,
            "image": image_bgr,
            "mask": mask,
            "edges": edges,
            "hist": hist,
            "lab_stats": lab_stats,
            "views": views,
        }

    def _build_views(self, image_bgr: np.ndarray, mask: np.ndarray) -> list[dict]:
        """Создать аффинные представления эталона и извлечь их ключевые точки."""
        views: list[dict] = []

        for affine_view in generate_affine_views(image_bgr, mask):
            gray = normalize_gray(affine_view.image)
            keypoints, descriptors = self.extractor.detectAndCompute(gray, affine_view.mask)
            descriptors = self._normalize_descriptors(descriptors)
            if descriptors is None or not keypoints:
                continue

            view_points = np.array([kp.pt for kp in keypoints], dtype=np.float32)
            base_to_view = affine_view.base_to_view.astype(np.float32)
            inv_transform = np.linalg.inv(base_to_view)

            ones = np.ones((len(view_points), 1), dtype=np.float32)
            view_points_h = np.hstack([view_points, ones])
            base_points_h = (inv_transform @ view_points_h.T).T
            base_points = base_points_h[:, :2] / base_points_h[:, 2:3]

            valid = (
                (base_points[:, 0] >= 0)
                & (base_points[:, 0] < image_bgr.shape[1])
                & (base_points[:, 1] >= 0)
                & (base_points[:, 1] < image_bgr.shape[0])
            )
            if not np.any(valid):
                continue

            base_points_valid = base_points[valid].astype(np.float32)
            point_mask = mask[
                np.clip(np.round(base_points_valid[:, 1]).astype(int), 0, mask.shape[0] - 1),
                np.clip(np.round(base_points_valid[:, 0]).astype(int), 0, mask.shape[1] - 1),
            ] > 0

            if int(np.count_nonzero(point_mask)) < 18:
                continue

            view_descriptors = descriptors[valid][point_mask]
            view_points_valid = view_points[valid][point_mask].astype(np.float32)
            base_points_selected = base_points_valid[point_mask].astype(np.float32)
            view_descriptors, view_points_valid, base_points_selected = self._trim_view_features(
                view_descriptors,
                view_points_valid,
                base_points_selected,
            )

            views.append(
                {
                    "label": affine_view.label,
                    "descriptors": view_descriptors.astype(np.float32 if self.feature_name == "sift" else view_descriptors.dtype),
                    "points": view_points_valid,
                    "base_points": base_points_selected,
                    "base_to_view": base_to_view,
                }
            )

        views.sort(key=lambda item: len(item["points"]), reverse=True)
        return views

    def _save_reference_payload(self, item_dir: Path, payload: dict) -> None:
        """Записать подготовленный набор данных эталона на диск."""
        cv2.imwrite(str(item_dir / "template.png"), payload["image"])
        cv2.imwrite(str(item_dir / "mask.png"), payload["mask"])
        cv2.imwrite(str(item_dir / "edges.png"), payload["edges"])
        np.save(str(item_dir / "hist.npy"), payload["hist"])
        np.save(str(item_dir / "lab_stats.npy"), payload["lab_stats"])

        with open(item_dir / "meta.json", "w", encoding="utf-8") as file_obj:
            json.dump(payload["meta"], file_obj, ensure_ascii=False, indent=2)

        np.savez_compressed(
            str(item_dir / "views.npz"),
            labels=np.array([view["label"] for view in payload["views"]], dtype=object),
            descriptors=np.array([view["descriptors"] for view in payload["views"]], dtype=object),
            points=np.array([view["points"] for view in payload["views"]], dtype=object),
            base_points=np.array([view["base_points"] for view in payload["views"]], dtype=object),
            base_to_view=np.stack([view["base_to_view"] for view in payload["views"]]).astype(np.float32),
        )

    def _load_views(self, item_dir: Path, image: np.ndarray, mask: np.ndarray, edges: np.ndarray) -> list[dict]:
        """Загрузить сериализованные представления и восстановить служебные метаданные."""
        data = np.load(str(item_dir / "views.npz"), allow_pickle=True)
        labels = list(data["labels"])
        descriptors_list = data["descriptors"]
        points_list = data["points"]
        base_points_list = data["base_points"]
        base_to_view = data["base_to_view"].astype(np.float32)

        view_bg_color = estimate_border_color(image)
        views: list[dict] = []

        for index in range(len(base_to_view)):
            transform = base_to_view[index]
            descriptors = np.asarray(descriptors_list[index], dtype=np.float32 if self.feature_name == "sift" else np.uint8)
            points = np.asarray(points_list[index], dtype=np.float32)
            base_points = np.asarray(base_points_list[index], dtype=np.float32)
            descriptors, points, base_points = self._trim_view_features(descriptors, points, base_points)
            affine_2x3 = transform[:2, :]
            view_image = cv2.warpAffine(
                image,
                affine_2x3,
                (image.shape[1], image.shape[0]),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=view_bg_color,
            )
            view_mask = cv2.warpAffine(
                mask,
                affine_2x3,
                (image.shape[1], image.shape[0]),
                flags=cv2.INTER_NEAREST,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=0,
            )
            view_edges = cv2.warpAffine(
                edges,
                affine_2x3,
                (image.shape[1], image.shape[0]),
                flags=cv2.INTER_NEAREST,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=0,
            )
            view_gray = normalize_gray(view_image)
            contour = self._largest_contour(view_mask)
            aspect_ratio, rectangularity = self._shape_stats(contour)
            box_points = self._contour_box_points(contour)

            views.append(
                {
                    "label": str(labels[index]),
                    "descriptors": descriptors,
                    "points": points,
                    "base_points": base_points,
                    "base_to_view": transform,
                    "mask": view_mask,
                    "edges": view_edges,
                    "gray": view_gray,
                    "grad": gradient_magnitude(view_gray),
                    "width": int(image.shape[1]),
                    "height": int(image.shape[0]),
                    "contour": contour,
                    "aspect_ratio": aspect_ratio,
                    "rectangularity": rectangularity,
                    "box_points": box_points,
                    "area": int(cv2.countNonZero(view_mask)),
                }
            )

        return views

    def _trim_view_features(
        self,
        descriptors: np.ndarray,
        points: np.ndarray,
        base_points: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Ограничить число признаков в одном представлении эталона."""
        if len(points) <= self.max_features_per_view:
            return descriptors, points, base_points

        indices = np.linspace(0, len(points) - 1, self.max_features_per_view, dtype=np.int32)
        return descriptors[indices], points[indices], base_points[indices]

    def _upgrade_reference_item(self, item_dir: Path, fallback_name: str) -> None:
        """Пересобрать старый эталон в соответствии с текущей схемой."""
        image = cv2.imread(str(item_dir / "template.png"))
        mask = cv2.imread(str(item_dir / "mask.png"), cv2.IMREAD_GRAYSCALE)
        if image is None or mask is None:
            raise ValueError(f"Reference '{fallback_name}' is incomplete and cannot be upgraded")

        crop, crop_mask = resize_reference(image, mask, max_side=self.max_reference_side)
        payload = self._build_reference_payload(fallback_name, crop, crop_mask)
        self._save_reference_payload(item_dir, payload)

    def _read_meta(self, item_dir: Path) -> dict:
        """Считать метаданные эталона с диска."""
        with open(item_dir / "meta.json", "r", encoding="utf-8") as file_obj:
            return json.load(file_obj)

    def _normalize_descriptors(self, descriptors: np.ndarray | None) -> np.ndarray | None:
        """Нормализовать дескрипторы в формат, ожидаемый сопоставителем."""
        if descriptors is None:
            return None
        if self.feature_name == "sift":
            return apply_rootsift(descriptors)
        return descriptors

    @staticmethod
    def _largest_contour(mask: np.ndarray) -> np.ndarray:
        """Вернуть самый большой контур в бинарной маске."""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return np.zeros((0, 1, 2), dtype=np.int32)
        return max(contours, key=cv2.contourArea)

    @staticmethod
    def _shape_stats(contour: np.ndarray) -> tuple[float, float]:
        """Вычислить отношение сторон и прямоугольность контура."""
        if contour is None or len(contour) == 0:
            return 1.0, 0.0

        area = max(1.0, float(cv2.contourArea(contour)))
        (_, _), (w, h), _ = cv2.minAreaRect(contour)
        min_side = max(1.0, min(w, h))
        max_side = max(1.0, max(w, h))
        aspect_ratio = max_side / min_side
        rectangularity = area / max(1.0, w * h)
        return float(aspect_ratio), float(rectangularity)

    @staticmethod
    def _contour_box_points(contour: np.ndarray) -> np.ndarray:
        """Вернуть упорядоченные углы минимального прямоугольника контура."""
        if contour is None or len(contour) < 4:
            return np.zeros((4, 2), dtype=np.float32)

        points = cv2.boxPoints(cv2.minAreaRect(contour)).astype(np.float32)
        return order_points(points)

    @staticmethod
    def _hsv_stats(image_bgr: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Вычислить среднее и стандартное отклонение в HSV для маски."""
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
        pixels = hsv[mask > 0]
        if pixels.size == 0:
            return np.zeros(3, dtype=np.float32), np.ones(3, dtype=np.float32)
        return pixels.mean(axis=0).astype(np.float32), pixels.std(axis=0).astype(np.float32)

    @staticmethod
    def _safe_name(name: str) -> str:
        """Преобразовать имя эталона в безопасное имя папки."""
        clean = "".join(ch if ch.isalnum() or ch in ("_", "-", " ") else "_" for ch in name)
        return clean.strip().replace(" ", "_")
