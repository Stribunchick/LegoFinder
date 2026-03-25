# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
import math

import cv2
import numpy as np


@dataclass(slots=True)
class AffineView:
    image: np.ndarray
    mask: np.ndarray
    base_to_view: np.ndarray
    label: str


def normalize_gray(image_bgr: np.ndarray) -> np.ndarray:
    """Преобразовать изображение в оттенки серого с нормализацией контраста."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
    return clahe.apply(gray)


def extract_reference_mask(image_bgr: np.ndarray, min_area: int = 500) -> np.ndarray | None:
    """Выделить эталонный объект на преимущественно однотонном фоне."""
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    h, w = lab.shape[:2]

    border = np.concatenate(
        [
            lab[0, :, :],
            lab[h - 1, :, :],
            lab[:, 0, :],
            lab[:, w - 1, :],
        ],
        axis=0,
    )

    bg_color = np.median(border, axis=0)
    diff = np.linalg.norm(lab - bg_color, axis=2)

    _, mask = cv2.threshold(diff.astype(np.uint8), 18, 255, cv2.THRESH_BINARY)

    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(contour) < min_area:
        return None

    clean_mask = np.zeros_like(mask)
    cv2.drawContours(clean_mask, [contour], -1, 255, thickness=-1)
    return clean_mask


def crop_to_mask(
    image_bgr: np.ndarray,
    mask: np.ndarray,
    padding: int = 10,
) -> tuple[np.ndarray, np.ndarray, tuple[int, int, int, int]] | tuple[None, None, None]:
    """Обрезать изображение и маску по границам объекта с отступом."""
    ys, xs = np.where(mask > 0)
    if len(xs) == 0 or len(ys) == 0:
        return None, None, None

    x1 = max(0, int(xs.min()) - padding)
    y1 = max(0, int(ys.min()) - padding)
    x2 = min(image_bgr.shape[1], int(xs.max()) + padding + 1)
    y2 = min(image_bgr.shape[0], int(ys.max()) + padding + 1)

    crop = image_bgr[y1:y2, x1:x2].copy()
    crop_mask = mask[y1:y2, x1:x2].copy()
    return crop, crop_mask, (x1, y1, x2, y2)


def resize_reference(
    image_bgr: np.ndarray,
    mask: np.ndarray,
    max_side: int = 960,
) -> tuple[np.ndarray, np.ndarray]:
    """Изменить размер эталона и маски с сохранением пропорций."""
    h, w = image_bgr.shape[:2]
    scale = max_side / max(h, w)
    if scale >= 1.0:
        return image_bgr.copy(), mask.copy()

    new_size = (max(1, int(round(w * scale))), max(1, int(round(h * scale))))
    image_resized = cv2.resize(image_bgr, new_size, interpolation=cv2.INTER_AREA)
    mask_resized = cv2.resize(mask, new_size, interpolation=cv2.INTER_NEAREST)
    _, mask_resized = cv2.threshold(mask_resized, 127, 255, cv2.THRESH_BINARY)
    return image_resized, mask_resized


def compute_masked_hs_hist(image_bgr: np.ndarray, mask: np.ndarray | None) -> np.ndarray:
    """Вычислить нормализованную гистограмму по H и S внутри маски."""
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], mask, [36, 32], [0, 180, 0, 256])
    cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_L1)
    return hist


def compute_lab_stats(image_bgr: np.ndarray, mask: np.ndarray | None) -> np.ndarray:
    """Вычислить среднее и стандартное отклонение в пространстве LAB для пикселей маски."""
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    if mask is None:
        pixels = lab.reshape(-1, 3).astype(np.float32)
    else:
        pixels = lab[mask > 0].astype(np.float32)

    if pixels.size == 0:
        return np.zeros(6, dtype=np.float32)

    means = pixels.mean(axis=0)
    stds = pixels.std(axis=0)
    return np.concatenate([means, stds]).astype(np.float32)


def build_edge_map(image_bgr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Построить расширенную карту границ внутри области объекта."""
    gray = normalize_gray(image_bgr)
    edges = cv2.Canny(gray, 60, 150)
    if mask is not None:
        edges = cv2.bitwise_and(edges, edges, mask=mask)
    edges = cv2.dilate(edges, np.ones((3, 3), dtype=np.uint8), iterations=1)
    return edges


def resize_if_needed(image_bgr: np.ndarray, max_side: int = 1280) -> tuple[np.ndarray, float]:
    """Изменить размер изображения, если его сторона превышает лимит."""
    h, w = image_bgr.shape[:2]
    scale = max_side / max(h, w)
    if scale >= 1.0:
        return image_bgr.copy(), 1.0

    new_size = (max(1, int(round(w * scale))), max(1, int(round(h * scale))))
    return cv2.resize(image_bgr, new_size, interpolation=cv2.INTER_AREA), scale


def apply_rootsift(descriptors: np.ndarray | None) -> np.ndarray | None:
    """Применить нормализацию RootSIFT к дескрипторам типа SIFT."""
    if descriptors is None or len(descriptors) == 0:
        return None

    descriptors = descriptors.astype(np.float32)
    descriptors /= np.maximum(np.sum(descriptors, axis=1, keepdims=True), 1e-12)
    return np.sqrt(descriptors)


def generate_affine_views(
    image_bgr: np.ndarray,
    mask: np.ndarray,
    tilt_degrees: tuple[int, ...] = (0, 15, 30),
    rotations: tuple[int, ...] = (-90, -30, 0, 30, 90, 180),
) -> list[AffineView]:
    """Сгенерировать синтетические аффинные варианты эталонного объекта."""
    h, w = image_bgr.shape[:2]
    center = (w / 2.0, h / 2.0)
    bg_color = _estimate_border_color(image_bgr)
    views: list[AffineView] = []
    seen: set[tuple[int, int]] = set()

    for tilt in tilt_degrees:
        scale_x = max(0.72, math.cos(math.radians(tilt)))
        for rotation in rotations:
            key = (tilt, rotation % 360)
            if key in seen:
                continue
            seen.add(key)

            affine_2x3 = cv2.getRotationMatrix2D(center, rotation, 1.0)
            affine_2x3[0, 0] *= scale_x
            affine_2x3[0, 1] *= scale_x
            affine_2x3[0, 2] += (w - (w * scale_x)) / 2.0

            transformed = cv2.warpAffine(
                image_bgr,
                affine_2x3,
                (w, h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=bg_color,
            )
            transformed_mask = cv2.warpAffine(
                mask,
                affine_2x3,
                (w, h),
                flags=cv2.INTER_NEAREST,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=0,
            )

            if cv2.countNonZero(transformed_mask) < 250:
                continue

            views.append(
                AffineView(
                    image=transformed,
                    mask=transformed_mask,
                    base_to_view=np.vstack([affine_2x3, [0.0, 0.0, 1.0]]).astype(np.float32),
                    label=f"tilt_{tilt}_rot_{rotation % 360}",
                )
            )

    return views


def warp_binary_mask(mask: np.ndarray, homography: np.ndarray, frame_shape: tuple[int, int, int] | tuple[int, int]) -> np.ndarray:
    """Спроецировать бинарную маску в целевой кадр с помощью гомографии."""
    height, width = frame_shape[:2]
    return cv2.warpPerspective(
        mask,
        homography,
        (width, height),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )


def _estimate_border_color(image_bgr: np.ndarray) -> tuple[int, int, int]:
    """Оценить цвет фона по пикселям на границе изображения."""
    h, w = image_bgr.shape[:2]
    border = np.concatenate(
        [
            image_bgr[0, :, :],
            image_bgr[h - 1, :, :],
            image_bgr[:, 0, :],
            image_bgr[:, w - 1, :],
        ],
        axis=0,
    )
    color = np.median(border, axis=0).astype(np.uint8)
    return int(color[0]), int(color[1]), int(color[2])
