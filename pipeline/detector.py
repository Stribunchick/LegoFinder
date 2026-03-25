# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
import math

import cv2
import numpy as np

from pipeline.preprocessing import (
    apply_rootsift,
    compute_lab_stats,
    compute_masked_hs_hist,
    normalize_gray,
    resize_if_needed,
    warp_binary_mask,
)


@dataclass(slots=True)
class DetectionResult:
    name: str
    confidence: float
    bbox: list[int]
    polygon: np.ndarray
    debug: dict


class RobustPartDetector:
    def __init__(self):
        """Создать детектор и его компоненты для сопоставления признаков."""
        self.feature_name = "sift" if hasattr(cv2, "SIFT_create") else "akaze"
        self.extractor = self._create_extractor()
        self.matcher = self._create_matcher()
        self.homography_method = getattr(cv2, "USAC_MAGSAC", cv2.RANSAC)
        self._frame_index = 0
        self._tracked_reference_name: str | None = None
        self._tracked_bbox_norm: tuple[float, float, float, float] | None = None
        self._tracking_misses = 0
        self._max_tracking_misses = 6
        self._min_proposal_pixels = 160
        self._sparse_global_search_interval = 5
        self._tracked_refresh_interval = 4
        self._top_feature_blobs = 2
        self._global_max_side = 896
        self._tracked_max_side = 704
        self._max_feature_views = 4
        self._tracked_feature_views = 2
        self._max_ranked_views = 3
        self._max_candidate_contours = 6
        self._tracked_candidate_contours = 4
        self._fast_track_confidence = 56.0

    def _create_extractor(self):
        """Создать локальный экстрактор признаков для сопоставления кадров."""
        if self.feature_name == "sift":
            return cv2.SIFT_create(
                nfeatures=1400,
                contrastThreshold=0.018,
                edgeThreshold=10,
                sigma=1.4,
            )
        return cv2.AKAZE_create(threshold=0.0008, nOctaves=5, nOctaveLayers=5)

    def _create_matcher(self):
        """Создать сопоставитель дескрипторов для выбранного типа признаков."""
        if self.feature_name == "sift":
            index_params = dict(algorithm=1, trees=6)
            search_params = dict(checks=40)
            return cv2.FlannBasedMatcher(index_params, search_params)
        return cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    def detect(
        self,
        frame_bgr: np.ndarray,
        reference: dict | None,
        confidence_threshold: float = 50.0,
    ) -> DetectionResult | None:
        """Найти активный эталонный объект на кадре."""
        if frame_bgr is None or reference is None:
            return None

        self._frame_index += 1
        if self._tracked_reference_name not in (None, reference["name"]):
            self.reset_tracking()

        resize_limit = self._tracked_max_side if self._tracked_bbox_norm is not None else self._global_max_side
        frame_small, scale = resize_if_needed(frame_bgr, max_side=resize_limit)
        gray = normalize_gray(frame_small)
        focus_bbox = self._predict_focus_bbox(frame_small.shape, reference["name"])
        proposal_mask = self._combined_candidate_mask(frame_small, reference, focus_bbox=focus_bbox)
        local_mask = self._restrict_mask_to_bbox(proposal_mask, focus_bbox, margin=12) if focus_bbox else proposal_mask

        best_candidate = None

        if focus_bbox is not None:
            tracked_candidate = self._tracked_fast_candidate(
                frame_bgr=frame_small,
                frame_gray=gray,
                reference=reference,
                proposal_mask=local_mask,
            )
            if tracked_candidate is not None:
                best_candidate = tracked_candidate

        proposal_pixels = int(cv2.countNonZero(local_mask if focus_bbox is not None else proposal_mask))
        candidate_mask = local_mask if focus_bbox is not None and cv2.countNonZero(local_mask) > 0 else proposal_mask
        geometry_checked = False

        if focus_bbox is None and proposal_pixels >= self._min_proposal_pixels:
            quick_candidate = self._proposal_from_candidates(
                frame_small,
                gray,
                reference,
                candidate_mask,
                max_candidates=min(4, self._max_candidate_contours),
            )
            geometry_checked = True
            if quick_candidate is not None:
                best_candidate = quick_candidate

            if best_candidate is None or best_candidate["confidence"] < max(confidence_threshold, 54.0):
                quick_fallback = self._fallback_color_shape_candidate(
                    frame_small,
                    gray,
                    reference,
                    candidate_mask,
                    max_candidates=3,
                )
                if quick_fallback is not None and (
                    best_candidate is None or quick_fallback["confidence"] > best_candidate["confidence"]
                ):
                    best_candidate = quick_fallback

        allow_feature_search = True
        feature_view_limit = self._max_feature_views
        min_keypoints = 22
        search_mask = self._feature_search_mask(candidate_mask, frame_small.shape, focus_bbox=focus_bbox)

        if focus_bbox is not None:
            feature_view_limit = self._tracked_feature_views
            min_keypoints = 14
            allow_feature_search = (
                best_candidate is None
                or best_candidate["confidence"] < max(self._fast_track_confidence, confidence_threshold - 4.0)
                or self._tracking_misses > 0
                or self._frame_index % self._tracked_refresh_interval == 0
            )
        elif proposal_pixels < self._min_proposal_pixels:
            allow_feature_search = self._frame_index % self._sparse_global_search_interval == 0
            if allow_feature_search:
                search_mask = None

        if allow_feature_search and (best_candidate is None or best_candidate["confidence"] < max(42.0, confidence_threshold - 6.0)):
            feature_candidate = self._detect_feature_candidate(
                frame_bgr=frame_small,
                frame_gray=gray,
                reference=reference,
                search_mask=search_mask,
                min_keypoints=min_keypoints,
                view_limit=feature_view_limit,
            )
            if feature_candidate is not None and (
                best_candidate is None or feature_candidate["confidence"] > best_candidate["confidence"]
            ):
                best_candidate = feature_candidate

        needs_geometry_pass = (
            not geometry_checked
            and (
                best_candidate is None
                or best_candidate["confidence"] < max(confidence_threshold + 2.0, 58.0)
                or focus_bbox is None
            )
        )

        if needs_geometry_pass:
            contour_limit = self._tracked_candidate_contours if focus_bbox is not None else self._max_candidate_contours
            proposal_candidate = self._proposal_from_candidates(
                frame_small,
                gray,
                reference,
                candidate_mask,
                max_candidates=contour_limit,
            )
            if proposal_candidate is not None and (
                best_candidate is None or proposal_candidate["confidence"] > best_candidate["confidence"]
            ):
                best_candidate = proposal_candidate

            if best_candidate is None or best_candidate["confidence"] < max(confidence_threshold, 52.0):
                fallback_candidate = self._fallback_color_shape_candidate(
                    frame_small,
                    gray,
                    reference,
                    candidate_mask,
                    max_candidates=contour_limit,
                )
                if fallback_candidate is not None and (
                    best_candidate is None or fallback_candidate["confidence"] > best_candidate["confidence"]
                ):
                    best_candidate = fallback_candidate

        if best_candidate is None or best_candidate["confidence"] < confidence_threshold:
            self._register_miss(reference["name"])
            return None

        self._register_success(reference["name"], best_candidate["bbox"], frame_small.shape)
        polygon_full = best_candidate["polygon"] / scale
        bbox_full = [int(round(coord / scale)) for coord in best_candidate["bbox"]]

        return DetectionResult(
            name=reference["name"],
            confidence=best_candidate["confidence"],
            bbox=bbox_full,
            polygon=polygon_full.astype(np.int32),
            debug=best_candidate["debug"],
        )

    def _detect_feature_candidate(
        self,
        frame_bgr: np.ndarray,
        frame_gray: np.ndarray,
        reference: dict,
        search_mask: np.ndarray | None,
        min_keypoints: int,
        view_limit: int | None = None,
    ) -> dict | None:
        """Запустить поиск по признакам в указанной области кадра."""
        keypoints_frame, descriptors_frame = self.extractor.detectAndCompute(frame_gray, search_mask)
        if descriptors_frame is None or len(keypoints_frame) < min_keypoints:
            return None

        descriptors_frame = self._normalize_descriptors(descriptors_frame)
        if descriptors_frame is None:
            return None

        frame_points = np.array([kp.pt for kp in keypoints_frame], dtype=np.float32)
        best_candidate = None

        views = reference["views"] if view_limit is None else reference["views"][:view_limit]
        for view_index, view in enumerate(views):
            candidate = self._evaluate_view(
                frame_bgr=frame_bgr,
                frame_gray=frame_gray,
                frame_points=frame_points,
                frame_descriptors=descriptors_frame,
                reference=reference,
                view=view,
                view_index=view_index,
            )
            if candidate is None:
                continue
            if best_candidate is None or candidate["confidence"] > best_candidate["confidence"]:
                best_candidate = candidate

        return best_candidate

    def _evaluate_view(
        self,
        frame_bgr: np.ndarray,
        frame_gray: np.ndarray,
        frame_points: np.ndarray,
        frame_descriptors: np.ndarray,
        reference: dict,
        view: dict,
        view_index: int,
    ) -> dict | None:
        """Оценить одно аффинное представление эталона на текущем кадре."""
        matches = self._mutual_ratio_matches(view["descriptors"], frame_descriptors)
        if len(matches) < 10:
            return None

        src_points = np.float32([view["points"][match.queryIdx] for match in matches]).reshape(-1, 1, 2)
        matched_base_points = np.float32([view["base_points"][match.queryIdx] for match in matches])
        dst_points = np.float32([frame_points[match.trainIdx] for match in matches]).reshape(-1, 1, 2)

        homography, inlier_mask = cv2.findHomography(
            src_points,
            dst_points,
            self.homography_method,
            3.5,
        )
        if homography is None or inlier_mask is None:
            return None

        inlier_mask = inlier_mask.ravel().astype(bool)
        inliers = int(inlier_mask.sum())
        inlier_ratio = inliers / max(1, len(matches))
        if inliers < 8 or inlier_ratio < 0.30:
            return None

        warped_mask = warp_binary_mask(view["mask"], homography, frame_bgr.shape)
        bbox, polygon = self._mask_geometry(warped_mask)
        if bbox is None or polygon is None:
            return None

        warped_edges = warp_binary_mask(view["edges"], homography, frame_bgr.shape)

        feature_score = self._feature_score(inliers, len(matches))
        coverage_score = self._coverage_score(
            matched_base_points[inlier_mask],
            reference["mask_area"],
        )
        if feature_score < 0.34 or coverage_score < 0.08:
            return None

        edge_score = self._edge_score(frame_gray, warped_edges, bbox)
        appearance_score = self._appearance_score(frame_gray, homography, view)
        if edge_score < 0.16 or appearance_score < 0.14:
            return None

        color_score = self._color_score(frame_bgr, warped_mask, reference, bbox)
        mask_score = self._mask_quality_score(warped_mask, polygon, frame_bgr.shape)

        confidence = 100.0 * (
            0.32 * feature_score
            + 0.18 * coverage_score
            + 0.14 * edge_score
            + 0.14 * appearance_score
            + 0.12 * color_score
            + 0.10 * mask_score
        )
        confidence = round(float(confidence), 1)

        return {
            "confidence": confidence,
            "bbox": bbox,
            "polygon": polygon,
            "debug": {
                "mode": "feature",
                "view_index": view_index,
                "view_label": view["label"],
                "good_matches": len(matches),
                "inliers": inliers,
                "inlier_ratio": round(inlier_ratio, 3),
                "feature_score": round(feature_score, 3),
                "coverage_score": round(coverage_score, 3),
                "edge_score": round(edge_score, 3),
                "appearance_score": round(appearance_score, 3),
                "color_score": round(color_score, 3),
                "mask_score": round(mask_score, 3),
            },
        }

    def _proposal_from_candidates(
        self,
        frame_bgr: np.ndarray,
        frame_gray: np.ndarray,
        reference: dict,
        proposal_mask: np.ndarray | None,
        max_candidates: int | None = None,
    ) -> dict | None:
        """Оценить предложения контуров, извлечённые из маски кандидатов."""
        if proposal_mask is None or cv2.countNonZero(proposal_mask) < 160:
            return None

        contours = self._extract_candidate_contours(proposal_mask, reference, max_candidates=max_candidates)
        if not contours:
            return None

        best_candidate = None
        for contour in contours:
            candidate = self._evaluate_contour_candidate(frame_bgr, frame_gray, reference, contour)
            if candidate is None:
                continue
            if best_candidate is None or candidate["confidence"] > best_candidate["confidence"]:
                best_candidate = candidate
        return best_candidate

    def _evaluate_contour_candidate(
        self,
        frame_bgr: np.ndarray,
        frame_gray: np.ndarray,
        reference: dict,
        contour: np.ndarray,
    ) -> dict | None:
        """Оценить один контур-кандидат относительно представлений эталона."""
        contour_area = float(cv2.contourArea(contour))
        if contour_area < max(120.0, reference["mask_area"] * 0.012):
            return None

        candidate_mask = np.zeros(frame_gray.shape, dtype=np.uint8)
        cv2.drawContours(candidate_mask, [contour], -1, 255, thickness=-1)

        x, y, w, h = cv2.boundingRect(contour)
        if w < 14 or h < 14:
            return None

        bbox = [x, y, x + w, y + h]
        shape_score = self._shape_score(contour, reference)
        if shape_score < 0.10:
            return None

        color_score = self._color_score(frame_bgr, candidate_mask, reference, bbox)
        if color_score < 0.16:
            return None

        candidate_box = self._contour_box_points(contour)
        if candidate_box is None:
            return None

        rect = cv2.minAreaRect(contour)
        rect_w, rect_h = rect[1]
        min_side = max(1.0, min(rect_w, rect_h))
        max_side = max(1.0, max(rect_w, rect_h))
        candidate_aspect = max_side / min_side

        best_view_candidate = None
        for view_index, view in self._rank_views_for_candidate(reference["views"], candidate_aspect):
            if view["box_points"] is None or np.count_nonzero(view["box_points"]) == 0:
                continue

            transform = cv2.getPerspectiveTransform(view["box_points"], candidate_box)
            warped_mask = warp_binary_mask(view["mask"], transform, frame_bgr.shape)
            alignment_score = self._mask_alignment_score(candidate_mask, warped_mask)
            if alignment_score < 0.15:
                continue

            warped_edges = warp_binary_mask(view["edges"], transform, frame_bgr.shape)
            edge_score = self._edge_score(frame_gray, warped_edges, bbox)
            appearance_score = self._appearance_score(frame_gray, transform, view)
            if edge_score < 0.12 or appearance_score < 0.10:
                continue

            support_mask = cv2.bitwise_and(candidate_mask, warped_mask)
            if cv2.countNonZero(support_mask) < 140:
                support_mask = candidate_mask
            refined_color_score = self._color_score(frame_bgr, support_mask, reference, bbox)

            candidate_confidence = 100.0 * (
                0.32 * alignment_score
                + 0.24 * appearance_score
                + 0.20 * edge_score
                + 0.16 * refined_color_score
                + 0.08 * shape_score
            )
            candidate_confidence = round(float(candidate_confidence), 1)

            candidate = {
                "confidence": candidate_confidence,
                "bbox": bbox,
                "polygon": cv2.convexHull(contour).astype(np.float32),
                "debug": {
                    "mode": "proposal_color_geometry",
                    "view_index": view_index,
                    "view_label": view["label"],
                    "alignment_score": round(alignment_score, 3),
                    "appearance_score": round(appearance_score, 3),
                    "edge_score": round(edge_score, 3),
                    "color_score": round(refined_color_score, 3),
                    "shape_score": round(shape_score, 3),
                },
            }
            if best_view_candidate is None or candidate["confidence"] > best_view_candidate["confidence"]:
                best_view_candidate = candidate

        return best_view_candidate

    def _fallback_color_shape_candidate(
        self,
        frame_bgr: np.ndarray,
        frame_gray: np.ndarray,
        reference: dict,
        base_mask: np.ndarray | None = None,
        max_candidates: int | None = None,
    ) -> dict | None:
        """Использовать резервную оценку контура по цвету и форме."""
        if base_mask is None or cv2.countNonZero(base_mask) == 0:
            hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
            mask = self._reference_color_mask(hsv, reference)
        else:
            mask = base_mask.copy()

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        if max_candidates is not None:
            contours = contours[:max_candidates]
        best_candidate = None

        for contour in contours:
            area = float(cv2.contourArea(contour))
            if area < max(180.0, reference["mask_area"] * 0.04):
                continue

            x, y, w, h = cv2.boundingRect(contour)
            if w < 18 or h < 18:
                continue

            candidate_mask = np.zeros(mask.shape, dtype=np.uint8)
            cv2.drawContours(candidate_mask, [contour], -1, 255, thickness=-1)

            bbox = [x, y, x + w, y + h]
            color_score = self._color_score(frame_bgr, candidate_mask, reference, bbox)
            if color_score < 0.25:
                continue

            shape_score = self._shape_score(contour, reference)
            edge_score = self._edge_score(frame_gray, cv2.Canny(candidate_mask, 50, 150), bbox)
            mask_score = self._mask_quality_score(candidate_mask, contour.astype(np.float32), frame_bgr.shape)
            if shape_score < 0.18 or edge_score < 0.12:
                continue

            confidence = 100.0 * (
                0.44 * color_score
                + 0.34 * shape_score
                + 0.12 * edge_score
                + 0.10 * mask_score
            )
            confidence = round(float(confidence), 1)

            candidate = {
                "confidence": confidence,
                "bbox": bbox,
                "polygon": cv2.convexHull(contour).astype(np.float32),
                "debug": {
                    "mode": "fallback_color_shape",
                    "color_score": round(color_score, 3),
                    "shape_score": round(shape_score, 3),
                    "edge_score": round(edge_score, 3),
                    "mask_score": round(mask_score, 3),
                },
            }
            if best_candidate is None or candidate["confidence"] > best_candidate["confidence"]:
                best_candidate = candidate

        return best_candidate

    def _tracked_fast_candidate(
        self,
        frame_bgr: np.ndarray,
        frame_gray: np.ndarray,
        reference: dict,
        proposal_mask: np.ndarray | None,
    ) -> dict | None:
        """Быстро оценить кандидата внутри ROI без полного feature-refresh."""
        if proposal_mask is None or cv2.countNonZero(proposal_mask) < self._min_proposal_pixels:
            return None

        best_candidate = self._proposal_from_candidates(
            frame_bgr,
            frame_gray,
            reference,
            proposal_mask,
            max_candidates=self._tracked_candidate_contours,
        )
        if best_candidate is None or best_candidate["confidence"] < self._fast_track_confidence:
            fallback_candidate = self._fallback_color_shape_candidate(
                frame_bgr,
                frame_gray,
                reference,
                proposal_mask,
                max_candidates=self._tracked_candidate_contours,
            )
            if fallback_candidate is not None and (
                best_candidate is None or fallback_candidate["confidence"] > best_candidate["confidence"]
            ):
                best_candidate = fallback_candidate

        if best_candidate is None:
            return None

        best_candidate["debug"] = {
            **best_candidate["debug"],
            "mode": f"tracked_{best_candidate['debug']['mode']}",
        }
        return best_candidate

    def _combined_candidate_mask(
        self,
        frame_bgr: np.ndarray,
        reference: dict,
        focus_bbox: list[int] | None = None,
    ) -> np.ndarray:
        """Объединить несколько цветовых предложений в одну маску кандидатов."""
        if focus_bbox is not None:
            x1, y1, x2, y2 = self._expand_bbox(focus_bbox, frame_bgr.shape, margin=20)
            if x2 <= x1 or y2 <= y1:
                return np.zeros(frame_bgr.shape[:2], dtype=np.uint8)

            local_mask = self._build_candidate_mask(frame_bgr[y1:y2, x1:x2], reference)
            combined = np.zeros(frame_bgr.shape[:2], dtype=np.uint8)
            combined[y1:y2, x1:x2] = local_mask
            return combined

        return self._build_candidate_mask(frame_bgr, reference)

    def _build_candidate_mask(self, frame_bgr: np.ndarray, reference: dict) -> np.ndarray:
        """Построить комбинированную маску кандидатов для полного кадра или ROI."""
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        coarse_mask = self._reference_color_mask(hsv, reference)
        backprojection_mask = self._hist_backprojection_mask(hsv, reference)
        lab_mask = self._lab_chroma_mask(frame_bgr, reference)

        conservative = cv2.bitwise_and(coarse_mask, lab_mask)
        permissive = cv2.bitwise_and(backprojection_mask, cv2.bitwise_or(coarse_mask, lab_mask))
        combined = cv2.bitwise_or(conservative, permissive)

        if cv2.countNonZero(combined) < 160:
            combined = cv2.bitwise_or(cv2.bitwise_or(coarse_mask, backprojection_mask), lab_mask)

        kernel_size = 5 if max(frame_bgr.shape[:2]) < 900 else 7
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)
        combined = cv2.dilate(combined, kernel, iterations=1)
        return combined

    def _feature_search_mask(
        self,
        proposal_mask: np.ndarray | None,
        frame_shape: tuple[int, ...],
        focus_bbox: list[int] | None = None,
    ) -> np.ndarray | None:
        """Расширить маску кандидата для извлечения локальных признаков."""
        height, width = frame_shape[:2]
        search_mask = np.zeros((height, width), dtype=np.uint8)

        if proposal_mask is not None:
            pixels = int(cv2.countNonZero(proposal_mask))
            if pixels >= self._min_proposal_pixels:
                contours, _ = cv2.findContours(proposal_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                contours = sorted(contours, key=cv2.contourArea, reverse=True)
                min_blob_area = max(80.0, (height * width) * 0.00012)
                blobs_added = 0

                for contour in contours:
                    area = float(cv2.contourArea(contour))
                    if area < min_blob_area:
                        continue

                    x, y, w, h = cv2.boundingRect(contour)
                    margin_x = max(12, int(round(w * 0.35)))
                    margin_y = max(12, int(round(h * 0.35)))
                    x1 = max(0, x - margin_x)
                    y1 = max(0, y - margin_y)
                    x2 = min(width, x + w + margin_x)
                    y2 = min(height, y + h + margin_y)
                    cv2.rectangle(search_mask, (x1, y1), (x2, y2), 255, thickness=-1)
                    blobs_added += 1
                    if blobs_added >= self._top_feature_blobs:
                        break

        if focus_bbox is not None:
            x1, y1, x2, y2 = self._expand_adaptive_bbox(focus_bbox, frame_shape, scale=0.55, min_margin=28)
            cv2.rectangle(search_mask, (x1, y1), (x2, y2), 255, thickness=-1)

        if cv2.countNonZero(search_mask) == 0:
            return None

        coverage = cv2.countNonZero(search_mask) / float(max(1, height * width))
        if focus_bbox is None and coverage > 0.72:
            return None

        kernel_size = 11 if focus_bbox is not None else 15
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        return cv2.dilate(search_mask, kernel, iterations=1)

    def _extract_candidate_contours(
        self,
        proposal_mask: np.ndarray,
        reference: dict,
        max_candidates: int | None = None,
    ) -> list[np.ndarray]:
        """Извлечь подходящие контуры-кандидаты из маски."""
        contours, _ = cv2.findContours(proposal_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return []

        frame_area = proposal_mask.shape[0] * proposal_mask.shape[1]
        min_area = max(120.0, reference["mask_area"] * 0.010, frame_area * 0.00015)
        max_area = frame_area * 0.75

        filtered: list[np.ndarray] = []
        for contour in contours:
            area = float(cv2.contourArea(contour))
            if area < min_area or area > max_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            if w < 14 or h < 14:
                continue

            extent = area / max(1.0, float(w * h))
            if extent < 0.18:
                continue
            filtered.append(contour)

        filtered.sort(key=cv2.contourArea, reverse=True)
        limit = self._max_candidate_contours if max_candidates is None else max_candidates
        return filtered[:limit]

    def _rank_views_for_candidate(self, views: list[dict], candidate_aspect: float) -> list[tuple[int, dict]]:
        """Отсортировать представления эталона по близости отношения сторон."""
        ranked = sorted(
            enumerate(views),
            key=lambda item: abs(math.log(max(1e-6, candidate_aspect / max(1e-6, item[1]["aspect_ratio"])))),
        )
        return ranked[:self._max_ranked_views]

    def _mask_alignment_score(self, candidate_mask: np.ndarray, warped_mask: np.ndarray) -> float:
        """Оценить качество перекрытия маски кандидата и спроецированного вида."""
        candidate_area = float(cv2.countNonZero(candidate_mask))
        warped_area = float(cv2.countNonZero(warped_mask))
        if candidate_area < 1.0 or warped_area < 1.0:
            return 0.0

        intersection = float(cv2.countNonZero(cv2.bitwise_and(candidate_mask, warped_mask)))
        coverage = intersection / warped_area
        precision = intersection / candidate_area
        return float(0.58 * coverage + 0.42 * precision)

    def _hist_backprojection_mask(self, frame_hsv: np.ndarray, reference: dict) -> np.ndarray:
        """Построить маску кандидата с помощью обратной проекции гистограммы."""
        backprojection = cv2.calcBackProject([frame_hsv], [0, 1], reference["hist"], [0, 180, 0, 256], 1.0)
        backprojection = cv2.GaussianBlur(backprojection, (5, 5), 0)
        backprojection = cv2.normalize(backprojection, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        _, mask = cv2.threshold(backprojection, 45, 255, cv2.THRESH_BINARY)
        return mask

    def _lab_chroma_mask(self, frame_bgr: np.ndarray, reference: dict) -> np.ndarray:
        """Построить маску кандидата по сходству хромы в цветовом пространстве LAB."""
        lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
        ref_mean = reference["lab_stats"][:3].astype(np.float32)
        ref_std = reference["lab_stats"][3:].astype(np.float32)

        chroma_diff = np.linalg.norm(lab[:, :, 1:3] - ref_mean[1:3], axis=2)
        chroma_tol = float(np.clip(max(18.0, np.linalg.norm(ref_std[1:3]) * 2.5), 18.0, 64.0))

        luminance_diff = np.abs(lab[:, :, 0] - ref_mean[0])
        luminance_tol = float(np.clip(max(32.0, ref_std[0] * 3.2), 32.0, 88.0))

        mask = (chroma_diff <= chroma_tol) & (luminance_diff <= luminance_tol)
        return (mask.astype(np.uint8) * 255)

    def reset_tracking(self) -> None:
        """Сбросить состояние поиска вокруг последней детекции."""
        self._tracked_reference_name = None
        self._tracked_bbox_norm = None
        self._tracking_misses = 0

    def warmup(self, reference: dict | None) -> None:
        """Подготовить экстрактор и matcher после загрузки эталона."""
        if reference is None:
            return

        try:
            gray = normalize_gray(reference["image"])
            self.extractor.detectAndCompute(gray, reference["mask"])

            if reference["views"]:
                descriptors = reference["views"][0]["descriptors"]
                if descriptors is not None and len(descriptors) >= 8:
                    sample = descriptors[: min(64, len(descriptors))]
                    self.matcher.knnMatch(sample, sample, k=2)
        except Exception:
            return

    def _register_success(self, reference_name: str, bbox: list[int], frame_shape: tuple[int, ...]) -> None:
        """Сохранить область успешной детекции для следующих кадров."""
        height, width = frame_shape[:2]
        x1, y1, x2, y2 = bbox
        self._tracked_reference_name = reference_name
        self._tracked_bbox_norm = (
            x1 / float(max(1, width)),
            y1 / float(max(1, height)),
            x2 / float(max(1, width)),
            y2 / float(max(1, height)),
        )
        self._tracking_misses = 0

    def _register_miss(self, reference_name: str) -> None:
        """Обновить счетчик пропусков для ROI-поиска."""
        if self._tracked_reference_name != reference_name or self._tracked_bbox_norm is None:
            return
        self._tracking_misses += 1
        if self._tracking_misses > self._max_tracking_misses:
            self.reset_tracking()

    def _predict_focus_bbox(self, frame_shape: tuple[int, ...], reference_name: str) -> list[int] | None:
        """Восстановить область поиска по последней детекции."""
        if self._tracked_reference_name != reference_name or self._tracked_bbox_norm is None:
            return None

        height, width = frame_shape[:2]
        x1 = int(round(self._tracked_bbox_norm[0] * width))
        y1 = int(round(self._tracked_bbox_norm[1] * height))
        x2 = int(round(self._tracked_bbox_norm[2] * width))
        y2 = int(round(self._tracked_bbox_norm[3] * height))
        bbox = [x1, y1, x2, y2]
        return list(self._expand_adaptive_bbox(bbox, frame_shape, scale=0.45 + 0.10 * self._tracking_misses, min_margin=24))

    def _restrict_mask_to_bbox(
        self,
        mask: np.ndarray | None,
        bbox: list[int] | None,
        margin: int,
    ) -> np.ndarray | None:
        """Ограничить маску областью вокруг ROI."""
        if mask is None or bbox is None:
            return mask

        x1, y1, x2, y2 = self._expand_bbox(bbox, mask.shape, margin=margin)
        restricted = np.zeros_like(mask)
        restricted[y1:y2, x1:x2] = mask[y1:y2, x1:x2]
        return restricted

    def _mutual_ratio_matches(self, reference_descriptors: np.ndarray, frame_descriptors: np.ndarray) -> list[cv2.DMatch]:
        """Найти совпадения, прошедшие проверку отношения расстояний и взаимную проверку."""
        forward_pairs = self.matcher.knnMatch(reference_descriptors, frame_descriptors, k=2)
        reverse_pairs = self.matcher.knnMatch(frame_descriptors, reference_descriptors, k=2)

        reverse_best: dict[int, int] = {}
        for pair in reverse_pairs:
            if len(pair) < 2:
                continue
            best, second = pair
            if best.distance < 0.82 * second.distance:
                reverse_best[best.queryIdx] = best.trainIdx

        good_matches: list[cv2.DMatch] = []
        for pair in forward_pairs:
            if len(pair) < 2:
                continue
            best, second = pair
            if best.distance >= 0.78 * second.distance:
                continue
            if reverse_best.get(best.trainIdx) != best.queryIdx:
                continue
            good_matches.append(best)
        return good_matches

    def _mask_geometry(self, warped_mask: np.ndarray) -> tuple[list[int] | None, np.ndarray | None]:
        """Извлечь ограничивающий прямоугольник и полигон из спроецированной маски."""
        contours, _ = cv2.findContours(warped_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, None

        contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(contour)
        if area < 350:
            return None, None

        hull = cv2.convexHull(contour)
        x, y, w, h = cv2.boundingRect(hull)
        if w < 16 or h < 16:
            return None, None

        polygon = cv2.approxPolyDP(hull, 0.015 * cv2.arcLength(hull, True), True)
        if polygon is None or len(polygon) < 4:
            polygon = hull
        return [x, y, x + w, y + h], polygon.astype(np.float32)

    def _color_score(self, frame_bgr: np.ndarray, warped_mask: np.ndarray, reference: dict, bbox: list[int]) -> float:
        """Оценить цветовое сходство кандидата и эталона."""
        x1, y1, x2, y2 = self._expand_bbox(bbox, frame_bgr.shape, margin=14)
        frame_crop = frame_bgr[y1:y2, x1:x2]
        mask_crop = warped_mask[y1:y2, x1:x2]
        if cv2.countNonZero(mask_crop) < 220:
            return 0.0

        hist = compute_masked_hs_hist(frame_crop, mask_crop)
        hist_distance = cv2.compareHist(reference["hist"], hist, cv2.HISTCMP_BHATTACHARYYA)
        hist_score = max(0.0, 1.0 - float(hist_distance))

        lab = cv2.cvtColor(frame_crop, cv2.COLOR_BGR2LAB).astype(np.float32)
        pixels = lab[mask_crop > 0]
        if pixels.size == 0:
            return float(hist_score)

        ref_mean = reference["lab_stats"][:3].astype(np.float32)
        distances = np.linalg.norm(pixels - ref_mean, axis=1)
        cutoff = float(np.quantile(distances, 0.75))
        trimmed_pixels = pixels[distances <= cutoff]
        if trimmed_pixels.size == 0:
            trimmed_pixels = pixels

        trimmed_mean = trimmed_pixels.mean(axis=0)
        trimmed_std = trimmed_pixels.std(axis=0)
        trimmed_stats = np.concatenate([trimmed_mean, trimmed_std]).astype(np.float32)

        diff = float(np.linalg.norm(reference["lab_stats"] - trimmed_stats))
        lab_score = math.exp(-diff / 36.0)
        return float(0.45 * hist_score + 0.55 * lab_score)

    def _edge_score(self, frame_gray: np.ndarray, warped_edges: np.ndarray, bbox: list[int]) -> float:
        """Оценить, насколько спроецированные границы совпадают с границами кадра."""
        x1, y1, x2, y2 = self._expand_bbox(bbox, frame_gray.shape, margin=18)
        gray_crop = frame_gray[y1:y2, x1:x2]
        edges_crop = warped_edges[y1:y2, x1:x2]

        edge_pixels = int(cv2.countNonZero(edges_crop))
        if edge_pixels < 40:
            return 0.0

        frame_edges = cv2.Canny(gray_crop, 60, 150)
        dist = cv2.distanceTransform(255 - frame_edges, cv2.DIST_L2, 3)
        distances = dist[edges_crop > 0]
        if distances.size == 0:
            return 0.0

        near_fraction = float(np.mean(distances <= 3.0))
        mean_distance = float(np.mean(distances))
        smooth_score = math.exp(-(mean_distance ** 2) / (2.0 * 3.0 ** 2))
        return float(0.6 * near_fraction + 0.4 * smooth_score)

    def _appearance_score(self, frame_gray: np.ndarray, homography: np.ndarray, view: dict) -> float:
        """Оценить сходство внешнего вида после обратного преобразования в пространство вида."""
        try:
            inverse_h = np.linalg.inv(homography)
        except np.linalg.LinAlgError:
            return 0.0

        rectified_gray = cv2.warpPerspective(
            frame_gray,
            inverse_h,
            (view["width"], view["height"]),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT,
        )
        rectified_grad = self._gradient_magnitude(rectified_gray)
        mask = view["mask"] > 0
        if int(np.count_nonzero(mask)) < 250:
            return 0.0

        gray_score = self._masked_correlation(view["gray"], rectified_gray, mask)
        grad_score = self._masked_correlation(view["grad"], rectified_grad, mask)
        return float(0.35 * gray_score + 0.65 * grad_score)

    def _feature_score(self, inliers: int, total_matches: int) -> float:
        """Преобразовать сырую поддержку признаков в нормализованную оценку."""
        support_score = min(1.0, inliers / 24.0)
        ratio_score = min(1.0, inliers / max(1.0, total_matches))
        return float(0.6 * support_score + 0.4 * ratio_score)

    def _coverage_score(self, inlier_base_points: np.ndarray, reference_mask_area: int) -> float:
        """Оценить, какая часть эталона покрыта согласованными совпадениями."""
        if len(inlier_base_points) < 4:
            return 0.0

        hull = cv2.convexHull(inlier_base_points.reshape(-1, 1, 2).astype(np.float32))
        hull_area = cv2.contourArea(hull)
        denom = max(1200.0, float(reference_mask_area) * 0.45)
        return float(min(1.0, hull_area / denom))

    def _mask_quality_score(self, warped_mask: np.ndarray, polygon: np.ndarray, frame_shape: tuple[int, int, int]) -> float:
        """Оценить, насколько спроецированная маска похожа на корректную детекцию."""
        mask_area = float(cv2.countNonZero(warped_mask))
        polygon_area = float(cv2.contourArea(polygon.reshape(-1, 2).astype(np.float32)))
        if mask_area <= 1.0 or polygon_area <= 1.0:
            return 0.0

        fill_ratio = min(mask_area, polygon_area) / max(mask_area, polygon_area)

        h, w = frame_shape[:2]
        x1 = max(0, int(np.min(polygon[:, 0, 0])))
        y1 = max(0, int(np.min(polygon[:, 0, 1])))
        x2 = min(w, int(np.max(polygon[:, 0, 0])))
        y2 = min(h, int(np.max(polygon[:, 0, 1])))
        if x2 <= x1 or y2 <= y1:
            return 0.0

        bbox_area_ratio = ((x2 - x1) * (y2 - y1)) / float(max(1, w * h))
        if bbox_area_ratio > 0.70:
            return 0.0

        return float(fill_ratio)

    def _shape_score(self, contour: np.ndarray, reference: dict) -> float:
        """Оценить геометрическое сходство контура и эталона."""
        if reference["contour"] is None or len(reference["contour"]) == 0:
            return 0.0

        shape_distance = cv2.matchShapes(reference["contour"], contour, cv2.CONTOURS_MATCH_I1, 0.0)
        shape_match = math.exp(-3.2 * float(shape_distance))

        (_, _), (w, h), _ = cv2.minAreaRect(contour)
        min_side = max(1.0, min(w, h))
        max_side = max(1.0, max(w, h))
        aspect_ratio = max_side / min_side
        rectangularity = float(cv2.contourArea(contour)) / max(1.0, w * h)

        aspect_score = math.exp(-1.6 * abs(math.log(max(1e-6, aspect_ratio / reference["aspect_ratio"]))))
        rect_score = math.exp(-4.0 * abs(rectangularity - reference["rectangularity"]))
        return float(0.5 * shape_match + 0.3 * aspect_score + 0.2 * rect_score)

    def _contour_box_points(self, contour: np.ndarray) -> np.ndarray | None:
        """Вернуть упорядоченные углы прямоугольника для контура-кандидата."""
        if contour is None or len(contour) < 4:
            return None

        points = cv2.boxPoints(cv2.minAreaRect(contour)).astype(np.float32)
        return self._order_points(points)

    def _reference_color_mask(self, frame_hsv: np.ndarray, reference: dict) -> np.ndarray:
        """Построить грубую маску в HSV по цветовой статистике эталона."""
        ref_mean = reference["hsv_mean"]
        ref_std = reference["hsv_std"]

        h_tol = int(np.clip(max(12.0, ref_std[0] * 3.5), 12, 32))
        s_tol = int(np.clip(max(34.0, ref_std[1] * 3.4), 34, 108))
        v_tol = int(np.clip(max(46.0, ref_std[2] * 4.0), 46, 132))

        hue = frame_hsv[:, :, 0].astype(np.int16)
        sat = frame_hsv[:, :, 1].astype(np.int16)
        val = frame_hsv[:, :, 2].astype(np.int16)

        ref_h = int(round(float(ref_mean[0])))
        hue_diff = np.abs(hue - ref_h)
        hue_diff = np.minimum(hue_diff, 180 - hue_diff)

        sat_diff = np.abs(sat - int(round(float(ref_mean[1]))))
        val_diff = np.abs(val - int(round(float(ref_mean[2]))))

        mask = (
            (hue_diff <= h_tol)
            & (sat_diff <= s_tol)
            & (val_diff <= v_tol)
            & (sat >= max(18, int(round(float(ref_mean[1]) * 0.25))))
        )
        return (mask.astype(np.uint8) * 255)

    def _normalize_descriptors(self, descriptors: np.ndarray | None) -> np.ndarray | None:
        """Нормализовать дескрипторы перед передачей в сопоставитель."""
        if descriptors is None:
            return None
        if self.feature_name == "sift":
            return apply_rootsift(descriptors)
        return descriptors

    def _expand_bbox(self, bbox: list[int], frame_shape: tuple[int, ...], margin: int) -> tuple[int, int, int, int]:
        """Расширить ограничивающий прямоугольник на заданный отступ в пределах кадра."""
        height, width = frame_shape[:2]
        x1, y1, x2, y2 = bbox
        return (
            max(0, x1 - margin),
            max(0, y1 - margin),
            min(width, x2 + margin),
            min(height, y2 + margin),
        )

    def _expand_adaptive_bbox(
        self,
        bbox: list[int],
        frame_shape: tuple[int, ...],
        scale: float,
        min_margin: int,
    ) -> tuple[int, int, int, int]:
        """Расширить ROI пропорционально его размеру."""
        x1, y1, x2, y2 = bbox
        width_box = max(1, x2 - x1)
        height_box = max(1, y2 - y1)
        margin = max(min_margin, int(round(max(width_box, height_box) * scale)))
        return self._expand_bbox(bbox, frame_shape, margin=margin)

    def _masked_correlation(self, first: np.ndarray, second: np.ndarray, mask: np.ndarray) -> float:
        """Вычислить нормализованную корреляцию внутри бинарной маски."""
        values_a = first[mask].astype(np.float32)
        values_b = second[mask].astype(np.float32)
        if values_a.size < 100:
            return 0.0

        values_a -= float(values_a.mean())
        values_b -= float(values_b.mean())
        std_a = float(values_a.std())
        std_b = float(values_b.std())
        if std_a < 1e-6 or std_b < 1e-6:
            return 0.0

        corr = float(np.mean((values_a / std_a) * (values_b / std_b)))
        corr = max(-1.0, min(1.0, corr))
        return max(0.0, min(1.0, (corr + 1.0) / 2.0))

    @staticmethod
    def _gradient_magnitude(gray: np.ndarray) -> np.ndarray:
        """Вычислить модуль градиента для изображения в оттенках серого."""
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        return cv2.magnitude(gx, gy)

    @staticmethod
    def _order_points(points: np.ndarray) -> np.ndarray:
        """Упорядочить точки прямоугольника по часовой стрелке от левого верхнего угла."""
        points = np.asarray(points, dtype=np.float32)
        if points.shape != (4, 2):
            raise ValueError("Expected four 2D points")

        sums = points.sum(axis=1)
        diffs = np.diff(points, axis=1).ravel()

        ordered = np.zeros((4, 2), dtype=np.float32)
        ordered[0] = points[np.argmin(sums)]
        ordered[2] = points[np.argmax(sums)]
        ordered[1] = points[np.argmin(diffs)]
        ordered[3] = points[np.argmax(diffs)]
        return ordered
